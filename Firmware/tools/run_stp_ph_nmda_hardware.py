#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""STP x NMDA/APV hardware test, active ideal VC, COM5, deterministic release.

This is an illustrative educational conductance model test, not an independent
electrophysiological validation of NMDA receptor kinetics. The expected current
is reconstructed from the *recorded presynaptic event times* and the frozen
single-event STP and receptor equations, including NMDA rise/decay and Mg block.

SOURCE (separate Spikeling, ordinary current clamp) Axon/Syn Out -> RECEIVER
Synapse 1 via TRS. One receiver COM port; close GUI/Arduino Serial Monitor.
"""
import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import time

from run_stp_vc_hardware import ContinuousReader, reference, send, write_rows
from run_stp_ph_hardware import CASES, commands_for

DT_MS=0.1
DECAY=.990
GAIN=6.
E_AMPA=0.
E_NMDA=0.
V_HOLD=-70.
TAU_RISE_MS=4.
TAU_DECAY_MS=100.
RATIO_NMDA_AMPA=2.
MG_MM=1.
APV_IC50_UM=3.7
NBQX_IC50_UM=.30

@dataclass(frozen=True)
class NMDAProtocol:
    name: str
    nmda: bool
    apv_uM: float=0.
    nbqx_uM: float=0.

CASES_NMDA={
    "01_fast_ampa_only":NMDAProtocol("01_fast_ampa_only",False),
    "02_ampa_plus_nmda":NMDAProtocol("02_ampa_plus_nmda",True),
    "03_nmda_apv_half":NMDAProtocol("03_nmda_apv_half",True,apv_uM=3.7),
    "04_fast_nbqx_half":NMDAProtocol("04_fast_nbqx_half",True,nbqx_uM=.30),
}


def commands_for_nmda(case):
    """Begin from the tested deterministic AMPA command set, replacing N, APV and NBQX."""
    cmd=commands_for(CASES["04_ampa_conductance"])
    change={"PH N 0":f"PH N {int(case.nmda)}",
            "PH D 6 0":f"PH D 6 {case.apv_uM:g}",
            "PH D 4 0.0":f"PH D 4 {case.nbqx_uM:g}"}
    for original,replacement in change.items():
        if cmd.count(original)!=1:
            raise ValueError(f"Expected one original command: {original!r}")
        cmd[cmd.index(original)]=replacement
    return cmd


def nmdamath():
    tp=TAU_RISE_MS*TAU_DECAY_MS/(TAU_DECAY_MS-TAU_RISE_MS)*math.log(TAU_DECAY_MS/TAU_RISE_MS)
    norm=1/(math.exp(-tp/TAU_DECAY_MS)-math.exp(-tp/TAU_RISE_MS))
    mg=1/(1+(MG_MM/3.57)*math.exp(-.062*V_HOLD))
    return norm,mg


def predict_waveform(ticks, event_ticks, protocol):
    """Independent full-time-course recurrence; one update per firmware model tick.

    Fast AMPA conductance decays by .990 each step. NMDA's two unnormalised
    states decay at 4 and 100 ms respectively. Both components arise from
    the exact same facilitated event. APV blocks the NMDA output only;
    NBQX blocks the AMPA output only.
    """
    event_ticks=[int(t) for t in event_ticks]
    event_multipliers=reference(1,event_ticks)
    events=dict(zip(event_ticks,event_multipliers))
    norm,mg=nmdamath()
    r=math.exp(-DT_MS/TAU_RISE_MS)
    d=math.exp(-DT_MS/TAU_DECAY_MS)
    fb=1-protocol.nbqx_uM/(protocol.nbqx_uM+NBQX_IC50_UM) if protocol.nbqx_uM else 1.
    sb=1-protocol.apv_uM/(protocol.apv_uM+APV_IC50_UM) if protocol.apv_uM else 1.
    gfast=rise=decay=0.
    output=[]
    for tick in ticks:
        if int(tick) in events:
            increment=GAIN/(E_AMPA-V_HOLD)*events[int(tick)]
            gfast+=increment
            if protocol.nmda:
                rise+=increment*RATIO_NMDA_AMPA
                decay+=increment*RATIO_NMDA_AMPA
        gfast*=DECAY
        rise*=r
        decay*=d
        fast=fb*gfast*(E_AMPA-V_HOLD)*.01
        slow=(sb*norm*max(0.,decay-rise)*mg*(E_NMDA-V_HOLD)*.01) if protocol.nmda else 0.
        output.append({"tick":int(tick),"model_fast_nA":fast,
                       "model_nmda_nA":slow,"model_total_nA":fast+slow})
    return output


def inspect(rows, case, minimum_events=10):
    """Extract fast AMPA jumps, then validate the full slow-current waveform."""
    result={"case":case.name,"status":"INCONCLUSIVE","reason":"","samples":len(rows)}
    if len(rows)<100:result["reason"]="Insufficient VC2 samples";return result
    signal=[-row["receptor_nA"] for row in rows]
    # An NMDA event introduces only ~0.000151 nA on the event tick, much
    # smaller than the 0.0594 nA fast AMPA jump; avoid mistaking the
    # slow rising NMDA component for another presynaptic spike.
    ticks=[int(row["tick"]) for row in rows]
    events=[]
    gaps=0
    for i in range(1,len(rows)):
        if (ticks[i]-ticks[i-1])%2**32!=1:
            gaps+=1
            continue
        candidate=signal[i]-DECAY*signal[i-1]
        if candidate>0.020:
            events.append(ticks[i])
    expected=predict_waveform(ticks,events,case)
    observed=[-row["receptor_nA"] for row in rows]
    errors=[abs(row["model_total_nA"]-o) for row,o in zip(expected,observed)]
    maxerr=max(errors)
    rmse=(sum(v*v for v in errors)/len(errors))**.5
    max_balance=max(abs(r["clamp_nA"]+r["input_nA"]-
                        r["capacitive_nA"]-r["leak_nA"]-
                        r["sodium_nA"]-r["potassium_nA"]-r["receptor_nA"])
                    for r in rows)
    flags={str(bit):sum((int(row["flags"])&bit)!=0 for row in rows)
           for bit in (1,2,4,8,16,32,64,128)}
    wrong_holding=sum(abs(row["command_mV"]-V_HOLD)>1e-5 or
                      abs(row["voltage_mV"]-V_HOLD)>1e-4 for row in rows)
    elapsed=rows[-1]["host_seconds"]-rows[0]["host_seconds"]
    rate=(ticks[-1]-ticks[0])/elapsed if elapsed>0 else 0
    maxloop=max(row["previous_loop_us"] for row in rows)
    maxsolver=max(row["solve_us"] for row in rows)
    maxslow=max(row["model_nmda_nA"] for row in expected)
    result.update(
        detected_event_ticks=events,
        events=len(events),missing_or_duplicate_tick_pairs=gaps,
        max_waveform_error_nA=maxerr,root_mean_square_waveform_error_nA=rmse,
        max_predicted_nmda_component_nA=maxslow,
        maximum_current_balance_residual_nA=max_balance,
        flags=flags,bad_holding_voltage_rows=wrong_holding,
        effective_rate_hz=rate,max_loop_us=maxloop,max_solver_us=maxsolver)
    if len(events)<minimum_events:
        result["reason"]="Too few identified source events"
    elif gaps:
        result["reason"]="Missing/duplicate firmware ticks"
    elif any(flags.values()):
        result.update(status="FAIL",reason="Nonzero voltage-clamp diagnostic flags")
    elif wrong_holding:
        result.update(status="FAIL",reason="Command voltage or ideal clamp differed from -70 mV")
    elif not 450<=rate<=550:
        result["reason"]="Device tick rate inconsistent with ~500 Hz"
    elif max_balance>.0001 or maxloop>=2000:
        result.update(status="FAIL",reason="Current balance or loop deadline failed")
    elif maxerr>.0005 or rmse>.00015:
        result.update(status="FAIL",reason="Measured receptor-current waveform disagrees with AMPA+NMDA STP model")
    elif case.nmda and maxslow<.001:
        result.update(status="FAIL",reason="Expected detectable delayed NMDA component absent")
    else:
        result.update(status="PASS",reason="STP-spike timing, AMPA/NMDA waveform, blockers, timing and VC balance passed")
    return result,expected


def run(args):
    try:import serial
    except ImportError as exc:raise SystemExit("Install pyserial: python -m pip install pyserial") from exc
    folder=Path(args.output);folder.mkdir(parents=True,exist_ok=True)
    names=list(CASES_NMDA) if args.all else args.cases
    summary={"port":args.port,"generated_utc":datetime.now(timezone.utc).isoformat(),
             "firmware":"STP × pharmacology PR #19, active ideal VC, Synapse 1",
             "warning":"Aggregate VC2 records do not independently timestamp presynaptic TTL failures",
             "cases":{}}
    with serial.Serial(args.port,baudrate=500000,timeout=.15,write_timeout=2) as ser:
        reader=ContinuousReader(ser,"active")
        reader.start()
        time.sleep(1.)
        try:
            send(ser,"DT 2000","PH E 0","VCT 0","VCM 1","VCA 1","VCI 1","VCMD -70")
            for name in names:
                case=CASES_NMDA[name]
                print(f"\nCASE {name}  NMDA={case.nmda}, APV={case.apv_uM:g} uM, NBQX={case.nbqx_uM:g} uM",flush=True)
                input("STOP the presynaptic source. Press Enter to reset the receiver ... ")
                send(ser,*commands_for_nmda(case))
                time.sleep(1.5)
                input("Keep source STOPPED. Press Enter to start recording; then SOURCE 1–3 Hz ... ")
                print("RECORDING STARTED — begin source firing now",flush=True)
                rows=reader.record(args.seconds)
                result,model=inspect(rows,case,args.min_events)
                write_rows(folder/(name+"_samples.csv"),rows)
                write_rows(folder/(name+"_model.csv"),model)
                summary["cases"][name]=result
                print(f"{name}: {result['status']}, {result.get('events',0)} events, "
                      f"max waveform error {result.get('max_waveform_error_nA')} nA — {result['reason']}",flush=True)
                (folder/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
            statuses=[x["status"] for x in summary["cases"].values()]
            summary["overall_status"]="PASS" if statuses and all(x=="PASS" for x in statuses) else (
                "FAIL" if "FAIL" in statuses else "INCONCLUSIVE")
        finally:
            try:
                send(ser,"VCT 0","PH E 0","VCA 0","VCI 0","VCM 0",
                     "STP1 0","STP2 0","SG10","SG20","SD10","SD20",
                     "NO0","PG0","PC0","DT 2000")
            except Exception as exc:
                print("WARNING: could not fully restore current-clamp settings:",exc,flush=True)
            reader.close()
    (folder/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print("FINAL:",summary.get("overall_status"),"Results:",folder)
    return 0 if summary.get("overall_status")=="PASS" else 2


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("port",nargs="?",default="COM5")
    p.add_argument("--all",action="store_true",help="Run the four NMDA control/blocker protocols")
    p.add_argument("--cases",nargs="+",choices=list(CASES_NMDA),
                   default=["01_fast_ampa_only","02_ampa_plus_nmda","03_nmda_apv_half","04_fast_nbqx_half"])
    p.add_argument("--seconds",type=float,default=25.)
    p.add_argument("--min-events",type=int,default=10)
    p.add_argument("--output",default="STP_PH_NMDA_APV_COM5")
    args=p.parse_args()
    if args.seconds<12 or args.min_events<4:
        p.error("Use >=12 seconds and >=4 presynaptic events")
    raise SystemExit(run(args))


if __name__=="__main__":
    main()
