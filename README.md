<p align="left"><img width="270" height="170" src="./Documentation/Images/SpikyLogo.png">
</p>

<div align="center">

# **Spikeling v3**

### **An open-source hardware + software platform for neuroscience teaching and outreach:**  

A hands-on “artificial spiking neuron” running the **Izhikevich model** on an **ESP32**, with a desktop **GUI** for visualization, interaction, and data export.

<p>
  <a href="LICENSE.txt">
    <img alt="License" src="https://img.shields.io/github/license/OpenSourceNeuro/Spikeling">
  </a>
  <a href="https://github.com/OpenSourceNeuro/Spikeling/releases">
    <img alt="Release" src="https://img.shields.io/github/v/release/OpenSourceNeuro/Spikeling">
  </a>
  <a href="https://opensourceneuro.github.io/Spikeling/Firmware/Spikeling_V3">
  <img alt="Firmware" src="https://img.shields.io/badge/firmware-v3.1-blue">
</a>
  <a href="https://opensourceneuro.github.io/Spikeling/">
    <img alt="Docs" src="https://img.shields.io/badge/docs-wiki-green">
  </a>
</p>

<p align="right">
  developed by M.J.Y. Zimmermann<br>
  maintained by P. Rignanese & A. Koumoundourou<br>
  based on an original idea by T. Baden
</p>

</div>


