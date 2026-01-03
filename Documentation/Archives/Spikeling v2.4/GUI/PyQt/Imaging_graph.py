"""
Imaging Graph Module

This module provides functionality for plotting and recording data from the Spikeling device and computing the imaging simulation.
It handles data visualization, and data export.
"""

########################################################################
#                          Libraries import                            #

from PySide6.QtCore import QObject, QTimer
from PySide6.QtGui import QPen
import pyqtgraph as pg

import numpy as np
import pandas as pd
import collections
from decimal import Decimal

import Settings
from serial_manager import serial_manager


# Constants
DOWNSAMPLING = 5
SAMPLE_INTERVAL = 0.1
TIME_WINDOW = 500
PEN_WIDTH = 1
STIM_MIN = -100
STIM_MAX = 100


class ImagingGraph(QObject):
    """
    Class for handling Imaging data visualization and recording.

    This class manages the connection to the Spikeling data, data acquisition,
    plotting, and recording of the data to CSV files.
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.ui = parent.ui

        # state
        self.data = ['0'] * 8
        self.last_valid_data = None
        self.record_flag = False
        self.secondaryVB = None

        # Set ConnectionFlag in parent for use in Page201
        self.parent.ImagingConnectionFlag = False


        # Start QTimer for plotting
        self.imagingtimer = QTimer()
        self.imagingtimer.timeout.connect(self.update_plot)

        # Connect to serial_manager data signal
        serial_manager.data_received.connect(self.on_data_received)



    # -------------------------------------------------------------------------
    # Connection Management
    # -------------------------------------------------------------------------
    def connect(self):
        """Called when connect button is checked."""
        ## Need to add a flag here coneting to spikeling plot with a pop up message
        # Initialize buffers and plotting
        self.set_init_parameters()
        self.set_plot()

        self.parent.ImagingConnectionFlag = True

        self.imagingtimer.start() # add time frame from microsope here


    def disconnect(self):
        self.cleanup()
        self.parent.ImagingConnectionFlag = False

        self.ui.Imaging_pushButton.setText("Connect Imaging screen to Spikeling screen")
        self.ui.Imaging_pushButton.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[14])) + ";\n"
                                                 "background-color: rgb" + str(tuple(Settings.DarkSolarized[2])) + ";\n"
                                                 "border: 1px solid rgb" + str(tuple(Settings.DarkSolarized[14])) + ";\n"
                                                 "border-radius: 10px;"
                                                )



    # -------------------------------------------------------------------------
    # Data Handling
    # -------------------------------------------------------------------------
    def on_data_received(self, data):
        """Slot for serial_manager.data_received signal."""
        if data and len(data) == 8:
            self.ImagingData = data
            self.last_valid_data = data


    def update_plot(self):
        """Main loop: called periodically by QTimer."""
        try:
            self.compute_data()
            self.buff_data()
            self.save_plot_data()
            self.plot_curve()


        except Exception as e:
            print(f"Error in update_plot: {e}")



    # -------------------------------------------------------------------------
    # Initialization Methods
    # -------------------------------------------------------------------------
    def set_init_parameters(self):
        """
        Initialize parameters for Spikeling plotting.
        """
        # Recording flag
        self.Imagingrecordflag = False

        # Parameters
        self.CalciumData1 = 0.1
        self.CalciumData2 = 0.1
        self.CalciumData3 = 0.1
        self.SpikeThreshold = -20
        self.CalciumDecay = 0.05
        self.SpikeCa = 200.0
        self.SatNoise1 = 0.0
        self.SatNoise2 = 0.0
        self.SatNoise3 = 0.0
        self.FluoScale = 1.0
        self.DissociationConstant = 300.0
        self.HillCoef = 4.0
        self.Laser = 1.0
        self.PMT = 1.0
        self.FluoOffset = 0.0
        self.update_interval = 10

        # Buffers for calcium, fluorescence, Vm, stimulus, trigger
        self._Imaging_bufsize = int(TIME_WINDOW / SAMPLE_INTERVAL)

        # Initialize data buffers
        self.Stimdatabuffer = collections.deque([0.0] * self._Imaging_bufsize, self._Imaging_bufsize)
        self.Triggerdatabuffer = collections.deque([0.0] * self._Imaging_bufsize, self._Imaging_bufsize)

        self.Fluodatabuffer1 = collections.deque([0.0] * self._Imaging_bufsize, self._Imaging_bufsize)
        self.Calciumdatabuffer1 = collections.deque([0.0] * self._Imaging_bufsize, self._Imaging_bufsize)
        self.Vmdatabuffer1 = collections.deque([0.0] * self._Imaging_bufsize, self._Imaging_bufsize)

        self.Fluodatabuffer2 = collections.deque([0.0] * self._Imaging_bufsize, self._Imaging_bufsize)
        self.Calciumdatabuffer2 = collections.deque([0.0] * self._Imaging_bufsize, self._Imaging_bufsize)
        self.Vmdatabuffer2 = collections.deque([0.0] * self._Imaging_bufsize, self._Imaging_bufsize)

        self.Fluodatabuffer3 = collections.deque([0.0] * self._Imaging_bufsize, self._Imaging_bufsize)
        self.Calciumdatabuffer3 = collections.deque([0.0] * self._Imaging_bufsize, self._Imaging_bufsize)
        self.Vmdatabuffer3 = collections.deque([0.0] * self._Imaging_bufsize, self._Imaging_bufsize)

        # Numpy arrays for plotting
        self.Imagingx  = np.linspace(-TIME_WINDOW, 0.0, self._Imaging_bufsize)            # Create arrays of self._Imaging_bufsize length

        self.yCalcium1 = np.zeros(self._Imaging_bufsize, dtype=float)
        self.yCalcium2 = np.zeros(self._Imaging_bufsize, dtype=float)
        self.yCalcium3 = np.zeros(self._Imaging_bufsize, dtype=float)
        self.yFluo1    = np.zeros(self._Imaging_bufsize, dtype=float)
        self.yFluo2    = np.zeros(self._Imaging_bufsize, dtype=float)
        self.yFluo3    = np.zeros(self._Imaging_bufsize, dtype=float)
        self.yVm1      = np.zeros(self._Imaging_bufsize, dtype=float)
        self.yVm2      = np.zeros(self._Imaging_bufsize, dtype=float)
        self.yVm3      = np.zeros(self._Imaging_bufsize, dtype=float)
        self.yStim     = np.zeros(self._Imaging_bufsize, dtype=float)

        # Internal calcium state for computation
        self.CalciumData1 = 0.0
        self.CalciumData2 = 0.0
        self.CalciumData3 = 0.0
        self.FluoData1 = 0.0
        self.FluoData2 = 0.0
        self.FluoData3 = 0.0

        # Data recording arrays
        self.imaging_data = []
        for _ in range(12):
            self.imaging_data.append([])

        # Set button appearance
        if self.ui.Imaging_ConnectButton.isChecked():
            self.ui.Imaging_ConnectButton.setText("Connected")
            self.ui.Imaging_ConnectButton.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[3])) + ";\n"
                                                        "background-color: rgb" + str(tuple(Settings.DarkSolarized[11])) + ";\n"
                                                        "border: 1px solid rgb" + str(tuple(Settings.DarkSolarized[14])) + ";\n"
                                                        "border-radius: 10px;"
                                                        )
        else:
            self.ui.Imaging_ConnectButton.setText("Connect Imaging screen to Spikeling screen")
            self.ui.Imaging_ConnectButton.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[14])) + ";\n"
                                                        "background-color: rgb" + str(tuple(Settings.DarkSolarized[2])) + ";\n"
                                                        "border: 1px solid rgb" + str(tuple(Settings.DarkSolarized[14])) + ";\n"
                                                        "border-radius: 10px;"
                                                        )



    # -------------------------------------------------------------------------
    # Buffers + Computing + Plotting
    # -------------------------------------------------------------------------

    def buff_data(self):
        try:
            self.Stimdatabuffer.append(self.StimData)
            self.Triggerdatabuffer.append(self.TriggerData)

            self.Fluodatabuffer1.append(self.FluoData1)
            self.Calciumdatabuffer1.append(self.CalciumData1)
            self.Vmdatabuffer1.append(self.VmData1)

            self.Fluodatabuffer2.append(self.FluoData2)
            self.Calciumdatabuffer2.append(self.CalciumData2)
            self.Vmdatabuffer2.append(self.VmData2)

            self.Fluodatabuffer3.append(self.FluoData3)
            self.Calciumdatabuffer3.append(self.CalciumData3)
            self.Vmdatabuffer3.append(self.VmData3)

        except Exception as e:
            print(f"Error in buff_data: {e}")


    def compute_data(self):
        try:
            # Extract floats
            self.VmData1 = self.ImagingData[0]
            self.VmData2 = self.ImagingData[3]
            self.VmData3 = self.ImagingData[5]
            self.TriggerData = self.ImagingData[7]
            self.StimData = self.ImagingData[1]

            # Imaging parameters
            self.FrameRate = self.ui.Imaging_FrameRate_Slider.value()
            self.ImagingDelta = 1 / self.FrameRate * 10000  # imaging resolution in ms
            self.PMT = self.ui.Imaging_PMT_Slider.value() / 100
            self.Laser = self.ui.Imaging_Laser_Slider.value() / 100

            # Calcium parameters
            self.CalciumDecay = self.ui.Imaging_CalciumDecay_Slider.value() / 10000  # Indicator decay constant in ms
            self.SpikeOccurence = 0  # number of spike at t
            self.SpikeConcentrationRise = self.ui.Imaging_CalciumJump_Slider.value()  # calcicum concentration rise for each spike in micromolar
            self.CalciumBaseline = self.ui.Imaging_CalciumBaseline_Slider.value() / 100  # in micromolar
            self.NoiseScale = self.ui.Imaging_CalciumNoise_Slider.value() / 10  # sigmac

            # Fluorescence parameters
            self.FluoScale = self.ui.Imaging_FluoScale_Slider.value() / 10
            self.FluoOffset = self.ui.Imaging_FluoOffset_Slider.value()
            self.FluoNoiseScale = self.ui.Imaging_FluoNoise_Slider.value() / 10
            self.HillCoef = self.ui.Imaging_Hill_Slider.value() / 100
            self.PhotoShotNoise = self.ui.Imaging_PhotoShotNoise_Slider.value() / 10000 / 100
            self.DissociationConstant = self.ui.Imaging_kd_Slider.value() * 10  # micromolar

            if float(self.Vmdatabuffer1[-1]) >= self.SpikeThreshold and float(self.Vmdatabuffer1[-2]) <= self.SpikeThreshold:
                self.SpikeOccurence1 = 1
            else:
                self.SpikeOccurence1 = 0

            if float(self.Vmdatabuffer2[-1]) >= self.SpikeThreshold and float(self.Vmdatabuffer2[-2]) <= self.SpikeThreshold:
                self.SpikeOccurence2 = 1
            else:
                self.SpikeOccurence2 = 0

            if float(self.Vmdatabuffer3[-1]) >= self.SpikeThreshold and float(self.Vmdatabuffer3[-2]) <= self.SpikeThreshold:
                self.SpikeOccurence3 = 1
            else:
                self.SpikeOccurence3 = 0

            self.CalciumGaussianNoise1 = np.random.normal(0, 1)
            self.CalciumData1 = self.CalciumData1 - self.CalciumDecay * self.CalciumData1 + self.CalciumBaseline + self.SpikeConcentrationRise * self.SpikeOccurence1 + self.NoiseScale * np.sqrt(self.ImagingDelta / 10000) * self.CalciumGaussianNoise1

            self.CalciumGaussianNoise2 = np.random.normal(0, 1)
            self.CalciumData2 = self.CalciumData2 - self.CalciumDecay * self.CalciumData2 + self.CalciumBaseline + self.SpikeConcentrationRise * self.SpikeOccurence2 + self.NoiseScale * np.sqrt(self.ImagingDelta / 10000) * self.CalciumGaussianNoise2

            self.CalciumGaussianNoise3 = np.random.normal(0, 1)
            self.CalciumData3 = self.CalciumData3 - self.CalciumDecay * self.CalciumData3 + self.CalciumBaseline + self.SpikeConcentrationRise * self.SpikeOccurence3 + self.NoiseScale * np.sqrt(self.ImagingDelta / 10000) * self.CalciumGaussianNoise3

            self.FluoNoiseScale = self.FluoNoiseScale / 10000

            self.FluoGaussianNoise1 = np.random.normal(0, 1)
            self.SatNoise1 = np.sqrt(self.PhotoShotNoise * self.CalciumData1 ** self.HillCoef / (self.CalciumData1 ** self.HillCoef + self.DissociationConstant) + self.FluoNoiseScale) * self.FluoGaussianNoise1
            self.FluoData1 = self.DissociationConstant * (self.Laser * self.PMT * self.FluoScale * (self.CalciumData1 ** self.HillCoef / (self.CalciumData1 ** self.HillCoef + self.DissociationConstant)) + self.SatNoise1) + self.FluoOffset

            self.FluoGaussianNoise2 = np.random.normal(0, 1)
            self.SatNoise2 = np.sqrt(self.PhotoShotNoise * self.CalciumData2 ** self.HillCoef / (self.CalciumData2 ** self.HillCoef + self.DissociationConstant) + self.FluoNoiseScale) * self.FluoGaussianNoise2
            self.FluoData2 = self.DissociationConstant * (self.Laser * self.PMT * self.FluoScale * (self.CalciumData2 ** self.HillCoef / (self.CalciumData2 ** self.HillCoef + self.DissociationConstant)) + self.SatNoise2) + self.FluoOffset

            self.FluoGaussianNoise3 = np.random.normal(0, 1)
            self.SatNoise3 = np.sqrt(self.PhotoShotNoise * self.CalciumData3 ** self.HillCoef / (self.CalciumData3 ** self.HillCoef + self.DissociationConstant) + self.FluoNoiseScale) * self.FluoGaussianNoise3
            self.FluoData3 = self.DissociationConstant * (self.Laser * self.PMT * self.FluoScale * (self.CalciumData3 ** self.HillCoef / ( self.CalciumData3 ** self.HillCoef + self.DissociationConstant)) + self.SatNoise3) + self.FluoOffset

        except Exception as e:
            print(f"Error in compute_data: {e}")


    def set_plot(self):
        """
        Set up the plot widget and curves.
        """
        # Main plot setup
        pw = self.ui.Imaging_Oscilloscope_widget
        pw.showGrid(x=True, y=True)
        pw.setRange(xRange=[-TIME_WINDOW, 0])

        # Set axis labels
        pw.setLabel('left', 'Fluorescence  /  [Ca2+]    ', 'a.u.  /  µM')
        pw.setLabel('bottom', 'time', 'ms')
        pw.setLabel('right', 'Stimulus Intensity / Vm', 'a.u. / mV')
        pw.setAntialiasing(True)


        # -----------------------------
        # Setup secondary ViewBox
        # -----------------------------
        self.secondaryVB = pg.ViewBox()
        pw.scene().addItem(self.secondaryVB)
        self.secondaryVB.setXLink(pw)
        self.secondaryVB.setRange(yRange=[STIM_MIN, STIM_MAX])
        pw.getAxis("right").linkToView(self.secondaryVB)

        # Create plot curves for calcium and fluorescence on the main plot with anti-aliasing
        self.Calciumcurve1 = self.ui.Imaging_Oscilloscope_widget.plot(self.Imagingx, self.yCalcium1, pen=pg.mkPen(Settings.DarkSolarized[10], width=PEN_WIDTH, cosmetic=True))
        self.Calciumcurve1.clear()
        self.Calciumcurve2 = self.ui.Imaging_Oscilloscope_widget.plot(self.Imagingx, self.yCalcium2, pen=pg.mkPen(Settings.DarkSolarized[9], width=PEN_WIDTH, cosmetic=True))
        self.Calciumcurve2.clear()
        self.Calciumcurve3 = self.ui.Imaging_Oscilloscope_widget.plot(self.Imagingx, self.yCalcium3, pen=pg.mkPen(Settings.DarkSolarized[7], width=PEN_WIDTH, cosmetic=True))
        self.Calciumcurve3.clear()

        self.Fluocurve1 = self.ui.Imaging_Oscilloscope_widget.plot(self.Imagingx, self.yFluo1, pen=pg.mkPen(Settings.DarkSolarized[4], width=PEN_WIDTH, cosmetic=True))
        self.Fluocurve1.clear()
        self.Fluocurve2 = self.ui.Imaging_Oscilloscope_widget.plot(self.Imagingx, self.yFluo2, pen=pg.mkPen([0, 255, 133], width=PEN_WIDTH, cosmetic=True))
        self.Fluocurve2.clear()
        self.Fluocurve3 = self.ui.Imaging_Oscilloscope_widget.plot(self.Imagingx, self.yFluo3, pen=pg.mkPen([133, 255, 0], width=PEN_WIDTH, cosmetic=True))
        self.Fluocurve3.clear()

        # Create plot curves for Vmand stimulus (secondary plot - right y-axis) with anti-aliasing
        self.Vmcurve1 = pg.PlotCurveItem(self.Imagingx, self.yVm1, pen=pg.mkPen(Settings.DarkSolarized[3], width=PEN_WIDTH, cosmetic=True))
        self.Vmcurve1.clear()
        self.Vmcurve2 = pg.PlotCurveItem(self.Imagingx, self.yVm2, pen=pg.mkPen(Settings.DarkSolarized[6], width=PEN_WIDTH, cosmetic=True))
        self.Vmcurve2.clear()
        self.Vmcurve3 = pg.PlotCurveItem(self.Imagingx, self.yVm3, pen=pg.mkPen(Settings.DarkSolarized[8], width=PEN_WIDTH, cosmetic=True))
        self.Vmcurve3.clear()

        self.Stimcurve = pg.PlotCurveItem(self.Imagingx, self.yStim, pen=pg.mkPen(Settings.DarkSolarized[5], width=PEN_WIDTH, cosmetic=True))
        self.Stimcurve.clear()

        # Add current and stimulus curves to the secondary plot (right y-axis)
        self.secondaryVB.addItem(self.Vmcurve1)
        self.secondaryVB.addItem(self.Vmcurve2)
        self.secondaryVB.addItem(self.Vmcurve3)
        self.secondaryVB.addItem(self.Stimcurve)

        # Update secondary ViewBox when main plot resizes
        def update_views():
            self.secondaryVB.setGeometry(pw.getViewBox().sceneBoundingRect())
            self.secondaryVB.linkedViewChanged(pw.getViewBox(), self.secondaryVB.XAxis)

        pw.getViewBox().sigResized.connect(update_views)


    def plot_curve(self):
        """
        Update the plot curves with the latest data from buffers.
        """
        try:
            # Check if all required attributes are initialized
            required_attrs = ['Imagingx', 'yCalcium1', 'yCalcium2', 'yCalcium3', 'yFluo1', 'yFluo2', 'yFluo3', 'yVm1', 'yVm2', 'yVm3', 'yStim'
                              'Calciumcurve1', 'Calciumcurve2', 'Calciumcurve3', 'Fluocurve1', 'Fluocurve2', 'Fluocurve3', 'Vmcurve1', 'Vmcurve2', 'Vmcurve3', 'Stimcurve',
                              'Calciumdatabuffer1', 'Calciumdatabuffer2', 'Calciumdatabuffer3', 'Fluodatabuffer1','Fluodatabuffer2', 'Fluodatabuffer3', 'Vmdatabuffer1', 'Vmdatabuffer2', 'Vmdatabuffer3', 'Stimdatabuffer']

            # Plot calcium on the main plots
            if self.ui.Imaging_Calcium1_Checkbox.isChecked():
                self.yCalcium1[:] = self.Calciumdatabuffer1
                self.Calciumcurve1.setData(self.Imagingx, self.yCalcium1)
            else:
                self.Calciumcurve1.clear()

            if self.ui.Imaging_Calcium2_Checkbox.isChecked():
                self.yCalcium2[:] = self.Calciumdatabuffer2
                self.Calciumcurve2.setData(self.Imagingx, self.yCalcium2)
            else:
                self.Calciumcurve2.clear()

            if self.ui.Imaging_Calcium3_Checkbox.isChecked():
                self.yCalcium3[:] = self.Calciumdatabuffer3
                self.Calciumcurve3.setData(self.Imagingx, self.yCalcium3)
            else:
                self.Calciumcurve3.clear()

            # Plot fluorescence on the main plot
            if self.ui.Imaging_Fluorescence1_Checkbox.isChecked():
                self.yFluo1[:] = self.Fluodatabuffer1
                self.Fluocurve1.setData(self.Imagingx, self.yFluo1)
            else:
                self.Fluocurve1.clear()

            if self.ui.Imaging_Fluorescence2_Checkbox.isChecked():
                self.yFluo2[:] = self.Fluodatabuffer2
                self.Fluocurve2.setData(self.Imagingx, self.yFluo2)
            else:
                self.Fluocurve2.clear()

            if self.ui.Imaging_Fluorescence3_Checkbox.isChecked():
                self.yFluo3[:] = self.Fluodatabuffer3
                self.Fluocurve3.setData(self.Imagingx, self.yFluo3)
            else:
                self.Fluocurve3.clear()

            # Plot membrane potentials on the main plot
            if self.ui.Imaging_Vm1_Checkbox.isChecked():
                self.yVm1[:] = self.Vmdatabuffer1
                self.Vmcurve1.setData(self.Imagingx, self.yVm1)
            else:
                self.Vmcurve1.clear()

            if self.ui.Imaging_Vm2_Checkbox.isChecked():
                self.yVm2[:] = self.Vmdatabuffer2
                self.Vmcurve2.setData(self.Imagingx, self.yVm2)
            else:
                self.Vmcurve2.clear()

            if self.ui.Imaging_Vm3_Checkbox.isChecked():
                self.yVm3[:] = self.Vmdatabuffer3
                self.Vmcurve3.setData(self.Imagingx, self.yVm3)
            else:
                self.Vmcurve3.clear()

            # Plot stimulus on the main plot
            if self.ui.Imaging_Stimulus_Checkbox.isChecked():
                self.yStim[:] = self.Stimdatabuffer
                self.Stimcurve.setData(self.Imagingx, self.yStim)
            else:
                self.Stimcurve.clear()

            # Secondary ViewBox auto-syncs y-axis (current/stimulus)
            self.secondaryVB.setGeometry(self.ui.Imaging_Oscilloscope_widget.getViewBox().sceneBoundingRect())


        except Exception as e:
            print(f"Error in plot_curve: {e}")



    # -------------------------------------------------------------------------
    # Saving Data
    # -------------------------------------------------------------------------

    def save_plot_data(self):
        """
        Save the latest buffer data and export them as CSV when recording is stopped.
        """
        # If recording was on and is now turned off, save the data
        if not self.ui.Imaging_DataRecording_Record_pushButton.isChecked() and self.record_flag:
            self.export_data_to_csv()
            self.record_flag = False
            # Clear data arrays
            for i in range(12):
                self.imaging_data[i].clear()

        # If recording is on, append data to arrays
        if self.ui.Imaging_DataRecording_Record_pushButton.isChecked():
            self.record_flag = True

            # Append latest data points to recording arrays
            self.imaging_data[1].append(self.Stimdatabuffer[-1])
            self.imaging_data[2].append(self.Triggerdatabuffer[-1])
            self.imaging_data[3].append(self.Fluodatabuffer1[-1])
            self.imaging_data[4].append(self.Calciumdatabuffer1[-1])
            self.imaging_data[5].append(self.Vmdatabuffer1[-1])
            self.imaging_data[6].append(self.Fluodatabuffer2[-1])
            self.imaging_data[7].append(self.Calciumdatabuffer2[-1])
            self.imaging_data[8].append(self.Vmdatabuffer2[-1])
            self.imaging_data[9].append(self.Fluodatabuffer3[-1])
            self.imaging_data[10].append(self.Calciumdatabuffer3[-1])
            self.imaging_data[11].append(self.Vmdatabuffer3[-1])


    def export_data_to_csv(self):
        """
        Export recorded data to a CSV file.
        """
        # Create a numpy array for the dataset
        ImagingDataset = np.empty([12, len(self.imaging_data[1])], dtype=float)

        # Fill the dataset with recorded data
        _interval = Decimal(str(SAMPLE_INTERVAL))
        for i in range(len(self.imaging_data[1])):
            ImagingDataset[0][i] = i * _interval
            for j in range(1, 12):
                ImagingDataset[j][i] = self.imaging_data[j][i]


        dict = {'Time (ms)': ImagingDataset[0],
                'Stimulus (%)': ImagingDataset[1],
                'Trigger': ImagingDataset[2],
                'Spikeling Fluorescence': ImagingDataset[3],
                'Spikeling Calcium': ImagingDataset[4],
                'Spikeling Vm (mV)': ImagingDataset[5],
                'Neuron Aux1 Fluorescence': ImagingDataset[6],
                'Neuron Aux1 Calcium': ImagingDataset[7],
                'Neuron Aux1 Vm (mV)': ImagingDataset[8],
                'Neuron Aux2 Fluorescence': ImagingDataset[9],
                'Neuron Aux2 Calcium': ImagingDataset[10],
                'Neuron Aux2 Vm (mV)': ImagingDataset[11]
                }

        df = pd.DataFrame(dict)

        recording_file_name = str(self.ui.Imaging_SelectedFolderLabel.text())
        df.to_csv(f"{recording_file_name}.csv", index=False)

        self.Imagingrecordflag = False


        if self.ui.Imaging_DataRecording_Record_pushButton.isChecked() == True:
            self.Imagingrecordflag = True





    # -------------------------------------------------------------------------
    # Cleanup
    # -------------------------------------------------------------------------

    def cleanup(self):
        """Release resources."""
        if self.imagingtimer.isActive():
            self.imagingtimer.stop()

        self.last_valid_data = None

        self.imaging_data[0].clear()
        self.imaging_data[1].clear()
        self.imaging_data[2].clear()
        self.imaging_data[3].clear()
        self.imaging_data[4].clear()
        self.imaging_data[5].clear()
        self.imaging_data[6].clear()
        self.imaging_data[7].clear()
        self.imaging_data[8].clear()
        self.imaging_data[9].clear()
        self.imaging_data[10].clear()
        self.imaging_data[11].clear()

        self.ui.Imaging_Oscilloscope_widget.clear()
        if self.secondaryVB:
            self.secondaryVB.clear()

