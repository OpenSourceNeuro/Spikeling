# **Synapses and inputs**

This experiment introduces synaptic integration using Spikeling. You will connect a presynaptic unit to a postsynaptic unit (or emulate the same setup in software) and observe how spikes from one neuron produce input currents and Vm changes in another neuron.

Spikeling simplifies synaptic physiology into a teaching-friendly model:

- presynaptic **spikes** arrive as discrete events
- each spike generates an **exponentially decaying synaptic current**
- synapse gain can be **positive** (excitatory) or **negative** (inhibitory)

Background reading: [Concepts → Synapses and networks](../user-guide/concepts.md#synapses-and-networks-two-synaptic-inputs).

---

## **Learning goals**

By the end of this experiment, students should be able to:

- explain how presynaptic spikes create postsynaptic input currents
- distinguish **excitatory** vs **inhibitory** synapses by sign and effect on Vm
- demonstrate temporal summation (integration) of repeated synaptic events
- predict how synapse gain and decay shape postsynaptic spiking
- build simple network motifs (feedforward excitation, inhibition, E/I balance)

---

## **What you need**

### Hardware route
- **Two Spikeling units** (Unit A presynaptic, Unit B postsynaptic)
- A **TRS cable** to connect:
  - **Axon output (Unit A) → Synapse input (Unit B)**
- Spikeling GUI for monitoring and recording

### Emulator route
- One computer running the GUI
- Emulator mode with **Auxiliary Neuron 1** (and optionally Auxiliary Neuron 2)

Recommended signals to display on the postsynaptic unit:
- **Vm**
- **Synapse 1 input current** / **Synapse 2 input current** (if available)
- **Total input current (Itot)** (optional but very helpful)

---

## **Part A — Wiring (hardware)**

1. Connect Unit A and Unit B to the GUI (or select one to monitor at a time depending on your setup).
2. Patch a TRS cable:
   - **Axon output (Unit A) → Synapse input 1 (Unit B)**

!!! note "Ground reference"
    If you see confusing behaviour, confirm that both units share a consistent ground reference through the cable conventions used in your setup (see: [Controls and I/O](../user-guide/controls-and-io.md)).

---

## **Part B — Create a presynaptic spike train**

### Presynaptic (Unit A)
1. Choose a neuron mode that spikes reliably.
2. Use injected current (hardware knob or Patch clamp slider) to produce steady spiking.
3. Optionally add a low level of noise for realism (but keep it minimal at first).

### Target
A stable, regular presynaptic spike train makes postsynaptic effects easier to interpret.

---

## **Part C — Excitatory synapse (positive gain)**

### Postsynaptic (Unit B)
1. Ensure Unit B is initially **below threshold** (silent) using its current injection / patch clamp.
2. Set **Synapse 1 gain** to a **positive** value.
3. Observe Vm on Unit B.

### What to look for
- Each presynaptic spike produces a **brief depolarising drive**
- With repeated spikes, depolarisations can **summate**
- If strong enough, the synaptic drive can recruit postsynaptic spiking

!!! tip "Teaching tip"
    Start with Unit B just below threshold. Then increase synapse gain slightly until synaptic input reliably triggers spikes. This makes “synapses can drive firing” very intuitive.

---

## **Part D — Inhibitory synapse (negative gain)**

1. Keep the presynaptic spike train the same.
2. Set **Synapse 1 gain** to a **negative** value.
3. Observe postsynaptic Vm and spiking.

### What to look for
- Each presynaptic spike produces a **hyperpolarising** effect or a reduction in spiking probability
- Inhibition can:
  - suppress spiking entirely
  - delay spikes
  - create spike skipping (missed spikes)

---

## **Part E — Synaptic summation and time constants (decay)**

**Concept:** synapses are filters in time. If the synaptic current decays slowly, inputs integrate more strongly.

### Steps
1. Set Unit B below threshold.
2. Keep synapse gain fixed (moderate excitatory).
3. Increase presynaptic firing rate (increase injection in Unit A).
4. Observe whether postsynaptic depolarisation builds up.

### Expected observations
- At low presynaptic rate: isolated postsynaptic responses
- At higher presynaptic rate: responses overlap and **summate**
- Summation can push Vm over threshold and trigger postsynaptic spikes

If your build exposes synapse decay parameters in the GUI:
- **faster decay** → sharper, briefer postsynaptic effects (less summation)
- **slower decay** → more integration (more summation)

---

## **Part F — Two synapses: coincidence and competition**

Spikeling supports **two synaptic inputs**, which enables simple network motifs.

### Motif 1: coincidence detection (two excitatory synapses)
1. Connect Unit A → Synapse 1 on Unit B.
2. Connect a second presynaptic unit (Unit C) → Synapse 2 on Unit B (or use emulator Auxiliary Neuron 2).
3. Set both synapses excitatory at moderate gain.
4. Adjust presynaptic timing/rates so that spikes sometimes coincide.

**Observation:** coincident excitatory input can trigger postsynaptic spikes when either input alone cannot.

### Motif 2: E/I balance (excitation + inhibition)
1. Set Synapse 1 as excitatory (positive gain).
2. Set Synapse 2 as inhibitory (negative gain).
3. Compare postsynaptic output under different E/I ratios.

**Observation:** inhibition can veto or shape excitation, controlling spike timing and probability.

---

## **Emulator version (no hardware needed)**

In emulator mode, reproduce the same logic:

1. Start emulator and configure the **main neuron** (postsynaptic).
2. Open **Auxiliary Neuron 1** and drive it to spike (Patch clamp).
3. Enable coupling (toggle **Synapse main neuron**).
4. Use Synapse gain (1 or 2) to set:
   - excitatory (positive)
   - inhibitory (negative)
5. Repeat with a second auxiliary neuron if available to demonstrate E/I balance.

---

## **What to measure (simple, robust metrics)**

Choose one metric depending on your course level:

- **Postsynaptic spike probability** vs synapse gain
- **Postsynaptic firing rate** vs presynaptic firing rate
- **Latency** from presynaptic spike to postsynaptic spike (when recruited)
- **Summation index**: Vm deflection after a burst vs a single presynaptic spike

---

## **Discussion prompts**

- Why do synapses need a time course (why not instantaneous)?
- What changes when synapse sign is inverted?
- How does presynaptic firing rate interact with synaptic decay to control integration?
- In what situations might inhibition be more important than excitation?

---

## **What to read next**

- Two-unit experiments and motifs: [Network with two units](network-two-units.md)
- Threshold and adaptation background:
  - [Excitability and threshold](excitability-and-threshold.md)
  - [Adaptation and firing patterns](adaptation-and-firing-patterns.md)
- Recording and analysis pipeline: [Recording and export](../user-guide/recording-and-export.md)
