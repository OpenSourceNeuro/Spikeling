# Active VC verification and access-timing revision — 30 October 2026

All eight core active VC protocols now have passing physical recordings across
the staged validation sequence: cases 01 to 03 at ddabb4a, and cases 04 to 08
at voltage=2 revision 5c2e063. This is not a single eight-case run at one revision.
The five first-stage integration protocols also have passing captures at
5c2e063, including repeated switching and a one-minute access recording.
The current code passes 84 software tests; the firmware source retains the
verified ESP32 build. Synaptic/release pharmacology, mixed-input timing and
physical output checks remain, together with the unresolved isolated pause
documented below.

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
for this ideal-clamp protocol on the tested board. The subsequent blocker and
finite-access recordings are documented below. PC receive timestamps establish
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

## Finite access: numerical PASS, one deadline failure

The physical 04_access_resistance run at ddabb4a contains 1,703 contiguous
samples and quiet inputs. Both reports and independent CSV re-analysis agree:

| Check | Physical finite-access recording |
| --- | ---: |
| Average rate / complete one-second windows | 499.8511 Hz / 499.7708 to 499.8996 Hz |
| Median / maximum previous loop | 1,905 / 2,048 microseconds |
| Median / maximum solver | 531 / 567 microseconds |
| Deadline flags / all other diagnostic flags | 1 / 0 |
| Maximum coupled-reference Vm error | 0.0298423 mV |
| Maximum clamp-current reference error | 0.0030423 nA |
| Maximum gate reference error | 0.0003433 |
| Maximum current-balance residual | 0.000002 nA |
| Late step Vm / command | -26.91563 / -20 mV |
| Late clamp current | 1.38312 nA |
| CC binary stream after cleanup | Resumed |

The 18.5447 mV maximum deviation from Vcmd includes early capacitive lag;
it is not the numerical solver error. The late approximately 6.916 mV offset
matches 5 MOhm times 1.383 nA. The Na-associated overshoot, altered gating and
late K-related offset agree with the independent coupled ODE. The only failed
criterion is one genuine 48-microsecond deadline overrun. Average rate alone
does not make this a PASS; the small nominal timing margin warrants improvement.

## Second timing revision: voltage=2

The shared passive/access solver previously computed exp(-z) for the endpoint
and expm1(-z) separately for the exact interval mean. It now computes q=expm1(-z)
once, using the mathematically equivalent formulas:

    V_end  = V_start + (V_start - V_equilibrium) * q
    V_mean = V_equilibrium + (V_start - V_equilibrium) * (-q) / z

This retains the analytic RC/access/compliance solution and all four active
substeps. A normal active access tick now uses four voltage special-function
calls rather than eight; ideal mode still uses none. The model parameters,
gate table, current averaging, current limits, shared inputs and acceptance
criteria are unchanged. Cached double-precision access conductance also removes
repeated divisions and avoids premature float rounding of Vcmd/Rs, exposed by
the new extended parameter sweep at very low access resistance.

**70 native tests PASS**, including every earlier test and a new long-double
reference sweep of endpoint voltage, mean current and capacitive charge across
108 combinations of Cm, Rm, Rs and numerical dt. Compiler output confirms
405,265 program bytes, 24,224 global bytes and 303,456 remaining bytes with
ESP32 Arduino core 3.3.12 and the existing target. The four-call hot path is
verified by wrapped exp/expm1 counters. These are software/build checks, not a
measurement of the new board execution time. The eight-case simulated serial
workflow is checked separately.

The active identity adds voltage=2; runner 1.2 requires it alongside gates=2.
The original finite-access CSV remains a FAIL under the updated analyser,
with one deadline flag. No timing threshold or numerical tolerance is relaxed.
The physical rerun below now verifies this voltage=2 revision for the access case.

## Physical finite-access rerun at voltage=2: PASS

The 04_access_resistance recording at 5c2e063, identified by
clock=2,gates=2,voltage=2 and runner 1.2, passes all existing checks. Independent
offline re-analysis of the uploaded CSV agrees with both reports. The 1,703
samples are contiguous, include the complete 200-sample pulse and recovery,
and have quiet inputs and no diagnostic flags.

