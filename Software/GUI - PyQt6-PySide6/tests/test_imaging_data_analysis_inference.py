"""Synthetic fluorescence-only inference and explicit reference validation tests."""
import unittest
from types import SimpleNamespace

import numpy as np

from spikeling_gui.features.imaging_data_analysis.inference import (
    InferenceSettings, _Kernel, _analysis_indices, _one_to_one_match,
    infer_activity, validate_activity,
)


def fake_recording(*, dt=20.0, duration_ms=4000, model='ar1', positions=(600., 1500., 2800.),
                   amplitudes=(20., 18., 15.), noise=0., gaps=(), reference=True,
                   source_kind='emulator'):
    t = np.arange(int(duration_ms/dt)+1)*dt
    defaults = InferenceSettings(model=model, decay_ms=250., rise_ms=40.,
                                 sparsity_penalty=.35, event_threshold=1.,
                                 max_iterations=220, analysis_interval_ms=20.)
    s = np.zeros(len(t))
    indices = [int(np.argmin(abs(t-pos))) for pos in positions]
    for j, a in zip(indices, amplitudes):
        s[j] = a
    y = _Kernel(t, defaults).apply(s)+3.
    if noise:
        y += np.random.default_rng(8).normal(0, noise, len(t))
    channels = np.repeat(y[:, None], 3, axis=1)
    gap = np.zeros(len(t), bool)
    for i in gaps:
        gap[i] = True
    # Reference event times are on the underlying source/model sample clock.
    sample_time = np.arange(0., float(t[-1])+1e-8, 2.)
    flags = np.zeros((len(sample_time),3), dtype=np.uint8)
    for p in positions:
        j = int(np.argmin(abs(sample_time-p)))
        flags[j,:] = 1
    meta = {'event_provenance':['source events'] if source_kind == 'emulator'
            else ['Vm threshold crossings'], 'source':source_kind}
    return SimpleNamespace(
        n_frames=len(t), n_samples=len(sample_time),
        frame_time_ms=t, frame_gap_before=gap,
        recorded_dff_percent=channels, reference_events=flags,
        sample_time_ms=sample_time, metadata=meta, source_kind=source_kind,
    ), defaults


