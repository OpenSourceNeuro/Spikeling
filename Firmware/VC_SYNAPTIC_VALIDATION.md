# Synaptic VC test pack — validation and scope

30 October 2026. PC-side tools for the existing `5c2e063` active firmware;
no changes to `Firmware/Spikeling_V3` or its numerical/timing thresholds.
The user has confirmed access to a second Spikeling and a stereo TRS cable.
The first requested physical capture is `14_synaptic_input --synapse 1` on COM13.
All cases below remain pending physical-board evidence.

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
