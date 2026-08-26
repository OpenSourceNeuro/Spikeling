# Extracellular recording

!!! info "Curriculum status"
    These entries are architecture specifications, not final lesson plans. They define teaching intent, logistics, outputs and scientific boundaries; release-ready settings, worksheets, notebooks and answer keys still require empirical validation.

[Return to the module catalogue](index.md)


**Family source cluster:** \[P3; P4; O2; O4; G7\]

## EXT-01 — Intracellular versus extracellular signals { #ext-01 }

| **Concept / theme**        | Extracellular waveforms are geometry-dependent field measurements, not scaled copies of membrane voltage.                                                                                                        |
|----------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Advanced undergraduate. Formal practical, workshop or modular course. Prior modules: FND-02, DAT-02.                                                                                                             |
| **Logistics**              | 45 min; 1–3; boards: 0–1; software: Spikeling extracellular GUI; Jupyter/SpikeInterface; prepared dataset: GUI-generated or prepared timestamped traces. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | GUI simulation. Stages: 6–11.                                                                                                                                                                                    |
| **Spikeling relationship** | 6 — GUI simulation workflow; 7 — Conceptual analogy; 8 — External computational comparison                                                                                                                       |

**Learning outcomes.**

- Identify and predict the principal behaviour described in extracellular waveforms are geometry-dependent field measurements, not scaled copies of membrane voltage.

- Configure or document compare ground-truth Vm with template and dv/dt extracellular modes and record Vm, source spikes and four contact traces.

- Measure, calculate or compare compare ground-truth Vm with template and dv/dt extracellular modes using an explicit operational rule.

- Interpret the result and state why forward model is reduced and µv-like; no tissue/morphology solution is implied

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Compare ground-truth Vm with template and dV/dt extracellular modes.
>
> 4\. Acquire or inspect Vm, source spikes and four contact traces.
>
> 5\. Produce aligned intra/extra figure and representation critique.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: Forward model is reduced and µV-like; no tissue/morphology solution is implied.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate compare ground-truth Vm with template and dv/dt extracellular modes. The reusable output is aligned intra/extra figure and representation critique.

**Sources / connections / priority.** Sources: \[P3; P4; O2; O4; G7\]. Natural follow-ons: EXT-02, EXT-04. Development priority: Core module. Boundary: Forward model is reduced and µV-like; no tissue/morphology solution is implied.

## EXT-02 — Electrode geometry and tetrode projection { #ext-02 }

| **Concept / theme**        | Distance and orientation change the multichannel amplitude pattern that supports unit separation.                                                                                                                |
|----------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Advanced undergraduate. Formal practical, workshop or modular course. Prior modules: EXT-01.                                                                                                                     |
| **Logistics**              | 60 min; 1–3; boards: 0–1; software: Spikeling extracellular GUI; Jupyter/SpikeInterface; prepared dataset: GUI-generated or prepared timestamped traces. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | GUI simulation. Stages: 6–11.                                                                                                                                                                                    |
| **Spikeling relationship** | 6 — GUI simulation workflow; 8 — External computational comparison                                                                                                                                               |

**Learning outcomes.**

- Identify and predict the principal behaviour described in distance and orientation change the multichannel amplitude pattern that supports unit separation.

- Configure or document move source/electrode geometry or load saved tetrode geometry and record source/contact distance, channel amplitudes.

- Measure, calculate or compare move source/electrode geometry or load saved tetrode geometry using an explicit operational rule.

- Interpret the result and state why projection law is pedagogical and clipped; not an exact volume-conductor model

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Move source/electrode geometry or load saved tetrode geometry.
>
> 4\. Acquire or inspect source/contact distance, channel amplitudes.
>
> 5\. Produce geometry-to-feature map.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: Projection law is pedagogical and clipped; not an exact volume-conductor model.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate move source/electrode geometry or load saved tetrode geometry. The reusable output is geometry-to-feature map.

**Sources / connections / priority.** Sources: \[P3; P4; O2; O4; G7\]. Natural follow-ons: EXT-05. Development priority: High-priority extension. Boundary: Projection law is pedagogical and clipped; not an exact volume-conductor model.

## EXT-03 — Recording chain: noise, hum, reference and filtering { #ext-03 }

| **Concept / theme**        | Recorded extracellular data combine signal, independent/common noise, line hum, referencing and filters.                                                                                                         |
|----------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Master’s. Formal practical, workshop or modular course. Prior modules: EXT-01, EPH-05, EPH-04.                                                                                                                   |
| **Logistics**              | 60 min; 1–3; boards: 0–1; software: Spikeling extracellular GUI; Jupyter/SpikeInterface; prepared dataset: GUI-generated or prepared timestamped traces. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | GUI simulation + analysis. Stages: 6–11.                                                                                                                                                                         |
| **Spikeling relationship** | 6 — GUI simulation workflow; 5 — Recorded-dataset analysis; 7 — Conceptual analogy                                                                                                                               |

**Learning outcomes.**

- Identify and predict the principal behaviour described in recorded extracellular data combine signal, independent/common noise, line hum, referencing and filters.