| Check | Physical voltage=2 recording |
| --- | ---: |
| Average rate / complete one-second windows | 499.9067 Hz / 499.4994 to 500.0808 Hz |
| Median / 99th percentile / maximum previous loop | 1,785 / 1,840 / 1,945 microseconds |
| Median / maximum solver | 466 / 503 microseconds |
| Deadline flags / all other diagnostic flags | 0 / 0 |
| Maximum coupled-reference Vm error | 0.0298423 mV |
| Maximum clamp-current reference error | 0.0030423 nA |
| Maximum gate reference error | 0.0003433 |
| Maximum current-balance residual | 0.000002 nA |
| Late step Vm / command | -26.91563 / -20 mV |
| Late clamp current | 1.38312 nA |
| CC binary stream after cleanup | Resumed |

Compared with the previous finite-access run, median loop time falls by
120 microseconds and median solver time by 65 microseconds. The reference
errors remain unchanged at the precision shown. The maximum loop has
55 microseconds of margin in this approximately 3.405-second analysed capture;
this result is not a long-duration or mixed-input timing qualification.

The late command-to-Vm difference is 6.91563 mV; Rs times mean clamp current
is 6.91560 mV. This is the intended access-resistance error, distinct from the
0.02984 mV numerical error against the coupled reference. No firmware changes,
threshold relaxation or repeat of cases 01 to 04 is needed for the next checks.

Evidence: report(20261030-070810).json (top-level live report),
report(20261030-070817).json (case report), recording(8).csv and recording(10).png.
CSV SHA-256: cbb1b53ca6e3af1f885d09286cc8960f566da598f00dc5c127e81a2b118d9eb2.

## Physical reversal, inactivation and tail checks: PASS

The four recordings in vc_active_20261030_082606.zip use runner 1.2 and
clock=2,gates=2,voltage=2. Independent re-analysis of all four CSVs with the
exact constant-voltage gate/product reference confirms every numerical,
response, clock and diagnostic check. All 6,814 samples are contiguous within
their respective recordings; every pulse has 200 samples and complete recovery.
All flags are zero and all four top-level live reports confirm resumed CC
binary streaming after cleanup.

| Case | Recorded response | Update rate, Hz | Maximum loop, microseconds |
| --- | --- | ---: | ---: |
| 05_sodium_reversal | Na current is zero throughout the +50 mV pulse | 499.9957 | 1674 |
| 06_sodium_inactivation | Peak Na -0.294541 nA after a -40 mV hold | 499.9433 | 1670 |
| 07_above_sodium_reversal | Peak outward Na +1.160989 nA at +60 mV | 499.9403 | 1651 |
| 08_potassium_tail | Initial inward K tail -0.440375 nA at -90 mV | 499.9628 | 1674 |

The largest clamp-current reference error across these four recordings is
0.0019513 nA, the largest gate error is below 0.000000548, and Vm follows the
ideal command exactly. Current-balance residuals are at most 0.000002 nA.
Complete one-second windows also pass the unchanged 500 Hz +/-2% criterion.

For case 06, peak inward Na is 9.548% of the earlier -70 mV-hold control
(-3.084861 nA), a 90.452% reduction. The pre-step h gate is 0.050441 versus
0.754080 at -70 mV. This is holding-voltage inactivation with no blocker present;
the drug-dependent gNa multiplier remains 1. At the sodium reversal potential,
K and leak currents still contribute
to total clamp current. At -90 mV, the K driving force is negative relative to
the model's -77 mV K reversal; the inward tail decays to -0.000040 nA as n closes.

These results complete the core Na/K/leak bench sequence. They do not establish
combined receptor/blocker behaviour, active-VC physical input routing, repeated
CC/VC handover, calibrated analogue output or long-duration timing robustness.
No firmware adjustment or repetition of the completed cases is needed to
proceed to integration checks.

Evidence archive SHA-256:
f9b7eb328a4f0af21cb539df14dc6c68e3dbb64a12108f21222104dfc7602ba3.
The four source folders are vc_active_20261030_082606, _082623, _082639 and
_082653; each contains its top-level live report, case report, CSV and plot.

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

## First timing revision: gates=2

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

## Software checks for the first timing revision

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

## Physical active-VC noise integration: PASS

Case 09_active_noise with the installed 5c2e063 firmware and integration runner
1.0 passes on the board. Independent offline re-analysis of the CSV agrees with
both live reports. All 13,160 samples are contiguous across 26.3199 wall seconds,
including the operator's changes between baseline, active and recovery phases.

