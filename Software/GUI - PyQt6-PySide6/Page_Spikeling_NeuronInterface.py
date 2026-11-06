
########################################################################
#                          Libraries import                            #

from PySide6.QtWidgets import QFileDialog, QMessageBox
from PySide6.QtGui import QIcon, QIntValidator
from PySide6.QtCore import Qt, QSize, QObject, QFileInfo, QSignalBlocker
from Parameters_ToggleButtons import PyToggle
from Parameters_Sliders import configure_styled_slider
from Parameters_Sliders import SliderBinding

from serial_manager import serial_manager
import os
import math
import numpy as np
import pandas as pd

import Parameters_Settings as Settings
import Parameters_NavigationButtons as NavigationButtons
from Parameters_Izhikevich import IzhikevichNeurons
from connection_supervisor import ConnectionState


# Use the global serial_manager instance
serial_port = serial_manager

class CustomStimulusController(QObject):
    """Own custom-stimulus loading, playback and control lockout."""

    SAMPLE_INTERVAL_MS = 0.1

    def __init__(self, host):
        super().__init__(host)

        self.host = host
        self.ui = host.ui

        self.samples = None
        self.filename = ""
        self.running = False

        self.index = 0
        self.completed_loops = 0
        self.requested_loops = 1
        self.last_sent_value = None
        self._locked_widgets = []

        loop_editor = self.ui.Spikeling_CustomStimulus_Loop_lineEdit
        loop_editor.setValidator(
            QIntValidator(1, 1000000, loop_editor)
        )
        loop_editor.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if not loop_editor.text().strip():
            loop_editor.setText("1")

        with QSignalBlocker(self.ui.StimCus_toggleButton):
            self.ui.StimCus_toggleButton.setChecked(False)

        self.ui.Spikeling_CustomStimulus_Load_pushButton.clicked.connect(
            self.load
        )
        self.ui.StimCus_toggleButton.toggled.connect(
            self._on_apply_toggled
        )

        serial_port.data_received.connect(self._on_packet)
        serial_port.connection_changed.connect(
            self._on_connection_changed
        )

        # Refresh availability after the connection handshake.
        graph = getattr(host, "spikeling_graph", None)

        if graph is not None:
            graph.supervisor.connected.connect(
                lambda port: self._refresh_controls()
            )
            graph.supervisor.reconnected.connect(
                lambda port: self._refresh_controls()
            )

        self._refresh_controls()

    def _connection_ready(self):
        graph = getattr(self.host, "spikeling_graph", None)

        return (
            serial_port.is_open
            and graph is not None
            and graph.supervisor.state == ConnectionState.CONNECTED
        )

    def _refresh_controls(self):
        self.ui.Spikeling_CustomStimulus_Load_pushButton.setEnabled(
            not self.running
        )
        self.ui.Spikeling_CustomStimulus_Loop_lineEdit.setEnabled(
            not self.running
        )

        self.ui.StimCus_toggleButton.setEnabled(
            self.running
            or (
                self.samples is not None
                and self._connection_ready()
            )
        )

        self.ui.Spikeling_CustomStimulus_Label.setText(
            "Stop stimulus" if self.running else "Apply stimulus"
        )

    def _set_apply_checked(self, checked):
        # Avoid recursively calling the playback handler.
        with QSignalBlocker(self.ui.StimCus_toggleButton):
            self.ui.StimCus_toggleButton.setChecked(checked)

        # PyToggle uses stateChanged to animate its circle.
        self.ui.StimCus_toggleButton.start_transition(int(checked))

    def load(self, checked=False):
        if self.running:
            return

        path, _ = QFileDialog.getOpenFileName(
            self.host,
            caption="Select a custom stimulus",
            dir="./Stimuli",
            filter="CSV files (*.csv)",
        )

        if not path:
            return

        try:
            frame = pd.read_csv(path)

            if "Stim" not in frame.columns:
                raise ValueError(
                    "The CSV must contain a column named 'Stim'."
                )

            values = pd.to_numeric(
                frame["Stim"],
                errors="raise",
            ).to_numpy(dtype=float)

            if values.size == 0:
                raise ValueError("The stimulus contains no samples.")

            if not np.isfinite(values).all():
                raise ValueError(
                    "Stimulus values must all be finite numbers."
                )

            if ((values < -100) | (values > 100)).any():
                raise ValueError(
                    "Stimulus values must be between -100 and 100."
                )

            # SC1 currently accepts integer stimulus commands.
            if not np.allclose(
                values,
                np.rint(values),
                rtol=0,
                atol=1e-9,
            ):
                raise ValueError(
                    "Stimulus values must be integers "
                    "because SC1 uses integer commands."
                )

            samples = np.rint(values).astype(np.int16)

        except (
            OSError,
            ValueError,
            pd.errors.ParserError,
        ) as error:
            QMessageBox.warning(
                self.host,
                "Cannot load stimulus",
                str(error),
            )
            return

        # Commit only after the entire file has passed validation.
        self.samples = samples.copy()
        self.filename = os.path.splitext(
            os.path.basename(path)
        )[0]

        self.ui.Spikeling_CustomStimulus_StimLabel.setText(
            self.filename
        )

        x = (
            np.arange(samples.size, dtype=float)
            * self.SAMPLE_INTERVAL_MS
        )

        preview = self.ui.Spikeling_CustomStimulus_display
        preview.clear()
        preview.showGrid(x=False, y=False)
        preview.setLabel("bottom", "Model time", units="ms")
        preview.setLabel("left", "Stimulus", units="%")
        preview.plot(
            x=x,
            y=samples,
            pen=Settings.DarkSolarized[5],
        )

        self._refresh_controls()

    def _on_apply_toggled(self, checked):
        if checked:
            self.start()
        else:
            self.stop()

    def start(self):
        if self.running:
            return

        error = None
        editor = self.ui.Spikeling_CustomStimulus_Loop_lineEdit

        if self.samples is None:
            error = "Load a stimulus first."
        elif not self._connection_ready():
            error = "Connect the board before applying a stimulus."
        elif not editor.hasAcceptableInput():
            error = "Enter a loop count between 1 and 1000000."

        if error is not None:
            self._set_apply_checked(False)
            self._refresh_controls()
            QMessageBox.warning(
                self.host,
                "Cannot apply stimulus",
                error,
            )
            return

        self.requested_loops = int(editor.text())
        self.completed_loops = 0
        self.index = 0
        self.last_sent_value = None
        self.running = True

        # Enter custom mode before releasing the normal GUI overrides.
        if not self._send_next_sample():
            return

        if not self._write("TR\n"):
            return

        self._lock_normal_controls()
        self._set_apply_checked(True)
        self._update_progress()
        self._refresh_controls()

    def _lock_normal_controls(self):
        for toggle, binding in (
            (
                self.ui.StimFre_toggleButton,
                self.host.stimulus_frequency_binding,
            ),
            (
                self.ui.StimStr_toggleButton,
                self.host.stimulus_strength_binding,
            ),
        ):
            binding.cancel_pending()

            # Allow normal toggle animation and binding synchronisation.
            toggle.setChecked(False)
            binding.set_active(False)

            self._locked_widgets.append(
                (toggle, toggle.isEnabled())
            )
            toggle.setEnabled(False)

            binding.editor.setText("Custom stimulus")

        # Prevent changing the waveform's interpretation mid-playback.
        for widget in (
            self.ui.PatchClampMode_toggleButton,
            self.ui.Spikeling_PatchClamp_MembraneModel_comboBox,
        ):
            self._locked_widgets.append(
                (widget, widget.isEnabled())
            )
            widget.setEnabled(False)

    def _unlock_normal_controls(self):
        for widget, was_enabled in self._locked_widgets:
            widget.setEnabled(was_enabled)

        self._locked_widgets.clear()

        # Refresh normal readings through their public binding API.
        for binding in (
            self.host.stimulus_frequency_binding,
            self.host.stimulus_strength_binding,
        ):
            binding.set_value(binding.value, send=False)

    def _write(self, command):
        if serial_port.is_open and serial_port.write(command):
            return True

        self.stop(send=False)
        self.ui.Spikeling_CustomStimulus_StimLabel.setText(
            "Stopped: serial write failed"
        )
        return False

    def _send_next_sample(self):
        value = int(self.samples[self.index])

        # The firmware holds the last command between changes.
        if value != self.last_sent_value:
            if not self._write(f"SC1 {value}\n"):
                return False

            self.last_sent_value = value

        self.index += 1
        return True

    def _on_packet(self, data):
        if not self.running:
            return

        # Wait until the following packet before advancing beyond
        # the final sample of a loop.
        if self.index >= self.samples.size:
            self.completed_loops += 1

            if self.completed_loops >= self.requested_loops:
                self.stop(completed=True)
                return

            self.index = 0

            if not self._write("TR\n"):
                return

            self._update_progress()

        self._send_next_sample()

    def _update_progress(self):
        self.ui.Spikeling_CustomStimulus_StimLabel.setText(
            f"{self.filename} — "
            f"loop {self.completed_loops + 1}/"
            f"{self.requested_loops}"
        )

    def stop(self, *, send=True, completed=False):
        was_running = self.running
        self.running = False

        self._set_apply_checked(False)

        if was_running:
            self._unlock_normal_controls()

            if send and serial_port.is_open:
                # Resume the standard generator with knob control.
                serial_port.write("SC0\n")

        self.last_sent_value = None

        if self.filename:
            suffix = " — completed" if completed else ""
            self.ui.Spikeling_CustomStimulus_StimLabel.setText(
                self.filename + suffix
            )

        self._refresh_controls()

    def _on_connection_changed(self, connected):
        if not connected:
            self.stop(send=False)

        self._refresh_controls()

    def restore_after_connection(self):
        """Abort stale playback and restore the normal stimulus route."""
        self.stop(send=False)

        if serial_port.is_open:
            serial_port.write("SC0\n")
            serial_port.write("FR0\n")
            serial_port.write("ST0\n")

        self._refresh_controls()

