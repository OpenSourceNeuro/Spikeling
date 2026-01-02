# **Concepts**

This page introduces the minimum set of concepts needed to use Spikeling effectively. It is written for quick scanning: each section links a familiar neuroscience idea (current clamp, spikes, synapses) to what you can **see, touch, and measure** on the device and in the GUI.

If you are new: read this once, then return to it while doing Quickstart and the first teaching labs.

---

## **The core idea: practise electrophysiology-style experiments without a full rig**

In a traditional patch-clamp setup, you inject a known current into a neuron and measure the resulting membrane potential (**Vm**), including whether and how the cell fires action potentials. Spikeling recreates this workflow with:

- a compact hardware device implementing a spiking neuron model
- a desktop GUI that provides real-time visualisation and stimulus generation
- a data export path (CSV) supports the same downstream analysis you would do for real electrophysiology

The goal is not to replace patch-clamp hardware, but to make the **logic of electrophysiology** accessible, interactive, repeatable, and teachable.
It is designed to let students practise *the reasoning* of electrophysiology: input–output relationships, excitability, adaptation, synaptic integration, and network interactions.  
(See also: [Device overview](device-overview.md), [GUI overview](gui-overview.md).)

---

## **Signals you will see (what the traces mean)**

### **Membrane potential (Vm), red**

**Vm** is the main signal. It represents the “state” of the neuron model. It is the trace students learn to read first.

Typical behaviours you will observe:

- **Resting baseline**: stable Vm without spiking
- **Hyperpolarisation**: Vm shifts downward (more negative)
- **Depolarisation**: Vm shifts upward (more positive)
- **Spikes**: rapid events when Vm crosses threshold and the model generates an action potential
- **Adaptation**: with sustained input, spikes may slow down over time

In Spikeling teaching labs, most conclusions come from how Vm changes in response to input.

!!! tip "Teaching tip"
    Early teaching wins come from having students predict: “If I increase depolarising current, what should Vm do? When should spikes appear? What should happen to firing rate over time?”

### **Input current (current clamp logic)**

Spikeling is used primarily in a **current-clamp style** workflow: you control an input current and observe Vm.

There are two common ways the input is applied:

- **Direct current injection (DC)** using the on-board **current injection potentiometer**
- **Programmed stimuli** (steps, pulses, trains, noise) initiated from the GUI

These correspond to the same conceptual action: changing the net input current over time.

### **Trigger / digital events**

Many workflows include a digital marker (often called **trigger**) that indicates when a stimulus begins/ends or when a protocol event occurs.

This is used to align traces during analysis and to segment recordings into “baseline vs stimulation” windows.

---
### **Total input current (Itot), green**

In addition to Vm, Spikeling can display a **current trace** that represents the **total input drive** entering the neuron model (**Itot**). This is useful because it makes explicit that the neuron is responding to a *sum* of inputs.

Itot typically includes contributions from:

- **Direct current injection** (current injection potentiometer)
- **Photodiode input** (light converted into current; Photo-gain sets sign and gain)
- **Noise input** (Gaussian noise, adjustable amplitude)
- **Synaptic inputs** (spike-triggered exponentially decaying currents from Synapse 1 and 2)

!!! tip "Teaching tip"
    Encourage students to interpret experiments as: **Itot (input) → Vm (state) → spikes (output)**.  
    When something “unexpected” happens, Itot is often the quickest way to see which input pathway is dominating.

---

## **The most important control: current injection potentiometer**

Spikeling includes a **centre-detent potentiometer** representing direct current injection from a patch pipette.

- **Centre detent**: 0 current (no injection)
- Turn **left**: hyperpolarising current (Vm decreases)
- Turn **right**: depolarising current (Vm increases)

This control is deliberately physical and immediate: it is the fastest way to demonstrate the transition:

**silent → depolarised → spiking → spike-frequency adaptation**

(Quickstart uses this to teach “how to drive Vm” before introducing more structured protocols.)

---

## **Threshold and excitability (why spiking starts)**

Spiking starts when Vm crosses an effective **threshold**. The threshold is not a fixed “line” in all neuron models—many models have state-dependent dynamics—but for teaching, a useful mental model is:

- below threshold: inputs shift Vm but do not spike
- near threshold: small changes can trigger spikes
- above threshold: repeated spiking occurs

This is what makes neurons **excitable**: a small difference in input can qualitatively change the output.

---

## **Adaptation (why firing slows down)**

