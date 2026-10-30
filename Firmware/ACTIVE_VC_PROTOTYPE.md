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
NBQX/gabazine/APV and deterministic GVIA release scaling. Firmware remains at
5c2e063. Start with case 14 on Synapse 1; all new physical captures are pending.
See VC_SYNAPTIC_WINDOWS.md and VC_SYNAPTIC_VALIDATION.md. The native suite now
passes 100 tests, with source GPIO/clock/serial simulated.
