# ESP32-S3 pin map and ADC budgets

## Audited GPIO categories

This reference map targets **ESP32-S3-WROOM-1 N4** (quad 4 MB flash, no PSRAM). It must be re-audited
if another module suffix or carrier is selected.

| GPIO category | Pins | Decision |
| --- | --- | --- |
| Native USB D− / D+ | 19, 20 | Reserved for Hardware CDC and JTAG; never assigned by this firmware. |
| Module flash / SPI0/1 | 26–32 | Not used. Espressif says these are normally occupied by flash/PSRAM. |
| Octal-memory signals | 33–37 | Used only because the target N4 has quad flash and no PSRAM. Do not use this map on an octal-flash/PSRAM module. |
| Strapping | 0, 3, 45, 46 | Not used. External loads can change boot behaviour. |
| Restricted | 46 | Input-only and a strapping pin; not used. |
| External JTAG defaults | 39–42 | Repurposed after reset. Native USB-JTAG remains on 19/20. Disconnect external JTAG headers from these pins. |
| General-purpose selected | 1,2,4–18,21,33–44 | Used as listed below. |
| Unassigned safe reserve in this profile | 47, 48 | Available subject to the final carrier schematic. |

## Concrete reference assignments

| Function | GPIO | Direction / boot state | Notes |
| --- | ---: | --- | --- |
| Synapse spike inputs 1–12 | 1, 2, 4, 5, 6, 7, 8, 9, 14, 15, 16, 17 | Input pulldown | Rising-edge interrupts; 3.3 V logic. |
| SPI SCK / MOSI / MISO | 12 / 11 / 13 | Bus | Shared by all MCP3208s and MCP4922. |
| MCP3208 CS 0 / 1 / 2 | 21 / 38 / 39 | Output, HIGH | Default three-ADC profile. |
| MCP3208 CS 3 | 40 | Output, HIGH | Used only by the optional four-ADC profile. |
| MCP4922 CS | 41 | Output, HIGH | DAC channel A is Vm/axon analogue output; LDAC is assumed tied LOW. |
| Axon digital spike | 18 | Output, LOW | One 2 ms pulse per model spike. |
| Dendrite LED data zones 1–4 | 33, 34, 35, 36 | Output, LOW | Each drives three chained 8-pixel rings through its own level shifter. |
| Soma LED data | 37 | Output, LOW | One 24-pixel reference ring. |
| Axon LED data | 42 | Output, LOW | One 60-pixel reference strip. |
| Physical LED-disable switch | 43 | Input pulldown | HIGH disables and clears every LED without stopping the model. |
| Physical self-test button | 44 | Input pulldown | Debounced rising edge starts labelled visual self-test. |
| Native USB | 19, 20 | Reserved | Hardware CDC/JTAG, CDC on boot. |

## Input connector and protection assumption

Default unpowered TRS wiring:

- tip: 3.3 V presynaptic digital spike;
- ring: optional analogue presynaptic Vm or reserved;
- sleeve: common ground;
- **no power is carried through TRS**.

Spike polarity is active-HIGH. Firmware expects LOW below 0.8 V and HIGH above 2.0 V, never above the
3.3 V rail. Recommended source pulses are at least 50 µs HIGH and 50 µs LOW. Rising edges less than
1,500 µs apart on the same input are rejected as glitches; this still permits legitimate rates up to about
666 Hz. The interval is `DIGITAL_REFRACTORY_US` in `BigSpiky_Config.h`.

For public hot-plug use, place a protected 3.3 V input stage at every jack: low-capacitance ESD protection,
a 0.5–2.2 kΩ series resistor, a 3.3 V Schmitt buffer such as an appropriate LVC-family part, and a defined
pulldown. The exact buffer/protection must be validated against cable capacitance and the module output.
ESP32-S3 pins are not 5 V tolerant.

Spike + analogue Vm + power + ground needs four conductors (TRRS) or separate power. A powered-TRS option
is not enabled; it would require per-port current limiting, ESD protection and engineered hot-plug behaviour.
Firmware cannot provide that electrical protection.

## Three-MCP3208 channel budget (default)

| ADC | Channels | Allocation |
| --- | --- | --- |
| MCP3208 #0 | CH0–CH7 | Synaptic gain pots 1–8 |
| MCP3208 #1 | CH0–CH3 | Synaptic gain pots 9–12 |
| MCP3208 #1 | CH4 | Patch/current-clamp pot |
| MCP3208 #1 | CH5 | Noise pot |
| MCP3208 #1 | CH6 | Photodiode gain pot |
| MCP3208 #1 | CH7 | Optional LED-brightness pot (disabled by default) |
| MCP3208 #2 | CH0–CH1 | Analogue presynaptic Vm for synapses 1–2 |
| MCP3208 #2 | CH2 | External bipolar current input, centred near midscale |
| MCP3208 #2 | CH3 | Photodiode sensor |
| MCP3208 #2 | CH4–CH7 | Explicit spare channels |

## Four-MCP3208 channel budget (optional full analogue Vm)

Compile with `-DBIGSPIKY_ADC_PROFILE=4` after fitting ADC #3 and rechecking the carrier.

| ADC | Channels | Allocation |
| --- | --- | --- |
| MCP3208 #0 | CH0–CH7 | Synaptic gain pots 1–8 |
| MCP3208 #1 | CH0–CH3 | Synaptic gain pots 9–12 |
| MCP3208 #1 | CH4–CH7 | Patch, noise, photodiode-gain, optional brightness pots |
| MCP3208 #2 | CH0–CH7 | Analogue presynaptic Vm for synapses 1–8 |
| MCP3208 #3 | CH0–CH3 | Analogue presynaptic Vm for synapses 9–12 |
| MCP3208 #3 | CH4 | External bipolar current input |
| MCP3208 #3 | CH5 | Photodiode sensor |
| MCP3208 #3 | CH6–CH7 | Explicit spare channels |

The MCP3208 has no identity register, so firmware cannot positively identify a fitted device. A channel is
held inactive until it has produced a non-rail reading. A channel that remains at a rail for 32 pre-trust
samples is faulted; turning a legitimate full-scale pot away from the rail establishes trust and clears it.
This prevents an absent or uninitialised gain channel from injecting a large current at boot.
