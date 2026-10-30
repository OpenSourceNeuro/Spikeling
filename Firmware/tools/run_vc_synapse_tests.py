#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Two-Spikeling synaptic VC tests for the existing gates=2,voltage=2 firmware.

Only the postsynaptic port is opened. A second unit supplies ordinary CC axon
spikes through one stereo TRS cable. Never flashes or controls the source unit.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import time

from capture_vc_inputs_v2 import BufferedCapture, diagnostics, hold_phase, wait_enter
from run_active_vc_tests import identity, parse_sample, save_csv
from run_vc_hardware_tests import send, check_binary_stream
from run_vc_integration_tests import integrity, load_csv
from verify_vc_clock import clock_metrics
import vc_hh_reference as hh
import vc_synapse_reference as syn

VERSION = '1.0'
CASES = ('14_synaptic_input', '15_nbqx', '16_gabazine', '17_ampa_reversal',
         '18_gaba_reversal', '19_nmda_apv', '20_gvia')
CLEANUP = ['SG11 0', 'SG21 0', 'PH X', 'VCT 0', 'PH E 0', 'PH M 0',
           'PH N 0', 'PH C 0', 'VCA 0', 'VCI 0', 'VCM 0', 'PC0', 'NO0', 'PG0',
           'SG10', 'SG20', 'SD10', 'SD20']


def membrane_check(rows):
    state = [rows[0][key] for key in ('voltage_mV', 'm', 'h', 'n')]
    errors = {k: 0. for k in ('voltage_mV', 'clamp_nA', 'capacitive_nA',
                               'leak_nA', 'sodium_nA', 'potassium_nA')}
    gates = 0.
    for row in rows[1:]:
        state, predicted = hh.advance(state, row['command_mV'], inward=row['input_nA'])
        # Here HH/capacitive currents are checked independently. Receptor current
        # is separately checked against exponential event superposition below.
        predicted['clamp_nA'] += row['receptor_nA']
        for key in errors:
            errors[key] = max(errors[key], abs(row[key] - predicted[key]))
        gates = max(gates, *[abs(row[k]-v) for k, v in zip(('m', 'h', 'n'), state[1:])])
    balance = max(abs(r['clamp_nA'] + r['input_nA'] - sum(r[k] for k in
                 ('capacitive_nA', 'leak_nA', 'sodium_nA', 'potassium_nA', 'receptor_nA')))
                 for r in rows)
    bounded = all(0 <= r[k] <= 1 for r in rows for k in ('m', 'h', 'n'))
    passed = (errors['voltage_mV'] <= .05 and gates <= .003 and bounded and
              balance <= .00002 and max(v for k, v in errors.items() if k != 'voltage_mV') <= .01)
    return {'passed': bool(passed), 'max_reference_errors': errors,
            'max_gate_error': gates, 'max_balance_error_nA': balance,
            'reference': 'exact HH gate/product integrals; separate synaptic impulse-superposition fit'}


def assess(rows, case):
    integrity(rows)
    diag = diagnostics(rows)
    diag['timing_passed'] &= diag['max_previous_loop_us'] < 2000
    clock = clock_metrics(rows)
    model = membrane_check(rows)
    receptor = syn.analyse(rows, case)
    quiet = max(abs(r['input_nA']) for r in rows) <= .003
    return {'all_passed': all((diag['timing_passed'], diag['other_diagnostics_passed'],
                              clock['passed'], model['passed'], receptor['passed'], quiet)),
            'samples': len(rows), 'sample_integrity_passed': True,
            'other_inputs_quiet': quiet, 'clock': clock, 'diagnostics': diag,
            'membrane': model, 'synaptic_response': receptor}


def configure(stream, case, channel):
    config = syn.configuration(case)
    other = 3-channel
    commands = ['VCT 0', 'PH E 0', 'VCM 0', 'DT 2000', 'VCA 1', 'VCM 1',
                'VCP 20 500 5 -70', 'VCL -20 20', 'VCI 1',
                f'VCMD {syn.phases(case)[0].voltage:g}', 'NO1 0', 'PG1 0',
                'SG11 0', 'SG21 0', 'SD11 990', 'SD21 990']
    commands += [f'PH D {i} 0' for i in range(8)]
    commands += ['PH M 1', f'PH R {channel} {config["receptor_index"]}',
                 f'PH R {other} 0', 'PH G -80', f'PH N {int(config["nmda"])}',
                 f'PH C {int(config["presynaptic"])}', f'PH F {channel} 0.35',
                 'PH L 1 0', 'PH L 2 0', 'PH E 1',
                 f'SG{channel}1 {config["gain_legacy"] * 4:g}', 'PH X']
    send(stream, commands)
    return identity(stream)


