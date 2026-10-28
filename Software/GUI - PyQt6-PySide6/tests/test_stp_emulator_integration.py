"""Headless integration tests for STP inside the actual emulator GetData function.

Loads GetData from Graph_Emulator.py with ast (no Qt import required), substitutes
only a controlled presynaptic spike source, and exercises the *real* current
routing and accumulator code. This is not a complete Qt/three-neuron GUI test.
"""

import ast
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

GUI_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GUI_ROOT))

from stp_model import COMBINED, DEPRESSION, FACILITATION, OFF, STPState


def load_real_emulator_step(spike1_steps, spike2_steps):
    """Extract the production GetData body, substituting only neuron spiking."""
    source = (GUI_ROOT / "Graph_Emulator.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef)
                 and n.name == "GetData"]
    if len(functions) != 1:
        raise AssertionError("Cannot locate unique production GetData implementation")

    count = [0]
    spikes = (set(spike1_steps), set(spike2_steps))

    def deterministic_neuron(v, u, i, izh, dt):
        frame, neuron = divmod(count[0], 3)
        count[0] += 1
        return v, u, (neuron in (1, 2) and frame in spikes[neuron - 1])

    env = {"izhikevich_step": deterministic_neuron,
           "photodiode_step": lambda *_: (0.0, 1.0)}
    code = compile(ast.Module(body=functions, type_ignores=[]),
                   str(GUI_ROOT / "Graph_Emulator.py"), "exec")
    exec(code, env)
    return env["GetData"]


def state():
    """Minimal state required by production GetData (same initial conditions)."""
    return SimpleNamespace(
        Emulator_timestep_ms=0.1, Emulator_sim_time_ms=0.0,
        Emulator_v=-65.0, Emulator_u=0.0, Emulator_TotalCurrent_Data=0.0,
        Emulator_v1=-65.0, Emulator_u1=0.0, Emulator_TotalCurrent1_Data=0.0,
        Emulator_v2=-65.0, Emulator_u2=0.0, Emulator_TotalCurrent2_Data=0.0,
        Emulator_Syn1Input_Data=0.0, Emulator_Syn2Input_Data=0.0,
        Emulator_Spike1=False, Emulator_Spike2=False,
        Emulator_StimTriggerEnable=False, Emulator_PendingStimTrigger=False,
        Emulator_StimCounter=0, Emulator_StimSteps=1000,
        Emulator_Stim_DutyCycle=500, Emulator_Stim_DutyCycle_Min=10,
        Emulator_Photodiode_Value=0.0, Emulator_Stimulus_Data=0.0,
        Emulator_Trigger=0,
        _emulator_stp=[STPState(), STPState()],
    )


def snapshot(modes=(OFF, OFF), gains=(5.0, -4.0),
             decays=(0.95, 0.96), enabled=(True, True)):
    """Snapshot of controls used in the step function."""
    return SimpleNamespace(
        izh=(0.02, 0.2, -65.0, 8.0),
        izh_syn1=(0.02, 0.2, -65.0, 8.0),
        izh_syn2=(0.02, 0.2, -65.0, 8.0),
        stim_custom_enabled=False, stim_custom_wave=None,
        stim_strength=0.0, stim_frequency=0.0,
        stim_as_light=False, stim_as_current=False,
        photo_gain=0.0, photo_decay=0.0, photo_recovery=0.0,
        patch_clamp=0.0,
        syn_enabled=enabled, syn_as_light=(False, False),
        syn_as_current=(False, False), syn_gain=gains,
        syn_decay=decays, stp_mode=modes,
        syn_patch_clamp=(0.0, 0.0),
        syn_photo_gain=(0.0, 0.0),
        syn_photo_decay=(0.0, 0.0),
        syn_photo_recovery=(0.0, 0.0),
    )


def series(modes=(OFF, OFF), gains=(5.0, -4.0),
           decays=(0.95, 0.96), spikes1=(0, 100),
           spikes2=(0, 100), steps=102):
    """Execute production code with deterministic presynaptic event times."""
    run_step = load_real_emulator_step(spikes1, spikes2)
    runtime = state()
    controls = snapshot(modes=modes, gains=gains, decays=decays)
    outputs = [run_step(runtime, controls, (0.0, 0.0, 0.0))
               for _ in range(steps)]
    return runtime, outputs


