# Spikeling Web Emulator

Phase 1 implements the browser-independent numerical core of the Open Source
Neuro Spikeling emulator. It does not add a user interface, Web Worker,
WordPress integration, serial support, or deployment configuration.

## Requirements

- Node.js 24 or later. Node runs the erasable TypeScript syntax directly.
- Python 3.10 or later.
- A complete checkout of the Spikeling repository, including the existing
  desktop emulator under Software/GUI - PyQt6-PySide6.

There are no third-party runtime or test dependencies in Phase 1.

## Run the checks

From Software/Web-Emulator:

    npm run fixtures
    npm run verify

The first command regenerates committed Python desktop-reference fixtures. The
second checks that those fixtures still match the pinned desktop source and then
runs the TypeScript model and cross-language parity tests.

Run individual groups with:

    npm run test:model
    npm run test:parity

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

Phase 2 will add the worker-based simulation clock, bounded ring buffers,
simulation-speed controls, start/pause/reset coordination, and a DataSource
boundary. It must retain the Phase 1 model and golden checks unchanged.

## Licence

GPL-3.0-or-later, consistent with the Spikeling software repository.
