# Synaptic VC test pack — validation and scope

30 October 2026. PC-side tools for the existing `5c2e063` active firmware;
no changes to `Firmware/Spikeling_V3` or its numerical/timing thresholds.
The user has confirmed access to a second Spikeling and a stereo TRS cable.
The first requested physical capture is `14_synaptic_input --synapse 1` on COM13.
Basic Synapse 1 and Synapse 2 now have verified passing physical captures
(see below). Case 15 now has a verified NBQX response but its first run FAILS
timing; a repeat is next. Cases 16 to 20 remain pending physical-board evidence.

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
