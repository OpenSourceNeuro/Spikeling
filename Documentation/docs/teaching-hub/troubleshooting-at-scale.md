# Troubleshooting at scale

This page routes instructors and teaching assistants to the current operational documentation and curriculum validation checks. It does not duplicate device-specific troubleshooting instructions.

## Fast triage route

1. **Confirm the affected scope.** Determine whether the problem affects one station, one board, one computer image or the whole class.
2. **Return to a known baseline.** Run the operational checks in [Quickstart troubleshooting](../quickstart/troubleshooting.md).
3. **Check the relevant workflow.** Use the [hardware setup](../quickstart/hardware-setup.md), [GUI installation](../quickstart/install-gui.md), [controls and I/O](../user-guide/controls-and-io.md), or [recording and export](../user-guide/recording-and-export.md) page as appropriate.
4. **Protect the scientific result.** If timing, parameters, recording metadata or board-to-board behaviour cannot be validated, do not continue to quantitative interpretation.
5. **Record the failure.** Note the hardware, firmware and GUI versions, settings, expected behaviour, observed behaviour and whether the fault follows the board, cable or computer.

## Curriculum-specific stop conditions

Pause or adapt the activity when:

- the EPH-04 timing gateway has not been completed for a time-derived measure;
- an imaging preset's active parameters have not been checked;
- a multi-board activity relies on unmeasured delays;
- an extracellular activity relies on unvalidated timestamps or spectral scales; or
- a required fallback dataset or notebook is referenced by the specification but has not yet been released.

These conditions are documented in [Development status and validation gates](development-status.md).

## Escalation

If the operational guides do not resolve a reproducible problem, search or open an issue in the [Spikeling GitHub repository](https://github.com/OpenSourceNeuro/Spikeling/issues). Include version information and a minimal reproduction; do not include student-identifiable data.
