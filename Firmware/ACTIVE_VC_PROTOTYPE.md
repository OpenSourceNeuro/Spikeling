# Active voltage-clamp prototype

This experimental firmware extends the passive prototype at `08212b9`.
The passive prototype passed the user's RC, input and clock bench checks on
29 October 2026. The initial active model passed its current/shape checks on that board, but
failed the 2 ms timing budget. The optimised revision at ddabb4a passed the
first ideal-clamp active step on the physical board on 30 October 2026:
500.075 Hz, zero deadline flags, and all numerical/response checks passing.
Single-dose ideal-clamp TTX (92 nM) and TEA (5 mM) tests also pass on the
physical board, with selective 1/11 current scaling and no deadline flags.
The first finite-access recording passes the coupled-model numerical checks,
but one 2.048 ms loop exceeds the 2 ms budget. The subsequent voltage=2
revision at 5c2e063 removes a redundant voltage exponential and passes the
physical access rerun: 499.907 Hz, zero diagnostic/deadline flags, maximum
loop 1.945 ms, and all coupled-model numerical checks passing.
Physical reversal, holding-voltage inactivation and potassium-tail cases also
pass at 5c2e063: approximately 500 Hz, no diagnostic/deadline flags and maximum
loops no greater than 1.674 ms. The staged sequence now has passing recordings
for all eight core protocols. The five first-stage integration cases also have
passing physical captures: noise, light, Patch command, five mode-switch cycles
with retained half-block TTX/TEA effects, and one minute of settled access VC.
The first Patch run's isolated 22.9 ms pause and unconfirmed cleanup remain
recorded despite a passing repeat; its cause is unresolved. Synaptic/receptor/
release pharmacology, mixed-input timing and physical output calibration remain.
See ACTIVE_VC_VALIDATION.md for the evidence, scope and revision of each capture.
Keep the working passive ZIP as a fallback.

## Model and switching

Boot uses original Izhikevich current clamp, pharmacology OFF, active VC OFF.
`VCM 1` selects voltage clamp; `VCA 1` selects the active backend.
`VCA 0` restores passive VC; `VCM 0` restores Izhikevich CC.
Changing the active selector while in CC never changes its equations.
Changing backends preserves present Vm; HH gates initialise at that voltage.
Entering VC resets its model-tick counter and anchors the wall clock.
Leaving VC uses present Vm and evolved Izhikevich recovery variable u;
output rearming suppresses a false inherited spike. No VC spike reset, TTL
spike or buzzer pulse is generated, including at commands above +30 mV.
Vm DAC and Vm LED follow the simulated voltage with their existing mappings.

The active membrane is a single compartment with HH Na activation m,
Na inactivation h, delayed-rectifier activation n, and passive leak:

    I_Na = 0.240 * m^3 * h * (Vm - 50)       [nA]
    I_K  = 0.072 * n^4 * (Vm + 77)           [nA]
    I_L  = (Vm - E_L) / Rm                  [nA]
    (Cm/1000) dVm/dt = I_clamp + I_input - I_Na - I_K - I_L - I_receptor

Here g is in uS, Vm in mV, Cm in pF, R in MOhm, and t in model ms.
Positive ionic current is outward. Positive external/input or clamp injection
is inward. At steady clamp the reported injected current equals the sum of
outward membrane currents minus other inward input currents.
All currents in diagnostic records are interval means, with Vm/gates at the
interval end. Capacitive current includes voltage-step charge; an ideal-clamp
command jump is averaged over its 0.1 ms output bin, not an infinite spike.
Ideal mode intentionally ignores current compliance; access mode enforces it.

Kinetics use the canonical absolute-voltage HH rate functions in NEURON
hh.mod at a fixed *model temperature* of 6.3 C, independent of room temperature.
The 240/72 nS conductance choices retain the canonical ratio while reducing
channel density to suit the teaching cell. Cm=20 pF, Rm=500 MOhm,
E_L=-70 mV and Rs=5 MOhm keep the validated passive defaults.
These combined parameters are an educational choice, not a fitted preparation.
Na reversal is +50 mV; K reversal is -77 mV. Command range remains -110..+80 mV.

