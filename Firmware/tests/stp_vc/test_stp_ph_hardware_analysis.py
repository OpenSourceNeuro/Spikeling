# SPDX-License-Identifier: GPL-3.0-or-later
"""Offline regression for COM5 STP+PH hardware analyser.

Synthetic VC2 rows are generated from an independent event recurrence with
no serial hardware. False-positive PASS conditions must be rejected.
"""
import importlib.util
from pathlib import Path
import unittest

TOOLS=Path(__file__).resolve().parents[2]/"tools"
spec=importlib.util.spec_from_file_location("run_stp_ph_hardware",TOOLS/"run_stp_ph_hardware.py")
import sys
sys.path.insert(0,str(TOOLS))
m=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=m
spec.loader.exec_module(m)


def synthetic(case, event_ticks=None):
    ticks=event_ticks if event_ticks is not None else [20+55*i for i in range(9)]
    expected=m.reference(case.mode,ticks)
    impulse=dict(zip(ticks,expected))
    tail=0.
    rows=[]
    for tick in range(550):
        tail=(tail+case.gain*.01*case.event_factor*impulse.get(tick,0.))*.99
        inward=round(tail,8)
        receptor=-inward if case.conductance else 0.
        injected=0. if case.conductance else inward
        rows.append({"tick":tick,"time_ms":tick*.1,"host_seconds":tick*.002,
                     "flags":0,"command_mV":-70.,"voltage_mV":-70.,
                     "input_nA":injected,"receptor_nA":receptor,
                     "clamp_nA":-inward,"capacitive_nA":0.,"leak_nA":0.,
                     "sodium_nA":0.,"potassium_nA":0.,
                     "solve_us":150.,"previous_loop_us":1300.})
    return rows


class PharmacologyHardwareAnalysis(unittest.TestCase):
    def test_all_seven_current_and_receptor_cases_pass_independent_synthetic_model(self):
        for case in m.CASES.values():
            with self.subTest(case=case.name):
                result=m.assessment(synthetic(case),case)
                self.assertEqual(result["status"],"PASS",result["reason"])
                self.assertEqual(result["event_count"],9)
                self.assertLess(result["max_multiplier_error"],.0001)
                self.assertLess(result["maximum_current_balance_error_nA"],.00001)

    def test_wrong_block_or_gvia_factor_is_not_accepted(self):
        control=m.CASES["01_current_facilitation"]
        for name in ("02_current_nbqx","03_current_gvia"):
            wrong=m.CASES[name]
            result=m.assessment(synthetic(control),wrong)
            self.assertEqual(result["status"],"FAIL")
            self.assertIn("disagree",result["reason"])

    def test_wrong_receptor_gain_polarity_fails(self):
        gaba=m.CASES["06_gaba_conductance"]
        ampa=m.CASES["04_ampa_conductance"]
        result=m.assessment(synthetic(ampa),gaba)
        self.assertNotEqual(result["status"],"PASS")

    def test_missing_and_duplicated_frames_are_inconclusive(self):
        case=m.CASES["01_current_facilitation"]
        rows=synthetic(case)
        del rows[100]
        self.assertEqual(m.assessment(rows,case)["status"],"INCONCLUSIVE")
        rows=synthetic(case)
        rows.insert(100,dict(rows[100]))
        self.assertEqual(m.assessment(rows,case)["status"],"INCONCLUSIVE")

    def test_rejected_serial_command_is_not_pass(self):
        case=m.CASES["04_ampa_conductance"]
        rows=synthetic(case)
        rows[150]["flags"]=2
        self.assertEqual(m.assessment(rows,case)["status"],"FAIL")

    def test_solver_and_transport_faults_are_not_pass(self):
        case=m.CASES["02_current_nbqx"]
        for fault in (4,64,128):
            rows=synthetic(case)
            rows[150]["flags"]=fault
            self.assertEqual(m.assessment(rows,case)["status"],"FAIL")

    def test_bad_current_conservation_fails(self):
        case=m.CASES["06_gaba_conductance"]
        rows=synthetic(case)
        rows[200]["clamp_nA"]+=.04
        self.assertEqual(m.assessment(rows,case)["status"],"FAIL")

    def test_bad_wall_clock_rate_is_inconclusive(self):
        case=m.CASES["01_current_facilitation"]
        rows=synthetic(case)
        for row in rows:
            row["host_seconds"]*=.70
        self.assertEqual(m.assessment(rows,case)["status"],"INCONCLUSIVE")

    def test_voltage_command_not_held_rejected(self):
        case=m.CASES["04_ampa_conductance"]
        rows=synthetic(case)
        rows[220]["voltage_mV"]=-65.
        self.assertEqual(m.assessment(rows,case)["status"],"FAIL")

    def test_no_incoming_spikes_is_inconclusive(self):
        case=m.CASES["01_current_facilitation"]
        rows=synthetic(case,[])
        self.assertEqual(m.assessment(rows,case)["status"],"INCONCLUSIVE")

    def test_setting_changes_never_accumulate_previous_drug_doses(self):
        for case in m.CASES.values():
            with self.subTest(case=case.name):
                cmd=m.commands_for(case)
                self.assertIn("PH E 0",cmd)
                self.assertIn("PH E 1",cmd)
                self.assertIn("PH X",cmd)
                self.assertIn("PH D 4 "+str(case.nbqx),cmd)
                self.assertIn("PH D 5 "+str(case.gabazine),cmd)
                self.assertIn("PH D 7 "+str(case.gvia),cmd)
                self.assertEqual(cmd.count("STP1 "+str(case.mode)),1)
                self.assertEqual(cmd[-1],"VCT 1")


if __name__=="__main__":
    unittest.main()
