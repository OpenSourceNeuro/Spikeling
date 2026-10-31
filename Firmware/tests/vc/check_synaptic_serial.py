#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Linux host QA: real sketch/parser + pyserial/PTY + complete synaptic CLI.

SIMULATED IO AND EXTERNALLY PACED CLOCK. Not an ESP32 timing measurement.
Usage: python Firmware/tests/vc/check_synaptic_serial.py NEW_OUTPUT_FOLDER
Requires g++, pyserial, scipy and matplotlib. Operator actions are simulated.
Exit success means semantic/cleanup workflow checks passed; actual CLI timing
failures remain FAIL in reports and all_capture_checks_as_expected is false.
"""
import json
import os
from pathlib import Path
import pty
import queue
import select
import subprocess
import sys
import threading
import time
import tty

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
TOOLS = ROOT / 'Firmware/tools'


def exercise(executable, case, output, missing_signal=False, channel=1,
             drop_first_identity=False, timing_trace=False, inject_short_write=False,
             phase_seconds=12, host_pause_us=0):
    master, slave = pty.openpty()
    tty.setraw(slave)
    port = os.ttyname(slave)
    native = subprocess.Popen([str(executable)], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    stop = threading.Event()
    actions = queue.Queue()
    errors = []

    def bridge():
        pending = b''
        source_on = False
        source_counter = 0
        gpio = 38 if channel == 1 else 39
        queries = 0
        newline_free = False
        tick = time.monotonic()
        try:
            while not stop.is_set():
                while not actions.empty():
                    action = actions.get_nowait()
                    if action == 'source_on':
                        source_on = not missing_signal
                        if inject_short_write:
                            native.stdin.write(b'W0 0\n')
                        if host_pause_us:
                            native.stdin.write(f'U{host_pause_us}\n'.encode())
                    elif action == 'source_off':
                        source_on = False
                    else:
                        native.stdin.write(action.encode() + b'\n')
                    native.stdin.flush()
                readable, _, _ = select.select([master, native.stdout], [], [], .0005)
                if master in readable:
                    pending += os.read(master, 65536)
                    lines = pending.split(b'\n')
                    pending = lines.pop()
                    for line in lines:
                        if line.strip():
                            if line.strip() == b'VCINFO':
                                queries += 1
                                if drop_first_identity and queries == 1:
                                    newline_free = True
                                    continue
                                newline_free = False
                            native.stdin.write(b'!' + line.strip() + b'\n')
                    native.stdin.flush()
                if native.stdout in readable:
                    data = os.read(native.stdout.fileno(), 65536)
                    if not data:
                        raise RuntimeError('Native sketch stopped')
                    if newline_free:
                        # Continuous newline-free binary is the observed hang
                        # condition. Alter no samples in normal capture QA.
                        data = data.replace(b'\n', b'\x00')
                    os.write(master, data)
                now = time.monotonic()
                if now >= tick:
                    high = int(source_on and source_counter % 250 == 0)
                    native.stdin.write(f'D{gpio} {high}\n'.encode())
                    source_counter += 1
                    native.stdin.write(b'R1\n')
                    native.stdin.flush()
                    tick += .002
        except Exception as error:
            if not stop.is_set():
                errors.append(str(error))

    thread = threading.Thread(target=bridge, daemon=True)
    thread.start()
    args = [sys.executable, str(TOOLS / 'run_vc_synapse_tests.py'), port,
            '--case', case, '--output', str(output), '--synapse', str(channel)]
    if timing_trace:
        args.append('--timing-trace')
    if phase_seconds != 12:
        args += ['--phase-seconds', str(phase_seconds)]
    client = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, text=True, bufsize=1)
    lines = []

    def operator():
        for line in client.stdout:
            lines.append(line)
            if 'SOURCE: turn its Patch knob up' in line:
                actions.put('source_on')
            elif 'SOURCE: return its Patch knob' in line:
                actions.put('source_off')
            if 'Press Enter AFTER' in line:
                client.stdin.write('\n')
                client.stdin.flush()

    observer = threading.Thread(target=operator, daemon=True)
    observer.start()
    try:
        code = client.wait(timeout=3*phase_seconds+65)
        observer.join(timeout=2)
    finally:
        if client.poll() is None:
            client.kill()
            client.wait()
        stop.set()
        thread.join(timeout=2)
        native.terminate()
        native.wait(timeout=2)
        os.close(master)
        os.close(slave)
        output.mkdir(exist_ok=True)
        (output / 'cli.log').write_text(''.join(lines))
    if errors:
        raise RuntimeError('; '.join(errors))
    report = json.loads((output / 'report.json').read_text())
    if timing_trace:
        assert (output/'serial_rx.bin').stat().st_size > 1000
        assert (output/'serial_rx_chunks.csv').exists()
        assert (output/'trace_query_rx.bin').exists()
        assert report['timing_trace']['summary']['ticks'] > 0
        assert report['pc_reader_metrics']['raw_bytes_truncated'] == 0
        assert report['cc_binary_stream_resumed']
    if phase_seconds > 12:
        assert report['analysis']['extended_duration']['passed']
    if inject_short_write:
        assert code == 1 and not report['all_passed']
        assert report['error'] == 'Missing or duplicated device sample'
        assert report['timing_trace']['summary']['short_writes'] == 1
        assert report['timing_trace']['events'][0]['written_bytes'] == 0
        assert report['capture_complete'] and report['cc_binary_stream_resumed']
        return {'case':'expected_short_write','workflow_checks_passed':True,
                'all_passed':False,'trace_detected_short_write':True,
                'cc_binary_stream_resumed':True}
    if host_pause_us >= 100000:
        assert code == 1 and not report['all_passed']
        assert report['error'] == 'Missing or duplicated device sample'
        assert report['timing_trace']['summary']['capacity_skips'] > 0
        assert report['timing_trace']['summary']['overruns'] == 0
        assert report['capture_complete'] and report['cc_binary_stream_resumed']
        return {'case':'expected_capacity_skip','workflow_checks_passed':True,
                'all_passed':False,'trace_detected_capacity_skip':True,
                'cc_binary_stream_resumed':True}
    if drop_first_identity:
        assert code == 1 and not report['all_passed']
        assert not report['capture_complete'] and 'analysis' not in report
        assert report['startup_stage'] == 'checking_firmware_identity'
        assert 'No matching VCINFO reply within 4 s' in report['error']
        assert report['cc_binary_stream_resumed']
        assert 'cleanup_error' not in report
        return {'case': 'expected_missing_identity', 'workflow_checks_passed': True,
                'all_passed': False, 'startup_timeout_detected': True,
                'cc_binary_stream_resumed': True}
    expected = not missing_signal
    analysis = report.get('analysis', {})
    # A shared host can delay the paced bridge/PTY reader. Preserve the actual
    # CLI FAIL and clock metrics; assess serial workflow independently. Never
    # alter timestamps, production analyser rules or report['all_passed'].
    workflow_ok = (report.get('capture_complete') and
                   report.get('cc_binary_stream_resumed') and
                   not any(k in report for k in ('error', 'reader_error', 'cleanup_error')) and
                   analysis.get('sample_integrity_passed') and
                   analysis.get('other_inputs_quiet') and
                   analysis.get('membrane', {}).get('passed') and
                   analysis.get('diagnostics', {}).get('timing_passed') and
                   analysis.get('diagnostics', {}).get('other_diagnostics_passed') and
                   bool(analysis.get('synaptic_response', {}).get('passed')) == expected)
    if not workflow_ok or bool(code == 0) != bool(report.get('all_passed')):
        raise RuntimeError('Failed workflow ' + case + ': ' + ''.join(lines))
    if missing_signal:
        assert not report['all_passed']
    return {'case': case, 'workflow_checks_passed': True,
            'expected_capture_pass': expected, 'all_passed': report['all_passed'],
            'host_receive_cadence_passed': analysis['clock']['passed'], 'channel': channel,
            'cc_binary_stream_resumed': report['cc_binary_stream_resumed']}


def main():
    output = Path(sys.argv[1]).resolve()
    output.mkdir(parents=True, exist_ok=False)
    executable = output / 'native_sketch'
    library = ROOT / 'Firmware/Librairies/Arduino-SerialCommand/src'
    subprocess.run(['g++', '-std=gnu++17', '-O2', '-ffp-contract=off', '-DARDUINO=10819',
                    '-DVC_PROTOTYPE_TEST', '-I', str(HERE / 'stubs'),
                    '-I', str(ROOT / 'Firmware/Spikeling_V3'), '-I', str(library),
                    str(HERE / 'sketch_driver.cpp'), str(library / 'SerialCommand.cpp'),
                    '-o', str(executable)], check=True)
    sys.path.insert(0, str(TOOLS))
    from run_vc_synapse_tests import CASES
    results = []
    for case in CASES:
        print('Simulated serial: ' + case, flush=True)
        results.append(exercise(executable, case, output / case))
    results.append(exercise(executable, CASES[0], output / 'synapse_two', channel=2))
    results.append(exercise(executable, CASES[0], output / 'expected_missing_signal', missing_signal=True))
    startup_fault = exercise(executable, CASES[0], output / 'expected_missing_identity',
                             drop_first_identity=True)
    summary = {'execution': 'SIMULATED IO / externally paced native clock; NOT physical ESP32 timing',
               'all_workflow_checks_passed': True,
               'all_capture_checks_as_expected': all(r['all_passed'] == r['expected_capture_pass'] for r in results),
               'results': results, 'startup_fault': startup_fault}
    (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2), flush=True)
    if not summary['all_capture_checks_as_expected']:
        print('Host cadence failures retained in raw CLI reports; workflow checks passed.', flush=True)


if __name__ == '__main__':
    main()
