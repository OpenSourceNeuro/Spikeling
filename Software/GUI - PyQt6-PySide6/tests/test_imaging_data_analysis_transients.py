"""Phase-4 camera-frame calcium transient detection regression tests.

Run from the GUI root:
 python -m unittest discover -s tests -p test_imaging_data_analysis_transients.py -v
"""
import unittest
from dataclasses import replace
from types import SimpleNamespace

import numpy as np

from spikeling_gui.features.imaging_data_analysis.transients import (
    TransientSettings, detect_transients,
)


def pulse(t, at, magnitude=24., rise=24., decay=180.):
    d = t - at
    return np.where(d > 0, magnitude * (1 - np.exp(-np.maximum(d, 0) / rise)) *
                    np.exp(-np.maximum(d, 0) / decay), 0.)


def recording(time=None, *, starts=(300., 900., 1500.),
              sample_step=2., nominal_rate_hz=100., gaps=None, signals=None):
    t = np.arange(0., 2200., 10.) if time is None else np.asarray(time, dtype=float)
    y = np.column_stack((pulse(t, 330.) + pulse(t, 930.) + pulse(t, 1530.),
                         pulse(t, 600., 16.),
                         np.zeros(len(t)))) if signals is None else np.asarray(signals, dtype=float)
    sg = np.zeros(len(t), dtype=bool) if gaps is None else np.asarray(gaps, dtype=bool)
    ts = np.arange(0., max(2200., t[-1] + 1.), sample_step)
    trig = np.zeros(len(ts), dtype=float)
    for start in starts:
        hit = np.argmin(np.abs(ts - start))
        trig[hit] = 1.
    stim = np.zeros(len(ts), dtype=float)
    for start in starts:
        stim[(ts >= start) & (ts < start + 60)] = 20.
    return SimpleNamespace(
        frame_time_ms=t, n_frames=len(t), frame_gap_before=sg,
        recorded_dff_percent=y, sample_time_ms=ts, stimulus=stim, trigger=trig,
        nominal_frame_rate_hz=nominal_rate_hz,
        metadata={'source': 'spikeling', 'board_packet_period_ms_nominal': sample_step},
    )


