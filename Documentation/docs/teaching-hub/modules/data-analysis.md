# Neural-data analysis

!!! info "Curriculum status"
    These entries are architecture specifications, not final lesson plans. They define teaching intent, logistics, outputs and scientific boundaries; release-ready settings, worksheets, notebooks and answer keys still require empirical validation.

[Return to the module catalogue](index.md)


**Family source cluster:** \[T5 Chs.1–4; T6 Chs.7,10–11; O1; O5; G4, G9\]

## DAT-01 — Import, data structure and metadata { #dat-01 }

| **Concept / theme**        | A recording is usable only when columns, units, timebase, conditions and provenance are explicit.                                                                                               |
|----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Undergraduate. Formal practical, workshop or modular course. Prior modules: FND-04, EPH-04.                                                                                                     |
| **Logistics**              | 45 min; 1–2 per computer; boards: 0–1; software: Jupyter; GUI for acquisition/QC; prepared dataset: Yes: generated earlier or prepared. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | Jupyter analysis. Stages: 6–12.                                                                                                                                                                 |
| **Spikeling relationship** | 5 — Recorded-dataset analysis; 3 — Hybrid board + Jupyter                                                                                                                                       |

**Learning outcomes.**

- Identify and predict the principal behaviour described in a recording is usable only when columns, units, timebase, conditions and provenance are explicit.

- Configure or document load csv, inspect schema and construct a metadata dictionary and record columns, dtypes, missing values, dt and condition labels.

- Measure, calculate or compare load csv, inspect schema and construct a metadata dictionary using an explicit operational rule.

- Interpret the result and state why do not infer missing units or sample interval from column names alone

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Load CSV, inspect schema and construct a metadata dictionary.
>
> 4\. Acquire or inspect columns, dtypes, missing values, dt and condition labels.
>
> 5\. Produce validated data object and metadata record.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: Do not infer missing units or sample interval from column names alone.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate load csv, inspect schema and construct a metadata dictionary. The reusable output is validated data object and metadata record.

**Sources / connections / priority.** Sources: \[T5 Chs.1–4; T6 Chs.7,10–11; O1; O5; G4, G9\]. Natural follow-ons: DAT-02, MET-06. Development priority: Core module. Boundary: Do not infer missing units or sample interval from column names alone.

## DAT-02 — Plotting and quality control { #dat-02 }

| **Concept / theme**        | Raw visualisation should precede feature extraction and statistical testing.                                                                                                                    |
|----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Undergraduate. Formal practical, workshop or modular course. Prior modules: DAT-01.                                                                                                             |
| **Logistics**              | 45 min; 1–2 per computer; boards: 0–1; software: Jupyter; GUI for acquisition/QC; prepared dataset: Yes: generated earlier or prepared. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | Jupyter analysis. Stages: 6–12.                                                                                                                                                                 |
| **Spikeling relationship** | 5 — Recorded-dataset analysis; 3 — Hybrid board + Jupyter                                                                                                                                       |

**Learning outcomes.**

- Identify and predict the principal behaviour described in raw visualisation should precede feature extraction and statistical testing.

- Configure or document plot aligned channels, inspect baseline, clipping, discontinuities and trigger consistency and record Vm, current, stimulus, synaptic channels, trigger.

- Measure, calculate or compare plot aligned channels, inspect baseline, clipping, discontinuities and trigger consistency using an explicit operational rule.

- Interpret the result and state why a visually plausible trace can still have timing or metadata errors

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Plot aligned channels, inspect baseline, clipping, discontinuities and trigger consistency.
>
> 4\. Acquire or inspect Vm, current, stimulus, synaptic channels, trigger.
>
> 5\. Produce qc figure and accept/reject/flag log.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: A visually plausible trace can still have timing or metadata errors.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate plot aligned channels, inspect baseline, clipping, discontinuities and trigger consistency. The reusable output is qc figure and accept/reject/flag log.

