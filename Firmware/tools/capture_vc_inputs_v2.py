#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""VC input capture v2: buffered background reads, confirmed phases, separate timing.

Uses VC-PASSIVE-1 firmware without flashing. Keep run_vc_hardware_tests.py beside
this file. --analyse recording.csv works offline, including recordings from v1.
"""
import argparse
import csv
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import select
import statistics
import sys
import threading
import time

from run_vc_hardware_tests import (BASE, DT, FIELDS, check_binary_stream, identity,
                                 parse_sample, reference_step, restore_cc, send)

VERSION = '2.1'
PHASE_SECONDS = 5.
FLAG_NAMES = {1: 'compliance', 2: 'rejected_command', 4: 'solver_fault',
              8: 'display_range', 16: 'packet_range', 32: 'unsupported_pharmacology',
              64: 'loop_deadline'}


def integrity(rows):
    if len(rows) < 100:
        raise ValueError('Too few samples')
    for row in rows:
        if not all(math.isfinite(row[k]) for k in [*FIELDS, 'wall_s']):
            raise ValueError('Nonfinite sample')
        for key in ('sequence', 'flags', 'solve_us', 'previous_loop_us'):
            if row[key] < 0 or not float(row[key]).is_integer():
                raise ValueError('Invalid integer field: ' + key)
        if abs(row['command_mV']+70) > 1e-5:
            raise ValueError('Command changed from -70 mV')
    for previous, row in zip(rows, rows[1:]):
        if (int(row['sequence'])-int(previous['sequence'])) % 2**32 != 1:
            raise ValueError('Missing or duplicated device samples; reference propagation cannot cross a gap')
        if abs(row['time_ms']-previous['time_ms']-DT) > 1e-4:
            raise ValueError('Unexpected model-time interval')
        if row['wall_s'] < previous['wall_s']:
            raise ValueError('PC timestamps run backwards')


def equations(rows):
    """Evaluate RC agreement independently of diagnostic flags; never clear flags."""
    integrity(rows)
    v = rows[0]['voltage_mV']
    errors = [0., 0., 0., 0.]
    balance = 0.
    for row in rows[1:]:
        expected = reference_step(v, -70, row['input_nA'], BASE)
        v = expected[0]
        for i, key in enumerate(('voltage_mV', 'clamp_nA', 'capacitive_nA', 'leak_nA')):
            errors[i] = max(errors[i], abs(row[key]-expected[i]))
        balance = max(balance, abs(row['clamp_nA']+row['input_nA']
                                  -row['capacitive_nA']-row['leak_nA']))
    return {'passed': errors[0] <= .02 and max(errors[1:]) <= .002 and balance <= .00001,
            'max_voltage_error_mV': errors[0], 'max_clamp_error_nA': errors[1],
            'max_capacitive_error_nA': errors[2], 'max_leak_error_nA': errors[3],
            'max_balance_error_nA': balance}


def diagnostics(rows):
    if not rows:
        raise ValueError('No diagnostic samples')
    counts = {name: sum(bool(int(r['flags']) & bit) for r in rows)
              for bit, name in FLAG_NAMES.items()}
    unknown = sum(bool(int(r['flags']) & ~127) for r in rows)
    events = []
    for i, row in enumerate(rows):
        if int(row['flags']) & 64 and len(events) < 50:
            events.append({'sequence': row['sequence'], 'model_time_ms': row['time_ms'],
                           'pc_time_s': row['wall_s'], 'previous_loop_us': row['previous_loop_us'],
                           'previous_solver_us': rows[i-1]['solve_us'] if i else None})
    durations = [r['previous_loop_us'] for r in rows]
    ordered = sorted(durations)
    return {'timing_passed': counts['loop_deadline'] == 0,
            'other_diagnostics_passed': unknown == 0 and not any(n for k,n in counts.items() if k != 'loop_deadline'),
            'flag_counts': counts, 'unknown_flag_samples': unknown,
            'max_previous_loop_us': max(durations, default=0),
            'median_previous_loop_us': statistics.median(durations) if durations else None,
            'p99_previous_loop_us': ordered[min(len(ordered)-1, int(.99*len(ordered)))] if ordered else None,
            'max_solver_us': max((r['solve_us'] for r in rows), default=0),
            'first_50_deadline_events': events,
            'note': 'Flag 64 is a timing failure even when the recorded RC equations agree.'}


def response(rows, kind):
    phases = {}
    for phase in ('baseline', 'active', 'recovery'):
        group = [r for r in rows if r['phase'] == phase]
        if not group:
            raise ValueError('Missing ' + phase + ' phase')
        start, end = group[0]['wall_s'], group[-1]['wall_s']
        selected = [r for r in group if start+1 <= r['wall_s'] < end-.5]
        if len(selected) < 100:
            raise ValueError('Too few settled samples in ' + phase)
        phases[phase] = {
            'samples': len(selected), 'pc_start_s': start, 'pc_end_s': end,
            'mean_input_nA': statistics.fmean(r['input_nA'] for r in selected),
            'std_input_nA': statistics.pstdev(r['input_nA'] for r in selected),
            'mean_clamp_nA': statistics.fmean(r['clamp_nA'] for r in selected),
            'std_clamp_nA': statistics.pstdev(r['clamp_nA'] for r in selected),
            'mean_voltage_mV': statistics.fmean(r['voltage_mV'] for r in selected)}
    before, active, after = (phases[p] for p in ('baseline', 'active', 'recovery'))
    quiet = all(abs(p['mean_input_nA']) <= .003 and p['std_input_nA'] <= .003 for p in (before, after))
    if kind == 'photodiode':
        present = (active['mean_input_nA']-before['mean_input_nA'] > .005
                   and active['mean_clamp_nA']-before['mean_clamp_nA'] < -.002)
        advice = 'Keep positive gain fixed; fully cover the sensor and keep it covered during recovery.'
    else:
        present = (active['std_input_nA']-before['std_input_nA'] > .005
                   and active['std_clamp_nA']-before['std_clamp_nA'] > .001)
        advice = 'Return Noise completely to minimum before confirming recovery.'
    return {'passed': quiet and present, 'active_response_detected': present,
            'quiet_baseline_and_recovery': quiet, 'phases': phases,
            'setup_advice': '' if quiet and present else advice,
            'criterion_note': 'Signal-presence thresholds; not a physiological or sensor calibration.'}


class BufferedCapture:
    """Read available byte batches on a dedicated thread throughout user prompts."""
    def __init__(self, stream, parser=parse_sample, raw_limit=0):
        self.stream = stream
        self.parser = parser
        self.rows = []
        self.error = None
        self.stop_event = threading.Event()
        self.lock = threading.Lock()
        self.phase = 'baseline'
        self.started = time.monotonic()
        self.events = [{'phase': 'baseline', 'wall_s': 0.}]
        self.metrics = {'read_calls': 0, 'bytes_read': 0, 'max_waiting_bytes': 0,
                        'max_pc_read_gap_s': 0.}
        self.raw_limit = raw_limit
        self.raw_chunk_limit = 250000
        self.raw_data = bytearray()
        self.raw_chunks = []
        if raw_limit:
            self.metrics.update(raw_bytes_truncated=0, raw_chunks_truncated=0, non_sample_lines=0)
        self.thread = threading.Thread(target=self.run, daemon=True)

    def set_phase(self, name):
        with self.lock:
            self.phase = name
            self.events.append({'phase': name, 'wall_s': time.monotonic()-self.started})

    def check(self):
        if self.error:
            raise RuntimeError(self.error)

    def start(self):
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        self.thread.join(timeout=1)
        if self.thread.is_alive():
            self.stream.cancel_read()
            self.thread.join(timeout=1)
        if self.thread.is_alive():
            raise RuntimeError('Background serial reader did not stop')

    def run(self):
        pending = bytearray()
        last_data = last_valid = time.monotonic()
        try:
            while not self.stop_event.is_set():
                waiting = self.stream.in_waiting
                self.metrics['max_waiting_bytes'] = max(self.metrics['max_waiting_bytes'], waiting)
                data = self.stream.read(min(max(waiting, 1), 65536))
                now = time.monotonic()
                self.metrics['read_calls'] += 1
                if now-self.started > 300:
                    raise TimeoutError('Recording exceeded five minutes')
                if not data:
                    if now-last_valid > 3:
                        raise TimeoutError('No complete VC samples for three seconds')
                    continue
                self.metrics['bytes_read'] += len(data)
                if self.raw_limit:
                    # Memory only on the reader thread. Disk output occurs after
                    # acquisition stops; a bounded cap never interrupts draining.
                    kept = data[:max(0, self.raw_limit-len(self.raw_data))]
                    if kept:
                        if len(self.raw_chunks) < self.raw_chunk_limit:
                            self.raw_chunks.append((now-self.started,len(self.raw_data),len(kept)))
                        else:
                            self.metrics['raw_chunks_truncated'] += 1
                        self.raw_data.extend(kept)
                    self.metrics['raw_bytes_truncated'] += len(data)-len(kept)
                self.metrics['max_pc_read_gap_s'] = max(self.metrics['max_pc_read_gap_s'], now-last_data)
                last_data = now
                pending.extend(data)
                lines = pending.split(b'\n')
                pending = bytearray(lines.pop())
                if len(pending) > 8192:
                    raise ValueError('Serial stream has no valid line framing')
                with self.lock:
                    phase = self.phase
                for line in lines:
                    row = self.parser(line)
                    if row is None and self.raw_limit:
                        self.metrics['non_sample_lines'] += 1
                    if row is not None:
                        last_valid = now
                        row['wall_s'] = now-self.started
                        row['phase'] = phase
                        self.rows.append(row)
        except Exception as error:
            self.error = str(error)


def hold_phase(recorder, seconds):
    end = time.monotonic()+seconds
    while time.monotonic() < end:
        recorder.check()
        time.sleep(.02)


def quiet_input_metrics(rows):
    if not rows:
        return None
    latest = rows[-1]['wall_s']
    recent = [r for r in rows[-2000:] if r['wall_s'] >= latest-.5]
    if len(recent) < 100 or latest-recent[0]['wall_s'] < .45:
        return None
    mean = statistics.fmean(r['input_nA'] for r in recent)
    deviation = statistics.pstdev(r['input_nA'] for r in recent)
    return {'mean_nA': mean, 'std_nA': deviation,
            'quiet': abs(mean) <= .003 and deviation <= .003}


def wait_for_quiet(recorder, timeout=30):
    print('Checking that the input is quiet before starting recovery ...', flush=True)
    end = time.monotonic()+timeout
    next_message = 0.
    while time.monotonic() < end:
        recorder.check()
        now = time.monotonic()
        metrics = quiet_input_metrics(recorder.rows)
        fresh = recorder.rows and now-recorder.started-recorder.rows[-1]['wall_s'] < .25
        if metrics and fresh and metrics['quiet']:
            return
        if metrics and now >= next_message:
            print('Input still present: mean={:+.5f} nA, std={:.5f} nA. '
                  'Keep the photodiode fully covered / Noise at minimum.'.format(
                      metrics['mean_nA'], metrics['std_nA']), flush=True)
            next_message = now+1
        time.sleep(.05)
    raise TimeoutError('Input did not become quiet: check opaque sensor covering, positive gain and Noise minimum')


def wait_enter(prompt, recorder, timeout=60):
    print('\n'+prompt, flush=True)
    print('Press Enter AFTER making the change. Recording continues while you do it.', flush=True)
    end = time.monotonic()+timeout
    # Windows console input cannot be polled with select(). msvcrt keeps the
    # main thread responsive while the acquisition thread drains USB.
    if os.name == 'nt' and sys.stdin.isatty():
        import msvcrt
        while time.monotonic() < end:
            recorder.check()
            if msvcrt.kbhit():
                char = msvcrt.getwch()
                if char == '\x03':
                    raise KeyboardInterrupt
                if char in ('\r', '\n'):
                    return
            time.sleep(.02)
    elif not sys.stdin.isatty():
        # Also supports scripted host QA with piped confirmation lines.
        recorder.check()
        if sys.stdin.readline():
            return
        raise EOFError('No operator confirmation received')
    else:
        while time.monotonic() < end:
            recorder.check()
            ready, _, _ = select.select([sys.stdin], [], [], .05)
            if ready:
                if sys.stdin.readline():
                    return
                raise EOFError('No operator confirmation received')
    raise TimeoutError('Operator confirmation timed out after 60 seconds')


def save_csv(path, rows):
    with path.open('w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['wall_s', 'phase', *FIELDS])
        writer.writeheader()
        writer.writerows(rows)


def load_csv(path):
    with path.open(newline='') as file:
        return [{**{k:float(row[k]) for k in [*FIELDS, 'wall_s']}, 'phase':row['phase']}
                for row in csv.DictReader(file)]


def plot(path, rows, kind):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(3, 1, figsize=(11, 8), sharex=True)
    t = [r['wall_s'] for r in rows]
    axes[0].plot(t, [r['voltage_mV'] for r in rows], color='#16798a', label='Vm')
    axes[0].axhline(-70, ls='--', color='#c45c47', label='Command')
    axes[0].set_ylabel('Voltage (mV)')
    axes[1].plot(t, [r['input_nA'] for r in rows], color='#c45c47', label='Input', lw=.8)
    axes[1].plot(t, [r['clamp_nA'] for r in rows], color='#16798a', label='Clamp', lw=.8)
    axes[1].set_ylabel('Current (nA)')
    axes[2].plot(t, [r['previous_loop_us'] for r in rows], color='#6c71c4', label='Previous loop')
    flagged = [r for r in rows if int(r['flags']) & 64]
    if flagged:
        axes[2].scatter([r['wall_s'] for r in flagged], [r['previous_loop_us'] for r in flagged],
                        color='#dc322f', marker='x', label='Deadline flag 64', zorder=3)
    axes[2].set_ylabel('Loop duration (us)')
    axes[2].set_ylim(bottom=0)
    axes[2].set_xlabel('PC receive time (s); active window follows recorded phase labels')
    active = [r['wall_s'] for r in rows if r['phase'] == 'active']
    for ax in axes:
        if active:
            ax.axvspan(active[0], active[-1], color='#859900', alpha=.12, label='Active phase')
        ax.spines[['top', 'right']].set_visible(False)
        ax.legend(loc='best', fontsize=8)
    fig.suptitle('Passive VC input test v2: '+kind)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def finish_report(report, rows, kind):
    report['samples'] = len(rows)
    report['sample_integrity_passed'] = False
    report['numerical_passed'] = False
    report['response_passed'] = False
    report['timing_passed'] = False
    report['other_diagnostics_passed'] = False
    try:
        integrity(rows)
        report['sample_integrity_passed'] = True
    except Exception as error:
        report['sample_integrity_error'] = str(error)
    # Preserve timing/flag evidence even if a sample is missing.
    try:
        report['diagnostics'] = diagnostics(rows)
        report['timing_passed'] = report['diagnostics']['timing_passed']
        report['other_diagnostics_passed'] = report['diagnostics']['other_diagnostics_passed']
    except Exception as error:
        report['diagnostic_error'] = str(error)
    if report['sample_integrity_passed']:
        try:
            report['numerical_metrics'] = equations(rows)
            report['numerical_passed'] = report['numerical_metrics']['passed']
        except Exception as error:
            report['numerical_error'] = str(error)
        try:
            report['response'] = response(rows, kind)
            report['response_passed'] = report['response']['passed']
        except Exception as error:
            report['response_error'] = str(error)
    required = ('sample_integrity_passed', 'numerical_passed', 'timing_passed',
                'other_diagnostics_passed', 'response_passed')
    report['all_passed'] = all(report[k] for k in required) and 'session_error' not in report
    if report['mode'] == 'live':
        report['all_passed'] &= report['capture_complete'] and report['cc_binary_stream_resumed']
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('port', nargs='?', help='e.g. COM13; omit for --analyse')
    parser.add_argument('--input', choices=('photodiode', 'noise'), dest='kind', required=True)
    parser.add_argument('--analyse', type=Path, help='Analyse a v1 or v2 CSV without connecting to a board')
    parser.add_argument('--output', type=Path, help='New output folder')
    parser.add_argument('--no-plots', action='store_true')
    args = parser.parse_args()
    if bool(args.port) == bool(args.analyse):
        parser.error('Provide a port OR --analyse CSV')
    mode = 'offline' if args.analyse else 'live'
    report = {'tool_version': VERSION, 'mode': mode, 'input': args.kind,
              'created_utc': datetime.now(timezone.utc).isoformat(),
              'expected_firmware': 'VC-PASSIVE-1', 'port': args.port,
              'parameters': {'cm_pF':20, 'rm_MOhm':500, 'rs_MOhm':5, 'el_mV':-70, 'command_mV':-70},
              'capture_complete': False, 'cleanup_commands_sent': False,
              'cc_binary_stream_resumed': None if mode == 'offline' else False,
              'note': 'Equation agreement, timing and response are independent checks; overruns still fail overall.'}
    output = args.output or Path('vc_input_v2_'+args.kind+'_'+datetime.now().strftime('%Y%m%d_%H%M%S'))
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    if mode == 'offline':
        report['source_csv'] = str(args.analyse.resolve())
        report['phase_note'] = 'Original CSV phase labels retained; v1 timed cues do not become operator confirmations.'
        try:
            rows = load_csv(args.analyse)
            report['capture_complete'] = True
        except Exception as error:
            report['session_error'] = str(error)
    else:
        try:
            import serial
        except ImportError:
            parser.error('Install pyserial with this Python interpreter')
        print('Close GUI/serial windows. Disconnect Current-In and incoming synapses. Centre Patch.')
        if args.kind == 'photodiode':
            print('Noise minimum; positive PD gain beyond its dead zone. Fully cover the photodiode.')
            print('Reset the covered board and wait three seconds. Keep gain fixed throughout.')
        else:
            print('PD gain zero; Noise at minimum. You will change only Noise when asked.')
        input('Press Enter when ready to open USB: ')
        recorder = None
        try:
            with serial.Serial(args.port, 500000, timeout=.05, write_timeout=2) as stream:
                time.sleep(2)
                stream.reset_input_buffer()
                identity(stream)
                try:
                    send(stream, ['VCT 0', 'VCM 0', 'VCM 1', 'VCP 20 500 5 -70',
                                  'VCL -20 20', 'VCI 0', 'VCMD -70'])
                    identity(stream)
                    stream.reset_input_buffer()
                    recorder = BufferedCapture(stream)
                    recorder.start()
                    send(stream, ['VCT 1'])
                    print('Recording quiet baseline for five seconds ...', flush=True)
                    hold_phase(recorder, PHASE_SECONDS)
                    recorder.set_phase('transition_to_active')
                    action = ('Uncover the sensor and shine a steady lamp on it; leave gain fixed.'
                              if args.kind == 'photodiode' else 'Raise Noise moderately, about one-quarter of its travel.')
                    wait_enter(action, recorder)
                    recorder.set_phase('active')
                    print('Recording ACTIVE input for five seconds ...', flush=True)
                    hold_phase(recorder, PHASE_SECONDS)
                    recorder.set_phase('transition_to_recovery')
                    action = ('Cover the photodiode completely and KEEP IT COVERED; leave gain fixed.'
                              if args.kind == 'photodiode' else 'Return Noise completely to MINIMUM and leave it there.')
                    wait_enter(action, recorder)
                    wait_for_quiet(recorder)
                    recorder.set_phase('recovery')
                    print('Recording quiet RECOVERY for five seconds ...', flush=True)
                    hold_phase(recorder, PHASE_SECONDS)
                    report['capture_complete'] = True
                finally:
                    # Stop the dedicated reader before asking for protocol barriers.
                    # Always try CC cleanup, even if the reader encounters an error.
                    try:
                        if recorder:
                            recorder.stop()
                    finally:
                        restore_cc(stream)
                        report['cleanup_commands_sent'] = True
                        report['cc_binary_stream_resumed'] = check_binary_stream(stream)
        except (Exception, KeyboardInterrupt) as error:
            report['session_error'] = str(error) or 'Interrupted by user'
        finally:
            if recorder:
                rows = recorder.rows
                report['phase_events'] = recorder.events
                report['pc_reader_metrics'] = recorder.metrics
                if recorder.error:
                    report['session_error'] = recorder.error
    save_csv(output/'recording.csv', rows)
    finish_report(report, rows, args.kind)
    if rows and not args.no_plots:
        try:
            plot(output/'recording.png', rows, args.kind)
        except Exception as error:
            report['plot_error'] = str(error)
    (output/'report.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print('Results:', output.resolve())
    for label, key in [('Sample continuity','sample_integrity_passed'), ('RC equations','numerical_passed'),
                       ('Loop timing','timing_passed'), ('Other firmware flags','other_diagnostics_passed'),
                       ('Input and recovery','response_passed')]:
        print(label+': '+('PASS' if report[key] else 'FAIL / CHECK REPORT'))
    print('OVERALL: '+('PASS' if report['all_passed'] else 'FAIL - see report.json'))
    if report.get('diagnostics'):
        detail = report['diagnostics']
        print('Deadline flags: {}; maximum loop: {:.0f} us'.format(
            detail['flag_counts']['loop_deadline'], detail['max_previous_loop_us']))
    if mode == 'live':
        if not report['cc_binary_stream_resumed']:
            print('CC restoration was not confirmed; reset/reconnect before opening the GUI.')
        print('Minimise Noise and zero PD gain before opening the GUI.')
    return 0 if report['all_passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
