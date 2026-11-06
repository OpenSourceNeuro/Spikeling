"""
Spikeling Graph Module

This module provides functionality for plotting and recording data from the Spikeling device.
It handles serial communication, data visualization, and data export.
"""

from PySide6.QtCore import QObject, QTimer, Qt, QSignalBlocker
from PySide6.QtWidgets import QMessageBox, QFileDialog, QDialog

import pyqtgraph as pg
from pathlib import Path

import numpy as np
import pandas as pd
import os
import tempfile
import time

from theme_manager import theme_manager
import Parameters_Settings as Settings
from serial_manager import serial_manager
from graph_core import RingBuffer, apply_scope_timebase, configure_scope, safe_reconnect


from connection_supervisor import ConnectionState, SpikelingConnectionSupervisor
from spikeling_discovery import discover_spikeling_ports

serial_port = serial_manager

# Constants
SAMPLE_INTERVAL = 0.1
TIME_WINDOW = 2000
TIME_WINDOW_DISPLAY = 250
PEN_WIDTH = 1.5
VM_MIN, VM_MAX = -100, 40 # Membrane potential
CURRENT_MIN, CURRENT_MAX = -100, 100 # Current-clamp current, arbitrary units
VC_CURRENT_MIN, VC_CURRENT_MAX = -2.0, 2.0 # Voltage-clamp current, nanoamperes
STIMULUS_MIN, STIMULUS_MAX = -100.0, 100.0 # Stimulus amplitude, percentage
N_STREAM_CHANNELS = 8

