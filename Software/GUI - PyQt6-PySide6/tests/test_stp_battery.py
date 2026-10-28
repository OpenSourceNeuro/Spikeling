"""Behavioural and numerical regression battery for educational STP.

Run without Qt or a Spikeling board:
    python -m unittest -v tests.test_stp_battery

Tests use independent closed-form paired-pulse predictions rather than only
testing the implementation against its own outputs. All times are model ms.
"""

import math
import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from stp_model import (
    COMBINED, DEPRESSION, FACILITATION, OFF, PRESETS, STPState,
)


def paired_pulse_oracle(mode, interval_ms):
    """Independent closed-form prediction for two spikes after full recovery.

    We assume a baseline-normalised Tsodyks-Markram event: the first spike
    depletes U resources, and, if facilitated, raises utilisation by U(1-U).
    Between spikes, both independent processes recover exponentially.
    """
    if mode == OFF:
        return 1.0
    U, tau_fac, tau_rec = PRESETS[mode]
    facilitation = (1.0 + (1.0 - U) * math.exp(-interval_ms / tau_fac)
                    if tau_fac else 1.0)
    resources = (1.0 - U * math.exp(-interval_ms / tau_rec)
                 if tau_rec else 1.0)
    return facilitation * resources


def event_series(mode, intervals_ms):
    """Return event amplitudes for the given successive inter-spike intervals."""
    state = STPState()
    t = 0.0
    result = [state.spike_multiplier(t, mode)]
    for interval in intervals_ms:
        t += interval
        result.append(state.spike_multiplier(t, mode))
    return result