The membrane uses four internal steps per 0.1 ms output bin. Normal gate
half-steps use equilibrium values and exponential update fractions precomputed
on a 0.25 mV grid over -250..+250 mV, with linear interpolation. The 48,024-byte
constant table resides in flash. It avoids 72 gate exp/expm1 calls per normal
output tick while retaining the same four internal steps. General nonstandard
timesteps use the analytic fallback. The table is generated reproducibly by
Firmware/tools/generate_vc_gate_table.py at the fixed model temperature 6.3 C.
No temperature or timestep setting can silently reinterpret this table.
The voltage=2 revision reuses a single expm1 result for both the exact voltage
endpoint and mean, halving voltage-solver exponentials. Access conductance is
computed once per internal step and reused in double precision.
Each frozen-conductance membrane step reuses the
validated exact passive/access/compliance solver. Failed internal steps leave
membrane and gate states unchanged and raise solver flag 4. Active steps reject
Vm outside -250..+250 mV rather than silently clipping it. This is a supported
numerical domain, not a biological voltage bound.

The scheduler remains 2,000 microseconds per tick (500 Hz). Each tick advances
0.1 model ms: the demonstration runs 20 times slower than its model time.
Timing is judged independently of numerical agreement. Flag 64 still fails a
capture, even if its equations agree. PC arrival times establish average rate,
not individual hardware edge jitter. No nonblocking-USB redesign is claimed.

## Shared inputs and pharmacology

Patch control, Current-In command routing, photodiode, noise, both synapses,
stimulus output, physical toggles, and existing binary packet layout are retained.
Inputs and receptor/release states advance once per outer tick, independently
of HH substeps. Direct VCMD/VSTEP commands still ignore the Current-In voltage
command; hardware-source VC accepts it as a voltage command, not an extra current.
The source branch's actual input routing is retained; no new independent injected
stimulus-current path is invented.

The six pharmacology modules are taken from the current frozen integrated-v2
validation kit dated 28 October 2026, not from the older unconnected two-header
snapshot. Its existing PH command family, drug units, Hill occupancies, CC
phenomenology, receptor states and independent release RNG streams are retained.
This is a consolidation for experimental testing, not a claim of combined
physical-board pharmacology validation.

| Effect | Active VC behaviour |
| --- | --- |
| TTX, PH D 0, nM | gNa multiplied by 1 - C/(9.2+C) |
| TEA, PH D 1, mM | gK multiplied by 1 - C/(0.5+C) |
| NBQX / gabazine | Existing AMPA / GABA-A block; requires explicit receptor selection |
| APV | Existing NMDA block, when conductance/NMDA mode is selected |
| GVIA | Existing event-time presynaptic release effect, when presynaptic mode is enabled |
| Apamin / 4-AP | SK/A channels absent: raise unsupported flag 32; do not invent an effect |

Concentrations are the existing educational conventions, not universal IC50s.
CC continues to use the integrated-v2 intrinsic phenomenology when PH E 1;
PH E 0 keeps the original CC equations. Stored doses and receptor/RNG states
survive CC/VC handover. Auxiliary CC availability relaxes during VC, without
running a CC voltage update. HH gates are separate states, not the CC h_na proxy.
Synaptic conductances enter the VC membrane through sum(g) and sum(gE), preventing
double counting and preserving their reversal potentials. NMDA magnesium unblock
is evaluated once at the outer-tick Vm and frozen during that 0.1 ms bin.
This approximation should be revisited before high-precision NMDA protocols.

STP/LTP from the separate development branch is not merged into this prototype.
Its future release/weight stage must precede the shared receptor update and must
not sample release again inside the membrane solver.

## Protocol additions

