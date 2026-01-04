# **Network with two units**

This experiment builds a minimal spiking network using **two Spikeling units** (or a two-neuron setup in **Emulator mode**). You will create a connection from one unit’s **axon output** to the other unit’s **synapse input**, then explore how coupling sign, strength, and presynaptic firing pattern shape the postsynaptic output.

The point is to teach the simplest network truth in neuroscience:

> Neurons influence each other through spikes, and synapses determine whether those spikes drive or suppress activity.

Background reading:
- [Concepts → Synapses and networks](../user-guide/concepts.md#synapses-and-networks-two-synaptic-inputs)
- [Synapses and inputs](synapses-and-inputs.md)

---

## **Learning goals**

By the end of this experiment, students should be able to:

- wire a two-unit network (axon → synapse) safely and consistently
- demonstrate **excitatory** vs **inhibitory** coupling
- show how presynaptic firing rate affects postsynaptic Vm/spiking (temporal summation)
- create basic motifs: feedforward excitation, feedforward inhibition, and E/I balance (optional)
- measure a simple “network transfer function” (presynaptic rate → postsynaptic rate)

---

## **What you need**

### Hardware route
- **Two Spikeling units** (Unit A presynaptic, Unit B postsynaptic)
- TRS cable for: **Axon output (A) → Synapse input (B)**
- Spikeling GUI

### Emulator route
- Emulator mode with **Auxiliary Neuron 1**
- Optional: Auxiliary Neuron 2 (for E/I balance motifs)

Recommended signals to display (postsynaptic):
- **Vm**
- **Synapse input current** (Synapse 1 / Synapse 2, if available)
- Optional: **Total input current (Itot)**

---

## **Part A — Build the connection**

### Hardware wiring
1. Power and connect both units to the GUI as appropriate for your setup.
2. Patch the TRS cable:
   - **Unit A Axon output → Unit B Synapse input 1**

!!! tip "Cable sanity check"
    If the connection behaves oddly, confirm you have not swapped stimulus and axon ports. Use your labelled cables and the mapping in [Controls and I/O](../user-guide/controls-and-io.md).

### Emulator wiring
1. Start emulator.
2. Configure the main neuron as postsynaptic.
3. Open **Auxiliary Neuron 1**.
4. Enable coupling using **Synapse main neuron**.

---

## **Part B — Establish stable presynaptic spiking (Unit A)**

1. Choose a neuron mode that produces reliable tonic spiking.
2. Use injected current (hardware current injection pot / patch clamp slider) to set a steady spike train.
3. Keep noise off for the first pass.

**Goal:** a stable presynaptic spike train makes synaptic effects easier to interpret.

---

## **Part C — Excitatory coupling (positive synapse gain)**

### Setup (Unit B)
1. Set Unit B to a stable baseline below threshold (silent).
2. Set **Synapse 1 gain** to a small **positive** value.

### Sweep
- Increase synapse gain until you observe:
  - clear depolarising postsynaptic responses, and then
  - postsynaptic spiking (if strong enough)

### What to look for
- postsynaptic Vm deflections time-locked to presynaptic spiking
- summation when presynaptic rate increases
- recruitment into spiking when net drive crosses threshold

---

## **Part D — Inhibitory coupling (negative synapse gain)**

### Setup
1. Keep the same presynaptic spike train.
2. Set **Synapse 1 gain** to a **negative** value.

### What to look for
- postsynaptic Vm becomes more hyperpolarised or less excitable
- spiking is delayed, reduced, or abolished
- inhibition can create **spike skipping** if the postsynaptic neuron is already spiking

---

## **Part E — Network transfer function: presynaptic rate → postsynaptic rate**

This is a clean quantitative network measurement.

### Steps
1. Fix synapse sign and gain (e.g., moderate excitatory).
2. Run several presynaptic firing rates by changing Unit A injected current:
   - low rate
   - medium rate
   - high rate
3. For each presynaptic rate, record 10–20 seconds and measure:
   - presynaptic firing rate (Hz)
   - postsynaptic firing rate (Hz)

### Expected observations
- excitatory coupling: postsynaptic rate increases with presynaptic rate (often non-linear)
- inhibitory coupling: postsynaptic rate decreases as presynaptic rate increases

---

## **Part F — Timing and coincidence (optional)**

If you have **three units** (or emulator with two auxiliaries), you can show coincidence detection:

- Unit A → Synapse 1 on Unit B (excitatory)
- Unit C → Synapse 2 on Unit B (excitatory)

Adjust presynaptic timing so spikes sometimes coincide.

**Observation:** coincident input can recruit a postsynaptic spike when either input alone cannot.

---

## **Part G — E/I balance (optional but powerful)**

Use two inputs with opposite sign:

- Synapse 1: excitatory (positive)
- Synapse 2: inhibitory (negative)

Explore how inhibition shapes excitation:

- vetoing spikes
- delaying spikes
- sharpening spike timing
- controlling output rate without changing mean input current directly

---

## **Measurements (choose one, depending on level)**

Simple, robust metrics:

- **Postsynaptic firing rate** vs synapse gain
- **Postsynaptic spike probability** per presynaptic burst
- **Latency** between presynaptic spike and postsynaptic spike
- **Summation index**: peak Vm deflection after a burst / after a single spike

---

## **Common issues**

- **No postsynaptic effect**
  - presynaptic unit may not be spiking
  - synapse gain may be near zero
  - wrong ports/cable routing

- **Postsynaptic neuron saturates**
  - synapse gain too strong
  - postsynaptic bias current too depolarising
  - reduce gain and re-centre the postsynaptic baseline

---

## **Discussion prompts**

- Why does synaptic decay enable temporal integration?
- How can inhibition control spike timing without necessarily changing mean Vm much?
- Why is the network transfer function non-linear near threshold?
- What would happen if both neurons were adapting strongly?

---

## **What to read next**

- Detailed synapse mechanisms: [Synapses and inputs](synapses-and-inputs.md)
- Intrinsic dynamics: [Adaptation and firing patterns](adaptation-and-firing-patterns.md)
- Threshold background: [Excitability and threshold](excitability-and-threshold.md)
- Record and analyse: [Recording and export](../user-guide/recording-and-export.md)
