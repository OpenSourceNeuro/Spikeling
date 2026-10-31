# Two-Spikeling synaptic voltage-clamp tests — Windows

30 October 2026. Python-only tests for the installed active VC firmware
`5c2e063` (`clock=2,gates=2,voltage=2`). Keep that firmware on COM13.
The source unit uses its usual working Izhikevich current-clamp firmware.
No firmware upload is required for either unit.

**Runner 1.1 startup fix:** extract this updated ZIP into a **new folder** and
run from that folder. Keep using the existing `.venv-vc` Python executable; it
can remain in your older `Spikeling_VC_Prototype_d245d07` folder. Do not run an
older copy of the scripts from that folder. The complete tool set is included.

This update replaces the initial line-based identity read with bounded byte
reads and a true four-second reply deadline. It drains output during startup,
sends configuration commands individually and shows each startup stage. It
changes no firmware, model parameters or numerical/timing acceptance limits.

Start with **14_synaptic_input on Synapse 1 only**. Send its results before
moving to the receptor/drug sequence. These new cases have host validation;
they still need measurements on the physical boards.

## 1. Connect the two units

Identify the units before connecting:

| Role | Unit | Setting |
| --- | --- | --- |
| POSTSYNAPTIC | Your tested COM13 unit | Python selects active voltage clamp |
| SOURCE | The second Spikeling | Normal current clamp, pharmacology off |

Power both units by USB. Only the postsynaptic unit needs a PC serial connection;
the source can use a USB power supply. If it is connected to the PC, its COM port
is separate and is not opened by this runner.

With the source quiet, connect **one 3.5 mm stereo TRS cable**:

| Cable end | Label on the board |
| --- | --- |
| SOURCE output | **Synapse Out / Axon Out** |
| POSTSYNAPTIC input | **Synapse 1 In** |

Use the labelled external jacks. A normal straight-through stereo TRS cable
carries digital spikes on the tip, analogue Vm on the ring and shared ground on
the sleeve. Do not use a mono TS cable. For this test the firmware uses received
digital spike edges, not the analogue waveform as an injected current.

On both units disconnect Current-In and all unused incoming synaptic cables.
Start with Patch centred, Noise at minimum, and photodiode gain at zero. Keep
both postsynaptic synapse knobs centred. Leave the SOURCE in its ordinary tonic
spiking CC preset, with no GUI-driven stimulation or drugs. Its centred Patch
should give no spontaneous spikes. If necessary select/reset its usual default
preset and verify this before starting. Close GUI/Serial Monitor on COM13.

## 2. Extract and run the first test

Extract the ZIP to a new folder. In PowerShell, change into the extracted folder
that contains `START_HERE_WINDOWS.md` and `Firmware`.

Reuse the Python environment from your successful earlier tests:

```powershell
$vcPython = "C:\Users\Agatrhe\Desktop\Spikeling_VC_Prototype_d245d07\.venv-vc\Scripts\python.exe"
& $vcPython .\Firmware\tools\run_vc_synapse_tests.py COM13 --case 14_synaptic_input --synapse 1
```

If that environment has moved, use its new path. If packages are missing:

```powershell
& $vcPython -m pip install -r .\Firmware\tools\requirements_active_vc.txt
```

Follow the prompts in order:

1. Keep the **SOURCE Patch centred**, with no spikes. Press Enter when ready.
   The script checks quiet input and records a baseline.
2. At the next prompt, turn the **SOURCE Patch** clockwise until it fires
   steadily at roughly **1–3 visible spikes per wall second**. Use its spike LED
   or buzzer to judge the rate. Leave it fixed and press Enter. The script records
   10 seconds. Do not adjust COM13's Patch or synapse knobs.
3. When prompted, return the **SOURCE Patch** to centre so spikes stop, then
   press Enter. The script waits for quiet input and records recovery.

Before the SOURCE prompt, runner 1.1 prints `Opening COM13`, then
`Port open. Draining startup output for 2 seconds`, configuration progress,
`Checking firmware identity (4 s deadline)` and the received firmware identity.
If no valid reply arrives, it reports a timeout instead of waiting indefinitely.
Keep the source quiet until the operator prompt appears.

