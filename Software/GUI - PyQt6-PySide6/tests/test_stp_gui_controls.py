"""Offscreen Qt tests for the real STP dialog, mode controls and serial protocol.

Requires PySide6. No physical board is used: serial_manager is replaced with a
recording fake, while all GUI controls and Qt signals are real.
Run: QT_QPA_PLATFORM=offscreen python -m unittest -v tests.test_stp_gui_controls
"""

import importlib.util
import os
import sys
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QComboBox, QPushButton, QVBoxLayout, QWidget
except ImportError:
    QApplication = None

GUI_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GUI_ROOT))
from stp_model import COMBINED, DEPRESSION, FACILITATION, OFF, STPState


class FakeSerial:
    """Record serial messages without opening a COM port."""

    def __init__(self):
        self.is_open = True
        self.messages = []

    def write(self, message):
        self.messages.append(message)
        return True


@unittest.skipUnless(QApplication, "PySide6 not installed; real GUI test skipped")
class TestSTPGUIControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.serial = FakeSerial()
        stub = types.ModuleType("serial_manager")
        stub.serial_manager = cls.serial

        # Import under a private module name: the rest of the application's
        # serial_manager and PySide6 modules remain untouched.
        spec = importlib.util.spec_from_file_location(
            "stp_controls_under_test", GUI_ROOT / "stp_controls.py")
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {"serial_manager": stub}):
            spec.loader.exec_module(module)
        cls.STPControls = module.STPControls

    def setUp(self):
        self.serial.messages.clear()
        self.serial.is_open = True

        self.window = QWidget()
        hw = QWidget(self.window)
        em = QWidget(self.window)
        hw.setFixedSize(350, 180)         # Legacy fixed-geometry page
        em.setFixedSize(350, 200)
        QVBoxLayout(em)                   # Modern layout-based page

        self.window.ui = SimpleNamespace(
            NeuronParameter_page=hw,
            Emulator_NeuronParameter_page=em,
        )
        self.controls = self.STPControls(self.window)

    def tearDown(self):
        for dialog in self.controls.dialogs.values():
            dialog.close()
        self.window.close()
        self.window.deleteLater()

    def test_both_pages_receive_an_stp_button(self):
        hw = self.window.ui.NeuronParameter_page
        em = self.window.ui.Emulator_NeuronParameter_page
        self.assertIsInstance(self.controls.buttons[hw], QPushButton)
        self.assertIsInstance(self.controls.buttons[em], QPushButton)
        self.assertIn("plasticity", self.controls.buttons[hw].text().lower())
        self.assertIn("plasticity", self.controls.buttons[em].text().lower())
        self.assertEqual(self.controls.modes["hardware"], [0, 0])
        self.assertEqual(self.controls.modes["emulator"], [0, 0])

    def test_serial_protocol_and_independence(self):
        self.controls.set_mode("hardware", 0, DEPRESSION)
        self.controls.set_mode("hardware", 1, COMBINED)
        self.assertEqual(self.serial.messages, ["STP1 2\n", "STP2 3\n"])
        self.assertEqual(self.controls.modes["hardware"], [2, 3])
        self.assertEqual(self.controls.modes["emulator"], [0, 0])
        self.controls.reset("hardware", 0)
        self.assertEqual(self.serial.messages[-1], "STP1 2\n")

    def test_disconnected_selection_is_remembered_and_replayed(self):
        self.serial.is_open = False
        self.controls.set_mode("hardware", 0, FACILITATION)
        self.controls.set_mode("hardware", 1, DEPRESSION)
        self.assertEqual(self.serial.messages, [])
        self.serial.is_open = True
        self.controls.replay_hardware()
        self.assertEqual(self.serial.messages, ["STP1 1\n", "STP2 2\n"])

    def test_emulator_selection_resets_only_target_synapse(self):
        first, second = STPState(), STPState()
        first.spike_multiplier(0, DEPRESSION)
        first.spike_multiplier(20, DEPRESSION)
        second.spike_multiplier(0, COMBINED)
        self.window._emulator_stp = [first, second]
        untouched = (second.mode, second.x, second.u)
        self.controls.set_mode("emulator", 0, FACILITATION)
        self.assertEqual(self.window.ui.stp_mode_emulator1, FACILITATION)
        self.assertEqual(self.window.ui.stp_mode_emulator2, OFF)
        self.assertEqual(first.mode, FACILITATION)
        self.assertFalse(first.has_event)
        self.assertEqual((second.mode, second.x, second.u), untouched)
        self.assertEqual(self.serial.messages, [])

    def test_real_combobox_signal_changes_hardware_and_emulator_modes(self):
        self.controls.show_dialog("hardware")
        dialog = self.controls.dialogs["hardware"]
        selectors = dialog.findChildren(QComboBox)
        self.assertEqual(len(selectors), 2)
        selectors[0].setCurrentIndex(FACILITATION)
        selectors[1].setCurrentIndex(DEPRESSION)
        self.assertEqual(self.serial.messages, ["STP1 1\n", "STP2 2\n"])

        self.controls.show_dialog("emulator")
        other = self.controls.dialogs["emulator"]
        other.findChildren(QComboBox)[0].setCurrentIndex(COMBINED)
        self.assertEqual(self.window.ui.stp_mode_emulator1, COMBINED)
        self.assertEqual(self.controls.modes["hardware"], [1, 2])

    def test_explicit_reset_button_restores_emulator_state(self):
        self.window._emulator_stp = [STPState(), STPState()]
        self.controls.set_mode("emulator", 0, DEPRESSION)
        state = self.window._emulator_stp[0]
        state.spike_multiplier(0, DEPRESSION)
        state.spike_multiplier(20, DEPRESSION)
        self.assertLess(state.x, 1.0)
        self.controls.show_dialog("emulator")
        reset_buttons = [
            w for w in self.controls.dialogs["emulator"].findChildren(QPushButton)
            if w.text() == "Reset transient state"
        ]
        self.assertEqual(len(reset_buttons), 2)
        reset_buttons[0].click()
        self.assertFalse(state.has_event)
        self.assertEqual(state.x, 1.0)
        self.assertEqual(state.mode, DEPRESSION)

    def test_invalid_selector_mode_does_not_change_state(self):
        self.controls.set_mode("hardware", 0, DEPRESSION)
        self.serial.messages.clear()
        self.controls.set_mode("hardware", 0, 8)
        self.assertEqual(self.controls.modes["hardware"][0], DEPRESSION)
        self.assertEqual(self.serial.messages, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
