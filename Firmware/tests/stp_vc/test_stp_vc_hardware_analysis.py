# SPDX-License-Identifier: GPL-3.0-or-later
"""Adversarial tests for the physical STP/VC diagnostic analyser (no serial port)."""
import importlib.util
from pathlib import Path
import unittest

TOOL = Path(__file__).resolve().parents[2]/"tools/run_stp_vc_hardware.py"
spec=importlib.util.spec_from_file_location("stp_vc_hardware",TOOL)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def fake_trace(mode=1,gain=6.,decay=.99,count=7,break_balance=False):
    impulses=[20+50*k for k in range(count)]
    expected=m.reference(mode,impulses)
    amplitudes=dict(zip(impulses,expected))
    current=0.
    rows=[]
    for tick in range(420):
        current=(current+gain*amplitudes.get(tick,0.)) *decay
        inward=round(current*.01,6)
        row={"tick":tick,"time_ms":tick*.1,"input_nA":inward,
             "clamp_nA":-inward+(.04 if break_balance and tick>=200 else 0.),
             "capacitive_nA":0.,"leak_nA":0.,"sodium_nA":0.,
             "potassium_nA":0.,"receptor_nA":0.,
             "voltage_mV":-70.,"flags":0,"host_seconds":tick*.002}
        rows.append(row)
    return rows


class HardwareAnalysis(unittest.TestCase):
    def test_full_reference_agreement_for_all_presets_and_signs(self):
        for mode in range(4):
            for gain in (6.,-6.):
                with self.subTest(mode=mode,gain=gain):
                    rows=fake_trace(mode,gain)
                    result=m.extract(rows,gain,.99,mode,5)
                    self.assertEqual(result["status"],"PASS",result["reason"])
                    self.assertEqual(result["event_count"],7)
                    self.assertLess(result["max_multiplier_error"],.003)

    def test_corrupt_model_cannot_pass(self):
        rows=fake_trace(mode=1)
        result=m.extract(rows,6.,.99,2,5)
        self.assertEqual(result["status"],"FAIL")

    def test_missing_spikes_are_not_pass(self):
        self.assertEqual(m.extract(fake_trace(count=0),6.,.99,1,5)["status"],"INCONCLUSIVE")

    def test_dropped_tick_is_not_pass(self):
        rows=fake_trace()
        del rows[100]
        self.assertEqual(m.extract(rows,6.,.99,1,5)["status"],"INCONCLUSIVE")

    def test_deadline_fault_is_not_pass(self):
        rows=fake_trace()
        rows[200]["flags"]=64
        self.assertEqual(m.extract(rows,6.,.99,1,5)["status"],"FAIL")

    def test_wrong_wall_time_cannot_pass(self):
        rows=fake_trace()
        for row in rows: row["host_seconds"]*=.8
        self.assertEqual(m.extract(rows,6.,.99,1,5)["status"],"INCONCLUSIVE")

    def test_bad_clamp_compensation_is_not_pass(self):
        rows=fake_trace(break_balance=True)
        self.assertEqual(m.extract(rows,6.,.99,1,5)["status"],"FAIL")

    def test_invalid_vc2_row_is_rejected(self):
        good=b"VC2,1,0.1,-70,-70,0,0,0,0,0,300,100,0,0,0,0.1,0.5,0.3"
        self.assertEqual(m.decode_line(good,"active")["tick"],1)
        self.assertIsNone(m.decode_line(b"VC2,1,2,3","active"))
        self.assertIsNone(m.decode_line(good.replace(b"0.5",b"NaN"),"active"))


if __name__=="__main__":
    unittest.main()
