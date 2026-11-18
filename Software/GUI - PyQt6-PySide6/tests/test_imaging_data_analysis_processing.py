"""Camera-frame scientific-processing regression tests (no Qt required)."""
from dataclasses import replace
from types import SimpleNamespace
import json
import unittest

import numpy as np

from spikeling_gui.features.imaging_data_analysis.processing import (
    ProcessingSettings, process_imaging_recording,
)
from spikeling_gui.features.imaging_data_analysis.align import align_imaging_cycles


def recording(*, n=180, dt=20.0, baseline=100.0, pulse=True, gaps=()):
    t = np.arange(n, dtype=float)*dt
    signal = np.full((n,3),baseline,dtype=float)
    if pulse:
        signal[20:26,0] += 20.0
        signal[80:86,1] += 25.0
        signal[100:106,2] += 30.0
    camera_gaps=np.zeros(n,dtype=bool)
    for i in gaps:camera_gaps[i]=True
    source_t=np.arange(0,t[-1]+200,1.0)
    trigger=np.zeros(len(source_t))
    for start in range(100,min(2600,len(source_t)),200):trigger[start]=1
    return SimpleNamespace(
        n_frames=n, frame_time_ms=t, frame_fluorescence_au=signal,
        recorded_dff_percent=((signal-baseline)/baseline*100 if baseline else np.zeros_like(signal)),
        frame_gap_before=camera_gaps, nominal_frame_rate_hz=1000.0/dt,
        metadata={'normalisation':{'offset_a.u.':10.0},'source':'emulator',
                  'sample_interval_ms_fallback':1.0,'imaging_params':{'frame_rate':1000/dt}},
        n_samples=len(source_t), sample_time_ms=source_t, stimulus=np.zeros(len(source_t)),
        trigger=trigger,
    )