Many neurons show **spike-frequency adaptation**: a constant depolarising input initially produces fast spiking, then the spiking rate slows.

In Spikeling, you can see adaptation by:

1. Turning the current injection potentiometer rightward enough to cause sustained spiking
2. Holding it steady for several seconds
3. Watching the interval between spikes increase over time

In experiments, adaptation is often summarised by an **F–I curve** (firing rate vs input current) and by comparing early vs late firing rate during a step.

---

## **The neuron model: Izhikevich dynamics and “modes”**

Spikeling uses an **Izhikevich-style** spiking neuron model, which is widely used in computational neuroscience because it can reproduce diverse firing patterns with a compact set of equations and a small number of parameters.

### **What changes when you change “mode”**
A “mode” changes the four key parameters of the Izhikevich formulation (commonly labelled **a, b, c, d**), which tune:

- recovery/adaptation dynamics
- spike reset behaviour
- whether the neuron behaves more like regular-spiking, fast-spiking, bursting, etc.

### **How modes are selected (board revision detail)**

- **Board v2.x**: an on-board **Mode** button cycles through **12 preset modes**
- **Board v3.x**: neuron mode is selected from the **GUI** (no on-board cycling)

!!! note
    Mode selection changes the model’s intrinsic excitability and adaptation. For teaching, it is useful to keep the stimulus fixed and show how different modes produce different firing patterns.

---
## **Stimulus protocols: what is built in vs what the GUI adds**

A stimulus protocol is simply the time-course of injected input.

### **On-board stimulus (default)**
By default, the board provides a **square-wave stimulus** where users can adjust:

- **frequency** (how fast it repeats)
- **strength** (amplitude)

This is ideal for rapid classroom demonstrations: “change frequency, change strength, watch Vm.”

### **GUI stimulus modes (built-in)**
The GUI expands stimulus generation for proper protocol settings. Out of the box, users can select:

- **Steps** (baseline → constant input → baseline)
- **Sine waves**
- **Triangle waves**
- **Chirps / ZAP-style sweeps**
  (linear sweep, exponential sweep, and amplitude-increasing variants)
- **Noise**

These waveforms are standard in electrophysiology and modelling for probing excitability, resonance/impedance, temporal integration, and variability.

### **Custom stimuli**
Beyond built-in modes, the GUI supports imported user-defined/custom stimuli. This is the bridge from “following a lab handout” to “designing your own protocol”.

!!! tip "Teaching tip"
    Treat the stimulus generator as a “function generator for neurons”. Have students state the hypothesis first (“I think this neuron prefers low frequencies”), then choose a waveform that tests it (e.g., a chirp).

---
---

## **Noise input: why spikes can become stochastic**

Real neurons are never perfectly quiet: thermal (Johnson–Nyquist) noise, ion channel fluctuations, synaptic background activity, and measurement noise all add variability. This is one reason spike timing can be **probabilistic**, especially near threshold.

Spikeling includes an on-board **Noise** potentiometer that generates **Gaussian noise** added to the input drive.

- Increasing the Noise potentiometer increases the **noise amplitude**
- Noise is summed into the **total input current (Itot)**
- Near threshold, noise can:
  - trigger occasional spikes (“stochastic spiking”)
  - jitter spike timing (reduced precision / increased variability)
  - reveal that small differences in Vm can change spike outcome

!!! tip "Teaching tip"
    A simple classroom demonstration is to set the neuron *just below* spiking with the current injection potentiometer, then slowly increase Noise. Students will see spiking emerge intermittently without changing the mean input—illustrating variability-driven threshold crossings.
---

## **Light input: photodiode as a visual sensory stimulation pathway**

Spikeling includes a **photodiode** that converts changes in light intensity into an input current pathway for the neuron model. Conceptually, this is intended to mimic a **visual sensory experiment**: light is used as the stimulus (as in retinal stimulation), and the neuron’s response is read out as **Vm and spikes**.

### **Two ways to deliver light stimuli**

1. **Controlled light stimulation (recommended): LED stimulus cable**  
   Use the dedicated **LED cable** plugged into the **stimulus output port**. This allows the GUI (or on-board stimulus) to drive the LED with precise timing and amplitude, producing reproducible light flashes or flicker patterns aimed at the photodiode.

2. **Flexible demonstrations: external light source**  
   You can also use **any external LED/light source** aimed at the photodiode (for example, a handheld LED, a lamp with modulation, or another experimental light source) to deliver a stimulus. This is useful for quick classroom demonstrations and exploratory setups.

