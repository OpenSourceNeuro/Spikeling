"""Standalone tests for the event-driven STP model (no Qt dependency)."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from stp_model import STPState, OFF, FACILITATION, DEPRESSION, COMBINED


class ShortTermPlasticityTests(unittest.TestCase):
    def test_disabled_mode_preserves_original_gain(self):
        state = STPState()
        self.assertEqual([state.spike_multiplier(t, OFF) for t in (0, 1, 2)], [1.0, 1.0, 1.0])

    def test_first_spike_has_baseline_amplitude(self):
        for mode in (FACILITATION, DEPRESSION, COMBINED):
            with self.subTest(mode=mode):
                self.assertAlmostEqual(STPState().spike_multiplier(0.0, mode), 1.0)

    def test_facilitation_and_long_pause(self):
        state = STPState()
        state.spike_multiplier(0.0, FACILITATION)
        self.assertGreater(state.spike_multiplier(100.0, FACILITATION), 1.0)
        self.assertAlmostEqual(state.spike_multiplier(20000.0, FACILITATION), 1.0, places=5)

    def test_depression_and_long_pause(self):
        state = STPState()
        state.spike_multiplier(0.0, DEPRESSION)
        self.assertLess(state.spike_multiplier(100.0, DEPRESSION), 1.0)
        self.assertAlmostEqual(state.spike_multiplier(30000.0, DEPRESSION), 1.0, places=5)

    def test_combined_changes_with_frequency(self):
        early = STPState()
        early.spike_multiplier(0.0, COMBINED)
        second = early.spike_multiplier(50.0, COMBINED)
        train = [early.spike_multiplier(i * 50.0, COMBINED) for i in range(2, 50)]
        self.assertGreater(second, 1.0)
        self.assertLess(train[-1], second)

    def test_modes_and_reset_are_independent(self):
        first, second = STPState(), STPState()
        first.spike_multiplier(0, DEPRESSION)
        first.spike_multiplier(5, DEPRESSION)
        self.assertAlmostEqual(second.spike_multiplier(5, COMBINED), 1.0)
        first.set_mode(DEPRESSION)
        self.assertAlmostEqual(first.spike_multiplier(6, DEPRESSION), 1.0)

    def test_multiplier_preserves_inhibitory_sign(self):
        state = STPState()
        state.spike_multiplier(0, FACILITATION)
        self.assertLess(-4.0 * state.spike_multiplier(50, FACILITATION), 0.0)

    def test_invalid_mode(self):
        with self.assertRaises(ValueError):
            STPState().set_mode(9)


if __name__ == "__main__":
    unittest.main()
