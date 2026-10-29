#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Additional on-board tests for Spikeling VC-PASSIVE-1 (d245d07).

Never flashes firmware. Requires pyserial; matplotlib is optional with --no-plots.
"""
import argparse
import csv
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sys
import time

FIELDS = ['sequence', 'time_ms', 'command_mV', 'voltage_mV', 'clamp_nA',
          'capacitive_nA', 'leak_nA', 'input_nA', 'flags', 'solve_us', 'previous_loop_us']
IDENTITY = b'VC-PASSIVE-1,mV,ms,nA,pF,MOhm'
DT = 0.1


@dataclass(frozen=True)
class Case:
    name: str
    cm: float = 20
    rm: float = 500
    rs: float = 5
    el: float = -70
    hold: float = -70
    target: float = -60
    minimum: float = -20
    maximum: float = 20
    ideal: bool = False
    limited: bool = False
    delay: float = 10
    duration: float = 20
    post: float = 10


BASE = Case('01_baseline')
CASES = [BASE,
         replace(BASE, name='02_capacitance_100pF', cm=100),
         replace(BASE, name='03_membrane_250MOhm', rm=250),
         replace(BASE, name='04_membrane_1000MOhm', rm=1000),
         replace(BASE, name='05_access_20MOhm', rs=20),
         replace(BASE, name='06_hyperpolarising', target=-80),
         replace(BASE, name='07_ideal_clamp', ideal=True),
         replace(BASE, name='08_current_limits', minimum=-.25, maximum=.25, limited=True)]


def parse_sample(line):
    if not line.startswith(b'VC1,'):
        return None
    values = line.decode('ascii').strip().split(',')[1:]
    if len(values) != len(FIELDS):
        raise ValueError('Incomplete VC1 sample')
    row = dict(zip(FIELDS, map(float, values)))
    if not all(math.isfinite(v) for v in row.values()):
        raise ValueError('Nonfinite VC1 sample')
    for key in ('sequence', 'flags', 'solve_us', 'previous_loop_us'):
        if row[key] < 0 or not row[key].is_integer():
            raise ValueError('Invalid integer field: ' + key)
    return row


def reference_step(v, command, injected, case, dt=DT):
    """Exact RC / ideal solution; independent RK4 ODE reference for clipped access."""
    cm = case.cm / 1000
    if case.ideal:
        end = average = command
        leak = (average - case.el) / case.rm
        capacitive = cm * (end - v) / dt
        return end, capacitive + leak - injected, capacitive, leak
    if not case.limited:
        g = 1 / case.rm + 1 / case.rs
        eq = (command / case.rs + case.el / case.rm + injected) / g
        z = dt * g / cm
        end = eq + (v - eq) * math.exp(-z)
        average = eq + (v - eq) * (-math.expm1(-z)) / z
        return (end, (command - average) / case.rs,
                cm * (end - v) / dt, (average - case.el) / case.rm)
    # Integrate dV/dt = (clip((Vcmd-V)/Rs) - (V-EL)/Rm + Iin) / Cm.
    # Integrating the currents separately avoids copying the firmware's exact
    # boundary-crossing solver. A 0.001 ms substep resolves this case's dynamics.
    initial = v
    n = max(1, math.ceil(dt / .001))
    h = dt / n
    total_clamp = total_leak = 0.

    def currents(value):
        clamp = min(case.maximum, max(case.minimum, (command - value) / case.rs))
        leak = (value - case.el) / case.rm
        return (clamp - leak + injected) / cm, clamp, leak

    for _ in range(n):
        a = currents(v)
        b = currents(v + h * a[0] / 2)
        c = currents(v + h * b[0] / 2)
        d = currents(v + h * c[0])
        v += h * (a[0] + 2*b[0] + 2*c[0] + d[0]) / 6
        total_clamp += h * (a[1] + 2*b[1] + 2*c[1] + d[1]) / 6
        total_leak += h * (a[2] + 2*b[2] + 2*c[2] + d[2]) / 6
    return v, total_clamp / dt, cm * (v - initial) / dt, total_leak / dt


def validate(rows, case):
    if len(rows) < 10:
        raise ValueError('Too few samples')
    allowed_flags = 1 if case.limited else 0
    for row in rows:
        if int(row['flags']) & ~allowed_flags:
            raise ValueError('Unexpected firmware flags: ' + str(int(row['flags'])))
    pulse = [i for i, r in enumerate(rows) if abs(r['command_mV'] - case.target) < 1e-5]
    if not pulse or pulse[0] < 2 or pulse[-1] == len(rows)-1:
        raise ValueError('Missing baseline, pulse or return phase')
    if pulse != list(range(pulse[0], pulse[-1]+1)):
        raise ValueError('More than one pulse received')
    if len(pulse) != round(case.duration / DT):
        raise ValueError('Wrong device-timed pulse duration')
    if len(rows) - pulse[-1] - 1 < round(case.post / DT):
        raise ValueError('Return phase is too short')
    if any(min(abs(r['command_mV']-case.hold), abs(r['command_mV']-case.target)) > 1e-5
           for r in rows):
        raise ValueError('Unexpected voltage command')
    max_input = max(abs(r['input_nA']) for r in rows)
    if max_input > .002:
        raise ValueError('External input exceeds 0.002 nA; centre gains, minimise noise and disconnect inputs')
    voltage = rows[0]['voltage_mV']
    errors = [0., 0., 0., 0.]
    balance_error = 0.
    for previous, row in zip(rows, rows[1:]):
        if (int(row['sequence']) - int(previous['sequence'])) % 2**32 != 1:
            raise ValueError('Missing or duplicated model samples')
        if abs(row['time_ms'] - previous['time_ms'] - DT) > 1e-4:
            raise ValueError('Unexpected model-time interval; expected 0.1 ms')
        expected = reference_step(voltage, row['command_mV'], row['input_nA'], case)
        voltage = expected[0]
        for j, key in enumerate(('voltage_mV', 'clamp_nA', 'capacitive_nA', 'leak_nA')):
            errors[j] = max(errors[j], abs(row[key] - expected[j]))
        balance_error = max(balance_error, abs(row['clamp_nA'] + row['input_nA']
                            - row['capacitive_nA'] - row['leak_nA']))
        if not case.ideal and not (case.minimum-.002 <= row['clamp_nA'] <= case.maximum+.002):
            raise ValueError('Recorded clamp current exceeds the configured limits')
    if errors[0] > .02 or max(errors[1:]) > .002 or balance_error > .00001:
        raise ValueError('Reference mismatch (Vm, Iclamp, Icap, Ileak): ' + str(errors))
    if case.limited:
        onset = rows[pulse[0]:pulse[-1]+1]
        returned = rows[pulse[-1]+1:]
        if not any(int(r['flags']) & 1 and r['clamp_nA'] > 0 for r in onset):
            raise ValueError('Positive current compliance was not exercised')
        if not any(int(r['flags']) & 1 and r['clamp_nA'] < 0 for r in returned):
            raise ValueError('Negative current compliance was not exercised')
        if any(int(r['flags']) & 1 for r in onset[-20:] + returned[-20:]):
            raise ValueError('Compliance did not clear after settling')
    steady = rows[pulse[-1]-19:pulse[-1]+1]
    mean = lambda key: sum(r[key] for r in steady) / len(steady)
    eq = (case.target/case.rs + case.el/case.rm) / (1/case.rs + 1/case.rm)
    return {
        'samples': len(rows), 'pulse_samples': len(pulse),
        'max_voltage_error_mV': errors[0], 'max_clamp_error_nA': errors[1],
        'max_capacitive_error_nA': errors[2], 'max_leak_error_nA': errors[3],
        'max_balance_error_nA': balance_error,
        'max_previous_loop_us': max(r['previous_loop_us'] for r in rows),
        'max_solver_us': max(r['solve_us'] for r in rows),
        'max_input_nA': max_input,
        'compliance_samples': sum(bool(int(r['flags']) & 1) for r in rows),
        'steady_voltage_mV': mean('voltage_mV'), 'steady_clamp_nA': mean('clamp_nA'),
        'zero_input_expected_steady_voltage_mV': case.target if case.ideal else eq,
        'zero_input_expected_steady_clamp_nA': (case.target-case.el)/case.rm if case.ideal else (eq-case.el)/case.rm,
        'unlimited_access_tau_ms': 0 if case.ideal else (case.cm/1000)/(1/case.rm+1/case.rs),
        'note': 'Current-limited onset is not a single exponential.' if case.limited else ''}


def send(stream, commands):
    data = ('\n'.join(commands) + '\n').encode('ascii')
    if any(len(c) > 31 for c in commands):
        raise ValueError('Command exceeds firmware buffer')
    stream.write(data)
    stream.flush()


def identity(stream, timeout=4):
    send(stream, ['VCINFO'])
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if IDENTITY in stream.readline():
            return
    raise RuntimeError('Board did not identify as VC-PASSIVE-1; check port and firmware')


def capture_case(stream, case, timeout=20):
    send(stream, ['VCT 0', 'VCM 0', 'VCM 1',
                  f'VCP {case.cm:g} {case.rm:g} {case.rs:g} {case.el:g}',
                  f'VCL {case.minimum:g} {case.maximum:g}',
                  f'VCI {int(case.ideal)}', f'VCMD {case.hold:g}'])
    identity(stream)  # Commands were processed; the reply also drains preceding output.
    stream.reset_input_buffer()
    send(stream, ['VCT 1', f'VSTEP {case.target:g} {case.delay:g} {case.duration:g}'])
    rows = []
    stepped = False
    returned_at = None
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        row = parse_sample(stream.readline())
        if row is None:
            continue
        rows.append(row)
        if abs(row['command_mV'] - case.target) < 1e-5:
            stepped = True
        elif stepped and abs(row['command_mV'] - case.hold) < 1e-5 and returned_at is None:
            returned_at = row['time_ms']
        if returned_at is not None and row['time_ms'] - returned_at >= case.post - DT - .0001:
            return rows
    raise TimeoutError('No complete device-timed pulse received; check the connection')


def restore_cc(stream):
    # Restore the normal passive defaults as well as the saved CC knob/command selection.
    send(stream, ['VCT 0', 'VCMD -70', 'VCP 20 500 5 -70', 'VCL -20 20', 'VCI 0', 'VCM 0'])


def check_binary_stream(stream, timeout=2):
    """Check stream resumption only; actual CC firing/TTL still needs a bench check."""
    stream.reset_input_buffer()
    send(stream, ['VCINFO'])  # Barrier after cleanup; does not change the mode.
    deadline = time.monotonic() + timeout
    data = bytearray()
    seen_identity = False
    while time.monotonic() < deadline:
        data.extend(stream.read(256))
        if not seen_identity:
            offset = data.find(IDENTITY)
            if offset < 0:
                continue
            end = data.find(b'\n', offset)
            if end < 0:
                continue
            del data[:end+1]
            seen_identity = True
        for offset in range(max(0, len(data)-55)):
            if all(data[offset+k:offset+k+2] == b'\xaa\x55' for k in (0, 18, 36)):
                return True
    return False


def save_csv(path, rows):
    with path.open('w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def plot_case(path, rows, case):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    t = [r['time_ms'] - rows[0]['time_ms'] + DT for r in rows]
    onset = next(i for i, r in enumerate(rows) if abs(r['command_mV']-case.target)<1e-5)
    start = t[onset] - DT
    fig, axes = plt.subplots(2, 2, figsize=(10, 7))
    for col in range(2):
        axes[0, col].step(t, [r['command_mV'] for r in rows], where='pre', ls='--', color='#c45c47', label='Command')
        axes[0, col].plot(t, [r['voltage_mV'] for r in rows], color='#16798a', label='Vm')
        axes[0, col].set_ylabel('Voltage (mV)')
        for key, label, colour in [('clamp_nA', 'Clamp', '#16798a'),
                                   ('capacitive_nA', 'Capacitive', '#6c71c4'),
                                   ('leak_nA', 'Leak', '#c45c47')]:
            axes[1, col].step(t, [r[key] for r in rows], where='pre', label=label, color=colour)
        axes[1, col].set_ylabel('Current (nA)')
        for row in range(2):
            axes[row, col].set_xlabel('Model time since capture start (ms)')
            axes[row, col].legend(fontsize=8)
            axes[row, col].spines[['top', 'right']].set_visible(False)
            if col:
                axes[row, col].set_xlim(start-.2, start+3)
    axes[0, 0].set_title('Complete protocol')
    axes[0, 1].set_title('Step onset')
    fig.suptitle(f'{case.name}: Cm={case.cm:g} pF, Rm={case.rm:g} MOhm, Rs={case.rs:g} MOhm')
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('port', nargs='?', help='e.g. COM13')
    parser.add_argument('--output', type=Path, help='New results folder; default includes timestamp')
    parser.add_argument('--case', choices=[c.name for c in CASES], help='Run one case only')
    parser.add_argument('--list', action='store_true', help='List cases without connecting')
    parser.add_argument('--no-plots', action='store_true')
    parser.add_argument('--timeout', type=float, default=20, help='Seconds per capture')
    args = parser.parse_args()
    if args.list:
        for case in CASES:
            print(case.name)
        return 0
    if not args.port:
        parser.error('A serial port is required')
    try:
        import serial
    except ImportError:
        parser.error('Install pyserial with this Python interpreter')
    cases = [c for c in CASES if not args.case or c.name == args.case]
    output = args.output or Path('vc_results_' + datetime.now().strftime('%Y%m%d_%H%M%S'))
    output.mkdir(parents=True, exist_ok=False)
    report = {'created_utc': datetime.now(timezone.utc).isoformat(),
              'firmware_identity': IDENTITY.decode(), 'expected_firmware_commit': 'd245d07223576f448609895f80bea5717c5cd7fd',
              'port': args.port, 'model_dt_ms': DT, 'cases': [],
              'cc_binary_stream_resumed': False, 'cleanup_commands_sent': False,
              'scope': 'On-board passive dynamics and serial transport; no analogue or TTL certification.'}
    identified = False
    failure = None
    try:
        with serial.Serial(args.port, 500000, timeout=.2, write_timeout=2) as stream:
            time.sleep(2)
            stream.reset_input_buffer()
            identity(stream)
            identified = True
            try:
                for case in cases:
                    print('Running ' + case.name + ' ...', flush=True)
                    record = {'name': case.name, 'parameters': asdict(case), 'status': 'FAIL'}
                    report['cases'].append(record)
                    try:
                        rows = capture_case(stream, case, args.timeout)
                        # Stop CSV streaming before reference calculations or plotting:
                        # a paused PC reader must not stall the board's USB transmitter.
                        send(stream, ['VCT 0', 'VCM 0'])
                        identity(stream)
                        save_csv(output / (case.name + '.csv'), rows)
                        record['metrics'] = validate(rows, case)
                        record['status'] = 'PASS'
                        print('  PASS: max Vm error={:.6g} mV; max loop={:.0f} us'.format(
                            record['metrics']['max_voltage_error_mV'], record['metrics']['max_previous_loop_us']), flush=True)
                        if not args.no_plots:
                            try:
                                plot_case(output / (case.name + '.png'), rows, case)
                            except Exception as error:
                                record['plot_error'] = str(error)
                                print('  Plot failed; CSV retained: ' + str(error), flush=True)
                    except Exception as error:
                        record['error'] = str(error)
                        print('  FAIL: ' + str(error), flush=True)
                        # Do not hide a broken port or an unsafe-to-interpret partial session
                        # behind later cases. Diagnostic failures are preserved in report.json.
                        break
            finally:
                restore_cc(stream)
                report['cleanup_commands_sent'] = True
                report['cc_binary_stream_resumed'] = check_binary_stream(stream)
    except (Exception, KeyboardInterrupt) as error:
        failure = str(error) or 'Interrupted by user'
        report['session_error'] = failure
    report['all_passed'] = (failure is None and len(report['cases']) == len(cases)
                            and all(r['status'] == 'PASS' for r in report['cases'])
                            and report['cc_binary_stream_resumed'])
    report['plotting_complete'] = args.no_plots or all('plot_error' not in r for r in report['cases'])
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('Results: ' + str(output.resolve()))
    print('OVERALL: ' + ('PASS' if report['all_passed'] else 'FAIL'))
    if not report['cleanup_commands_sent'] and identified:
        print('Cleanup could not be confirmed. Reconnect/reset the board before using the GUI.')
    if failure:
        print(failure, file=sys.stderr)
    if report['all_passed']:
        print('CC binary stream resumed. Check normal knob-controlled firing in the GUI next.')
    return 0 if report['all_passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
