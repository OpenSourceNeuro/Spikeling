# Networks and neural computation

!!! info "Curriculum status"
    These entries are architecture specifications, not final lesson plans. They define teaching intent, logistics, outputs and scientific boundaries; release-ready settings, worksheets, notebooks and answer keys still require empirical validation.

[Return to the module catalogue](index.md)


**Family source cluster:** \[T1 Ch.10; T5 Chs.7–8; T6 Parts III–IV; O1; G1, G3\]

## NET-01 — Feedforward excitation { #net-01 }

| **Concept / theme**        | A presynaptic board can drive a downstream board through a positive synaptic connection.                                                                                                  |
|----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | School to undergraduate. Formal practical, workshop or modular course. Prior modules: SYN-01, EPH-03.                                                                                     |
| **Logistics**              | 45 min; 4–8; boards: 2–4; software: Multi-recording GUI or multiple laptops; prepared dataset: Generated; exemplar traces useful. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | Multi-board circuit. Stages: 3–10, 11.                                                                                                                                                    |
| **Spikeling relationship** | 4 — Multi-board implementation; 2 — Direct board + GUI                                                                                                                                    |

**Learning outcomes.**

- Identify and predict the principal behaviour described in a presynaptic board can drive a downstream board through a positive synaptic connection.

- Configure or document wire axon output to downstream synapse and vary gain/input and record pre/post Vm, spike transfer, delay.

- Measure, calculate or compare wire axon output to downstream synapse and vary gain/input using an explicit operational rule.

- Interpret the result and state why connection represents functional event transmission, not a complete chemical synapse

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Wire axon output to downstream synapse and vary gain/input.
>
> 4\. Acquire or inspect pre/post Vm, spike transfer, delay.
>
> 5\. Produce network diagram and transfer-function trace.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: Connection represents functional event transmission, not a complete chemical synapse.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate wire axon output to downstream synapse and vary gain/input. The reusable output is network diagram and transfer-function trace.

**Sources / connections / priority.** Sources: \[T1 Ch.10; T5 Chs.7–8; T6 Parts III–IV; O1; G1, G3\]. Natural follow-ons: NET-02, NET-03. Development priority: Core module. Boundary: Connection represents functional event transmission, not a complete chemical synapse.

## NET-02 — Feedforward inhibition { #net-02 }

| **Concept / theme**        | An upstream board can suppress or delay a downstream response through negative gain.                                                                                                      |
|----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Undergraduate. Formal practical, workshop or modular course. Prior modules: SYN-02, NET-01.                                                                                               |
| **Logistics**              | 60 min; 4–8; boards: 2–4; software: Multi-recording GUI or multiple laptops; prepared dataset: Generated; exemplar traces useful. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | Multi-board experiment. Stages: 3–10, 11.                                                                                                                                                 |
| **Spikeling relationship** | 4 — Multi-board implementation; 3 — Hybrid board + Jupyter; 7 — Conceptual analogy                                                                                                        |

**Learning outcomes.**

- Identify and predict the principal behaviour described in an upstream board can suppress or delay a downstream response through negative gain.

- Configure or document add inhibitory pathway during a controlled downstream stimulus and record post spike count/latency with and without inhibition.

- Measure, calculate or compare add inhibitory pathway during a controlled downstream stimulus using an explicit operational rule.

- Interpret the result and state why no inhibitory transmitter or interneuron subtype is identified

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Add inhibitory pathway during a controlled downstream stimulus.
>
> 4\. Acquire or inspect post spike count/latency with and without inhibition.
>
> 5\. Produce controlled inhibition comparison.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: No inhibitory transmitter or interneuron subtype is identified.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate add inhibitory pathway during a controlled downstream stimulus. The reusable output is controlled inhibition comparison.

**Sources / connections / priority.** Sources: \[T1 Ch.10; T5 Chs.7–8; T6 Parts III–IV; O1; G1, G3\]. Natural follow-ons: NET-04, NET-05. Development priority: High-priority extension. Boundary: No inhibitory transmitter or interneuron subtype is identified.

## NET-03 — Recurrent excitation and persistence { #net-03 }

| **Concept / theme**        | Positive feedback can amplify, prolong or destabilise activity.                                                                                                                           |
|----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Advanced undergraduate. Formal practical, workshop or modular course. Prior modules: NET-01, EPH-06.                                                                                      |
| **Logistics**              | 60 min; 4–8; boards: 2–4; software: Multi-recording GUI or multiple laptops; prepared dataset: Generated; exemplar traces useful. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | Multi-board circuit. Stages: 3–10, 11.                                                                                                                                                    |
| **Spikeling relationship** | 4 — Multi-board implementation; 3 — Hybrid board + Jupyter; 7 — Conceptual analogy                                                                                                        |

