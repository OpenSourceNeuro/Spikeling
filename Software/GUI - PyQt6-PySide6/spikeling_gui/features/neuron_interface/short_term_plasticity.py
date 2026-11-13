"""Configure short-term plasticity independently for each hardware synapse."""

from PySide6.QtCore import QLocale, QObject
from PySide6.QtGui import QDoubleValidator, QIntValidator
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLabel, QLineEdit

from spikeling_gui.appearance.dialogs import themed_message_box
from spikeling_gui.appearance.theme_manager import theme_manager
from spikeling_gui.hardware.connection_supervisor import ConnectionState
from spikeling_gui.hardware.serial_manager import serial_manager
from spikeling_gui.recording_metadata import stp_parameters


# Firmware/Spikeling_V3/STP_functions.h, in STP1/STP2 mode order.
# Each preset gives resting utilisation, facilitation time and recovery time.
PRESETS = (
    (1.00, 0, 0),      # Off
    (0.15, 500, 0),    # Facilitation
    (0.40, 0, 800),    # Depression
    (0.25, 500, 600),  # Combined
)


class SynapseSTPControl(QObject):
    """Track one synapse's settings by mode for the current GUI session."""

    def __init__(self, synapse, selector, advanced_button, reset_button, supervisor):
        super().__init__(selector)
        self.synapse = synapse
        self.selector = selector
        self.supervisor = supervisor
        self.advanced_button = advanced_button
        self.reset_button = reset_button
        self._parameters = list(PRESETS)
        self._last_sent_command = None

        selector.setCurrentIndex(0)
        selector.setToolTip(self.tr(
            "Choose how recent presynaptic spikes change this synapse's response. "
            "The selected preset is applied when the Spikeling board connects."
        ))
        reset_button.setToolTip(self.tr(
            "Clear the effects of recent spikes while keeping the current STP parameters."
        ))
        selector.activated.connect(self._apply_selection)
        selector.currentIndexChanged.connect(self._update_buttons)
        advanced_button.clicked.connect(self._edit_parameters)
        reset_button.clicked.connect(self._reset_state)
        supervisor.state_changed.connect(self._update_buttons)
        supervisor.register_state_restorer(self._restore_selection)
        self._update_buttons()

    def recording_settings(self):
        mode = self.selector.currentIndex()
        return {"mode": mode, "mode_label": self.selector.currentText(),
                **stp_parameters(self._parameters[mode])}

    def _connection_ready(self):
        return serial_manager.is_open and self.supervisor.state == ConnectionState.CONNECTED

    def _update_buttons(self, *_):
        active = self.selector.currentIndex() > 0
        self.advanced_button.setEnabled(active)
        self.reset_button.setEnabled(active and self._connection_ready())

    def _command(self, mode, parameters):
        command = f"STP{self.synapse} {mode}"
        if parameters != PRESETS[mode]:
            utilisation, facilitation_ms, recovery_ms = parameters
            command += f" {utilisation:.3f} {facilitation_ms} {recovery_ms}"
        return command + "\n"

    def _send(self, command):
        # The firmware accepts the command silently. This is local write status.
        if serial_manager.write(command):
            self._last_sent_command = command
            return True
        self._last_sent_command = None
        return False

    def _restore_selection(self):
        # The supervisor calls restorers after receiving data and before
        # announcing CONNECTED. Replay Off too, in case the board stayed powered.
        mode = self.selector.currentIndex()
        if not self._send(self._command(mode, self._parameters[mode])):
            raise RuntimeError(f"Could not restore Synapse {self.synapse} STP mode")

    def _apply_selection(self, mode):
        command = self._command(mode, self._parameters[mode])
        if self._connection_ready() and command != self._last_sent_command and not self._send(command):
            self._show_write_error()

    def _reset_state(self):
        mode = self.selector.currentIndex()
        if mode > 0 and self._connection_ready():
            # Reapply the same parameters to reset the firmware's transient state.
            if not self._send(self._command(mode, self._parameters[mode])):
                self._show_write_error()

    def _show_write_error(self):
        themed_message_box(
            self.selector.window(),
            self.tr("Short-Term Plasticity"),
            self.tr("The STP command could not be sent. Check the connection and try again."),
        ).exec()

    def _edit_parameters(self):
        mode = self.selector.currentIndex()
        if mode == 0:
            return

        def apply_parameters(parameters):
            command = self._command(mode, parameters)
            if self._connection_ready() and command != self._last_sent_command and not self._send(command):
                return False
            self._parameters[mode] = parameters
            return True

        edit_stp_settings(self.selector, self.synapse, mode, self._parameters[mode], apply_parameters)


