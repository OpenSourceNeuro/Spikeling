#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Bounded retrieval of a frozen firmware timing trace; never changes thresholds."""
import csv
import time
from run_vc_hardware_tests import _read_before, send_paced

STAGES = ('command', 'input', 'release', 'stimulus', 'membrane', 'output', 'format', 'write')
SUMMARY = ('ticks', 'records', 'overruns', 'late_starts', 'short_writes', 'format_errors', 'overflow')
EVENT = ('sequence', 'elapsed_us', 'total_us', *(s+'_us' for s in STAGES),
         'expected_bytes', 'written_bytes', 'solve_us', 'reason')


def decode(lines):
    summary = maximum = ending = None
    events = []
    for line in lines:
        tag, *parts = line.decode('ascii').strip().split(',')
        values = [int(v) for v in parts]
        if any(v < 0 or v > 2**32-1 for v in values):
            raise ValueError('Out-of-range trace field')
        fields = SUMMARY + (('capacity_skips',) if tag == 'VCPR2' else ())
        if tag in ('VCPR1', 'VCPR2') and len(values) == len(fields) and summary is None:
            summary = dict(zip(fields, values))
        elif tag == 'VCE1' and len(values) == len(EVENT):
            events.append(dict(zip(EVENT, values)))
        elif tag == 'VCPMAX' and len(values) == len(STAGES) and maximum is None:
            maximum = dict(zip((s+'_us' for s in STAGES), values))
        elif tag == 'VCPREND' and len(values) == 1 and ending is None:
            ending = values[0]
        else:
            raise ValueError('Malformed or duplicated timing-trace record')
    if (summary is None or maximum is None or ending is None or
            summary['records'] != len(events) or ending != len(events) or ending > 16):
        raise ValueError('Incomplete timing trace')
    return {'summary': summary, 'maximum_stage_us': maximum, 'events': events,
            'scope': 'Elapsed stage times include pre-emption within the measured span; '
                     'a long write span alone does not identify host/USB/OS causality. '
                     'First 16 exceptional ticks retained; overflow remains explicit.'}


def query(stream, timeout=4., raw_path=None):
    # Called only after the background reader stops. Freeze before dumping, so
    # query/analysis/cleanup traffic cannot be mistaken for acquisition faults.
    send_paced(stream, ['VCT 0', 'VCPR 0', 'VCPR ?'])
    end = time.monotonic()+timeout
    pending = bytearray()
    raw = bytearray()
    lines = []
    prefixes = (b'VCPR1,', b'VCPR2,', b'VCE1,', b'VCPMAX,', b'VCPREND,')
    try:
        while time.monotonic() < end:
            data = _read_before(stream, end)
            raw.extend(data)
            pending.extend(data)
            split = pending.split(b'\n')
            pending = bytearray(split.pop())[-8192:]
            for line in split:
                found = [(line.find(p), p) for p in prefixes if p in line]
                if found:
                    offset, prefix = min(found)
                    lines.append(line[offset:])
                    if prefix == b'VCPREND,':
                        result = decode(lines)
                        result['query_bytes'] = len(raw)
                        return result, bytes(raw)
            if len(raw) > 2*1024*1024:
                raise ValueError('Timing trace query exceeded byte limit')
        raise TimeoutError('No complete timing trace within 4 s')
    finally:
        if raw_path is not None:
            raw_path.write_bytes(raw)


def save_raw(output, recorder):
    (output/'serial_rx.bin').write_bytes(recorder.raw_data)
    with (output/'serial_rx_chunks.csv').open('w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(('wall_s', 'offset', 'size'))
        writer.writerows(recorder.raw_chunks)
