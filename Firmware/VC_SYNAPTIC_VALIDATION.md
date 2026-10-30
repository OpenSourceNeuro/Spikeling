# Synaptic VC test pack — validation and scope

30 October 2026. Physical captures below use the `5c2e063` active firmware.
The subsequent opt-in diagnostic revision adds stage timing and serial-write
evidence; it does not change model equations or numerical/timing thresholds.
The user has confirmed access to a second Spikeling and a stereo TRS cable.
The first requested physical capture is `14_synaptic_input --synapse 1` on COM13.
Basic Synapse 1 and Synapse 2 now have verified passing physical captures
(see below). Case 15 also has a verified passing NBQX repeat; its first timing
FAIL remains recorded and unresolved. Case 16 gabazine also has a verified
passing capture. Case 17 AMPA reversal now also passes. Case 18 GABA-A
reversal now also passes. Case 19 NMDA/APV also passes, with selective slow
component block and preserved fast AMPA. Case 20 GVIA now has four operator
FAILs (three loop-deadline failures and one sequence-integrity failure), now
confirmed by independent CSV/report review, followed by one verified PASS on
the instrumented 3d78f06 firmware. Earlier failures remain unresolved. Next is
one pre-defined extended diagnostic capture using that installed firmware;
see VC_EXTENDED_DIAGNOSTICS_WINDOWS.md and the evidence below.

## Protocol and independent reference

The source stays in normal Izhikevich CC; only the postsynaptic serial port is
opened. Its ordinary axon spikes enter one selected synaptic input. Serial gain,
decay, receptor, holding voltage and doses are explicit. The unused synapse,
noise and photodiode are disabled; Current-In is physically disconnected.
Cleanup clears synaptic state, disables pharmacology and restores original CC
and knob controls. A background reader remains active through operator prompts,
analysis and plotting, with partial CSV/report preservation on failures.

`vc_synapse_reference.py` models fast exponential impulse superposition and
fits a separate slow biexponential NMDA coefficient using linear least squares.
Initial latent exponentials permit tails from before each analysis window.
It uses analytic decay constants rather than calling the firmware receptor
update. Its fixed-voltage conductance relation is `I = g(V-E)`.

The AMPA calibration is 0.0014285714 uS per received event; GABA-A is 0.010 uS.
Both fast states decay by 0.99 per 0.1 model-ms outer tick, corresponding to a
9.9499 model-ms time constant. First-bin AMPA at -70 mV is -0.099 nA; GABA-A at
-70 mV with E_GABA=-80 mV is +0.099 nA. Conductances and synaptic states update
once per outer tick, as in the existing firmware, not once per HH substep.
NMDA uses 4/100 model-ms rise/decay, gain ratio 2 and 1 mM magnesium. Holding at
-20 mV retains nonzero fast AMPA as the event marker while allowing NMDA current.

The HH/gate/capacitive reference remains independent. At ideal clamp, receptor
current does not alter Vm; the HH check adds measured receptor current to the
independent predicted clamp balance. This alone is not a receptor validation:
the separate exponential reference must also pass. Deliberate double-counting
of receptor current in the clamp trace fails the membrane/balance check.

Events are inferred from sign-correct jumps of the fast current. Each analysed
active phase needs at least five resolved events, intervals of at least 100 ms
wall time, sufficient settled samples, full fit rank, correct command and signed
amplitudes, and a maximum waveform residual of 0.00002 nA. Fast amplitude tolerance
is 2% (floor 0.000005 nA); slow NMDA tolerance is 5% (floor 0.00001 nA).
These are software agreement criteria, not experimental noise specifications.

Reversal fits use three nonzero-driving-force voltages with received events on
both sides. The zero crossing must be within 1 mV of the selected reversal.
Drug tests compare per-event control/drug/washout coefficients; ratio tolerances
are +/-0.04. NBQX/gabazine/APV use the existing educational half-effect doses;
GVIA uses deterministic `(1-0.35*0.5)^3 = 0.561515625` event efficacy. APV must
preserve the fast AMPA coefficient while reducing NMDA. A changing event rate
therefore cannot, by itself, satisfy a drug-block criterion.

No independent source spike count is present in VC2. These tests cannot prove
that every emitted physical spike was received, nor measure release failures.
A nominally zero current at reversal is not treated as proof of an input event.
Stochastic release, STP/LTP and hidden-state handover tests need other observables.

The existing checks are retained: contiguous sequence/model time, finite values,
500 Hz +/-2% overall and in complete one-second PC receive windows, all diagnostic
flags zero, every recorded previous-loop duration below 2,000 us, bounded gates,
Vm reference error <=0.05 mV, current reference errors <=0.01 nA and balance error
<=0.00002 nA. Input current outside the receptor pathway must stay within 0.003 nA.
Native timing fields are zero/test doubles and do not qualify ESP32 execution.

## Native regression tests

```sh
python -m unittest discover -s Firmware/tests/vc -v
```

**100 tests pass** (33.629 s): the previous 84 plus 16 new tests in
`Firmware/tests/vc/test_vc_synapses.py`. The actual sketch and vendored serial
parser are compiled with g++; ADC/GPIO/clock/serial IO are simulated.

Positive cases cover Synapse 1 and 2, both receptor reversals, NBQX/gabazine,
separate AMPA/NMDA with APV, and single-application GVIA scaling. Fault cases cover
absent input with otherwise correct membrane physics, absent drug effect,
missing NMDA, excessive source rate, double-counted clamp current, missed deadline
or long loop, sample gaps and wrong cadence. No synthetic pass is substituted
for a physical board recording.

## Complete CLI serial QA

```sh
python Firmware/tests/vc/check_synaptic_serial.py NEW_OUTPUT_FOLDER
```

This Linux QA compiles the real sketch/parser, uses actual pyserial through a
PTY, and simulates source spike edges plus operator confirmations. The native
clock is externally paced at nominal 500 Hz. Plots and cleanup are exercised.
It includes all seven cases, the basic Synapse 2 case and a missing-input case
that must fail response while resuming CC streaming.

The first serial attempt lacked the host's pyserial package and stopped before
opening a port. After installing pyserial 3.5, one basic-input capture passed
all membrane/receptor/cleanup checks but failed a PC receive window (556.23 Hz),
with a 144.85 ms maximum host read gap. Overall cadence was 500.001 Hz. This is
retained as a failed simulated-host capture; it does not identify a physical
ESP32 issue or justify relaxing the existing cadence criteria.

