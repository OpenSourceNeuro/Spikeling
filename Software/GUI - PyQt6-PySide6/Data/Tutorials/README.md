# Demonstration data — synthetic, not a hardware recording

`tutorial_CC_spikes.csv` is an **illustrative synthetic** current-clamp recording for the first Data Analysis tutorial. It was generated using a simple regular-spiking Izhikevich model (`a=0.02`, `b=0.2`, `c=-65`, `d=8`, `dt=0.1 ms`) and three current pulses. This is **not** data captured from the Spikeling board or its current emulator build, nor is it claimed to reproduce the complete current firmware. It is intentionally free of noise and synaptic inputs.

Stimulus windows: 200–500 ms (8 model current units), 700–1000 ms (12 units), 1200–1500 ms (8 units). The `Stimulus (%)` column is an illustrative marker (35/55/35); it is **not a calibrated mapping** between model current and hardware percentage. `Trigger` has a one-sample onset marker for each pulse. The six other signal columns use Spikeling's expected CSV naming convention; unused synaptic columns are zeros. No acquisition metadata is attached, by design.

You can use this recording to practise importing, viewing Vm and stimulus, selecting a spike threshold and inspecting detected spike events. Do not use this synthetic dataset to validate the physical hardware, infer drug pharmacology, or quantify real experimental uncertainty.