| Check | Physical noise integration recording |
| --- | ---: |
| Command / Vm throughout capture | -70 / -70 mV |
| Average update rate | 499.9636 Hz |
| Complete one-second window rates | 499.7072 to 500.1911 Hz |
| Median / maximum previous loop | 1,525 / 1,801 microseconds |
| Maximum solver | 305 microseconds |
| Deadline flags / all other diagnostic flags | 0 / 0 |
| Settled active input / clamp standard deviation | 0.09708838 / 0.09708839 nA |
| Input-to-clamp correlation in settled active phase | -0.999999999992 |
| Maximum clamp-current reference error | 0.0000008233 nA |
| Maximum current-balance residual | 0.000001 nA |
| CC binary streaming after cleanup | Resumed |

Both settled baseline and recovery have zero input current and the same
0.001279 nA holding clamp current. During the settled active phase, the sum of
input and clamp current remains within 0.000001 nA of that holding current.
The numerical check includes the ongoing Na/K/leak currents and fixed-voltage
gating. Thus the added shared noise is compensated by clamp current while the
ideal voltage stays controlled. The 199-microsecond maximum-loop margin applies
to this recorded setup; noisy finite-access VC remains a separate combination.

Evidence: vc_integration_20261030_094428_326236.zip, containing both reports,
09_active_noise/recording.csv and recording.png.
CSV SHA-256: 8f411a85ecf548676f851f009eec1f7087baf2b855c2a8bf051d1ce9c18b67b1.

## Physical active-VC photodiode integration: PASS

Case 10_active_photodiode with the installed 5c2e063 firmware and integration
runner 1.0 passes on the board. Independent re-analysis confirms both reports
from 12,522 contiguous samples over 25.0428 wall seconds. The command and Vm
remain -70 mV throughout; all diagnostic flags are zero and CC binary streaming
resumes after cleanup.

| Check | Physical photodiode integration recording |
| --- | ---: |
| Average update rate | 499.9840 Hz |
| Complete one-second window rates | 499.8757 to 501.3162 Hz |
| Median / maximum previous loop | 1,473 / 1,555 microseconds |
| Maximum solver | 283 microseconds |
| Maximum clamp-current reference error | 0.0000008233 nA |
| Maximum current-balance residual | 0.000001 nA |
| Mean input: baseline / illuminated / recovery | 0.00001020 / 0.10124043 / 0.00252048 nA |
| Mean clamp: baseline / illuminated / recovery | 0.00126885 / -0.09996126 / -0.00124131 nA |

Illumination increases settled mean inward input by 0.10123023 nA and shifts
clamp current by -0.10123011 nA. At every recorded sample, input plus clamp
current remains within 0.000001 nA of the 0.001279 nA holding current needed
for the fixed-voltage Na/K/leak membrane. This confirms compensating clamp
current for the photodiode's shared input at ideal -70 mV.

The recovery input has a 0.00252048 nA (2.52048 pA) mean residual, with
0.00029499 nA standard deviation. Both pass the existing 0.003 nA quiet-phase
limits; the recovery is not an exact return to the starting sensor baseline.
This capture alone does not identify the cause of that small residual. No
acceptance threshold was changed. The result does not calibrate sensor gain
or establish noisy/light-driven finite-access behaviour.

Evidence: vc_integration_20261030_095547_721716.zip, containing both reports,
10_active_photodiode/recording.csv and recording.png.
CSV SHA-256: df180048ce657596f722075b44d5d5a979b6b8a209d0792823f8c3ad9e64731f.

## Physical Patch-command integration: response PASS, overall FAIL

The first 11_patch_command run with firmware 5c2e063 and integration runner
1.0 is a genuine timing failure. Independent re-analysis confirms the reports
from all 10,082 contiguous samples over 20.18375 wall seconds.

| Check | Physical Patch-command recording |
| --- | ---: |
| Settled command: baseline / clockwise / recovery | -70 / -46.259155 / -70 mV |
| Clockwise command change | +23.740845 mV |
| Vm command error | 0 mV |
| Maximum clamp-current reference error | 0.00001493 nA |
| Median / 99th percentile previous loop | 1,480 / 1,521 microseconds |
| Maximum previous loop | 22,900 microseconds |
| Deadline flags / all other diagnostic flags | 1 / 0 |
| Overall rate / lowest one-second window | 499.4612 / 489.5273 Hz |
| CC binary streaming after cleanup | Not confirmed (false in live report) |

