# Short-term plasticity: facilitation and depression

Spikeling provides three optional short-term plasticity (STP) presets for each
incoming synapse: **facilitation**, **depression**, and **combined**.
These are illustrative, event-driven versions of a resource/utilisation model,
not quantitative predictions for any particular biological preparation.
The original static synapse remains the default.

## Experimental objective

Determine how the **history and frequency of presynaptic spikes** changes the
amplitude of subsequent synaptic-current increments, without changing the
neuron model or manually changing synaptic gain.

## Setup

1. Connect the presynaptic unit's axon output to the receiving unit's
   Synapse 1 input using the normal TRS connection.
2. Set the receiver to a stable neuron preset, with minimal noise and a
   nonzero synaptic gain; record the synaptic-current channel.
3. Use short trains of presynaptic spikes or paired pulses separated by a
   controlled interval. Keep all other conditions unchanged.
4. In the receiver GUI, open **Neuron Parameters → Synaptic plasticity (STP)**.
   Select Synapse 1; choose Off, Facilitation, Depression, or Combined.
5. Use **Reset transient state** before each independent protocol, so the
   first spike represents the fully recovered baseline.

In the **emulator**, use the identically named STP control in the emulator
Neuron Parameters page; the emulator's presynaptic neurons remain configured
in their existing Synapse 1 and Synapse 2 parameter pages.

## Presets

| Mode | U | Facilitation recovery | Resource recovery | Expected response |
| --- | ---: | ---: | ---: | --- |
| Off | 1.00 | — | — | Unchanged static synapse |
| Facilitation | 0.15 | 500 ms | — | Closely spaced spikes evoke larger increments |
| Depression | 0.40 | — | 800 ms | Closely spaced spikes evoke smaller increments |
| Combined | 0.25 | 500 ms | 600 ms | Early facilitation and later depletion may coexist |

The first spike after selecting or resetting a preset always has multiplier 1.
Presets are **not** measured biological parameters. All times are **simulated
model milliseconds**; the hardware speed control can change how quickly the
experiment unfolds in wall-clock time.

## Suggested investigations

### 1. Paired-pulse response

For each preset, record identical pairs separated by 50, 100, 200, 500 and
1000 model ms. Quantify the normalized **current increment** of the second
event relative to the first:

    PPR = second event increment / first event increment

An important control is that the decaying current from the first event may
still be present when the second arrives. Compare the event-associated
increment after subtracting the predicted/observed residual baseline, **not
the absolute peaks** of an overlapping current trace.

### 2. Train and recovery

Apply a train of spikes at a fixed interval and measure each event-associated
current increment. Introduce a pause, then measure the recovered response.
The combined preset is designed to reveal a possible increase early in a
train followed by resource-limited depression.

### 3. Sign and independence

Repeat with an inhibitory (negative) baseline gain. The STP multiplier is
always positive, preserving inhibitory polarity. Then activate STP only on
Synapse 1 and use Synapse 2 as a static control.

## Analysis and interpretation

Record the existing synaptic-current channel and postsynaptic Vm. Graph the
event increment against stimulus number and the paired-pulse ratio against
interval. Explain how a change in synaptic efficacy differs from (i) temporal
summation of residual current, (ii) changing the current-decay knob, and
(iii) a change in the postsynaptic neuron's intrinsic excitability.

In hardware recordings, use dedicated baseline and STP files with the preset
included in each filename. The current 16-byte binary sample payload and
eight recorded signals remain unchanged: STP states are *not* yet explicit
telemetry channels. The hardware CSV timing is reconstructed from packets
and can be affected by packet loss; do not treat it as a precisely timestamped
STDP dataset.

## Implementation notes

Firmware: \`STP_functions.h\`, called from \`update_Synapse()\` on each rising
edge. GUI: \`stp_controls.py\`. Emulator: \`stp_model.py\`.
Both synapses hold independent transient histories. The \`STP1 N\` and
\`STP2 N\` serial commands select modes 0–3 and reset transient history.
A GUI reconnect replays the selected modes and therefore resets history.
The original signed gain knobs and synaptic-current decay remain separate.

To verify the mathematical models independently of the full application:

- Python: run \`python -m unittest discover -s tests -p test_stp_model.py\`
  from the desktop GUI directory.
- C++: run \`g++ -std=c++17 -Wall -Wextra -pedantic
  Firmware/Spikeling_V3/tests/stp_model_smoke.cpp -o /tmp/stp_smoke && /tmp/stp_smoke\`
  from the repository root.

Use Arduino IDE and an ESP32-S3 board for the separate firmware compilation
and device validation; the host-side smoke test only checks the pure STP model.
