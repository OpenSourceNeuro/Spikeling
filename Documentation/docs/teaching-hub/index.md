# Spikeling Teaching Hub

The Teaching Hub brings together open resources for using Spikeling in practical neuroscience education. It is intended for university lecturers, teaching-lab coordinators, workshop instructors and educators adapting activities for their own courses.

Spikeling is an open-source hardware/software teaching platform built around a real-time Izhikevich spiking-neuron model. The hub treats it as an experimental interface for asking questions, manipulating variables, recording observations, analysing data and evaluating what a model can—and cannot—show.

!!! info "Current release status"
    The hub now includes an evidence-mapped architecture for 80 short modules, course pathways and existing practical guides. Most catalogue entries are **module specifications**, not yet validated student handouts. Pages identify this distinction explicitly so that planned resources are not mistaken for released material.

## Start here

| If you want to… | Begin with… |
|---|---|
| Prepare students and teaching stations | [Prepare a class](classroom-setup.md) |
| Run an existing practical | [Current practical guides](teaching-resources.md#current-practical-guides) |
| Choose activities by topic | [Curriculum catalogue](modules/index.md) |
| Assemble a workshop or course | [Course pathways and bundles](course-module-outlines.md) |
| Adapt or develop a module | [Development status and validation gates](development-status.md) |
| Check scientific claims and limits | [Scope, evidence and teaching limits](scope-and-evidence.md) |

## Getting started with a class

1. Confirm the [hardware and software requirements](../quickstart/what-you-need.md).
2. Complete the [hardware setup](../quickstart/hardware-setup.md) and [GUI installation](../quickstart/install-gui.md) before the session.
3. Run the [first experiment](../quickstart/first-experiment.md) on every teaching station.
4. Select a released [practical guide](teaching-resources.md#current-practical-guides) or a catalogue module appropriate to your audience.
5. For any activity that interprets latency, rate, interspike interval, spectrum, phase or kinetics, complete the [EPH-04 timing-validation gateway](modules/electrophysiology.md#eph-04) first.

## Neurophysiology practicals

The current documentation provides practical guides for:

- [excitability and threshold](../experiments/excitability-and-threshold.md);
- [adaptation and firing patterns](../experiments/adaptation-and-firing-patterns.md);
- [synaptic inputs](../experiments/synapses-and-inputs.md);
- [two-unit networks](../experiments/network-two-units.md);
- [stimulus design](../experiments/stimulus-recipes.md); and
- [patch-clamp-style investigations](../experiments/patch-clamp-style-labs.md), with explicit limits on the analogy.

The curriculum catalogue extends these topics into foundations, electrophysiology, sensory neuroscience, computational neuroscience, methodology and scientific reasoning:

- [Foundations and orientation](modules/foundations.md)
- [Neurophysiology](modules/neurophysiology.md)
- [Electrophysiology and instrumentation](modules/electrophysiology.md)
- [Synapses and integration](modules/synapses.md)
- [Sensory neuroscience](modules/sensory-neuroscience.md)
- [Networks and neural computation](modules/networks.md)

## Recording, analysis and inference

Use the [recording and export guide](../user-guide/recording-and-export.md) for the current operational workflow. The architecture then provides progressive specifications for:

- [neural-data analysis](modules/data-analysis.md);
- [statistics and uncertainty](modules/statistics.md);
- [calcium-imaging simulation](modules/calcium-imaging.md); and
- [extracellular-recording simulation](modules/extracellular-recording.md).

No current, validated teaching notebook or example dataset is shipped in the live documentation yet. The catalogue marks modules that require those resources, and the [development plan](development-status.md) records the validation work required before release.

## Experimental design and responsible interpretation

Spikeling is most useful when students follow the full experimental workflow:

**question → manipulation → observation → recording → analysis → interpretation**

The [experimental-methodology](modules/experimental-methodology.md) and [epistemology](modules/epistemology.md) families make protocol design, measurement rules, uncertainty, reproducibility and claim restraint part of the teaching activity rather than hidden instructor details.

!!! warning "Teaching scope and limits"
    Spikeling is an educational computational model and experimental interface. It is not a biological preparation, a research-grade electrophysiology recorder, a complete calcium-imaging microscope simulation or a complete biophysical extracellular forward model. Distinguish model behaviour, measurement representation and biological interpretation in every activity.

## Teaching resources and adaptation

See [Teaching resources](teaching-resources.md) for released guides, editable curriculum source links and the status of planned notebooks, datasets, worksheets and assessment material.

The curriculum is designed for adaptation. Preserve the scientific boundary notes, record the hardware/firmware/GUI versions used, and validate timing and active parameters before publishing local protocol values.