The flagged row at sequence 4158 reports the preceding 22.900 ms loop. The
corresponding preceding row's measured HH solve is only 258 microseconds,
leaving 22.642 ms outside that measured solver interval. The event is during
baseline, 2.4397 seconds after capture start, with command and Vm still -70 mV.
The command first changes at 6.9411 seconds, about 4.5 seconds later. All other
recorded loops are at most 1,579 microseconds. This is an isolated wall-time
pause rather than sustained HH compute overload or a pause coinciding with
the knob movement. Existing diagnostics cannot distinguish serial blocking,
other firmware/IO work or task pre-emption as its cause.

The overall average lies inside 500 Hz +/-2%, but the affected one-second
window is below the 490 Hz lower limit. The deadline and clock failures remain
failures under unchanged thresholds. The full trace preserves sample order and
matches the independent channel/current reference; this does not recover the
missed wall time. The live report also fails to confirm binary streaming after
cleanup. Its console cleanup sentence reports requested commands, not observed
restoration; this second issue must not be reported as a successful return to CC.

Retain this failure and repeat only case 11 once after a fresh USB boot and an
operator check of ordinary CC in the GUI. Keep the firmware, test tool, timing
thresholds and protocol unchanged. A repeated pause calls for additional
firmware/transport timing instrumentation before assigning a cause or changing
the biological model. A passing repeat would not erase this intermittent event.

Evidence: vc_integration_20261030_100127_293521.zip, both reports and the case
CSV/plot. CSV SHA-256:
a00b4e9984c0d6e03290703c9452b7542a90011cb3a5228de4e4af320be26738.

## Physical Patch-command repeat: PASS; intermittent pause remains open

The requested repeat of 11_patch_command with the same firmware and runner
passes all checks. Independent CSV re-analysis confirms both reports from
9,202 contiguous samples over 18.40229 wall seconds. The valid clockwise knob
excursion is larger than in the first recording; the independent reference uses
each actual recorded command rather than assuming an identical waveform.

| Check | Physical Patch-command repeat |
| --- | ---: |
| Settled command: baseline / clockwise / recovery | -70 / -35.216900 / -70 mV |
| Clockwise command change | +34.783100 mV |
| Vm command error | 0 mV |
| Average rate / complete one-second windows | 499.9922 Hz / 499.7096 to 500.0592 Hz |
| Median / maximum previous loop | 1,477 / 1,534 microseconds |
| Maximum solver | 266 microseconds |
| Deadline flags / all other diagnostic flags | 0 / 0 |
| Maximum clamp-current reference error | 0.00002213 nA |
| Maximum gate reference error | 0.000009247 |
| Maximum current-balance residual | 0.000002 nA |
| CC binary streaming after cleanup | Resumed |

The first recording remains a timing FAIL with unconfirmed cleanup. The repeat
provides a passing Patch-command and cleanup capture, but no firmware/tool change
was made and the earlier pause's cause has not been identified. No fixed cause,
permanent timing correction or reproducibility conclusion is inferred from a
single clean repeat. Continue to the distinct mode-switch and longer access
protocols; preserve their deadline evidence under the unchanged rules.

Evidence: vc_integration_20261030_100829_986219.zip, both reports and the case
CSV/plot. CSV SHA-256:
49b44ac45d0a8b2b43c0996c46bfe84f4e7c343e0727ca9b7db99fab6ada36c2.

## Physical one-minute finite-access recording: PASS

Case 13_access_stress at firmware 5c2e063 and integration runner 1.0 passes.
Independent re-analysis confirms both live reports from 30,003 contiguous
samples spanning 60.00656 wall seconds, with quiet inputs and a fixed -20 mV
command through 5 MOhm access. All diagnostic flags are zero and CC binary
streaming resumes after cleanup.