**Learning outcomes.**

- Identify and predict the principal behaviour described in positive feedback can amplify, prolong or destabilise activity.

- Configure or document close a recurrent excitatory loop and vary gain while monitoring safety/limits and record activity duration, rate, saturation, recovery.

- Measure, calculate or compare close a recurrent excitatory loop and vary gain while monitoring safety/limits using an explicit operational rule.

- Interpret the result and state why electronic loop delays and clipping can dominate; do not equate persistence with biological working memory without qualification

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Close a recurrent excitatory loop and vary gain while monitoring safety/limits.
>
> 4\. Acquire or inspect activity duration, rate, saturation, recovery.
>
> 5\. Produce regime map with stable/unstable regions.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: Electronic loop delays and clipping can dominate; do not equate persistence with biological working memory without qualification.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate close a recurrent excitatory loop and vary gain while monitoring safety/limits. The reusable output is regime map with stable/unstable regions.

**Sources / connections / priority.** Sources: \[T1 Ch.10; T5 Chs.7–8; T6 Parts III–IV; O1; G1, G3\]. Natural follow-ons: NET-06, EPI-02. Development priority: Advanced specialised module. Boundary: Electronic loop delays and clipping can dominate; do not equate persistence with biological working memory without qualification.

## NET-04 — Reciprocal and lateral inhibition { #net-04 }

| **Concept / theme**        | Mutual inhibition can produce competition, alternation or winner-take-all-like behaviour.                                                                                                 |
|----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Advanced undergraduate to master’s. Formal practical, workshop or modular course. Prior modules: NET-02, SYN-04.                                                                          |
| **Logistics**              | 60 min; 4–8; boards: 2–4; software: Multi-recording GUI or multiple laptops; prepared dataset: Generated; exemplar traces useful. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | Multi-board experiment. Stages: 3–10, 11.                                                                                                                                                 |
| **Spikeling relationship** | 4 — Multi-board implementation; 3 — Hybrid board + Jupyter; 7 — Conceptual analogy                                                                                                        |

**Learning outcomes.**

- Identify and predict the principal behaviour described in mutual inhibition can produce competition, alternation or winner-take-all-like behaviour.

- Configure or document cross-connect two boards with negative gains and asymmetric drive and record winner identity, switching, rate difference.

- Measure, calculate or compare cross-connect two boards with negative gains and asymmetric drive using an explicit operational rule.

- Interpret the result and state why small deterministic circuit is an analogy to circuit motifs, not a cortical lateral-inhibition preparation

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Cross-connect two boards with negative gains and asymmetric drive.
>
> 4\. Acquire or inspect winner identity, switching, rate difference.
>
> 5\. Produce competition phase diagram.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: Small deterministic circuit is an analogy to circuit motifs, not a cortical lateral-inhibition preparation.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate cross-connect two boards with negative gains and asymmetric drive. The reusable output is competition phase diagram.

**Sources / connections / priority.** Sources: \[T1 Ch.10; T5 Chs.7–8; T6 Parts III–IV; O1; G1, G3\]. Natural follow-ons: NET-05, NET-06. Development priority: High-priority extension. Boundary: Small deterministic circuit is an analogy to circuit motifs, not a cortical lateral-inhibition preparation.

## NET-05 — Disinhibition { #net-05 }

| **Concept / theme**        | Inhibiting an inhibitory pathway can release a downstream unit from suppression.                                                                                                          |
|----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Master’s/intensive workshop. Formal practical, workshop or modular course. Prior modules: NET-02, NET-04, MET-03.                                                                         |
| **Logistics**              | 60 min; 4–8; boards: 2–4; software: Multi-recording GUI or multiple laptops; prepared dataset: Generated; exemplar traces useful. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | Multi-board circuit. Stages: 3–10, 11.                                                                                                                                                    |
| **Spikeling relationship** | 4 — Multi-board implementation; 3 — Hybrid board + Jupyter; 7 — Conceptual analogy                                                                                                        |

**Learning outcomes.**

- Identify and predict the principal behaviour described in inhibiting an inhibitory pathway can release a downstream unit from suppression.

- Configure or document construct a three-board motif and compare control, inhibition and disinhibition conditions and record downstream response across three conditions.

- Measure, calculate or compare construct a three-board motif and compare control, inhibition and disinhibition conditions using an explicit operational rule.