This project is licensed under the [GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0.en.html)
<br>
The hardware is licensed under the [ CERN-OHL-S-2.0](https://gitlab.com/ohwr/project/cernohl/-/wikis/uploads/b88fd806c337866bff655f2506f23d37/cern_ohl_s_v2_user_guide.txt)

## Contents

- [What is Spikeling?](#what-is-spikeling)
- [Spikeling in academia & outreach](#spikeling-in-academia--outreach)
- [A brief summary of Spikeling functions](#a-brief-summary-of-spikeling-functions)
  - [Neurophysiology](#neurophysiology)
  - [Data analysis](#data-analysis)
  - [Neuron generator](#neuron-generator)
  - [Stimulus generator](#stimulus-generator)
  - [Multi-recording & networking](#multi-recording--networking-multi-unit-experiments)
  - [Fluorescence imaging simulation](#fluorescence-imaging-simulation)
  - [Exercises](#exercises)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

---

<br>

<div align="center">

## What is Spikeling?

<br>

![](./Documentation/Images/SpikelingGUI.gif)

<p style='text-align: justify;'>
  Spikeling is an open-source neuroscience education platform designed to make core neurophysiology concepts teachable through hands-on experimentation, even in settings where traditional wet-lab electrophysiology is impractical.
</p>

<p style='text-align: justify;'>
  In many degree programs, students learn about action potentials and synaptic signalling largely through lectures or static datasets because living preparations, microscopes, amplifiers, and specialist supervision do not scale well to large cohorts. Spikeling addresses this gap with a low-cost “in silico neuron” implemented in hardware.
</p>

<p style='text-align: justify;'>
  The device runs the computationally efficient and versatile <strong>Izhikevich spiking neuron model</strong> in real time on an ESP32-based microcontroller, providing electrophysiology-style interaction: controlled stimulation, measurable membrane-voltage dynamics, spike output, and parameter manipulation to explore firing regimes, adaptation, and input integration.
</p>

<p style='text-align: justify;'>
  A dedicated <strong>cross-platform desktop GUI</strong> supports real-time plotting, experiment control, and recording/export to standard formats—enabling teaching modules that extend beyond neurophysiology into protocol design, data collection, analysis pipelines, and model-based reasoning.
</p>

</div>

<br>

<div align="center">

<img align="center" src="./Documentation/Images/SpikelingNetwork.png" >

<h6 align="center">Two spikeling units (red and green), that are synchronously stimulated (white cables), synapse with a third unit (blue).</h6>

</div>

---

<br>

<div align="center">

## Spikeling in academia & outreach

<br>

<p style='text-align: justify;'>
  The spikeling project emerged from local needs to teach neuroscience class modules for direct interaction with <strong>neuron physiology, data analysis, fluorescence imaging, protocol design, etc.</strong>
</p>

<p style='text-align: justify;'>
  The aim was to provide <strong>hands-on experience</strong> on how neurons encode information and how diverse variables modulates their activities, while engaging students with <strong>crucial aspects of data collection, experimental limitations, methodology and statistical analysis.</strong>
</p>

<p style='text-align: justify;'>
  Spikeling is currently used in <strong>university teaching, computational neuroscience training, and outreach events</strong>. It is intentionally <strong>open (hardware + firmware + software)</strong> so educators can customize activities for their courses and contribute back to a shared pool of teaching material.
</p>

<p align="center">
  <img src="./Documentation/Images/Workshop_SouthAfrica.jpg" width="900" alt="Spikeling workshop — students using the device in South Africa (2022)">
</p>

<table>
  <tr>
    <td width="33%">
      <img src="./Documentation/Images/Workshop_Ghana.jpg"  height="300"><br>
      <sub><b>Outreach demonstration of neuron activities to primary school student in Ghana (2025)</b></sub>
    </td>
    <td width="33%">
      <img src="./Documentation/Images/Workshop_Zambia.jpg" height="300"><br>
      <sub><b>Hands-on electrophysiology-style experiments in Zambia (2025)</b></sub>
    </td>
    <td width="33%">
      <img src="./Documentation/Images/Workshop_Rwanda.JPG" height="300"><br>
      <sub><b>Small-group protocol design & parameter exploration in Rwanda (2024)</b></sub>
    </td>
  </tr>

</table>

</div>

***

<br>

<div align="center">

## A brief summary of Spikeling functions

<br>


<h3 align="left"> Neurophysiology:</h3></p>

<p style='text-align: justify;'>
  Spikeling implements the <strong>Izhikevich model</strong>, which “reproduces spiking and bursting behaviour of known type of cortical neurons. The model combines the <strong>biologically plausibility of Hodgkin-Huxley-type dynamics</strong> and the <strong>computational efficiency of integrate-and-fire neurons</strong>” <a href="https://ieeexplore.ieee.org/document/1257420"> E. M. Izhikevich, "Simple model of spiking neurons, 2003"</a>.
  This makes it well-suited for teaching as learners can move quickly between <strong>hypothesis → stimulation → observation → interpretation</strong>.
</p>

<p style='text-align: justify;'>
  Neurophysiology concepts are taught through electrophysiology-style interaction: students apply controlled inputs and directly observe membrane-voltage dynamics,
  thresholding, spike generation, and adaptation. This supports practical teaching objectives such as protocol design, parameter sensitivity, and reproducible experimentation.
</p>

<ul align="left">
  <li>
    <b>Patch-clamp style stimulation (current injection):</b>
    A simulated patch-clamp interface allows students to inject controlled current steps and waveforms.
    Learners can vary <b>amplitude</b>, <b>duration</b>, and <b>timing</b> to explore excitability, threshold, refractory effects, and spike-frequency adaptation.
  </li>

  <li>
    <b>Photo-sensitive input (photodiode / “photoreceptor”):</b>
    Spikeling includes a photodiode input that mimics sensory-driven current input.
    Students can test simple stimuli (e.g., flashlight pulses) and progress to controlled protocols using an external LED driven via the stimulus port
    (frequency/intensity). Advanced discussions can include response dynamics such as effective decay/recovery behaviour under repeated stimulation.
  </li>

  <li>
    <b>Synapses and networks (dendrites + axon):</b>
    Each unit provides <b>two dendritic inputs</b> with gain and polarity control (supporting excitatory and inhibitory effects) and <b>one axonal spike output</b>.
    This enables multi-unit experiments on coincidence detection, inhibition-driven gating, synchrony, and simple network motifs.
    Auxiliary units can be stimulated synchronously to keep network experiments controlled and reproducible.
  </li>
</ul>

<p style='text-align: justify;'>
  Together, these features let students reproduce classic teaching experiments:
  step-current response curves, threshold measurements, adaptation quantification, sensory-driven spiking, and basic synaptic/network computations—using the same device and workflow.
</p>

<br>

<img src="./Documentation/Images/Spikeling_cover_inverted.png" width="400" height="250">
<img src="./Documentation/Images/101_graph.png" width="400" height="250">

<h6 align="center">Left: Drawing on the acrylic cover of the Spikeling version 2.2, representing the controls knobs along with the input/ouput jacks.

Right: Spikeling GUI displaying the unit membrane voltage (red trace) while being light-stimulated by a controlled LED (blue trace) which generates input current (green trace).
</h6>

</div>

***

<div align="center">

<h3 align="left"> Data analysis</h3></p>

<p style='text-align: justify;'>
  Spikeling is designed to extend practical teaching beyond “watching spikes” into the full experimental workflow:
  <strong>recording</strong>, <strong>quality control</strong>, <strong>basic quantification</strong>, and <strong>export for reproducible analysis</strong>.
  This is particularly valuable in neuroscience curricula where students may have limited exposure to programming and data pipelines, yet are expected to interpret real experimental data.
</p>

<p style='text-align: justify;'>
Any data generated by Spikeling can be <strong>saved and exported</strong> for downstream analysis. The GUI also provides a lightweight,
<strong>built-in analysis</strong> layer that helps students validate recordings and immediately compute core measures such as spike detection and trial-averaged responses.
This supports in-class demonstrations, rapid iteration during labs, and structured home assignments.
</p>

<p style='text-align: justify;'>
  For advanced data analysis and basic statistics, <strong>python notebooks</strong> are provided to serve as template for the teaching staff. We are engage with the Spikeling community where users could share courses, exercises and data analysis scripts to be widely used in neuroscience and coding courses.
</p>

<ul align="left">
  <li>
    <b>Recording & export:</b>
    save time series (e.g., Vm, stimulus, derived currents, triggers) and export to standard formats (e.g., <b>CSV</b>) compatible with Python, MATLAB, R, Excel, etc.
  </li>
  <li>
    <b>Basic QC and annotation:</b>
    quickly verify signal integrity, confirm stimulus timing, and identify artefacts before committing to a full analysis workflow.
  </li>
  <li>
    <b>Spike detection and raster plots:</b>
    detect spikes from membrane-voltage traces and visualize them as rasters to introduce spike trains, variability, and stimulus-locked responses.
  </li>
  <li>
    <b>Trial alignment, looping, and averaging:</b>
    repeat identical stimulus protocols, align trials, and compute averaged traces and spike-rate summaries—making it easy to teach concepts like reliability,
    response variability, and signal-to-noise.
  </li>
  <li>
    <b>Bridge to coding modules:</b>
    provide exported datasets and template <b>Python notebooks</b> so teaching staff can scaffold progressively from GUI-based inspection to student-written analysis code.
  </li>
</ul>

<p style='text-align: justify;'>
  In short, Spikeling supports a gradual learning curve: students can begin with GUI-based inspection and built-in metrics,
  then transition to reproducible, script-based analysis using the exact same datasets—mirroring modern research practice.
</p>
<br>

<img align="center" src="./Documentation/Images/103_dataanalysis.jpg" width="400" height="250">
<img align="center" src="./Documentation/Images/103_data%20analysis.jpg" width="400" height="250">

<h6 align="center">Left: Displayed data from the previous experiment (light stimulation) spikes are detected and ploted along the Vm trace (red). Right: Traces looped and averaged showing the spike rate (white), the raster plot (red dots), the averaged Vm recording (red) and the averaged input current (green)</h6>

</div>

***

<div align="center">

<h3 align="left"> Neuron generator</h3></p>


<p style='text-align: justify;'>
  The <strong>Neuron Generator</strong> is an interactive space for exploring the Izhikevich model beyond “playing with a few knobs”.
  It is designed to help students connect <strong>model parameters</strong> to <strong>observable firing behaviours</strong> (e.g., tonic spiking, bursting, adaptation, rebound, irregular firing),
  and to build intuition for how different neurons can emerge from the same compact set of equations.
</p>

<p style='text-align: justify;'>
  In practice, the Neuron Generator lets learners rapidly prototype neuron “types” by adjusting Izhikevich parameters and immediately observing
  how the neuron responds to standardized stimuli. This encourages a scientific workflow: formulate a hypothesis (e.g., “increasing adaptation should reduce firing rate over time”),
  test it with controlled stimulation, then iterate.
</p>

<ul align="left">
  <li><b>Explore firing regimes:</b> interactively vary Izhikevich parameters and observe changes in excitability, thresholding, bursting, and adaptation.</li>
  <li><b>Compare neurons under identical protocols:</b> run the same stimulus recipe on multiple parameter sets to build mechanistic intuition.</li>
  <li><b>Create & share presets:</b> save custom neuron parameter sets for labs, assignments, or reproducible classroom demonstrations.</li>
  <li><b>Bridge theory and experiment:</b> connect equations/parameters to patch-clamp-style readouts (Vm traces, spike trains, firing-rate changes).</li>
</ul>

<br>

<img align="center" src="./Documentation/Images/Neurogen.jpg" width="75%">

<h6 align="center">GUI displaying the “Neuron Generator” page where users can appreciate the model underlying Spikeling activity and from which they can generate unique neuron to further run on Spikeling.</h6>

</div>

***

<div align="center">

<h3 align="left">Stimulus generator:</h3>

<p style='text-align: justify;'>
  Spikeling includes a dedicated <strong>Stimulus Generator</strong> to teach one of the most important (and often under-taught) parts of experimental neuroscience:
  <strong>protocol design</strong>. While Spikeling board only has a simple repeated square-wave stimulus (useful for classic current-step experiments and LED/light stimulation),
  the Stimulus Generator encourages students to move beyond “turning knobs” and instead design inputs that directly test experimental hypotheses.
</p>

<p style='text-align: justify;'>
  Users can create and iterate custom stimuli—such as <strong>step families</strong>, <strong>sinusoids</strong>, <strong>chirps</strong>, <strong>pulse trains</strong>, and <strong>binary/noise-like</strong> sequences—
  then apply them to current injection or light stimulation. A built-in <strong>stimulus preview</strong> allows learners to verify waveform timing, amplitude, and repetition structure
  <em>before</em> running an experiment, reinforcing good practice around sanity checks and reproducibility.
</p>

<ul align="left">
  <li><b>From standard to custom protocols:</b> start with square pulses and progress to structured waveforms used in electrophysiology and systems neuroscience.</li>
  <li><b>Preview before running:</b> confirm duration, inter-stimulus intervals, amplitude scaling, and repetition count to avoid protocol errors.</li>
  <li><b>Reproducible experimentation:</b> define explicit parameters to enable trial averaging and fair comparisons across neuron modes or conditions.</li>
  <li><b>Hypothesis-driven design:</b> link stimulus structure to questions like threshold, adaptation time constants, resonance, and response reliability under noise.</li>
</ul>

<br>

  <img align="center" src="./Documentation/Images/401_steps.jpg" width="400" height="250">
  <img align="center" src="./Documentation/Images/401_sine.jpg"  width="400" height="250">

  <h6 align="center">
    Stimulus Generator examples (with preview). Left: classic electrophysiology-style step family (10 steps, 10 a.u. increment, 25 ms per step, 5 ms rest at 0 a.u.).
    Right: sine-wave stimulus (50 a.u. amplitude, 20 Hz, 250 ms duration, 100 ms rest at 0 a.u.).
  </h6>

</div>

***

<div align="center">

<h3 align="left">Multi-recording & networking (multi-unit experiments):</h3>

<p style='text-align: justify;'>
  A key strength of Spikeling is that it can be scaled from a single “neuron” demo to <strong>small, interpretable networks</strong>.
  Each unit provides an <strong>axonal spike output</strong> and two <strong>dendritic (synaptic) inputs</strong>, enabling multiple Spikelings to be physically connected
  and studied as a functional circuit. This makes it possible to teach network-level computation using the same workflow as single-cell experiments:
  controlled stimulation, direct observation, and quantitative comparison.
</p>

<p style='text-align: justify;'>
  Importantly, each synaptic input can be configured as <strong>excitatory or inhibitory</strong> (via the synaptic gain control), allowing learners to explore
  how the <strong>sign</strong> and <strong>strength</strong> of coupling shapes membrane dynamics and spiking output. The GUI supports <strong>multi-recording</strong> by plotting and saving,
  in the same session, the activity of the main unit alongside the incoming synaptic streams (and, when available, the associated presynaptic signals),
  which is essential for teaching causality, timing, and interaction effects.
</p>

<ul align="left">
  <li><b>Excitation vs inhibition:</b> set synaptic gain positive or negative to illustrate recruitment of spiking vs suppression/gating.</li>
  <li><b>Timing-dependent effects:</b> compare synchronous vs offset inputs to demonstrate coincidence detection and integration windows.</li>
  <li><b>Simple circuit motifs:</b> build and test canonical motifs (feedforward excitation, inhibitory gating, E/I balance, two-input integration).</li>
  <li><b>Multi-channel recording:</b> visualize and export multiple traces simultaneously (main Vm, stimulus, synaptic inputs, and optional partner activity) for downstream analysis.</li>
</ul>

<br>

<div>
  <!-- Rename/move these screenshots into your repo (recommended location: ./Documentation/Images/ ) -->
  <img align="center" src="./Documentation/Images/101_12SynapseDC01.jpg" width="400" height="250">
  <img align="center" src="./Documentation/Images/101_12SynapseDC02.jpg" width="400" height="250">

  <h6 align="center">
    Multi-unit / synaptic networking example recorded in the GUI.
    Left: <b>excitatory</b> synaptic drive increases firing probability and can recruit spikes in the postsynaptic neuron.
    Right: <b>inhibitory</b> synaptic drive suppresses spiking and gates responses despite ongoing stimulation.
    In both cases, synaptic streams and membrane activity are visualised together, enabling direct comparison of circuit configurations.
  </h6>

</div>

---

<div align="center">

<h3 align="left">Fluorescence imaging simulation:</h3>

<p style='text-align: justify;'>
  Because Spikeling produces real-time <strong>membrane-voltage</strong> traces (and therefore a known spike train), it provides an ideal “ground truth” signal
  to introduce students to <strong>calcium imaging</strong> and the relationship between spikes, intracellular calcium dynamics, and measured fluorescence.
  The GUI can transform spiking activity into a simulated <strong>calcium concentration transient</strong>, and then into a simulated <strong>fluorescence signal</strong>,
  allowing learners to explore how imaging readouts relate to the underlying electrophysiology.
</p>

<p style='text-align: justify;'>
  Students can manipulate variables that mirror real experimental constraints—both on the acquisition side (e.g., <strong>frame rate</strong>, <strong>detector gain</strong>, <strong>noise level</strong>)
  and on the biophysical/indicator side (e.g., <strong>baseline calcium</strong>, <strong>decay time constant</strong>, <strong>spike-triggered calcium increment</strong>,
  <strong>indicator affinity / dissociation constant</strong>, <strong>brightness</strong>, and <strong>photobleaching-like effects</strong>).
  This helps learners understand why calcium traces are not a direct copy of spikes, and why interpretation depends on both biology and measurement.
</p>

<p style='text-align: justify;'>
  For increased realism, the simulation can be switched from a <strong>linear</strong> fluorescence model to a <strong>non-linear saturating</strong> model,
  illustrating common limitations such as dynamic range, saturation at high activity, and the consequences for comparing firing rates across conditions.
</p>

<br>

<img align="center" src="./Documentation/Images/201_graph.png" width="400" height="250">
<img align="center" src="./Documentation/Images/201_graphsat.png" width="400" height="250">

<h6 align="center">
  Imaging simulation in the GUI: linear (left) and saturating / non-linear (right) fluorescence models (green) generated from simulated calcium concentration dynamics (pink).
</h6>

<p style='text-align: justify;'>
  The objective is to familiarise students with the type of data they will encounter in modern systems and circuit neuroscience:
  signals that are <strong>indirect</strong>, <strong>noisy</strong>, and shaped by both the underlying biology and the measurement apparatus.
  This creates a natural pathway to discussing experimental limitations (sampling, noise, saturation, bleaching) and good analysis practice.
</p>

<p style='text-align: justify;'>
  In advanced modules, students can analyse the simulated imaging data and implement <strong>spike inference</strong> methods, then directly compare inferred spikes
  to the known “ground truth” spike train that generated the fluorescence trace—turning a common challenge in imaging into a controlled, teachable problem.
</p>

</div>

***

<div align="center">

<h3 align="left">Exercises:</h3>

<p style='text-align: justify;'>
  Spikeling is accompanied by a set of <strong>suggested exercises</strong> designed to help teaching staff run structured practicals with minimal setup.
  The exercises are intended to create a concrete bridge between core neurophysiology concepts taught in lectures and a responsive, real-time <strong>in silico</strong> neuron model
  that students can stimulate, measure, and analyse.
</p>

<p style='text-align: justify;'>
  Beyond technical skills, the exercises are also a vehicle for introducing scientific reasoning and epistemology:
  how a concept becomes knowledge, what it means to test a hypothesis, and how results can <strong>support, constrain, or falsify</strong> an interpretation.
  In advanced modules, students can be asked to design their own experiment as an assignment—emphasising good practice in <strong>methodology</strong> and <strong>protocol design</strong>
  (controls, parameter choices, repeatability, and appropriate analysis), rather than treating “methods” as a checklist.
</p>

<ul align="left">
  <li><b>Ready-to-run practicals:</b> structured activities covering excitability, threshold, adaptation, synaptic integration, and basic networks.</li>
  <li><b>Analysis-focused assignments:</b> exported datasets for plotting, spike detection, summary metrics, and interpretation.</li>
  <li><b>Open-ended projects:</b> student-designed stimuli and protocols to answer a defined question (with clear evaluation criteria).</li>
</ul>

<p style='text-align: justify;'>
  We encourage educators to adapt and extend these exercises to match their curricula. Our goal is to grow a shared pool of teaching material where users can contribute
  new exercises, datasets, and analysis notebooks—making Spikeling progressively more useful across institutions and course formats.
</p>

</div>

---


## Documentation

<div align="left">
The full documentation is hosted as a project wiki and is the recommended entry point for educators and new users.

It covers:
- **Getting started** (hardware overview, connections, first experiment)
- **Firmware** (flashing, configuration, serial protocol)
- **GUI user guide** (controls, plotting, recording/export, troubleshooting)
- **Teaching materials** (suggested lab exercises, workflows, assignments)
- **Advanced modules** (synapses/networks, stimulus design, fluorescence imaging simulation, emulator mode)

**Docs website:** https://opensourceneuro.github.io/Spikeling/  
**Firmware documentation:** https://opensourceneuro.github.io/Spikeling/Firmware/Spikeling_V3  
**Releases (pre-built GUI):** https://github.com/OpenSourceNeuro/Spikeling/releases

---

## Contributing

Spikeling is an open hardware + open software teaching platform. Contributions are welcome across **hardware**, **firmware**, **GUI/software**, **documentation**, and **teaching materials**.

### How to contribute
- **Report bugs / request features:** open an issue  
  https://github.com/OpenSourceNeuro/Spikeling/issues
- **Submit improvements:** open a pull request  
  https://github.com/OpenSourceNeuro/Spikeling/pulls
- **Share teaching content:** contribute new exercises, worksheets, datasets, and analysis notebooks (with learning goals and expected outcomes) so other instructors can reuse them.

### What to include in an issue (so we can reproduce it)
- your OS (Windows/macOS/Linux) + Spikeling GUI version
- firmware version (and board revision if known)
- clear steps to reproduce + what you expected vs what happened
- screenshots/logs and (when relevant) a short exported CSV

### Pull request guidelines (practical and lightweight)
- Keep PRs focused (one improvement per PR when possible).
- Follow existing style and folder structure.
- For GUI changes: include a screenshot/GIF and note any new dependencies.
- For firmware changes: document parameters/commands and keep backward compatibility when reasonable.
- For docs/exercises: include learning objectives, required materials, and approximate duration.

### Community and attribution
Spikeling is used in teaching and outreach worldwide. If you adapt it for a course, workshop, or public event, please consider contributing back:
- photos (with permission), module outlines, and lab handouts
- custom neuron presets and stimulus protocols
- analysis notebooks and grading rubrics

All contributors will be acknowledged via GitHub history, and substantial contributions can be credited in documentation and release notes.

---

## License

Spikeling is released under **open-source / open-hardware** licenses:

- **Software & firmware:** **GNU General Public License v3.0** (GPL-3.0)  
  See `LICENSE.txt` (and individual file headers where applicable).

- **Hardware:** **CERN Open Hardware Licence – Strongly Reciprocal v2.0** (**CERN-OHL-S-2.0**)  
  See the `LICENSES/` folder for the full text and attribution of hardware design files.

If you reuse Spikeling in a course, workshop, publication, or derivative project, please keep the appropriate license notices and cite the project where relevant.

</div>
