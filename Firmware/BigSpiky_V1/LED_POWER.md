# LED topology, wiring and power budget

## Reference topology

Six independent WS2812-compatible data zones are used:

1. four dendrite zones, each chaining three local 8-pixel rings (24 pixels per branch);
2. one 24-pixel soma ring;
3. one 60-pixel axon strip.

This gives 96 synaptic-ring + 24 soma + 60 axon = **180 pixels**. It avoids one long data route crossing
the whole 1,150 mm sculpture. A single-chain alternative would save five GPIOs and level-shifter channels,
but would create a longer, harder-to-service signal path and a larger single point of failure.

Adafruit NeoPixel 1.15.5 is pinned. On ESP32, its transport delegates to the Arduino-ESP32 RMT path. All six
zones are rendered at 40 fps by a task pinned to core 0; the model loop remains on core 1. The longest
single zone is 60 pixels, about 1.8 ms of 800 kHz wire time. Six sequential transfers take roughly 5.4 ms
on the visual core every 25 ms. Actual RMT/core interaction and jitter must still be verified on the final PCB.

## Visual semantics

- Red ring arc: excitatory gain; blue ring arc: inhibitory gain; centre: off/dim neutral.
- Arc length and intensity both encode `abs(gain)`; colour is not the only indication.
- A real incoming event brightens its existing sign colour and decays visually over 150 ms.
- Soma colour is calculated from `Vm_min`, `v_rest`, `Vm_spike` and `Vm_peak`; a model spike gives an
  80 ms white flash without changing the model.
- Each real model spike queues one 350 ms white head/tail trip down the axon. The queue serialises up to four
  trips; overflow drops only the visual trip and raises status bit 8. It never drops the model or TTL spike.
- Self-test is an explicit visual-only command/button sequence. It never injects current or drives the TTL
  axon. Model spikes are not queued while self-test overrides the display, preventing stale decorative trips.

Fabricated labels must include `− inhibitory`, `0`, and `+ excitatory` at every gain control.

## Current estimates

The conservative RGB worst case is 60 mA per pixel:

- 180 × 60 mA = **10.8 A at 5 V (54 W)** theoretical full-white worst case;
- 25% default firmware brightness gives about **2.7 A (13.5 W)** channel-current estimate;
- the hard software estimator is set to **3.0 A**, but it is not a safety device and does not include every
  LED batch's tolerance, idle current, cable loss or fault current.

Use a regulated 5 V supply sized from the final verified pixel model and wiring, with engineering margin.
For the 180-pixel reference installation, a quality 5 V / 12–15 A supply permits safe electrical testing at
uncapped full white; normal public operation remains capped. Never power the installation from ESP32 USB.

## Required installation details

- Separate fused or resettable-fused 5 V branches for each dendrite, soma and axon zone.
- Power injection at each physical branch and both ends of the long axon where voltage-drop measurements
  show it is needed. Do not pass the full installation current through thin strip traces.
- One common logic/LED ground bonded with a deliberate low-impedance topology.
- One suitable 3.3-to-5 V HCT/AHCT level-shifter channel per data zone, placed near the transmitter.
- 300–500 Ω series resistor at the beginning of every LED data line, after the buffer.
- Local 100 nF decoupling per pixel/module where not already fitted and 500–1,000 µF bulk capacitance at
  each major 5 V entry. Observe capacitor surge and branch-fuse ratings.
- Wire gauge, connectors, terminals, strain relief, enclosure temperature and fusing rated for measured
  continuous and fault currents.
- Verify data integrity with the actual cable lengths and public plug/unplug electromagnetic environment.