def apply_phase(stream, phase):
    commands = [f'VCMD {phase.voltage:g}']
    commands += [f'PH D {i} {phase.dose if i == phase.drug else 0:g}' for i in (4, 5, 6, 7)]
    send(stream, commands)


def wait_quiet_receptor(recorder, timeout=30):
    end = time.monotonic()+timeout
    print('Waiting for the source to stop and the synaptic tail to decay ...', flush=True)
    while time.monotonic() < end:
        recorder.check()
        if recorder.rows:
            last = recorder.rows[-1]['wall_s']
            recent = [r for r in recorder.rows[-1000:] if r['wall_s'] >= last-.5]
            fresh = time.monotonic()-recorder.started-last < .25
            if (fresh and len(recent) >= 200 and
                    max(abs(r['receptor_nA']) for r in recent) <= .003 and
                    max(abs(r['input_nA']) for r in recent) <= .003):
                return
        time.sleep(.03)
    raise TimeoutError('Synaptic input remains present: centre the SOURCE Patch knob; check other inputs.')


def capture(stream, recorder, case, channel):
    wait_enter(f'SOURCE: Patch centred and no spikes. Cable: SOURCE Axon/Synapse Out -> '
               f'POSTSYNAPTIC Synapse {channel} In. Both postsynaptic synapse knobs centred.', recorder)
    wait_quiet_receptor(recorder)
    hold_phase(recorder, 2.1)
    start = len(recorder.rows)
    if case == '14_synaptic_input':
        recorder.set_phase('baseline')
        hold_phase(recorder, 4.)
    recorder.set_phase('change')
    wait_enter('SOURCE: turn its Patch knob up for steady spiking, roughly 1-3 visible '
               'spikes per second. Leave it fixed; do not move the postsynaptic knobs.', recorder)
    if case == '14_synaptic_input':
        recorder.set_phase('active')
        hold_phase(recorder, 10.)
    else:
        for phase in syn.phases(case):
            apply_phase(stream, phase)
            recorder.set_phase(phase.name)
            print(f'{phase.name}: holding {phase.voltage:g} mV for 12 seconds ...', flush=True)
            hold_phase(recorder, 12.)
    recorder.set_phase('change')
    wait_enter('SOURCE: return its Patch knob to centre so spiking stops.', recorder)
    if case != '14_synaptic_input':
        send(stream, ['VCMD -70'])
    wait_quiet_receptor(recorder)
    recorder.set_phase('recovery' if case == '14_synaptic_input' else 'post_protocol_recovery')
    hold_phase(recorder, 4.)
    recorder.check()
    return list(recorder.rows[start:])