class TestInference(unittest.TestCase):
    def test_ar1_finds_three_clean_events(self):
        rec, settings = fake_recording()
        result = infer_activity(rec, settings=settings)
        self.assertEqual([round(x.time_ms) for x in result.for_neuron(0)], [600,1500,2800])
        self.assertEqual(len(result.events),9)
        self.assertGreater(result.metrics[0]['reconstruction_r2'], .99)

    def test_ar2_finds_clean_events(self):
        rec, settings = fake_recording(model='ar2')
        result = infer_activity(rec, settings=settings)
        self.assertEqual([round(x.time_ms) for x in result.for_neuron(0)], [600,1500,2800])
        self.assertGreater(result.metrics[0]['reconstruction_r2'], .99)

    def test_high_frequency_optical_frames_uses_real_measured_subsampling(self):
        rec, settings = fake_recording(dt=.1, duration_ms=1000, positions=(300.,), amplitudes=(15.,))
        result = infer_activity(rec, settings=settings)
        self.assertEqual([round(x.time_ms) for x in result.for_neuron(0)], [300])
        self.assertLess(result.metrics[0]['analysis_frames'],rec.n_frames/5)
        self.assertEqual(len(result.time_ms),rec.n_frames)
        self.assertGreater(result.metrics[0]['reconstruction_r2'], .99)

    def test_recording_is_not_mutated(self):
        rec, settings = fake_recording()
        original = rec.recorded_dff_percent.copy()
        infer_activity(rec, settings=settings)
        np.testing.assert_array_equal(rec.recorded_dff_percent, original)

    def test_inference_does_not_touch_reference_events(self):
        rec, settings = fake_recording()
        class Blind:
            def __getattr__(self, key):
                if key == 'reference_events':
                    raise AssertionError('Inference must not read reference events')
                return getattr(rec, key)
        self.assertEqual(len(infer_activity(Blind(), settings=settings).events), 9)

    def test_irregular_kernel_has_true_adjoint(self):
        t = np.asarray([0., 10., 20., 55., 80., 101., 170.])
        rng = np.random.default_rng(10)
        for model in ('ar1','ar2'):
            k = _Kernel(t, InferenceSettings(model=model, rise_ms=20., decay_ms=250.))
            x, r = rng.normal(size=len(t)), rng.normal(size=len(t))
            self.assertAlmostEqual(float(k.apply(x) @ r),float(x @ k.transpose(r)),places=10)

    def test_uniform_kernel_has_true_adjoint(self):
        t = np.arange(80,dtype=float)*5
        rng = np.random.default_rng(11)
        for model in ('ar1','ar2'):
            k = _Kernel(t, InferenceSettings(model=model))
            x, r = rng.normal(size=len(t)), rng.normal(size=len(t))
            self.assertAlmostEqual(float(k.apply(x) @ r),float(x @ k.transpose(r)),places=9)

    def test_irregular_frame_timing_is_preserved(self):
        rec, settings = fake_recording()
        rec.frame_time_ms = rec.frame_time_ms + np.linspace(0, 2.5, rec.n_frames)**2
        result = infer_activity(rec,settings=settings)
        self.assertEqual(result.time_ms[-1],rec.frame_time_ms[-1])
        self.assertTrue(np.isfinite(result.reconstruction_percent[:,0]).any())

    def test_gap_is_respected(self):
        rec, settings = fake_recording(gaps=(120,))
        result = infer_activity(rec,settings=settings)
        self.assertTrue(result.gaps_before[120])
        self.assertTrue(np.isfinite(result.reconstruction_percent).any())
        self.assertGreater(result.metrics[0]['segments_fitted'], 1)

    def test_nan_frames_do_not_produce_inference(self):
        rec, settings = fake_recording()
        rec.recorded_dff_percent[80:94,:] = np.nan
        result = infer_activity(rec,settings=settings)
        self.assertTrue(np.isnan(result.reconstruction_percent[80:94]).all())
        self.assertTrue(np.isnan(result.innovations_percent[80:94]).all())

    def test_processed_source_requires_previous_processing(self):
        rec, settings = fake_recording()
        settings = InferenceSettings(source='processed')
        with self.assertRaisesRegex(ValueError,'Apply processing'):
            infer_activity(rec,settings=settings)
        processed = SimpleNamespace(time_ms=rec.frame_time_ms,
                                    dff_percent=rec.recorded_dff_percent)
        result = infer_activity(rec,processed=processed,settings=settings)
        self.assertEqual(result.settings.source,'processed')

    def test_mismatched_processed_recording_rejected(self):
        rec, _ = fake_recording()
        processed = SimpleNamespace(time_ms=rec.frame_time_ms + 1,
                                    dff_percent=rec.recorded_dff_percent)
        with self.assertRaisesRegex(ValueError,'another acquisition'):
            infer_activity(rec,processed=processed,settings=InferenceSettings(source='processed'))

    def test_invalid_models_and_decay(self):
        rec, _ = fake_recording()
        for kw in ({'model':'ar3'}, {'model':'ar2','rise_ms':400,'decay_ms':300},
                   {'decay_ms':0}, {'analysis_interval_ms':0}, {'baseline_percentile':120},
                   {'sparsity_penalty':-1}, {'max_iterations':4}):
            with self.subTest(kw=kw), self.assertRaises(ValueError):
                infer_activity(rec,settings=InferenceSettings(**kw))

    def test_selects_actual_frames_without_interpolation(self):
        t = np.arange(0., 1000., .1)
        picks = _analysis_indices(t,20)
        self.assertGreater(len(picks),2)
        self.assertEqual(picks[0],0)
        self.assertEqual(picks[-1],len(t)-1)
        self.assertTrue(np.all(np.diff(picks)>0))
        self.assertTrue(np.all(np.isin(t[picks],t)))

    def test_event_separation_in_time(self):
        rec, settings = fake_recording(positions=(600.,700.), amplitudes=(20.,10.))
        settings = InferenceSettings(**{**settings.to_dict(), 'min_separation_ms':150.})
        result = infer_activity(rec,settings=settings)
        self.assertEqual(len(result.for_neuron(0)),1)

    def test_l1_penalty_cannot_produce_negative_innovations(self):
        rec, settings = fake_recording(noise=.3)
        result = infer_activity(rec,settings=settings)
        s = result.innovations_percent[:,0]
        self.assertTrue((s[np.isfinite(s)] >= 0).all())

    def test_validation_matches_reference_without_duplicate(self):
        rec, settings = fake_recording()
        inferred = infer_activity(rec,settings=settings)
        val = validate_activity(rec,inferred,tolerance_ms=30.,bin_ms=500.)
        self.assertEqual(val.metrics[0]['matched'],3)
        self.assertEqual(val.metrics[0]['false_positive'],0)
        self.assertEqual(val.metrics[0]['false_negative'],0)
        self.assertEqual(val.metrics[0]['f1'],1.)

    def test_nearest_match_is_one_to_one(self):
        pairs, ei, rj = _one_to_one_match(np.array([10.,11.]),np.array([10.]),3.)
        self.assertEqual(len(pairs),1)
        self.assertEqual(len(ei),1)
        self.assertEqual(len(rj),1)

    def test_validation_does_not_count_unobservable_reference(self):
        rec, settings = fake_recording(gaps=(130,))
        # Force only an event in the optical gap from 100*20ms to 130*20ms:
        rec.recorded_dff_percent[101:129,:] = np.nan
        extra = int(np.argmin(abs(rec.sample_time_ms-2300.)))
        rec.reference_events[extra,:] = 1
        inferred = infer_activity(rec,settings=settings)
        val = validate_activity(rec,inferred,tolerance_ms=30.)
        self.assertGreaterEqual(val.metrics[0]['unobservable_reference_count'],1)

    def test_hardware_reference_provenance_is_qualified(self):
        rec, settings = fake_recording(source_kind='spikeling')
        val = validate_activity(rec,infer_activity(rec,settings=settings))
        self.assertTrue(any('Vm-threshold' in w for w in val.warnings))

    def test_validation_requires_valid_matching_options(self):
        rec, settings = fake_recording()
        inferred = infer_activity(rec,settings=settings)
        for tol, rate in [(0,1000),(-5,500),(20,0),(20,float('inf'))]:
            with self.subTest(tol=tol,rate=rate),self.assertRaises(ValueError):
                validate_activity(rec,inferred,tolerance_ms=tol,bin_ms=rate)

    def test_validation_rejects_other_recording(self):
        rec, settings = fake_recording()
        inferred = infer_activity(rec,settings=settings)
        rec.frame_time_ms = rec.frame_time_ms+5.
        with self.assertRaisesRegex(ValueError,'does not correspond'):
            validate_activity(rec,inferred)

    def test_missing_reference_is_counted(self):
        rec, settings = fake_recording(positions=(600.,1500.,2800.))
        extra = int(np.argmin(abs(rec.sample_time_ms-3200.)))
        rec.reference_events[extra,:] = 1
        val = validate_activity(rec,infer_activity(rec,settings=settings),tolerance_ms=30.)
        self.assertEqual(val.metrics[0]['false_negative'],1)
        self.assertEqual(sum(x['classification']=='missed reference' for x in val.rows),3)

    def test_no_inferred_event_has_undefined_precision(self):
        rec, settings = fake_recording(amplitudes=(0.,0.,0.))
        result = infer_activity(rec,settings=settings)
        val = validate_activity(rec,result)
        self.assertIsNone(val.metrics[0]['precision'])
        self.assertEqual(val.metrics[0]['recall'],0.)


if __name__ == '__main__':
    unittest.main()
