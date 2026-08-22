# Spikeling Web Emulator

Phases 1–3 implement the numerically validated, worker-based simulation engine
and scientific oscilloscope for the Open Source Neuro Spikeling emulator. The
package includes the browser-independent model, a dedicated worker,
desktop-equivalent timing, bounded full-precision histories, a UI-independent
data-source interface and a responsive dual-axis rolling oscilloscope. It does
not yet add full neuron/synapse control panels, WordPress integration, serial
support or deployment configuration.

## Requirements

- Node.js 24 or later. Node runs the erasable TypeScript syntax directly.
- Python 3.10 or later.
- A complete checkout of the Spikeling repository, including the existing
  desktop emulator under Software/GUI - PyQt6-PySide6.

There are no third-party runtime or test dependencies.

## Run the checks

From Software/Web-Emulator:

    npm run fixtures
    npm run verify

The first command regenerates committed Python desktop-reference fixtures. The
second checks that those fixtures still match the pinned desktop source and then
runs the TypeScript model, cross-language parity, engine, worker, oscilloscope
and performance tests.

Run individual groups with:

    npm run test:model
    npm run test:parity
    npm run test:engine
    npm run test:worker
    npm run test:performance
    npm run test:visualisation

## Run the local oscilloscope preview

From Software/Web-Emulator:

    npm run dev

Open the printed local address, normally http://127.0.0.1:4173/, and select
Start. The standalone preview runs the actual dedicated worker, displays
desktop-matched membrane-voltage, stimulus and current traces, and exposes the
existing start/pause/stop/reset and speed controls. The seven trace checkboxes
use semantic, keyboard-operable native inputs.

The local server strips Node-supported erasable TypeScript syntax on demand and
serves native browser modules with their correct MIME types. It requires no
Vite installation, third-party framework, package download, WordPress access or
website deployment. Set SPIKELING_DEV_PORT to select a different local port.

## Public model API

Import SpikelingModel and the 20 NEURON_PRESETS from src/index.ts:

    const model = new SpikelingModel({
      controls: {
        main: { presetId: 1, patchCurrent: 18 },
      },
      seed: 123456,
    });

    const firstSample = model.step();
    const nextThousandSamples = model.run(1000);
    model.updateControls({ main: { patchCurrent: 24 } });
    model.reset();

The model exposes a 0.1 ms fixed timestep; main and auxiliary-neuron recovery
states; internal and custom stimuli; deterministic Gaussian noise; a recovering
photoreceptor; and two signed, decaying synaptic inputs.

## Worker-backed data source

Browser rendering and controls should depend on the DataSource boundary instead
of importing the model or managing a worker directly:

    const source = new EmulatorSource({
      simulation: {
        seed: 123456,
        controls: { main: { presetId: 1, patchCurrent: 18 } },
      },
      speedIndex: 5,
    });

    source.subscribe((fullResolutionSamples) => {
      // Supply scientific samples to a future recorder or visualisation.
    });

    source.subscribeState((state) => {
      // Observe run state, true speed, retained history and background drops.
    });

    await source.connect();
    source.start();
    source.updateControls({ main: { patchCurrent: 24 } });
    source.setSpeed(6);
    source.pause();
    source.start();
    source.reset();
    source.stop();
    await source.disconnect();

EmulatorSource creates a dedicated ES-module Web Worker. Its worker core owns
the scientific model, scheduler and bounded history. Each bounded simulation
slice is packed into a transferable Float64Array; the browser-side source
maintains a second bounded history for the oscilloscope and provides complete
0.1 ms samples to subscribers. No scientific value is downsampled or converted to
Float32.

The DataSource interface deliberately permits a later physical-hardware source
without making the oscilloscope depend on emulator implementation details. Web
Serial is not implemented and is not required for this phase.

## Timing and simulation speed

Numerical integration always uses the existing fixed 0.1 ms timestep. The
desktop-equivalent scheduler ticks every 50 wall-clock milliseconds, independently
of monitor refresh or the oscilloscope visualisation/render loop. Desktop speed
positions have the following audited meanings:

| Slider | Steps / 50 ms | Scientific samples / s | True real-time speed | Legacy desktop label |
| --- | ---: | ---: | ---: | ---: |
| 0 | 10 | 200 | 0.02× | 0.001× |
| 1 | 20 | 400 | 0.04× | 0.002× |
| 2 | 50 | 1,000 | 0.10× | 0.005× |
| 3 | 100 | 2,000 | 0.20× | 0.010× |
| 4 | 200 | 4,000 | 0.40× | 0.020× |
| 5 | 500 | 10,000 | 1.00× | 0.050× |
| 6 | 1,000 | 20,000 | 2.00× | 0.100× |
| 7 | 2,000 | 40,000 | 4.00× | 0.200× |
| 8 | 5,000 | 100,000 | 10.00× | 0.500× |
| 9 | 10,000 | 200,000 | 20.00× | 1.000× |

The desktop label describes a normalised slider position, not a physical
real-time multiplier. getSimulationSpeed exposes both values explicitly to
prevent a future UI from presenting the legacy label as a scientific timing
measurement.

By default, a simulation slice contains at most 250 model steps before the
worker yields. Therefore stop, pause, reset, speed changes and parameter changes
can be handled between slices, even at the maximum speed setting. A late or
background-throttled tick catches up at most four desktop intervals; additional
work is discarded deliberately and is visible in the droppedSteps diagnostic.

Pause preserves scientific state; start after pause resumes that state. Stop
clears history and restores the model's initial state without discarding chosen
controls. Reset clears history and reproducibly restarts the seeded model;
resetting an already-running engine keeps it running.

## Bounded scientific history

