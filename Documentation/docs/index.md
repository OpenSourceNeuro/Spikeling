# **Spikeling Documentation**

Welcome to the Spikeling documentation. Spikeling is an open hardware + software platform for hands-on neuroscience teaching and outreach, built to make spiking neuron dynamics interactive, measurable, and reproducible.

This site covers:

- **Getting started** (hardware setup, GUI install, firmware flashing)
- **Using Spikeling** for patch-clamp-style experiments and teaching labs
- **Fluorescence imaging simulation** driven by the membrane potential (Vm)
- **Recording/export** (CSV) and starter **data analysis** workflows
- **Hardware / Firmware / GUI** reference and developer extension points

## **Start here**

- New to Spikeling: **[Quickstart → First experiment](quickstart/first-experiment.md)**
- Installing and configuring: **[Quickstart overview](quickstart/index.md)**
- Learning workflows and concepts: **[User guide overview](user-guide/index.md)**
- Ready-to-run activities: **[Experiments](experiments/index.md)**
- Teaching materials (handouts, rubrics, classroom setup): **[Teaching hub](teaching-hub/index.md)**

## **What Spikeling is**

Spikeling is designed to let students and instructors run electrophysiology-inspired experiments without a full patch-clamp rig. A compact hardware device streams signals to a desktop GUI for real-time visualization and interaction. Users can apply stimuli, observe membrane potential dynamics and spiking behavior, and record sessions for later analysis.

Spikeling also includes:

- A **software emulator** for demonstrations, remote teaching, and development without hardware.
- A **fluorescence imaging simulation** that transforms Vm into a simulated calcium trace and fluorescence readout, bridging electrophysiology and imaging concepts.

## **Three-step quickstart**

1. **Connect**: power the device and connect over USB/serial  
   → [Quickstart: Hardware setup](quickstart/hardware-setup.md)

2. **Run**: launch the GUI and run a simple stimulus while watching Vm  
   → [Quickstart: First experiment](quickstart/first-experiment.md)

3. **Record**: export a short session to CSV and plot it in Python  
   → [User guide: Recording and export](user-guide/recording-and-export.md) and
   → [Data analysis: Python quickstart](data-analysis/python-quickstart.md)

## **What you will learn here**

By following this documentation, you will be able to:

- Set up hardware, install the GUI, and flash firmware reliably
- Run standard protocols (steps, pulse trains, noise) and interpret Vm/spiking responses
- Record and export data, then perform basic analysis (plots, spike features, F–I curves)
- Use emulator mode for rapid iteration or teaching without devices
- Understand how the fluorescence simulation relates to the underlying Vm dynamics
- Extend Spikeling by adding stimuli, models, or multi-unit/network experiments (advanced)

## **Who this documentation is for**

- **Students**: step-by-step guides and experiments with expected outcomes
- **Instructors / TAs**: classroom setup, lab handouts, and troubleshooting at scale
- **Developers / contributors**: reference material for hardware, firmware, GUI, and extension points

## **Support and community**

- For bugs and feature requests, use the project **GitHub Issues** (include your OS, GUI version, firmware version, and steps to reproduce).
- For improvements to documentation, experiments, and teaching material, see **[Community → How to contribute](community/contribute.md)**.
- For common questions, start with **[Reference → FAQ](reference/faq.md)** and **[Quickstart → Troubleshooting](quickstart/troubleshooting.md)**.

## **See also**

- [Quickstart overview](quickstart/index.md)
- [User guide overview](user-guide/index.md)
- [Experiments](experiments/index.md)
- [Teaching hub](teaching-hub/index.md)
