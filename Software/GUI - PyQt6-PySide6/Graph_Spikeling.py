"""
Spikeling Graph Module

This module provides functionality for plotting and recording data from the Spikeling device.
It handles serial communication, data visualization, and data export.
"""

from PySide6.QtCore import QObject, QTimer
import pyqtgraph as pg
from pathlib import Path

import numpy as np
import pandas as pd

import Parameters_Settings as Settings
from serial_manager import serial_manager
from graph_core import RingBuffer, apply_scope_timebase, configure_scope, safe_reconnect

from PySide6.QtWidgets import QMessageBox

from connection_supervisor import ConnectionState, SpikelingConnectionSupervisor
from spikeling_discovery import discover_spikeling_ports

serial_port = serial_manager

# Constants
SAMPLE_INTERVAL = 0.1
TIME_WINDOW = 2000
TIME_WINDOW_DISPLAY = 250
PEN_WIDTH = 1.5
VM_MIN, VM_MAX = -100, 40
CURRENT_MIN, CURRENT_MAX = -100, 100
N_STREAM_CHANNELS = 8

# Suppress redundant serial writes when the custom stimulus value is unchanged
# (a 50 % duty square wave then costs 2 writes per period instead of ~10 000).
SKIP_REPEATED_STIM_WRITES = True


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

        # --- Data buffers (always exist, pre-filled with zeros) ---
        self._bufsize = int(TIME_WINDOW / SAMPLE_INTERVAL)
        self.databuffers = [RingBuffer(self._bufsize) for _ in range(N_STREAM_CHANNELS)]

        # state
        self.data = [0.0] * 8
        self.last_valid_data = None
        self.record_flag = False
        self.stim_counter = 0
        self.current_plots = None
        self._last_stim_value = None


        # Set SerialFlag in parent for use in Page101
        self.parent.SerialFlag = False

        # Initialize attributes that will be set later
        self.df_Stim = None
        self.df_yStim = None

        self._cus_prev_enabled = False

        # Timer for GUI updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)

        # Serial manager signals
        serial_manager.data_received.connect(self.on_data_received)
        serial_manager.connection_changed.connect(self.on_connection_changed)
        serial_manager.error_occurred.connect(self.on_error)
        self.setup_auto_connection()

    # -------------------------------------------------------------------------
    # Connection Management
    # -------------------------------------------------------------------------
    def connect_device(self):
        """Called when connect button is checked."""
        self.supervisor.start()

    def disconnect_device(self):
        """Called when connect button is unchecked."""
        # user-initiated disconnect must not trigger auto-reconnect
        self.supervisor.stop()
        self.ui.Spikeling_Speed_slider.setEnabled(False)

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
        """
        Reflect the serial manager state on the connect button.

        ``setChecked`` is issued with signals blocked because the toggled slot
        calls back into ``disconnect_device``, which re-enters this handler.
        """
        if not is_connected:
            self.disconnect_device()

        button = self.ui.Spikeling_ConnectButton
        was_blocked = button.blockSignals(True)
        button.setChecked(is_connected)
        button.blockSignals(was_blocked)

    def on_error(self, message: str):
        """Handle serial errors."""
        print("Serial error:", message)
        self.disconnect_device()



    # -------------------------------------------------------------------------
    # Data Handling
    # -------------------------------------------------------------------------
    def on_data_received(self, data: list):
        """Slot for serial_manager.data_received signal.

        Expects a list of 8 floats:
        [Vm, stim_state, Itot, syn1_vm, Isyn1, syn2_vm, Isyn2, trigger]
        """
        if not data or len(data) != 8:
            return

        #self.data = data
        self.last_valid_data = data

        try:
            values = [float(v) for v in data]
        except ValueError:
            return

        # Push one sample into each buffer PER PACKET
        for i, v in enumerate(values):
            getattr(self, f"databuffers")[i].append(v)

        # If recording, also store these values for CSV export
        if self.ui.Spikeling_DataRecording_Record_pushButton.isChecked() and self.record_flag:
            # spikeling_data[0] will be time (added on export)
            for index, value in enumerate(values):
                self.databuffers[index].append(value)

        self.step_custom_stimulus_on_packet()

    def update_plot(self):
        """Main loop: called periodically by QTimer."""
        try:
            #self.buff_data() # Data are already pushed into databuffers in on_data_received
            self.save_plot_data()
            self.plot_curve()
            #self.handle_custom_stimulus()
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
        self._bufsize = int(TIME_WINDOW / SAMPLE_INTERVAL)
        for buffer in self.databuffers:
            buffer.fill_with(0.0)
        self.x = np.linspace(-TIME_WINDOW, 0.0, self._bufsize)
        self.spikeling_data = [[] for _ in range(9)]

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
    # Automatic connection management
    # -------------------------------------------------------------------------
    def setup_auto_connection(self) -> None:
        """
        Install the hot-plug supervisor and its UI feedback.

        Replaces the manual *select COM port then press Connect* flow: the board
        is opened as soon as it is plugged in, and re-opened by itself after a
        cable drop without restarting the GUI.
        """
        self.supervisor = SpikelingConnectionSupervisor(serial_manager, parent=self)
        self.supervisor.register_state_restorer(self.restore_device_state)
        self.supervisor.connected.connect(self.on_device_connected)
        self.supervisor.reconnected.connect(self.on_device_reconnected)
        self.supervisor.disconnected.connect(self.on_device_disconnected)
        self._disconnect_dialog = None
        self.supervisor.start()

    def restore_device_state(self) -> None:
        """
        Re-send every GUI override to a freshly opened board.

        The firmware always boots in potentiometer mode, so overrides issued
        before the unplug are lost and must be replayed for the recording to
        remain comparable across the disconnection.
        """
        serial_manager.write("CON\n")
        if hasattr(self.parent, "ChangeSpeed"):
            self.parent.ChangeSpeed()
        for activator in ("SelectNeuronMode", "SelectPatchClampMode",
                          "ActivateStimFre", "ActivateStimStr",
                          "ActivatePhotoGain", "ActivatePRDecay", "ActivatePRRecovery",
                          "ActivateInjectedCurrent", "ActivateNoiseLevel",
                          "ActivateSynapticGain1", "ActivateSynapseDecay1",
                          "ActivateSynapticGain2", "ActivateSynapseDecay2"):
            handler = getattr(self.parent, activator, None)
            if callable(handler):
                handler()

    def on_device_connected(self, port) -> None:
        """Start acquisition on first successful connection."""
        self.parent.SerialFlag = True
        self.stim_counter = 0
        self.ui.Spikeling_Speed_slider.setEnabled(True)
        self.ui.Spikeling_SelectPortComboBox.setCurrentText(port.port_name)
        self.set_init_parameters()
        self.set_plot()
        if not self.timer.isActive():
            self.timer.start(10)

    def on_device_reconnected(self, port) -> None:
        """Resume acquisition after a hot-plug and dismiss the warning popup."""
        if self._disconnect_dialog is not None:
            self._disconnect_dialog.close()
            self._disconnect_dialog = None
        self.on_device_connected(port)

    def on_device_disconnected(self, reason: str) -> None:
        """
        Freeze acquisition and warn the user, without blocking the event loop.

        A non-modal dialog is used deliberately: a modal ``exec()`` would still
        pump timers, but it would also trap the user if the board is replugged
        while the dialog is up.
        """
        self.parent.SerialFlag = False
        if self.timer.isActive():
            self.timer.stop()
        self.ui.Spikeling_DataRecording_Record_pushButton.setChecked(False)
        self.ui.Spikeling_ConnectButton.setText("Reconnecting...")

        if self._disconnect_dialog is None:
            dialog = QMessageBox(self.parent)
            dialog.setIcon(QMessageBox.Warning)
            dialog.setWindowTitle("Spikeling disconnected")
            dialog.setText(
                f"The Spikeling board was disconnected ({reason}).\n\n"
                "Plug the USB cable back in: the connection and all current "
                "settings will be restored automatically."
            )
            dialog.setStandardButtons(QMessageBox.Ok)
            dialog.finished.connect(lambda _: setattr(self, "_disconnect_dialog", None))
            self._disconnect_dialog = dialog
            dialog.open()

    def populate_port_combobox(self) -> None:
        """Fill the port selector with detected boards, for manual override only."""
        combo = self.ui.Spikeling_SelectPortComboBox
        combo.clear()
        for port in discover_spikeling_ports(serial_manager.identity):
            combo.addItem(port.label, userData=port)



