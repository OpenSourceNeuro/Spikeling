Spikeling now possesses its own GUI, written in python and using the latest PyQt6/PySide6 library. The script then uses
pyInstaller so it can be translated into a windows/linux/mac app, ready to be easily distributed to users.


The GUI is divided into distinct pages. The first one is the main GUI window where users connect the board to the
computer. From there they can choose to either select the neuronal mode on the board directly (neuron mode box) or
through the GUI (note that custom modes will have to be selected from here, and in this instance the GUI takes priority
over the board commands).

The main window displays the Spikeling activity (Neuron Vm, total current input from all sources & stimulus ). If
connected to other Spikelings, the GUI can display synaptic inputs: their incoming neuron Vm and their spiking events,
which will be translated into input current for the main neuron. Traces can be selected through checkbox and
superimposed over the same graph with a common timeline.

The "Neuron Mode" defines the current Izhikevich model being used [see Neuron Generator](user-guide/neuron-generator.md)
. Twelve are encoded by default on the Spikeling unit and can be chosen either from the board itself or directly from
the GUI: "Select Neuron Mode". Note that any command from the GUI will take priority over the board. Custom Neuron Modes
can be selected from here and upload to the board.

The neuron interface page also possesses two buttons to enable/disable the spike buzzer sound and the spike LED, which
in a class room full of spikeling, are regarded as huge relieves.

Below the main window, sits the recording window. All last generated data from traces that are checked on the main
window will be saved in a .csv format.

On the right hand side two control columns can be found. For all commands, when the toggle button is enabled, the GUI
takes over the potentiometer and controls directly the Spikeling variables. This allows users to design an experimental
protocol in a controlled fashion.
