"""Phase-1 integration-independent checks for imaging recording compatibility.

Run from GUI root:
    python -m unittest discover -s tests -p test_imaging_data_analysis_phase1.py -v
"""

from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import numpy as np
import pandas as pd

from spikeling_gui.features.imaging_data_analysis.recording import (
    FRAME_COLUMNS, SAMPLE_COLUMNS, ImagingRecordingError, load_imaging_recording,
)


class TestImagingRecordingLoader(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / "imaging_run.csv"
        self.frames_path = self.root / "imaging_run_frames.csv"
        self.meta_path = self.root / "imaging_run_meta.json"
        self.samples = pd.DataFrame({
            "Time (ms)": [0.0, 0.1, 0.2, 0.3, 0.4, 0.5],
            "Stim": [0, 0, 1, 1, 0, 0],
            "Trigger": [0, 0, 1, 0, 0, 0],
            "Vm1 (mV)": [-70, -70, 30, -70, -70, -70],
            "Vm2 (mV)": [-70] * 6,
            "Vm3 (mV)": [-70] * 6,
            "Ca1 (uM)": [.1, .1, .2, .2, .12, .1],
            "Ca2 (uM)": [.1] * 6,
            "Ca3 (uM)": [.1] * 6,
            "F1 (a.u.)": [np.nan, np.nan, 3., 3., 5., 5.],
            "F2 (a.u.)": [np.nan, np.nan, 2., 2., 2., 2.],
            "F3 (a.u.)": [np.nan, np.nan, 2., 2., 2., 2.],
            "FrameIdx": [-1, -1, 0, 0, 1, 1],
            "FrameTime (ms)": [np.nan, np.nan, .2, .2, .4, .4],
            "Calcium event 1": [0, 0, 1, 0, 0, 0],
            "Calcium event 2": [0] * 6,
            "Calcium event 3": [0] * 6,
        })[list(SAMPLE_COLUMNS)]
        self.frames = pd.DataFrame({
            "FrameIdx": [0, 1],
            "FrameTime (ms)": [.2, .4],
            "NearestSampleIdx": [2, 4],
            "F1 (a.u.)": [3., 5.],
            "F2 (a.u.)": [2., 2.],
            "F3 (a.u.)": [2., 2.],
            "SourceSampleTime (ms)": [.2, .4],
            "DF/F0 1 (%)": [5., 10.],
            "DF/F0 2 (%)": [0., 0.],
            "DF/F0 3 (%)": [0., 0.],
        })[list(FRAME_COLUMNS)]
        self.metadata = {
            "schema_version": 2,
            "source": "emulator",
            "imaging_params": {"frame_rate": 5000.0},
            "sample_interval_ms_fallback": 0.1,
            "n_samples": 6,
            "n_frames": 2,
            "indicator_name": "Generic",
            "fluorescence_model": "hill",
            "event_provenance": ["source events"],
            "timing_interruptions": [],
            "columns": {"samples_csv": list(SAMPLE_COLUMNS), "frames_csv": list(FRAME_COLUMNS)},
        }
        self.publish()

    def publish(self, *, hashes=False):
        with np.errstate(invalid="ignore"):
            self.samples.to_csv(self.path, index=False)
        self.frames.to_csv(self.frames_path, index=False)
        if hashes:
            self.metadata["file_sha256"] = {
                "samples_csv": sha256(self.path.read_bytes()).hexdigest(),
                "frames_csv": sha256(self.frames_path.read_bytes()).hexdigest(),
            }
        self.meta_path.write_text(json.dumps(self.metadata), encoding="utf-8")

    def test_valid_legacy_three_file_recording(self):
        loaded = load_imaging_recording(self.path)
        self.assertEqual(loaded.n_samples, 6)
        self.assertEqual(loaded.n_frames, 2)
        self.assertEqual(loaded.frame_fluorescence_au.shape, (2, 3))
        self.assertEqual(loaded.reference_events.shape, (6, 3))
        self.assertEqual(loaded.reference_events[:, 0].sum(), 1)
        self.assertIn("file hashes unavailable", "; ".join(loaded.warnings))
        self.assertEqual(loaded.summary()["one_pixel_neurons"], 3)

    def test_entry_from_sidecar(self):
        loaded = load_imaging_recording(self.frames_path)
        self.assertEqual(loaded.source, self.path)
        self.assertEqual(load_imaging_recording(self.meta_path).n_frames, 2)

    def test_hashes_and_file_tampering(self):
        self.publish(hashes=True)
        loaded = load_imaging_recording(self.path)
        self.assertEqual(loaded.warnings, ())
        self.frames.loc[0, "F1 (a.u.)"] += 1
        self.frames.to_csv(self.frames_path, index=False)
        with self.assertRaisesRegex(ImagingRecordingError, "Checksum mismatch"):
            load_imaging_recording(self.path)

    def test_missing_sidecar(self):
        self.frames_path.unlink()
        with self.assertRaisesRegex(ImagingRecordingError, "Missing imaging acquisition file"):
            load_imaging_recording(self.path)

    def test_bad_column(self):
        self.frames.drop(columns=["F3 (a.u.)"], inplace=True)
        self.frames.to_csv(self.frames_path, index=False)
        with self.assertRaisesRegex(ImagingRecordingError, "missing required columns"):
            load_imaging_recording(self.path)

    def test_bad_frame_cross_reference(self):
        self.frames.loc[0, "NearestSampleIdx"] = 3
        self.frames.to_csv(self.frames_path, index=False)
        with self.assertRaisesRegex(ImagingRecordingError, "timestamps do not match"):
            load_imaging_recording(self.path)

    def test_invalid_time(self):
        self.samples.loc[3, "Time (ms)"] = .19
        self.samples.to_csv(self.path, index=False)
        with self.assertRaisesRegex(ImagingRecordingError, "strictly increasing"):
            load_imaging_recording(self.path)

    def test_metadata_count_mismatch(self):
        self.metadata["n_frames"] = 4
        self.meta_path.write_text(json.dumps(self.metadata), encoding="utf-8")
        with self.assertRaisesRegex(ImagingRecordingError, "counts do not match"):
            load_imaging_recording(self.path)

    def test_timing_discontinuity(self):
        self.samples.loc[4:, "Time (ms)"] += .3
        self.frames.loc[1, "FrameTime (ms)"] += .3
        self.samples.loc[4:, "FrameTime (ms)"] += .3
        self.frames.loc[1, "SourceSampleTime (ms)"] += .3
        self.publish()
        loaded = load_imaging_recording(self.path)
        self.assertEqual(loaded.sample_gap_before.sum(), 1)
        self.assertEqual(loaded.frame_gap_before.sum(), 1)

    def test_incorrect_event_flag(self):
        self.samples.loc[2, "Calcium event 1"] = 4
        self.samples.to_csv(self.path, index=False)
        with self.assertRaisesRegex(ImagingRecordingError, "0/1 flags"):
            load_imaging_recording(self.path)


if __name__ == "__main__":
    unittest.main()
