# Computational neuroscience

!!! info "Curriculum status"
    These entries are architecture specifications, not final lesson plans. They define teaching intent, logistics, outputs and scientific boundaries; release-ready settings, worksheets, notebooks and answer keys still require empirical validation.

[Return to the module catalogue](index.md)


**Family source cluster:** \[T1 Chs.1,3–10; T5 Chs.5–8; T6; P1; O1; G2–G5\]

## CMP-01 — The Izhikevich equations as an executable model { #cmp-01 }

| **Concept / theme**        | Two differential equations plus reset generate the implemented voltage and recovery dynamics.                                                         |
|----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Undergraduate computational neuroscience. Formal practical, workshop or modular course. Prior modules: FND-02, FND-04.                                |
| **Logistics**              | 60 min; 1–3; boards: 0–1; software: GUI and Jupyter; prepared dataset: Generated or prepared. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | Simulation comparison. Stages: 1–3, 6–11.                                                                                                             |
| **Spikeling relationship** | 2 — Direct board + GUI; 8 — External computational comparison                                                                                         |

**Learning outcomes.**

- Identify and predict the principal behaviour described in two differential equations plus reset generate the implemented voltage and recovery dynamics.

- Configure or document map firmware terms to equations and reproduce one trace in a notebook and record v, u, input current, spike/reset.

- Measure, calculate or compare map firmware terms to equations and reproduce one trace in a notebook using an explicit operational rule.

- Interpret the result and state why equation variables are phenomenological and not one-to-one ion-channel states

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Map firmware terms to equations and reproduce one trace in a notebook.
>
> 4\. Acquire or inspect v, u, input current, spike/reset.
>
> 5\. Produce annotated equations and board–simulation overlay.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: Equation variables are phenomenological and not one-to-one ion-channel states.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate map firmware terms to equations and reproduce one trace in a notebook. The reusable output is annotated equations and board–simulation overlay.

**Sources / connections / priority.** Sources: \[T1 Chs.1,3–10; T5 Chs.5–8; T6; P1; O1; G2–G5\]. Natural follow-ons: CMP-02, CMP-04. Development priority: Core module. Boundary: Equation variables are phenomenological and not one-to-one ion-channel states.

## CMP-02 — Meaning of a, b, c and d { #cmp-02 }

| **Concept / theme**        | Parameters control recovery timescale, coupling, reset voltage and post-spike recovery increment.                                                     |
|----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Undergraduate. Formal practical, workshop or modular course. Prior modules: CMP-01, DAT-05.                                                           |
| **Logistics**              | 60 min; 1–3; boards: 0–1; software: GUI and Jupyter; prepared dataset: Generated or prepared. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | Board + simulation. Stages: 1–3, 6–11.                                                                                                                |
| **Spikeling relationship** | 2 — Direct board + GUI; 3 — Hybrid board + Jupyter; 8 — External computational comparison                                                             |

**Learning outcomes.**

- Identify and predict the principal behaviour described in parameters control recovery timescale, coupling, reset voltage and post-spike recovery increment.

- Configure or document change one parameter at a time from a baseline model and record parameters and extracted firing features.

- Measure, calculate or compare change one parameter at a time from a baseline model using an explicit operational rule.

- Interpret the result and state why one-at-a-time changes do not establish independence; parameter labels are model meanings, not molecular identities

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Change one parameter at a time from a baseline model.
>
> 4\. Acquire or inspect parameters and extracted firing features.
>
> 5\. Produce parameter–effect table with interaction caveat.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: One-at-a-time changes do not establish independence; parameter labels are model meanings, not molecular identities.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate change one parameter at a time from a baseline model. The reusable output is parameter–effect table with interaction caveat.

**Sources / connections / priority.** Sources: \[T1 Chs.1,3–10; T5 Chs.5–8; T6; P1; O1; G2–G5\]. Natural follow-ons: CMP-03, CMP-04. Development priority: Core module. Boundary: One-at-a-time changes do not establish independence; parameter labels are model meanings, not molecular identities.

## CMP-03 — Preset phenotype atlas { #cmp-03 }