- `VCA 0|1`: select passive or active VC. No change to membrane charge.
- `VCINFO`: passive identity remains VC-PASSIVE-1; active identity is VC-ACTIVE-1.
  Both include units and `clock=2`; the timing-optimised active version also
  includes `gates=2,voltage=2`. Runner version 1.2 requires both markers.
- Passive CSV remains VC1 with its existing fields.
- Active CSV is VC2: sequence,time_ms,command_mV,voltage_mV,clamp_nA,
  capacitive_nA,leak_nA,input_nA,flags,solve_us,previous_loop_us,
  sodium_nA,potassium_nA,receptor_nA,m,h,n.
- VCT 0 returns the existing binary packet; VCT 1 selects diagnostic CSV.
- Existing VCP, VCL, VCI, VCMD, VSTEP and VRS commands retain their meanings.

Existing GUI VC labels have not been updated for these quantitative units.
Use the Python tools for active-current measurements. No new GUI toggle is included.
The runner restores PH E 0, passive backend, access mode, CC and Patch knob control.
It does not restore previous drug doses/receptor selections; it deliberately
configures and clears them for reproducible bench tests.

## Tests and remaining work

Run from repository root:

    python -m unittest discover -s Firmware/tests/vc -v

Requires numpy, scipy, g++, git, and pinned baseline commit 927a70a locally.
The independent Python reference uses exact gate/product integrals under ideal
voltage clamp and DOP853 for coupled Vm/gate/access dynamics. It does not copy
the firmware's split-step method. The 39 passive regression tests include packet
comparison with the original CC path for all 20 presets under the tested inputs.
Active tests cover Na transient/inactivation/recovery, delayed K, reversal,
current balance, compliance, shared inputs, dose scaling, receptor reversal,
NMDA/APV, release RNG sampling and mode transitions.

Physical validation sequence: first active step and timing; then TTX/TEA;
then access resistance and reversals; then combined receptor/pharmacology and
hardware IO. SK/A-current extensions and STP integration follow as distinct
changes. A passing serial test does not calibrate DAC voltages or TTL edges.

## Scientific sources

- Hodgkin AL, Huxley AF (1952). A quantitative description of membrane current
  and its application to conduction and excitation in nerve. J Physiol 117:500-544.
  https://doi.org/10.1113/jphysiol.1952.sp004764
- NEURON canonical HH mechanism; rate functions and 6.3 C convention, consulted
  29 October 2026: https://github.com/neuronsimulator/nrn/blob/master/src/nrnoc/hh.mod
- Gerstner et al., Neuronal Dynamics, section 2.2; voltage-clamp interpretation
  of gating and driving force: https://neuronaldynamics.epfl.ch/online/Ch2.S2.html
- Rush S, Larsen H (1978). A practical algorithm for solving dynamic membrane
  equations. IEEE Trans Biomed Eng 25:389-392. https://doi.org/10.1109/TBME.1978.326270

These sources ground the channel/gating structure. Conductance scaling,
passive parameters and teaching test thresholds are our explicit design choices.

## Two-Spikeling synaptic test pack

