# **User guide**

This section explains how to **use Spikeling day-to-day**: what the signals mean, how the hardware inputs/outputs map to the GUI, how to record/export data, and how to run common classroom workflows.

If you are still setting up the device (drivers, firmware, first connection), start with **[Quickstart](../quickstart/index.md)**.

---

## **What you will learn here**

By working through the User guide you will be able to:

- interpret the main traces (**Vm**, **total input current**, stimulus, synaptic channels)
- understand how inputs (current, stimulus, light, synapses, noise) combine to drive the neuron
- use the GUI efficiently (neuron modes, parameter panels, stimulus tools, patch clamp control)
- record sessions and export clean CSV files for analysis
- use emulator mode for teaching, development, and reproducible demonstrations
- apply common workflows (threshold, F–I curves, adaptation, sensory stimulation, synaptic integration)

---

## **Recommended reading order**

If you are new, follow this sequence once. After that, use the pages as reference while running labs.

1. **[Concepts](concepts.md)**  
   The minimum neuroscience concepts needed to use Spikeling effectively (current clamp logic, threshold, adaptation, synapses, noise, light pathway).

2. **[Device overview](device-overview.md)**  
   What is on the board, what each control affects, and how signals flow from inputs to outputs.

3. **[Controls and I/O](controls-and-io.md)**  
   TRS (3.5 mm) connectors, cable conventions, and the three most common wiring patterns:
   stimulus → LED/photodiode, stimulus → current injection, axon → synapse.

4. **[GUI overview](gui-overview.md)**  
   How to navigate the interface, configure neuron modes, use the right-hand parameter panel (including patch clamp), and manage recording.

5. **[Recording and export](recording-and-export.md)**  
   How to record reliably, what is inside the CSV file, and how to avoid common logging mistakes.

Then continue with the two “bridge” topics:

- **[Fluorescence imaging simulation](fluorescence-imaging-sim.md)**  
  Connect Vm dynamics to calcium/fluorescence-style readouts used in imaging.

- **[Emulator mode](emulator-mode.md)**  
  Use Spikeling without hardware, teach remotely, and emulate network interactions.

Finally, use the task-oriented reference:

- **[Common workflows](common-workflows.md)**  
  High-frequency workflows written as reproducible mini-protocols (threshold, F–I, adaptation, noise, light input, synapses, networks, record → analyse).

---

## **When to use emulator vs hardware**

- Use **hardware** when you want the full physical experience: knobs, cables, LED/buzzer feedback, and real classroom variability.
- Use **emulator mode** when you want a controlled baseline for teaching, rapid iteration, and demonstrations without devices.

---

## **Where to go next**

- Ready-to-run protocols with expected outcomes: **[Experiments](../experiments/index.md)**
- Teaching materials (handouts, classroom setup, troubleshooting at scale): **[Teaching hub](../teaching-hub/index.md)**
- Data analysis starter workflows: **[Data analysis](../data-analysis/index.md)**

---

## **Quick help**

- If something looks wrong in the traces, start with **[Quickstart → Troubleshooting](../quickstart/troubleshooting.md)**.
- If you are teaching a large group, consider starting with **[Emulator mode](emulator-mode.md)** for a consistent baseline before introducing hardware variability.
