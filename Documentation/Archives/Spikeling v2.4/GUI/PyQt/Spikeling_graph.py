"""
Spikeling Graph Module

This module provides functionality for plotting and recording data from the Spikeling device.
It handles serial communication, data visualization, and data export.
"""

from PySide6.QtCore import QObject, QTimer
from PySide6.QtGui import QPen
import pyqtgraph as pg

import collections
import numpy as np
import pandas as pd
from decimal import Decimal

import Settings
from serial_manager import serial_manager
# Use the global serial_manager instance
serial_port = serial_manager

# Constants
DOWNSAMPLING = 5
SAMPLE_INTERVAL = 0.1
TIME_WINDOW = 500
TIME_WINDOW_DISPLAY = 200
PEN_WIDTH = 1.5
VM_MIN = -90
VM_MAX = 30
CURRENT_MIN = -100
CURRENT_MAX = 100


class SpikelingGraph(QObject):
    """
    Class for handling Spikeling device data visualization and recording.

    This class manages the connection to the Spikeling device, data acquisition,
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
        self.stim_counter = 0
        self.current_plots = None

        # Set SerialFlag in parent for use in Page101
        self.parent.SerialFlag = False

        # Initialize attributes that will be set later
        self.df_Stim = None
        self.df_yStim = None

        # Timer for GUI updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)

        # Serial manager signals
        serial_manager.data_received.connect(self.on_data_received)
        serial_manager.connection_changed.connect(self.on_connection_changed)
        serial_manager.error_occurred.connect(self.on_error)


    # -------------------------------------------------------------------------
    # Connection Management
    # -------------------------------------------------------------------------
    def connect_device(self):
        """Called when connect button is checked."""
        port_name = self.ui.Spikeling_SelectPortComboBox.currentText()
        if not serial_manager.configure_port(port_name):
            self.ui.Spikeling_ConnectButton.setChecked(False)
            return

        if not serial_manager.open():
            self.ui.Spikeling_ConnectButton.setChecked(False)
            if self.parent.SerialFlag == False:
                Settings.show_popup(self, Title="Error: Spikeling not connected",
                                    Text="Spikeling first needs to be connected, then a COM port has to be selected and finally press the - Connect Spikeling Screen - button")
            return

        self.set_init_parameters()
        self.set_plot()

        self.parent.SerialFlag = True
        self.stim_counter = 0

        self.timer.start()  # update every 1ms

    def disconnect_device(self):
        """Called when connect button is unchecked."""
        self.cleanup()
        self.parent.SerialFlag = False

        if serial_port.is_open:
            serial_port.write('CON' + '\n')

        self.ui.Spikeling_ConnectButton.setText("Connect Spikeling Screen")
        self.ui.Spikeling_ConnectButton.setStyleSheet(
            f"color: rgb{tuple(Settings.DarkSolarized[14])};\n"
            f"background-color: rgb{tuple(Settings.DarkSolarized[2])};\n"
            f"border: 1px solid rgb{tuple(Settings.DarkSolarized[14])};\n"
            f"border-radius: 10px;"
        )

    def on_connection_changed(self, is_connected: bool):
        """Handle serial manager connection state."""
        if not is_connected:
            self.disconnect_device()
        self.ui.Spikeling_ConnectButton.setChecked(is_connected)

    def on_error(self, message: str):
        """Handle serial errors."""
        print("Serial error:", message)
        self.disconnect_device()



    # -------------------------------------------------------------------------
    # Data Handling
    # -------------------------------------------------------------------------
    def on_data_received(self, data: list):
        """Slot for serial_manager.data_received signal."""
        if data and len(data) == 8:
            self.data = data
            self.last_valid_data = data


    def update_plot(self):
        """Main loop: called periodically by QTimer."""
        try:
            self.buff_data()
            self.save_plot_data()
            self.plot_curve()
            self.handle_custom_stimulus()
            self.handle_noise()
        except Exception as e:
            print(f"Error in update_plot: {e}")



    # -------------------------------------------------------------------------
    # Initialization Methods
    # -------------------------------------------------------------------------
    def set_init_parameters(self):
        """
        Initialize parameters for Spikeling plotting.
        """
        self.record_flag = False
        self.trigger = 0
        self.last_valid_data = None  # Reset the last valid data
        self.ui.Spikeling_Oscilloscope_widget.clear()

        # Buffers for Vm, current and stimulus
        self._bufsize = int(TIME_WINDOW / SAMPLE_INTERVAL)

        # Initialize data buffers
        for i in range(8):
            setattr(self, f"databuffer{i}", collections.deque([0.0] * self._bufsize, self._bufsize))

        # Numpy arrays for plotting
        self.x = np.linspace(-TIME_WINDOW, 0.0, self._bufsize)
        for i in range(7):
            setattr(self, f"y{i}", np.zeros(self._bufsize, dtype=float))

        # Data recording arrays
        self.spikeling_data = []
        for _ in range(9):
            self.spikeling_data.append([])

        # Set button appearance
        if self.ui.Spikeling_ConnectButton.isChecked() and serial_manager.is_open:
            self.ui.Spikeling_ConnectButton.setText("Connected")
            self.ui.Spikeling_ConnectButton.setStyleSheet(
                f"color: rgb{tuple(Settings.DarkSolarized[3])};\n"
                f"background-color: rgb{tuple(Settings.DarkSolarized[11])};\n"
                f"border: 1px solid rgb{tuple(Settings.DarkSolarized[14])};\n"
                f"border-radius: 10px;"
            )
        else:
            self.ui.Spikeling_ConnectButton.setText("Connect Spikeling Screen")
            self.ui.Spikeling_ConnectButton.setStyleSheet(
                f"color: rgb{tuple(Settings.DarkSolarized[14])};\n"
                f"background-color: rgb{tuple(Settings.DarkSolarized[2])};\n"
                f"border: 1px solid rgb{tuple(Settings.DarkSolarized[14])};\n"
                f"border-radius: 10px;"
            )



# -------------------------------------------------------------------------
# Buffers + Plotting
# -------------------------------------------------------------------------

    def buff_data(self):
        try:
            if not self.data or len(self.data) < 8:
                values = [0.0] * 8
            else:
                try:
                    values = [float(val) if val else 0.0 for val in self.data]
                except Exception:
                    values = [0.0] * 8

            for i in range(8):
                getattr(self, f"databuffer{i}").append(values[i])
        except Exception as e:
            print(f"Error in buff_data: {e}")


    def set_plot(self):
        """
        Set up the plot widget and curves.
        """
        # Main plot setup
        pw = self.ui.Spikeling_Oscilloscope_widget
        pw.showGrid(x=True, y=True)
        pw.setRange(xRange=[-TIME_WINDOW_DISPLAY, 0], yRange=[VM_MIN, VM_MAX])

        # Set axis labels
        pw.setLabel('left', 'Membrane potential', 'mV')
        pw.setLabel('bottom', 'time', 'ms')
        pw.setLabel('right', 'Current Input', 'a.u.')
        pw.setAntialiasing(True)


        # -----------------------------
        # Setup secondary ViewBox
        # -----------------------------
        self.current_plots = pg.ViewBox()
        pw.scene().addItem(self.current_plots)
        self.current_plots.setXLink(pw)
        self.current_plots.setRange(yRange=[CURRENT_MIN, CURRENT_MAX])
        pw.getAxis("right").linkToView(self.current_plots)

        # Create plot curves for membrane potentials on the main plot with anti-aliasing
        self.curve0 = self.ui.Spikeling_Oscilloscope_widget.plot(self.x, self.y0, pen=pg.mkPen(Settings.DarkSolarized[3], width=PEN_WIDTH, cosmetic=True))
        self.curve0.clear()
        self.curve3 = self.ui.Spikeling_Oscilloscope_widget.plot(self.x, self.y3, pen=pg.mkPen(Settings.DarkSolarized[6], width=PEN_WIDTH, cosmetic=True))
        self.curve3.clear()
        self.curve5 = self.ui.Spikeling_Oscilloscope_widget.plot(self.x, self.y5, pen=pg.mkPen(Settings.DarkSolarized[8], width=PEN_WIDTH, cosmetic=True))
        self.curve5.clear()

        # Create plot curves for currents and stimulus (secondary plot - right y-axis) with anti-aliasing
        self.curve1 = pg.PlotCurveItem(self.x, self.y1, pen=pg.mkPen(Settings.DarkSolarized[5], width=PEN_WIDTH, cosmetic=True))
        self.curve1.clear()
        self.curve2 = pg.PlotCurveItem(self.x, self.y2, pen=pg.mkPen(Settings.DarkSolarized[4], width=PEN_WIDTH, cosmetic=True))
        self.curve2.clear()
        self.curve4 = pg.PlotCurveItem(self.x, self.y4, pen=pg.mkPen(Settings.DarkSolarized[7], width=PEN_WIDTH, cosmetic=True))
        self.curve4.clear()
        self.curve6 = pg.PlotCurveItem(self.x, self.y6, pen=pg.mkPen(Settings.DarkSolarized[10], width=PEN_WIDTH, cosmetic=True))
        self.curve6.clear()

        # Add current and stimulus curves to the secondary plot (right y-axis)
        self.current_plots.addItem(self.curve1)
        self.current_plots.addItem(self.curve2)
        self.current_plots.addItem(self.curve4)
        self.current_plots.addItem(self.curve6)


        # Update secondary ViewBox when main plot resizes
        def update_views():
            self.current_plots.setGeometry(pw.getViewBox().sceneBoundingRect())
            self.current_plots.linkedViewChanged(pw.getViewBox(), self.current_plots.XAxis)

        pw.getViewBox().sigResized.connect(update_views)


    def plot_curve(self):
        """
        Update the plot curves with the latest data from buffers.
        """
        try:
            # Check if all required attributes are initialized
            required_attrs = ['x', 'y0', 'y1', 'y2', 'y3', 'y4', 'y5', 'y6',
                              'curve0', 'curve1', 'curve2', 'curve3', 'curve4', 'curve5', 'curve6',
                             'databuffer0', 'databuffer1', 'databuffer2', 'databuffer3', 'databuffer4', 'databuffer5', 'databuffer6']


            # Plot on the main plot
            if self.ui.Spikeling_VmCheckbox.isChecked():
                self.y0[:] = self.databuffer0
                self.curve0.setData(self.x, self.y0)
            else:
                self.curve0.clear()

            if self.ui.Spikeling_StimulusCheckbox.isChecked():
                self.y1[:] = self.databuffer1
                self.curve1.setData(self.x, self.y1)
            else:
                self.curve1.clear()

            if self.ui.Spikeling_InputCurrentCheckbox.isChecked():
                self.y2[:] = self.databuffer2
                self.curve2.setData(self.x, self.y2)
            else:
                self.curve2.clear()

            if self.ui.Spikeling_Syn1VmCheckbox.isChecked():
                self.y3[:] = self.databuffer3
                self.curve3.setData(self.x, self.y3)
            else:
                self.curve3.clear()

            if self.ui.Spikeling_Syn1InputCheckbox.isChecked():
                self.y4[:] = self.databuffer4
                self.curve4.setData(self.x, self.y4)
            else:
                self.curve4.clear()

            if self.ui.Spikeling_Syn2VmCheckbox.isChecked():
                self.y5[:] = self.databuffer5
                self.curve5.setData(self.x, self.y5)
            else:
                self.curve5.clear()

            if self.ui.Spikeling_Syn2InputCheckbox.isChecked():
                self.y6[:] = self.databuffer6
                self.curve6.setData(self.x, self.y6)
            else:
                self.curve6.clear()

            # Secondary ViewBox auto-syncs y-axis (current/stimulus)
            self.current_plots.setGeometry(self.ui.Spikeling_Oscilloscope_widget.getViewBox().sceneBoundingRect())


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
        if not self.ui.Spikeling_DataRecording_Record_pushButton.isChecked() and self.record_flag:
            self.export_data_to_csv()
            self.record_flag = False
            # Clear data arrays
            for i in range(9):
                self.spikeling_data[i].clear()

        # If recording is on, append data to arrays
        if self.ui.Spikeling_DataRecording_Record_pushButton.isChecked():
            self.record_flag = True

            # Append latest data points to recording arrays
            for i in range(8):
                buffer_name = f"databuffer{i}"
                if hasattr(self, buffer_name) and getattr(self, buffer_name):
                    self.spikeling_data[i + 1].append(getattr(self, buffer_name)[-1])


    def export_data_to_csv(self):
        """
        Export recorded data to a CSV file.
        """
        # Create a numpy array for the dataset
        dataset = np.empty([9, len(self.spikeling_data[1])], dtype=float)

        # Fill the dataset with recorded data
        _interval = Decimal(str(SAMPLE_INTERVAL))
        for i in range(len(self.spikeling_data[1])):
            dataset[0][i] = i * _interval  # Time
            for j in range(1, 9):
                dataset[j][i] = self.spikeling_data[j][i]

        # Create a dictionary for pandas DataFrame
        data_dict = {
            'Time (ms)': dataset[0],
            'Spikeling Vm (mV)': dataset[1],
            'Stimulus (%)': dataset[2],
            'Total Current Input (a.u.)': dataset[3],
            'Synapse 1 Vm (mV)': dataset[4],
            'Synapse 1 Input (a.u.)': dataset[5],
            'Synapse 2 Vm (mV)': dataset[6],
            'Synapse 2 Input (a.u.)': dataset[7],
            'Trigger': dataset[8]
        }

        # Create DataFrame and save to CSV
        df = pd.DataFrame(data_dict)
        recording_file_name = str(self.ui.Spikeling_SelectedFolderLabel.text())
        df.to_csv(f"{recording_file_name}.csv", index=False)



# -------------------------------------------------------------------------
# Cleanup
# -------------------------------------------------------------------------

    def cleanup(self):
        """Release resources."""
        if self.timer.isActive():
            self.timer.stop()

        self.last_valid_data = None

        for i in range(8):
            buf_name = f"databuffer{i}"
            if hasattr(self, buf_name):
                getattr(self, buf_name).clear()

        self.ui.Spikeling_Oscilloscope_widget.clear()
        if self.current_plots:
            self.current_plots.clear()





# -------------------------------------------------------------------------
# Handlers
# -------------------------------------------------------------------------

    def handle_custom_stimulus(self):
        """
        Handle custom stimulus if enabled.
        """
        try:
            if not hasattr(self.ui, 'StimCus_toggleButton'):
                return

            if self.ui.StimCus_toggleButton.isChecked():
                try:
                    # # Check if df_yStim and df_Stim are initialized
                    if not hasattr(self, 'df_yStim') or self.ui.df_yStim is None or not hasattr(self, 'df_Stim') or self.ui.df_Stim is None:
                        print("returning early from handle_custom_stimulus: df_yStim or df_Stim not defined")
                        return

                    # Check if stim_counter is within bounds
                    if self.stim_counter >= len(self.ui.df_yStim):
                        self.stim_counter = 0

                    self.stim_cus_value = self.ui.df_yStim[self.stim_counter]

                    if serial_manager.is_open:
                        serial_manager.write(f'SC1 {self.stim_cus_value}\n')
                        self.stim_counter += 1

                    if self.stim_counter > len(self.ui.df_Stim) - 1:
                        self.stim_counter = 0
                        if serial_manager.is_open:
                            serial_manager.write('TR\n')
                except (AttributeError, IndexError) as e:
                    # Handle case where df_yStim or df_Stim is not defined or index is out of range
                    print(f"Error in handle_custom_stimulus: {e}")
            else:
                if serial_manager.is_open:
                    serial_manager.write('SC0\n')
        except Exception as e:
            # Log the error but don't crash the application
            print(f"Error in handle_custom_stimulus: {e}")


    def handle_noise(self):
        """
        Generate and send a new noise value if noise is enabled.

        This function is called by the timer to continuously update the noise
        value sent to the device.
        """
        try:
            # Check if noise toggle button exists
            if not hasattr(self.ui, 'Noise_toggleButton'):
                return

            # Check if noise is enabled
            if self.ui.Noise_toggleButton.isChecked():
                try:
                    # Check if noise slider exists
                    if not hasattr(self.ui, 'Spikeling_Noise_slider'):
                        return

                    # Get the current noise amplitude
                    noise_value = self.ui.Spikeling_Noise_slider.value()

                    # Generate a new random noise value
                    noise = np.random.normal(0, noise_value / 2)

                    # Send the noise value to the device
                    if serial_manager.is_open:
                        serial_manager.write(f'NO1 {noise}\n')
                except Exception as e:
                    # Log specific errors in noise generation
                    print(f"Error generating noise: {e}")
        except Exception as e:
            # Log the error but don't crash the application
            print(f"Error in handle_noise: {e}")