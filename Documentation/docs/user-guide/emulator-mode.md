# **Emulator mode**

Spikeling includes a built-in **software emulator** that behaves like the hardware from the user’s point of view: you apply inputs, observe **Vm** and **spikes**, and record to CSV.

Emulator mode is designed for:

- **Teaching without devices** (classroom demos, remote workshops, preparation)
- **Developing stimuli/workflows** without needing a board plugged in
- **Troubleshooting** (to separate “GUI issue” from “hardware/serial issue”)
- **Exploring network logic** (synapses) in a controlled, reproducible setup

---

## **What emulator mode reproduces**

Emulator mode mirrors the same conceptual blocks as the physical device:

- **Neuron model behaviour** (Vm dynamics, threshold, spiking, adaptation)
- **Current-clamp style control** (inject current and read Vm)
- **Stimulus generation** (with options to route the stimulus as current or as light)
- **Noise-driven variability**
- **Synapses** (excitatory/inhibitory sign and strength, exponential decay)
- **Recording/export** to CSV in the same spirit as hardware recordings

It is not intended as a biophysically detailed simulator; the goal is to support the **teaching workflow** and the **interpretation skills** used in electrophysiology-style experiments.

---

## **How to start the emulator**

1. In the left navigation, open **Neuron Emulator**.
2. Click **Start Spikeling Emulator** (this is a toggle button).
3. You should see Vm update in the main plot area once the emulator is running.

!!! tip "If nothing moves"
    - Confirm **Start Spikeling Emulator** is enabled (toggled on).  
    - If plots still appear static, change the **Speed** slider slightly, then return it to a mid setting.

---

## **Interface layout (what to look at first)**

Emulator mode uses the same “read the traces, then adjust inputs” teaching loop:

- **Main trace area**: where you watch **Vm** (and other signals depending on your GUI view).
- **Right-hand parameter panel**: where you configure inputs and neuron settings.
- **Four parameter pages** (buttons at the top of the parameter panel):
  - **Neuron Parameters**
  - **Stimulus Parameters**
  - **Synapse 1 Parameters**
  - **Synapse 2 Parameters**
- A **Hide Parameters** button collapses the parameter panel when you want maximum plot space.

---

## **Neuron mode selection (model “modes”)**

Near the top of the emulator controls you can set:

- **Neuron Mode:** (dropdown list)
- **Browse:** (load a mode definition from file)
- **Apply:** (apply the selected/loaded mode)

Use this to demonstrate how different parameter sets (Izhikevich-style **modes**) change excitability and firing pattern under identical input.

!!! note
    For teaching, keep the stimulus fixed and only change mode. Students will see that intrinsic dynamics matter, not just the input waveform.

---

## **Neuron Parameters (inputs and coupling)**

This page controls the core input pathways that shape Vm.

### **Patch clamp (direct current injection)**

The emulator includes a **Patch clamp** control representing direct injected current (current clamp logic).

Typical use:

- Move the patch clamp control to shift Vm from silent → depolarised → spiking → adapting.

### **Noise**

Noise adds variability to the input drive and is the fastest way to demonstrate:

- near-threshold **stochastic spiking**
- spike-time **jitter**
- trial-to-trial variability even under “same” conditions

### **Synapses (network inputs)**

The emulator supports **two synaptic inputs** (Synapse 1 and Synapse 2), mirroring the hardware concept:

- presynaptic spikes generate an **exponentially decaying synaptic current**
- **Synaptic Gain** determines excitatory (positive) vs inhibitory (negative) effect
- **Synaptic Decay** controls how long the synaptic current persists

This enables classic demonstrations:

- summation of synaptic events
- competition between excitation and inhibition
- “one neuron driving another” network logic

---

## **Stimulus Parameters (waveform routing and settings)**

This page controls the emulator’s stimulus generator and how it is applied.


### **Enable/disable and Route the stimulus: Current vs Light**

You can choose whether the stimulus drives:

- **Current** (inject waveform as current), or
- **Light** (treat stimulus as a light-modulated input pathway)

Use the toggle buttons to enable the stimulus pathway.

This is useful pedagogically because it separates:

- “what waveform did I generate?”
from
- “which input pathway did I stimulate?”

