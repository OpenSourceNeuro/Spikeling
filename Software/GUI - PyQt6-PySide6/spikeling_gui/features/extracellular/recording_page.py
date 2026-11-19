"""Recording overview, bounded preview and CSV export."""
from concurrent.futures import Future
from itertools import islice
import json
from pathlib import Path
from threading import Thread

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import QEvent, QTimer
from PySide6.QtWidgets import QFileDialog, QWidget

from spikeling_gui.appearance.theme_manager import EXTRACELLULAR_CHANNEL_KEYS, theme_manager
from spikeling_gui.paths import recordings_directory
from spikeling_gui.ui.generated.UI_ExtracellularRecording import Ui_ExtracellularRecording

from .acquisition import CONTACTS
from .legacy_import import LegacyRecording
from .session_reader import SessionReader

MAX_PREVIEW_ROWS = 40000


def load_overview(path):
    if path.suffix.lower() == ".csv":
        reader = LegacyRecording(path)
        return reader, {"summary": reader.summary, "sidecar": reader.metadata}
    reader = SessionReader(path.parent)
    # Preview the opening provenance and epochs. All epochs and gaps remain
    # available to callers via the iterator, including very long sessions.
    return reader, {
        "summary": reader.summary,
        "acquisition": reader.manifest["acquisition"],
        "capture_id": reader.manifest["capture_id"],
        "failure": reader.failure,
        "opening_metadata": [(kind, data[:3] if kind == "spans" else data)
                             for kind, data in islice(reader.iter_metadata(), 12)],
    }


def preview_data(reader, stage, start, stop, channels):
    times, values = [], []
    previous = None
    for _, segment, time, matrix in reader.iter_interval(stage, start, stop, channels):
        if previous is not None and segment != previous:
            times.append(np.array([np.nan]))
            values.append(np.full((1, len(channels)), np.nan))
        times.append(time)
        values.append(matrix)
        previous = segment
    if times:
        return np.concatenate(times), np.concatenate(values)
    return np.empty(0), np.empty((0, len(channels)))