The script controls postsynaptic gain, decay, receptor, drug and holding-voltage
settings. It keeps the serial reader running throughout prompts and plotting.

## 3. Expected first result

`OVERALL: PASS` requires:

- Vm held at **−70 mV** throughout the capture.
- At least five resolved AMPA events in the analysed active interval, with
  negative/inward receptor-current pulses and their predicted exponential decay.
  The first event is about −0.099 nA at the chosen test gain.
- Matching compensating clamp-current changes, with quiet baseline/recovery.
- Contiguous samples, approximately 500 Hz, no diagnostic/deadline flags,
  every measured loop below 2,000 microseconds, and resumed CC binary streaming.

The plots use **outward-positive receptor current** and **inward-positive clamp
injection**. An inward AMPA event is negative in the receptor trace; its outward
compensating injection is also negative in the clamp trace. Compare changes from
each trace's baseline. The model advances 0.1 ms per 2 ms wall tick: it runs 20
times slower than model time. The requested source rate is in ordinary wall time.

The output folder `vc_synapse_...` contains `report.json`, `recording.csv` and
`recording.png`. Keep all three. To send the evidence, zip the complete folder:

```powershell
Compress-Archive -Path .\vc_synapse_TIMESTAMP -DestinationPath .\vc_synapse_TIMESTAMP.zip
```

Replace `TIMESTAMP` with the actual folder suffix, then upload that ZIP here.
Stop after this first Synapse 1 case for review.

## 4. After Synapse 1 is verified

Stop the SOURCE first, move the cable's postsynaptic end to **Synapse 2 In**, then
repeat the basic case with `--synapse 2`. Keep the source end in Synapse Out.
Do not move the cable while the source is firing.

```powershell
& $vcPython .\Firmware\tools\run_vc_synapse_tests.py COM13 --case 14_synaptic_input --synapse 2
```

After both inputs pass, return to Synapse 1 and run each remaining case
separately, reviewing its report before the next. Each receptor/drug case records
three 12-second phases while you leave the source steadily firing. The runner
changes voltage/dose automatically; stop the source only when prompted.

| Case | Protocol | Expected teaching behaviour |
| --- | --- | --- |
| `15_nbqx` | AMPA, −70 mV; control / 0.30 µM NBQX / washout | Fast current per event falls to 50%, then recovers |
| `16_gabazine` | GABA-A, −70 mV; control / 0.90 µM gabazine / washout | Outward GABA-A current per event falls to 50%, then recovers |
| `17_ampa_reversal` | AMPA at −70, −20, +20 mV | Inward then outward currents; fitted reversal near 0 mV |
| `18_gaba_reversal` | GABA-A at −90, −70, −50 mV | Inward below −80 mV, outward above; fitted reversal near −80 mV |
| `19_nmda_apv` | AMPA + NMDA, −20 mV; control / 3.7 µM APV / washout | Slow NMDA contribution halves; fast AMPA stays unchanged |
| `20_gvia` | AMPA, −70 mV; control / 10 nM GVIA / washout | Deterministic release efficacy falls to about 56%, then recovers |

Example (only after both basic input checks pass):

```powershell
& $vcPython .\Firmware\tools\run_vc_synapse_tests.py COM13 --case 15_nbqx --synapse 1
```

The test keeps received events visible on both sides of reversal, then fits the
zero crossing. It does not accept absence of current at a single reversal voltage
as evidence that spikes arrived. Drug comparisons use amplitude per resolved
event, rather than mean current, so a modest source-rate change does not imitate
a receptor block. Bursts with resolved intervals below 100 ms are rejected;
use the recommended 1–3 Hz source rate.

## 5. Cleanup and failures

