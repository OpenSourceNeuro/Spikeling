#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Verify the clock-corrected passive VC firmware at 500 updates/second.

Requires capture_vc_inputs_v2.py and run_vc_hardware_tests.py beside this file.
Never flashes firmware. --analyse CSV checks an earlier recording offline.
"""
import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sys
import time

from capture_vc_inputs_v2 import (BufferedCapture, diagnostics, equations, hold_phase,
                                 load_csv, save_csv)
from run_vc_hardware_tests import check_binary_stream, restore_cc, send

TARGET_HZ = 500.
TOLERANCE = .02


def clock_metrics(rows):
    if len(rows) < 100:
        raise ValueError('Too few samples for a clock measurement')
    first = rows[0]['wall_s']
    duration = rows[-1]['wall_s']-first
    ticks = sum((int(r['sequence'])-int(p['sequence'])) % 2**32
                for p,r in zip(rows,rows[1:]))
    if duration <= 0:
        raise ValueError('No PC elapsed time')
    hz = ticks/duration
    windows = []
    for second in range(math.ceil(duration)):
        block = [r for r in rows if second <= r['wall_s']-first < second+1]
        if len(block) < 100:
            continue
        span = block[-1]['wall_s']-block[0]['wall_s']
        if span < .9:
            continue
        count = sum((int(r['sequence'])-int(p['sequence'])) % 2**32 for p,r in zip(block,block[1:]))
        windows.append({'start_pc_s':second, 'end_pc_s':second+1,
                        'updates_per_second':count/span})
    low,high = TARGET_HZ*(1-TOLERANCE),TARGET_HZ*(1+TOLERANCE)
    passed = low <= hz <= high and len(windows) >= 3 and all(
        low <= w['updates_per_second'] <= high for w in windows)
    return {'passed':passed, 'target_updates_per_second':TARGET_HZ,
            'relative_tolerance':TOLERANCE, 'updates_per_second':hz,
            'recorded_pc_duration_s':duration, 'device_tick_intervals':ticks,
            'duration_implied_by_2ms_ticks_s':ticks*.002,
            'windows':windows,
            'note':'PC receive timestamps measure average cadence, not oscilloscope edge jitter.'}


def require_fixed_firmware(stream):
    send(stream,['VCINFO'])
    deadline = time.monotonic()+4
    while time.monotonic() < deadline:
        line = stream.readline()
        if b'VC-PASSIVE-1,' in line:
            text = line.decode('ascii',errors='replace').strip()
            if b'clock=2' not in line.strip().split(b','):
                raise RuntimeError('Board has the older VC clock. Upload the clock-fix firmware first.')
            return text
    raise RuntimeError('No passive VC identity received; check firmware and port')


def plot_clock(path,rows,metrics):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    start = rows[0]['wall_s']
    observed = [r['wall_s']-start for r in rows]
    implied = [0.]
    for previous,row in zip(rows,rows[1:]):
        implied.append(implied[-1]+.002*((int(row['sequence'])-int(previous['sequence'])) % 2**32))
    fig,axes = plt.subplots(2,1,figsize=(9,7))
    axes[0].plot(observed,implied,color='#16798a',label='Time implied by device ticks')
    axes[0].plot(observed,observed,'--',color='#c45c47',label='Expected 1:1 relation')
    axes[0].set_xlabel('PC elapsed time (s)')
    axes[0].set_ylabel('Device ticks x 2 ms (s)')
    axes[0].legend()
    windows = metrics['windows']
    axes[1].plot([w['start_pc_s']+.5 for w in windows],
                 [w['updates_per_second'] for w in windows],'o-',color='#16798a')
    axes[1].axhline(TARGET_HZ,color='#c45c47',ls='--')
    axes[1].axhspan(490,510,color='#859900',alpha=.12,label='500 Hz +/-2% acceptance')
    axes[1].set_xlabel('PC elapsed time (s)')
    axes[1].set_ylabel('Updates per second')
    axes[1].legend()
    for ax in axes:
        ax.spines[['top','right']].set_visible(False)
    fig.suptitle('Passive VC wall-clock verification')
    fig.tight_layout()
    fig.savefig(path,dpi=160)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('port',nargs='?',help='e.g. COM13')
    parser.add_argument('--analyse',type=Path,help='Offline CSV; assumes a configured 2,000 us period')
    parser.add_argument('--output',type=Path,help='New result directory')
    parser.add_argument('--no-plots',action='store_true')
    args = parser.parse_args()
    if bool(args.port) == bool(args.analyse):
        parser.error('Supply a port OR --analyse CSV')
    output = args.output or Path('vc_clock_'+datetime.now().strftime('%Y%m%d_%H%M%S'))
    output.mkdir(parents=True,exist_ok=False)
    report = {'created_utc':datetime.now(timezone.utc).isoformat(),
              'mode':'offline' if args.analyse else 'live', 'target_period_us':2000,
              'capture_complete':False, 'cleanup_commands_sent':False,
              'cc_binary_stream_resumed':None if args.analyse else False}
    rows = []
    recorder = None
    try:
        if args.analyse:
            rows = load_csv(args.analyse)
            report['source_csv'] = str(args.analyse.resolve())
            report['capture_complete'] = True
        else:
            import serial
            print('Close GUI/serial windows. Centre Patch; minimise Noise; set PD gain to ZERO.')
            print('Disconnect Current-In and incoming synapses. Capturing ten seconds at -70 mV.',flush=True)
            with serial.Serial(args.port,500000,timeout=.05,write_timeout=2) as stream:
                time.sleep(2)
                stream.reset_input_buffer()
                report['firmware_identity'] = require_fixed_firmware(stream)
                try:
                    send(stream,['VCT 0','VCM 0','DT 2000','VCM 1','VCP 20 500 5 -70',
                                 'VCL -20 20','VCI 0','VCMD -70'])
                    require_fixed_firmware(stream)
                    stream.reset_input_buffer()
                    recorder = BufferedCapture(stream)
                    recorder.start()
                    send(stream,['VCT 1'])
                    hold_phase(recorder,10)
                    report['capture_complete'] = True
                finally:
                    try:
                        if recorder:recorder.stop()
                    finally:
                        restore_cc(stream)
                        report['cleanup_commands_sent'] = True
                        report['cc_binary_stream_resumed'] = check_binary_stream(stream)
    except (Exception,KeyboardInterrupt) as error:
        report['session_error'] = str(error) or 'Interrupted by user'
    finally:
        if recorder:
            rows = recorder.rows
            report['pc_reader_metrics'] = recorder.metrics
            if recorder.error:report['session_error'] = recorder.error
    save_csv(output/'recording.csv',rows)
    for key,function in [('clock',clock_metrics),('numerical',equations),('diagnostics',diagnostics)]:
        try:report[key] = function(rows)
        except Exception as error:report[key+'_error'] = str(error)
    quiet = bool(rows) and max(abs(r['input_nA']) for r in rows) <= .002
    report['quiet_inputs'] = quiet if not args.analyse else None
    d = report.get('diagnostics',{})
    report['all_passed'] = (report['capture_complete'] and 'session_error' not in report
                            and report.get('clock',{}).get('passed',False)
                            and report.get('numerical',{}).get('passed',False)
                            and d.get('timing_passed',False) and d.get('other_diagnostics_passed',False))
    if not args.analyse:
        report['all_passed'] &= quiet and report['cc_binary_stream_resumed']
    if rows and report.get('clock') and not args.no_plots:
        try:plot_clock(output/'clock.png',rows,report['clock'])
        except Exception as error:report['plot_error'] = str(error)
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('Results:',output.resolve())
    if report.get('clock'):
        print('Average cadence: {:.3f} updates/s (target 500)'.format(report['clock']['updates_per_second']))
        print('Clock check:', 'PASS' if report['clock']['passed'] else 'FAIL')
    if report.get('session_error'):print(report['session_error'])
    print('OVERALL:', 'PASS' if report['all_passed'] else 'FAIL - see report.json')
    return 0 if report['all_passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
