# Start here: finite-access voltage-clamp timing revision (Windows)

The ideal active step, TTX and TEA cases passed on your board. The finite-access
case passed its waveform/model checks but recorded one 2.048 ms loop against
the 2 ms period. This revision reuses one voltage exponential for the exact
endpoint and interval mean, retaining all four internal steps and test limits.
The physical finite-access rerun at 5c2e063 now passes: 499.907 Hz, no diagnostic
flags and maximum loop 1.945 ms. Cases 05 to 08 now also pass on this revision.
If you completed that sequence, keep the firmware installed and use the
post-test checks below. Steps 1 to 6 describe installation and the access check
for a fresh setup; the subsequent-case commands remain available for new boards.

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

The finite-access case selects active VC with 5 MOhm access and a -70 mV hold. It controls
Vcmd during this test, so leave the physical knobs unchanged. It uses 0.1 model
ms per 2 ms hardware tick: 1 model ms lasts 20 ms of wall time.

## 5. Repeat ONLY the finite-access case

```powershell
& $vcPython .\Firmware\tools\run_active_vc_tests.py COM13 --case 04_access_resistance
```

Allow roughly ten seconds, plus plotting time. Dependencies are unchanged;
if the previous installation succeeded, the pip command above is optional. The programme checks for the new gates=2,voltage=2 identity, then
conditions the model, then applies a -70 to -20 mV step lasting 20 model ms.
It records the return to -70 mV and checks the entire response and clock.
No GUI command or additional serial command is needed.

Expected observations:

1. Vm approaches the imposed step gradually; ionic currents produce command-tracking error.
2. Brief capacitive currents appear at the voltage changes.
3. Sodium current becomes negative (inward), peaks early and then inactivates.
4. Potassium current becomes positive (outward) more slowly and persists.
5. At the end, the runner requests original CC, pharmacology OFF, access-clamp
   defaults and Patch knob control, and checks that binary streaming resumes.

The previous finite-access run gave about -3.16 nA peak Na current and +1.43 nA
late K current, with late Vm near -26.92 mV at a -20 mV command. These are model
values, not biological calibration targets. Such departures from Vcmd are an
intended finite-access effect; they are compared with the coupled ODE reference.

The PASS checks include: all samples present, currents agreeing with an independent
reference, current conservation, bounded gates, 500 Hz within 2% globally and in
complete one-second windows, and no firmware diagnostic flags. Any deadline flag
fails the run even if the numerical currents look correct. PC timestamps measure
average cadence; individual output jitter would require an oscilloscope.

## 6. Send the finite-access result before changing the setup

A new vc_active_TIMESTAMP folder is created. Send:

- Its TOP-LEVEL report.json (includes CC-stream cleanup and the case results).
- 04_access_resistance/recording.png.
- 04_access_resistance/recording.csv.

Then reopen the GUI and check ordinary Patch-controlled CC firing. Binary-stream
resumption alone does not prove normal physical firing or calibrated DAC output.
If the active test reports overruns, keep its files; do not hide the fault by
changing the timing or ignoring flags. Return to the known working passive
sketch if you need the device immediately for teaching.

## Subsequent checks, after the finite-access case passes

The first three cases already passed on the earlier revision. After the access
rerun passes, cases 05 to 08 are the next new physical checks:

| Case | Purpose |
| --- | --- |
| 02_TTX | 92 nM: existing Hill model leaves 1/11 of gNa |
| 03_TEA | 5 mM: leaves 1/11 of delayed-rectifier gK |
| 04_access_resistance | Finite 5 MOhm access; Vm deviates from command |
| 05_sodium_reversal | At +50 mV the Na driving force is zero |
| 06_sodium_inactivation | A -40 mV hold reduces available Na before the step |
| 07_above_sodium_reversal | At +60 mV Na current is outward |
| 08_potassium_tail | After a -20 mV hold, a -90 mV step gives inward K tail current |

Run one case by substituting its name after --case.

To run only the four remaining cases after a passing access rerun, use the
same extracted folder, quiet inputs and Python environment. No upload is needed:

```powershell
$cases = "05_sodium_reversal", "06_sodium_inactivation", "07_above_sodium_reversal", "08_potassium_tail"
foreach ($case in $cases) {
    & $vcPython .\Firmware\tools\run_active_vc_tests.py COM13 --case $case
    if ($LASTEXITCODE -ne 0) { break }
}
```

Each case creates its own vc_active_TIMESTAMP folder. Send those new folders
as one ZIP, preserving the top-level report.json and the case CSV/PNG. A failure
stops this sequence; keep that result before changing anything. After testing,
reopen the GUI and check normal Patch-controlled CC firing.

For a fresh full validation, run all eight:

```powershell
& $vcPython .\Firmware\tools\run_active_vc_tests.py COM13
```

The full run typically takes about a minute and stops at the first failed case.
The script deliberately clears drug doses and receptor selections for repeatable
tests; it does not restore an earlier drug experiment. The firmware always boots
into original CC with pharmacology OFF.

## After completing the eight core cases

The staged bench sequence now has passing recordings for cases 01 to 08,
with cases 01 to 03 at ddabb4a and cases 04 to 08 at 5c2e063. The four newest
recordings pass at about 500 Hz, with zero flags and maximum loops below 1.675 ms.
No new upload or repeat of those cases is needed for the next integration stage.

After Python exits, reopen the GUI on COM13. With quiet inputs, turn the Patch
knob until ordinary CC firing starts, then turn it back until firing stops.
Check the usual noise and photodiode responses in CC. The test cleanup requests
CC, pharmacology OFF and Patch control; binary streaming alone does not verify
normal firing on the display or physical outputs.

The user has confirmed normal knobs/functions and GUI behaviour after the core
sequence. The next Python-only pack starts active-VC shared inputs, repeated mode
transitions and longer access-mode timing; see VC_INTEGRATION_WINDOWS.md.
Receptor/release pharmacology follows separately. The core step runner above
deliberately requires quiet inputs, so its PASS does not establish those combined
behaviours. The detailed evidence is in ACTIVE_VC_VALIDATION.md.

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
