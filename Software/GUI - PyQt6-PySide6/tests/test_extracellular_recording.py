"""Regression coverage for the tetrode detector and CSV recording lifecycle."""
from contextlib import ExitStack
import csv
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
from PySide6.QtWidgets import QApplication

from spikeling_gui.features.extracellular import scope
from spikeling_gui.main_window import MainWindow


APP = QApplication.instance() or QApplication([])
HEADINGS = [
    "Time (ms)", "Stim", "Trigger", "Vm1 (mV)", "Vm2 (mV)", "Vm3 (mV)",
    "GT Spike1", "GT Spike2", "GT Spike3", "Ch1 (uV)", "Ch2 (uV)", "Ch3 (uV)",
    "Ch4 (uV)", "Threshold (uV)", "Event",
]


class ExtracellularRecordingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.window = MainWindow()
        cls.graph = cls.window.extracellular_graph

    @classmethod
    def tearDownClass(cls):
        cls.window.close()

    def setUp(self):
        stack = ExitStack()
        self.addCleanup(stack.close)
        folder = stack.enter_context(TemporaryDirectory())
        self.path = Path(folder) / "capture.csv"
        self.sidecar = self.path.with_name("capture_meta.json")
        self.ui = self.window.ui
        self.ui.ExtraCellular_Source_comboBox.setCurrentIndex(1)
        self.ui.Emulator_Connect_pushButton.setChecked(True)
        self.ui.ExtraCellular_ConnectButton.setChecked(True)
        self.window.extracellular_page.ToggleConnection()
        self.graph._rx_timer.stop()
        self.ui.ExtraCellular_DataRecording_RecordFolder_value.setText("capture")
        self.button = self.ui.ExtraCellular_DataRecording_Record_pushButton
        stack.enter_context(patch("spikeling_gui.features.extracellular.page.show_popup"))
        module = "spikeling_gui.features.extracellular.page"
        self.choose_path = stack.enter_context(patch(module + ".prepare_recording", return_value=self.path))
        stack.enter_context(patch.object(self.graph, "_apply_bandpass_block", side_effect=lambda block: block))

    def tearDown(self):
        self.graph.stop_recording(retry=True)
        self.graph.disconnect()
        self.ui.Emulator_Connect_pushButton.setChecked(False)

    def feed(self, times, trace, trigger=None):
        times = np.asarray(times, dtype=float)
        vm = np.zeros((len(times), 3))
        trigger = np.zeros(len(times)) if trigger is None else np.asarray(trigger)
        self.graph._finalize_block(times, np.zeros(len(times)), trigger, vm, vm, trace)

    def one_event(self):
        trace = np.zeros((2, 4))
        trace[1, :2] = -500
        self.feed([0, 0.1], trace)

    def rows(self):
        with self.path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            self.assertEqual(reader.fieldnames, HEADINGS)
            return list(reader)

    def test_alignment_partition_invariance_and_trigger(self):
        trace = np.zeros((23, 4))
        trace[2, :2] = -500
        trace[4, 2] = -500
        trace[9, 3] = -500
        trace[21, 0] = -500
        times = np.arange(len(trace)) * 0.1
        trigger = np.zeros(len(trace))
        trigger[6] = 1
        partitions = ([0, 23], [0, 2, 3, 4, 9, 11, 21, 23], list(range(24)))
        for boundaries in partitions:
            with self.subTest(boundaries=boundaries):
                self.graph.disconnect()
                self.graph.connect()
                self.graph._rx_timer.stop()
                self.button.click()
                for start, end in zip(boundaries, boundaries[1:]):
                    self.feed(times[start:end], trace[start:end], trigger[start:end])
                self.button.click()
                rows = self.rows()
                indices = [index for index, row in enumerate(rows) if row["Event"] == "1"]
                self.assertEqual(indices, [2, 9, 21])
                np.testing.assert_array_equal(
                    [float(rows[i]["Time (ms)"]) for i in indices], list(self.graph._event_marks)
                )
                np.testing.assert_array_equal(
                    [[float(row[f"Ch{k} (uV)"]) for k in range(1, 5)] for row in rows], trace
                )
                np.testing.assert_array_equal([float(row["Time (ms)"]) for row in rows], times)
                self.assertEqual(rows[6]["Trigger"], "1.0")
                self.assertEqual(rows[6]["Event"], "0")
                meta = json.loads(self.sidecar.read_text(encoding="utf-8"))
                self.assertEqual(meta["event_column"], "sample_aligned_merged_detection_v1")
                self.assertEqual(meta["sample_count"], 23)

    def test_empty_denied_and_source_loss_during_confirmation(self):
        self.choose_path.return_value = None
        self.button.click()
        self.assertFalse(self.graph.recording_active)
        self.choose_path.return_value = self.path
        self.button.click()
        self.assertEqual(self.graph.recording_state, "armed")
        self.assertFalse(self.window.tetrode_window.isEnabled())
        self.button.click()
        self.assertEqual(self.graph.recording_state, "empty")
        self.assertFalse(self.path.exists())
        self.assertTrue(self.window.tetrode_window.isEnabled())
        self.choose_path.side_effect = lambda *args: (self.graph.on_emulator_stopped(), self.path)[1]
        with patch.object(self.window.extracellular_page, "_show_source_required") as unavailable:
            self.button.click()
        unavailable.assert_called_once()
        self.assertFalse(self.graph.recording_active)

    def test_stop_disconnect_emulator_source_switch_and_close(self):
        reasons = (
            (lambda: self.button.click(), "Stopped"),
            (lambda: self.ui.ExtraCellular_ConnectButton.click(), "Scope disconnected"),
            (lambda: self.ui.Emulator_Connect_pushButton.click(), "Emulator stopped"),
            (lambda: self.ui.ExtraCellular_Source_comboBox.setCurrentIndex(0), "Source changed"),
            (lambda: self.window.close(), "Window closed"),
        )
        for action, reason in reasons:
            with self.subTest(reason=reason):
                self.graph.disconnect()
                self.ui.ExtraCellular_Source_comboBox.setCurrentIndex(1)
                self.ui.Emulator_Connect_pushButton.setChecked(reason != "Emulator stopped")
                if reason == "Emulator stopped":
                    self.ui.Emulator_Connect_pushButton.click()
                    self.window.Emulator_timer.stop()
                self.ui.ExtraCellular_ConnectButton.click()
                self.graph._rx_timer.stop()
                self.button.click()
                self.one_event()
                action()
                self.assertEqual(self.graph.recording_state, "saved")
                self.assertEqual([row["Event"] for row in self.rows()], ["0", "1"])
                self.assertEqual(json.loads(self.sidecar.read_text())["stop_reason"], reason)
                self.assertTrue(self.graph.stop_recording())

    def test_hardware_queue_boundary_and_connection_loss(self):
        self.ui.ExtraCellular_Source_comboBox.setCurrentIndex(0)
        packet = [-60, 0, 0, -60, 0, -60, 0, 0]
        for _ in range(3):
            self.graph.on_data_received(packet)
        with patch.object(type(scope.serial_manager), "is_open", True):
            self.button.click()
        self.assertEqual(self.graph.recording_state, "armed")
        self.assertFalse(self.graph._rx_queue)
        self.graph.on_data_received(packet)
        self.graph._process_rx_queue()
        self.graph.on_data_received(packet)
        scope.serial_manager.connection_changed.emit(False)
        self.assertEqual(self.graph.recording_state, "saved")
        self.assertEqual([float(row["Time (ms)"]) for row in self.rows()], [0.4])
        self.assertFalse(self.graph._rx_queue)
        self.assertIn("Hardware disconnected", self.ui.ExtraCellular_SelectedFolderLabel.text())

    def test_csv_failure_retains_data_and_blocks_close(self):
        self.button.click()
        self.one_event()
        with patch.object(scope.pd.DataFrame, "to_csv", side_effect=OSError("CSV write failed")):
            self.button.click()
        self.assertEqual(self.graph.recording_state, "error")
        self.assertFalse(self.path.exists())
        self.feed([2], np.zeros((1, 4)))
        with patch("spikeling_gui.main_window.themed_message_box"):
            self.assertFalse(self.window.close())
        self.button.click()
        self.assertEqual([row["Event"] for row in self.rows()], ["0", "1"])

    def test_json_staging_failure_and_publish_rollback(self):
        self.path.write_text("previous CSV", encoding="utf-8")
        self.sidecar.write_text("previous JSON", encoding="utf-8")
        self.button.click()
        self.one_event()
        with patch.object(scope.json, "dump", side_effect=OSError("JSON write failed")):
            self.button.click()
        self.assertEqual(self.graph.recording_state, "error")
        self.assertEqual(self.path.read_text(), "previous CSV")
        self.assertEqual(self.sidecar.read_text(), "previous JSON")
        replace = os.replace

        def fail_sidecar(source, destination):
            if destination == self.sidecar:
                raise OSError("sidecar replacement failed")
            return replace(source, destination)

        with patch.object(scope.os, "replace", side_effect=fail_sidecar):
            self.button.click()
        self.assertEqual(self.graph.recording_state, "error")
        self.assertEqual(self.path.read_text(), "previous CSV")
        self.assertEqual(self.sidecar.read_text(), "previous JSON")
        self.button.click()
        self.assertEqual(self.graph.recording_state, "saved")
        self.assertEqual([row["Event"] for row in self.rows()], ["0", "1"])

    def test_destination_changed_retry_to_new_path(self):
        self.button.click()
        self.one_event()
        self.path.write_text("another capture", encoding="utf-8")
        self.button.click()
        self.assertEqual(self.graph.recording_state, "error")
        alternate = self.path.with_name("retry.csv")
        self.ui.ExtraCellular_DataRecording_RecordFolder_value.setText("retry")
        self.choose_path.return_value = alternate
        self.button.click()
        self.assertEqual(self.graph.recording_state, "saved")
        self.assertTrue(alternate.exists())
        self.assertEqual(self.path.read_text(), "another capture")
