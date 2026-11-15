from math import isfinite
from typing import NamedTuple

from PySide6.QtCore import QCoreApplication, QIODevice, QSaveFile, QSignalBlocker, Qt
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFileDialog
import numpy as np
import pandas as pd
import pyqtgraph as pg
from spikeling_gui.appearance.dialogs import show_popup
from spikeling_gui.neuron_csv import NEURON_COLUMNS, read_neuron_csv
from spikeling_gui.appearance.theme_manager import theme_manager
from spikeling_gui.neuron_presets import IzhikevichNeurons
from spikeling_gui.paths import save_dialog_directory, data_directory
from spikeling_gui.ui.generated.UI_NeuronGeneratorAdvanced import Ui_NeuronGeneratorAdvanced


# CSV keys in the order shown in the dialog.
_ADVANCED_COLUMNS = NEURON_COLUMNS[4:]
_ADVANCED_DEFAULTS = (0, 0.001, 0.025, 0, 0.995, 0, 0.995)


# Broad exploration bounds, including all twenty presets. These guard the
# preview, not a claim that every permitted combination is physiologically valid.
_MAIN_LIMITS = (("a", 0, 1), ("b", -2, 2), ("c", -100, 29),
                ("d", -100, 100), ("Input current", -1000, 1000))
_ADVANCED_LIMITS = tuple(
    (name, -100, 100) if "Gain" in name else (name, 0, 1)
    for name in _ADVANCED_COLUMNS
)


def _number(text, name, lower, upper):
    try:
        value = float(str(text).strip().replace(",", "."))
    except (TypeError, ValueError, OverflowError):
        value = float("nan")
    if not isfinite(value) or not lower <= value <= upper:
        raise ValueError(f"{name}: enter a finite number between {lower:g} and {upper:g}.")
    return value


def _validated_advanced(parameters):
    if len(parameters) != len(_ADVANCED_LIMITS):
        raise ValueError("Advanced parameters require seven values. Restore Defaults and try again.")
    return tuple(_number(value, *limits) for value, limits in zip(parameters, _ADVANCED_LIMITS))


def _read_inputs(host):
    values = []
    for field_name, limits in zip(("a_value", "b_value", "c_value", "d_value", "StimInt_value"), _MAIN_LIMITS):
        field = getattr(host.ui, field_name)
        try:
            values.append(_number(field.text(), *limits))
        except ValueError:
            field.setFocus()
            field.selectAll()
            raise
    return tuple(values), _validated_advanced(_advanced_parameters(host))


_DT_MS = 0.1
_DURATION_MS = 250
_STEP, _RAMP, _PAIRED, _REBOUND = range(4)
_DEFAULT_MODEL = (0.02, 0.2, -65.0, 2.0, -65.0)


class Preview(NamedTuple):
    time: np.ndarray
    voltage: np.ndarray
    current: np.ndarray
    spikes: np.ndarray


def _simulate(parameters, v_rest=-65.0, protocol=_STEP):
    a, b, c, d, amplitude = parameters
    ticks = np.arange(round(_DURATION_MS / _DT_MS) + 1)
    times = ticks * _DT_MS
    current = np.zeros(times.size)
    if protocol == _RAMP:
        current[500:2000] = np.linspace(0, amplitude, 1500)
    elif protocol == _PAIRED:
        current[500:600] = current[1000:1100] = amplitude
    elif protocol == _REBOUND:
        current[500:1500] = -abs(amplitude)
    else:
        current[500:2000] = amplitude

    voltage = np.empty_like(times)
    v, u = v_rest, b * v_rest
    voltage[0] = v
    spikes = []
    for index, injected in enumerate(current[:-1], start=1):
        # Spikeling's drug-free update uses the new voltage for recovery.
        v += _DT_MS * (0.04 * v * v + 5.0 * v + 140.0 - u + float(injected))
        u += _DT_MS * a * (b * v - u)
        if not isfinite(v) or not isfinite(u) or abs(v) > 1e6 or abs(u) > 1e6:
            raise ValueError("The simulation became unstable. Reduce the parameter magnitudes or load a preset.")
        if v >= 30.0:
            voltage[index] = 30.0
            spikes.append(times[index])
            v, u = c, u + d
        else:
            v = max(-110.0, v)
            voltage[index] = v
    return Preview(times, voltage, current, np.asarray(spikes))


def _measure(preview, protocol):
    spikes = preview.spikes
    onset = 150 if protocol == _REBOUND else 50
    response = spikes[spikes >= onset]
    latency = float(response[0] - onset) if response.size else None
    intervals = np.diff(spikes[(spikes >= 50) & (spikes <= 200)])
    adaptation = float(intervals[-1] / intervals[0]) if protocol == _STEP and intervals.size >= 2 else None
    return spikes.size, spikes.size * 1000 / _DURATION_MS, latency, adaptation