**Sources / connections / priority.** Sources: \[T5 Chs.1–4; T6 Chs.7,10–11; O1; O5; G4, G9\]. Natural follow-ons: DAT-03, EPH-06, MET-04. Development priority: Core module. Boundary: A visually plausible trace can still have timing or metadata errors.

## DAT-03 — Spike detection and validation { #dat-03 }

| **Concept / theme**        | Detection is an operational algorithm whose errors depend on threshold, noise and refractory settings.                                                                                          |
|----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Undergraduate. Formal practical, workshop or modular course. Prior modules: DAT-02, EPH-05.                                                                                                     |
| **Logistics**              | 60 min; 1–2 per computer; boards: 0–1; software: Jupyter; GUI for acquisition/QC; prepared dataset: Yes: generated earlier or prepared. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | Jupyter analysis. Stages: 6–12.                                                                                                                                                                 |
| **Spikeling relationship** | 5 — Recorded-dataset analysis; 3 — Hybrid board + Jupyter; 6 — GUI simulation workflow                                                                                                          |

**Learning outcomes.**

- Identify and predict the principal behaviour described in detection is an operational algorithm whose errors depend on threshold, noise and refractory settings.

- Configure or document implement upward-crossing or peak detection and compare against known/synthetic events and record detected times, threshold, false positives/negatives.

- Measure, calculate or compare implement upward-crossing or peak detection and compare against known/synthetic events using an explicit operational rule.

- Interpret the result and state why detected events are algorithm outputs; retain uncertainty and ground-truth checks where available

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Implement upward-crossing or peak detection and compare against known/synthetic events.
>
> 4\. Acquire or inspect detected times, threshold, false positives/negatives.
>
> 5\. Produce detection performance table and selected parameters.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: Detected events are algorithm outputs; retain uncertainty and ground-truth checks where available.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate implement upward-crossing or peak detection and compare against known/synthetic events. The reusable output is detection performance table and selected parameters.

**Sources / connections / priority.** Sources: \[T5 Chs.1–4; T6 Chs.7,10–11; O1; O5; G4, G9\]. Natural follow-ons: DAT-04, IMG-05, EXT-04. Development priority: Core module. Boundary: Detected events are algorithm outputs; retain uncertainty and ground-truth checks where available.

## DAT-04 — Firing rate and interspike intervals { #dat-04 }

| **Concept / theme**        | Spike trains can be summarised by counts, rates and interval distributions at different timescales.                                                                                             |
|----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Undergraduate. Formal practical, workshop or modular course. Prior modules: DAT-03, EPH-04.                                                                                                     |
| **Logistics**              | 60 min; 1–2 per computer; boards: 0–1; software: Jupyter; GUI for acquisition/QC; prepared dataset: Yes: generated earlier or prepared. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | Jupyter analysis. Stages: 6–12.                                                                                                                                                                 |
| **Spikeling relationship** | 5 — Recorded-dataset analysis; 3 — Hybrid board + Jupyter                                                                                                                                       |

**Learning outcomes.**

- Identify and predict the principal behaviour described in spike trains can be summarised by counts, rates and interval distributions at different timescales.

- Configure or document compute trial rate, instantaneous/filtered rate and isis and record spike times, window/kernel, rate and isi.

- Measure, calculate or compare compute trial rate, instantaneous/filtered rate and isis using an explicit operational rule.

- Interpret the result and state why rates depend on estimator/window; validated time units are mandatory

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Compute trial rate, instantaneous/filtered rate and ISIs.
>
> 4\. Acquire or inspect spike times, window/kernel, rate and isi.
>
> 5\. Produce rate panels and isi distribution.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: Rates depend on estimator/window; validated time units are mandatory.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate compute trial rate, instantaneous/filtered rate and isis. The reusable output is rate panels and isi distribution.