class RecordingPage(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.ui = Ui_ExtracellularRecording()
        self.ui.setupUi(self)
        self.host = parent
        self.reader = None
        self.result = None
        self.timer = QTimer(self, interval=40)
        self.timer.timeout.connect(self._poll)
        self.ui.openButton.clicked.connect(self.open_recording)
        self.ui.previewButton.clicked.connect(self.preview)
        self.ui.stageCombo.activated.connect(self.preview)
        self.ui.exportButton.clicked.connect(self.export)
        self.ui.indexEdit.returnPressed.connect(self.preview)
        self.ui.countEdit.returnPressed.connect(self.preview)
        self.plots = pg.GraphicsLayoutWidget()
        self.ui.plotLayout.addWidget(self.plots)
        theme_manager.set_plot_background_role(self.plots, "panel_background")
        self.axes = []
        for row, (channel, colour) in enumerate(zip(CONTACTS, EXTRACELLULAR_CHANNEL_KEYS)):
            axis = self.plots.addPlot(row=row, col=0)
            axis.setLabel("left", channel, units="µV")
            if self.axes:
                axis.setXLink(self.axes[0][0])
            axis.setLabel("bottom", self.tr("Model time"), units="ms")
            if row != len(CONTACTS) - 1:
                axis.showAxis("bottom", False)
            curve = theme_manager.themed_plot(axis, [], [], colour, connect="finite")
            self.axes.append((axis, curve))
        self._enable()

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.Type.LanguageChange and hasattr(self, "axes"):
            selected = self.ui.stageCombo.currentData()
            self.ui.retranslateUi(self)
            self._stage_choices(selected)
            for axis, _ in self.axes:
                axis.setLabel("bottom", self.tr("Model time"), units="ms")

    def show_page(self):
        self.host.ui.mainbody_stackedWidget.setCurrentWidget(self)

    def _enable(self):
        busy = self.result is not None
        ready = self.reader is not None and not busy and self.reader.sample_count > 0
        self.ui.openButton.setEnabled(not busy)
        for widget in (self.ui.stageCombo, self.ui.indexEdit, self.ui.countEdit, self.ui.previewButton):
            widget.setEnabled(ready)
        self.ui.exportButton.setEnabled(ready and isinstance(self.reader, SessionReader))

    def _background(self, function, complete):
        if self.result is not None:
            return
        future = Future()

        def run():
            try:
                future.set_result(function())
            except Exception as error:
                future.set_exception(error)

        self.result = future, complete
        self._enable()
        self.timer.start()
        Thread(target=run, daemon=True, name="Extracellular recording reader").start()

    def _poll(self):
        future, complete = self.result
        if not future.done():
            return
        self.timer.stop()
        self.result = None
        self._enable()
        try:
            complete(future.result())
        except Exception as error:
            self.ui.statusLabel.setText(self.tr("Recording error") + " · " + str(error))

    def _stage_choices(self, selected=None):
        self.ui.stageCombo.clear()
        if self.reader is None:
            return
        for stage in self.reader.stages:
            label = self.tr("Synthetic broadband") if stage == "broadband" else self.tr("Live processed")
            self.ui.stageCombo.addItem(label, stage)
        index = self.ui.stageCombo.findData(selected)
        if index >= 0:
            self.ui.stageCombo.setCurrentIndex(index)

    def open_recording(self):
        name, _ = QFileDialog.getOpenFileName(
            self, self.tr("Open extracellular recording"), str(recordings_directory()),
            self.tr("Extracellular recordings (manifest.json *.csv)"),
        )
        if name:
            self.open_path(name)

    def open_path(self, name):
        writer = self.host.extracellular_graph.session_recording.writer
        if writer is not None and Path(name).parent.resolve() == writer.partial.resolve():
            self.ui.statusLabel.setText(self.tr("Stop the capture before opening this session."))
            return
        self.ui.statusLabel.setText(self.tr("Validating recording…"))
        self._background(lambda: load_overview(Path(name)), self._loaded)

    def _loaded(self, result):
        self.reader, metadata = result
        self.ui.metadata.setPlainText(json.dumps(metadata, ensure_ascii=False, indent=2))
        self.ui.indexEdit.setText(str(self.reader.first_index))
        self._stage_choices()
        self._enable()
        self.preview()

    def _interval(self):
        try:
            first = int(self.ui.indexEdit.text())
            count = int(self.ui.countEdit.text())
            if not self.reader.first_index <= first < self.reader.end_index or not 1 <= count <= MAX_PREVIEW_ROWS:
                raise ValueError
        except ValueError:
            self.ui.statusLabel.setText(self.tr("Use an accepted index in range and 1–40,000 rows."))
            return None
        return first, min(first + count, self.reader.end_index)

    def preview(self):
        if self.reader is None or self.result is not None:
            return
        summary = self.reader.summary
        status = (self.tr("Recovered · incomplete") if self.reader.recovered else
                  self.tr("Validated · complete") if isinstance(self.reader, SessionReader) else
                  self.tr("Validated CSV"))
        if "broadband" not in self.reader.stages:
            status += " · " + self.tr("Broadband unavailable")
        self.ui.statusLabel.setText(f"{status} · {summary['samples']:,} {self.tr('samples')}")
        if not self.reader.sample_count:
            for _, curve in self.axes:
                curve.setData([], [])
            return
        interval = self._interval()
        if interval is None:
            return
        reader, stage, channels = self.reader, self.ui.stageCombo.currentData(), summary["channels"]
        self._background(lambda: preview_data(reader, stage, *interval, channels),
                         lambda data: self._draw(data, channels))

    def _draw(self, data, channels):
        times, values = data
        finite = values[np.isfinite(values)]
        if finite.size:
            low, high = float(finite.min()), float(finite.max())
            if low == high:
                low, high = low - 1, high + 1
        for channel, (axis, curve) in zip(CONTACTS, self.axes):
            visible = channel in channels
            axis.setVisible(visible)
            axis.showAxis("bottom", visible and channel == channels[-1])
            if visible:
                curve.setData(times, values[:, channels.index(channel)])
                axis.enableAutoRange(axis="x")
                if finite.size:
                    axis.setYRange(low, high)
            else:
                curve.setData([], [])

    def export(self):
        interval = self._interval()
        if interval is None:
            return
        name, _ = QFileDialog.getSaveFileName(
            self, self.tr("Export selected interval"), str(recordings_directory()), self.tr("CSV files (*.csv)"),
        )
        if name:
            reader, stage = self.reader, self.ui.stageCombo.currentData()
            path = Path(name)
            if path.suffix.lower() != ".csv":
                path = path.with_suffix(".csv")
            self._background(lambda: reader.export_csv(path, stage, *interval),
                             lambda _: self.ui.statusLabel.setText(self.tr("CSV interval exported")))
