"""Desktop view for reference and comparison conditions."""

from dataclasses import asdict, replace
from pathlib import Path

import numpy as np
import pandas as pd
import pyqtgraph as pg
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QAbstractItemView, QFileDialog, QTableWidgetItem

from spikeling_gui.appearance.theme_manager import theme_manager
from spikeling_gui.paths import recordings_directory, save_dialog_directory

from . import page
from .comparison import (
    CC, VC, STP, TRAIN, COMMAND, EVENT_SOURCES, PROXY, STIM, METRICS, Condition, Settings,
    condition_trials, matched_groups, source_signal, subtraction, trace,
)
from .recording import NEURON_NAMES, load_recording
from .sweep_view import display, number


ROLES = ("neuron_vm", "neuron_current")


class CompareView(QObject):
    def __init__(self, window):
        super().__init__(window.ui.DataAnalysis_comparePage)
        self.widget = window.ui.DataAnalysis_comparePage
        self.window = window
        self.form = ui = page.bind_controls(window.ui, "Compare", (
            "ampEdit", "ampFieldLabel", "baselineEdit", "baselineFieldLabel", "cmpCurrent",
            "cmpEnd", "cmpFile", "cmpLoad", "cmpName", "cmpStart", "compareSplitter",
            "differenceCheck", "differenceDirectionCombo", "differenceLabel", "differenceOverlayCheck",
            "exportButton", "floorEdit", "groupCombo",
            "historyCheck", "inputPlot", "intervalEdit", "intervalFieldLabel", "metricCombo",
            "metricPlot", "minEdit", "neuronCombo", "preEdit", "presetCombo",
            "probeEdit", "probeLabel", "refCurrent", "refEnd", "refFile", "refLoad", "refName",
            "refStart", "responseFloorEdit", "responseFloorLabel", "responsePlot", "runButton",
            "signalCombo", "sourceCombo", "summaryLabel", "thresholdEdit",
            "timeEdit", "timingButton", "trialTable", "windowEdit", "windowFieldLabel",
        ))
        self.timing_button = ui.timingButton
        self.timing_button.clicked.connect(self.show_timing)
        self.conditions = [None, None]
        self.groups = []
        self.unmatched = ([], [])
        self.settings = None
        self.table_trials = []
        self.fields = [
            (ui.refName, ui.refStart, ui.refEnd, ui.refFile),
            (ui.cmpName, ui.cmpStart, ui.cmpEnd, ui.cmpFile),
        ]
        for index, button in enumerate((ui.refLoad, ui.cmpLoad)):
            button.clicked.connect(lambda checked=False, i=index: self.open_csv(i))
        for index, button in enumerate((ui.refCurrent, ui.cmpCurrent)):
            button.clicked.connect(lambda checked=False, i=index: self.capture(i))
        ui.responseFloorEdit.setToolTip(
            "Minimum absolute response amplitude in the selected signal units. Unscorable windows are excluded."
        )
        ui.probeEdit.setToolTip(
            "Optional. A single pulse after the train is a probe when its gap exceeds the within-train maximum "
            "and does not exceed this value."
        )
        ui.presetCombo.currentTextChanged.connect(self.preset_changed)
        ui.sourceCombo.currentTextChanged.connect(self.source_changed)
        ui.runButton.clicked.connect(self.run_comparison)
        ui.exportButton.clicked.connect(self.export)
        ui.groupCombo.currentIndexChanged.connect(self.draw_group)
        ui.metricCombo.currentTextChanged.connect(self.draw_metrics)
        ui.differenceCheck.toggled.connect(self.draw_traces)
        ui.differenceDirectionCombo.currentIndexChanged.connect(self.draw_traces)
        ui.differenceOverlayCheck.toggled.connect(self.draw_traces)
        ui.trialTable.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        ui.trialTable.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        ui.trialTable.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        ui.trialTable.currentCellChanged.connect(self.draw_traces)
        for widget in (ui.inputPlot, ui.responsePlot, ui.metricPlot):
            theme_manager.set_plot_background_role(widget, "panel_background")
            widget.showGrid(x=True, y=True, alpha=.2)
        ui.inputPlot.setXLink(ui.responsePlot)
        ui.compareSplitter.setSizes([480, 480])
        for field in (ui.neuronCombo, ui.signalCombo):
            field.currentIndexChanged.connect(self.invalidate)
        ui.historyCheck.toggled.connect(self.invalidate)
        for field in (*[item for row in self.fields for item in row[:3]], ui.baselineEdit,
                      ui.ampEdit, ui.timeEdit, ui.minEdit, ui.preEdit, ui.windowEdit,
                      ui.thresholdEdit, ui.intervalEdit, ui.floorEdit, ui.responseFloorEdit, ui.probeEdit):
            field.textChanged.connect(self.invalidate)
        self.preset_changed()

    def show_current_available(self):
        available = getattr(self.window, "analysis_recording", None) is not None
        self.form.refCurrent.setEnabled(available)
        self.form.cmpCurrent.setEnabled(available)

    def preset_changed(self):
        ui = self.form
        preset = ui.presetCombo.currentText()
        ui.sourceCombo.blockSignals(True)
        ui.sourceCombo.clear()
        ui.sourceCombo.addItems([*EVENT_SOURCES, PROXY] if preset in (STP, TRAIN) else [STIM, COMMAND])
        if preset == VC:
            ui.sourceCombo.setCurrentText(COMMAND)
        ui.sourceCombo.blockSignals(False)
        ui.signalCombo.setEnabled(preset in (STP, TRAIN))
        ui.windowEdit.setEnabled(preset != CC)
        ui.neuronCombo.setEnabled(preset != VC)
        ui.windowFieldLabel.setText("Late window (ms)" if preset == VC else "Response window (ms)")
        ui.historyCheck.setEnabled(preset not in (STP, TRAIN))
        ui.thresholdEdit.setEnabled(preset == CC)
        ui.intervalEdit.setEnabled(preset in (STP, TRAIN))
        ui.intervalFieldLabel.setText("Max within-train gap (ms)" if preset == TRAIN else "Max pair interval (ms)")
        ui.responseFloorLabel.setText("Response threshold (signal units)")
        for widget in (ui.responseFloorEdit, ui.responseFloorLabel, ui.probeEdit, ui.probeLabel):
            widget.setVisible(preset == TRAIN)
        ui.floorEdit.setEnabled(preset == STP)
        ui.differenceCheck.setChecked(False)
        ui.differenceCheck.setVisible(preset == VC)
        ui.metricCombo.blockSignals(True)
        ui.metricCombo.clear()
        ui.metricCombo.addItems(METRICS[preset])
        ui.metricCombo.setCurrentIndex(1 if preset == CC else 2 if preset == STP else 0)
        ui.metricCombo.blockSignals(False)
        self.source_changed()

    def source_changed(self):
        ui = self.form
        source = ui.sourceCombo.currentText()
        preset = ui.presetCombo.currentText()
        if source == COMMAND:
            unit = "mV" if preset == VC else "a.u."
        else:
            unit = "%"
        ui.baselineFieldLabel.setText(f"Input baseline ({unit})")
        ui.ampFieldLabel.setText(f"Amplitude tolerance ({unit})")
        for field in (ui.baselineEdit, ui.ampEdit, ui.minEdit):
            field.setEnabled(source not in EVENT_SOURCES)
        self.invalidate()

    def invalidate(self, *args):
        self.groups = []
        self.unmatched = ([], [])
        self.settings = None
        self.table_trials = []
        ui = self.form
        ui.groupCombo.clear()
        ui.trialTable.setRowCount(0)
        ui.differenceLabel.clear()
        self.draw_traces()
        ui.summaryLabel.setToolTip("")
        for plot in (ui.inputPlot, ui.responsePlot, ui.metricPlot):
            plot.clear()
        ui.exportButton.setEnabled(False)
        self.timing_button.setEnabled(False)
        message = "Choose two conditions, then compare."
        if all(c is not None for c in self.conditions):
            source = ui.sourceCombo.currentText()
            if source == STIM:
                message = "Ready. Matching uses the recorded stimulus in %, which is the input shown on the axis."
            elif source == PROXY:
                message = "Use this source when the recorded stimulus pulses represent presynaptic input."
            else:
                message = "Ready. Click Compare to match the recordings."
        ui.summaryLabel.setText(message)

    def open_csv(self, index):
        filename, _ = QFileDialog.getOpenFileName(
            self.widget, "Open condition recording", save_dialog_directory(recordings_directory()), "CSV files (*.csv)"
        )
        if not filename:
            return
        try:
            recording = load_recording(filename)
        except (OSError, ValueError) as error:
            page.show_error(self.window.ui, "Cannot load recording", error)
            return
        self.assign(index, recording)

    def capture(self, index):
        recording = getattr(self.window, "analysis_recording", None)
        if recording is None:
            return
        sweeps = getattr(self.window, "analysis_sweep_view", None)
        if sweeps is not None and sweeps.recording is recording and sweeps.sweeps:
            reviewed = tuple(s for s in sweeps.sweeps if sweeps.is_included(s))
            source = COMMAND if sweeps.input_key else STIM
            self.assign(index, recording, reviewed, sweeps.settings["Input baseline"], source)
        else:
            self.assign(index, recording)
        condition = self.window.ui.DataAnalysis_conditionEdit.text().strip()
        if condition:
            self.fields[index][0].setText(condition)

    def assign(self, index, recording, reviewed=None, baseline=0, source=STIM):
        time = recording.time_ms
        provenance = f"Reviewed sweeps · {source}" if reviewed is not None else "Recording · detected input events"
        self.conditions[index] = Condition("", recording, time[0], time[-1] + recording.nominal_step_ms,
                                           reviewed, provenance, baseline, source)
        _, start, end, label = self.fields[index]
        start.clear()
        end.clear()
        label.setText(f"{recording.source.name} · {recording.clamp_mode}")
        label.setToolTip(f"{recording.source}\n{provenance}")
        self.invalidate()

    def selected_conditions(self):
        if any(condition is None for condition in self.conditions):
            raise ValueError("Load a recording for each condition.")
        result = []
        for condition, (name, start, end, _) in zip(self.conditions, self.fields):
            lower = number(start, "condition start", optional=True)
            upper = number(end, "condition end", optional=True)
            label = name.text().strip()
            lower = condition.start if lower is None else lower
            upper = condition.end if upper is None else upper
            if not label or not condition.start <= lower < upper <= condition.end:
                raise ValueError("Each condition needs a name and a range within its recording.")
            result.append(replace(condition, label=label, start=lower, end=upper))
        ref, cmp = result
        if ref.label.casefold() == cmp.label.casefold():
            raise ValueError("Give the two conditions different names.")
        if ref.recording.recording_id == cmp.recording.recording_id and max(ref.start, cmp.start) < min(ref.end, cmp.end):
            raise ValueError("Conditions from the same recording must use non-overlapping ranges.")
        if ref.recording.clamp_mode != cmp.recording.clamp_mode:
            raise ValueError("Use the same clamp mode for both conditions.")
        return result

    def collect_settings(self):
        ui = self.form
        preset, source = ui.presetCombo.currentText(), ui.sourceCombo.currentText()
        return Settings(
            preset, source,
            baseline=number(ui.baselineEdit, "input baseline") if source not in EVENT_SOURCES else 0,
            amplitude_tolerance=number(ui.ampEdit, "amplitude tolerance", 0.001) if source not in EVENT_SOURCES else 0,
            time_tolerance=number(ui.timeEdit, "time tolerance", 0),
            minimum_step=number(ui.minEdit, "minimum step", 0.001) if source not in EVENT_SOURCES else 0,
            pre=number(ui.preEdit, "baseline window", 0.001),
            window=number(ui.windowEdit, "response window", 0.001) if preset != CC else 5,
            threshold=number(ui.thresholdEdit, "spike threshold") if preset == CC else -20,
            pair_interval=number(ui.intervalEdit, "maximum pair interval", 0.001) if preset in (STP, TRAIN) else 100,
            ratio_floor=number(ui.floorEdit, "response 1 ratio floor", 0.001) if preset == STP else .1,
            neuron=0 if preset == VC else ui.neuronCombo.currentIndex(),
            current_response=preset in (STP, TRAIN) and ui.signalCombo.currentIndex() == 1,
            match_history=preset not in (STP, TRAIN) and ui.historyCheck.isChecked(),
            response_floor=number(ui.responseFloorEdit, "response threshold", .001) if preset == TRAIN else .1,
            probe_limit=number(ui.probeEdit, "maximum recovery gap", .001, optional=True) if preset == TRAIN else None,
        )

    def run_comparison(self):
        self.invalidate()
        ui = self.form
        try:
            ref, cmp = self.selected_conditions()
            settings = self.collect_settings()
            if settings.probe_limit is not None and settings.probe_limit <= settings.pair_interval:
                raise ValueError("The maximum recovery gap must exceed the within-train gap.")
            left, excluded_left = condition_trials(ref, settings)
            right, excluded_right = condition_trials(cmp, settings)
            self.groups, left_only, right_only = matched_groups(left, right, settings)
        except ValueError as error:
            ui.summaryLabel.setText(str(error))
            return
        self.settings = settings
        self.unmatched = left_only, right_only
        self.excluded_counts = excluded_left, excluded_right
        _, self.input_label = source_signal(ref.recording, settings)
        result = (
            f"{len(self.groups)} matched groups · unmatched groups: {ref.label} {len(left_only)}, {cmp.label} {len(right_only)}"
            f" · skipped candidates: {excluded_left}, {excluded_right}"
        )
        if settings.source == STIM:
            result += " · matching on recorded stimulus (%)"
        ui.summaryLabel.setText(result)
        unmatched_labels = ["; ".join(self.group_label(g[0]) for g in side) for side in self.unmatched]
        ui.summaryLabel.setToolTip(f"Unmatched {ref.label}: {unmatched_labels[0] or 'None'}\n"
                                   f"Unmatched {cmp.label}: {unmatched_labels[1] or 'None'}")
        ui.exportButton.setEnabled(bool(self.groups or left_only or right_only))
        ui.groupCombo.blockSignals(True)
        for left_group, _ in self.groups:
            ui.groupCombo.addItem(self.group_label(left_group[0]))
        ui.groupCombo.blockSignals(False)
        self.draw_group()
        self.draw_metrics()

    def group_label(self, trial):
        if self.settings.preset == TRAIN:
            return trial.label
        if self.settings.preset == STP:
            if self.settings.source == PROXY:
                return f"{trial.key[0]:g} ms · pulses {trial.key[1]:g}/{trial.key[2]:g}%"
            return trial.label
        amplitude, duration, holding, *_ = trial.key
        level = holding + amplitude
        return f"{level:g} · {duration:g} ms · baseline {holding:g}"

    def show_timing(self):
        from .recording import detect_spikes
        from .spike_timing import spike_row

        index = self.form.groupCombo.currentIndex()
        if not 0 <= index < len(self.groups) or self.settings.preset != CC:
            return
        neuron = self.settings.neuron
        threshold = self.settings.threshold
        groups, detected = [], {}
        for trials in self.groups[index]:
            recording = trials[0].condition.recording
            if recording.recording_id not in detected:
                detected[recording.recording_id] = detect_spikes(recording, threshold).indices[neuron]
            indices = detected[recording.recording_id]
            rows = [spike_row(recording, indices, neuron, number, trial.start, trial.onset,
                              trial.offset, trial.end) for number, trial in enumerate(trials, 1)]
            groups.append((trials[0].condition.label, rows))
        page.Spikeling103.ShowSpikeTiming(
            self.window, groups, NEURON_NAMES[neuron], threshold, 2, self.form.groupCombo.currentText(),
        )

    def draw_group(self, *args):
        index = self.form.groupCombo.currentIndex()
        self.table_trials = []
        self.table_pulses = []
        self.timing_button.setEnabled(0 <= index < len(self.groups) and self.settings.preset == CC)
        table = self.form.trialTable
        table.blockSignals(True)
        table.clearContents()
        table.setRowCount(0)
        if 0 <= index < len(self.groups):
            left, right = self.groups[index]
            names = METRICS[self.settings.preset]
            headers = ["Condition", "Onset (ms)", *(self.metric_label(n) for n in names), "Review"]
            rows = []
            if self.settings.preset == TRAIN:
                headers.insert(2, "Pulse")
                for trial in left + right:
                    for pulse in trial.pulses:
                        self.table_trials.append(trial)
                        self.table_pulses.append(pulse.number)
                        values = pulse.metrics()
                        rows.append([trial.condition.label, display(pulse.onset),
                                     "Probe" if pulse.recovery else str(pulse.number),
                                     *(display(values[name]) for name in names),
                                     "Unscored" if pulse.success is None else ""])
            else:
                self.table_trials = left + right
                rows = [[trial.condition.label, display(trial.onset),
                         *(display(trial.metrics[name]) for name in names), trial.review] for trial in self.table_trials]
            table.setColumnCount(len(headers))
            table.setHorizontalHeaderLabels(headers)
            table.setRowCount(len(rows))
            for row, values in enumerate(rows):
                for column, value in enumerate(values):
                    table.setItem(row, column, QTableWidgetItem(value))
            table.resizeColumnsToContents()
        table.blockSignals(False)
        self.draw_traces()
        if self.settings is not None and self.settings.preset == TRAIN:
            self.draw_metrics()
        else:
            self.show_difference()

    def show_difference(self):
        ui = self.form
        index = ui.groupCombo.currentIndex()
        if not 0 <= index < len(self.groups):
            ui.differenceLabel.clear()
            return
        metric = ui.metricCombo.currentText()
        if not metric:
            return
        left, right = self.groups[index]
        groups = (left, right)
        if self.settings.preset == TRAIN:
            labels = [f"{group[0].condition.label}: {len(group)} trains" for group in groups]
            ui.differenceLabel.setText(" · ".join(labels) + " · Points show trials. Lines connect pulse means.")
            return
        values = [[t.metrics[metric] for t in group if t.metrics[metric] is not None] for group in groups]
        means = [float(np.mean(v)) if v else None for v in values]
        labels = [group[0].condition.label for group in groups]
        delta = means[1] - means[0] if all(v is not None for v in means) else None
        details = [f"{label} {display(avg)} ({len(v)}/{len(group)} sweeps)"
                   for label, avg, v, group in zip(labels, means, values, groups)]
        ui.differenceLabel.setText(
            f"{self.metric_label(metric)} · " + " · ".join(details)
            + f" · {labels[1]} − {labels[0]} {display(delta)}"
        )

    def draw_traces(self, *args):
        ui = self.form
        ui.inputPlot.clear()
        ui.responsePlot.clear()
        is_vc = ui.presetCombo.currentText() == VC
        subtract = is_vc and ui.differenceCheck.isChecked()
        can_overlay = subtract and ui.sourceCombo.currentText() == COMMAND
        overlay = can_overlay and ui.differenceOverlayCheck.isChecked()
        ui.differenceDirectionCombo.setVisible(subtract)
        ui.differenceOverlayCheck.setVisible(can_overlay)
        if ui.responsePlot.plotItem.legend is not None:
            ui.responsePlot.plotItem.legend.setVisible(overlay)
        index = ui.groupCombo.currentIndex()
        if not 0 <= index < len(self.groups):
            return
        left, right = self.groups[index]
        legend = ui.inputPlot.addLegend(offset=(8, 6)) if ui.inputPlot.plotItem.legend is None else ui.inputPlot.plotItem.legend
        legend.clear()
        ui.inputPlot.setLabel("left", self.input_label)
        ui.responsePlot.setLabel("bottom", "Time from onset (ms)")
        if overlay:
            self.draw_voltage_differences()
            return
        for trials, role in zip((left, right), ROLES):
            self.overlay(ui.inputPlot, trials, "stimulus", role, trials[0].condition.label)
        if subtract:
            first, second = self.subtraction_order(left, right)
            x, y = subtraction(second, first)
            ui.responsePlot.setLabel("left", self.subtraction_label(first, second))
            theme_manager.themed_plot(ui.responsePlot, x, y, ROLES[0], connect="finite")
        else:
            unit = left[0].response_unit
            ui.responsePlot.setLabel("left", f"Response ({unit})")
            for trials, role in zip((left, right), ROLES):
                self.overlay(ui.responsePlot, trials, "signal", role)
            row = ui.trialTable.currentRow()
            if 0 <= row < len(self.table_trials):
                x, y = trace(self.table_trials[row], self.table_trials[row].signal)
                theme_manager.themed_plot(ui.responsePlot, x, y, "neuron_stimulus", width_scale=2.5, connect="finite")
        theme_manager.style_traces()

    def subtraction_order(self, left, right):
        return (left, right) if self.form.differenceDirectionCombo.currentIndex() == 1 else (right, left)

    @staticmethod
    def subtraction_label(first, second):
        return f"{first[0].condition.label} − {second[0].condition.label} (nA)"

    def draw_voltage_differences(self):
        ui = self.form
        if ui.responsePlot.plotItem.legend is None:
            ui.responsePlot.addLegend(offset=(8, 6), colCount=3)
        ui.responsePlot.plotItem.legend.show()
        first, second = self.subtraction_order(*self.groups[0])
        ui.responsePlot.setLabel("left", self.subtraction_label(first, second))
        for i, (left, right) in enumerate(self.groups):
            first, second = self.subtraction_order(left, right)
            x, y = subtraction(second, first)
            if not np.isfinite(y).any():
                continue
            pen = pg.mkPen(pg.intColor(i, hues=max(6, len(self.groups))), width=2)
            trial = left[0]
            amplitude, duration, holding, *_ = trial.key
            label = f"{holding + amplitude:g} mV"
            if sum(abs(other[0].key[0] + other[0].key[2] - holding - amplitude) < 1e-9
                   for other, _ in self.groups) > 1:
                label += f" · {duration:g} ms · hold {holding:g} mV"
            ui.responsePlot.plot(x, y, pen=pen, name=label, connect="finite")
            time, command = trace(trial, trial.stimulus)
            ui.inputPlot.plot(time, command, pen=pen, connect="finite")

    def overlay(self, plot, trials, channel, role, name=None):
        x, y = [], []
        for trial in trials:
            t, values = trace(trial, getattr(trial, channel))
            x.extend((t, [np.nan]))
            y.extend((values, [np.nan]))
        theme_manager.themed_plot(plot, np.concatenate(x), np.concatenate(y), role, name=name, connect="finite")

    def metric_label(self, metric):
        if metric in ("Response 1", "Response 2", "Response amplitude", "Successful response amplitude") and self.groups:
            return f"{metric} ({self.groups[0][0][0].response_unit})"
        return metric

    def draw_metrics(self, *args):
        self.show_difference()
        plot = self.form.metricPlot
        plot.clear()
        if not self.groups:
            return
        metric = self.form.metricCombo.currentText()
        if not metric:
            return
        plot.setLabel("left", self.metric_label(metric))
        plot.enableAutoRange(axis="y")
        preset = self.settings.preset
        if preset == TRAIN:
            index = self.form.groupCombo.currentIndex()
            if 0 <= index < len(self.groups):
                self.draw_train_metrics(plot, *self.groups[index], metric)
            return
        base_positions = []
        for left, _ in self.groups:
            trial = left[0]
            base_positions.append(trial.key[0] if preset == STP else trial.key[0] + trial.key[2])
        distinct = len(set(base_positions)) == len(base_positions)
        positions = base_positions if distinct else list(range(1, len(self.groups) + 1))
        ticks = [(value, f"{value:g}" if distinct else self.group_label(self.groups[i][0][0]))
                 for i, value in enumerate(positions)]
        plot.getAxis("bottom").setTicks([ticks])
        axis_label = "Pulse interval (ms)" if preset == STP else self.input_label
        plot.setLabel("bottom", axis_label if distinct else "Matched group")
        span = np.diff(sorted(set(positions)))
        spacing = min(span) if len(span) else max(abs(positions[0]) * .1, 1)
        iv_means = ([], [])
        connect_iv = False
        if preset == VC and self.settings.source == COMMAND and distinct:
            durations = [left[0].key[1] for left, _ in self.groups]
            holding_levels = [left[0].key[2] for left, _ in self.groups]
            connect_iv = (np.ptp(durations) <= self.settings.time_tolerance
                          and np.ptp(holding_levels) <= self.settings.amplitude_tolerance)
        for index, (left, right) in enumerate(self.groups):
            for side, trials in enumerate((left, right)):
                values = [(trial, trial.metrics[metric]) for trial in trials if trial.metrics[metric] is not None]
                if not values:
                    continue
                centre = positions[index] + (-.12 if side == 0 else .12) * spacing
                ys = [float(value) for _, value in values]
                if connect_iv:
                    iv_means[side].append((positions[index], float(np.mean(ys))))
                xs = centre + np.linspace(-.075, .075, len(ys)) * spacing if len(ys) > 1 else [centre]
                colour = theme_manager.active_colour(ROLES[side])
                scatter = pg.ScatterPlotItem(xs, ys, data=[(index, id(trial)) for trial, _ in values],
                                             size=7, brush=colour, pen=None)
                scatter.sigClicked.connect(self.select_point)
                plot.addItem(scatter)
                theme_manager.themed_plot(
                    plot, [centre - .075 * spacing, centre + .075 * spacing],
                    [float(np.mean(ys))] * 2, ROLES[side], width_scale=2,
                )
        for means, role in zip(iv_means, ROLES):
            if means:
                voltages, currents = zip(*sorted(means))
                theme_manager.themed_plot(plot, voltages, currents, role, width_scale=2)
        theme_manager.style_traces()

    def draw_train_metrics(self, plot, left, right, metric):
        plot.setLabel("left", self.metric_label(metric))
        plot.setLabel("bottom", "Pulse number")
        if metric == "Response probability (%)":
            plot.setYRange(-3, 103, padding=0)
        index = self.form.groupCombo.currentIndex()
        positions = left[0].pulses
        plot.getAxis("bottom").setTicks([[
            (pulse.number, "Probe" if pulse.recovery else str(pulse.number)) for pulse in positions
        ]])
        for side, group in enumerate((left, right)):
            role = ROLES[side]
            x_mean, y_mean = [], []
            for p, pulse in enumerate(positions):
                values = [(t, t.pulses[p].metrics()[metric]) for t in group]
                values = [(t, y) for t, y in values if y is not None]
                centre = pulse.number + (-.13 if side == 0 else .13)
                x_mean.append(centre)
                y_mean.append(float(np.mean([y for _, y in values])) if values else np.nan)
                if not values:
                    continue
                xs = centre + np.linspace(-.075, .075, len(values)) if len(values) > 1 else [centre]
                scatter = pg.ScatterPlotItem(
                    xs, [y for _, y in values], data=[(index, id(t), pulse.number) for t, _ in values],
                    size=7, brush=theme_manager.active_colour(role), pen=None,
                )
                scatter.sigClicked.connect(self.select_point)
                plot.addItem(scatter)
            theme_manager.themed_plot(plot, x_mean, y_mean, role, width_scale=2, connect="finite")
        theme_manager.style_traces()

    def select_point(self, item, points, event):
        if not len(points):
            return
        group, identity, *pulse = points[0].data()
        self.form.groupCombo.setCurrentIndex(group)
        row = next((i for i, trial in enumerate(self.table_trials) if id(trial) == identity
                    and (not pulse or self.table_pulses[i] == pulse[0])), None)
        if row is not None:
            self.form.trialTable.setCurrentCell(row, 0)
            self.draw_traces()

    def export(self):
        if self.settings is None:
            return
        folder = page.choose_export_folder("Data", "Export comparison")
        if folder is None:
            return
        trials, summaries = [], []
        train = self.settings.preset == TRAIN
        names = METRICS[self.settings.preset]
        for group_id, (left, right) in enumerate(self.groups, 1):
            positions = range(len(left[0].pulses)) if train else (None,)
            for position in positions:
                for name in names:
                    lv, rv = [self.metric_values(group, name, position) for group in (left, right)]
                    a, b = (float(np.mean(v)) if v else None for v in (lv, rv))
                    summaries.append({
                        "Group": group_id, "Matched input": self.group_label(left[0]), "Input source": self.input_label,
                        "Pulse": left[0].pulses[position].number if train else None,
                        "Recovery probe": left[0].pulses[position].recovery if train else None,
                        "Metric": self.metric_label(name), "Reference": left[0].condition.label,
                        "Comparison": right[0].condition.label, "Reference sweeps": len(left),
                        "Comparison sweeps": len(right), "Reference defined": len(lv), "Comparison defined": len(rv),
                        "Reference recordings": len({t.condition.recording.recording_id for t in left}),
                        "Comparison recordings": len({t.condition.recording.recording_id for t in right}),
                        "Reference mean": a, "Comparison mean": b,
                        "Reference SD": np.std(lv, ddof=1) if len(lv) > 1 else None,
                        "Comparison SD": np.std(rv, ddof=1) if len(rv) > 1 else None,
                        "Comparison minus reference": b - a if a is not None and b is not None else None,
                    })
            for trial in left + right:
                trials.extend(self.export_rows(trial, group_id, "Matched"))
        for side in self.unmatched:
            for group in side:
                for trial in group:
                    trials.extend(self.export_rows(trial, None, "Unmatched or ambiguous"))
        try:
            pd.DataFrame(trials).to_csv(Path(folder) / "Spikeling_comparison_trials.csv", index=False)
            columns = [
                "Group", "Matched input", "Input source", "Metric", "Reference", "Comparison",
                "Reference sweeps", "Comparison sweeps", "Reference defined", "Comparison defined",
                "Reference recordings", "Comparison recordings", "Reference mean", "Comparison mean",
                "Reference SD", "Comparison SD", "Comparison minus reference",
            ]
            if train:
                columns[3:3] = ["Pulse", "Recovery probe"]
            pd.DataFrame(summaries, columns=columns).to_csv(
                Path(folder) / "Spikeling_comparison_summary.csv", index=False
            )
        except (OSError, ValueError) as error:
            page.show_error(self.window.ui, "Cannot export comparison", error)

    def metric_values(self, group, name, position):
        values = [t.metrics[name] if position is None else t.pulses[position].metrics()[name] for t in group]
        return [value for value in values if value is not None]

    def export_rows(self, trial, group, status):
        base = self.export_trial(trial, group, status)
        if not trial.pulses:
            return [base]
        return [{
            **base,
            "Pulse": pulse.number, "Pulse onset (ms)": pulse.onset,
            "Pulse baseline start (ms)": pulse.baseline_start, "Pulse response end (ms)": pulse.response_end,
            "Recovery probe": pulse.recovery, "Detected response": pulse.success, **pulse.metrics(),
        } for pulse in trial.pulses]

    def export_trial(self, trial, group, status):
        condition = trial.condition
        return {
            **condition.recording.metadata(),
            "Condition": condition.label, "Condition start (ms)": condition.start,
            "Condition end (ms)": condition.end,
            "Provenance": condition.provenance if self.settings.source == STIM else "Detected from selected input",
            "Group": group, "Status": status, "Matched input": self.group_label(trial),
            "Matching values": repr(trial.key), "Input source": self.input_label,
            "Neuron": NEURON_NAMES[self.settings.neuron],
            "Onset (ms)": trial.onset, "Second pulse (ms)": trial.second_onset,
            "Measurement start (ms)": trial.start, "Measurement end (ms)": trial.end,
            "Response unit": trial.response_unit, "Review": trial.review,
            **asdict(self.settings), **trial.metrics,
        }
