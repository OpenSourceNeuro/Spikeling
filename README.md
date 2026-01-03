<p align="left"><img width="270" height="170" src="https://github.com/OpenSourceNeuro/Spikeling-V2/blob/main/Images/SpikyLogo.png">

<h1 align="center"> Spikeling V 2.2</h1></p>
<h3 align="center">  A hardware implementation of spiking neurons for neuroscience teaching and outreach</h3></p>
<p align="center"><h6 align="right">developed by M.J.Y. Zimmermann, A.M. Chagas & T. Baden</h6></p>

<br></br>


![](https://github.com/OpenSourceNeuro/Spikeling-V2/blob/main/GUI/PyQt/resources/spike.gif)


This project is licensed under the [GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0.en.html)<br>
The hardware is licensed under the [ CERN-OHL-S-2.0](https://gitlab.com/ohwr/project/cernohl/-/wikis/uploads/b88fd806c337866bff655f2506f23d37/cern_ohl_s_v2_user_guide.txtE)

***

<p style='text-align: justify;'>
Understanding how neurons encode and compute information is fundamental to our study of the brain, but opportunities for hands-on experience with neurophysiological techniques on living neurons are scarce in science education.

<p style='text-align: justify;'>
Due to budgetary constraints and logistical hurdles, few students can be afforded the opportunity to experience electrophysiological recordings on living neurons in action. Yet, a fundamental aspect of neuroscience courses is to understand electrical signalling within neurons and the transmission of signals across synapses, as well as the experimental techniques necessary to observe these properties.

<p style='text-align: justify;'>
To support university-level neuroscience teaching, we designed ‘Spikeling’, an open-source teaching support device that mimics the electrical properties of spiking neurons by running the computationally efficient yet versatile Izhikevich model.

<p style='text-align: justify;'>
It is an artificial neuron that can receive different inputs, integrate them and outputs its computation, just like a spiking neuron would!

<p style='text-align: justify;'>
Technically, it consists on a microcontroller (an ESP32) running the computationally efficient Izhikevich model of a spiking neuron.


<br>

<div>
<img align="center" src="https://github.com/OpenSourceNeuro/Spikeling-V2/blob/main/Images/PCB.png" width="400" height="250" >

<img align="center"  src="https://github.com/OpenSourceNeuro/Spikeling-V2/blob/main/Images/Spikeling_cover.png" width="400" height="250">

<h6 align="center">Left: Rendering of spikeling electronic components. Right: Acrylic cover detailing spikeling functionalities.</h6>

</div>

<div>

<p style='text-align: justify;'>
The spikeling project emerged from local needs to teach neuroscience class modules for direct interaction with neuron physiology, data analysis, fluorescence imaging, protocol design, etc. The aim is to provide hands-on experience on how neurons encode information and how diverse variables modulates their activities, while engaging students with crucial aspects of data collection, experimental limitations, methodology and statistical analysis.

<p style='text-align: justify;'>
In order to give users a full interactive experience with the Spikeling neuron, a drawing engraved on the cover details in a neuro-morphic fashion all device functionalities. Furthermore, a spike-triggered LED and buzzer have been added to the device.

<p style='text-align: justify;'>
A dedicated GUI (Graphical User Interface) allows users to fully interact with Spikeling, plot all data generated and record them for further analysis.

<p style='text-align: justify;'>
Overall, Spikeling is a versatile device, allowing any teaching staff to conceive dry-lab tutorials or home assignments related to their own teaching course materials.

<p style='text-align: justify;'>
Enthusiasts and potential collaborators can source the electronic bits for this project from <a href="https://kitspace.org/boards/github.com/maxzimmer/spikeling-v2/">KitSpace</a></p>


</div>

***


<h2 align="center"> A brief summary of Spikeling functions</h3>

<br>

<div>

<h3 align="left"> Neurophysiology:</h3></p>

<p style='text-align: justify;'>
Spikeling is conceived on the Izhikevich model, which “reproduces spiking and bursting behaviour of known type of cortical neurons. The model combines the biologically plausibility of Hodgkin-Huxley-type dynamics and the computational efficiency of integrate-and-fire neurons” (E.M. Izhikevich, IEEE Transactions on Neural Networks, 2003, doi: 10.1109/TNN.2003.820440).

<p style='text-align: justify;'>
Students can appreciate playing with many variables that can be encountered in textbook or related to class material. A simulated patch-clamp experiment (represented by a pipette drawing on the top cover) allows students to “inject current” into the Spikeling neuron. They can furthermore modulate the amount of current injected, the speed and duration at which it is injected and observe the adaptation effect on a spiking neuron.

<p style='text-align: justify;'>
Spikeling also possesses a photodiode (modelized on the top cover as a photoreceptor) making Spikeling photo-sensitive. The photodiode mimics current inputs a photoreceptor would have on a spiking neuron. Students can appreciate the impact of a flash light onto the photoreceptor and investigate the different effects it may have. Ultimately, a supplied LED can be connected to the stimulus port and can then be controlled in frequency and intensity for controlled experiments. Advanced variable such as photoreceptor decay and recovery rate could also be investigated.

<p style='text-align: justify;'>
Each Spikeling unit possesses one “axonal” output and two “dendritic” inputs. Each dendritic input possesses a knob that can modulate the synaptic gain positively or negatively (mimicking excitatory and inhibitory synapses). In advanced stages, students could be encouraged to form neuronal networks. Auxiliary neurons can furthermore be stimulated synchronously from the “main neuron” experiment box to set a controlled environment.

</div>

<br>

<div>

<img align="center"  src="https://github.com/OpenSourceNeuro/Spikeling-V2/blob/main/Images/Spikeling_hardware.png" width="400" height="250">

<img align="center" src="https://github.com/OpenSourceNeuro/Spikeling-V2/blob/main/Images/101_graph.png" width="400" height="250">

<h6 align="center">Left: A Spikeling unit being stimulated by a direct current injection (blue cable) while receiving synaptic inputs from a second unit (pink cable). Right: Spikeling GUI displaying the unit membrane voltage (red trace) while being light-stimulated by a controlled LED (blue trace) which generates input current (green trace).</h6>

</div>

<br>

***

<br>

<div>

<h3 align="left"> Data analysis</h3></p>

<p style='text-align: justify;'>
Handling large dataset is an important part of daily academic work. However, few universities offer coding and programming modules for their neuroscience courses. A proper data analysis of any kind starts with the understanding of a program language and the understanding of every steps of the analysis pipeline. Only then, students can appreciate the results of their experiments and engage in their critical interpretation.

<p style='text-align: justify;'>
Any data generated by Spikeling can be saved and exported.  The GUI comes with a simple built-in data analysis that allows students to check their data and generate raster plots. From this simple analysis they could appreciate how neuronal information is encoded within stochastic spike trains (see below).

<p style='text-align: justify;'>
This simple analysis could be used for home assignments in the early stages of student degree before engaging them in developing their own analysis code.

<p style='text-align: justify;'>
For advanced data analysis and basic statistics, python notebooks are provided to serve as template for the teaching staff. It is our hope to create a Spikeling community where users could share courses, exercises and data analysis scripts to be widely used in neuroscience and coding courses.

</div>

<br>

<div>

<img align="center" src="https://github.com/OpenSourceNeuro/Spikeling-V2/blob/main/Images/103_dataanalysis.jpg" width="400" height="250">

<img align="center" src="https://github.com/OpenSourceNeuro/Spikeling-V2/blob/main/Images/103_data%20analysis.jpg" width="400" height="250">

<h6 align="center">GUI displaying the “Neuron Generator” page where users can appreciate the model underlying Spikeling activity and from which they can generate unique neuron to further run on Spikeling.</h6>

</div>

<br>

***

<br>

<div>

<h3 align="left">Stimulus generator:</h3>

<p style='text-align: justify;'>
Spikeling comes by default with a repeated square wave pattern stimulus, on which the user could only modulate the intensity and the frequency, might it be for direct current injection or light stimulation.

<p style='text-align: justify;'>
Here users are encouraged to develop their own stimulus (successive waves, sinusoidal loops, chirp, binary noise, etc.). Some basic stimuli are already available. The main point of this feature is to encourage the students to conceive their own experiments leading them to think about the protocol that needs to be implemented in order to answer the experimental questions they are being faced with.

</div>

<br>

<div>

<img align="center"  src="https://github.com/OpenSourceNeuro/Spikeling-V2/blob/main/Images/401_steps.jpg" width="400" height="250">

<img align="center" src="https://github.com/OpenSourceNeuro/Spikeling-V2/blob/main/Images/401_sine.jpg" width="400" height="250">

<h6 align="center">GUI displaying the “Simulus Generator” page where users can generate their own unique stimuli. The left screen shows repetitive increments of current, as seen in classic electrophysiology experiments (10 steps with 10 a.u. current increment lasting 25 ms with a resting period of 5ms at 0 a.u. current). The right screen shows a sine wave stimulus (50 a.u. amplitude, 20 Hz frequency over a period of 250 ms and a resting period of 100 ms at 0 a.u. current)</h6>

</div>

<br>

***

<br>

<div>

<h3 align="left">Fluorescence imaging simulation:</h3>

<p style='text-align: justify;'>
Since Spikeling generates membrane voltage data, we could use this “ground truth data” to generate a simulated calcium concentration transient underlying spike occurrence in the neuron. And from then, use the later to model a simulated fluorescence.

<p style='text-align: justify;'>
Students could then be engaged into dynamic calcium fluorescence imaging (i.e two-photon microscopy) and play with many variables that could be encountered from the experimenter side (frame rate, laser power, photo detector gain, etc.), from the calcium concentration properties within the neuron (concentration baseline, decay, increase jump per spike, etc.)  or from the calcium indicator properties itself (indicator affinity, dissociation constant, brightness, photo-bleach, etc.).

<p style='text-align: justify;'>
For an even more realistic simulation, students could choose to move from a linear model to a non-linear saturation model of the fluorescence signal.

</div>

<br>

<div>

<img align="center"  src="https://github.com/OpenSourceNeuro/Spikeling-V2/blob/main/Images/201_graph.png" width="400" height="250">

<img align="center" src="https://github.com/OpenSourceNeuro/Spikeling-V2/blob/main/Images/201_graphsat.png" width="400" height="250">

<h6 align="center">GUI displaying linear(left) and (non-linear) models of simulated fluorescence (green) based on simulated calcium concentration (pink)</h6>

</div>

<div>

<p style='text-align: justify;'>
Here, the aim is to familiarise students with the type of data they could encounter in their future academic work, incorporating noise and limitations to the data that are inherent to every experiments.

<p style='text-align: justify;'>
Ultimately, students could be encouraged to analyse imaging data, even implement spike inference algorithms and compare their results to the “ground truth data” that generated the fluorescence trace.

</div>

<br>

***

<br>

<div>

<h3 align="left">Exercises:</h3>

<p style='text-align: justify;'>
Spikeling comes with a set of suggested exercises that could be used in class as a guideline for the teaching staff to explore Spikeling functionalities. They are conceived to allow students to make a concrete connection between neurophysiology concepts seen in lectures with a responsive in silico model.

<p style='text-align: justify;'>
Exercises are also a mean to introduce some epistemology into the teaching material: Understanding how a neurobiology concept became a knowledge and how it can be tested, confirmed or refuted.
In advance courses, giving students the opportunity to design their own experiment as assignment also allows to introduce good methodology and protocol design practices. Which, unfortunately has shown to be too often mistaken with methods.

<p style='text-align: justify;'>
We would always encourage teachers to develop their own exercises based on the content they cover in class. It is our hope that such exercises could also be used as homework grading system.

</div>

<br>

***

<br>

<h2 align="center">Detailed Spikeling functions</h3></p>

<br>

- [Spikeling: A spiking neuron interface](#a-spiking-neuron-interface)
- [Spikeling: GUI - neuron parameters](#spikeling-gui-neuron-parameters)
- [Spikeling: GUI - stimuli parameters](#spikeling-gui-stimuli-parameters)
- [Spikeling: Data Analysis](#-data-analysis)
- [Spikeling: Neuron generator](#spikeling-neuron-generator)
- [Spikeling: Stimulus Generator](#stimulus-generator)
- [Spikeling: Multiple recording](#spikeling-multiple-recording)

<br>

- [Fluorescence: imaging simulation](#fluorescence-imaging-simulation)
- [Fluorescence: Imaging parameters](#fluorescence-imaging-parameters)
- [Fluorescence: Calcium parameters](#fluorescence-calcium-parameters)
- [Fluorescence: Fluorescence parameters](#fluorescence-imaging-parameters)
- [Fluorescence: Data Analysis](#fluorescence-data-analysis)
- [Fluorescence: Multiple fluorescence](#fluorescence-multiple-fluorescence)

<br>

- [Exercices: GUI](#exercises-gui)
- [Exercices: Python](#exercises-python)

<br>

- [GitHub Contributions](#gitHub-Contributions)

- [Arduino code and libraries](#)

- [GUI PyQt6 / PySide6 script](#)

<br>

***

<br>

## A spiking neuron interface

<br>

<img align="left"  src="https://github.com/OpenSourceNeuro/Spikeling-V2/blob/main/Images/Spikeling_cover.png" width="400" height="250">

<p style='text-align: justify;'>
The entire layout of the Spikeling board has been reconceived and a laser-cut acrylic sheet repesenting a neuron now sits on top of the board. All ports and potentiometers are now strategically placed.

<p style='text-align: justify;'>
The ESP32 is placed below the soma, the synaptic inputs from other Spikeling units are placed on the left, the synaptic output is placed on the right. Along the axon now sits a RGB LED, the red LED brightness follows as before the Vm status of the neuron, and the LED sparks in white when the neuron spike. The spike buzzer also sit along the axon, a small hole on the acrylic sheet sitting just above so the click can be heard coming from that direction. Both indicators can now be disabled by users at their pleasure.

<p style='text-align: justify;'>
The Vm potentiometer and the Current-in port are now grouped together and sit on the acrylic sheet at the bottom of an electrode pipette. They can now be considered as patch clamp experiment variables.

<p style='text-align: justify;'>
A photoreceptor is now drawn on the acrylic sheet, below the opsin sits a photodiode, and a potentiometer on the photoreceptor body now controls the photoreceptor sensitivity and its polarity (users can thus decide if the photoreceptor has an excitatory or an inhibitory effect on the neuron)

<p style='text-align: justify;'>
The noise potentiometer now sits in a box by itself as it represents parasitic noise from the experiment environment (synaptic inputs, receptor noise, thermal noise, experimental setup, etc.) and is independent from the rest of the Spikeling functions. This potentiometer is different from the others: it is not center-detented as it generates noise from a zero to a maximum value.

<p style='text-align: justify;'>
Next is the Neuron mode box which contains the twelve available modes to the users and a push button that allows the user to switch between them.

<p style='text-align: justify;'>
Finally, the last box contains all experimental tools allowing stimuli generation. As detailed on the acrylic top cover, the user can control the stimulus frequency and the stimulus intensity, along with its polarity. The stimulus output can either be directly connected to the current-in port to simulate a current applied to a patched neuron through the pipette; or be connected to a cable with a 5mm LED soldered at its tip which can be placed directly on top of the photoreceptor opsin (photodiode below). The photoreceptor potentiometer allows to modulate the gain and polarity of the light-induced input current. Furthermore, the photoreceptor possesses functions (on the GUI: decay/recovery) simulating how a variety of photoreceptors would integrate a light stimuli and how it will adapt to prolonged stimulation.  


<br>

***

<br>

<p style='text-align: justify;'>
Spikeling now possesses its own GUI, written in python and using the latest PyQt6/PySide6 library. The script then uses pyInstaller so it can be translated into a windows/linux/mac app, ready to be easily distributed to users.

<br>

<img align="left" width="400" height="250" src="https://github.com/OpenSourceNeuro/Spikeling-V2/blob/main/Images/101_graph.png">

<p style='text-align: justify;'>
The GUI is divided into distinct pages. The first one is the main GUI window where users connect the board to the computer. From there they can choose to either select the neuronal mode on the board directly (neuron mode box) or through the GUI (note that custom modes will have to be selected from here, and in this instance the GUI takes priority over the board commands).

<p style='text-align: justify;'>
The main window displays the Spikeling activity (Neuron Vm, total current input from all sources & stimulus ). If connected to other Spikelings, the GUI can display synaptic inputs: their incoming neuron Vm and their spiking events, which will be translated into input current for the main neuron. Traces can be selected through checkbox and superimposed over the same graph with a common timeline.

<p style='text-align: justify;'>
The "Neuron Mode" defines the current Izhikevich model being used [see Neuron Generator](#Spikeling-Neuron-generator). Twelve are encoded by default on the Spikeling unit and can be chosen either from the board itself or directly from the GUI: "Select Neuron Mode". Note that any command from the GUI will take priority over the board. Custom Neuron Modes can be selected from here and upload to the board.

<p style='text-align: justify;'>
The neuron interface page also possesses two buttons to enable/disable the spike buzzer sound and the spike LED, which in a class room full of spikeling, are regarded as huge relieves.

<p style='text-align: justify;'>
Below the main window, sits the recording window. All last generated data from traces that are checked on the main window will be saved in a .csv format.

<p style='text-align: justify;'>
On the right hand side two control columns can be found. For all commands, when the toggle button is enabled, the GUI takes over the potentiometer and controls directly the Spikeling variables. This allows users to design an experimental protocol in a controlled fashion.

<br>

***

<br>

<p style='text-align: justify;'>
Spikeling membrane voltage (Vm), displayed on the GUI in red, is generated by the Izhikevich model equation.
It is rather simple and relies on four parameters [see Neuron Generator](#Spikeling-Neuron-generator).

<br>

<p style='text-align: justify;'>
When Vm > 30mV, then a spike is generated, both the spike LED and spike buzzer on the board are activated, and the Vm model is reset accordingly (see above).

<p style='text-align: justify;'>
The green trace represents all current inputs received by the board and summed up in the variable "I" in the Izhikevich equation.
These current inputs correspond to the synaptic inputs, the direct current injection from the patch clamp port or the light induced current from the photodiode, and the noise generator potentiometer. All will influence the Vm equation and the subsequent spiking pattern.

<p style='text-align: justify;'>
The blue trace represents the square wave stimulus, which can be manually modulated in length, intensity and polarity through the potentiometer located in the "experiment box". The resulting stimulus signal is sent to the "Stimulus Output" port.
A jack cable connecting the "Stimulus Output" port to the "Current In" port will deliver the stimulus signal directly into the Spikeling neuron, simulating a direct current injection through a patched clamp electrode.
If a LED is connected to the "Stimulus Output" port and placed onto the photodiode, then the "photoreceptor" is stimulated accordingly and generates a current that will in turn be injected into the Izhikevich equation.

<p style='text-align: justify;'>
Users can also interact with the "Current In" potentiometer placed on the electrode and constantly inject steady current in order to either hyperpolarise or depolarise Spikeling.
Users can also interact with the "Photo-Gain" potentiometer and modulate the light sensitivity and polarity of the photodiode, thus generating ON/OFF neurons.

<p style='text-align: justify;'>
If Spikeling is connected to other units, the main window can display their Vm and their synaptic current inputs. Users can modulate these inputs by interacting with the "Synapse Gain" potentiometers which modulate the intensity and polarity of the synaptic inputs, giving rise to excitatory and inhibitory synapses.

<p style='text-align: justify;'>
Furthermore, users can stimulate the auxiliary Spikeling units in synchrony via the main unit's "Stimulus Output" port by using a splitter audio jack

<br>

***

<br>

## Spikeling GUI neuron parameters

<br>

TBC

<br>

***

<br>

## Spikeling GUI stimuli parameters

<br>

TBC

<br>

***

<br>

## Spikeling Neuron generator

<br>

<img align="left" width="400" height="250" src="https://github.com/OpenSourceNeuro/Spikeling-V2/blob/main/Images/Neurogen.jpg">

<p style='text-align: justify;'>
Spikeling GUI comes with a "Neuron Generator" page where users can interact with the Izhikevich equation, understand the model generating Spikeling membrane voltage, and create their own "neuron mode" to be loaded on the main page.

<p style='text-align: justify;'>
The main window computes the Izhikevich model with a modifiable current input. Users can change the 4 variable of the code and display the resulting "neuron mode". This is also where users can come up with their own neuronal modes to experiment on. This is also where teachers can generate their own custo-made neuron, save them, and impose them as experimental model for, i.e. home assignments.

<p style='text-align: justify;'>
From <a href="https://pubmed.ncbi.nlm.nih.gov/18244602">Izhikevich publication</a>:
<em> Bifurcation methodologies enable us to reduce many biophysically accurate Hodgkin–Huxley-type neuronal models to a two-dimensional (2-D) system of ordinary differential equations of the form:</em>

```math
v' = 0.04v^2 + 5v + 140 - u + I
```
```math
u' = a * (bv - u)
```

With the auxiliary after-spike resetting:

<p align="center">
if:
</p>

```math
v >= 30mV
```
<p align="center">
 then:
 </p>

 ```math
 v = c
 ```

<p align="center">
 and:
 </p>

 ```math
 u = u + d
```

<br>

<img align="left"  src="https://github.com/OpenSourceNeuro/Spikeling-V2/blob/main/GUI/PyQt/resources/izhik.png" width="270" height="200">

<p style='text-align: justify;'>
Here, v and u are dimensionless variables, and a, b, c, and d are dimensionless parameters, and '= d/dt, where t is the time (0.1 µs).

<p style='text-align: justify;'>
The variable v represents the membrane potential of the neuron and u represents a membrane recovery variable, which accounts for the activation of K+ ionic currents and inactivation of Na+ ionic currents, and it provides negative feedback to v.

<p style='text-align: justify;'>
After the spike reaches its apex (+30 mV), the membrane voltage and the recovery variable are reset.
Synaptic currents or injected DC-currents are delivered via the variable I.

<p style='text-align: justify;'>
Below the stimulus frequency and strength sliders can be found a custom stimulus display. Here the user can choose to use instead of the classical square wave, either a stimulus from a pre-design library (comprising sine wave, chirp, white noise, etc.), or either a custom made stimulus generated from the GUI "stimulus generator" tab.

<br>

***

<br>

## Spikeling Stimulus Generator

<br>

<p style='text-align: justify;'>
Spikeling GUI also comes with a "Stimulus Generator" page where users can generate their own stimuli. In the current version seven distinct stimulus pattern are available with various parameters to interact with.
All stimuli can then be saved and further loaded from the Spikeling main window.

<br>

<div>

<img align="center" width="400" height="250" src="https://github.com/OpenSourceNeuro/Spikeling-V2/blob/main/Images/401_steps.jpg">

<img align="center" width="400" height="250" src="https://github.com/OpenSourceNeuro/Spikeling-V2/blob/main/Images/401_sine.jpg">

<h6 align="center">GUI displaying the “Simulus Generator” page where users can generate their own unique stimuli. The left screen shows repetitive increments of current, as seen in classic electrophysiology experiments (10 steps with 10 a.u. current increment lasting 25 ms with a resting period of 5ms at 0 a.u. current). The right screen shows a sine wave stimulus (50 a.u. amplitude, 20 Hz frequency over a period of 250 ms and a resting period of 100 ms at 0 a.u. current)</h6>

</div>

<br>

<div>

<img align="center" width="400" height="250" src="https://github.com/OpenSourceNeuro/Spikeling-V2/blob/main/Images/401_triangle.jpg">

<img align="center" width="400" height="250" src="https://github.com/OpenSourceNeuro/Spikeling-V2/blob/main/Images/401_ampchirp.jpg">

<h6 align="center">GUI displaying the “Simulus Generator” page where users can generate their own unique stimuli. The left screen shows a triangular wave stimulus (50 a.u. amplitude, 20 Hz frequency over a period of 250 ms and a resting period of 100 ms at 0 a.u. current). The right screen shows a chirp stimulus with an increased intensity from a 0 to a 100 a.u. amplitude at 100 Hz over 1000 ms </h6>

</div>

<br>

<div>

<img align="center" width="400" height="250" src="https://github.com/OpenSourceNeuro/Spikeling-V2/blob/main/Images/401_linchirp.jpg">

<img align="center" width="400" height="250" src="https://github.com/OpenSourceNeuro/Spikeling-V2/blob/main/Images/401_expchirp.jpg">

<h6 align="center">GUI displaying the “Simulus Generator” page where users can generate their own unique stimuli. The left screen shows a linear chirp stimulus with an increased frequency from a 0 to a 50 Hz with an amplitude of 100 a.u. over 1000 ms. The right screen show the same stimulus with an exponential frequency increase </h6>

</div>

<br>

***

<br>

## Spikeling Multiple recording

<br>

TBC

<div>

<img align="center" width="400" height="250" src="https://github.com/OpenSourceNeuro/Spikeling-V2/blob/main/Images/101_1SynapseDC01.jpg">

<img align="center" width="400" height="250" src="https://github.com/OpenSourceNeuro/Spikeling-V2/blob/main/Images/101_1SynapseDC02.jpg">

<h6 align="center"> ... </h6>

</div>

<br>

<div>

<img align="center" width="400" height="250" src="https://github.com/OpenSourceNeuro/Spikeling-V2/blob/main/Images/101_12SynapseDC01.jpg">

<img align="center" width="400" height="250" src="https://github.com/OpenSourceNeuro/Spikeling-V2/blob/main/Images/101_12SynapseDC02.jpg">

<h6 align="center"> ... </h6>

</div>

<br>

***

<br>

## Fluorescence Imaging simulation

<br>

TBC

```math
[Ca^{2+}]_{t} = [Ca^{2+}]_{t-1} - \tau . [Ca^{2+}]_{t-1} + [Ca^{2+}]_{b} + A . n_{t} + \sigma_{Ca} . \sqrt{\Delta} . \varepsilon_{Ca,t}
```

Where:
- $\tau$ is the Calcium decay constant
- $[Ca^{2+}]_{b}$ the Calcium baseline concentration
- A is the calcium concentration jump each spike triggers
- $n_{t}$ is the number of spikes at time t
- $\sigma_{Ca}$ scales the Calcium noise
- $\Delta$ represents the imaging frame timeline
- $\varepsilon_{Ca,t}$ is a standard normal Gaussian noise source

<br>

```math
F_{t} = \alpha[Ca^{2+}]_{t} + \beta + \sigma_{F}.\varepsilon_{F,t}
```

<br>

<div>
<p align="center">
<img align="center"  src="https://github.com/OpenSourceNeuro/Spikeling-V2/blob/main/Images/201_graph.png" width="400" height="250">

</div>

<br>

Where:
- $\alpha$ scales the Fluorescence
- $\beta$ offsets the fluorescence
- $\sigma_{F}$ scales the Fluorescence noise
- $\varepsilon_{F,t}$ is a standard normal Gaussian noise source


<br></br>

```math
Fsat_{t} = \alpha.S.[Ca^{2+}]_{t} + \beta + \eta_{t}

```

Where:
- The gain $\alpha$ scales the fluorescence. It accounts for all factors contributing to signal amplification, including the number of fluorophores in the neuron, the brightness of each fluorophore, the gain of the image acquisition system, etc.
- The offset $\beta$, accounts for any factor leading to a constant background signal, such as baseline fluorescence.
- $S . [Ca^{2+}]_{t}$ is a nonlinear saturation function, often taken as the Hill equation:
  - $S_{x} = \frac{x_{n}} {(x_{n} + kd)}$, where n is the Hill coefficient and kd the dissociation constant.
- Assuming the primary noise source is photon shot noise, it would be appropriate to model noise as a Poisson process, which could be well approximated by a Gaussian distribution for large photon counts: $\eta_{t}$

```math
\eta_{t} = \sqrt{\varepsilon.S . ([Ca^{2+}]_{t}) + \sigma_{F}} . \varepsilon_{F,t}
```

<br>


<div>

<p align="center">
<img align="center"  src="https://github.com/OpenSourceNeuro/Spikeling-V2/blob/main/Images/201_graphsat.png" width="400" height="250">

</div>

<br>

***

<br>

## Fluorescence Imaging parameters

<br>

TBC

<br>

***

<br>

## Fluorescence Calcium parameters

<br>

TBC

<br>

***

<br>

## Fluorescence Imaging parameters

<br>

TBC

<br>

***

<br>

## Fluorescence Data Analysis

<br>

TBC

<br>

***

<br>

## Fluorescence Multiple fluorescence

<br>

TBC

<br>

***

<br>

## Exercises GUI

<br>

TBC

<br>

***

<br>

## Exercises Python

<br>

TBC

<br>

***

<br>

## GitHub Contributions

<br>

TBC

<br>
