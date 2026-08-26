# Scope, evidence and teaching limits

This page records the evidential basis for the curriculum and the limits that must accompany biological interpretation. It should be read before adapting or releasing a module.

## Executive summary

| **Core recommendation.** Develop Spikeling as a curriculum library with a common module contract, not as a single syllabus. The proposed library contains 80 modules across 14 families, each designed for 30, 45 or 60 minutes and tagged by implementation mode, prerequisite, output, evidence level and interpretive boundary. |
|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

- The platform has strongest direct coverage for controlled stimulation, phenomenological membrane-voltage behaviour, threshold and firing-pattern exploration, signed synaptic integration, photodiode-driven sensory analogies, physical multi-board motifs, recording/export, and comparison of known electrical ground truth with synthetic fluorescence or extracellular signals.

- Its strongest advanced pedagogical value is methodological: students can move from manipulation to protocol design, data acquisition, analysis, model comparison, uncertainty and reproducibility while retaining visibility into the instrument and software pipeline.

- Biophysical claims must remain bounded. Spikeling does not identify ion channels, receptors, transmitters or molecular mechanisms; model current is not a calibrated biological current; the voltage-clamp mode is a numerical PI-control analogue; imaging and extracellular modes are reduced forward simulations; and the present v3 firmware implements static event-driven synaptic currents with decay, not a demonstrated STP/STD state model.

- A mandatory timing-validation gateway is recommended before any module that interprets latency, frequency, interspike intervals, spectra, phase or kinetic constants. Current GUI code uses a fixed 0.1 ms fallback/export interval and built-in rate calculations assume 10 kHz, whereas firmware update periods are configurable and default to 2,000 µs. This is a curriculum-development validation issue, not a request to change firmware.

- The first development wave should establish 18 core modules spanning first contact, stimulation and threshold, current clamp, timing/QC, synapses, photodiode sensory work, experimental design, data import/QC, spike detection, firing-rate analysis, uncertainty, Izhikevich parameters, multi-board feedforward networks, imaging forward models, extracellular geometry and epistemic limits.

### How to read and use this architecture

| **Element**       | **Meaning**                                                                                                                    |
|-------------------|--------------------------------------------------------------------------------------------------------------------------------|
| Module family     | A stable conceptual namespace such as NPH, SYN, DAT or MET.                                                                    |
| Relationship code | One of nine implementation relationships defined by the user; a module may carry a primary and secondary code.                 |
| Stages            | The Explore-to-Reproduce progression addressed by the module.                                                                  |
| Output            | A reusable artefact: dataset, plot, protocol, parameter table, conclusion, critique or explanation.                            |
| Priority          | Core, high-priority extension, advanced specialised, outreach, dataset-only, future possibility or not recommended.            |
| Validation flag   | A practical behaviour or quantitative scale that must be checked on the target release before final protocol values are fixed. |

## Research method and evidential hierarchy

| **Source hierarchy.** Textbooks and primary/methods papers establish neuroscience content; official project documentation establishes software workflows; the current Spikeling repository establishes platform behaviour. Where these conflict, repository behaviour governs what can be taught directly, while neuroscience sources govern interpretation and limitations. |
|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

| **Source class**            | **Use in this architecture**                                                      | **Examples**                                                                                                   |
|-----------------------------|-----------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------|
| Current implementation      | Ground truth for controls, variables, packet fields, modes and known limitations. | Spikeling firmware, GUI code and repository documentation \[G1–G9\].                                           |
| Major textbooks             | Conceptual spine, terminology, progression and biological context.                | Izhikevich \[T1\], Kandel \[T2\], Bear \[T3\], Purves \[T4\], Dayan & Abbott \[T5\], Neuronal Dynamics \[T6\]. |
| Primary research            | Original model or measurement claims and known-ground-truth comparisons.          | Izhikevich model \[P1\], calcium inference \[P2\], extracellular waveform \[P3\], tetrode accuracy \[P4\].     |
| Reviews/methods             | Experimental caveats, technique interpretation and methodological consensus.      | Axon Guide \[M1\], STP review \[R1\], estimation/statistics \[R4–R5\].                                         |
| Official software/data docs | Modern analysis practice and reusable teaching workflows.                         | Neuromatch \[O1\], SpikeInterface \[O2\], Suite2p \[O3\], Open Ephys \[O4\], NWB \[O5\].                       |
| Open-science guidance       | Protocol transparency, data management and reproducibility.                       | NC3Rs EDA \[O6\], The Turing Way \[O7\], FAIR principles \[P5\].                                               |