| Check | Physical one-minute access recording |
| --- | ---: |
| Average rate / complete one-second windows | 499.9787 Hz / 499.7533 to 500.1174 Hz |
| Median / 99th percentile / maximum previous loop | 1,721 / 1,746 / 1,800 microseconds |
| Maximum solver | 488 microseconds |
| Vm throughout capture, at CSV precision | -26.916933 mV |
| Mean clamp current | 1.383387 nA |
| Maximum settled coupled-reference Vm error | 0.00006314 mV |
| Maximum clamp-current reference error | 0.00001223 nA |
| Maximum gate reference error | 0.000005493 |
| Maximum current-balance residual | 0.000001 nA |
| Deadline flags / all other diagnostic flags | 0 / 0 |
| CC binary streaming after cleanup | Resumed |

The 6.916933 mV command-to-Vm offset agrees with Rs times clamp current
(6.916935 mV). This is the intended series-resistance error; Vm is stationary
at the recorded precision and the settled Na/K/access solution agrees with
the independent ODE. The test validates this settled one-minute condition;
transient accuracy is documented separately by case 04.

The maximum recorded loop has 200 microseconds of margin. The earlier isolated
22.9 ms Patch-test pause was not reproduced in this capture and remains an
unresolved observation. This result does not establish a fix for that event,
individual analogue/TTL edge jitter or every mixed-input condition.

Evidence: vc_integration_20261030_101425_529160.zip, both reports and the case
CSV/plot. CSV SHA-256:
86749178db3719536d71a3504a6b8fdad3fe5b09285bf5840848e7ac277db22c.
This archive contains only case 13. The physical case 12 switching recordings
were supplied separately and are verified in the following section.

## Physical five-cycle mode switching: PASS

Case 12_mode_switching at firmware 5c2e063 and integration runner 1.0 passes
all five recorded cycles. Independent re-analysis confirms every CSV and the
top-level live report, including CC binary streaming after each cycle and final
cleanup. The five VC segments contain 8,284 samples, contiguous within each
segment; model sequence counters restart on VC entry and are assessed separately.

| Cycle | Samples | Update rate, Hz | Maximum loop, microseconds | CC streaming |
| --- | ---: | ---: | ---: | --- |
| 01 | 1652 | 499.9881 | 1468 | Resumed |
| 02 | 1657 | 500.0310 | 1460 | Resumed |
| 03 | 1655 | 499.9988 | 1463 | Resumed |
| 04 | 1659 | 500.0263 | 1448 | Resumed |
| 05 | 1661 | 499.9968 | 1478 | Resumed |

All flags are zero and every complete one-second window passes. Vm remains
at the imposed -20 mV. TTX 9.2 nM and TEA 0.5 mM are configured once at setup,
with no PH settings resent between handovers. Every settled segment has mean
Na current -0.050448 nA, K current +0.998377 nA and clamp current +1.047929 nA.
Na and K are respectively 0.50000192 and 0.50000008 of the independently
calculated unblocked steady currents, consistent with the intended half block
at recording precision. The five component-current/gate traces agree at CSV
precision and each passes the independent constant-voltage reference.

The largest component-current reference error is 0.000002726 nA; clamp error
is at most 0.0000004091 nA. This supports retention of the specified TTX/TEA
effect across the tested mode sequence. Each VC segment starts after 2.1 wall
seconds of conditioning; these recordings do not resolve instantaneous handover
transients, physical TTL edges, CC voltage trajectories or hidden receptor/RNG
states. Backend selection intentionally initialises HH gates at the current Vm.

Evidence: vc_integration_20261030_101351_194427.zip, top-level live report and
cycle_01 through cycle_05, each with its case report, CSV and plot.
Archive SHA-256: b9b619d4a8ae8b35352ecff2cd77d518c6e9536a142fa8e3186d29454e9474b4.

The eight core protocols and five first-stage integration protocols now each
have passing physical captures across the staged revisions. The first case 11
timing/cleanup failure remains recorded, with its cause unresolved. This is a
completed validation stage, not a claim of a clean single-revision full-suite
run or complete pharmacology/hardware qualification.

## Next board action

After the eight core tests, the user confirmed that all knobs and functions work
correctly and the GUI displays proper behaviour. This records the requested
post-test operator check of ordinary operation, separately from the quantitative
VC captures. It is not a measurement of TTL timing or analogue calibration.

