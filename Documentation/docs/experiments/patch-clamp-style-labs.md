# **Patch-clamp-style labs**

This page provides a set of **patch-clamp-inspired laboratory activities** designed for Spikeling. The goal is to teach the *logic* of electrophysiology (current clamp thinking, excitability, adaptation, synaptic integration) using a reproducible hardware+GUI workflow.

These labs are written for university-level teaching:

- quick to run (typically 10–30 minutes per activity)
- easy to scaffold (intro → prediction → run → interpret)
- compatible with **hardware** and **emulator mode**

If you want a minimal setup sequence first, see: **[Quickstart → First experiment](../quickstart/first-experiment.md)**.

---

## **What students should practise**

Across the labs, students will practise:

- identifying baseline Vm, threshold, and spiking regimes
- predicting responses before changing a parameter (“hypothesis-first”)
- designing simple protocols to test excitability and adaptation
- measuring outputs (spike count, firing rate, latency, jitter)
- connecting stimulation choice (waveform, frequency, amplitude) to interpretation
- recording and exporting data for analysis (CSV → Python)

---

## **General workflow (applies to all labs)**

1. **Start from a known baseline**
   - current injection at **0** (centre detent / patch clamp neutral)
   - stimulus off
   - noise off (unless the lab is about noise)

2. **Choose one neuron mode and keep it fixed**
   - The neuron mode controls intrinsic dynamics.
   - Changing mode mid-lab is useful, but only after students have drawn conclusions with one stable mode.

3. **Apply an input**
   - DC injection (Patch clamp / current injection potentiometer), or
   - programmed stimulus from the GUI (Steps, sine/triangle, chirp, noise), or
   - synaptic input from another unit / emulator auxiliary neuron.

4. **Observe Vm and spikes**
   - Vm tells the state; spikes are discrete events.

5. **Record**
   - Record a short segment (10–30 s) once the behaviour is stable.
   - Export to CSV.

6. **Measure one thing**
   - spike count, firing rate, latency, adaptation index, etc.

7. **Interpret**
   - connect “what I changed” to “what I saw”.

!!! tip "Teaching rhythm"
    The fastest way to build intuition is: **predict → test → explain**.
    Make students state the expected change *before* moving a slider.

---

## **Lab 0 — Warm-up: finding threshold (current clamp intuition)**

**Question:** How much injected current is needed to make the neuron spike?

**Inputs:** DC current injection (Patch clamp / current injection potentiometer)

### Steps
1. Ensure stimulus and noise are off.
2. Increase injected current until Vm begins to spike.
3. Reduce slightly until spiking stops again.
4. Repeat once to confirm reproducibility.

### What to record / measure
- threshold current (approximate)
- Vm just below threshold vs just above threshold
- spike latency (time from start of injection to first spike)

### Expected observations
- Below threshold: Vm shifts but no spikes.
- Near threshold: small differences can change outcome.
- Above threshold: sustained spiking.

---

## **Lab 1 — Step protocol: excitability and firing rate**

**Question:** How does firing rate depend on input amplitude?

**Inputs:** GUI **Steps** stimulus routed as **Current** (or manual DC steps)

### Steps
1. Route stimulus to **Current**.
2. Choose a simple step: baseline → step → baseline (e.g., 1–2 s step).
3. Run multiple step amplitudes (increasing strength).
4. Keep neuron mode fixed.

### What to measure
- spike count during the step
- mean firing rate during the step (spikes / second)

### Expected observations
- increased step amplitude increases firing rate
- spiking may show adaptation (rate decreases over time during the step)

---

## **Lab 2 — Spike-frequency adaptation (early vs late rate)**

**Question:** Does firing rate remain constant under constant drive?

**Inputs:** constant DC injection or a long step

### Steps
1. Apply a sustained depolarising current that produces stable spiking.
2. Keep it constant for 5–10 seconds.
3. Record and export.

### What to measure
- firing rate in an early window (e.g., first 1–2 s)
- firing rate in a late window (e.g., last 1–2 s)
- adaptation index: (early − late) / early

### Expected observations
- rate typically decreases over time in adapting modes
- some modes adapt weakly or not at all (fast-spiking-like behaviour)

---

## **Lab 3 — Subthreshold dynamics and resonance (optional extension)**

**Question:** Does the neuron respond preferentially to certain frequencies?

**Inputs:** sine wave or chirp stimulus at subthreshold amplitude

### Steps
1. Set injected current so Vm is below threshold (no spikes).
2. Apply a small sine wave (or chirp) stimulus.
3. Observe the amplitude of Vm oscillations as frequency changes.

### What to look for
- Vm response may grow at certain frequency ranges (resonance-like behaviour)
- responses may depend strongly on neuron mode

!!! note
    This is an advanced conceptual lab. If short on time, run it as a demonstration.

---

## **Lab 4 — Noise and stochastic spiking**

**Question:** Can noise alone trigger spikes near threshold?

**Inputs:** Noise + near-threshold bias current

### Steps
1. Bias Vm just below threshold using injected current.
2. Increase Noise gradually.
3. Observe when intermittent spikes appear.

### What to measure
- spike rate as a function of noise level
- spike-time jitter (variability)

### Expected observations
- spikes appear probabilistically at sufficient noise levels
- rate increases with noise amplitude
- spike timing becomes less precise

---

## **Lab 5 — Synaptic input as a current source (two-unit coupling)**

**Question:** How do excitatory vs inhibitory synapses affect postsynaptic spiking?

**Inputs:** presynaptic spiking from another unit (or emulator auxiliary neuron)

### Steps (hardware)
1. Connect: **Axon output (Unit A) → Synapse input (Unit B)**.
2. Make Unit A spike reliably (inject current).
3. Set synapse gain on Unit B:
   - positive (excitatory) then negative (inhibitory)
4. Observe changes in Unit B Vm and spiking.

### Steps (emulator)
1. Configure **Auxiliary Neuron 1** to spike.
2. Enable **Synapse main neuron**.
3. Set synapse sign/gain and observe the main neuron output.

### What to measure
- probability of postsynaptic spikes per presynaptic spike train
- change in baseline Vm under sustained synaptic drive
- suppression effects under inhibition

---

## **Lab 6 — “Design your own protocol” (capstone mini-lab)**

**Question:** Can students propose and test a hypothesis about excitability?

### Example hypotheses
- “This neuron responds more strongly to low frequencies than high frequencies.”
- “Inhibition can prevent spiking even when DC current is above threshold.”
- “Noise increases spike-time variability but not mean Vm.”

### Requirements (student checklist)
- write a one-sentence hypothesis
- choose a stimulus waveform that tests it (Steps, sine, chirp, noise)
- record one dataset
- compute one metric
- interpret results in 3–5 sentences

---

## **Practical notes (common issues)**

!!! tip "Start simple"
    If results are confusing, disable everything except one input pathway:
    **no noise, no light, no synapses** — then add one pathway at a time.

- If traces clip or look unstable, reduce stimulus strength and confirm grounding/cables.
- If the device stops streaming, press **Reset** and re-connect in the GUI.
- For teaching at scale, use emulator mode first to standardise expectations.

---

## **What to read next**

- Structured activities by topic:
  - [Excitability and threshold](excitability-and-threshold.md)
  - [Adaptation and firing patterns](adaptation-and-firing-patterns.md)
  - [Synapses and inputs](synapses-and-inputs.md)
  - [Network with two units](network-two-units.md)

- How to record and analyse:
  - [Recording and export](../user-guide/recording-and-export.md)
  - [Python quickstart](../data-analysis/python-quickstart.md)
