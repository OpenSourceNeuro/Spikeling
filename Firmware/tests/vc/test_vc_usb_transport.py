# SPDX-License-Identifier: GPL-3.0-or-later
"""Bounded active-VC transport against a simulated finite USB FIFO/host pause.

Uses the actual sketch/parser. This is not an ESP32 driver or timing benchmark.
"""
import sys
import unittest
import test_voltage_clamp as base
import test_vc_timing_trace as profile
sys.path.insert(0,str(base.ROOT/'Firmware/tools'))
import run_active_vc_tests as active


def setUpModule():
    profile.setUpModule()


class GuardedUsb(unittest.TestCase):
    def test_twenty_millisecond_host_pause_is_buffered_without_model_delay_or_loss(self):
        data,trace=profile.run(profile.PREFIX+'U20000\nR40\n!VCPR ?\n')
        rows=[active.parse_sample(line) for line in data.splitlines() if line.startswith(b'VC2,')]
        self.assertEqual([r['sequence'] for r in rows],list(range(1,41)))
        self.assertTrue(all(r['flags']==0 and r['previous_loop_us']==0 for r in rows))
        self.assertEqual(trace['summary']['capacity_skips'],0)
        self.assertEqual(trace['summary']['overruns'],0)
        self.assertEqual(trace['summary']['late_starts'],0)

    def test_full_fifo_skips_whole_records_without_blocking_and_latches_failure(self):
        data,trace=profile.run(profile.PREFIX+'U100000\nR80\n!VCPR ?\n')
        rows=[active.parse_sample(line) for line in data.splitlines() if line.startswith(b'VC2,')]
        sequences=[r['sequence'] for r in rows]
        self.assertGreater(trace['summary']['capacity_skips'],0)
        self.assertEqual(trace['summary']['short_writes'],0)
        self.assertEqual(trace['summary']['overruns'],0)
        self.assertEqual(trace['summary']['late_starts'],0)
        self.assertLess(len(sequences),80)
        self.assertEqual(sequences[-1],80)
        self.assertTrue(any(b-a>1 for a,b in zip(sequences,sequences[1:])))
        self.assertTrue(all(r['flags']==128 for r in rows if r['sequence']>=50))
        self.assertTrue(all(e['reason']==16 and e['written_bytes']==0 for e in trace['events']))

    def test_short_driver_write_remains_a_transport_failure(self):
        data,trace=profile.run(profile.PREFIX+'W0 0\nR4\n!VCPR ?\n')
        rows=[active.parse_sample(line) for line in data.splitlines() if line.startswith(b'VC2,')]
        self.assertEqual(trace['summary']['short_writes'],1)
        self.assertEqual(trace['summary']['capacity_skips'],0)
        self.assertEqual(rows[0]['sequence'],2)
        self.assertTrue(all(r['flags']==128 for r in rows))

    def test_new_diagnostic_session_resets_transport_latch(self):
        data,trace=profile.run(profile.PREFIX+'W0 0\nR3\n!VCT 0\n!VCT 1\nR3\n!VCPR ?\n')
        rows=[active.parse_sample(line) for line in data.splitlines() if line.startswith(b'VC2,')]
        self.assertTrue(all(r['flags']==0 for r in rows if r['sequence']>=4))
        self.assertEqual(trace['summary']['short_writes'],1)  # Trace was not reset.

    def test_cc_restores_audited_timeout_and_preserves_binary_framing(self):
        # The original byte-stream regression also covers CC without tracing;
        # this exercises the extra transition after an explicitly guarded stream.
        data,_=profile.run(profile.PREFIX+'R2\nQ\n!VCT 0\n!VCM 0\nR2\nQ\n!VCPR ?\n')
        self.assertIn(b'\xaa\x55',data)
        self.assertIn(b'USBSTATE,1,1,0,0,4096',data)
        self.assertIn(b'USBSTATE,1,0,0,100,4096',data)


if __name__=='__main__':unittest.main()
