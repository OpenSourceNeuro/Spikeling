# Active VC timing correction — 30 October 2026

## Physical rerun: first active step PASS

The 01_active_step rerun with firmware identity clock=2,gates=2 and runner 1.1
passes all checks. Both reports and independent re-analysis of the 1,702-sample
CSV agree. The optimised firmware tested is ddabb4a.

| Check | Optimised physical recording |
| --- | ---: |
| Average update rate | 500.0752 Hz |
| Complete one-second windows | 499.9310 to 500.2049 Hz |
| Median / maximum previous loop | 1,543 / 1,667 microseconds |
| Median / maximum solver | 256 / 271 microseconds |
| Deadline flags / other diagnostic flags | 0 / 0 |
| Maximum Vm reference error, ideal clamp | 0 mV |
| Maximum clamp-current reference error | 0.0007481 nA |
| Maximum gate reference error | 0.0000005673 |
| Peak inward Na / late outward K | -3.084861 / +1.995735 nA |
| CC binary stream after cleanup | Resumed |

The slowest recorded loop has 333 microseconds of margin against the 2 ms
period. Median solver time falls from 1,252 to 256 microseconds, while the
waveform/reference checks remain passing. This verifies the timing correction
for this ideal-clamp protocol on the tested board; finite-access and blocker
protocols have not yet been run physically. PC receive timestamps establish
average cadence, not individual output edge jitter. Actual normal CC firing,
TTL edges and DAC calibration are separate physical observations.

## Physical TTX and TEA checks: PASS

The 02_TTX and 03_TEA physical recordings at ddabb4a pass all numerical,
response, continuity, input and timing checks. Independent CSV re-analysis
confirms both reports. The following compares each 200-sample ideal-clamp pulse
with the earlier control at the same -70 to -20 mV command:

| Condition | Peak inward Na, nA | Late outward K, nA | Update rate, Hz | Maximum loop, microseconds |
| --- | ---: | ---: | ---: | ---: |
| Control | -3.084861 | 1.995735 | 500.0752 | 1667 |
| TTX 92 nM | -0.280442 | 1.995735 | 499.9851 | 1679 |
| TEA 5 mM | -3.084862 | 0.181430 | 500.0018 | 1665 |

Both blockers leave the expected 1/11 (9.09%) of their targeted current,
a 90.91% reduction under the existing illustrative Hill model. Maximum waveform
error relative to this scaling is 0.0000005455 nA for either targeted component.
The preserved K trace changes by 0 nA under TTX; the preserved Na trace differs
by at most 0.000001 nA under TEA. Recorded m/h/n traces are unchanged across
the pulse at the CSV precision, as expected when ideal Vm is imposed.

TTX has 1,701 contiguous samples; TEA has 1,704. Every diagnostic flag is zero,
and both top-level reports confirm return to CC binary streaming. These are
selected-dose checks of the implemented educational pharmacology, not a new
biological potency calibration or validation of all drug combinations.

## Original failure on the physical ESP32-S3

The uploaded 01_active_step recording from original active commit 6f37a74
contains 1,705 contiguous samples, with zero external input and no diagnostic
flags other than deadline flag 64. Both provided reports and the CSV agree:

| Check | Physical recording |
| --- | ---: |
| Average update rate | 384.7816 Hz, target 500 Hz |
| One-second window rates | 381.0077 to 385.9329 Hz |
| Median / maximum previous loop | 2,575 / 2,729 microseconds |
| Median / maximum HH solver | 1,252 / 1,325 microseconds |
| Median non-solver loop work | 1,323 microseconds |
| Deadline flag count | 1,705 of 1,705 samples |
| Vm reference error, ideal clamp | 0 mV |
| Maximum clamp-current reference error | 0.0007481 nA |
| Maximum gate reference error | 0.0000005110 |
| Maximum current-balance residual | 0.000001 nA |
| Peak inward Na / late outward K | -3.084862 / +1.995735 nA |
| CC binary stream after cleanup | Resumed |

The failure is a genuine firmware compute overrun. Median non-solver work pairs
each reported previous-loop duration with the PRECEDING sample's solver time;
the diagnostic columns refer to different ticks. PC receive gaps do not explain
away the device's measured 2.6 ms loops. The sodium transient and delayed
potassium response already pass; the complete test correctly remains FAIL.

## Firmware change

