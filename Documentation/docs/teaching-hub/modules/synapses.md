# Synapses and integration

!!! info "Curriculum status"
    These entries are architecture specifications, not final lesson plans. They define teaching intent, logistics, outputs and scientific boundaries; release-ready settings, worksheets, notebooks and answer keys still require empirical validation.

[Return to the module catalogue](index.md)


**Family source cluster:** \[T2 Chs.11–15; T3 Ch.5; T4 Chs.5,7; T5 Chs.5–6; T6 Ch.3; R1; G3\]

## SYN-01 — From presynaptic event to postsynaptic current { #syn-01 }

| **Concept / theme**        | A rising presynaptic event launches a decaying signed current that influences the postsynaptic model.                                                                                   |
|----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Undergraduate. Formal practical, workshop or modular course. Prior modules: EPH-03, NPH-02.                                                                                             |
| **Logistics**              | 45 min; 3–5; boards: 1–3; software: GUI; Jupyter for quantitative/ plasticity modules; prepared dataset: Optional or generated. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | Multi-board guided experiment. Stages: 1–8, 10–11.                                                                                                                                      |
| **Spikeling relationship** | 2 — Direct board + GUI; 4 — Multi-board implementation; 7 — Conceptual analogy                                                                                                          |

**Learning outcomes.**

- Identify and predict the principal behaviour described in a rising presynaptic event launches a decaying signed current that influences the postsynaptic model.

- Configure or document connect one board or pulse source to one synaptic input and inspect pre-Vm, synaptic current and post-Vm and record presynaptic Vm/event, synaptic current, postsynaptic Vm.

- Measure, calculate or compare connect one board or pulse source to one synaptic input and inspect pre-Vm, synaptic current and post-Vm using an explicit operational rule.

- Interpret the result and state why this is not direct evidence of transmitter release, receptor activation or conductance change

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Connect one board or pulse source to one synaptic input and inspect pre-Vm, synaptic current and post-Vm.
>
> 4\. Acquire or inspect presynaptic Vm/event, synaptic current, postsynaptic Vm.
>
> 5\. Produce annotated transmission trace.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: This is not direct evidence of transmitter release, receptor activation or conductance change.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate connect one board or pulse source to one synaptic input and inspect pre-Vm, synaptic current and post-Vm. The reusable output is annotated transmission trace.

**Sources / connections / priority.** Sources: \[T2 Chs.11–15; T3 Ch.5; T4 Chs.5,7; T5 Chs.5–6; T6 Ch.3; R1; G3\]. Natural follow-ons: SYN-02, SYN-03, NET-01. Development priority: Core module. Boundary: This is not direct evidence of transmitter release, receptor activation or conductance change.

## SYN-02 — Excitation, inhibition and signed gain { #syn-02 }

| **Concept / theme**        | The sign and magnitude of synaptic gain determine functional excitatory or inhibitory influence.                                                                                        |
|----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | School to undergraduate. Formal practical, workshop or modular course. Prior modules: SYN-01.                                                                                           |
| **Logistics**              | 60 min; 3–5; boards: 1–3; software: GUI; Jupyter for quantitative/ plasticity modules; prepared dataset: Optional or generated. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | Board + GUI experiment. Stages: 1–8, 10–11.                                                                                                                                             |
| **Spikeling relationship** | 2 — Direct board + GUI; 3 — Hybrid board + Jupyter; 4 — Multi-board implementation; 7 — Conceptual analogy                                                                              |

**Learning outcomes.**

- Identify and predict the principal behaviour described in the sign and magnitude of synaptic gain determine functional excitatory or inhibitory influence.

- Configure or document sweep gain across negative, zero and positive settings and record synaptic current sign, post-Vm, spike probability.

- Measure, calculate or compare sweep gain across negative, zero and positive settings using an explicit operational rule.

- Interpret the result and state why functional sign does not identify receptor type or reversal potential

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Sweep gain across negative, zero and positive settings.
>
> 4\. Acquire or inspect synaptic current sign, post-Vm, spike probability.
>
> 5\. Produce gain–response plot and functional e/i definition.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: Functional sign does not identify receptor type or reversal potential.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate sweep gain across negative, zero and positive settings. The reusable output is gain–response plot and functional e/i definition.

