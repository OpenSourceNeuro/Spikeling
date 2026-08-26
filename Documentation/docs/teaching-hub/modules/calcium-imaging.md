# Calcium imaging

!!! info "Curriculum status"
    These entries are architecture specifications, not final lesson plans. They define teaching intent, logistics, outputs and scientific boundaries; release-ready settings, worksheets, notebooks and answer keys still require empirical validation.

[Return to the module catalogue](index.md)


**Family source cluster:** \[P2; O3; T2 Ch.6; G6\]

## IMG-01 — Spikes to calcium to fluorescence { #img-01 }

| **Concept / theme**        | The imaging GUI is a forward model from known electrical events to indirect fluorescence observations.                                                                                  |
|----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Undergraduate. Formal practical, workshop or modular course. Prior modules: DAT-03 helpful.                                                                                             |
| **Logistics**              | 45 min; 1–3; boards: 0–1; software: Spikeling imaging GUI; Jupyter; prepared dataset: GUI-generated or prepared imaging traces. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | GUI simulation workflow. Stages: 6–11.                                                                                                                                                  |
| **Spikeling relationship** | 6 — GUI simulation workflow; 2 — Direct board + GUI; 7 — Conceptual analogy                                                                                                             |

**Learning outcomes.**

- Identify and predict the principal behaviour described in the imaging GUI is a forward model from known electrical events to indirect fluorescence observations.

- Configure or document drive the pipeline from board/emulator and identify each transformation stage and record Vm, detected spikes, calcium and fluorescence.

- Measure, calculate or compare drive the pipeline from board/emulator and identify each transformation stage using an explicit operational rule.

- Interpret the result and state why synthetic calcium/fluorescence does not validate a real indicator or optical system

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Drive the pipeline from board/emulator and identify each transformation stage.
>
> 4\. Acquire or inspect Vm, detected spikes, calcium and fluorescence.
>
> 5\. Produce forward-model diagram and aligned traces.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: Synthetic calcium/fluorescence does not validate a real indicator or optical system.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate drive the pipeline from board/emulator and identify each transformation stage. The reusable output is forward-model diagram and aligned traces.

**Sources / connections / priority.** Sources: \[P2; O3; T2 Ch.6; G6\]. Natural follow-ons: IMG-02, IMG-03. Development priority: Core module. Boundary: Synthetic calcium/fluorescence does not validate a real indicator or optical system.

## IMG-02 — Frame rate and temporal filtering { #img-02 }

| **Concept / theme**        | Camera sampling and indicator kinetics blur and discretise fast electrical events.                                                                                                      |
|----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Advanced undergraduate. Formal practical, workshop or modular course. Prior modules: IMG-01, EPH-04.                                                                                    |
| **Logistics**              | 60 min; 1–3; boards: 0–1; software: Spikeling imaging GUI; Jupyter; prepared dataset: GUI-generated or prepared imaging traces. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | GUI + Jupyter. Stages: 6–11.                                                                                                                                                            |
| **Spikeling relationship** | 6 — GUI simulation workflow; 5 — Recorded-dataset analysis; 8 — External computational comparison                                                                                       |

**Learning outcomes.**

- Identify and predict the principal behaviour described in camera sampling and indicator kinetics blur and discretise fast electrical events.

- Configure or document vary frame rate and kinetic constants for the same ground-truth spike train and record frame times, spike times, ca/f traces.

- Measure, calculate or compare vary frame rate and kinetic constants for the same ground-truth spike train using an explicit operational rule.

- Interpret the result and state why timing fallback and active parameter values require validation

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Vary frame rate and kinetic constants for the same ground-truth spike train.
>
> 4\. Acquire or inspect frame times, spike times, ca/f traces.
>
> 5\. Produce temporal-resolution comparison and missed/merged-event count.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: Timing fallback and active parameter values require validation.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate vary frame rate and kinetic constants for the same ground-truth spike train. The reusable output is temporal-resolution comparison and missed/merged-event count.

**Sources / connections / priority.** Sources: \[P2; O3; T2 Ch.6; G6\]. Natural follow-ons: IMG-05. Development priority: High-priority extension. Boundary: Timing fallback and active parameter values require validation.

## IMG-03 — Baseline, ΔF/F, noise and bleaching { #img-03 }

| **Concept / theme**        | Fluorescence normalisation and background processes can alter apparent response size.                                                                                                   |
|----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Advanced undergraduate. Formal practical, workshop or modular course. Prior modules: IMG-01, DAT-02.                                                                                    |
| **Logistics**              | 60 min; 1–3; boards: 0–1; software: Spikeling imaging GUI; Jupyter; prepared dataset: GUI-generated or prepared imaging traces. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | GUI simulation + analysis. Stages: 6–11.                                                                                                                                                |
| **Spikeling relationship** | 6 — GUI simulation workflow; 5 — Recorded-dataset analysis                                                                                                                              |

**Learning outcomes.**

- Identify and predict the principal behaviour described in fluorescence normalisation and background processes can alter apparent response size.

- Configure or document manipulate baseline, pmt/noise and bleaching settings; calculate δf/f and record f0, f, δf/f, noise and bleach factor.