# -------------------------------------------------------------------------
# Plotting
# -------------------------------------------------------------------------

    def set_plot(self):
        """
        Build the Spikeling oscilloscope: Vm on the left axis, currents right.

        The timebase is pinned through :func:`graph_core.apply_scope_timebase`
        rather than ``setRange``, so the initial window is exactly
        ``TIME_WINDOW_DISPLAY`` regardless of widget geometry or launch mode.
        """
        pw = self.ui.Spikeling_Oscilloscope_widget
        plot_item = pw.getPlotItem()
        vb = plot_item.getViewBox()

        plot_item.setMouseEnabled(x=True, y=False)
        pw.showGrid(x=True, y=True)
        pw.setLabel('left', 'Membrane potential', 'mV')
        pw.setLabel('bottom', 'time', 'ms')
        pw.setLabel('right', 'Current Input', 'a.u.')
        pw.setAntialiasing(True)

        configure_scope(plot_item)
        apply_scope_timebase(plot_item, TIME_WINDOW, TIME_WINDOW_DISPLAY,
                             y_range=(VM_MIN, VM_MAX))

        # --- Secondary ViewBox: currents on the right axis ----------------
        self.current_plots = pg.ViewBox()
        self.current_plots.setMouseEnabled(x=False, y=False)
        self.current_plots.setMenuEnabled(False)
        pw.scene().addItem(self.current_plots)
        self.current_plots.setXLink(pw)

        # Zero padding here too: a padded current axis makes a +/-100 a.u.
        # trace render at a height that depends on the widget size.
        self.current_plots.enableAutoRange(axis=pg.ViewBox.YAxis, enable=False)
        self.current_plots.setYRange(CURRENT_MIN, CURRENT_MAX, padding=0.0)
        pw.getAxis("right").linkToView(self.current_plots)

        zeros = np.zeros(self._bufsize, dtype=float)
        self.curve0 = pw.plot(self.x, zeros, pen=pg.mkPen(Settings.DarkSolarized[3], width=PEN_WIDTH, cosmetic=True))
        self.curve3 = pw.plot(self.x, zeros, pen=pg.mkPen(Settings.DarkSolarized[6], width=PEN_WIDTH, cosmetic=True))
        self.curve5 = pw.plot(self.x, zeros, pen=pg.mkPen(Settings.DarkSolarized[8], width=PEN_WIDTH, cosmetic=True))

        self.curve1 = pg.PlotCurveItem(self.x, zeros, pen=pg.mkPen(Settings.DarkSolarized[5], width=PEN_WIDTH, cosmetic=True))
        self.curve2 = pg.PlotCurveItem(self.x, zeros, pen=pg.mkPen(Settings.DarkSolarized[4], width=PEN_WIDTH, cosmetic=True))
        self.curve4 = pg.PlotCurveItem(self.x, zeros, pen=pg.mkPen(Settings.DarkSolarized[7], width=PEN_WIDTH, cosmetic=True))
        self.curve6 = pg.PlotCurveItem(self.x, zeros, pen=pg.mkPen(Settings.DarkSolarized[10], width=PEN_WIDTH, cosmetic=True))

        for curve in (self.curve1, self.curve2, self.curve4, self.curve6):
            self.current_plots.addItem(curve)

        self._update_views()
        safe_reconnect(pw.getViewBox().sigResized, self._update_views)

    def _update_views(self):
        """Keep the right-axis current ViewBox aligned with the main ViewBox."""
        pw = self.ui.Spikeling_Oscilloscope_widget
        main_vb = pw.getViewBox()
        self.current_plots.setGeometry(main_vb.sceneBoundingRect())
        self.current_plots.linkedViewChanged(main_vb, self.current_plots.XAxis)

    def plot_curve(self):
        """
        Push the visible rolling buffers to their curves.

        Reads use the contiguous :class:`RingBuffer` views, so no per-redraw
        deque-to-array copy is performed.
        """
        ui = self.ui
        channels = (
            (ui.Spikeling_VmCheckbox, self.curve0, 0),
            (ui.Spikeling_StimulusCheckbox, self.curve1, 1),
            (ui.Spikeling_InputCurrentCheckbox, self.curve2, 2),
            (ui.Spikeling_Syn1VmCheckbox, self.curve3, 3),
            (ui.Spikeling_Syn1InputCheckbox, self.curve4, 4),
            (ui.Spikeling_Syn2VmCheckbox, self.curve5, 5),
            (ui.Spikeling_Syn2InputCheckbox, self.curve6, 6),
        )
        try:
            for checkbox, curve, index in channels:
                visible = checkbox.isChecked()
                curve.setVisible(visible)
                if visible:
                    curve.setData(self.x, self.databuffers[index].data)
        except Exception as error:
            print(f"Error in plot_curve: {error}")

    # -------------------------------------------------------------------------
    # Saving Data
    # -------------------------------------------------------------------------

    def save_plot_data(self):
        """
        Save the latest buffer data and export them as CSV when recording is stopped.
        Handles overwrite/rename/cancel before recording starts.
        """
        # --- If recording is starting ---
        if self.ui.Spikeling_DataRecording_Record_pushButton.isChecked() and not self.record_flag:
            FolderName = self.ui.Spikeling_DataRecording_SelectRecordFolder_label.text()
            FileName = self.ui.Spikeling_DataRecording_RecordFolder_value.text()
            folder = Path(FolderName)

            if not FolderName or not FileName:
                # No folder or filename selected
                self.ui.Spikeling_DataRecording_Record_pushButton.setChecked(False)
                Settings.show_popup(self.parent,
                                    Title="Error: no file selected",
                                    Text="Select a file where to record your data by clicking on the - browse directory - button")
                return

            file_path = folder / f"{FileName}.csv"

            # Ask user if file exists
            if file_path.exists():
                action, new_path = Settings.confirm_overwrite(self.parent, file_path)
                if action == "cancel":
                    self.ui.Spikeling_DataRecording_Record_pushButton.setChecked(False)
                    self.ui.Spikeling_DataRecording_Record_pushButton.setText("Record")
                    self.ui.Spikeling_DataRecording_Record_pushButton.setStyleSheet("color: rgb(250, 250, 250);\n"
                                                                                    "background-color: rgb(220, 50, 47);")
                    return
                elif action == "rename":
                    self.ui.Spikeling_DataRecording_RecordFolder_value.setText(new_path.stem)
                    save_path = new_path
                elif action == "overwrite":
                    save_path = file_path
                else:
                    # Unknown action: fail closed rather than raising NameError
                    self.ui.Spikeling_DataRecording_Record_pushButton.setChecked(False)
                    return

            else:
                save_path = file_path

            # Start recording
            self.record_flag = True
            if not hasattr(self, "spikeling_data") or not self.spikeling_data:
                self.spikeling_data = [[] for _ in range(9)]
            else:
                for i in range(9):
                    if not self.spikeling_data[i]:
                        self.spikeling_data[i] = []

            # Save path for later use
            self._current_save_path = save_path

        # # --- If recording is on, append latest buffer data ---
        # if self.ui.Spikeling_DataRecording_Record_pushButton.isChecked():
        #     for i in range(8):
        #         buffer_name = f"databuffer{i}"
        #         if hasattr(self, buffer_name) and getattr(self, buffer_name):
        #             self.spikeling_data[i + 1].append(getattr(self, buffer_name)[-1])

        # --- If recording is stopped, export data ---
        if not self.ui.Spikeling_DataRecording_Record_pushButton.isChecked() and self.record_flag:
            if hasattr(self, "_current_save_path"):
                self.export_data_to_csv(self._current_save_path)
            self.record_flag = False
            # Clear data arrays
            for i in range(9):
                self.spikeling_data[i].clear()

    def export_data_to_csv(self, file_path: Path) -> None:
        """
        Export the recorded Spikeling stream to CSV.

        Parameters
        ----------
        file_path : pathlib.Path
            Destination ``.csv`` path.

        Notes
        -----
        The time axis is reconstructed as ``k * SAMPLE_INTERVAL`` and therefore
        assumes no packet loss on the serial link. Prefer a device-side
        timestamp if sample-accurate timing matters for the analysis.
        """
        n_samples = len(self.spikeling_data[1])
        if n_samples == 0:
            print("No data to save.")
            return

        columns = [
            'Spikeling Vm (mV)', 'Stimulus (%)', 'Total Current Input (a.u.)',
            'Synapse 1 Vm (mV)', 'Synapse 1 Input (a.u.)',
            'Synapse 2 Vm (mV)', 'Synapse 2 Input (a.u.)', 'Trigger',
        ]
        frame = {'Time (ms)': np.arange(n_samples, dtype=float) * SAMPLE_INTERVAL}
        frame.update({
            name: np.asarray(self.spikeling_data[j + 1], dtype=float)
            for j, name in enumerate(columns)
        })

        try:
            pd.DataFrame(frame).to_csv(file_path, index=False)
        except Exception as error:
            print(f"Failed to save data: {error}")
            Settings.show_popup(
                self.parent, Title="Error saving file",
                Text=f"Could not save recording to {file_path}.\nError: {error}",
            )

