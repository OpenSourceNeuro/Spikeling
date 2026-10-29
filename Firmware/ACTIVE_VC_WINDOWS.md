# Start here: active voltage-clamp prototype (Windows)

Your passive RC model, input response and 500 Hz clock have passed the planned
bench checks. The next stage adds voltage-gated sodium and potassium currents.
This is a new experimental firmware, not a release. Its active timing still
needs testing on your ESP32-S3. Start with ONE case, then inspect the result.

## 1. Keep the working passive firmware

Keep Spikeling_VC_Clock_Fix_08212b9.zip and its extracted sketch as a fallback.
Extract this active ZIP into a NEW folder. Open the folder containing this guide
and the Firmware directory. Do not mix individual new headers with old firmware.
There is no hardware modification for this step.

## 2. Upload the complete new sketch

Open Firmware/Spikeling_V3/Spikeling_V3.ino from THIS package in Arduino IDE.
Keep all files in its Spikeling_V3 folder together. Use your working settings:

- ESP32S3 Dev Module; ESP32 core 3.3.12 was used for the supplied build.
- USB Mode: Hardware CDC and JTAG; USB CDC On Boot: Enabled.
- CPU 240 MHz; QIO 80 MHz; 4 MB flash; PSRAM disabled.
- Use the same partition/upload settings that worked for the passive build.
- Select COM13 if Windows still assigns that port.

The bundled Firmware/Librairies directory contains the four required libraries.
Use the libraries already installed for the previous prototype, or install these
copies if Arduino IDE reports a missing dependency. Upload the WHOLE sketch,
then close Serial Monitor and the Spikeling GUI so Python can own the port.
Compiled images are also included for reproducibility; Arduino IDE upload of the
source is the recommended route. No manual flash-offset commands are required.

## 3. Use your existing Python environment

Open PowerShell in the extracted folder containing this guide and Firmware.
The following path uses the environment you already created:

```powershell
$vcPython = "C:\Users\Agatrhe\Desktop\Spikeling_VC_Prototype_d245d07\.venv-vc\Scripts\python.exe"
& $vcPython -m pip install -r .\Firmware\tools\requirements_active_vc.txt
```

If you moved the old prototype folder, update only that interpreter path.
Keep all Python files in Firmware/tools together; the runner imports its helpers.
NumPy is installed through the plotting/scientific dependencies. No compiler is
needed on your PC to run these hardware tests.

## 4. Prepare quiet external inputs

- Patch centred; Noise fully down; photodiode gain at zero.
- Disconnect Current-In and incoming synaptic cables.
- Close the GUI, Serial Monitor and other programs using COM13.

The script selects ideal active VC and a -70 mV holding potential. It controls
Vcmd during this test, so leave the physical knobs unchanged. It uses 0.1 model
ms per 2 ms hardware tick: 1 model ms lasts 20 ms of wall time.

## 5. Run ONLY the first active-step case

```powershell
& $vcPython .\Firmware\tools\run_active_vc_tests.py COM13 --case 01_active_step
```

Allow roughly ten seconds, plus first-run plotting time. The programme first
conditions the model, then applies a -70 to -20 mV step lasting 20 model ms.
It records the return to -70 mV and checks the entire response and clock.
No GUI command or additional serial command is needed.

Expected observations:

1. Vm follows the imposed step exactly in this IDEAL-clamp case.
2. Brief capacitive currents appear at the voltage changes.
3. Sodium current becomes negative (inward), peaks early and then inactivates.
4. Potassium current becomes positive (outward) more slowly and persists.
5. At the end, the runner requests original CC, pharmacology OFF, access-clamp
   defaults and Patch knob control, and checks that binary streaming resumes.

This implementation's software reference predicts an approximately -3.1 nA
sodium peak and +2.0 nA late potassium current for that step. These are designed
model values, not calibration targets for a biological neuron. A nonzero holding
current in the active cell is expected even when external inputs are quiet.

The PASS checks include: all samples present, currents agreeing with an independent
reference, current conservation, bounded gates, 500 Hz within 2% globally and in
complete one-second windows, and no firmware diagnostic flags. Any deadline flag
fails the run even if the numerical currents look correct. PC timestamps measure
average cadence; individual output jitter would require an oscilloscope.

## 6. Send the first result before changing the setup

A new vc_active_TIMESTAMP folder is created. Send:

- Its TOP-LEVEL report.json (includes CC-stream cleanup and the case results).
- 01_active_step/recording.png.
- If anything fails, also 01_active_step/recording.csv.

Then reopen the GUI and check ordinary Patch-controlled CC firing. Binary-stream
resumption alone does not prove normal physical firing or calibrated DAC output.
If the active test reports overruns, keep its files; do not hide the fault by
changing the timing or ignoring flags. Return to the known working passive
sketch if you need the device immediately for teaching.

## Subsequent checks, after the first case passes

These cases are ready, but they are not required for the first report:

| Case | Purpose |
| --- | --- |
| 02_TTX | 92 nM: existing Hill model leaves 1/11 of gNa |
| 03_TEA | 5 mM: leaves 1/11 of delayed-rectifier gK |
| 04_access_resistance | Finite 5 MOhm access; Vm deviates from command |
| 05_sodium_reversal | At +50 mV the Na driving force is zero |
| 06_sodium_inactivation | A -40 mV hold reduces available Na before the step |
| 07_above_sodium_reversal | At +60 mV Na current is outward |
| 08_potassium_tail | After a -20 mV hold, a -90 mV step gives inward K tail current |

Run one case by substituting its name after --case. To run all eight:

```powershell
& $vcPython .\Firmware\tools\run_active_vc_tests.py COM13
```

The full run typically takes about a minute and stops at the first failed case.
The script deliberately clears drug doses and receptor selections for repeatable
tests; it does not restore an earlier drug experiment. First upload always boots
into original CC with pharmacology OFF.

## Scope of this stage

The active model is Na/K/leak, with classic HH gating and deliberately chosen
teaching-cell conductances. Existing integrated-v2 pharmacology modules supply
shared doses, receptors and release states. Active VC implements TTX/TEA and
adapts receptor currents; apamin/4-AP raise unsupported flag 32 because SK/A
channels have not been added. Combined pharmacology hardware tests remain ahead.
The separate STP/LTP branch has not been merged. GUI controls/labels for this new
active mode are not included; use the Python runner for quantitative recordings.
See Firmware/ACTIVE_VC_PROTOTYPE.md and VALIDATION.md for model details, sources,
verification evidence and limitations.
