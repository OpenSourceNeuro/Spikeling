# Welcome to the official Spikeling GitHub

Understanding of how neurons encode and compute information is fundamental to our study of the brain, but opportunities for hands-on experience with neurophysiological techniques on live neurons are scarce in science education. Here, we present Spikeling, an open source £25 in silico implementation of a spiking neuron that mimics a wide range of neuronal behaviours for classroom education and public neuroscience outreach.

For details, please refer to
- the main manuscript on BioRxiv [here](https://www.biorxiv.org/content/early/2018/05/21/327502) 
- the entry on Open Labware [here](https://open-labware.net/projects/spikeling/)

![Spikeling in action](https://openlabwaredotnet.files.wordpress.com/2018/05/spikeling-picci.png)


Spikeling is based on an Arduino microcontroller running the computationally efficient Izhikevich model of a spiking neuron.  The microcontroller is connected to input ports that simulate synaptic excitation or inhibition, dials controlling current injection and noise levels, a photodiode that makes Spikeling light-sensitive and an LED and speaker that allows spikes to be seen and heard. Output ports provide access to variables such as membrane potential for recording in experiments or digital signals that can be used to excite other connected Spikelings. These features allow for the intuitive exploration of the function of neurons and networks.

# Files

In this repository and the associated publication (linked above) you will find all files needed to build a Spikeling, get started with it and do some basic data analysis.



