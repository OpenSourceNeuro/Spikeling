# Current Known Issues

## Purpose

This document records confirmed defects and compatibility issues present in the
pre-refactor Spikeling GUI baseline.

Its purpose is to prevent an existing defect from later being mistaken for a
regression introduced by the refactor.

Potential architectural weaknesses and unconfirmed risks belong in:

```text
docs/architecture/technical-debt-register.md
```

## Baseline reference

- GUI baseline tag: `gui-pre-refactor-2026-08-05`
- GUI baseline commit: `b98187c`
- Baseline date: `2026-08-05`

## Status definitions

- **Confirmed**: directly supported by reproducible behaviour or unambiguous
  source evidence.
- **Confirmed code-level mismatch**: incompatible source paths are present, but
  the physical or user-visible consequence has not yet been tested.
- **Intermittent**: reproduced, but not consistently.
- **Suspected**: plausible but not sufficiently verified.
- **Historical**: previously reported but not recently retested.
- **Resolved after baseline**: present in the baseline but fixed in a later
  commit.
- **Not reproducible**: retesting did not reproduce the issue.

## Severity definitions

- **Critical**: potential data corruption, hardware risk, or complete
  application failure.
- **High**: a major workflow cannot be completed.
- **Medium**: a function may fail or require a workaround, but the application
  remains usable.
- **Low**: minor functional, usability, visual, or maintenance effect.

## Issue index

| ID | Title | Area | Severity | Status |
|---|---|---|---|---|
| GUI-BASE-001 | GUI sends unregistered `VH1` command | Serial protocol / stimulation | Medium, provisional | Confirmed code-level mismatch |

No other baseline defect has yet been formally recorded in this document.

Additional defects should be added only after they are reproduced or supported
by logs, screenshots, serial captures, recordings, or unambiguous source
evidence.

## GUI-BASE-001 — GUI sends an unregistered `VH1` command

### Summary

The baseline GUI sends the serial command:

```text
VH1
```

from a custom-stimulus path in:

```text
Software/GUI - PyQt6-PySide6/Page_Spikeling_NeuronInterface.py
```

Neither the v2.5 nor v3 firmware command registry contains a corresponding
`VH1` registration or handler.

### Status

```text
Confirmed code-level mismatch
```

The user-visible and physical effects remain unverified because no physical
board was accessed during the source audit.

### Severity

```text
Medium — provisional
```

The severity must be reassessed after hardware testing.

It may be lower if the path is unused or obsolete. It may be higher if the
control is part of a primary stimulation workflow and silently fails.

### Affected components

GUI:

```text
Software/GUI - PyQt6-PySide6/Page_Spikeling_NeuronInterface.py
```

Firmware:

```text
Firmware/Spikeling_V2.5/Serial_functions.h
Firmware/Spikeling_V3/Serial_functions.h
```

Serial transport:

```text
Software/GUI - PyQt6-PySide6/serial_manager.py
```

### Preconditions

1. Launch the baseline GUI.
2. Connect a compatible Spikeling board.
3. Open the GUI workflow containing the custom-stimulus control that sends
   `VH1`.
4. Begin serial acquisition or otherwise ensure firmware serial output can be
   observed.

### Reproduction procedure

The following procedure has not yet been completed and must be performed for
each supported hardware family:

1. Flash a known firmware commit.
2. Record the board revision and firmware commit.
3. Connect the board to the baseline GUI.
4. Start a raw serial capture where possible.
5. Activate the GUI control that sends `VH1`.
6. Observe the firmware response.
7. Observe whether the intended physical or GUI behaviour occurs.
8. Repeat the operation.
9. Disconnect and reconnect.
10. Repeat on the other firmware family.

### Expected behaviour

The GUI command should be recognised by the connected firmware and should
perform the intended custom-stimulus operation.

The command should not inject unrelated diagnostic text into the acquisition
stream.

### Observed source-level behaviour

No matching `VH1` registration or handler exists in either inspected firmware
command registry.

The firmware unknown-command handler can emit ASCII output in the form:

```text
Unknown command: VH1
```

Because firmware diagnostic output and binary sample frames share the same
serial channel, this may also affect binary-frame parsing.

The actual runtime result has not yet been observed.

### Frequency

```text
Unknown — requires hardware verification
```

At source level, the mismatch occurs whenever the corresponding GUI path sends
`VH1`.

### Evidence

Detailed source audit:

```text
docs/baseline/evidence/2026-08-05_gui-pre-refactor/
codex-firmware-compatibility-audit.md
```

Source locations:

- GUI send path:
  `Page_Spikeling_NeuronInterface.py:242`
- v2.5 command registry:
  `Firmware/Spikeling_V2.5/Serial_functions.h`
- v3 command registry:
  `Firmware/Spikeling_V3/Serial_functions.h`

Hardware evidence:

```text
Not captured
```

Serial recording:

```text
Not captured
```

Screenshot or video:

```text
Not captured
```

### Workaround

No workaround has been verified.

Possible remedies must not be applied until the intended function is
identified. Possible explanations include:

- obsolete GUI command;
- command-token typographical error;
- missing firmware registration;
- intended use of another existing command;
- abandoned GUI feature.

### Refactor relevance

The `VH1` command must not be silently removed, renamed, or redirected during
general architecture work.

Before changing it:

1. identify the control and its intended behaviour;
2. trace the complete GUI call path;
3. compare the intended behaviour with available firmware handlers;
4. reproduce the baseline result on hardware;
5. add a protocol-level regression test;
6. document any migration.

### Required resolution evidence

The issue can be marked resolved only when:

- the intended GUI behaviour is documented;
- the correct firmware command is identified;
- both relevant firmware paths are reviewed;
- an automated command-generation test exists;
- hardware behaviour is verified where available;
- binary-stream integrity is preserved;
- the resolving commit or pull request is recorded.

## Baseline observations still awaiting verification

The following items are not currently classified as confirmed issues:

- reliability of 500000-baud communication on v2.5 hardware;
- reliability of native USB communication on v3 hardware;
- recovery from ASCII text interleaved with binary frames;
- equivalence of `NEU` behaviour between v2.5 and v3;
- maximum safe length of the `NE` command;
- disconnect and reconnect behaviour;
- duplicate Qt signal connections after reconnect;
- deterministic serial-worker shutdown;
- behaviour when no hardware is connected;
- behaviour when an unavailable COM port is selected.

These belong in the baseline smoke test and technical-debt register until they
are reproduced as defects.

## Adding future issues

Each future issue should contain:

- unique ID;
- concise title;
- status;
- severity;
- affected components;
- preconditions;
- exact reproduction steps;
- expected behaviour;
- observed behaviour;
- frequency;
- evidence paths;
- workaround;
- suspected cause, clearly labelled;
- refactor relevance;
- resolution criteria.

Do not describe an architectural concern as a confirmed runtime defect without
supporting evidence.
