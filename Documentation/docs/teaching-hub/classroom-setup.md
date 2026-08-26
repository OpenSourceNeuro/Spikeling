# Prepare a class

Use this page to move from a selected curriculum module to a teachable session. The catalogue specifies audience, duration, group size, boards, equipment, software and dataset needs; it does not replace a local pilot.

!!! warning "Pilot before teaching"
    Nominal timings and activities in the curriculum catalogue are architectural specifications. Validate the complete activity on the target hardware, firmware and GUI versions before using it with students.

## 1. Select the learning route

- For a first encounter, start with [FND-01 — First contact](modules/foundations.md#fnd-01) and the operational [first experiment](../quickstart/first-experiment.md).
- For a practical class, choose from the [current practical guides](teaching-resources.md#current-practical-guides).
- For a workshop or course, use the [dependency pathways and course bundles](course-module-outlines.md).
- For an unreleased catalogue module, follow the [full module-development template](development-status.md#template-for-later-full-module-development) before treating it as a handout.

## 2. Validate each teaching station

Complete these steps on every computer and board combination that students will use:

1. Check [what you need](../quickstart/what-you-need.md).
2. Complete the [hardware setup](../quickstart/hardware-setup.md).
3. [Install and open the GUI](../quickstart/install-gui.md).
4. Run the [first experiment](../quickstart/first-experiment.md).
5. Confirm that recording and export work using the [recording guide](../user-guide/recording-and-export.md).
6. Record the board, firmware and GUI versions used for the pilot.

## 3. Apply the validation gates

Complete [EPH-04 — Sampling and timebase validation](modules/electrophysiology.md#eph-04) before interpreting latency, firing rate, interspike intervals, spectra, phase or kinetic constants.

Imaging-indicator comparisons and extracellular timing/spectral activities require the additional parameter and timestamp checks described in [Development status and validation gates](development-status.md#recommended-development-order-and-validation-gates).

## 4. Prepare the teaching package

For a release-ready module, prepare the elements required by the curriculum architecture:

- version and empirical-validation record;
- instructor preparation and pilot checks;
- student activity and observable outcomes;
- variable, unit, sample-interval and metadata specification;
- analysis notebook or a tested non-code alternative where required;
- evidence-based questions and artefact criteria;
- accessibility and differentiation variants;
- explicit interpretive limits; and
- a fallback dataset when the activity depends on acquisition.

The live documentation does not yet ship validated fallback datasets or teaching notebooks. Do not assume that a catalogue reference to prepared data means the file is already available.

## 5. Plan support during the session

Keep the [quickstart troubleshooting guide](../quickstart/troubleshooting.md) available to instructors and teaching assistants. For multi-station triage and escalation routes, see [Troubleshooting at scale](troubleshooting-at-scale.md).
