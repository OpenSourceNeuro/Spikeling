# Sensory neuroscience

!!! info "Curriculum status"
    These entries are architecture specifications, not final lesson plans. They define teaching intent, logistics, outputs and scientific boundaries; release-ready settings, worksheets, notebooks and answer keys still require empirical validation.

[Return to the module catalogue](index.md)


**Family source cluster:** \[T2 Ch.17; T3 Chs.8–12; T4 Part II; T5 Chs.1–3; G3\]

## SEN-01 — Photodiode sensory transduction { #sen-01 }

| **Concept / theme**        | Light intensity is converted by the sensor/firmware path into a signed model current and neuronal response.                                                                                     |
|----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Outreach to undergraduate. Formal practical, workshop or modular course. Prior modules: FND-03, NPH-02.                                                                                         |
| **Logistics**              | 45 min; 2–4 per board; boards: 1; software: GUI; Jupyter for curves/statistics; prepared dataset: Generated; prepared repeats optional. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | Guided exploration. Stages: 1–10.                                                                                                                                                               |
| **Spikeling relationship** | 1 — Direct physical implementation; 2 — Direct board + GUI; 7 — Conceptual analogy                                                                                                              |

**Learning outcomes.**

- Identify and predict the principal behaviour described in light intensity is converted by the sensor/firmware path into a signed model current and neuronal response.

- Configure or document vary controlled illumination while recording sensor-driven current and Vm and record light condition, photodiode current, Vm, spikes.

- Measure, calculate or compare vary controlled illumination while recording sensor-driven current and Vm using an explicit operational rule.

- Interpret the result and state why the photodiode pathway is an electronic sensory analogue, not a retinal phototransduction pathway

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Vary controlled illumination while recording sensor-driven current and Vm.
>
> 4\. Acquire or inspect light condition, photodiode current, Vm, spikes.
>
> 5\. Produce stimulus–transduction–response diagram and trace set.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: The photodiode pathway is an electronic sensory analogue, not a retinal phototransduction pathway.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate vary controlled illumination while recording sensor-driven current and Vm. The reusable output is stimulus–transduction–response diagram and trace set.

**Sources / connections / priority.** Sources: \[T2 Ch.17; T3 Chs.8–12; T4 Part II; T5 Chs.1–3; G3\]. Natural follow-ons: SEN-02, SEN-04. Development priority: Core module. Boundary: The photodiode pathway is an electronic sensory analogue, not a retinal phototransduction pathway.

## SEN-02 — Sensory threshold and dynamic range { #sen-02 }

| **Concept / theme**        | A sensory response curve has detection threshold, responsive range and saturation.                                                                                                              |
|----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Undergraduate. Formal practical, workshop or modular course. Prior modules: SEN-01, DAT-03, EPH-04.                                                                                             |
| **Logistics**              | 60 min; 2–4 per board; boards: 1; software: GUI; Jupyter for curves/statistics; prepared dataset: Generated; prepared repeats optional. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | Hybrid experiment. Stages: 1–10.                                                                                                                                                                |
| **Spikeling relationship** | 2 — Direct board + GUI; 3 — Hybrid board + Jupyter; 7 — Conceptual analogy                                                                                                                      |

**Learning outcomes.**

- Identify and predict the principal behaviour described in a sensory response curve has detection threshold, responsive range and saturation.

- Configure or document present graded light levels in controlled order and estimate response features and record light level proxy, current, spike response.

- Measure, calculate or compare present graded light levels in controlled order and estimate response features using an explicit operational rule.

- Interpret the result and state why light must be measured or operationally standardised; uncalibrated distance/brightness is not an absolute irradiance

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Present graded light levels in controlled order and estimate response features.
>
> 4\. Acquire or inspect light level proxy, current, spike response.
>
> 5\. Produce sensory response curve with threshold/range.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: Light must be measured or operationally standardised; uncalibrated distance/brightness is not an absolute irradiance.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate present graded light levels in controlled order and estimate response features. The reusable output is sensory response curve with threshold/range.

**Sources / connections / priority.** Sources: \[T2 Ch.17; T3 Chs.8–12; T4 Part II; T5 Chs.1–3; G3\]. Natural follow-ons: SEN-05, STA-02. Development priority: Core module. Boundary: Light must be measured or operationally standardised; uncalibrated distance/brightness is not an absolute irradiance.

## SEN-03 — ON and OFF response analogies { #sen-03 }

| **Concept / theme**        | Signed sensor gain and changes in illumination can create ON-like or OFF-like response patterns.                                                                                                |
|----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | School to undergraduate. Formal practical, workshop or modular course. Prior modules: SEN-01.                                                                                                   |
| **Logistics**              | 45 min; 2–4 per board; boards: 1; software: GUI; Jupyter for curves/statistics; prepared dataset: Generated; prepared repeats optional. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | Board + GUI experiment. Stages: 1–10.                                                                                                                                                           |
| **Spikeling relationship** | 1 — Direct physical implementation; 2 — Direct board + GUI; 3 — Hybrid board + Jupyter; 7 — Conceptual analogy                                                                                  |

**Learning outcomes.**

- Identify and predict the principal behaviour described in signed sensor gain and changes in illumination can create on-like or off-like response patterns.