| **Concept / theme**        | The twenty presets occupy a practical catalogue of firing phenotypes.                                                                                 |
|----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Undergraduate to master’s. Formal practical, workshop or modular course. Prior modules: NPH-07, DAT-05.                                               |
| **Logistics**              | 60 min; 1–3; boards: 0–1; software: GUI and Jupyter; prepared dataset: Generated or prepared. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | Hybrid experiment. Stages: 1–3, 6–11.                                                                                                                 |
| **Spikeling relationship** | 2 — Direct board + GUI; 3 — Hybrid board + Jupyter; 8 — External computational comparison                                                             |

**Learning outcomes.**

- Identify and predict the principal behaviour described in the twenty presets occupy a practical catalogue of firing phenotypes.

- Configure or document run a standard stimulus battery across selected or all presets and record preset parameters, traces and feature labels.

- Measure, calculate or compare run a standard stimulus battery across selected or all presets using an explicit operational rule.

- Interpret the result and state why preset classification depends on stimulus protocol and validated timing

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Run a standard stimulus battery across selected or all presets.
>
> 4\. Acquire or inspect preset parameters, traces and feature labels.
>
> 5\. Produce searchable preset atlas.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: Preset classification depends on stimulus protocol and validated timing.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate run a standard stimulus battery across selected or all presets. The reusable output is searchable preset atlas.

**Sources / connections / priority.** Sources: \[T1 Chs.1,3–10; T5 Chs.5–8; T6; P1; O1; G2–G5\]. Natural follow-ons: CMP-04, CMP-05, CMP-06. Development priority: High-priority extension. Boundary: Preset classification depends on stimulus protocol and validated timing.

## CMP-04 — Parameter sweeps and sensitivity { #cmp-04 }

| **Concept / theme**        | Systematic sweeps reveal local and global sensitivity, interactions and regime boundaries.                                                            |
|----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Advanced undergraduate to master’s. Formal practical, workshop or modular course. Prior modules: CMP-02, DAT-05.                                      |
| **Logistics**              | 60 min; 1–3; boards: 0–1; software: GUI and Jupyter; prepared dataset: Generated or prepared. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | Jupyter + board validation. Stages: 1–3, 6–11.                                                                                                        |
| **Spikeling relationship** | 3 — Hybrid board + Jupyter; 8 — External computational comparison                                                                                     |

**Learning outcomes.**

- Identify and predict the principal behaviour described in systematic sweeps reveal local and global sensitivity, interactions and regime boundaries.

- Configure or document sweep one or two parameters in external simulation and compare selected points on board and record parameter grid, features, failure/transition regions.

- Measure, calculate or compare sweep one or two parameters in external simulation and compare selected points on board using an explicit operational rule.

- Interpret the result and state why board numerical step and GUI timing may differ from notebook; compare explicitly

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Sweep one or two parameters in external simulation and compare selected points on board.
>
> 4\. Acquire or inspect parameter grid, features, failure/transition regions.
>
> 5\. Produce sensitivity heatmap and validation trace set.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: Board numerical step and GUI timing may differ from notebook; compare explicitly.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate sweep one or two parameters in external simulation and compare selected points on board. The reusable output is sensitivity heatmap and validation trace set.

**Sources / connections / priority.** Sources: \[T1 Chs.1,3–10; T5 Chs.5–8; T6; P1; O1; G2–G5\]. Natural follow-ons: CMP-09, STA-05. Development priority: Advanced specialised module. Boundary: Board numerical step and GUI timing may differ from notebook; compare explicitly.

## CMP-05 — Class 1 and Class 2 excitability { #cmp-05 }

| **Concept / theme**        | Firing onset can be compared through frequency–input relationships and dynamical interpretation.                                                      |
|----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Master’s. Formal practical, workshop or modular course. Prior modules: NPH-04, CMP-03, EPH-04.                                                        |
| **Logistics**              | 60 min; 1–3; boards: 0–1; software: GUI and Jupyter; prepared dataset: Generated or prepared. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | Hybrid experiment. Stages: 1–3, 6–11.                                                                                                                 |
| **Spikeling relationship** | 2 — Direct board + GUI; 3 — Hybrid board + Jupyter; 8 — External computational comparison                                                             |

**Learning outcomes.**

- Identify and predict the principal behaviour described in firing onset can be compared through frequency–input relationships and dynamical interpretation.

- Configure or document measure low-input firing onset in class1/class2 presets and compare with simulations and record input, firing rate near onset, latency.

- Measure, calculate or compare measure low-input firing onset in class1/class2 presets and compare with simulations using an explicit operational rule.

