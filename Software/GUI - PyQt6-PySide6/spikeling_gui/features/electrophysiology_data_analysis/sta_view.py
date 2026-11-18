"""Embedded Data Analysis view for spike-triggered stimulus histories."""

import csv

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import QObject, QSignalBlocker
from PySide6.QtGui import QColor

from spikeling_gui.appearance.theme_manager import theme_manager

from . import page
from .recording import NEURON_NAMES, STIMULUS_COLUMN, detect_spikes, presynaptic_event_indices
from .sta import spike_triggered_average
from .sweep_view import number


class SpikeTriggeredAverageView(QObject):
    def __init__(self, window):
        super().__init__(window.ui.DataAnalysis_staPage)
        self.window = window
        self.recording = None
        self.result = None
        self.form = ui = page.bind_controls(window.ui, "STA", (
            "contextLabel", "neuronCombo", "signalCombo", "thresholdEdit", "windowEdit",
            "shuffleEdit", "seedEdit", "runButton", "exportButton", "summaryLabel", "staPlot",
        ))
        theme_manager.set_plot_background_role(ui.staPlot, "panel_background")
        ui.staPlot.setLabel("bottom", "Time relative to spike (ms)")
        ui.staPlot.showGrid(x=True, y=True, alpha=.25)
        ui.staPlot.addLegend(offset=(6, 5))
        for field in (ui.thresholdEdit, ui.windowEdit, ui.shuffleEdit, ui.seedEdit):
            field.textChanged.connect(self.invalidate)
        ui.neuronCombo.currentIndexChanged.connect(self.invalidate)
        ui.signalCombo.currentIndexChanged.connect(self.invalidate)
        ui.runButton.clicked.connect(self.calculate)
        ui.exportButton.clicked.connect(self.export)
        self.invalidate()

    def load(self, recording):
        if recording is self.recording:
            return
        self.recording = recording
        ui = self.form
        with QSignalBlocker(ui.neuronCombo), QSignalBlocker(ui.signalCombo), QSignalBlocker(ui.thresholdEdit):
            ui.neuronCombo.clear()
            ui.signalCombo.clear()
            ui.contextLabel.setText(recording.source.name)
            for index, label in enumerate(("Spikeling", "Auxiliary neuron 1", "Auxiliary neuron 2")):
                if index != 0 or recording.clamp_mode == "CC":
                    ui.neuronCombo.addItem(label, index)
            ui.thresholdEdit.setText(self.window.ui.Spikeling_DataAnalysis_Spike_lineEdit.text())
            ui.signalCombo.addItem(STIMULUS_COLUMN, "")
            for key, label in (("command_current", "Command current (a.u.)"),
                               ("command_voltage", "Command voltage (mV)")):
                if key in recording.extra_channels:
                    ui.signalCombo.addItem(label, key)
        self.invalidate()

    def event_flags(self):
        neuron = self.form.neuronCombo.currentData()
        return self.recording.extra_channels.get(f"presynaptic_events_{neuron}") if neuron and self.recording is not None else None

    def invalidate(self, *args):
        self.result = None
        ui = self.form
        ui.exportButton.setEnabled(False)
        ui.thresholdEdit.setEnabled(self.event_flags() is None)
        ui.staPlot.clear()
        ui.summaryLabel.setText("Calculate to average the recorded input before each eligible spike.")

    def calculate(self):
        self.invalidate()
        ui = self.form
        rec = self.recording
        if rec is None:
            return
        neuron = ui.neuronCombo.currentData()
        source = ui.signalCombo.currentText()
        key = ui.signalCombo.currentData()
        stimulus = rec.extra_channels[key] if key else rec.stimulus
        try:
            lookback = number(ui.windowEdit, "look-back", .001)
            shuffles = number(ui.shuffleEdit, "control shuffles", 0)
            seed = number(ui.seedEdit, "shuffle seed", 0)
            if not shuffles.is_integer() or not seed.is_integer() or seed > 2**32 - 1:
                raise ValueError("Use whole numbers for shuffles and a seed from 0 to 4294967295.")
            flags = self.event_flags()
            threshold = None
            if flags is None:
                threshold = number(ui.thresholdEdit, "spike threshold")
                events = detect_spikes(rec, threshold).indices[neuron]
                method = "Voltage threshold"
            else:
                events = presynaptic_event_indices(rec, f"presynaptic_events_{neuron}")
                method = "Recorded event flags"
            result = spike_triggered_average(rec, stimulus, events, lookback, int(shuffles), int(seed))
        except ValueError as error:
            ui.summaryLabel.setText(str(error))
            return
        self.result = result
        self.details = {
            **rec.metadata(), "Neuron": NEURON_NAMES[neuron], "Input": source, "Spike source": method,
            "Spike threshold (mV)": threshold, "Requested look-back (ms)": lookback,
            "Spikes found": result.event_count, "Spikes used": result.used_count,
            "Shuffles": result.shuffle_count, "Shiftable spikes": result.shuffled_spikes,
            "Shuffle seed": int(seed),
        }
        self.draw(source, result, method)

    def draw(self, source, result, method):
        ui = self.form
        plot = ui.staPlot
        plot.setLabel("left", source)
        x = result.lags_ms
        if result.control_mean is not None:
            colour = QColor(theme_manager.active_colour("analysis_loop"))
            colour.setAlpha(65)
            low = theme_manager.themed_plot(plot, x, result.control_low, "analysis_loop", width_scale=.6)
            high = theme_manager.themed_plot(plot, x, result.control_high, "analysis_loop", width_scale=.6)
            plot.addItem(pg.FillBetweenItem(low, high, brush=pg.mkBrush(colour)))
            theme_manager.themed_plot(plot, x, result.control_mean, "neuron_current", name="Shuffled mean")
        theme_manager.themed_plot(plot, x, result.average, "neuron_stimulus", name="Spike-triggered average",
                                  width_scale=2)
        plot.setXRange(x[0], x[-1], padding=.02)
        summary = f"{method} · {result.used_count}/{result.event_count} spikes had complete histories"
        if result.shuffle_count:
            summary += f" · {result.shuffle_count} circular shuffles · shaded band: pointwise 95% shuffle range"
            if result.shuffled_spikes != result.used_count:
                summary += f" · {result.shuffled_spikes} spikes eligible to shift"
        elif float(self.form.shuffleEdit.text()):
            summary += " · no eligible histories could be shifted"
        if np.ptp(result.average) == 0:
            summary += " · the average input is flat"
        ui.summaryLabel.setText(summary)
        ui.exportButton.setEnabled(True)
        theme_manager.style_traces()

    def export(self):
        if self.result is None:
            return
        folder = page.choose_export_folder("Data", "Export spike-triggered average")
        if folder is None:
            return
        result = self.result
        path = folder / f"{self.recording.source.stem}_{self.details['Neuron']}_STA.csv"
        columns = {
            "Lag (ms)": result.lags_ms, "STA": result.average,
            "Shuffled mean": result.control_mean, "Shuffle 2.5%": result.control_low,
            "Shuffle 97.5%": result.control_high,
        }
        try:
            with path.open("w", encoding="utf-8", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=[*self.details, *columns])
                writer.writeheader()
                for i in range(len(result.lags_ms)):
                    writer.writerow({
                        **self.details, **{name: values[i] if values is not None else None
                                           for name, values in columns.items()},
                    })
        except OSError as error:
            page.show_error(self.window.ui, "Cannot export spike-triggered average", error)
