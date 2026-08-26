# Curriculum catalogue

The catalogue contains 80 short modules across 14 families. Each entry records audience, duration, prerequisites, implementation mode, learning outcomes, reusable outputs and a specific interpretive boundary.

!!! warning "Specifications, not released handouts"
    The catalogue is a curriculum architecture. Do not treat nominal durations, settings or activities as validated classroom protocols until the module has passed the development and validation process described in [Development status](../development-status.md).

## Browse by family

| Family | Scope | Modules |
|---|---|---:|
| [FND — Foundations and orientation](foundations.md) | Foundations and orientation | 4 |
| [NPH — Neurophysiology](neurophysiology.md) | Neurophysiology | 7 |
| [EPH — Electrophysiology and instrumentation](electrophysiology.md) | Electrophysiology and instrumentation | 6 |
| [SYN — Synapses and integration](synapses.md) | Synapses and integration | 6 |
| [SEN — Sensory neuroscience](sensory-neuroscience.md) | Sensory neuroscience | 5 |
| [NET — Networks and neural computation](networks.md) | Networks and neural computation | 7 |
| [CMP — Computational neuroscience](computational-neuroscience.md) | Computational neuroscience | 9 |
| [DAT — Neural-data analysis](data-analysis.md) | Neural-data analysis | 8 |
| [STA — Statistics](statistics.md) | Statistics | 6 |
| [IMG — Calcium imaging](calcium-imaging.md) | Calcium imaging | 5 |
| [EXT — Extracellular recording](extracellular-recording.md) | Extracellular recording | 5 |
| [MET — Experimental methodology](experimental-methodology.md) | Experimental methodology | 6 |
| [EPI — Epistemology and scientific reasoning](epistemology.md) | Epistemology and scientific reasoning | 4 |
| [OSC — Outreach and educator practice](educator-practice.md) | Outreach and educator practice | 2 |

## Implementation relationship codes

| **Code** | **Relationship**                                             | **Use**                                                                               |
|----------|--------------------------------------------------------------|---------------------------------------------------------------------------------------|
| 1        | Direct physical implementation                               | Board controls and observable electronic behaviour are the main learning object.      |
| 2        | Direct implementation using board and GUI                    | Board behaviour is recorded, visualised or controlled through the GUI.                |
| 3        | Hybrid board and Jupyter implementation                      | Students acquire Spikeling data and analyse it in a notebook.                         |
| 4        | Multi-board implementation                                   | Two or more boards are physically connected into a circuit.                           |
| 5        | Recorded-dataset analysis                                    | A prepared or previously acquired dataset is the primary input.                       |
| 6        | GUI simulation workflow                                      | The imaging, extracellular or emulator workflow supplies synthetic data.              |
| 7        | Conceptual analogy using Spikeling                           | The platform supports a bounded analogy rather than direct biological implementation. |
| 8        | External computational comparison grounded in Spikeling data | Recorded data are compared with external equations, simulations or fitted models.     |
| 9        | Not presently suitable                                       | The concept should not be represented as supported by the current platform.           |

## Curriculum taxonomy and module contract

| **ID** | **Family**                            | **Scope**                                                                       |
|--------|---------------------------------------|---------------------------------------------------------------------------------|
| FND    | Foundations and orientation           | First encounter, representation, signals and platform literacy.                 |
| NPH    | Neurophysiology                       | Baseline, polarity, threshold, excitability and firing patterns.                |
| EPH    | Electrophysiology and instrumentation | Clamp modes, acquisition, noise, sampling, calibration and artefacts.           |
| SYN    | Synapses and integration              | Signed inputs, summation, timing, decay and plasticity comparisons.             |
| SEN    | Sensory neuroscience                  | Photodiode transduction, thresholds, adaptation, tuning and detection.          |
| NET    | Networks and neural computation       | Feedforward/recurrent motifs, inhibition, oscillation, synchrony and logic.     |
| CMP    | Computational neuroscience            | Izhikevich equations, parameter space, dynamical systems and inference.         |
| DAT    | Neural-data analysis                  | Import, QC, events, rates, temporal features, trial analysis and decoding.      |
| STA    | Statistics                            | Variability, uncertainty, comparisons, regression, power and multiplicity.      |
| IMG    | Calcium imaging                       | Forward models, sampling, ΔF/F, indicators, ROI concepts and deconvolution.     |
| EXT    | Extracellular recording               | Geometry, recording chain, detection, sorting and quality metrics.              |
| MET    | Experimental methodology              | Questions, operationalisation, controls, uncertainty and reproducible workflow. |
| EPI    | Epistemology and scientific reasoning | Evidence, model validity, causality, falsification and transparency.            |
| OSC    | Outreach and educator practice        | Public explanation, demonstrations and facilitation.                            |

### Standard module contract

- Identity: ID, title, family, concept statement and principal pedagogical theme.

- Audience: level, prior knowledge, required modules and suitable context.

- Logistics: 30/45/60 minutes, group size, boards, equipment, software and dataset requirement.

- Learning outcomes: three to five observable outcomes.

