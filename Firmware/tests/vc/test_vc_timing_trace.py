# SPDX-License-Identifier: GPL-3.0-or-later
"""Trace localisation and loss detection with actual sketch/parser, simulated IO."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import test_voltage_clamp as base
from test_vc_serial_startup import SerialDouble, PACKET
sys.path.insert(0,str(base.ROOT/'Firmware/tools'))
import vc_timing_trace as trace
from capture_vc_inputs_v2 import BufferedCapture

PREFIX='!VCM 1\n!VCA 1\n!VCI 1\n!VCMD -70\n!VCT 1\n!VCPR 1\n'


def setUpModule():
    base.compile_sketch(base.SKETCH,base.TMP/'trace_sketch',True)


def run(script):
    data=subprocess.run([str(base.TMP/'trace_sketch')],input=script.encode(),
                        capture_output=True,check=True).stdout
    prefixes=(b'VCPR1,',b'VCE1,',b'VCPMAX,',b'VCPREND,')
    lines=[line[min(line.find(p) for p in prefixes if p in line):]
           for line in data.splitlines() if any(p in line for p in prefixes)]
    return data,trace.decode(lines)


class FirmwareTrace(unittest.TestCase):
    def test_clean_tick_trace_and_freeze(self):
        _,r=run(PREFIX+'R10\n!VCPR 0\nR5\n!VCPR ?\n')
        self.assertEqual(r['summary']['ticks'],10)
        self.assertEqual(r['events'],[])

    def test_serial_stall_is_localised_and_next_tick_reports_deadline(self):
        data,r=run(PREFIX+'W21000 4294967295\nR1\nT0\n!VCPR ?\n')
        self.assertEqual(r['summary']['overruns'],1)
        self.assertEqual(r['summary']['late_starts'],1)
        e=r['events'][0]
        self.assertEqual((e['sequence'],e['write_us'],e['total_us']),(1,21000,21000))
        self.assertEqual(e['membrane_us'],0)
        lines=[l for l in data.splitlines() if l.startswith(b'VC2,')]
        self.assertEqual(int(lines[1].split(b',')[9]),64)

    def test_zero_byte_write_retains_missing_sequence_evidence(self):
        data,r=run(PREFIX+'W0 0\nR3\n!VCPR ?\n')
        self.assertEqual(r['summary']['short_writes'],1)
        e=r['events'][0]
        self.assertEqual((e['sequence'],e['written_bytes'],e['reason']),(1,0,4))
        self.assertGreater(e['expected_bytes'],100)
        self.assertNotIn(b'VC2,1,',data)
        self.assertIn(b'VC2,2,',data)

    def test_trace_overflow_retains_failure_counts(self):
        _,r=run(PREFIX+('W0 0\nR1\n'*20)+'!VCPR ?\n')
        self.assertEqual(r['summary']['short_writes'],20)
        self.assertEqual(r['summary']['records'],16)
        self.assertEqual(r['summary']['overflow'],4)

    def test_disabled_trace_does_not_collect_or_change_vc2(self):
        _,r=run(PREFIX+'!VCPR 0\nW21000 4294967295\nR1\n!VCPR ?\n')
        self.assertEqual(r['summary']['ticks'],0)
        self.assertEqual(r['events'],[])

    def test_exit_to_cc_stops_collection_without_erasing_evidence(self):
        _,r=run(PREFIX+'W0 0\nR1\n!VCM 0\nR5\n!VCPR ?\n')
        self.assertEqual(r['summary']['ticks'],1)
        self.assertEqual(r['summary']['short_writes'],1)


class TraceTransport(unittest.TestCase):
    def test_query_recovers_markers_after_binary_with_bounded_reads(self):
        data=(PACKET+b'VCPR1,10,0,0,0,0,0,0\n'+b'VCPMAX,1,2,3,4,5,6,7,8\nVCPREND,0\n')
        s=SerialDouble(chunks=[data[i:i+7] for i in range(0,len(data),7)])
        r,raw=trace.query(s)
        self.assertEqual(r['summary']['ticks'],10)
        self.assertEqual(r['maximum_stage_us']['write_us'],8)
        self.assertIn(b'VCPREND,0',raw)
        self.assertLessEqual(max(s.read_sizes),512)

    def test_missing_reply_times_out_on_continuous_binary(self):
        s=SerialDouble()
        with patch('run_vc_hardware_tests.time.monotonic',s.clock):
            with self.assertRaisesRegex(TimeoutError,'No complete timing trace'):
                trace.query(s,timeout=.2)
        self.assertLess(s.now,.22)

    def test_inconsistent_record_count_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'Incomplete timing trace'):
            trace.decode([b'VCPR1,10,1,0,0,0,0,0',b'VCPMAX,0,0,0,0,0,0,0,0',b'VCPREND,0'])

    def test_raw_capture_is_exact_and_capped_without_stopping_reader(self):
        class Input:
            def __init__(self):self.chunks=[b'ignored\n',b'ok\n',b'last\n']
            @property
            def in_waiting(self):return len(self.chunks[0])
            def read(self,n):
                data=self.chunks.pop(0)
                if not self.chunks:recorder.stop_event.set()
                return data
        stream=Input()
        recorder=BufferedCapture(stream,parser=lambda line:{} if line in (b'ok',b'last') else None,raw_limit=10)
        recorder.run()
        self.assertEqual(recorder.raw_data,b'ignored\nok')
        self.assertEqual(recorder.metrics['raw_bytes_truncated'],6)
        self.assertEqual(recorder.metrics['non_sample_lines'],1)
        self.assertEqual(len(recorder.rows),2)
        with tempfile.TemporaryDirectory() as d:
            trace.save_raw(Path(d),recorder)
            self.assertEqual((Path(d)/'serial_rx.bin').read_bytes(),b'ignored\nok')
        stream=Input()
        recorder=BufferedCapture(stream,parser=lambda line:{} if line in (b'ok',b'last') else None,raw_limit=100)
        recorder.raw_chunk_limit=1
        recorder.run()
        self.assertEqual(recorder.raw_data,b'ignored\nok\nlast\n')
        self.assertEqual(len(recorder.raw_chunks),1)
        self.assertEqual(recorder.metrics['raw_chunks_truncated'],2)
        self.assertEqual(len(recorder.rows),2)


if __name__=='__main__':unittest.main()