All nine serial workflow checks completed: seven protocols, the basic Synapse 2
case and deliberate missing input, each with plots and resumed CC streaming.
Six of eight intended positive captures pass every CLI criterion. Gabazine and
APV pass their membrane/receptor/cleanup checks but retain host receive-cadence
FAIL results. The missing-input capture correctly fails receptor response and
also has a host cadence failure; its valid membrane equations and successful
cleanup are checked separately. No raw FAIL is relabelled as a complete PASS.

The QA harness reports workflow success separately from full capture success;
its exit success does not imply all clock checks passed. It never rewrites
receive timestamps or production analyser criteria. Final results are recorded
with the downloadable kit in `QA/SIMULATED_SERIAL_RESULTS.json`, alongside the
nine raw reports, initial failed basic capture and complete host unit-test log.

## Hardware routing and reference sources

The repository's hardware setup specifies stereo TRS: tip=digital, ring=analogue,
sleeve=ground. The current v3.2 PCB confirms J6=Synapse Out, J2=Synapse1 In,
J3=Synapse2 In; pin functions T_3/R_2/S_1 match that contract. Use labelled jacks,
not GPIO jumper instructions. The older exported XML netlist is not used to infer
current ESP32-S3 pin mapping. The tested firmware reads digital inputs 38/39;
these pins are simulated only within native QA.