**Edition policy.** Page references are supplied when an edition and pagination are verifiable. Izhikevich references use the 2007 MIT Press edition; Bear references use the enhanced fourth edition (2020); Kandel references use the sixth edition. For sources whose pagination varies across print/e-book formats, chapter and section references are used rather than invented page numbers.

## Source map by curriculum domain

| **Domain**                                            | **Strongest sources**                                                                                                         | **Contribution and interpretive note**                                                                                                                                      |
|-------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Neuron, model and representation                      | T1 Ch.1 pp.1–24, esp. §§1.1.1–1.1.4 and 1.2.4–1.2.5; T2 Chs.3,5; T3 Chs.1–2; O1 Model Types.                                  | Separates biological neuron, mathematical model and experimental representation; supports explicit discussion of “what/how/why” models.                                     |
| Membrane potential and passive properties             | T1 Ch.2 pp.25–52, §§2.1.1–2.1.5; T2 Chs.8–9; T3 Ch.3; T4 Chs.2–4.                                                             | Biological electrochemical gradients, equivalent circuits and passive properties. With Spikeling, use as conceptual grounding, not evidence of channel-specific mechanisms. |
| Action potentials, threshold and refractory behaviour | T1 Ch.1 §§1.1.1–1.1.2; Chs.3 and 7; T2 Ch.10; T3 Ch.4; T4 Chs.2–3.                                                            | Contrasts fixed threshold language with dynamical threshold/excitability; provides biological context for phenomenological spike events.                                    |
| Current and voltage clamp                             | T1 §2.1.5 pp.30–32; T2 Chs.9–10; M1 and official current/voltage-clamp primers.                                               | Defines independent/dependent variables and real experimental limitations. Spikeling current clamp is direct model manipulation; voltage clamp is a numerical analogue.     |
| Neuronal diversity and Izhikevich presets             | T1 Chs.7–9, pp.215–384; P1 Fig.1 and equations; G2 preset table.                                                              | Maps excitability, tonic/phasic spiking, bursting, resonance, rebound, bistability and adaptation to implemented presets without assigning molecular causes.                |
| Synaptic integration                                  | T2 Chs.11–15; T3 Ch.5; T4 Chs.5 and 7; T5 Chs.5–6; T6 Ch.3.                                                                   | Provides EPSP/IPSP, summation and integration concepts. Spikeling represents event-driven signed currents, not transmitter or receptor biology.                             |
| Short-term plasticity                                 | R1 Zucker & Regehr; T6 §3.1.3 and Ch.19; O1 dynamic-synapse tutorial.                                                         | Supports simulation and dataset comparison. Current v3 repository evidence does not establish an STP/STD state implementation.                                              |
| Sensory coding                                        | T2 Ch.17 and modality chapters; T3 Chs.8–12; T4 Part II; T5 Chs.1–3; O1 GLM tutorial.                                         | Stimulus–response curves, thresholds, reliability, receptive-field and encoding concepts. Photodiode modules remain reduced transduction analogies.                         |
| Networks and computation                              | T1 Ch.10; T5 Chs.7–8; T6 Parts III–IV; O1 Wilson–Cowan and dynamical-systems tutorials.                                       | Feedforward/recurrent motifs, inhibition, oscillation, synchronization and population ideas; physical multi-board circuits provide small-network embodiments.               |
| Spike-train analysis                                  | T5 Chs.1–4; T6 Ch.7 and Chs.10–11; O1 signal-processing and GLM tutorials.                                                    | Firing rate, ISI, PSTH, variability, encoding/decoding and model fitting; requires validated time metadata.                                                                 |
| Statistics and inference                              | O1 statistics/model-fitting tutorials; R4 Estimation for Better Inference; R5 New Statistics for Neuroscience Majors; O6 EDA. | Progresses from distributions to effect sizes, intervals, paired/independent designs, regression, power and multiple-comparison control.                                    |
| Calcium imaging                                       | P2 Vogelstein et al.; O3 Suite2p extraction/neuropil/deconvolution; T2 Ch.6 imaging overview; G6.                             | Forward transformation and inverse inference, temporal filtering, ΔF/F, saturation, noise and ground-truth comparison.                                                      |
| Extracellular recording                               | P3 Gold et al.; P4 Harris et al.; O2 SpikeInterface; O4 Open Ephys; G7.                                                       | Waveform origin, geometry, tetrode advantages, detection, sorting and uncertainty. GUI signals are pedagogical µV-like simulations.                                         |
| Experimental design and reproducibility               | O6 NC3Rs EDA; O7 The Turing Way; P5 FAIR; O5 NWB.                                                                             | Questions, variables, controls, randomisation, blinding, metadata, reproducible code/data and standardised neurophysiology formats.                                         |
| Epistemology and responsible communication            | T1 Ch.1; O1 Model Types; O7; R4.                                                                                              | Observation versus inference, model validity, underdetermination, causal restraint, negative results and transparent reporting.                                             |