- Interpret the result and state why requires fine input control and validated rates; do not generalise beyond the model behaviour

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Measure low-input firing onset in Class1/Class2 presets and compare with simulations.
>
> 4\. Acquire or inspect input, firing rate near onset, latency.
>
> 5\. Produce comparative onset plot and classification argument.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: Requires fine input control and validated rates; do not generalise beyond the model behaviour.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate measure low-input firing onset in class1/class2 presets and compare with simulations. The reusable output is comparative onset plot and classification argument.

**Sources / connections / priority.** Sources: \[T1 Chs.1,3–10; T5 Chs.5–8; T6; P1; O1; G2–G5\]. Natural follow-ons: CMP-08, EPI-02. Development priority: Advanced specialised module. Boundary: Requires fine input control and validated rates; do not generalise beyond the model behaviour.

## CMP-06 — Integrators and resonators { #cmp-06 }

| **Concept / theme**        | Response depends differently on accumulated input and input timing/frequency.                                                                         |
|----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Advanced undergraduate to master’s. Formal practical, workshop or modular course. Prior modules: CMP-03, SYN-05, EPH-04.                              |
| **Logistics**              | 60 min; 1–3; boards: 0–1; software: GUI and Jupyter; prepared dataset: Generated or prepared. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | Hybrid experiment. Stages: 1–3, 6–11.                                                                                                                 |
| **Spikeling relationship** | 2 — Direct board + GUI; 3 — Hybrid board + Jupyter; 8 — External computational comparison                                                             |

**Learning outcomes.**

- Identify and predict the principal behaviour described in response depends differently on accumulated input and input timing/frequency.

- Configure or document compare integrator and resonator presets with paired pulses or frequency sweeps and record spike probability versus interval/frequency.

- Measure, calculate or compare compare integrator and resonator presets with paired pulses or frequency sweeps using an explicit operational rule.

- Interpret the result and state why frequency response is protocol- and timebase-dependent

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Compare Integrator and Resonator presets with paired pulses or frequency sweeps.
>
> 4\. Acquire or inspect spike probability versus interval/frequency.
>
> 5\. Produce integrator–resonator comparison plot.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: Frequency response is protocol- and timebase-dependent.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate compare integrator and resonator presets with paired pulses or frequency sweeps. The reusable output is integrator–resonator comparison plot.

**Sources / connections / priority.** Sources: \[T1 Chs.1,3–10; T5 Chs.5–8; T6; P1; O1; G2–G5\]. Natural follow-ons: CMP-08, NET-06. Development priority: Advanced specialised module. Boundary: Frequency response is protocol- and timebase-dependent.

## CMP-07 — Rebound, bistability and bursting regimes { #cmp-07 }

| **Concept / theme**        | Selected presets demonstrate history dependence and multi-timescale firing patterns.                                                                  |
|----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Advanced undergraduate to master’s. Formal practical, workshop or modular course. Prior modules: CMP-03, DAT-05.                                      |
| **Logistics**              | 60 min; 1–3; boards: 0–1; software: GUI and Jupyter; prepared dataset: Generated or prepared. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | Board + simulation. Stages: 1–3, 6–11.                                                                                                                |
| **Spikeling relationship** | 2 — Direct board + GUI; 3 — Hybrid board + Jupyter; 8 — External computational comparison                                                             |

**Learning outcomes.**

- Identify and predict the principal behaviour described in selected presets demonstrate history dependence and multi-timescale firing patterns.

- Configure or document apply hyperpolarising/depolarising steps and standard perturbation sequences and record state before/after perturbation, burst metrics.

- Measure, calculate or compare apply hyperpolarising/depolarising steps and standard perturbation sequences using an explicit operational rule.

- Interpret the result and state why behaviours do not prove h-current, t-type calcium or other biological mechanisms

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Apply hyperpolarising/depolarising steps and standard perturbation sequences.
>
> 4\. Acquire or inspect state before/after perturbation, burst metrics.
>
> 5\. Produce regime-transition traces and operational definitions.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: Behaviours do not prove H-current, T-type calcium or other biological mechanisms.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate apply hyperpolarising/depolarising steps and standard perturbation sequences. The reusable output is regime-transition traces and operational definitions.