- Configure or document manipulate noise/hum/car/band settings and compare waveform/snr and record raw/processed channels, noise level, filter/reference state.

- Measure, calculate or compare manipulate noise/hum/car/band settings and compare waveform/snr using an explicit operational rule.

- Interpret the result and state why filter frequencies require a valid sample rate; real amplifier/electrode artefacts are broader

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Manipulate noise/hum/CAR/band settings and compare waveform/SNR.
>
> 4\. Acquire or inspect raw/processed channels, noise level, filter/reference state.
>
> 5\. Produce processing-chain diagram and before/after qc.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: Filter frequencies require a valid sample rate; real amplifier/electrode artefacts are broader.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate manipulate noise/hum/car/band settings and compare waveform/snr. The reusable output is processing-chain diagram and before/after qc.

**Sources / connections / priority.** Sources: \[P3; P4; O2; O4; G7\]. Natural follow-ons: EXT-04, EXT-05. Development priority: Advanced specialised module. Boundary: Filter frequencies require a valid sample rate; real amplifier/electrode artefacts are broader.

## EXT-04 — Threshold detection and waveform features { #ext-04 }

| **Concept / theme**        | Spike detection trades missed events against false detections and feeds feature extraction.                                                                                                                      |
|----------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Master’s. Formal practical, workshop or modular course. Prior modules: EXT-03, DAT-03.                                                                                                                           |
| **Logistics**              | 60 min; 1–3; boards: 0–1; software: Spikeling extracellular GUI; Jupyter/SpikeInterface; prepared dataset: GUI-generated or prepared timestamped traces. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | GUI + Jupyter. Stages: 6–11.                                                                                                                                                                                     |
| **Spikeling relationship** | 6 — GUI simulation workflow; 5 — Recorded-dataset analysis; 8 — External computational comparison                                                                                                                |

**Learning outcomes.**

- Identify and predict the principal behaviour described in spike detection trades missed events against false detections and feeds feature extraction.

- Configure or document vary threshold/refractory under controlled noise and extract peak/energy/channel features and record detections, true events, waveform features.

- Measure, calculate or compare vary threshold/refractory under controlled noise and extract peak/energy/channel features using an explicit operational rule.

- Interpret the result and state why threshold crossings are events, not automatically well-isolated units

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Vary threshold/refractory under controlled noise and extract peak/energy/channel features.
>
> 4\. Acquire or inspect detections, true events, waveform features.
>
> 5\. Produce detection roc-like table and waveform panel.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: Threshold crossings are events, not automatically well-isolated units.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate vary threshold/refractory under controlled noise and extract peak/energy/channel features. The reusable output is detection roc-like table and waveform panel.

**Sources / connections / priority.** Sources: \[P3; P4; O2; O4; G7\]. Natural follow-ons: EXT-05. Development priority: High-priority extension. Boundary: Threshold crossings are events, not automatically well-isolated units.

## EXT-05 — Clustering, spike sorting and quality metrics { #ext-05 }

| **Concept / theme**        | Tetrode features support clustering, but unit identity remains an inference with contamination and incompleteness.                                                                                               |
|----------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Master’s/doctoral methods. Formal practical, workshop or modular course. Prior modules: EXT-02, EXT-04, STA-02.                                                                                                  |
| **Logistics**              | 60 min; 1–3; boards: 0–1; software: Spikeling extracellular GUI; Jupyter/SpikeInterface; prepared dataset: GUI-generated or prepared timestamped traces. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | Prepared-dataset/Jupyter. Stages: 6–11.                                                                                                                                                                          |
| **Spikeling relationship** | 5 — Recorded-dataset analysis; 6 — GUI simulation workflow; 8 — External computational comparison                                                                                                                |

**Learning outcomes.**

- Identify and predict the principal behaviour described in tetrode features support clustering, but unit identity remains an inference with contamination and incompleteness.

- Configure or document cluster synthetic waveforms, compare with ground truth and calculate refractory/snr/quality metrics and record feature vectors, labels, true unit ids, quality metrics.

- Measure, calculate or compare cluster synthetic waveforms, compare with ground truth and calculate refractory/snr/quality metrics using an explicit operational rule.

- Interpret the result and state why ground-truth synthetic success does not guarantee performance on biological recordings; avoid treating refractory checks as proof of isolation

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Cluster synthetic waveforms, compare with ground truth and calculate refractory/SNR/quality metrics.
>
> 4\. Acquire or inspect feature vectors, labels, true unit ids, quality metrics.
>
> 5\. Produce sorting report with error trade-off and curation decision.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: Ground-truth synthetic success does not guarantee performance on biological recordings; avoid treating refractory checks as proof of isolation.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate cluster synthetic waveforms, compare with ground truth and calculate refractory/snr/quality metrics. The reusable output is sorting report with error trade-off and curation decision.

**Sources / connections / priority.** Sources: \[P3; P4; O2; O4; G7\]. Natural follow-ons: EPI-01, DAT-08. Development priority: Advanced specialised module. Boundary: Ground-truth synthetic success does not guarantee performance on biological recordings; avoid treating refractory checks as proof of isolation.
