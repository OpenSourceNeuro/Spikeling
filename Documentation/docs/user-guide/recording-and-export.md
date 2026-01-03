# **Recording and export**

This page explains how to **record data from Spikeling**, how files are saved, what is inside the export, and how to organise recordings for teaching labs.

For a practical walkthrough, see: **[Quickstart → First experiment](../quickstart/first-experiment.md)**.  
For downstream workflows, see: **[Data analysis → Python quickstart](../data-analysis/python-quickstart.md)**.

---

## **What gets recorded (what “data logging” means)**

When you record in the Spikeling GUI, you are saving a time series of the signals you see on screen. Recordings include:

- **Time (ms)** (in 0.1ms increment)
- **Spikeling Vm (mV)** (membrane potential; main trace)
- **Stimulus (%)** (the waveform being applied)
- **Total Current Input (a.u.)** (total input drive; sum of pathways)
- **Synapse 1 Vm (mV)** (Synapse 1 Vm)
- **Synapse 1 Input (a.u.)** (Synapse 1 input current)
- **Synapse 2 Vm (mV)** (Synapse 2 Vm)
- **Synapse 2 Input (a.u.)**  (Synapse 2 input current)
- **Trigger**  (marks the start of each stimulus loop)

!!! note
    The most important teaching feature of Spikeling exports is that **input and output are saved together**. Students can later ask: “What exactly did I apply?” and “How did Vm respond?”

---

## **Where to record from**

### **A) Neuron Interface / Neuron Emulator**
Use this for electrophysiology-style datasets:

- Vm, stimulus, input current, synapse channels, etc.
- ideal for F–I curves, threshold, adaptation, synaptic integration, noise demos

### **B) Imaging Simulation**
Use this when teaching “Vm → calcium → fluorescence”:

- fluorescence and calcium traces can be logged in a separate dataset
- useful for comparing fast Vm signals to slower imaging-like readouts

---

## **How to record (Neuron Interface / Emulator workflow)**

On the **Neuron Interface** (or **Neuron Emulator**) screen, the recording controls are located along the bottom:

1. Click **Browse directory** and choose where recordings will be saved.
2. Enter a **Data Logging: Filename**.
3. Click **Record** to start logging.
4. Click **Record** again (or the stop control, depending on version) to stop logging.

!!! tip "Teaching tip"
    Start recording **2–5 seconds before** your stimulus begins and stop **2–5 seconds after** it ends. Students need baseline segments for interpretation and plots.

---

## **Filename conventions (highly recommended)**

In teaching settings, recordings become confusing quickly unless filenames encode the condition.

A robust convention is:

`YYYY-MM-DD_group_condition_mode_protocol_run.csv`

Examples:
- `2026-01-03_A01_tonicspiking_step20pA_run01.csv`
- `2026-01-03_A01_phasic_noiseNearThresh_run02.csv`
- `2026-01-03_B02_synEplusI_network_run01.csv`

Minimum recommended fields:
- neuron mode
- stimulus type / key parameter
- run number

---

## **What the CSV contains (Spikeling GUI export)**

Spikeling exports one row per sample, with an explicit time column. In the file you provided, the columns are:

| Column (exact header) | Units | Meaning |
|---|---:|---|
| `Time (ms)` | ms | Sample time (in milliseconds). In this export the step is **0.1 ms** (10 kHz sampling). |
| `Spikeling Vm (mV)` | mV | Membrane potential output (Vm). This is the primary signal used for spike detection and interpretation. |
| `Stimulus (%)` | % | The stimulus command level (percentage scale, consistent with the GUI stimulus strength). |
| `Total Current Input (a.u.)` | a.u. | The net input drive delivered to the neuron model (**sum of pathways**), e.g. current injection / stimulus / light / synapses / noise (depending on which are enabled). |
| `Synapse 1 Vm (mV)` | mV | Presynaptic Vm trace arriving via Synapse 1 (from another Spikeling’s axon output). Typically 0 if not connected/used. |
| `Synapse 1 Input (a.u.)` | a.u. | The synaptic current drive produced by Synapse 1 (spike-evoked, exponentially decaying input, scaled by synapse gain). Typically 0 if not used. |
| `Synapse 2 Vm (mV)` | mV | Presynaptic Vm trace arriving via Synapse 2. Typically 0 if not connected/used. |
| `Synapse 2 Input (a.u.)` | a.u. | The synaptic current drive produced by Synapse 2. Typically 0 if not used. |
| `Trigger` | (0/1) | Digital marker for events (protocol timing / stimulus gating / synchronisation). Often 0 most of the time, with pulses during events. |

!!! note
    The `Total Current Input (a.u.)` column is particularly valuable for teaching because it is the best “single summary” of what the neuron is receiving at each moment, alongside the Vm response.

!!! tip "Practical tip"
    If you are exporting for student analysis, encourage them to plot **Vm**, **Stimulus (%)**, and **Total Current Input (a.u.)** together first. That usually resolves most confusion about “what caused what”.

---

## **Exporting from Data Analysis (spike events and averages)**

The **Data Analysis** page provides additional exports that are often useful in teaching:

- **Spike events** extracted from Vm using a chosen threshold  
  (useful for rasters, firing rate plots, and spike-time statistics)
- **Averaged traces** aligned to stimulus cycles  
  (useful when a stimulus repeats and you want a mean response)

Typical workflow:
1. Load a recorded CSV
2. Set spike threshold
3. Display spike events / averages
4. Export as `.csv` and/or save images

!!! warning
    Spike detection depends on threshold choice. In teaching, it is often useful to show that “reasonable thresholds” produce similar spike times, but extreme thresholds can miss spikes or detect false positives.

---

## **Good recording practice (especially in labs)**

### **1) Record baseline**
Always include baseline so students can compare:
- resting Vm vs driven Vm
- spontaneous vs stimulus-evoked spikes
- with/without noise

### **2) Avoid clipping and confusing axes**
If students will analyse the data later, keep plot settings consistent:
- same axis scale across conditions (when comparing)
- avoid autoscale if it hides changes in amplitude

### **3) Keep one change per run**
For clean interpretation, change **one thing at a time**:
- neuron mode *or*
- stimulus strength *or*
- noise amplitude *or*
- synapse gain

### **4) Note the “hardware state”**
If possible, record (in a notebook or spreadsheet):
- mode name
- stimulus type + parameters
- synapse gain sign/magnitude
- photo-gain sign/magnitude
- noise setting

This turns the recording into a reproducible experiment, not just a trace.

---

## **Troubleshooting recording**

### **“Record button does nothing”**
- confirm you selected a valid directory (write permissions)
- check the filename is not empty
- avoid special characters in filenames

### **“File saved but empty / too short”**
- confirm you actually started recording before stopping
- check whether the GUI logs only when the stream is connected/running

### **“Data looks wrong after export”**
- confirm the right traces were enabled before recording
- if time looks compressed or stretched, check whether the export includes timestamps or uses a fixed sampling step
- for multi-unit recordings, confirm synapse channels were enabled

---

## **What to read next**

- How to interpret recorded signals: [Concepts](concepts.md)
- Spike detection and simple metrics: [Data analysis → Spike detection](../data-analysis/spike-detection.md)
- Using Python with exported CSV: [Data analysis → Python quickstart](../data-analysis/python-quickstart.md)