### Terminological differences that must be taught explicitly

- Threshold: introductory texts often present a convenient voltage threshold; dynamical-systems treatments emphasise state, trajectory and stimulus history. Spikeling permits both pedagogical levels, but students should not infer a universal biological threshold voltage.

- Current: electrophysiology texts use calibrated current units; current terms in Spikeling are model or arbitrary units unless a specific interface is independently calibrated. Labels must not be translated into pA or nA by analogy.

- Voltage clamp: biological voltage clamp measures the current required to control a real membrane, with access resistance, capacitance and space-clamp limitations. Spikeling’s mode controls the model variable through a PI controller and reports controller current.

- Synaptic weight: in Spikeling it is a signed scalar applied to an event-driven current trace. It does not establish neurotransmitter identity, conductance, reversal potential, release probability or receptor kinetics.

- Calcium event and extracellular unit: both are inferred variables in biological experiments. The GUI provides known synthetic ground truth, which is pedagogically valuable precisely because the inference can be checked.

## Current Spikeling implementation audit

| **Audit basis.** The implementation audit uses the current main-branch snapshot identified above. Firmware, GUI and documentation are treated as executable specifications. Earlier reports and teaching analyses inform organisation but do not override current code behaviour. |
|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

| **Capability**                    | **Interface**                                     | **Representation**                                                               | **Level**                   | **Data output**                                  | **Interpretive limit**                                                                   |
|-----------------------------------|---------------------------------------------------|----------------------------------------------------------------------------------|-----------------------------|--------------------------------------------------|------------------------------------------------------------------------------------------|
| Physical current control          | Patch/current input and GUI override              | Current-clamp command applied directly to the Izhikevich-style model.            | Intro–Master                | Vm, total current, trigger                       | Model/arbitrary current units; not calibrated biological injection.                      |
| Positive and negative stimulation | Signed stimulus DAC/current path                  | Depolarising or hyperpolarising model input.                                     | School–Master               | Stimulus, Vm, total current                      | Polarity is direct; biological ionic mechanism is not.                                   |
| Stimulus frequency                | Physical/GUI square-wave control                  | Repeated controlled stimulation and timing protocols.                            | School–Master               | Stimulus, trigger, Vm                            | Frequency/latency claims require timebase validation.                                    |
| Current clamp                     | Physical knob or GUI command                      | Independent current-like command, dependent model Vm.                            | Undergrad–Master            | Vm and total current                             | Phenomenological model, not cell membrane impedance measurement.                         |
| Model voltage clamp               | GUI/firmware PI control                           | Command model Vm and observe controller current.                                 | Advanced undergrad–Doctoral | Vm command, clamp current                        | Analogue only; no ion-current separation, access resistance or space clamp.              |
| Noise                             | Physical/GUI Gaussian current                     | Manipulate variability and reliability.                                          | School–Master               | Noise contribution via total current, Vm, spikes | Noise source is generated model current; not a complete biological noise taxonomy.       |
| Photodiode                        | Light sensor, signed gain, decay/recovery         | Sensory transduction analogue with adaptive current.                             | Outreach–Master             | Photodiode-driven current, Vm, spikes            | Not a retinal photoreceptor or specified transduction cascade.                           |
| Two synaptic inputs               | Digital spike events plus analogue presynaptic Vm | Two event-driven decaying currents with signed gain.                             | Undergrad–Master            | Pre-Vm, synaptic currents, post-Vm               | Static current trace; no demonstrated release probability or STP/STD state.              |
| Signed synaptic gains             | Centre-detent controls/GUI                        | Excitatory or inhibitory effect by sign.                                         | School–Master               | Synaptic current and post-Vm                     | Sign is functional, not receptor or reversal-potential evidence.                         |
| Analogue Vm output                | DAC axon output                                   | Continuous model voltage for external display/connection.                        | School–Master               | Vm analogue output                               | Scaled electronic output of a model variable.                                            |
| Digital spike output              | TTL axon output                                   | Discrete event communication and network wiring.                                 | Outreach–Master             | Spike TTL                                        | Spike event is a model threshold/reset event.                                            |
| Multiple boards                   | Physical axon-to-synapse cabling                  | Feedforward, recurrent, inhibitory and oscillatory motifs.                       | School–Doctoral             | Multi-neuron Vm, spikes, synaptic currents       | Small deterministic/pseudostochastic network; topology and delays are hardware-specific. |
| GUI recording                     | Binary stream to CSV                              | Record Vm, stimulus, total current, synapse variables and trigger.               | Undergrad–Master            | CSV                                              | Metadata and timebase require explicit QC.                                               |
| Calcium-imaging simulation        | GUI forward model                                 | Vm→spike→Ca→indicator→F/ΔF/F with noise, kinetics and frame sampling.            | Undergrad–Doctoral          | Vm, Ca, fluorescence, frames                     | Synthetic forward model; no real optics, motion or tissue.                               |
| Extracellular/tetrode simulation  | GUI reduced forward model                         | Known spike times→4 contacts with geometry, noise, hum, reference and filtering. | Advanced undergrad–Doctoral | Ground truth, 4 channels, detections             | µV-like pedagogical units; not morphology-based field solution.                          |
| Data-analysis workflow            | GUI import/plot/detection and external Python     | Raw inspection, threshold detection and further notebook analysis.               | Undergrad–Master            | Plots, spikes, rates                             | Built-in rate computation assumes fixed sample scale; use validated notebooks.           |
| Custom parameters                 | GUI/serial a,b,c,d                                | Construct and compare custom Izhikevich-style neurons.                           | Undergrad–Doctoral          | Parameter set, traces, feature table             | Current custom import retains existing v_rest unless separately set.                     |
| Twenty presets                    | Firmware preset table                             | Named firing-pattern starting points.                                            | School–Master               | Preset identity and recordings                   | Preset labels describe phenomenology, not cell type or channel mechanism.                |
| Custom stimulus files             | GUI CSV waveform streaming                        | Steps, arbitrary sequences and comparison protocols.                             | Undergrad–Master            | Stimulus waveform and response                   | Playback cadence is packet-linked; timing must be validated.                             |
| Trigger channel                   | Digital event in stream                           | Trial alignment and protocol segmentation.                                       | Undergrad–Master            | Trigger                                          | Verify edge timing and export alignment before inferential use.                          |

