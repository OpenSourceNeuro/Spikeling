# Validation record

## Automated functional tests

Run from the sketch folder with:

```bash
bash tests/run_host_tests.sh /tmp/bigspiky-host-tests
```

The deterministic suite covers:

1. all 12 gain pots at minimum, centre and maximum;
2. negative/zero/positive mapping and per-channel reversal configuration;
3. single excitatory and inhibitory events;
4. several counted events between model steps;
5. simultaneous events on all 12 inputs;
6. independent decay and mixed excitation/inhibition;
7. current bounds, non-finite containment and enable/disable;
8. exact 16-byte legacy payload and field order;
9. 82-byte V2 framing, payload length and CRC check vector;
10. malformed, non-finite and out-of-range command arguments;
11. monotonic soma Vm normalisation;
12. one queued axon trip per one-shot model event;
13. worst-case LED estimate/current-limit scale; and
14. complete non-blocking self-test state progression.

The same script compiles the complete `.ino`/header graph against minimal Arduino API stubs with C++17,
`-Wall -Wextra -Wpedantic -Werror`, then runs a 200,000-step deterministic host timing simulation.

Local result before ESP32 cross-compilation: **all functional tests and the Arduino API smoke compile passed**.
Host timing is a logic benchmark, not MCU evidence; OS pre-emption outliers are reported separately.

## ESP32-S3 and extracted-ZIP compilation

The GitHub branch workflow pins Arduino-ESP32 3.3.11 and Adafruit NeoPixel 1.15.5, uses the exact FQBN/options
from `README.md`, compiles with all warnings, packages the sketch folder, extracts it into a clean temporary
directory and compiles the extracted copy. The final workflow log, flash/RAM summary, warnings and artifact
hash are delivered with the validated ZIP.

## Timing evidence boundary

Implemented instrumentation records model overruns and maximum model-step execution. Scheduling analysis:

- default deadline: 2,000 µs on core 1;
- one control ADC transaction is scheduled every 500 µs (16 controls ≈125 Hz each);
- sensor/analogue reads are deterministic in each model step;
- extended serial is 82 bytes ×100 Hz ≈8.2 kB/s; legacy is 18 bytes ×500 Hz =9 kB/s, both below the
  50 kB/s nominal capacity of 500,000 8N1;
- the longest LED zone has ≈1.8 ms wire time, but all LED transfers execute on core 0 at 40 fps;
- interrupt counters distinguish all 12 channels and retain several accepted events per channel.

The host benchmark and compilation demonstrate bounded logic and toolchain feasibility. They cannot prove RMT,
SPI, USB, interrupt latency or dual-core jitter on the actual carrier. The following must be measured on hardware.

## Required hardware-only bench tests

- Confirm every chosen GPIO is exposed and unloaded on the exact ESP32-S3-WROOM-1 N4 carrier.
- Scope boot/reset: axon TTL LOW, LED data LOW, all CS HIGH and no false external spike.
- Inject calibrated 50 µs pulses on every input; sweep inter-spike intervals around 1.5 ms and compare accepted,
  rejected and saturation counters.
- Drive all 12 inputs simultaneously and in bursts while streaming protocol 1 and 2.
- Measure model execution maximum/overruns for at least an eight-hour public-display soak.
- Measure RMT/NeoPixel updates with all six zones, USB streaming and SPI ADC/DAC active; verify core isolation.
- Disconnect each MCP3208 and force each used channel to ground/3.3 V; confirm zero gain and status flags.
- Calibrate pot centres/dead zone/direction, external-current midscale, photodiode dark/full counts and analogue
  Vm mapping against the final analogue front ends.
- Validate MCP4922 gain/reference/LDAC wiring and analogue Vm endpoints; confirm GPIO18 TTL amplitude/pulse width.
- Hot-plug protected TRS cables repeatedly with ESD-safe procedure; verify no phantom events or MCU resets.
- Measure 5 V voltage drop/current/temperature at every branch at default and engineered worst-case brightness;
  verify fuses, injection, wire gauge, bulk capacitance and level shifters.
- Brownout and power-cycle the ESP32 and LED supply in both orders; confirm safe recovery and no decorative firing.
- Verify self-test labels and that no self-test visual drives model current, DAC or TTL output.

