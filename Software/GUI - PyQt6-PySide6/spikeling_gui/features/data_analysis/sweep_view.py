"""Qt view for reviewing individual stimulus steps."""

from dataclasses import replace
import math

import numpy as np
import pandas as pd
import pyqtgraph as pg
from PySide6.QtCore import QObject, QSignalBlocker, Qt
from PySide6.QtWidgets import QTableWidgetItem

from spikeling_gui.appearance.theme_manager import theme_manager

from . import page
from .recording import NEURON_NAMES, VOLTAGE_COLUMNS, custom_step_cycles, trigger_onsets
from .sweep_analysis import (
    Step, command_windows, detect_steps, manual_steps, matching_sweeps, measure_sweep, review_windows, sample_bounds,
    scheduled_steps, with_preceding_intervals,
)


STEP_INPUT_KEYS = ("", "command_current", "command_voltage")
STEP_INPUT_UNITS = ("%", "a.u.", "mV")


def number(editor, label, minimum=None, optional=False):
    text = editor.text().strip()
    if optional and not text:
        return None
    try:
        value = float(text)
    except ValueError:
        value = math.nan
    if not math.isfinite(value) or (minimum is not None and value < minimum):
        raise ValueError(f"Enter a valid value for {label}.")
    return value


def display(value):
    return "—" if value is None else f"{value:.6g}"


