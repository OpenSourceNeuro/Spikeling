# **Hardware setup**

This page walks you through the physical setup of Spikeling: powering the board, establishing a USB/serial connection, and preparing the TRS I/O used for analog + digital signals and light stimulation.

## **Identify your board family**

Spikeling exists in two official board families:

- **v2.x (e.g., v2.5)**: ESP32 **WROOM-32**, **mini-USB**, USB-to-UART bridge (**CP210x**)
- **v3.x (e.g., v3.0)**: ESP32 **S3 WROOM-1**, **USB-C**, native USB (**USB CDC serial**), additional DAC IC

If you are unsure, the USB connector is usually the easiest identifier:
- v2.x: **mini-USB**
- v3.x: **USB-C**

## **Step 1 — Connect power and USB**

1. Place the board on a non-conductive surface.
2. Connect the board to your computer using a **data-capable** USB cable:
   - v2.x: mini-USB data cable
   - v3.x: USB-C data cable
3. Avoid charge-only cables. If the board is not detected later, swap the cable first.

!!! tip "Classroom best practice"
    Use a powered USB hub at each station. It improves stability on laptops with weak USB power and reduces intermittent disconnects.

## **Step 2 — Confirm the board appears as a serial device**

This is the most important checkpoint before opening the GUI.

### **v2.x (CP210x) — confirm driver + COM/serial port**

1. Install the CP210x driver if you have not already:
```
https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers
```
2. Reconnect the board after installation.
3. Confirm a serial port appears:

**Windows**
- Open **Device Manager**
- Look under **Ports (COM & LPT)** for something like **“Silicon Labs CP210x USB to UART Bridge (COMx)”**

**macOS**
- In Terminal:
  - `ls /dev/tty.*`
- CP210x devices often appear as something like:
  - `/dev/tty.SLAB_USBtoUART`

**Linux**
- In Terminal:
  - `ls /dev/ttyUSB* /dev/ttyACM* 2>/dev/null`
- CP210x commonly enumerates as:
  - `/dev/ttyUSB0`

If no port appears:
- try a different USB cable
- try a powered hub or a different USB port
- confirm the CP210x driver is installed (Windows especially)

### **v3.x (ESP32-S3 native USB) — confirm USB CDC port**

v3.x boards typically enumerate without a separate driver.

**Windows**
- Device Manager → **Ports (COM & LPT)**
- Look for a **USB Serial Device (COMx)** or an Espressif/USB CDC serial entry (naming may vary)

**macOS**
- `ls /dev/tty.*` (or `ls /dev/cu.*`)
- You should see a new `/dev/tty.*` or `/dev/cu.*` entry after plugging the board in

**Linux**
- `ls /dev/ttyACM* /dev/ttyUSB* 2>/dev/null`
- Native USB CDC devices often show up as `/dev/ttyACM0`

If no port appears:
- swap the USB-C cable (most common issue)
- try a different port/hub
- avoid front-panel ports on desktops (they can be noisier/less reliable)

## **Step 2.5 — Choose the right port in the GUI**

When you open the Spikeling GUI, you will need to select the correct serial/COM port.

### **Typical port names (examples)**

**Windows**
- v2.x (CP210x): `COM3`, `COM4`, … (often labeled as CP210x in Device Manager)
- v3.x (USB CDC): `COMx` (often labeled “USB Serial Device” or similar)

**macOS**
- v2.x (CP210x): `/dev/tty.SLAB_USBtoUART` (or similar)  
- v3.x (USB CDC): commonly shows as `/dev/tty.usbmodem*` or `/dev/cu.usbmodem*`

**Linux**
- v2.x (CP210x): `/dev/ttyUSB0` (or another `ttyUSB*`)
- v3.x (USB CDC): `/dev/ttyACM0` (or another `ttyACM*`)

### **If the GUI cannot open the port**

Only one application can own a serial port at a time. If the GUI cannot connect:

- Close **Arduino IDE Serial Monitor**
- Close **PlatformIO Serial Monitor**
- Close any other serial terminal (PuTTY, CoolTerm, screen, minicom, etc.)
- Unplug/replug the board and refresh the port list in the GUI

!!! tip "Fast identification trick"
    Unplug the board, note the list of ports, plug it back in, and select the **new** port that appears.

## **Step 3 — Understand TRS I/O wiring**

Spikeling uses **3.5 mm stereo TRS** jacks to carry both digital and analog signals with a shared ground:

- **Tip (T)** = digital / TTL (trigger, sync, digital events)
- **Ring (R)** = analog signal
- **Sleeve (S)** = ground

### **Recommended cabling practice**

- Use **short TRS cables** for analog signals when possible (reduces noise pickup).
- Keep **sleeve/ground continuity** consistent across connected devices.
- If you need to interface to breadboards or external hardware, use a **TRS-to-breakout adapter** so you can access Tip/Ring/Sleeve explicitly.

!!! warning "Ground matters"
    Many “mystery” issues (noise, unstable readings, incorrect triggers) are grounding problems. If you connect Spikeling to other devices, ensure a shared ground reference via the TRS sleeve or an explicit ground lead.

## **Step 4 — Set up the LED light stimulus (photodiode workflow)**

Spikeling can use a **3.5 mm jack cable wired to an LED** to deliver a light stimulus that the onboard photodiode reads.

1. Plug the LED stimulus cable into the appropriate jack (as used by your board’s light stimulus input).
2. Position the LED so it illuminates the photodiode reliably:
   - keep the LED close and stable (tape or a small mount helps)
   - reduce ambient light if you want clean responses
3. In later steps (GUI), you will use the stimulus controls to drive the LED and observe the photodiode response.

Recommended checks:
- Verify LED polarity and wiring if it does not light.
- If the photodiode response is noisy, reduce ambient light and shorten cables.

## **Step 5 — Quick functional checks (before opening the GUI)**

- [ ] Board is connected with a **data-capable** USB cable
- [ ] A new serial/COM port appears (v2.x: CP210x; v3.x: USB CDC)
- [ ] I can identify the correct port and it is not in use by another program
- [ ] I have at least one **TRS cable** available for I/O
- [ ] (Optional) LED stimulus cable is connected and positioned for photodiode reading

## **Next steps**

- Install and launch the GUI: **[Install the GUI](install-gui.md)**
- Run your first test protocol: **[First experiment](first-experiment.md)**
- If anything fails: **[Troubleshooting](troubleshooting.md)**
