# Electrophysiology and instrumentation

!!! info "Curriculum status"
    These entries are architecture specifications, not final lesson plans. They define teaching intent, logistics, outputs and scientific boundaries; release-ready settings, worksheets, notebooks and answer keys still require empirical validation.

[Return to the module catalogue](index.md)


**Family source cluster:** \[T1 Ch.2; T2 Chs.9–10; M1; G3–G5, G9\]

## EPH-01 — Current clamp: command and response { #eph-01 }

| **Concept / theme**        | Current clamp controls input and observes model voltage as the dependent variable.                                                                                                                   |
|----------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Undergraduate. Formal practical, workshop or modular course. Prior modules: FND-04, NPH-02.                                                                                                          |
| **Logistics**              | 45 min; 2–3 per board; boards: 1; software: GUI; notebook for quantitative variants; prepared dataset: No; timing reference file for EPH-04. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | Guided experiment. Stages: 3–7, 10–11.                                                                                                                                                               |
| **Spikeling relationship** | 1 — Direct physical implementation; 2 — Direct board + GUI; 7 — Conceptual analogy                                                                                                                   |

**Learning outcomes.**

- Identify and predict the principal behaviour described in current clamp controls input and observes model voltage as the dependent variable.

- Configure or document apply defined current steps and document command, response and baseline and record command current a.u., Vm, total current.

- Measure, calculate or compare apply defined current steps and document command, response and baseline using an explicit operational rule.

- Interpret the result and state why no electrode, seal or access resistance is present; current is model-scaled

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Apply defined current steps and document command, response and baseline.
>
> 4\. Acquire or inspect command current a.u., Vm, total current.
>
> 5\. Produce current-clamp protocol diagram and trace set.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: No electrode, seal or access resistance is present; current is model-scaled.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate apply defined current steps and document command, response and baseline. The reusable output is current-clamp protocol diagram and trace set.

**Sources / connections / priority.** Sources: \[T1 Ch.2; T2 Chs.9–10; M1; G3–G5, G9\]. Natural follow-ons: NPH-03, EPH-02, MET-03. Development priority: Core module. Boundary: No electrode, seal or access resistance is present; current is model-scaled.

## EPH-02 — Model voltage clamp and controller current { #eph-02 }

| **Concept / theme**        | The GUI/firmware can command model voltage through feedback and expose the required controller current.                                                                                              |
|----------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Advanced undergraduate to master’s. Formal practical, workshop or modular course. Prior modules: EPH-01, FND-02.                                                                                     |
| **Logistics**              | 60 min; 2–3 per board; boards: 1; software: GUI; notebook for quantitative variants; prepared dataset: No; timing reference file for EPH-04. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | Board + GUI experiment. Stages: 3–7, 10–11.                                                                                                                                                          |
| **Spikeling relationship** | 2 — Direct board + GUI; 7 — Conceptual analogy; 8 — External computational comparison                                                                                                                |

**Learning outcomes.**

- Identify and predict the principal behaviour described in the GUI/firmware can command model voltage through feedback and expose the required controller current.

- Configure or document step holding commands and inspect Vm tracking and clamp current and record command Vm, actual Vm, i_clamp, controller limits.

- Measure, calculate or compare step holding commands and inspect Vm tracking and clamp current using an explicit operational rule.

- Interpret the result and state why not suitable for attributing currents to channels, conductances or reversal potentials

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Step holding commands and inspect Vm tracking and clamp current.
>
> 4\. Acquire or inspect command Vm, actual Vm, i_clamp, controller limits.
>
> 5\. Produce command–response plot and analogue-vs-biological clamp critique.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: Not suitable for attributing currents to channels, conductances or reversal potentials.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate step holding commands and inspect Vm tracking and clamp current. The reusable output is command–response plot and analogue-vs-biological clamp critique.

**Sources / connections / priority.** Sources: \[T1 Ch.2; T2 Chs.9–10; M1; G3–G5, G9\]. Natural follow-ons: CMP-08, EPI-02. Development priority: Advanced specialised module. Boundary: Not suitable for attributing currents to channels, conductances or reversal potentials.

## EPH-03 — Analogue, digital and event signals { #eph-03 }