class SweepView(QObject):
    def __init__(self, window):
        super().__init__(window.ui.DataAnalysis_stepPage)
        self.widget = window.ui.DataAnalysis_stepPage
        self.window = window
        self.form = ui = page.bind_controls(window.ui, "Sweeps", (
            "inputCombo", "stimulusBaselineFieldLabel", "toleranceFieldLabel", "averageButton",
            "anchorEdit", "baselineEdit", "conditionEdit", "countEdit", "expectedEdit",
            "exportButton", "lateEdit", "methodCombo", "minimumEdit", "neuronCombo",
            "offEdit", "offsetEdit", "onEdit", "overviewPlot", "pauseEdit", "postEdit",
            "preEdit", "previewButton", "recordingLabel", "responsePlot", "signalCombo",
            "spikesButton", "stepSummaryButton", "stimulusPlot", "summaryLabel",
            "sweepSplitter", "sweepTable", "timingButton", "timingStack", "toleranceEdit",
        ))
        self.timing_button = ui.timingButton
        self.timing_button.clicked.connect(self.show_timing)
        self.summary_button = ui.stepSummaryButton
        self.summary_button.clicked.connect(self.show_step_summary)
        ui.averageButton.clicked.connect(lambda: self.show_step_summary(averages=True))
        ui.inputCombo.currentIndexChanged.connect(self.input_changed)
        self.recording = None
        self.sweeps = []
        self.excluded = set()
        self.settings = {}
        self.metrics = []
        self.highlight = None
        self.updating = False
        ui.sweepSplitter.setStretchFactor(0, 3)
        ui.sweepSplitter.setStretchFactor(1, 2)
        ui.sweepSplitter.setSizes([520, 360])
        for plot in (ui.overviewPlot, ui.stimulusPlot, ui.responsePlot):
            plot.getAxis("bottom").enableAutoSIPrefix(False)
            plot.showGrid(x=True, y=True, alpha=0.25)
            theme_manager.set_plot_background_role(plot, "panel_background")
        self.aligned_plots = (ui.stimulusPlot, ui.responsePlot)
        for plot in self.aligned_plots:
            plot.setDownsampling(auto=True, mode="peak")
            view = plot.getViewBox()
            view.enableAutoRange(axis="x", enable=False)
            view.sigXRangeChanged.connect(
                lambda source, limits: page.sync_plot_x_range(self.aligned_plots, source, limits)
            )
        ui.previewButton.clicked.connect(self.preview)
        ui.exportButton.clicked.connect(self.export)
        ui.spikesButton.clicked.connect(self.detect_spikes)
        ui.methodCombo.currentIndexChanged.connect(ui.timingStack.setCurrentIndex)
        ui.methodCombo.currentIndexChanged.connect(self.invalidate_preview)
        ui.neuronCombo.currentIndexChanged.connect(self.refresh)
        ui.signalCombo.currentIndexChanged.connect(self.refresh)
        ui.sweepTable.currentCellChanged.connect(self.selection_changed)
        ui.sweepTable.itemChanged.connect(self.include_changed)
        for edit in (
            ui.baselineEdit, ui.preEdit, ui.postEdit, ui.lateEdit, ui.toleranceEdit,
            ui.minimumEdit, ui.expectedEdit, ui.offsetEdit, ui.onEdit, ui.offEdit,
            ui.countEdit, ui.anchorEdit, ui.pauseEdit,
        ):
            edit.textEdited.connect(self.invalidate_preview)

    def load(self, recording):
        if recording is self.recording:
            self.refresh()
            return
        self.recording = recording
        combo = self.form.inputCombo
        voltage_index = STEP_INPUT_KEYS.index("command_voltage")
        with QSignalBlocker(combo):
            for index, key in enumerate(STEP_INPUT_KEYS[1:], 1):
                values = recording.extra_channels.get(key)
                combo.model().item(index).setEnabled(values is not None and bool(np.isfinite(values).any()))
            has_voltage = combo.model().item(voltage_index).isEnabled()
            combo.setCurrentIndex(voltage_index if recording.clamp_mode == "VC" and has_voltage else 0)
        with QSignalBlocker(self.form.signalCombo):
            self.form.signalCombo.setCurrentIndex(1 if recording.clamp_mode == "VC" else 0)
        self.input_changed()
        self.form.conditionEdit.clear()
        self.form.anchorEdit.setPlaceholderText(f"{recording.time_ms[0]:g}")
        has_triggers = bool(trigger_onsets(recording).size)
        self.form.anchorEdit.setEnabled(not has_triggers)
        self.form.pauseEdit.setEnabled(not has_triggers)
        self.preview()

    def input_changed(self, *_):
        index = self.form.inputCombo.currentIndex()
        previous_key = getattr(self, "input_key", "")
        self.input_key = STEP_INPUT_KEYS[index]
        self.input_unit = STEP_INPUT_UNITS[index]
        self.input_signal = self.recording.extra_channels.get(self.input_key, self.recording.stimulus)
        self.input_label = self.form.inputCombo.currentText()
        self.form.stimulusBaselineFieldLabel.setText(f"Input baseline ({self.input_unit})")
        self.form.toleranceFieldLabel.setText(f"Minimum change ({self.input_unit})")
        if self.input_key or previous_key != self.input_key:
            finite = np.flatnonzero(np.isfinite(self.input_signal))
            baseline = self.input_signal[finite[0]] if self.input_key and finite.size else 0
            self.form.baselineEdit.setText(f"{baseline:g}")
        self.excluded.clear()
        self.invalidate_preview()

    def invalidate_preview(self):
        self.sweeps = []
        self.metrics = []
        self.highlight = None
        self.form.sweepTable.setRowCount(0)
        self.form.exportButton.setEnabled(False)
        self.timing_button.setEnabled(False)
        self.summary_button.setEnabled(False)
        self.form.averageButton.setEnabled(False)
        self.form.summaryLabel.setText("Preview steps to apply these settings.")
        self.draw_overview()
        self.draw_aligned()

    def with_recorded_voltage(self, steps, pre_ms):
        sweeps = review_windows(self.recording, steps, pre_ms, 0)
        reviewed = []
        for sweep in sweeps:
            step = sweep.step
            samples = command_windows(self.recording, sweep, self.input_signal, settled=True)
            if samples is None:
                reviewed.append(replace(step, amplitude=None, issue=step.issue or "Missing command voltage"))
            else:
                before, active = samples
                reviewed.append(replace(step, amplitude=float(np.median(active) - np.median(before))))
        return reviewed

    def preview(self):
        if self.recording is None:
            return
        ui = self.form
        try:
            baseline = number(ui.baselineEdit, "input baseline")
            input_recording = replace(self.recording, stimulus=self.input_signal)
            pre = number(ui.preEdit, "baseline window", 0)
            post = number(ui.postEdit, "recovery window", 0)
            late = number(ui.lateEdit, "late window", 0.001)
            if ui.methodCombo.currentIndex() == 0:
                tolerance = number(ui.toleranceEdit, "edge tolerance", 0.001)
                minimum = number(ui.minimumEdit, "minimum on-time", 0.001)
                expected = number(ui.expectedEdit, "expected on-time", minimum, optional=True)
                steps = None
                protocol = None
                if self.input_key == "command_voltage":
                    steps = scheduled_steps(self.recording, 0, 0.5, minimum, expected, voltage=True)
                    if steps is not None:
                        steps = self.with_recorded_voltage(steps, pre)
                elif not self.input_key:
                    steps = scheduled_steps(self.recording, baseline, tolerance, minimum, expected)
                    if steps is None and baseline == 0:
                        protocol = custom_step_cycles(self.recording)
                if steps is not None:
                    alignment = "Recorded step schedule"
                elif protocol is None:
                    steps = detect_steps(input_recording, baseline, tolerance, minimum, expected)
                    alignment = "Detected step onset"
                else:
                    _, durations, matches = protocol
                    time = self.recording.time_ms
                    steps = []
                    for series, (_, starts, stops) in enumerate(matches, 1):
                        for position, (start, stop, duration) in enumerate(zip(starts, stops, durations), 1):
                            if duration < minimum or (expected is not None and
                                    abs(duration - expected) > self.recording.nominal_step_ms):
                                continue
                            amplitude = float(np.median(self.input_signal[start:stop]))
                            if abs(amplitude) > tolerance:
                                steps.append(Step(len(steps) + 1, time[start], time[stop], amplitude,
                                                  series, position, nominal_duration_ms=float(duration)))
                    steps = with_preceding_intervals(steps)
                    alignment = "Verified custom stimulus timing"
                self.settings = {
                    "Alignment": alignment, "Edge tolerance": tolerance,
                    "Minimum on-time (ms)": minimum, "Expected on-time (ms)": expected,
                }
            else:
                offset = number(ui.offsetEdit, "first step offset", 0)
                on = number(ui.onEdit, "on-time", 0.001)
                off = number(ui.offEdit, "off-time", 0)
                count = number(ui.countEdit, "steps per series", 1)
                if not count.is_integer() or count > len(self.recording.time_ms):
                    raise ValueError("Steps per series must be a whole number within the recording size.")
                anchor = None if not ui.anchorEdit.isEnabled() else number(ui.anchorEdit, "first anchor")
                pause = 0 if anchor is None else number(ui.pauseEdit, "series pause", 0)
                steps = manual_steps(input_recording, baseline, offset, on, off, int(count), anchor, pause)
                self.settings = {
                    "Alignment": "Manual timing", "First step offset (ms)": offset,
                    "On-time (ms)": on, "Off-time (ms)": off, "Steps per series": int(count),
                    "First anchor (ms)": anchor, "Series pause (ms)": pause if anchor is not None else None,
                }
        except ValueError as error:
            self.invalidate_preview()
            ui.summaryLabel.setText(str(error))
            return
        self.settings.update({
            "Step input": self.input_label, "Input baseline": baseline,
            "Input unit": self.input_unit, "Requested baseline (ms)": pre,
            "Requested recovery (ms)": post, "Requested late window (ms)": late,
        })
        if not self.input_key:
            self.settings["Stimulus baseline (%)"] = baseline
            if "Edge tolerance" in self.settings:
                self.settings["Edge tolerance (%)"] = self.settings["Edge tolerance"]
        self.sweeps = review_windows(self.recording, steps, pre, post)
        self.excluded.intersection_update((s.step.onset_ms, s.step.offset_ms) for s in self.sweeps)
        self.refresh()

    def show_step_summary(self, *, averages=False):
        from .step_summary_view import StepSummaryView

        if not any(self.is_included(sweep) for sweep in self.sweeps):
            return
        if not hasattr(self, "summary_view"):
            self.summary_view = StepSummaryView(self)
        if not averages and self.recording.clamp_mode == "VC" and self.input_key == "command_voltage":
            self.form.neuronCombo.setCurrentIndex(0)
            self.form.signalCombo.setCurrentIndex(1)
        self.summary_view.load(averages=averages)
        ui = self.window.ui
        ui.DataAnalysis_sweepStack.setCurrentWidget(ui.DataAnalysis_stepSummaryPage)

    def show_timing(self):
        from .spike_timing import spike_row

        index = self.form.sweepTable.currentRow()
        spikes = self.window.analysis_spikes
        if spikes is None or not 0 <= index < len(self.sweeps):
            return
        selected = self.sweeps[index]
        group = matching_sweeps(
            (s for s in self.sweeps if self.is_included(s)), selected,
            self.settings.get("Edge tolerance", .001), self.recording.nominal_step_ms + 1e-9,
        )
        if not group:
            self.form.summaryLabel.setText("No included sweeps match this amplitude and duration.")
            return
        neuron = self.form.neuronCombo.currentIndex()
        rows = [spike_row(
            self.recording, spikes.indices[neuron], neuron, sweep.step.number, sweep.baseline_start_ms,
            sweep.step.onset_ms, sweep.step.offset_ms, sweep.recovery_end_ms,
        ) for sweep in group]
        label = self.form.conditionEdit.text().strip() or self.recording.source.stem
        page.Spikeling103.ShowSpikeTiming(
            self.window, [(label, rows)], NEURON_NAMES[neuron], spikes.threshold_mv, 1,
            f"{self.recording.source.name} · {selected.step.amplitude:g} {self.input_unit} · {selected.step.offset_ms - selected.step.onset_ms:g} ms",
        )

    def response(self):
        neuron = self.form.neuronCombo.currentIndex()
        if self.form.signalCombo.currentIndex() == 0:
            return neuron, self.recording.voltage[neuron], VOLTAGE_COLUMNS[neuron], "mV", page.VOLTAGE_ROLES[neuron]
        units = "nA" if self.recording.clamp_mode == "VC" else "a.u."
        return neuron, self.recording.current[neuron], self.recording.current_columns[neuron], units, page.CURRENT_ROLES[neuron]

    def detect_spikes(self):
        page.Spikeling103.FindSpike(self.window)
        self.refresh()

    def is_included(self, sweep):
        step = sweep.step
        return not step.issue and (step.onset_ms, step.offset_ms) not in self.excluded

    def refresh(self):
        if self.recording is None:
            return
        ui = self.form
        spikes = self.window.analysis_spikes
        ui.spikesButton.setText("Detect spikes" if spikes is None else f"Spikes detected ({spikes.threshold_mv:g} mV)")
        ui.recordingLabel.setText(f"Sweeps · {self.recording.source.name} · {self.recording.clamp_mode}")
        neuron, signal, _, units, _ = self.response()
        table = ui.sweepTable
        selected = table.currentRow()
        self.metrics = [
            measure_sweep(self.recording, sweep, neuron, signal, spikes, self.settings["Requested late window (ms)"])
            for sweep in self.sweeps
        ]
        self.updating = True
        table.setRowCount(len(self.sweeps))
        headers = [
            "Use", "Sweep", f"Δ Input ({self.input_unit})", "Spikes", "Rate (Hz)", "Latency (ms)",
            f"Baseline ({units})", f"Peak Δ ({units})", f"Late ({units})", "Review",
            "Series", "Position", "Onset (ms)", "Offset (ms)", "Off before (ms)",
        ]
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        for column, width in enumerate([44, 55, 80, 58, 73, 86, 101, 93, 94, 180, 53, 64, 86, 86, 101]):
            table.setColumnWidth(column, width)
        for row, (sweep, metrics) in enumerate(zip(self.sweeps, self.metrics)):
            step = sweep.step
            included = QTableWidgetItem()
            flags = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
            if not step.issue:
                flags |= Qt.ItemFlag.ItemIsUserCheckable
            included.setFlags(flags)
            included.setCheckState(Qt.CheckState.Checked if self.is_included(sweep) else Qt.CheckState.Unchecked)
            table.setItem(row, 0, included)
            values = [step.number, step.amplitude]
            values.extend(metrics.get(key) for key in ("count", "rate", "latency", "baseline", "peak", "late"))
            clipped = ", ".join(
                name for name, flag in (("baseline", sweep.baseline_clipped), ("recovery", sweep.recovery_clipped)) if flag
            )
            status = step.issue or (f"Clipped {clipped}" if clipped else "")
            timing = (step.series, step.position, step.onset_ms, step.offset_ms, step.preceding_off_ms)
            for column, text in enumerate([*(display(v) for v in values), status, *(display(v) for v in timing)], 1):
                item = QTableWidgetItem(text)
                item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                table.setItem(row, column, item)
        if self.sweeps:
            if selected < 0:
                selected = next((i for i, s in enumerate(self.sweeps) if self.is_included(s)), 0)
            table.setCurrentCell(min(selected, len(self.sweeps) - 1), 1)
        self.updating = False
        self.update_summary()
        self.draw_overview()
        self.selection_changed()

    def update_summary(self):
        count = sum(self.is_included(sweep) for sweep in self.sweeps)
        self.form.exportButton.setEnabled(bool(self.sweeps))
        self.timing_button.setEnabled(bool(count) and self.window.analysis_spikes is not None)
        self.summary_button.setEnabled(bool(count))
        self.form.averageButton.setEnabled(bool(count))
        if self.sweeps:
            self.form.summaryLabel.setText(
                f"{len(self.sweeps)} candidates · {count} included. "
                + (self.settings["Alignment"] + ". " if self.sweeps[0].step.nominal_duration_ms is not None else "")
                + "Select a row to inspect its amplitude and duration group."
            )
        else:
            self.form.summaryLabel.setText("No step candidates. Check the baseline and tolerance, or enter step timing.")

    def include_changed(self, item):
        if self.updating or item.column() != 0 or item.row() >= len(self.sweeps):
            return
        step = self.sweeps[item.row()].step
        key = (step.onset_ms, step.offset_ms)
        if item.checkState() == Qt.CheckState.Checked:
            self.excluded.discard(key)
        else:
            self.excluded.add(key)
        self.update_summary()
        self.draw_aligned()

    def draw_overview(self):
        plot = self.form.overviewPlot
        plot.clear()
        self.highlight = None
        plot.setLabel("left", self.input_label)
        plot.setLabel("bottom", "Recording time (ms)")
        if self.recording is None:
            return
        page.plot_recorded(plot, self.recording, self.input_signal, "neuron_stimulus")
        for edge, symbol, role in (("onset_ms", "t1", "neuron_vm"), ("offset_ms", "t", "neuron_current")):
            times = np.array([getattr(s.step, edge) for s in self.sweeps], dtype=float)
            indices = np.searchsorted(self.recording.time_ms, times)
            keep = indices < len(self.recording.time_ms)
            values = self.input_signal[indices[keep]]
            theme_manager.themed_plot(plot, times[keep], values, role, symbol=symbol, symbol_size=7)
        plot.enableAutoRange(axis="y")
        plot.setXRange(self.recording.time_ms[0], self.recording.time_ms[-1], padding=0)

    def selection_changed(self, *args):
        if self.updating:
            return
        overview = self.form.overviewPlot
        if self.highlight is not None:
            overview.removeItem(self.highlight)
            self.highlight = None
        row = self.form.sweepTable.currentRow()
        if 0 <= row < len(self.sweeps):
            step = self.sweeps[row].step
            self.highlight = pg.LinearRegionItem(
                (step.onset_ms, step.offset_ms), movable=False,
                brush=pg.mkBrush(80, 170, 185, 45), pen=pg.mkPen(None),
            )
            overview.addItem(self.highlight, ignoreBounds=True)
        self.draw_aligned()

    def draw_aligned(self, *, measurement=None):
        ui = self.form
        ui.stimulusPlot.clear()
        ui.responsePlot.clear()
        if self.recording is None:
            return
        _, signal, label, _, role = self.response()
        ui.stimulusPlot.setLabel("left", self.input_label)
        ui.responsePlot.setLabel("left", label)
        ui.stimulusPlot.setLabel("bottom", "Time from step onset (ms)")
        ui.responsePlot.setLabel("bottom", "Time from step onset (ms)")
        row = ui.sweepTable.currentRow()
        if not 0 <= row < len(self.sweeps):
            return
        selected = self.sweeps[row]
        duration = selected.step.offset_ms - selected.step.onset_ms
        tolerance = self.settings.get("Edge tolerance", 0.001)
        group = matching_sweeps(
            (s for s in self.sweeps if s is not selected and self.is_included(s)),
            selected, tolerance, self.recording.nominal_step_ms + 1e-9,
        )
        # Each trace uses actual recorded relative timestamps. NaN separators
        # preserve gaps both within a recording and between individual sweeps.
        for plot, values, trace_role in (
            (ui.stimulusPlot, self.input_signal, "neuron_stimulus"),
            (ui.responsePlot, signal, role),
        ):
            for sweeps, colour in ((group, "analysis_loop"), ([selected], trace_role)):
                if sweeps:
                    x, y = self.overlay(sweeps, values)
                    theme_manager.themed_plot(plot, x, y, colour, connect="finite")
            plot.addItem(pg.LinearRegionItem(
                (0, duration), movable=False, brush=pg.mkBrush(80, 170, 185, 35), pen=pg.mkPen(None),
            ), ignoreBounds=True)
        if measurement in ("peak", "peak_inward", "peak_outward", "late", "late_change"):
            start = max(0, duration - self.settings["Requested late window (ms)"]) if measurement.startswith("late") else 0
            ui.responsePlot.addItem(pg.LinearRegionItem(
                (start, duration), movable=False, brush=pg.mkBrush(181, 137, 0, 65),
                pen=pg.mkPen(181, 137, 0),
            ), ignoreBounds=True)
        pre = self.settings["Requested baseline (ms)"]
        post = self.settings["Requested recovery (ms)"]
        page.sync_plot_x_range(self.aligned_plots, None, (-pre, duration + post))
        ui.responsePlot.enableAutoRange(axis="y")
        ui.stimulusPlot.enableAutoRange(axis="y")
        theme_manager.style_traces()

    def overlay(self, sweeps, values):
        times, traces = [], []
        for sweep in sweeps:
            left, right = sample_bounds(self.recording, sweep.baseline_start_ms, sweep.recovery_end_ms)
            gaps = np.flatnonzero(self.recording.gap_before[left:right])
            relative = self.recording.time_ms[left:right] - sweep.step.onset_ms
            times.extend((np.insert(relative, gaps, np.nan), [np.nan]))
            traces.extend((np.insert(values[left:right], gaps, np.nan), [np.nan]))
        return np.concatenate(times), np.concatenate(traces)

    def export(self):
        if not self.sweeps:
            return
        folder = page.choose_export_folder("Data", "Export sweep measurements")
        if folder is None:
            return
        neuron, _, signal_label, units, _ = self.response()
        rows = []
        for sweep, measured in zip(self.sweeps, self.metrics):
            step = sweep.step
            included = self.is_included(sweep)
            metrics = measured if included else {}
            rows.append({
                **self.recording.metadata(),
                **self.settings,
                "Condition": self.form.conditionEdit.text().strip(),
                "Neuron": NEURON_NAMES[neuron],
                "Response signal": signal_label,
                "Sweep": step.number,
                "Series": step.series,
                "Position": step.position,
                "Included": included,
                "Exclusion reason": step.issue or ("" if included else "Excluded by user"),
                "Step onset (ms)": step.onset_ms,
                "Step offset (ms)": step.offset_ms,
                ("Stimulus amplitude relative to baseline (%)" if not self.input_key
                 else f"Input change ({self.input_unit})"): step.amplitude,
                "Preceding off interval (ms)": step.preceding_off_ms,
                "Baseline start (ms)": sweep.baseline_start_ms,
                "Baseline clipped": sweep.baseline_clipped,
                "Recovery end (ms)": sweep.recovery_end_ms,
                "Recovery clipped": sweep.recovery_clipped,
                "Late window start (ms)": max(step.onset_ms, step.offset_ms - self.settings["Requested late window (ms)"]),
                "Spike threshold (mV)": self.window.analysis_spikes.threshold_mv if self.window.analysis_spikes else None,
                "Spike count": metrics.get("count"),
                "Rate (Hz)": metrics.get("rate"),
                "First-spike latency (ms)": metrics.get("latency"),
                f"Baseline ({units})": metrics.get("baseline"),
                f"Peak change ({units})": metrics.get("peak"),
                f"Late response ({units})": metrics.get("late"),
            })
        response = "vm" if self.form.signalCombo.currentIndex() == 0 else "current"
        filename = folder / f"{self.recording.source.stem}_{NEURON_NAMES[neuron]}_{response}_sweeps.csv"
        try:
            pd.DataFrame(rows).to_csv(filename, index=False)
        except (OSError, ValueError) as error:
            page.show_error(self.window.ui, "Cannot export sweeps", error)
