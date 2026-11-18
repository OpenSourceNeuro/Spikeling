"""Scientific behaviour tests for live-acquired imaging loop alignment."""
import unittest
from types import SimpleNamespace

import numpy as np

from spikeling_gui.features.imaging_data_analysis.align import (
    align_imaging_cycles, find_anchors, infer_period_ms, mean_sem,
)


def sample_recording(*, source='emulator', sample_dt=1.0, period=200.0,
                     onsets=(100, 300, 500, 700, 900), duration=1400.0,
                     frame_dt=20.0, frame_offset=3.0):
    sample_t = np.arange(0.0, duration, sample_dt)
    frame_t = np.arange(frame_offset, duration, frame_dt)
    trigger = np.zeros_like(sample_t)
    stim = np.zeros_like(sample_t)
    for onset in onsets:
        i = int(round(onset / sample_dt))
        if i < len(sample_t):
            trigger[i] = 1.0
        stim[(sample_t >= onset) & (sample_t < onset + 50)] = 70.0
    # Camera traces may have a different acquisition offset and rate.
    fluorescence = np.ones((len(frame_t), 3)) * 10.0
    for onset in onsets:
        mask = (frame_t >= onset) & (frame_t < onset + 160)
        fluorescence[mask, :] += (1.2 * np.exp(-(frame_t[mask] - onset) / 65))[:, None]
    dff = (fluorescence - 10) * 10
    meta = {
        'source': source,
        'sample_interval_ms_fallback': 0.1 if source == 'spikeling' else sample_dt,
        'board_packet_period_ms_nominal': 2.0 if source == 'spikeling' else None,
        'indicator_name': 'Generic',
    }
    return SimpleNamespace(
        n_frames=len(frame_t), sample_time_ms=sample_t, frame_time_ms=frame_t,
        trigger=trigger, stimulus=stim, frame_fluorescence_au=fluorescence,
        recorded_dff_percent=dff, frame_gap_before=np.zeros(len(frame_t), dtype=bool),
        metadata=meta, nominal_frame_rate_hz=1000 / frame_dt,
    )


class ImagingAlignTests(unittest.TestCase):
    def test_camera_acquisition_is_not_model_resampling(self):
        rec=sample_recording()
        aligned=align_imaging_cycles(rec,pre_ms=40)
        self.assertEqual(aligned.n_cycles, 5)
        self.assertEqual(aligned.response.shape, (5, 12))
        self.assertAlmostEqual(aligned.frame_step_ms,20)
        self.assertTrue(np.isclose(aligned.time_ms[0],-40))
        self.assertAlmostEqual(aligned.duration_ms,200)
        avg,_,_,n=mean_sem(aligned.response)
        self.assertTrue(np.isfinite(avg).any())
        self.assertGreater(n.max(), 3)
        self.assertLess(n.max(), 6)

    def test_observed_trigger_has_no_false_edges(self):
        rec=sample_recording()
        np.testing.assert_allclose(find_anchors(rec),[100,300,500,700,900])
        np.testing.assert_allclose(find_anchors(rec,'stimulus',stimulus_threshold=30),
                                   [100,300,500,700,900])
        self.assertEqual(len(find_anchors(rec,'stimulus',stimulus_threshold=100)),0)

    def test_onset_at_start_is_permitted_only_for_one_sample_trigger(self):
        rec=sample_recording(onsets=(0,200,400,600,800),duration=1200)
        np.testing.assert_allclose(find_anchors(rec,'trigger'),[0,200,400,600,800])
        self.assertEqual(find_anchors(rec,'stimulus')[0],200)

    def test_board_regular_2ms_packets_not_classed_as_0point1ms_gaps(self):
        rec=sample_recording(source='spikeling',sample_dt=2.0)
        result=align_imaging_cycles(rec)
        self.assertEqual(result.n_cycles,5)

    def test_last_partial_loop_and_pretrigger_are_excluded(self):
        rec=sample_recording(duration=950)
        result=align_imaging_cycles(rec,pre_ms=120)
        self.assertEqual(result.n_cycles,3)
        self.assertEqual(result.excluded_incomplete,2)

    def test_acquisition_gaps_are_never_interpolated_through(self):
        rec=sample_recording()
        # At camera frame around 560 ms, a new imaging segment begins.
        idx=np.searchsorted(rec.frame_time_ms,560)
        rec.frame_gap_before[idx]=True
        result=align_imaging_cycles(rec)
        self.assertTrue(result.excluded_frame_gaps >= 1 or np.isnan(result.response).any())
        self.assertTrue(np.isfinite(result.response).any())

    def test_irregular_period_is_rejected_without_corrupting_other_cycles(self):
        rec=sample_recording(onsets=(100,300,500,650,900,1100),duration=1400)
        result=align_imaging_cycles(rec)
        self.assertEqual(result.duration_ms,200)
        self.assertGreaterEqual(result.excluded_irregular,2)
        self.assertEqual(result.n_cycles,4)

    def test_manual_period_with_only_two_markers(self):
        rec=sample_recording(onsets=(100,300),duration=700)
        with self.assertRaisesRegex(ValueError,'three observed'):
            align_imaging_cycles(rec)
        result=align_imaging_cycles(rec,period_ms=200)
        self.assertEqual(result.n_cycles,2)

    def test_competing_cycle_periods_require_manual_choice(self):
        with self.assertRaisesRegex(ValueError,'competing'):
            infer_period_ms(np.array([0.0,100,300]),.1)

    def test_too_few_optical_samples_cannot_support_average(self):
        rec=sample_recording(period=40,frame_dt=20,onsets=(100,140,180),duration=300)
        with self.assertRaisesRegex(ValueError,'too short'):
            align_imaging_cycles(rec,period_ms=40)

    def test_missing_bins_preserve_per_bin_count(self):
        data=np.array([[1.,2.,np.nan,4.],[3.,2.,4.,np.nan]])
        mean,sd,sem,n=mean_sem(data)
        np.testing.assert_array_equal(n,[2,2,1,1])
        np.testing.assert_allclose(mean,[2,2,4,4])
        self.assertTrue(np.isnan(sem[2]))
        self.assertAlmostEqual(sd[0],np.sqrt(2))

    def test_settings_validation(self):
        rec=sample_recording()
        for kwargs in ({'pre_ms':-2},{'period_ms':0},{'neuron':3},
                       {'signal':'calcium'},{'source':'unknown'},
                       {'stimulus_threshold':float('nan')}):
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):
                align_imaging_cycles(rec,**kwargs)

    def test_dff_and_raw_fluorescence_are_separate_modes(self):
        rec=sample_recording()
        raw=align_imaging_cycles(rec,signal='fluorescence')
        dff=align_imaging_cycles(rec,signal='dff')
        self.assertGreater(float(np.nanmean(raw.response)),float(np.nanmean(dff.response)) * .5)
        self.assertFalse(np.allclose(raw.response,dff.response,equal_nan=True))


if __name__=='__main__':
    unittest.main()
