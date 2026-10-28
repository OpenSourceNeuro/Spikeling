# Passive voltage-clamp firmware prototype

This is the first VC integration milestone: a passive leak/capacitance cell,
with ideal clamp or finite access resistance and current compliance. It replaces
the old Izhikevich PI path **only when VCM 1 is selected**. VCM 0 retains the
original Izhikevich current-clamp equations, presets, reset and inputs.

No PCB modification is required. Axon analogue output remains Vm, the stimulus
DAC remains stimulus output, and clamp current is available over USB. There is
no physical current-monitor DAC output in this milestone.

## What works, and what this milestone does not claim

- Photodiode adaptation, noise and both incoming synapses advance once per model
  tick and remain inputs in VC. The VC solver never invokes input/release RNGs.
- PC1 and the patch knob set holding voltage; Current-In can add voltage steps
  in the existing hardware-command route. That ADC signal is not also injected
  as a current. VCMD/VSTEP provide separate explicit absolute commands.
- Vm LED and analogue output continue; axon TTL and spike buzzer are low in VC.
  An exit from a depolarised clamp must recover below the existing spike-output
  threshold before CC spike outputs rearm, avoiding a mode-change pulse.
- Incoming digital edge history, synaptic decay, drug state and release RNG
  state are not reset by switching modes. CC current command/pot selection is
  restored; the original CC preset remains selected.
- Izhikevich u continues its existing relaxation equation using VC Vm, without
  spike resets during VC. Returning to CC starts from present Vm and this u;
  this is an educational handover, not exact equivalence between cell models.
- The cell is passive: **no Na, K, A-type, calcium/SK or receptor kinetics have
  been added yet**. The pharmacology branch's dose/release helpers remain intact
  but are not connected to this passive solver. If pharmacology.enabled is set,
  diagnostic flag 32 explicitly identifies unsupported pharmacology. Retaining
  drug settings is not evidence that those drugs affect the passive cell.
- The portable solver already accepts an optional sum(g), sum(g*E) interface for
  later conductance synapses. The current sketch feeds legacy current synapses;
  that future conductance interface is tested mathematically, not wired to the
  in-development AMPA/GABA/NMDA implementation.

## Units and numerical model

The portable `VoltageClamp.h` module uses mV, ms, nA, pF, MOhm and uS. Defaults:
Cm=20 pF, Rm=500 MOhm, Rs=5 MOhm, EL=-70 mV, limits=-20/+20 nA.
The initial teaching conversion is **1 legacy current unit = 0.01 nA**. It is
explicit and fixed in vc::Runtime, not a biological calibration. CC stays in a.u.

The access circuit solves:

```
Iaccess = clip((Vcmd - Vm)/Rs, Imin, Imax)
Cm*dVm/dt = Iaccess + Iinput - (Vm-EL)/Rm - Ireceptor
```

Each interval is solved analytically with frozen input, including crossings
into/out of compliance. State is stored as float with double intermediates.
Vm is not clipped to spike peak or rescued with hidden resets. The DAC can still
clip voltages outside its display mapping; flag 8 reports that separately.

Ideal mode imposes Vcmd and reports capacitive charge as one-bin mean current;
its current is not compliance-limited. States are at interval ends; currents
are interval averages. Do not treat the first-bin current as an instantaneous
capacitive peak or add capacitance a second time to access current.

## Build for the current ESP32-S3 board

Validated compiler setup: Arduino CLI 1.5.1, Espressif Arduino core 3.3.12,
ESP32S3 Dev Module, hardware CDC/JTAG, CDC enabled at boot, 4 MB flash, no PSRAM.
Use the vendored libraries; their Gaussian header now uses portable `math.h`.

From the repository root:

```bash
arduino-cli core update-index --additional-urls https://espressif.github.io/arduino-esp32/package_esp32_index.json
arduino-cli core install esp32:esp32@3.3.12 --additional-urls https://espressif.github.io/arduino-esp32/package_esp32_index.json
arduino-cli compile --fqbn esp32:esp32:esp32s3:USBMode=hwcdc,CDCOnBoot=cdc,FlashSize=4M,PSRAM=disabled --libraries Firmware/Librairies Firmware/Spikeling_V3
```

For Arduino IDE, use the same board settings and install the supplied libraries.
Build/upload the complete sketch folder, including both new VoltageClamp headers.
The prototype has been compiled for ESP32-S3; it has not been flashed or bench
tested on a physical board by this development session.

## First board experiment

Disconnect the desktop GUI so it releases the USB port. Install the capture
tool's dependencies and run:

```bash
python -m pip install -r Firmware/tests/vc/requirements.txt
python Firmware/tools/capture_passive_vc.py COM5 --output passive_vc.csv
# Linux example: replace COM5 with /dev/ttyACM0.
```

The script checks VCINFO before selecting VC, commands a -70 to -60 mV pulse
with 10-ms pre-hold and 20-ms duration, then collects 10 ms after return. It saves
CSV and compares Vm and bin-average current with the passive RC solution using
the actually recorded input current. It checks sample continuity, firmware
flags and model time. It returns to CC without overwriting the prior CC command
or pot selection. It never flashes firmware. A GUI must not read the same port.

