# **Device overview**

This page gives a high-level tour of the Spikeling hardware: what is on the board, what each control influences, and how signals flow from inputs (current, light, synapses, stimuli) to outputs (Vm, spikes, axon output) and into the GUI.

For exact connector pinout and cable conventions, see: [Controls and I/O](controls-and-io.md).

---

## **At a glance: what the device does**

Spikeling implements a spiking neuron model in hardware and exposes it like a teaching-friendly electrophysiology preparation:

- multiple **input pathways** that contribute to the neuron’s net input drive
- a measurable **membrane potential (Vm)** output
- discrete **spike events** (for triggering, synchronisation, and network coupling)
- real-time streaming to a desktop GUI for visualisation, stimulation, and recording

---

## **Hardware revisions (v2.x vs v3.x)**

Spikeling exists in two main official board families:

### **v2.x (e.g., v2.5)**
- ESP32 WROOM-32
- mini-USB
- uses a CP210x USB-to-UART bridge (driver typically required)
- on-board **Mode** button cycles through **12 preset neuron modes**

### **v3.x (e.g., v3.0.1)**
- ESP32-S3 WROOM-1
- USB-C
- uses ESP32-S3 native USB (typically no extra driver required)
- includes an additional DAC IC compared to v2.x
- neuron mode is selected from the **GUI**
- additional power/control hardware for the **LiPo battery extension** (power switch)
- additional control to **disable the Vm LED** (useful in teaching environments)

!!! note
    The user workflow remains the same across revisions (stimulate → observe Vm/spikes → record/export). Differences mainly affect connection/driver behaviour, how neuron modes are selected, and a small number of extra convenience controls on v3.x.

---

## **Signal flow (mental model)**

A useful way to understand Spikeling is as a “summing junction” feeding a neuron model:

### **Input pathways (sources of drive)**
- **Current injection potentiometer** (centre-detent; left hyperpolarises, right depolarises)
- **On-board stimulus generator** (square-wave; adjustable frequency and strength)
- **GUI stimulus generator** (steps, sine, triangle, chirps, noise, and custom/imported waveforms)
- **Photodiode** (light → input drive; polarity and gain set by Photo-gain potentiometer)
- **Synapse 1 / Synapse 2 inputs** (from other Spikeling units; spike-evoked exponential synaptic currents; gain and sign adjustable)

### **Model and outputs**
- the neuron model generates **Vm**
- when Vm crosses threshold, a **spike event** is produced
- Vm and spikes are:
  - streamed to the GUI for display/recording
  - exposed through the board’s output connectors for networking and external use

---

## **On-board controls (what each one affects)**

The exact naming may vary slightly by revision/label, but the concepts are consistent:

| Control | What it does | Teaching use |
|---|---|---|
| Current injection (centre-detent) | Adds DC drive; left = hyperpolarising, right = depolarising | Threshold, excitability, adaptation |
| Stimulus strength | Sets square-wave amplitude | Input–output gain, recruitment into spiking |
| Stimulus frequency | Sets square-wave repetition rate | Frequency following, spike reliability |
| Noise (Gaussian) | Adds Gaussian noise to the input drive; amplitude set by Noise potentiometer | Variability, near-threshold stochastic spiking, spike-time jitter |
| Photo-gain (±) | Sets gain and polarity for photodiode input | Visual sensory stimulation analogue; excitation vs inhibition |
| Synapse 1 gain (±) | Sets strength/sign of synapse 1 (excitatory/inhibitory) | Synaptic integration; E/I balance |
| Synapse 2 gain (±) | Sets strength/sign of synapse 2 (excitatory/inhibitory) | Network motifs; coincidence and competition |
| Mode button (v2.x) | Cycles through 12 preset neuron modes (Izhikevich parameter sets) | Compare firing patterns under identical stimuli |
| Reset | Restarts the microcontroller/firmware (returns to a known state) | Quick recovery if the device stops responding |
| Buzzer mute | Disables the spike click/buzzer | Classroom comfort; reduce distraction |
| Vm LED disable (v3.x) | Disables the Vm-following LED/spike flash | Classroom comfort; reduce distraction |
| LiPo power switch (v3.x) | Enables/disables the LiPo battery extension power path | Safe power management for battery use |

!!! tip "Practical note"
    If the GUI does not detect the device, or the serial stream appears stuck, using **Reset** is the quickest way to return to a known state before troubleshooting cables, ports, or firmware.


### **Noise (Gaussian): why spikes can become stochastic**

The **Noise** potentiometer adds **Gaussian noise** to the neuron’s input drive. This makes the system feel more realistic and helps demonstrate a core idea in neuroscience: **near threshold, spike timing can be probabilistic**.

In practice, noise contributes to the **total input current (Itot)** alongside direct current injection, light input, synaptic inputs, and any programmed stimulus. With the neuron held just below threshold, increasing noise can:

- trigger occasional spikes without changing the mean input (“stochastic spiking”)
- introduce spike-time jitter (reduced timing precision)
- reveal that small fluctuations can determine whether a spike occurs

!!! tip "Teaching tip"
    Set the current injection potentiometer so Vm sits just below spiking, then slowly increase Noise. Students will see intermittent spiking emerge purely from fluctuations—an intuitive demonstration of variability-driven threshold crossings.

---

## **Neuron “modes” (Izhikevich parameter sets)**

Spikeling uses an Izhikevich-style neuron model. Different “modes” correspond to different parameter sets (a, b, c, d), changing intrinsic excitability and firing pattern.

- **v2.x**: an on-board **Mode** button cycles through 12 preset modes
- **v3.x**: neuron mode is selected from the **GUI** (20 preset modes)

---

## **Visual and auditory feedback (useful in teaching)**

Spikeling includes immediate non-screen feedback:

- **On-board LED** follows Vm and flashes strongly on spikes
- **On-board buzzer** clicks on each spike

These cues help students build intuition about spiking without needing to focus on plots continuously. They can be disabled if they become distracting.

---

## **Connectors (overview)**

Spikeling uses stereo **3.5 mm stereo jack** connectors to carry analogue and digital signals plus ground:

- **Tip (T)**: digital (commonly spike/trigger)
- **Ring (R)**: analogue (commonly Vm or stimulus, depending on jack)
- **Sleeve (S)**: ground

Common use patterns include:
- **Axon output** from one unit → **Synapse input** on another unit
- **Stimulus output** → LED cable → photodiode (controlled light stimulation)
- **Stimulus output** → **DC/current injection input** (use the waveform generator as injected current)

For the full mapping and recommended cables, see: [Controls and I/O](controls-and-io.md).

---

## **What to read next**

- Exact jack mapping and cable conventions: [Controls and I/O](controls-and-io.md)
- GUI signal layout and controls: [GUI overview](gui-overview.md)
- Recording/export workflow: [Recording and export](recording-and-export.md)
