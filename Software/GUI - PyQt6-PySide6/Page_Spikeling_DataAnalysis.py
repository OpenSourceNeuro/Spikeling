########################################################################
#                          Libraries import                            #

from PySide6.QtWidgets import QFileDialog
import pyqtgraph as pg
import pyqtgraph.exporters

import numpy as np
import pandas as pd

import Parameters_Settings as Settings
from theme_manager import theme_manager


# =============================================================================
# Panel layout
# =============================================================================
# Oscilloscope widgets per stacked page, as (page, row) -> column count. Used
# to tag every canvas with its background role without hard-coding 36 names.
ANALYSIS_WIDGET_LAYOUT = {1: (4, 3, 3), 2: (4, 4, 4), 3: (4, 4, 4)}

# Analysis canvases keep the lighter panel colour that visually separates them
# from the live oscilloscopes; the role is resolved per theme, not frozen.
ANALYSIS_BACKGROUND_ROLE = "panel_background"

SAMPLES_PER_MS = 10.0

# Per-neuron signal mapping. ``vm`` and ``current`` name the ``df_DataAnalysis``
# arrays prepared by DisplayRawData; the roles are the *same* ones driving the
# live scopes, so a recorded trace keeps the colour it was acquired with.
NEURON_PANELS = (
    {"vm": "y0", "vm_role": "neuron_vm",
     "current": "y1", "current_role": "neuron_current",
     "rate": "spike_rate0", "marks": "spike_points0Plot"},
    {"vm": "y3", "vm_role": "neuron_syn1_vm",
     "current": "y4", "current_role": "neuron_syn1_input",
     "rate": "spike_rate1", "marks": "spike_points1Plot"},
    {"vm": "y5", "vm_role": "neuron_syn2_vm",
     "current": "y6", "current_role": "neuron_syn2_input",
     "rate": "spike_rate2", "marks": "spike_points2Plot"},
)

# Raw-data page: (widget suffix, ((array, role), ...), left label, bottom label)
RAW_PANELS = (
    ("1_0_0", (("y0", "neuron_vm"),), "Membrane Voltage (mV)", None),
    ("1_0_1", (("y1", "neuron_current"),), "Input Current (a.u.)", None),
    ("1_0_2", (("y2", "neuron_stimulus"),), "Intensity", None),
    ("1_0_3", (("y6", "neuron_syn2_input"), ("y4", "neuron_syn1_input")),
     "Synaptic Current (a.u.)", "Time (ms)"),

    ("1_1_0", (("y3", "neuron_syn1_vm"),), "Membrane Voltage (mV)", None),
    ("1_1_1", (("y4", "neuron_syn1_input"),), "Synaptic Input (a.u.)", None),
    ("1_1_2", (("y2", "neuron_stimulus"),), "Intensity", "Time (ms)"),

    ("1_2_0", (("y5", "neuron_syn2_vm"),), "Membrane Voltage (mV)", None),
    ("1_2_1", (("y6", "neuron_syn2_input"),), "Synaptic Input (a.u.)", None),
    ("1_2_2", (("y2", "neuron_stimulus"),), "Intensity", "Time (ms)"),
)

# Mean traces are drawn at this multiple of the global trace width, so they
# stay readable on top of the repetitions whatever thickness the user picks.
MEAN_WIDTH_SCALE = 2.0
RASTER_SYMBOL_SIZE = 5


def analysis_plot_widgets(ui):
    """
    Yield every data-analysis oscilloscope widget present on the UI.

    Parameters
    ----------
    ui : object
        Generated Qt UI object.

    Yields
    ------
    pyqtgraph.PlotWidget
        Existing analysis canvases, skipping any the UI file does not define.
    """
    for page, column_counts in ANALYSIS_WIDGET_LAYOUT.items():
        for row, count in enumerate(column_counts):
            for column in range(count):
                name = f"Spikeling_DataAnalysis_Oscilloscope_widget{page}_{row}_{column}"
                widget = getattr(ui, name, None)
                if widget is not None:
                    yield widget


