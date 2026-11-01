# SPDX-License-Identifier: GPL-3.0-or-later
"""Full-sketch native regression: one STP event and one pharmacological release.

The actual Arduino sketch and serial command parser are compiled against the
established VC host GPIO/ADC/USB stubs. This does not measure ESP32 timing.
"""
import math
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
VC = ROOT / "Firmware/tests/vc"
SKETCH = ROOT / "Firmware/Spikeling_V3"
LIB = ROOT / "Firmware/Librairies/Arduino-SerialCommand/src"

COLUMNS = [
    "tick", "enabled", "ph_mode", "clamp_mode",
    "event1", "raw1", "stp1", "released1", "conductance1", "rise1",
    "decay1", "effective1", "release1", "quanta1", "rng1",
    "event2", "raw2", "stp2", "released2", "conductance2", "rise2",
    "decay2", "effective2", "release2", "quanta2", "rng2", "total",
]


def reference(mode, event_ticks, dt_ms=0.1):
    """Independent Tsodyks-Markram recurrence with event-time recovery."""
    U, tf, tr = {0:(1.,0.,0.), 1:(.15,500.,0.), 2:(.4,0.,800.),
                 3:(.25,500.,600.)}[mode]
    u,x,last = U,1.,None
    result=[]
    for tick in event_ticks:
        if last is not None:
            elapsed=(tick-last)*dt_ms
            u=U+(u-U)*math.exp(-elapsed/tf) if tf else U
            x=1-(1-x)*math.exp(-elapsed/tr) if tr else 1.
        result.append((u/U)*x)
        if tr: x *= 1-u
        if tf: u += U*(1-u)
        last=tick
    return result


def script_prefix(*, active=True, conductance=False, mode1=1, mode2=2,
                  gain1=6., gain2=-6., nmda=False):
    return (
        "!NO1 0\n!PG1 0\n"
        f"!SG11 {gain1*4:g}\n!SG21 {gain2*4:g}\n"
        "!SD11 990\n!SD21 990\n"
        f"!STP1 {mode1}\n!STP2 {mode2}\n"
        f"!PH M {int(conductance)}\n"
        "!PH R 1 1\n!PH R 2 2\n"
        f"!PH N {int(nmda)}\n"
        "!PH C 0\n!PH D 4 0\n!PH D 5 0\n"
        "!PH D 6 0\n!PH D 7 0\n"
        "!PH L 1 0\n!PH L 2 0\n"
        "!PH E 1\n!PH X\n"
        f"!VCM 1\n!VCA {int(active)}\n"
        "!VCI 1\n!VCMD -70\n!VCT 1\nR1100\n"
    )


def pulse(channel, gap=0):
    return (f"R{gap}\n" if gap else "") + \
           f"D{38 if channel==1 else 39} 1\nR1\nJ\nD{38 if channel==1 else 39} 0\n"


def decode(output):
    rows=[]
    for line in output.splitlines():
        if b"PHSTP," not in line:
            continue
        line=line.split(b"PHSTP,",1)[1]
        values=[float(x) for x in line.split(b",")]
        if len(values)!=len(COLUMNS):
            raise AssertionError(f"Native PHSTP record has {len(values)} fields, expected {len(COLUMNS)}")
        rows.append(dict(zip(COLUMNS,values)))
    return rows


