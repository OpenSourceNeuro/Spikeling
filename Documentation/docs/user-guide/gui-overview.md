# **GUI overview**

This page explains how to use the Spikeling desktop GUI as a teaching and experiment interface. It is written for quick scanning: each section maps a visible GUI element (button, slider, panel) to a neuroscience task (stimulate, record, analyse).

If you are new, start with **Neuron Interface** and learn the workflow: **connect → stimulate → observe → record → analyse**.

See also: [Device overview](device-overview.md), [Controls and I/O](controls-and-io.md), and [Concepts](concepts.md).

---

## **Mental model: what the GUI is doing**

Think of the GUI as three things at once:

1. **An oscilloscope** (plots Vm and other traces in real time)
2. **A stimulus generator** (built-in waveforms + custom/imported protocols)
3. **A lab notebook** (recording to CSV and quick analysis)

Spikeling itself is the “preparation”: it integrates inputs (current injection, stimulus, light, synapses, noise) and produces outputs (Vm, spikes, axon output). The GUI makes those signals visible and controllable.

---

## **Left-hand navigation: workspaces**

The GUI is organised into workspaces accessed from the left menu:

- **Spikeling**
  - **Neuron Interface** (hardware-connected oscilloscope + controls)
  - **Neuron Emulator** (same interface, but simulated)
  - **Data Analysis** (load CSV, detect spikes, averages, export)
  - **Tutorial** (guided teaching pages)
- **Imaging**
  - **Imaging Simulation** (Vm → calcium → fluorescence; optional ΔF/F)
  - **Data Analysis**
  - **Tutorial** (guided teaching pages)
- **Neuron Generator** (build/edit neuron modes and parameters)
- **Stimulus Generator** (build/save waveforms for later use)
- **Exercises** (teaching labs and instructions)
- **Settings** (preferences and configuration)
- **About**
- **Help**
- **GitHub**

### **Hide/Show menus**
Buttons such as **Hide Menus** / **Hide Sub-Menus** are purely for screen space: they do not change any model settings. Use them when teaching on a projector or a small screen.

---

## **Spikeling → Neuron Interface (hardware mode)**

This is the primary teaching screen. You will typically use it for:
- basic excitability demonstrations (current clamp style)
- stimulus-response experiments (frequency/strength sweeps, chirps, noise)
- synaptic integration (two-unit or three-unit networks)
- structured recording for later analysis

### **1) Connect to a device**

1. Plug the Spikeling board in via USB.
2. In the top bar, choose the correct **COM/serial port**.
3. Click the **Connect** button.

**Tip:** if several ports are listed, the correct one often produces visible LED activity on the device when selected.

If connection fails, see the troubleshooting box below.

!!! tip "Teaching tip"
    Start with the device in a stable baseline (no spiking), then move deliberately: show how small changes near threshold can switch the output from silent to spiking.

### **2) What you see on the oscilloscope (central plot)**

The oscilloscope can display multiple traces simultaneously. The most important are:

- **Vm** (membrane potential): the “main readout”, red
- **Input current / total drive**: the net current the model receives, green
- **Stimulus**: the waveform being applied (board square-wave or GUI waveform), blue

When synaptic inputs are used, additional traces can be enabled for:
- **Synapse 1** (presynaptic Vm and/or synaptic current) orange/cyan
- **Synapse 2** (presynaptic Vm and/or synaptic current) yellow/magenta

Use the trace tick-boxes to declutter the view when teaching.

!!! note
    The **input current/total drive trace** is especially useful for teaching because it reflects the *sum* of pathways: direct current injection, stimulus, photodiode/light drive, synaptic currents, and added noise.

### **3) Speed control (display rate)**
A **Speed** slider and multiplier controls how quickly the oscilloscope advances in time (and/or how densely points are displayed). Use it to:
- slow down fast spiking for explanation
- speed up for long recordings or adaptation demonstrations

### **4) Neuron mode selection**
Neuron “modes” are named patterns (parameter sets) for the Izhikevich-style model (e.g., tonic spiking, phasic spiking, bursting, adaptation, etc.).

Typical workflow:
1. Select a mode from the **Neuron Mode** drop-down list.
2. Click **Apply** to push the change.

You can also **Browse** to load a custom neuron definition created in **Neuron Generator**.

!!! tip "Teaching tip"
    Keep the stimulus fixed and change only the mode. This isolates the concept that *intrinsic membrane dynamics* (not just input strength) shapes firing patterns.

### **5) LED and buzzer controls (classroom ergonomics)**
Top-right controls toggle:
- the **Vm LED** behaviour (visual feedback)
- the **buzzer** click on spikes (auditory feedback)

In a quiet teaching room, it is often worth muting the buzzer after the first demonstration.

### **6) The right-hand parameter panel (where most teaching happens)**

The right panel contains grouped controls. When a toggle button is activated, it automatically deactivates the knob on the board responsible for the selected variable. The exact grouping varies slightly across versions, but conceptually it contains:

#### **A) Stimulus controls**
- Adjust **Stimulus Frequency** and **Stimulus Strength** (board-like square wave control)
- Enable **Custom Stimulus** and **Load** a saved waveform (from Stimulus Generator)

Use the small stimulus preview plot to confirm what will be delivered before enabling it.

#### **B) Photo-receptor (photodiode) dynamics**
- **Photo-gain** (including sign: positive or negative gain)
- **Photo decay** and **Photo recovery** (shape of the light-evoked current)