**Sources / connections / priority.** Sources: \[T1 Chs.1,3–10; T5 Chs.5–8; T6; P1; O1; G2–G5\]. Natural follow-ons: CMP-08, EPI-02. Development priority: Advanced specialised module. Boundary: Behaviours do not prove H-current, T-type calcium or other biological mechanisms.

## CMP-08 — Nullclines, phase portraits and dynamical interpretation { #cmp-08 }

| **Concept / theme**        | Companion simulation exposes v–u geometry that cannot be directly measured from the board stream.                                                     |
|----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Master’s to doctoral intensive. Formal practical, workshop or modular course. Prior modules: CMP-01, CMP-02, calculus helpful.                        |
| **Logistics**              | 60 min; 1–3; boards: 0–1; software: GUI and Jupyter; prepared dataset: Generated or prepared. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | External computational comparison. Stages: 1–3, 6–11.                                                                                                 |
| **Spikeling relationship** | 8 — External computational comparison; 3 — Hybrid board + Jupyter                                                                                     |

**Learning outcomes.**

- Identify and predict the principal behaviour described in companion simulation exposes v–u geometry that cannot be directly measured from the board stream.

- Configure or document simulate trajectories/nullclines for a board-matched parameter set and align events to recorded Vm and record v, u, nullclines, equilibria, trajectories.

- Measure, calculate or compare simulate trajectories/nullclines for a board-matched parameter set and align events to recorded Vm using an explicit operational rule.

- Interpret the result and state why u is not currently exported as an experimental channel; phase portrait is reconstructed from the model

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Simulate trajectories/nullclines for a board-matched parameter set and align events to recorded Vm.
>
> 4\. Acquire or inspect v, u, nullclines, equilibria, trajectories.
>
> 5\. Produce phase portrait linked to an experimental trace.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: u is not currently exported as an experimental channel; phase portrait is reconstructed from the model.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate simulate trajectories/nullclines for a board-matched parameter set and align events to recorded Vm. The reusable output is phase portrait linked to an experimental trace.

**Sources / connections / priority.** Sources: \[T1 Chs.1,3–10; T5 Chs.5–8; T6; P1; O1; G2–G5\]. Natural follow-ons: CMP-09, EPI-02. Development priority: Advanced specialised module. Boundary: u is not currently exported as an experimental channel; phase portrait is reconstructed from the model.

## CMP-09 — Mystery neuron: parameter inference and model comparison { #cmp-09 }

| **Concept / theme**        | Unknown a,b,c,d can be inferred probabilistically from designed stimuli and summary features.                                                         |
|----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Master’s/doctoral intensive. Formal practical, workshop or modular course. Prior modules: CMP-04, DAT-05, STA-02, MET-03.                             |
| **Logistics**              | 60 min; 1–3; boards: 0–1; software: GUI and Jupyter; prepared dataset: Generated or prepared. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | Jupyter inference module. Stages: 1–3, 6–11.                                                                                                          |
| **Spikeling relationship** | 3 — Hybrid board + Jupyter; 5 — Recorded-dataset analysis; 8 — External computational comparison                                                      |

**Learning outcomes.**

- Identify and predict the principal behaviour described in unknown a,b,c,d can be inferred probabilistically from designed stimuli and summary features.

- Configure or document design informative protocols, fit candidate models and compare posterior/predictive performance and record stimuli, traces, feature likelihoods, parameter distributions.

- Measure, calculate or compare design informative protocols, fit candidate models and compare posterior/predictive performance using an explicit operational rule.

- Interpret the result and state why identifiability may be weak; equivalent parameter sets and model mismatch must be reported

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Design informative protocols, fit candidate models and compare posterior/predictive performance.
>
> 4\. Acquire or inspect stimuli, traces, feature likelihoods, parameter distributions.
>
> 5\. Produce inference report with uncertainty and validation prediction.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: Identifiability may be weak; equivalent parameter sets and model mismatch must be reported.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate design informative protocols, fit candidate models and compare posterior/predictive performance. The reusable output is inference report with uncertainty and validation prediction.

**Sources / connections / priority.** Sources: \[T1 Chs.1,3–10; T5 Chs.5–8; T6; P1; O1; G2–G5\]. Natural follow-ons: EPI-02, EPI-03. Development priority: Advanced specialised module. Boundary: Identifiability may be weak; equivalent parameter sets and model mismatch must be reported.