After every live case, the script requests original Izhikevich CC, pharmacology
off, passive/access defaults and normal Patch/Noise/photodiode/synapse knob
control. It clears synaptic states. It does not restore an earlier drug
experiment's settings. Keep the SOURCE Patch centred afterwards; disconnect the
synaptic cable before checking ordinary firing in the COM13 GUI.

- **No/too few events:** check the source spike LED, correct output/input jacks,
  fully seated stereo TRS cable and selected `--synapse`. Increase a very slow
  source slightly; use steady firing instead of bursts.
- **Input stays active during recovery:** centre SOURCE Patch and wait. NMDA has
  a long tail (100 model ms = 2 wall seconds decay constant). The runner allows
  up to 30 seconds for quiet input.
- **Clock/deadline FAIL:** keep the CSV and report, including an isolated pause.
  Correct-looking currents alone do not pass timing. Do not relax thresholds.
- **Interrupted with Ctrl+C:** cleanup is attempted; inspect `report.json` for
  confirmation that CC streaming resumed. If the process or USB connection was
  forcibly lost, stop the source and power-cycle the postsynaptic unit before
  ordinary operation.
- **Missing packages:** use the dependency command above with `$vcPython`, not
  another Python installation. The kit contains text-only Python sources.

Offline reanalysis, without opening COM13:

```powershell
& $vcPython .\Firmware\tools\run_vc_synapse_tests.py --case 14_synaptic_input --synapse 1 --analyse .\vc_synapse_TIMESTAMP\recording.csv
```

## Model choices and validation limits

These protocols use the existing integrated-v2 pharmacology and ideal active VC;
they add PC tests rather than new firmware physiology. Synaptic currents follow
`I = g(V − E)`, with fast conductance decay and a slow NMDA component with
voltage-dependent magnesium block. NMDA rise/decay are 4/100 model ms; magnesium
is 1 mM and its maximum gain ratio is 2. These mechanisms follow established
conductance-based teaching models. The chosen reversals, gains, decay and drug
half-effect concentrations are explicit educational settings, not a fit to one
preparation or universal pharmacological potencies. Drug application/washout here
changes availability immediately; perfusion and binding kinetics are not modelled.

GVIA uses deterministic event efficacy with N-type fraction 0.35. At the selected
half-block dose the existing release rule gives `(1 − 0.35 × 0.5)^3 = 0.561515625`.
It does not simulate or validate a measured probability of individual failures.

Incoming events are inferred from resolved fast current jumps. The runner has no
independent count of the source's output spikes: it cannot establish how many
physical spikes were missed or validate stochastic release-failure statistics.
The tests also do not establish finite-access synaptic timing, mixed-input
performance, TTL pulse calibration, analogue output calibration, STP/LTP or
hidden-state preservation through a mode switch. SK/A currents remain absent.
All new physical synaptic cases are pending your board captures.

References:

- [Spikeling hardware setup: TRS contract](https://github.com/OpenSourceNeuro/Spikeling/blob/796fbd4c33b1e3f66b02b97d49d320f9ff74a619/Documentation/docs/quickstart/hardware-setup.md).
- [Current v3.2 PCB](https://github.com/OpenSourceNeuro/Spikeling/blob/796fbd4c33b1e3f66b02b97d49d320f9ff74a619/Hardware/PCB/Spikeling%203.2/Spikeling_v3.2.kicad_pcb): J6 Synapse Out, J2/J3 Synapse 1/2 In.
- [Gerstner et al., Neuronal Dynamics, Chapter 3.1](https://neuronaldynamics.epfl.ch/online/Ch3.S1.html): conductance currents, reversal potentials, exponential synapses and NMDA magnesium block.
- [Compatible prototype source](https://github.com/OpenSourceNeuro/Spikeling/tree/5c2e063feb193c6b916331ac44cfcdf1b266e2e8/Firmware/Spikeling_V3).
- [Draft active-VC PR #17](https://github.com/OpenSourceNeuro/Spikeling/pull/17).

The ZIP's `SOURCE.json`, `MANIFEST.json` and `QA_RESULTS.md` record the exact PC
tool revision and host validation. Host simulations do not measure ESP32 timing.
