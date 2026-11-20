"""Qt controls for bounded, reproducible extracellular analysis."""
from concurrent.futures import Future
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from threading import Event, Thread

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import QCoreApplication, QObject, QSignalBlocker, Qt, QTimer
from PySide6.QtWidgets import QFileDialog, QHeaderView, QTableWidgetItem

from spikeling_gui.appearance.theme_manager import EXTRACELLULAR_CHANNEL_KEYS, theme_manager
from spikeling_gui.paths import recordings_directory

from .acquisition import CONTACTS
from .analysis_comparison import validate_tolerance
from .analysis_measurements import measure, spectrum
from .offline_analysis import Recipe, analyse, compare, compare_source, export_analysis
from .offline_detection import Detector
from .offline_processing import MAX_ANALYSIS_ROWS, Processing
from .session_reader import SessionReader
from .waveform_analysis import WaveformSettings

MAX_EVENT_MARKERS = 5_000


class AnalysisPage(QObject):
    def __init__(self, page):
        super().__init__(page)
        self.page, self.ui = page, page.ui
        self.reader = None
        self.reference = self.current = None
        self.comparison = self.source = None
        self.tolerance = None
        self.dirty = True
        self.generation = 0
        self.job = self.pending = None
        self.plots = None
        self.spectrum_plot = None
        self.ui.measurementTable.setRowCount(len(CONTACTS))
        self.ui.measurementTable.verticalHeader().hide()
        self.ui.measurementTable.verticalHeader().setDefaultSectionSize(20)
        self.ui.measurementTable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.ui.measurementTable.setAlternatingRowColors(True)
        self.timer = QTimer(self, interval=40)
        self.timer.timeout.connect(self._poll)
        self.ui.pageStack.currentChanged.connect(self._activate)
        for button in (self.ui.runButton, self.ui.rerunButton):
            button.clicked.connect(self.run)
        self.ui.pinButton.clicked.connect(self.pin)
        self.ui.matchButton.clicked.connect(self.refresh_agreement)
        self.ui.analysisExportButton.clicked.connect(self.export)
        self.ui.indexEdit.textChanged.connect(self._selection_changed)
        self.ui.countEdit.textChanged.connect(self._selection_changed)
        self.ui.sourceCombo.activated.connect(self._source_changed)
        self.ui.toleranceEdit.textChanged.connect(self._match_edited)
        for combo in (self.ui.referenceCombo, self.ui.singleReferenceCombo, self.ui.notchCombo):
            combo.currentIndexChanged.connect(self._recipe_edited)
        self.ui.polarityCombo.currentIndexChanged.connect(self._polarity_changed)
        self.ui.spectrumContact.currentIndexChanged.connect(self._draw_spectrum)
        for edit in (self.ui.baselineStartEdit, self.ui.baselineCountEdit):
            edit.textChanged.connect(self._show_measurements)
        for control in (self.ui.bandpassCheck, *self._checks("reference"), *self._checks("detector")):
            control.toggled.connect(self._recipe_edited)
        for control in (self.ui.lowEdit, self.ui.highEdit, self.ui.thresholdEdit, self.ui.refractoryEdit,
                        self.ui.groupingEdit, self.ui.preEdit, self.ui.postEdit, self.ui.snippetEdit,
                        self.ui.firstGroupEdit, self.ui.groupCountEdit):
            control.textChanged.connect(self._recipe_edited)
        self.set_reader(None)

    def _checks(self, prefix):
        return tuple(getattr(self.ui, f"{prefix}{channel}") for channel in range(1, 5))

    def _contacts(self, prefix):
        return tuple(contact for contact, box in zip(CONTACTS, self._checks(prefix)) if box.isChecked())

    def _recipe(self):
        ui = self.ui
        band = (float(ui.lowEdit.text()), float(ui.highEdit.text())) if ui.bandpassCheck.isChecked() else None
        count = ui.groupCountEdit.text().strip()
        reference = ("none", "car", "single")[ui.referenceCombo.currentIndex()]
        contacts = ((CONTACTS[ui.singleReferenceCombo.currentIndex()],)
                    if reference == "single" else self._contacts("reference"))
        return Recipe(
            Processing(reference, contacts, band, (None, 50, 60)[ui.notchCombo.currentIndex()]),
            Detector(float(ui.thresholdEdit.text()), float(ui.refractoryEdit.text()),
                     float(ui.groupingEdit.text()), self._contacts("detector"), self._polarity()),
            WaveformSettings(float(ui.preEdit.text()), float(ui.postEdit.text()),
                             int(ui.snippetEdit.text()), int(ui.firstGroupEdit.text()),
                             int(count) if count else None),
        )

    def _polarity(self):
        return ("negative", "positive", "both")[self.ui.polarityCombo.currentIndex()]

    def _polarity_changed(self, _index):
        edit = self.ui.thresholdEdit
        try:
            value = float(edit.text())
        except ValueError:
            pass
        else:
            sign = -1 if self._polarity() == "negative" else 1
            with QSignalBlocker(edit):
                edit.setText(f"{sign * abs(value):g}")
        self._recipe_edited()

    def set_reader(self, reader):
        self.reader = reader
        self._source_options("")
        self._selection_changed()

    def _source_options(self, selected):
        combo = self.ui.sourceCombo
        combo.clear()
        combo.addItem(self.tr("Hide source events"), "")
        if self._eligible():
            combo.addItem(self.tr("Inferred Vm launches (proxy)"), "waveform_launch")
            if self.reader.manifest["native_truth"]:
                combo.addItem(self.tr("Reveal native emulator events"), "native_model_spike")
        combo.setCurrentIndex(max(0, combo.findData(selected)))

    def retranslate(self):
        self._source_options(self.ui.sourceCombo.currentData())
        if self.plots is not None:
            self.plots.translate()
        self._enable()
        if self.current is not None and not self.dirty:
            self._describe()
        self._draw()

    def _eligible(self):
        return isinstance(self.reader, SessionReader) and self.reader.sample_count > 0

    def _interval(self):
        if not self._eligible():
            return None
        try:
            start = int(self.ui.indexEdit.text())
            count = int(self.ui.countEdit.text())
        except ValueError:
            return None
        if not self.reader.first_index <= start < self.reader.end_index or not 1 <= count <= MAX_ANALYSIS_ROWS:
            return None
        return start, min(start + count, self.reader.end_index)

    def _enable(self):
        ready = self._interval() is not None
        result = self.current is not None and not self.dirty and self.job is None
        for button in (self.ui.runButton, self.ui.rerunButton):
            button.setEnabled(ready)
        self.ui.pinButton.setEnabled(ready and result)
        self.ui.matchButton.setEnabled(ready and result)
        self.ui.analysisExportButton.setEnabled(ready and result and self.tolerance is not None)
        have_source = self._eligible()
        self.ui.sourceCombo.setEnabled(have_source)
        band = self.ui.bandpassCheck.isChecked()
        self.ui.lowEdit.setEnabled(band)
        self.ui.highEdit.setEnabled(band)
        reference_index = self.ui.referenceCombo.currentIndex()
        self.ui.singleReferenceCombo.setVisible(reference_index == 2)
        self.ui.refContactsLabel.setVisible(reference_index == 1)
        for box in self._checks("reference"):
            box.setEnabled(reference_index == 1)
            box.setVisible(reference_index == 1)
        self.ui.thresholdEditLabel.setText({
            "negative": self.tr("Negative threshold (µV)"),
            "positive": self.tr("Positive threshold (µV)"),
            "both": self.tr("Threshold magnitude (µV)"),
        }[self._polarity()])
        if ready:
            start, stop = self._interval()
            status = self.tr("Accepted rows %1–%2 · %3 model Hz · set the interval in Recording")
            status = status.replace("%1", str(start)).replace("%2", str(stop - 1)).replace(
                "%3", str(self.reader.manifest["nominal_model_rate_hz"]))
            status += " · " + self.reader.directory.name
            if self.reader.recovered:
                status += " · " + self.tr("Recovered prefix")
            if self.reader.manifest["acquisition"]["source"] == "spikeling":
                status += " · " + self.tr("Nominal model time; upstream continuity unknown")
        elif self.reader is None:
            status = self.tr("Open a recording in Recording to begin.")
        elif not self._eligible():
            status = self.tr("Offline processing needs a non-empty versioned broadband session. Inspect this file in Recording.")
        else:
            status = self.tr("Select an accepted interval of 1–40,000 rows in Recording.")
        self.ui.analysisSelection.setText(status)

    def _selection_changed(self):
        self._invalidate()
        self.current = self.reference = self.comparison = self.source = None
        self.tolerance = None
        self.dirty = True
        self.ui.analysisStatus.clear()
        self.ui.comparisonStatus.clear()
        self.ui.comparisonDetails.clear()
        self._show_measurements()
        self._enable()
        self._draw()

    def _recipe_edited(self):
        self._invalidate()
        self.dirty = True
        self.tolerance = None
        if self.current is not None:
            self.ui.analysisStatus.setText(self.tr("Settings edited. Run B to apply them; plots show the last completed run."))
        self._enable()

    def _match_edited(self):
        self._invalidate()
        self.comparison = self.source = self.tolerance = None
        self._enable()
        self._draw()
        if self.current is not None:
            self._describe()

    def _source_changed(self):
        self._match_edited()
        if not self.dirty:
            self.refresh_agreement()

    def _invalidate(self):
        self.generation += 1
        self.pending = None
        if self.job is not None:
            self.job[2].set()

    def _queue(self, work, deliver):
        self._invalidate()
        self.pending = self.generation, work, deliver
        if self.job is None:
            self._start()

    def _start(self):
        generation, work, deliver = self.pending
        self.pending = None
        future, cancel = Future(), Event()
        self.job = generation, future, cancel, deliver
        self.timer.start()
        self._enable()

        def worker():
            try:
                future.set_result(work(cancel))
            except Exception as error:
                future.set_exception(error)
        Thread(target=worker, daemon=True, name="Extracellular offline analysis").start()

    def _poll(self):
        if self.job is None:
            return
        generation, future, _, deliver = self.job
        if not future.done():
            return
        self.timer.stop()
        self.job = None
        if generation == self.generation:
            try:
                deliver(future.result())
            except Exception as error:
                message = self.tr("Analysis error") + " · " + str(error)
                self.ui.analysisStatus.setText(message)
                self.ui.comparisonStatus.setText(message)
        if self.pending is not None:
            self._start()
        else:
            self._enable()

    def _comparison_settings(self):
        tolerance = float(self.ui.toleranceEdit.text())
        validate_tolerance(tolerance)
        return tolerance, self.ui.sourceCombo.currentData()

    def run(self):
        interval = self._interval()
        if interval is None:
            return
        try:
            recipe = self._recipe()
            tolerance, stream = self._comparison_settings()
        except ValueError as error:
            self.ui.analysisStatus.setText(str(error))
            self.ui.comparisonStatus.setText(str(error))
            return
        reader, reference = self.reader, self.reference
        self.dirty = True
        self.ui.analysisStatus.setText(self.tr("Processing the selected broadband interval…"))
        self.ui.comparisonStatus.setText(self.ui.analysisStatus.text())

        def work(cancel):
            result = analyse(reader, *interval, recipe, cancel)
            if result is not None and not cancel.is_set():
                return self._combine(reader, reference, result, tolerance, stream, cancel)
            return None
        self._queue(work, self._applied)

    @staticmethod
    def _combine(reader, reference, result, tolerance, stream, cancel):
        agreement = None if reference is None else compare(reference, result, tolerance, cancel)
        source = None if not stream or cancel.is_set() else compare_source(reader, result, stream, tolerance, cancel)
        return result, agreement, source, tolerance

    def _applied(self, result):
        if result is None:
            return
        self.current, self.comparison, self.source, self.tolerance = result
        self.dirty = False
        self._describe()
        self._draw()

    def pin(self):
        if self.current is None or self.dirty:
            return
        self.reference = self.current
        self.refresh_agreement()

    def refresh_agreement(self):
        if self.current is None or self.dirty:
            return
        try:
            tolerance, stream = self._comparison_settings()
        except ValueError as error:
            self.ui.comparisonStatus.setText(str(error))
            return
        reader, reference, current = self.reader, self.reference, self.current
        self.ui.comparisonStatus.setText(self.tr("Matching events…"))
        self._queue(lambda cancel: self._combine(reader, reference, current, tolerance, stream, cancel),
                    self._applied)

    def export(self):
        if self.current is None or self.dirty or self.tolerance is None or self.job is not None:
            return
        filename, _ = QFileDialog.getSaveFileName(
            self.page, self.tr("Export extracellular analysis"), str(recordings_directory()),
            self.tr("Analysis recipe (*.json)"),
        )
        if filename:
            path = Path(filename)
            if path.suffix.lower() != ".json":
                path = path.with_suffix(".json")
            arguments = (path, self.reader.directory, self.current, self.reference,
                         self.tolerance, self.comparison, self.source)
            measurements, _ = self._measurement_data()
            self._queue(lambda _: export_analysis(*arguments, measurements=measurements),
                        lambda _: self.ui.comparisonStatus.setText(self.tr("Analysis exported")))

    def _describe(self):
        current = self.current
        if current is None:
            return
        wave = current.waveforms
        status = self.tr("B: %1 grouped detections · %2 filter warm-up rows · A dashed, B solid")
        status = status.replace("%1", str(len(current.groups))).replace("%2", str(current.warmup_rows))
        if any(len(events) > MAX_EVENT_MARKERS for events in (
                current.groups, self.reference.groups if self.reference else (),
                self.source.events if self.source else ())):
            status += " · " + self.tr("Event markers show a display subset; counts include all groups")
        self.ui.analysisStatus.setText(status)
        message = self.tr("%1 valid waveforms from %2 selected groups · %3 excluded · %4 overlays")
        for index, value in enumerate((len(wave.event_ids), wave.selected_count, len(wave.excluded),
                                       len(wave.snippets)), 1):
            message = message.replace(f"%{index}", str(value))
        self.ui.comparisonStatus.setText(message + " · " + self.tr("A mean dashed, B mean and overlays solid"))
        crossings = sum(len(group.crossings) for group in current.groups)
        lines = [self.tr("B contains %1 contact crossings, grouped into %2 candidate events.")
                 .replace("%1", str(crossings)).replace("%2", str(len(current.groups)))]
        if not current.groups:
            lines.append(self.tr("No detections at this threshold. Inspect signal amplitude and reference settings before interpreting neuronal activity."))
        if current.recipe.processing.reference == "car":
            values = np.concatenate([run.values_uV for run in current.runs])
            if not np.any(values):
                lines.append(self.tr("The analysed CAR signal is exactly zero: identical contact voltages can cancel completely. Inspect saved broadband in Recording."))
        for reason, count in Counter(reason for _, reason in wave.excluded).items():
            explanation = (self.tr("window crosses the selected interval, segment or settings boundary")
                           if reason == "interval_segment_or_epoch_boundary" else self.tr("window overlaps filter warm-up"))
            lines.append(self.tr("Excluded waveforms: %1 — %2").replace("%1", str(count)).replace("%2", explanation))
        if self.reference is not None:
            a_groups, b_groups = len(self.reference.groups), len(current.groups)
            lines.append(self.tr("Grouped detections: A %1 · B %2").replace("%1", str(a_groups)).replace(
                "%2", str(b_groups)))
        if self.reference is not None and self.comparison is not None:
            result, excluded_a, excluded_b = self.comparison
            lines.append(self.tr("A/B agreement: %1 matched · %2 A only · %3 B only · %4 outside common exposure"
                                 ).replace("%1", str(len(result.pairs))).replace("%2", str(len(result.left_only)))
                         .replace("%3", str(len(result.right_only))).replace("%4", f"A {excluded_a}, B {excluded_b}"))
        if self.source is not None:
            if not self.source.available:
                lines.append(self.tr("Source evidence unavailable in the eligible interval."))
            else:
                if not self.source.events:
                    lines.append(self.tr("Source evidence covers the eligible interval; no source events were recorded there."))
                label = (self.tr("Native emulator events") if self.source.stream == "native_model_spike"
                         else self.tr("Inferred Vm launches"))
                result = self.source.agreement
                lines.append(label + " · " + self.tr(
                    "%1 matched · %2 source only · %3 B only · %4 ambiguous detections · %5 eligible rows · %6 detections excluded"
                ).replace("%1", str(len(result.pairs))).replace("%2", str(len(result.left_only)))
                    .replace("%3", str(len(result.right_only))).replace("%4", str(len(result.ambiguous_right)))
                    .replace("%5", str(self.source.eligible_rows)).replace("%6", str(self.source.excluded_detections)))
        if self.reference is not None:
            before, after = asdict(self.reference.recipe), asdict(current.recipe)
            labels = {"reference": self.tr("reference method"), "reference_contacts": self.tr("reference contacts"),
                      "bandpass": self.tr("bandpass"), "notch_hz": self.tr("mains notch"),
                      "polarity": self.tr("detection polarity"), "threshold_uV": self.tr("threshold"),
                      "refractory_ms": self.tr("refractory time"), "grouping_ms": self.tr("grouping window"),
                      "contacts": self.tr("detection contacts"), "pre_ms": self.tr("pre-event window"),
                      "post_ms": self.tr("post-event window"), "max_snippets": self.tr("overlay count"),
                      "first_group": self.tr("first waveform group"), "group_count": self.tr("waveform group count")}
            differences = [labels.get(key, key) for section, settings in before.items()
                           for key, value in settings.items() if value != after[section][key]]
            lines.append(self.tr("Changed settings") + ": " + (", ".join(differences) if differences else self.tr("None — A and B use identical settings")))
            lines.append(self._recipe_summary("A", self.reference.recipe))
        else:
            lines.append(self.tr("To compare: save completed B as baseline A, change one setting, then run B again."))
        lines.append(self._recipe_summary("B", current.recipe))
        self.ui.comparisonDetails.setPlainText("\n".join(lines))
        self._show_measurements()

    def _recipe_summary(self, name, recipe):
        processing, detector, waveform = recipe.processing, recipe.detector, recipe.waveform
        reference = {
            "car": self.tr("Common average of %1"),
            "single": self.tr("Single contact %1"),
            "none": self.tr("No reference subtraction"),
        }[processing.reference].replace("%1", ", ".join(processing.reference_contacts))
        band = (self.tr("bandpass %1–%2 Hz").replace("%1", f"{processing.bandpass[0]:g}").replace("%2", f"{processing.bandpass[1]:g}")
                if processing.bandpass else self.tr("bandpass off"))
        notch = (self.tr("notch off") if processing.notch_hz is None else
                 self.tr("%1 Hz notch").replace("%1", str(processing.notch_hz)))
        polarity = {"negative": self.tr("negative"), "positive": self.tr("positive"),
                    "both": self.tr("both polarities")}[detector.polarity]
        return (f"{name} · {reference} · {band} · {notch}\n"
                + self.tr("Threshold %1 µV (%5) · refractory %2 ms · grouping %3 ms · contacts %4")
                .replace("%5", polarity)
                .replace("%1", f"{detector.threshold_uV:g}").replace("%2", f"{detector.refractory_ms:g}")
                .replace("%3", f"{detector.grouping_ms:g}").replace("%4", ", ".join(detector.contacts))
                + "\n" + self.tr("Waveform window: %1 ms before / %2 ms after each group anchor.")
                .replace("%1", f"{waveform.pre_ms:g}").replace("%2", f"{waveform.post_ms:g}"))

    def _measurement_data(self):
        if self.current is None:
            return None, self.tr("Run B to measure the signal.")
        start = self.ui.baselineStartEdit.text().strip()
        count = self.ui.baselineCountEdit.text().strip()
        if not start and not count:
            return measure(self.reference, self.current), self.tr("Choose a quiet interval for RMS.")
        try:
            start, count = int(start), int(count)
            if count < 2 or not self.current.start <= start < start + count <= self.current.stop:
                raise ValueError
        except ValueError:
            return measure(self.reference, self.current), self.tr("Enter a start index and at least two samples within the analysed interval.")
        data = measure(self.reference, self.current, (start, start + count))
        status = (self.tr("Quiet interval uses %1 common settled samples.").replace("%1", str(count))
                  if data["baseline_available"] else
                  self.tr("Choose a quiet interval within one common settled block, clear of gaps and warm-up."))
        return data, status

    def _show_measurements(self):
        data, status = self._measurement_data()
        values = {}
        if data is not None:
            values = {name: data.get(name, {}) for name in ("a", "b")}
            counts = "   ".join(f"{name.upper()}: {row['waveform_count']}"
                                for name, row in values.items() if row)
            status += " " + self.tr("Waveforms in each mean") + " · " + counts
        self.ui.measurementStatus.setText(status)
        columns = (("a", "baseline_rms_uV"), ("b", "baseline_rms_uV"),
                   ("a", "mean_waveform_peak_to_peak_uV"), ("b", "mean_waveform_peak_to_peak_uV"))
        for index, contact in enumerate(CONTACTS):
            self.ui.measurementTable.setItem(index, 0, QTableWidgetItem(contact))
            for column, (recipe, key) in enumerate(columns, 1):
                numbers = values.get(recipe, {}).get(key)
                item = QTableWidgetItem("—" if numbers is None else f"{numbers[index]:.3g}")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.ui.measurementTable.setItem(index, column, item)

    def _draw_spectrum(self, *_):
        if self.ui.pageStack.currentWidget() is not self.ui.spectrumTab:
            return
        contact = self.ui.spectrumContact.currentIndex()
        if self.spectrum_plot is None:
            axis = pg.PlotWidget()
            axis.showGrid(x=True, y=True, alpha=.2)
            theme_manager.set_plot_background_role(axis, "panel_background")
            axis.setXRange(0, 200, padding=0)
            axis.getViewBox().setLimits(xMin=0, yMin=0)
            self.ui.spectrumPlotLayout.addWidget(axis)
            self.spectrum_plot = (
                axis, AnalysisPlots._curve(axis, "text_muted", dashed=True),
                AnalysisPlots._curve(axis, EXTRACELLULAR_CHANNEL_KEYS[0]),
            )
        axis, baseline, current = self.spectrum_plot
        axis.setLabel("bottom", self.tr("Frequency"), units="Hz")
        axis.setLabel("left", self.tr("Power spectral density"), units="µV²/Hz")
        result = None if self.current is None else spectrum(self.reference, self.current, contact)
        if result is None:
            baseline.setData([], [])
            current.setData([], [])
            self.ui.spectrumStatus.setText(self.tr("Run B with at least 0.5 s of contiguous settled samples."))
            return
        start, stop, frequency, power_a, power_b = result
        if power_a is None:
            baseline.setData([], [])
        else:
            baseline.setData(frequency, power_a)
        current.setData(frequency, power_b)
        current.setPen(theme_manager.pen(EXTRACELLULAR_CHANNEL_KEYS[contact]))
        theme_manager.tag_item(current, EXTRACELLULAR_CHANNEL_KEYS[contact])
        self.ui.spectrumStatus.setText(
            self.tr("Rows %1–%2 · %3 Hz resolution").replace("%1", str(start))
            .replace("%2", str(stop - 1)).replace("%3", f"{frequency[1]:.3g}")
        )

    def _activate(self, _):
        if self.ui.pageStack.currentWidget() in (self.ui.processingTab, self.ui.detectionTab, self.ui.comparisonTab):
            if self.plots is None:
                self.plots = AnalysisPlots(self.ui)
            if self.ui.pageStack.currentWidget() in (self.ui.processingTab, self.ui.detectionTab):
                layout = (self.ui.detectionTabLayout if self.ui.pageStack.currentWidget() is self.ui.detectionTab
                          else self.ui.processingTabLayout)
                layout.addWidget(self.ui.analysisPlotHost, 1)
        self._draw()

    def _draw(self):
        self._draw_spectrum()
        if self.plots is not None:
            current_tab = self.ui.pageStack.currentWidget()
            self.plots.draw(self.reference, self.current, self.source, self.comparison,
                            traces=current_tab in (self.ui.processingTab, self.ui.detectionTab),
                            waveforms=current_tab is self.ui.comparisonTab)


