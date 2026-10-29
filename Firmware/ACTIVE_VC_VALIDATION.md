# Active VC timing correction — 30 October 2026

## Measured failure on the physical ESP32-S3

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
A physical rerun is required before declaring the timing problem resolved.
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

Upload the entire timing-optimised Spikeling_V3 sketch, then repeat only
01_active_step using runner 1.1. Keep Patch centred, Noise minimum, PD gain zero
and incoming signal cables disconnected; close the GUI and Serial Monitor.
Send the top-level report.json, 01_active_step/recording.csv and recording.png.
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