The user has a second Spikeling and stereo TRS cable. The Python-only cases
14 to 20 now cover received AMPA input on either synapse, AMPA/GABA-A reversals,
NBQX/gabazine/APV and deterministic GVIA release scaling. Initial synaptic
captures use 5c2e063; diagnostic/guarded follow-ups name their revisions below.
Case 14 on physical Synapse 1 passes with runner 1.1: 21,670
contiguous samples, 499.985491 Hz, zero flags, maximum loop 1,561 us, 22 resolved
events and resumed CC streaming. The Synapse 2 repeat also passes: 23,460
contiguous samples, 499.987518 Hz, no flags, maximum loop 1,535 us and resumed
CC streaming. Both inputs give the configured -0.099 nA event contribution.
Case 15 NBQX now has a verified passing repeat: 26,409 samples, 499.994257 Hz,
no flags, maximum loop 1,607 us and resumed CC streaming, with the expected
half-block and washout. Its first timing FAIL remains recorded below. Next is
a focused finite-access case-13 repeat after the guarded extended GVIA PASS
on Synapse 1: case 19 NMDA/APV passes with 24,928 samples,
499.993319 Hz, zero flags, maximum loop 1,690 us, selective NMDA half-block,
preserved AMPA and washout. Case 18 GABA-A reversal also passes, with
31,812 samples, 499.996309 Hz, zero flags, maximum loop 1,621 us and reversal
near -80 mV. Case 17 AMPA reversal passes
with 25,591 samples, 499.995562 Hz, zero flags, maximum loop 1,634 us and
reversal near 0 mV. Case 16 gabazine passes with
24,230 samples, 500.000290 Hz, no flags, maximum loop 1,620 us and confirmed
half-block/washout and CC cleanup. Case 20 now passes on instrumented 3d78f06
firmware, with 25,288 samples, zero flags, maximum loop 1,673 us and matching
GVIA efficacy. The extended follow-up FAIL localises 20.501 ms to the serial-write
span. Its c70dff2 guarded follow-up now passes with 100,891 analysed samples,
zero flags, max loop 1,858 us and complete raw/trace evidence. Keep this firmware
and kit for the focused case-13 repeat; see VC_SYNAPTIC_VALIDATION.md.
See VC_SYNAPTIC_WINDOWS.md and VC_SYNAPTIC_VALIDATION.md. The native suite now
passes 131 tests, with source GPIO/clock/serial simulated, including startup,
duration and guarded-transport regressions.

The first physical case 15 NBQX capture verifies the configured half-block and
washout but FAILS overall: one 22.256 ms loop occurs before received events or
drug application, with only 262 us in its preceding measured HH solve. Cleanup
succeeds. This runtime timing issue remains unresolved; repeat case 15 once
with the same kit/firmware, retain the failure and instrument IO timing if it
recurs. Cases 16 to 20 remain pending; no thresholds or model parameters change.

The unchanged case-15 repeat passes all criteria, with 22 events per phase and
NBQX/control ratio 0.499999168 followed by washout/control 1.000000062. It does
not resolve the earlier intermittent timing pauses. Keep that issue open while
proceeding to case 16 gabazine with the same kit, firmware and Synapse 1 wiring.

Case 16 gabazine passes with outward-positive GABA-A event contributions
+0.099 / +0.0495 / +0.099 nA at -70 mV (35 resolved events per phase).
Next is case 17 AMPA reversal using the same kit/wiring; the script restores
AMPA and changes holding voltage automatically. The earlier isolated runtime
pauses stay open; no firmware, model or acceptance limits have changed.

Case 17 AMPA reversal passes: event contributions at -70/-20/+20 mV are
-0.09900047321 / -0.02828581351 / +0.02828583075 nA, with fitted zero near 0 mV,
clean timing and resumed CC streaming. Next is case 18 GABA-A reversal using
the same kit/wiring. Previous isolated timing failures remain open; no model,
firmware, tool or acceptance limits change.

Case 18 GABA-A reversal passes: event contributions at -90/-70/-50 mV are
-0.09900052643 / +0.09900053548 / +0.29700147581 nA, with fitted reversal near
-80 mV, clean timing over 63.62247 wall seconds and resumed CC streaming.
Next is case 19 NMDA/APV, testing selective slow-component block with preserved
fast AMPA and washout at -20 mV. Existing kit/firmware/criteria remain unchanged;
earlier intermittent timing pauses remain open.

Case 19 NMDA/APV passes: at -20 mV, fitted slow-component drug/control is
0.5000000438 and washout/control is 0.9999991081; fast AMPA drug/control is
0.9999985723. Timing, independent membrane/receptor checks and CC cleanup
pass. Settled recovery has a small nonzero tail (maximum 0.001399 nA), within
the original quiet limit. Next is case 20 GVIA, testing deterministic
presynaptic release scaling at -70 mV: event-amplitude ratio 0.561515625 at
simulated 10 nM, then washout. Same kit/firmware and thresholds; earlier
intermittent timing pauses remain unresolved.

