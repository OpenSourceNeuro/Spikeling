"""Recording, spike detection and stimulus-cycle views for the desktop GUI."""

from html import escape
import json
from pathlib import Path
from types import SimpleNamespace

from PySide6.QtCore import QSignalBlocker, Qt
from PySide6.QtWidgets import QButtonGroup, QFileDialog
import numpy as np
import pandas as pd
import pyqtgraph as pg
from pyqtgraph.exporters import ImageExporter

from spikeling_gui.appearance.dialogs import themed_message_box
from spikeling_gui.appearance.theme_manager import theme_manager
from spikeling_gui.paths import recordings_directory, save_dialog_directory

from .recording import (
    NEURON_NAMES,
    STIMULUS_COLUMN,
    TIME_COLUMN,
    VOLTAGE_COLUMNS,
    align_cycles,
    detect_spikes,
    load_recording,
)


VOLTAGE_ROLES = ("neuron_vm", "neuron_syn1_vm", "neuron_syn2_vm")
CURRENT_ROLES = ("neuron_current", "neuron_syn1_input", "neuron_syn2_input")
MEAN_WIDTH_SCALE = 2.0

# Item order of DataAnalysis_sweepModeCombo in UI_Spikeling.ui.
CYCLE_MODE_INDEX = 0
STEP_MODE_INDEX = 1


def recording_plots(ui):
    return (ui.DataAnalysis_inputPlot, ui.DataAnalysis_voltagePlot, ui.DataAnalysis_currentPlot,
            ui.DataAnalysis_synapticPlot, ui.DataAnalysis_ratePlot)


def bind_controls(ui, prefix, names):
    return SimpleNamespace(**{name: getattr(ui, f"DataAnalysis_{prefix}_{name}") for name in names})


def cycle_plots(ui):
    return (ui.DataAnalysis_Cycles_stimulusPlot, ui.DataAnalysis_Cycles_rasterPlot,
            ui.DataAnalysis_Cycles_voltagePlot, ui.DataAnalysis_Cycles_currentPlot,
            ui.DataAnalysis_Cycles_synapticPlot, ui.DataAnalysis_Cycles_ratePlot)


def sync_plot_x_range(plots, source, limits):
    # Copy data coordinates directly. A hidden plot can have stale screen geometry.
    for plot in plots:
        view = plot.getViewBox()
        if view is not source and tuple(view.viewRange()[0]) != tuple(limits):
            view.setXRange(*limits, padding=0)


def select_tab(window, index):
    window.ui.DataAnalysis_stack.setCurrentIndex(index)
    window.analysis_tabs.button(index).setChecked(True)


def sync_sweep_condition(window, text):
    sweeps = getattr(window, "analysis_sweep_view", None)
    if (sweeps is not None and sweeps.recording is getattr(window, "analysis_recording", None)
            and sweeps.form.conditionEdit.text() != text):
        sweeps.form.conditionEdit.setText(text)


def recording_trace_checks(ui):
    return (ui.DataAnalysis_stimulusCheck, ui.DataAnalysis_voltageCheck, ui.DataAnalysis_currentCheck,
            ui.DataAnalysis_synapticCheck, ui.DataAnalysis_rateCheck)


def set_recording_plot_visibility(window):
    ui = window.ui
    loaded = getattr(window, "analysis_recording", None) is not None
    main_neuron = ui.DataAnalysis_neuronCombo.currentIndex() == 0
    spikes_detected = getattr(window, "analysis_spikes", None) is not None
    available = (loaded, loaded, loaded, loaded and main_neuron, loaded and spikes_detected)
    plots = recording_plots(ui)
    bottom = None
    for plot, checkbox, enabled in zip(plots, recording_trace_checks(ui), available):
        checkbox.setEnabled(enabled)
        shown = checkbox.isChecked() and (enabled or (not loaded and plot in plots[:2]))
        plot.setVisible(shown)
        if shown:
            bottom = plot
    ui.Spikeling_DataAnalysis_SaveImage_pushButton.setEnabled(loaded and bottom is not None)
    for plot in plots:
        is_bottom = plot is bottom
        plot.setLabel("bottom", TIME_COLUMN if is_bottom else "")
        plot.getAxis("bottom").setStyle(showValues=is_bottom)


def set_trace_title(plot, text):
    plot.setTitle(escape(text), color=theme_manager.active_colour("text_primary"), size="9pt")
    plot.getPlotItem().layout.setRowFixedHeight(0, 22)


def plot_recorded(widget, recording, values, role):
    gaps = np.flatnonzero(recording.gap_before)
    theme_manager.themed_plot(
        widget, np.insert(recording.time_ms, gaps, np.nan),
        np.insert(values, gaps, np.nan), role, connect="finite",
    )


