# Statistics

!!! info "Curriculum status"
    These entries are architecture specifications, not final lesson plans. They define teaching intent, logistics, outputs and scientific boundaries; release-ready settings, worksheets, notebooks and answer keys still require empirical validation.

[Return to the module catalogue](index.md)


**Family source cluster:** \[O1 Statistics/Model Fitting; R4; R5; O6\]

## STA-01 — Distributions, variability and experimental units { #sta-01 }

| **Concept / theme**        | Variation should be displayed at the level of trials, boards and sessions, with the experimental unit stated.                                     |
|----------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Undergraduate. Formal practical, workshop or modular course. Prior modules: DAT-01, DAT-02.                                                       |
| **Logistics**              | 45 min; 1–3; boards: 0; software: Jupyter; prepared dataset: Yes: reused module datasets. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | Jupyter statistics. Stages: 8–12.                                                                                                                 |
| **Spikeling relationship** | 5 — Recorded-dataset analysis                                                                                                                     |

**Learning outcomes.**

- Identify and predict the principal behaviour described in variation should be displayed at the level of trials, boards and sessions, with the experimental unit stated.

- Configure or document plot distributions and decompose within/between-session variability and record repeated measurements, unit/session ids.

- Measure, calculate or compare plot distributions and decompose within/between-session variability using an explicit operational rule.

- Interpret the result and state why repeated samples from one board are not automatically independent biological replicates

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Plot distributions and decompose within/between-session variability.
>
> 4\. Acquire or inspect repeated measurements, unit/session ids.
>
> 5\. Produce distribution figure and experimental-unit statement.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: Repeated samples from one board are not automatically independent biological replicates.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate plot distributions and decompose within/between-session variability. The reusable output is distribution figure and experimental-unit statement.

**Sources / connections / priority.** Sources: \[O1 Statistics/Model Fitting; R4; R5; O6\]. Natural follow-ons: STA-02, STA-03. Development priority: Core module. Boundary: Repeated samples from one board are not automatically independent biological replicates.

## STA-02 — Confidence intervals and bootstrap uncertainty { #sta-02 }

| **Concept / theme**        | Point estimates require interval estimates and assumptions about resampling units.                                                                |
|----------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Undergraduate. Formal practical, workshop or modular course. Prior modules: STA-01.                                                               |
| **Logistics**              | 60 min; 1–3; boards: 0; software: Jupyter; prepared dataset: Yes: reused module datasets. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | Jupyter statistics. Stages: 8–12.                                                                                                                 |
| **Spikeling relationship** | 5 — Recorded-dataset analysis                                                                                                                     |

**Learning outcomes.**

- Identify and predict the principal behaviour described in point estimates require interval estimates and assumptions about resampling units.

- Configure or document bootstrap a threshold, rate or latency while respecting pairing/session structure and record estimate, resampling unit, interval.

- Measure, calculate or compare bootstrap a threshold, rate or latency while respecting pairing/session structure using an explicit operational rule.

- Interpret the result and state why intervals quantify sampling uncertainty under a model; they do not include all calibration/model uncertainty

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Bootstrap a threshold, rate or latency while respecting pairing/session structure.
>
> 4\. Acquire or inspect estimate, resampling unit, interval.
>
> 5\. Produce estimate plot with confidence interval and method note.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: Intervals quantify sampling uncertainty under a model; they do not include all calibration/model uncertainty.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate bootstrap a threshold, rate or latency while respecting pairing/session structure. The reusable output is estimate plot with confidence interval and method note.

**Sources / connections / priority.** Sources: \[O1 Statistics/Model Fitting; R4; R5; O6\]. Natural follow-ons: STA-03, CMP-09. Development priority: Core module. Boundary: Intervals quantify sampling uncertainty under a model; they do not include all calibration/model uncertainty.

## STA-03 — Paired comparisons and effect sizes { #sta-03 }

| **Concept / theme**        | Within-board/within-session comparisons can increase precision when pairing is preserved.                                                         |
|----------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Undergraduate. Formal practical, workshop or modular course. Prior modules: STA-01, STA-02.                                                       |
| **Logistics**              | 60 min; 1–3; boards: 0; software: Jupyter; prepared dataset: Yes: reused module datasets. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | Jupyter statistics. Stages: 8–12.                                                                                                                 |
| **Spikeling relationship** | 5 — Recorded-dataset analysis                                                                                                                     |

**Learning outcomes.**

- Identify and predict the principal behaviour described in within-board/within-session comparisons can increase precision when pairing is preserved.

- Configure or document compare two conditions using paired differences, raw effect size and interval and record matched outcomes and condition labels.

- Measure, calculate or compare compare two conditions using paired differences, raw effect size and interval using an explicit operational rule.

- Interpret the result and state why pairing must reflect design, not convenience; statistical significance is not biological importance

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Compare two conditions using paired differences, raw effect size and interval.
>
> 4\. Acquire or inspect matched outcomes and condition labels.
>
> 5\. Produce paired plot, effect estimate and interval.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: Pairing must reflect design, not convenience; statistical significance is not biological importance.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate compare two conditions using paired differences, raw effect size and interval. The reusable output is paired plot, effect estimate and interval.

**Sources / connections / priority.** Sources: \[O1 Statistics/Model Fitting; R4; R5; O6\]. Natural follow-ons: STA-05, MET-03. Development priority: High-priority extension. Boundary: Pairing must reflect design, not convenience; statistical significance is not biological importance.

