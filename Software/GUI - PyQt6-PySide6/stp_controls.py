"""
GUI controls for event-driven short-term synaptic plasticity (STP).

This module creates a compact STP button in the neuron parameter page for
both the physical Spikeling and emulator. It avoids modifying generated
UI_Spikeling.py (which is overwritten by Qt Designer regeneration).

Each synapse supports Off, Facilitation, Depression, and Combined.
Selecting any mode resets that synapse's transient STP state. The existing
gain and decay sliders continue to control baseline event amplitude and
current time course independently.
"""

from PySide6.QtCore import QObject, QEvent
from PySide6.QtWidgets import (QDialog, QPushButton, QComboBox, QFormLayout,
                               QGroupBox, QVBoxLayout, QHBoxLayout, QLabel)

from serial_manager import serial_manager


MODE_NAMES = (
    "Off (static synapse)",
    "Short-term facilitation",
    "Short-term depression",
    "Combined facilitation + depression",
)


class STPControls(QObject):
    """Own STP mode selection, reset and device reconnection replay."""

    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.modes = {"hardware": [0, 0], "emulator": [0, 0]}
        self.dialogs = {}
        self.buttons = {}
        window.ui.stp_mode_emulator1 = 0
        window.ui.stp_mode_emulator2 = 0

        # The hardware interface has one neuron-parameter page; emulator
        # presynaptic source configuration is separate from connection STP.
        self._install_button("hardware", window.ui.NeuronParameter_page)
        self._install_button("emulator", window.ui.Emulator_NeuronParameter_page)

    def _install_button(self, kind, page):
        """Insert a visible STP control without editing generated widgets."""
        button = QPushButton("Synaptic plasticity (STP)…", page)
        button.setObjectName(f"{kind}_STP_Button")
        button.setToolTip("Configure short-term facilitation, depression or both for Synapse 1 and 2.")
        button.clicked.connect(lambda: self.show_dialog(kind))
        self.buttons[page] = button

        # Use native layouts where possible; otherwise anchor to the lower
        # right corner and reposition when the containing page is resized.
        layout = page.layout()
        if layout is not None and hasattr(layout, "addWidget"):
            layout.addWidget(button)
        else:
            button.setFixedHeight(28)
            page.installEventFilter(self)
            self._place_button(page)
        button.show()

    def _place_button(self, page):
        """Anchor the button inside fixed-geometry legacy parameter pages."""
        button = self.buttons[page]
        width = min(195, max(120, page.width() - 12))
        button.setFixedWidth(width)
        button.move(max(4, page.width() - width - 6),
                    max(4, page.height() - button.height() - 6))
        button.raise_()

    def eventFilter(self, watched, event):
        """Keep the STP button visible after window size changes."""
        if watched in self.buttons and event.type() == QEvent.Resize:
            self._place_button(watched)
        return super().eventFilter(watched, event)

    def show_dialog(self, kind):
        """Open reusable settings; mode changes take effect immediately."""
        if kind not in self.dialogs:
            self.dialogs[kind] = self._build_dialog(kind)
        dialog = self.dialogs[kind]
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    def _build_dialog(self, kind):
        """Build per-synapse mode selectors and explicit history-reset buttons."""
        dialog = QDialog(self.window)
        dialog.setWindowTitle("Short-term plasticity – " + ("Spikeling" if kind == "hardware" else "Emulator"))
        dialog.setMinimumWidth(365)
        main = QVBoxLayout(dialog)
        hint = QLabel("Each presynaptic spike changes transient synaptic efficacy.\n"
                      "The physical gain and decay remain independently adjustable.")
        hint.setWordWrap(True)
        main.addWidget(hint)

        for index in (0, 1):
            group = QGroupBox(f"Synapse {index + 1}")
            group_layout = QFormLayout(group)
            selector = QComboBox(group)
            selector.addItems(MODE_NAMES)
            selector.setCurrentIndex(self.modes[kind][index])
            selector.currentIndexChanged.connect(
                lambda mode, syn=index, source=kind: self.set_mode(source, syn, mode))
            group_layout.addRow("STP mode", selector)
            reset = QPushButton("Reset transient state", group)
            reset.setToolTip("Replenish resources and return utilisation to baseline without changing the selected mode.")
            reset.clicked.connect(
                lambda checked=False, syn=index, source=kind: self.reset(source, syn))
            group_layout.addRow(reset)
            main.addWidget(group)

        note = QLabel("Presets: facilitation (U 0.15, τfac 500 ms); "
                      "depression (U 0.40, τrec 800 ms); "
                      "combined (U 0.25, τfac 500 ms, τrec 600 ms).\n"
                      "Time constants are in simulated model milliseconds.")
        note.setWordWrap(True)
        main.addWidget(note)
        close_row = QHBoxLayout()
        close_row.addStretch()
        close_button = QPushButton("Close", dialog)
        close_button.clicked.connect(dialog.close)
        close_row.addWidget(close_button)
        main.addLayout(close_row)
        return dialog

    def set_mode(self, kind, synapse, mode):
        """Set the selected mode and reset the corresponding state."""
        mode = int(mode)
        if mode not in range(4):
            return
        self.modes[kind][synapse] = mode
        self.reset(kind, synapse)

    def reset(self, kind, synapse):
        """Reset only one synapse, leaving its baseline signed gain intact."""
        mode = self.modes[kind][synapse]
        if kind == "hardware":
            if serial_manager.is_open:
                serial_manager.write(f"STP{synapse + 1} {mode}\n")
        else:
            setattr(self.window.ui, f"stp_mode_emulator{synapse + 1}", mode)
            states = getattr(self.window, "_emulator_stp", None)
            if states is not None:
                states[synapse].set_mode(mode)

    def replay_hardware(self):
        """Restore both STP modes after a board reconnect (transient state resets)."""
        for synapse, mode in enumerate(self.modes["hardware"], start=1):
            if serial_manager.is_open:
                serial_manager.write(f"STP{synapse} {mode}\n")
