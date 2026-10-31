"""Integration analyser checks using records from the actual compiled sketch.

ADC/serial/clock IO is simulated. These tests cannot measure ESP32 timing.
"""
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

import test_voltage_clamp as base

sys.path.insert(0, str(base.ROOT / 'Firmware/tools'))
import run_vc_integration_tests as tool


def setUpModule():
    base.compile_sketch(base.SKETCH, base.TMP / 'integration_sketch', True)


def records(kind, *, signal=True, recovery=True, blocked=True):
    setup = ('!PH E 0\n!VCM 1\n!VCA 1\n!VCP 20 500 5 -70\n!VCI 1\n'
             '!PH E 1\n!NO1 0\n!PG1 0\n!VCMD -70\n!VCT 1\n')
    if kind == 'patch':
        setup += '!PC0\n'
    if kind == 'photo':
        setup += '!PG1 10\n'
    if kind in ('switch', 'stress'):
        setup += '!VCMD -20\n'
    if kind == 'switch' and blocked:
        setup += '!PH D 0 9.2\n!PH D 1 .5\n'
    if kind == 'stress':
        setup += '!VCI 0\n'
    setup += 'R1100\n'
    if kind in ('switch', 'stress'):
        counts = [5100 if kind == 'stress' else 1700]
        phases = ['baseline']
        script = setup + f'R{counts[0]}\n'
    else:
        counts = [2000, 2000, 2000]
        phases = ['baseline', 'active', 'recovery']
        script = setup + 'R2000\n'
        if kind == 'noise':
            for i in range(20):
                value = (2 if i % 2 else -2) if signal else 0
                script += f'!NO1 {value}\nR100\n'
            script += '!NO1 0\nR2000\n'
        elif kind == 'photo':
            script += f'A1 5 {2448 if signal else 2048}\nR2000\n'
            script += f'A1 5 {2048 if recovery else 2448}\nR2000\n'
        else:
            script += f'A1 6 {2700 if signal else 2048}\nR2000\nA1 6 2048\nR2000\n'
    data = subprocess.run([str(base.TMP / 'integration_sketch')], input=script.encode(),
                          capture_output=True, check=True).stdout
    rows = [tool.parse_sample(line) for line in data.splitlines() if line.startswith(b'VC2,')][1100:]
    assert len(rows) == sum(counts)
    start = 0
    for count, phase in zip(counts, phases):
        for i in range(start, start + count):
            rows[i].update(wall_s=i * .002, phase=phase)
        start += count
    return rows


class IntegrationAnalysis(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.noise = records('noise')
        cls.photo = records('photo')
        cls.patch = records('patch')
        cls.switch = records('switch')
        cls.stress = records('stress')

    def test_noise_input_and_compensating_clamp_pass(self):
        self.assertTrue(tool.assess(self.noise, '09_active_noise')['all_passed'])

    def test_actual_photodiode_ADC_path_and_recovery_pass(self):
        self.assertTrue(tool.assess(self.photo, '10_active_photodiode')['all_passed'])

    def test_actual_patch_ADC_changes_command_and_returns(self):
        self.assertTrue(tool.assess(self.patch, '11_patch_command')['all_passed'])

    def test_stored_half_block_currents_match_reference(self):
        self.assertTrue(tool.assess(self.switch, '12_mode_switching')['all_passed'])

    def test_long_finite_access_equilibrium_matches_independent_ODE(self):
        result = tool.assess(self.stress, '13_access_stress', 10)
        self.assertTrue(result['all_passed'])
        self.assertTrue(json.loads(json.dumps(result))['all_passed'])

    def test_silent_input_fails_even_when_voltage_equations_pass(self):
        result = tool.assess(records('noise', signal=False), '09_active_noise')
        self.assertTrue(result['numerical']['passed'])
        self.assertFalse(result['response']['passed'])
        self.assertFalse(result['all_passed'])

    def test_photodiode_not_covered_again_fails_recovery(self):
        result = tool.assess(records('photo', recovery=False), '10_active_photodiode')
        self.assertTrue(result['numerical']['passed'])
        self.assertFalse(result['all_passed'])

    def test_unresponsive_patch_fails_despite_correct_equations(self):
        result = tool.assess(records('patch', signal=False), '11_patch_command')
        self.assertTrue(result['numerical']['passed'])
        self.assertFalse(result['all_passed'])

    def test_lost_drug_settings_fail_half_block_reference(self):
        result = tool.assess(records('switch', blocked=False), '12_mode_switching')
        self.assertFalse(result['numerical']['passed'])
        self.assertFalse(result['all_passed'])

    def test_wrong_compensation_sign_fails(self):
        rows = [dict(r, clamp_nA=-r['clamp_nA']) for r in self.noise]
        self.assertFalse(tool.assess(rows, '09_active_noise')['all_passed'])

    def test_deadline_and_slow_loop_fail_independently(self):
        for changes in ({'flags': 64.}, {'previous_loop_us': 2001.}):
            rows = copy.deepcopy(self.noise)
            rows[200].update(changes)
            result = tool.assess(rows, '09_active_noise')
            self.assertTrue(result['numerical']['passed'])
            self.assertFalse(result['all_passed'])

    def test_fast_cadence_fails(self):
        rows = [dict(r, wall_s=r['wall_s'] * .8) for r in self.switch]
        self.assertFalse(tool.assess(rows, '12_mode_switching')['all_passed'])

    def test_missing_or_nonfinite_samples_are_rejected(self):
        with self.assertRaises(ValueError):
            tool.assess(self.noise[:200] + self.noise[201:], '09_active_noise')
        rows = copy.deepcopy(self.noise)
        rows[200]['sodium_nA'] = float('nan')
        with self.assertRaises(ValueError):
            tool.assess(rows, '09_active_noise')

    def test_short_stress_capture_does_not_pass_requested_duration(self):
        result = tool.assess(self.stress, '13_access_stress', 60)
        self.assertTrue(result['numerical']['passed'])
        self.assertFalse(result['all_passed'])


if __name__ == '__main__':
    unittest.main()
