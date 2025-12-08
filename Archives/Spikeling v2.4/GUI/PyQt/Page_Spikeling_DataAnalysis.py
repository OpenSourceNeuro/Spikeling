
########################################################################
#                          Libraries import                            #

from PySide6.QtWidgets import QFileDialog
import pyqtgraph as pg
from pyqtgraph.metaarray import *
import pyqtgraph.exporters

import pandas as pd

import Settings


class Spikeling103():

    def ShowPage(self):
        self.ui.mainbody_stackedWidget.setCurrentWidget(self.ui.page_103)
        self.ui.DataAnalysis_Display_StackedWidget.setCurrentWidget(self.ui.page_103_1_0)
        self.ui.DataAnalysis_Oscilloscope_widget1_0_0.setBackground(Settings.DarkSolarized[1])
        self.ui.DataAnalysis_Oscilloscope_widget1_0_1.setBackground(Settings.DarkSolarized[1])
        self.ui.DataAnalysis_Oscilloscope_widget1_0_2.setBackground(Settings.DarkSolarized[1])
        self.ui.DataAnalysis_Oscilloscope_widget1_0_3.setBackground(Settings.DarkSolarized[1])
        self.ui.DataAnalysis_Oscilloscope_widget1_1_0.setBackground(Settings.DarkSolarized[1])
        self.ui.DataAnalysis_Oscilloscope_widget1_1_1.setBackground(Settings.DarkSolarized[1])
        self.ui.DataAnalysis_Oscilloscope_widget1_1_2.setBackground(Settings.DarkSolarized[1])
        self.ui.DataAnalysis_Oscilloscope_widget1_2_0.setBackground(Settings.DarkSolarized[1])
        self.ui.DataAnalysis_Oscilloscope_widget1_2_1.setBackground(Settings.DarkSolarized[1])
        self.ui.DataAnalysis_Oscilloscope_widget1_2_2.setBackground(Settings.DarkSolarized[1])

    def LoadData(self):
        FileName = QFileDialog.getOpenFileName(caption='Select recording file to load',
                                               dir=".\Recordings",
                                               filter='csv files (*.csv)'
                                               )
        self.DataAnalysis_LoadData_label.setText(FileName[0])

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

    def DisplayRawData(self):
        self.ui.DataAnalysis_Display_StackedWidget.setCurrentWidget(self.ui.page_103_1_0)

        self.ui.df_DataAnalysis_x = self.ui.df_DataAnalysis_Timing

        self.ui.df_DataAnalysis_y0 = np.zeros(len(self.ui.df_DataAnalysis_Vm))
        self.ui.df_DataAnalysis_y0 = self.ui.df_DataAnalysis_Vm

        self.ui.df_DataAnalysis_y1 = np.zeros(len(self.ui.df_DataAnalysis_Vm))
        self.ui.df_DataAnalysis_y1 = self.ui.df_DataAnalysis_ITotal

        self.ui.df_DataAnalysis_y2 = np.zeros(len(self.ui.df_DataAnalysis_Vm))
        self.ui.df_DataAnalysis_y2 = self.ui.df_DataAnalysis_Stimulus

        self.ui.df_DataAnalysis_y3 = np.zeros(len(self.ui.df_DataAnalysis_Vm))
        self.ui.df_DataAnalysis_y3 = self.ui.df_DataAnalysis_Synapse1Vm

        self.ui.df_DataAnalysis_y4 = np.zeros(len(self.ui.df_DataAnalysis_Vm))
        self.ui.df_DataAnalysis_y4 = self.ui.df_DataAnalysis_Synapse1Input

        self.ui.df_DataAnalysis_y5 = np.zeros(len(self.ui.df_DataAnalysis_Vm))
        self.ui.df_DataAnalysis_y5 = self.ui.df_DataAnalysis_Synapse2Vm

        self.ui.df_DataAnalysis_y6 = np.zeros(len(self.ui.df_DataAnalysis_Vm))
        self.ui.df_DataAnalysis_y6 = self.ui.df_DataAnalysis_Synapse2Input

        self.ui.DataAnalysis_Oscilloscope_widget1_0_0.clear()
        self.ui.DataAnalysis_Oscilloscope_widget1_0_0.showGrid(x=True, y=True)
        self.ui.DataAnalysis_Oscilloscope_widget1_0_0.getAxis('bottom').setStyle(showValues=False)
        self.ui.DataAnalysis_Oscilloscope_widget1_0_0.plot(x=self.ui.df_DataAnalysis_x, y=self.ui.df_DataAnalysis_y0,
                                                         pen=(Settings.DarkSolarized[3]))
        self.ui.DataAnalysis_Oscilloscope_widget1_0_1.clear()
        self.ui.DataAnalysis_Oscilloscope_widget1_0_1.showGrid(x=True, y=True)
        self.ui.DataAnalysis_Oscilloscope_widget1_0_1.getAxis('bottom').setStyle(showValues=False)
        self.ui.DataAnalysis_Oscilloscope_widget1_0_1.plot(x=self.ui.df_DataAnalysis_x, y=self.ui.df_DataAnalysis_y1,
                                                         pen=(Settings.DarkSolarized[4]))
        self.ui.DataAnalysis_Oscilloscope_widget1_0_2.clear()
        self.ui.DataAnalysis_Oscilloscope_widget1_0_2.showGrid(x=True, y=True)
        self.ui.DataAnalysis_Oscilloscope_widget1_0_2.getAxis('bottom').setStyle(showValues=False)
        self.ui.DataAnalysis_Oscilloscope_widget1_0_2.plot(x=self.ui.df_DataAnalysis_x, y=self.ui.df_DataAnalysis_y2,
                                                           pen=(Settings.DarkSolarized[5]))
        self.ui.DataAnalysis_Oscilloscope_widget1_0_3.clear()
        self.ui.DataAnalysis_Oscilloscope_widget1_0_3.showGrid(x=True, y=True)
        self.ui.DataAnalysis_Oscilloscope_widget1_0_3.plot(x=self.ui.df_DataAnalysis_x, y=self.ui.df_DataAnalysis_y6,
                                                         pen=(Settings.DarkSolarized[9]))
        self.ui.DataAnalysis_Oscilloscope_widget1_0_3.plot(x=self.ui.df_DataAnalysis_x, y=self.ui.df_DataAnalysis_y4,
                                                         pen=(Settings.DarkSolarized[7]))

        self.ui.DataAnalysis_Oscilloscope_widget1_1_0.clear()
        self.ui.DataAnalysis_Oscilloscope_widget1_1_0.showGrid(x=True, y=True)
        self.ui.DataAnalysis_Oscilloscope_widget1_1_0.getAxis('bottom').setStyle(showValues=False)
        self.ui.DataAnalysis_Oscilloscope_widget1_1_0.plot(x=self.ui.df_DataAnalysis_x, y=self.ui.df_DataAnalysis_y3,
                                                         pen=(Settings.DarkSolarized[6]))
        self.ui.DataAnalysis_Oscilloscope_widget1_1_1.clear()
        self.ui.DataAnalysis_Oscilloscope_widget1_1_1.showGrid(x=True, y=True)
        self.ui.DataAnalysis_Oscilloscope_widget1_1_1.getAxis('bottom').setStyle(showValues=False)
        self.ui.DataAnalysis_Oscilloscope_widget1_1_1.plot(x=self.ui.df_DataAnalysis_x, y=self.ui.df_DataAnalysis_y4,
                                                         pen=(Settings.DarkSolarized[7]))
        self.ui.DataAnalysis_Oscilloscope_widget1_1_2.clear()
        self.ui.DataAnalysis_Oscilloscope_widget1_1_2.showGrid(x=True, y=True)
        self.ui.DataAnalysis_Oscilloscope_widget1_1_2.plot(x=self.ui.df_DataAnalysis_x, y=self.ui.df_DataAnalysis_y2,
                                                           pen=(Settings.DarkSolarized[5]))

        self.ui.DataAnalysis_Oscilloscope_widget1_2_0.clear()
        self.ui.DataAnalysis_Oscilloscope_widget1_2_0.showGrid(x=True, y=True)
        self.ui.DataAnalysis_Oscilloscope_widget1_2_0.getAxis('bottom').setStyle(showValues=False)
        self.ui.DataAnalysis_Oscilloscope_widget1_2_0.plot(x=self.ui.df_DataAnalysis_x, y=self.ui.df_DataAnalysis_y5,
                                                         pen=(Settings.DarkSolarized[8]))
        self.ui.DataAnalysis_Oscilloscope_widget1_2_1.clear()
        self.ui.DataAnalysis_Oscilloscope_widget1_2_1.showGrid(x=True, y=True)
        self.ui.DataAnalysis_Oscilloscope_widget1_2_1.getAxis('bottom').setStyle(showValues=False)
        self.ui.DataAnalysis_Oscilloscope_widget1_2_1.plot(x=self.ui.df_DataAnalysis_x, y=self.ui.df_DataAnalysis_y6,
                                                         pen=(Settings.DarkSolarized[9]))
        self.ui.DataAnalysis_Oscilloscope_widget1_2_2.clear()
        self.ui.DataAnalysis_Oscilloscope_widget1_2_2.showGrid(x=True, y=True)
        self.ui.DataAnalysis_Oscilloscope_widget1_2_2.plot(x=self.ui.df_DataAnalysis_x, y=self.ui.df_DataAnalysis_y2,
                                                           pen=(Settings.DarkSolarized[5]))

        self.ui.DataAnalysis_Oscilloscope_widget1_0_0.setLabel('left', 'Membrane Voltage (mV)')
        self.ui.DataAnalysis_Oscilloscope_widget1_0_1.setLabel('left', 'Input Current (a.u.)')
        self.ui.DataAnalysis_Oscilloscope_widget1_0_2.setLabel('left', 'Intensity')
        self.ui.DataAnalysis_Oscilloscope_widget1_0_3.setLabel('left', 'Synaptic Current (a.u.)')
        self.ui.DataAnalysis_Oscilloscope_widget1_0_3.setLabel('bottom', 'Time (ms)')

        self.ui.DataAnalysis_Oscilloscope_widget1_1_0.setLabel('left', 'Membrane Voltage (mV)')
        self.ui.DataAnalysis_Oscilloscope_widget1_1_1.setLabel('left', 'Synaptic Input (a.u.)')
        self.ui.DataAnalysis_Oscilloscope_widget1_1_2.setLabel('left', 'Intensity')
        self.ui.DataAnalysis_Oscilloscope_widget1_1_2.setLabel('bottom', 'Time (ms)')

        self.ui.DataAnalysis_Oscilloscope_widget1_2_0.setLabel('left', 'Membrane Voltage (mV)')
        self.ui.DataAnalysis_Oscilloscope_widget1_2_1.setLabel('left', 'Synaptic Input (a.u.)')
        self.ui.DataAnalysis_Oscilloscope_widget1_2_2.setLabel('left', 'Intensity')
        self.ui.DataAnalysis_Oscilloscope_widget1_2_2.setLabel('bottom', 'Time (ms)')

        self.ui.DataAnalysis_Spike_lineEdit.setEnabled(True)
        self.ui.DataAnalysis_Spike_Display_pushButton.setEnabled(True)

    def FindSpike(self):
        self.ui.DataAnalysis_Display_StackedWidget.setCurrentWidget(self.ui.page_103_2_0)

        self.spike_threshold = self.ui.DataAnalysis_Spike_lineEdit.text()

        self.n_spikes0 = 0
        self.spike_points0 = []
        self.n_spikes1 = 0
        self.spike_points1 = []
        self.n_spikes2 = 0
        self.spike_points2 = []

        for x in range(1, len(self.ui.df_DataAnalysis_Vm) - 1):
            if (self.ui.df_DataAnalysis_Vm[x] > int(self.spike_threshold) and self.ui.df_DataAnalysis_Vm[x - 1] < int(self.spike_threshold)):  # looks for all instances where subsequent Vm points jump from <10 to >10
                self.spike_points0.append(x)
                self.n_spikes0 += 1
        for x in range(1, len(self.ui.df_DataAnalysis_Synapse1Vm) - 1):
            if (self.ui.df_DataAnalysis_Synapse1Vm[x] > int(self.spike_threshold) and self.ui.df_DataAnalysis_Synapse1Vm[x - 1] < int(self.spike_threshold)):  # looks for all instances where subsequent Vm points jump from <10 to >10
                self.spike_points1.append(x)
                self.n_spikes1 += 1
        for x in range(1, len(self.ui.df_DataAnalysis_Synapse2Vm) - 1):
            if (self.ui.df_DataAnalysis_Synapse2Vm[x] > int(self.spike_threshold) and self.ui.df_DataAnalysis_Synapse2Vm[x - 1] < int(self.spike_threshold)):  # looks for all instances where subsequent Vm points jump from <10 to >10
                self.spike_points2.append(x)
                self.n_spikes2 += 1

        self.ui.DataAnalysis_Spike_result_label.setText(str(self.n_spikes0) + " spikes detected")

        # Compute spike rate
        self.ui.spike_rate0 = np.zeros(len(self.ui.df_DataAnalysis_Vm))
        self.ui.spike_rate1 = np.zeros(len(self.ui.df_DataAnalysis_Synapse1Vm))
        self.ui.spike_rate2 = np.zeros(len(self.ui.df_DataAnalysis_Synapse2Vm))

        for x in range(0, self.n_spikes0 - 1):
            self.current_rate0 = 1 / (self.spike_points0[x + 1] - self.spike_points0[x]) * 10000
            self.ui.spike_rate0[self.spike_points0[x]:self.spike_points0[x + 1]] = self.current_rate0

        for x in range(0, self.n_spikes1 - 1):
            self.current_rate1 = 1 / (self.spike_points1[x + 1] - self.spike_points1[x]) * 10000
            self.ui.spike_rate1[self.spike_points1[x]:self.spike_points1[x + 1]] = self.current_rate1

        for x in range(0, self.n_spikes2 - 1):
            self.current_rate2 = 1 / (self.spike_points2[x + 1] - self.spike_points2[x]) * 10000
            self.ui.spike_rate2[self.spike_points2[x]:self.spike_points2[x + 1]] = self.current_rate2


        self.ui.DataAnalysis_Oscilloscope_widget2_0_0.setBackground(Settings.DarkSolarized[1])
        self.ui.DataAnalysis_Oscilloscope_widget2_0_1.setBackground(Settings.DarkSolarized[1])
        self.ui.DataAnalysis_Oscilloscope_widget2_0_2.setBackground(Settings.DarkSolarized[1])
        self.ui.DataAnalysis_Oscilloscope_widget2_0_3.setBackground(Settings.DarkSolarized[1])
        self.ui.DataAnalysis_Oscilloscope_widget2_1_0.setBackground(Settings.DarkSolarized[1])
        self.ui.DataAnalysis_Oscilloscope_widget2_1_1.setBackground(Settings.DarkSolarized[1])
        self.ui.DataAnalysis_Oscilloscope_widget2_1_2.setBackground(Settings.DarkSolarized[1])
        self.ui.DataAnalysis_Oscilloscope_widget2_1_3.setBackground(Settings.DarkSolarized[1])
        self.ui.DataAnalysis_Oscilloscope_widget2_2_0.setBackground(Settings.DarkSolarized[1])
        self.ui.DataAnalysis_Oscilloscope_widget2_2_1.setBackground(Settings.DarkSolarized[1])
        self.ui.DataAnalysis_Oscilloscope_widget2_2_2.setBackground(Settings.DarkSolarized[1])
        self.ui.DataAnalysis_Oscilloscope_widget2_2_3.setBackground(Settings.DarkSolarized[1])

        self.spike_points0Plot = np.zeros(self.n_spikes0)
        self.spike_points1Plot = np.zeros(self.n_spikes1)
        self.spike_points2Plot = np.zeros(self.n_spikes2)

        for i in range (self.n_spikes0):
            self.spike_points0Plot[i] = self.spike_points0[i] /10

        for i in range (self.n_spikes1):
            self.spike_points1Plot[i] = self.spike_points1[i] /10

        for i in range (self.n_spikes2):
            self.spike_points2Plot[i] = self.spike_points2[i] /10
        self.ui.ySpike0 = np.zeros(len(self.spike_points0))


        for i in range(len(self.spike_points0)):
            self.ui.ySpike0[i] = 45

        self.ui.ySpike1 = np.zeros(len(self.spike_points1))
        for i in range(len(self.spike_points1)):
            self.ui.ySpike1[i] = 45

        self.ui.ySpike2 = np.zeros(len(self.spike_points2))
        for i in range(len(self.spike_points2)):
            self.ui.ySpike2[i] = 45

        self.ui.DataAnalysis_Oscilloscope_widget2_0_0.clear()
        self.ui.DataAnalysis_Oscilloscope_widget2_0_0.showGrid(x=True, y=True)
        self.ui.DataAnalysis_Oscilloscope_widget2_0_0.getAxis('bottom').setStyle(showValues=False)
        self.ui.DataAnalysis_Oscilloscope_widget2_0_0.plot(x=self.ui.df_DataAnalysis_x, y=self.ui.spike_rate0,
                                                           pen=(Settings.DarkSolarized[15]))
        self.ui.DataAnalysis_Oscilloscope_widget2_0_1.clear()
        self.ui.DataAnalysis_Oscilloscope_widget2_0_1.showGrid(x=True, y=True)
        self.ui.DataAnalysis_Oscilloscope_widget2_0_1.getAxis('bottom').setStyle(showValues=False)
        self.ui.DataAnalysis_Oscilloscope_widget2_0_1.plot(x=self.spike_points0Plot, y=self.ui.ySpike0, pen=None,
                                                           symbol='o', symbolBrush=tuple(Settings.DarkSolarized[3]), symbolSize=3)
        self.ui.DataAnalysis_Oscilloscope_widget2_0_1.plot(x=self.ui.df_DataAnalysis_x, y=self.ui.df_DataAnalysis_y0,
                                                           pen=(Settings.DarkSolarized[3]))
        self.ui.DataAnalysis_Oscilloscope_widget2_0_2.clear()
        self.ui.DataAnalysis_Oscilloscope_widget2_0_2.showGrid(x=True, y=True)
        self.ui.DataAnalysis_Oscilloscope_widget2_0_2.getAxis('bottom').setStyle(showValues=False)
        self.ui.DataAnalysis_Oscilloscope_widget2_0_2.plot(x=self.ui.df_DataAnalysis_x, y=self.ui.df_DataAnalysis_y1,
                                                           pen=(Settings.DarkSolarized[4]))
        self.ui.DataAnalysis_Oscilloscope_widget2_0_3.clear()
        self.ui.DataAnalysis_Oscilloscope_widget2_0_3.showGrid(x=True, y=True)
        self.ui.DataAnalysis_Oscilloscope_widget2_0_3.plot(x=self.ui.df_DataAnalysis_x, y=self.ui.df_DataAnalysis_y2,
                                                           pen=(Settings.DarkSolarized[5]))


        self.ui.DataAnalysis_Oscilloscope_widget2_1_0.clear()
        self.ui.DataAnalysis_Oscilloscope_widget2_1_0.showGrid(x=True, y=True)
        self.ui.DataAnalysis_Oscilloscope_widget2_1_0.getAxis('bottom').setStyle(showValues=False)
        self.ui.DataAnalysis_Oscilloscope_widget2_1_0.plot(x=self.ui.df_DataAnalysis_x, y=self.ui.spike_rate1,
                                                           pen=(Settings.DarkSolarized[15]))
        self.ui.DataAnalysis_Oscilloscope_widget2_1_1.clear()
        self.ui.DataAnalysis_Oscilloscope_widget2_1_1.showGrid(x=True, y=True)
        self.ui.DataAnalysis_Oscilloscope_widget2_1_1.getAxis('bottom').setStyle(showValues=False)
        self.ui.DataAnalysis_Oscilloscope_widget2_1_1.plot(x=self.spike_points1Plot, y=self.ui.ySpike1, pen=None,
                                                           symbol='o', symbolBrush=tuple(Settings.DarkSolarized[6]),symbolSize=3)
        self.ui.DataAnalysis_Oscilloscope_widget2_1_1.plot(x=self.ui.df_DataAnalysis_x, y=self.ui.df_DataAnalysis_y3,
                                                           pen=(Settings.DarkSolarized[6]))
        self.ui.DataAnalysis_Oscilloscope_widget2_1_2.clear()
        self.ui.DataAnalysis_Oscilloscope_widget2_1_2.showGrid(x=True, y=True)
        self.ui.DataAnalysis_Oscilloscope_widget2_1_2.getAxis('bottom').setStyle(showValues=False)
        self.ui.DataAnalysis_Oscilloscope_widget2_1_2.plot(x=self.ui.df_DataAnalysis_x, y=self.ui.df_DataAnalysis_y4,
                                                           pen=(Settings.DarkSolarized[7]))
        self.ui.DataAnalysis_Oscilloscope_widget2_1_3.clear()
        self.ui.DataAnalysis_Oscilloscope_widget2_1_3.showGrid(x=True, y=True)
        self.ui.DataAnalysis_Oscilloscope_widget2_1_3.plot(x=self.ui.df_DataAnalysis_x, y=self.ui.df_DataAnalysis_y2,
                                                           pen=(Settings.DarkSolarized[5]))


        self.ui.DataAnalysis_Oscilloscope_widget2_2_0.clear()
        self.ui.DataAnalysis_Oscilloscope_widget2_2_0.showGrid(x=True, y=True)
        self.ui.DataAnalysis_Oscilloscope_widget2_2_0.getAxis('bottom').setStyle(showValues=False)
        self.ui.DataAnalysis_Oscilloscope_widget2_2_0.plot(x=self.ui.df_DataAnalysis_x, y=self.ui.spike_rate2,
                                                           pen=(Settings.DarkSolarized[15]))
        self.ui.DataAnalysis_Oscilloscope_widget2_2_1.clear()
        self.ui.DataAnalysis_Oscilloscope_widget2_2_1.showGrid(x=True, y=True)
        self.ui.DataAnalysis_Oscilloscope_widget2_2_1.getAxis('bottom').setStyle(showValues=False)
        self.ui.DataAnalysis_Oscilloscope_widget2_2_1.plot(x=self.spike_points2Plot, y=self.ui.ySpike2, pen=None,
                                                           symbol='o', symbolBrush=tuple(Settings.DarkSolarized[8]),symbolSize=3)
        self.ui.DataAnalysis_Oscilloscope_widget2_2_1.plot(x=self.ui.df_DataAnalysis_x, y=self.ui.df_DataAnalysis_y3,
                                                           pen=(Settings.DarkSolarized[8]))
        self.ui.DataAnalysis_Oscilloscope_widget2_2_2.clear()
        self.ui.DataAnalysis_Oscilloscope_widget2_2_2.showGrid(x=True, y=True)
        self.ui.DataAnalysis_Oscilloscope_widget2_2_2.getAxis('bottom').setStyle(showValues=False)
        self.ui.DataAnalysis_Oscilloscope_widget2_2_2.plot(x=self.ui.df_DataAnalysis_x, y=self.ui.df_DataAnalysis_y6,
                                                           pen=(Settings.DarkSolarized[9]))
        self.ui.DataAnalysis_Oscilloscope_widget2_2_3.clear()
        self.ui.DataAnalysis_Oscilloscope_widget2_2_3.showGrid(x=True, y=True)
        self.ui.DataAnalysis_Oscilloscope_widget2_2_3.plot(x=self.ui.df_DataAnalysis_x, y=self.ui.df_DataAnalysis_y2,
                                                           pen=(Settings.DarkSolarized[5]))

        self.ui.DataAnalysis_Oscilloscope_widget2_0_0.setLabel('left', 'Spike Rate (Hz)')
        self.ui.DataAnalysis_Oscilloscope_widget2_0_1.setLabel('left', 'Membrane Voltage (mV)')
        self.ui.DataAnalysis_Oscilloscope_widget2_0_2.setLabel('left', 'Input Current (a.u.)')
        self.ui.DataAnalysis_Oscilloscope_widget2_0_3.setLabel('left', 'Intensity')
        self.ui.DataAnalysis_Oscilloscope_widget2_0_3.setLabel('bottom', 'Time (ms)')

        self.ui.DataAnalysis_Oscilloscope_widget2_1_0.setLabel('left', 'Spike Rate (Hz)')
        self.ui.DataAnalysis_Oscilloscope_widget2_1_1.setLabel('left', 'Membrane Voltage (mV)')
        self.ui.DataAnalysis_Oscilloscope_widget2_1_2.setLabel('left', 'Spike Input (a.u.)')
        self.ui.DataAnalysis_Oscilloscope_widget2_1_3.setLabel('left', 'Intensity')
        self.ui.DataAnalysis_Oscilloscope_widget2_1_3.setLabel('bottom', 'Time (ms)')

        self.ui.DataAnalysis_Oscilloscope_widget2_2_0.setLabel('left', 'Spike Rate (Hz)')
        self.ui.DataAnalysis_Oscilloscope_widget2_2_1.setLabel('left', 'Membrane Voltage (mV)')
        self.ui.DataAnalysis_Oscilloscope_widget2_2_2.setLabel('left', 'Spike Input (a.u.)')
        self.ui.DataAnalysis_Oscilloscope_widget2_2_3.setLabel('left', 'Intensity')
        self.ui.DataAnalysis_Oscilloscope_widget2_2_3.setLabel('bottom', 'Time (ms)')

        self.ui.DataAnalysis_Average_Display_pushButton.setEnabled(True)
        self.ui.DataAnalysis_Average_Save_pushButton.setEnabled(True)



    def AverageTraces(self):
    # Display Average traces frame for the main neuron
        self.ui.DataAnalysis_Display_StackedWidget.setCurrentWidget(self.ui.page_103_3_0)

    # Set all plots background
        self.ui.DataAnalysis_Oscilloscope_widget3_0_0.setBackground(Settings.DarkSolarized[1])
        self.ui.DataAnalysis_Oscilloscope_widget3_0_1.setBackground(Settings.DarkSolarized[1])
        self.ui.DataAnalysis_Oscilloscope_widget3_0_2.setBackground(Settings.DarkSolarized[1])
        self.ui.DataAnalysis_Oscilloscope_widget3_0_3.setBackground(Settings.DarkSolarized[1])
        self.ui.DataAnalysis_Oscilloscope_widget3_1_0.setBackground(Settings.DarkSolarized[1])
        self.ui.DataAnalysis_Oscilloscope_widget3_1_1.setBackground(Settings.DarkSolarized[1])
        self.ui.DataAnalysis_Oscilloscope_widget3_1_2.setBackground(Settings.DarkSolarized[1])
        self.ui.DataAnalysis_Oscilloscope_widget3_1_3.setBackground(Settings.DarkSolarized[1])
        self.ui.DataAnalysis_Oscilloscope_widget3_2_0.setBackground(Settings.DarkSolarized[1])
        self.ui.DataAnalysis_Oscilloscope_widget3_2_1.setBackground(Settings.DarkSolarized[1])
        self.ui.DataAnalysis_Oscilloscope_widget3_2_2.setBackground(Settings.DarkSolarized[1])
        self.ui.DataAnalysis_Oscilloscope_widget3_2_3.setBackground(Settings.DarkSolarized[1])

    # Determine single stimulus length
        self.stimulus_times = []
        for x in range(0, len(self.ui.df_DataAnalysis_x) - 1):                           # Goes through each timepoint
            if (self.ui.df_DataAnalysis_Trigger[x] == 1):
                self.stimulus_times.append(x)                                             # Make a list of times  when stimulus increased
        self.loop_duration = self.stimulus_times[1] - self.stimulus_times[0]              # Compute arraylength for single stimulus

    # Generate looped arrays
        self.Spikerate0_loops = []
        self.Spikerate1_loops = []
        self.Spikerate2_loops = []
        self.Vm0_loops = []
        self.Vm1_loops = []
        self.Vm2_loops = []
        self.Spike0_loops = []
        self.Spike1_loops = []
        self.Spike2_loops = []
        self.ITotal_loops = []
        self.ISynpase1_loops = []
        self.ISynpase2_loops = []
        self.Stim_loops = []


    # Looping spike rate traces
        self.Spikerate0_loops = np.vstack(
            [self.ui.spike_rate0[x:x + self.loop_duration] for x in self.stimulus_times[:-1]])
        self.Spikerate1_loops = np.vstack(
            [self.ui.spike_rate1[x:x + self.loop_duration] for x in self.stimulus_times[:-1]])
        self.Spikerate2_loops = np.vstack(
            [self.ui.spike_rate2[x:x + self.loop_duration] for x in self.stimulus_times[:-1]])

    # Looping Vm traces
        self.Vm0_loops = np.vstack(
            [self.ui.df_DataAnalysis_y0[x:x + self.loop_duration] for x in self.stimulus_times[:-1]])
        self.Vm1_loops = np.vstack(
            [self.ui.df_DataAnalysis_y3[x:x + self.loop_duration] for x in self.stimulus_times[:-1]])
        self.Vm2_loops = np.vstack(
            [self.ui.df_DataAnalysis_y5[x:x + self.loop_duration] for x in self.stimulus_times[:-1]])

    # Looping Current traces (total and synaptic)
        self.ITotal_loops = np.vstack(
            [self.ui.df_DataAnalysis_y1[x:x + self.loop_duration] for x in self.stimulus_times[:-1]])
        self.ISynapse1_loops = np.vstack(
            [self.ui.df_DataAnalysis_y4[x:x + self.loop_duration] for x in self.stimulus_times[:-1]])
        self.ISynapse2_loops = np.vstack(
            [self.ui.df_DataAnalysis_y6[x:x + self.loop_duration] for x in self.stimulus_times[:-1]])

    # Calculate the number of loops
        self.Stim_loops = np.vstack(
            [self.ui.df_DataAnalysis_y2[x:x + self.loop_duration] for x in self.stimulus_times[:-1]])

    # Compute main neuron spike
        for i, x in enumerate(self.stimulus_times[:-1]):
            self.Spike0_loops.append(
                [self.ui.df_DataAnalysis_x[sp] - self.ui.df_DataAnalysis_x[x] for sp in self.spike_points0 if sp > x and sp < x + self.loop_duration])
    # Compute auxiliary neuron 1 spike
        for i, x in enumerate(self.stimulus_times[:-1]):
            self.Spike1_loops.append(
                [self.ui.df_DataAnalysis_x[sp] - self.ui.df_DataAnalysis_x[x] for sp in self.spike_points1 if sp > x and sp < x + self.loop_duration])
    # Compute auxiliary neuron 2 spike
        for i, x in enumerate(self.stimulus_times[:-1]):
            self.Spike2_loops.append(
                [self.ui.df_DataAnalysis_x[sp] - self.ui.df_DataAnalysis_x[x] for sp in self.spike_points2 if sp > x and sp < x + self.loop_duration])


    # Print the number of loops on app
        self.ui.DataAnalysis_Average_label.setText(
            str(len(self.Stim_loops)) + " loops (" + str(self.loop_duration/10) + "ms each)")


    ##########
    # Average Traces Plotting
    ##########

    # Generate looped x array
        self.ui.StimLoop_x = np.linspace(0, self.loop_duration/10 - 1, self.loop_duration)


    # Page 103_3_0:
    # Clear previous traces
        self.ui.DataAnalysis_Oscilloscope_widget3_0_0.clear()
        self.ui.DataAnalysis_Oscilloscope_widget3_0_1.clear()
        self.ui.DataAnalysis_Oscilloscope_widget3_0_2.clear()
        self.ui.DataAnalysis_Oscilloscope_widget3_0_3.clear()
    # Set graph display parameters
        self.ui.DataAnalysis_Oscilloscope_widget3_0_0.getAxis('bottom').setStyle(showValues=False)
        self.ui.DataAnalysis_Oscilloscope_widget3_0_0.showGrid(x=True, y=True)
        self.ui.DataAnalysis_Oscilloscope_widget3_0_1.getAxis('bottom').setStyle(showValues=False)
        self.ui.DataAnalysis_Oscilloscope_widget3_0_1.showGrid(x=True, y=False)
        self.ui.DataAnalysis_Oscilloscope_widget3_0_2.getAxis('bottom').setStyle(showValues=False)
        self.ui.DataAnalysis_Oscilloscope_widget3_0_2.showGrid(x=True, y=True)
        self.ui.DataAnalysis_Oscilloscope_widget3_0_3.showGrid(x=True, y=True)
        self.ui.DataAnalysis_Oscilloscope_widget3_0_0.setLabel('left', 'Spike Rate (Hz)')
        self.ui.DataAnalysis_Oscilloscope_widget3_0_1.setLabel('left', 'Loops')
        self.ui.DataAnalysis_Oscilloscope_widget3_0_2.setLabel('left', 'Membrane Voltage (mV)')
        self.ui.DataAnalysis_Oscilloscope_widget3_0_3.setLabel('left', 'Input Current (a.u.)')
        self.ui.DataAnalysis_Oscilloscope_widget3_0_3.setLabel('bottom', 'Time (ms)')

    # For all Loops:
        for i in range(0, len(self.Stim_loops)):
        # Display all Spike rate loops
            self.ui.DataAnalysis_Oscilloscope_widget3_0_0.plot(x=self.ui.StimLoop_x, y=self.Spikerate0_loops[i], pen=(Settings.DarkSolarized[11]))
        # Display all Spikes within loops
            self.ui.ySpikeLoops0 = np.zeros(len(self.Spike0_loops[i]))
            for j in range(len(self.Spike0_loops[i])):
                self.ui.ySpikeLoops0[j] = i
            self.ui.DataAnalysis_Oscilloscope_widget3_0_1.plot(x=self.Spike0_loops[i], y=self.ui.ySpikeLoops0, pen=None, symbol='o', symbolBrush=tuple(Settings.DarkSolarized[3]), symbolSize=5)
            self.ui.DataAnalysis_Oscilloscope_widget3_0_1.setXRange(0, self.loop_duration/10)
        # Display all Vm loops
            self.ui.DataAnalysis_Oscilloscope_widget3_0_2.plot(x=self.ui.StimLoop_x, y=self.Vm0_loops[i], pen=(Settings.DarkSolarized[11]))
        # Display all I_Total loops
            self.ui.DataAnalysis_Oscilloscope_widget3_0_3.plot(x=self.ui.StimLoop_x, y=self.ITotal_loops[i], pen=(Settings.DarkSolarized[11]))

    # Compute average traces
        self.SpikeRate_mean = np.mean(self.Spikerate0_loops, axis=0)
        self.Vm0_mean = np.mean(self.Vm0_loops, axis=0)
        self.ITotal_mean = np.mean(self.ITotal_loops, axis=0)
        self.Stim_mean = np.mean(self.Stim_loops, axis=0)

    # Display Spike rate Average Trace
        self.ui.DataAnalysis_Oscilloscope_widget3_0_0.plot(x=self.ui.StimLoop_x, y=self.SpikeRate_mean, pen={'color':tuple(Settings.DarkSolarized[15]), 'width':3})
    # Display Vm Average Trace
        self.ui.DataAnalysis_Oscilloscope_widget3_0_2.plot(x=self.ui.StimLoop_x, y=self.Vm0_mean, pen={'color':(Settings.DarkSolarized[3]), 'width':3})
    # Display Current Average Trace
        self.ui.DataAnalysis_Oscilloscope_widget3_0_3.plot(x=self.ui.StimLoop_x, y=self.ITotal_mean, pen={'color':(Settings.DarkSolarized[4]), 'width':3})

    # Page 103_3_1:
    # Clear previous traces
        self.ui.DataAnalysis_Oscilloscope_widget3_1_0.clear()
        self.ui.DataAnalysis_Oscilloscope_widget3_1_1.clear()
        self.ui.DataAnalysis_Oscilloscope_widget3_1_2.clear()
        self.ui.DataAnalysis_Oscilloscope_widget3_1_3.clear()
    # Set graph display parameters
        self.ui.DataAnalysis_Oscilloscope_widget3_1_0.showGrid(x=True, y=True)
        self.ui.DataAnalysis_Oscilloscope_widget3_1_0.getAxis('bottom').setStyle(showValues=False)
        self.ui.DataAnalysis_Oscilloscope_widget3_1_1.showGrid(x=True, y=False)
        self.ui.DataAnalysis_Oscilloscope_widget3_1_1.getAxis('bottom').setStyle(showValues=False)
        self.ui.DataAnalysis_Oscilloscope_widget3_1_2.showGrid(x=True, y=True)
        self.ui.DataAnalysis_Oscilloscope_widget3_1_2.getAxis('bottom').setStyle(showValues=False)
        self.ui.DataAnalysis_Oscilloscope_widget3_1_3.showGrid(x=True, y=True)
        self.ui.DataAnalysis_Oscilloscope_widget3_1_0.setLabel('left', 'Spike Rate (Hz)')
        self.ui.DataAnalysis_Oscilloscope_widget3_1_1.setLabel('left', 'Loops')
        self.ui.DataAnalysis_Oscilloscope_widget3_1_2.setLabel('left', 'Membrane Voltage (mV)')
        self.ui.DataAnalysis_Oscilloscope_widget3_1_3.setLabel('left', 'Input Current (a.u.)')
        self.ui.DataAnalysis_Oscilloscope_widget3_1_3.setLabel('bottom', 'Time (ms)')

    # For all loops
        for i in range(0, len(self.Stim_loops) - 1):
        # Display all Spike rate loops
            self.ui.DataAnalysis_Oscilloscope_widget3_1_0.plot(x=self.ui.StimLoop_x, y=self.Spikerate1_loops[i], pen=(Settings.DarkSolarized[11]))
        # Display all Spikes within loops
            self.ui.ySpikeLoops1 = np.zeros(len(self.Spike1_loops[i]))
            for j in range(len(self.Spike1_loops[i])):
                self.ui.ySpikeLoops1[j] = i
            self.ui.DataAnalysis_Oscilloscope_widget3_1_1.plot(x=self.Spike1_loops[i], y=self.ui.ySpikeLoops1,
                                                               pen=None, symbol='o', symbolBrush=tuple(Settings.DarkSolarized[6]),symbolSize=5)
            self.ui.DataAnalysis_Oscilloscope_widget3_1_1.setXRange(0, self.loop_duration)

        # Display all Vm loops
            self.ui.DataAnalysis_Oscilloscope_widget3_1_2.plot(x=self.ui.StimLoop_x, y=self.Vm1_loops[i],
                                                               pen=(Settings.DarkSolarized[11]))
        # Display Synaptic 1 Current
            self.ui.DataAnalysis_Oscilloscope_widget3_1_3.plot(x=self.ui.StimLoop_x, y=self.ISynapse1_loops[i],
                                                               pen=(Settings.DarkSolarized[11]))

    # Compute average traces
        self.SpikeRate1_mean = np.mean(self.Spikerate1_loops, axis=0)
        self.Vm1_mean = np.mean(self.Vm1_loops, axis=0)
        self.ISynapse1_mean = np.mean(self.ISynapse1_loops, axis=0)

    # Display Spike rate Average Trace
        self.ui.DataAnalysis_Oscilloscope_widget3_1_0.plot(x=self.ui.StimLoop_x, y=self.SpikeRate1_mean,
                                                           pen={'color': tuple(Settings.DarkSolarized[15]), 'width': 3})
    # Display Vm Average Trace
        self.ui.DataAnalysis_Oscilloscope_widget3_1_2.plot(x=self.ui.StimLoop_x, y=self.Vm1_mean,
                                                           pen={'color': (Settings.DarkSolarized[6]), 'width': 3})
    # Display Current Average Trace
        self.ui.DataAnalysis_Oscilloscope_widget3_1_3.plot(x=self.ui.StimLoop_x, y=self.ISynapse1_mean,
                                                           pen={'color': (Settings.DarkSolarized[7]), 'width': 3})

    # Page 103_3_2:
    # Clear previous traces
        self.ui.DataAnalysis_Oscilloscope_widget3_2_0.clear()
        self.ui.DataAnalysis_Oscilloscope_widget3_2_1.clear()
        self.ui.DataAnalysis_Oscilloscope_widget3_2_2.clear()
        self.ui.DataAnalysis_Oscilloscope_widget3_2_3.clear()
    # Set graph display parameters
        self.ui.DataAnalysis_Oscilloscope_widget3_2_0.showGrid(x=True, y=True)
        self.ui.DataAnalysis_Oscilloscope_widget3_2_0.getAxis('bottom').setStyle(showValues=False)
        self.ui.DataAnalysis_Oscilloscope_widget3_2_1.showGrid(x=True, y=False)
        self.ui.DataAnalysis_Oscilloscope_widget3_2_1.getAxis('bottom').setStyle(showValues=False)
        self.ui.DataAnalysis_Oscilloscope_widget3_2_2.showGrid(x=True, y=True)
        self.ui.DataAnalysis_Oscilloscope_widget3_2_2.getAxis('bottom').setStyle(showValues=False)
        self.ui.DataAnalysis_Oscilloscope_widget3_2_3.showGrid(x=True, y=True)
        self.ui.DataAnalysis_Oscilloscope_widget3_2_0.setLabel('left', 'Spike Rate (Hz)')
        self.ui.DataAnalysis_Oscilloscope_widget3_2_1.setLabel('left', 'Loops')
        self.ui.DataAnalysis_Oscilloscope_widget3_2_2.setLabel('left', 'Membrane Voltage (mV)')
        self.ui.DataAnalysis_Oscilloscope_widget3_2_3.setLabel('left', 'Input Current (a.u.)')
        self.ui.DataAnalysis_Oscilloscope_widget3_2_3.setLabel('bottom', 'Time (ms)')

    # For all loops
        for i in range(0, len(self.Stim_loops) - 1):
        # Display all Spike rate loops
            self.ui.DataAnalysis_Oscilloscope_widget3_2_0.plot(x=self.ui.StimLoop_x, y=self.Spikerate2_loops[i],
                                                               pen=(Settings.DarkSolarized[11]))

            self.ui.ySpikeLoops2 = np.zeros(len(self.Spike2_loops[i]))
            for j in range(len(self.Spike2_loops[i])):
                self.ui.ySpikeLoops2[j] = i
            self.ui.DataAnalysis_Oscilloscope_widget3_2_1.plot(x=self.Spike2_loops[i], y=self.ui.ySpikeLoops2,
                                                               pen=None, symbol='o', symbolBrush=tuple(Settings.DarkSolarized[8]),symbolSize=5)
            self.ui.DataAnalysis_Oscilloscope_widget3_2_1.setXRange(0, self.loop_duration)

        # Display all Vm loops
            self.ui.DataAnalysis_Oscilloscope_widget3_2_2.plot(x=self.ui.StimLoop_x, y=self.Vm2_loops[i],
                                                               pen=(Settings.DarkSolarized[11]))
        # Display Synaptic 2 Current
            self.ui.DataAnalysis_Oscilloscope_widget3_2_3.plot(x=self.ui.StimLoop_x, y=self.ISynapse2_loops[i],
                                                               pen=(Settings.DarkSolarized[11]))
    # Compute average traces
        self.SpikeRate2_mean = np.mean(self.Spikerate2_loops, axis=0)
        self.Vm2_mean = np.mean(self.Vm2_loops, axis=0)
        self.ISynapse2_mean = np.mean(self.ISynapse2_loops, axis=0)

    # Display Spike rate Average Trace
        self.ui.DataAnalysis_Oscilloscope_widget3_2_0.plot(x=self.ui.StimLoop_x, y=self.SpikeRate2_mean,
                                                           pen={'color': tuple(Settings.DarkSolarized[15]), 'width': 3})
    # Display Vm Average Trace
        self.ui.DataAnalysis_Oscilloscope_widget3_2_2.plot(x=self.ui.StimLoop_x, y=self.Vm2_mean,
                                                           pen={'color': (Settings.DarkSolarized[8]), 'width': 3})
    # Display Current Average Trace
        self.ui.DataAnalysis_Oscilloscope_widget3_2_3.plot(x=self.ui.StimLoop_x, y=self.ISynapse2_mean,
                                                           pen={'color': (Settings.DarkSolarized[9]), 'width': 3})



    def SaveRawDataImage(self):
        FolderName = QFileDialog.getExistingDirectory(caption='Select folder to save graphs on screen',
                                                      dir="./Recordings/Graphs")
        currentStackedWidget = self.ui.DataAnalysis_Display_StackedWidget.currentWidget()

        if currentStackedWidget == self.ui.page_103_1_0:
            exporter100 = pg.exporters.ImageExporter(self.ui.DataAnalysis_Oscilloscope_widget1_0_0.plotItem)
            exporter101 = pg.exporters.ImageExporter(self.ui.DataAnalysis_Oscilloscope_widget1_0_1.plotItem)
            exporter102 = pg.exporters.ImageExporter(self.ui.DataAnalysis_Oscilloscope_widget1_0_2.plotItem)
            exporter103 = pg.exporters.ImageExporter(self.ui.DataAnalysis_Oscilloscope_widget1_0_3.plotItem)
            exporter100.export(FolderName + '/Spikeling Vm.png')
            exporter101.export(FolderName + '/Spikeling Total Input Current.png')
            exporter102.export(FolderName + '/Stimulus.png')
            exporter103.export(FolderName + '/Synaptic Input.png')

        if currentStackedWidget == self.ui.page_103_1_1:
            exporter110 = pg.exporters.ImageExporter(self.ui.DataAnalysis_Oscilloscope_widget1_1_0.plotItem)
            exporter111 = pg.exporters.ImageExporter(self.ui.DataAnalysis_Oscilloscope_widget1_1_1.plotItem)
            exporter112 = pg.exporters.ImageExporter(self.ui.DataAnalysis_Oscilloscope_widget1_1_2.plotItem)
            exporter110.export(FolderName + '/Auxillary Neuron1 Vm.png')
            exporter111.export(FolderName + '/Auxillary Neuron1 Synpatic Input.png')
            exporter112.export(FolderName + '/Stimulus.png')

        if currentStackedWidget == self.ui.page_103_1_2:
            exporter120 = pg.exporters.ImageExporter(self.ui.DataAnalysis_Oscilloscope_widget1_2_0.plotItem)
            exporter121 = pg.exporters.ImageExporter(self.ui.DataAnalysis_Oscilloscope_widget1_2_1.plotItem)
            exporter122 = pg.exporters.ImageExporter(self.ui.DataAnalysis_Oscilloscope_widget1_2_2.plotItem)
            exporter120.export(FolderName + '/Auxillary Neuron2 Vm.png')
            exporter121.export(FolderName + '/Auxillary Neuron2 Synpatic Input.png')
            exporter122.export(FolderName + '/Stimulus.png')


    def SaveSpikeTraces(self):
        FolderName = QFileDialog.getExistingDirectory(caption='Save Spike data traces on screen',
                                                      dir="./Recordings/Data")
        currentStackedWidget = self.ui.DataAnalysis_Display_StackedWidget.currentWidget()

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
        currentStackedWidget = self.ui.DataAnalysis_Display_StackedWidget.currentWidget()

        if currentStackedWidget == self.ui.page_103_2_0:
            exporter200 = pg.exporters.ImageExporter(self.ui.DataAnalysis_Oscilloscope_widget2_0_0.plotItem)
            exporter201 = pg.exporters.ImageExporter(self.ui.DataAnalysis_Oscilloscope_widget2_0_1.plotItem)
            exporter202 = pg.exporters.ImageExporter(self.ui.DataAnalysis_Oscilloscope_widget2_0_2.plotItem)
            exporter203 = pg.exporters.ImageExporter(self.ui.DataAnalysis_Oscilloscope_widget2_0_3.plotItem)
            exporter200.export(FolderName + '/Spikeling Spike Rate.png')
            exporter201.export(FolderName + '/Spikeling Vm & spike.png')
            exporter202.export(FolderName + '/Spikeling Total current.png')
            exporter203.export(FolderName + '/Stimulus.png')

        if currentStackedWidget == self.ui.page_103_2_1:
            exporter210 = pg.exporters.ImageExporter(self.ui.DataAnalysis_Oscilloscope_widget2_1_0.plotItem)
            exporter211 = pg.exporters.ImageExporter(self.ui.DataAnalysis_Oscilloscope_widget2_1_1.plotItem)
            exporter212 = pg.exporters.ImageExporter(self.ui.DataAnalysis_Oscilloscope_widget2_1_2.plotItem)
            exporter213 = pg.exporters.ImageExporter(self.ui.DataAnalysis_Oscilloscope_widget2_1_3.plotItem)
            exporter210.export(FolderName + '/Auxillary Neuron1 Spike Rate.png')
            exporter211.export(FolderName + '/Auxillary Neuron1 Vm & spike.png')
            exporter212.export(FolderName + '/Auxillary Neuron1 Total current.png')
            exporter213.export(FolderName + '/Stimulus.png')

        if currentStackedWidget == self.ui.page_103_2_2:
            exporter220 = pg.exporters.ImageExporter(self.ui.DataAnalysis_Oscilloscope_widget2_2_0.plotItem)
            exporter221 = pg.exporters.ImageExporter(self.ui.DataAnalysis_Oscilloscope_widget2_2_1.plotItem)
            exporter222 = pg.exporters.ImageExporter(self.ui.DataAnalysis_Oscilloscope_widget2_2_2.plotItem)
            exporter223 = pg.exporters.ImageExporter(self.ui.DataAnalysis_Oscilloscope_widget2_2_3.plotItem)
            exporter220.export(FolderName + '/Auxillary Neuron2 Spike Rate.png')
            exporter221.export(FolderName + '/Auxillary Neuron2 Vm & spike.png')
            exporter222.export(FolderName + '/Auxillary Neuron2 Total current.png')
            exporter223.export(FolderName + '/Stimulus.png')

    def SaveAverageTraces(self):
        FolderName = QFileDialog.getExistingDirectory(caption='Save Spike data traces on screen',
                                                      dir="./Recordings/Data")
        currentStackedWidget = self.ui.DataAnalysis_Display_StackedWidget.currentWidget()

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
        currentStackedWidget = self.ui.DataAnalysis_Display_StackedWidget.currentWidget()

        if currentStackedWidget == self.ui.page_103_3_0:
            exporter300 = pg.exporters.ImageExporter(self.ui.DataAnalysis_Oscilloscope_widget3_0_0.plotItem)
            exporter301 = pg.exporters.ImageExporter(self.ui.DataAnalysis_Oscilloscope_widget3_0_1.plotItem)
            exporter302 = pg.exporters.ImageExporter(self.ui.DataAnalysis_Oscilloscope_widget3_0_2.plotItem)
            exporter303 = pg.exporters.ImageExporter(self.ui.DataAnalysis_Oscilloscope_widget3_0_3.plotItem)
            exporter300.export(FolderName + '/Spikeling Spike Rate Average.png')
            exporter301.export(FolderName + '/Spikeling spike rasterplot.png')
            exporter302.export(FolderName + '/Spikeling Vm Average.png')
            exporter303.export(FolderName + '/Spikeling Total Current Average.png')

        if currentStackedWidget == self.ui.page_103_3_1:
            exporter310 = pg.exporters.ImageExporter(self.ui.DataAnalysis_Oscilloscope_widget3_1_0.plotItem)
            exporter311 = pg.exporters.ImageExporter(self.ui.DataAnalysis_Oscilloscope_widget3_1_1.plotItem)
            exporter312 = pg.exporters.ImageExporter(self.ui.DataAnalysis_Oscilloscope_widget3_1_2.plotItem)
            exporter313 = pg.exporters.ImageExporter(self.ui.DataAnalysis_Oscilloscope_widget3_1_3.plotItem)
            exporter310.export(FolderName + '/AuxNeuron1 Spike Rate Average.png')
            exporter311.export(FolderName + '/AuxNeuron1 spike rasterplot.png')
            exporter312.export(FolderName + '/AuxNeuron1 Vm Average.png')
            exporter313.export(FolderName + '/AuxNeuron1 Synapse Current Average.png')

        if currentStackedWidget == self.ui.page_103_3_2:
            exporter320 = pg.exporters.ImageExporter(self.ui.DataAnalysis_Oscilloscope_widget3_2_0.plotItem)
            exporter321 = pg.exporters.ImageExporter(self.ui.DataAnalysis_Oscilloscope_widget3_2_1.plotItem)
            exporter322 = pg.exporters.ImageExporter(self.ui.DataAnalysis_Oscilloscope_widget3_2_2.plotItem)
            exporter323 = pg.exporters.ImageExporter(self.ui.DataAnalysis_Oscilloscope_widget3_2_3.plotItem)
            exporter320.export(FolderName + '/AuxNeuron2 Spike Rate Average.png')
            exporter321.export(FolderName + '/AuxNeuron2 spike rasterplot.png')
            exporter322.export(FolderName + '/AuxNeuron2 Vm Average.png')
            exporter323.export(FolderName + '/AuxNeuron2 Synapse Current Average.png')



