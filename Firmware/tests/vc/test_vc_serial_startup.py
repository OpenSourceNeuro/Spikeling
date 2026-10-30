# SPDX-License-Identifier: GPL-3.0-or-later
"""Bounded startup regressions; simulated serial/clock, not ESP32 timing."""
from collections import deque
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[3]/'Firmware/tools'))
import run_active_vc_tests as active
import run_vc_hardware_tests as hardware
import run_vc_synapse_tests as synaptic

ACTIVE = b'VC-ACTIVE-1,mV,ms,nA,pF,MOhm,clock=2,gates=2,voltage=2\n'
PACKET = b'\xaa\x55'+bytes(16)  # Continuous valid CC framing, no newline.


class SerialDouble:
    def __init__(self, reply=None, chunks=(), binary=PACKET, timeout=.05):
        self.timeout = timeout
        self.reply = reply
        self.chunks = deque(chunks)
        self.binary = binary
        self.writes = []
        self.now = 0.
        self.read_sizes = []
        self.reset_count = 0

    def clock(self):
        return self.now

    @property
    def in_waiting(self):
        return len(self.chunks[0]) if self.chunks else len(self.binary)*100

    def read(self, size):
        self.read_sizes.append(size)
        self.now += min(.01, self.timeout)
        if self.chunks:
            data = self.chunks.popleft()
            if len(data) > size:
                self.chunks.appendleft(data[size:])
            return data[:size]
        return (self.binary*(size//max(1, len(self.binary))+1))[:size]

    def write(self, data):
        assert len(data) <= 32, 'Oversized command burst'
        self.writes.append(data)
        if data == b'VCINFO\n' and self.reply is not None:
            self.chunks.append(self.reply)
        return len(data)

    def reset_input_buffer(self):
        self.reset_count += 1
        self.chunks.clear()

    def readline(self):
        raise AssertionError('Unbounded line read must not be used')

    def flush(self):
        raise AssertionError('Unbounded OS flush must not be used')


class StartupSerialValidation(unittest.TestCase):
    def clock(self, stream):
        return patch.object(hardware.time, 'monotonic', side_effect=stream.clock)

    def test_continuous_binary_without_newlines_has_four_second_deadline(self):
        stream = SerialDouble()
        with self.clock(stream), self.assertRaisesRegex(TimeoutError, 'within 4 s'):
            active.identity(stream)
        self.assertGreaterEqual(stream.now, 4.)
        self.assertLess(stream.now, 4.02)
        self.assertLessEqual(max(stream.read_sizes), 512)
        self.assertEqual(stream.timeout, .05)

    def test_silent_serial_also_times_out_and_restores_blocking_setting(self):
        stream = SerialDouble(binary=b'', timeout=None)
        with self.clock(stream), self.assertRaises(TimeoutError):
            active.identity(stream)
        self.assertIsNone(stream.timeout)

    def test_identity_split_between_byte_chunks_after_binary(self):
        stream = SerialDouble(chunks=[PACKET, b'VC-', b'ACTIVE-1,mV,',
            b'ms,nA,pF,MOhm,clock=2,gates=2,voltage=2', b'\r\n'])
        with self.clock(stream):
            self.assertEqual(active.identity(stream), ACTIVE.decode().strip())
        self.assertEqual(stream.writes, [b'\n', b'VCINFO\n'])

    def test_false_partial_prefix_does_not_hide_valid_reply(self):
        stream = SerialDouble(reply=b'VC-junk'+ACTIVE)
        with self.clock(stream):
            self.assertEqual(active.identity(stream), ACTIVE.decode().strip())

    def test_wrong_firmware_identity_is_reported(self):
        stream = SerialDouble(reply=hardware.IDENTITY+b',clock=2\n')
        with self.clock(stream), self.assertRaisesRegex(RuntimeError, 'Unexpected VCINFO'):
            active.identity(stream)

    def test_missing_version_marker_is_not_accepted(self):
        stream = SerialDouble(reply=ACTIVE.replace(b',voltage=2', b''))
        with self.clock(stream), self.assertRaises(RuntimeError):
            active.identity(stream)

    def test_timeout_setting_restored_after_interrupt(self):
        stream = SerialDouble(timeout=.123)
        stream.read = lambda size: (_ for _ in ()).throw(KeyboardInterrupt())
        with self.clock(stream), self.assertRaises(KeyboardInterrupt):
            active.identity(stream)
        self.assertEqual(stream.timeout, .123)

    def test_complete_configuration_is_paced_and_drains_stream(self):
        stream = SerialDouble(reply=ACTIVE)
        stages = []
        with self.clock(stream):
            result = synaptic.configure(stream, '14_synaptic_input', 1,
                                         lambda stage, message: stages.append(stage))
        self.assertEqual(result, ACTIVE.decode().strip())
        self.assertEqual(len(stream.writes), 38)  # 36 commands + newline + query.
        self.assertTrue(all(len(x) <= 32 for x in stream.writes))
        self.assertGreater(stream.now, .35)
        self.assertEqual(stages, ['configuring', 'checking_firmware_identity'])
        self.assertIn(b'PH E 1\n', stream.writes)
        self.assertEqual(stream.timeout, .05)

    def test_invalid_command_rejected_before_any_write(self):
        for commands in (['VCM 1', 'x'*32], ['VCM 1', 'PH X\nVCM 1']):
            stream = SerialDouble()
            with self.assertRaises(ValueError):
                hardware.send_paced(stream, commands)
            self.assertEqual(stream.writes, [])

    def test_incomplete_write_is_not_accepted(self):
        stream = SerialDouble()
        stream.write = lambda data: len(data)-1
        with self.assertRaisesRegex(IOError, 'Incomplete'):
            hardware.send_paced(stream, ['VCINFO'])

    def test_startup_drain_has_deadline(self):
        stream = SerialDouble()
        with self.clock(stream):
            self.assertGreater(hardware.drain_serial(stream, 2), 0)
        self.assertGreaterEqual(stream.now, 2.)
        self.assertLess(stream.now, 2.02)
        self.assertEqual(stream.timeout, .05)

    def test_cleanup_requires_passive_identity_and_cc_packets(self):
        stream = SerialDouble(reply=hardware.IDENTITY+b',clock=2\n')
        with self.clock(stream):
            self.assertTrue(hardware.check_binary_stream_bounded(stream))
        self.assertEqual(stream.reset_count, 1)

    def test_cleanup_without_cc_packets_is_not_confirmed(self):
        stream = SerialDouble(reply=hardware.IDENTITY+b',clock=2\n', binary=b'')
        with self.clock(stream):
            self.assertFalse(hardware.check_binary_stream_bounded(stream))


if __name__ == '__main__':
    unittest.main()
