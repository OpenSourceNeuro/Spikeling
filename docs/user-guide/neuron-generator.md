
## Spikeling Neuron generator

<br>

<img align="left" width="400" height="250" src="https://github.com/OpenSourceNeuro/Spikeling-V2/blob/main/Images/Neurogen.jpg">

<p style='text-align: justify;'>
Spikeling GUI comes with a "Neuron Generator" page where users can interact with the Izhikevich equation, understand the
model generating Spikeling membrane voltage, and create their own "neuron mode" to be loaded on the main page.

<p style='text-align: justify;'>
The main window computes the Izhikevich model with a modifiable current input. Users can change the 4 variable of the
code and display the resulting "neuron mode". This is also where users can come up with their own neuronal modes to
experiment on. This is also where teachers can generate their own custo-made neuron, save them, and impose them as
experimental model for, i.e. home assignments.

<p style='text-align: justify;'>
From <a href="https://pubmed.ncbi.nlm.nih.gov/18244602">Izhikevich publication</a>:
<em> Bifurcation methodologies enable us to reduce many biophysically accurate Hodgkin–Huxley-type neuronal models to a
two-dimensional (2-D) system of ordinary differential equations of the form:</em>

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
Here, v and u are dimensionless variables, and a, b, c, and d are dimensionless parameters, and '= d/dt, where t is the
time (0.1 µs).

<p style='text-align: justify;'>
The variable v represents the membrane potential of the neuron and u represents a membrane recovery variable, which
accounts for the activation of K+ ionic currents and inactivation of Na+ ionic currents, and it provides negative
feedback to v.

<p style='text-align: justify;'>
After the spike reaches its apex (+30 mV), the membrane voltage and the recovery variable are reset.
Synaptic currents or injected DC-currents are delivered via the variable I.

<p style='text-align: justify;'>
Below the stimulus frequency and strength sliders can be found a custom stimulus display. Here the user can choose to
use instead of the classical square wave, either a stimulus from a pre-design library (comprising sine wave, chirp,
white noise, etc.), or either a custom made stimulus generated from the GUI "stimulus generator" tab.
