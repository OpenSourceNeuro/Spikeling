"""Scientific regression tests: compare independent one-pixel imaging acquisitions."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
import unittest

import numpy as np

from spikeling_gui.features.imaging_data_analysis.compare import (
    ComparisonSettings, compare_recordings, _empirical_dff, _difference,
)
from spikeling_gui.features.imaging_data_analysis.processing import ProcessingSettings


def recording(name='reference', *, increment=0.0, indicator='GCaMP6f',
              frame_dt=25., nan_slot=None, cam_gap=False):
    sample_time = np.arange(0, 1500, 10., dtype=float)
    frame_t = np.arange(0, 1500, frame_dt, dtype=float)
    trigger = np.zeros(len(sample_time))
    for at in (100, 400, 700, 1000, 1300):
        trigger[int(at/10)] = 1.0
    stimulus = np.zeros(len(sample_time))
    for at in (100, 400, 700, 1000, 1300):
        stimulus[(sample_time >= at) & (sample_time < at + 90)] = 15.0
    signal = np.zeros(len(frame_t))
    for at in (100, 400, 700, 1000, 1300):
        z = frame_t-at
        signal += np.where(z >= 0, np.exp(-np.maximum(z,0)/140.), 0)
    signal = signal + increment
    dff = np.stack((signal,signal*.7,signal*.4),axis=1)
    fluo = 100.0 + dff*1.4
    gaps = np.zeros(len(frame_t),dtype=bool)
    if cam_gap:
        gaps[12] = True
        # A real gap requires a clock jump, not just an artificial marker.
        frame_t[12:] += frame_dt * 5
    if nan_slot is not None:
        dff[nan_slot,0] = np.nan
        fluo[nan_slot,0] = np.nan
    return SimpleNamespace(
        source=Path('/tmp/'+name+'.csv'),
        frames_source=Path('/tmp/'+name+'_frames.csv'),
        metadata_source=Path('/tmp/'+name+'_meta.json'),
        n_frames=len(frame_t),n_samples=len(sample_time),
        nominal_frame_rate_hz=1000./frame_dt,
        frame_time_ms=frame_t, sample_time_ms=sample_time,
        frame_gap_before=gaps, sample_gap_before=np.zeros(len(sample_time),dtype=bool),
        frame_fluorescence_au=fluo, recorded_dff_percent=dff,
        stimulus=stimulus,trigger=trigger,
        warnings=(),source_kind='emulator',
        metadata={'source':'emulator','indicator_name':indicator,
                  'fluorescence_model':'Hill','sample_interval_ms_fallback':10.,
                  'imaging_params':{'frame_rate':1000./frame_dt},
                  'normalisation':{'method':'model baseline','F0_a.u.':[100]*3,
                                   'offset_a.u.':0}},
    )


class TestComparison(unittest.TestCase):
    def setUp(self):
        self.a=recording()
        self.b=recording('comparison',increment=2.)

    def test_cycle_means_match_camera_bins(self):
        result=compare_recordings(self.a,self.b,ComparisonSettings())
        self.assertEqual(result.settings.mode,'cycles')
        self.assertGreater(result.reference.cycles[0],1)
        self.assertEqual(result.reference.y.shape[1],3)
        self.assertEqual(result.comparison.y.shape[1],3)
        self.assertEqual(len(result.reference.x_ms),len(result.reference.y))

    def test_cycle_mean_difference(self):
        result=compare_recordings(self.a,self.b,ComparisonSettings())
        delta=result.difference[:,0]
        self.assertGreater(np.isfinite(delta).sum(),2)
        np.testing.assert_allclose(delta[np.isfinite(delta)],-2.,atol=.06)

    def test_inverted_difference_direction(self):
        result=compare_recordings(self.a,self.b,ComparisonSettings(
            difference_direction='comparison_minus_reference'))
        delta=result.difference[:,0]
        np.testing.assert_allclose(delta[np.isfinite(delta)],2.,atol=.06)

    def test_elapsed_independent_clock(self):
        result=compare_recordings(self.a,self.b,ComparisonSettings(mode='elapsed'))
        self.assertEqual(result.reference.x_ms[0],0.)
        self.assertEqual(result.comparison.x_ms[0],0.)
        self.assertEqual(result.units,'ΔF/F₀ (%)')

    def test_first_anchor_alignment(self):
        result=compare_recordings(self.a,self.b,ComparisonSettings(mode='first_anchor'))
        self.assertAlmostEqual(result.reference.x_ms[0],-100.)
        self.assertAlmostEqual(result.comparison.x_ms[0],-100.)

    def test_first_anchor_missing(self):
        b=recording('none')
        b.trigger[:] = 0
        with self.assertRaisesRegex(ValueError,'no trigger anchor'):
            compare_recordings(self.a,b,ComparisonSettings(mode='first_anchor'))

    def test_stimulus_rise_anchor(self):
        result=compare_recordings(self.a,self.b,ComparisonSettings(
            mode='first_anchor',anchor_source='stimulus',stimulus_threshold=2.))
        self.assertAlmostEqual(result.reference.x_ms[0],-100.)

    def test_manual_cycle_period(self):
        result=compare_recordings(self.a,self.b,ComparisonSettings(period_ms=300.))
        self.assertGreater(result.reference.cycles[0],1)

    def test_irregular_manual_period_fails(self):
        with self.assertRaises(ValueError):
            compare_recordings(self.a,self.b,ComparisonSettings(period_ms=5.))

    def test_invalid_settings(self):
        for setting in (ComparisonSettings(source='abc'),ComparisonSettings(mode='abc'),
                        ComparisonSettings(pre_ms=-2),ComparisonSettings(baseline_percentile=101),
                        ComparisonSettings(stimulus_threshold=float('nan')),
                        ComparisonSettings(period_ms=-2),
                        ComparisonSettings(difference_direction='wrong')):
            with self.subTest(setting=setting),self.assertRaises(ValueError):
                compare_recordings(self.a,self.b,setting)

    def test_same_source_forbidden(self):
        with self.assertRaisesRegex(ValueError,'independently'):
            compare_recordings(self.a,self.a,ComparisonSettings())

    def test_raw_overlay_disables_difference(self):
        result=compare_recordings(self.a,self.b,ComparisonSettings(source='raw',mode='elapsed'))
        self.assertEqual(result.units,'a.u.')
        self.assertEqual(result.difference.shape,(0,3))
        self.assertTrue(any('uncalibrated' in x for x in result.warnings))

    def test_empirical_recipe_same_for_both(self):
        settings=ComparisonSettings(source='empirical',mode='elapsed',baseline_percentile=10.)
        result=compare_recordings(self.a,self.b,settings)
        self.assertAlmostEqual(np.nanpercentile(result.reference.y[:,0],10),0.,places=5)
        self.assertAlmostEqual(np.nanpercentile(result.comparison.y[:,0],10),0.,places=5)
        self.assertEqual(result.reference.processing['percentile'],10.)

    def test_empirical_rejects_nonpositive_baseline(self):
        b=recording('negative')
        b.frame_fluorescence_au[:]=0
        with self.assertRaisesRegex(ValueError,'not positive'):
            compare_recordings(self.a,b,ComparisonSettings(source='empirical'))

    def test_processed_requires_common_settings(self):
        with self.assertRaisesRegex(ValueError,'processing parameters'):
            compare_recordings(self.a,self.b,ComparisonSettings(source='processed'))

    def test_processed_applies_identical_recipe(self):
        result=compare_recordings(self.a,self.b,ComparisonSettings(source='processed',mode='elapsed'),
                                  ProcessingSettings())
        self.assertIsNotNone(result.reference.processing)
        self.assertEqual(result.reference.processing['parameters']['settings'],
                         result.comparison.processing['parameters']['settings'])

    def test_different_indicator_caution(self):
        b=recording('different',indicator='jRGECO1a')
        result=compare_recordings(self.a,b,ComparisonSettings(mode='elapsed'))
        self.assertTrue(any('Indicators differ' in x for x in result.warnings))

    def test_different_frame_rate_caution(self):
        b=recording('slow',frame_dt=50.)
        result=compare_recordings(self.a,b,ComparisonSettings(mode='elapsed'))
        self.assertTrue(any('Frame rates differ' in x for x in result.warnings))
        self.assertAlmostEqual(float(np.median(np.diff(result.difference_x_ms))),50.,places=4)

    def test_camera_gap_is_not_interpolated(self):
        b=recording('gap',cam_gap=True)
        result=compare_recordings(self.a,b,ComparisonSettings(mode='elapsed'))
        x=result.difference_x_ms
        # Gap between the previous camera frame and the shifted next one.
        self.assertFalse(np.isfinite(result.difference[(x>275)&(x<425),0]).any())

    def test_nonfinite_frame_is_not_interpolated(self):
        b=recording('nan',nan_slot=20)
        result=compare_recordings(self.a,b,ComparisonSettings(mode='elapsed'))
        x=result.difference_x_ms
        self.assertFalse(np.isfinite(result.difference[np.argmin(abs(x-500)),0]))

    def test_auc_cannot_bridge_gap(self):
        b=recording('auc',cam_gap=True)
        result=compare_recordings(self.a,b,ComparisonSettings(mode='elapsed'))
        self.assertTrue(np.isfinite(result.comparison.metrics[0]['auc_positive']))
        self.assertLess(result.comparison.metrics[0]['valid_bins'],b.n_frames+1)

    def test_no_reference_event_access(self):
        # No voltage, calcium or event reference attributes on these fixtures.
        result=compare_recordings(self.a,self.b,ComparisonSettings(mode='elapsed'))
        self.assertTrue(np.isfinite(result.reference.y).any())

    def test_metrics_rows(self):
        result=compare_recordings(self.a,self.b,ComparisonSettings())
        rows=result.metrics_rows(0)
        self.assertTrue(any(label=='Peak above baseline' for label,_,_ in rows))
        self.assertTrue(any(label=='Accepted cycles' for label,_,_ in rows))

    def test_recorded_baseline_caution(self):
        result=compare_recordings(self.a,self.b,ComparisonSettings(mode='elapsed'))
        self.assertTrue(any('simulator normalisation' in x for x in result.warnings))

    def test_first_anchor_without_trigger_uses_stimulus(self):
        b=recording('stimonly')
        b.trigger[:]=0
        result=compare_recordings(self.a,b,ComparisonSettings(mode='first_anchor',anchor_source='stimulus'))
        self.assertAlmostEqual(result.comparison.x_ms[0],-100)

    def test_cycle_exclusions_are_reported(self):
        b=recording('noisy',nan_slot=15)
        result=compare_recordings(self.a,b,ComparisonSettings())
        self.assertGreaterEqual(result.comparison.exclusions[0],0)


if __name__=='__main__':
    unittest.main()
