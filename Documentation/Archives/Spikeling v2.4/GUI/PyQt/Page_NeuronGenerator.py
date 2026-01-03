from PySide6.QtWidgets import QFileDialog, QWidget
import numpy as np
import pandas as pd
import pyqtgraph as pg
import Settings
from Izhikevich_parameters import IzhikevichNeurons



def ShowPage(self):
    self.ui.mainbody_stackedWidget.setCurrentWidget(self.ui.page_301)
    self.ui.NeuronGenerator_Oscilloscope_widget.clear()
    NeuronGenerator.SetGraph(self)

    self.ui.NeuronParameter_PRGain = 0
    self.ui.NeuronParameter_PRDecay = 0.001
    self.ui.NeuronParameter_PRRecovery = 0.025

    self.ui.NeuronParameter_Syn1Gain = 0
    self.ui.NeuronParameter_Syn1Decay = 0.995

    self.ui.NeuronParameter_Syn2Gain = 0
    self.ui.NeuronParameter_Syn2Decay = 0.995

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
        self.ui.NeuronGenerator_Oscilloscope_widget.getViewBox().sigResized.connect(NeuronGenerator.NeuronUpdateView(self))

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

        self.ui.NeuronGenerator_Oscilloscope_widget.plot(nt, vs, pen=(Settings.DarkSolarized[3]))
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
        self.ui.NeuronGenerator_Oscilloscope_widget.setBackground(Settings.DarkSolarized[0])
        self.ui.NeuronGenerator_Oscilloscope_widget.setLabel('left', 'Membrane potential', 'mV')
        self.ui.NeuronGenerator_Oscilloscope_widget.setLabel('bottom', 'time', 'ms')
        self.ui.NeuronGenerator_Oscilloscope_widget.setLabel('right', 'Current Input', 'a.u.')

        self.StimPlot = pg.ViewBox()
        self.ui.NeuronGenerator_Oscilloscope_widget.scene().addItem(self.StimPlot)
        self.ui.NeuronGenerator_Oscilloscope_widget.getAxis("right").linkToView(self.StimPlot)
        self.StimPlot.setXLink(self.ui.NeuronGenerator_Oscilloscope_widget)
        self.StimPlot.setRange(yRange=[-10, 50])

        self.NeuronCurve = self.ui.NeuronGenerator_Oscilloscope_widget.plot(nt, vs, pen=(Settings.DarkSolarized[3]))
        #self.NeuronCurve.clear()
        self.StimCurve = pg.PlotCurveItem(nt, nstim, pen=(Settings.DarkSolarized[4]))
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
        if self.load_neuron_index <= 12:
            self.ui.NeuronParameter_PRGain = 0
            self.ui.NeuronParameter_PRDecay = 0.001
            self.ui.NeuronParameter_PRRecovery = 0.025
            self.ui.NeuronParameter_Syn1Gain = 0
            self.ui.NeuronParameter_Syn1Decay = 0.995
            self.ui.NeuronParameter_Syn2Gain = 0
            self.ui.NeuronParameter_Syn2Decay = 0.995

        self.ui.a_value.setText(str(self.a))
        self.ui.b_value.setText(str(self.b))
        self.ui.c_value.setText(str(self.c))
        self.ui.d_value.setText(str(self.d))

    def SaveNeuron(self):
        a = float(self.ui.a_value.text())
        b = float(self.ui.b_value.text())
        c = float(self.ui.c_value.text())
        d = float(self.ui.d_value.text())
        dict = {
            'a': a,
            'b': b,
            'c': c,
            'd': d,
            'PhotoGain( %)': self.ui.NeuronParameter_PRGain,
            'PhotoDecay(1 / ms)': self.ui.NeuronParameter_PRDecay,
            'PhotoRecovery(1 / ms)': self.ui.NeuronParameter_PRRecovery,
            'Syn1 Gain( %)': self.ui.NeuronParameter_Syn1Gain,
            'Syn1 Decay(1 / ms)': self.ui.NeuronParameter_Syn1Decay,
            'Syn2 Gain( %)': self.ui.NeuronParameter_Syn2Gain,
            'Syn2 Decay(1 / ms)': self.ui.NeuronParameter_Syn2Decay
            }

        IzhikNeuron = pd.DataFrame(dict, index=[0])

        FileName = QFileDialog.getSaveFileName(caption='Save current neuron parameters',
                                               dir="./Neurons",
                                               filter='csv files (*.csv)')
        IzhikNeuron.to_csv(FileName[0], index = False)

