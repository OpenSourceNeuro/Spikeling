# **Quickstart**

This Quickstart is a linear path to get a working Spikeling setup in minutes. The goal is to reach a first successful experiment where you can:

- connect to the device from the GUI,
- observe live membrane potential (Vm),
- control Vm with the **current injection potentiometer** (center detent = 0 current),
- record a short dataset and export it to CSV.

If you are teaching a class, follow the same sequence and then use the Teaching Hub material to scale to multiple stations.

---

## **Recommended path (follow in order)**

1. **What you need**  
   Board differences (v2.x vs v3.x), cables, TRS connectors, LED stimulus cable, and drivers.  
   → [What you need](what-you-need.md)

2. **Hardware setup**  
   Connect the board, confirm the serial/COM port appears, and learn how to select the correct port in the GUI.  
   → [Hardware setup](hardware-setup.md)

3. **Install the GUI**  
   Install from release or from source (Python virtual environment + requirements).  
   → [Install the GUI](install-gui.md)

4. **Flash firmware (if needed)**  
   Recommended when setting up a new device, updating firmware, or developing.  
   → [Flash firmware](flash-firmware.md)

5. **First experiment**  
   Use the current injection potentiometer (center detent) to drive Vm through hyperpolarization, depolarization, spiking, and adaptation. Record a short CSV.  
   → [First experiment](first-experiment.md)

6. **Troubleshooting**  
   If any step fails, use symptom-based fixes (port missing, cannot connect, flat/noisy signal, LED/photodiode issues, flashing errors).  
   → [Troubleshooting](troubleshooting.md)

---

## **Board-specific notes (read once)**

### **Spikeling v2.x (mini-USB, CP210x)**

- Uses a CP210x USB-to-UART bridge and typically requires the CP210x driver.
- Appears as a CP210x/SLAB serial device (COM port on Windows).

### **Spikeling v3.x (USB-C, native USB)**

- Uses ESP32-S3 native USB (USB CDC serial) and typically does not require a driver.
- Includes an additional DAC IC compared to v2.x.

---

## **Common pitfalls (avoid these)**

- **Charge-only USB cable**: the device powers but does not appear as a serial port.
- **Wrong port selected**: use the unplug/plug trick to identify the new port.
- **Serial port already in use**: close Arduino Serial Monitor and any serial terminal.
- **Noise and instability**: keep TRS cables short and ensure a clean shared ground.

---

## **After Quickstart**

Once Quickstart is complete, continue with:

- Concepts and workflows: [User guide](../user-guide/index.md)
- Ready-to-run activities: [Experiments](../experiments/index.md)
- Teaching materials: [Teaching hub](../teaching-hub/index.md)
- Data analysis: [Data analysis](../data-analysis/index.md)
