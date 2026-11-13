from math import isfinite

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QLabel, QLineEdit
import numpy as np
import pandas as pd
import pyqtgraph as pg
from spikeling_gui.appearance.palette import DarkSolarized
from spikeling_gui.appearance.theme_manager import theme_manager
from spikeling_gui.neuron_presets import IzhikevichNeurons
from spikeling_gui.paths import save_dialog_directory, data_directory


# CSV keys in the order shown in the dialog.
_ADVANCED_COLUMNS = (
    "PhotoGain( %)", "PhotoDecay(1 / ms)", "PhotoRecovery(1 / ms)",
    "Syn1 Gain( %)", "Syn1 Decay(1 / ms)", "Syn2 Gain( %)", "Syn2 Decay(1 / ms)",
)
_ADVANCED_DEFAULTS = (0, 0.001, 0.025, 0, 0.995, 0, 0.995)


def _advanced_parameters(host):
    return getattr(host, "neuron_generator_advanced_parameters", _ADVANCED_DEFAULTS)


def EditAdvancedParameters(host):
    """Edit the seven advanced values saved with a generated neuron."""
    dialog = QDialog(host)
    dialog.setWindowTitle(QCoreApplication.translate("NeuronGenerator", "Advanced Neuron Parameters"))
    dialog.setStyleSheet(theme_manager.stylesheet())
    form = QFormLayout(dialog)

    labels = (
        QCoreApplication.translate("NeuronGenerator", "Photo-Receptor Gain (%)"),
        QCoreApplication.translate("NeuronGenerator", "Photo-Receptor Decay (ms⁻¹)"),
        QCoreApplication.translate("NeuronGenerator", "Photo-Receptor Recovery (ms⁻¹)"),
        QCoreApplication.translate("NeuronGenerator", "Synapse 1 Gain (%)"),
        QCoreApplication.translate("NeuronGenerator", "Synapse 1 Decay (ms⁻¹)"),
        QCoreApplication.translate("NeuronGenerator", "Synapse 2 Gain (%)"),
        QCoreApplication.translate("NeuronGenerator", "Synapse 2 Decay (ms⁻¹)"),
    )
    fields = []
    for label in labels:
        field = QLineEdit(dialog)
        form.addRow(label, field)
        fields.append(field)

    status = QLabel(dialog)
    status.setWordWrap(True)
    form.addRow(status)

    def populate(parameters):
        for field, value in zip(fields, parameters):
            field.setText(str(value))
        status.clear()

    def save():
        parameters = []
        for field in fields:
            try:
                value = float(field.text().strip().replace(",", "."))
            except ValueError:
                value = float("nan")
            if not isfinite(value):
                status.setText(QCoreApplication.translate(
                    "NeuronGenerator", "Enter a finite number in each field."
                ))
                field.setFocus()
                field.selectAll()
                return
            parameters.append(value)
        host.neuron_generator_advanced_parameters = tuple(parameters)
        dialog.accept()

    standard = QDialogButtonBox.StandardButton
    buttons = QDialogButtonBox(standard.Ok | standard.Cancel | standard.RestoreDefaults, dialog)
    defaults = buttons.button(standard.RestoreDefaults)
    defaults.setText(QCoreApplication.translate("NeuronGenerator", "Restore Defaults"))
    defaults.clicked.connect(lambda: populate(_ADVANCED_DEFAULTS))
    buttons.accepted.connect(save)
    buttons.rejected.connect(dialog.reject)
    form.addRow(buttons)
    populate(_advanced_parameters(host))
    dialog.exec()


def ShowPage(self):
    self.ui.mainbody_stackedWidget.setCurrentWidget(self.ui.page_NeuronGenerator)
    self.ui.NeuronGenerator_Oscilloscope_widget.clear()
    NeuronGenerator.SetGraph(self)