class TestSTPEmulatorIntegration(unittest.TestCase):
    def test_off_matches_exact_legacy_increment_and_decay(self):
        decay1, decay2 = 0.91, 0.93
        spikes1, spikes2 = {0, 5, 20}, {0, 20}
        runtime, outputs = series(
            modes=(OFF, OFF), decays=(decay1, decay2),
            spikes1=spikes1, spikes2=spikes2, steps=22,
        )
        i1, i2 = 0.0, 0.0
        for step, row in enumerate(outputs):
            i1 = (i1 + (5.0 if step in spikes1 else 0.0)) * decay1
            i2 = (i2 - (4.0 if step in spikes2 else 0.0)) * decay2
            self.assertAlmostEqual(row[4], i1, delta=1e-10)
            self.assertAlmostEqual(row[6], i2, delta=1e-10)
            self.assertAlmostEqual(row[2], i1 + i2, delta=1e-10)
        self.assertEqual(runtime.Emulator_TotalCurrent_Data, outputs[-1][2])

    def test_facilitation_amplifies_only_event_increment(self):
        decay = 0.95
        runtime, outputs = series(
            modes=(FACILITATION, OFF), decays=(decay, 1.0),
            spikes1=(0, 100), spikes2=(), steps=101,
        )
        previous_current = outputs[99][4]
        second_increment = outputs[100][4] / decay - previous_current
        predictor = STPState()
        predictor.spike_multiplier(0, FACILITATION)
        expected = 5.0 * predictor.spike_multiplier(10.0, FACILITATION)
        self.assertAlmostEqual(second_increment, expected, delta=1e-9)
        self.assertGreater(second_increment, 5.0)
        self.assertEqual(outputs[-1][6], 0.0)
        self.assertEqual(runtime._emulator_stp[1].mode, OFF)

    def test_depression_scales_inhibitory_current_without_sign_flip(self):
        decay = 0.96
        _, outputs = series(
            modes=(OFF, DEPRESSION), decays=(1.0, decay),
            spikes1=(), spikes2=(0, 100), steps=101,
        )
        previous_current = outputs[99][6]
        increment = outputs[100][6] / decay - previous_current
        predictor = STPState()
        predictor.spike_multiplier(0, DEPRESSION)
        expected = -4.0 * predictor.spike_multiplier(10.0, DEPRESSION)
        self.assertAlmostEqual(increment, expected, delta=1e-9)
        self.assertLess(increment, 0.0)
        self.assertGreater(increment, -4.0)

    def test_combined_mode_independent_synapses(self):
        runtime, outputs = series(
            modes=(COMBINED, DEPRESSION), spikes1=(0, 100),
            spikes2=(0, 100), steps=101,
        )
        pred1, pred2 = STPState(), STPState()
        pred1.spike_multiplier(0.0, COMBINED)
        pred2.spike_multiplier(0.0, DEPRESSION)
        event1 = outputs[100][4] / 0.95 - outputs[99][4]
        event2 = outputs[100][6] / 0.96 - outputs[99][6]
        self.assertAlmostEqual(event1,
                               5.0 * pred1.spike_multiplier(10.0, COMBINED),
                               delta=1e-9)
        self.assertAlmostEqual(event2,
                               -4.0 * pred2.spike_multiplier(10.0, DEPRESSION),
                               delta=1e-9)
        self.assertNotEqual(runtime._emulator_stp[0].x, runtime._emulator_stp[1].x)

    def test_disabled_synapse_cannot_advance_plasticity(self):
        run_step = load_real_emulator_step((0, 1), ())
        runtime = state()
        disabled = snapshot(modes=(DEPRESSION, OFF),
                            enabled=(False, True))
        enabled = snapshot(modes=(DEPRESSION, OFF),
                           enabled=(True, True))
        row0 = run_step(runtime, disabled, (0.0, 0.0, 0.0))
        self.assertEqual(row0[4], 0.0)
        self.assertFalse(runtime._emulator_stp[0].has_event)
        row1 = run_step(runtime, enabled, (0.0, 0.0, 0.0))
        self.assertAlmostEqual(row1[4], 5.0 * 0.95)
        self.assertTrue(runtime._emulator_stp[0].has_event)

    def test_zero_gain_changes_no_current_or_total_current(self):
        _, outputs = series(
            modes=(FACILITATION, DEPRESSION), gains=(0.0, 0.0),
            spikes1=(0, 20, 40), spikes2=(0, 20, 40), steps=42,
        )
        for row in outputs:
            self.assertEqual(row[4], 0.0)
            self.assertEqual(row[6], 0.0)
            self.assertEqual(row[2], 0.0)

    def test_current_decay_unchanged_on_no_spike_steps(self):
        decay = 0.97
        _, outputs = series(
            modes=(COMBINED, OFF), decays=(decay, 1.0),
            spikes1=(0,), spikes2=(), steps=101,
        )
        for before, after in zip(outputs, outputs[1:]):
            self.assertAlmostEqual(after[4], before[4] * decay,
                                   delta=1e-10)


if __name__ == "__main__":
    unittest.main(verbosity=2)