# -------------------------------------------------------------------------
# Cleanup
# -------------------------------------------------------------------------

    def cleanup(self):
        """Release resources."""
        if self.timer.isActive():
            self.timer.stop()

        self.last_valid_data = None

        for buffer in self.databuffers:
            buffer.fill_with(0.0)

        self.ui.Spikeling_Oscilloscope_widget.clear()
        if self.current_plots:
            self.current_plots.clear()

# -------------------------------------------------------------------------
# Handlers
# -------------------------------------------------------------------------

    def step_custom_stimulus_on_packet(self):
        """Advance custom stimulus exactly once per received data packet."""
        # basic guards
        if not hasattr(self.ui, "StimCus_toggleButton"):
            return
        if not serial_manager.is_open:
            return

        # IMPORTANT: pick ONE place where the waveform lives
        # Prefer self.df_yStim (it exists in __init__), fall back to ui.df_yStim if you truly use that elsewhere.
        y = self.df_yStim
        if y is None and hasattr(self.ui, "df_yStim"):
            y = self.ui.df_yStim

        enabled = (self.ui.StimCus_toggleButton.isChecked() and y is not None and len(y) > 0)

        # edge: OFF -> ON
        if enabled and not self._cus_prev_enabled:
            self.stim_counter = 0
            serial_manager.write("TR\n")  # if you want a trigger pulse at start

        # edge: ON -> OFF
        if (not enabled) and self._cus_prev_enabled:
            serial_manager.write("SC0\n")
            self._last_stim_value = None

        self._cus_prev_enabled = enabled
        if not enabled:
            return

        # wrap + send one sample per packet
        if self.stim_counter >= len(y):
            self.stim_counter = 0
            serial_manager.write("TR\n")

        value = y[self.stim_counter]
        self.stim_counter += 1

        # The device latches the last received value, so identical consecutive
        # samples need not be transmitted. A square wave then costs 2 writes
        # per period instead of one per packet (~10 kHz).
        if SKIP_REPEATED_STIM_WRITES and value == self._last_stim_value:
            return
        self._last_stim_value = value
        serial_manager.write(f"SC1 {value}\n")


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