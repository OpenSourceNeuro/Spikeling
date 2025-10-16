## A spiking neuron interface

<br>

<img align="left"  src="https://github.com/OpenSourceNeuro/Spikeling-V2/blob/main/Images/Spikeling_cover.png" width="400" height="250">

<p style='text-align: justify;'>
The entire layout of the Spikeling board has been reconceived and a laser-cut acrylic sheet repesenting a neuron now
sits on top of the board. All ports and potentiometers are now strategically placed.

<p style='text-align: justify;'>
The ESP32 is placed below the soma, the synaptic inputs from other Spikeling units are placed on the left, the synaptic
output is placed on the right. Along the axon now sits a RGB LED, the red LED brightness follows as before the Vm status
of the neuron, and the LED sparks in white when the neuron spike. The spike buzzer also sit along the axon, a small hole
on the acrylic sheet sitting just above so the click can be heard coming from that direction. Both indicators can now be
disabled by users at their pleasure.

<p style='text-align: justify;'>
The Vm potentiometer and the Current-in port are now grouped together and sit on the acrylic sheet at the bottom of an
electrode pipette. They can now be considered as patch clamp experiment variables.

<p style='text-align: justify;'>
A photoreceptor is now drawn on the acrylic sheet, below the opsin sits a photodiode, and a potentiometer on the
photoreceptor body now controls the photoreceptor sensitivity and its polarity (users can thus decide if the 
photoreceptor has an excitatory or an inhibitory effect on the neuron)

<p style='text-align: justify;'>
The noise potentiometer now sits in a box by itself as it represents parasitic noise from the experiment environment
(synaptic inputs, receptor noise, thermal noise, experimental setup, etc.) and is independent from the rest of the
Spikeling functions. This potentiometer is different from the others: it is not center-detented as it generates noise
from a zero to a maximum value.

<p style='text-align: justify;'>
Next is the Neuron mode box which contains the twelve available modes to the users and a push button that allows the 
user to switch between them.

<p style='text-align: justify;'>
Finally, the last box contains all experimental tools allowing stimuli generation. As detailed on the acrylic top cover,
the user can control the stimulus frequency and the stimulus intensity, along with its polarity. The stimulus output can
either be directly connected to the current-in port to simulate a current applied to a patched neuron through the
pipette; or be connected to a cable with a 5mm LED soldered at its tip which can be placed directly on top of the
photoreceptor opsin (photodiode below). The photoreceptor potentiometer allows to modulate the gain and polarity of the
light-induced input current. Furthermore, the photoreceptor possesses functions (on the GUI: decay/recovery) simulating
how a variety of photoreceptors would integrate a light stimuli and how it will adapt to prolonged stimulation.  