| **Concept / theme**        | Continuous variables and discrete events support different measurements and network functions.                                                                                                       |
|----------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | School to undergraduate. Formal practical, workshop or modular course. Prior modules: FND-04.                                                                                                        |
| **Logistics**              | 45 min; 2–3 per board; boards: 1; software: GUI; notebook for quantitative variants; prepared dataset: No; timing reference file for EPH-04. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | Instructor-LED practical. Stages: 3–7, 10–11.                                                                                                                                                        |
| **Spikeling relationship** | 1 — Direct physical implementation; 2 — Direct board + GUI                                                                                                                                           |

**Learning outcomes.**

- Identify and predict the principal behaviour described in continuous variables and discrete events support different measurements and network functions.

- Configure or document observe analogue Vm, digital spike TTL, stimulus output and trigger and record amplitude, edge timing, event identity.

- Measure, calculate or compare observe analogue Vm, digital spike TTL, stimulus output and trigger using an explicit operational rule.

- Interpret the result and state why TTL represents an event; analogue output is scaled model Vm

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Observe analogue Vm, digital spike TTL, stimulus output and trigger.
>
> 4\. Acquire or inspect amplitude, edge timing, event identity.
>
> 5\. Produce signal-type comparison table and wiring diagram.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: TTL represents an event; analogue output is scaled model Vm.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate observe analogue Vm, digital spike TTL, stimulus output and trigger. The reusable output is signal-type comparison table and wiring diagram.

**Sources / connections / priority.** Sources: \[T1 Ch.2; T2 Chs.9–10; M1; G3–G5, G9\]. Natural follow-ons: NET-01, DAT-01, MET-02. Development priority: Core module. Boundary: TTL represents an event; analogue output is scaled model Vm.

## EPH-04 — Sampling and timebase validation { #eph-04 }

| **Concept / theme**        | Every temporal result depends on the true sample interval, timestamps and dropped-sample behaviour.                                                                                                  |
|----------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Undergraduate to doctoral methods. Formal practical, workshop or modular course. Prior modules: FND-04.                                                                                              |
| **Logistics**              | 60 min; 2–3 per board; boards: 1; software: GUI; notebook for quantitative variants; prepared dataset: No; timing reference file for EPH-04. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | Methodology + acquisition exercise. Stages: 3–7, 10–11.                                                                                                                                              |
| **Spikeling relationship** | 2 — Direct board + GUI; 3 — Hybrid board + Jupyter; 7 — Conceptual analogy                                                                                                                           |

**Learning outcomes.**

- Identify and predict the principal behaviour described in every temporal result depends on the true sample interval, timestamps and dropped-sample behaviour.

- Configure or document measure packet/sample cadence against a known periodic stimulus and compare firmware/GUI settings and exported time and record sample count, reference period, inferred dt, missing packets.

- Measure, calculate or compare measure packet/sample cadence against a known periodic stimulus and compare firmware/GUI settings and exported time using an explicit operational rule.

- Interpret the result and state why final reference method and acceptable tolerance require empirical validation on each release/computer

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Measure packet/sample cadence against a known periodic stimulus and compare firmware/GUI settings and exported time.
>
> 4\. Acquire or inspect sample count, reference period, inferred dt, missing packets.
>
> 5\. Produce validated timing certificate and metadata entry for the session.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: Final reference method and acceptable tolerance require empirical validation on each release/computer.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate measure packet/sample cadence against a known periodic stimulus and compare firmware/GUI settings and exported time. The reusable output is validated timing certificate and metadata entry for the session.

**Sources / connections / priority.** Sources: \[T1 Ch.2; T2 Chs.9–10; M1; G3–G5, G9\]. Natural follow-ons: All timing-dependent NPH, DAT, IMG and EXT modules. Development priority: Core module. Boundary: Final reference method and acceptable tolerance require empirical validation on each release/computer.

## EPH-05 — Noise, filtering and signal-to-noise { #eph-05 }

