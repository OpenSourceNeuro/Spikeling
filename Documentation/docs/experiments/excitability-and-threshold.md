# **Excitability and threshold**

This experiment teaches the core electrophysiology idea of **excitability**: a neuron can switch abruptly from **silent** to **spiking** when input drive crosses a threshold-like boundary.

In Spikeling, you will reproduce this using a current-clamp style workflow:

- control input drive (DC injection, steps, stimulus strength)
- observe **Vm** and **spikes**
- quantify the transition point and how it depends on neuron mode, noise, and stimulus waveform

If you need background first, see: **[Concepts → Threshold and excitability](../user-guide/concepts.md#threshold-and-excitability-why-spiking-starts)**.

---

## **Learning goals**

By the end of this experiment, students should be able to:

- define excitability in terms of **input–output transformation**
- locate an approximate **threshold** for spiking under current clamp
- explain why threshold can be **state dependent** (history and adaptation)
- predict how **noise** alters threshold and spike probability
- compare excitability across different **neuron modes**

---

## **What you need**

- Spikeling hardware (or **Emulator mode**)
- Spikeling GUI
- Optional: second unit for synaptic threshold comparisons

Recommended signals to display:

- **Vm**
- **Total input current** (Itot / Input Current, if available)
- **Stimulus** (if using stimulus protocols)

---

## **Practical notes**

- Start with **small** currents/stimulus strengths.
- Keep **noise off** for the first pass (you will add it later).

---

## **Part A — Threshold with direct DC injection (fastest demonstration)**

**Concept:** in current clamp, the simplest protocol is “hold a constant injected current and observe Vm”.

### Steps (hardware)
1. Set the **current injection potentiometer** to the **centre detent** (0 current).
2. Confirm Vm shows a stable baseline.
3. Turn the potentiometer **slowly right** (depolarising) until spikes begin.
4. Turn slightly back left until spiking stops.
5. Repeat once to confirm reproducibility.

### Steps (emulator)
1. Start emulator and open **Neuron Parameters**.
2. Increase **Patch clamp injected current** slowly until spikes begin.
3. Reduce slightly until spiking stops.
4. Repeat once.

### Record / report
- the approximate injection level where spikes first appear (“threshold injection”)
- Vm baseline and Vm just below threshold
- whether the transition is sharp or gradual

!!! tip "Teaching tip"
    Ask students to predict before turning the knob: *“What should Vm do as I increase depolarising current? When do spikes appear?”*

---

## **Part B — Threshold with a step protocol (more measurable)**

**Concept:** threshold depends on timing; a step stimulus gives you a clean “before/after” window.

### Setup
- Use the GUI **Steps** stimulus routed to **Current**.
- Choose a simple baseline → step → baseline waveform.

### Steps
1. Ensure injected DC is near 0 (or at a fixed small bias).
2. Start with a low step strength (no spikes).
3. Increase step strength in small increments until spikes occur during the step.
4. Run each amplitude 2–3 times.

### Record / measure
- minimal step amplitude that evokes spikes
- spike latency (time from step onset to first spike)
- spike count during the step

### Expected observations
- below threshold: Vm depolarises but no spikes
- at threshold: occasional spikes (often variable)
- above threshold: reliable spiking

---

## **Part C — Threshold is not always a fixed number (state dependence)**

In many neuron models (and biological neurons), the effective threshold depends on the neuron’s state and recent history.

### Demonstration 1: adaptation changes threshold-like behaviour
1. Drive the neuron into sustained spiking for a few seconds.
2. Return to a near-threshold condition.
3. Repeat the same step stimulus as in Part B.

**Observation:** the neuron may require a larger step (or spikes may become less reliable) after recent spiking.

### Demonstration 2: bias current shifts threshold
1. Set a small constant depolarising bias.
2. Re-run the step series.

**Observation:** threshold step amplitude decreases as baseline Vm is closer to spiking.

---

## **Part D — Noise makes threshold probabilistic**

**Concept:** near threshold, noise can trigger spikes even when the mean input is below the deterministic threshold.

### Steps
1. Set injected current so the neuron is **just below threshold** (no spikes).
2. Increase **Noise** gradually.
3. Observe when intermittent spikes appear.
4. Increase noise further to see spike probability/rate rise.

### Measure (simple)
- spike rate vs noise level
- time to first spike after noise is increased (optional)

### Interpretation
- threshold becomes a **probability boundary**, not a single line
- spikes appear via **fluctuation-driven threshold crossings**

---

## **Part E — Compare excitability across neuron modes**

**Concept:** neuron modes differ in intrinsic dynamics; the same input can produce different outputs.

### Steps
1. Choose two or three modes (e.g., regular spiking-like, fast spiking-like, bursting-like).
2. For each mode:
   - find threshold with DC injection (Part A), or
   - find minimal step amplitude that evokes spiking (Part B)
3. Compare:
   - threshold injection/step
   - firing rate above threshold
   - adaptation strength

### Report
A simple table works well:

| Mode | Threshold (DC or step) | Firing rate above threshold | Adaptation (qualitative) |
|---|---:|---:|---|
| Mode A |  |  |  |
| Mode B |  |  |  |
| Mode C |  |  |  |

---

## **Discussion prompts (useful for lab reports)**

- Why might “threshold” depend on recent spiking?
- How does adding noise change the meaning of threshold?
- What does it mean for a neuron to be “more excitable”?
- If two modes have the same threshold, can their firing patterns still differ?

---

## **Extensions (optional)**

- **Strength–duration curve:** vary step duration as well as amplitude.
- **Spike-triggered averages:** align Vm or current around spikes.
- **Synaptic threshold:** use an excitatory synapse input as the drive and ask how much presynaptic spiking is needed to recruit postsynaptic spikes.

---

## **What to read next**

- Pattern diversity: [Adaptation and firing patterns](adaptation-and-firing-patterns.md)
- Synaptic drive: [Synapses and inputs](synapses-and-inputs.md)
- Two-unit coupling: [Network with two units](network-two-units.md)
- Data pipeline: [Recording and export](../user-guide/recording-and-export.md)
