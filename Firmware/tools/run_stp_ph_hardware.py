#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""First physical STP x pharmacology validation with active voltage clamp.

Runs on the *receiver* Spikeling only. Requires a separate ordinary CC source
with Axon/Syn Out -> receiver Synapse 1 In via TRS. One serial port: COM5.
The current and conductance protocols are deterministic. Probabilistic release
is covered by native full-sketch tests but is NOT claimed as physically
validated by this script (individual failed releases are not time-stamped).
"""

import argparse
import json
import math
from pathlib import Path
import time
from datetime import datetime, timezone
from dataclasses import dataclass

from run_stp_vc_hardware import ContinuousReader, reference, send, write_rows


@dataclass(frozen=True)
class Case:
    name: str
    mode: int
    gain: float
    receptor: int
    conductance: bool = False
    nbqx: float = 0.0
    gabazine: float = 0.0
    gvia: float = 0.0
    ca_enabled: bool = False

    @property
    def release_factor(self):
        # Receptor release efficacy from unchanged frozen PH model.
        block = self.gvia/(self.gvia+10.) if self.gvia else 0.
        return (1-.35*block)**3 if self.ca_enabled else 1.

    @property
    def receptor_factor(self):
        if self.receptor == 1 and self.nbqx:
            return 1-self.nbqx/(self.nbqx+.30)
        if self.receptor == 2 and self.gabazine:
            return 1-self.gabazine/(self.gabazine+.90)
        return 1.

    @property
    def event_factor(self):
        return self.release_factor*self.receptor_factor


CASES = {
    "01_current_facilitation": Case("01_current_facilitation",1,+6.,1),
    "02_current_nbqx":         Case("02_current_nbqx",1,+6.,1,nbqx=.30),
    "03_current_gvia":         Case("03_current_gvia",1,+6.,1,gvia=10.,ca_enabled=True),
    "04_ampa_conductance":     Case("04_ampa_conductance",1,+6.,1,conductance=True),
    "05_ampa_nbqx":            Case("05_ampa_nbqx",1,+6.,1,conductance=True,nbqx=.30),
    "06_gaba_conductance":     Case("06_gaba_conductance",2,-6.,2,conductance=True),
    "07_gaba_gabazine":        Case("07_gaba_gabazine",2,-6.,2,conductance=True,gabazine=.90),
}


def assessment(rows, case, min_events=8):
    """Independent current-impulse/STP check; refuse contaminated or incomplete capture.

    The VC2 parser gives: input_nA, clamp_nA, receptor_nA, Na, K, leak,
    capacitive, flags and device tick. At ideal -70 mV conductance mode
    yields inward synaptic current = -receptor_nA. Current mode yields it
    as input_nA. Receptor blockers affect the *output* not stored activation.
    """
    report = {"case":case.name, "status":"INCONCLUSIVE", "reason":"",
              "events":[], "sample_count":len(rows)}
    if len(rows)<100:
        report["reason"]="Too few diagnostic samples"
        return report
    gain=case.gain
    decay=.990
    factor=case.event_factor
    baseline=gain*.01*decay*factor
    if abs(baseline)<.0001:
        raise ValueError("Predicted impulse is too small to identify")
    def signal(row):
        return -row["receptor_nA"] if case.conductance else row["input_nA"]

    events=[]
    gaps=0
    max_balance=0.
    flag_count={str(bit):0 for bit in (1,2,4,8,16,32,64,128)}
    max_loop=0.
    max_solver=0.
    bad_command=0
    threshold=max(.0002,abs(baseline)*.007)
    for r in rows:
        for bit in (1,2,4,8,16,32,64,128):
            if r["flags"] & bit: flag_count[str(bit)]+=1
        max_loop=max(max_loop,r["previous_loop_us"])
        max_solver=max(max_solver,r["solve_us"])
        max_balance=max(max_balance,abs(
            r["clamp_nA"] + r["input_nA"] -
            r["capacitive_nA"] - r["leak_nA"] -
            r["sodium_nA"] - r["potassium_nA"] - r["receptor_nA"]))
        if abs(r["command_mV"]+70)>1e-5 or abs(r["voltage_mV"]+70)>1e-4:
            bad_command+=1
    for prev,row in zip(rows,rows[1:]):
        delta_tick=(int(row["tick"])-int(prev["tick"])) % 2**32
        if delta_tick!=1:
            gaps+=1
            continue
        delta=signal(row)-signal(prev)*decay
        if delta*baseline > 0 and abs(delta)>threshold:
            events.append({"tick":int(row["tick"]), "time_ms":row["time_ms"],
                           "measured_event_nA":delta,
                           "multiplier_measured":delta/baseline})
    predicted=reference(case.mode,[e["tick"] for e in events])
    for event,want in zip(events,predicted):
        event["multiplier_expected"]=want
        event["error"]=abs(event["multiplier_measured"]-want)
    elapsed=rows[-1]["host_seconds"]-rows[0]["host_seconds"]
    rate=(int(rows[-1]["tick"])-int(rows[0]["tick"]))/elapsed if elapsed>0 else 0.
    max_error=max((e["error"] for e in events),default=None)
    report.update(
        events=events,event_count=len(events),
        lost_or_duplicate_tick_pairs=gaps,
        event_factor_expected=factor,
        event_peak_baseline_nA=baseline,
        max_multiplier_error=max_error,
        maximum_loop_us=max_loop,maximum_solver_us=max_solver,
        maximum_current_balance_error_nA=max_balance,
        bad_holding_voltage_rows=bad_command,
        flags=flag_count,
        effective_rate_hz=rate,
        sample_elapsed_seconds=elapsed)
    if len(events)<min_events:
        report["reason"]="Fewer than requested detected synaptic events"
    elif gaps:
        report["reason"]="One or more VC2 device ticks missing/duplicated"
    elif any(flag_count.values()):
        report.update(status="FAIL",reason="Non-zero VC2 diagnostic flags")
    elif bad_command:
        report.update(status="FAIL",reason="Command voltage or ideal holding voltage moved")
    elif not (450<=rate<=550):
        report["reason"]="USB/VC2 cadence not near 500 Hz"
    elif max_error is None or max_error>.03:
        report.update(status="FAIL",reason="Event multipliers disagree with independent STP+drug model")
    elif max_balance>.0001:
        report.update(status="FAIL",reason="Kirchhoff current balance failed")
    elif max_loop>=2000:
        report.update(status="FAIL",reason="VC update exceeded 2-ms loop period")
    else:
        report.update(status="PASS",reason="Model, polarity, pharmacological scaling, VC timing and balance passed")
    return report


def commands_for(case):
    """Set only supported short serial commands, with a fresh synaptic history.

    PH X clears pharmacological current and receptor states; STP1 explicitly
    clears the independent plasticity history. The presynaptic source MUST be
    stopped before this phase to avoid unrecorded release events.
    """
    return [
        "VCT 0",                         # Stop diagnostic stream during configuration.
        "PH E 0",                        # Disable while replacing pharmacological settings.
        "PH M "+str(int(case.conductance)),
        "PH R 1 "+str(case.receptor),
        "PH R 2 0",                      # Synapse 2 not used in this initial battery.
        "PH N 0",                        # NMDA tested separately after fast receptor path.
        "PH G -80",
        "PH C "+str(int(case.ca_enabled)),
        "PH F 1 .35",
        "PH L 1 0", "PH L 2 0",           # Deterministic release; frozen prob. tests are host-side.
        "PH D 0 0", "PH D 1 0",            # Clear intrinsic Na/K blockers from earlier sessions.
        "PH D 2 0", "PH D 3 0",            # Clear unsupported SK/A blockers to prevent VC flag 32.
        "PH D 4 "+str(case.nbqx),
        "PH D 5 "+str(case.gabazine),
        "PH D 6 0", "PH D 7 "+str(case.gvia),
        "SG11 "+f"{case.gain*4:g}",
        "SG21 0", "SD11 990", "SD21 990",
        "STP1 "+str(case.mode), "STP2 0",
        "PH E 1", "PH X",                # Clear old current tails, preserve STP mode set above.
        "VCM 1", "VCA 1", "VCI 1", "VCMD -70",
        "VCT 1",
    ]


def run(args):
    try:
        import serial
    except ImportError as exc:
        raise SystemExit("Install pyserial: python -m pip install pyserial") from exc
    output=Path(args.output)
    output.mkdir(parents=True,exist_ok=True)
    selected=list(CASES) if args.all else args.cases
    summary={"port":args.port,"utc":datetime.now(timezone.utc).isoformat(),
             "firmware":"STP+PH Stage 2 draft PR #19", "cases":{},
             "notes":"PH current/conductance deterministic release, active ideal -70 mV, Synapse 1"}
    with serial.Serial(args.port,baudrate=500000,timeout=.15,write_timeout=2) as ser:
        reader=ContinuousReader(ser,"active")
        reader.start()
        time.sleep(1)
        try:
            send(ser,"DT 2000","PH E 0","NO1 0","PG1 0",
                 "SG11 0","SG21 0","VCT 0","VCM 1","VCA 1","VCI 1","VCMD -70")
            time.sleep(.5)
            for name in selected:
                case=CASES[name]
                print(f"\nCASE {case.name}: mode={case.mode}, gain={case.gain:+g}, "
                      f"receptor={case.receptor}, conductance={case.conductance}, "
                      f"drug factor={case.event_factor:.6f}",flush=True)
                if not args.noninteractive:
                    input("STOP SOURCE firing, then press Enter to configure receiver ... ")
                send(ser,*commands_for(case))
                time.sleep(1.5)
                if not args.noninteractive:
                    input("Keep SOURCE stopped. Press Enter to start capture; then start SOURCE ~1-3 Hz ... ")
                print("RECORDING STARTED — begin SOURCE firing now",flush=True)
                rows=reader.record(args.seconds)
                result=assessment(rows,case,args.min_events)
                write_rows(output/f"{name}_samples.csv",rows)
                write_rows(output/f"{name}_events.csv",result.pop("events"))
                summary["cases"][name]=result
                print(f"{name}: {result['status']}; events={result.get('event_count',0)}; "
                      f"error={result.get('max_multiplier_error')}; reason={result['reason']}",
                      flush=True)
                (output/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
            statuses=[item["status"] for item in summary["cases"].values()]
            summary["overall_status"]="PASS" if statuses and all(v=="PASS" for v in statuses) else (
                "FAIL" if "FAIL" in statuses else "INCONCLUSIVE")
        finally:
            try:
                send(ser,"VCT 0","PH E 0","VCA 0","VCI 0","VCM 0",
                     "STP1 0","STP2 0","SG10","SG20",
                     "SD10","SD20","NO0","PG0","PC0","DT 2000")
            except Exception as exc:
                print("WARNING: could not restore receiver CC/knob controls:",exc,flush=True)
            reader.close()
    (output/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print("Results:",output/"summary.json","Overall:",summary.get("overall_status","INCONCLUSIVE"))
    return 0 if summary.get("overall_status")=="PASS" else 2


def cli():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("port",nargs="?",default="COM5")
    p.add_argument("--cases",nargs="+",choices=CASES,default=["01_current_facilitation",
                   "02_current_nbqx","03_current_gvia"])
    p.add_argument("--all",action="store_true",
                   help="Run all current, AMPA and GABA-A protocols")
    p.add_argument("--seconds",type=float,default=25.)
    p.add_argument("--min-events",type=int,default=8)
    p.add_argument("--output",default="STP_PH_Results")
    p.add_argument("--noninteractive",action="store_true",
                   help="Use only with a controlled periodic source; operator setup skipped")
    args=p.parse_args()
    if args.seconds<10 or args.min_events<3:
        p.error("Use >=10 seconds per case and >=3 events")
    raise SystemExit(run(args))


if __name__=="__main__":
    cli()