- [Hardware setup at 796fbd4](https://github.com/OpenSourceNeuro/Spikeling/blob/796fbd4c33b1e3f66b02b97d49d320f9ff74a619/Documentation/docs/quickstart/hardware-setup.md).
- [v3.2 PCB at 796fbd4](https://github.com/OpenSourceNeuro/Spikeling/blob/796fbd4c33b1e3f66b02b97d49d320f9ff74a619/Hardware/PCB/Spikeling%203.2/Spikeling_v3.2.kicad_pcb).
- [Neuronal Dynamics, Chapter 3.1](https://neuronaldynamics.epfl.ch/online/Ch3.S1.html): conductance, reversal, exponential receptor kinetics and voltage-dependent NMDA magnesium block.

The existing 13 core/first-integration protocols have staged passing physical
captures as documented in ACTIVE_VC_VALIDATION.md. The earlier isolated Patch
pause remains unresolved. This pack advances to physical synaptic/receptor
validation; it does not establish mixed-input finite-access timing, output
calibration, general pharmacological accuracy or a production-ready release.

## Runner 1.1 startup correction — 30 October 2026

The user's Windows traceback identifies `run_active_vc_tests.identity()` waiting
inside pyserial's read called by `readline()`, beyond its nominal four-second
outer deadline. The interrupted report at 18:30:15 UTC has capture_complete=false
and cc_binary_stream_resumed=true. This is a PC handshake failure before the
synaptic protocol, not a failed membrane experiment. The evidence does not
establish why the requested identity reply was missed.

A continuous binary stream can keep a line read alive without a newline. The
new identity query scans bounded chunks (at most 512 bytes), limits every read
to the remaining deadline (at most 50 ms), limits retained search data and
restores the previous read timeout. It accepts split replies embedded among
binary packets, checks all required firmware markers, and reports a wrong reply
explicitly. A newline before VCINFO terminates a preceding partial command.

The synaptic runner now drains the first two seconds of output instead of
sleeping without reading. It sends the 36 configuration commands as separate
short writes (10 ms intervals) with output drained between commands. The old
configuration was one 296-byte burst. Pacing/draining reduces buffer pressure;
it is not proof that buffer overflow caused the missed reply or an independent
acknowledgement of each setting. Writes retain their two-second timeout and no
unbounded OS flush is used in the new startup/cleanup path. During capture the
background reader remains the only reader. Cleanup has its own bounded identity
barrier and verifies three complete CC packets. Startup progress is printed and
its latest stage is saved in the report.

The complete native/host regression suite passes **113 tests** (21.647 s),
including 13 new serial-startup tests. Faults cover continuous newline-free binary,
silence, partial replies, wrong/missing version markers, incomplete writes,
invalid commands, interrupted reads and missing CC packets. These are simulated
serial/clock tests, not physical execution-time measurements.

A real pyserial/PTY regression suppresses the first VCINFO reply and supplies
newline-free binary output. The runner must time out at the identity stage,
mark capture incomplete/FAIL, then resume CC streaming during cleanup. The
normal basic Synapse 1, Synapse 2 and NBQX control/drug/washout workflows also
pass every CLI criterion with the native sketch, plots, cadence and cleanup.
The updated kit records their raw results separately
from the original pack's nine workflows; any host cadence failure remains FAIL.

Firmware and all membrane/receptor/pharmacology equations and acceptance
thresholds remain unchanged. The first COM13 startup/physical capture
verification is recorded below; other synaptic channels/protocols remain pending.

## Physical basic Synapse 1 — PASS, 30 October 2026

Case `14_synaptic_input --synapse 1`, runner 1.1 at tool revision 797f054,
installed firmware 5c2e063 (`clock=2,gates=2,voltage=2`). The new startup reaches
the active identity and operator prompts on COM13. This verifies the corrected
startup in this run; it does not establish why the old reply was missed or
resolve the earlier isolated Patch-loop pause.

Independent reanalysis of all **21,670 contiguous CSV samples** agrees with the
live report (allowing machine-rounding differences in least-squares results).
The recording lasts 43.33926 wall seconds including operator-change intervals;
the active capture lasts 10.00643 seconds. All existing criteria pass.

| Measurement | Result |
| --- | --- |
| Overall cadence | 499.985491 Hz |
| Complete one-second receive windows | 499.808891–500.236434 Hz |
| Median / maximum previous loop | 1,479 / 1,561 us |
| Diagnostic/deadline flags | All zero |
| Command / Vm | -70 mV throughout; zero recorded tracking error |
| Resolved events in settled active window | 22; minimum interval 0.402 wall s |
| Fitted event contribution | -0.0990005281 nA; expected -0.099 nA |
| Maximum synaptic waveform fit residual | 0.000000771944 nA |
| Maximum independent clamp-reference error | 0.000000823227 nA |
| Maximum current-balance error | 0.000001 nA |
| Quiet baseline / settled recovery receptor maximum | 0 / 0.000001 nA |
| CC binary streaming after cleanup | Confirmed by the live report |

An additional direct recurrence check, separate from the regression fit, finds
22 fast-current increments with mean -0.09899993 nA. Maximum increment error is
0.00000007 nA; maximum non-event decay residual is 0.00000095 nA. This agrees with
`I[k] = 0.99*I[k-1] - 0.099*event[k]` at fixed -70 mV. The active absolute peaks
reach about -0.11414 nA because preceding events leave a residual tail; the
event contribution rather than raw peak/mean is the relevant drug comparison.
Vm stays fixed while compensating clamp current changes with receptor current.
These tiny reference errors concern exported model values and rounding; they
are not measurements of biological or analogue-output accuracy.

Evidence: `vc_synapse_20261030_195517_858406.zip`, containing the live report,
CSV and plot. Archive SHA-256:
`923d71ab69a217ebebb0f6d62bf2d7fd9c10ae6d9669f457e6a291a83d9686bb`.
CSV SHA-256:
`7c7afc7c3530dab6ceea66c5889d6deb79d17e759555c60c199e0602627cd513`.

Scope: received AMPA events through physical Synapse 1 under ideal active VC
at -70 mV, with quiet baseline/recovery and measured timing. There is still no
independent source spike count, proof of zero missed TTL events, stochastic
release qualification, receptor/drug selectivity result or finite-access
synaptic timing result. Stop the source, move only the receiving cable end to
Synapse 2 In, and repeat case 14 with `--synapse 2` before cases 15 to 20.
Firmware, tools and all acceptance thresholds remain unchanged.

## Physical basic Synapse 2 — PASS, 30 October 2026

Case `14_synaptic_input --synapse 2`, runner 1.1 at 797f054, with unchanged
5c2e063 firmware. Independent analysis of all **23,460 contiguous samples**
agrees with the live report within machine-rounding precision. Recording
length is 46.91917 wall seconds including operator changes; the active phase
lasts 9.99830 seconds. All existing criteria pass.

| Measurement | Result |
| --- | --- |
| Overall cadence | 499.987518 Hz |
| Complete one-second receive windows | 499.656148–500.251880 Hz |
| Median / maximum previous loop | 1,383 / 1,535 us |
| All diagnostic/deadline flags | Zero |
| Vm / command | -70 mV throughout |
| Resolved events in settled active window | 20; minimum interval 0.452 wall s |
| Fitted event contribution | -0.0990004464 nA; expected -0.099 nA |
| Maximum synaptic waveform fit residual | 0.000000748826 nA |
| Maximum independent clamp-reference error | 0.000000823227 nA |
| Maximum current-balance error | 0.000001 nA |
| Quiet baseline / settled recovery receptor maximum | 0 / 0 nA at export precision |
| CC binary streaming after cleanup | Confirmed by the live report |

A separate direct difference check finds 20 increments averaging -0.09900004 nA,
maximum increment error 0.00000004 nA and maximum non-event decay residual
0.00000090 nA. Fitted Synapse 2 / Synapse 1 event-amplitude ratio is 0.9999991746
at the same configured gain. This checks consistent model event size; it is not
analogue gain calibration or an independent source spike-count comparison.
Different mean currents or initial summed peaks are not interpreted as a gain
change because the source rates/manual-change histories differ.

Evidence: `vc_synapse_20261030_200340_672425.zip`, containing CSV, report and plot.
Archive SHA-256:
`44fc9726faf8e0a858c6cdceb0c003ca97cec1bc1676c1346326a3a8624baed1`.
CSV SHA-256:
`4c3feeef25897ee470bfaa8a320c53c37e31ecade09850f82226e45c46026e8f`.

Both individual physical inputs now pass received AMPA-event tests at ideal
-70 mV active VC, with quiet recovery, timing and resumed CC streaming. This
is not simultaneous-input, finite-access, receptor-reversal, antagonist or
stochastic release qualification. The earlier isolated Patch pause remains
unresolved. Firmware, tools and thresholds are unchanged.

Next board action: stop the source, return the receiving cable end to Synapse 1,
then run `15_nbqx --synapse 1`. Keep source firing steady through all three
12-second phases; the script applies simulated 0.30 uM NBQX and washout.
Expected per-event AMPA contributions are -0.099, -0.0495 and -0.099 nA.
Review that capture before proceeding to gabazine or other receptor/release tests.

## First physical NBQX capture — response PASS, overall FAIL

Case `15_nbqx --synapse 1`, runner 1.1 at 797f054 and unchanged 5c2e063 firmware.
Independent analysis of all **26,549 contiguous samples** over 53.11688 wall
seconds agrees with the live report, including its overall FAIL. The receptor,
membrane, integrity and cleanup results pass; timing does not. This capture
must not be counted as a complete NBQX protocol PASS.

At fixed -70 mV, each settled phase has 21 resolved events (minimum interval
0.526 wall seconds). Simulated 0.30 uM NBQX produces the configured half-block
and washout restores the event contribution:

| Phase | Fitted contribution per event (nA) | Expected (nA) |
| --- | --- | --- |
| Control | -0.09900046618 | -0.099 |
| NBQX | -0.04950020418 | -0.0495 |
| Washout | -0.09900046598 | -0.099 |

Drug/control ratio is 0.499999708; washout/control is 0.999999998. Maximum
synaptic fit residual is 0.000000834053 nA. A separate direct difference/decay
check finds 21 event increments per phase, averaging -0.0989997062,
-0.0495002900 and -0.0989995800 nA. Independent HH/current balance agrees within
export precision; maximum clamp-reference error is 0.000000823227 nA. Vm remains
-70 mV, other input current is quiet and CC streaming resumes after cleanup.
These establish the specified software drug effect on received events, not
universal biological potency or independently measured source-spike statistics.

### Timing failure and event chronology

One flag-64 record at sequence 6146 reports previous_loop_us=22,256. All other
loops are at most 1,614 us (overall median 1,489 us). The preceding sample at
sequence 6145 has solve_us=262, so **21,994 us lies outside that measured HH solve**.
The flag occurs in the manual `change` interval with receptor current zero:

| Event | PC time from first captured sample |
| --- | --- |
| Deadline flag record | 0.500526 s |
| First nonzero received receptor response | 2.370526 s |
| Start of labelled control phase | 6.286600 s |
| Start of labelled drug phase | 18.360628 s |

Thus the overlong tick precedes the first recorded receptor response and NBQX
application.
The device duration/flag demonstrates an actual board-loop overrun; this is not
merely a slow host receive window. The CSV also has a 27.0361 ms receive gap
before a batch containing sequences 6143 to 6145. Host batching and the board
pause occur together, but the existing instrumentation cannot assign causality
to USB backpressure, console/host scheduling, other IO or device pre-emption.
Do not attribute the delay to the HH solver or NBQX computation from these data.

Overall cadence is 499.803431 Hz, but the first complete one-second receive
window is 489.756429 Hz and fails the unchanged +/-2% rule. The single 22.256 ms
loop also independently fails the unchanged 2 ms deadline. The earlier case 11
22.9 ms pause remains unresolved; this new quiet-period occurrence has a similar
pattern without establishing a shared cause. Startup identity and cleanup both
succeed, so the corrected line-read hang is separate from this runtime overrun.

Evidence: `vc_synapse_20261030_201130_252214.zip`, containing report, CSV and plot.
Archive SHA-256:
`2ac9db0b32a382709ce7511df6880fcdb2b8a0f270cbbc4e82935c2c632cc538`.
CSV SHA-256:
`bcddde217779d18c521ac6ed8f5faf43d119dbed3c815c52c45551ee22b5b365`.

Next: repeat case 15 once with the same firmware, kit, Synapse 1 wiring and
source procedure. Retain this failed recording even if the repeat passes; a
clean repeat cannot establish a permanent fix for the intermittent pause. If
it recurs, isolate IO/serial/pre-emption timing with targeted instrumentation
before advancing the board qualification. No model or threshold is changed.

## Physical NBQX repeat — overall PASS, 30 October 2026

Case `15_nbqx --synapse 1`, repeated with the same runner 1.1 at 797f054 and
unchanged 5c2e063 firmware. Independent reanalysis of **26,409 contiguous
samples** over 52.81661 wall seconds agrees with the live report. All existing
response, membrane, integrity, timing and cleanup criteria pass.

| Measurement | Result |
| --- | --- |
| Overall cadence | 499.994257 Hz |
| Complete one-second receive windows | 499.834944–500.356015 Hz |
| Median / maximum previous loop | 1,488 / 1,607 us |
| All diagnostic/deadline flags | Zero |
| Command / Vm | -70 mV throughout |
| Resolved events per settled phase | 22 / 22 / 22 |
| Control event contribution | -0.09900054073 nA |
| NBQX event contribution | -0.04950018797 nA |
| Washout event contribution | -0.09900054683 nA |
| Drug / control contribution ratio | 0.499999168 |
| Washout / control contribution ratio | 1.000000062 |
| Maximum synaptic waveform residual | 0.000000894134 nA |
| Maximum independent clamp-reference error | 0.000000823227 nA |
| Settled post-protocol receptor maximum | 0 nA at export precision |
| CC binary streaming after cleanup | Confirmed by the live report |

A separate direct current-increment/decay check finds 22 increments in every
phase, averaging -0.09900013591 / -0.04949959000 / -0.09900018000 nA, with
non-event decay residuals <=0.00000098 nA. Thus the expected simulated half-block
and washout are verified per received event, not by unnormalised mean current.
The control, drug and washout labelled phases last 12.06021, 12.05400 and
12.01399 wall seconds. Dose is the model's illustrative 0.30 uM NBQX setting.

Evidence: `vc_synapse_20261030_202600_819949.zip`, containing CSV, report and plot.
Archive SHA-256:
`c87cf76bc33d189274e106a76ee71dba9a72cf4e35860102f265c44010a9c276`.
CSV SHA-256:
`7be5cbc413a88d5d2ef068fe1582684cf845434372abff9bf5318c7176e0e727`.

The first NBQX run remains FAIL for its 22.256 ms quiet-period loop. This clean
repeat establishes a passing case-15 capture at unchanged criteria; it does not
identify or permanently correct that intermittent pause or the earlier Patch
pause. Keep those observations open during subsequent qualification. No model,
firmware, tool or threshold change is made.

Next: `16_gabazine --synapse 1`, using the same cable/source setup. The runner
selects GABA-A and the required synaptic gain automatically; keep postsynaptic
knobs fixed. At -70 mV with E_GABA=-80 mV, expected outward-positive event
contributions are +0.099 / +0.0495 / +0.099 nA through control / simulated
0.90 uM gabazine / washout. Maintain steady source firing through all three
12-second phases and review the capture before reversal or NMDA/release tests.

## Physical gabazine — overall PASS, 30 October 2026

Case `16_gabazine --synapse 1`, runner 1.1 at 797f054 and unchanged 5c2e063
firmware. Independent reanalysis of all **24,230 contiguous samples** over
48.45797 wall seconds agrees with the live report within machine precision.
All existing numerical, response, integrity, timing and cleanup criteria pass.

At -70 mV with the explicitly configured E_GABA=-80 mV, receptor event currents
are outward-positive. Simulated 0.90 uM gabazine halves the GABA-A contribution,
and washout restores it:

| Phase | Resolved settled events | Fitted event contribution (nA) | Expected (nA) |
| --- | --- | --- | --- |
| Control | 35 | +0.09900060781 | +0.099 |
| Gabazine | 35 | +0.04950033568 | +0.0495 |
| Washout | 35 | +0.09900060914 | +0.099 |

Drug/control ratio is 0.500000321; washout/control is 1.000000013. Minimum
resolved event interval is 0.308 wall seconds in all three settled phases.
A separate direct current-increment check also finds 35 events per phase,
with means +0.09900021 / +0.04950010 / +0.09900021 nA. Maximum non-event decay
residual is 0.000001 nA; maximum waveform-fit residual is 0.000000855143 nA.
These are agreement tests for the existing teaching model, not universal drug
potencies or analogue current calibration.

| Measurement | Result |
| --- | --- |
| Overall cadence | 500.000290 Hz |
| Complete one-second receive windows | 499.878142–500.210078 Hz |
| Median / maximum previous loop | 1,493 / 1,620 us |
| All diagnostic/deadline flags | Zero |
| Command / Vm | -70 mV throughout |
| Maximum independent clamp-reference error | 0.000000823227 nA |
| Maximum current-balance error | 0.000001 nA |
| Settled post-protocol receptor maximum | 0.000001 nA at export precision |
| CC binary streaming after cleanup | Confirmed by the live report |

Evidence: `vc_synapse_20261030_203227_620637.zip`, containing CSV, report and plot.
Archive SHA-256:
`5211c495de9960734dde6b083d347f683b9c9e4e8031af2b155d858c97958e32`.
CSV SHA-256:
`e845609a915481101f5e91ce9a367b6aaff549f49b3fe289d18036ef610d2a62`.

Scope: specified GABA-A polarity, half-block, washout, timing and cleanup at
ideal -70 mV clamp. The earlier NBQX 22.256 ms and Patch pauses remain unresolved;
this clean run is not a demonstrated fix. No model, firmware, tool or threshold
change is made. Source spike counts/release failures, receptor reversals and
mixed-input/finite-access timing remain separate measurements.

Next: case `17_ampa_reversal --synapse 1`, with the same wiring and source.
The runner automatically restores AMPA selection, clears drugs and steps the
holding command through -70, -20 and +20 mV for 12 seconds each. Expected
contributions per event are -0.099, -0.0282857143 and +0.0282857143 nA. Maintain
steady source firing until prompted to stop. The fitted zero crossing should
be near 0 mV; received events are required at all three nonzero-driving-force
points, so absence of a current at one voltage cannot alone pass a reversal test.

## Physical AMPA reversal — overall PASS, 30 October 2026

Case `17_ampa_reversal --synapse 1`, runner 1.1 at 797f054 with unchanged
5c2e063 firmware. Independent reanalysis of all **25,591 contiguous samples**
over 51.18045 wall seconds agrees with the live report within machine precision.
All original numerical, response, integrity, timing and cleanup criteria pass.

| Holding voltage | Resolved settled events | Fitted event contribution (nA) | Expected (nA) |
| --- | --- | --- | --- |
| -70 mV | 21 | -0.09900047321 | -0.099 |
| -20 mV | 20 | -0.02828581351 | -0.02828571429 |
| +20 mV | 20 | +0.02828583075 | +0.02828571429 |

The fitted reversal is -0.0000012562 mV, effectively 0 mV at meaningful model
precision; fitted event conductance is 0.001428578085 uS. A separate direct
increment/decay check finds the same 21/20/20 events, with mean increments
-0.09899968905 / -0.02828618 / +0.02828618 nA. Fitting those direct means gives
reversal -0.000089993 mV and conductance 0.001428572451 uS. The tiny numerical
offsets arise at export/fitting precision, not as a physical voltage-calibration
measurement. Received events are present at all three nonzero-driving-force
points; the result does not rely on an absent current at a single command.

| Measurement | Result |
| --- | --- |
| Overall cadence | 499.995562 Hz |
| Complete one-second receive windows | 499.879137–500.175914 Hz |
| Median / maximum previous loop | 1,523 / 1,634 us |
| All diagnostic/deadline flags | Zero |
| Maximum Vm / command discrepancy | 0 mV at export precision |
| Maximum independent clamp-reference error | 0.0007501154 nA |
| Maximum independent sodium-reference error | 0.0007533932 nA |
| Maximum gate-reference error | 0.0000005266783 |
| Maximum current-balance error | 0.000001 nA |
| Maximum synaptic waveform residual | 0.000000824993 nA |
| Settled post-protocol receptor maximum | 0 nA at export precision |
| CC binary streaming after cleanup | Confirmed by the live report |

The small transient HH-current integration errors are within the unchanged
0.01 nA current tolerance; they are not all at the CSV rounding floor. Synaptic
reversal is judged from the receptor-current contribution, not total clamp
injection, which also contains Na/K/leak and voltage-step capacitance currents.

Evidence: `vc_synapse_20261030_203954_842898.zip`, containing CSV, report and plot.
Archive SHA-256:
`2b411600c90a813fed0ae437bb00a98858dc5d879a1c7bf1f60226f7d191f0e4`.
CSV SHA-256:
`93781eb70e5803f6f126d8e8873d56bd952a3c9508ac36595b26eade85f38ecc`.

Scope: expected AMPA driving-force scaling and sign reversal under ideal active
VC, with event-resolved currents, timing and cleanup. The prior intermittent
NBQX/Patch pauses remain open; this is not finite-access, analogue-output,
source-spike count or stochastic-release qualification. No model, firmware,
tool or acceptance threshold changes are made.

Next: `18_gaba_reversal --synapse 1`, with the same source/wiring. The runner
selects GABA-A and commands -90, -70 and -50 mV for 12 seconds each. Expected
contributions per event are -0.099, +0.099 and +0.297 nA, with fitted reversal
near the configured -80 mV. Keep the source steady and postsynaptic knobs fixed
until prompted to stop; NMDA/APV and GVIA cases follow after review.

## Physical GABA-A reversal — overall PASS, 30 October 2026

Case `18_gaba_reversal --synapse 1`, runner 1.1 at 797f054 and unchanged
5c2e063 firmware. Independent reanalysis of all **31,812 contiguous samples**
over 63.62247 wall seconds agrees with the live report within machine precision.
All unchanged response, numerical, integrity, timing and cleanup criteria pass.

| Holding voltage | Resolved settled events | Fitted event contribution (nA) | Expected (nA) |
| --- | --- | --- | --- |
| -90 mV | 23 | -0.09900052643 | -0.099 |
| -70 mV | 23 | +0.09900053548 | +0.099 |
| -50 mV | 22 | +0.29700147581 | +0.297 |

The fitted reversal is -79.9999994334 mV, effectively the configured -80 mV;
fitted conductance is 0.010000050562 uS. A separate direct-increment check finds
23/23/22 events with means -0.09899991 / +0.09899991 / +0.29699973 nA. Fitting
those direct means gives -80 mV and 0.009999990909 uS. This checks the model's
driving-force scaling and sign reversal, not physical voltage calibration.
Events are resolved at all three nonzero-driving-force points, with minimum
interval 0.472 wall seconds; zero current alone is never accepted as evidence
that an input arrived. Maximum waveform-fit residual is 0.000001478404 nA.

| Measurement | Result |
| --- | --- |
| Overall cadence | 499.996309 Hz |
| Complete one-second receive windows | 499.857656–500.066141 Hz |
| Median / maximum previous loop | 1,517 / 1,621 us |
| All diagnostic/deadline flags | Zero |
| Maximum Vm / command discrepancy | 0 mV at export precision |
| Maximum independent clamp-reference error | 0.00019185794 nA |
| Maximum independent sodium-reference error | 0.00019216141 nA |
| Maximum gate-reference error | 0.0000005253871 |
| Maximum current-balance error | 0.000001 nA |
| Settled post-protocol receptor maximum | 0 nA at export precision |
| CC binary streaming after cleanup | Confirmed by the live report |

The transient HH-current errors remain within the original 0.01 nA tolerance.
Synaptic reversal uses receptor current; total injection additionally contains
Na/K/leak and capacitive current. Prior intermittent NBQX/Patch pauses remain
unresolved despite this clean one-minute capture. No model, firmware, tool or
acceptance thresholds are changed.

Evidence: `vc_synapse_20261030_204825_321782.zip`, containing report, CSV and plot.
Archive SHA-256:
`a6104671fa77b767d9fb306549823b6caa06ebc7d7b82ab21a7e13c49ac91a8b`.
CSV SHA-256:
`49763b5cc34c64925a7e6b8ced3d3ce302a377db6222f58df5921d81f109aa56`.

Next: `19_nmda_apv --synapse 1`, with the same source/wiring. The runner restores
AMPA plus NMDA, holds -20 mV and applies control / simulated 3.7 uM APV /
washout for 12 seconds each. The fast AMPA contribution should stay near
-0.0282857143 nA per event; the fitted slow NMDA coefficient should halve and
recover. That coefficient is not a raw peak of the summed current. Source
firing stays steady until prompted to stop. Recovery may take longer while
NMDA tails decay; keep the source quiet and allow the script to finish.

## Physical NMDA/APV selectivity — overall PASS, 30 October 2026

Case `19_nmda_apv --synapse 1`, runner 1.1 at 797f054 and unchanged
5c2e063 firmware. Independent reanalysis of all **24,928 contiguous samples**
over 49.85467 wall seconds reproduces the live report within machine precision.
All original numerical, receptor, integrity, timing and cleanup criteria pass.

The runner holds -20 mV with AMPA plus NMDA enabled, applies simulated 3.7 uM
APV and then removes it. These are fitted contributions of resolved received
events, with latent exponentials accounting for preceding synaptic tails.

| Phase | Resolved settled events | Fast AMPA contribution (nA) | Slow NMDA coefficient (nA) |
| --- | --- | --- | --- |
| Control | 19 | -0.02828581578 | -0.03458738249 |
| APV | 19 | -0.02828577539 | -0.01729369276 |
| Washout | 18 | -0.02828579905 | -0.03458735165 |

NMDA drug/control is 0.5000000438 and washout/control is 0.9999991081.
AMPA drug/control is 0.9999985723 and washout/control is 0.9999994087.
The expected AMPA event contribution is -0.0282857143 nA throughout; the
expected slow coefficients are -0.03458773976 / -0.01729386988 /
-0.03458773976 nA. The NMDA coefficient multiplies a biexponential waveform;
it is not the raw peak or mean of total receptor/clamp current. The summed
receptor trace contains temporal summation, so halving its overall peak or
mean is not the acceptance test. Minimum resolved event interval is 0.576 wall
seconds in each phase.

A separate closed-form fit builds each event's exponential waveform directly
from its age, without the analyser's convolution recurrences. It reproduces
both component coefficients and their ratios. After subtracting the fitted
slow contribution, mean fast increments are -0.02828551547 /
-0.02828576375 / -0.02828566440 nA; maximum non-event fast-decay residual is
0.000000999530 nA. Maximum summed waveform residual is 0.000000746563 nA.

| Measurement | Result |
| --- | --- |
| Overall cadence | 499.993319 Hz |
| Complete one-second receive windows | 499.874530–500.097113 Hz |
| Median / maximum previous loop | 1,527 / 1,690 us |
| Maximum measured solver interval | 305 us |
| All diagnostic/deadline flags | Zero |
| Maximum Vm / command discrepancy | 0 mV at export precision |
| Maximum independent clamp-reference error | 0.0001242676 nA |
| Maximum independent sodium-reference error | 0.0001260491 nA |
| Maximum gate-reference error | 0.000000525243 |
| Maximum current-balance error | 0.000001 nA |
| Settled post-protocol receptor maximum | 0.001399 nA, within the original 0.003 nA quiet limit |
| CC binary streaming after cleanup | Confirmed by the live report |

The slow recovery tail is small but nonzero; this is not an exact return to
zero at export precision. This capture validates the configured receptor
kinetics and selective APV scaling at -20 mV. It does not independently count
source spikes, calibrate analogue outputs, test the full magnesium-block
voltage relation or establish real drug binding/washout kinetics. Earlier
intermittent NBQX/Patch pauses remain unresolved. Firmware, tools, model
parameters and acceptance thresholds are unchanged.

Evidence: `vc_synapse_20261030_210026_760655.zip`, containing report, CSV and plot.
Archive SHA-256:
`d9f3a5fe876ea9ed3a13d49d92bd78d676df73c9f13b77d27b09ca033aa37d15`.
CSV SHA-256:
`e61a166007c672880a7d680ce9b3660f712d2836869526fbbdb5e584b3b60765`.

Next: `20_gvia --synapse 1`, using the same kit, firmware and wiring. The runner
selects AMPA at -70 mV, disables NMDA and enables deterministic presynaptic
release scaling with N-type fraction 0.35. Control / simulated 10 nM GVIA /
washout phases each last 12 seconds. Expected contributions are -0.099 /
-0.055590046875 / -0.099 nA per resolved event: drug/control efficacy
`(1-0.35*0.5)^3 = 0.561515625`. This tests deterministic event amplitude,
not stochastic release failures. Source firing stays steady until prompted
to stop; retain the full result archive.

## Physical GVIA — four console-reported FAILs, 30 October 2026

The user ran `20_gvia --synapse 1` four times with runner 1.1 and the installed
identity `VC-ACTIVE-1,mV,ms,nA,pF,MOhm,clock=2,gates=2,voltage=2`. This section
records the supplied console output only. The four CSVs/reports have not yet
been supplied or independently reanalysed; no archive hashes are available.

| Result folder | Console result | Cadence | Maximum loop | Deadline flags | Resolved control / drug / washout events |
| --- | --- | --- | --- | --- | --- |
| vc_synapse_20261030_211129_302995 | Overall FAIL; all three response phases PASS | 499.778 Hz | 23,312 us | 1 | 18 / 18 / 18 |
| vc_synapse_20261030_211245_619508 | Overall FAIL; all three response phases PASS | 499.846 Hz | 16,665 us | 1 | 34 / 34 / 33 |
| vc_synapse_20261030_211356_139436 | Overall FAIL: Missing or duplicated device sample | Not printed | Not printed | Not printed | Not printed |
| vc_synapse_20261030_211532_623345 | Overall FAIL; all three response phases PASS | 499.777 Hz | 23,226 us | 1 | 22 / 23 / 22 |

The three complete analyses report the intended receptor response while
failing the unchanged loop-deadline criterion. Average cadence near 500 Hz
does not override a missed 2 ms deadline. The third run fails the sequence
integrity check before response analysis; its gap/duplicate direction and
size are unknown from the console. No numerical reference should be propagated
across that discontinuity. The cleanup message states requested actions;
it does not establish successful CC resumption without the report.

These recurrences make targeted timing/transport diagnosis the next board
action. Do not repeat until one run happens to pass, relax thresholds, slow
the model or change receptor parameters to conceal the failures. Preserve
all four folders, including partial captures. The earlier NBQX/Patch pauses
also remain open; a shared cause is not yet established.

Code inspection finds that deterministic GVIA uses a fixed, small arithmetic
path on incoming events, while complete-loop timing includes command handling,
shared inputs/release, membrane work, outputs, formatting and serial writing.
The active VC2 write does not currently record its returned byte count.
The PC reader ignores non-VC2 lines and does not preserve a raw byte stream.
These are diagnostic coverage limits, not proof of a USB or parser fault.

Next: obtain all four original reports/CSVs; locate each flagged record relative
to source onset, phase changes and recovery; compare its previous-loop value
with the preceding row's solver interval; inspect PC receive gaps and every
sequence discontinuity. If these cannot isolate the cause, instrument command
handling, input/release, membrane/output work, formatting and transmission,
including serial short-write counters, before another qualification run.
Keep the current firmware installed while collecting the existing evidence.

## Physical GVIA — all four raw captures reviewed, 30 October 2026

The uploaded archive is named `vc_synapse_20261030_211129_302995.zip` but contains
all four result folders. All **113,290 CSV rows** were inspected. Independent
reanalysis reproduces the three complete reports within machine precision and
reproduces the fourth report's integrity exception. Every overall result
remains FAIL. All four original reports confirm CC binary streaming resumed.

| Folder suffix | Samples | Overall cadence (Hz) | Minimum one-second window (Hz) | Failure |
| --- | --- | --- | --- | --- |
| 211129_302995 | 24,391 | 499.778056 | 489.355566 | One 23,312 us loop; deadline flag 64 |
| 211245_619508 | 25,697 | 499.846250 | 492.685917 | One 16,665 us loop; deadline flag 64 |
| 211356_139436 | 38,029 | 499.992351 | 499.866769 | Exactly one absent exported record, sequence 19575 |
| 211532_623345 | 25,173 | 499.776667 | 489.306252 | One 23,226 us loop; deadline flag 64 |

The second run passes the average and one-second cadence criterion but fails
the individual loop deadline. The first and fourth also fail a one-second
window. The third has no recorded diagnostic flags and maximum loop 1,615 us;
good observed timing does not excuse its missing record. At that gap the CSV
advances 19574 -> 19576, model time advances 0.2 ms and PC receive time advances
4.1894 ms. It is not a duplicated row. The raw serial bytes were not retained,
so firmware omission, a short write, byte loss or parser rejection cannot be
distinguished. No reference propagation crosses that missing record.

| Run | Flagged sequence | Measured loop sequence | Phase | Wall time from first CSV row | Preceding HH solve | Loop outside that solve |
| --- | --- | --- | --- | --- | --- | --- |
| First | 15740 | 15739 | Drug | 26.123798 s | 270 us | 23,042 us |
| Second | 23249 | 23248 | Washout | 39.997535 s | 269 us | 16,396 us |
| Fourth | 15281 | 15280 | Drug | 25.446215 s | 273 us | 22,953 us |

`previous_loop_us` describes the preceding loop; the preceding row's solver
measurement is used above. The nearest resolved synaptic events are 50 ticks
before, 51 ticks after and 103 ticks before the measured long loops. Thus no
new resolved input event occurs on those loops. The pauses are several seconds
after phase changes and occur during both drug and washout. Existing telemetry
locates them outside the measured HH solve but does not identify which other
operation or scheduling event consumed the time.

Each long-loop region also contains a receive-data gap before a batch of old
records: 27.8889 / 21.0374 / 27.9421 ms in the exported row timestamps. This
association makes serial/host scheduling useful to instrument; it does not
establish the direction of causation or a specific USB fault.

The three contiguous captures independently pass membrane agreement and the
configured GVIA response. Control / drug / washout fitted contributions (nA):

| Run | Control | GVIA | Washout | Drug/control | Washout/control |
| --- | --- | --- | --- | --- | --- |
| First | -0.09900048811 | -0.05559027239 | -0.09900048752 | 0.5615151344 | 0.9999999941 |
| Second | -0.09900051731 | -0.05559037210 | -0.09900053889 | 0.5615159760 | 1.0000002180 |
| Fourth | -0.09900054904 | -0.05559034497 | -0.09900054793 | 0.5615155220 | 0.9999999888 |

Expected efficacy is 0.561515625. Separate fast-increment/decay checks agree.
Maximum independent clamp-reference error is 0.000000823228 nA in these three
captures. Quiet recovery passes in all four; the third retains at most
0.000001 nA at export precision. Intact control/drug windows in the third also
have the expected direct increments, but its broken washout sequence prevents
acceptance of that complete protocol.

Combined archive SHA-256:
`d9f6820b1152ea2daaaaeff1e5328bc2b33890e75bce94f84e3e11ca6c4bc749`.

| Folder suffix | CSV SHA-256 |
| --- | --- |
| 211129_302995 | 064f84168cc0a22ababb28362ac706b0a7b9adc5b5e342c0fcfa56cd889b5060 |
| 211245_619508 | 2e82b78b1265c87b91cf9d5d33cb36cb0e47c29b1f73cec3eec9db664c936a9e |
| 211356_139436 | b56a26c925df29f1fe6c09fc52f9f021f20df9fceab3a958e48c51f502981492 |
| 211532_623345 | bbfe8c0293da29cdd8a153c323a4ca38e23a9e8d6571885cff31176a25dc64be |

## Opt-in timing diagnostic revision

`VCPR 1` enables a fixed-size 16-record buffer and stage maxima; `VCPR 0`
freezes it; `VCPR ?` explicitly retrieves it. No extra per-tick fields or
unsolicited lines are added to VC2 or the original CC binary protocol. Trace
records identify the loop that actually ran long, late starts, format faults
and returned-versus-requested VC2 byte counts. Entry counts and overflow stay
explicit. Leaving VC disables tracing without erasing the stored evidence.
Model equations, shared input/release behaviour, RNG and all thresholds are
unchanged. This is an instrumented experiment, not a demonstrated timing fix.

Runner 1.2 adds `--timing-trace`, requires identity marker `trace=1`, freezes
profiling while the receive thread still drains, then retrieves it before
analysis/plotting/cleanup. Exact received bytes and chunk timestamps are kept
in bounded memory during capture and saved afterward. Missing samples,
nonzero trace-fault counters, overflow or truncated forensic capture remain
FAIL. Without the option, the runner remains compatible with 5c2e063.

Native regression suite: **123 tests PASS**, including 10 new instrumentation
and transport tests. A synthetic 21 ms serial write is localised to the write
span and still produces a deadline failure; a zero-byte write is retained in
the trace and still produces a missing-sample failure. The full real-pyserial/
PTY GVIA CLI passes all criteria with simulated IO. A second full CLI with a
deliberately omitted sample FAILS as expected, saves raw bytes/trace and
confirms CC cleanup. These checks do not measure physical ESP32 timing.

The current environment lacks the installed ESP32 core and cannot download it;
the diagnostic revision has **not been ESP32 cross-compiled here**. Provide
source only, requiring local Arduino Verify before upload, with the tested
5c2e063 source for rollback. See VC_TIMING_DIAGNOSTICS_WINDOWS.md. Run one
instrumented case 20 after successful Verify/upload, then review its complete
result folder; do not keep repeating for a clean outcome. Earlier NBQX/Patch
pauses and the four GVIA failures all remain open.

## First physical instrumented GVIA capture — PASS, 30 October 2026

Case `20_gvia --synapse 1 --timing-trace`, runner 1.2 and diagnostic firmware
3d78f06, identity ending `trace=1`. The user's successful physical execution
confirms that this source was compiled/uploaded on their setup; local build
logs or binary size were not supplied. It does not retroactively establish an
ESP32 cross-build in this workspace. Independent reanalysis reproduces the
live response/numerical/clock result and frozen trace within machine precision.

| Measurement | Result |
| --- | --- |
| Analysed contiguous samples | 25,288 |
| CSV receive duration | 50.5752456 wall seconds |
| Average cadence | 499.987686 Hz |
| Complete one-second windows | 499.718695–500.280568 Hz |
| Median / maximum previous loop | 1,576 / 1,673 us |
| All diagnostic flags | Zero |
| Vm / command discrepancy | 0 mV at export precision |
| Maximum independent clamp-reference error | 0.000000823228 nA |
| Maximum gate-reference error | 0.000000465525 |
| Maximum current-balance error | 0.000001 nA |
| Settled post-protocol receptor maximum | 0.000002 nA, inside the original 0.003 nA quiet limit |
| CC binary streaming after cleanup | Confirmed by the live report |

Each settled phase resolves 22 events. Control / simulated 10 nM GVIA /
washout fitted contributions are -0.09900054907 / -0.05559035672 /
-0.09900054336 nA. Drug/control is 0.5615156405 (expected 0.561515625), and
washout/control is 0.9999999423. A separate direct-increment/decay check agrees.
This is the first complete passing case-20 capture; its firmware revision
differs from the four preceding failed captures.

The frozen trace covers 27,519 ticks, including setup/quiet activity outside
the analysed CSV. Exceptional records, overruns, late starts, short writes,
format errors and buffer overflow are all zero. Stage maxima below are
separate maxima, not one observed worst-case tick:

| Span | Maximum elapsed time |
| --- | --- |
| Command handling | 97 us |
| Shared inputs | 272 us |
| Release/receptors | 42 us |
| Stimulus/current assembly | 268 us |
| Membrane plus associated state | 389 us |
| Outputs | 83 us |
| VC2 formatting | 595 us |
| VC2 write | 96 us |

Raw evidence was independently checked, not just the JSON PASS flag:

- All 4,056,215 bytes are covered by 75,800 consecutive, non-overlapping
  timestamped chunks; no byte/timestamp storage truncation occurred.
- All 25,288 CSV records, every exported field and every receive timestamp
  match the complete VC2 records in the raw bytes exactly.
- The ordinary line parser sees 27,518 contiguous VC2 records, sequences
  840–28357. One initial line combines old binary framing with VC2 sequence
  839; recovering that prefixed initial record gives 27,519 consecutive raw
  records, matching the trace count. This startup transition lies before the
  analysed CSV (3057–28344), not within a test phase. It does not explain the
  earlier missing record 19575 during washout.
- The 91 trailing bytes follow the diagnostic stop; they are outside the
  analysed sample stream. The 1,536-byte frozen-query receive buffer separately
  reproduces the reported trace. Its metadata records are complete.

This is a clean instrumented run with no fault to localise. It verifies the
diagnostic workflow and configured GVIA response but does not identify or fix
the preceding intermittent timing/record-loss causes. Instrumentation also
changes execution timing; passing it is not proof that the old firmware's
intermittent issue is gone. All earlier failures remain retained.

Evidence: `vc_synapse_20261030_214914_049603.zip`.
Archive SHA-256: `19b9fac2758034439c092f31a33de54beb7e9d065049f638cf5b3fd41e1b656e`.
CSV SHA-256: `036ed25806340bec56c782dbf4829bf091f93515070c7c310e567f7176ba2bce`.
Raw RX SHA-256: `357fea5219dc244bd9dc310ea1063b79cc92039edf3134c01d82766a3d9dd1b3`.
Chunk CSV SHA-256: `550ab4260c48074a91c81df929bca4fe5b15338c1e4561ce0a825d68108d5f3e`.
Trace query SHA-256: `7d56d083bf43b685c44507f4b637b75731c8df95303574b42f26b4b5655d0011`.

## Pre-defined extended observation, PC-only runner 1.3

Next is one instrumented 60 / 60 / 60 wall-second control / GVIA / washout
capture, using installed 3d78f06 firmware with no upload. Runner 1.3 adds
`--phase-seconds 12|30|60` for automatic cases 15–20, preserving default 12
and case 14. It records the requested duration and adds a duration/sample-count
check for extended captures, without relaxing existing criteria. A normal
12-second correct-response recording cannot pass as the requested long test.
Raw timestamp capacity increases to 600,000 batches; the 32 MiB raw-byte cap,
explicit truncation FAIL and five-minute acquisition limit remain. The larger
timestamp cap is needed because the first 55-second raw capture already used
75,800 batches. Firmware, receptor/membrane equations and doses are unchanged.

Validation: **126 native/host tests PASS**, including complete three-minute
native-sketch GVIA response, rejection of a short capture presented as long,
and an otherwise complete long recording retaining a deadline FAIL. Targeted
trace tests also verify timestamp-cap truncation is counted while raw-byte
draining continues. One full real-pyserial/PTY 60/60/60-second CLI capture
passes all original and extended criteria with actual sketch/parser and
simulated IO, saves complete raw/trace files and resumes CC. This is software
validation with an externally paced native clock, not physical ESP32 timing.
The pre-defined extended physical capture remains pending.
