# Spikeling V3 source audit

Big Spiky V1 was based on `OpenSourceNeuro/Spikeling` main commit
`3e3fd9a06c659aa43eb404fdd86715e01b96bf8e` (2026-08-26). Every file in
`Firmware/Spikeling_V3` was inspected in full before this folder was created.

| Source file | Git blob SHA | Bytes reported by GitHub |
| --- | --- | ---: |
| `Core_functions.h` | `ac86277f8e619e9c563113f9262a96fc80b47854` | 49,958 |
| `General_settings.h` | `898bcd0fba9c77e5282857b05a4a73b00e44b16d` | 62,916 |
| `Izhikevich_parameters.h` | `fda48f4554a2ca8019cd84258fa778ce6e7f0e71` | 6,138 |
| `Serial_functions.h` | `3eaaf753e3c315a06c9593a7113e914dfd178ed4` | 8,787 |
| `Spikeling_V3.ino` | `efa9ff29ea6cab13101c0ca9b977104e8c1e033d` | 8,862 |
| `WiFi_functions.h` | `590988db25324a9add568e797baa29ccc1889174` | 7,457 |
| `build_opt.h` | `8eb1034cfe68613ed16f7cc7d008df74d3c16d21` | 95 |

## Retained

- The 2,000 µs drift-resistant `micros()` schedule and `dt_ms = 0.1` integration step.
- The Izhikevich equations, state (`v`, `u`, `a`, `b`, `c`, `d`) and all 20 presets.
- `v_rest`, `Vm_min`, `Vm_spike`, `Vm_peak`, custom models and safe state reset.
- Gaussian current noise, current clamp, serial-controlled voltage clamp and PI anti-windup.
- Optional photodiode current, external current input, MCP4922 Vm output and TTL axon output.
- Native USB serial at the retained 500,000 setting.
- The exact legacy `0xAA 0x55` header, 16-byte payload, field order and scaling.

## Adapted

- Two separately coded, polled synapses became `Synapse synapses[12]` with shared loop logic.
- Rising edges are captured by per-pin ISRs into saturating event counters. The model atomically
  snapshots counts, so coincident events and several accepted events between steps are not coalesced.
- Potentiometers use the V3 median-of-three, IIR and dead-band principle, scanned independently at
  approximately 125 Hz through a device/channel ADC mapping.
- MCP3208 and MCP4922 access is implemented directly over the retained shared SPI bus. This removes
  per-device global library objects and makes three-/four-ADC profiles compile-time choices.
- Spike handling exposes one explicit model event before resetting `v`; the physical TTL pulse and
  visual queue consume that event once. The Izhikevich equations are unchanged.
- RGB visualisation moved to a separate core/task at 40 fps. Its 350 ms axon travel time never changes
  model time, current or spike generation.
- Legacy commands relevant to model, clamp, noise, the first two synapses and connection behaviour are
  retained. Indexed `BS...` commands and a CRC-protected V2 packet were added.

## Replaced or intentionally omitted

- One `digitalRead()` per 2 ms step and Boolean edge state were replaced by counted interrupts.
- `syn1`/`syn2` command duplication was replaced by indexed commands; legacy aliases remain for inputs 1–2.
- Blocking connection/LED animations were replaced by timestamped visual states.
- Boot `delay()` calls and blocking 200-sample photodiode calibration were replaced by safe immediate
  outputs and a 128-step, zero-current calibration state.
- Optional Wi-Fi/WebSocket code is not compiled in V1. Native USB is the authoritative GUI transport,
  avoiding extra radio and dynamic JSON work in the exhibit firmware.
- The V3 stimulus-output hardware is not assumed. Its legacy serial tokens remain parseable for host
  compatibility, while Big Spiky uses central patch/external-current controls and has no stimulus DAC output.

