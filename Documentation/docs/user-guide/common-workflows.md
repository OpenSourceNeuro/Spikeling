# **Common workflows**

This page collects a set of high-frequency “how people actually use Spikeling” workflows. Each workflow is written to be:

- **quick to scan**
- **reproducible** (clear start state, clear steps)
- **teaching-friendly** (what students should notice and conclude)

If you are new, start with: **Quickstart → First experiment** and return here when you want structured protocols.

See also:
- [Concepts](concepts.md)
- [Device overview](device-overview.md)
- [Recording and export](recording-and-export.md)
- [Experiments](../experiments/index.md)

---

## **Workflow 1 — Connect, verify signal, and set a baseline**

**Goal:** confirm the device/emulator is behaving and Vm is readable.

1. **Connect** hardware (or start emulator).
2. In the Neuron Interface plot, enable:
   - **Vm**
   - **Total Current Input** (if available)
   - **Stimulus** (if you will use it)
3. Confirm Vm shows a stable baseline (no drift, no clipping).
4. Use the **current injection** (hardware knob or patch clamp slider) to bring Vm:
   - below threshold (silent), then
   - close to threshold (occasional spikes), then
   - above threshold (sustained spiking)

**What to look for**
- Vm should change smoothly with injected current.
- Spikes should appear only once threshold is crossed.
- Spike feedback (LED/buzzer) should match the trace (hardware).

---

## **Workflow 2 — Find threshold and demonstrate excitability**

**Goal:** teach “below threshold vs above threshold” clearly.

1. Start from **0 injected current** (centre detent / patch clamp neutral).
2. Increase injected current slowly until spikes appear.
3. Reduce slightly until spikes stop again.

**What to look for**
- A small change in input can switch the system from silent to spiking.
- Near threshold, noise and small fluctuations matter.

**Teaching prompt**
- “What changes qualitatively when threshold is crossed?”

---

## **Workflow 3 — Spike-frequency adaptation under constant drive**

**Goal:** show that firing rate can change even when the input is constant.

1. Inject enough current to produce sustained spiking.
2. Hold the injection steady for several seconds.
3. Observe whether the spike rate slows down.

**Optional quantification**
- Record 10–20 seconds.
- Compute firing rate in early vs late window.
- Summarise as adaptation strength.

**Teaching prompt**
- “Why might a neuron reduce its firing over time under constant input?”

---

## **Workflow 4 — F–I curve (firing rate vs injected current)**

**Goal:** replicate a classic current-clamp characterisation.

1. Choose one neuron mode and keep it fixed.
2. Apply a series of current steps (manual or GUI Steps stimulus).
3. For each step level, measure mean firing rate.
4. Plot firing rate vs input level.

**What to look for**
- threshold-like onset of firing
- gain (slope) changes across modes
- adaptation can create differences between “early rate” and “late rate”

See also: [Experiments → Excitability and threshold](../experiments/excitability-and-threshold.md)

---

## **Workflow 5 — Use the stimulus output as injected current**

**Goal:** use the GUI stimulus generator as a function generator for current injection.

1. Patch a cable:
   - **Stimulus output → DC/current injection input**
2. In the GUI, choose a stimulus type (Steps is best to start).
3. Increase stimulus strength slowly while watching Vm.

**What to look for**
- Vm follows the stimulus time-course.
- spikes align with stimulus epochs (especially for steps/pulses).

**Teaching prompt**
- “How does waveform shape change spiking compared to constant DC injection?”

---

## **Workflow 6 — Square-wave stimulation: frequency vs strength**

**Goal:** teach how two intuitive stimulus knobs affect output.

1. Use the **on-board square stimulus** (or GUI square/pulse train).
2. Sweep **strength** at fixed frequency.
3. Sweep **frequency** at fixed strength.

**What to look for**
- strength controls recruitment into spiking and spike reliability
- frequency determines how often depolarising drive is applied (and may push the neuron into different regimes)

---

## **Workflow 7 — Noise near threshold (stochastic spiking)**

**Goal:** show why spiking can be probabilistic.

1. Set injected current so Vm sits **just below threshold** (no spikes).
2. Increase **Noise** gradually.
3. Observe occasional spikes emerge without changing the mean input.

**What to look for**
- variability and spike-time jitter
- spikes occur at unpredictable times, but rate increases with noise amplitude

**Teaching prompt**
- “Why does the same mean input produce different outcomes when noise is present?”

---

## **Workflow 8 — Light stimulation (photoreceptor pathway)**

**Goal:** demonstrate sensory stimulation logic: light input → Vm/spikes.

**Two common setups**
- **Controlled LED pathway:** Stimulus output → LED cable → photodiode
- **External light:** any modulated LED/light source aimed at the photodiode

**Workflow**
1. Set **Photo-gain** to a modest value.
2. Deliver light pulses or flicker.
3. Invert gain sign to show excitatory vs inhibitory sensory drive.

**What to look for**
- polarity matters: same light can depolarise or hyperpolarise depending on gain sign
- photoreceptor dynamics (decay/recovery) shape responses to rapid flicker

---

## **Workflow 9 — Two-unit network: Axon → Synapse**

**Goal:** teach synaptic integration and E/I coupling.

1. Connect:
   - **Axon output (unit A) → Synapse input (unit B)**
2. Make unit A spike (inject current).
3. Adjust Synapse gain on unit B:
   - positive = excitatory
   - negative = inhibitory

**What to look for**
- spike-evoked synaptic currents with exponential decay
- summation across repeated presynaptic spikes
- recruitment or suppression of postsynaptic firing

See also:
- [Experiments → Synapses and inputs](../experiments/synapses-and-inputs.md)
- [Experiments → Network with two units](../experiments/network-two-units.md)

---

## **Workflow 10 — Emulator: build a network without cables**

**Goal:** teach network logic in a reproducible environment.

1. Start emulator.
2. Configure **Auxiliary Neuron 1** to spike.
3. Toggle **Synapse main neuron**.
4. Set synapse sign/gain (Synapse 1 or 2).
5. Observe main neuron recruitment / suppression.

This workflow is ideal for large classes where not every student has two physical units.

---

## **Workflow 11 — Record, export, and analyse (minimal pipeline)**

**Goal:** produce a clean dataset students can analyse.

1. Choose a simple protocol (Steps or square stimulation).
2. Record 10–30 seconds.
3. Export CSV.
4. Analyse:
   - Vm trace
   - stimulus/current trace
   - spike detection and rate
   - optionally: F–I curve or adaptation index

See also:
- [Recording and export](recording-and-export.md)
- [Data analysis → Python quickstart](../data-analysis/python-quickstart.md)

---

## **Workflow 12 — Classroom-ready “demo sequence” (3 minutes)**

If you need a fast outreach demonstration:

1. Inject current to show silent → spiking transition.
2. Turn up noise near threshold for stochastic spikes.
3. Switch neuron mode and repeat (same input, different output).
4. Optional: connect a second unit and show synaptic recruitment.

---

## **What to read next**

- Structured protocols with expected outcomes: [Experiments](../experiments/index.md)
- Curriculum modules and teaching resources: [Teaching Hub](../teaching-hub/index.md)
- If you want analysis templates: [Data analysis](../data-analysis/index.md)
