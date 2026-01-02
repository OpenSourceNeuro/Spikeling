# **What you need**

This page lists the minimum equipment required to run Spikeling, plus recommended extras for reliable classroom deployments.

Spikeling is distributed in two official board families:

- **Spikeling v2.x (e.g., v2.5)**: ESP32 **WROOM-32**, **mini-USB**, USB-to-UART bridge (**CP210x**). Driver often required.
- **Spikeling v3.x (e.g., v3.0)**: ESP32 **S3 WROOM-1**, **USB-C**, native USB (USB CDC serial). Driver typically not required. Includes an **additional DAC IC** compared to v2.x.

Spikeling I/O is carried primarily over **3.5 mm stereo TRS** jacks:
- **Tip (T)** = digital / TTL (trigger, sync, digital events)
- **Ring (R)** = analog signal
- **Sleeve (S)** = ground

You can also use a **3.5 mm jack cable wired to an LED** to send light stimuli that the onboard photodiode reads.

---

## **Minimum requirements**

### **Hardware**

- **One Spikeling board** (v2.x or v3.x)
- **USB data cable** matching your board:
  - v2.x: **mini-USB** data cable
  - v3.x: **USB-C** data cable
- **At least one 3.5 mm TRS stereo cable** (for analog/digital I/O as needed)
- **LED stimulus cable** (3.5 mm jack cable wired to an LED) if you plan photodiode/light experiments

!!! warning "Charge-only USB cables are a common failure point"
    If Spikeling is not detected by your computer, the first thing to change is the USB cable. Many cables provide power but no data.

### **Computer**

- Windows / macOS / Linux computer with:
  - an available USB port
  - permission to install software (and a driver if using v2.x)

### **Software**

- **Spikeling GUI (desktop app)** for control, plotting, and recording/export
- **Firmware flashing tools** (only if you update firmware or build from source)

---

## **Board-specific requirements**

### **Spikeling v2.x (mini-USB, CP210x)**

Most v2.x boards use a **CP210x** USB-to-UART bridge. On many systems (especially Windows), you must install the CP210x driver for the board to appear as a serial/COM port.

#### **Driver installation (v2.x only)**

Spikeling runs on an Espressif ESP32 board and requires the USB-to-UART bridge **CP210x driver**, which can be obtained from Silicon Labs:

- CP210x VCP drivers page: [CP210x driver](https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers)
- Downloads tab: [Download here](https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers?tab=downloads)

Once the driver has been installed, users can:

- operate the GUI (see the [GUI UserManual](https://github.com/OpenSourceNeuro/Spikeling-V2/tree/main/GUI)), or
- modify the [microcontroller code](https://github.com/OpenSourceNeuro/Spikeling-V2/tree/main/Arduino%20Code/Spikeling_V2_2) through the Arduino IDE.

!!! tip "If you are using the newer Spikeling repository"
    Additional setup notes (including driver installation and firmware guidance) may also be available in the project’s Instruction Manual folder.

Recommended checks:
- After installing the driver, confirm the board appears as a serial device (COM port on Windows, `/dev/tty.*` on macOS, `/dev/ttyUSB*` or `/dev/ttyACM*` on Linux).
- If it still does not appear, swap USB cable and/or use a powered hub.

### **Spikeling v3.x (USB-C, native USB CDC)**

v3.x boards use the ESP32-S3 native USB interface and typically enumerate as a USB serial device without requiring a separate driver.

Recommended checks:
- Prefer a known-good USB-C **data** cable.
- If the port does not appear, try another USB port or a powered hub before troubleshooting software.

---

## **TRS connectors and cabling**

Spikeling uses **3.5 mm stereo TRS** jacks to carry both digital and analog signals with a shared ground:

- **Tip (T)** = digital / TTL
- **Ring (R)** = analog
- **Sleeve (S)** = ground

Recommended accessories:
- **TRS-to-breakout adapter(s)** (TRS → 3 wires / screw terminals / header pins)  
  Very useful for debugging and classroom setups where you want explicit access to Tip/Ring/Sleeve.
- **Spare TRS cables** (they are among the most common classroom failure points)

---

## **Recommended extras (high value in practice)**

### **For reliable experiments (especially in classrooms)**

- **Powered USB hub** (improves stability on laptops with weak USB power)
- **Multimeter** (quick checks: ground continuity, obvious wiring faults)
- **Small oscilloscope or logic analyzer** (optional but very helpful)
  - Validate TTL triggers (Tip) and confirm analog levels (Ring)

### **For multi-unit / networks**

- **Two or more Spikeling units**
- **Short TRS patch cables**
- A clear **grounding plan** (shared ground between units is usually required for stable analog measurements)

### **For data analysis**

- A Python environment (optional) to run example analysis:
  - Load CSV
  - Plot Vm
  - Detect spikes
  - Compute basic metrics (e.g., firing rate, F–I curves)

---

## **Before you start (quick checklist)**

- [ ] I know my board family (**v2.x** vs **v3.x**)
- [ ] I have a **data-capable** USB cable (mini-USB or USB-C)
- [ ] (v2.x only) I installed the **CP210x** driver
- [ ] The board appears as a serial port on my computer
- [ ] I have at least one **TRS cable**
- [ ] I have the **LED stimulus cable** if I plan photodiode/light workflows
- [ ] I can launch the GUI

---

## **Next steps**

- Proceed to **[Hardware setup](hardware-setup.md)** and **[Install the GUI](install-gui.md)**
- If you plan to update firmware: **[Flash firmware](flash-firmware.md)**
- If something fails: **[Troubleshooting](troubleshooting.md)**