class IntegratedSTPPharmacology(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if shutil.which("g++") is None:
            raise unittest.SkipTest("g++ required for compiled full-sketch regressions")
        cls.temp=tempfile.TemporaryDirectory(prefix="spikeling-stp-ph-")
        cls.exe=Path(cls.temp.name)/"sketch"
        args=["g++","-std=gnu++17","-O2","-ffp-contract=off",
              "-DARDUINO=10819","-DVC_PROTOTYPE_TEST",
              "-I",str(VC/"stubs"),"-I",str(SKETCH),"-I",str(LIB),
              str(VC/"sketch_driver.cpp"),str(LIB/"SerialCommand.cpp"),"-o",str(cls.exe)]
        subprocess.run(args,check=True,capture_output=True,text=True)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def run_sketch(self,script):
        data=subprocess.run([str(self.exe)],input=script.encode(),
                            capture_output=True,check=True).stdout
        return decode(data)

    def test_off_preserves_original_deterministic_pharmacology_current(self):
        rows=self.run_sketch(script_prefix(mode1=0,mode2=0,conductance=False)+
                             pulse(1)+pulse(2))
        self.assertEqual(len(rows),2)
        self.assertAlmostEqual(rows[0]["event1"],6.,places=6)
        self.assertAlmostEqual(rows[0]["released1"],5.94,places=5)
        self.assertAlmostEqual(rows[0]["effective1"],5.94,places=5)
        self.assertAlmostEqual(rows[1]["event2"],-6.,places=6)
        self.assertAlmostEqual(rows[1]["released2"],-5.94,places=5)
        self.assertEqual(rows[1]["release1"],1)
        self.assertEqual(rows[1]["release2"],1)
        self.assertEqual(rows[1]["quanta1"],0)
        self.assertEqual(rows[1]["quanta2"],0)

    def test_facilitation_in_pharm_current_matches_independent_reference(self):
        script=script_prefix(mode1=1,mode2=0,conductance=False)
        for gap in (0,50,50,200,20):
            script+=pulse(1,gap)
        rows=self.run_sketch(script)
        multipliers=reference(1,[r["tick"] for r in rows])
        previous=0.
        prev_tick=None
        for row,want in zip(rows,multipliers):
            self.assertAlmostEqual(row["event1"],6*want,delta=7e-5)
            gap=0 if prev_tick is None else row["tick"]-prev_tick-1
            expected=(previous*.99**gap+6*want)*.99
            self.assertAlmostEqual(row["released1"],expected,delta=7e-5)
            self.assertAlmostEqual(row["effective1"],expected,delta=7e-5)
            self.assertEqual(row["quanta1"],0)
            previous=row["released1"]
            prev_tick=row["tick"]
        self.assertGreater(multipliers[-1],multipliers[0])

    def test_depression_signed_events_current_and_conductance(self):
        for conductance in (False,True):
            with self.subTest(conductance=conductance):
                script=script_prefix(mode1=0,mode2=2,conductance=conductance)
                for gap in (0,50,50,50):
                    script+=pulse(2,gap)
                rows=self.run_sketch(script)
                multipliers=reference(2,[r["tick"] for r in rows])
                for row,want in zip(rows,multipliers):
                    self.assertAlmostEqual(row["event2"],-6*want,delta=7e-5)
                    self.assertLess(row["released2"],0)
                    self.assertLess(row["effective2"],0)
                    self.assertEqual(row["stp1"],0)
                    self.assertEqual(row["stp2"],2)
                    self.assertGreaterEqual(row["conductance2"],0)
                self.assertLess(multipliers[-1],multipliers[0])

    def test_combined_on_two_independent_synapses(self):
        script=script_prefix(mode1=3,mode2=1,conductance=False)
        for gap in (0,31,31,31):
            script+=pulse(1,gap)+pulse(2)
        rows=self.run_sketch(script)
        s1=[r for r in rows if r["event1"]!=0]
        s2=[r for r in rows if r["event2"]!=0]
        for ch,mode,group in ((1,3,s1),(2,1,s2)):
            predicted=reference(mode,[r["tick"] for r in group])
            for row,expect in zip(group,predicted):
                signed=6 if ch==1 else -6
                self.assertAlmostEqual(row[f"event{ch}"],signed*expect,delta=7e-5)
        self.assertNotEqual(s1[-1]["event1"],6.)
        self.assertNotEqual(s2[-1]["event2"],-6.)

    def test_ampa_and_gabaa_conductances_each_receive_single_stp_factor(self):
        script=script_prefix(conductance=True,mode1=1,mode2=2)
        rows=self.run_sketch(script+pulse(1)+pulse(2))
        a,b=rows
        self.assertAlmostEqual(a["conductance1"],6/70*.99,delta=1e-6)
        self.assertAlmostEqual(a["effective1"],5.94,delta=2e-5)
        self.assertAlmostEqual(b["conductance2"],.6*.99,delta=1e-6)
        self.assertAlmostEqual(b["effective2"],-5.94,delta=2e-5)

    def test_nmda_states_share_one_facilitated_ampa_release_event(self):
        script=script_prefix(conductance=True,nmda=True,mode1=1)
        rows=self.run_sketch(script+pulse(1)+pulse(1,50))
        a,b=rows
        w=reference(1,[a["tick"],b["tick"]])[1]
        self.assertAlmostEqual(b["event1"],6*w,delta=7e-5)
        self.assertGreater(a["decay1"],a["rise1"])
        self.assertGreater(b["decay1"],b["rise1"])
        # NMDA activation is triggered once by the same STP-scaled glutamatergic event.
        self.assertGreater(b["effective1"],b["released1"])
        self.assertGreater(b["conductance1"],a["conductance1"])

    def test_nbqx_and_gabazine_halve_only_applicable_fast_receptor(self):
        base=script_prefix(conductance=True,nmda=False)
        controls=self.run_sketch(base+pulse(1)+pulse(2))
        drugs=self.run_sketch(base+"!PH D 4 .30\n!PH D 5 .90\n"+pulse(1)+pulse(2))
        self.assertAlmostEqual(drugs[0]["effective1"],controls[0]["effective1"]*.5,delta=1e-5)
        self.assertAlmostEqual(drugs[1]["effective2"],controls[1]["effective2"]*.5,delta=1e-5)
        for idx in (0,1):
            self.assertAlmostEqual(drugs[idx]["released1"],controls[idx]["released1"],delta=1e-6)
            self.assertAlmostEqual(drugs[idx]["released2"],controls[idx]["released2"],delta=1e-6)
            self.assertAlmostEqual(drugs[idx]["conductance1"],controls[idx]["conductance1"],delta=1e-6)
            self.assertAlmostEqual(drugs[idx]["conductance2"],controls[idx]["conductance2"],delta=1e-6)

    def test_apv_halves_nmda_not_fast_ampa(self):
        base=script_prefix(conductance=True,nmda=True,mode1=1)
        control=self.run_sketch(base+pulse(1))[0]
        treated=self.run_sketch(base+"!PH D 6 3.7\n"+pulse(1))[0]
        self.assertAlmostEqual(control["released1"],treated["released1"],delta=1e-6)
        self.assertAlmostEqual(control["conductance1"],treated["conductance1"],delta=1e-6)
        fast=control["conductance1"]*70.
        expected=fast+(control["effective1"]-fast)*.5
        self.assertAlmostEqual(treated["effective1"],expected,delta=2e-5)

    def test_gvia_scales_one_event_and_not_presynaptic_stp_state(self):
        base=script_prefix(conductance=False,mode1=1)
        control=self.run_sketch(base+pulse(1)+pulse(1,50))
        drug=self.run_sketch(base+"!PH C 1\n!PH F 1 .35\n!PH D 7 10\n"+
                             pulse(1)+pulse(1,50))
        efficacy=(1.-.35*.5)**3
        for a,b in zip(control,drug):
            self.assertAlmostEqual(b["event1"],a["event1"],delta=1e-6)
            self.assertAlmostEqual(b["release1"],efficacy,delta=1e-6)
            self.assertAlmostEqual(b["released1"],a["released1"]*efficacy,delta=2e-5)
        self.assertGreater(drug[-1]["event1"],drug[0]["event1"])

    def test_binomial_quanta_and_rng_are_invariant_to_stp_mode(self):
        def trial(mode):
            script=script_prefix(conductance=False,mode1=mode)
            script+="!PH L 1 1\n!PH S 1 8\n!PH P 1 .5\n!PH Z 1234\n"
            script+="!PH X\n"
            for gap in (0,40,40,40,40,40,40):
                script+=pulse(1,gap)
            return self.run_sketch(script)
        static=trial(0)
        facil=trial(1)
        self.assertEqual(len(static),7)
        self.assertEqual([r["quanta1"] for r in static],[r["quanta1"] for r in facil])
        self.assertEqual([r["rng1"] for r in static],[r["rng1"] for r in facil])
        self.assertEqual([r["release1"] for r in static],[r["release1"] for r in facil])
        expected=reference(1,[r["tick"] for r in facil])
        for row,mult in zip(facil,expected):
            self.assertAlmostEqual(row["event1"],6*mult,delta=7e-5)
            self.assertAlmostEqual(row["release1"],row["quanta1"]/(8*.5),delta=1e-6)
        self.assertTrue(any(r["quanta1"]>0 for r in facil))

    def test_release_failure_does_not_prevent_stp_progress(self):
        # A zero-quanta draw is not needed: p0 small gives a deterministic
        # zero-release scenario under a fixed xorshift seed.
        script=script_prefix(mode1=1,conductance=False)
        script+="!PH L 1 1\n!PH S 1 1\n!PH P 1 .00001\n!PH Z 7\n!PH X\n"
        rows=self.run_sketch(script+pulse(1)+pulse(1,50))
        self.assertEqual([r["quanta1"] for r in rows],[0.,0.])
        self.assertEqual([r["released1"] for r in rows],[0.,0.])
        self.assertGreater(rows[1]["event1"],rows[0]["event1"])

    def test_ph_reset_does_not_reset_independent_stp_utilisation(self):
        script=script_prefix(mode1=1)
        rows=self.run_sketch(script+pulse(1)+"!PH X\nJ\n"+pulse(1,50))
        self.assertEqual(len(rows),3)
        self.assertAlmostEqual(rows[1]["released1"],0,delta=1e-8)
        self.assertEqual(rows[1]["event1"],rows[0]["event1"])  # cached event, no new edge
        self.assertGreater(rows[2]["event1"],rows[0]["event1"])

    def test_cc_and_vc_both_consume_same_stp_pharmacology_path(self):
        def trial(vc_enabled):
            script=script_prefix(active=True,conductance=False,mode1=1)
            if not vc_enabled:
                script+="!VCT 0\n!VCM 0\n"
            return self.run_sketch(script+pulse(1)+pulse(1,50))
        cc,vc=trial(False),trial(True)
        self.assertEqual([x["clamp_mode"] for x in cc],[0.,0.])
        self.assertEqual([x["clamp_mode"] for x in vc],[1.,1.])
        for a,b in zip(cc,vc):
            self.assertAlmostEqual(a["event1"],b["event1"],delta=1e-6)
            self.assertAlmostEqual(a["released1"],b["released1"],delta=1e-6)

if __name__=="__main__":
    unittest.main()