def _show_measurements(ui, preview, protocol):
    count, rate, latency, adaptation = _measure(preview, protocol)
    latency_text = "—" if latency is None else f"{latency:.1f} ms"
    adaptation_text = "—" if adaptation is None else f"{adaptation:.2f}×"
    if protocol == _REBOUND:
        latency_label = QCoreApplication.translate("NeuronGenerator", "Release latency")
    else:
        latency_label = QCoreApplication.translate("NeuronGenerator", "First-spike latency")
    template = QCoreApplication.translate(
        "NeuronGenerator", "Last display · Spikes: {count} · Mean rate: {rate:g} Hz · "
        "{latency_label}: {latency} · Adaptation: {adaptation}"
    )
    ui.NeuronGenerator_metrics_label.setText(template.format(
        count=count, rate=rate, latency_label=latency_label, latency=latency_text,
        adaptation=adaptation_text,
    ))


def _reference_model(host):
    return getattr(host, "_neuron_generator_reference", _DEFAULT_MODEL)


def _advanced_parameters(host):
    return getattr(host, "neuron_generator_advanced_parameters", _ADVANCED_DEFAULTS)


def EditAdvancedParameters(host):
    """Edit the seven advanced values saved with a generated neuron."""
    dialog = QDialog(host)
    ui = Ui_NeuronGeneratorAdvanced()
    ui.setupUi(dialog)
    dialog.setStyleSheet(theme_manager.stylesheet())
    fields = (ui.photoGain, ui.photoDecay, ui.photoRecovery, ui.syn1Gain,
              ui.syn1Decay, ui.syn2Gain, ui.syn2Decay)
    status = ui.validationMessage

    def populate(parameters):
        for field, value in zip(fields, parameters):
            field.setText(str(value))
        status.clear()

    def save():
        try:
            parameters = _validated_advanced([field.text() for field in fields])
        except ValueError as error:
            status.setText(str(error))
            return
        host.neuron_generator_advanced_parameters = parameters
        dialog.accept()

    defaults = ui.buttonBox.button(QDialogButtonBox.StandardButton.RestoreDefaults)
    defaults.clicked.connect(lambda: populate(_ADVANCED_DEFAULTS))
    ui.buttonBox.accepted.connect(save)
    ui.buttonBox.rejected.connect(dialog.reject)
    populate(_advanced_parameters(host))
    dialog.exec()


def ShowPage(self):
    self.ui.mainbody_stackedWidget.setCurrentWidget(self.ui.page_NeuronGenerator)
    NeuronGenerator.SetGraph(self)


