# Neurophysiology

!!! info "Curriculum status"
    These entries are architecture specifications, not final lesson plans. They define teaching intent, logistics, outputs and scientific boundaries; release-ready settings, worksheets, notebooks and answer keys still require empirical validation.

[Return to the module catalogue](index.md)


**Family source cluster:** \[T1 Chs.1,3,7–9; T2 Chs.9–10; T3 Chs.3–4; T4 Chs.2–3; G2–G4\]

## NPH-01 — Baseline and resting state { #nph-01 }

| **Concept / theme**        | A stable baseline is an operational reference, not proof of biological resting-potential mechanisms.                                                               |
|----------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | First-year undergraduate. Formal practical, workshop or modular course. Prior modules: FND-04, EPH-04 for quantitative timing.                                     |
| **Logistics**              | 45 min; 2–4 per board; boards: 1; software: Spikeling GUI; prepared dataset: No; optional reference trace. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | Board and GUI experiment. Stages: 1–8, 10–11.                                                                                                                      |
| **Spikeling relationship** | 2 — Direct board + GUI; 3 — Hybrid board + Jupyter                                                                                                                 |

**Learning outcomes.**

- Identify and predict the principal behaviour described in a stable baseline is an operational reference, not proof of biological resting-potential mechanisms.

- Configure or document record baseline across presets and input settings and record baseline Vm, variance, spontaneous spikes.

- Measure, calculate or compare record baseline across presets and input settings using an explicit operational rule.

- Interpret the result and state why the model v_rest parameter and observed equilibrium are not an ion-specific resting membrane potential

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Record baseline across presets and input settings.
>
> 4\. Acquire or inspect baseline Vm, variance, spontaneous spikes.
>
> 5\. Produce baseline table and stability criterion.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: The model v_rest parameter and observed equilibrium are not an ion-specific resting membrane potential.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate record baseline across presets and input settings. The reusable output is baseline table and stability criterion.

**Sources / connections / priority.** Sources: \[T1 Chs.1,3,7–9; T2 Chs.9–10; T3 Chs.3–4; T4 Chs.2–3; G2–G4\]. Natural follow-ons: NPH-02, EPH-06, DAT-02. Development priority: Core module. Boundary: The model v_rest parameter and observed equilibrium are not an ion-specific resting membrane potential.

## NPH-02 — Depolarisation and hyperpolarisation { #nph-02 }

| **Concept / theme**        | Signed inputs move model voltage toward or away from spike generation.                                                                                             |
|----------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | School to undergraduate. Formal practical, workshop or modular course. Prior modules: FND-01, FND-04.                                                              |
| **Logistics**              | 45 min; 2–4 per board; boards: 1; software: Spikeling GUI; prepared dataset: No; optional reference trace. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | Guided experiment. Stages: 1–8, 10–11.                                                                                                                             |
| **Spikeling relationship** | 1 — Direct physical implementation; 2 — Direct board + GUI                                                                                                         |

**Learning outcomes.**

- Identify and predict the principal behaviour described in signed inputs move model voltage toward or away from spike generation.

- Configure or document apply positive and negative current steps of controlled magnitude and record Vm deflection, recovery, spike occurrence.

- Measure, calculate or compare apply positive and negative current steps of controlled magnitude using an explicit operational rule.

- Interpret the result and state why direction is direct model behaviour; ionic basis is not established

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Apply positive and negative current steps of controlled magnitude.
>
> 4\. Acquire or inspect Vm deflection, recovery, spike occurrence.
>
> 5\. Produce overlaid traces and polarity comparison.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: Direction is direct model behaviour; ionic basis is not established.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate apply positive and negative current steps of controlled magnitude. The reusable output is overlaid traces and polarity comparison.

**Sources / connections / priority.** Sources: \[T1 Chs.1,3,7–9; T2 Chs.9–10; T3 Chs.3–4; T4 Chs.2–3; G2–G4\]. Natural follow-ons: NPH-03, EPH-01, SYN-02. Development priority: Core module. Boundary: Direction is direct model behaviour; ionic basis is not established.

## NPH-03 — Threshold and operational rheobase { #nph-03 }

| **Concept / theme**        | Threshold and rheobase are protocol-dependent operational measurements.                                                                                            |
|----------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Undergraduate. Formal practical, workshop or modular course. Prior modules: NPH-02, MET-02; EPH-04 for timing.                                                     |
| **Logistics**              | 60 min; 2–4 per board; boards: 1; software: Spikeling GUI; prepared dataset: No; optional reference trace. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | Board + GUI experiment. Stages: 1–8, 10–11.                                                                                                                        |
| **Spikeling relationship** | 2 — Direct board + GUI; 3 — Hybrid board + Jupyter                                                                                                                 |