### **Frequency and strength**

The stimulus controls include:

- **Frequency** (how fast the waveform repeats / oscillates, depending on mode)
- **Strength** (amplitude)

Use these to build intuition about input–output gain and spike recruitment.

### **Custom stimuli**

If you enable **Custom stimulus**, the emulator can use user-defined waveforms (useful for structured labs and for designing new protocols).

### **Photo-Receptor (photodiode / light pathway parameters)**

When the stimulus is routed to **Light**, the emulator exposes a **Photo-Receptor** block that models how light is converted into an effective input drive for the neuron.

This block has three key controls:

- **Photo-Gain (%)**  
Sets the strength (and sign) of the light-to-drive conversion.
  - **Positive gain**: more light produces a **depolarising** drive (Vm tends to rise)
  - **Negative gain**: more light produces a **hyperpolarising/inhibitory** drive (Vm tends to fall)

- **Photo Decay: λ (ms⁻¹)**  
  Controls how fast the light-driven response **decays** after a light change.
  - Higher λ (towards *Fast*) → quicker decay (shorter, sharper transients)
  - Lower λ (towards *Slow*) → longer decay (more sustained effect)

- **Photo Recovery: λ (ms⁻¹)**  
  Controls how fast the photo-receptor response **recovers** back to baseline and is ready to respond again.
  - Higher λ (towards *Fast*) → faster recovery (tracks rapid flicker better)
  - Lower λ (towards *Slow*) → slower recovery (adaptation-like behaviour)

!!! tip "Teaching tip"
    Use a flickering light stimulus (or a square-wave stimulus routed to **Light**) and vary **Decay** and **Recovery**:
    - fast decay + fast recovery → the response follows rapid flicker more cleanly
    - slow decay → responses overlap and integrate over time
    - slow recovery → the system behaves as if it “adapts” and becomes less responsive to repeated flashes

---

## **Emulating networks (multi-unit coupling in the GUI)**

Emulator mode can simulate **two-unit network interactions** without any physical cables by running an **auxiliary neuron** alongside the main Spikeling neuron and routing its output as a synaptic drive.

This is the cleanest way to teach core network concepts (E/I coupling, synaptic filtering, recruitment into spiking) in a fully reproducible setup.

---

### **How the GUI represents a two-neuron network**

In emulator mode, you typically have:

- a **Main neuron** (the one displayed as “Spikeling” in the plot)
- Two **Auxiliary neurons**

Auxiliary neurons can be configured to send its spikes/Vm into the main neuron through a *virtual* synapse.

