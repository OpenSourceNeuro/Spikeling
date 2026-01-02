# **First experiment**

This page walks you through a minimal “first success” experiment: connect to Spikeling, stream data, apply a simple stimulus, and record a short CSV. The goal is to confirm your setup works end-to-end before attempting more advanced protocols.

## **Before you start**

Complete these first:

- **Hardware is connected and the port is visible**: see [Hardware setup](hardware-setup.md)
- **GUI is installed and launches**: see [Install the GUI](install-gui.md)
- (Optional) Firmware is up to date: see [Flash firmware](flash-firmware.md)

!!! warning "Close other serial tools"
    If Arduino Serial Monitor or another terminal is open, the GUI may not be able to connect to the port.

---

## **Step 1 — Connect to the device**

1. Plug the board in and confirm it appears as a serial/COM port.
2. Open the Spikeling GUI.
3. Select the correct **Port**:
   - v2.x (CP210x): typically appears as a CP210x/SLAB serial port (COMx on Windows)
   - v3.x (USB CDC): typically appears as a USB serial device (COMx on Windows)
4. Click **Connect** (or the equivalent connect action in your GUI).

### **Success criteria**

- The GUI shows **Connected** (or an equivalent status)
- a little light gimmick is displayed on the board
- Live plots begin to update (even if flat/no stimulus yet)

If you cannot connect, go to [Troubleshooting](troubleshooting.md).

---

## **Step 2 — Verify live streaming (baseline)**

Before applying any stimulus, check that the streaming pipeline is alive.

1. Confirm the main traces update at a steady rate.
2. Confirm you can see at least one channel that changes over time (even small noise is fine).

### **If everything is flat**

A flat baseline can still be normal depending on the channel shown and defaults. The key is:
- the plot is updating in real time, and
- the connection is stable (no repeated disconnects).

---

## **Step 3 — Use the current injection potentiometer (first hands-on control)**

Before running any stimulus protocol, use the **current input potentiometer** on the board to directly inject DC current, like a patch-clamp pipette in current-clamp mode.

On Spikeling, this potentiometer is located in the **bottom-left corner** of the board, on the drawing of the **electrophysiology pipette**. It corresponds to the **direct current input from the pipette**.

### **Center detent behavior (important)**

This is a **center-detent potentiometer**:

- **Center detent** = **0 current** (no DC injection)
- Turn **left** from center = **hyperpolarizing current** (Vm decreases)
- Turn **right** from center = **depolarizing current** (Vm increases)

### **What you are doing conceptually**

By turning this knob you are changing a **constant input current**. This should shift the membrane potential (Vm) and can drive different regimes:

- hyperpolarizing current → **hyperpolarization**
- depolarizing current → **depolarization**
- sufficiently depolarizing current → **spiking**
- sustained spiking → **spike-frequency adaptation** (spikes slow down over time)

### **Procedure**

1. Ensure the GUI is connected and you are viewing the **Vm** trace.
2. Set the potentiometer to the **center detent** (0 current).
   - You should see a stable baseline Vm (with small noise).
3. Turn the potentiometer **slightly left** of center:
   - observe **hyperpolarization** (Vm baseline shifts downward)
4. Return to the **center detent**:
   - Vm should return toward baseline
5. Turn the potentiometer **slightly right** of center:
   - observe **depolarization** (Vm baseline shifts upward)
6. Continue turning **right** until you reach **spiking**:
   - spikes should appear on the Vm trace
7. Hold the knob at a fixed rightward position for several seconds:
   - observe **spike adaptation** (firing rate decreases over time; inter-spike interval increases)

!!! tip "Move slowly and allow settling time"
    Small knob movements can produce large qualitative changes (silent → spiking). Make changes gradually and give the trace time to settle.

### **Success criteria**

You should be able to demonstrate all four regimes, in order:

- **Zero-current baseline** at the center detent
- **Hyperpolarized** Vm (turn left)
- **Depolarized** Vm (turn right)
- **Spiking** and **adaptation** during sustained rightward current

If you cannot reach spiking:
- confirm you are observing the correct channel (Vm)
- confirm the GUI is streaming live data
- verify your board is running the expected firmware/configuration
- see [Troubleshooting](troubleshooting.md)

---

## **Step 4 — Run a simple stimulus protocol**

Once you have confirmed that direct current injection works, you can run a simple stimulus protocol from the GUI (for example a step or pulse train) to observe transient responses superimposed on the baseline set by the current injection knob.

Procedure:

1. Set the current injection potentiometer back to the **center detent** so the baseline is stable.
2. On the experiment box on the board (dashed lines), select square stimulus strength and frequency by modifying the two potentiometer on the right. At first set the stimulus strength to positive (right) values.
3. Plug a cable from **stimulus output** (bottom right corner) to **current input** (bottom left)
4. Run the stimulus and observe how Vm responds.

### **Success criteria**

- Vm shows a reproducible change aligned with the stimulus window
- The response depends on baseline (e.g., near threshold you may trigger spikes)

---

## **Step 5 — (Optional) Test the LED/photodiode workflow**

If you have the **LED stimulus cable** connected:

1. Plug the LED cable on the **stimulus output** and place the LED on top of the photodiode situated on the photoreceptor drawing.
2. Apply a similar stimulus as before (note that there is no negative stimulus strength here, no negative light obviously)
3. Observe the photodiode/optical input signal on the current input traces and Vm in the GUI.

### **Success criteria**

- The LED turns on/off as commanded
- The photodiode signal changes reliably with the stimulus

---

## **Step 6 — Record a short dataset (CSV)**

Record a short run (10–30 seconds is enough) that includes some transitions between regimes (for example baseline → spiking) and, if possible, a sustained spiking segment to capture adaptation.

1. Select on the GUI a record folder, then enter a file name on which the data will be recorded
2. Start recording in the GUI.
3. With the potentiometer at the **center detent**, record ~2 seconds of baseline.
4. Turn **left** briefly to hyperpolarize, then return to center.
5. Turn **right** into spiking and hold long enough to see adaptation.
6. Stop recording and export as **CSV**.

### **Recommended naming convention**

Use a filename that captures key context:

- `<date>_<protocol>_<notes>.csv`

Example:
- `2025-12-29_current-injection_adaptation.csv`

---

## **Step 7 — Quick sanity-check your CSV**

Open the CSV in a spreadsheet viewer or in Python (see [Data analysis → Python quickstart](../data-analysis/python-quickstart.md)).
The .csv file can also be opened directly on the GUI on the data analysis tab. This part will be covered later for proper experiments

Confirm:

- The file spans the full recording duration
- Vm transitions are visible (baseline, hyperpolarization, depolarization, spiking)
- During sustained spiking, the firing rate decreases over time (adaptation)
