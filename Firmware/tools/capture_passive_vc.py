#!/usr/bin/env python3
"""Capture the on-board passive RC step and check it against its analytic solution.

This script controls the connected board via USB, but never flashes firmware.
Run with the desktop GUI disconnected. Dependencies: pyserial (numpy not needed).
"""
import argparse
import csv
import math
from pathlib import Path
import time

FIELDS=['sequence','time_ms','command_mV','voltage_mV','clamp_nA','capacitive_nA',
        'leak_nA','input_nA','flags','solve_us','previous_loop_us']


def parse_sample(line):
    if not line.startswith(b'VC1,'):return None
    parts=line.decode('ascii').strip().split(',')[1:]
    if len(parts)!=len(FIELDS):raise ValueError('Incomplete VC1 record')
    row=dict(zip(FIELDS,map(float,parts)))
    if not all(math.isfinite(v) for v in row.values()):raise ValueError('Nonfinite VC record')
    return row


def validate(rows,cm_pF=20,rm=500,rs=5,el=-70,dt=.1):
    if len(rows)<3:raise ValueError('Too few samples')
    if any(int(row['flags']) for row in rows):raise ValueError('Firmware diagnostic flags are set')
    voltage=rows[0]['voltage_mV']
    vm_error=0.;current_error=0.;max_loop=0
    g=1/rm+1/rs;cm=cm_pF/1000
    z=dt*g/cm;decay=math.exp(-z);mean_factor=-math.expm1(-z)/z
    for previous,row in zip(rows,rows[1:]):
        if (int(row['sequence'])-int(previous['sequence']))%2**32!=1:
            raise ValueError('Missing or duplicated model samples')
        if abs(row['time_ms']-previous['time_ms']-dt)>1e-4:
            raise ValueError('Unexpected model-time interval')
        if int(row['flags']):raise ValueError(f"Firmware flags: {int(row['flags'])}")
        equilibrium=(row['command_mV']/rs+el/rm+row['input_nA'])/g
        avg=equilibrium+(voltage-equilibrium)*mean_factor
        voltage=equilibrium+(voltage-equilibrium)*decay
        current=(row['command_mV']-avg)/rs
        vm_error=max(vm_error,abs(voltage-row['voltage_mV']))
        current_error=max(current_error,abs(current-row['clamp_nA']))
        max_loop=max(max_loop,row['previous_loop_us'])
    if vm_error>.02 or current_error>.002:
        raise ValueError(f'RC mismatch: {vm_error:.6g} mV, {current_error:.6g} nA')
    return {'max_voltage_error_mV':vm_error,'max_current_error_nA':current_error,
            'max_previous_loop_us':max_loop,'samples':len(rows)}


def capture(port,timeout=20):
    import serial
    rows=[];seen_step=False;returned_at=None
    with serial.Serial(port,500000,timeout=.5) as stream:
        # Opening a port may reset an ESP32 board. Allow the existing boot calibration.
        time.sleep(2)
        stream.reset_input_buffer()
        stream.write(b'VCINFO\n');stream.flush()
        identity_deadline=time.monotonic()+3
        while time.monotonic()<identity_deadline:
            if b'VC-PASSIVE-1,' in stream.readline():break
        else:raise RuntimeError('Board does not identify as the passive VC prototype')
        commands=['VCM 1','VCP 20 500 5 -70','VCL -20 20','VCI 0','VCMD -70',
                  'VCT 1','VSTEP -60 10 20']
        try:
            stream.write(('\n'.join(commands)+'\n').encode('ascii'));stream.flush()
            deadline=time.monotonic()+timeout
            while time.monotonic()<deadline:
                row=parse_sample(stream.readline())
                if row is None:continue
                rows.append(row)
                if abs(row['command_mV']+60)<.01:seen_step=True
                elif seen_step and abs(row['command_mV']+70)<.01 and returned_at is None:
                    returned_at=row['time_ms']
                if returned_at is not None and row['time_ms']-returned_at>=10-.0001:break
            if returned_at is None:raise TimeoutError('No complete device-timed VC step received')
        finally:
            # Leave CC with its previous current-command/pot selection restored.
            stream.write(b'VCT 0\nVCM 0\n');stream.flush()
    return rows


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('port',help='USB serial device, e.g. COM5 or /dev/ttyACM0')
    parser.add_argument('--output',type=Path,default=Path('passive_vc.csv'))
    parser.add_argument('--timeout',type=float,default=20)
    args=parser.parse_args()
    rows=capture(args.port,args.timeout)
    with args.output.open('w',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=FIELDS);writer.writeheader();writer.writerows(rows)
    print('Saved',args.output)
    print(validate(rows))


if __name__=='__main__':main()