- Measure, calculate or compare manipulate baseline, pmt/noise and bleaching settings; calculate δf/f using an explicit operational rule.

- Interpret the result and state why δf/f depends on baseline definition; simulated bleaching/noise are didactic models

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Manipulate baseline, PMT/noise and bleaching settings; calculate ΔF/F.
>
> 4\. Acquire or inspect f0, f, δf/f, noise and bleach factor.
>
> 5\. Produce normalisation/qc figure and artefact log.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: ΔF/F depends on baseline definition; simulated bleaching/noise are didactic models.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate manipulate baseline, pmt/noise and bleaching settings; calculate δf/f. The reusable output is normalisation/qc figure and artefact log.

**Sources / connections / priority.** Sources: \[P2; O3; T2 Ch.6; G6\]. Natural follow-ons: IMG-04, IMG-05. Development priority: High-priority extension. Boundary: ΔF/F depends on baseline definition; simulated bleaching/noise are didactic models.

## IMG-04 — Indicator kinetics, affinity and saturation { #img-04 }

| **Concept / theme**        | Indicator properties trade temporal response, sensitivity and dynamic range.                                                                                                            |
|----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Master’s. Formal practical, workshop or modular course. Prior modules: IMG-02, IMG-03.                                                                                                  |
| **Logistics**              | 60 min; 1–3; boards: 0–1; software: Spikeling imaging GUI; Jupyter; prepared dataset: GUI-generated or prepared imaging traces. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | GUI simulation. Stages: 6–11.                                                                                                                                                           |
| **Spikeling relationship** | 6 — GUI simulation workflow; 8 — External computational comparison                                                                                                                      |

**Learning outcomes.**

- Identify and predict the principal behaviour described in indicator properties trade temporal response, sensitivity and dynamic range.

- Configure or document compare selected indicator presets or parameter sets under identical spikes and record kd, hill coefficient, rise/decay, df/fmax.

- Measure, calculate or compare compare selected indicator presets or parameter sets under identical spikes using an explicit operational rule.

- Interpret the result and state why verify active GUI parameters; preset values are model assumptions, not calibration of a physical indicator

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Compare selected indicator presets or parameter sets under identical spikes.
>
> 4\. Acquire or inspect kd, hill coefficient, rise/decay, df/fmax.
>
> 5\. Produce indicator comparison matrix.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: Verify active GUI parameters; preset values are model assumptions, not calibration of a physical indicator.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate compare selected indicator presets or parameter sets under identical spikes. The reusable output is indicator comparison matrix.

**Sources / connections / priority.** Sources: \[P2; O3; T2 Ch.6; G6\]. Natural follow-ons: IMG-05. Development priority: Advanced specialised module. Boundary: Verify active GUI parameters; preset values are model assumptions, not calibration of a physical indicator.

## IMG-05 — ROI, neuropil and spike inference against ground truth { #img-05 }

| **Concept / theme**        | Imaging analysis estimates cellular signals and hidden spikes from indirect noisy fluorescence.                                                                                         |
|----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Master’s/doctoral methods. Formal practical, workshop or modular course. Prior modules: IMG-03, DAT-03, STA-02.                                                                         |
| **Logistics**              | 60 min; 1–3; boards: 0–1; software: Spikeling imaging GUI; Jupyter; prepared dataset: GUI-generated or prepared imaging traces. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | Prepared-dataset/Jupyter. Stages: 6–11.                                                                                                                                                 |
| **Spikeling relationship** | 5 — Recorded-dataset analysis; 6 — GUI simulation workflow; 8 — External computational comparison                                                                                       |

**Learning outcomes.**

- Identify and predict the principal behaviour described in imaging analysis estimates cellular signals and hidden spikes from indirect noisy fluorescence.

- Configure or document use prepared roi/neuropil traces or simplified synthetic data; deconvolve and compare with known spikes and record f, fneu, corrected f, inferred events, true events.

- Measure, calculate or compare use prepared roi/neuropil traces or simplified synthetic data; deconvolve and compare with known spikes using an explicit operational rule.

- Interpret the result and state why spikeling GUI does not generate full movies/motion; roi/neuropil work needs prepared data and inference cannot recover exact spike counts reliably

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Use prepared ROI/neuropil traces or simplified synthetic data; deconvolve and compare with known spikes.
>
> 4\. Acquire or inspect f, fneu, corrected f, inferred events, true events.
>
> 5\. Produce inference performance report and uncertainty statement.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: Spikeling GUI does not generate full movies/motion; ROI/neuropil work needs prepared data and inference cannot recover exact spike counts reliably.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate use prepared roi/neuropil traces or simplified synthetic data; deconvolve and compare with known spikes. The reusable output is inference performance report and uncertainty statement.

**Sources / connections / priority.** Sources: \[P2; O3; T2 Ch.6; G6\]. Natural follow-ons: EPI-01, EXT-05. Development priority: Advanced specialised module. Boundary: Spikeling GUI does not generate full movies/motion; ROI/neuropil work needs prepared data and inference cannot recover exact spike counts reliably.