class Spikeling():

    def ShowPage(self):
        self.ui.Spikeling_rightMenuContainer.setMinimumSize(QSize(NavigationButtons.spikerightMenu_max, 16777215))
        self.ui.Spikeling_Oscilloscope_widget.setBackground(Settings.DarkSolarized[0])
        self.ui.Spikeling_CustomStimulus_display.setBackground(Settings.DarkSolarized[0])
        self.ui.mainbody_stackedWidget.setCurrentWidget(self.ui.page_Spikeling_NeuronInterface)
        NavigationButtons.toggleMenu(self, self.ui.Spikeling_rightMenuContainer, NavigationButtons.spikerightMenu_min, NavigationButtons.spikerightMenu_max, NavigationButtons.animation_speed,
                                     self.ui.Spikeling_rightMenuSubContainer_pushButton, self.icon_SpikelingMenuRight, self.icon_SpikelingDropMenuRight, True)

    # Serial Port Functions
    def ChangePort(self):
        """
        Handle a manual port selection from the combo box.

        Notes
        -----
        A no-op whenever the connection supervisor owns the link. The
        supervisor is reached through ``spikeling_graph``, which constructs
        it in ``setup_auto_connection``; probing ``self`` directly finds
        nothing, because ``self`` is the main window here.

        Reopening the port on an index change also cascades:
        ``configure_port`` emits ``connection_changed(False)``, which
        ``SpikelingGraph.on_connection_changed`` routes to
        ``disconnect_device``, which calls ``supervisor.stop()`` and disables
        reconnection for the rest of the session.
        """
        graph = getattr(self, "spikeling_graph", None)
        supervisor = getattr(graph, "supervisor", None)
        if supervisor is not None and supervisor.state is not ConnectionState.IDLE:
            return

        self.COM = self.ui.Spikeling_SelectPortComboBox.currentText()
        if not self.COM:
            return
        if serial_port.configure_port(self.COM) and serial_port.open():
            serial_port.write('CON' + '\n')
        self.ui.Spikeling_ConnectButton.setChecked(False)

    # Modifu microcontroller loop time
    def ChangeSpeed(self):
        self.Speed_SliderValue = self.ui.Spikeling_Speed_slider.value()
        if self.Speed_SliderValue == 0:
            self.Speed = 20000
        elif self.Speed_SliderValue == 1:
            self.Speed = 10000
        elif self.Speed_SliderValue == 2:
            self.Speed = 4000
        elif self.Speed_SliderValue == 3:
            self.Speed = 2000
        elif self.Speed_SliderValue == 4:
            self.Speed = 1000
        elif self.Speed_SliderValue == 5:
            self.Speed = 400
        elif self.Speed_SliderValue == 6:
            self.Speed = 200

        self.DT_Display = round(0.1 / self.Speed * 1000, 3)
        self.DT_Speed = self.Speed
        self.ui.Spikeling_Speed_value.setText("x " + str(self.DT_Display))

        if serial_port.is_open:
            serial_port.write('DT ' + str(self.DT_Speed) + '\n')

    # Control buzzer sound
    def ControlBuzzer(self):
        global serial_port
        icon_buzzer_off = QIcon()
        icon_buzzer_off.addFile(u":/resources/resources/SoundOFF.png", QSize(), QIcon.Normal, QIcon.Off)
        icon_buzzer_on = QIcon()
        icon_buzzer_on.addFile(u":/resources/resources/SoundON.png", QSize(), QIcon.Normal, QIcon.Off)
        if self.ui.Sound_pushButton.isChecked():
            self.ui.Sound_pushButton.setIcon(icon_buzzer_off)
            self.ui.Sound_pushButton.setText("Buzzer Off   ")
            if serial_port.is_open:
                serial_port.write('BZ0' + '\n')
        else:
            self.ui.Sound_pushButton.setIcon(icon_buzzer_on)
            self.ui.Sound_pushButton.setText("Buzzer On   ")
            if serial_port.is_open:
                serial_port.write('BZ1' + '\n')

    # Control LED light
    def ControlLED(self):
        global serial_port
        icon_LED_off = QIcon()
        icon_LED_off.addFile(u":/resources/resources/LEDOFF.png", QSize(), QIcon.Normal, QIcon.Off)
        icon_LED_on = QIcon()
        icon_LED_on.addFile(u":/resources/resources/LEDON.png", QSize(), QIcon.Normal, QIcon.Off)
        if self.ui.LED_pushButton.isChecked():
            self.ui.LED_pushButton.setIcon(icon_LED_off)
            self.ui.LED_pushButton.setText("LED Off   ")
            if serial_port.is_open:
                serial_port.write('LED0' + '\n')
        else:
            self.ui.LED_pushButton.setIcon(icon_LED_on)
            self.ui.LED_pushButton.setText("LED On   ")
            if serial_port.is_open:
                serial_port.write('LED1' + '\n')


    # Data Recording Functions
    def BrowseRecordFolder(self):
        FolderName = QFileDialog.getExistingDirectory(caption = 'Hey! Select the folder where your experiment will be saved',
                                      dir = ".\\Recordings")
        if FolderName:
            self.Spikeling_DataRecording_SelectRecordFolder_label.setText(FolderName)
            self.Spikeling_DataRecording_RecordFolder_value.setEnabled(True)
            self.Spikeling_DataRecording_RecordFolder_value.setPlaceholderText("Enter a file name")
            self.NeuronRecordFolderFlag = True


    def RecordFolderText(self):
        FolderName = self.ui.Spikeling_DataRecording_SelectRecordFolder_label.text()
        FileName = self.ui.Spikeling_DataRecording_RecordFolder_value.text()
        self.ui.Spikeling_SelectedFolderLabel.setText(FolderName + '/' + FileName + '   ')


    def RecordButton(self):
        SerialPortFlag = False
        FolderFlag = False
        FileFlag = False

        if self.ui.Spikeling_DataRecording_Record_pushButton.isChecked():

            if self.SerialFlag == False:
                self.ui.Spikeling_DataRecording_Record_pushButton.setChecked(False)
                Settings.show_popup(self,
                                    Title = "Error: Spikeling not connected",
                                    Text = "Spikeling first needs to be connected, then a COM port has to be selected and finally press the - Connect Spikeling Screen - button" )
            else:
                SerialPortFlag = True


            if self.ui.NeuronRecordFolderFlag == True:
                FolderFlag = True

            else:
                self.ui.Spikeling_DataRecording_Record_pushButton.setChecked(False)
                Settings.show_popup(self,
                                    Title = "Error: no folder selected",
                                    Text = "Select a folder where to record your data by clicking on the - browse directory - button")


            if self.ui.Spikeling_DataRecording_RecordFolder_value.text():
                FileFlag = True

            else:
                self.ui.Spikeling_DataRecording_Record_pushButton.setChecked(False)
                Settings.show_popup(self,
                                    Title="Error: no file selected",
                                    Text="Select a file where to record your data by clicking on the - browse directory - button")


            if SerialPortFlag == True and FolderFlag == True and FileFlag == True:
                if self.ui.Spikeling_DataRecording_Record_pushButton.isChecked():
                    self.ui.Spikeling_DataRecording_Record_pushButton.setText("Stop Recording")
                    self.ui.Spikeling_DataRecording_Record_pushButton.setStyleSheet("color: rgb(250, 250, 250);\n"
                                                                                    "background-color: rgb(50, 220, 47);")

        if self.ui.Spikeling_DataRecording_Record_pushButton.isChecked() == False:
            self.ui.Spikeling_DataRecording_Record_pushButton.setText("Record")
            self.ui.Spikeling_DataRecording_Record_pushButton.setStyleSheet("color: rgb(250, 250, 250);\n"
                                                                            "background-color: rgb(220, 50, 47);")




    # Stimulus Frequency
    ##################################################
    def ConfigureStimulusFrequency(self):
        """Connect the frequency slider, editable reading and serial commands."""

        if hasattr(self, "stimulus_frequency_binding"):
            return

        slider = self.ui.Spikeling_StimFre_slider

        # Preserve the constants used by the existing frequency conversion.
        self.Stim_DutyCycle = 500
        self.Stim_MinCycle = 10
        duty_cycle = self.Stim_DutyCycle
        minimum_cycle = self.Stim_MinCycle

        def period_from_position(position):
            return ( duty_cycle - position * duty_cycle / 100 + minimum_cycle )

        # Every available slider position must produce a positive period.
        if min(period_from_position(slider.minimum()), period_from_position(slider.maximum()),) <= 0:
            raise ValueError("Stimulus-frequency slider range produces a non-positive period.")

        def frequency_from_position(position):
            """Convert a slider position into the existing frequency units."""
            return 10000 / period_from_position(position)

        def format_frequency(frequency):
            """Preserve the existing integer frequency display."""
            return str(round(frequency))

        def position_from_frequency(frequency):
            """Select the slider position giving the nearest frequency."""
            endpoint_frequencies = (
                frequency_from_position(slider.minimum()),
                frequency_from_position(slider.maximum()),
            )

            lower = min(endpoint_frequencies)
            upper = max(endpoint_frequencies)

            if not lower <= frequency <= upper:
                raise ValueError("Frequency is outside the available range.")

            # Integer readings can represent several slider positions.
            # Re-entering the displayed value should preserve the current one.
            current_position = slider.value()
            current_text = format_frequency(frequency_from_position(current_position))

            if frequency == float(current_text):
                return current_position

            # Invert the existing frequency equation.
            raw_position = ( (duty_cycle + minimum_cycle - 10000 / frequency) * 100 / duty_cycle )

            # Compare neighbouring positions in frequency units.
            # Simply rounding raw_position is less accurate for this
            # nonlinear mapping.
            candidates = {
                max(
                    slider.minimum(),
                    min(slider.maximum(), math.floor(raw_position)),
                ),
                max(
                    slider.minimum(),
                    min(slider.maximum(), math.ceil(raw_position)),
                ),
            }

            return min(
                candidates,
                key=lambda position: (
                    abs(frequency_from_position(position) - frequency),
                    position,
                ),
            )

        binding = SliderBinding(
            slider=slider,
            editor=self.ui.Spikeling_StimFre_readings,
            alignment=Qt.AlignmentFlag.AlignCenter,
            active=self.ui.StimFre_toggleButton.isChecked(),
            default_position=0,
            disabled_text="Knob control",
            active_editor_style=( "color: rgb" + str(tuple(Settings.DarkSolarized[5])) + "; font: 700 10pt;" ),
            disabled_editor_style=( "color: rgb(88, 110, 117);" "font-size: 9pt;" "font-weight: 400;" ),
            to_display=frequency_from_position,
            to_slider=position_from_frequency,
            format_value=format_frequency,
            interval_ms=40,
        )

        self.stimulus_frequency_binding = binding

        def remember_value(position):
            # Preserve the existing attributes and their meanings.
            self.StimFreValue = -position
            self.setTextStimFre = format_frequency(frequency_from_position(position))

        def apply_value(position):
            if serial_port.is_open:
                serial_port.write(f"FR1 {-position}\n")

        def disable_control():
            if serial_port.is_open:
                serial_port.write("FR0\n")

        def connection_changed(connected):
            binding.cancel_pending()

        # Initialise application attributes without sending a command.
        remember_value(binding.value)

        binding.valueChanged.connect(remember_value)
        binding.applyRequested.connect(apply_value)
        binding.disableRequested.connect(disable_control)

        self.ui.StimFre_toggleButton.toggled.connect(binding.set_active)

        serial_port.connection_changed.connect(connection_changed)



    # Stimulus Strength
    ##################################################
    def ConfigureStimulusStrength(self):
        """Create and connect the stimulus-strength slider binding once."""

        # Avoid duplicate connections if setup is called again.
        if hasattr(self, "stimulus_strength_binding"):
            return

        binding = SliderBinding(
            slider=self.ui.Spikeling_StimStr_slider,
            editor=self.ui.Spikeling_StimStr_readings,
            alignment=Qt.AlignmentFlag.AlignCenter,
            active=self.ui.StimStr_toggleButton.isChecked(),
            default_position=0,
            disabled_text="Knob control",
            active_editor_style=("color: rgb" + str(tuple(Settings.DarkSolarized[5])) + "; font: 700 10pt;"),
            disabled_editor_style=("color: rgb(88, 110, 117);" "font-size: 9pt;" "font-weight: 400;"),
            to_display=float,
            to_slider=float,
            format_value=lambda value: f"{value:.0f}",
            interval_ms=40,
        )

        # Keep a reference and initialise the application value.
        self.stimulus_strength_binding = binding
        self.StimStrValue = binding.value

        def remember_value(value):
            self.StimStrValue = value

        def apply_value(value):
            if serial_port.is_open:
                serial_port.write(f"ST1 {value}\n")

        def disable_control():
            if serial_port.is_open:
                serial_port.write("ST0\n")

        def connection_changed(connected):
            # Discard updates scheduled before a connection transition.
            binding.cancel_pending()

        binding.valueChanged.connect(remember_value)
        binding.applyRequested.connect(apply_value)
        binding.disableRequested.connect(disable_control)

        self.ui.StimStr_toggleButton.toggled.connect(binding.set_active)

        serial_port.connection_changed.connect(connection_changed)


    # Custom Stimulus
    def ConfigureCustomStimulus(self):
        """Create the custom-stimulus controller once."""

        if hasattr(self, "custom_stimulus_controller"):
            return

        self.custom_stimulus_controller = CustomStimulusController(self)


    # Patch Clamp
    ##################################################
    def ConfigurePatchClamp(self):
        """Configure CC/VC presentation, slider binding and serial callbacks."""

        if hasattr(self, "patch_clamp_binding"):
            return

        slider = self.ui.Spikeling_PatchClamp_slider
        mode_toggle = self.ui.PatchClampMode_toggleButton
        override_toggle = self.ui.PatchClamp_toggleButton

        membrane_combo = self.ui.Spikeling_PatchClamp_MembraneModel_comboBox
        membrane_label = self.ui.Spikeling_PatchClamp_MembraneModel_label

        modes = {
            False: {
                "minimum": -100,
                "maximum": 100,
                "default": 0,
                "title": "Injected Current (a.u.)",
                "colour": "rgb(133, 153, 0)",
                "fill": "#859900",
            },
            True: {
                "minimum": -110,
                "maximum": 30,
                "default": -70,
                "title": "Holding Voltage (mV)",
                "colour": "rgb(220, 50, 47)",
                "fill": "#DC322F",
            },
        }

        initial = modes[mode_toggle.isChecked()]

        # Set the correct initial range before constructing the binding.
        with QSignalBlocker(slider):
            slider.setRange(initial["minimum"], initial["maximum"])
            slider.setValue(initial["default"])

        binding = SliderBinding(
            slider=slider,
            editor=self.ui.Spikeling_PatchClamp_readings,
            alignment=Qt.AlignmentFlag.AlignCenter,
            active=override_toggle.isChecked(),
            default_position=initial["default"],
            disabled_text="Knob control",
            active_editor_style=(f"color: {initial['colour']}; font: 700 10pt;"),
            disabled_editor_style=("color: rgb(88, 110, 117);""font-size: 9pt;""font-weight: 400;"),
            to_display=float,
            to_slider=float,
            format_value=lambda value: f"{value:.0f}",
            interval_ms=40,
        )

        self.patch_clamp_binding = binding

        def remember_value(value):
            self.PatchClampValue = value

            # Preserve the attribute used by the previous implementation.
            self.InjectedCurrent = value

        def apply_value(value):
            if serial_port.is_open:
                serial_port.write(f"PC1 {value}\n")

        def disable_control():
            if serial_port.is_open:
                serial_port.write("PC0\n")

        def select_mode(is_vc, *, send=True):
            """Update the complete GUI before sending the new clamp mode."""
            settings = modes[bool(is_vc)]
            colour = settings["colour"]

            binding.reconfigure(
                minimum=settings["minimum"],
                maximum=settings["maximum"],
                default_position=settings["default"],
                active_editor_style=f"color: {colour}; font: 700 10pt;",
            )

            # Update labels inside Spikeling_PatchClampSelector_label.
            cc_colour = ("rgb(88, 110, 117)"if is_vc else "rgb(133, 153, 0)"
            )
            vc_colour = ("rgb(220, 50, 47)"if is_vc else "rgb(88, 110, 117)"
            )

            self.ui.Spikeling_CurrentClamp_label.setStyleSheet(f"color: {cc_colour}; font: 700 10pt;")
            self.ui.Spikeling_VoltageClamp_label.setStyleSheet(f"color: {vc_colour}; font: 700 10pt;")

            # Membrane-model selection is available only in VC.
            membrane_colour = ("rgb(190, 205, 205)" if is_vc else "rgb(88, 110, 117)")
            membrane_combo.setEnabled(bool(is_vc))
            membrane_combo.setStyleSheet(f"color: {membrane_colour};")
            membrane_label.setStyleSheet(f"color: {membrane_colour};")

            # Update contents of Spikeling_PatchClamp_Command_frame.
            self.ui.Spikeling_PatchClamp_Label.setText(settings["title"])

            slider.set_fill_color(settings["fill"])
            override_toggle.set_active_color(settings["fill"])

            minimum = settings["minimum"]
            maximum = settings["maximum"]
            midpoint = (minimum + maximum) // 2

            self.ui.Spikeling_PatchClamp_values_min.setText(str(minimum))
            self.ui.Spikeling_PatchClamp_values_0.setText(str(midpoint))
            self.ui.Spikeling_PatchClamp_values_max.setText(str(maximum))

            # Update graph units even during initial UI configuration.
            graph = getattr(self, "spikeling_graph", None)

            if graph is not None:
                graph.configure_current_axis(voltage_clamp=bool(is_vc))

            if send:
                Spikeling.SyncPatchClampState(self)

        def connection_changed(connected):
            # Reconnection restoration happens after the board handshake.
            binding.cancel_pending()

        def select_membrane_model(index):
            # Change the backend without resetting the holding-voltage slider.
            if mode_toggle.isChecked():
                Spikeling.SyncPatchClampState(self)

        remember_value(binding.value)

        binding.valueChanged.connect(remember_value)
        binding.applyRequested.connect(apply_value)
        binding.disableRequested.connect(disable_control)

        override_toggle.toggled.connect(binding.set_active)
        mode_toggle.toggled.connect(select_mode)
        membrane_combo.currentIndexChanged.connect(select_membrane_model)

        serial_port.connection_changed.connect(connection_changed)

        # Initialise presentation without sending commands.
        select_mode(mode_toggle.isChecked(), send=False)

    def SyncPatchClampState(self):
        """
        Synchronise the patch-clamp mode with the firmware.

        The CC/VC toggle determines the graph's current units.
        The Patch Clamp override toggle determines whether PC1
        or the physical potentiometer controls the command.

        Called with the MainWindow instance as self.
        """

        binding = getattr(self, "patch_clamp_binding", None)

        if binding is None:
            return

        binding.cancel_pending()

        # The clamp mode is determined only by the CC/VC toggle.
        is_vc = self.ui.PatchClampMode_toggleButton.isChecked()

        # Update the existing graph object, not MainWindow.
        graph = getattr(self, "spikeling_graph", None)

        if graph is not None:
            graph.configure_current_axis(voltage_clamp=is_vc)

        # Allow local GUI presentation to update while disconnected.
        if not serial_port.is_open:
            return

        # Tell the firmware which model to use.
        # PC1 is interpreted in the correct units only after VCM.
        if not serial_port.write(f"VCM {int(is_vc)}\n"):
            return
        # Select the actual membrane backend when voltage clamp is active.
        if is_vc:
            combo = self.ui.Spikeling_PatchClamp_MembraneModel_comboBox
            model_name = combo.currentText().strip().casefold()

            if model_name == "active":
                active_model = 1
            elif model_name == "passive":
                active_model = 0
            else:
                raise ValueError(
                    f"Unknown membrane model: {combo.currentText()}"
                )

            if not serial_port.write(f"VCA {active_model}\n"):
                return

        # Independently select GUI override or physical potentiometer.
        if self.ui.PatchClamp_toggleButton.isChecked():
            serial_port.write(f"PC1 {binding.value}\n")
        else:
            serial_port.write("PC0\n")


    # Noise
    ##################################################
    def ConfigureNoise(self):
        """Configure GUI noise level; samples are generated by the ESP32."""

        if hasattr(self, "noise_binding"):
            return

        binding = SliderBinding(
            slider=self.ui.Spikeling_Noise_slider,
            editor=self.ui.Spikeling_Noise_readings,
            alignment=Qt.AlignmentFlag.AlignCenter,
            active=self.ui.Noise_toggleButton.isChecked(),
            default_position=0,
            disabled_text="Knob control",
            active_editor_style=("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;" ),
            disabled_editor_style=( "color: rgb(88, 110, 117);" "font-size: 9pt;" "font-weight: 400;"),
            to_display=float,
            to_slider=float,
            format_value=lambda value: f"{value:.0f}",
            interval_ms=40,
        )

        self.noise_binding = binding
        self.NoiseValue = binding.value

        def remember_value(value):
            self.NoiseValue = value

        def apply_value(value):
            # Send the level once; the ESP32 generates subsequent samples.
            if serial_port.is_open:
                serial_port.write(f"NOA {value}\n")

        def disable_control():
            if serial_port.is_open:
                serial_port.write("NO0\n")

        def connection_changed(connected):
            binding.cancel_pending()

        binding.valueChanged.connect(remember_value)
        binding.applyRequested.connect(apply_value)
        binding.disableRequested.connect(disable_control)

        self.ui.Noise_toggleButton.toggled.connect(binding.set_active)

        serial_port.connection_changed.connect(connection_changed)

    def SyncNoiseState(self):
        """Restore the GUI noise level or physical control after connection."""
        binding = getattr(self, "noise_binding", None)

        if binding is None:
            return

        binding.cancel_pending()

        if not serial_port.is_open:
            return

        if binding.active:
            binding.apply_current()
        else:
            serial_port.write("NO0\n")




    # Photoreceptor Parameters
    ##################################################
    def ConfigurePhotoreceptors(self):
        """Configure gain, decay and recovery slider/editor bindings."""

        active_style = (
                "color: rgb"
                + str(tuple(Settings.DarkSolarized[4]))
                + "; font: 700 10pt;"
        )

        disabled_style = (
            "color: rgb(88, 110, 117);"
            "font-size: 9pt;"
            "font-weight: 400;"
        )

        def register(
                *,
                binding_name,
                slider,
                editor,
                toggle,
                value_attribute,
                default_position,
                scale,
                decimals,
                disabled_text,
                apply_command,
                disable_command,
        ):
            """Create one binding and its parameter-specific callbacks."""
            if hasattr(self, binding_name):
                return

            binding = SliderBinding(
                slider=slider,
                editor=editor,
                alignment=Qt.AlignmentFlag.AlignCenter,

                active=toggle.isChecked(),
                default_position=default_position,
                disabled_text=disabled_text,

                active_editor_style=active_style,
                disabled_editor_style=disabled_style,

                to_display=lambda position: position / scale,
                to_slider=lambda value: value * scale,
                format_value=lambda value: f"{value:.{decimals}f}",
                interval_ms=40,
            )

            setattr(self, binding_name, binding)

            # Preserve existing attributes in integer slider units.
            setattr(self, value_attribute, binding.value)

            def remember_value(position):
                setattr(self, value_attribute, position)

            def apply_value(position):
                if serial_port.is_open:
                    argument = f"{position / scale:.{decimals}f}"
                    serial_port.write(
                        f"{apply_command} {argument}\n"
                    )

            def disable_control():
                if serial_port.is_open:
                    serial_port.write(f"{disable_command}\n")

            def connection_changed(connected):
                binding.cancel_pending()

            binding.valueChanged.connect(remember_value)
            binding.applyRequested.connect(apply_value)
            binding.disableRequested.connect(disable_control)

            toggle.toggled.connect(binding.set_active)
            serial_port.connection_changed.connect(connection_changed)

        register(
            binding_name="photo_gain_binding",
            slider=self.ui.Spikeling_PR_PhotoGain_slider,
            editor=self.ui.Spikeling_PR_Photogain_readings,
            toggle=self.ui.PhotoGain_toggleButton,
            value_attribute="PhotoGain",
            default_position=0,
            scale=1,
            decimals=0,
            disabled_text="Knob control",
            apply_command="PG1",
            disable_command="PG0",
        )

        register(
            binding_name="photo_decay_binding",
            slider=self.ui.Spikeling_PR_Decay_slider,
            editor=self.ui.Spikeling_PR_Decay_readings,
            toggle=self.ui.PhotoDecay_toggleButton,
            value_attribute="PhotoDecay",
            default_position=100,
            scale=100000,
            decimals=5,
            disabled_text="Default: 0.001",
            apply_command="PD1",
            disable_command="PD0",
        )

        register(
            binding_name="photo_recovery_binding",
            slider=self.ui.Spikeling_PR_Recovery_slider,
            editor=self.ui.Spikeling_PR_Recovery_readings,
            toggle=self.ui.PhotoRecovery_toggleButton,
            value_attribute="PhotoRecovery",
            default_position=25,
            scale=1000,
            decimals=3,
            disabled_text="Default: 0.025",
            apply_command="PR1",
            disable_command="PR0",
        )

    def SyncPhotoreceptorState(self):
        """Restore photoreceptor overrides or defaults after connection."""
        if not serial_port.is_open:
            return

        controls = (
            ("photo_gain_binding", "PG0"),
            ("photo_decay_binding", "PD0"),
            ("photo_recovery_binding", "PR0"),
        )

        for binding_name, disable_command in controls:
            binding = getattr(self, binding_name, None)

            if binding is None:
                continue

            binding.cancel_pending()

            if binding.active:
                binding.apply_current()
            else:
                serial_port.write(f"{disable_command}\n")

    # Synapse 1 Parameters
    ##################################################
    def ConfigureSynapse1(self):
        """Configure synapse 1 gain and decay slider/editor bindings."""

        if hasattr(self, "synapse1_gain_binding"):
            return

        active_style = ("color: rgb" + str(tuple(Settings.DarkSolarized[7])) + "; font: 700 10pt;" )
        disabled_style = ( "color: rgb(88, 110, 117);" "font-size: 9pt;" "font-weight: 400;" )

        # Gain: displayed and transmitted in integer slider units.
        gain = SliderBinding(
            slider=self.ui.Spikeling_Synapse1_slider,
            editor=self.ui.Spikeling_Synapse1_Gain_readings,
            alignment=Qt.AlignmentFlag.AlignCenter,
            active=self.ui.Synapse1_Gain_toggleButton.isChecked(),
            default_position=0,
            disabled_text="Knob control",
            active_editor_style=active_style,
            disabled_editor_style=disabled_style,
            to_display=float,
            to_slider=float,
            format_value=lambda value: f"{value:.0f}",
            interval_ms=40,
        )

        # Decay: display the factor, but transmit the integer position.
        decay = SliderBinding(
            slider=self.ui.Spikeling_Synapse1_Decay_slider,
            editor=self.ui.Spikeling_Synapse1_Decay_readings,
            alignment=Qt.AlignmentFlag.AlignCenter,
            active=self.ui.Synapse1Decay_toggleButton.isChecked(),
            default_position=995,
            disabled_text="Default: 0.995",
            active_editor_style=active_style,
            disabled_editor_style=disabled_style,
            to_display=lambda position: position / 1000,
            to_slider=lambda value: value * 1000,
            format_value=lambda value: f"{value:.3f}",
            interval_ms=40,
        )

        self.synapse1_gain_binding = gain
        self.synapse1_decay_binding = decay

        # Preserve existing application attributes in slider units.
        self.Synapse1Gain = gain.value
        self.Synapse1Decay = decay.value

        def remember_gain(position):
            self.Synapse1Gain = position

        def remember_decay(position):
            self.Synapse1Decay = position

        def apply_gain(position):
            if serial_port.is_open:
                serial_port.write(f"SG11 {position}\n")

        def apply_decay(position):
            if serial_port.is_open:
                serial_port.write(f"SD11 {position}\n")

        def disable_gain():
            if serial_port.is_open:
                serial_port.write("SG10\n")

        def disable_decay():
            if serial_port.is_open:
                serial_port.write("SD10\n")

        def connection_changed(connected):
            gain.cancel_pending()
            decay.cancel_pending()

        gain.valueChanged.connect(remember_gain)
        gain.applyRequested.connect(apply_gain)
        gain.disableRequested.connect(disable_gain)

        decay.valueChanged.connect(remember_decay)
        decay.applyRequested.connect(apply_decay)
        decay.disableRequested.connect(disable_decay)

        self.ui.Synapse1_Gain_toggleButton.toggled.connect(
            gain.set_active
        )
        self.ui.Synapse1Decay_toggleButton.toggled.connect(
            decay.set_active
        )

        serial_port.connection_changed.connect(connection_changed)

    def SyncSynapse1State(self):
        """Restore synapse 1 overrides or hardware/default control."""
        if not serial_port.is_open:
            return

        controls = (
            ("synapse1_gain_binding", "SG10"),
            ("synapse1_decay_binding", "SD10"),
        )

        for binding_name, disable_command in controls:
            binding = getattr(self, binding_name, None)

            if binding is None:
                continue

            binding.cancel_pending()

            if binding.active:
                binding.apply_current()
            else:
                serial_port.write(f"{disable_command}\n")



    # Synapse 2 Parameters
    ##################################################
    def ConfigureSynapse2(self):
        """Configure synapse 2 gain and decay slider/editor bindings."""

        if hasattr(self, "synapse2_gain_binding"):
            return

        active_style = ("color: rgb" + str(tuple(Settings.DarkSolarized[10])) + "; font: 700 10pt;")

        disabled_style = ("color: rgb(88, 110, 117);" "font-size: 9pt;" "font-weight: 400;")

        gain = SliderBinding(
            slider=self.ui.Spikeling_Synapse2_slider,
            editor=self.ui.Spikeling_Synapse2_Gain_readings,
            alignment=Qt.AlignmentFlag.AlignCenter,
            active=self.ui.Synapse2_Gain_toggleButton.isChecked(),
            default_position=0,
            disabled_text="Knob control",
            active_editor_style=active_style,
            disabled_editor_style=disabled_style,
            to_display=float,
            to_slider=float,
            format_value=lambda value: f"{value:.0f}",
            interval_ms=40,
        )

        decay = SliderBinding(
            slider=self.ui.Spikeling_Synapse2_Decay_slider,
            editor=self.ui.Spikeling_Synapse2_Decay_readings,
            alignment=Qt.AlignmentFlag.AlignCenter,
            active=self.ui.Synapse2Decay_toggleButton.isChecked(),
            default_position=990,
            disabled_text="Default: 0.990",
            active_editor_style=active_style,
            disabled_editor_style=disabled_style,
            to_display=lambda position: position / 1000,
            to_slider=lambda value: value * 1000,
            format_value=lambda value: f"{value:.3f}",
            interval_ms=40,
        )

        self.synapse2_gain_binding = gain
        self.synapse2_decay_binding = decay

        # Preserve existing application attributes in slider units.
        self.Synapse2Gain = gain.value
        self.Synapse2Decay = decay.value

        def remember_gain(position):
            self.Synapse2Gain = position

        def remember_decay(position):
            self.Synapse2Decay = position

        def apply_gain(position):
            if serial_port.is_open:
                serial_port.write(f"SG21 {position}\n")

        def apply_decay(position):
            if serial_port.is_open:
                serial_port.write(f"SD21 {position}\n")

        def disable_gain():
            if serial_port.is_open:
                serial_port.write("SG20\n")

        def disable_decay():
            if serial_port.is_open:
                serial_port.write("SD20\n")

        def connection_changed(connected):
            gain.cancel_pending()
            decay.cancel_pending()

        gain.valueChanged.connect(remember_gain)
        gain.applyRequested.connect(apply_gain)
        gain.disableRequested.connect(disable_gain)

        decay.valueChanged.connect(remember_decay)
        decay.applyRequested.connect(apply_decay)
        decay.disableRequested.connect(disable_decay)

        self.ui.Synapse2_Gain_toggleButton.toggled.connect(
            gain.set_active
        )
        self.ui.Synapse2Decay_toggleButton.toggled.connect(
            decay.set_active
        )

        serial_port.connection_changed.connect(connection_changed)

    def SyncSynapse2State(self):
        """Restore synapse 2 overrides or hardware/default control."""
        if not serial_port.is_open:
            return

        controls = (
            ("synapse2_gain_binding", "SG20"),
            ("synapse2_decay_binding", "SD20"),
        )

        for binding_name, disable_command in controls:
            binding = getattr(self, binding_name, None)

            if binding is None:
                continue

            binding.cancel_pending()

            if binding.active:
                binding.apply_current()
            else:
                serial_port.write(f"{disable_command}\n")




    # Pharmacology Parameters
    ##################################################
    def ConfigureDrugSliders(self):
        """Create one independent slider/editor binding for each drug."""

        if getattr(self, "_drug_setup_complete", False):
            return

        self.drug_controls = []
        self._drug_last_commands = {}

        active_style = ("color: rgb" + str(tuple(Settings.DarkSolarized[8])) + "; font: 700 10pt;")
        disabled_style = ("color: rgb(88, 110, 117);" "font-size: 9pt;" "font-weight: 400;")

        def register(
                *,
                widget_key,
                toggle,
                drug_index,
                scale,
                decimals,
                label,
        ):
            """Create one drug binding with its own widgets and conversions."""
            prefix = f"Spikeling_Pharmacology_{widget_key}"

            slider = getattr(self.ui, f"{prefix}_slider")
            editor = getattr(self.ui, f"{prefix}_readings")

            # More positions allow decimal concentrations to be entered.
            with QSignalBlocker(slider):
                slider.setRange(0, 1000)
                slider.setSingleStep(1)
                slider.setPageStep(100)
                slider.setValue(0)

            binding = SliderBinding(
                slider=slider,
                editor=editor,
                alignment=Qt.AlignmentFlag.AlignCenter,
                active=toggle.isChecked(),
                default_position=0,
                disabled_text=f"{0:.{decimals}f}",
                active_editor_style=active_style,
                disabled_editor_style=disabled_style,
                to_display=lambda position: position / scale,
                to_slider=lambda value: value * scale,
                format_value=lambda value: f"{value:.{decimals}f}",
                interval_ms=40,
            )

            # Keep units visible without including them in editable text.
            getattr(self.ui, f"{prefix}_Label").setText(label)

            self.drug_controls.append({
                "binding": binding,
                "toggle": toggle,
                "index": drug_index,
                "scale": scale,
                "decimals": decimals,
            })

            def apply_value(position):
                Spikeling.SyncDrugState(self)

            def disable_drug():
                Spikeling.SyncDrugState(self)

            binding.applyRequested.connect(apply_value)
            binding.disableRequested.connect(disable_drug)
            toggle.toggled.connect(binding.set_active)

            return binding

        self.ttx_binding = register(
            widget_key="TTX",
            toggle=self.ui.TTX_toggleButton,
            drug_index=0,
            scale=10,
            decimals=1,
            label="TTX (nM)",
        )

        self.tea_binding = register(
            widget_key="TEA",
            toggle=self.ui.TEA_toggleButton,
            drug_index=1,
            scale=100,
            decimals=2,
            label="TEA (mM)",
        )

        self.fourap_binding = register(
            widget_key="4AP",
            toggle=self.ui.FourAP_toggleButton,
            drug_index=3,
            scale=100,
            decimals=2,
            label="4-AP (mM)",
        )

        self.apamin_binding = register(
            widget_key="Apamin",
            toggle=self.ui.Apamin_toggleButton,
            drug_index=2,
            scale=10,
            decimals=1,
            label="Apamin (nM)",
        )

        self.nbqx_binding = register(
            widget_key="NBQX",
            toggle=self.ui.NBQX_toggleButton,
            drug_index=4,
            scale=100,
            decimals=2,
            label="NBQX (µM)",
        )

        self.apv_binding = register(
            widget_key="APV",
            toggle=self.ui.APV_toggleButton,
            drug_index=6,
            scale=10,
            decimals=1,
            label="APV (µM)",
        )

        self.gabazine_binding = register(
            widget_key="Gabazine",
            toggle=self.ui.Gabazine_toggleButton,
            drug_index=5,
            scale=100,
            decimals=2,
            label="Gabazine (µM)",
        )

        self.gvia_binding = register(
            widget_key="GVIA",
            toggle=self.ui.GVIA_toggleButton,
            drug_index=7,
            scale=10,
            decimals=1,
            label="ω-GVIA (nM)",
        )

        def connection_changed(connected):
            # Previously queued commands must not cross connection sessions.
            for control in self.drug_controls:
                control["binding"].cancel_pending()

            # A new connection requires a complete configuration replay.
            self._drug_last_commands = {}

        serial_port.connection_changed.connect(connection_changed)

        clear_button = self.ui.Spikeling_Pharmacology_Clear_pushButton

        clear_button.setCheckable(False)
        clear_button.setCursor(Qt.CursorShape.PointingHandCursor)

        clear_button.setStyleSheet("""
            QPushButton#Spikeling_Pharmacology_Clear_pushButton {color: #B58900; background-color: #073642; border: 1px solid #586E75; border-radius: 4px;}

            QPushButton#Spikeling_Pharmacology_Clear_pushButton:hover {color: #002B36; background-color: #B58900; border-color: #B58900;}

            QPushButton#Spikeling_Pharmacology_Clear_pushButton:pressed {color: #FDF6E3; background-color: #806000; border-color: #806000;}

            QPushButton#Spikeling_Pharmacology_Clear_pushButton:disabled {color: #586E75; background-color: #073642; border-color: #073642;}
        """)

        clear_button.clicked.connect(lambda checked=False: Spikeling.ClearAllDrugs(self))

        self._drug_setup_complete = True


    def SyncDrugState(self, force=False):
        """Synchronise drug concentrations and their required model settings."""

        controls = getattr(self, "drug_controls", None)

        if controls is None:
            return

        # Apply all currently accepted values together.
        for control in controls:
            control["binding"].cancel_pending()

        if not serial_port.is_open:
            return

        cache = self._drug_last_commands

        if force:
            cache.clear()

        def send(command, argument):
            """Avoid repeating unchanged configuration commands."""
            argument = str(argument)

            if cache.get(command) == argument:
                return True

            if not serial_port.write(f"{command} {argument}\n"):
                cache.clear()
                return False

            # This records local write acceptance, not firmware acknowledgement.
            cache[command] = argument
            return True

        drug_enabled = any(
            control["binding"].active
            for control in controls
        )

        # Pharmacology is also needed by probabilistic release controls.
        # Do not switch it off while either release toggle remains enabled.
        release_enabled = any(
            toggle is not None and toggle.isChecked()
            for toggle in (
                getattr(self.ui, "Synapse1Release_toggleButton", None),
                getattr(self.ui, "Synapse2Release_toggleButton", None),
            )
        )

        pharmacology_enabled = drug_enabled or release_enabled

        # On a new session, configure concentrations before enabling effects.
        # When the final user of pharmacology is disabled, turn effects off first.
        if not cache or not pharmacology_enabled:
            if not send("PH E", 0):
                return

        # APV needs the NMDA/conductance synaptic model.
        use_nmda = self.apv_binding.active

        # GVIA needs the presynaptic CaV2.2 pathway.
        use_presynaptic_calcium = self.gvia_binding.active

        settings = (
            ("PH M", int(use_nmda)),
            ("PH N", int(use_nmda)),
            ("PH C", int(use_presynaptic_calcium)),
            ("PH R 1", 3),
            ("PH R 2", 3),
        )

        for command, argument in settings:
            if not send(command, argument):
                return

        for control in controls:
            binding = control["binding"]

            concentration = (
                binding.value / control["scale"]
                if binding.active
                else 0.0
            )

            argument = (
                f"{concentration:.{control['decimals']}f}"
            )

            if not send(
                    f"PH D {control['index']}",
                    argument,
            ):
                return

        if not send("PH E", int(pharmacology_enabled)):
            return

    def ClearAllDrugs(self):
        """Uncheck all drug toggles, reset concentrations and synchronise once."""

        controls = getattr(self, "drug_controls", None)

        if controls is None:
            return

        for control in controls:
            binding = control["binding"]
            toggle = control["toggle"]

            # Keep toggle signals active so PyToggle animates correctly.
            # Block binding signals to avoid individual serial updates.
            with QSignalBlocker(binding):
                toggle.setChecked(False)

                # Also reconcile the binding if it was already unchecked.
                binding.set_active(False)
                binding.set_value(0, send=False)

        Spikeling.SyncDrugState(self)


    def SelectNeuronMode(self):
        global serial_port
        neuron_mode_index = self.ui.Spikeling_NeuronModeComboBox.currentIndex()

        if neuron_mode_index <= 0:
            return

        mode_idx = neuron_mode_index - 1
        if mode_idx < 20 and serial_port.is_open:
            serial_port.write('NEU ' + str(mode_idx) + '\n')

        if mode_idx >= 20 and serial_port.is_open:
            import_idx = mode_idx - 20  # 0-based index into ImportNeuron list
            self.a_Izhi = self.ui.ImportNeuron[import_idx][0]
            self.b_Izhi = self.ui.ImportNeuron[import_idx][1]
            self.c_Izhi = self.ui.ImportNeuron[import_idx][2]
            self.d_Izhi = self.ui.ImportNeuron[import_idx][3]
            serial_port.write('NE ' + str(self.a_Izhi) + ' ' + str(self.b_Izhi) + ' ' + str(self.c_Izhi) + ' ' + str(self.d_Izhi) + '\n')

            self.PGain = self.ui.ImportNeuron[import_idx][4]
            serial_port.write('PG1 ' + str(self.PGain) + '\n')
            self.PDecay = self.ui.ImportNeuron[import_idx][5]
            serial_port.write('PD1 ' + str(self.PDecay) + '\n')
            self.PRecovery = self.ui.ImportNeuron[import_idx][6]
            serial_port.write('PR1 ' + str(self.PRecovery) + '\n')

            self.Syn1Gain = self.ui.ImportNeuron[import_idx][7]
            serial_port.write('SG11 ' + str(self.Syn1Gain) + '\n')
            self.Syn1Decay = self.ui.ImportNeuron[import_idx][8]
            serial_port.write('SD11 ' + str(self.Syn1Decay) + '\n')

            self.Syn2Gain = self.ui.ImportNeuron[import_idx][9]
            serial_port.write('SG21 ' + str(self.Syn2Gain) + '\n')
            self.Syn2Decay = self.ui.ImportNeuron[import_idx][10]
            serial_port.write('SD21 ' + str(self.Syn2Decay) + '\n')




    def BrowseNeuron(self):
        FileName, _= QFileDialog.getOpenFileName(caption='Select Neuron',
                                                 dir="./Neurons",
                                                 filter='csv files (*.csv)')

        Df = pd.read_csv(FileName)
        self.df_Neuron_a = Df["a"]
        self.df_Neuron_b = Df["b"]
        self.df_Neuron_c = Df["c"]
        self.df_Neuron_d = Df["d"]

        self.df_Neuron_PGain = Df["PhotoGain (%)"]
        self.df_Neuron_PDecay = Df["PhotoDecay (1/ms)"]
        self.df_Neuron_PRecovery = Df["PhotoRecovery (1/ms)"]

        self.df_Neuron_Syn1Gain = Df["Syn1 Gain (%)"]
        self.df_Neuron_Syn1Decay = Df["Syn1 Decay (1/ms)"]

        self.df_Neuron_Syn2Gain = Df["Syn2 Gain (%)"]
        self.df_Neuron_Syn2Decay = Df["Syn2 Decay (1/ms)"]

        self.ParametersNeuron = [self.df_Neuron_a[0],
                                 self.df_Neuron_b[0],
                                 self.df_Neuron_c[0],
                                 self.df_Neuron_d[0],
                                 self.df_Neuron_PGain[0],
                                 self.df_Neuron_PDecay[0],
                                 self.df_Neuron_PRecovery[0],
                                 self.df_Neuron_Syn1Gain[0],
                                 self.df_Neuron_Syn1Decay[0],
                                 self.df_Neuron_Syn2Gain[0],
                                 self.df_Neuron_Syn2Decay[0]
                                 ]
        self.ui.ImportNeuron.append(self.ParametersNeuron)


        self.ui.Spikeling_NeuronModeComboBox.addItem('')
        self.neuron_count = self.ui.Spikeling_NeuronModeComboBox.count()
        self.filename = os.path.splitext(os.path.basename(QFileInfo(FileName).fileName()))[0]
        self.ui.Spikeling_NeuronModeComboBox.setItemText(self.neuron_count-1, self.filename)
        self.ui.Spikeling_NeuronModeComboBox.setCurrentIndex(self.neuron_count-1)