**Sources / connections / priority.** Sources: \[T2 Chs.11–15; T3 Ch.5; T4 Chs.5,7; T5 Chs.5–6; T6 Ch.3; R1; G3\]. Natural follow-ons: SYN-03, NET-02, NET-04. Development priority: Core module. Boundary: Functional sign does not identify receptor type or reversal potential.

## SYN-03 — Temporal summation { #syn-03 }

| **Concept / theme**        | Inputs arriving within the integration window combine more strongly than widely separated inputs.                                                                                       |
|----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Undergraduate. Formal practical, workshop or modular course. Prior modules: SYN-01, EPH-04.                                                                                             |
| **Logistics**              | 60 min; 3–5; boards: 1–3; software: GUI; Jupyter for quantitative/ plasticity modules; prepared dataset: Optional or generated. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | Hybrid multi-board experiment. Stages: 1–8, 10–11.                                                                                                                                      |
| **Spikeling relationship** | 2 — Direct board + GUI; 3 — Hybrid board + Jupyter; 4 — Multi-board implementation                                                                                                      |

**Learning outcomes.**

- Identify and predict the principal behaviour described in inputs arriving within the integration window combine more strongly than widely separated inputs.

- Configure or document vary the interval between repeated events on one input and record peak post-Vm/current, output spike, interval.

- Measure, calculate or compare vary the interval between repeated events on one input using an explicit operational rule.

- Interpret the result and state why observed decay/integration reflects model and firmware parameters, not a measured membrane/synaptic time constant

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Vary the interval between repeated events on one input.
>
> 4\. Acquire or inspect peak post-Vm/current, output spike, interval.
>
> 5\. Produce summation-vs-interval curve.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: Observed decay/integration reflects model and firmware parameters, not a measured membrane/synaptic time constant.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate vary the interval between repeated events on one input. The reusable output is summation-vs-interval curve.

**Sources / connections / priority.** Sources: \[T2 Chs.11–15; T3 Ch.5; T4 Chs.5,7; T5 Chs.5–6; T6 Ch.3; R1; G3\]. Natural follow-ons: SYN-05, SYN-06, DAT-06. Development priority: Core module. Boundary: Observed decay/integration reflects model and firmware parameters, not a measured membrane/synaptic time constant.

## SYN-04 — Spatial summation with two inputs { #syn-04 }

| **Concept / theme**        | Two independently controlled inputs can sum, cancel or gate one another.                                                                                                                |
|----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Undergraduate. Formal practical, workshop or modular course. Prior modules: SYN-02.                                                                                                     |
| **Logistics**              | 60 min; 3–5; boards: 1–3; software: GUI; Jupyter for quantitative/ plasticity modules; prepared dataset: Optional or generated. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | Multi-board experiment. Stages: 1–8, 10–11.                                                                                                                                             |
| **Spikeling relationship** | 2 — Direct board + GUI; 3 — Hybrid board + Jupyter; 4 — Multi-board implementation                                                                                                      |

**Learning outcomes.**

- Identify and predict the principal behaviour described in two independently controlled inputs can sum, cancel or gate one another.

- Configure or document present two-input combinations with varied sign, amplitude and simultaneity and record syn1/syn2 currents, post-Vm and spikes.

- Measure, calculate or compare present two-input combinations with varied sign, amplitude and simultaneity using an explicit operational rule.

- Interpret the result and state why “spatial” denotes separate input channels, not dendritic location or cable filtering

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Present two-input combinations with varied sign, amplitude and simultaneity.
>
> 4\. Acquire or inspect syn1/syn2 currents, post-Vm and spikes.
>
> 5\. Produce two-factor response matrix.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: “Spatial” denotes separate input channels, not dendritic location or cable filtering.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate present two-input combinations with varied sign, amplitude and simultaneity. The reusable output is two-factor response matrix.

**Sources / connections / priority.** Sources: \[T2 Chs.11–15; T3 Ch.5; T4 Chs.5,7; T5 Chs.5–6; T6 Ch.3; R1; G3\]. Natural follow-ons: NET-02, NET-05, STA-05. Development priority: High-priority extension. Boundary: “Spatial” denotes separate input channels, not dendritic location or cable filtering.