**Sources / connections / priority.** Sources: \[T5 Chs.1–4; T6 Chs.7,10–11; O1; O5; G4, G9\]. Natural follow-ons: DAT-05, STA-01. Development priority: Core module. Boundary: Rates depend on estimator/window; validated time units are mandatory.

## DAT-05 — Latency, adaptation and burst features { #dat-05 }

| **Concept / theme**        | Feature extraction turns qualitative patterns into reproducible operational measurements.                                                                                                       |
|----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Advanced undergraduate. Formal practical, workshop or modular course. Prior modules: DAT-03, DAT-04.                                                                                            |
| **Logistics**              | 60 min; 1–2 per computer; boards: 0–1; software: Jupyter; GUI for acquisition/QC; prepared dataset: Yes: generated earlier or prepared. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | Jupyter analysis. Stages: 6–12.                                                                                                                                                                 |
| **Spikeling relationship** | 5 — Recorded-dataset analysis; 3 — Hybrid board + Jupyter                                                                                                                                       |

**Learning outcomes.**

- Identify and predict the principal behaviour described in feature extraction turns qualitative patterns into reproducible operational measurements.

- Configure or document calculate first-spike latency, adaptation indices and burst criteria and record spike times, stimulus onset, burst thresholds.

- Measure, calculate or compare calculate first-spike latency, adaptation indices and burst criteria using an explicit operational rule.

- Interpret the result and state why feature thresholds must be justified and sensitivity-checked

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Calculate first-spike latency, adaptation indices and burst criteria.
>
> 4\. Acquire or inspect spike times, stimulus onset, burst thresholds.
>
> 5\. Produce feature table with definitions.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: Feature thresholds must be justified and sensitivity-checked.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate calculate first-spike latency, adaptation indices and burst criteria. The reusable output is feature table with definitions.

**Sources / connections / priority.** Sources: \[T5 Chs.1–4; T6 Chs.7,10–11; O1; O5; G4, G9\]. Natural follow-ons: CMP-03, STA-03. Development priority: High-priority extension. Boundary: Feature thresholds must be justified and sensitivity-checked.

## DAT-06 — Trial alignment, rasters and PSTHs { #dat-06 }

| **Concept / theme**        | Repeated trials reveal response timing, reliability and condition-dependent structure.                                                                                                          |
|----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Advanced undergraduate. Formal practical, workshop or modular course. Prior modules: DAT-01, DAT-03, EPH-04.                                                                                    |
| **Logistics**              | 60 min; 1–2 per computer; boards: 0–1; software: Jupyter; GUI for acquisition/QC; prepared dataset: Yes: generated earlier or prepared. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | Jupyter analysis. Stages: 6–12.                                                                                                                                                                 |
| **Spikeling relationship** | 5 — Recorded-dataset analysis; 3 — Hybrid board + Jupyter                                                                                                                                       |

**Learning outcomes.**

- Identify and predict the principal behaviour described in repeated trials reveal response timing, reliability and condition-dependent structure.

- Configure or document align by trigger, create rasters, averages and psths and record trigger times, spike times, trial labels.

- Measure, calculate or compare align by trigger, create rasters, averages and psths using an explicit operational rule.

- Interpret the result and state why trigger alignment and sample timing must be validated; psth bin width changes interpretation

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Align by trigger, create rasters, averages and PSTHs.
>
> 4\. Acquire or inspect trigger times, spike times, trial labels.
>
> 5\. Produce raster/psth figure and trial-exclusion log.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: Trigger alignment and sample timing must be validated; PSTH bin width changes interpretation.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate align by trigger, create rasters, averages and psths. The reusable output is raster/psth figure and trial-exclusion log.

**Sources / connections / priority.** Sources: \[T5 Chs.1–4; T6 Chs.7,10–11; O1; O5; G4, G9\]. Natural follow-ons: SEN-05, STA-03. Development priority: High-priority extension. Boundary: Trigger alignment and sample timing must be validated; PSTH bin width changes interpretation.