def edit_stp_settings(selector, synapse, mode, current_parameters, apply_parameters):
    """Edit one STP preset, committing only after the backend accepts it."""
    dialog = QDialog(selector.window())
    dialog.setWindowTitle(selector.tr("Synapse {synapse} STP · {mode}").format(
        synapse=synapse, mode=selector.currentText(),
    ))
    dialog.setStyleSheet(theme_manager.stylesheet())
    form = QFormLayout(dialog)

    utilisation = QLineEdit(dialog)
    validator = QDoubleValidator(0.001, 1.0, 3, utilisation)
    validator.setNotation(QDoubleValidator.Notation.StandardNotation)
    numeric_locale = QLocale()
    numeric_locale.setNumberOptions(QLocale.NumberOption.RejectGroupSeparator)
    validator.setLocale(numeric_locale)
    utilisation.setValidator(validator)
    form.addRow(selector.tr("Resting utilisation"), utilisation)

    time_fields = []
    for label, default in (
        (selector.tr("Facilitation time constant (ms)"), PRESETS[mode][1]),
        (selector.tr("Resource recovery time constant (ms)"), PRESETS[mode][2]),
    ):
        field = QLineEdit(dialog)
        field.setToolTip(selector.tr("Time constant in milliseconds of model time."))
        if default:
            time_validator = QIntValidator(1, 60000, field)
            time_validator.setLocale(numeric_locale)
            field.setValidator(time_validator)
        else:
            field.setText(selector.tr("Inactive"))
            field.setEnabled(False)
        form.addRow(label, field)
        time_fields.append(field)

    status = QLabel(dialog)
    status.setWordWrap(True)
    form.addRow(status)

    def populate(parameters):
        utilisation.setText(numeric_locale.toString(parameters[0], "f", 3))
        for field, milliseconds in zip(time_fields, parameters[1:]):
            if field.isEnabled():
                field.setText(str(milliseconds))
        status.clear()

    def save():
        if not utilisation.hasAcceptableInput() or any(
            field.isEnabled() and not field.hasAcceptableInput() for field in time_fields
        ):
            status.setText(selector.tr("Enter a utilisation from 0.001 to 1 and active time constants from 1 to 60000 ms."))
            return
        parameters = (
            numeric_locale.toDouble(utilisation.text())[0],
            *(numeric_locale.toInt(field.text())[0] if field.isEnabled() else 0 for field in time_fields),
        )
        if not apply_parameters(parameters):
            status.setText(selector.tr("The STP settings could not be sent. Check the connection and try again."))
            return
        dialog.accept()

    standard = QDialogButtonBox.StandardButton
    buttons = QDialogButtonBox(standard.Ok | standard.Cancel | standard.RestoreDefaults, dialog)
    buttons.button(standard.RestoreDefaults).setText(selector.tr("Restore Defaults"))
    buttons.button(standard.RestoreDefaults).clicked.connect(lambda: populate(PRESETS[mode]))
    buttons.accepted.connect(save)
    buttons.rejected.connect(dialog.reject)
    form.addRow(buttons)
    populate(current_parameters)
    dialog.exec()