Four subsequent case-20 console logs report overall FAIL: three have passing
receptor phases but single loop-deadline failures (23,312 / 16,665 / 23,226 us),
and one reports a missing or duplicated device sample. These logs have not yet
been checked against their CSVs/reports. Pause repeated case-20 attempts and
review all four original captures before targeted timing/transport changes.
Average cadence near 500 Hz does not excuse individual deadline failures.
Keep the installed firmware and all criteria; no specific cause or permanent
fix is established. See VC_SYNAPTIC_VALIDATION.md for the evidence ledger.

All four GVIA captures are now independently reviewed (113,290 rows). The three
timing failures lie outside their measured HH solves; the remaining capture
is missing exported sequence 19575, with no observed deadline flags. All four
reports confirm CC cleanup. GVIA response ratios in the contiguous captures
match the configured 0.561515625 efficacy, but no overall PASS is claimed.

An opt-in diagnostic revision adds stage timing and serial short-write evidence
in a fixed buffer, plus runner 1.2 raw-byte capture. It changes no model
equations or existing protocols/thresholds. Native tests (123) and two full
serial workflows validate normal GVIA capture and an intentionally missing
sample using simulated IO. ESP32 cross-compilation is unavailable here;
the source kit requires local Arduino Verify/upload and includes 5c2e063 for
rollback. One instrumented case-20 capture is next. No cause or permanent
timing fix has been established; prior failures remain retained.

The first physical instrumented case-20 capture passes: 499.987686 Hz,
25,288 analysed samples, max loop 1,673 us, zero flags, intact raw data and
resumed CC streaming. Drug/control is 0.5615156405, washout/control 0.9999999423.
The 27,519-tick firmware trace has zero exception counters; no earlier pause
or record-loss fault recurred, so there is no cause or permanent fix to infer.
Earlier failures remain retained. A PC-only duration option in runner 1.3
supports one 60/60/60-second observation using the same installed firmware.
All existing criteria and model parameters remain unchanged; see the extended
Windows guide and VC_SYNAPTIC_VALIDATION.md.

Runner 1.3 passes 126 native/host tests and a full three-minute serial workflow
with simulated IO, raw bytes, trace retrieval and CC cleanup. The extended
physical observation is next; the firmware remains the user's tested 3d78f06.

The extended physical follow-up FAILS despite correct GVIA/model/phase-duration
checks: one 22.022 ms loop, with 20.501 ms in the serial-write span and HH solve
0.276 ms. All bytes/analysed records are intact and CC cleanup succeeds. This
locates the elapsed stall but does not establish its host/SDK cause. The next
prototype guards active-VC2 writes with a preallocated 4,096-byte Hardware CDC
buffer and zero-wait whole-frame capacity checks on pinned core 3.3.12. Capacity
skips or short writes latch flag 128 and remain FAIL. Trace protocol 2 and
runner 1.4 retain original numerical/timing criteria. ESP32 cross-compilation
is unavailable here; local Verify/upload is required before physical checking.
Earlier failures remain retained; no permanent timing fix is yet established.

Guarded transport software checks: 131 native/host tests PASS; a full
three-minute serial workflow with simulated 20 ms host backpressure passes,
while explicit short-write/full-FIFO workflows remain FAIL and preserve
diagnostics/cleanup. Physical guarded-transport timing has not yet been tested.

Guarded c70dff2 now has a passing extended physical GVIA capture: 100,891
analysed samples, 500.000115 Hz, zero flags, max loop 1,858 us and resumed CC.
The 102,948-tick trace has zero overruns, short writes or capacity skips;
write-span maximum is 87 us. Raw bytes independently reproduce all analysed
records/timestamps, and GVIA efficacy/washout match the configured model.
Earlier intermittent causes remain open; this is one condition and a different
source event rate, not proof of permanent correction. Next is one existing
finite-access case-13 stress capture on this same firmware, then GUI/CC checking.