Keep the tested voltage=2 firmware installed. Cases 09 to 13 now have verified
passing captures, with the first case 11 failure retained above. No repetition
of the completed protocols or firmware upload is needed for this milestone.
The user has confirmed a second Spikeling and stereo TRS cable. The next
Python-only pack uses its normal CC axon output as the source, connected through
the labelled Synapse Out -> Synapse In jacks. Case 14 on Synapse 1 now has a
verified passing physical capture with runner 1.1; the Synapse 2 repeat also
passes. Case 15 NBQX now also has a verified passing repeat; its first timing
FAIL remains recorded below and unresolved. Case 16 gabazine also passes.
Cases 17 AMPA and 18 GABA-A reversal now also pass. Case 19 NMDA/APV also
passes selective slow-component block with preserved AMPA. Next is case 20
GVIA on Synapse 1 using the same setup. See VC_SYNAPTIC_WINDOWS.md for wiring and
VC_SYNAPTIC_VALIDATION.md for the independent reference, evidence and limits.
Cases 15 (repeat), 16, 17, 18 and 19 pass; case 20 remains pending.
The firmware model and all existing tolerances are unchanged.

The first integration pack passed 84 native tests: the original 70 and 14
integration analyser tests using the actual sketch with simulated ADC/clock/serial
IO. The synaptic pack adds 16 tests, bringing the passing suite to 100.
Fault cases include missing input, wrong compensation sign, failed recovery,
unresponsive command control, lost drug settings, cadence/deadline failure,
sample gaps and incomplete recording duration. The CLI/PTY QA covers all five
new cases with plots and cleanup, including two handovers and a full 60-second
capture; a deliberately missing signal must fail while cleanup still succeeds.
None of these host checks measures the new cases on the physical board.

The remaining integration work includes external command input, both synapses,
receptor/release pharmacology, hidden-state preservation during mode transitions,
mixed-input access-mode timing, physical TTL behaviour and analogue calibration.
Keep current thresholds for 500 Hz cadence and diagnostic/deadline failures
when adding those protocols. The earlier isolated pause remains an open timing
observation for subsequent captures.

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

## Synaptic runner startup diagnosis and PC fix

Runner 1.0 stalled before its first operator prompt on Windows. The user's
faulthandler trace locates the wait in the active identity line read; the
interrupted report confirms CC streaming resumed. Runner 1.1 replaces that
line read with a bounded byte scan, drains startup output, paces configuration
and logs its startup stage. The native suite now passes 113 tests including
13 startup regressions. See VC_SYNAPTIC_VALIDATION.md for the demonstrated scope
and the missing-reply/continuous-binary serial regression. No firmware, model
or acceptance-threshold change is made. The first physical Synapse 1 result
is recorded below; other synaptic cases remain pending.

## First physical synaptic capture — Synapse 1 PASS

With runner 1.1 at 797f054 and unchanged 5c2e063 firmware, case 14 on Synapse 1
passes independent analysis of all 21,670 CSV samples over 43.33926 wall seconds:
499.985491 Hz, zero flags, maximum loop 1,561 us, Vm=-70 mV throughout, 22
resolved settled-window events and resumed CC streaming. The fitted AMPA event
contribution is -0.0990005281 nA versus -0.099 nA expected, with quiet baseline
and recovered tail. A direct difference/decay check separately agrees with the
fast synaptic recurrence. The startup fix reaches the identity and prompts on
the physical COM13 board in this run.

Evidence: vc_synapse_20261030_195517_858406.zip; SHA-256
923d71ab69a217ebebb0f6d62bf2d7fd9c10ae6d9669f457e6a291a83d9686bb.
See VC_SYNAPTIC_VALIDATION.md for all metrics, CSV hash and scope. Next board
case is the same basic protocol on Synapse 2; receptor reversals and drug/release
checks remain pending. This clean capture does not resolve the earlier isolated
Patch pause. No firmware/tool/threshold change or new download is required.

## Both basic physical synaptic inputs PASS

The Synapse 2 case 14 capture also passes independent reanalysis with the same
runner/firmware: all 23,460 samples are contiguous, cadence is 499.987518 Hz,
all flags are zero, maximum loop is 1,535 us, Vm remains -70 mV and CC streaming
resumes. Twenty settled-window events give -0.0990004464 nA per event versus
-0.099 nA expected. Quiet baseline/recovery and a separate direct decay/increment
check pass. The two input fits agree in event size at the selected model gain;
source rates need not match and no independent source event count is available.