The default desktop-sized history retains 50,000 full-resolution samples, or
5,000 ms at the fixed 0.1 ms timestep. Its 12 preallocated Float64 columns use
exactly 4,800,000 bytes per ring buffer; the browser and worker each own one
independent bounded ring. The oscilloscope requests the desktop-sized visible
window of approximately 5,000 samples, corresponding to 500 ms.

When the ring fills, the oldest samples are overwritten in chronological order.
Display decimation is applied only to rendering and does not change the values
delivered to scientific consumers or future recording.

The performance tests verify maximum-speed slicing, 10,000-sample scientific
parity, 70,000-sample bounded-history runs and a simulated one-minute background
suspension. They also measure complete 5,000-sample, three-trace oscilloscope
frames and verify that rendering never changes scientific source samples.

## Desktop-matched scientific oscilloscope

Mount the oscilloscope against any object implementing DataSource:

    const source = new EmulatorSource({
      speedIndex: 5,
      simulation: {
        controls: {
          main: { patchCurrent: 18, directCurrentEnabled: true },
          stimulus: { strength: 25 },
        },
      },
    });

    const scope = new SpikelingOscilloscope(containerElement, source);
    await source.connect();
    source.start();
    scope.setTraceVisible("synapse1Current", true);

    // When removing the instrument:
    scope.dispose();
    await source.disconnect();

Load src/styles/oscilloscope.css alongside the component. Its named Solarized
CSS custom properties are scoped to .spk-oscilloscope and do not alter global
WordPress, Elementor or host-page styling.

The desktop Graph_Emulator.py plotting contract is preserved:

- Rolling x-axis: −500 to 0 ms of simulation time.
- Left axis: membrane potential, −90 to +30 mV.
- Right axis: current input, −100 to +100 arbitrary units.
- One CSS-pixel straight-segment traces; no spline or aesthetic interpolation.
- Device-pixel-ratio-aware backing Canvas with narrower mobile axis margins.
- Native keyboard-operable trace checkboxes and textual live signal readings.

| Desktop signal | Browser sample field | Axis | Source-matched colour | Initially visible |
| --- | --- | --- | --- | --- |
| Main membrane potential | mainVm | Voltage | Red #DC322F | Yes |
| Stimulus | stimulus | Current | Blue #268BD2 | Yes |
| Input current | totalCurrent | Current | Green #859900 | Yes |
| Synapse 1 membrane potential | synapse1Vm | Voltage | Orange #CB4B16 | No |
| Synapse 1 input current | synapse1Current | Current | Cyan #2AA198 | No |
| Synapse 2 membrane potential | synapse2Vm | Voltage | Yellow #B58900 | No |
| Synapse 2 input current | synapse2Current | Current | Magenta #D33682 | No |

The display decimator retains each horizontal pixel bucket's first, minimum,
maximum and last genuine samples in chronological order. Consequently a narrow
+30 mV action-potential peak or abrupt stimulus edge cannot disappear merely
because the chart is narrower than the full-resolution scientific window. No
new sample values are invented, and worker/recording data remains unchanged.

Worker batches invalidate an independent requestAnimationFrame-driven visual
loop. Multiple incoming batches are coalesced into a single paint; a frame is
not requested when the simulation is paused, stopped or the browser tab is
hidden. ResizeObserver updates Canvas geometry without changing the simulation
timestep, history or axis ranges.

## Desktop numerical contract

The reference is pinned to commit
4d5dbf8d5c14c6e9f95d4f2f2e8307ed3d164918 and verifies the exact Git blob hashes
of Graph_Emulator.py and Parameters_Izhikevich.py before generating fixtures.

The model preserves the desktop's:

- Izhikevich voltage update followed by a recovery update using the new voltage.
- 30 mV reset threshold, 30 mV displayed peak, and -110 mV lower clamp.
- One-sample delay before a newly assembled input current reaches the neuron.
- First 1,000-sample internal stimulus period and one-sample rollover trigger.
- Photoreceptor adaptation order and one-sample coefficient-update delay.
- Auxiliary-cell hidden-state retention when a synapse is switched off.
- Full 0.1 ms sample timestamps and unmodified scientific values.

Golden parity uses a maximum absolute error of 1e-8 and exact trigger timing.
Both implementations use the same portable xorshift32 plus Box-Muller generator
for deterministic noise.

## Approved differences from the desktop

The default browser initialisation honours the selected preset, including its
resting potential and its own a, b, c and d parameters. The initial recovery
state remains zero, as in the desktop. The alternative desktop initialisation
starts at -65 mV for direct reference comparisons.

All 20 desktop-source presets are exposed, although the current Qt combo boxes
only show the first 12. Spike Frequency Adaptation intentionally retains the
Python source value b=0.22; the firmware currently uses 0.20.

The desktop-compatible Inhibition Induced Bursting preset did not generate
displayed spikes under the tested negative-current conditions with its existing
u=0 initialisation. Its fixture therefore uses a documented positive-current
control to exercise the preset; its educational phenotype needs separate review
before a UI presents it as a validated inhibition-triggered demonstration.

Synapse 2 correctly uses its selected decay slider. The source-pinned desktop
bug can be reproduced only when legacySynapse2DecayBug is explicitly enabled
for parity tests. Auxiliary patch current accepts the intended signed -50..50
range instead of the desktop slider's erroneous 0..100 range.

## Next phase

Phase 4 will introduce the main-neuron controls: the neuron selector, stimulus,
injected current, noise, photoreceptor controls, custom stimulus and appropriate
parameter displays. The Phase 1 scientific contract, Phase 2 worker/data-source
boundary and Phase 3 truthful rolling oscilloscope should remain unchanged.

## Licence

GPL-3.0-or-later, consistent with the Spikeling software repository.