### Implementation findings that change curriculum design

| **Timing and rate metadata — validation required** Firmware update period is configurable and defaults to 2,000 µs. Several GUI paths use a fixed 0.1 ms fallback/export interval; the built-in analysis calculates rates from sample indices using a 10 kHz scale. Time-derived modules therefore require a validated sample interval stored as metadata before development of final values. |
|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

| **Voltage clamp — computational analogue** The firmware PI controller computes a clamp current that holds the model voltage; the normal spike reset is disabled in this mode. It is suitable for control-system and I–V analogies, but not for channel identification. |
|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

| **Synaptic plasticity — not demonstrated in current v3** The implemented synaptic state accumulates signed current on rising edges and decays it each update. Repository searches and code inspection did not identify facilitation/depression resource variables. STP/STD belongs in simulation or comparison modules unless separate validated material is supplied. |
|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

| **Imaging parameter application — validate presets** The imaging forward model is rich, but one GUI method appears to interchange dF/F maximum, rise and decay values when applying indicator settings. Indicator-comparison protocols should verify the actual active values rather than trust labels alone. |
|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

| **Extracellular sampling — use ground-truth/simulation carefully** The extracellular model defines a 0.1 ms fallback, derives a 10 kHz nominal sample rate and offers a 300–3000 Hz band. Live hardware packet timing may differ; geometry, waveform, detection and sorting concepts remain valuable, while spectral claims require validation or prepared timestamped simulation data. |
|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

## Coverage and gap analysis