**Learning outcomes.**

- Identify and predict the principal behaviour described in threshold and rheobase are protocol-dependent operational measurements.

- Configure or document use ascending or bracketed current steps to estimate the smallest reliable spiking input and record spike probability/occurrence, Vm, command level.

- Measure, calculate or compare use ascending or bracketed current steps to estimate the smallest reliable spiking input using an explicit operational rule.

- Interpret the result and state why do not report the command as pa or infer a fixed biological threshold voltage

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Use ascending or bracketed current steps to estimate the smallest reliable spiking input.
>
> 4\. Acquire or inspect spike probability/occurrence, Vm, command level.
>
> 5\. Produce threshold estimate with protocol and uncertainty.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: Do not report the command as pA or infer a fixed biological threshold voltage.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate use ascending or bracketed current steps to estimate the smallest reliable spiking input. The reusable output is threshold estimate with protocol and uncertainty.

**Sources / connections / priority.** Sources: \[T1 Chs.1,3,7–9; T2 Chs.9–10; T3 Chs.3–4; T4 Chs.2–3; G2–G4\]. Natural follow-ons: NPH-04, STA-02, CMP-05. Development priority: Core module. Boundary: Do not report the command as pA or infer a fixed biological threshold voltage.

## NPH-04 — Input–output and firing-rate curve { #nph-04 }

| **Concept / theme**        | Response magnitude can be expressed as an empirical transfer function.                                                                                             |
|----------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Undergraduate. Formal practical, workshop or modular course. Prior modules: NPH-03, DAT-03, EPH-04.                                                                |
| **Logistics**              | 60 min; 2–4 per board; boards: 1; software: Spikeling GUI; prepared dataset: No; optional reference trace. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | Hybrid board + Jupyter. Stages: 1–8, 10–11.                                                                                                                        |
| **Spikeling relationship** | 2 — Direct board + GUI; 3 — Hybrid board + Jupyter                                                                                                                 |

**Learning outcomes.**

- Identify and predict the principal behaviour described in response magnitude can be expressed as an empirical transfer function.

- Configure or document present graded inputs in randomised or ascending order and measure spike output and record input level, spike count/rate, latency.

- Measure, calculate or compare present graded inputs in randomised or ascending order and measure spike output using an explicit operational rule.

- Interpret the result and state why use validated timebase for rates; curve belongs to selected model and protocol

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Present graded inputs in randomised or ascending order and measure spike output.
>
> 4\. Acquire or inspect input level, spike count/rate, latency.
>
> 5\. Produce f–i-style curve with dynamic-range annotation.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: Use validated timebase for rates; curve belongs to selected model and protocol.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate present graded inputs in randomised or ascending order and measure spike output. The reusable output is f–i-style curve with dynamic-range annotation.

**Sources / connections / priority.** Sources: \[T1 Chs.1,3,7–9; T2 Chs.9–10; T3 Chs.3–4; T4 Chs.2–3; G2–G4\]. Natural follow-ons: SEN-02, STA-05, CMP-05. Development priority: Core module. Boundary: Use validated timebase for rates; curve belongs to selected model and protocol.

## NPH-05 — Refractory and recovery behaviour { #nph-05 }

| **Concept / theme**        | A system’s response to closely spaced stimuli reveals recovery constraints.                                                                                        |
|----------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Advanced undergraduate. Formal practical, workshop or modular course. Prior modules: NPH-03, EPH-04, DAT-03.                                                       |
| **Logistics**              | 60 min; 2–4 per board; boards: 1; software: Spikeling GUI; prepared dataset: No; optional reference trace. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | Hybrid experiment. Stages: 1–8, 10–11.                                                                                                                             |
| **Spikeling relationship** | 2 — Direct board + GUI; 3 — Hybrid board + Jupyter; 8 — External computational comparison                                                                          |

**Learning outcomes.**

- Identify and predict the principal behaviour described in a system’s response to closely spaced stimuli reveals recovery constraints.

- Configure or document deliver paired stimuli with varied intervals or use repeated pulse trains and record second-response probability, latency and Vm trajectory.

- Measure, calculate or compare deliver paired stimuli with varied intervals or use repeated pulse trains using an explicit operational rule.

