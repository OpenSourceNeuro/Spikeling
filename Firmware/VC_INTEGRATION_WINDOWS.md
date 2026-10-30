# Active VC integration tests — Windows

Keep the working 5c2e063 firmware installed. This is a Python test pack, with
no firmware upload or hardware modification required. It checks the existing
active identity clock=2,gates=2,voltage=2 before taking measurements.

The eight core protocols have passing board recordings across the staged
validation sequence. You also reported that all knobs/functions and the GUI
behave correctly after returning to CC. This next stage measures shared inputs
while active VC is enabled, stored TTX/TEA settings across repeated handovers,
and longer finite-access timing.

## Start with case 09 only

1. Extract the ZIP into a new folder. Open PowerShell in the folder containing
   START_HERE_WINDOWS.md and Firmware. Keep the Python files in Firmware/tools
   together; the new runner imports the supplied helpers.
2. Close the Spikeling GUI, Arduino Serial Monitor and any other COM13 client.
3. Disconnect Current-In and both incoming synaptic cables. Centre Patch and
   photodiode gain; put Noise fully down. Leave the other controls unchanged.
4. Run this command using your existing Python environment:

```powershell
$vcPython = "C:\Users\Agatrhe\Desktop\Spikeling_VC_Prototype_d245d07\.venv-vc\Scripts\python.exe"
& $vcPython .\Firmware\tools\run_vc_integration_tests.py COM13 --case 09_active_noise
```

Dependencies are the same as the previous active tests. If needed:

```powershell
& $vcPython -m pip install -r .\Firmware\tools\requirements_active_vc.txt
```

Follow the prompts in PowerShell:

- Confirm the initial quiet setup by pressing Enter. The program conditions the
  active model, then records a four-second baseline.
- When prompted, turn Noise up moderately and leave it fixed, then press Enter.
  The program records four seconds with noise present.
- When prompted, turn Noise completely down, then press Enter. Keep it down
  while the program checks quiet recovery and records another four seconds.

The background reader stays active during prompts and analysis. Each operator
prompt allows 60 seconds. Do not open the GUI while the capture is running.

This case uses ideal active VC at -70 mV. Vm should remain controlled while
input and clamp currents fluctuate in opposite directions. Na/K currents remain
part of the membrane model. Signal-presence limits are teaching/test thresholds,
not a calibrated noise-amplitude specification.

Send the entire new vc_integration_TIMESTAMP folder as a ZIP, including the
top-level report.json and case recording.csv, recording.png and report.json.
The program prints the update rate, maximum loop duration and deadline count.
Cleanup requests original CC, pharmacology OFF and normal Patch/Noise/photodiode
knob control, and checks that CC binary streaming resumes.

## The remaining cases

Run these individually after the previous result has been checked:

| Case | Operation and expected response |
| --- | --- |
| 10_active_photodiode | Cover, illuminate, then cover the sensor. Positive gain is set to 1 by serial; inward light-driven input should require a more negative clamp current at fixed Vm. |
| 11_patch_command | Centre Patch, turn it about a quarter turn clockwise, then return to centre. Vcmd must increase by at least 5 mV and return within 1 mV of baseline; ideal Vm follows Vcmd. Noise and light inputs are disabled for this case. |
| 12_mode_switching | Automatic: five VC/CC cycles with stored TTX 9.2 nM and TEA 0.5 mM. Numerical VC currents must retain half Na/K conductance, and CC binary streaming must resume after each handover. |
| 13_access_stress | Automatic: 60 wall seconds of active VC at -20 mV through 5 MOhm access. All samples, current balance, settled coupled-ODE agreement, cadence and timing flags are checked. |

Substitute the case name in the command, for example:

```powershell
& $vcPython .\Firmware\tools\run_vc_integration_tests.py COM13 --case 10_active_photodiode
```

For the photodiode case, use an opaque cover for baseline and recovery, and
steady illumination for the active phase. The physical gain knob is temporarily
overridden by the test and restored at cleanup. The existing photoreceptor
adaptation remains active, so the light current need not be perfectly constant.

For the automatic cases keep all incoming cables disconnected. Noise and light
inputs are temporarily disabled by serial. The test deliberately clears drug
doses and receptor selections at setup, then applies only the specified drugs.
It does not restore a previous drug experiment. Mode switching retains the
specified doses between cycles; it does not claim preservation of HH gates,
which initialise on backend selection, or of unobserved release RNG state.

The one-minute timing case tests a settled access response. Transient accuracy
was checked separately by case 04. Model time remains 20 times slower than wall
time: 60 wall seconds represent 3,000 model ms. A timing PASS is specific to the
recorded setup, rather than a guarantee of every future input combination.

## Acceptance and troubleshooting

- Every device sample must be present; model time advances 0.1 ms per sample.
- Average cadence and complete one-second windows must be 500 Hz +/-2%.
- No diagnostic flags are allowed; flag 64 fails even if the equations agree.
  The maximum recorded loop must also be below 2,000 microseconds.
- The existing numerical limits are retained: Vm 0.05 mV; component currents
  0.01 nA; gates 0.003; current balance 0.00002 nA.
- Noise and light tests require a quiet baseline and recovery, plus a detectable
  active input and the expected compensating clamp-current response.
- Patch response limits establish direction and return, not ADC/DAC calibration.

If a test fails, retain its output folder and send it before changing timing or
model parameters. Ctrl+C requests cleanup and saves the available partial
recording. A missing dependency fails before measurement; install requirements
with the same Python executable. If COM13 is busy, close the other serial client.

You can reanalyse a saved CSV without connecting the board:

```powershell
& $vcPython .\Firmware\tools\run_vc_integration_tests.py --case 09_active_noise --analyse .\vc_integration_TIMESTAMP\09_active_noise\recording.csv
```

For an offline mode-switch CSV, this checks one recorded VC cycle only. The
top-level live report is required as evidence for the complete handover sequence
and cleanup; offline analysis cannot establish that binary streaming resumed.

## Verification and scope

The supplied analyser has 14 new native-sketch tests, including deliberate
missing-signal, wrong-sign, failed recovery, lost-dose, timing and sample faults.
The complete 84-test native suite passes. Simulated serial QA exercises all
five CLI cases, background capture, prompts, reports, plots and cleanup,
including two mode-switch cycles and a full 60-second capture. An additional
missing-input capture must fail its response check while still returning to CC
streaming. The externally paced host clock is not a physical ESP32 timing
measurement. See QA_RESULTS.md in the test pack for the verification scope.

These new integration cases have not yet been run on your board. No firmware
model or acceptance tolerance was changed. Synaptic cable routing, AMPA/GABA-A/
NMDA blockers, GVIA/release behaviour, stimulus loopback, TTL edges and analogue
calibration require subsequent bench protocols. SK/A-current extensions and
STP/LTP integration remain separate work.