def prepare_panel(ui, suffix, left_label=None, bottom_label=None, show_y_grid=True):
    """
    Clear one analysis canvas and apply its axes and grid.

    Parameters
    ----------
    ui : object
        Generated Qt UI object.
    suffix : str
        Widget suffix, e.g. ``'2_1_3'``.
    left_label, bottom_label : str, optional
        Axis labels; the bottom tick values are hidden when no bottom label is
        given, which is what stacks the panels into one shared time axis.
    show_y_grid : bool, optional
        Disabled for raster panels, where horizontal rules compete with the
        spike rows.

    Returns
    -------
    pyqtgraph.PlotWidget or None
        The prepared widget, or ``None`` when the UI has no such panel.
    """
    widget = getattr(ui, f"Spikeling_DataAnalysis_Oscilloscope_widget{suffix}", None)
    if widget is None:
        return None

    widget.clear()
    widget.showGrid(x=True, y=show_y_grid)
    widget.getAxis("bottom").setStyle(showValues=bottom_label is not None)

    if left_label:
        widget.setLabel("left", left_label)
    if bottom_label:
        widget.setLabel("bottom", bottom_label)
    return widget


def stack_repetitions(x, rows):
    """
    Flatten stimulus repetitions into one NaN-separated polyline.

    Drawing N repetitions as N separate curves costs N scene-graph items and N
    theme updates. A single item carrying ``NaN`` breaks renders identically
    with ``connect='finite'`` and collapses a 100-loop overlay to one item.

    Parameters
    ----------
    x : numpy.ndarray
        Shared time axis of length ``n``.
    rows : numpy.ndarray
        Repetitions of shape ``(n_loops, n)``.

    Returns
    -------
    x_flat, y_flat : numpy.ndarray
        Coordinates to pass with ``connect='finite'``.
    """
    rows = np.asarray(rows, dtype=float)
    if rows.ndim != 2 or rows.size == 0:
        return np.empty(0), np.empty(0)

    gap = np.full((rows.shape[0], 1), np.nan)
    y_flat = np.concatenate([rows, gap], axis=1).ravel()
    x_flat = np.tile(np.append(np.asarray(x, dtype=float), np.nan), rows.shape[0])
    return x_flat, y_flat


def flatten_raster(loops):
    """
    Flatten per-loop spike times into scatter coordinates.

    Parameters
    ----------
    loops : sequence of sequence of float
        Spike times, one list per repetition.

    Returns
    -------
    times, rows : numpy.ndarray
        Spike time and repetition index of every event.
    """
    times, rows = [], []
    for index, spikes in enumerate(loops):
        if not len(spikes):
            continue
        times.extend(float(t) for t in spikes)
        rows.extend([index] * len(spikes))
    return np.asarray(times, dtype=float), np.asarray(rows, dtype=float)