class ProcessingTests(unittest.TestCase):
    def test_global_percentile_dff_and_ground_truth_are_distinct(self):
        rec=recording()
        initial=rec.frame_fluorescence_au.copy()
        result=process_imaging_recording(rec,ProcessingSettings())
        self.assertAlmostEqual(result.baseline_au[2,0],100)
        self.assertAlmostEqual(result.dff_percent[21,0],20)
        self.assertEqual(result.metrics[0]['valid_frames'],180)
        np.testing.assert_array_equal(rec.frame_fluorescence_au,initial)
        self.assertFalse(np.shares_memory(result.fluorescence_au,rec.frame_fluorescence_au))

    def test_manual_background_and_empirical_denominator(self):
        rec=recording()
        settings=ProcessingSettings(background_method='manual',background_au=10)
        result=process_imaging_recording(rec,settings)
        self.assertAlmostEqual(result.background_au[0],10)
        self.assertAlmostEqual(result.baseline_au[0,0],90)
        self.assertAlmostEqual(result.dff_percent[21,0],100*20/90)

    def test_recorded_optical_offset_from_metadata(self):
        result=process_imaging_recording(recording(),ProcessingSettings(background_method='metadata'))
        np.testing.assert_allclose(result.background_au,[10,10,10])

    def test_missing_metadata_offset_is_an_error(self):
        rec=recording()
        rec.metadata['normalisation']={}
        with self.assertRaisesRegex(ValueError,'optical offset'):
            process_imaging_recording(rec,ProcessingSettings(background_method='metadata'))

    def test_non_positive_empirical_baseline_is_an_error(self):
        with self.assertRaisesRegex(ValueError,'zero or negative'):
            process_imaging_recording(recording(),ProcessingSettings(background_method='manual',background_au=100))

    def test_fixed_time_window_is_reproducible(self):
        rec=recording()
        r=process_imaging_recording(rec,ProcessingSettings(
            baseline_method='fixed',baseline_start_ms=0,baseline_end_ms=200))
        self.assertAlmostEqual(r.baseline_au[160,0],100)
        self.assertAlmostEqual(r.dff_percent[21,0],20)
        with self.assertRaisesRegex(ValueError,'no camera frames'):
            process_imaging_recording(rec,ProcessingSettings(
                baseline_method='fixed',baseline_start_ms=8000,baseline_end_ms=8500))

    def test_rolling_baseline_never_crosses_frame_gap(self):
        rec=recording(n=60,gaps=(30,),pulse=False)
        rec.frame_fluorescence_au[30:,:]=200
        r=process_imaging_recording(rec,ProcessingSettings(
            baseline_method='rolling',baseline_window_ms=500))
        self.assertAlmostEqual(r.baseline_au[29,0],100)
        self.assertAlmostEqual(r.baseline_au[30,0],200)
        self.assertAlmostEqual(r.dff_percent[30,0],0)

    def test_nan_breaks_one_neuron_without_breaking_others(self):
        rec=recording(pulse=False)
        rec.frame_fluorescence_au[55:60,0]=np.nan
        r=process_imaging_recording(rec,ProcessingSettings(filter_method='mean',filter_window_ms=200))
        self.assertTrue(np.isnan(r.dff_percent[55:60,0]).all())
        self.assertTrue(np.isfinite(r.dff_percent[55:60,1]).all())
        self.assertEqual(r.metrics[0]['valid_frames'],rec.n_frames-5)

    def test_smoothing_does_not_mix_gap_sides(self):
        rec=recording(n=60,pulse=False,gaps=(30,))
        rec.frame_fluorescence_au[30:,:]=150
        r=process_imaging_recording(rec,ProcessingSettings(filter_method='mean',filter_window_ms=600))
        self.assertAlmostEqual(r.fluorescence_au[29,0],100)
        self.assertAlmostEqual(r.fluorescence_au[30,0],150)

    def test_savgol_is_local_to_continuous_segments(self):
        rec=recording(n=80,gaps=(40,),pulse=False)
        rec.frame_fluorescence_au[:40,:]=100+np.linspace(0,3,40)[:,None]
        rec.frame_fluorescence_au[40:,:]=200+np.linspace(0,3,40)[:,None]
        r=process_imaging_recording(rec,ProcessingSettings(filter_method='savgol',filter_window_ms=100))
        self.assertLess(r.fluorescence_au[39,0],110)
        self.assertGreater(r.fluorescence_au[40,0],190)

    def test_bleach_correction_detrends_slow_fluorescence(self):
        rec=recording(n=300,pulse=False)
        trend=100*np.exp(-rec.frame_time_ms/10000.0)
        rec.frame_fluorescence_au[:,:]=trend[:,None]
        raw_ratio=rec.frame_fluorescence_au[-1,0]/rec.frame_fluorescence_au[0,0]
        r=process_imaging_recording(rec,ProcessingSettings(
            bleach_correct=True,bleach_window_ms=2000))
        processed_ratio=r.fluorescence_au[-1,0]/r.fluorescence_au[0,0]
        self.assertGreater(processed_ratio,raw_ratio)
        self.assertTrue(np.isfinite(r.bleach_envelope_au[:,0]).all())
        self.assertTrue(np.isfinite(r.bleach_factor[:,0]).all())

    def test_bleach_without_background_cannot_accept_negative_trend(self):
        rec=recording(pulse=False,baseline=0)
        with self.assertRaisesRegex(ValueError,'non-positive bleaching envelope'):
            process_imaging_recording(rec,ProcessingSettings(bleach_correct=True))

    def test_invalid_parameters_rejected(self):
        rec=recording()
        for update in [dict(baseline_percentile=110),dict(baseline_end_ms=0,baseline_method='fixed'),
                       dict(filter_method='mean',filter_window_ms=0),dict(background_au=float('nan')),
                       dict(bleach_correct=True,bleach_window_ms=-10)]:
            with self.subTest(update=update),self.assertRaises(ValueError):
                process_imaging_recording(rec,replace(ProcessingSettings(),**update))

    def test_quality_metrics_label_gap_count_and_serialise(self):
        rec=recording(gaps=(30,60))
        r=process_imaging_recording(rec,ProcessingSettings())
        self.assertEqual(r.metrics[1]['frame_gap_boundaries'],2)
        self.assertAlmostEqual(r.metrics[1]['effective_rate_hz'],50)
        self.assertTrue(r.metrics[1]['valid_frames']==180)
        json.dumps({'parameters':r.parameters(),'metrics':r.metrics},allow_nan=False)

    def test_alignment_accepts_processed_camera_frames_without_truth(self):
        rec=recording()
        r=process_imaging_recording(rec,ProcessingSettings(background_method='manual',background_au=10))
        aligned=align_imaging_cycles(rec,neuron=0,signal='dff',frame_values=r.dff_percent)
        standard=align_imaging_cycles(rec,neuron=0,signal='dff')
        self.assertEqual(aligned.response.shape,standard.response.shape)
        self.assertTrue(np.isfinite(aligned.response).any())
        self.assertFalse(np.allclose(aligned.response,standard.response,equal_nan=True))
        with self.assertRaisesRegex(ValueError,'three camera-frame'):
            align_imaging_cycles(rec,frame_values=np.ones((rec.n_frames,2)))

    def test_unsupported_rate_is_exportable_as_null(self):
        rec=recording(n=8,pulse=False,gaps=tuple(range(1,8)))
        result=process_imaging_recording(rec,ProcessingSettings())
        self.assertIsNone(result.metrics[0]['effective_rate_hz'])
        self.assertIsNone(result.metrics[0]['snr_proxy'])
        json.dumps({'metrics':result.metrics,'recipe':result.parameters()},allow_nan=False)

    def test_acquisition_frame_time_remains_original(self):
        rec=recording()
        original=rec.frame_time_ms.copy()
        r=process_imaging_recording(rec,ProcessingSettings())
        np.testing.assert_array_equal(r.time_ms,original)
        np.testing.assert_array_equal(rec.frame_time_ms,original)


if __name__ == '__main__':
    unittest.main()