| **Concept / theme**        | Noise affects detection, estimation and reproducibility; filtering changes both noise and signal.                                                                                                    |
|----------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Undergraduate. Formal practical, workshop or modular course. Prior modules: DAT-02; EPH-04 for filter design.                                                                                        |
| **Logistics**              | 60 min; 2–3 per board; boards: 1; software: GUI; notebook for quantitative variants; prepared dataset: No; timing reference file for EPH-04. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | Hybrid experiment. Stages: 3–7, 10–11.                                                                                                                                                               |
| **Spikeling relationship** | 2 — Direct board + GUI; 3 — Hybrid board + Jupyter; 7 — Conceptual analogy                                                                                                                           |

**Learning outcomes.**

- Identify and predict the principal behaviour described in noise affects detection, estimation and reproducibility; filtering changes both noise and signal.

- Configure or document vary noise input; optionally compare raw and notebook-filtered traces and record baseline sd, spike detectability, waveform distortion.

- Measure, calculate or compare vary noise input; optionally compare raw and notebook-filtered traces using an explicit operational rule.

- Interpret the result and state why generated gaussian current is only one noise model; causal noise source cannot be inferred from trace shape alone

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Vary noise input; optionally compare raw and notebook-filtered traces.
>
> 4\. Acquire or inspect baseline sd, spike detectability, waveform distortion.
>
> 5\. Produce snr table and filter-justification note.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: Generated Gaussian current is only one noise model; causal noise source cannot be inferred from trace shape alone.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate vary noise input; optionally compare raw and notebook-filtered traces. The reusable output is snr table and filter-justification note.

**Sources / connections / priority.** Sources: \[T1 Ch.2; T2 Chs.9–10; M1; G3–G5, G9\]. Natural follow-ons: SEN-05, DAT-03, EXT-03. Development priority: Core module. Boundary: Generated Gaussian current is only one noise model; causal noise source cannot be inferred from trace shape alone.

## EPH-06 — Calibration, dynamic range and artefacts { #eph-06 }

| **Concept / theme**        | A measurement pipeline has baseline, range, saturation and clipping limits that must be documented.                                                                                                  |
|----------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audience / context**     | Advanced undergraduate. Formal practical, workshop or modular course. Prior modules: FND-04, EPH-04.                                                                                                 |
| **Logistics**              | 60 min; 2–3 per board; boards: 1; software: GUI; notebook for quantitative variants; prepared dataset: No; timing reference file for EPH-04. Equipment: Standard USB cable; worksheet/protocol card. |
| **Mode / stages**          | Methodology experiment. Stages: 3–7, 10–11.                                                                                                                                                          |
| **Spikeling relationship** | 1 — Direct physical implementation; 2 — Direct board + GUI; 3 — Hybrid board + Jupyter; 7 — Conceptual analogy                                                                                       |

**Learning outcomes.**

- Identify and predict the principal behaviour described in a measurement pipeline has baseline, range, saturation and clipping limits that must be documented.

- Configure or document probe low/high inputs, offsets and GUI display/export behaviour and record minimum/maximum readable values, clipping, baseline drift.

- Measure, calculate or compare probe low/high inputs, offsets and GUI display/export behaviour using an explicit operational rule.

- Interpret the result and state why the module characterises the platform, not biological membrane dynamic range

**Roadmap.**

> 1\. Initial prediction or classification.
>
> 2\. Configure the board, GUI, simulation or dataset and record metadata.
>
> 3\. Probe low/high inputs, offsets and GUI display/export behaviour.
>
> 4\. Acquire or inspect minimum/maximum readable values, clipping, baseline drift.
>
> 5\. Produce qc checklist and usable-range chart.
>
> 6\. Compare conditions or models and justify the chosen measurement.
>
> 7\. Answer a limitation question: The module characterises the platform, not biological membrane dynamic range.

**Inputs → outputs.** Students receive a configuration/protocol prompt, variable definitions and any required starter data. They manipulate probe low/high inputs, offsets and GUI display/export behaviour. The reusable output is qc checklist and usable-range chart.

**Sources / connections / priority.** Sources: \[T1 Ch.2; T2 Chs.9–10; M1; G3–G5, G9\]. Natural follow-ons: MET-04, DAT-02, EPI-01. Development priority: High-priority extension. Boundary: The module characterises the platform, not biological membrane dynamic range.