In the right-hand panel (Auxiliary Neuron #), you will see:

- **Neuron Mode** (dropdown + Browse + Apply)
- **Synapse main neuron** (toggle)
- **Patch Clamp** (Injected Current)
- **Noise** (Noise Level)
- **Stimulus** routing and **Photo-Receptor** parameters (if using light stimulation logic)

---

### **Step-by-step: create a simple 2-neuron network**

1. **Start the emulator** and ensure the main neuron Vm is updating.

2. Open **Auxiliary Neuron 1** parameter panel.

3. Set the auxiliary neuron’s **Neuron Mode** and click **Apply**  
   Choose a mode that spikes reliably (tonic spiking is the easiest to start with).

4. Drive the auxiliary neuron to spike using **Patch Clamp**  
   Increase injected current until you see stable spiking in the auxiliary neuron trace (if displayed).

5. Enable coupling: toggle **Synapse main neuron**  
   This routes the auxiliary neuron’s output into the main neuron as a synaptic input.

6. In **Neuron Parameters**, configure the synaptic effect using **Synapse 1** or **Synapse 2** panel  
   Use the synapse gain/sign (sets to 0 by default so synaptic input has no effect on the main spikeling by default) controls to set:
   - **excitatory** coupling (positive gain: auxiliary spikes depolarise the main neuron)
   - **inhibitory** coupling (negative gain: auxiliary spikes hyperpolarise/suppress the main neuron)

7. Observe the main neuron:
   - Does synaptic input recruit spikes?
   - Does inhibition silence spiking?
   - Does the main neuron show temporal summation (multiple presynaptic spikes accumulate)?

---

### **What to teach with this (high-value network demonstrations)**

#### **1) Excitatory drive: “one neuron makes another fire”**
- Make Auxiliary Neuron 1 spike regularly (Patch Clamp).
- Set Synapse gain **positive**.
- Watch the main neuron depolarise and (often) begin spiking even if its own injected current is low.

Teaching questions:
- “What happens if I halve the synapse gain?”
- “How many presynaptic spikes are needed to trigger a postsynaptic spike?”

#### **2) Inhibitory control: vetoing spiking**
- Keep the main neuron just above threshold (so it would normally spike).
- Enable auxiliary neuron coupling with **negative** synapse gain.
- Increase auxiliary firing rate and observe suppression / spike skipping.

Teaching questions:
- “Can inhibition completely silence the neuron?”
- “How does inhibition change spike timing reliability?”

#### **3) Temporal filtering (synaptic decay)**
Use synapse decay parameters (where available in Synapse panels) to show:
- fast decay: brief, well-separated postsynaptic effects
- slow decay: integration over time (more summation)

Teaching questions:
- “Why does slow synapse decay promote integration?”
- “Why does fast decay make timing more precise?”

#### **4) Noise + synapses: variability in networks**
- Hold the main neuron just below threshold.
- Turn on auxiliary synaptic input and add a small amount of noise.
- Show probabilistic recruitment: sometimes spikes occur, sometimes they do not.

Teaching question:
- “Why can two identical synaptic events produce different postsynaptic outcomes near threshold?”

---

### **Optional: stimulus routing through the auxiliary neuron**

Auxiliary neurons have their own **Stimulus** routing controls:

- **Apply Direct Current Stimulus**
- **Apply Light Stimulus**
- plus the **Photo-Receptor** parameters (Photo-Gain, Decay λ, Recovery λ)

This enables an additional “sensory network” demonstration:

- Use the stimulus generator to drive the **auxiliary neuron** (current or light pathway).
- Route the auxiliary neuron to the main neuron with **Synapse main neuron**.
- The main neuron now responds indirectly to the stimulus via a presynaptic unit.

Teaching translation:
> “A sensory-like input drives one neuron, which then drives another neuron through a synapse.”

---

### **Common pitfalls**

- **No effect on main neuron after enabling coupling**  
  Check:
  - auxiliary neuron is actually spiking (increase Patch Clamp or reduce inhibitory inputs)
  - synapse gain is not near zero
  - you are editing the correct synapse (Synapse 1 vs Synapse 2)

- **Main neuron saturates / spikes continuously**  
  Reduce:
  - auxiliary neuron drive (Patch Clamp)
  - synapse gain (excitatory)
  - noise level

---

### **Links**

- Practical synapse experiments: [Synapses and inputs](../experiments/synapses-and-inputs.md)  
- Two-unit motifs: [Network with two units](../experiments/network-two-units.md)


---

## **Recording in emulator mode**

Emulator mode includes a **Data Recording** box:

1. Set **Data Logging: Filename**
2. Click **Browse directory** to select a save folder
3. Click **Record** to start logging

The output is intended to be analysed exactly like a hardware recording (plot Vm, compute firing rate, build F–I curves, etc.).

See also: **[Recording and export](recording-and-export.md)** and **[Data analysis → Python quickstart](../data-analysis/python-quickstart.md)**.

---

## **Suggested classroom workflow (5–10 minutes)**

1. Start emulator, pick a default neuron mode.
2. Use **Patch clamp** to find threshold (silent → occasional spikes → sustained spiking).
3. Turn on **Noise** and demonstrate stochastic spiking near threshold.
4. Enable **Synapse 1**, make it excitatory, and show how synaptic input can recruit spikes without changing mean injected current.
5. Record 10–20 seconds, export, and plot Vm/spike rate from the CSV.

---

## **What to read next**

- Concepts refresher: **[Concepts](concepts.md)**
- How synapses are used in labs: **[Synapses and inputs](../experiments/synapses-and-inputs.md)**, **[Network with two units](../experiments/network-two-units.md)**
- Imaging link (if you use it): **[Fluorescence imaging simulation](fluorescence-imaging-sim.md)**
