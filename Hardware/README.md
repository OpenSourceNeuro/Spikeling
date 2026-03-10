<p align="left">
  <img width="270" height="170" src="../Documentation/Images/SpikyLogo.png" alt="Spikeling logo">
</p>

<div align="center">

# **Hardware design, assembly, and revision notes**

<p>
  <a href="../LICENSES/CERN-OHL-S-2.0.txt">
    <img alt="Hardware license" src="https://img.shields.io/badge/hardware-CERN--OHL--S--2.0-blue">
  </a>
  <a href="https://opensourceneuro.github.io/Spikeling/hardware/">
    <img alt="Hardware docs" src="https://img.shields.io/badge/docs-hardware-green">
  </a>
  <a href="https://opensourceneuro.github.io/Spikeling/reference/pinout-and-connectors/">
    <img alt="Pinout" src="https://img.shields.io/badge/reference-pinout-orange">
  </a>
  <a href="https://opensourceneuro.github.io/Spikeling/reference/specs/">
    <img alt="Specs" src="https://img.shields.io/badge/reference-specs-purple">
  </a>
</p>

</div>

This folder contains the hardware side of **Spikeling**: board revisions, build notes, connector conventions, and practical guidance for bringing a unit from PCB to a working neuroscience teaching device.

Spikeling is an open hardware + software platform for hands-on neuroscience teaching and outreach. It exposes a spiking neuron model through real controls, real I/O, and real-time visualisation, allowing students to run electrophysiology-style experiments without a full wet-lab rig.

