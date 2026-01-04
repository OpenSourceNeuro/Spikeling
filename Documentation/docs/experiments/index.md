# **Experiments**

This section contains ready-to-run experiments for Spikeling. Each page is designed to work both in:

- **Hardware mode** (real device connected over USB/serial)
- **Emulator mode** (no hardware required)

The experiments follow an electrophysiology-inspired workflow:

1. apply a defined input (DC injection, stimulus waveform, light, synapses)
2. observe **Vm** and spikes
3. record/export (CSV)
4. measure one or two simple metrics
5. interpret the result

If you are still installing or connecting the system, start with:
- **[Quickstart → First experiment](../quickstart/first-experiment.md)**

If you need conceptual background first, see:
- **[User guide → Concepts](../user-guide/concepts.md)**

---

## **Start here (recommended path)**

1. **[Patch-clamp-style labs](patch-clamp-style-labs.md)**  
   A set of classroom-friendly labs that teach current clamp logic, excitability, adaptation, and synapses.

2. **[Excitability and threshold](excitability-and-threshold.md)**  
   Find threshold, quantify the silent→spiking transition, and show how noise makes threshold probabilistic.

3. **[Adaptation and firing patterns](adaptation-and-firing-patterns.md)**  
   Measure spike-frequency adaptation and compare firing regimes across neuron modes.

4. **[Synapses and inputs](synapses-and-inputs.md)**  
   Build synapses (axon → synapse), demonstrate excitation vs inhibition, and observe temporal summation.

5. **[Network with two units](network-two-units.md)**  
   Create minimal network motifs and map presynaptic activity to postsynaptic output.

6. **[Stimulus recipes](stimulus-recipes.md)**  
   A cookbook of stimuli (steps, sine/triangle, chirps, noise, light flicker) with “what it teaches” guidance.

---

## **Choosing an experiment**

If you only have **one unit**:
- do **Excitability and threshold**
- then **Adaptation and firing patterns**
- use **Stimulus recipes** to extend

If you have **two units**:
- add **Synapses and inputs**
- then **Network with two units**

If you are teaching a large class:
- use **Emulator mode** for the first run of each experiment to standardise expectations, then transition to hardware.

---

## **Recording and analysis (recommended)**

Most experiments become more valuable if students record and analyse at least one dataset.

- Export workflow: **[User guide → Recording and export](../user-guide/recording-and-export.md)**
- Starter analysis: **[Data analysis → Python quickstart](../data-analysis/python-quickstart.md)**

---

## **Troubleshooting**

If something does not behave as expected:
- start with **[Quickstart → Troubleshooting](../quickstart/troubleshooting.md)**
- confirm cables and ports using **[Controls and I/O](../user-guide/controls-and-io.md)**

---