- Learning mode and stages: activity format plus Explore-to-Reproduce stages.

- Spikeling relationship: controls, interfaces, preset, variables, relationship code and explicit limit.

- Roadmap: prediction, configuration, manipulation, recording, analysis, interpretation and limitation.

- Inputs/outputs: artefacts designed for reuse by subsequent modules.

- Sources/connections/priority: evidence base, prerequisites, follow-ons, bundle compatibility and development priority.

## Complete module index

| **ID** | **Title**                                                          | **Min** | **Mode**                           | **Priority**                         |
|--------|--------------------------------------------------------------------|---------|------------------------------------|--------------------------------------|
| FND-01 | First contact: make a neuron respond                               | 30      | Exploratory board activity         | Core module                          |
| FND-02 | Neuron, model and instrument                                       | 45      | Methodology exercise               | Core module                          |
| FND-03 | The stimulus–response chain                                        | 30      | Guided exploration                 | Core module                          |
| FND-04 | Signals, variables and units                                       | 45      | Instructor-LED practical           | Core module                          |
| NPH-01 | Baseline and resting state                                         | 45      | Board and GUI experiment           | Core module                          |
| NPH-02 | Depolarisation and hyperpolarisation                               | 45      | Guided experiment                  | Core module                          |
| NPH-03 | Threshold and operational rheobase                                 | 60      | Board + GUI experiment             | Core module                          |
| NPH-04 | Input–output and firing-rate curve                                 | 60      | Hybrid board + Jupyter             | Core module                          |
| NPH-05 | Refractory and recovery behaviour                                  | 60      | Hybrid experiment                  | High-priority extension              |
| NPH-06 | Latency and adaptation                                             | 60      | Hybrid board + Jupyter             | Core module                          |
| NPH-07 | Atlas of neuronal firing diversity                                 | 60      | Board + GUI experiment             | Core module                          |
| EPH-01 | Current clamp: command and response                                | 45      | Guided experiment                  | Core module                          |
| EPH-02 | Model voltage clamp and controller current                         | 60      | Board + GUI experiment             | Advanced specialised module          |
| EPH-03 | Analogue, digital and event signals                                | 45      | Instructor-LED practical           | Core module                          |
| EPH-04 | Sampling and timebase validation                                   | 60      | Methodology + acquisition exercise | Core module                          |
| EPH-05 | Noise, filtering and signal-to-noise                               | 60      | Hybrid experiment                  | Core module                          |
| EPH-06 | Calibration, dynamic range and artefacts                           | 60      | Methodology experiment             | High-priority extension              |
| SYN-01 | From presynaptic event to postsynaptic current                     | 45      | Multi-board guided experiment      | Core module                          |
| SYN-02 | Excitation, inhibition and signed gain                             | 60      | Board + GUI experiment             | Core module                          |
| SYN-03 | Temporal summation                                                 | 60      | Hybrid multi-board experiment      | Core module                          |
| SYN-04 | Spatial summation with two inputs                                  | 60      | Multi-board experiment             | High-priority extension              |
| SYN-05 | Coincidence detection and input timing                             | 60      | Multi-board + Jupyter              | Advanced specialised module          |
| SYN-06 | Static synapses versus short-term plasticity                       | 60      | Simulation comparison              | Dataset-only/high-priority extension |
| SEN-01 | Photodiode sensory transduction                                    | 45      | Guided exploration                 | Core module                          |
| SEN-02 | Sensory threshold and dynamic range                                | 60      | Hybrid experiment                  | Core module                          |
| SEN-03 | ON and OFF response analogies                                      | 45      | Board + GUI experiment             | High-priority extension              |
| SEN-04 | Sensory adaptation and recovery                                    | 60      | Hybrid experiment                  | High-priority extension              |
| SEN-05 | Reliability, tuning and signal detection                           | 60      | Hybrid experiment/Jupyter          | Advanced specialised module          |
| NET-01 | Feedforward excitation                                             | 45      | Multi-board circuit                | Core module                          |
| NET-02 | Feedforward inhibition                                             | 60      | Multi-board experiment             | High-priority extension              |
| NET-03 | Recurrent excitation and persistence                               | 60      | Multi-board circuit                | Advanced specialised module          |
| NET-04 | Reciprocal and lateral inhibition                                  | 60      | Multi-board experiment             | High-priority extension              |
| NET-05 | Disinhibition                                                      | 60      | Multi-board circuit                | Advanced specialised module          |
| NET-06 | Oscillation, central-pattern-generation analogy and synchrony      | 60      | Multi-board + Jupyter              | Advanced specialised module          |
| NET-07 | Neural logic and temporal computation                              | 60      | Multi-board challenge              | High-priority extension              |
| CMP-01 | The Izhikevich equations as an executable model                    | 60      | Simulation comparison              | Core module                          |
| CMP-02 | Meaning of a, b, c and d                                           | 60      | Board + simulation                 | Core module                          |
| CMP-03 | Preset phenotype atlas                                             | 60      | Hybrid experiment                  | High-priority extension              |
| CMP-04 | Parameter sweeps and sensitivity                                   | 60      | Jupyter + board validation         | Advanced specialised module          |
| CMP-05 | Class 1 and Class 2 excitability                                   | 60      | Hybrid experiment                  | Advanced specialised module          |
| CMP-06 | Integrators and resonators                                         | 60      | Hybrid experiment                  | Advanced specialised module          |
| CMP-07 | Rebound, bistability and bursting regimes                          | 60      | Board + simulation                 | Advanced specialised module          |
| CMP-08 | Nullclines, phase portraits and dynamical interpretation           | 60      | External computational comparison  | Advanced specialised module          |
| CMP-09 | Mystery neuron: parameter inference and model comparison           | 60      | Jupyter inference module           | Advanced specialised module          |
| DAT-01 | Import, data structure and metadata                                | 45      | Jupyter analysis                   | Core module                          |
| DAT-02 | Plotting and quality control                                       | 45      | Jupyter analysis                   | Core module                          |
| DAT-03 | Spike detection and validation                                     | 60      | Jupyter analysis                   | Core module                          |
| DAT-04 | Firing rate and interspike intervals                               | 60      | Jupyter analysis                   | Core module                          |
| DAT-05 | Latency, adaptation and burst features                             | 60      | Jupyter analysis                   | High-priority extension              |
| DAT-06 | Trial alignment, rasters and PSTHs                                 | 60      | Jupyter analysis                   | High-priority extension              |
| DAT-07 | Correlation, cross-correlation, phase and synchrony                | 60      | Jupyter analysis                   | Advanced specialised module          |
| DAT-08 | Encoding, decoding and reproducible analysis pipeline              | 60      | Jupyter analysis                   | Advanced specialised module          |
| STA-01 | Distributions, variability and experimental units                  | 45      | Jupyter statistics                 | Core module                          |
| STA-02 | Confidence intervals and bootstrap uncertainty                     | 60      | Jupyter statistics                 | Core module                          |
| STA-03 | Paired comparisons and effect sizes                                | 60      | Jupyter statistics                 | High-priority extension              |
| STA-04 | Independent groups and non-parametric comparisons                  | 60      | Jupyter statistics                 | Advanced specialised module          |
| STA-05 | Regression and repeated-measures designs                           | 60      | Jupyter statistics                 | Advanced specialised module          |
| STA-06 | Multiplicity, power and statistical versus scientific significance | 60      | Jupyter methodology                | Advanced specialised module          |
| IMG-01 | Spikes to calcium to fluorescence                                  | 45      | GUI simulation workflow            | Core module                          |
| IMG-02 | Frame rate and temporal filtering                                  | 60      | GUI + Jupyter                      | High-priority extension              |
| IMG-03 | Baseline, ΔF/F, noise and bleaching                                | 60      | GUI simulation + analysis          | High-priority extension              |
| IMG-04 | Indicator kinetics, affinity and saturation                        | 60      | GUI simulation                     | Advanced specialised module          |
| IMG-05 | ROI, neuropil and spike inference against ground truth             | 60      | Prepared-dataset/Jupyter           | Advanced specialised module          |
| EXT-01 | Intracellular versus extracellular signals                         | 45      | GUI simulation                     | Core module                          |
| EXT-02 | Electrode geometry and tetrode projection                          | 60      | GUI simulation                     | High-priority extension              |
| EXT-03 | Recording chain: noise, hum, reference and filtering               | 60      | GUI simulation + analysis          | Advanced specialised module          |
| EXT-04 | Threshold detection and waveform features                          | 60      | GUI + Jupyter                      | High-priority extension              |
| EXT-05 | Clustering, spike sorting and quality metrics                      | 60      | Prepared-dataset/Jupyter           | Advanced specialised module          |
| MET-01 | From observation to a testable question                            | 30      | Methodology exercise               | Core module                          |
| MET-02 | Operational definitions and measurement                            | 45      | Methodology exercise               | Core module                          |
| MET-03 | Protocol design, controls and confounding                          | 60      | Methodology exercise               | Core module                          |
| MET-04 | Calibration, repeatability and uncertainty budget                  | 60      | Methodology experiment             | High-priority extension              |
| MET-05 | Exploratory versus confirmatory analysis                           | 60      | Methodology seminar + analysis     | Advanced specialised module          |
| MET-06 | Reproducible data, code and reporting                              | 60      | Reproducibility exercise           | Core module                          |
| EPI-01 | Observation, measurement and inference                             | 45      | Conceptual seminar                 | Core module                          |
| EPI-02 | Model validity, analogy and underdetermination                     | 60      | Epistemological seminar            | Core module                          |
| EPI-03 | Causality, falsification and negative results                      | 60      | Conceptual/methodology seminar     | Advanced specialised module          |
| EPI-04 | Open hardware, transparency and responsible communication          | 45      | Seminar/workshop                   | Core module                          |
| OSC-01 | Explain a spike without a black box                                | 30      | Outreach demonstration             | Outreach module                      |
| OSC-02 | Facilitate challenge cards and teacher-LED inquiry                 | 60      | Educator workshop                  | Outreach module                      |