Evidence: vc_synapse_20261030_200340_672425.zip; SHA-256
44fc9726faf8e0a858c6cdceb0c003ca97cec1bc1676c1346326a3a8624baed1.
See VC_SYNAPTIC_VALIDATION.md for full metrics and CSV hash. Next is case 15
NBQX on Synapse 1 (control/drug/washout), using the same kit and firmware.
Receptor/drug/release cases remain pending; neither this clean capture nor the
startup fix resolves the earlier isolated Patch-loop pause.

## First physical NBQX run — pharmacology response passes; timing FAIL

The first case 15 capture independently matches control / simulated half-block /
washout, with 21 resolved events per phase and contributions -0.09900046618 /
-0.04950020418 / -0.09900046598 nA. All 26,549 samples are contiguous, Vm stays
-70 mV, the membrane reference agrees and CC streaming resumes. Overall status
remains FAIL: one previous-loop duration is 22,256 us, with flag 64 and a failed
489.756429 Hz first one-second receive window (global average 499.803431 Hz).
All other loops are <=1,614 us.

The flagged record occurs 0.500526 s after capture starts, before the first
received receptor response (2.370526 s), control phase (6.286600 s) or drug
phase (18.360628 s). The preceding HH solve is only 262 us: 21,994 us is outside
that measured interval. Serial/IO/host scheduling or pre-emption cannot be
separated by the available data. This resembles the earlier unresolved Patch
pause but does not prove the same cause. The startup line-read correction is
not a demonstrated fix for this runtime timing issue.

Evidence: vc_synapse_20261030_201130_252214.zip, archive SHA-256
2ac9db0b32a382709ce7511df6880fcdb2b8a0f270cbbc4e82935c2c632cc538.
Full metrics, CSV hash and chronology are in VC_SYNAPTIC_VALIDATION.md. Repeat
case 15 once with unchanged firmware/tools/criteria, preserving this FAIL.
A clean repeat does not establish a permanent correction; another overrun calls
for targeted IO/serial timing instrumentation before further qualification.

## Physical NBQX repeat PASS; earlier timing failure retained

The unchanged case-15 repeat passes independent analysis of all 26,409
contiguous samples over 52.81661 wall seconds: 499.994257 Hz, no flags,
maximum loop 1,607 us, Vm=-70 mV throughout and resumed CC streaming.
There are 22 resolved events per settled phase, with contributions
-0.09900054073 / -0.04950018797 / -0.09900054683 nA. Drug/control ratio is
0.499999168; washout/control is 1.000000062. A separate direct recurrence check
also agrees. The model's simulated 0.30 uM NBQX half-block and recovery are
therefore verified in a complete passing capture under the original criteria.

Evidence: vc_synapse_20261030_202600_819949.zip; archive SHA-256
c87cf76bc33d189274e106a76ee71dba9a72cf4e35860102f265c44010a9c276.
Full metrics and CSV hash are in VC_SYNAPTIC_VALIDATION.md. The prior NBQX
22.256 ms failure and earlier isolated Patch pause remain unresolved; this
clean repeat is not a demonstrated permanent fix. Next is case 16 gabazine on
Synapse 1, with the existing kit and firmware and automatic GABA-A selection.

## Physical gabazine PASS

The unchanged case-16 capture passes independent analysis of all 24,230
contiguous samples over 48.45797 wall seconds: 500.000290 Hz, zero flags,
maximum loop 1,620 us, Vm=-70 mV and resumed CC streaming. The outward-positive
GABA-A contributions from 35 events per phase are +0.09900060781 /
+0.04950033568 / +0.09900060914 nA. Simulated 0.90 uM gabazine yields
0.500000321 of control, with washout/control 1.000000013. An additional direct
increment/decay check agrees. Numerical/current balance and settled recovery pass.

Evidence: vc_synapse_20261030_203227_620637.zip; archive SHA-256
5211c495de9960734dde6b083d347f683b9c9e4e8031af2b155d858c97958e32.
Full metrics and CSV hash are in VC_SYNAPTIC_VALIDATION.md. The earlier runtime
pauses remain unresolved. Next is case 17 AMPA reversal on Synapse 1, with
automatic -70/-20/+20 mV command phases and expected negative-to-positive
synaptic event currents. Firmware, tools and all thresholds remain unchanged.

## Physical AMPA reversal PASS

