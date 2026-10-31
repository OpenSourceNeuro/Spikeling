#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Active VC integration captures for the installed gates=2,voltage=2 firmware.

Never flashes firmware. Run one --case at a time; see VC_INTEGRATION_WINDOWS.md.
No cable or second board is required for this first integration stage.
"""
import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import statistics
import time

from capture_vc_inputs_v2 import (BufferedCapture, diagnostics, hold_phase,
                                 response, wait_enter, wait_for_quiet)
from run_active_vc_tests import FIELDS, identity, parse_sample, save_csv
from run_vc_hardware_tests import check_binary_stream, send
from verify_vc_clock import clock_metrics
import vc_hh_reference as reference

VERSION = '1.0'
CASES = ('09_active_noise', '10_active_photodiode', '11_patch_command',
         '12_mode_switching', '13_access_stress')
COMPONENTS = ('voltage_mV', 'clamp_nA', 'capacitive_nA', 'leak_nA',
              'sodium_nA', 'potassium_nA', 'receptor_nA')
CLEANUP = ['VCT 0', 'PH E 0', 'VCA 0', 'VCI 0', 'VCM 0', 'PC0', 'NO0', 'PG0']


def load_csv(path):
    import csv
    with path.open(newline='') as file:
        return [{k: (v if k == 'phase' else float(v)) for k, v in row.items()}
                for row in csv.DictReader(file)]


def integrity(rows):
    if len(rows) < 100:
        raise ValueError('Too few samples')
    for row in rows:
        if not all(math.isfinite(row[k]) for k in [*FIELDS, 'wall_s']):
            raise ValueError('Nonfinite sample')
        for k in ('sequence', 'flags', 'solve_us', 'previous_loop_us'):
            if row[k] < 0 or not float(row[k]).is_integer():
                raise ValueError('Invalid integer field: ' + k)
        if not -110 <= row['command_mV'] <= 80:
            raise ValueError('Command outside supported range')
    for a, b in zip(rows, rows[1:]):
        if (int(b['sequence']) - int(a['sequence'])) % 2**32 != 1:
            raise ValueError('Missing or duplicated device sample')
        if abs(b['time_ms'] - a['time_ms'] - .1) > 1e-4:
            raise ValueError('Unexpected model timestep')
        if b['wall_s'] < a['wall_s']:
            raise ValueError('PC timestamps run backwards')


def numerical(rows, steady_access=False, reserve=1.):
    errors = {k: 0. for k in COMPONENTS}
    gate_error = 0.
    if steady_access:
        # Independent coupled ODE establishes the settled finite-access state.
        # The long recording tests drift/equilibrium, not a new transient ODE
        # propagation benchmark. Case 04 separately validates transient accuracy.
        state, _ = reference.advance(reference.initial(), -20, ideal=False, dt=120.)
        expected_gates, predicted = reference.advance(state, -20, ideal=False)
    else:
        state = [rows[0][k] for k in ('voltage_mV', 'm', 'h', 'n')]
    for row in rows[1:]:
        if steady_access:
            gates = expected_gates[1:]
        else:
            state, predicted = reference.advance(state, row['command_mV'],
                inward=row['input_nA'], sodium=reserve, potassium=reserve)
            gates = state[1:]
        for k in COMPONENTS:
            errors[k] = max(errors[k], abs(row[k] - float(predicted[k])))
        gate_error = max(gate_error, *[abs(row[k] - float(v))
                        for k, v in zip(('m', 'h', 'n'), gates)])
    balance = max(abs(r['clamp_nA'] + r['input_nA'] - sum(r[k] for k in
                  ('capacitive_nA', 'leak_nA', 'sodium_nA', 'potassium_nA', 'receptor_nA')))
                  for r in rows)
    bounded = all(0 <= r[k] <= 1 for r in rows for k in ('m', 'h', 'n'))
    passed = (errors['voltage_mV'] <= .05 and gate_error <= .003 and bounded and
              balance <= .00002 and max(v for k, v in errors.items()
                                       if k != 'voltage_mV') <= .01)
    return {'passed': passed, 'max_reference_errors': errors,
            'max_gate_error': gate_error, 'max_balance_error_nA': balance,
            'reference': ('settled independent SciPy DOP853 access solution'
                          if steady_access else 'exact constant-voltage gate/product integrals')}


def patch_response(rows):
    means = {}
    for phase in ('baseline', 'active', 'recovery'):
        group = [r for r in rows if r['phase'] == phase]
        if not group:
            raise ValueError('Missing phase: ' + phase)
        settled = [r for r in group if group[0]['wall_s'] + 1 <= r['wall_s']
                   < group[-1]['wall_s'] - .5]
        if len(settled) < 100:
            raise ValueError('Too few settled samples: ' + phase)
        means[phase] = statistics.fmean(r['command_mV'] for r in settled)
    shift = means['active'] - means['baseline']
    recovered = abs(means['recovery'] - means['baseline']) <= 1.
    quiet = max(abs(r['input_nA']) for r in rows) <= .003
    tracking = max(abs(r['voltage_mV'] - r['command_mV']) for r in rows) <= .0001
    return {'passed': shift >= 5 and recovered and quiet and tracking,
            'mean_command_mV': means, 'clockwise_change_mV': shift,
            'returned_to_baseline': recovered, 'quiet_current_input': quiet,
            'ideal_voltage_tracking': tracking,
            'note': 'The Patch knob supplies Vcmd in this case, rather than injected current.'}


def assess(rows, case, seconds=60.):
    integrity(rows)
    stress = case == '13_access_stress'
    switching = case == '12_mode_switching'
    diag = diagnostics(rows)
    # Preserve both the flag-based deadline check and the measured duration.
    diag['timing_passed'] &= diag['max_previous_loop_us'] < 2000
    clock = clock_metrics(rows)
    model = numerical(rows, steady_access=stress, reserve=.5 if switching else 1.)
    fixed_command = -20 if stress or switching else -70
    command_ok = case == '11_patch_command' or all(
        abs(r['command_mV'] - fixed_command) <= .0001 for r in rows)
    if case in CASES[:2]:
        effect = response(rows, 'noise' if case == CASES[0] else 'photodiode')
    elif case == '11_patch_command':
        effect = patch_response(rows)
    else:
        quiet = max(abs(r['input_nA']) for r in rows) <= .003
        duration = rows[-1]['wall_s'] - rows[0]['wall_s']
        effect = {'passed': quiet and (not stress or duration >= seconds - .1),
                  'quiet_inputs': quiet, 'recorded_seconds': duration}
    passed = all((command_ok, model['passed'], effect['passed'], clock['passed'],
                  diag['timing_passed'], diag['other_diagnostics_passed']))
    return {'all_passed': passed, 'samples': len(rows), 'sample_integrity_passed': True,
            'command_routing_passed': command_ok, 'numerical': model,
            'response': effect, 'clock': clock, 'diagnostics': diag}


def configure(stream, case):
    commands = ['VCT 0', 'PH E 0', 'VCM 0', 'DT 2000', 'VCA 1', 'VCM 1',
                'VCP 20 500 5 -70', 'VCL -20 20', 'VCI 1', 'PC0', 'NO0', 'PG0']
    commands += [f'PH D {i} 0' for i in range(8)]
    commands += ['PH M 0', 'PH R 1 0', 'PH R 2 0', 'PH C 0', 'PH E 1']
    if case == '11_patch_command':
        commands += ['NO1 0', 'PG1 0', 'PC0']
    else:
        commands += ['VCMD -70']
    if case == '10_active_photodiode':
        commands += ['PG1 10']  # Existing serial scale: positive gain = 1.
    if case in ('12_mode_switching', '13_access_stress'):
        commands += ['NO1 0', 'PG1 0', 'VCMD -20']
    if case == '12_mode_switching':
        commands += ['PH D 0 9.2', 'PH D 1 0.5']  # Half Na/K conductance.
    if case == '13_access_stress':
        commands += ['VCI 0']
    send(stream, commands)
    return identity(stream)


def begin_capture(stream):
    stream.reset_input_buffer()
    recorder = BufferedCapture(stream, parser=parse_sample)
    recorder.start()
    send(stream, ['VCT 1'])
    return recorder


def manual_capture(recorder, case):
    if case == '09_active_noise':
        initial = 'Noise fully down; photodiode gain zero; Patch centred; incoming cables disconnected.'
        active = 'Turn Noise up moderately and leave it fixed.'
        recovery = 'Return Noise fully to minimum.'
    elif case == '10_active_photodiode':
        initial = 'Noise fully down; cover the photodiode fully with an opaque object. Positive gain is set by this test.'
        active = 'Uncover and illuminate the photodiode with steady light. Keep the light fixed.'
        recovery = 'Fully cover the photodiode again and keep it covered.'
    else:
        initial = 'Centre the Patch knob. Incoming cables disconnected; Noise and photodiode are disabled by this test.'
        active = 'Turn Patch about a quarter turn clockwise, then leave it fixed (at least a 5 mV command change).'
        recovery = 'Return Patch to its centre detent.'
    wait_enter(initial, recorder)
    wait_for_quiet(recorder)
    hold_phase(recorder, 2.1)
    start = len(recorder.rows)
    recorder.set_phase('baseline')
    hold_phase(recorder, 4.)
    recorder.set_phase('change')
    wait_enter(active, recorder)
    recorder.set_phase('active')
    hold_phase(recorder, 4.)
    recorder.set_phase('change')
    wait_enter(recovery, recorder)
    wait_for_quiet(recorder)
    recorder.set_phase('recovery')
    hold_phase(recorder, 4.)
    recorder.check()
    return list(recorder.rows[start:])


def plot(path, rows, title):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    # All samples are analysed. Downsample only the drawing of long recordings.
    chosen = rows[::max(1, len(rows) // 6000)]
    t = [r['wall_s'] - rows[0]['wall_s'] for r in chosen]
    fig, axes = plt.subplots(4, 1, figsize=(10, 10), sharex=True)
    for k, label in [('voltage_mV', 'Vm'), ('command_mV', 'Command')]:
        axes[0].plot(t, [r[k] for r in chosen], label=label)
    axes[0].set_ylabel('mV')
    for k, label in [('input_nA', 'Shared inward input'), ('clamp_nA', 'Clamp injection')]:
        axes[1].plot(t, [r[k] for r in chosen], label=label, lw=.8)
    axes[1].set_ylabel('nA')
    for k, label in [('sodium_nA', 'Na (outward +)'), ('potassium_nA', 'K (outward +)')]:
        axes[2].plot(t, [r[k] for r in chosen], label=label)
    axes[2].set_ylabel('nA')
    axes[3].plot(t, [r['previous_loop_us'] for r in chosen], label='Previous loop')
    axes[3].axhline(2000, ls='--', color='#cb4b16', label='2 ms deadline')
    flagged = [r for r in rows if int(r['flags']) & 64]
    if flagged:
        axes[3].scatter([r['wall_s'] - rows[0]['wall_s'] for r in flagged],
                        [r['previous_loop_us'] for r in flagged], color='red', label='Deadline flag')
    axes[3].set_ylabel('microseconds')
    axes[3].set_xlabel('PC receive time from capture start (s)')
    active = [r['wall_s'] - rows[0]['wall_s'] for r in rows if r['phase'] == 'active']
    for ax in axes:
        if active:
            ax.axvspan(active[0], active[-1], color='#859900', alpha=.1)
        ax.spines[['top', 'right']].set_visible(False)
        ax.legend(fontsize=8)
    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('port', nargs='?', help='e.g. COM13')
    parser.add_argument('--case', required=True, choices=CASES)
    parser.add_argument('--seconds', type=float, default=60., help='Stress duration: 10-120 wall seconds')
    parser.add_argument('--cycles', type=int, default=5, help='Mode-switch cycles: 2-20')
    parser.add_argument('--analyse', type=Path, help='Offline CSV; mode case analyses one saved VC cycle only')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--no-plots', action='store_true')
    args = parser.parse_args()
    if bool(args.port) == bool(args.analyse):
        parser.error('Supply a port OR --analyse CSV')
    if not math.isfinite(args.seconds) or not 10 <= args.seconds <= 120:
        parser.error('--seconds must be between 10 and 120')
    if not 2 <= args.cycles <= 20:
        parser.error('--cycles must be between 2 and 20')
    output = args.output or Path('vc_integration_' + datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    output.mkdir(parents=True, exist_ok=False)
    report = {'tool_version': VERSION, 'case': args.case,
              'created_utc': datetime.now(timezone.utc).isoformat(),
              'execution': 'saved CSV analysis' if args.analyse else 'live serial capture',
              'capture_results': [], 'cc_binary_stream_resumed': None if args.analyse else False,
              'scope': 'First integration stage; no synaptic receptor/release or physical TTL/DAC calibration.'}
    stream = recorder = None
    rows = []
    try:
        if not args.analyse:
            import serial
            print('Close GUI/Serial Monitor. Disconnect Current-In and both incoming synapses.', flush=True)
            stream = serial.Serial(args.port, 500000, timeout=.05, write_timeout=2)
            time.sleep(2)
            report['firmware_identity'] = configure(stream, args.case)
        count = args.cycles if args.case == '12_mode_switching' and not args.analyse else 1
        for index in range(count):
            folder = output / (f'cycle_{index+1:02}' if count > 1 else args.case)
            folder.mkdir()
            rows = []
            result = {'all_passed': False}
            try:
                if args.analyse:
                    rows = load_csv(args.analyse)
                else:
                    if args.case == '12_mode_switching':
                        # Do not resend PH settings: subsequent VC currents test
                        # whether the stored half-block doses survive each handover.
                        send(stream, ['VCA 1', 'VCM 1', 'VCI 1', 'VCMD -20'])
                    recorder = begin_capture(stream)
                    if args.case in CASES[:3]:
                        rows = manual_capture(recorder, args.case)
                    else:
                        hold_phase(recorder, 2.1)
                        start = len(recorder.rows)
                        seconds = args.seconds if args.case == '13_access_stress' else 3.3
                        print(f'Recording {seconds:g} seconds; cycle {index+1}/{count} ...', flush=True)
                        hold_phase(recorder, seconds)
                        rows = list(recorder.rows[start:])
                    result['pc_reader_metrics'] = dict(recorder.metrics)
                save_csv(folder / 'recording.csv', rows)
                result.update(assess(rows, args.case, args.seconds))
                if not args.no_plots:
                    plot(folder / 'recording.png', rows, args.case)
            except (Exception, KeyboardInterrupt) as error:
                result['error'] = str(error) or type(error).__name__
                result['all_passed'] = False
                rows = rows or (list(recorder.rows) if recorder is not None else [])
                if rows:
                    save_csv(folder / 'recording.csv', rows)
                if rows and 'diagnostics' not in result:
                    result['diagnostics'] = diagnostics(rows)
            finally:
                if recorder is not None:
                    try:
                        recorder.stop()
                        if recorder.error:
                            raise RuntimeError(recorder.error)
                    except Exception as error:
                        result['reader_error'] = str(error)
                        result['all_passed'] = False
                    recorder = None
            if stream is not None and args.case == '12_mode_switching':
                send(stream, ['VCT 0', 'VCA 0', 'VCM 0'])
                result['cc_binary_stream_resumed'] = check_binary_stream(stream)
                result['all_passed'] &= result['cc_binary_stream_resumed']
            (folder / 'report.json').write_text(json.dumps(result, indent=2) + '\n')
            report['capture_results'].append(result)
            print(('PASS' if result['all_passed'] else 'FAIL') + ' - ' + str(folder.resolve()), flush=True)
            if 'clock' in result and 'diagnostics' in result:
                d = result['diagnostics']
                print(f"Clock {result['clock']['updates_per_second']:.3f} Hz; "
                      f"max loop {d['max_previous_loop_us']:g} us; "
                      f"deadline flags {d['flag_counts']['loop_deadline']}", flush=True)
            if not result['all_passed'] and 'numerical' in result:
                print(f"Numerical={result['numerical']['passed']}; "
                      f"response={result['response']['passed']}; "
                      f"command routing={result['command_routing_passed']}", flush=True)
            if 'error' in result:
                print('Reason: ' + result['error'], flush=True)
            if not result['all_passed']:
                break
    except (Exception, KeyboardInterrupt) as error:
        report['session_error'] = str(error) or type(error).__name__
    finally:
        if recorder is not None:
            try:
                recorder.stop()
            except Exception as error:
                report['reader_cleanup_error'] = str(error)
        if stream is not None:
            try:
                send(stream, CLEANUP)
                report['cc_binary_stream_resumed'] = check_binary_stream(stream)
            except Exception as error:
                report['cleanup_error'] = str(error)
            stream.close()
        expected = args.cycles if args.case == '12_mode_switching' and not args.analyse else 1
        report['all_passed'] = (len(report['capture_results']) == expected and
            all(r['all_passed'] for r in report['capture_results']) and
            not any(k in report for k in ('session_error', 'cleanup_error', 'reader_cleanup_error')) and
            (bool(args.analyse) or report['cc_binary_stream_resumed']))
        (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print('OVERALL: ' + ('PASS' if report['all_passed'] else 'FAIL'), flush=True)
    if 'session_error' in report:
        print('Reason: ' + report['session_error'], flush=True)
    print('Results: ' + str(output.resolve()), flush=True)
    if stream is not None:
        print('Cleanup requests original CC, pharmacology OFF, and Patch/Noise/photodiode knob control.', flush=True)
    return 0 if report['all_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
