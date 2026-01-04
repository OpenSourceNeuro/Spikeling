# **Adaptation and firing patterns**

This experiment focuses on two closely related ideas:

1. **Spike-frequency adaptation**: firing rate can decrease over time during sustained input.
2. **Firing patterns**: different neurons (and different model parameter sets) produce qualitatively different spike trains under the same stimulation.

Spikeling is ideal for teaching these concepts because you can hold the input constant, change only the neuron **mode**, and observe how the output changes.

Background reading: [Concepts → Adaptation](../user-guide/concepts.md#adaptation-why-firing-slows-down) and [Concepts → Neuron modes](../user-guide/concepts.md#the-neuron-model-izhikevich-dynamics-and-modes).

---

## **Learning goals**

By the end of this experiment, students should be able to:

- describe spike-frequency adaptation and identify it in Vm traces
- quantify adaptation using simple metrics (early vs late firing rate)
- recognise and compare firing patterns across neuron modes
- explain how intrinsic dynamics shape output even under identical input
- connect firing patterns to likely functional roles (e.g., fast-spiking vs adapting)

---

## **What you need**

- Spikeling hardware or **Emulator mode**
- Spikeling GUI
- Recording enabled (recommended)

Signals to display:

- **Vm**
- **Stimulus** (if using step protocols)
- Optional: **Total input current (Itot)**

---

## **General setup (recommended)**

1. Choose a neuron mode and **keep it fixed** for each run.
2. Start with:
   - noise **off**
   - synapses **off**
   - photoreceptor/light input **off**
3. Use either:
   - **DC injection** (hardware current injection pot / patch clamp slider), or
   - a GUI **Step** stimulus routed to **Current**

---

## **Part A — Demonstrate spike-frequency adaptation**

**Concept:** under constant depolarising drive, firing rate can slow over time.

### Protocol (DC injection, simplest)
1. Increase injected current until the neuron shows sustained spiking.
2. Hold the injection constant for **5–10 seconds**.
3. Record the trace.

### Protocol (Step stimulus, cleaner timing)
1. Use the GUI **Steps** stimulus: baseline → step → baseline.
2. Use a step duration of **5–10 seconds**.
3. Increase step amplitude until sustained spiking occurs during the step.
4. Record at least one run.

### What to look for
- spike intervals (ISI) increase over time
- Vm may show a gradual change in baseline during the step
- the first seconds of the step differ from the last seconds

---

## **Part B — Quantify adaptation (simple metrics)**

Pick one recorded run and compute an adaptation metric.

### Metric 1: early vs late firing rate
1. Define:
   - **early window** (e.g., first 1–2 seconds of the step)
   - **late window** (e.g., last 1–2 seconds of the step)
2. Count spikes in each window.
3. Compute firing rates:
   - \( f_\mathrm{early} = \frac{N_\mathrm{early}}{T_\mathrm{early}} \)
   - \( f_\mathrm{late}  = \frac{N_\mathrm{late}}{T_\mathrm{late}} \)

### Metric 2: adaptation index (normalised)
A robust scalar summary is:

\[
AI = \frac{f_\mathrm{early} - f_\mathrm{late}}{f_\mathrm{early}}
\]

- AI ≈ 0: little/no adaptation
- AI closer to 1: strong adaptation

!!! tip "Teaching tip"
    Students often confuse “firing rate slows” with “Vm decreases”. Emphasise that adaptation can occur even if mean Vm stays depolarised.

---

## **Part C — Compare firing patterns across neuron modes**

**Concept:** modes represent different intrinsic dynamics (Izhikevich parameter sets). Under the same input, the output can change qualitatively.

### Suggested mode comparisons
If your build labels differ, choose modes that behave like:

- **Regular spiking-like**: sustained spiking with moderate adaptation
- **Fast spiking-like**: high-rate spiking with weak adaptation
- **Bursting-like**: clusters of spikes separated by quiescence
- **Phasic spiking-like**: one spike (or a brief burst) at onset only

### Protocol
1. Choose a fixed input protocol (important):
   - a long step stimulus, or
   - a constant injected current level
2. For each mode:
   - apply the same input
   - record the Vm trace
3. Compare:
   - onset behaviour (first spike latency, first ISI)
   - steady-state firing rate
   - adaptation strength (AI)
   - whether spiking is tonic, bursting, or phasic

### Report format (recommended)
A simple table works well:

| Mode | Pattern label | First spike latency | Early rate | Late rate | Adaptation index |
|---|---|---:|---:|---:|---:|
| Mode A |  |  |  |  |  |
| Mode B |  |  |  |  |  |
| Mode C |  |  |  |  |  |

---

## **Part D — Input dependence: adaptation changes with drive**

**Concept:** adaptation is often stronger at higher drive, but this depends on mode.

### Steps
1. Select one mode.
2. Run **three step amplitudes** (low, medium, high) that all produce spiking.
3. Compute AI for each.

### Expected observation
- adaptation typically increases with higher firing rate, but not always.
- some modes show minimal adaptation across amplitudes.

---

## **Discussion prompts (for lab report)**

- Why might adaptation be useful biologically?
- How can two neurons with the same threshold have different firing patterns?
- Which mode best matches a neuron type you know (e.g., inhibitory interneuron vs pyramidal cell)?
- How would adaptation affect information transmission over time?

---

## **Extensions (optional)**

- **Inter-spike interval (ISI) plots:** plot ISI vs spike number.
- **Instantaneous firing rate:** \( f_i = 1/\mathrm{ISI}_i \).
- **Spike-triggered averages:** align Vm around spikes.
- **Burst metrics:** number of spikes per burst, burst frequency.

---

## **What to read next**

- If you want the “why” of spikes and threshold: [Excitability and threshold](excitability-and-threshold.md)
- For synaptic interaction and E/I balance: [Synapses and inputs](synapses-and-inputs.md)
- For coupling two devices: [Network with two units](network-two-units.md)
- For data export and analysis: [Recording and export](../user-guide/recording-and-export.md)