- Interpret the result and state why requires careful sign and baseline control; functional disinhibition does not identify biological pathways

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Construct a three-board motif and compare control, inhibition and disinhibition conditions.
>
> 4\. Acquire or inspect downstream response across three conditions.
>
> 5\. Produce logic/motif table and causal intervention diagram.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: Requires careful sign and baseline control; functional disinhibition does not identify biological pathways.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate construct a three-board motif and compare control, inhibition and disinhibition conditions. The reusable output is logic/motif table and causal intervention diagram.

**Sources / connections / priority.** Sources: \[T1 Ch.10; T5 Chs.7–8; T6 Parts III–IV; O1; G1, G3\]. Natural follow-ons: NET-07, EPI-03. Development priority: Advanced specialised module. Boundary: Requires careful sign and baseline control; functional disinhibition does not identify biological pathways.

## NET-06 — Oscillation, central-pattern-generation analogy and synchrony { #net-06 }

| **Concept / theme**        | Reciprocal or delayed loops can generate rhythmic activity whose frequency and phase can be measured.                                                                                     |
|----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Advanced undergraduate to master’s. Formal practical, workshop or modular course. Prior modules: NET-03 or NET-04, EPH-04.                                                                |
| **Logistics**              | 60 min; 4–8; boards: 2–4; software: Multi-recording GUI or multiple laptops; prepared dataset: Generated; exemplar traces useful. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | Multi-board + Jupyter. Stages: 3–10, 11.                                                                                                                                                  |
| **Spikeling relationship** | 4 — Multi-board implementation; 3 — Hybrid board + Jupyter; 8 — External computational comparison                                                                                         |

**Learning outcomes.**

- Identify and predict the principal behaviour described in reciprocal or delayed loops can generate rhythmic activity whose frequency and phase can be measured.

- Configure or document build an oscillatory two- or three-board loop and vary gains/input and record period, phase difference, regularity.

- Measure, calculate or compare build an oscillatory two- or three-board loop and vary gains/input using an explicit operational rule.

- Interpret the result and state why timing, latency and saturation require validation; cpg terminology is analogical

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Build an oscillatory two- or three-board loop and vary gains/input.
>
> 4\. Acquire or inspect period, phase difference, regularity.
>
> 5\. Produce oscillation trace, phase plot and stability note.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: Timing, latency and saturation require validation; CPG terminology is analogical.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate build an oscillatory two- or three-board loop and vary gains/input. The reusable output is oscillation trace, phase plot and stability note.

**Sources / connections / priority.** Sources: \[T1 Ch.10; T5 Chs.7–8; T6 Parts III–IV; O1; G1, G3\]. Natural follow-ons: DAT-07, CMP-08. Development priority: Advanced specialised module. Boundary: Timing, latency and saturation require validation; CPG terminology is analogical.

## NET-07 — Neural logic and temporal computation { #net-07 }

| **Concept / theme**        | Signed connections and timing can implement AND-, OR-, NOT-like and coincidence operations.                                                                                               |
|----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | School to master’s. Formal practical, workshop or modular course. Prior modules: SYN-04, SYN-05.                                                                                          |
| **Logistics**              | 60 min; 4–8; boards: 2–4; software: Multi-recording GUI or multiple laptops; prepared dataset: Generated; exemplar traces useful. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | Multi-board challenge. Stages: 3–10, 11.                                                                                                                                                  |
| **Spikeling relationship** | 4 — Multi-board implementation; 3 — Hybrid board + Jupyter; 7 — Conceptual analogy                                                                                                        |

**Learning outcomes.**

- Identify and predict the principal behaviour described in signed connections and timing can implement and-, or-, not-like and coincidence operations.

- Configure or document configure two-input motifs and test a truth table plus timing variants and record binary outputs, latency, error cases.

- Measure, calculate or compare configure two-input motifs and test a truth table plus timing variants using an explicit operational rule.

- Interpret the result and state why neural computation is graded and temporal; boolean labels are simplified operational descriptions

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Configure two-input motifs and test a truth table plus timing variants.
>
> 4\. Acquire or inspect binary outputs, latency, error cases.
>
> 5\. Produce truth table, timing diagram and limits critique.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: Neural computation is graded and temporal; Boolean labels are simplified operational descriptions.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate configure two-input motifs and test a truth table plus timing variants. The reusable output is truth table, timing diagram and limits critique.

**Sources / connections / priority.** Sources: \[T1 Ch.10; T5 Chs.7–8; T6 Parts III–IV; O1; G1, G3\]. Natural follow-ons: OSC-02, CMP-09. Development priority: High-priority extension. Boundary: Neural computation is graded and temporal; Boolean labels are simplified operational descriptions.