class NeuronGenerator():

    def DrawNeuron(self):
        try:
            parameters, _ = _read_inputs(self)
            protocol = self.ui.NeuronGenerator_protocol_combo.currentIndex()
            original = _reference_model(self)
            preview = _simulate(parameters, original[4], protocol)
        except (ValueError, TypeError, OverflowError) as error:
            show_popup(self, "Cannot display neuron", str(error))
            return
        NeuronGenerator.SetGraph(self)
        self.a, self.b, self.c, self.d, self.I_dc = parameters
        self.NeuronCurve.setData(preview.time, preview.voltage)
        self.StimCurve.setData(preview.time, preview.current)
        try:
            reference = _simulate(original[:4] + (self.I_dc,), original[4], protocol)
        except ValueError:
            reference = None
        checkbox = self.ui.NeuronGenerator_reference_check
        if reference is None:
            self.NeuronReferenceCurve.setData([], [])
            checkbox.setChecked(False)
        else:
            self.NeuronReferenceCurve.setData(reference.time, reference.voltage)
        checkbox.setEnabled(reference is not None)
        _show_measurements(self.ui, preview, protocol)
        graph = self.ui.NeuronGenerator_Oscilloscope_widget
        lowest = min(float(preview.voltage.min()), float(reference.voltage.min())) if reference else float(preview.voltage.min())
        graph.setYRange(min(-90, lowest - 5), 40, padding=0)
        low, high = float(preview.current.min()), float(preview.current.max())
        margin = max(1.0, (high - low) * 0.1)
        self.StimPlot.setYRange(low - margin, high + margin, padding=0)
        NeuronGenerator.NeuronUpdateView(self)

    def NeuronUpdateView(self):
        view = self.ui.NeuronGenerator_Oscilloscope_widget.getViewBox()
        self.StimPlot.setGeometry(view.sceneBoundingRect())
        self.StimPlot.linkedViewChanged(view, self.StimPlot.XAxis)

    def SetGraph(self):
        graph = self.ui.NeuronGenerator_Oscilloscope_widget
        if getattr(self, "_neuron_generator_graph", None) is graph:
            NeuronGenerator.NeuronUpdateView(self)
            return
        graph.setRange(xRange=[0, 250], yRange=[-90, 40], padding=0)
        graph.getViewBox().setLimits(xMin=0, xMax=250)
        graph.setLabel('left', 'Membrane potential', 'mV')
        graph.setLabel('bottom', 'time', 'ms')
        graph.setLabel('right', 'Current Input', 'a.u.')
        graph.showAxis('right')
        self.StimPlot = pg.ViewBox()
        graph.scene().addItem(self.StimPlot)
        graph.getAxis('right').linkToView(self.StimPlot)
        self.StimPlot.setXLink(graph.getViewBox())
        self.StimPlot.setYRange(-1, 1, padding=0)
        dash = Qt.PenStyle.DashLine
        self.NeuronReferenceCurve = graph.plot([], [], pen=theme_manager.pen("text_primary", style=dash))
        theme_manager.tag_item(self.NeuronReferenceCurve, "text_primary", style=dash)
        self.NeuronReferenceCurve.setVisible(self.ui.NeuronGenerator_reference_check.isChecked())
        self.ui.NeuronGenerator_reference_check.toggled.connect(self.NeuronReferenceCurve.setVisible)
        self.NeuronCurve = graph.plot([], [], pen=theme_manager.pen("neuron_vm"))
        self.StimCurve = pg.PlotCurveItem([], [], pen=theme_manager.pen("neuron_current"))
        self.StimPlot.addItem(self.StimCurve)
        for checkbox, curve in (
            (self.ui.NeuronGenerator_subframe1_Oscilloscope_widget_Vm_checkbox, self.NeuronCurve),
            (self.ui.NeuronGenerator_subframe1_Oscilloscope_widget_stimulus_checkbox, self.StimCurve),
        ):
            curve.setVisible(checkbox.isChecked())
            checkbox.toggled.connect(curve.setVisible)
        self._neuron_generator_resize = lambda: NeuronGenerator.NeuronUpdateView(self)
        graph.getViewBox().sigResized.connect(self._neuron_generator_resize)
        self._neuron_generator_graph = graph
        NeuronGenerator.NeuronUpdateView(self)

    def LoadNeuron(self):
        index = self.ui.LoadNeuron_comboBox.currentIndex() - 1
        if 0 <= index < len(IzhikevichNeurons):
            NeuronGenerator.SetModel(self, tuple(IzhikevichNeurons[index][:5]), _ADVANCED_DEFAULTS)

    def SetModel(self, model, advanced):
        self._neuron_generator_reference = model
        self.neuron_generator_advanced_parameters = advanced
        for field, value in zip(("a_value", "b_value", "c_value", "d_value"), model):
            getattr(self.ui, field).setText(str(value))

    def OpenNeuron(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Open neuron CSV", str(data_directory("Neurons")), "CSV files (*.csv)"
        )
        if not filename:
            return
        try:
            parameters = read_neuron_csv(filename)
            model = tuple(_number(value, *limits)
                          for value, limits in zip(parameters[:4], _MAIN_LIMITS[:4]))
            advanced = _validated_advanced(parameters[4:])
        except (OSError, ValueError) as error:
            show_popup(self, "Cannot open neuron", str(error))
            return
        with QSignalBlocker(self.ui.LoadNeuron_comboBox):
            self.ui.LoadNeuron_comboBox.setCurrentIndex(0)
        # CSV files have no resting-voltage field.
        NeuronGenerator.SetModel(self, model + (_DEFAULT_MODEL[4],), advanced)

    def SaveNeuron(self):
        try:
            values, advanced = _read_inputs(self)
            # Save must reject unstable models just as Display does.
            _simulate(values, _reference_model(self)[4],
                      self.ui.NeuronGenerator_protocol_combo.currentIndex())
        except (ValueError, TypeError, OverflowError) as error:
            show_popup(self, "Cannot save neuron", str(error))
            return
        frame = pd.DataFrame([values[:4] + advanced], columns=NEURON_COLUMNS)
        filename, _ = QFileDialog.getSaveFileName(
            caption='Save current neuron parameters',
            dir=save_dialog_directory(data_directory("Neurons")),
            filter='csv files (*.csv)')
        if not filename:
            return
        # Atomic replacement protects an existing CSV from a failed write.
        output = QSaveFile(filename)
        payload = frame.to_csv(index=False).encode("utf-8")
        if not output.open(QIODevice.OpenModeFlag.WriteOnly):
            show_popup(self, "Cannot save neuron", output.errorString())
            return
        if output.write(payload) != len(payload):
            message = output.errorString()
            output.cancelWriting()
            show_popup(self, "Cannot save neuron", message)
        elif not output.commit():
            show_popup(self, "Cannot save neuron", output.errorString())
