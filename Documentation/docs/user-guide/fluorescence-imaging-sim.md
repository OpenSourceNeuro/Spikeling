# **Fluorescence imaging simulation**

This page explains the **fluorescence imaging simulation** in the Spikeling GUI: what it represents, how it is computed from membrane potential (**Vm**), and how to use it for teaching.

Spikeling’s imaging simulation is not a camera and not a microscope pipeline. It is a **conceptual bridge** between:
- fast electrical activity (Vm and spikes), and
- slower optical readouts (calcium and fluorescence) that students commonly see in modern systems neuroscience.

See also:
- [Concepts](concepts.md) (why Vm can be transformed into fluorescence)
- [GUI overview](gui-overview.md) (where the Imaging screen lives)
- [Teaching hub → Lab 4 — Imaging](../teaching-hub/lab-handouts/lab-04-imaging.md) (structured activity)

---

## **What this simulation is **

- a teaching model that converts **Vm / spiking activity** into:
  1) a simulated **intracellular calcium** trace, and  
  2) a simulated **fluorescence** trace
- a way to explain why fluorescence signals are:
  - delayed relative to spikes
  - smoother (low-pass filtered)
  - often non-linear and baseline-dependent
- a tool for demonstrating common analysis concepts such as **ΔF/F**

---

## **The conceptual pipeline: Vm → calcium → fluorescence**

The simulation is built around three simple ideas that match how students should reason about imaging data:

### **1) Spikes drive calcium influx**
Spikes (or spike-like events inferred from Vm) are treated as the main driver of calcium entry.

Teaching translation:
> “A spike happens quickly, but calcium rises and decays more slowly.”

### **2) Calcium is slow compared to Vm**
The calcium trace is a **filtered** representation of spiking: it rises with activity and decays with a characteristic time constant.

Teaching translation:
> “Even if Vm returns to baseline, calcium can stay elevated.”

### **3) Fluorescence is a transformation of calcium**
The fluorescence trace is a further transformation of calcium into an optical-like signal. In real imaging, this relationship can be non-linear and depends on indicator kinetics and baseline.

Teaching translation:
> “Fluorescence is an indirect proxy for spikes, not a direct measurement of Vm.”

---

## **Where to find it in the GUI**

Go to:

**Imaging → Imaging Simulation**

The imaging screen is designed to look and behave like the main oscilloscope page, but for calcium/fluorescence.

---

## **How to use the Imaging Simulation screen**

### **Step 1 — Choose a source**

Spikeling imaging can be driven by either:

- **Spikeling hardware** (live Vm stream from the device), or
- **GUI emulator** (no hardware required; best for demonstrations)

Use the “source” selector (e.g., *from GUI emulator*). If you are teaching a class without enough devices, the emulator is often the cleanest option.

### **Step 2 — Choose which traces to display**

Typical display options include:

- **Vm** (Spikeling and optional Synapse channels)
- **Calcium** (Spikeling and optional Synapse channels)
- **Fluorescence** (Spikeling and optional Synapse channels)
- **Stimulus** (so students can align cause and effect)

### **Step 3 — (Optional) Enable ΔF/F**

ΔF/F is a common normalised fluorescence metric.

- **F** is a baseline fluorescence level (often estimated from a low-activity period)
- **ΔF** is the change relative to baseline
- ΔF/F makes it easier to compare recordings with different baseline brightness

Teaching translation:
> “ΔF/F is a normalised measure of relative activity rather than absolute brightness.”

### **Step 4 — Axis scaling**

If available, **Auto Range Y axis** is helpful in early demos.
For comparative labs (same stimulus, different mode), it is often better to keep axis ranges fixed so students can compare amplitudes honestly.

### **Step 5 — Record imaging data**

The imaging screen includes a recording section similar to the Neuron Interface:

1. Choose a **directory**
2. Enter a **filename**
3. Press **Record**

This produces an export students can analyse later (e.g., comparing Vm vs fluorescence timing).

---

## **What students should learn from it**

### **Key lesson 1: fluorescence is delayed**
A spike occurs in milliseconds. Calcium and fluorescence typically peak later. Students should be able to answer:
- “Why does fluorescence peak after spikes?”
- “Why can fluorescence remain elevated after spiking stops?”

### **Key lesson 2: fluorescence is smoother**
Vm can contain sharp spikes and fast oscillations. Fluorescence is slower and smoother. Students should be able to explain:
- why fast voltage features are lost in fluorescence
- why individual spikes can merge into a single broad transient at high firing rates

### **Key lesson 3: the mapping is not one-to-one**
At low firing rates, individual spikes may produce distinct transients.
At higher rates, transients overlap and it becomes difficult to infer exact spike timing.

This supports a core modern neuroscience idea:
> Imaging is excellent for population activity patterns, but it is not a direct substitute for electrophysiology when precise spike timing is required.

---

## **Suggested demonstrations (work well in teaching)**

### **Demo A — one stimulus, two neuron modes**
1. Keep the stimulus the same (e.g., square-wave or a step protocol).
2. Switch neuron mode (tonic spiking vs adapting / phasic).
3. Observe:
   - Vm spikes differ strongly across modes
   - calcium/fluorescence patterns differ (peak height, decay, steady-state)

Teaching question:
> “Does fluorescence reflect ‘number of spikes’, ‘burstiness’, or both?”

### **Demo B — frequency sweep (chirp / ZAP-like input)**
1. Apply a chirp stimulus (linear or exponential sweep).
2. Observe Vm resonance-like behaviours (if present) and how fluorescence averages over them.

Teaching question:
> “Which features survive the Vm → fluorescence transformation?”

### **Demo C — near-threshold noise**
1. Hold Vm just below threshold (DC injection / patch clamp).
2. Add noise until occasional spikes occur.
3. Observe that fluorescence becomes an intermittent transient signal.

Teaching question:
> “Why is imaging often analysed statistically rather than spike-by-spike?”

---

## **Common pitfalls and how to explain them**

### **“Fluorescence does not look like Vm”**
Correct: it should not. Fluorescence is downstream of calcium kinetics and indicator dynamics.

### **“My fluorescence amplitude changed when I changed baseline”**
That is expected. Baseline and normalisation (ΔF/F) matter a lot in optical measurements.

### **“I cannot infer exact spike timing from fluorescence”**
Also expected, especially at high firing rates where transients overlap.

---

## **What to read next**

- How to record and export: [Recording and export](recording-and-export.md)
- Analysis of fluorescence-like signals: [Data analysis → Fluorescence analysis](../data-analysis/fluorescence-analysis.md)
- Structured teaching activity: [Teaching hub → Lab 4 — Imaging](../teaching-hub/lab-handouts/lab-04-imaging.md)
