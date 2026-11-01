#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Physical COM-port STP x voltage-clamp experiments (PHARMACOLOGY OFF).

Requires the integrated firmware and one presynaptic Spikeling connected to the
selected receiver synapse. VC diagnostics are enabled only during recording.
Distinguishes model agreement from transport, clamp and wall-cadence validity.
"""
import argparse
import csv
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import time
import threading

COLUMN_NAMES = ("tick time_ms command_mV voltage_mV clamp_nA capacitive_nA "
                "leak_nA input_nA flags solve_us previous_loop_us").split()
ACTIVE_EXTRA = ("sodium_nA potassium_nA receptor_nA m h n").split()
PRESETS = {0:(1.,0.,0.),1:(.15,500.,0.),2:(.4,0.,800.),3:(.25,500.,600.)}
FLAG_FAILURE_MASK = 1 | 4 | 16 | 64 | 128


def reference(mode, event_ticks, dt_ms=.1):
    """Independent analytic recurrence for event-triggered normalised gains."""
    U,tf,tr=PRESETS[mode]
    u,x,last=U,1.,None
    predicted=[]
    for tick in event_ticks:
        if last is not None:
            elapsed=(tick-last)*dt_ms
            u=U+(u-U)*math.exp(-elapsed/tf) if tf else U
            x=1-(1-x)*math.exp(-elapsed/tr) if tr else 1.
        predicted.append(u*x/U)
        if tr:x*=1-u
        if tf:u+=U*(1-u)
        last=tick
    return predicted


def decode_line(raw,backend):
    prefix=b"VC2," if backend=="active" else b"VC1,"
    if not raw.startswith(prefix):return None
    fields=COLUMN_NAMES+(ACTIVE_EXTRA if backend=="active" else [])
    parts=raw.strip().split(b",")[1:]
    if len(parts)!=len(fields):return None
    try:
        values=[float(v) for v in parts]
    except (ValueError,OverflowError):
        return None
    if not all(math.isfinite(v) for v in values):
        return None
    result=dict(zip(fields,values))
    for field in ("tick","flags"):
        if not values[fields.index(field)].is_integer() or result[field]<0:
            return None
        result[field]=int(result[field])
    return result


def extract(rows,gain,decay,mode,min_events):
    """Deconvolve per-tick synaptic decay. Reject lost/duplicated firmware ticks."""
    if len(rows)<100:
        return {"status":"INCONCLUSIVE","reason":"Fewer than 100 valid VC samples","events":[]}
    events=[]
    gaps=0
    expected_impulse=gain*.01*decay
    if not abs(expected_impulse)>0.001:
        raise ValueError("Test gain too small for reliable 6-decimal VC input diagnostics")
    threshold=max(.0005,abs(expected_impulse)*.008)
    for old,new in zip(rows,rows[1:]):
        ticks=(new["tick"]-old["tick"])%(1<<32)
        if ticks!=1:
            gaps+=1
            continue
        delta=new["input_nA"]-old["input_nA"]*decay
        if delta*expected_impulse>0 and abs(delta)>=threshold:
            events.append({"tick":new["tick"],"time_ms":new["time_ms"],
                           "measured_increment_nA":delta,
                           "measured_multiplier":delta/expected_impulse,
                           "clamp_nA":new["clamp_nA"],"voltage_mV":new["voltage_mV"]})
    predicted=reference(mode,[e["tick"] for e in events])
    for event,estimate in zip(events,predicted):
        event["predicted_multiplier"]=estimate
        event["absolute_error"]=abs(event["measured_multiplier"]-estimate)
    errors=[e["absolute_error"] for e in events]
    flags=[r["flags"] for r in rows]
    time_elapsed=rows[-1]["host_seconds"]-rows[0]["host_seconds"]
    observed_rate=(rows[-1]["tick"]-rows[0]["tick"])/time_elapsed if time_elapsed>0 else 0
    # Kirchhoff's law for the measured interval: clamp + inward input =
    # capacitive + leak + Na + K + receptor.  The ionic terms can be nonzero
    # in active VC, so clamp must NOT be tested against -inward alone.
    balance_residuals=[
        abs(r["clamp_nA"]+r["input_nA"]-r["capacitive_nA"]-r["leak_nA"]
            -r.get("sodium_nA",0.)-r.get("potassium_nA",0.)-r.get("receptor_nA",0.))
        for r in rows[len(rows)//10:]]
    balance_max=max(balance_residuals,default=float("inf"))
    flag_count={str(bit):sum(bool(f&bit) for f in flags) for bit in (1,4,16,64,128)}
    result={"status":"PASS","reason":"Valid events, current balance, VC health and wall cadence",
            "event_count":len(events),"events":events,"lost_or_duplicate_tick_pairs":gaps,
            "sample_count":len(rows),"wall_elapsed_seconds":time_elapsed,
            "observed_firmware_ticks_per_wall_second":observed_rate,
            "max_multiplier_error":max(errors,default=None),
            "max_compensation_balance_residual_nA":balance_max,
            "flag_counts":flag_count,"expected_gain_legacy_units":gain}
    if len(events)<min_events:
        result.update(status="INCONCLUSIVE",reason="Insufficient identified presynaptic spikes")
    elif gaps:
        result.update(status="INCONCLUSIVE",reason="Missing or duplicated VC diagnostic tick(s)")
    elif sum(flag_count.values()):
        result.update(status="FAIL",reason="VC compliance, solver, range, deadline or transport flag(s)")
    elif max(errors)>0.035:
        result.update(status="FAIL",reason="Measured event multipliers differ from independent STP model")
    elif not 450<=observed_rate<=550:
        result.update(status="INCONCLUSIVE",reason="Measured firmware cadence outside 500 Hz +/-10%")
    elif balance_max>.025:
        result.update(status="FAIL",reason="Compensating current inconsistent with injected input")
    elif mode==1 and not events[-1]["measured_multiplier"]>1.10:
        result.update(status="FAIL",reason="Expected facilitation not observed")
    elif mode==2 and not events[-1]["measured_multiplier"]<.95:
        result.update(status="FAIL",reason="Expected depression not observed")
    elif mode==3 and not events[1]["measured_multiplier"]>1.05:
        result.update(status="FAIL",reason="Combined STP did not facilitate initially")
    return result


def write_rows(path,rows):
    if not rows:return
    with path.open("w",newline="",encoding="utf-8") as handle:
        writer=csv.DictWriter(handle,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)


def send(port,*commands):
    for command in commands:
        port.write((command+"\n").encode("ascii"))
        port.flush()
        time.sleep(.07)


class ContinuousReader:
    """Drain serial continuously, including during operator prompts.

    Only samples received while armed enter a measurement. The reader never
    flushes the ESP32 TX buffer or silently treats old queued rows as new data.
    The same reader remains alive across STP mode changes and VC/CC cleanup.
    """
    def __init__(self,port,backend):
        self.port=port
        self.backend=backend
        self.lock=threading.Lock()
        self.stop_event=threading.Event()
        self.active=False
        self.rows=[]
        self.error=None
        self.thread=threading.Thread(target=self._read,name="stp_vc_serial_reader",daemon=True)

    def start(self):
        self.thread.start()

    def _read(self):
        while not self.stop_event.is_set():
            try:
                packet=self.port.readline(512)
                received=time.monotonic()
                row=decode_line(packet,self.backend)
            except Exception as exc:
                self.error=str(exc)
                break
            if row is None:
                continue
            row["host_seconds"]=received
            with self.lock:
                if self.active:
                    self.rows.append(row)

    def record(self,seconds):
        if self.error:
            raise RuntimeError("Background serial reader failed: "+self.error)
        with self.lock:
            self.rows=[]
            self.active=True
        time.sleep(seconds)
        with self.lock:
            self.active=False
            rows=self.rows
            self.rows=[]
        if self.error:
            raise RuntimeError("Background serial reader failed: "+self.error)
        if rows:
            first=rows[0]["host_seconds"]
            for row in rows:
                row["host_seconds"]-=first
        return rows

    def close(self):
        self.stop_event.set()
        self.thread.join(timeout=2)
        if self.thread.is_alive():
            raise RuntimeError("Background reader did not terminate; check COM-port connection")


def run(args):
    try:import serial
    except ImportError as err:
        raise SystemExit("Install pyserial: python -m pip install pyserial") from err
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    report={"port":args.port,"utc":datetime.now(timezone.utc).isoformat(),
            "backend":args.backend,"synapse":args.synapse,"gain":args.gain,
            "dt_us":2000,"seconds_per_mode":args.seconds,
            "pharmacology_enabled":False,"modes":{}}
    modes=range(4) if args.all_modes else (args.mode,)
    with serial.Serial(args.port,baudrate=500000,timeout=.25,write_timeout=2) as port:
        reader=ContinuousReader(port,args.backend)
        reader.start()                                      # Never leave binary/VC diagnostics unread during prompts
        time.sleep(1)
        try:
            send(port,"DT 2000","PH E 0","NO1 0","PG1 0","PC0",
                 "SG11 0","SG21 0","SD11 990","SD21 990",
                 f"SG{args.synapse}1 {args.gain*4:g}",
                 "VCM 1","VCA "+("1" if args.backend=="active" else "0"),
                 "VCI 1","VCMD -70","VCT 1")
            # Allow the HH gates and ADC measurements to settle at -70 mV.
            time.sleep(2)
            for mode in modes:
                print(f"Mode {mode}: centre SOURCE Patch/Stim knob and stop firing.")
                if not args.noninteractive:input("Press Enter once SOURCE has stopped ... ")
                send(port,f"STP{args.synapse} {mode}")
                # Drain old responses in the background; never discard or queue
                # UART/USB records while the operator prepares the next mode.
                time.sleep(1.0)
                print(f"Press Enter to begin the {args.seconds:g}s recording with SOURCE still stopped.")
                print("As soon as capture begins, start SOURCE at 1-3 Hz; then hold the rate steady.")
                if not args.noninteractive:input("Press Enter to start capture ... ")
                rows=reader.record(args.seconds)
                result=extract(rows,args.gain,.99,mode,args.min_events)
                name=f"syn{args.synapse}_{args.backend}_mode{mode}"
                write_rows(out/f"{name}_samples.csv",rows)
                write_rows(out/f"{name}_events.csv",result.pop("events"))
                report["modes"][str(mode)]=result
                print(f"Mode {mode}: {result['status']}, events={result.get('event_count',0)}, "
                      f"error={result.get('max_multiplier_error')}, reason={result['reason']}")
                (out/"summary.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
            statuses=[v["status"] for v in report["modes"].values()]
            report["overall_status"]="PASS" if statuses and all(v=="PASS" for v in statuses) else (
                "FAIL" if "FAIL" in statuses else "INCONCLUSIVE")
        finally:
            # Never leave the receiver in VC diagnostics, override gains or
            # non-default timing. Restores CC and the original physical knobs.
            try:
                send(port,"VCT 0","VCA 0","VCI 0","VCM 0",
                     "STP1 0","STP2 0","SG10","SG20","SD10","SD20",
                     "NO0","PG0","PC0","DT 2000")
            except Exception as exc:
                print("WARNING: serial cleanup failed:",exc)
            reader.close()
    (out/"summary.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print("Summary:",out/"summary.json")
    print("Overall:",report.get("overall_status","INCONCLUSIVE"))
    return 0 if report.get("overall_status")=="PASS" else 2


def cli():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("port",nargs="?",default="COM5")
    parser.add_argument("--synapse",type=int,choices=(1,2),default=1)
    parser.add_argument("--backend",choices=("active","passive"),default="active")
    parser.add_argument("--mode",type=int,choices=range(4),default=1)
    parser.add_argument("--all-modes",action="store_true")
    parser.add_argument("--gain",type=float,default=6.)
    parser.add_argument("--seconds",type=float,default=25.)
    parser.add_argument("--min-events",type=int,default=8)
    parser.add_argument("--output",default="STP_VC_Results")
    parser.add_argument("--noninteractive",action="store_true",
                        help="Only if source spikes are managed independently; first-event baseline may be missed")
    a=parser.parse_args()
    if a.gain==0 or abs(a.gain)<.2 or abs(a.gain)>20:
        parser.error("Set a nonzero gain with magnitude 0.2..20 legacy units")
    if a.seconds<5 or a.min_events<2:parser.error("Use >=5 seconds and >=2 events")
    raise SystemExit(run(a))


if __name__=="__main__":
    cli()