class Spikeling103():

    def ShowPage(self):
        """
        Display the data-analysis page and bind its canvases to the theme.

        The background colour is applied through
        :meth:`theme_manager.ThemeManager.set_plot_background_role` rather than
        ``setBackground``, so the panels follow later theme changes instead of
        freezing the colour that happened to be active on first display.
        """
        self.ui.mainbody_stackedWidget.setCurrentWidget(self.ui.page_103)
        self.ui.Spikeling_DataAnalysis_Display_StackedWidget.setCurrentWidget(
            self.ui.page_103_1_0)

        for widget in analysis_plot_widgets(self.ui):
            theme_manager.set_plot_background_role(widget, ANALYSIS_BACKGROUND_ROLE)

        theme_manager.style_traces()

    # -------------------------------------------------------------------------
    # Raw data
    # -------------------------------------------------------------------------

    def DisplayRawData(self):
        """
        Plot the loaded recording across the three raw-data panels.

        Each trace is drawn with the *same* theme role as its live counterpart,
        so a recording is visually continuous with the oscilloscope it came
        from. The synapse 2 current previously used an unrelated palette slot
        and no longer does.
        """
        ui = self.ui
        ui.Spikeling_DataAnalysis_Display_StackedWidget.setCurrentWidget(ui.page_103_1_0)

        ui.df_DataAnalysis_x = ui.df_DataAnalysis_Timing
        ui.df_DataAnalysis_y0 = ui.df_DataAnalysis_Vm
        ui.df_DataAnalysis_y1 = ui.df_DataAnalysis_ITotal
        ui.df_DataAnalysis_y2 = ui.df_DataAnalysis_Stimulus
        ui.df_DataAnalysis_y3 = ui.df_DataAnalysis_Synapse1Vm
        ui.df_DataAnalysis_y4 = ui.df_DataAnalysis_Synapse1Input
        ui.df_DataAnalysis_y5 = ui.df_DataAnalysis_Synapse2Vm
        ui.df_DataAnalysis_y6 = ui.df_DataAnalysis_Synapse2Input

        x = ui.df_DataAnalysis_x

        for suffix, traces, left_label, bottom_label in RAW_PANELS:
            widget = prepare_panel(ui, suffix, left_label, bottom_label)
            if widget is None:
                continue
            for array_name, role in traces:
                theme_manager.themed_plot(
                    widget, x, getattr(ui, f"df_DataAnalysis_{array_name}"), role)

        ui.Spikeling_DataAnalysis_Spike_lineEdit.setEnabled(True)
        ui.Spikeling_DataAnalysis_Spike_Display_pushButton.setEnabled(True)

        theme_manager.style_traces()

    # -------------------------------------------------------------------------
    # Spike detection
    # -------------------------------------------------------------------------

    def FindSpike(self):
        """
        Detect spikes on the three neurons and plot rate, Vm and markers.

        Detection is an upward threshold crossing on each membrane potential,
        and the instantaneous rate is the reciprocal of the interval to the
        next spike, held until that spike occurs.

        Notes
        -----
        The synapse 2 panel previously plotted the synapse 1 membrane
        potential; it now shows its own trace.
        """
        ui = self.ui
        ui.Spikeling_DataAnalysis_Display_StackedWidget.setCurrentWidget(ui.page_103_2_0)

        threshold = float(ui.Spikeling_DataAnalysis_Spike_lineEdit.text())
        x = np.asarray(ui.df_DataAnalysis_x, dtype=float)

        self.spike_points0, self.spike_points1, self.spike_points2 = [], [], []
        spike_lists = (self.spike_points0, self.spike_points1, self.spike_points2)

        for neuron, panel in enumerate(NEURON_PANELS):
            trace = np.asarray(getattr(ui, f"df_DataAnalysis_{panel['vm']}"), dtype=float)
            crossings = np.flatnonzero((trace[1:] > threshold) & (trace[:-1] <= threshold)) + 1
            spike_lists[neuron].extend(int(index) for index in crossings)

            rate = np.zeros(trace.size, dtype=float)
            for start, stop in zip(crossings[:-1], crossings[1:]):
                rate[start:stop] = SAMPLES_PER_MS * 1000.0 / (stop - start)
            setattr(ui, panel["rate"], rate)
            setattr(self, panel["marks"], crossings / SAMPLES_PER_MS)

        self.n_spikes0 = len(self.spike_points0)
        self.n_spikes1 = len(self.spike_points1)
        self.n_spikes2 = len(self.spike_points2)
        ui.Spikeling_DataAnalysis_Spike_result_label.setText(
            f"{self.n_spikes0} spikes detected")

        for neuron, panel in enumerate(NEURON_PANELS):
            rate = getattr(ui, panel["rate"])
            marks = getattr(self, panel["marks"])
            vm = getattr(ui, f"df_DataAnalysis_{panel['vm']}")
            current = getattr(ui, f"df_DataAnalysis_{panel['current']}")

            widget = prepare_panel(ui, f"2_{neuron}_0", "Spike Rate (Hz)")
            if widget is not None:
                theme_manager.themed_plot(widget, x, rate, "analysis_spike_rate")

            widget = prepare_panel(ui, f"2_{neuron}_1", "Membrane Voltage (mV)")
            if widget is not None:
                theme_manager.themed_plot(widget, x, vm, panel["vm_role"])
                theme_manager.themed_plot(
                    widget, marks, np.full(marks.size, 45.0), panel["vm_role"],
                    symbol="o", symbol_size=RASTER_SYMBOL_SIZE)

            label = "Input Current (a.u.)" if neuron == 0 else "Synaptic Input (a.u.)"
            widget = prepare_panel(ui, f"2_{neuron}_2", label)
            if widget is not None:
                theme_manager.themed_plot(widget, x, current, panel["current_role"])

            widget = prepare_panel(ui, f"2_{neuron}_3", "Intensity", "Time (ms)")
            if widget is not None:
                theme_manager.themed_plot(
                    widget, x, ui.df_DataAnalysis_y2, "neuron_stimulus")

        ui.Spikeling_DataAnalysis_Average_Display_pushButton.setEnabled(True)
        ui.Spikeling_DataAnalysis_Average_Save_pushButton.setEnabled(True)

        theme_manager.style_traces()

    # -------------------------------------------------------------------------
    # Stimulus-locked averages
    # -------------------------------------------------------------------------

    def AverageTraces(self):
        """
        Segment the recording on the stimulus trigger and average the repeats.

        For every neuron the page shows, from top to bottom: instantaneous
        rate, a spike raster, membrane potential and input current, each with
        the individual repetitions behind the mean.

        Notes
        -----
        Repetitions are drawn as one ``NaN``-separated polyline per panel
        rather than one curve per repeat, which keeps a 100-repeat overlay at
        a single scene-graph item. The last repetition is now included on all
        three neurons; two of them previously stopped one short.
        """
        ui = self.ui
        ui.Spikeling_DataAnalysis_Display_StackedWidget.setCurrentWidget(ui.page_103_3_0)

        trigger = np.asarray(ui.df_DataAnalysis_Trigger, dtype=float)
        x_full = np.asarray(ui.df_DataAnalysis_x, dtype=float)

        self.stimulus_times = np.flatnonzero(trigger[:-1] == 1).tolist()
        if len(self.stimulus_times) < 2:
            ui.Spikeling_DataAnalysis_Average_label.setText("No repeated stimulus found")
            return

        self.loop_duration = self.stimulus_times[1] - self.stimulus_times[0]
        starts = self.stimulus_times[:-1]
        ui.StimLoop_x = np.linspace(0, self.loop_duration / SAMPLES_PER_MS - 1,
                                    self.loop_duration)

        def segment(array):
            """Stack one signal into ``(n_loops, loop_duration)``."""
            values = np.asarray(array, dtype=float)
            return np.vstack([values[s:s + self.loop_duration] for s in starts])

        self.Stim_loops = segment(ui.df_DataAnalysis_y2)
        ui.Spikeling_DataAnalysis_Average_label.setText(
            f"{len(self.Stim_loops)} loops "
            f"({self.loop_duration / SAMPLES_PER_MS}ms each)")

        rate_means, vm_means, current_means, raster_loops = [], [], [], []

        for neuron, panel in enumerate(NEURON_PANELS):
            rate_loops = segment(getattr(ui, panel["rate"]))
            vm_loops = segment(getattr(ui, f"df_DataAnalysis_{panel['vm']}"))
            current_loops = segment(getattr(ui, f"df_DataAnalysis_{panel['current']}"))

            spike_indices = (self.spike_points0, self.spike_points1,
                             self.spike_points2)[neuron]
            loops = [
                [x_full[s] - x_full[start] for s in spike_indices
                 if start < s < start + self.loop_duration]
                for start in starts
            ]
            raster_loops.append(loops)

            rate_means.append(np.mean(rate_loops, axis=0))
            vm_means.append(np.mean(vm_loops, axis=0))
            current_means.append(np.mean(current_loops, axis=0))

            # --- Spike rate ------------------------------------------------
            widget = prepare_panel(ui, f"3_{neuron}_0", "Spike Rate (Hz)")
            if widget is not None:
                flat_x, flat_y = stack_repetitions(ui.StimLoop_x, rate_loops)
                theme_manager.themed_plot(widget, flat_x, flat_y, "analysis_loop",
                                          connect="finite")
                theme_manager.themed_plot(widget, ui.StimLoop_x, rate_means[neuron],
                                          "analysis_spike_rate",
                                          width_scale=MEAN_WIDTH_SCALE)

            # --- Raster ----------------------------------------------------
            widget = prepare_panel(ui, f"3_{neuron}_1", "Loops", show_y_grid=False)
            if widget is not None:
                times, rows = flatten_raster(loops)
                theme_manager.themed_plot(widget, times, rows, panel["vm_role"],
                                          symbol="o", symbol_size=RASTER_SYMBOL_SIZE)
                widget.setXRange(0, self.loop_duration / SAMPLES_PER_MS)

            # --- Membrane potential -----------------------------------------
            widget = prepare_panel(ui, f"3_{neuron}_2", "Membrane Voltage (mV)")
            if widget is not None:
                flat_x, flat_y = stack_repetitions(ui.StimLoop_x, vm_loops)
                theme_manager.themed_plot(widget, flat_x, flat_y, "analysis_loop",
                                          connect="finite")
                theme_manager.themed_plot(widget, ui.StimLoop_x, vm_means[neuron],
                                          panel["vm_role"],
                                          width_scale=MEAN_WIDTH_SCALE)

            # --- Current -----------------------------------------------------
            widget = prepare_panel(ui, f"3_{neuron}_3", "Input Current (a.u.)",
                                   "Time (ms)")
            if widget is not None:
                flat_x, flat_y = stack_repetitions(ui.StimLoop_x, current_loops)
                theme_manager.themed_plot(widget, flat_x, flat_y, "analysis_loop",
                                          connect="finite")
                theme_manager.themed_plot(widget, ui.StimLoop_x, current_means[neuron],
                                          panel["current_role"],
                                          width_scale=MEAN_WIDTH_SCALE)

        # Attribute names kept for the existing Save* exporters.
        self.SpikeRate_mean, self.SpikeRate1_mean, self.SpikeRate2_mean = rate_means
        self.Vm0_mean, self.Vm1_mean, self.Vm2_mean = vm_means
        self.ITotal_mean, self.ISynapse1_mean, self.ISynapse2_mean = current_means
        self.Spike0_loops, self.Spike1_loops, self.Spike2_loops = raster_loops
        self.Stim_mean = np.mean(self.Stim_loops, axis=0)

        theme_manager.style_traces()

    def LoadData(self):
        FileName = QFileDialog.getOpenFileName(caption='Select recording file to load',
                                               dir="./Recordings",
                                               filter='csv files (*.csv)'
                                               )
        self.Spikeling_DataAnalysis_LoadData_label.setText(FileName[0])

        Df = pd.read_csv(FileName[0])
        self.df_DataAnalysis_Timing = Df["Time (ms)"]
        self.df_DataAnalysis_Vm = Df["Spikeling Vm (mV)"]
        self.df_DataAnalysis_ITotal = Df["Total Current Input (a.u.)"]
        self.df_DataAnalysis_Stimulus = Df["Stimulus (%)"]
        self.df_DataAnalysis_Synapse1Vm = Df["Synapse 1 Vm (mV)"]
        self.df_DataAnalysis_Synapse1Input = Df["Synapse 1 Input (a.u.)"]
        self.df_DataAnalysis_Synapse2Vm = Df["Synapse 2 Vm (mV)"]
        self.df_DataAnalysis_Synapse2Input = Df["Synapse 2 Input (a.u.)"]
        self.df_DataAnalysis_Trigger = Df["Trigger"]

    def SaveRawDataImage(self):
        FolderName = QFileDialog.getExistingDirectory(caption='Select folder to save graphs on screen',
                                                      dir="./Recordings/Graphs")
        currentStackedWidget = self.ui.Spikeling_DataAnalysis_Display_StackedWidget.currentWidget()

        if currentStackedWidget == self.ui.page_103_1_0:
            exporter100 = pg.exporters.ImageExporter(self.ui.Spikeling_DataAnalysis_Oscilloscope_widget1_0_0.plotItem)
            exporter101 = pg.exporters.ImageExporter(self.ui.Spikeling_DataAnalysis_Oscilloscope_widget1_0_1.plotItem)
            exporter102 = pg.exporters.ImageExporter(self.ui.Spikeling_DataAnalysis_Oscilloscope_widget1_0_2.plotItem)
            exporter103 = pg.exporters.ImageExporter(self.ui.Spikeling_DataAnalysis_Oscilloscope_widget1_0_3.plotItem)
            exporter100.export(FolderName + '/Spikeling Vm.png')
            exporter101.export(FolderName + '/Spikeling Total Input Current.png')
            exporter102.export(FolderName + '/Stimulus.png')
            exporter103.export(FolderName + '/Synaptic Input.png')

        if currentStackedWidget == self.ui.page_103_1_1:
            exporter110 = pg.exporters.ImageExporter(self.ui.Spikeling_DataAnalysis_Oscilloscope_widget1_1_0.plotItem)
            exporter111 = pg.exporters.ImageExporter(self.ui.Spikeling_DataAnalysis_Oscilloscope_widget1_1_1.plotItem)
            exporter112 = pg.exporters.ImageExporter(self.ui.Spikeling_DataAnalysis_Oscilloscope_widget1_1_2.plotItem)
            exporter110.export(FolderName + '/Auxillary Neuron1 Vm.png')
            exporter111.export(FolderName + '/Auxillary Neuron1 Synpatic Input.png')
            exporter112.export(FolderName + '/Stimulus.png')

        if currentStackedWidget == self.ui.page_103_1_2:
            exporter120 = pg.exporters.ImageExporter(self.ui.Spikeling_DataAnalysis_Oscilloscope_widget1_2_0.plotItem)
            exporter121 = pg.exporters.ImageExporter(self.ui.Spikeling_DataAnalysis_Oscilloscope_widget1_2_1.plotItem)
            exporter122 = pg.exporters.ImageExporter(self.ui.Spikeling_DataAnalysis_Oscilloscope_widget1_2_2.plotItem)
            exporter120.export(FolderName + '/Auxillary Neuron2 Vm.png')
            exporter121.export(FolderName + '/Auxillary Neuron2 Synpatic Input.png')
            exporter122.export(FolderName + '/Stimulus.png')


    def SaveSpikeTraces(self):
        FolderName = QFileDialog.getExistingDirectory(caption='Save Spike data traces on screen',
                                                      dir="./Recordings/Data")
        currentStackedWidget = self.ui.Spikeling_DataAnalysis_Display_StackedWidget.currentWidget()

        if currentStackedWidget == self.ui.page_103_2_0:
            dict_spikerate = {'Spikeling SpikeRate': self.ui.spike_rate0}
            dict_spike = {'Spikeling Spike Events (timepoints)': self.spike_points0}
            self.df_spikerate = pd.DataFrame(dict_spikerate)
            self.df_spike = pd.DataFrame(dict_spike)
        self.df_spikerate.to_csv(FolderName + '/Spikeling_spikerate' + '.csv', index=False)
        self.df_spike.to_csv(FolderName + '/Spikeling_spike' + '.csv', index=False)

        if currentStackedWidget == self.ui.page_103_2_1:
            dict_spikerate = {'Aux Neuron 1 SpikeRate': self.ui.spike_rate1}
            dict_spike = {'Aux Neuron 1 Spike Events (timepoints)': self.spike_points1}
            self.df_spikerate = pd.DataFrame(dict_spikerate)
            self.df_spike = pd.DataFrame(dict_spike)
        self.df_spikerate.to_csv(FolderName + '/AuxNeuron1_spikerate' + '.csv', index=False)
        self.df_spike.to_csv(FolderName + '/AuxNeuron1_spike' + '.csv', index=False)

        if currentStackedWidget == self.ui.page_103_2_2:
            dict_spikerate = {'Aux Neuron 2 SpikeRate': self.ui.spike_rate2}
            dict_spike = {'Aux Neuron 2 Spike Events (timepoints)': self.spike_points2}
            self.df_spikerate = pd.DataFrame(dict_spikerate)
            self.df_spike = pd.DataFrame(dict_spike)
        self.df_spikerate.to_csv(FolderName + '/AuxNeuron2_spikerate' + '.csv', index=False)
        self.df_spike.to_csv(FolderName + '/AuxNeuron2_spike' + '.csv', index=False)


    def SaveSpikeImage(self):
        FolderName = QFileDialog.getExistingDirectory(caption='Select folder to save graphs on screen',
                                                      dir="./Recordings/Graphs")
        currentStackedWidget = self.ui.Spikeling_DataAnalysis_Display_StackedWidget.currentWidget()

        if currentStackedWidget == self.ui.page_103_2_0:
            exporter200 = pg.exporters.ImageExporter(self.ui.Spikeling_DataAnalysis_Oscilloscope_widget2_0_0.plotItem)
            exporter201 = pg.exporters.ImageExporter(self.ui.Spikeling_DataAnalysis_Oscilloscope_widget2_0_1.plotItem)
            exporter202 = pg.exporters.ImageExporter(self.ui.Spikeling_DataAnalysis_Oscilloscope_widget2_0_2.plotItem)
            exporter203 = pg.exporters.ImageExporter(self.ui.Spikeling_DataAnalysis_Oscilloscope_widget2_0_3.plotItem)
            exporter200.export(FolderName + '/Spikeling Spike Rate.png')
            exporter201.export(FolderName + '/Spikeling Vm & spike.png')
            exporter202.export(FolderName + '/Spikeling Total current.png')
            exporter203.export(FolderName + '/Stimulus.png')

        if currentStackedWidget == self.ui.page_103_2_1:
            exporter210 = pg.exporters.ImageExporter(self.ui.Spikeling_DataAnalysis_Oscilloscope_widget2_1_0.plotItem)
            exporter211 = pg.exporters.ImageExporter(self.ui.Spikeling_DataAnalysis_Oscilloscope_widget2_1_1.plotItem)
            exporter212 = pg.exporters.ImageExporter(self.ui.Spikeling_DataAnalysis_Oscilloscope_widget2_1_2.plotItem)
            exporter213 = pg.exporters.ImageExporter(self.ui.Spikeling_DataAnalysis_Oscilloscope_widget2_1_3.plotItem)
            exporter210.export(FolderName + '/Auxillary Neuron1 Spike Rate.png')
            exporter211.export(FolderName + '/Auxillary Neuron1 Vm & spike.png')
            exporter212.export(FolderName + '/Auxillary Neuron1 Total current.png')
            exporter213.export(FolderName + '/Stimulus.png')

        if currentStackedWidget == self.ui.page_103_2_2:
            exporter220 = pg.exporters.ImageExporter(self.ui.Spikeling_DataAnalysis_Oscilloscope_widget2_2_0.plotItem)
            exporter221 = pg.exporters.ImageExporter(self.ui.Spikeling_DataAnalysis_Oscilloscope_widget2_2_1.plotItem)
            exporter222 = pg.exporters.ImageExporter(self.ui.Spikeling_DataAnalysis_Oscilloscope_widget2_2_2.plotItem)
            exporter223 = pg.exporters.ImageExporter(self.ui.Spikeling_DataAnalysis_Oscilloscope_widget2_2_3.plotItem)
            exporter220.export(FolderName + '/Auxillary Neuron2 Spike Rate.png')
            exporter221.export(FolderName + '/Auxillary Neuron2 Vm & spike.png')
            exporter222.export(FolderName + '/Auxillary Neuron2 Total current.png')
            exporter223.export(FolderName + '/Stimulus.png')

    def SaveAverageTraces(self):
        FolderName = QFileDialog.getExistingDirectory(caption='Save Spike data traces on screen',
                                                      dir="./Recordings/Data")
        currentStackedWidget = self.ui.Spikeling_DataAnalysis_Display_StackedWidget.currentWidget()

        if currentStackedWidget == self.ui.page_103_3_0:
            dict_spikerateaverage = {'Spikeling SpikeRate Average': self.SpikeRate_mean}
            dict_spikerasterplot = {'Spikeling Spike Raster Plot': self.ui.ySpikeLoops0}
            dict_vmaverage = {'Spikeling Vm Average': self.Vm0_mean}
            dict_currentaverage = {'Spikeling Current Average': self.ITotal_mean}
            self.df_means = pd.DataFrame(dict_spikerateaverage,dict_vmaverage,dict_currentaverage)
            self.df_rasterplot = pd.DataFrame(dict_spikerasterplot)
        self.df_means.to_csv(FolderName + '/Spikeling_means' + '.csv', index=False)
        self.df_rasterplot.to_csv(FolderName + '/Spikeling_rasterplot' + '.csv', index=False)

        if currentStackedWidget == self.ui.page_103_3_1:
            dict_spikerateaverage = {'AuxNeuron1 SpikeRate Average': self.SpikeRate1_mean}
            dict_spikerasterplot = {'AuxNeuron1 Spike Raster Plot': self.ui.ySpikeLoops1}
            dict_vmaverage = {'AuxNeuron1 Vm Average': self.Vm1_mean}
            dict_currentaverage = {'AuxNeuron1 Current Average': self.ISynapse1_mean}
            self.df_means = pd.DataFrame(dict_spikerateaverage,dict_vmaverage,dict_currentaverage)
            self.df_rasterplot = pd.DataFrame(dict_spikerasterplot)
        self.df_means.to_csv(FolderName + '/AuxNeuron1_means' + '.csv', index=False)
        self.df_rasterplot.to_csv(FolderName + '/AuxNeuron1_rasterplot' + '.csv', index=False)

        if currentStackedWidget == self.ui.page_103_3_2:
            dict_spikerateaverage = {'AuxNeuron2 SpikeRate Average': self.SpikeRate2_mean}
            dict_spikerasterplot = {'AuxNeuron2 Spike Raster Plot': self.ui.ySpikeLoops2}
            dict_vmaverage = {'AuxNeuron2 Vm Average': self.Vm2_mean}
            dict_currentaverage = {'AuxNeuron2 Current Average': self.ISynapse2_mean}
            self.df_means = pd.DataFrame(dict_spikerateaverage,dict_vmaverage,dict_currentaverage)
            self.df_rasterplot = pd.DataFrame(dict_spikerasterplot)
        self.df_means.to_csv(FolderName + '/AuxNeuron2_means' + '.csv', index=False)
        self.df_rasterplot.to_csv(FolderName + '/AuxNeuron2_rasterplot' + '.csv', index=False)

    def SaveAverageImage(self):
        FolderName = QFileDialog.getExistingDirectory(caption='Select folder to save graphs on screen',
                                                      dir="./Recordings/Graphs")
        currentStackedWidget = self.ui.Spikeling_DataAnalysis_Display_StackedWidget.currentWidget()

        if currentStackedWidget == self.ui.page_103_3_0:
            exporter300 = pg.exporters.ImageExporter(self.ui.Spikeling_DataAnalysis_Oscilloscope_widget3_0_0.plotItem)
            exporter301 = pg.exporters.ImageExporter(self.ui.Spikeling_DataAnalysis_Oscilloscope_widget3_0_1.plotItem)
            exporter302 = pg.exporters.ImageExporter(self.ui.Spikeling_DataAnalysis_Oscilloscope_widget3_0_2.plotItem)
            exporter303 = pg.exporters.ImageExporter(self.ui.Spikeling_DataAnalysis_Oscilloscope_widget3_0_3.plotItem)
            exporter300.export(FolderName + '/Spikeling Spike Rate Average.png')
            exporter301.export(FolderName + '/Spikeling spike rasterplot.png')
            exporter302.export(FolderName + '/Spikeling Vm Average.png')
            exporter303.export(FolderName + '/Spikeling Total Current Average.png')

        if currentStackedWidget == self.ui.page_103_3_1:
            exporter310 = pg.exporters.ImageExporter(self.ui.Spikeling_DataAnalysis_Oscilloscope_widget3_1_0.plotItem)
            exporter311 = pg.exporters.ImageExporter(self.ui.Spikeling_DataAnalysis_Oscilloscope_widget3_1_1.plotItem)
            exporter312 = pg.exporters.ImageExporter(self.ui.Spikeling_DataAnalysis_Oscilloscope_widget3_1_2.plotItem)
            exporter313 = pg.exporters.ImageExporter(self.ui.Spikeling_DataAnalysis_Oscilloscope_widget3_1_3.plotItem)
            exporter310.export(FolderName + '/AuxNeuron1 Spike Rate Average.png')
            exporter311.export(FolderName + '/AuxNeuron1 spike rasterplot.png')
            exporter312.export(FolderName + '/AuxNeuron1 Vm Average.png')
            exporter313.export(FolderName + '/AuxNeuron1 Synapse Current Average.png')

        if currentStackedWidget == self.ui.page_103_3_2:
            exporter320 = pg.exporters.ImageExporter(self.ui.Spikeling_DataAnalysis_Oscilloscope_widget3_2_0.plotItem)
            exporter321 = pg.exporters.ImageExporter(self.ui.Spikeling_DataAnalysis_Oscilloscope_widget3_2_1.plotItem)
            exporter322 = pg.exporters.ImageExporter(self.ui.Spikeling_DataAnalysis_Oscilloscope_widget3_2_2.plotItem)
            exporter323 = pg.exporters.ImageExporter(self.ui.Spikeling_DataAnalysis_Oscilloscope_widget3_2_3.plotItem)
            exporter320.export(FolderName + '/AuxNeuron2 Spike Rate Average.png')
            exporter321.export(FolderName + '/AuxNeuron2 spike rasterplot.png')
            exporter322.export(FolderName + '/AuxNeuron2 Vm Average.png')
            exporter323.export(FolderName + '/AuxNeuron2 Synapse Current Average.png')



