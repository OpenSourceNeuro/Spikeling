#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""On-board active VC validation. Never flashes firmware.

First run: python run_active_vc_tests.py COM13 --case 01_active_step
The remaining tools in this directory must stay beside this script.
"""
import argparse
import csv
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import time
from capture_vc_inputs_v2 import BufferedCapture, diagnostics, hold_phase
from run_vc_hardware_tests import send, check_binary_stream
from verify_vc_clock import clock_metrics
import vc_hh_reference as reference

VERSION = '1.1'
FIELDS = ['sequence','time_ms','command_mV','voltage_mV','clamp_nA','capacitive_nA',
          'leak_nA','input_nA','flags','solve_us','previous_loop_us','sodium_nA',
          'potassium_nA','receptor_nA','m','h','n']


@dataclass(frozen=True)
class Case:
    name: str
    hold: float = -70
    target: float = -20
    ideal: bool = True
    ttx_nM: float = 0
    tea_mM: float = 0
    delay: float = 10
    duration: float = 20
    post: float = 140


CASES = [Case('01_active_step'), Case('02_TTX',ttx_nM=92),
         Case('03_TEA',tea_mM=5), Case('04_access_resistance',ideal=False),
         Case('05_sodium_reversal',target=50),
         Case('06_sodium_inactivation',hold=-40),
         Case('07_above_sodium_reversal',target=60),
         Case('08_potassium_tail',hold=-20,target=-90)]


def parse_sample(line):
    if not line.startswith(b'VC2,'):
        return None
    parts = line.decode('ascii').strip().split(',')[1:]
    if len(parts) != len(FIELDS):
        raise ValueError('Incomplete VC2 record')
    row = dict(zip(FIELDS,map(float,parts)))
    if not all(math.isfinite(v) for v in row.values()):
        raise ValueError('Nonfinite VC2 record')
    for k in ('sequence','flags','solve_us','previous_loop_us'):
        if row[k] < 0 or not row[k].is_integer():
            raise ValueError('Invalid integer field '+k)
    return row


def identity(stream):
    send(stream,['VCINFO'])
    end = time.monotonic()+4
    while time.monotonic()<end:
        line = stream.readline()
        if (b'VC-ACTIVE-1,' in line and b'clock=2' in line.strip().split(b',') and
            b'gates=2' in line.strip().split(b',')):
            return line[line.index(b'VC-ACTIVE-1,'):].decode('ascii').strip()
    raise RuntimeError('No active gates=2 reply. Upload the complete timing-optimised active prototype first.')


def assess(rows, case):
    if len(rows)<100:
        raise ValueError('Too few samples')
    for a,b in zip(rows,rows[1:]):
        if (int(b['sequence'])-int(a['sequence']))%2**32 != 1:
            raise ValueError('Missing or duplicated samples')
        if abs(b['time_ms']-a['time_ms']-.1)>1e-4:
            raise ValueError('Wrong model time interval')
    pulse=[i for i,r in enumerate(rows) if abs(r['command_mV']-case.target)<1e-5]
    if not pulse or pulse[0]<2 or pulse != list(range(pulse[0],pulse[-1]+1)):
        raise ValueError('Missing baseline or a single contiguous step')
    if len(pulse)!=round(case.duration/.1) or len(rows)-pulse[-1]-1<round(case.post/.1)-1:
        raise ValueError('Wrong step duration or incomplete recovery')
    if any(min(abs(r['command_mV']-case.hold),abs(r['command_mV']-case.target))>1e-5 for r in rows):
        raise ValueError('Unexpected command voltage')
    na=1-case.ttx_nM/(9.2+case.ttx_nM)
    k=1-case.tea_mM/(.5+case.tea_mM)
    state=[rows[0][key] for key in ('voltage_mV','m','h','n')]
    names=('voltage_mV','clamp_nA','capacitive_nA','leak_nA','sodium_nA','potassium_nA','receptor_nA')
    errors={key:0. for key in names}
    gate_error=0.
    for r in rows[1:]:
        state,predicted=reference.advance(state,r['command_mV'],inward=r['input_nA'],
                                         ideal=case.ideal,sodium=na,potassium=k)
        for key in names:
            errors[key]=max(errors[key],abs(r[key]-predicted[key]))
        gate_error=max(gate_error,*[abs(r[key]-v) for key,v in zip(('m','h','n'),state[1:])])
    balance=max(abs(r['clamp_nA']+r['input_nA']-sum(r[key] for key in
                ('capacitive_nA','leak_nA','sodium_nA','potassium_nA','receptor_nA'))) for r in rows)
    quiet=max(abs(r['input_nA']) for r in rows)<=.003
    gates_bounded=all(0<=r[key]<=1 for r in rows for key in ('m','h','n'))
    numerical=(errors['voltage_mV']<=.05 and
               max(value for key,value in errors.items() if key!='voltage_mV')<=.01 and
               balance<=.00002 and gate_error<=.003 and gates_bounded)
    diag=diagnostics(rows)
    clock=clock_metrics(rows)
    on=[rows[i] for i in pulse]
    teaching={'peak_inward_sodium_nA':min(r['sodium_nA'] for r in on),
              'last_step_sodium_nA':on[-1]['sodium_nA'],
              'last_step_potassium_nA':on[-1]['potassium_nA'],
              'maximum_step_voltage_error_mV':max(abs(r['voltage_mV']-case.target) for r in on),
              'sodium_reserve':na,'potassium_reserve':k}
    shape=True
    if case.name=='01_active_step':
        peak=min(range(len(on)),key=lambda i:on[i]['sodium_nA'])
        shape=(0<peak<40 and on[peak]['sodium_nA']<-.1 and
               abs(on[-1]['sodium_nA'])<abs(on[peak]['sodium_nA'])*.1 and
               on[-1]['potassium_nA']>10*on[0]['potassium_nA'])
    elif case.name=='05_sodium_reversal':
        shape=max(abs(r['sodium_nA']) for r in on)<.00001
    elif case.name=='07_above_sodium_reversal':
        shape=max(r['sodium_nA'] for r in on)>.001
    elif case.name=='08_potassium_tail':
        shape=min(r['potassium_nA'] for r in on)<-.001
    return {'all_passed':all((quiet,numerical,shape,clock['passed'],
                             diag['timing_passed'],diag['other_diagnostics_passed'])),
            'samples':len(rows),'sample_integrity_passed':True,'quiet_inputs':quiet,
            'numerical_passed':numerical,'max_reference_errors':errors,
            'max_gate_error':gate_error,'max_balance_error_nA':balance,
            'teaching_response_passed':bool(shape),'teaching_metrics':teaching,
            'clock':clock,'diagnostics':diag,
            'reference':'exact gate/product integrals' if case.ideal else 'independent SciPy DOP853 coupled ODE'}


def capture(stream,case):
    commands=['VCT 0','PH E 0','VCM 0','VCA 1','DT 2000','VCM 1',
              'VCP 20 500 5 -70','VCL -20 20',f'VCI {int(case.ideal)}',f'VCMD {case.hold:g}']
    commands += [f'PH D {i} 0' for i in range(8)]
    commands += [f'PH D 0 {case.ttx_nM:g}',f'PH D 1 {case.tea_mM:g}',
                 'PH M 0','PH R 1 0','PH R 2 0','PH C 0','PH E 1']
    send(stream,commands)
    identity(stream)
    # Record and continuously drain USB while conditioning for 100 model ms.
    stream.reset_input_buffer()
    recorder=BufferedCapture(stream,parser=parse_sample)
    recorder.start()
    try:
        send(stream,['VCT 1'])
        hold_phase(recorder,2.1)
        start=len(recorder.rows)
        send(stream,[f'VSTEP {case.target:g} {case.delay:g} {case.duration:g}'])
        deadline=time.monotonic()+12
        while time.monotonic()<deadline:
            recorder.check()
            rows=list(recorder.rows[start:])
            pulse=[r for r in rows if abs(r['command_mV']-case.target)<1e-5]
            if pulse:
                after=[r for r in rows if r['sequence']>pulse[-1]['sequence'] and
                       abs(r['command_mV']-case.hold)<1e-5]
                if after and after[-1]['time_ms']-after[0]['time_ms']>=case.post-.1001:
                    # Keep draining USB throughout reference analysis and plots.
                    # Main owns the returned reader until this case is saved.
                    return rows,recorder.metrics,recorder
            time.sleep(.01)
        raise TimeoutError('No complete active VC pulse/recovery received')
    except BaseException as error:
        error.recorded_rows=list(recorder.rows)
        recorder.stop()
        raise


def save_csv(path,rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['wall_s','phase',*FIELDS]);w.writeheader();w.writerows(rows)


def plot(path,rows,case):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    start=next(r['time_ms']-.1 for r in rows if abs(r['command_mV']-case.target)<1e-5)
    t=[r['time_ms']-start for r in rows]
    fig,axes=plt.subplots(5,1,figsize=(10,12),sharex=True)
    axes[0].plot(t,[r['voltage_mV'] for r in rows],label='Vm')
    axes[0].plot(t,[r['command_mV'] for r in rows],'--',label='Command')
    axes[0].set_ylabel('mV');axes[0].legend()
    for key,label in [('clamp_nA','Total clamp'),('capacitive_nA','Capacitive')]:
        axes[1].plot(t,[r[key] for r in rows],label=label)
    axes[1].set_ylabel('nA');axes[1].legend()
    for key,label in [('sodium_nA','Na (outward +)'),('potassium_nA','K (outward +)'),('leak_nA','Leak')]:
        axes[2].plot(t,[r[key] for r in rows],label=label)
    axes[2].set_ylabel('nA');axes[2].legend()
    for k in ('m','h','n'):axes[3].plot(t,[r[k] for r in rows],label=k)
    axes[3].set_ylabel('Gate fraction');axes[3].legend()
    axes[4].plot(t,[r['previous_loop_us'] for r in rows],label='Previous loop')
    axes[4].axhline(2000,color='#cb4b16',ls='--',label='2 ms period')
    axes[4].set_ylabel('microseconds');axes[4].legend()
    axes[4].set_xlabel('Model time from step onset (ms); 1 model ms = 20 wall ms')
    axes[4].set_xlim(-5,case.duration+20)
    for ax in axes:
        ax.axvspan(0,case.duration,color='#859900',alpha=.08)
        ax.spines[['top','right']].set_visible(False)
    fig.suptitle(case.name+' — active educational VC')
    fig.tight_layout();fig.savefig(path,dpi=160);plt.close(fig)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('port',nargs='?',help='e.g. COM13')
    parser.add_argument('--case',choices=[c.name for c in CASES])
    parser.add_argument('--analyse',type=Path,help='Offline recording.csv; requires --case')
    parser.add_argument('--output',type=Path,help='New output folder')
    parser.add_argument('--no-plots',action='store_true')
    args=parser.parse_args()
    if not args.analyse and not args.port:parser.error('Specify COM port or --analyse')
    if args.analyse and not args.case:parser.error('--analyse requires --case')
    if args.case=='04_access_resistance' or args.case is None:
        try:import scipy
        except ImportError:parser.error('Install scipy with the same Python interpreter for access-resistance checks')
    out=args.output or Path('vc_active_'+datetime.now().strftime('%Y%m%d_%H%M%S'))
    out.mkdir(parents=True,exist_ok=False)
    cases=[c for c in CASES if not args.case or c.name==args.case]
    report={'tool_version':VERSION,'created_utc':datetime.now(timezone.utc).isoformat(),
            'mode':'offline' if args.analyse else 'live','case_results':[],
            'cc_binary_stream_resumed':False,
            'execution':'saved CSV analysis' if args.analyse else 'live serial capture'}
    stream=None;recorder=None
    try:
        if not args.analyse:
            import serial
            stream=serial.Serial(args.port,500000,timeout=.05,write_timeout=2)
            time.sleep(2)
            send(stream,['VCT 0','VCA 1']);report['firmware_identity']=identity(stream)
        for c in cases:
            print('Running '+c.name+' ...',flush=True)
            folder=out/c.name;folder.mkdir()
            rows=[];recorder=None;result={'case':asdict(c),'all_passed':False}
            try:
                if args.analyse:
                    with args.analyse.open(newline='') as f:
                        rows=[{k:(v if k=='phase' else float(v)) for k,v in r.items()} for r in csv.DictReader(f)]
                else:
                    rows,metrics,recorder=capture(stream,c);result['pc_reader_metrics']=metrics
                save_csv(folder/'recording.csv',rows)
                result.update(assess(rows,c))
            except Exception as error:
                rows=rows or getattr(error,'recorded_rows',[])
                result['error']=str(error)
                if rows:save_csv(folder/'recording.csv',rows)
            if rows and not args.no_plots:
                try:plot(folder/'recording.png',rows,c)
                except Exception as error:result['plot_error']=str(error)
            (folder/'report.json').write_text(json.dumps(result,indent=2)+'\n')
            if recorder is not None:
                recorder.stop()
                if recorder.error:
                    result['reader_error']=recorder.error
                    result['all_passed']=False
                    (folder/'report.json').write_text(json.dumps(result,indent=2)+'\n')
            report['case_results'].append(result)
            print(('  PASS' if result['all_passed'] else '  FAIL')+' — '+str(folder.resolve()),flush=True)
            if not result['all_passed']:
                print('  Checks: '+', '.join(f'{k}={result.get(k)}' for k in
                    ('sample_integrity_passed','quiet_inputs','numerical_passed','teaching_response_passed')),flush=True)
                if 'clock' in result:
                    print(f"  Clock: {result['clock']['updates_per_second']:.3f} Hz (target 500 +/-2%)",flush=True)
                if 'diagnostics' in result:
                    d=result['diagnostics']
                    print(f"  Loop: max {d['max_previous_loop_us']:g} us; deadline flags {d['flag_counts']['loop_deadline']}",flush=True)
                if 'error' in result:print('  Error: '+result['error'],flush=True)
            if not result['all_passed']:break
    except Exception as error:
        report['session_error']=str(error)
    finally:
        if recorder is not None and recorder.thread.is_alive():
            try:recorder.stop()
            except Exception as error:report['reader_cleanup_error']=str(error)
        if stream is not None:
            try:
                send(stream,['VCT 0','PH E 0','VCA 0','VCI 0','VCM 0','PC0'])
                report['cc_binary_stream_resumed']=check_binary_stream(stream)
            except Exception as error:report['cleanup_error']=str(error)
            stream.close()
        report['all_passed']=bool(report['case_results']) and len(report['case_results'])==len(cases) and all(
            r['all_passed'] for r in report['case_results']) and 'session_error' not in report and (
            bool(args.analyse) or report['cc_binary_stream_resumed'])
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('OVERALL: '+('PASS' if report['all_passed'] else 'FAIL'))
    print('Results: '+str(out.resolve()))
    if stream is not None:print('Cleanup requests original CC, pharmacology OFF, and Patch knob control; check firing in the GUI.')
    return 0 if report['all_passed'] else 1


if __name__=='__main__':raise SystemExit(main())
