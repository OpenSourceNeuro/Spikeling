# Big Spiky V1 firmware

Complete firmware for the 1,150 mm Big Spiky interactive neuron at Maker Faire Rome 2026. It runs a
scientifically coherent, real-time Izhikevich educational model while independently visualising 12 synaptic
inputs, continuous soma Vm and one-shot action-potential events.

This is an educational computational neuron, not a biological preparation or research-grade recorder.
No decorative firing occurs in normal mode. The idle display is a dim resting soma; the only non-model
sequence is the explicitly invoked, visual-only self-test.

## Source and licence

The scientific baseline is Spikeling V3 at commit
`3e3fd9a06c659aa43eb404fdd86715e01b96bf8e`. See [SOURCE_AUDIT.md](SOURCE_AUDIT.md).
Source files retain GPL-3.0-or-later SPDX headers and Open Source Neuro attribution. Existing
`Firmware/Spikeling_V3` files are not modified.

## Reference configuration

- ESP32-S3-WROOM-1 N4; ESP32S3 Dev Module; 240 MHz; 4 MB QIO flash at 80 MHz; PSRAM disabled.
- Hardware CDC and JTAG; USB CDC on boot; GPIO19/20 reserved for native USB.
- 500 Hz / 2,000 µs drift-resistant model schedule; retained `dt_ms = 0.1`.
- 12 direct 3.3 V rising-edge spike inputs with per-input counted ISRs and 1.5 ms glitch rejection.
- Three MCP3208 ADCs by default; fourth optional at compile time.
- MCP4922 channel A for analogue Vm and GPIO18 for the real TTL axon spike.
- Four 24-pixel dendrite zones, one 24-pixel soma zone and one 60-pixel axon zone.
- Exact V3 legacy telemetry by default; separate extended Big Spiky protocol at 100 Hz.

## File structure

| File | Responsibility |
| --- | --- |
| `BigSpiky_V1.ino` | Safe setup and cooperative real-time scheduling |
| `BigSpiky_Config.h` | Compile-time profiles, all pins, ADC mappings and limits |
| `BigSpiky_Hardware.h` | Safe GPIO, shared SPI, MCP3208/MCP4922 transfers and diagnostics |
| `BigSpiky_Adc.h` | Median/IIR/dead-band filters and rail-stuck containment |
| `BigSpiky_Synapses.h` | Indexed synapses, IRAM ISR counters, event snapshots and decay |
| `BigSpiky_Model.h` | Izhikevich state, clamp/noise/photodiode/current contributions |
| `BigSpiky_Leds.h` | 40 fps core-0 visual task, current limiting, self-test and axon queue |
| `BigSpiky_Serial.h` | Strict command parser and legacy/V2 streaming |
| `BigSpiky_Logic.h` | Pure reusable logic exercised by host tests |
| `BigSpiky_Protocol.h` | Exact packed packet layouts and compile-time size checks |
| `Izhikevich_parameters.h` | All 20 retained presets |
| `PINMAP.md` | GPIO audit, connector assumptions and both ADC budgets |
| `PROTOCOL.md` | Wire layouts, CRC, commands and examples |
| `LED_POWER.md` | Topology, semantics, current estimates and wiring requirements |
| `VALIDATION.md` | Reproducible compilation/tests and remaining bench work |
| `tests/` | Deterministic host tests, timing simulation and API smoke stubs |

## Model and synaptic behaviour

Every ISR accepts a rising edge only when it is at least 1,500 µs after that input's preceding accepted edge.
It performs no floating-point work, LED update or serial output. It only timestamps, increments a saturating
pending count and diagnostics. The model atomically snapshots and clears all 12 counts. For each accepted
event it applies `current += gain`, bounds the per-input state, and then multiplies by that input's decay.
Positive gain is excitatory; negative gain is inhibitory; the centre dead zone is exactly zero.

The total is bounded after summing patch/clamp, external current, photodiode, all scaled synapses and Gaussian
noise. Voltage clamp retains PI feedback and anti-windup. Changing a model or custom parameters resets `v`,
`u`, clamp history, currents and output state safely.

The host GUI is optional. Integration, physical outputs and visual activity continue after disconnection.

## Build

Pinned reproducible toolchain:

- Arduino CLI 1.x (the workflow records the exact patch version);
- Arduino-ESP32 `3.3.11`;
- Adafruit NeoPixel `1.15.5`.

```bash
arduino-cli core update-index
arduino-cli core install esp32:esp32@3.3.11
arduino-cli lib install "Adafruit NeoPixel@1.15.5"
arduino-cli compile --warnings all \
  --fqbn 'esp32:esp32:esp32s3:CDCOnBoot=cdc,USBMode=hwcdc,CPUFreq=240,FlashFreq=80,FlashMode=qio,FlashSize=4M,PSRAM=disabled' \
  Firmware/BigSpiky_V1
```

The branch workflow runs the host suite, compiles the repository copy, constructs the ZIP, extracts it into a
clean directory and compiles that extracted copy with the same command. It records flash/RAM use and warnings.

For the optional full analogue profile, add `--build-property compiler.cpp.extra_flags=-DBIGSPIKY_ADC_PROFILE=4`
only after fitting ADC #3 and reviewing the carrier/power/connector design.

## Normal-operation reliability

- Axon and all chip-select/data outputs enter safe states before SPI, DAC, LEDs or interrupts start.
- LEDs are transmitted from a separate task/core; normal code and self-test contain no `delay()` calls.
- Model deadlines are advanced from the preceding deadline, not from completion time; missed deadlines,
  maximum execution time, serial overflow, ADC faults, event saturation and visual queue drops are counted.
- Pot gains stay zero until a channel produces a trustworthy non-rail sample.
- A five-minute no-activity timeout removes ring illumination and leaves a dim resting soma. It never fires the
  model. A model/input spike immediately exits quiet display.
- Physical LED disable affects visuals only. Self-test never changes current, Vm or TTL output.
- The watchdog-friendly loop always yields, while the model does not depend on USB availability.

Use `BSSTATUS` to retrieve instrumentation. Clear/restart is intentionally required to clear historical sticky
fault bits; live mode bits follow their current state.

## Hardware assumptions and unresolved decisions

The compileable reference map assumes a custom carrier or breakout that exposes every selected N4 pin and
does not connect external JTAG to GPIO39–42. The final carrier schematic has not yet been supplied; it must be
checked before PCB routing or assembly.

Default decisions are: unpowered TRS; separately powered external modules; 3.3 V pulses; protected local input
buffers; 12 gain pots; two analogue Vm monitors; 12 eight-pixel rings; 24-pixel soma; 60-pixel axon; separately
fused external 5 V LED supply. Unresolved items include the exact carrier, TRS/TRRS choice, source pulse width,
input protection part values, final LED batch/pixel count, final 5 V supply and whether all 12 analogue Vm lines
are educationally necessary. Each is isolated in configuration or documented as a hardware gate.

A powered connector profile is deliberately absent. Spike + Vm + power + ground needs TRRS or separate power,
and public hot-plug power needs hardware current limiting and ESD design that firmware cannot replace.