## STA-04 — Independent groups and non-parametric comparisons { #sta-04 }

| **Concept / theme**        | Independent-group inference depends on genuine independent units and distributional assumptions.                                                  |
|----------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Advanced undergraduate. Formal practical, workshop or modular course. Prior modules: STA-01, STA-02.                                              |
| **Logistics**              | 60 min; 1–3; boards: 0; software: Jupyter; prepared dataset: Yes: reused module datasets. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | Jupyter statistics. Stages: 8–12.                                                                                                                 |
| **Spikeling relationship** | 5 — Recorded-dataset analysis                                                                                                                     |

**Learning outcomes.**

- Identify and predict the principal behaviour described in independent-group inference depends on genuine independent units and distributional assumptions.

- Configure or document compare board/session groups with robust visualisation and parametric/non-parametric alternatives and record independent outcomes and group ids.

- Measure, calculate or compare compare board/session groups with robust visualisation and parametric/non-parametric alternatives using an explicit operational rule.

- Interpret the result and state why small numbers of boards limit generalisation; do not pseudo-replicate trials

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Compare board/session groups with robust visualisation and parametric/non-parametric alternatives.
>
> 4\. Acquire or inspect independent outcomes and group ids.
>
> 5\. Produce group effect estimate, interval and assumption check.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: Small numbers of boards limit generalisation; do not pseudo-replicate trials.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate compare board/session groups with robust visualisation and parametric/non-parametric alternatives. The reusable output is group effect estimate, interval and assumption check.

**Sources / connections / priority.** Sources: \[O1 Statistics/Model Fitting; R4; R5; O6\]. Natural follow-ons: STA-06. Development priority: Advanced specialised module. Boundary: Small numbers of boards limit generalisation; do not pseudo-replicate trials.

## STA-05 — Regression and repeated-measures designs { #sta-05 }

| **Concept / theme**        | Continuous predictors and repeated observations are better represented by regression or multilevel structures than many pairwise tests.           |
|----------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Master’s. Formal practical, workshop or modular course. Prior modules: STA-02, NPH-04 or SEN-02.                                                  |
| **Logistics**              | 60 min; 1–3; boards: 0; software: Jupyter; prepared dataset: Yes: reused module datasets. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | Jupyter statistics. Stages: 8–12.                                                                                                                 |
| **Spikeling relationship** | 5 — Recorded-dataset analysis; 8 — External computational comparison                                                                              |

**Learning outcomes.**

- Identify and predict the principal behaviour described in continuous predictors and repeated observations are better represented by regression or multilevel structures than many pairwise tests.

- Configure or document fit input–response or adaptation models with session/board structure and record predictors, outcome, repeated-unit ids.

- Measure, calculate or compare fit input–response or adaptation models with session/board structure using an explicit operational rule.

- Interpret the result and state why model form, dependence and extrapolation limits must be reported

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Fit input–response or adaptation models with session/board structure.
>
> 4\. Acquire or inspect predictors, outcome, repeated-unit ids.
>
> 5\. Produce model coefficient/effect plot and residual/qc report.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: Model form, dependence and extrapolation limits must be reported.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate fit input–response or adaptation models with session/board structure. The reusable output is model coefficient/effect plot and residual/qc report.

**Sources / connections / priority.** Sources: \[O1 Statistics/Model Fitting; R4; R5; O6\]. Natural follow-ons: STA-06, CMP-04. Development priority: Advanced specialised module. Boundary: Model form, dependence and extrapolation limits must be reported.

## STA-06 — Multiplicity, power and statistical versus scientific significance { #sta-06 }

| **Concept / theme**        | Testing many outcomes or parameters inflates false positives; power and effect magnitude guide design and interpretation.                         |
|----------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Master’s/doctoral methods. Formal practical, workshop or modular course. Prior modules: STA-02, MET-03.                                           |
| **Logistics**              | 60 min; 1–3; boards: 0; software: Jupyter; prepared dataset: Yes: reused module datasets. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | Jupyter methodology. Stages: 8–12.                                                                                                                |
| **Spikeling relationship** | 5 — Recorded-dataset analysis; 8 — External computational comparison                                                                              |

**Learning outcomes.**

- Identify and predict the principal behaviour described in testing many outcomes or parameters inflates false positives; power and effect magnitude guide design and interpretation.

- Configure or document simulate multiplicity/power or analyse a module with multiple outcomes and record number of tests, effect sizes, alpha/fdr, power.

- Measure, calculate or compare simulate multiplicity/power or analyse a module with multiple outcomes using an explicit operational rule.

- Interpret the result and state why correction does not rescue poor measurement or undisclosed analytic flexibility

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Simulate multiplicity/power or analyse a module with multiple outcomes.
>
> 4\. Acquire or inspect number of tests, effect sizes, alpha/fdr, power.
>
> 5\. Produce analysis plan and corrected/estimation-focused conclusion.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: Correction does not rescue poor measurement or undisclosed analytic flexibility.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate simulate multiplicity/power or analyse a module with multiple outcomes. The reusable output is analysis plan and corrected/estimation-focused conclusion.

**Sources / connections / priority.** Sources: \[O1 Statistics/Model Fitting; R4; R5; O6\]. Natural follow-ons: EPI-03, MET-05. Development priority: Advanced specialised module. Boundary: Correction does not rescue poor measurement or undisclosed analytic flexibility.