## SYN-05 — Coincidence detection and input timing { #syn-05 }

| **Concept / theme**        | Output can depend on relative timing rather than only total input magnitude.                                                                                                            |
|----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Advanced undergraduate. Formal practical, workshop or modular course. Prior modules: SYN-03, SYN-04, EPH-04.                                                                            |
| **Logistics**              | 60 min; 3–5; boards: 1–3; software: GUI; Jupyter for quantitative/ plasticity modules; prepared dataset: Optional or generated. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | Multi-board + Jupyter. Stages: 1–8, 10–11.                                                                                                                                              |
| **Spikeling relationship** | 3 — Hybrid board + Jupyter; 4 — Multi-board implementation; 8 — External computational comparison                                                                                       |

**Learning outcomes.**

- Identify and predict the principal behaviour described in output can depend on relative timing rather than only total input magnitude.

- Configure or document shift two input trains across positive and negative delays and record output probability/rate versus relative delay.

- Measure, calculate or compare shift two input trains across positive and negative delays using an explicit operational rule.

- Interpret the result and state why delay precision and network latency require validation; no dendritic mechanism is implied

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Shift two input trains across positive and negative delays.
>
> 4\. Acquire or inspect output probability/rate versus relative delay.
>
> 5\. Produce coincidence window plot.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: Delay precision and network latency require validation; no dendritic mechanism is implied.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate shift two input trains across positive and negative delays. The reusable output is coincidence window plot.

**Sources / connections / priority.** Sources: \[T2 Chs.11–15; T3 Ch.5; T4 Chs.5,7; T5 Chs.5–6; T6 Ch.3; R1; G3\]. Natural follow-ons: NET-07, DAT-07. Development priority: Advanced specialised module. Boundary: Delay precision and network latency require validation; no dendritic mechanism is implied.

## SYN-06 — Static synapses versus short-term plasticity { #syn-06 }

| **Concept / theme**        | History-dependent facilitation/depression can be distinguished from a static decaying synapse through controlled trains and model comparison.                                           |
|----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Advanced undergraduate to master’s. Formal practical, workshop or modular course. Prior modules: SYN-03, DAT-05.                                                                        |
| **Logistics**              | 60 min; 3–5; boards: 1–3; software: GUI; Jupyter for quantitative/ plasticity modules; prepared dataset: Optional or generated. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | Simulation comparison. Stages: 1–8, 10–11.                                                                                                                                              |
| **Spikeling relationship** | 3 — Hybrid board + Jupyter; 5 — Recorded-dataset analysis; 8 — External computational comparison                                                                                        |

**Learning outcomes.**

- Identify and predict the principal behaviour described in history-dependent facilitation/depression can be distinguished from a static decaying synapse through controlled trains and model comparison.

- Configure or document record the current static response, then compare with a notebook stp/std simulation or prepared dataset and record event times, response amplitudes, fitted dynamic-synapse variables.

- Measure, calculate or compare record the current static response, then compare with a notebook stp/std simulation or prepared dataset using an explicit operational rule.

- Interpret the result and state why current v3 repository does not establish board-level stp/std; do not present the simulation as implemented hardware behaviour

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Record the current static response, then compare with a notebook STP/STD simulation or prepared dataset.
>
> 4\. Acquire or inspect event times, response amplitudes, fitted dynamic-synapse variables.
>
> 5\. Produce static-vs-dynamic comparison and model-selection statement.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: Current v3 repository does not establish board-level STP/STD; do not present the simulation as implemented hardware behaviour.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate record the current static response, then compare with a notebook stp/std simulation or prepared dataset. The reusable output is static-vs-dynamic comparison and model-selection statement.

**Sources / connections / priority.** Sources: \[T2 Chs.11–15; T3 Ch.5; T4 Chs.5,7; T5 Chs.5–6; T6 Ch.3; R1; G3\]. Natural follow-ons: CMP-09, STA-05. Development priority: Dataset-only/high-priority extension. Boundary: Current v3 repository does not establish board-level STP/STD; do not present the simulation as implemented hardware behaviour.
