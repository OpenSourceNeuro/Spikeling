#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Linux host QA: real sketch/parser + pyserial/PTY + complete integration CLI.

SIMULATED IO AND EXTERNALLY PACED CLOCK. Not an ESP32 timing measurement.
Usage: python Firmware/tests/vc/check_integration_serial.py NEW_OUTPUT_FOLDER
Requires g++, pyserial, scipy and matplotlib. Operator actions are simulated.
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


def exercise(executable, case, output, missing_signal=False, seconds=10):
    master, slave = pty.openpty()
    tty.setraw(slave)
    port = os.ttyname(slave)
    native = subprocess.Popen([str(executable)], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    stop = threading.Event()
    actions = queue.Queue()
    errors = []

    def bridge():
        pending = b''
        noisy = False
        noise_counter = 0
        tick = time.monotonic()
        try:
            while not stop.is_set():
                while not actions.empty():
                    action = actions.get_nowait()
                    if action == 'noise_on':
                        noisy = not missing_signal
                    elif action == 'noise_off':
                        noisy = False
                        native.stdin.write(b'!NO1 0\n')
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
                            native.stdin.write(b'!' + line.strip() + b'\n')
                    native.stdin.flush()
                if native.stdout in readable:
                    data = os.read(native.stdout.fileno(), 65536)
                    if not data:
                        raise RuntimeError('Native sketch stopped')
                    os.write(master, data)
                now = time.monotonic()
                if now >= tick:
                    if noisy and noise_counter % 10 == 0:
                        value = 2 if (noise_counter // 10) % 2 else -2
                        native.stdin.write(f'!NO1 {value}\n'.encode())
                    noise_counter += 1
                    native.stdin.write(b'R1\n')
                    native.stdin.flush()
                    tick += .002
        except Exception as error:
            if not stop.is_set():
                errors.append(str(error))

    thread = threading.Thread(target=bridge, daemon=True)
    thread.start()
    args = [sys.executable, str(TOOLS / 'run_vc_integration_tests.py'), port,
            '--case', case, '--output', str(output), '--cycles', '2', '--seconds', str(seconds)]
    client = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, text=True, bufsize=1)
    lines = []

    def operator():
        for line in client.stdout:
            lines.append(line)
            if 'Turn Noise up' in line:
                actions.put('noise_on')
            elif 'Return Noise fully' in line:
                actions.put('noise_off')
            elif 'Uncover and illuminate' in line:
                actions.put('A1 5 2448')
            elif 'Fully cover the photodiode again' in line:
                actions.put('A1 5 2048')
            elif 'Turn Patch about' in line:
                actions.put('A1 6 2700')
            elif 'Return Patch to its centre' in line:
                actions.put('A1 6 2048')
            if 'Press Enter AFTER' in line:
                client.stdin.write('\n')
                client.stdin.flush()

    observer = threading.Thread(target=operator, daemon=True)
    observer.start()
    try:
        code = client.wait(timeout=100)
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
    expected = not missing_signal
    if (bool(code == 0) != expected or bool(report['all_passed']) != expected
            or not report['cc_binary_stream_resumed']):
        raise RuntimeError('Failed ' + case + ': ' + ''.join(lines))
    if missing_signal:
        assert report['capture_results'][0]['numerical']['passed']
        assert not report['capture_results'][0]['response']['passed']
    return {'case': case, 'qa_passed': True, 'expected_capture_pass': expected,
            'all_passed': report['all_passed'], 'captures': len(report['capture_results']),
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
    from run_vc_integration_tests import CASES
    results = []
    for case in CASES:
        print('Simulated serial: ' + case, flush=True)
        results.append(exercise(executable, case, output / case))
    results.append(exercise(executable, CASES[0], output / 'expected_missing_signal', missing_signal=True))
    summary = {'execution': 'SIMULATED IO / externally paced native clock; NOT physical ESP32 timing',
               'all_passed': True, 'results': results}
    (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == '__main__':
    main()