At the default 2000-us wall period and 0.1-ms model dt, the simulation is slowed
20-fold; the 40-ms model protocol takes about 0.8 wall seconds. Increase the
capture timeout if a slower loop period was previously selected.

Manual terminal sequence (newline after each command):

```
VCINFO
VCM 1
VCP 20 500 5 -70
VCL -20 20
VCI 0
VCMD -70
VCT 1
VSTEP -60 10 20
```

Stop diagnostic mode with VCT 0; return to current clamp with VCM 0.
Confirm Vm DAC step timing/calibration on an oscilloscope, then repeat with light,
noise and incoming spikes. Real loop timing, USB throughput, DAC/ADC calibration
and physical TTL behaviour remain bench acceptance tasks.

## Commands

| Command | Meaning |
| --- | --- |
| VCINFO | Explicit text identity/units query: VC-PASSIVE-1,mV,ms,nA,pF,MOhm |
| VCM 0 / 1 | Original Izhikevich CC / passive VC |
| VCMD voltage | Absolute Vcmd; ignores Current-In voltage commands |
| PC1 voltage | VC holding voltage, retaining Current-In voltage-step route |
| PC0 | Return command control to patch knob and Current-In |
| VCP Cm Rm Rs EL | Atomic validated parameter update; pF, MOhm, MOhm, mV |
| VCL minimum maximum | Validated VC current limits, nA; VIL is an alias |
| VCI 0 / 1 | Finite access resistance / ideal clamp |
| VSP span | Patch-knob voltage span around the selected preset's resting voltage, mV |
| VCT 0 / 1 | Existing binary frames / diagnostic CSV in VC |
| VSTEP target delay duration | Absolute pulse target and delay/duration in model ms |
| VRS | Explicitly clear displayed current/reset cell sample at current Vm; cancel protocol |

Vcmd range is -110..+80 mV, separate from the Izhikevich spike peak. Cm accepts
1..1000 pF, Rm 10..10000 MOhm, Rs 0.1..100 MOhm. Limits must straddle zero and
lie within -100..+100 nA. Step delay/duration must be integer multiples of dt and
no more than 60000 ms each; duration must be positive. Bad numeric arguments,
NaN/Inf, trailing tokens and invalid ranges are rejected atomically. Flag 2
tracks the last control command; the next accepted control command clears it.
VPID is obsolete for this circuit and is rejected instead of silently ignored.

VSTEP captures the current holding voltage, runs on device ticks and then holds
that baseline. It ignores Current-In command steps throughout the protocol and
after completion until PC0/PC1 or another command source is selected. Light,
noise and synaptic current remain active. Ordinary command steps preserve charge.
An explicit neuron-preset change remains an explicit neuron reset and cancels
the protocol. The passive parameters do not pretend to represent all 20 presets.

## Diagnostic stream and compatibility

VCT 1 emits only CSV records during VC, no interleaved sample packets:

```
VC1,sequence,time_ms,Vcmd_mV,Vm_mV,Iclamp_nA,Icap_nA,Ileak_nA,Iinput_nA,flags,solve_us,previous_loop_us
```

The example above names the fields; actual records contain numeric values after
VC1. The sequence is the low 32 bits of the session tick. Current model time uses
the full tick; VCM entry starts a new session. solve_us measures the solver and
previous_loop_us measures the preceding complete tick, including serial output.

| Flag bit | Meaning |
| --- | --- |
| 1 | Current compliance was active for part of the interval |
| 2 | Last VC control command rejected |
| 4 | Solver rejected an invalid input/step; last valid state retained |
| 8 | Vm outside analogue/display mapping range |
| 16 | Clamp current exceeds the legacy int16 current field |
| 32 | Pharmacology enabled but unsupported by this passive milestone |
| 64 | Preceding complete model tick took at least its scheduled wall period |

With VCT 0 the existing 0xAA55 + 16-byte payload remains unchanged in size/order.
CC packets keep their original values and a.u. units. In VC all current fields
use 0.01 nA, voltages use 0.01 mV, and stim_state is rounded Vcmd in mV. Existing
GUI labels still say a.u./stimulus percent; use the supplied capture tool for
quantitative VC validation until the GUI gains version-aware labels. Leaving
VC disables diagnostic streaming automatically.

## Automated checks

```bash
python -m unittest discover -s Firmware/tests/vc -v
```

The tests compile the actual portable C++ solver and actual complete sketch plus
vendored serial parser, using deterministic ADC/DAC/GPIO/noise doubles. The CC
comparison compiles the original files from pinned base commit
927a70abb46f2b189af1bbe4647a7e7a58c9d2a8 (must be available in local Git history).
It compares packets byte-for-byte for all 20 presets under injected current,
synaptic, noise-override and photodiode scenarios. This proves those host traces,
not every possible input or ESP32 bitwise equivalence.

The numerical checks cover analytic RC charging, interval-average current,
capacitive charge, Kirchhoff balance, compliance crossings, current input,
conductance reversal and float tolerances. Integration checks cover commands,
device timing, ADC command arbitration, handover, packet units, input continuity,
pharmacology/RNG retention, and capture validation. Host doubles do not certify
physical IO, stochastic Gaussian distribution or board deadlines.