**Quick links**
- [Main repository](../)
- [Firmware folder](../Firmware)
- [Software folder](../Software)
- [Documentation folder](../Documentation)
- [Hardware documentation](https://opensourceneuro.github.io/Spikeling/hardware/)
- [Quickstart: hardware setup](https://opensourceneuro.github.io/Spikeling/quickstart/hardware-setup/)
- [Reference: pinout and connectors](https://opensourceneuro.github.io/Spikeling/reference/pinout-and-connectors/)
- [Reference: specs](https://opensourceneuro.github.io/Spikeling/reference/specs/)

<p align="right">
  developed by M.J.Y. Zimmermann<br>
  maintained by P. Rignanese & A. Koumoundourou<br>
  based on an original idea by T. Baden
</p>

---

## **1. What this folder is for**

Use the `Hardware` folder as the entry point for:

- PCB design files and revision history
- manufacturing outputs and sourcing material
- assembly notes and bring-up checks
- connector / wiring conventions
- calibration and troubleshooting notes
- hardware differences between Spikeling generations

This README is meant to help contributors, builders, and teaching staff quickly understand which board they have, how it differs from other revisions, and where to find the next level of detail.

---

## **2. Hardware families**

Spikeling currently exists in two official board families.

### **Spikeling v2.x**
- **Microcontroller:** ESP32 WROOM-32
- **USB connector:** mini-USB
- **USB behaviour:** USB-to-UART bridge (**CP210x**)
- **Driver requirement:** often required, especially on Windows
- **Neuron mode selection:** on-board **Mode** button
- **Preset neuron modes:** 12

### **Spikeling v3.x**
- **Microcontroller:** ESP32-S3 WROOM-1
- **USB connector:** USB-C
- **USB behaviour:** native USB (**USB CDC serial**)
- **Driver requirement:** typically no separate USB-UART driver required
- **Neuron mode selection:** from the **GUI**
- **Preset neuron modes:** 20
- **Additional hardware compared to v2.x:** external DAC IC
- **Additional convenience features:** LiPo power-control hardware and a dedicated control to disable the Vm LED

> In practice, both families support the same teaching workflow: stimulate the model neuron, observe Vm and spikes, connect units together, and record/export data. The main differences affect USB connection, firmware target, mode selection, and a few hardware conveniences.

---

## **3. Version 2 vs version 3 — practical differences**

### **Connection and setup**
- **v2.x** uses a CP210x USB-to-UART bridge, so serial detection depends on that driver being installed.
- **v3.x** uses the ESP32-S3 native USB interface and usually enumerates directly as a USB serial device.

### **User interaction**
- **v2.x** changes neuron behaviour using an on-board **Mode** button.
- **v3.x** moves neuron mode selection into the GUI, which makes classroom switching and software-driven workflows more convenient.

### **Analogue output hardware**
- **v3.x** adds an external DAC compared with **v2.x**, improving the hardware architecture for the newer board generation.

### **Power and convenience controls**
- **v3.x** adds hardware support for the LiPo extension and includes a control to disable the Vm LED.
- **v2.x** is the simpler earlier platform and is closer to the minimal USB-to-ESP32 teaching-board architecture.

### **How to identify them quickly**
- **mini-USB = v2.x**
- **USB-C = v3.x**

---

## **4. What Spikeling hardware does**

At the hardware level, Spikeling behaves like a compact teaching-oriented electrophysiology preparation:

- multiple input pathways contribute to the neuron’s total drive
- the board exposes a measurable membrane potential (**Vm**)
- threshold crossings generate discrete spike events
- the board streams signals to the desktop GUI for visualisation, stimulation, and recording

### **Main input pathways**
- current injection control
- on-board square-wave stimulus generator
- GUI-driven stimulus generator
- photodiode input for light stimulation
- Synapse 1 / Synapse 2 inputs from other Spikeling units

### **Main outputs**
- analogue **Vm**
- digital spike events
- stimulus output for external use
- real-time USB serial stream to the GUI

---

## **5. Controls and I/O philosophy**

Spikeling uses **3.5 mm stereo TRS jacks** to carry both analogue and digital signals with a shared ground.

### **TRS convention**
- **Tip (T)** = digital / TTL
- **Ring (R)** = analogue signal
- **Sleeve (S)** = ground

This makes the hardware compact and classroom-friendly: one cable can carry both a continuously varying signal and an event marker.

### **Typical signal roles**
- **Synaptic / axon output:** analogue = presynaptic Vm, digital = spike events
- **Stimulus output:** analogue = stimulus waveform, digital = PWM / timing signal
- **Synapse input 1 / 2:** receives a TRS feed from another unit
- **Current input:** receives an injected analogue waveform
- **Photodiode workflow:** an LED driven through the stimulus path can act as a controlled light stimulus

### **Common wiring patterns**
- **Axon output (unit A) → Synapse input (unit B)** for two-unit network experiments
- **Stimulus output → LED cable → photodiode** for controlled light stimulation
- **Stimulus output → current input** for waveform-based injected current experiments

> Ground continuity matters. Many noisy or unstable measurements are caused by missing or inconsistent ground reference on the TRS sleeve.

---

## **6. Core teaching-facing controls**

The exact silkscreen may vary slightly between revisions, but the core controls remain conceptually stable.

- **Current injection**: direct depolarising / hyperpolarising drive
- **Stimulus strength**: amplitude of the on-board square-wave drive
- **Stimulus frequency**: repetition rate of the on-board stimulus
- **Noise**: Gaussian noise added to the input drive
- **Photo gain (±)**: gain and polarity of the photodiode input
- **Synapse 1 gain (±)**: excitatory or inhibitory strength of synapse 1
- **Synapse 2 gain (±)**: excitatory or inhibitory strength of synapse 2
- **Reset**: return the board to a known state
- **Buzzer mute**: disable spike audio feedback

### **Revision-specific controls**
- **v2.x:** Mode button selects one of 12 preset Izhikevich parameter sets
- **v3.x:** neuron mode is selected in the GUI, and the board adds:
  - **Vm LED disable**
  - **LiPo power switch / power-control hardware**

---

## **7. Minimum hardware needed to use a board**

### **For either generation**
- one Spikeling unit
- one data-capable USB cable
- at least one **3.5 mm TRS stereo cable**
- a computer running the GUI
- optionally, an LED stimulus cable for photodiode experiments

### **Board-specific USB cables**
- **v2.x:** mini-USB data cable
- **v3.x:** USB-C data cable

### **Recommended extras**
- powered USB hub
- spare TRS patch cables
- TRS-to-breakout adapter(s)
- multimeter
- optional oscilloscope or logic analyser for debugging

---

## **8. Quick bring-up checklist**

Before troubleshooting firmware or GUI issues, confirm the physical layer first.

- I know whether the board is **v2.x** or **v3.x**
- I am using a **data-capable** USB cable
- The board appears as a serial device on the computer
- For **v2.x**, the **CP210x** driver is installed
- I have at least one known-good **TRS** cable
- I understand the **Tip / Ring / Sleeve** mapping
- No other application is already holding the serial port
- The board can be reset cleanly and reconnects

---

## **9. Recommended workflow**

### **If you are using an already-built board**
1. Identify the board family (**v2.x** or **v3.x**)
2. Connect USB and confirm the serial port appears
3. Install / launch the GUI
4. Flash the correct firmware if needed
5. Run a simple current injection or stimulus protocol
6. Add TRS cabling for synapse or photodiode experiments

### **If you are assembling hardware**
1. Start from the correct board revision
2. Follow a disciplined soldering order
3. Inspect for shorts, polarity mistakes, and connector orientation
4. Bring the board up with USB only before adding more hardware
5. Verify serial enumeration
6. Verify basic stimulus / Vm / spike behaviour before multi-unit experiments

---

## **10. Documentation map**

### **Hardware**
- [Hardware overview](https://opensourceneuro.github.io/Spikeling/hardware/)
- [Bill of materials](https://opensourceneuro.github.io/Spikeling/hardware/bom/)
- [Assembly](https://opensourceneuro.github.io/Spikeling/hardware/assembly/)
- [Calibration](https://opensourceneuro.github.io/Spikeling/hardware/calibration/)
- [Mechanical mounting](https://opensourceneuro.github.io/Spikeling/hardware/mechanical-mounting/)
- [Revisions](https://opensourceneuro.github.io/Spikeling/hardware/revisions/)
- [Known hardware issues](https://opensourceneuro.github.io/Spikeling/hardware/known-hardware-issues/)
- [Safety and handling](https://opensourceneuro.github.io/Spikeling/hardware/safety-and-handling/)

### **Quickstart / use**
- [What you need](https://opensourceneuro.github.io/Spikeling/quickstart/what-you-need/)
- [Hardware setup](https://opensourceneuro.github.io/Spikeling/quickstart/hardware-setup/)
- [Flash firmware](https://opensourceneuro.github.io/Spikeling/quickstart/flash-firmware/)
- [First experiment](https://opensourceneuro.github.io/Spikeling/quickstart/first-experiment/)

### **Reference**
- [Device overview](https://opensourceneuro.github.io/Spikeling/user-guide/device-overview/)
- [Controls and I/O](https://opensourceneuro.github.io/Spikeling/user-guide/controls-and-io/)
- [Specs](https://opensourceneuro.github.io/Spikeling/reference/specs/)
- [Pinout and connectors](https://opensourceneuro.github.io/Spikeling/reference/pinout-and-connectors/)

### **Related repository folders**
- [Firmware](../Firmware)
- [Software](../Software)
- [Documentation](../Documentation)

---

## **11. Contributing hardware changes**

Contributions are welcome for:

- new board revisions
- BOM cleanup and sourcing notes
- manufacturing outputs
- assembly photos and bring-up procedures
- known-issue tracking and validated fixes
- connector diagrams and calibration procedures

When submitting hardware changes, it helps to include:
- board revision name
- schematic / PCB source files
- fabrication outputs if relevant
- BOM updates
- assembly notes
- photos or annotated screenshots
- compatibility notes with firmware and GUI versions

---

## **12. License**

Spikeling hardware is released under the **CERN Open Hardware Licence – Strongly Reciprocal v2.0 (CERN-OHL-S-2.0)**.

See:
- [`../LICENSES`](../LICENSES)
- [`../LICENSE.txt`](../LICENSE.txt)

Software and firmware are released separately under **GPL-3.0-or-later**.

If you reuse or modify the hardware, keep the appropriate license notices and attribution.

---