class TestSTPClosedForm(unittest.TestCase):
    """Verify the mechanistic and didactic behaviour quantitatively."""

    def test_presets_are_finite_and_bounded(self):
        self.assertEqual(set(PRESETS), {OFF, FACILITATION, DEPRESSION, COMBINED})
        for mode, (U, tau_fac, tau_rec) in PRESETS.items():
            with self.subTest(mode=mode):
                self.assertTrue(0.0 < U <= 1.0)
                self.assertGreaterEqual(tau_fac, 0.0)
                self.assertGreaterEqual(tau_rec, 0.0)
                for parameter in (U, tau_fac, tau_rec):
                    self.assertTrue(math.isfinite(parameter))

    def test_off_is_exactly_one_for_irregular_train(self):
        rng = random.Random(20261028)
        intervals = [rng.uniform(0.0, 1500.0) for _ in range(500)]
        self.assertTrue(all(value == 1.0 for value in event_series(OFF, intervals)))

    def test_fully_recovered_first_pulse_for_all_modes(self):
        for mode in PRESETS:
            with self.subTest(mode=mode):
                state = STPState()
                self.assertEqual(state.spike_multiplier(137.0, mode), 1.0)
                self.assertEqual(state.mode, mode)
                self.assertTrue(state.has_event)

    def test_closed_form_paired_pulses_across_intervals(self):
        for mode in PRESETS:
            for interval in (0.0, 0.1, 1.0, 10.0, 25.0, 50.0,
                             100.0, 250.0, 500.0, 1000.0, 5000.0, 30000.0):
                with self.subTest(mode=mode, interval_ms=interval):
                    state = STPState()
                    state.spike_multiplier(0.0, mode)
                    actual = state.spike_multiplier(interval, mode)
                    expected = paired_pulse_oracle(mode, interval)
                    self.assertAlmostEqual(actual, expected, delta=1e-12)

    def test_facilitation_pair_ratio_decreases_with_interval(self):
        intervals = (0, 10, 25, 50, 100, 250, 500, 1000, 5000)
        pprs = [event_series(FACILITATION, [dt])[1] for dt in intervals]
        self.assertTrue(all(a > b for a, b in zip(pprs, pprs[1:])))
        self.assertTrue(all(1.0 <= value < 2.0 for value in pprs))

    def test_depression_pair_ratio_recovers_with_interval(self):
        intervals = (0, 10, 25, 50, 100, 250, 500, 1000, 5000)
        pprs = [event_series(DEPRESSION, [dt])[1] for dt in intervals]
        self.assertTrue(all(a < b for a, b in zip(pprs, pprs[1:])))
        self.assertTrue(all(0.0 < value <= 1.0 for value in pprs))

    def test_combined_initial_facilitation_then_train_depletion(self):
        train = event_series(COMBINED, [50.0] * 59)
        self.assertGreater(train[1], train[0])
        self.assertLess(train[-1], train[1])
        self.assertTrue(all(math.isfinite(value) and value > 0 for value in train))

    def test_higher_rate_generally_increases_depression(self):
        fast = event_series(DEPRESSION, [20.0] * 39)
        slow = event_series(DEPRESSION, [500.0] * 39)
        self.assertLess(fast[-1], slow[-1])

    def test_activity_recovery_after_a_silent_period(self):
        for mode in (FACILITATION, DEPRESSION, COMBINED):
            with self.subTest(mode=mode):
                response = event_series(mode, [50.0] * 19 + [30000.0])[-1]
                self.assertAlmostEqual(response, 1.0, delta=1e-9)

    def test_finite_state_bounds_after_many_random_spikes(self):
        rng = random.Random(314159)
        for mode in PRESETS:
            state = STPState()
            t = 0.0
            for _ in range(2000):
                t += rng.uniform(0, 1000)
                value = state.spike_multiplier(t, mode)
                U = PRESETS[mode][0]
                self.assertTrue(math.isfinite(value))
                self.assertGreaterEqual(value, 0.0)
                self.assertLessEqual(value, 1 / U + 1e-12)
                self.assertGreaterEqual(state.x, -1e-12)
                self.assertLessEqual(state.x, 1 + 1e-12)
                self.assertGreaterEqual(state.u, U - 1e-12)
                self.assertLessEqual(state.u, 1 + 1e-12)

    def test_recovery_depends_on_simulated_interval_not_gui_polling(self):
        # The event-driven model is not called every integration step.
        direct = STPState()
        direct.spike_multiplier(0.0, COMBINED)
        after_100ms = direct.spike_multiplier(100.0, COMBINED)
        # An extra UI update without a spike must not cause extra recovery.
        indirect = STPState()
        indirect.spike_multiplier(0.0, COMBINED)
        self.assertEqual(indirect.spike_multiplier(100.0, COMBINED), after_100ms)

    def test_identical_model_interval_at_different_step_sizes(self):
        # 500 steps @ 0.1 model ms == 1000 steps @ 0.05 model ms.
        # Only model time is passed to STP; hardware loop wall-time is irrelevant.
        for mode in PRESETS:
            with self.subTest(mode=mode):
                one = event_series(mode, [50.0, 50.0, 300.0])
                two = event_series(mode, [500 * 0.1, 1000 * 0.05, 3000 * 0.1])
                self.assertEqual(one, two)

    def test_reset_returns_to_full_resources_without_changing_mode(self):
        for mode in (FACILITATION, DEPRESSION, COMBINED):
            state = STPState()
            state.spike_multiplier(0, mode)
            state.spike_multiplier(50, mode)
            state.set_mode(mode)
            self.assertEqual(state.mode, mode)
            self.assertEqual(state.x, 1.0)
            self.assertFalse(state.has_event)
            self.assertEqual(state.spike_multiplier(51, mode), 1.0)

    def test_switching_mode_clears_history(self):
        state = STPState()
        event_series(DEPRESSION, [10] * 4)
        state.spike_multiplier(0, DEPRESSION)
        state.spike_multiplier(10, DEPRESSION)
        self.assertEqual(state.spike_multiplier(11, FACILITATION), 1.0)
        self.assertEqual(state.spike_multiplier(12, OFF), 1.0)
        self.assertEqual(state.spike_multiplier(13, COMBINED), 1.0)

    def test_invalid_mode_leaves_existing_configuration_unchanged(self):
        state = STPState()
        state.spike_multiplier(0, DEPRESSION)
        original = (state.mode, state.u, state.x, state.last_event_ms, state.has_event)
        for invalid in (-1, 4, 99):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    state.set_mode(invalid)
                self.assertEqual(
                    (state.mode, state.u, state.x, state.last_event_ms, state.has_event),
                    original,
                )

    def test_synapses_are_independent(self):
        syn1 = STPState()
        syn2 = STPState()
        syn1.spike_multiplier(0.0, DEPRESSION)
        syn1.spike_multiplier(10.0, DEPRESSION)
        self.assertEqual(syn2.spike_multiplier(10.0, FACILITATION), 1.0)
        syn1.set_mode(OFF)
        self.assertGreater(syn2.spike_multiplier(20.0, FACILITATION), 1.0)

    def test_excitation_inhibition_and_zero_gain(self):
        for mode in PRESETS:
            multipliers = event_series(mode, [50.0] * 5)
            self.assertTrue(all(m >= 0.0 for m in multipliers))
            self.assertTrue(all(3.0 * m >= 0.0 for m in multipliers))
            self.assertTrue(all(-3.0 * m <= 0.0 for m in multipliers))
            self.assertTrue(all(0.0 * m == 0.0 for m in multipliers))

    def test_synaptic_current_decay_not_replaced_by_plasticity(self):
        # Independent discrete current recursion (gain increment, then decay).
        gain, decay = -4.0, 0.995
        intervals = [50.0, 100.0, 500.0]
        for mode in PRESETS:
            state = STPState()
            current = 0.0
            event_time = 0.0
            for interval in [0.0] + intervals:
                event_time += interval
                multiplier = state.spike_multiplier(event_time, mode)
                before = current
                current = (before + gain * multiplier) * decay
                recovered_increment = current / decay - before
                self.assertAlmostEqual(recovered_increment, gain * multiplier, delta=1e-12)

    def test_deterministic_for_identical_input_and_mode(self):
        rng = random.Random(9482)
        intervals = [rng.uniform(0, 1000) for _ in range(200)]
        self.assertEqual(event_series(COMBINED, intervals),
                         event_series(COMBINED, intervals))


if __name__ == "__main__":
    unittest.main(verbosity=2)
