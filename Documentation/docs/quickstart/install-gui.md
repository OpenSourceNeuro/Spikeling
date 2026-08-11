# **Install the GUI**

This page explains how to install and run the Spikeling desktop GUI. The GUI is used to connect to Spikeling hardware (or the emulator), visualize signals in real time, run protocols, and record/export data.

## **Choose an installation method**

There are two common ways to install the GUI:

1. **Install from a pre-built release (recommended for most users)**  
   Best for teaching, outreach, and classroom use.

2. **Install from source (recommended for developers and contributors)**  
   Best if you want to modify the GUI, test changes, or run the latest code from the repository.

---

## **Option A — Install from a pre-built release (recommended)**

If you have a packaged GUI release (installer or pre-built application):

Use **[Latest GUI release](https://github.com/OpenSourceNeuro/Spikeling/releases/latest)** to find GitHub's most recently published release, or browse **[All GUI releases](https://github.com/OpenSourceNeuro/Spikeling/releases)** to select a specific version. "Latest" means newest publication; it does not by itself confirm compatibility with your hardware and firmware. For managed teaching deployments, use the version approved for your equipment.

1. Download the clearly versioned asset for your operating system.
2. Extract / install it.
3. Launch the application.

### **First-run checklist**

- The GUI opens without errors.
- You can open the **Port / Connection** menu and see a list of serial ports.
- If you are using Spikeling hardware:
  - **v2.x**: you installed the **CP210x driver** and the board appears as a COM/serial port.
  - **v3.x**: the board appears as a USB serial device (typically no driver needed).

If the GUI launches but the device does not appear, see **[Troubleshooting](troubleshooting.md)**.

---

## **Option B — Install from source (developers)**

This option runs the GUI using Python. It is cross-platform and convenient for development, but requires installing dependencies.

### **1) Prerequisites**

- **Python 3.10+** (recommended)
- **Git** (recommended)
- (Optional) A virtual environment to isolate dependencies

### **2) Get the source code**

Clone the repository and enter it:

```
git clone https://github.com/OpenSourceNeuro/Spikeling.git
cd Spikeling
```

### **3) Create and activate a virtual environment**

Windows (PowerShell):

```
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS / Linux:

```
python3 -m venv .venv
source .venv/bin/activate
```

### **4) Install dependencies**

Install from the project `requirements.txt`:

```
pip install -r requirements.txt
```

For reference, the GUI depends on the following pinned versions:

- PySide6==6.9.2
- numpy==2.3.2
- pandas==2.3.2
- pyinstaller==6.15
- pyqtgraph==0.13.7
- scipy==1.16.1

### **5) Run the GUI**

Run the GUI entry point used by the repository (a common pattern is `main.py`):

```
python main.py
```

If your GUI lives in a subfolder (for example `GUI/`), run it from there:

```
cd GUI
python main.py
```

---

## **Verify the GUI is working**

### **Connect to hardware**

1. Plug in your Spikeling board and confirm the serial port is visible (see **[Hardware setup](hardware-setup.md)**).
2. In the GUI, select the correct port and connect.
3. Run a basic stimulus and confirm you see live Vm data.

### **Use emulator mode (no hardware)**

1. Switch the GUI to **Emulator** mode.
2. Start the simulation.
3. Confirm plots update smoothly and recording/export works.

---

## **Common issues**

### **The GUI does not start**

- Confirm your Python version is supported.
- If using a virtual environment, confirm it is activated.
- Reinstall dependencies:

```
pip install -r requirements.txt
```

### **No ports appear / cannot connect**

- **v2.x**: confirm CP210x driver installation and use a known-good USB data cable.
- **v3.x**: try a different USB-C data cable and port.
- Close Arduino Serial Monitor and any serial terminal that might own the port.

See **[Troubleshooting](troubleshooting.md)** for step-by-step triage.

---

## **Next steps**

- If you need to update firmware: **[Flash firmware](flash-firmware.md)**
- Run your first protocol: **[First experiment](first-experiment.md)**
