# **Troubleshooting**

This page helps you quickly diagnose and fix the most common Spikeling setup issues.
Start with the symptom that best matches what you see.

## **Quick triage checklist (do this first)**

- [ ] Use a **known-good USB data cable** (charge-only cables are the #1 cause of failures)
- [ ] Try a different USB port (or a **powered USB hub**)
- [ ] Close anything that can own the serial port (Arduino Serial Monitor, PlatformIO monitor, PuTTY, CoolTerm, etc.)
- [ ] Confirm you selected the **correct port** in the GUI (unplug/plug trick)
- [ ] Confirm your board family:
  - v2.x: mini-USB + CP210x driver
  - v3.x: USB-C + native USB CDC (usually no driver)

---

## **Symptom A — The device does not appear as a serial/COM port**

### **A1) You are using v2.x (mini-USB, CP210x)**

Most likely causes:
- CP210x driver not installed
- bad/charge-only cable
- insufficient USB power

Fix:
1. Install the CP210x driver:
   - https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers
2. Unplug/replug the board.
3. Check again:
   - Windows: Device Manager → Ports (COM & LPT) → “Silicon Labs CP210x … (COMx)”
   - macOS: `/dev/tty.SLAB_USBtoUART`
   - Linux: `/dev/ttyUSB0` (or another `ttyUSB*`)

If still missing:
- try another USB cable
- try a powered hub

### **A2) You are using v3.x (USB-C, ESP32-S3 native USB)**

Most likely causes:
- bad/charge-only USB-C cable (very common)
- problematic USB port/hub

Fix:
1. Swap the USB-C cable (use a verified **data** cable).
2. Try a different USB port (or a powered hub).
3. Check again:
   - Windows: Device Manager → Ports (COM & LPT) → “USB Serial Device (COMx)” (name may vary)
   - macOS: `/dev/tty.usbmodem*` or `/dev/cu.usbmodem*`
   - Linux: `/dev/ttyACM0` (or another `ttyACM*`)

---

## **Symptom B — The port exists but the GUI cannot connect**

Most likely causes:
- another application is using the port
- wrong port selected
- intermittent USB cable/power

Fix (in order):
1. Close Arduino Serial Monitor / PlatformIO monitor / any serial terminal.
2. In the GUI, refresh the port list and reconnect.
3. Use the “unplug/plug trick”:
   - unplug the board
   - note the port list
   - plug it back in
   - select the **new** port that appears
4. Swap USB cable and/or use a powered hub.

---

## **Symptom C — The GUI connects, but plots are flat / not updating**

First, distinguish between “flat but updating” and “not updating”.

### **C1) The plot is updating (time moves), but Vm is flat**

This can be normal at baseline. To confirm the system responds:

1. Go to the board’s **current injection potentiometer** (bottom-left, on the pipette graphic).
2. Confirm it is at the **center detent** (0 current).
3. Turn **left** from center → Vm should **hyperpolarize**.
4. Return to center.
5. Turn **right** from center → Vm should **depolarize** and may spike.

If Vm does not respond:
- confirm you are viewing the correct trace (Vm)
- confirm the GUI is in hardware mode (not emulator-only, if applicable)
- consider reflashing firmware (see [Flash firmware](flash-firmware.md))

### **C2) The plot is not updating at all**

Most likely causes:
- streaming is not started/enabled in the GUI
- the GUI is connected but not receiving data
- a performance issue is freezing updates

Fix:
1. Look for a **Start/Stop streaming** control in the GUI and ensure streaming is enabled.
2. Disconnect and reconnect.
3. Reduce load:
   - close other heavy applications
   - try a powered hub
4. If the GUI becomes unresponsive, see “Symptom F — GUI is slow or freezes”.

---

## **Symptom D — I can depolarize/hyperpolarize, but I cannot reach spikes**

Most likely causes:
- knob range not reaching threshold due to configuration/calibration
- you are not observing the correct channel
- firmware mismatch for your board family

Fix:
1. Confirm you are looking at the correct Vm channel.
2. Move slowly to the right (depolarizing direction) and hold for a few seconds.
3. If still no spikes:
   - confirm the firmware you flashed matches your board family (v2.x vs v3.x)
   - reflash firmware with a clean upload (see [Flash firmware](flash-firmware.md))

---

## **Symptom E — Very noisy signal / unstable baseline**

Most likely causes:
- poor grounding between connected devices
- long TRS cables picking up noise
- USB power noise from laptop ports

Fix:
1. Keep TRS cables short, especially for analog (Ring).
2. Confirm a stable ground reference:
   - TRS Sleeve (S) is ground
   - if using multiple devices, ensure grounds are shared intentionally
3. Try a powered USB hub.
4. Move away from strong noise sources (chargers, laptop bricks, fluorescent lamps).

---

## **Symptom F — GUI is slow, freezes, or plots lag**

Most likely causes:
- plotting too much data at high refresh rate
- a slow machine or overloaded CPU
- background tasks interfering

Fix:
1. If the GUI has options for:
   - **decimation**
   - **buffer length**
   - **update rate**
   reduce them.
2. Close other applications.
3. Prefer a wired mouse/keyboard over heavy USB peripherals if using a marginal hub.
4. If you run from source, ensure you installed the pinned requirements versions.

---

## **Symptom G — LED stimulus does not work / photodiode does not respond**

### **G1) LED does not light**

Fix:
1. Verify the LED cable is connected to the correct jack.
2. Check LED polarity and wiring (LEDs are directional).
3. Run a simple on/off light stimulus in the GUI.

### **G2) LED lights, but photodiode trace does not change**

Fix:
1. Position the LED close to the photodiode and stabilize it (tape/mount).
2. Reduce ambient light for a clean signal.
3. Confirm you are viewing the correct photodiode/sensor channel in the GUI.

---

## **Symptom H — Flashing firmware fails**

Most likely causes:
- wrong board selected in Arduino IDE
- port is in use
- board not in download mode

Fix:
1. Close anything using the serial port.
2. Confirm you selected the correct board target:
   - v2.x: ESP32 Dev Module (or equivalent ESP32 target)
   - v3.x: ESP32S3 Dev Module (or equivalent ESP32-S3 target)
3. Try the BOOT/RESET download mode sequence (if available).
4. See the detailed guide: [Flash firmware](flash-firmware.md)

---

## **If you need help (what to include)**

When reporting an issue, include:

- board family: v2.x or v3.x
- OS: Windows/macOS/Linux
- which port name you see (COMx or `/dev/...`)
- GUI version (or commit, if running from source)
- firmware version (if known)
- what you expected vs what happened
- screenshots of:
  - GUI connection panel
  - Device Manager (Windows) or port list (`ls /dev/tty*`) if relevant
