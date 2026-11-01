# SPDX-License-Identifier: GPL-3.0-or-later
"""Compiled full-sketch STP x passive/active voltage clamp regression battery.

Host stubs simulate TTL/ADC/USB. Tests assert current conservation and STP
state against an independent analytical Python reference. They do not measure
ESP32 wall-clock timing or physical cables.
Run: python -m unittest discover -s Firmware/tests/stp_vc -v
"""
import math
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
VC_TESTS = ROOT / "Firmware/tests/vc"
SKETCH = ROOT / "Firmware/Spikeling_V3"
LIBRARY = ROOT / "Firmware/Librairies/Arduino-SerialCommand/src"

U = {0: 1.0, 1: .15, 2: .40, 3: .25}
TF = {0: 0., 1: 500., 2: 0., 3: 500.}
TR = {0: 0., 1: 0., 2: 800., 3: 600.}


def reference_multipliers(mode, ticks):
    """Independent recovery/consumption reference for model-step event indices."""
    if mode == 0:
        return [1.0] * len(ticks)
    u, x, last = U[mode], 1., None
    result = []
    for t in ticks:
        if last is not None:
            elapsed = (t - last) * .1
            u = U[mode] + (u-U[mode])*math.exp(-elapsed/TF[mode]) if TF[mode] else U[mode]
            x = 1.-(1.-x)*math.exp(-elapsed/TR[mode]) if TR[mode] else 1.
        result.append(u*x/U[mode])
        if TR[mode]:
            x *= 1.-u
        if TF[mode]:
            u += U[mode]*(1.-u)
        last = t
    return result


def decode(data):
    """Find host state probes and VC CSV records, even after old binary frames."""
    states, samples = [], []
    for line in data.splitlines():
        if b"STPSTATE," in line:
            text = line.split(b"STPSTATE,", 1)[1].decode("ascii").strip()
            x = [float(item) for item in text.split(",")]
            states.append(dict(tick=int(x[0]), mode1=int(x[1]), u1=x[2], x1=x[3],
                               seen1=bool(x[4]), current1=x[5],
                               mode2=int(x[6]), u2=x[7], x2=x[8],
                               seen2=bool(x[9]), current2=x[10],
                               total=x[11], clamp_mode=int(x[12]), pharm=bool(x[13])))
        for tag in (b"VC1,", b"VC2,"):
            if tag in line:
                text = line.split(tag, 1)[1].decode("ascii").strip()
                x = [float(item) for item in text.split(",")]
                if len(x) >= 11:
                    samples.append(dict(active=tag == b"VC2,", tick=int(x[0]),
                                        command=x[2], voltage=x[3], clamp=x[4],
                                        capacitive=x[5], leak=x[6], inward=x[7],
                                        flags=int(x[8])))
    return states, samples


def commands(*, active=False, mode1=0, mode2=0, gain1=6., gain2=-6., decay=990):
    # PH explicitly OFF. Ideal VC isolates compensating current from access error.
    return ("!PH E 0\n!NO1 0\n!PG1 0\n!SG11 "+str(gain1*4)+"\n"
            "!SG21 "+str(gain2*4)+"\n!SD11 "+str(decay)+"\n!SD21 "+str(decay)+"\n"
            "!STP1 "+str(mode1)+"\n!STP2 "+str(mode2)+"\n!VCM 1\n"
            "!VCA "+str(int(active))+"\n!VCI 1\n!VCMD -70\n!VCT 1\nR1100\n")


def pulse(channel, wait=0):
    return (f"R{wait}\n" if wait else "") + f"D{38 if channel==1 else 39} 1\nR1\nY\nD{38 if channel==1 else 39} 0\n"