Teaching use:
- demonstrate “transient vs sustained” sensory drive
- show how the same light input can excite or inhibit depending on gain polarity

#### **C) Patch Clamp**
When enabled, Patch clamp adds a DC offset to the neuron’s input drive. This is the most direct software analogue of patch pipette current injection:

- negative injected current tends to hyperpolarise Vm (less spiking)
- positive injected current tends to depolarise Vm (more spiking)
- zero is the neutral “no injection” point

This injected current is best thought of as baseline drive that can be combined with other inputs (stimulus waveforms, light input, synapses, noise).

!!! tip "Teaching use"
  Patch clamp is useful when you want a repeatable DC level (e.g., set the neuron just below threshold), then demonstrate how adding noise, synaptic input, or a stimulus waveform changes spiking.

#### **D) Noise**
Noise adds controlled variability to the total input drive.

Teaching use:
- stochastic spiking near threshold
- spike-time jitter
- realism: demonstrating that “no recording is noise-free”

A simple, effective classroom demo:
1. Set current injection just below spiking.
2. Increase noise until spikes occur intermittently.
3. Ask students why spike timing becomes unreliable near threshold.

#### **E) Synapse 1 / Synapse 2**
Each synapse has:
- a **gain** (positive = excitatory; negative = inhibitory)
- often a **decay** control (synaptic time constant shaping)

Teaching use:
- excitation vs inhibition
- temporal summation
- coincidence detection and competition (two inputs with different signs)

### **7) Recording (CSV logging)**
At the bottom of the screen:
1. Choose a **directory** (browse)
2. Enter a **filename**
3. Press **Record** to start logging

Recordings are saved as **CSV** for analysis in the GUI and in external tools (Python, MATLAB, R, etc.).

!!! warning
    If you reuse a filename, you may overwrite earlier recordings depending on your configuration. Consider a consistent naming convention (e.g., `mode_phasic_step_20s_01.csv`).

---

## **Spikeling → Neuron Emulator (no hardware required)**

The emulator reproduces the same user experience as the hardware screen:
- same plots
- same stimulus logic
- same neuron modes
- same recording pathway

Use it for:
- remote teaching and workshops
- classroom preparation without a physical unit
- debugging a protocol before running it on hardware

Typical workflow:
1. Open **Neuron Emulator**
2. Start the emulator
3. Use the same stimulus and parameter controls as in Neuron Interface
4. Record data exactly as you would with hardware

---

## **Spikeling → Data Analysis (quick classroom analysis)**

The analysis panel is designed for immediate feedback after a lab recording:

Typical workflow:
1. **Load Data**
2. Set a **Spike Threshold**
3. Display:
   - spike events (raster-like view)
   - spike rate over time
   - stimulus-aligned averages (when applicable)
4. **Export** results (CSV and/or images)

Teaching focus:
- show how threshold choice changes spike detection
- link stimulus structure to firing rate changes
- compare conditions (e.g., gain = 0 vs gain > 0 vs gain < 0)

---
## **Imaging → Imaging Simulation**

This workspace connects electrophysiology-style signals to modern imaging readouts.

Conceptually:
**Vm/spikes → simulated calcium transient → simulated fluorescence**

Common teaching use:
- explain why fluorescence is a filtered, delayed proxy for spiking
- compare “ground truth” Vm to fluorescence
- demonstrate ΔF/F and baseline normalisation

Typical controls include:
- selecting the **data source** (hardware vs emulator)
- choosing which traces to show (fluorescence, calcium, Vm)
- toggling **ΔF/F**
- recording fluorescence traces similarly to electrophysiology traces

---

## **Neuron Generator (build and save neuron modes)**

This workspace is for creating or editing neuron modes by adjusting model parameters (including the classic a, b, c, d parameter set). It is most useful for advanced teaching:

- exploring how parameter changes reshape firing patterns
- creating “custom neurons” for a lab class
- saving neuron definitions for reuse in Neuron Interface/Emulator

Recommended teaching approach:
- start from a known mode (e.g., tonic spiking)
- change *one parameter at a time*
- keep the stimulus fixed
- record before/after traces for comparison

---

## **Stimulus Generator (design waveforms for experiments)**

This workspace creates stimulation protocols beyond the board’s default square wave.

Common modes include:
- steps
- sine and triangle waves
- chirps / ZAP sweeps (linear, exponential, amplitude ramps)
- noise

Typical workflow:
1. Choose a stimulus type
2. Set parameters (amplitude, frequency, duration, ramps, inter-stimulus timing)
3. **Display Stimulus** to preview
4. **Save Stimulus**
5. Return to Neuron Interface/Emulator and **Load** it under Custom Stimulus

---

## **Troubleshooting: connection and “nothing is moving”**

If you do not see traces updating or cannot connect:

- Confirm the correct USB cable (some USB cables are power-only)
- Try a different USB port
- Select a different COM/serial port and retry
- Press **Reset** on the board (or unplug/replug)
- Close and reopen the GUI if the serial connection appears stuck

If the device connects but traces look flat:
- confirm at least one input pathway is active (current injection, stimulus, light, synapse)
- ensure the oscilloscope trace tick-boxes include **Vm**
- check that the speed/display rate is not effectively “paused” by settings

---

## **What to read next**

- Hardware signals and connectors: [Controls and I/O](controls-and-io.md)
- What the traces mean: [Concepts](concepts.md)
- Running your first protocol: [Quickstart](../quickstart/index.md)
- Recording and export conventions: [Recording and export](recording-and-export.md)
