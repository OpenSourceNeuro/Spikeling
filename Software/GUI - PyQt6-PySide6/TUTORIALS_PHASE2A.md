# Spikeling Tutorials — Phase 2A

Phase 2A upgrades **only the working Phase 1 tutorial subsystem** on your current
GUI checkout. It does not change `UI_Spikeling.ui`, `main_window.py`, firmware,
scientific controllers or your experimental recordings.

## Changes

- **NI-04 reference experiment:** ten steps covering device connection, Vm,
  current clamp and physical control ownership, a baseline observation,
  two explicit predictions, hyperpolarisation, spike initiation, recording
  and an independent interpretation challenge.
- **Observable progression:** connection, Vm trace visibility, CC/VC and
  GUI-override status, stream spikes, and a new recording successfully saved
  by the existing recorder. Required conditions are *observed*, never forced.
- **Scientific integrity:** no inference that a physical potentiometer moved
  merely because Vm changed; no claim that detecting a spike establishes its
  cause. Physical actions and exceptional observations require explicit manual
  confirmation, and the UI labels them as such.
- **Contextual guidance:** the tutorial can show the appropriate parameters
  panel on user request; it never changes experimental settings itself.
- **Reasoning:** prediction, observation and explanation text, stored only in
  the user's local Qt settings. Incomplete/short responses cannot be submitted
  as finished. The app does not automatically grade scientific reasoning.
- **Resumable curriculum:** v2 tutorial progress is separate from Phase 1
  progress so users can work through the expanded tutorial from the beginning.
- **Editable design:** `UI_TutorialPanel.ui` has the new fields. Its generated
  Python companion is included; no Qt Designer compilation is necessary.

## Installation (PowerShell)

Extract this ZIP to Downloads so that this installer is at
`$env:USERPROFILE\Downloads\spikeling_tutorials_phase2a\apply_spikeling_tutorials_phase2a.py`.

In `Software\GUI - PyQt6-PySide6`:

```powershell
$patch2a = Join-Path $env:USERPROFILE 'Downloads\spikeling_tutorials_phase2a\apply_spikeling_tutorials_phase2a.py'
python $patch2a --root . --check
python $patch2a --root . --apply
python -m pytest -q tests/test_tutorials_phase1.py tests/test_tutorials_phase2a.py
python Main.py
```

The installer refuses to overwrite modified Phase 1 tutorial files. It backs
up the five replaced files under `Data/Tutorials/.phase2a_backup` and supports
`--rollback` as long as none of the installed tutorial files has been modified
since Phase 2A.

To exercise the standalone installer test as well:

```powershell
$env:SPIKELING_TUTORIAL_PHASE2A_INSTALLER = $patch2a
python -m pytest -q tests/test_tutorials_phase2a.py
```

## Manual acceptance on the physical board

1. Launch Spikeling, select **Neuron Tutorial → NI-04** and confirm the panel
   remains usable alongside the live graph.
2. Connect the device. The connection step should become confirmed without
   attempting another serial connection.
3. Change Vm trace visibility; the guide should reflect the checkbox state.
4. Open **Neuron Parameters** using **Show relevant controls**. In VC mode, or
   with GUI patch override enabled, the CC preparation step must not complete.
   Return to CC, turn off the GUI override and explicitly confirm centring the
   physical potentiometer.
5. Enter a baseline observation and prediction. Confirm that an empty response
   cannot be marked complete and that the earlier prediction is retained when
   stepping back.
6. Hyperpolarise and depolarise the neuron physically. Confirm that the guide
   never alters serial parameters. At spike initiation it may detect spikes in
   the stream; this means only that a spike was seen, **not** that the knob
   caused it. If no spike was detected, use explicit manual visual confirmation
   only if you truly observed one.
7. Start and stop a fresh CSV recording through the normal GUI. The step must
   remain incomplete while recording is active or the file cannot be saved.
8. Complete the independent challenge, exit and reopen the catalogue.
9. Repeat with a board disconnect, theme switch, a smaller window, and
   temporarily navigating to a different module. No data loss should occur.

## Testing limitations

Automated tests cover catalogue structure, UI form parity, pure observation
logic, local progress persistence, and safe check/apply/rollback behaviour.
They do **not** replace a real GUI and board acceptance test. In particular,
spike detection uses a streamed Vm threshold crossing as a *possible* source of
observable evidence, with an explicit self-report fallback.

## Known next-stage work

- More sophisticated event-based instrumentation without affecting sampling
  performance, including distinguishable hardware command acknowledgements.
- Resumable action evidence across interrupted sessions (the current release
  resumes the step, not the previous recording event).
- Translation of structured scientific content and review of keyboard focus
  with assistive technology.
- User-controlled clearing/export of locally saved tutorial reflections.
