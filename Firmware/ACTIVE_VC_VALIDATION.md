# Active VC verification — 29 October 2026

## Outcome

The software prototype is ready for its first physical-board active-step check.
The physical ESP32-S3 has NOT run this active firmware in this development session.
Existing passive board results at commit 08212b9 do not establish active timing.

## Automated checks

- **63 native tests PASS**: the existing 39 passive/clock/CC regression checks,
  plus 24 active-model, shared-input/pharmacology and result-analyser checks.
- The real complete sketch and vendored SerialCommand parser are compiled for
  host tests with deterministic ADC/DAC/clock/IO stubs. These are simulated IO.
- Original CC binary packets remain equal to the pinned pre-VC baseline across
  all 20 presets and the existing representative input scenarios with PH OFF.
- Exact ideal-clamp gate/product integration and independent DOP853 access ODE
  references validate current/voltage trajectories. No firmware algorithm is
  used as its own numerical reference.
- Negative analyser checks reject fast cadence, deadline flags, a missing Na
  current and sequence gaps, even when other checks agree.

## Serial workflow integration

All **eight** active hardware-runner cases passed through pyserial and a PTY
connected to the native complete sketch. This verifies real command parsing,
continuous byte capture, case analysis, saved files and return to CC binary
streaming. The external bridge imposed 2 ms ticks: its rate and zero stubbed
solve times are NOT ESP32 performance measurements.

The PC reader stays active while each case is analysed/plotted. This avoids
introducing USB backpressure from a stopped reader during multi-case tests.
The final five-panel plot was also regenerated and visually inspected; Na/K
currents are shown separately from capacitive transients without clipping peaks.

Representative reference errors from the simulated serial run:

| Case | Max Vm error, mV | Max clamp-current error, nA |
| --- | ---: | ---: |
| Ideal -70 to -20 mV | 0 | 0.0007481 |
| TTX, 92 nM | 0 | 0.0000645 |
| TEA, 5 mM | 0 | 0.0007529 |
| Access resistance, 5 MOhm | 0.0298268 | 0.0030342 |
| Sodium reversal, +50 mV | 0 | 0.0007250 |
| Inactivated -40 mV hold | 0 | 0.0000282 |
| Above sodium reversal, +60 mV | 0 | 0.0019511 |
| Potassium tail, -90 mV | 0 | 0.0011154 |

These errors characterise numerical approximation relative to the chosen model,
not biological accuracy. Acceptance is 0.05 mV for Vm, 0.01 nA for component
currents, 0.003 for gate fractions and 0.00002 nA for current-balance residual.
The largest access-case gate error was 0.0003434.

## ESP32-S3 build

Arduino CLI 1.5.1; ESP32 Arduino core **3.3.12**. Target:

    esp32:esp32:esp32s3:USBMode=hwcdc,CDCOnBoot=cdc,FlashSize=4M,PSRAM=disabled

Compilation PASS: **356,745 bytes** program storage; **24,224 bytes** global
variables; **303,456 bytes** remaining for stack/local variables under the
reported build. USB CDC on boot is enabled, using Hardware CDC/JTAG.
The packaged BUILD.json records component hashes and exact flash offsets.
Source upload through Arduino IDE is recommended.

## Next physical checks

1. First active ideal step, with quiet inputs: evaluate currents, 500 Hz cadence,
   firmware flags and loop/solver timing. Do not treat a current waveform alone
   as a pass if timing fails.
2. TTX and TEA isolation, followed by finite access resistance.
3. Reversal potentials, depolarised-hold inactivation and K tails.
4. Recheck physical Patch-controlled CC firing after the runner exits.
5. Combined receptor/GVIA/CC pharmacology tests and hardware outputs remain
   separate work. Native receptor tests are not physical-board evidence.

## Scope limits

The active cell is Na/K/leak. Apamin/SK and 4-AP/A-current responses are not
implemented in VC and raise flag 32. The frozen integrated-v2 phenomenology
remains available in optional CC mode. Drug potencies and conductance scaling
are explicit educational design choices. The separate STP/LTP branch is not
merged. GUI active-mode controls, quantitative VC labels, DAC calibration and
oscilloscope timing verification are not included. NMDA magnesium gating is
frozen over each outer 0.1 ms model bin. See ACTIVE_VC_PROTOTYPE.md for sources.