The unchanged case-17 capture passes independent analysis of all 25,591
contiguous samples over 51.18045 wall seconds: 499.995562 Hz, zero flags,
maximum loop 1,634 us, exact recorded Vm tracking and resumed CC streaming.
At -70/-20/+20 mV, 21/20/20 resolved events give contributions
-0.09900047321 / -0.02828581351 / +0.02828583075 nA. Fitted reversal is
-0.0000012562 mV, effectively the configured 0 mV at meaningful model precision.
A separate direct-increment linear fit also locates the zero near 0 mV.
Maximum independent clamp-reference error is 0.0007501154 nA, within the
unchanged 0.01 nA current tolerance. Synaptic reversal uses receptor current;
total clamp injection additionally contains intrinsic and capacitive currents.

Evidence: vc_synapse_20261030_203954_842898.zip; archive SHA-256
2b411600c90a813fed0ae437bb00a98858dc5d879a1c7bf1f60226f7d191f0e4.
Full metrics and CSV hash are in VC_SYNAPTIC_VALIDATION.md. Earlier timing
pauses remain unresolved. Next is case 18 GABA-A reversal on Synapse 1 with
-90/-70/-50 mV command phases and expected -0.099/+0.099/+0.297 nA event
contributions, using the same kit/firmware and unchanged thresholds.

## Physical GABA-A reversal PASS

The unchanged case-18 capture passes independent analysis of all 31,812
contiguous samples over 63.62247 wall seconds: 499.996309 Hz, zero flags,
maximum loop 1,621 us, exact recorded Vm tracking and resumed CC streaming.
At -90/-70/-50 mV, 23/23/22 resolved events give receptor contributions
-0.09900052643 / +0.09900053548 / +0.29700147581 nA. Fitted reversal is
-79.9999994334 mV, effectively -80 mV at meaningful model precision. A separate
direct-increment fit gives -80 mV. Maximum independent clamp-reference error
is 0.00019185794 nA, inside the unchanged 0.01 nA tolerance.

Evidence: vc_synapse_20261030_204825_321782.zip; archive SHA-256
a6104671fa77b767d9fb306549823b6caa06ebc7d7b82ab21a7e13c49ac91a8b.
Full metrics and CSV hash are in VC_SYNAPTIC_VALIDATION.md. Earlier runtime
pauses remain unresolved. Next is case 19 NMDA/APV at -20 mV on Synapse 1:
selective reduction of the slow NMDA contribution, preserved fast AMPA and
washout. Same kit/firmware and all original thresholds are retained.

## Physical NMDA/APV selectivity PASS

The unchanged case-19 capture passes independent analysis of all 24,928
contiguous samples over 49.85467 wall seconds: 499.993319 Hz (one-second
windows 499.874530–500.097113), zero flags, maximum loop 1,690 us, exact
recorded Vm tracking and resumed CC streaming. At -20 mV, control / simulated
3.7 uM APV / washout resolve 19/19/18 events. Slow NMDA coefficients are
-0.03458738249 / -0.01729369276 / -0.03458735165 nA: drug/control 0.5000000438
and washout/control 0.9999991081. Fast AMPA stays near -0.0282858 nA per event,
with drug/control 0.9999985723. A separate direct closed-form exponential fit
reproduces both components without the analyser's convolution recurrences.

The slow coefficient is not a peak of the summed current. Maximum independent
clamp-reference error is 0.0001242676 nA, within the original 0.01 nA limit.
Settled recovery retains at most 0.001399 nA receptor current, within the
original 0.003 nA quiet limit; it is not exactly zero. This validates the
configured deterministic receptor response and selective APV scaling at this
voltage, not full magnesium voltage dependence or real drug binding kinetics.

Evidence: vc_synapse_20261030_210026_760655.zip; archive SHA-256
d9f3a5fe876ea9ed3a13d49d92bd78d676df73c9f13b77d27b09ca033aa37d15.
Full metrics and CSV hash are in VC_SYNAPTIC_VALIDATION.md. Earlier runtime
pauses remain unresolved. Next is case 20 GVIA on Synapse 1, using the same
kit/firmware: AMPA at -70 mV, deterministic release, simulated 10 nM GVIA and
washout. Expected event amplitudes are -0.099 / -0.055590046875 / -0.099 nA,
with drug/control 0.561515625. This is not a stochastic release-failure test.
All existing model and acceptance parameters remain unchanged.