- Interpret the result and state why the reset/recovery variable is phenomenological and cannot establish sodium-channel inactivation

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Deliver paired stimuli with varied intervals or use repeated pulse trains.
>
> 4\. Acquire or inspect second-response probability, latency and Vm trajectory.
>
> 5\. Produce recovery curve and operational refractory definition.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: The reset/recovery variable is phenomenological and cannot establish sodium-channel inactivation.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate deliver paired stimuli with varied intervals or use repeated pulse trains. The reusable output is recovery curve and operational refractory definition.

**Sources / connections / priority.** Sources: \[T1 Chs.1,3,7–9; T2 Chs.9–10; T3 Chs.3–4; T4 Chs.2–3; G2–G4\]. Natural follow-ons: DAT-04, CMP-03, EPI-02. Development priority: High-priority extension. Boundary: The reset/recovery variable is phenomenological and cannot establish sodium-channel inactivation.

## NPH-06 — Latency and adaptation { #nph-06 }

| **Concept / theme**        | Response timing and firing change during sustained or repeated input.                                                                                              |
|----------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Undergraduate. Formal practical, workshop or modular course. Prior modules: EPH-04, DAT-03.                                                                        |
| **Logistics**              | 60 min; 2–4 per board; boards: 1; software: Spikeling GUI; prepared dataset: No; optional reference trace. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | Hybrid board + Jupyter. Stages: 1–8, 10–11.                                                                                                                        |
| **Spikeling relationship** | 2 — Direct board + GUI; 3 — Hybrid board + Jupyter                                                                                                                 |

**Learning outcomes.**

- Identify and predict the principal behaviour described in response timing and firing change during sustained or repeated input.

- Configure or document compare early and late spikes during steps or pulse trains across presets and record first-spike latency, isis, rate slope.

- Measure, calculate or compare compare early and late spikes during steps or pulse trains across presets using an explicit operational rule.

- Interpret the result and state why timing must be validated; adaptation does not identify a particular after-hyperpolarising conductance

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Compare early and late spikes during steps or pulse trains across presets.
>
> 4\. Acquire or inspect first-spike latency, isis, rate slope.
>
> 5\. Produce latency/adaptation feature table.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: Timing must be validated; adaptation does not identify a particular after-hyperpolarising conductance.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate compare early and late spikes during steps or pulse trains across presets. The reusable output is latency/adaptation feature table.

**Sources / connections / priority.** Sources: \[T1 Chs.1,3,7–9; T2 Chs.9–10; T3 Chs.3–4; T4 Chs.2–3; G2–G4\]. Natural follow-ons: DAT-05, CMP-02, STA-03. Development priority: Core module. Boundary: Timing must be validated; adaptation does not identify a particular after-hyperpolarising conductance.

## NPH-07 — Atlas of neuronal firing diversity { #nph-07 }

| **Concept / theme**        | Different parameter sets generate distinct phenomenological response classes.                                                                                      |
|----------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Undergraduate to master’s. Formal practical, workshop or modular course. Prior modules: NPH-02, DAT-02.                                                            |
| **Logistics**              | 60 min; 2–4 per board; boards: 1; software: Spikeling GUI; prepared dataset: No; optional reference trace. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | Board + GUI experiment. Stages: 1–8, 10–11.                                                                                                                        |
| **Spikeling relationship** | 2 — Direct board + GUI; 3 — Hybrid board + Jupyter; 8 — External computational comparison                                                                          |

**Learning outcomes.**

- Identify and predict the principal behaviour described in different parameter sets generate distinct phenomenological response classes.

- Configure or document apply a standard stimulus panel to selected presets and record Vm traces, spike patterns, burst/adaptation features.

- Measure, calculate or compare apply a standard stimulus panel to selected presets using an explicit operational rule.

- Interpret the result and state why preset names are firing-pattern labels, not biological cell-type diagnoses

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Apply a standard stimulus panel to selected presets.
>
> 4\. Acquire or inspect Vm traces, spike patterns, burst/adaptation features.
>
> 5\. Produce preset phenotype atlas and classification rationale.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: Preset names are firing-pattern labels, not biological cell-type diagnoses.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate apply a standard stimulus panel to selected presets. The reusable output is preset phenotype atlas and classification rationale.

**Sources / connections / priority.** Sources: \[T1 Chs.1,3,7–9; T2 Chs.9–10; T3 Chs.3–4; T4 Chs.2–3; G2–G4\]. Natural follow-ons: CMP-03, CMP-04, DAT-05. Development priority: Core module. Boundary: Preset names are firing-pattern labels, not biological cell-type diagnoses.