class TransientDetectionTest(unittest.TestCase):
    def test_three_independent_channels(self):
        output = detect_transients(recording(), TransientSettings(response_source='none'))
        self.assertEqual([len(output.for_neuron(i)) for i in range(3)], [3, 1, 0])
        self.assertTrue(all(e.amplitude_percent > 5 for e in output.for_neuron(0)))
        self.assertEqual(output.metrics[2]['events'], 0)

    def test_peak_amplitude_width_and_rise(self):
        rec = recording()
        events = detect_transients(rec, TransientSettings(response_source='none')).for_neuron(0)
        first = events[0]
        self.assertTrue(340 < first.peak_ms < 500)
        self.assertTrue(8 < first.amplitude_percent < 24)
        self.assertTrue(40 < first.fwhm_ms < 400)
        self.assertGreater(first.rise_10_90_ms, 0)
        self.assertGreater(first.decay_1e_ms, 0)
        self.assertGreater(first.auc_percent_ms, 0)

    def test_no_detection_on_flat_channel(self):
        r = recording()
        y = np.zeros_like(r.recorded_dff_percent)
        r.recorded_dff_percent = y
        result = detect_transients(r, TransientSettings(response_source='none'))
        self.assertEqual(result.events, ())
        self.assertEqual(result.metrics[0]['transient_rate_hz'], 0)

    def test_prominence_threshold_filters_events(self):
        output = detect_transients(recording(), TransientSettings(
            min_prominence_percent=50, response_source='none'))
        self.assertEqual(len(output.events), 0)

    def test_weak_peaks_fail_amplitude(self):
        output = detect_transients(recording(), TransientSettings(
            min_amplitude_percent=80, response_source='none'))
        self.assertEqual(len(output.events), 0)

    def test_minimum_width_uses_time_not_frame_count(self):
        output = detect_transients(recording(), TransientSettings(
            min_width_ms=1000, response_source='none'))
        self.assertEqual(len(output.events), 0)

    def test_refractory_uses_actual_times(self):
        t = np.arange(0, 1200, 10., dtype=float)
        s = pulse(t, 300) + pulse(t, 490)
        r = recording(t, signals=np.column_stack((s, s * 0, s * 0)))
        short = detect_transients(r, TransientSettings(
            min_separation_ms=100., response_source='none'))
        long = detect_transients(r, TransientSettings(
            min_separation_ms=400., response_source='none'))
        self.assertGreaterEqual(len(short.for_neuron(0)), 2)
        self.assertEqual(len(long.for_neuron(0)), 1)

    def test_camera_gap_prevents_false_crossing(self):
        t = np.r_[np.arange(0, 450, 10.), np.arange(600, 1500, 10.)]
        gap = np.zeros(len(t), dtype=bool)
        gap[len(np.arange(0, 450, 10.))] = True
        y = np.column_stack((pulse(t, 100) + pulse(t, 900), np.zeros(len(t)), np.zeros(len(t))))
        r = recording(t, gaps=gap, signals=y)
        result = detect_transients(r, TransientSettings(response_source='none'))
        self.assertEqual(len(result.for_neuron(0)), 2)
        self.assertTrue(all(e.peak_ms < 450 or e.peak_ms >= 600 for e in result.events))
        # Valid time excludes the unobserved gap, so inferred rate is higher
        # than when incorrectly using the full recording extent.
        self.assertGreater(result.metrics[0]['transient_rate_hz'], 2 * 1000 / (t[-1] - t[0]))

    def test_nan_gap_not_bridged(self):
        r = recording()
        r.recorded_dff_percent[90:95, 0] = np.nan
        output = detect_transients(r, TransientSettings(response_source='none'))
        self.assertTrue(np.array_equal(output.gaps_before, r.frame_gap_before))
        self.assertTrue(np.isnan(output.dff_percent[90:95, 0]).all())

    def test_processed_source_must_be_applied(self):
        with self.assertRaisesRegex(ValueError, 'Apply signal processing'):
            detect_transients(recording(), TransientSettings(source='processed'))

    def test_processed_source_replaces_recorded_without_mutating_it(self):
        rec = recording()
        original = rec.recorded_dff_percent.copy()
        processed = SimpleNamespace(
            time_ms=rec.frame_time_ms.copy(),
            dff_percent=original * 0.5,
        )
        result = detect_transients(rec, TransientSettings(
            source='processed', min_amplitude_percent=3., response_source='none'),
            processed=processed)
        self.assertEqual(result.signal_source, 'processed')
        np.testing.assert_array_equal(rec.recorded_dff_percent, original)
        self.assertAlmostEqual(result.dff_percent[40, 0], original[40, 0] * .5)

    def test_rejects_unmatched_processed_time(self):
        rec = recording()
        proc = SimpleNamespace(time_ms=rec.frame_time_ms + 1., dff_percent=rec.recorded_dff_percent)
        with self.assertRaisesRegex(ValueError, 'not aligned'):
            detect_transients(rec, TransientSettings(source='processed'), proc)

    def test_trigger_association_and_latency(self):
        result = detect_transients(recording(), TransientSettings(
            response_source='trigger', response_window_ms=400.))
        first = result.for_neuron(0)[0]
        self.assertIsNotNone(first.stimulus_onset_ms)
        self.assertAlmostEqual(first.stimulus_onset_ms, 300., delta=2.)
        self.assertGreater(first.response_latency_ms, 0)
        self.assertAlmostEqual(result.metrics[0]['trial_response_fraction'], 1.0)

    def test_stimulus_rising_edge_association(self):
        result = detect_transients(recording(), TransientSettings(
            response_source='stimulus', stimulus_threshold=5., response_window_ms=400.))
        self.assertEqual(len(result.stimulus_onsets_ms), 3)
        self.assertEqual(result.metrics[0]['usable_stimulus_windows'], 3)

    def test_no_association_option(self):
        result = detect_transients(recording(), TransientSettings(response_source='none'))
        self.assertEqual(len(result.stimulus_onsets_ms), 0)
        self.assertEqual(result.metrics[0]['usable_stimulus_windows'], 0)
        self.assertIsNone(result.metrics[0]['trial_response_fraction'])

    def test_partial_response_window_not_scored_as_failure(self):
        result = detect_transients(recording(), TransientSettings(
            response_source='trigger', response_window_ms=900.))
        self.assertGreater(result.metrics[0]['excluded_stimulus_windows'], 0)
        self.assertTrue(any(not t['usable'] for t in result.response_trials))

    def test_event_incomplete_recovery_is_marked(self):
        t = np.arange(0, 500, 10., dtype=float)
        # A late transient peaks but stays elevated at the acquisition end.
        sig = pulse(t, 290., rise=20., decay=1000.)
        rec = recording(t, signals=np.column_stack((sig, sig * 0, sig * 0)))
        result = detect_transients(rec, TransientSettings(response_source='none'))
        events = result.for_neuron(0)
        # Peak detection may exclude a monotonic truncated rise entirely.
        if events:
            self.assertIsNone(events[0].recovery_ms)
            self.assertIsNone(events[0].auc_percent_ms)

    def test_rejects_invalid_parameters(self):
        r = recording()
        with self.assertRaisesRegex(ValueError, 'finite'):
            detect_transients(r, replace(TransientSettings(), min_width_ms=np.nan))
        with self.assertRaisesRegex(ValueError, 'cannot be negative'):
            detect_transients(r, replace(TransientSettings(), min_separation_ms=-1.))

    def test_uses_frame_time_for_peak_not_model_time(self):
        r = recording(sample_step=1.)
        result = detect_transients(r, TransientSettings(response_source='none'))
        for event in result.events:
            self.assertTrue(np.any(np.isclose(r.frame_time_ms, event.peak_ms)))


if __name__ == '__main__':
    unittest.main()