- Configure or document compare positive/negative gain and light-on/light-off transitions and record transition-aligned Vm/spikes and photodiode current.

- Measure, calculate or compare compare positive/negative gain and light-on/light-off transitions using an explicit operational rule.

- Interpret the result and state why no claim should be made about retinal on/off bipolar-cell circuitry

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Compare positive/negative gain and light-on/light-off transitions.
>
> 4\. Acquire or inspect transition-aligned Vm/spikes and photodiode current.
>
> 5\. Produce on/off response panel and analogy-limit statement.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: No claim should be made about retinal ON/OFF bipolar-cell circuitry.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate compare positive/negative gain and light-on/light-off transitions. The reusable output is on/off response panel and analogy-limit statement.

**Sources / connections / priority.** Sources: \[T2 Ch.17; T3 Chs.8–12; T4 Part II; T5 Chs.1–3; G3\]. Natural follow-ons: SEN-04, DAT-06. Development priority: High-priority extension. Boundary: No claim should be made about retinal ON/OFF bipolar-cell circuitry.

## SEN-04 — Sensory adaptation and recovery { #sen-04 }

| **Concept / theme**        | Response changes during sustained or repeated illumination can be quantified as adaptation/recovery in the implemented sensor pathway.                                                          |
|----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Undergraduate. Formal practical, workshop or modular course. Prior modules: SEN-01, EPH-04.                                                                                                     |
| **Logistics**              | 60 min; 2–4 per board; boards: 1; software: GUI; Jupyter for curves/statistics; prepared dataset: Generated; prepared repeats optional. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | Hybrid experiment. Stages: 1–10.                                                                                                                                                                |
| **Spikeling relationship** | 2 — Direct board + GUI; 3 — Hybrid board + Jupyter; 7 — Conceptual analogy                                                                                                                      |

**Learning outcomes.**

- Identify and predict the principal behaviour described in response changes during sustained or repeated illumination can be quantified as adaptation/recovery in the implemented sensor pathway.

- Configure or document vary stimulus duration and inter-stimulus interval and record peak/steady response, recovery ratio, latency.

- Measure, calculate or compare vary stimulus duration and inter-stimulus interval using an explicit operational rule.

- Interpret the result and state why separate photodiode firmware decay/recovery, neuron adaptation and illumination artefacts in interpretation

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Vary stimulus duration and inter-stimulus interval.
>
> 4\. Acquire or inspect peak/steady response, recovery ratio, latency.
>
> 5\. Produce adaptation and recovery curves.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: Separate photodiode firmware decay/recovery, neuron adaptation and illumination artefacts in interpretation.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate vary stimulus duration and inter-stimulus interval. The reusable output is adaptation and recovery curves.

**Sources / connections / priority.** Sources: \[T2 Ch.17; T3 Chs.8–12; T4 Part II; T5 Chs.1–3; G3\]. Natural follow-ons: NPH-06, STA-03. Development priority: High-priority extension. Boundary: Separate photodiode firmware decay/recovery, neuron adaptation and illumination artefacts in interpretation.

## SEN-05 — Reliability, tuning and signal detection { #sen-05 }

| **Concept / theme**        | Repeated noisy responses support operational detection, reliability and simple tuning analyses.                                                                                                 |
|----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Advanced undergraduate to master’s. Formal practical, workshop or modular course. Prior modules: SEN-02, DAT-06, STA-01.                                                                        |
| **Logistics**              | 60 min; 2–4 per board; boards: 1; software: GUI; Jupyter for curves/statistics; prepared dataset: Generated; prepared repeats optional. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | Hybrid experiment/Jupyter. Stages: 1–10.                                                                                                                                                        |
| **Spikeling relationship** | 3 — Hybrid board + Jupyter; 5 — Recorded-dataset analysis; 7 — Conceptual analogy; 8 — External computational comparison                                                                        |

**Learning outcomes.**

- Identify and predict the principal behaviour described in repeated noisy responses support operational detection, reliability and simple tuning analyses.

- Configure or document repeat several stimulus conditions under varied noise; classify or detect responses and record trial responses, hit/false-alarm rates, variability.

- Measure, calculate or compare repeat several stimulus conditions under varied noise; classify or detect responses using an explicit operational rule.

- Interpret the result and state why population coding is only justified with multiple boards or repeated synthetic units; biological signal-detection claims remain bounded

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Repeat several stimulus conditions under varied noise; classify or detect responses.
>
> 4\. Acquire or inspect trial responses, hit/false-alarm rates, variability.
>
> 5\. Produce reliability plot, tuning curve or simple decoder performance.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: Population coding is only justified with multiple boards or repeated synthetic units; biological signal-detection claims remain bounded.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate repeat several stimulus conditions under varied noise; classify or detect responses. The reusable output is reliability plot, tuning curve or simple decoder performance.

**Sources / connections / priority.** Sources: \[T2 Ch.17; T3 Chs.8–12; T4 Part II; T5 Chs.1–3; G3\]. Natural follow-ons: DAT-08, STA-06. Development priority: Advanced specialised module. Boundary: Population coding is only justified with multiple boards or repeated synthetic units; biological signal-detection claims remain bounded.