def stack_repetitions(time, rows):
    """Draw the repetitions as one plot item separated by NaN gaps."""
    flat_time = np.tile(np.append(time, np.nan), len(rows))
    flat_values = np.pad(rows, ((0, 0), (0, 1)), constant_values=np.nan).ravel()
    return flat_time, flat_values


def mean_trace(rows):
    finite = np.isfinite(rows)
    counts = finite.sum(axis=0)
    return np.divide(
        np.nansum(rows, axis=0), counts,
        out=np.full(rows.shape[1], np.nan), where=counts > 0,
    )


def plot_repetitions(widget, time, rows, role):
    x, y = stack_repetitions(time, rows)
    theme_manager.themed_plot(widget, x, y, "analysis_loop", connect="finite")
    theme_manager.themed_plot(
        widget, time, mean_trace(rows), role, width_scale=MEAN_WIDTH_SCALE, connect="finite",
    )


def show_error(ui, title, error):
    themed_message_box(ui.Spikeling_DataAnalysis_LoadData_label.window(), title, str(error)).exec()


def set_actions(window):
    ui = window.ui
    recording = getattr(window, "analysis_recording", None)
    loaded = recording is not None
    spikes = getattr(window, "analysis_spikes", None) is not None
    cycles = getattr(window, "analysis_cycles", None) is not None
    ui.DataAnalysis_metadataButton.setEnabled(loaded and recording.acquisition is not None)
    ui.DataAnalysis_staButton.setEnabled(loaded)
    ui.DataAnalysis_neuronCombo.setEnabled(loaded)
    ui.DataAnalysis_inputCombo.setEnabled(loaded)
    ui.DataAnalysis_conditionEdit.setEnabled(loaded)
    ui.Spikeling_DataAnalysis_Spike_lineEdit.setEnabled(loaded)
    ui.Spikeling_DataAnalysis_Spike_Display_pushButton.setEnabled(loaded)
    ui.Spikeling_DataAnalysis_Spike_Export_pushButton.setEnabled(spikes)
    ui.DataAnalysis_sweepModeCombo.setEnabled(loaded)
    ui.DataAnalysis_Cycles_calculateButton.setEnabled(loaded)
    ui.DataAnalysis_Cycles_neuronCombo.setEnabled(cycles)
    ui.DataAnalysis_Cycles_exportButton.setEnabled(cycles)


def cycle_trace_checks(ui):
    return (ui.DataAnalysis_Cycles_stimulusCheck, ui.DataAnalysis_Cycles_voltageCheck,
            ui.DataAnalysis_Cycles_currentCheck, ui.DataAnalysis_Cycles_synapticCheck,
            ui.DataAnalysis_Cycles_rateCheck)


def set_cycle_plot_visibility(window):
    ui = window.ui
    cycles = window.analysis_cycles
    stimulus, raster, voltage, current, synaptic, rate = cycle_plots(ui)
    ready = cycles is not None
    main_neuron = ui.DataAnalysis_Cycles_neuronCombo.currentIndex() == 0
    available = (ready, ready, ready, ready and main_neuron, ready and bool(rate.listDataItems()))
    for plot, checkbox, enabled in zip(
        (stimulus, voltage, current, synaptic, rate), cycle_trace_checks(ui), available,
    ):
        checkbox.setEnabled(enabled)
        plot.setVisible(enabled and checkbox.isChecked())
    raster.setVisible(ready and cycles.spike_times_ms is not None and not voltage.isHidden())

    plots = cycle_plots(ui)
    bottom = next((plot for plot in reversed(plots) if not plot.isHidden()), None)
    ui.DataAnalysis_Cycles_imageButton.setEnabled(bottom is not None)
    for plot in plots:
        is_bottom = plot is bottom
        plot.setLabel("bottom", "Time from trigger (ms)" if is_bottom else "")
        plot.getAxis("bottom").setStyle(showValues=is_bottom)


def clear_cycles(window):
    window.analysis_cycles = None
    window.ui.DataAnalysis_Cycles_summaryLabel.setText("Average stimulus cycles to view the aligned response.")
    for plot in cycle_plots(window.ui):
        plot.clear()
    set_cycle_plot_visibility(window)


def clear_results(window):
    window.analysis_spikes = None
    window.ui.Spikeling_DataAnalysis_Spike_result_label.clear()
    clear_cycles(window)
    set_actions(window)


def choose_export_folder(subfolder, caption):
    folder = QFileDialog.getExistingDirectory(
        caption=caption, dir=save_dialog_directory(recordings_directory() / subfolder),
    )
    return Path(folder) if folder else None