class NeuronGenerator():

    def DrawNeuron(self):
        t = 0.0
        vs = []
        v = -65.0
        v_thresh = 30.0
        u = 0.0
        time = 250
        time1 = 50
        time2 = 200
        dt = 1.0 / 200.0
        ntime = int(time / dt) + 1
        ntime1 = int(time1 / dt)
        ntime2 = int(time2 / dt)
        nt = np.linspace(0, time, ntime)
        nstim = np.zeros(ntime)
        self.ui.NeuronGenerator_Oscilloscope_widget.clear()
        NeuronGenerator.NeuronUpdateView(self)

        vb = self.ui.NeuronGenerator_Oscilloscope_widget.getViewBox()
        vb.sigResized.connect(lambda: NeuronGenerator.NeuronUpdateView(self))

        self.a = float(self.ui.a_value.text())
        self.b = float(self.ui.b_value.text())
        self.c = float(self.ui.c_value.text())
        self.d = float(self.ui.d_value.text())
        self.I_dc = int(self.ui.StimInt_value.text())

        while t < time:
            vs.append(v)
            dv = (0.04 * v * v) + (5.0 * v) + 140.0 - u
            du = self.a * ((self.b * v) - u)
            if t > 50.0 and t < 200:
                dv += self.I_dc
            v += dv * dt
            u += du * dt
            if v >= v_thresh:
                v = self.c
                u = u + self.d
            t += dt

        nstim[:] = 0
        nstim[ntime1:ntime2] = self.I_dc

        self.ui.NeuronGenerator_Oscilloscope_widget.plot(nt, vs, pen=(DarkSolarized[3]))
        self.StimCurve.setData(nt, nstim)


    def NeuronUpdateView(self):
        self.StimPlot.setGeometry(self.ui.NeuronGenerator_Oscilloscope_widget.getViewBox().sceneBoundingRect())
        self.StimPlot.linkedViewChanged(self.ui.NeuronGenerator_Oscilloscope_widget.getViewBox(), self.StimPlot.XAxis)


    def SetGraph(self):
        t = 0.0
        vs = []
        v = -65.0
        v_thresh = 30.0
        u = 0.0
        time = 250
        time1 = 50
        time2 = 200
        dt = 1.0 / 200.0
        ntime = int(time / dt) + 1
        ntime1 = int(time1 / dt)
        ntime2 = int(time2 / dt)
        nt = np.linspace(0, time, ntime)
        nstim = np.zeros(ntime)
        self.ui.NeuronGenerator_Oscilloscope_widget.showGrid(x=True, y=True)
        self.ui.NeuronGenerator_Oscilloscope_widget.setRange(xRange=[0, time], yRange=[-90, 40])
        self.ui.NeuronGenerator_Oscilloscope_widget.plotItem.vb.setLimits(xMin=0, xMax=time)
        self.ui.NeuronGenerator_Oscilloscope_widget.setBackground(DarkSolarized[0])
        self.ui.NeuronGenerator_Oscilloscope_widget.setLabel('left', 'Membrane potential', 'mV')
        self.ui.NeuronGenerator_Oscilloscope_widget.setLabel('bottom', 'time', 'ms')
        self.ui.NeuronGenerator_Oscilloscope_widget.setLabel('right', 'Current Input', 'a.u.')

        self.StimPlot = pg.ViewBox()
        self.ui.NeuronGenerator_Oscilloscope_widget.scene().addItem(self.StimPlot)
        self.ui.NeuronGenerator_Oscilloscope_widget.getAxis("right").linkToView(self.StimPlot)
        self.StimPlot.setXLink(self.ui.NeuronGenerator_Oscilloscope_widget)
        self.StimPlot.setRange(yRange=[-10, 50])

        self.NeuronCurve = self.ui.NeuronGenerator_Oscilloscope_widget.plot(nt, vs, pen=(DarkSolarized[3]))
        #self.NeuronCurve.clear()
        self.StimCurve = pg.PlotCurveItem(nt, nstim, pen=(DarkSolarized[4]))
        #self.StimCurve.clear()
        self.StimPlot.addItem(self.StimCurve)

    def LoadNeuron(self):
        self.load_neuron_index = self.ui.LoadNeuron_comboBox.currentIndex()
        if self.load_neuron_index == 0:
            self.a = IzhikevichNeurons[0][0]
            self.b = IzhikevichNeurons[0][1]
            self.c = IzhikevichNeurons[0][2]
            self.d = IzhikevichNeurons[0][3]
        if self.load_neuron_index == 1:
            self.a = IzhikevichNeurons[0][0]
            self.b = IzhikevichNeurons[0][1]
            self.c = IzhikevichNeurons[0][2]
            self.d = IzhikevichNeurons[0][3]
        if self.load_neuron_index == 2:
            self.a = IzhikevichNeurons[1][0]
            self.b = IzhikevichNeurons[1][1]
            self.c = IzhikevichNeurons[1][2]
            self.d = IzhikevichNeurons[1][3]
        if self.load_neuron_index == 3:
            self.a = IzhikevichNeurons[2][0]
            self.b = IzhikevichNeurons[2][1]
            self.c = IzhikevichNeurons[2][2]
            self.d = IzhikevichNeurons[2][3]
        if self.load_neuron_index == 4:
            self.a = IzhikevichNeurons[3][0]
            self.b = IzhikevichNeurons[3][1]
            self.c = IzhikevichNeurons[3][2]
            self.d = IzhikevichNeurons[3][3]
        if self.load_neuron_index == 5:
            self.a = IzhikevichNeurons[4][0]
            self.b = IzhikevichNeurons[4][1]
            self.c = IzhikevichNeurons[4][2]
            self.d = IzhikevichNeurons[4][3]
        if self.load_neuron_index == 6:
            self.a = IzhikevichNeurons[5][0]
            self.b = IzhikevichNeurons[5][1]
            self.c = IzhikevichNeurons[5][2]
            self.d = IzhikevichNeurons[5][3]
        if self.load_neuron_index == 7:
            self.a = IzhikevichNeurons[6][0]
            self.b = IzhikevichNeurons[6][1]
            self.c = IzhikevichNeurons[6][2]
            self.d = IzhikevichNeurons[6][3]
        if self.load_neuron_index == 8:
            self.a = IzhikevichNeurons[7][0]
            self.b = IzhikevichNeurons[7][1]
            self.c = IzhikevichNeurons[7][2]
            self.d = IzhikevichNeurons[7][3]
        if self.load_neuron_index == 9:
            self.a = IzhikevichNeurons[8][0]
            self.b = IzhikevichNeurons[8][1]
            self.c = IzhikevichNeurons[8][2]
            self.d = IzhikevichNeurons[8][3]
        if self.load_neuron_index == 10:
            self.a = IzhikevichNeurons[9][0]
            self.b = IzhikevichNeurons[9][1]
            self.c = IzhikevichNeurons[9][2]
            self.d = IzhikevichNeurons[9][3]
        if self.load_neuron_index == 11:
            self.a = IzhikevichNeurons[10][0]
            self.b = IzhikevichNeurons[10][1]
            self.c = IzhikevichNeurons[10][2]
            self.d = IzhikevichNeurons[10][3]
        if self.load_neuron_index == 12:
            self.a = IzhikevichNeurons[11][0]
            self.b = IzhikevichNeurons[11][1]
            self.c = IzhikevichNeurons[11][2]
            self.d = IzhikevichNeurons[11][3]
        if self.load_neuron_index == 13:
            self.a = IzhikevichNeurons[12][0]
            self.b = IzhikevichNeurons[12][1]
            self.c = IzhikevichNeurons[12][2]
            self.d = IzhikevichNeurons[12][3]
        if self.load_neuron_index == 14:
            self.a = IzhikevichNeurons[13][0]
            self.b = IzhikevichNeurons[13][1]
            self.c = IzhikevichNeurons[13][2]
            self.d = IzhikevichNeurons[13][3]
        if self.load_neuron_index == 15:
            self.a = IzhikevichNeurons[14][0]
            self.b = IzhikevichNeurons[14][1]
            self.c = IzhikevichNeurons[14][2]
            self.d = IzhikevichNeurons[14][3]
        if self.load_neuron_index == 16:
            self.a = IzhikevichNeurons[15][0]
            self.b = IzhikevichNeurons[15][1]
            self.c = IzhikevichNeurons[15][2]
            self.d = IzhikevichNeurons[15][3]
        if self.load_neuron_index == 17:
            self.a = IzhikevichNeurons[16][0]
            self.b = IzhikevichNeurons[16][1]
            self.c = IzhikevichNeurons[16][2]
            self.d = IzhikevichNeurons[16][3]
        if self.load_neuron_index == 18:
            self.a = IzhikevichNeurons[17][0]
            self.b = IzhikevichNeurons[17][1]
            self.c = IzhikevichNeurons[17][2]
            self.d = IzhikevichNeurons[17][3]
        if self.load_neuron_index == 19:
            self.a = IzhikevichNeurons[18][0]
            self.b = IzhikevichNeurons[18][1]
            self.c = IzhikevichNeurons[18][2]
            self.d = IzhikevichNeurons[18][3]
        if self.load_neuron_index == 20:
            self.a = IzhikevichNeurons[19][0]
            self.b = IzhikevichNeurons[19][1]
            self.c = IzhikevichNeurons[19][2]
            self.d = IzhikevichNeurons[19][3]

        if self.load_neuron_index <= 20:
            self.neuron_generator_advanced_parameters = _ADVANCED_DEFAULTS

        self.ui.a_value.setText(str(self.a))
        self.ui.b_value.setText(str(self.b))
        self.ui.c_value.setText(str(self.c))
        self.ui.d_value.setText(str(self.d))

    def SaveNeuron(self):
        a = float(self.ui.a_value.text())
        b = float(self.ui.b_value.text())
        c = float(self.ui.c_value.text())
        d = float(self.ui.d_value.text())
        parameters = {
            'a': a,
            'b': b,
            'c': c,
            'd': d,
        }
        parameters.update(zip(_ADVANCED_COLUMNS, _advanced_parameters(self)))

        IzhikNeuron = pd.DataFrame(parameters, index=[0])

        FileName = QFileDialog.getSaveFileName(caption='Save current neuron parameters',
                                               dir=save_dialog_directory(data_directory("Neurons")),
                                               filter='csv files (*.csv)')
        if FileName[0]:
            IzhikNeuron.to_csv(FileName[0], index=False)