Normal HH gate updates now interpolate equilibrium values and exponential
update fractions from a 0.25 mV grid over -250..250 mV at fixed 6.3 C.
The 48,024-byte table is generated from the independent canonical HH rate
functions by generate_vc_gate_table.py. It resides in .flash.rodata, verified
in the ESP32 ELF; global RAM consumption remains unchanged.

The four internal 0.025 ms steps, half-step gate ordering, conductances,
reversal potentials, access/compliance solver, current averaging, shared
inputs, pharmacology, CC handover and numerical acceptance limits are retained.
General nonstandard model timesteps retain the original analytic gate fallback.
Active identity gains gates=2 so runner 1.1 can detect an old upload.
Failure messages now print clock and deadline metrics directly.

Linker-wrapped native call-count tests verify, for a normal 0.1 ms output tick:

| Backend | Original exp/expm1 calls | Optimised calls |
| --- | ---: | ---: |
| Ideal clamp | 72 gate calls | 0 |
| Finite access | 72 gate + 8 voltage calls | 8 voltage calls |

This counts expensive calls; it does NOT predict or measure ESP32 execution time.
The physical rerun above verifies the first ideal protocol; further protocols
still require their own board timing checks.
The 2 ms period, 500 Hz target and deadline-failure rule have not been relaxed.

## Verification

- **69 native tests PASS**, including all original 63 regression/model/analyser
  checks and six new optimisation checks.
- A dense 16,004-point sweep covers both table endpoints, the removable HH
  singularities and voltages between grid points. Equilibrium and update-fraction
  errors are each below 0.00002; all fractions remain in [0,1].
- Voltages midway between table entries pass the independent current/gate
  reference checks; existing ideal and coupled-access ODE tolerances still pass.
- The generated header matches its generator exactly. Normal ideal updates
  make no exp/expm1 calls; finite access retains its eight voltage calls;
  a nonstandard timestep exercises the analytic fallback.
- Re-analysis of the uploaded physical CSV still FAILS at 384.782 Hz with 1,705
  deadline flags, while numerical and teaching-response checks pass. The update
  does not conceal or relabel the original timing failure.
- The complete sketch and real SerialCommand parser compile with simulated
  ADC/DAC/clock IO. The eight-case pyserial/PTY runner integration is verified
  separately; its externally imposed tick rate is not ESP32 timing evidence.

ESP32 build: Arduino CLI 1.5.1, ESP32 Arduino core 3.3.12, target:

    esp32:esp32:esp32s3:USBMode=hwcdc,CDCOnBoot=cdc,FlashSize=4M,PSRAM=disabled

Compilation PASS: **405,201 bytes** program storage, **24,224 bytes** globals,
**303,456 bytes** remaining for stack/local variables under the reported build.
The flash-table trade-off adds about 48 kB program storage, without adding RAM.
The build and packaged source hashes are checked against the committed source.

## Next board action

Keep the verified ddabb4a firmware installed. Run 04_access_resistance using
runner 1.1 and the same quiet-input setup. This selects a finite 5 MOhm access
resistance; voltage lag and current-dependent departure from Vcmd are expected.
Numerical agreement is assessed against the coupled finite-access ODE reference,
not against exact equality of Vm and Vcmd. Send its report, CSV and plot.
Then test reversals, holding-voltage inactivation and potassium tails.
Required outcomes remain 500 Hz within 2%, loop duration below 2 ms, zero deadline
flags and all existing waveform/numerical checks passing. Check actual knob-
controlled CC firing in the GUI after cleanup; resumed binary data alone is not
proof of physical firing, TTL timing or calibrated DAC output.

## Model scope and sources

Na/K/leak VC retains the integrated-v2 shared pharmacology conventions. TTX/TEA
scale Na/K conductance. Receptor/GVIA pathways retain their existing adapters;
combined pharmacology/IO bench validation is still ahead. Apamin/SK and 4-AP/A
currents are absent from active VC and raise unsupported flag 32. The separate
STP/LTP branch and new GUI controls are not merged.

The HH rate structure comes from NEURON hh.mod, which also uses tabulated gating
kinetics: https://github.com/neuronsimulator/nrn/blob/master/src/nrnoc/hh.mod
Our 0.25 mV grid, cached half-step fractions and interpolation-error bounds are
implementation choices established by the checks above. This change optimises
the existing educational model; it adds no new biological mechanisms.