class Spikeling103:
    def ShowPage(self):
        ui = self.ui
        if not hasattr(self, "analysis_tabs"):
            Spikeling103.ConfigurePage(self)
        ui.mainbody_stackedWidget.setCurrentWidget(ui.page_Spikeling_DataAnalysis)

    def ConfigurePage(self):
        ui = self.ui
        self.analysis_tabs = QButtonGroup(ui.page_Spikeling_DataAnalysis)
        self.analysis_tabs.setExclusive(True)
        for index, button in enumerate((ui.DataAnalysis_navRecording, ui.DataAnalysis_navSweeps,
                                        ui.DataAnalysis_navCompare)):
            self.analysis_tabs.addButton(button, index)
        self.analysis_tabs.idClicked.connect(lambda index: Spikeling103.OpenTab(self, index))
        ui.Spikeling_DataAnalysis_LoadData_pushButton.clicked.connect(lambda: Spikeling103.LoadData(self))
        ui.Spikeling_DataAnalysis_Spike_Display_pushButton.clicked.connect(lambda: Spikeling103.FindSpike(self))
        ui.Spikeling_DataAnalysis_Spike_lineEdit.textChanged.connect(lambda: Spikeling103.InvalidateSpikeAnalysis(self))
        ui.Spikeling_DataAnalysis_Spike_Export_pushButton.clicked.connect(lambda: Spikeling103.SaveSpikeTraces(self))
        ui.Spikeling_DataAnalysis_SaveImage_pushButton.clicked.connect(lambda: Spikeling103.SaveRawDataImage(self))
        ui.DataAnalysis_neuronCombo.currentIndexChanged.connect(lambda: Spikeling103.DisplayRawData(self))
        ui.DataAnalysis_inputCombo.currentIndexChanged.connect(lambda: Spikeling103.DisplayRawData(self))
        ui.DataAnalysis_inputCombo.setToolTip("A recorded clamp command is from the main neuron.")
        for checkbox in recording_trace_checks(ui):
            checkbox.toggled.connect(lambda: Spikeling103.DisplayRawData(self))
        ui.DataAnalysis_conditionEdit.textChanged.connect(lambda text: sync_sweep_condition(self, text))
        ui.DataAnalysis_staButton.clicked.connect(lambda: Spikeling103.ShowSTA(self))
        ui.DataAnalysis_STA_backButton.clicked.connect(
            lambda: ui.DataAnalysis_recordingStack.setCurrentWidget(ui.DataAnalysis_recordingOverview)
        )
        ui.DataAnalysis_Summary_backButton.clicked.connect(
            lambda: ui.DataAnalysis_sweepStack.setCurrentWidget(ui.DataAnalysis_stepPage)
        )
        ui.DataAnalysis_Timing_backButton.clicked.connect(
            lambda: select_tab(self, self.analysis_timing_origin)
        )
        ui.DataAnalysis_metadataButton.clicked.connect(lambda: Spikeling103.ShowMetadata(self))
        ui.DataAnalysis_metadataBack.clicked.connect(
            lambda: ui.DataAnalysis_recordingStack.setCurrentWidget(ui.DataAnalysis_recordingOverview)
        )
        ui.DataAnalysis_sweepModeCombo.currentIndexChanged.connect(lambda index: Spikeling103.SwitchSweepMode(self, index))
        ui.DataAnalysis_Cycles_calculateButton.clicked.connect(lambda: Spikeling103.AverageTraces(self))
        ui.DataAnalysis_Cycles_neuronCombo.currentIndexChanged.connect(lambda: Spikeling103.DisplayCycles(self))
        for checkbox in cycle_trace_checks(ui):
            checkbox.toggled.connect(lambda: set_cycle_plot_visibility(self))
        ui.DataAnalysis_Cycles_exportButton.clicked.connect(lambda: Spikeling103.SaveAverageTraces(self))
        ui.DataAnalysis_Cycles_imageButton.clicked.connect(lambda: Spikeling103.SaveAverageImage(self))
        for widget in (*recording_plots(ui), *cycle_plots(ui)):
            theme_manager.set_plot_background_role(widget, "panel_background")
        aligned_plots = cycle_plots(ui)
        for widget in aligned_plots:
            widget.showGrid(x=True, y=widget is not ui.DataAnalysis_Cycles_rasterPlot, alpha=.23)
            widget.getAxis("left").setWidth(25)
            view = widget.getViewBox()
            view.enableAutoRange(axis="x", enable=False)
            view.sigXRangeChanged.connect(
                lambda source, limits: sync_plot_x_range(aligned_plots, source, limits)
            )
        clear_cycles(self)
        for widget in recording_plots(ui):
            widget.showGrid(x=True, y=True, alpha=.23)
            widget.getAxis("left").setWidth(25)
            widget.setDownsampling(auto=True, mode="peak")
            if widget is not ui.DataAnalysis_voltagePlot:
                widget.setXLink(ui.DataAnalysis_voltagePlot)
        theme_manager.themeChanged.connect(lambda *_: Spikeling103.RefreshTheme(self))
        Spikeling103.RefreshTheme(self)
        set_actions(self)
        set_recording_plot_visibility(self)
        index = ui.DataAnalysis_stack.currentIndex()
        Spikeling103.OpenTab(self, index if self.analysis_tabs.button(index) is not None else 0)

    def RefreshTheme(self):
        ui = self.ui
        colour = theme_manager.active_colour
        window, panel_bg, surface, text, muted, accent = [
            colour(role) for role in ("window_background", "panel_background", "surface",
                                     "text_primary", "text_muted", "neuron_stimulus")
        ]
        ui.page_Spikeling_DataAnalysis.setStyleSheet(f"""
            QWidget#page_Spikeling_DataAnalysis {{background:{window};color:{text};}}
            QLabel#DataAnalysis_Compare_tracesHeading, QLabel#DataAnalysis_Compare_expandedHeading,
            QLabel#DataAnalysis_Compare_measurementsHeading,
            QLabel#DataAnalysis_Timing_heading {{font-size:12pt;font-weight:700;}}
            QLabel#DataAnalysis_Timing_plotHeading1, QLabel#DataAnalysis_Timing_plotHeading2,
            QLabel#DataAnalysis_Timing_plotHeading3, QLabel#DataAnalysis_Timing_plotHeading4 {{font-weight:700;}}
            QLabel#DataAnalysis_Timing_contextLabel {{color:{muted};}}
            QFrame#DataAnalysis_Compare_tracesPane, QFrame#DataAnalysis_Compare_expandedPlots,
            QFrame#DataAnalysis_Compare_measurementsPane, QFrame#DataAnalysis_Timing_plotPanel1,
            QFrame#DataAnalysis_Timing_plotPanel2, QFrame#DataAnalysis_Timing_plotPanel3,
            QFrame#DataAnalysis_Timing_plotPanel4 {{
                background:{panel_bg};border:1px solid {surface};border-radius:8px;
            }}
            QWidget#DataAnalysis_comparePage QPushButton, QWidget#DataAnalysis_Compare_expandedPage QPushButton,
            QWidget#DataAnalysis_timingPage QPushButton {{
                background:{surface};color:{text};border:1px solid {muted};
                border-radius:5px;padding:5px 9px;
            }}
            QWidget#DataAnalysis_comparePage QPushButton:hover,
            QWidget#DataAnalysis_Compare_expandedPage QPushButton:hover,
            QWidget#DataAnalysis_timingPage QPushButton:hover {{border-color:{accent};}}
            QWidget#DataAnalysis_comparePage QPushButton:focus,
            QWidget#DataAnalysis_Compare_expandedPage QPushButton:focus,
            QWidget#DataAnalysis_timingPage QPushButton:focus {{border:2px solid {accent};}}
            QWidget#DataAnalysis_comparePage QPushButton:disabled,
            QWidget#DataAnalysis_timingPage QPushButton:disabled {{
                color:{muted};border-color:{surface};
            }}
            QWidget#DataAnalysis_comparePage QLineEdit,
            QWidget#DataAnalysis_comparePage QComboBox, QWidget#DataAnalysis_timingPage QLineEdit,
            QWidget#DataAnalysis_timingPage QComboBox {{
                background:{surface};color:{text};border:1px solid {muted};
                border-radius:5px;padding:4px 7px;
            }}
            QWidget#DataAnalysis_comparePage QLineEdit:focus,
            QWidget#DataAnalysis_comparePage QComboBox:focus, QWidget#DataAnalysis_timingPage QLineEdit:focus,
            QWidget#DataAnalysis_timingPage QComboBox:focus {{border:2px solid {accent};}}
            QPushButton#DataAnalysis_navRecording, QPushButton#DataAnalysis_navSweeps,
            QPushButton#DataAnalysis_navCompare {{
                color:{muted};background:transparent;border:0;border-bottom:2px solid transparent;
                padding:7px 14px;
            }}
            QPushButton#DataAnalysis_navRecording:checked, QPushButton#DataAnalysis_navSweeps:checked,
            QPushButton#DataAnalysis_navCompare:checked {{
                color:{accent};border-bottom:2px solid {accent};
            }}
            QPushButton#DataAnalysis_navRecording:focus, QPushButton#DataAnalysis_navSweeps:focus,
            QPushButton#DataAnalysis_navCompare:focus {{background:{surface};}}
        """)
        for plot in (*recording_plots(ui), *cycle_plots(ui)):
            title = plot.getPlotItem().titleLabel
            title.setText(title.text, color=text)
        threshold = getattr(self, "analysis_threshold_line", None)
        if threshold is not None:
            threshold.setPen(pg.mkPen(muted, style=Qt.PenStyle.DashLine))
        theme_manager.style_traces()

    def OpenTab(self, index):
        ui = self.ui
        select_tab(self, index)
        if index == 1:
            Spikeling103.SwitchSweepMode(self, ui.DataAnalysis_sweepModeCombo.currentIndex())
        elif index == 2:
            Spikeling103.ShowCompare(self)

    def ShowSTA(self):
        recording = getattr(self, "analysis_recording", None)
        if recording is None:
            return
        if not hasattr(self, "analysis_sta_view"):
            from .sta_view import SpikeTriggeredAverageView

            self.analysis_sta_view = SpikeTriggeredAverageView(self)
        self.analysis_sta_view.load(recording)
        select_tab(self, 0)
        self.ui.DataAnalysis_recordingStack.setCurrentWidget(self.ui.DataAnalysis_staPage)

    def ShowSpikeTiming(self, groups, neuron, threshold, origin, context):
        if not hasattr(self, "analysis_timing_view"):
            from .timing_view import SpikeTimingView

            self.analysis_timing_view = SpikeTimingView(self)
        self.analysis_timing_origin = origin
        self.analysis_tabs.button(origin).setChecked(True)
        self.ui.DataAnalysis_stack.setCurrentWidget(self.ui.DataAnalysis_timingPage)
        self.analysis_timing_view.load(groups, neuron, threshold, context)

    def ShowMetadata(self):
        recording = getattr(self, "analysis_recording", None)
        if recording is not None and recording.acquisition is not None:
            self.ui.DataAnalysis_metadataText.setPlainText(
                json.dumps(recording.acquisition, ensure_ascii=False, indent=2)
            )
            self.ui.DataAnalysis_recordingStack.setCurrentWidget(self.ui.DataAnalysis_metadataPage)

    def ShowCompare(self):
        select_tab(self, 2)
        if not hasattr(self, "analysis_compare_view"):
            from .compare_view import CompareView

            self.analysis_compare_view = CompareView(self)

    def SwitchSweepMode(self, index):
        ui = self.ui
        if getattr(self, "analysis_recording", None) is None:
            ui.DataAnalysis_sweepStack.setCurrentWidget(ui.DataAnalysis_sweepsEmpty)
        elif index == STEP_MODE_INDEX:
            Spikeling103.ShowSweeps(self)
        else:
            ui.DataAnalysis_sweepStack.setCurrentWidget(ui.DataAnalysis_cyclePage)
        set_actions(self)

    def ShowSweeps(self):
        select_tab(self, 1)
        ui = self.ui
        recording = getattr(self, "analysis_recording", None)
        if recording is None:
            return
        if not hasattr(self, "analysis_sweep_view"):
            from .sweep_view import SweepView

            self.analysis_sweep_view = SweepView(self)
            self.analysis_sweep_view.form.conditionEdit.textEdited.connect(ui.DataAnalysis_conditionEdit.setText)
        with QSignalBlocker(ui.DataAnalysis_sweepModeCombo):
            ui.DataAnalysis_sweepModeCombo.setCurrentIndex(STEP_MODE_INDEX)
        sweeps = self.analysis_sweep_view
        ui.DataAnalysis_sweepStack.setCurrentWidget(sweeps.widget)
        sweeps.load(recording)
        label = ui.DataAnalysis_conditionEdit.text()
        if sweeps.form.conditionEdit.text() != label:
            sweeps.form.conditionEdit.setText(label)
        set_actions(self)

    def LoadData(self):
        ui = self.ui
        filename, _ = QFileDialog.getOpenFileName(
            caption="Select recording file to load",
            dir=save_dialog_directory(recordings_directory()),
            filter="CSV files (*.csv)",
        )
        if not filename:
            return
        try:
            recording = load_recording(filename)
        except (OSError, ValueError) as error:
            show_error(ui, "Cannot load recording", error)
            return

        for index, checkbox in enumerate(recording_trace_checks(ui)):
            with QSignalBlocker(checkbox):
                checkbox.setChecked(index < 2)
        self.analysis_recording = recording
        clear_results(self)
        ui.DataAnalysis_conditionEdit.clear()
        ui.DataAnalysis_metadataText.clear()
        gap_count = int(recording.gap_before.sum())
        summary = f"{recording.source.name} · {recording.clamp_mode}"
        if gap_count:
            summary += f" · {gap_count} time gaps"
        detail = "Recorded CSV time"
        if recording.acquisition is not None:
            metadata = recording.acquisition
            summary += f" · {metadata['source']}"
            kind = metadata["timebase"]["kind"]
            detail = {"nominal_sample_index": "Nominal model time",
                      "emulator_integration_step": "Emulator integration time"}.get(kind, kind)
        elif recording.acquisition_warning:
            summary += " · metadata ignored"
        ui.Spikeling_DataAnalysis_LoadData_label.setText(summary)
        ui.Spikeling_DataAnalysis_LoadData_label.setToolTip(
            f"{recording.source}\n{recording.acquisition_warning or detail}"
        )
        combo = ui.DataAnalysis_inputCombo
        command = "command_voltage" if recording.clamp_mode == "VC" else "command_current"

        with QSignalBlocker(combo):
            selected_index = 0
            for index, key in enumerate(("command_current", "command_voltage"), start=1):
                combo.setItemData(index, key)
                available = key == command and key in recording.extra_channels
                combo.model().item(index).setEnabled(available)
                if available:
                    selected_index = index

            combo.setCurrentIndex(selected_index)

        select_tab(self, 0)
        ui.DataAnalysis_recordingStack.setCurrentWidget(ui.DataAnalysis_recordingOverview)
        Spikeling103.DisplayRawData(self)
        time = recording.time_ms
        ui.DataAnalysis_voltagePlot.setXRange(time[0], time[-1], padding=.015)

    def DisplayRawData(self):
        recording = getattr(self, "analysis_recording", None)
        if recording is None:
            return
        ui = self.ui
        neuron = ui.DataAnalysis_neuronCombo.currentIndex()
        key = ui.DataAnalysis_inputCombo.currentData()
        spikes = getattr(self, "analysis_spikes", None)
        set_recording_plot_visibility(self)
        for widget in recording_plots(ui):
            widget.clear()
            widget.enableAutoRange(axis="y")
        self.analysis_threshold_line = None
        stimulus = recording.extra_channels[key] if key else recording.stimulus
        voltage = recording.voltage[neuron]
        set_trace_title(ui.DataAnalysis_inputPlot, ui.DataAnalysis_inputCombo.currentText())
        set_trace_title(ui.DataAnalysis_voltagePlot, "Membrane voltage (mV)")
        plot_recorded(ui.DataAnalysis_inputPlot, recording, stimulus, "neuron_stimulus")
        plot_recorded(ui.DataAnalysis_voltagePlot, recording, voltage, VOLTAGE_ROLES[neuron])
        if not ui.DataAnalysis_currentPlot.isHidden():
            set_trace_title(ui.DataAnalysis_currentPlot, recording.current_columns[neuron])
            plot_recorded(ui.DataAnalysis_currentPlot, recording, recording.current[neuron], CURRENT_ROLES[neuron])
        if not ui.DataAnalysis_synapticPlot.isHidden():
            unit = "nA" if recording.clamp_mode == "VC" else "a.u."
            set_trace_title(ui.DataAnalysis_synapticPlot, f"Synaptic input ({unit})")
            for aux in (1, 2):
                plot_recorded(ui.DataAnalysis_synapticPlot, recording, recording.current[aux], CURRENT_ROLES[aux])
        if not ui.DataAnalysis_ratePlot.isHidden():
            set_trace_title(ui.DataAnalysis_ratePlot, "Instantaneous rate (Hz)")
            plot_recorded(ui.DataAnalysis_ratePlot, recording, spikes.rates_hz[neuron], "analysis_spike_rate")
        if spikes is None:
            ui.Spikeling_DataAnalysis_Spike_result_label.setText("Spikes not detected")
        else:
            events = spikes.indices[neuron]
            colour = theme_manager.active_colour("text_muted")
            line = pg.InfiniteLine(pos=spikes.threshold_mv, angle=0,
                                   pen=pg.mkPen(colour, style=Qt.PenStyle.DashLine))
            ui.DataAnalysis_voltagePlot.addItem(line, ignoreBounds=True)
            self.analysis_threshold_line = line
            if events.size:
                marker_height = np.nanmax(voltage) + 8.0
                theme_manager.themed_plot(
                    ui.DataAnalysis_voltagePlot, recording.time_ms[events],
                    np.full(events.shape, marker_height), "analysis_spike_rate",
                    symbol="o", symbol_size=4,
                )
            ui.Spikeling_DataAnalysis_Spike_result_label.setText(f"Detected spikes: {len(events)}")
        theme_manager.style_traces()

    def InvalidateSpikeAnalysis(self):
        if getattr(self, "analysis_spikes", None) is not None:
            clear_results(self)
            Spikeling103.DisplayRawData(self)

    def FindSpike(self):
        recording = getattr(self, "analysis_recording", None)
        if recording is None:
            return
        ui = self.ui
        try:
            threshold = float(ui.Spikeling_DataAnalysis_Spike_lineEdit.text())
            spikes = detect_spikes(recording, threshold)
        except ValueError:
            show_error(ui, "Invalid spike threshold", "Enter a finite voltage threshold in mV.")
            return
        self.analysis_spikes = spikes
        clear_cycles(self)
        set_actions(self)
        Spikeling103.DisplayRawData(self)

    def AverageTraces(self):
        recording = getattr(self, "analysis_recording", None)
        if recording is None:
            return
        ui = self.ui
        select_tab(self, 1)
        with QSignalBlocker(ui.DataAnalysis_sweepModeCombo):
            ui.DataAnalysis_sweepModeCombo.setCurrentIndex(CYCLE_MODE_INDEX)
        ui.DataAnalysis_sweepStack.setCurrentWidget(ui.DataAnalysis_cyclePage)
        clear_cycles(self)
        try:
            self.analysis_cycles = align_cycles(recording, getattr(self, "analysis_spikes", None))
        except ValueError as error:
            ui.DataAnalysis_Cycles_summaryLabel.setText(str(error))
            set_actions(self)
            return
        Spikeling103.DisplayCycles(self, reset_range=True)
        set_actions(self)

    def DisplayCycles(self, reset_range=False):
        cycles = getattr(self, "analysis_cycles", None)
        if cycles is None:
            return
        ui = self.ui
        recording = self.analysis_recording
        neuron = ui.DataAnalysis_Cycles_neuronCombo.currentIndex()
        stimulus, raster, voltage, current, synaptic, rate = cycle_plots(ui)
        summary = f"{len(cycles.starts_ms)} cycles · {cycles.duration_ms:g} ms"
        if cycles.protocol_aligned:
            summary += " · verified custom stimulus timing"
        if cycles.excluded:
            summary += f" · {cycles.excluded} incomplete or irregular"
        mean_rate = None if cycles.rates_hz is None else mean_trace(cycles.rates_hz[neuron])
        show_rate = mean_rate is not None and bool(np.isfinite(mean_rate).any())
        if mean_rate is None:
            summary += " · Detect spikes in Recording, then average cycles again to show spike rate."
        elif not show_rate:
            summary += " · No usable interspike intervals for this neuron."
        ui.DataAnalysis_Cycles_summaryLabel.setText(summary)
        synaptic_unit = "nA" if recording.clamp_mode == "VC" else "a.u."
        for plot, label in zip(
            cycle_plots(ui),
            (STIMULUS_COLUMN, "Sweep", "Membrane voltage (mV)", recording.current_columns[neuron],
             f"Synaptic input ({synaptic_unit})", "Mean spike rate (Hz)"),
        ):
            plot.clear()
            set_trace_title(plot, label)
            plot.enableAutoRange(axis="y")
        plot_repetitions(stimulus, cycles.time_ms, cycles.stimulus, "neuron_stimulus")
        if cycles.spike_times_ms is not None:
            sweeps = cycles.spike_times_ms[neuron]
            times = np.concatenate(sweeps)
            rows = np.repeat(np.arange(1, len(sweeps) + 1), [len(sweep) for sweep in sweeps])
            raster.plot(
                times, rows, pen=None, symbol="o", symbolSize=3,
                symbolBrush="w", symbolPen=None,
            )
        raster.setYRange(0.5, len(cycles.starts_ms) + 0.5, padding=0)
        plot_repetitions(voltage, cycles.time_ms, cycles.voltage[neuron], VOLTAGE_ROLES[neuron])
        plot_repetitions(current, cycles.time_ms, cycles.current[neuron], CURRENT_ROLES[neuron])
        if neuron == 0:
            for aux in (1, 2):
                plot_repetitions(synaptic, cycles.time_ms, cycles.current[aux], CURRENT_ROLES[aux])
        if show_rate:
            theme_manager.themed_plot(
                rate, cycles.time_ms, mean_rate, "analysis_spike_rate",
                width_scale=MEAN_WIDTH_SCALE, connect="finite",
            )
        set_cycle_plot_visibility(self)
        if reset_range:
            sync_plot_x_range(cycle_plots(ui), None, (0, cycles.duration_ms))
        theme_manager.style_traces()

    def SaveRawDataImage(self):
        if getattr(self, "analysis_recording", None) is None:
            return
        ui = self.ui
        neuron = ui.DataAnalysis_neuronCombo.currentIndex()
        folder = choose_export_folder("Graphs", "Select folder to save visible recording plots")
        if folder is None:
            return
        channel = ui.DataAnalysis_inputCombo.currentData()
        input_label = {"command_current": "Command current", "command_voltage": "Command voltage"}.get(channel, "Stimulus")
        labels = (input_label, "Vm", "Current", "Synaptic input", "Spike rate")
        try:
            for plot, label in zip(recording_plots(ui), labels):
                if not plot.isHidden():
                    ImageExporter(plot.plotItem).export(str(folder / f"{NEURON_NAMES[neuron]} {label}.png"))
        except (OSError, RuntimeError, ValueError) as error:
            show_error(ui, "Cannot export graphs", error)

    def SaveAverageImage(self):
        if getattr(self, "analysis_cycles", None) is None:
            return
        folder = choose_export_folder("Graphs", "Select folder to save aligned cycle plots")
        if folder is None:
            return
        ui = self.ui
        prefix = NEURON_NAMES[ui.DataAnalysis_Cycles_neuronCombo.currentIndex()]
        try:
            labels = ("Aligned stimulus", "Raster", "Aligned Vm", "Aligned current",
                      "Aligned synaptic input", "Mean spike rate")
            for plot, label in zip(cycle_plots(ui), labels):
                if not plot.isHidden():
                    ImageExporter(plot.plotItem).export(str(folder / f"{prefix} {label}.png"))
        except (OSError, RuntimeError, ValueError) as error:
            show_error(ui, "Cannot export graphs", error)

    def SaveSpikeTraces(self):
        ui = self.ui
        neuron = ui.DataAnalysis_neuronCombo.currentIndex()
        spikes = getattr(self, "analysis_spikes", None)
        if spikes is None:
            return
        folder = choose_export_folder("Data", "Save spike data")
        if folder is None:
            return
        recording = self.analysis_recording
        prefix = NEURON_NAMES[neuron]
        metadata = {**recording.metadata(), "Neuron": prefix, "Threshold (mV)": spikes.threshold_mv,
                    "Condition": ui.DataAnalysis_conditionEdit.text().strip()}
        events = spikes.indices[neuron]
        try:
            pd.DataFrame({
                **metadata, TIME_COLUMN: recording.time_ms[events],
                VOLTAGE_COLUMNS[neuron]: recording.voltage[neuron][events],
            }).to_csv(folder / f"{prefix}_spike.csv", index=False)
            pd.DataFrame({
                **metadata, TIME_COLUMN: recording.time_ms,
                "Instantaneous spike rate (Hz)": spikes.rates_hz[neuron],
            }).to_csv(folder / f"{prefix}_spikerate.csv", index=False)
        except (OSError, ValueError) as error:
            show_error(ui, "Cannot export spike data", error)

    def SaveAverageTraces(self):
        ui = self.ui
        neuron = ui.DataAnalysis_Cycles_neuronCombo.currentIndex()
        cycles = getattr(self, "analysis_cycles", None)
        if cycles is None:
            return
        folder = choose_export_folder("Data", "Save aligned cycles")
        if folder is None:
            return
        recording = self.analysis_recording
        prefix = NEURON_NAMES[neuron]
        metadata = {**recording.metadata(), "Neuron": prefix}
        means = {
            **metadata, "Time from trigger (ms)": cycles.time_ms,
            "Cycles included": len(cycles.starts_ms),
            STIMULUS_COLUMN: mean_trace(cycles.stimulus),
            VOLTAGE_COLUMNS[neuron]: mean_trace(cycles.voltage[neuron]),
            recording.current_columns[neuron]: mean_trace(cycles.current[neuron]),
        }
        if cycles.rates_hz is not None:
            means["Mean instantaneous spike rate (Hz)"] = mean_trace(cycles.rates_hz[neuron])
            means["Threshold (mV)"] = self.analysis_spikes.threshold_mv
        try:
            pd.DataFrame(means).to_csv(folder / f"{prefix}_means.csv", index=False)
            pd.DataFrame({
                **metadata, "Sweep": np.arange(1, len(cycles.starts_ms) + 1),
                "Trigger time (ms)": cycles.starts_ms, "Cycle duration (ms)": cycles.duration_ms,
            }).to_csv(folder / f"{prefix}_cycles.csv", index=False)
            if cycles.spike_times_ms is not None:
                sweeps = cycles.spike_times_ms[neuron]
                pd.DataFrame({
                    **metadata, "Threshold (mV)": self.analysis_spikes.threshold_mv,
                    "Sweep": np.repeat(np.arange(1, len(sweeps) + 1), [len(sweep) for sweep in sweeps]),
                    "Time from trigger (ms)": np.concatenate(sweeps),
                }).to_csv(folder / f"{prefix}_rasterplot.csv", index=False)
        except (OSError, ValueError) as error:
            show_error(ui, "Cannot export aligned cycles", error)