def plot(path, rows, title):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    chosen = rows[::max(1, len(rows)//8000)]
    t = [r['wall_s']-rows[0]['wall_s'] for r in chosen]
    fig, axes = plt.subplots(5, 1, figsize=(11, 12), sharex=True)
    for key, label in [('voltage_mV', 'Vm'), ('command_mV', 'Command')]:
        axes[0].plot(t, [r[key] for r in chosen], label=label)
    axes[0].set_ylabel('mV')
    axes[1].plot(t, [r['receptor_nA'] for r in chosen], label='Synaptic current (outward +)')
    axes[1].set_ylabel('nA')
    for key, label in [('clamp_nA', 'Clamp injection (inward +)'), ('input_nA', 'Other inward inputs')]:
        axes[2].plot(t, [r[key] for r in chosen], label=label)
    axes[2].set_ylabel('nA')
    for key, label in [('sodium_nA', 'Na (outward +)'), ('potassium_nA', 'K (outward +)')]:
        axes[3].plot(t, [r[key] for r in chosen], label=label)
    axes[3].set_ylabel('nA')
    axes[4].plot(t, [r['previous_loop_us'] for r in chosen], label='Previous loop')
    axes[4].axhline(2000, color='#cb4b16', ls='--', label='2 ms deadline')
    flagged = [r for r in rows if int(r['flags']) & 64]
    if flagged:
        axes[4].scatter([r['wall_s']-rows[0]['wall_s'] for r in flagged],
                        [r['previous_loop_us'] for r in flagged], color='red', label='Deadline flag')
    axes[4].set_ylabel('microseconds')
    axes[4].set_xlabel('PC receive time from capture start (s); model runs 20 times slower than wall time')
    colors = ('#859900', '#cb4b16', '#268bd2')
    labels = list(dict.fromkeys(r['phase'] for r in rows if r['phase'] not in
                  ('baseline', 'recovery', 'change', 'setup', 'post_protocol_recovery')))
    for index, phase in enumerate(labels):
        group = [r['wall_s']-rows[0]['wall_s'] for r in rows if r['phase'] == phase]
        for ax in axes:
            ax.axvspan(group[0], group[-1], color=colors[index % len(colors)], alpha=.08)
        axes[1].text((group[0]+group[-1])/2, .98, phase, ha='center', va='top',
                     transform=axes[1].get_xaxis_transform(), fontsize=8)
    for ax in axes:
        ax.spines[['top', 'right']].set_visible(False)
        ax.legend(fontsize=8, loc='best')
    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('port', nargs='?', help='Postsynaptic port, e.g. COM13')
    parser.add_argument('--case', choices=CASES, required=True)
    parser.add_argument('--synapse', type=int, choices=(1, 2), default=1)
    parser.add_argument('--analyse', type=Path, help='Offline CSV from this case')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--no-plots', action='store_true')
    args = parser.parse_args()
    if bool(args.port) == bool(args.analyse):
        parser.error('Supply a postsynaptic port OR --analyse CSV')
    output = args.output or Path('vc_synapse_' + datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    output.mkdir(parents=True, exist_ok=False)
    report = {'tool_version': VERSION, 'case': args.case, 'synapse': args.synapse,
              'created_utc': datetime.now(timezone.utc).isoformat(),
              'execution': 'saved CSV analysis' if args.analyse else 'live serial capture',
              'settings': syn.configuration(args.case), 'capture_complete': False,
              'cc_binary_stream_resumed': None if args.analyse else False,
              'scope': 'Received deterministic events; no independent source spike count, '
                       'stochastic release-failure statistics or physical TTL/DAC calibration.'}
    rows = []
    stream = recorder = None
    try:
        if args.analyse:
            rows = load_csv(args.analyse)
        else:
            import serial
            print('Close GUI/Serial Monitor on the POSTSYNAPTIC port. The source remains in normal CC.', flush=True)
            stream = serial.Serial(args.port, 500000, timeout=.05, write_timeout=2)
            time.sleep(2)
            report['firmware_identity'] = configure(stream, args.case, args.synapse)
            recorder = BufferedCapture(stream, parser=parse_sample)
            recorder.set_phase('setup')
            recorder.start()
            send(stream, ['VCT 1'])
            rows = capture(stream, recorder, args.case, args.synapse)
            report['pc_reader_metrics'] = dict(recorder.metrics)
        report['capture_complete'] = True
        save_csv(output/'recording.csv', rows)
        report['analysis'] = assess(rows, args.case)
        if not args.no_plots:
            plot(output/'recording.png', rows, f'{args.case} - Synapse {args.synapse}')
    except (Exception, KeyboardInterrupt) as error:
        report['error'] = str(error) or type(error).__name__
        rows = rows or (list(recorder.rows) if recorder is not None else [])
        if rows:
            save_csv(output/'recording.csv', rows)
            if 'analysis' not in report:
                report['partial_diagnostics'] = diagnostics(rows)
    finally:
        if recorder is not None:
            try:
                recorder.stop()
                if recorder.error:
                    raise RuntimeError(recorder.error)
            except Exception as error:
                report['reader_error'] = str(error)
        if stream is not None:
            try:
                send(stream, CLEANUP)
                report['cc_binary_stream_resumed'] = check_binary_stream(stream)
            except Exception as error:
                report['cleanup_error'] = str(error)
            stream.close()
        report['all_passed'] = bool(report.get('analysis', {}).get('all_passed') and
            report['capture_complete'] and
            not any(k in report for k in ('error', 'reader_error', 'cleanup_error')) and
            (bool(args.analyse) or report['cc_binary_stream_resumed']))
        (output/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print('OVERALL: ' + ('PASS' if report['all_passed'] else 'FAIL'), flush=True)
    if 'analysis' in report:
        a = report['analysis']
        print(f"Clock {a['clock']['updates_per_second']:.3f} Hz; "
              f"max loop {a['diagnostics']['max_previous_loop_us']:g} us; "
              f"deadline flags {a['diagnostics']['flag_counts']['loop_deadline']}", flush=True)
        for phase, result in a['synaptic_response']['phases'].items():
            print(phase + ': ' + ('PASS' if result['passed'] else 'FAIL') +
                  (f"; resolved events {result['resolved_events']}" if 'resolved_events' in result else ''), flush=True)
    if 'error' in report:
        print('Reason: ' + report['error'], flush=True)
    print('Results: ' + str(output.resolve()), flush=True)
    if stream is not None:
        print('Cleanup requests original CC, pharmacology OFF, cleared synaptic states and normal knob control.', flush=True)
        print('Keep the SOURCE Patch centred after testing.', flush=True)
    return 0 if report['all_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