| **Topic**                                     | **Direct coverage**                            | **Best hybrid use**                      | **Prepared data need**                   | **Do not claim**                                                      |
|-----------------------------------------------|------------------------------------------------|------------------------------------------|------------------------------------------|-----------------------------------------------------------------------|
| Stimulus polarity, threshold, firing patterns | Strong direct board/GUI coverage               | Hybrid quantitative analysis             | —                                        | Biophysical mechanism attribution                                     |
| Current clamp                                 | Direct model manipulation                      | Jupyter response curves                  | —                                        | Real electrode/seal/access-resistance training                        |
| Voltage clamp                                 | Controller analogue only                       | Control-system and model I–V comparisons | Prepared biological traces recommended   | Channel-specific current isolation                                    |
| Synaptic excitation/inhibition and summation  | Strong functional coverage                     | Multi-board/Jupyter                      | —                                        | Transmitter, receptor, reversal potential and quantal release         |
| STP/STD                                       | No demonstrated current-board state            | Notebook simulation and comparison       | Prepared biological/synthetic datasets   | Claiming board implements plasticity without validation               |
| Networks and logic                            | Strong small-network physical motifs           | Timing/statistics notebooks              | —                                        | Large-population or anatomical circuit realism                        |
| Sensory transduction                          | Direct photodiode electronics; bounded analogy | Curves, adaptation and detection         | Prepared repeats/population examples     | Specific retinal/auditory receptor mechanisms                         |
| Izhikevich computational neuroscience         | Strong direct parameter/preset coverage        | Simulation, phase portraits, fitting     | —                                        | Interpreting parameters as unique ionic mechanisms                    |
| Neural data analysis                          | Strong CSV/Jupyter pathway                     | Advanced modelling/statistics            | Prepared datasets for breadth            | Unvalidated temporal measures                                         |
| Calcium imaging                               | Strong GUI forward simulation                  | Inference/ground-truth comparison        | Prepared movie/ROI data for segmentation | Real optics, motion correction, tissue/neuropil without external data |
| Extracellular/tetrode                         | Strong reduced GUI simulation                  | Detection, sorting, quality metrics      | Prepared timestamped recordings          | Real field physics, drift, hardware impedance, LFP source inference   |
| Methodology/open science                      | Strong cross-cutting coverage                  | Reproducible notebooks/data packages     | —                                        | Assuming openness alone guarantees validity                           |

### Important neuroscience subjects not presently supported as direct Spikeling claims

- Identification or pharmacological manipulation of specific ion channels, pumps, receptors, neurotransmitters or second-messenger pathways.

- Quantitative membrane capacitance, input resistance, series resistance, junction potentials, seal quality, space clamp or dendritic cable properties as real cellular measurements.

- Quantal synaptic release, vesicle depletion, release probability or long-term potentiation/depression from the current board alone.

- Morphology-dependent action-potential propagation, axonal conduction velocity or compartmental dendritic computation.

- Anatomical receptive fields, real sensory transduction cascades or genuine population coding without additional data/boards and carefully bounded analogy.

- Real calcium-microscopy motion correction, optical point-spread functions, ROI segmentation and neuropil contamination without external prepared data.

- Real extracellular volume conduction, electrode impedance, tissue damage, drift, LFP source localisation or definitive unit identity.

- Causal biological mechanism from model behaviour, correlation, successful fitting or statistical significance.

## Architectural conclusions

- The most coherent Spikeling curriculum is not organised solely by neuroscience topics. It should be dual-indexed by concept family and by scientific workflow stage, allowing the same threshold, synapse or sensory dataset to reappear in methodology, data-analysis, statistics and epistemology modules.

- The platform is particularly valuable when it makes transformations visible: input to model current, model state to event, event to network input, electrical activity to fluorescence, and intracellular ground truth to extracellular-like signals. These transformations provide a natural route to teach direct versus inferred variables.

- The curriculum should make validation a learning object. Timing, units, saturation, parameter application and analysis assumptions should not be hidden instructor details; they are core lessons in experimental neuroscience and transparent instrumentation.

- The first released modules should privilege robust, easily observed behaviour and reusable outputs. Advanced dynamics, STP/STD, imaging inference and spike sorting should follow only after the underlying data and timing pathways have validated reference datasets.

- No gap in this architecture should be interpreted as a firmware request. Topics classified as hybrid, dataset-only, analogy or not suitable are pedagogical scope decisions based on the present platform.