### **Photodiode gain and polarity (Photo-gain potentiometer)**

The **Photo-gain** potentiometer controls how strongly light is converted into input drive, and can be set with either polarity:

- **Positive gain**: increased light produces a **depolarising** effect (Vm tends to rise)
- **Negative gain**: increased light produces an **inhibitory/hyperpolarising** effect (Vm tends to fall)

This lets you demonstrate both “excitatory” and “inhibitory” sensory drive using the same light stimulus, and it supports classic teaching questions such as: *How does stimulus intensity affect firing rate? What changes when the sign of sensory input is inverted?*

---

## **Synapses and networks: two synaptic inputs**

Spikeling can receive up to **two synaptic inputs** from other Spikeling units.

### **Physical concept**
A cable from the **axon output** of a second unit into one of the **synaptic input** jacks transmits:

- a spike event (digital) and
- Vm (analogue)

### **What the synapse does**
When a presynaptic spike arrives, the receiving unit generates an **exponentially decaying synaptic current** (a classic simplified postsynaptic current model).

Each synapse has its own gain potentiometer:

- **Synapse 1 gain**: positive (excitatory) or negative (inhibitory)
- **Synapse 2 gain**: positive (excitatory) or negative (inhibitory)

This lets students practise the most important network idea in neuroscience:

> spikes from one neuron can drive or suppress another neuron, depending on sign and strength of synaptic coupling.

(See also: [Synapses and inputs](../experiments/synapses-and-inputs.md), [Network with two units](../experiments/network-two-units.md).)

---
## **Multisensory feedback: LED and buzzer**

Spikeling provides immediate “non-screen” feedback:

- **On-board LED** follows Vm and blinks strongly on spikes
- **On-board buzzer** clicks at each spike

These are not just cosmetic: they help students build intuition about spiking without staring at plots, which is useful in classroom demonstrations and outreach settings.
They can also be deactivated if they become annoying to the user or the class

---
## **Channels, connectors, and grounding (practical concept)**

Spikeling uses stereo **3.5 mm TRS** connectors:

- **Tip (T)**: digital (commonly trigger)
- **Ring (R)**: analogue (commonly Vm or stimulus signal, depending on the jack)
- **Sleeve (S)**: ground

Good grounding and short cables matter. Many “mystery noise” issues reduce to an incomplete ground reference or a swapped cable.

(See: [Controls and I/O](controls-and-io.md) and [Quickstart → Troubleshooting](../quickstart/troubleshooting.md).)

---

## **Emulator vs hardware (why both exist)**

Spikeling includes an emulator mode to support:

- demonstrations without physical devices
- remote teaching and workshops
- rapid development and testing of GUI workflows

Conceptually, the emulator behave like the hardware from the user’s point of view: you apply inputs, observe Vm/spiking, record, and analyse.


---

## **Fluorescence imaging simulation (why Vm can become fluorescence)**

Spikeling can simulate fluorescence imaging by transforming Vm into:

1. a simulated intracellular calcium trace
2. a simulated fluorescence readout

This helps connect spike-driven Vm dynamics to calcium transients and fluorescence signals commonly used in modern systems neuroscience.

(See: [Fluorescence imaging simulation](fluorescence-imaging-sim.md).)

--

## **What to read next**

- Physical layout and signals: [Device overview](device-overview.md)
- Knobs, jacks, and I/O: [Controls and I/O](controls-and-io.md)
- GUI workflow: [GUI overview](gui-overview.md)
- Export + analysis: [Recording and export](recording-and-export.md)

---

## **References (background reading)**

1. Izhikevich EM (2003). *Simple model of spiking neurons.* IEEE Trans Neural Networks. https://www.izhikevich.org/publications/spikes.pdf
2. Moleculardevices (overview). *What is current-clamp?* https://www.moleculardevices.com/applications/patch-clamp-electrophysiology/what-current-clamp-method
3. Hutcheon B, Yarom Y (2000). *Resonance, oscillation and the intrinsic frequency preferences of neurons.* Trends Neurosci. https://pubmed.ncbi.nlm.nih.gov/10782127/
4. Gerstner W, Kistler W, Naud R, Paninski L (online book). *Neuronal Dynamics: Synapses (exponential/biophysical synapse models).* https://neuronaldynamics.epfl.ch/online/Ch3.S1.html
5. Vogelstein JT et al. (2009). *Spike inference from calcium imaging using sequential Monte Carlo methods.* Biophys J. https://pubmed.ncbi.nlm.nih.gov/19619479/
