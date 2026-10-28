"""Recording-path regression tests relevant to STP practicals.

Execute the actual SpikelingGraph.on_data_received and export_data_to_csv
method bodies via ast, without importing Qt or opening a serial port.
"""

import ast
import csv
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

GUI_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GUI_ROOT))


def extract_method(name, extra_globals=None):
    """Compile one unmodified production SpikelingGraph method."""
    path = GUI_ROOT / "Graph_Spikeling.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef)
               and n.name == "SpikelingGraph")
    method = next(n for n in cls.body if isinstance(n, ast.FunctionDef)
                  and n.name == name)
    env = {"Path": Path}
    if extra_globals:
        env.update(extra_globals)
    exec(compile(ast.Module(body=[method], type_ignores=[]), str(path), "exec"), env)
    return env[name]


class FakeBuffer:
    def __init__(self):
        self.samples = []

    def append(self, value):
        self.samples.append(value)


class FakeButton:
    def __init__(self, recording):
        self.recording = recording

    def isChecked(self):
        return self.recording


def fake_graph(recording):
    instance = SimpleNamespace()
    instance.ui = SimpleNamespace(
        Spikeling_DataRecording_Record_pushButton=FakeButton(recording))
    instance.databuffers = [FakeBuffer() for _ in range(8)]
    instance.spikeling_data = [[] for _ in range(9)]
    instance.record_flag = recording
    instance.last_valid_data = None
    instance.step_custom_stimulus_on_packet = lambda: None
    return instance


class TestHardwareRecording(unittest.TestCase):
    def test_samples_are_recorded_once_not_twice(self):
        on_packet = extract_method("on_data_received")
        receiver = fake_graph(recording=True)
        a = [-65, 10, -4, -67, 1.25, -70, -1.5, 0]
        b = [-64, 10, -3, -66, 2.25, -68, -2.5, 1]
        on_packet(receiver, a)
        on_packet(receiver, b)

        for channel in range(8):
            self.assertEqual(receiver.databuffers[channel].samples,
                             [float(a[channel]), float(b[channel])])
            self.assertEqual(receiver.spikeling_data[channel + 1],
                             [float(a[channel]), float(b[channel])])
        self.assertEqual(receiver.spikeling_data[0], [])

    def test_no_recording_keeps_display_buffer_only(self):
        on_packet = extract_method("on_data_received")
        receiver = fake_graph(recording=False)
        sample = [float(index) for index in range(8)]
        on_packet(receiver, sample)
        self.assertEqual([len(x.samples) for x in receiver.databuffers], [1] * 8)
        self.assertEqual([len(x) for x in receiver.spikeling_data], [0] * 9)

    def test_invalid_packets_never_modify_buffers(self):
        on_packet = extract_method("on_data_received")
        receiver = fake_graph(recording=True)
        for invalid in ([], None, [0] * 7, ["not-a-number"] + [0] * 7):
            on_packet(receiver, invalid)
        self.assertEqual([len(x.samples) for x in receiver.databuffers], [0] * 8)
        self.assertEqual([len(x) for x in receiver.spikeling_data], [0] * 9)

    def test_csv_preserves_both_stp_current_channels(self):
        try:
            import numpy as np
            import pandas as pd
        except ImportError as exc:
            self.skipTest(f"numpy/pandas unavailable for CSV integration: {exc}")

        exporter = extract_method(
            "export_data_to_csv",
            {"np": np, "pd": pd, "SAMPLE_INTERVAL": 0.1,
             "Settings": SimpleNamespace(show_popup=lambda *args, **kwargs: None)},
        )
        receiver = fake_graph(recording=True)
        sample_a = [-65.0, 0.0, 3.0, -64.0, 1.25, -66.0, -2.0, 1.0]
        sample_b = [-62.0, 0.0, 4.0, -63.0, 2.5, -65.0, -1.75, 0.0]
        receiver.spikeling_data = [[]] + [[a, b] for a, b in zip(sample_a, sample_b)]
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "plasticity.csv"
            exporter(receiver, path)
            self.assertTrue(path.exists())
            with path.open(newline="", encoding="utf-8") as stream:
                rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 2)
        self.assertAlmostEqual(float(rows[0]["Time (ms)"]), 0.0)
        self.assertAlmostEqual(float(rows[1]["Time (ms)"]), 0.1)
        self.assertAlmostEqual(float(rows[0]["Synapse 1 Input (a.u.)"]), 1.25)
        self.assertAlmostEqual(float(rows[1]["Synapse 1 Input (a.u.)"]), 2.5)
        self.assertAlmostEqual(float(rows[0]["Synapse 2 Input (a.u.)"]), -2.0)
        self.assertAlmostEqual(float(rows[1]["Synapse 2 Input (a.u.)"]), -1.75)


if __name__ == "__main__":
    unittest.main(verbosity=2)