def _peak_points(x, y, stride):
    """Keep each bin's extrema at their original coordinates and order."""
    if stride <= 1 or len(x) <= stride:
        return x, y
    complete = len(y) // stride * stride
    blocks = y[:complete].reshape(-1, stride)
    positions = np.arange(len(blocks)) * stride
    extrema = np.sort(np.column_stack((positions + blocks.argmin(axis=1),
                                       positions + blocks.argmax(axis=1))), axis=1).ravel()
    indices = np.r_[0, extrema, np.arange(complete, len(x)), len(x) - 1]
    return x[indices], y[indices]


def _segments(result, contact):
    if result is None:
        return np.empty(0), np.empty(0)
    stride = max(1, (result.stop - result.start + 749) // 750)
    times, voltages = [], []
    for run in result.runs:
        if times:
            times.append(np.array([np.nan]))
            voltages.append(np.array([np.nan]))
        rows = np.arange(run.first, run.end, dtype=np.int64) - result.start
        x, y = _peak_points(rows, run.values_uV[:, contact], stride)
        times.append(x)
        voltages.append(y)
    return np.concatenate(times), np.concatenate(voltages)


class AnalysisPlots:
    """Presentation only. Gap separators and overlay caps never affect results."""
    def __init__(self, ui):
        self.trace_canvas = pg.GraphicsLayoutWidget()
        self.wave_canvas = pg.GraphicsLayoutWidget()
        ui.analysisPlotLayout.addWidget(self.trace_canvas)
        ui.waveformPlotLayout.addWidget(self.wave_canvas)
        self.traces, self.waves, self.snippets = [], [], []
        for canvas, collection in ((self.trace_canvas, self.traces), (self.wave_canvas, self.waves)):
            theme_manager.set_plot_background_role(canvas, "panel_background")
            for row, (contact, role) in enumerate(zip(CONTACTS, EXTRACELLULAR_CHANNEL_KEYS)):
                axis = canvas.addPlot(row=row, col=0)
                axis.setLabel("left", contact, units="µV")
                axis.getAxis("left").setWidth(65)
                if collection:
                    axis.setXLink(collection[0][0])
                if canvas is self.trace_canvas or row < 3:
                    axis.showAxis("bottom", False)
                if canvas is self.wave_canvas:
                    overlay = self._curve(axis, role, width=.55)
                    overlay.setZValue(-1)
                    self.snippets.append(overlay)
                collection.append((axis, self._curve(axis, role, dashed=True),
                                   self._curve(axis, role, width=1.25)))
        self.raster = self.trace_canvas.addPlot(row=4, col=0)
        self.raster.getAxis("left").setWidth(65)
        self.raster.setMaximumHeight(100)
        self.raster.setXLink(self.traces[0][0])
        self.raster.setYRange(-.5, 2.5, padding=0)
        self.marks = [theme_manager.themed_plot(self.raster, [], [], role, symbol=symbol, symbol_size=7)
                      for role, symbol in zip(EXTRACELLULAR_CHANNEL_KEYS[:3], ("s", "o", "t"))]
        self.unmatched = theme_manager.themed_plot(self.raster, [], [], "text_primary",
                                                  symbol="x", symbol_size=10)
        self.translate()

    def translate(self):
        self.raster.setLabel("bottom", QCoreApplication.translate(
            "AnalysisPage", "Accepted rows from interval start · × unmatched"))
        source_label = QCoreApplication.translate("AnalysisPage", "Source")
        self.raster.getAxis("left").setTicks([[(0, source_label), (1, "B"), (2, "A")]])
        self.waves[-1][0].setLabel("bottom", QCoreApplication.translate(
            "AnalysisPage", "Time from group anchor"), units="ms")

    @staticmethod
    def _curve(axis, role, *, dashed=False, width=1.0):
        style = Qt.PenStyle.DashLine if dashed else Qt.PenStyle.SolidLine
        curve = axis.plot(pen=theme_manager.pen(role, width, style), connect="finite")
        return theme_manager.tag_item(curve, role, width, style=style)

    @staticmethod
    def _range(collection, values):
        limits = [(float(value.min()), float(value.max()))
                  for value in values if value is not None and value.size]
        if limits:
            low = min(value[0] for value in limits)
            high = max(value[1] for value in limits)
            if high == low:
                low, high = low - 1, high + 1
            for axis, *_ in collection:
                axis.setYRange(low, high)

    @staticmethod
    def _marker_subset(events):
        return events[::max(1, (len(events) + MAX_EVENT_MARKERS - 1) // MAX_EVENT_MARKERS)]

    def draw(self, reference, current, source, comparison, *, traces=True, waveforms=True):
        if traces:
            self._draw_traces(reference, current, source, comparison)
        if waveforms:
            self._draw_waveforms(reference.waveforms if reference else None,
                                 current.waveforms if current else None)

    def _draw_traces(self, reference, current, source, comparison):
        for index, (_, a, b) in enumerate(self.traces):
            a.setData(*_segments(reference, index))
            b.setData(*_segments(current, index))
        self._range(self.traces, (run.values_uV for result in (reference, current)
                                  if result is not None for run in result.runs))
        if current is not None:
            self.traces[0][0].setXRange(0, max(1, current.stop - current.start - 1))
        offset = current.start if current is not None else 0
        for row, mark, events in zip((2, 1, 0), self.marks,
                                    (reference.groups if reference else (), current.groups if current else (),
                                     source.events if source else ())):
            subset = self._marker_subset(events)
            mark.setData([event.sample - offset for event in subset], [row] * len(subset))
        unmatched_x, unmatched_y = [], []
        agreement = comparison[0] if comparison else None
        for row, events in ((2, agreement.left_only if agreement else ()),
                            (1, agreement.right_only if agreement else ()),
                            (0, source.agreement.left_only if source and source.agreement else ())):
            subset = self._marker_subset(events)
            unmatched_x.extend(event.sample - offset for event in subset)
            unmatched_y.extend([row] * len(subset))
        self.unmatched.setData(unmatched_x, unmatched_y)

    def _draw_waveforms(self, reference, current):
        for index, (_, a, b) in enumerate(self.waves):
            overlay = self.snippets[index]
            if current is not None and current.snippets:
                stride = max(1, (len(current.times_ms) + 199) // 200)
                xs, ys = [], []
                for values in current.snippets:
                    x, y = _peak_points(current.times_ms, values[:, index], stride)
                    xs.extend((x, np.array([np.nan])))
                    ys.extend((y, np.array([np.nan])))
                overlay.setData(np.concatenate(xs), np.concatenate(ys))
            else:
                overlay.setData([], [])
            for curve, wave in ((a, reference), (b, current)):
                if wave is None or wave.mean_uV is None:
                    curve.setData([], [])
                else:
                    stride = max(1, (len(wave.times_ms) + 1499) // 1500)
                    curve.setData(*_peak_points(wave.times_ms, wave.mean_uV[:, index], stride))
        waves = [wave for wave in (reference, current) if wave is not None]
        values = [wave.mean_uV for wave in waves]
        if waves:
            self.waves[0][0].setXRange(min(wave.times_ms[0] for wave in waves),
                                     max(wave.times_ms[-1] for wave in waves))
        if current is not None:
            values.extend(current.snippets)
        self._range(self.waves, values)
