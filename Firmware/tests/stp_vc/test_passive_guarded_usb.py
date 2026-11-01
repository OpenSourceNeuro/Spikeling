# SPDX-License-Identifier: GPL-3.0-or-later
"""Guarded passive VC1 diagnostic transport against the complete compiled sketch.

Unlike the previous multi-print VC1 path, the corrected firmware prepares one
record and checks TX capacity before attempting an atomic USB write.
"""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[3]
STUBS=ROOT/"Firmware/tests/vc/stubs"
SKETCH=ROOT/"Firmware/Spikeling_V3"
LIB=ROOT/"Firmware/Librairies/Arduino-SerialCommand/src"
PREFIX="!PH E 0\n!VCM 1\n!VCA 0\n!VCI 1\n!VCMD -70\n!VCT 1\n"


class GuardedPassiveUSB(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if shutil.which("g++") is None:
            raise unittest.SkipTest("g++ required")
        cls.temp=tempfile.TemporaryDirectory(prefix="stp-passive-vc-usb-")
        cls.exe=Path(cls.temp.name)/"sketch"
        args=["g++","-std=gnu++17","-O2","-ffp-contract=off",
              "-DARDUINO=10819","-DVC_PROTOTYPE_TEST",
              "-I",str(STUBS),"-I",str(SKETCH),"-I",str(LIB),
              str(ROOT/"Firmware/tests/vc/sketch_driver.cpp"),
              str(LIB/"SerialCommand.cpp"),"-o",str(cls.exe)]
        subprocess.run(args,check=True,text=True,capture_output=True)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def run_sketch(self,script):
        return subprocess.run([str(self.exe)],input=script.encode(),capture_output=True,check=True).stdout

    def test_passive_vct_enables_buffered_usb_and_preserves_vc1_record_structure(self):
        data=self.run_sketch(PREFIX+"Q\nR25\n")
        self.assertIn(b"USBSTATE,1,1,0,0,4096",data)
        rows=[r for r in data.splitlines() if r.startswith(b"VC1,")]
        self.assertEqual(len(rows),25)
        self.assertEqual([int(r.split(b",")[1]) for r in rows],list(range(1,26)))
        self.assertTrue(all(len(r.split(b","))==12 for r in rows))
        self.assertTrue(all(int(r.split(b",")[9])==0 for r in rows))

    def test_short_host_pause_neither_blocks_model_nor_drops_records(self):
        data=self.run_sketch(PREFIX+"U20000\nR25\n")
        rows=[r for r in data.splitlines() if r.startswith(b"VC1,")]
        self.assertEqual([int(r.split(b",")[1]) for r in rows],list(range(1,26)))
        self.assertTrue(all(int(r.split(b",")[9])==0 for r in rows))

    def test_full_fifo_only_skips_whole_records_and_reports_transport_fault(self):
        data=self.run_sketch(PREFIX+"U250000\nR180\nQ\n")
        rows=[r for r in data.splitlines() if r.startswith(b"VC1,")]
        ticks=[int(r.split(b",")[1]) for r in rows]
        self.assertTrue(ticks)
        self.assertLess(len(ticks),180)
        self.assertEqual(ticks[-1],180)
        self.assertTrue(any(b-a>1 for a,b in zip(ticks,ticks[1:])))
        self.assertTrue(any(int(r.split(b",")[9])&128 for r in rows))
        self.assertFalse(any(int(r.split(b",")[9])&64 for r in rows))
        self.assertIn(b"USBSTATE,1,1,1,0,4096",data)

    def test_disabling_diagnostics_restores_ordinary_usb_timeout(self):
        data=self.run_sketch(PREFIX+"R2\n!VCT 0\nQ\n")
        self.assertIn(b"USBSTATE,1,0,0,100,4096",data)


if __name__=="__main__": unittest.main()
