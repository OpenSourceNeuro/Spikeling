# SPDX-License-Identifier: GPL-3.0-or-later
"""Synaptic analyser checks against the real sketch with simulated digital inputs.

The native clock/ADC/DAC are test doubles. No physical ESP32 timing is measured.
"""
import copy
from functools import lru_cache
import json
import subprocess
import sys
import unittest

import test_voltage_clamp as base
sys.path.insert(0, str(base.ROOT/'Firmware/tools'))
import run_vc_synapse_tests as tool
import vc_synapse_reference as ref


def setUpModule():
    base.compile_sketch(base.SKETCH, base.TMP/'synaptic_sketch', True)


@lru_cache(maxsize=None)
def recording(case, channel=1, signal=True, wrong_drug=False, nmda_absent=False, fast=False):
    config = ref.configuration(case)
    gpio = 38 if channel == 1 else 39
    script = ('!VCM 1\n!VCA 1\n!VCI 1\n!VCP 20 500 5 -70\n!NO1 0\n!PG1 0\n'
              '!SG11 0\n!SG21 0\n!SD11 990\n!SD21 990\n!PH M 1\n!PH G -80\n'
              f'!PH R {channel} {config["receptor_index"]}\n'
              f'!PH N {int(config["nmda"] and not nmda_absent)}\n'
              f'!PH C {int(config["presynaptic"])}\n!PH F {channel} .35\n'
              f'!SG{channel}1 {config["gain_legacy"]*4:g}\n!PH E 1\n!PH X\n'
              f'!VCMD {ref.phases(case)[0].voltage:g}\n!VCT 1\nR1100\n')
    groups = []

    def pulses(count):
        if not signal:
            return f'R{count}\n'
        step = 25 if fast else 250
        text = ''
        for start in range(0, count, step):
            remain = min(step, count-start)
            text += f'D{gpio} 1\nR1\nD{gpio} 0\n'
            if remain > 1:
                text += f'R{remain-1}\n'
        return text

    for phase in ref.phases(case):
        script += f'!VCMD {phase.voltage:g}\n'
        for drug in (4, 5, 6, 7):
            dose = phase.dose if drug == phase.drug and not wrong_drug else 0
            script += f'!PH D {drug} {dose:g}\n'
        count = 2000 if phase.name in ('baseline', 'recovery') else (5000 if case == '14_synaptic_input' else 6000)
        groups.append((phase.name, count))
        script += pulses(count) if phase.name not in ('baseline', 'recovery') else f'R{count}\n'
    data = subprocess.run([str(base.TMP/'synaptic_sketch')], input=script.encode(),
                          capture_output=True, check=True).stdout
    rows = [tool.parse_sample(line) for line in data.splitlines() if line.startswith(b'VC2,')][1100:]
    assert len(rows) == sum(count for name, count in groups)
    index = 0
    for name, count in groups:
        for i in range(index, index+count):
            rows[i].update(wall_s=i*.002, phase=name)
        index += count
    return rows


class SynapticValidation(unittest.TestCase):
    def check(self, case, **kwargs):
        result = tool.assess(recording(case, **kwargs), case)
        json.dumps(result)  # Regression against non-serialisable NumPy scalars.
        return result

    def test_synapse_one_receives_ampa_spikes(self):
        self.assertTrue(self.check('14_synaptic_input')['all_passed'])

    def test_synapse_two_receives_ampa_spikes(self):
        self.assertTrue(self.check('14_synaptic_input', channel=2)['all_passed'])

    def test_nbqx_halves_event_amplitude_and_washout_restores(self):
        result = self.check('15_nbqx')
        self.assertTrue(result['all_passed'])
        self.assertAlmostEqual(result['synaptic_response']['drug_effect']['event_amplitude_ratio'], .5, places=4)

    def test_gabazine_halves_outward_gaba_events(self):
        self.assertTrue(self.check('16_gabazine')['all_passed'])

    def test_ampa_reversal_estimated_from_signed_currents(self):
        result = self.check('17_ampa_reversal')
        self.assertTrue(result['all_passed'])
        self.assertAlmostEqual(result['synaptic_response']['reversal']['estimated_mV'], 0., places=3)

    def test_gaba_reversal_estimated_from_signed_currents(self):
        result = self.check('18_gaba_reversal')
        self.assertTrue(result['all_passed'])
        self.assertAlmostEqual(result['synaptic_response']['reversal']['estimated_mV'], -80., places=3)

    def test_apv_changes_slow_nmda_component_without_changing_fast_ampa(self):
        result = self.check('19_nmda_apv')
        self.assertTrue(result['all_passed'])
        phases = result['synaptic_response']['phases']
        self.assertAlmostEqual(phases['drug']['fitted_fast_event_nA']/phases['control']['fitted_fast_event_nA'], 1., places=3)
        self.assertAlmostEqual(result['synaptic_response']['drug_effect']['event_amplitude_ratio'], .5, places=3)

    def test_gvia_event_scaling_is_not_applied_twice(self):
        result = self.check('20_gvia')
        self.assertTrue(result['all_passed'])
        self.assertAlmostEqual(result['synaptic_response']['drug_effect']['event_amplitude_ratio'], .825**3, places=4)

    def test_no_incoming_spikes_fails_with_correct_membrane(self):
        result = self.check('14_synaptic_input', signal=False)
        self.assertTrue(result['membrane']['passed'])
        self.assertFalse(result['synaptic_response']['passed'])
        self.assertFalse(result['all_passed'])

    def test_absent_nbqx_effect_fails(self):
        result = self.check('15_nbqx', wrong_drug=True)
        self.assertTrue(result['membrane']['passed'])
        self.assertFalse(result['all_passed'])

    def test_absent_nmda_component_fails(self):
        result = self.check('19_nmda_apv', nmda_absent=True)
        self.assertTrue(result['membrane']['passed'])
        self.assertFalse(result['all_passed'])

    def test_excessive_source_rate_is_rejected(self):
        result = self.check('14_synaptic_input', fast=True)
        self.assertTrue(result['membrane']['passed'])
        self.assertFalse(result['all_passed'])

    def test_double_counted_receptor_current_fails(self):
        rows = [dict(r, clamp_nA=r['clamp_nA']+r['receptor_nA']) for r in recording('14_synaptic_input')]
        result = tool.assess(rows, '14_synaptic_input')
        self.assertTrue(result['synaptic_response']['passed'])
        self.assertFalse(result['membrane']['passed'])
        self.assertFalse(result['all_passed'])

    def test_deadline_and_slow_loop_fail(self):
        for changes in ({'flags': 64.}, {'previous_loop_us': 2001.}):
            rows = copy.deepcopy(recording('14_synaptic_input'))
            rows[300].update(changes)
            result = tool.assess(rows, '14_synaptic_input')
            self.assertTrue(result['synaptic_response']['passed'])
            self.assertFalse(result['all_passed'])

    def test_missing_samples_are_rejected(self):
        rows = recording('14_synaptic_input')
        with self.assertRaises(ValueError):
            tool.assess(rows[:200]+rows[201:], '14_synaptic_input')

    def test_wrong_clock_fails(self):
        rows = [dict(r, wall_s=r['wall_s']*.8) for r in recording('14_synaptic_input')]
        self.assertFalse(tool.assess(rows, '14_synaptic_input')['all_passed'])


if __name__ == '__main__':
    unittest.main()
