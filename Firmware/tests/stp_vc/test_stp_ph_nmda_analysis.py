# SPDX-License-Identifier: GPL-3.0-or-later
"""Offline, adversarial validation of STP×NMDA/APV hardware waveform analyser."""
import math
from pathlib import Path
import sys
import unittest

TOOLS=Path(__file__).resolve().parents[2]/"tools"
sys.path.insert(0,str(TOOLS))
import run_stp_ph_nmda_hardware as n


def independent_waveform(events,case,length=1600):
    """Compute separately the experimental reference from Euler-independent exponentials.

    This is deliberately distinct from the test runner's predict_waveform:
    receptor impulse train is generated from the presynaptic ticks, then
    convoluted with the analytic exponential impulse kernels.
    """
    amplitude=[]
    U=.15;u=.15; last=None
    for tick in events:
        if last is not None:
            u=U+(u-U)*math.exp(-(tick-last)*.1/500)
        amplitude.append(u/U)
        u+=U*(1-u)
        last=tick
    nbqx=1/(1+case.nbqx_uM/.30)
    apv=1/(1+case.apv_uM/3.7)
    norm,mg=n.nmdamath()
    result=[]
    for tick in range(length):
        fast=slow=0.
        for t,w in zip(events,amplitude):
            gap=tick-t
            if gap<0:continue
            x=gap+1
            ga=6/70*w
            fast+=ga*(.990**x)*70*.01*nbqx
            if case.nmda:
                biexponential=math.exp(-x*.1/100)-math.exp(-x*.1/4)
                slow+=ga*2*norm*biexponential*mg*70*.01*apv
        result.append(fast+slow)
    return result


def rows_for(case,events=(55,165,270,375,480,590,720,840,970,1100,1240,1370)):
    signal=independent_waveform(events,case)
    output=[]
    for tick,value in enumerate(signal):
        output.append({
            "tick":tick,"time_ms":tick*.1,"host_seconds":tick*.002,
            "flags":0,"command_mV":-70.,"voltage_mV":-70.,
            "input_nA":0.,"receptor_nA":round(-value,6),
            "clamp_nA":round(-value,6),
            "capacitive_nA":0.,"leak_nA":0.,
            "sodium_nA":0.,"potassium_nA":0.,
            "solve_us":210.,"previous_loop_us":1450.,
        })
    return output


class NMDAAnalysisTests(unittest.TestCase):
    def test_all_four_independent_biexponential_waveforms_pass(self):
        for case in n.CASES_NMDA.values():
            with self.subTest(case=case.name):
                result,model=n.inspect(rows_for(case),case)
                self.assertEqual(result["status"],"PASS",result["reason"])
                self.assertEqual(result["events"],12)
                self.assertLess(result["max_waveform_error_nA"],2e-6)
                self.assertEqual(result["missing_or_duplicate_tick_pairs"],0)

    def test_apv_halves_slow_component_not_fast_component(self):
        control=n.CASES_NMDA["02_ampa_plus_nmda"]
        apv=n.CASES_NMDA["03_nmda_apv_half"]
        ticks=range(150)
        a=n.predict_waveform(ticks,[20,60,110],control)
        b=n.predict_waveform(ticks,[20,60,110],apv)
        for x,y in zip(a,b):
            self.assertAlmostEqual(y["model_fast_nA"],x["model_fast_nA"])
            self.assertAlmostEqual(y["model_nmda_nA"],.5*x["model_nmda_nA"])

    def test_nbqx_halves_fast_but_spares_slow_nmda(self):
        control=n.CASES_NMDA["02_ampa_plus_nmda"]
        nbqx=n.CASES_NMDA["04_fast_nbqx_half"]
        a=n.predict_waveform(range(150),[20,60,110],control)
        b=n.predict_waveform(range(150),[20,60,110],nbqx)
        for x,y in zip(a,b):
            self.assertAlmostEqual(y["model_fast_nA"],.5*x["model_fast_nA"])
            self.assertAlmostEqual(y["model_nmda_nA"],x["model_nmda_nA"])

    def test_missing_nmda_kinetic_response_fails(self):
        control=n.CASES_NMDA["01_fast_ampa_only"]
        nmda=n.CASES_NMDA["02_ampa_plus_nmda"]
        actual=rows_for(control)
        result,_=n.inspect(actual,nmda)
        self.assertEqual(result["status"],"FAIL")

    def test_apv_command_missing_drug_effect_fails(self):
        control=n.CASES_NMDA["02_ampa_plus_nmda"]
        half=n.CASES_NMDA["03_nmda_apv_half"]
        result,_=n.inspect(rows_for(control),half)
        self.assertEqual(result["status"],"FAIL")

    def test_bad_flags_and_missing_samples_cannot_pass(self):
        case=n.CASES_NMDA["02_ampa_plus_nmda"]
        for flag in (2,4,32,64,128):
            rows=rows_for(case)
            rows[20]["flags"]=flag
            result,_=n.inspect(rows,case)
            self.assertEqual(result["status"],"FAIL")
        rows=rows_for(case)
        del rows[400]
        result,_=n.inspect(rows,case)
        self.assertEqual(result["status"],"INCONCLUSIVE")

    def test_current_balance_overshoot_fails(self):
        case=n.CASES_NMDA["03_nmda_apv_half"]
        rows=rows_for(case)
        rows[600]["clamp_nA"]+=.02
        result,_=n.inspect(rows,case)
        self.assertEqual(result["status"],"FAIL")

    def test_commands_reset_amplitude_state_and_select_independent_blockers(self):
        for case in n.CASES_NMDA.values():
            commands=n.commands_for_nmda(case)
            self.assertIn("PH X",commands)
            self.assertIn("STP1 1",commands)
            self.assertIn("PH N "+str(int(case.nmda)),commands)
            self.assertIn("PH D 6 "+f"{case.apv_uM:g}",commands)
            self.assertIn("PH D 4 "+f"{case.nbqx_uM:g}",commands)
            self.assertEqual(commands[-1],"VCT 1")


if __name__=="__main__":
    unittest.main()
