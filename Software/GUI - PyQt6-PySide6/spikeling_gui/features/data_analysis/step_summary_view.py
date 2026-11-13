"""Single-recording input–output measurements for reviewed sweeps."""

import csv

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import QObject, QSignalBlocker
from PySide6.QtWidgets import QTableWidgetItem
from pyqtgraph.exporters import ImageExporter

from spikeling_gui.appearance.theme_manager import theme_manager

from . import page
from .recording import NEURON_NAMES, STIMULUS_COLUMN
from .step_summary import average_step_traces, level_groups, points_for_sweeps, protocol_groups, statistics
from .sweep_view import STEP_INPUT_KEYS, STEP_INPUT_UNITS, display, number


SPIKE_METRICS = (
    ("rate", "Firing rate (Hz)"),
    ("count", "Spike count"),
    ("latency", "First-spike latency (ms)"),
    ("probability", "Sweeps with a spike (%)"),
)


class StepSummaryView(QObject):
    def __init__(self, sweeps):
        super().__init__(sweeps.window.ui.DataAnalysis_stepSummaryPage)
        self.sweeps = sweeps
        self.form = ui = page.bind_controls(sweeps.window.ui, "Summary", (
            "contextLabel", "inputCombo", "protocolCombo", "metricCombo", "toleranceEdit",
            "summaryLabel", "summaryTable", "summarySplitter", "plot", "inspectButton",
            "exportButton", "silentCheck", "averageInputPlot", "metricLabel", "averageImageButton",
        ))
        self.silent_check = ui.silentCheck
        self.averages = False
        self.average_rows = []
        self.summary_export_text = ui.exportButton.text()
        self.protocols = []
        self.groups = []
        self.selected = None
        self.silent_check.toggled.connect(self.rebuild)
        ui.summarySplitter.setSizes([650, 320])
        theme_manager.set_plot_background_role(ui.plot, "panel_background")
        ui.plot.showGrid(x=True, y=True, alpha=.25)
        theme_manager.set_plot_background_role(ui.averageInputPlot, "panel_background")
        ui.averageInputPlot.showGrid(x=True, y=True, alpha=.25)
        for axis in ("left", "bottom"):
            ui.averageInputPlot.getAxis(axis).enableAutoSIPrefix(False)
        for plot in (ui.averageInputPlot, ui.plot):
            plot.getViewBox().sigXRangeChanged.connect(self.sync_average_range)
        ui.plot.getAxis("bottom").enableAutoSIPrefix(False)
        ui.plot.getAxis("left").enableAutoSIPrefix(False)
        ui.inputCombo.currentIndexChanged.connect(self.input_changed)
        ui.toleranceEdit.editingFinished.connect(self.rebuild)
        ui.protocolCombo.currentIndexChanged.connect(self.draw)
        ui.metricCombo.currentIndexChanged.connect(self.draw)
        ui.inspectButton.clicked.connect(self.inspect)
        ui.exportButton.clicked.connect(self.export)
        ui.averageImageButton.clicked.connect(self.export_average_image)

    def sync_average_range(self, source, limits):
        if self.averages:
            page.sync_plot_x_range((self.form.averageInputPlot, self.form.plot), source, limits)

    def load(self, *, iv=False, averages=False):
        self.averages = averages
        sweeps = self.sweeps
        self.recording = sweeps.recording
        ui = self.form
        neuron, _, self.signal_label, unit, _ = sweeps.response()
        self.neuron = neuron
        self.spikes = sweeps.window.analysis_spikes if neuron != 0 or self.recording.clamp_mode == "CC" else None
        ui.contextLabel.setText(self.recording.source.name)
        ui.averageInputPlot.setVisible(averages)
        if ui.plot.plotItem.legend is not None:
            ui.plot.plotItem.legend.setVisible(averages)
        ui.metricCombo.setVisible(not averages)
        ui.metricLabel.setVisible(not averages)
        ui.summaryTable.setVisible(not averages)
        ui.inspectButton.setVisible(not averages)
        ui.averageImageButton.setVisible(averages)
        ui.exportButton.setText("Export average traces CSV" if averages else self.summary_export_text)
        with QSignalBlocker(ui.inputCombo), QSignalBlocker(ui.metricCombo), QSignalBlocker(ui.silentCheck):
            ui.silentCheck.setChecked(False)
            ui.silentCheck.setVisible(self.spikes is not None)
            ui.inputCombo.clear()
            ui.metricCombo.clear()
            ui.inputCombo.addItem("Recorded stimulus change (%)", "")
            for key, label in (("command_current", "Command current (a.u.)"),
                               ("command_voltage", "Command voltage (mV)")):
                if key in self.recording.extra_channels:
                    ui.inputCombo.addItem(label, key)
            metrics = [
                ("peak", f"Peak change ({unit})"), ("late_change", f"Late change ({unit})"),
                ("baseline", f"Baseline ({unit})"), ("late", f"Late response ({unit})"),
            ]
            if self.recording.clamp_mode == "VC" and sweeps.form.signalCombo.currentIndex() == 1:
                metrics = [
                    ("peak_inward", "Peak inward ΔI (nA)"),
                    ("peak_outward", "Peak outward ΔI (nA)"),
                    ("late", "Late mean current (nA)"),
                    *[(key, label) for key, label in metrics if key != "late"],
                ]
            if self.spikes is not None:
                metrics = [*SPIKE_METRICS, *metrics]
            for key, label in metrics:
                ui.metricCombo.addItem(label, key)
            ui.inputCombo.setCurrentIndex(ui.inputCombo.findData("command_voltage" if iv else sweeps.input_key))
        self.input_changed()

    def input_changed(self, *args):
        ui = self.form
        tolerance = .05 if ui.inputCombo.currentData() else self.sweeps.settings.get("Edge tolerance", .001)
        ui.toleranceEdit.setText(str(tolerance))
        self.rebuild()

    def rebuild(self, *args):
        ui = self.form
        ui.protocolCombo.blockSignals(True)
        ui.protocolCombo.clear()
        self.protocols = []
        self.tolerance_error = ""
        try:
            self.tolerance = number(ui.toleranceEdit, "input tolerance", 0)
        except ValueError as error:
            self.tolerance_error = str(error)
            ui.protocolCombo.blockSignals(False)
            self.draw()
            return
        key = ui.inputCombo.currentData()
        command = self.recording.extra_channels[key] if key else None

        points, self.skipped = points_for_sweeps(
            self.recording, self.sweeps.sweeps, self.sweeps.metrics, self.sweeps.is_included, command, self.tolerance,
            measure_stimulus_change=bool(self.sweeps.input_key and not key),
        )
        self.protocols = protocol_groups(points, self.recording.nominal_step_ms, self.tolerance)
        for points in self.protocols:
            duration = float(np.mean([point.duration_ms for point in points]))
            holding = points[0].holding
            label = f"{duration:g} ms"
            if holding is not None:
                label += f" · holding {np.mean([p.holding for p in points]):g}"
            ui.protocolCombo.addItem(label)
        ui.protocolCombo.blockSignals(False)
        self.draw()

    def draw(self, *args):
        ui = self.form
        if self.averages:
            self.draw_averages()
            return
        ui.plot.clear()
        ui.plot.enableAutoRange(axis="x")
        ui.plot.setLabel("bottom", ui.inputCombo.currentText())
        ui.plot.setLabel("left", ui.metricCombo.currentText())
        ui.plot.enableAutoRange(axis="y")
        ui.summaryTable.setRowCount(0)
        self.selected = None
        self.groups = []
        ui.inspectButton.setEnabled(False)
        ui.inspectButton.setText("Inspect selected sweep")
        ui.exportButton.setEnabled(False)
        index = ui.protocolCombo.currentIndex()
        if not 0 <= index < len(self.protocols):
            ui.summaryLabel.setText(self.tolerance_error or "No included sweeps have a usable input level.")
            return
        metric = ui.metricCombo.currentData()
        points = self.protocols[index]
        if self.silent_check.isChecked():
            points = [point for point in points if point.metrics.get("count") == 0]
        self.groups = level_groups(points, self.tolerance)
        rows = [statistics(group, metric) for group in self.groups]
        ui.summaryTable.setRowCount(len(rows))
        levels = [row["level"] for row in rows]
        spacing = min(np.diff(levels)) if len(levels) > 1 else max(abs(levels[0]) * .1, 1) if levels else 1
        x, y, indices = [], [], []
        for i, (group, row) in enumerate(zip(self.groups, rows)):
            for column, value in enumerate(row.values()):
                ui.summaryTable.setItem(i, column, QTableWidgetItem(display(value)))
            measured = [point for point in group if metric in point.metrics]
            offsets = np.linspace(-.1, .1, len(measured)) * spacing if len(measured) > 1 else np.zeros(len(measured))
            for point, offset in zip(measured, offsets):
                x.append(row["level"] + offset)
                y.append(point.metrics[metric])
                indices.append(point.row)
        ui.summaryTable.resizeColumnsToContents()
        if y:
            scatter = pg.ScatterPlotItem(
                x, y, data=indices, size=8, pen=None, brush=theme_manager.active_colour("neuron_vm"),
            )
            scatter.sigClicked.connect(self.select_point)
            ui.plot.addItem(scatter)
            means = np.array([np.nan if row["mean"] is None else row["mean"] for row in rows])
            theme_manager.themed_plot(ui.plot, levels, means, "neuron_current", width_scale=1.6,
                                      connect="finite")
            defined = [row for row in rows if row["sd"] is not None]
            if defined and metric != "probability":
                ui.plot.addItem(pg.ErrorBarItem(
                    x=np.array([row["level"] for row in defined]), y=np.array([row["mean"] for row in defined]),
                    height=2 * np.array([row["sd"] for row in defined]), beam=.08 * spacing,
                    pen=pg.mkPen(theme_manager.active_colour("neuron_current")),
                ))
            if metric == "probability":
                ui.plot.setYRange(-4, 104, padding=0)
        summary = f"{len(points)} sweeps · {len(self.groups)} input levels · {len(y)} defined measurements"
        if self.skipped:
            summary += f" · {self.skipped} sweeps lacked a stable input plateau or baseline"
        ui.summaryLabel.setText(summary + ". Select a point to inspect its sweep.")
        ui.exportButton.setEnabled(bool(self.groups))
        theme_manager.style_traces()

    def draw_averages(self):
        ui = self.form
        input_plot, response_plot = ui.averageInputPlot, ui.plot
        legend = response_plot.plotItem.legend or response_plot.addLegend()
        legend.clear()
        for plot in (input_plot, response_plot):
            plot.clear()
            plot.enableAutoRange(axis="x", enable=False)
            plot.enableAutoRange(axis="y")
            plot.getAxis("left").setWidth(70)
        input_plot.getAxis("bottom").setStyle(showValues=False)
        response_plot.setLabel("bottom", "Time from step onset (ms)")
        key = ui.inputCombo.currentData()
        input_signal = self.recording.extra_channels[key] if key else self.recording.stimulus
        input_plot.setLabel("left", ui.inputCombo.currentText() if key else STIMULUS_COLUMN)
        _, response, response_label, _, _ = self.sweeps.response()
        response_plot.setLabel("left", response_label)
        ui.exportButton.setEnabled(False)
        ui.averageImageButton.setEnabled(False)
        self.average_rows = []
        index = ui.protocolCombo.currentIndex()
        if not 0 <= index < len(self.protocols):
            ui.summaryLabel.setText(self.tolerance_error or "No included sweeps have a usable input level.")
            return

        points = self.protocols[index]
        if self.silent_check.isChecked():
            points = [point for point in points if point.metrics.get("count") == 0]
        groups = level_groups(points, self.tolerance)
        if not groups:
            ui.summaryLabel.setText("No sweeps match the selected filters.")
            return
        pre = self.sweeps.settings["Requested baseline (ms)"]
        post = self.sweeps.settings["Requested recovery (ms)"]
        end = max(point.duration_ms for point in points) + post
        sample_ms = self.recording.nominal_step_ms
        time_ms = np.arange(-int(np.floor(pre / sample_ms)), int(np.ceil(end / sample_ms))) * sample_ms
        unit = STEP_INPUT_UNITS[STEP_INPUT_KEYS.index(key or "")]
        for i, group in enumerate(groups):
            level = float(np.mean([point.input_level for point in group]))
            means, counts = average_step_traces(self.recording, group, time_ms, (input_signal, response))
            colour = pg.intColor(i, hues=max(len(groups), 6))
            name = f"{level:g} {unit} · {len(group)} sweeps"
            for plot, mean in zip((input_plot, response_plot), means):
                plot.plot(time_ms, mean, pen=pg.mkPen(colour, width=2),
                          name=name if plot is response_plot else None, connect="finite")
            self.average_rows.append((level, len(group), time_ms, means, counts))
        for plot in (input_plot, response_plot):
            plot.addItem(pg.InfiniteLine(pos=0, pen=pg.mkPen(theme_manager.active_colour("text_muted"))),
                         ignoreBounds=True)
        page.sync_plot_x_range((input_plot, response_plot), None, (-pre, end))
        ui.summaryLabel.setText(f"{len(points)} included sweeps · {len(groups)} input levels · "
                                "One mean trace per level. Time zero marks step onset.")
        ui.exportButton.setEnabled(True)
        ui.averageImageButton.setEnabled(True)

    def export_average_image(self):
        folder = page.choose_export_folder("Graphs", "Export average step plots")
        if folder is None:
            return
        try:
            for plot, label in ((self.form.averageInputPlot, "input"), (self.form.plot, "response")):
                ImageExporter(plot.plotItem).export(str(folder / f"{self.recording.source.stem}_step_average_{label}.png"))
        except (OSError, RuntimeError, ValueError) as error:
            page.show_error(self.sweeps.window.ui, "Cannot export average step plots", error)

    def select_point(self, item, points, event):
        if len(points):
            self.selected = int(points[0].data())
            self.form.inspectButton.setEnabled(True)
            self.form.inspectButton.setText(f"Inspect sweep {self.sweeps.sweeps[self.selected].step.number}")

    def inspect(self):
        if self.selected is not None:
            self.sweeps.form.sweepTable.setCurrentCell(self.selected, 1)
            ui = self.sweeps.window.ui
            ui.DataAnalysis_sweepStack.setCurrentWidget(ui.DataAnalysis_stepPage)
            self.sweeps.draw_aligned(measurement=self.form.metricCombo.currentData())

    def export(self):
        if self.averages:
            self.export_averages()
            return
        if not self.groups:
            return
        folder = page.choose_export_folder("Data", "Export step summary")
        if folder is None:
            return
        ui = self.form
        metric = ui.metricCombo.currentData()
        prefix = folder / f"{self.recording.source.stem}_{NEURON_NAMES[self.neuron]}_{metric}"
        metadata = {
            **self.recording.metadata(), **self.sweeps.settings,
            "Neuron": NEURON_NAMES[self.neuron], "Response signal": self.signal_label,
            "Condition": self.sweeps.form.conditionEdit.text().strip(),
            "Input axis": ui.inputCombo.currentText(), "Input tolerance": self.tolerance,
            "Protocol": ui.protocolCombo.currentText(), "Measurement": ui.metricCombo.currentText(),
            "Spike threshold (mV)": self.spikes.threshold_mv if self.spikes is not None else None,
            "Silent sweeps only": self.silent_check.isChecked(),
        }
        results, sweeps = [], []
        for group in self.groups:
            result = statistics(group, metric)
            results.append({**metadata, **result})
            for point in group:
                step = point.sweep.step
                sweeps.append({
                    **metadata, "Input group level": result["level"], "Sweep": step.number,
                    "Onset (ms)": step.onset_ms, "Duration (ms)": point.duration_ms,
                    "Input level": point.input_level, "Holding level": point.holding,
                    "Value": point.metrics.get(metric),
                })
        try:
            for suffix, rows in (("step_summary", results), ("step_points", sweeps)):
                with prefix.with_name(f"{prefix.name}_{suffix}.csv").open("w", encoding="utf-8", newline="") as file:
                    writer = csv.DictWriter(file, fieldnames=list(rows[0]))
                    writer.writeheader()
                    writer.writerows(rows)
        except OSError as error:
            page.show_error(self.sweeps.window.ui, "Cannot export step summary", error)


    def export_averages(self):
        if not self.average_rows:
            return
        folder = page.choose_export_folder("Data", "Export average step traces")
        if folder is None:
            return
        destination = folder / f"{self.recording.source.stem}_step_averages.csv"
        try:
            with destination.open("w", encoding="utf-8", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["Input axis", "Input level", "Protocol", "Neuron", "Sweeps",
                                 "Time from step onset (ms)", "Mean input", self.signal_label,
                                 "Input sweeps contributing", "Response sweeps contributing"])
                for level, sweeps, time, means, counts in self.average_rows:
                    context = (self.form.inputCombo.currentText(), level, self.form.protocolCombo.currentText(),
                               NEURON_NAMES[self.neuron], sweeps)
                    writer.writerows((*context, t, a if na else "", b if nb else "", na, nb)
                                     for t, a, b, na, nb in zip(time, *means, *counts))
        except OSError as error:
            page.show_error(self.sweeps.window.ui, "Cannot export average step traces", error)