## DAT-07 — Correlation, cross-correlation, phase and synchrony { #dat-07 }

| **Concept / theme**        | Relationships between signals require lag-aware measures and controls for common drive.                                                                                                         |
|----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Master’s. Formal practical, workshop or modular course. Prior modules: DAT-04, NET-06, EPH-04.                                                                                                  |
| **Logistics**              | 60 min; 1–2 per computer; boards: 0–1; software: Jupyter; GUI for acquisition/QC; prepared dataset: Yes: generated earlier or prepared. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | Jupyter analysis. Stages: 6–12.                                                                                                                                                                 |
| **Spikeling relationship** | 5 — Recorded-dataset analysis; 3 — Hybrid board + Jupyter; 4 — Multi-board implementation; 8 — External computational comparison                                                                |

**Learning outcomes.**

- Identify and predict the principal behaviour described in relationships between signals require lag-aware measures and controls for common drive.

- Configure or document analyse paired/multi-board traces with correlation, cross-correlation or phase metrics and record two or more time series/spike trains, lags, phase.

- Measure, calculate or compare analyse paired/multi-board traces with correlation, cross-correlation or phase metrics using an explicit operational rule.

- Interpret the result and state why correlation and synchrony do not establish direct connectivity or causation

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Analyse paired/multi-board traces with correlation, cross-correlation or phase metrics.
>
> 4\. Acquire or inspect two or more time series/spike trains, lags, phase.
>
> 5\. Produce relationship plot with surrogate/control comparison.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: Correlation and synchrony do not establish direct connectivity or causation.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate analyse paired/multi-board traces with correlation, cross-correlation or phase metrics. The reusable output is relationship plot with surrogate/control comparison.

**Sources / connections / priority.** Sources: \[T5 Chs.1–4; T6 Chs.7,10–11; O1; O5; G4, G9\]. Natural follow-ons: STA-06, EPI-03. Development priority: Advanced specialised module. Boundary: Correlation and synchrony do not establish direct connectivity or causation.

## DAT-08 — Encoding, decoding and reproducible analysis pipeline { #dat-08 }

| **Concept / theme**        | A complete notebook can predict stimulus condition while documenting preprocessing and validation.                                                                                              |
|----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Master’s. Formal practical, workshop or modular course. Prior modules: DAT-05 or DAT-06, STA-02.                                                                                                |
| **Logistics**              | 60 min; 1–2 per computer; boards: 0–1; software: Jupyter; GUI for acquisition/QC; prepared dataset: Yes: generated earlier or prepared. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | Jupyter analysis. Stages: 6–12.                                                                                                                                                                 |
| **Spikeling relationship** | 5 — Recorded-dataset analysis; 8 — External computational comparison                                                                                                                            |

**Learning outcomes.**

- Identify and predict the principal behaviour described in a complete notebook can predict stimulus condition while documenting preprocessing and validation.

- Configure or document build a simple classifier/regression model with train/test separation and record features, labels, predictions, cross-validation metrics.

- Measure, calculate or compare build a simple classifier/regression model with train/test separation using an explicit operational rule.

- Interpret the result and state why performance can reflect confounds, leakage or repeated samples; biological coding claims require restraint

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Build a simple classifier/regression model with train/test separation.
>
> 4\. Acquire or inspect features, labels, predictions, cross-validation metrics.
>
> 5\. Produce re-runnable notebook and model card.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: Performance can reflect confounds, leakage or repeated samples; biological coding claims require restraint.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate build a simple classifier/regression model with train/test separation. The reusable output is re-runnable notebook and model card.

**Sources / connections / priority.** Sources: \[T5 Chs.1–4; T6 Chs.7,10–11; O1; O5; G4, G9\]. Natural follow-ons: MET-06, EPI-03. Development priority: Advanced specialised module. Boundary: Performance can reflect confounds, leakage or repeated samples; biological coding claims require restraint.