class FullSketchSTPVC(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if shutil.which("g++") is None:
            raise unittest.SkipTest("g++ required for compiled-sketch tests")
        cls.tmp = tempfile.TemporaryDirectory(prefix="spikeling-stp-vc-")
        cls.exe = Path(cls.tmp.name)/"sketch"
        subprocess.run(["g++","-std=gnu++17","-O2","-ffp-contract=off","-DARDUINO=10819",
                        "-DVC_PROTOTYPE_TEST","-I",str(VC_TESTS/"stubs"),
                        "-I",str(SKETCH),"-I",str(LIBRARY),
                        str(VC_TESTS/"sketch_driver.cpp"),str(LIBRARY/"SerialCommand.cpp"),
                        "-o",str(cls.exe)],capture_output=True,text=True,check=True)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def execute(self, script):
        data = subprocess.run([str(self.exe)],input=script.encode(),capture_output=True,check=True).stdout
        return decode(data)

    def test_static_off_preserves_both_vc_backends(self):
        for active in (False, True):
            with self.subTest(active=active):
                states, rows = self.execute(commands(active=active)+pulse(1)+"Y\n")
                self.assertEqual(states[-1]["mode1"], 0)
                self.assertAlmostEqual(states[-1]["current1"], 6*.99,places=5)
                self.assertAlmostEqual(rows[-1]["inward"], .0594,delta=1e-5)
                self.assertAlmostEqual(rows[-1]["clamp"]-rows[-2]["clamp"],
                                       -.0594,delta=.0003)
                self.assertEqual(rows[-1]["flags"] & 4, 0)

    def test_facilitation_in_active_clamp_matches_independent_analytic_reference(self):
        script = commands(active=True,mode1=1)
        for gap in (0, 50, 50, 200, 10):
            script += pulse(1,gap)
        states, rows = self.execute(script)
        expected = reference_multipliers(1,[0,51,102,303,314])
        previous, last_tick = 0., None
        for s, want in zip(states, expected):
            gap = 0 if last_tick is None else s["tick"]-last_tick-1
            want_current = (previous * .99**gap + 6*want)*.99
            self.assertAlmostEqual(s["current1"], want_current,delta=3e-5)
            previous, last_tick = s["current1"], s["tick"]
        self.assertGreater(expected[1],expected[0])
        self.assertEqual(rows[-1]["flags"] & 4, 0)

    def test_negative_depression_in_active_clamp(self):
        script = commands(active=True,mode2=2)
        for gap in (0, 20, 20, 20):
            script += pulse(2,gap)
        states, rows = self.execute(script)
        reference = reference_multipliers(2,[0,21,42,63])
        previous,last_tick=0.,None
        for state,want in zip(states,reference):
            gap = 0 if last_tick is None else state["tick"]-last_tick-1
            expected = (previous*.99**gap - 6*want)*.99
            self.assertAlmostEqual(state["current2"],expected,delta=2e-5)
            self.assertLess(state["current2"],0)
            previous,last_tick=state["current2"],state["tick"]
        self.assertLess(reference[-1],reference[0])
        self.assertGreater(rows[-1]["inward"],-.3)

    def test_combined_biphasic_response_in_passive_clamp(self):
        script=commands(mode1=3)
        for gap in (0,20,20,20,20,20,20,20,20,20,20,20):
            script+=pulse(1,gap)
        states,rows=self.execute(script)
        multipliers=reference_multipliers(3,[0]+[21*i for i in range(1,12)])
        self.assertGreater(multipliers[1],1)
        self.assertLess(multipliers[-1],multipliers[1])
        self.assertEqual(states[-1]["seen1"],True)
        self.assertEqual(rows[-1]["flags"] & 4,0)

    def test_two_synapses_conserve_current_and_compensating_clamp(self):
        for active in (False,True):
            with self.subTest(active=active):
                script=commands(active=active,mode1=1,mode2=2)
                script+="R30\nY\n"+pulse(1)+"R2\n"+pulse(2)+"R25\n"+pulse(1)+"R7\n"+pulse(2)
                states,rows=self.execute(script)
                self.assertEqual(len(states),5)
                for s in states[1:]:
                    self.assertEqual(s["mode1"],1)
                    self.assertEqual(s["mode2"],2)
                self.assertTrue(states[-1]["seen1"] and states[-1]["seen2"])
                # Every diagnostic VC sample must represent exactly the raw signed currents
                # scaled once into nA when PH is OFF, not summed twice.
                self.assertLess(max(abs(r["clamp"]+r["inward"]) for r in rows[-30:]),.001)
                self.assertFalse(any(r["flags"] & 4 for r in rows))

    def test_state_survives_cc_vc_and_vc_cc_handover(self):
        script=("!PH E 0\n!NO1 0\n!PG1 0\n!SG11 24\n!STP1 1\n"
                "R20\n"+pulse(1)+"!VCM 1\nY\n!VCA 1\n!VCI 1\n!VCMD -70\n!VCT 1\n"
                "R20\n"+pulse(1)+"!VCM 0\nY\n")
        states,_=self.execute(script)
        self.assertEqual(len(states),4)
        self.assertEqual([s["clamp_mode"] for s in states],[0,1,1,0])
        self.assertTrue(all(s["seen1"] for s in states))
        self.assertGreater(states[2]["u1"],states[1]["u1"])
        self.assertAlmostEqual(states[2]["u1"],states[3]["u1"],delta=1e-6)

    def test_reselecting_mode_resets_plasticity_not_existing_tail(self):
        script=commands(mode1=1)+pulse(1)+"!STP1 1\nY\n"
        states,_=self.execute(script)
        last=states[-1]
        self.assertEqual(last["mode1"],1)
        self.assertFalse(last["seen1"])
        self.assertAlmostEqual(last["u1"],.15,delta=1e-7)
        self.assertAlmostEqual(last["x1"],1,delta=1e-7)
        self.assertAlmostEqual(last["current1"],states[-2]["current1"],delta=1e-6)

    def test_invalid_mode_does_not_change_existing_state(self):
        script=commands(mode1=1,mode2=3)+pulse(1)+"!STP1 4\n!STP2 -1\nY\n"
        states,_=self.execute(script)
        self.assertEqual(states[-1]["mode1"],1)
        self.assertEqual(states[-1]["mode2"],3)
        self.assertTrue(states[-1]["seen1"])

    def test_same_model_ticks_preserve_plasticity_at_different_wall_dt(self):
        outcome=[]
        for dt in (1000,2000,4000):
            script=commands(mode1=1)+f"!DT {dt}\n"+pulse(1)+"R100\n"+pulse(1)
            states,_=self.execute(script)
            outcome.append(states[-1]["u1"])
        self.assertLess(max(outcome)-min(outcome),1e-6)


if __name__=="__main__":
    unittest.main()