# Suppress redundant serial writes when the custom stimulus value is unchanged
# (a 50 % duty square wave then costs 2 writes per period instead of ~10 000).

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
        # Recording storage is independent of the rolling plot buffers.
        self.spikeling_data = [[] for _ in range(9)]
        self._recording_save_pending = False
        self._current_save_path = None
        self._recording_error = ""
        self._recording_stop_reason = ""
        self._record_folder_dialog = None
        self.stim_counter = 0
        # Secondary plotting areas.
        self.current_plots = None
        self.stimulus_plots = None

        # Default display mode is current clamp.
        self.voltage_clamp_display = False

        # Prevent duplicate resize-signal connections.
        self._resize_connected = False


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
        if self.record_flag:
            self.stop_recording(reason="Disconnected")

        self.supervisor.stop()
        self.ui.Spikeling_Speed_slider.setEnabled(False)

        self.cleanup()
        if self.stimulus_plots is not None:
            self.stimulus_plots.clear()
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

        Parameters
        ----------
        is_connected : bool
            New port state reported by the manager.

        Notes
        -----
        An unexpected close must not call :meth:`disconnect_device`: that is
        the user-initiated path and it stops the supervisor, which would
        disable hot-plug recovery permanently. Unexpected losses reach the
        supervisor through ``device_lost`` instead.
        """
        button = self.ui.Spikeling_ConnectButton
        was_blocked = button.blockSignals(True)
        button.setChecked(is_connected)
        button.blockSignals(was_blocked)

        if not is_connected:
            if self.record_flag:
                self.stop_recording(reason="Connection lost")
            if self.timer.isActive():
                self.timer.stop()
            self.parent.SerialFlag = False

    def on_error(self, message: str):
        """Handle serial errors."""
        print("Serial error:", message)
        self.disconnect_device()



    # -------------------------------------------------------------------------
    # Data Handling
    # -------------------------------------------------------------------------
    def on_data_received(self, data: list):
        """Store each valid packet once for plotting and once for recording."""
        if data is None or len(data) != N_STREAM_CHANNELS:
            return

        try:
            values = [float(value) for value in data]
        except (TypeError, ValueError):
            return

        if not all(np.isfinite(value) for value in values):
            return

        self.last_valid_data = values

        # One sample per channel enters the rolling display buffers.
        for index, value in enumerate(values):
            self.databuffers[index].append(value)

        if self.record_flag:
            # Keep one recording consistent in clamp mode and membrane model.
            if self._recording_mode() != self._recording_mode_at_start:
                self.stop_recording(reason="Clamp mode/model changed")
                return

            # One sample per channel enters the recording storage.
            for index, value in enumerate(values):
                self.spikeling_data[index + 1].append(value)


    def update_plot(self):
        """Main loop: called periodically by QTimer."""
        try:
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

        Notes
        -----
        This previously resolved the handlers with
        ``getattr(self.parent, name)``, but they are defined on
        ``Page_Spikeling_NeuronInterface.Spikeling``, not on the main window,
        so every lookup returned ``None`` and nothing was ever replayed,
        including the ``DT`` loop period. They are now resolved on the page
        class and invoked with the main window as ``self``, matching how the
        navigation buttons call them.

        The import is local because ``Page_Spikeling_NeuronInterface``
        imports ``Parameters_NavigationButtons``, which imports this module.
        """
        from Page_Spikeling_NeuronInterface import Spikeling as SpikelingPage

        serial_manager.write("CON\n")

        controller = getattr(self.parent, "custom_stimulus_controller", None,)

        if controller is not None:
            controller.restore_after_connection()

        for name in ("ChangeSpeed",
                     "SelectNeuronMode", "SyncPatchClampState",
                     "SyncNoiseState",
                     "SyncPhotoreceptorState",
                     "SyncDrugState",
                     "SyncSynapse1State", "SyncSynapse2State"):
            handler = getattr(SpikelingPage, name, None)
            if not callable(handler):
                continue
            try:
                handler(self.parent)
            except Exception as error:   # one broken restorer must not kill the link
                print(f"State restore failed for {name}: {error}")

        # Restore migrated stimulus bindings after the board handshake.
        for attribute in (
                "stimulus_frequency_binding",
                "stimulus_strength_binding",
        ):
            binding = getattr(self.parent, attribute, None)

            if binding is not None:
                binding.apply_current()

    def on_device_connected(self, port) -> None:
        """
        Start acquisition on a validated connection.

        Parameters
        ----------
        port : spikeling_discovery.SpikelingPort
            Descriptor of the board that passed the handshake.

        Notes
        -----
        The combo-box update is signal-blocked. ``currentIndexChanged`` is
        wired to ``Page_Spikeling_NeuronInterface.Spikeling.ChangePort``,
        which closes and reopens the port; letting it fire here tears down
        the link the supervisor has just validated. The failure was
        platform-specific because the reopen went through
        :meth:`SerialPortManager.open`, and only the Linux tty layer raises
        DTR implicitly -- without it the ESP32-S3 CDC stack discards every
        write. It was also once-only, because ``setCurrentText`` emits
        nothing when the index is already correct, which is why the link
        survived after a manual board reset.
        """
        self.parent.SerialFlag = True
        self.stim_counter = 0
        self.ui.Spikeling_Speed_slider.setEnabled(True)

        combo = self.ui.Spikeling_SelectPortComboBox
        index = combo.findText(port.port_name)
        if index < 0:
            combo.addItem(port.port_name)
            index = combo.count() - 1
        was_blocked = combo.blockSignals(True)
        combo.setCurrentIndex(index)
        combo.blockSignals(was_blocked)

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
        if self.record_flag:
            self.stop_recording(reason="Connection lost")

        self.parent.SerialFlag = False
        if self.timer.isActive():
            self.timer.stop()
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
            self._style_recording_dialog(dialog)
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
        # Remove secondary ViewBoxes from an earlier connection.
        # Clearing the PlotWidget does not remove these scene items.

        for attribute in ("current_plots", "stimulus_plots"):
            old_view = getattr(self, attribute, None)

            if old_view is not None:
                old_view.clear()

                scene = old_view.scene()
                if scene is not None:
                    scene.removeItem(old_view)

                old_view.deleteLater()
                setattr(self, attribute, None)

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
        # Independent stimulus plotting area.
        self.stimulus_plots = pg.ViewBox()
        self.stimulus_plots.setMouseEnabled(
            x=False,
            y=False
        )
        self.stimulus_plots.setMenuEnabled(False)
        pw.scene().addItem(self.stimulus_plots)
        self.stimulus_plots.setXLink(pw)
        self.stimulus_plots.enableAutoRange(
            axis=pg.ViewBox.YAxis,
            enable=False
        )
        self.stimulus_plots.setYRange(
            STIMULUS_MIN,
            STIMULUS_MAX,
            padding=0.0
        )
        self.current_plots.setMouseEnabled(x=False, y=False)
        self.current_plots.setMenuEnabled(False)
        pw.scene().addItem(self.current_plots)
        self.current_plots.setXLink(pw)
        self._timebase = apply_scope_timebase(plot_item, TIME_WINDOW,
                                              TIME_WINDOW_DISPLAY,
                                              y_range=(VM_MIN, VM_MAX))

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

        # Stimulus has an independent percentage scale.
        self.stimulus_plots.addItem(self.curve1)

        # Current traces share the current scale.
        for curve in (self.curve2, self.curve4, self.curve6):
            self.current_plots.addItem(curve)

        self.configure_current_axis(
            self.voltage_clamp_display
        )

        self._update_views()

        # The main oscilloscope ViewBox survives device reconnects.
        # Connect the resize handler only once.
        if not self._resize_connected:
            pw.getViewBox().sigResized.connect(self._update_views)
            self._resize_connected = True

    def _update_views(self):
        """
        Align the secondary current and stimulus ViewBoxes
        with the main membrane-potential ViewBox.

        All three ViewBoxes share the same time axis.
        """

        pw = self.ui.Spikeling_Oscilloscope_widget
        main_vb = pw.getViewBox()
        geometry = main_vb.sceneBoundingRect()

        if self.current_plots is not None:
            self.current_plots.setGeometry(geometry)
            self.current_plots.linkedViewChanged(main_vb, self.current_plots.XAxis
            )

        if self.stimulus_plots is not None:
            self.stimulus_plots.setGeometry(geometry)
            self.stimulus_plots.linkedViewChanged(main_vb, self.stimulus_plots.XAxis
            )

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

    def configure_current_axis(self, voltage_clamp=False):
        """
        Configure the current axis for CC or VC.

        CC: total current in legacy arbitrary units.
        VC: clamp current in nanoamperes.

        The independent stimulus axis is not modified.
        """

        self.voltage_clamp_display = bool(voltage_clamp)

        if self.voltage_clamp_display:
            minimum = VC_CURRENT_MIN
            maximum = VC_CURRENT_MAX
            label = "Clamp Current"
            unit = "nA"
        else:
            minimum = CURRENT_MIN
            maximum = CURRENT_MAX
            label = "Current Input"
            unit = "a.u."

        scope = self.ui.Spikeling_Oscilloscope_widget

        scope.setLabel(
            "right",
            label,
            units=unit
        )

        if self.current_plots is not None:
            self.current_plots.setYRange(
                minimum,
                maximum,
                padding=0.0
            )

    # -------------------------------------------------------------------------
    # Saving Data
    # -------------------------------------------------------------------------
    def configure_recording(self):
        """Configure the new recording widgets once."""
        folder = Path(__file__).resolve().parent / "Recordings"

        folder_editor = self.ui.Spikeling_DataRecording_Folder_lineEdit
        folder_editor.setEnabled(True)
        folder_editor.setReadOnly(True)
        folder_editor.setText(str(folder))

        self.ui.Spikeling_DataRecording_File_lineEdit.setPlaceholderText("Enter a file name")

        self.recording_status_timer = QTimer(self)
        self.recording_status_timer.setInterval(250)
        self.recording_status_timer.timeout.connect(self.update_recording_details)

        self._refresh_recording_theme()
        self.ui.Spikeling_DataRecording_Record_label.setWordWrap(True)
        self.ui.Spikeling_DataRecording_Record_label.setText("Ready to record")

        theme_manager.themeChanged.connect(self._refresh_recording_theme)

    def _refresh_recording_theme(self, *_):
        self._set_recording_ui()

        self.ui.Spikeling_DataRecording_Record_label.setStyleSheet("color: rgb(220, 50, 47);")

        for dialog in (self._record_folder_dialog,getattr(self, "_disconnect_dialog", None),):
            if dialog is not None:
                self._style_recording_dialog(dialog)

    def _style_recording_dialog(self, dialog):
        """Apply the active GUI theme to recording-related dialogs."""
        colour = theme_manager.active_colour

        background = colour("window_background")
        panel = colour("panel_background")
        surface = colour("surface")
        text = colour("text_primary")
        muted = colour("text_muted")
        accent = colour("neuron_stimulus")

        dialog.setStyleSheet(f"""
            QDialog, QMessageBox, QFileDialog {{background-color: {background};color: {text};}}
            QLabel, QCheckBox {{color: {text}; background-color: transparent;}}
            QFrame {{background-color: transparent;}}
            QTreeView, QListView, QTableView {{background-color: {panel}; alternate-background-color: {surface}; color: {text}; border: 1px solid {muted}; selection-background-color: {accent}; selection-color: {text};}}
            QTreeView::item:selected,
            QListView::item:selected,
            QTableView::item:selected {{background-color: {accent}; color: {text};}}
            QHeaderView::section {{background-color: {surface}; color: {text}; border: 1px solid {muted}; padding: 4px;}}
            QLineEdit, QComboBox {{background-color: {panel}; color: {text}; border: 1px solid {muted}; border-radius: 4px; padding: 4px;}}
            QComboBox QAbstractItemView {{background-color: {panel}; color: {text}; selection-background-color: {accent};}}
            QPushButton, QToolButton {{ background-color: {surface}; color: {text}; border: 1px solid {muted}; border-radius: 5px; padding: 5px 10px;}}
            QPushButton:hover, QToolButton:hover {{background-color: {panel}; border-color: {accent};}}
            QPushButton:pressed, QToolButton:pressed {{background-color: {background};}}
            QPushButton:disabled, QToolButton:disabled {{color: {muted};}}
        """)

    def _recording_message(self, title, text, question=False):
        """Use the active GUI colours for recording messages."""
        box = QMessageBox(self.parent)
        box.setWindowTitle(title)
        box.setTextFormat(Qt.TextFormat.PlainText)
        box.setText(text)
        box.setIcon(QMessageBox.Icon.Question if question else QMessageBox.Icon.Warning)


        if question:
            box.setStandardButtons(
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No
            )
            box.setDefaultButton(QMessageBox.StandardButton.No)
        else:
            box.setStandardButtons(QMessageBox.StandardButton.Ok)

        self._style_recording_dialog(box)
        return box.exec()

    def browse_record_folder(self, checked=False):
        """Open a reusable folder browser without a nested event loop."""
        if self.record_flag:
            return

        dialog = self._record_folder_dialog

        if dialog is None:
            dialog = QFileDialog(self.parent)

            # Set these options before configuring the browser.
            dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True,)
            dialog.setOption(QFileDialog.Option.DontUseCustomDirectoryIcons, True,)
            dialog.setOption(QFileDialog.Option.ShowDirsOnly, True,)

            dialog.setWindowTitle("Select a recording folder")
            dialog.setFileMode(QFileDialog.FileMode.Directory)
            dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)

            dialog.setLabelText(QFileDialog.DialogLabel.Accept, "Select folder",)

            dialog.finished.connect(self._record_folder_dialog_finished)

            # Keep the dialog and its filesystem model for subsequent uses.
            self._record_folder_dialog = dialog

        if dialog.isVisible():
            dialog.raise_()
            dialog.activateWindow()
            return

        folder = (self.ui.Spikeling_DataRecording_Folder_lineEdit.text())
        dialog.setDirectory(folder)
        self._style_recording_dialog(dialog)

        # Returns immediately; acquisition continues in the main event loop.
        dialog.open()

    def _record_folder_dialog_finished(self, result):
        """Update the destination only when a folder was accepted."""
        dialog = self._record_folder_dialog

        if dialog is None:
            return

        if result != QDialog.DialogCode.Accepted:
            return

        if self.record_flag:
            return

        folders = dialog.selectedFiles()

        if folders:
            self.ui.Spikeling_DataRecording_Folder_lineEdit.setText(folders[0])


    def _recording_path(self):
        """Validate the destination and confirm any replacement."""
        folder_text = (self.ui.Spikeling_DataRecording_Folder_lineEdit.text().strip())
        name = (self.ui.Spikeling_DataRecording_File_lineEdit.text().strip())

        if name.lower().endswith(".csv"):
            name = name[:-4].strip()

        invalid = '<>:"/\\|?*'

        reserved = {"CON", "PRN", "AUX", "NUL"}
        reserved.update(f"COM{i}" for i in range(1, 10))
        reserved.update(f"LPT{i}" for i in range(1, 10))

        if (
            not name
            or name in {".", ".."}
            or name.endswith((".", " "))
            or any(c in invalid or ord(c) < 32 for c in name)
            or name.split(".")[0].upper() in reserved
        ):
            raise ValueError(
                "Enter a valid file name without a folder path. "
                "The .csv extension is added automatically."
            )

        if not folder_text:
            raise ValueError(
                "Select a recording folder using Browse."
            )

        folder = Path(folder_text)
        default = Path(__file__).resolve().parent / "Recordings"

        if folder == default:
            folder.mkdir(parents=True, exist_ok=True)

        if not folder.is_dir():
            raise ValueError(
                "The recording folder does not exist. "
                "Select it again."
            )

        # Test actual file creation in the selected directory.
        with tempfile.TemporaryFile(dir=folder):
            pass

        path = folder / f"{name}.csv"

        if path.exists():
            answer = self._recording_message(
                "File already exists",
                f"{path.name} already exists.\n\n"
                "Replace it when this recording is saved?\n"
                "Choose No to enter another file name.",
                question=True,
            )

            if answer != QMessageBox.StandardButton.Yes:
                return None

        self.ui.Spikeling_DataRecording_File_lineEdit.setText(name)

        return path

    def _recording_mode(self):
        vc = self.ui.PatchClampMode_toggleButton.isChecked()

        model = (self.ui.Spikeling_PatchClamp_MembraneModel_comboBox.currentText() if vc else "")

        return vc, model


    def handle_record_button(self, checked=False):
        """Choose the action from recording state."""
        if self.record_flag:
            self.stop_recording()

        elif self._recording_save_pending:
            try:
                path = self._recording_path()
            except (OSError, ValueError) as error:
                self._set_recording_ui()
                self._recording_message(
                    "Cannot save recording",
                    str(error),
                )
                return

            if path is not None:
                self._current_save_path = path
                self.stop_recording()
            else:
                self._set_recording_ui()

        else:
            self.start_recording()

    def start_recording(self):
        if not (
            serial_manager.is_open
            and self.supervisor.state == ConnectionState.CONNECTED
        ):
            self._set_recording_ui()
            self._recording_message(
                "Spikeling not connected",
                "Connect a Spikeling board and wait until it is ready.",
            )
            return

        try:
            path = self._recording_path()
        except (OSError, ValueError) as error:
            self._set_recording_ui()
            self._recording_message(
                "Cannot start recording",
                str(error),
            )
            return

        if path is None:
            self._set_recording_ui()
            return

        # Modal dialogs process events, so check the connection again.
        if not (
            serial_manager.is_open
            and self.supervisor.state == ConnectionState.CONNECTED
        ):
            self._set_recording_ui()
            self._recording_message(
                "Spikeling not connected",
                "The board disconnected before recording started.",
            )
            return

        self.spikeling_data = [[] for _ in range(9)]
        self._current_save_path = path

        self._recording_mode_at_start = self._recording_mode()
        self._recording_started = time.monotonic()
        self._recording_stop_reason = ""
        self._recording_save_pending = False

        self.record_flag = True

        self.recording_status_timer.start()
        self._set_recording_ui()
        self.update_recording_details()


    def _set_recording_ui(self):
        button = self.ui.Spikeling_DataRecording_Record_pushButton

        with QSignalBlocker(button):
            button.setChecked(self.record_flag)

        button.setText(
            "Stop recording"
            if self.record_flag
            else "Retry save"
            if self._recording_save_pending
            else "Record"
        )

        # Preserve the existing red idle / green recording convention.
        palette = theme_manager.palette()
        background = palette[4] if self.record_flag else palette[3]
        rgb = tuple(background)

        button.setStyleSheet(
            f"QPushButton {{"
            f"color: white;"
            f"background-color: rgb{rgb};"
            f"}}"
            "QPushButton:hover { border: 2px solid white; }"
            "QPushButton:pressed { border: 2px solid #586e75; }"
        )

        for widget in (self.ui.Spikeling_DataRecording_Folder_pushButton, self.ui.Spikeling_DataRecording_File_lineEdit,):
            widget.setEnabled(not self.record_flag)

    def update_recording_details(self):
        if not self.record_flag:
            return

        count = len(self.spikeling_data[1])
        elapsed = time.monotonic() - self._recording_started

        vc, model = self._recording_mode_at_start
        mode = f"VC ({model})" if vc else "CC"

        neuron = self.ui.Spikeling_NeuronModeComboBox.currentText()

        stimulus = getattr(self.parent, "custom_stimulus_controller", None,)

        if stimulus is not None and stimulus.running:
            source = (
                f"Custom: {stimulus.filename} "
                f"(GUI loop {stimulus.completed_loops + 1}/"
                f"{stimulus.requested_loops})"
            )
        else:
            source = "Built-in stimulus"

        text = (
            f"Recording • {elapsed:.1f} s elapsed • {count:,} samples\n"
            f"{mode} • Preset selection: {neuron} • "
            f"Model step {SAMPLE_INTERVAL:g} ms\n"
            f"{source}"
        )

        label = self.ui.Spikeling_DataRecording_Record_label
        label.setText(text)
        label.setToolTip(
            f"File: {self._current_save_path}\n"
            "Time in CSV is reconstructed from sample count. "
            "This stream cannot yet detect missing samples."
        )


    def stop_recording(self, reason="Stopped"):
        """Stop capture, save, and retain samples if saving fails."""
        if not self.record_flag and not self._recording_save_pending:
            return True

        if self.record_flag:
            self._recording_stop_reason = reason

        self.record_flag = False
        self.recording_status_timer.stop()

        count = len(self.spikeling_data[1])
        self._recording_save_pending = count > 0

        self._set_recording_ui()

        if not count:
            self.ui.Spikeling_DataRecording_Record_label.setText(
                "Stopped • No samples received"
            )
            self._recording_message(
                "No samples recorded",
                "No samples were received. "
                "No recording file was created.",
            )
            return True

        if not self.export_data_to_csv(self._current_save_path):
            self._recording_save_pending = True
            self._set_recording_ui()

            self.ui.Spikeling_DataRecording_Record_label.setText(
                f"Save failed • {count:,} samples retained • Retry save"
            )

            self._recording_message(
                "Recording could not be saved",
                f"{self._recording_error}\n\n"
                "Samples are still held in memory. "
                "Select another folder or file name if needed, "
                "then click Retry save. "
                "Keep the application open until saving succeeds.",
            )
            return False

        self._recording_save_pending = False
        self.spikeling_data = [[] for _ in range(9)]

        self._set_recording_ui()

        self.ui.Spikeling_DataRecording_Record_label.setText(
            f"{self._recording_stop_reason} • "
            f"Saved {count:,} samples\n"
            f"{self._current_save_path.name}"
        )

        return True


    def export_data_to_csv(self, file_path):
        """Replace the destination only after writing a complete CSV."""
        temporary_path = None

        try:
            count = len(self.spikeling_data[1])

            if any(
                len(channel) != count
                for channel in self.spikeling_data[1:]
            ):
                raise ValueError(
                    "Recorded channels have different sample counts."
                )

            vc, _ = self._recording_mode_at_start
            unit = "nA" if vc else "a.u."
            current = "Clamp current" if vc else "Total Current Input"

            columns = [
                "Spikeling Vm (mV)",
                "Stimulus (%)",
                f"{current} ({unit})",
                "Synapse 1 Vm (mV)",
                f"Synapse 1 Input ({unit})",
                "Synapse 2 Vm (mV)",
                f"Synapse 2 Input ({unit})",
                "Trigger",
            ]

            frame = {
                "Time (ms)": (
                    np.arange(count, dtype=float) * SAMPLE_INTERVAL
                )
            }

            frame.update({
                name: self.spikeling_data[index + 1]
                for index, name in enumerate(columns)
            })

            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="",
                dir=file_path.parent,
                prefix=f".{file_path.stem}_",
                suffix=".tmp",
                delete=False,
            ) as handle:
                temporary_path = Path(handle.name)

                pd.DataFrame(frame).to_csv(handle, index=False)

                handle.flush()
                os.fsync(handle.fileno())

            os.replace(temporary_path, file_path)

            return True

        except Exception as error:
            self._recording_error = str(error)
            return False

        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    pass


# -------------------------------------------------------------------------
# Cleanup
# -------------------------------------------------------------------------

    def cleanup(self):
        """Release resources."""
        if self.record_flag:
            self.stop_recording(reason="Disconnected")

        if self.timer.isActive():
            self.timer.stop()

        self.last_valid_data = None

        for buffer in self.databuffers:
            buffer.fill_with(0.0)

        self.ui.Spikeling_Oscilloscope_widget.clear()
        if self.current_plots:
            self.current_plots.clear()

