// SPDX-License-Identifier: GPL-3.0-or-later

import assert from "node:assert/strict";
import test from "node:test";

import {
  DEFAULT_RANDOM_SEED,
  DISPLAY_PEAK_MV,
  INITIAL_STIMULUS_PERIOD_STEPS,
  MINIMUM_POTENTIAL_MV,
  NEURON_PRESETS,
  SeededRandomSource,
  SequenceRandomSource,
  SpikelingModel,
  TIMESTEP_MS,
  createPhotoreceptorState,
  getPreset,
  integrateNeuron,
  stepPhotoreceptor,
} from "../src/index.ts";

test("all 20 Python-source presets are exposed with stable one-based ids", () => {
  assert.equal(NEURON_PRESETS.length, 20);
  assert.deepEqual(
    NEURON_PRESETS.map((preset) => preset.id),
    Array.from({ length: 20 }, (_, index) => index + 1),
  );
  assert.equal(getPreset(6).b, 0.22);
  assert.equal(getPreset("rebound-burst").id, 14);
  assert.equal(getPreset("Inhibition Induced Bursting").id, 20);
  assert.throws(() => getPreset(0), RangeError);
  assert.throws(() => getPreset(21), RangeError);
});

test("default startup honours the selected preset rather than desktop fixed defaults", () => {
  const model = new SpikelingModel();
  assert.equal(model.getControls().main.presetId, 1);
  assert.equal(getPreset(1).d, 6);
  assert.equal(model.getState().main.neuron.v, -70);
  assert.equal(model.getState().main.neuron.u, 0);

  const rebound = new SpikelingModel({
    controls: { main: { presetId: 13 } },
  });
  assert.equal(rebound.getState().main.neuron.v, -64);
});

test("desktop initialisation is available for source-pinned parity fixtures", () => {
  const model = new SpikelingModel({
    controls: { main: { presetId: 13 } },
    initialisation: "desktop",
  });
  assert.equal(model.getState().main.neuron.v, -65);
  assert.equal(model.getControls().main.presetId, 13);
});

test("Izhikevich integration updates recovery using the newly integrated voltage", () => {
  const preset = getPreset(1);
  const previous = { v: -65, u: 0, totalCurrent: 12 };
  const expectedV =
    previous.v +
    TIMESTEP_MS *
      (0.04 * previous.v * previous.v +
        5 * previous.v +
        140 -
        previous.u +
        previous.totalCurrent);
  const expectedU =
    previous.u + TIMESTEP_MS * (preset.a * (preset.b * expectedV - previous.u));
  const result = integrateNeuron(previous, preset);

  assert.equal(result.v, expectedV);
  assert.equal(result.u, expectedU);
  assert.equal(result.spiked, false);
});

test("display peaks, threshold resets and lower clamps retain desktop ordering", () => {
  const preset = getPreset(1);
  const visiblePeak = integrateNeuron({ v: 0, u: 0, totalCurrent: 0 }, preset);
  assert.equal(visiblePeak.v, DISPLAY_PEAK_MV);
  assert.equal(visiblePeak.spiked, true);

  const immediateReset = integrateNeuron({ v: 29, u: 0, totalCurrent: 0 }, preset);
  assert.equal(immediateReset.v, preset.c);
  assert.equal(immediateReset.spiked, false);
  assert.ok(immediateReset.u > preset.d);

  const clamped = integrateNeuron(
    { v: -110, u: 0, totalCurrent: -1000 },
    preset,
  );
  assert.equal(clamped.v, MINIMUM_POTENTIAL_MV);
});

test("the main neuron sees a control-current change one sample later", () => {
  const baseline = new SpikelingModel({ initialisation: "desktop" });
  const injected = new SpikelingModel({
    initialisation: "desktop",
    controls: { main: { patchCurrent: 30 } },
  });

  const baselineFirst = baseline.step();
  const injectedFirst = injected.step();
  assert.equal(injectedFirst.mainVm, baselineFirst.mainVm);
  assert.equal(injectedFirst.totalCurrent, 30);

  const baselineSecond = baseline.step();
  const injectedSecond = injected.step();
  assert.notEqual(injectedSecond.mainVm, baselineSecond.mainVm);
});

test("the initial square-wave period remains 1000 samples with a one-sample trigger", () => {
  const model = new SpikelingModel({
    controls: {
      main: { directCurrentEnabled: true },
      stimulus: { strength: 25, frequencySlider: 35 },
    },
  });

  const samples = model.run(INITIAL_STIMULUS_PERIOD_STEPS + 3);
  assert.equal(samples[0].stimulus, 25);
  assert.equal(samples[499].stimulus, 25);
  assert.equal(samples[500].stimulus, 0);
  assert.equal(samples[999].trigger, 0);
  assert.equal(samples[1000].trigger, 1);
  assert.equal(samples[1001].trigger, 0);
  assert.equal(model.getState().stimulus.steps, 335);
});

test("custom stimuli loop at 0.1 ms and trigger on every wrap", () => {
  const model = new SpikelingModel({
    controls: {
      main: { directCurrentEnabled: true },
      stimulus: { mode: "custom", customSamples: [5, -2, 11] },
    },
  });

  const samples = model.run(7);
  assert.deepEqual(
    samples.map((sample) => sample.stimulus),
    [5, -2, 11, 5, -2, 11, 5],
  );
  assert.deepEqual(
    samples.map((sample) => sample.trigger),
    [1, 0, 0, 1, 0, 0, 1],
  );
});

test("photoreceptor coefficients change after the current recovery update", () => {
  const state = createPhotoreceptorState();
  const current = stepPhotoreceptor(state, 25, {
    gain: 10,
    decaySlider: 125,
    recoverySlider: 50,
  });

  assert.equal(current, 20);
  assert.equal(state.recovery, 1.005);
  assert.equal(state.decay, 0.00125);
  assert.equal(state.recoveryRate, 0.05);
});

test("photoreceptor recovery never falls below zero before its recovery increment", () => {
  const state = createPhotoreceptorState();
  state.decay = 1;

  stepPhotoreceptor(state, 100, {
    gain: 100,
    decaySlider: 100,
    recoverySlider: 25,
  });

  assert.equal(state.recovery, 0.025);
});

test("positive and negative auxiliary gains produce the correct current sign", () => {
  for (const gain of [20, -20]) {
    const model = new SpikelingModel({
      initialisation: "desktop",
      controls: {
        synapse1: {
          enabled: true,
          patchCurrent: 45,
          gain,
        },
      },
    });
    const samples = model.run(900);
    const active = samples.find((sample) => sample.synapse1Current !== 0);
    assert.ok(active, "Expected a presynaptic spike for gain " + gain);
    assert.equal(Math.sign(active.synapse1Current), Math.sign(gain));
  }
});

test("Synapse 2 uses its selected decay and can reproduce the legacy defect explicitly", () => {
  const controls = {
    synapse2: {
      enabled: true,
      patchCurrent: 45,
      gain: 20,
      decaySlider: 980,
    },
  };

  const corrected = new SpikelingModel({
    initialisation: "desktop",
    controls,
  });
  const legacy = new SpikelingModel({
    initialisation: "desktop",
    controls,
    compatibility: { legacySynapse2DecayBug: true },
  });

  const correctedSamples = corrected.run(900);
  const legacySamples = legacy.run(900);
  const firstSpike = correctedSamples.findIndex(
    (sample) => sample.synapse2Current !== 0,
  );

  assert.ok(firstSpike >= 0, "Expected a Synapse 2 presynaptic spike.");
  assert.equal(correctedSamples[firstSpike].synapse2Current, 20 * 0.98);
  assert.equal(legacySamples[firstSpike].synapse2Current, 20 * 0.995);
});

test("auxiliary patch current supports the intended signed -50..50 range", () => {
  const model = new SpikelingModel({
    controls: {
      synapse1: { enabled: true, patchCurrent: -50 },
      synapse2: { enabled: true, patchCurrent: 50 },
    },
  });
  assert.equal(model.getControls().synapse1.patchCurrent, -50);
  assert.equal(model.getControls().synapse2.patchCurrent, 50);
  assert.throws(
    () =>
      new SpikelingModel({
        controls: { synapse1: { patchCurrent: 51 } },
      }),
    RangeError,
  );
});

test("disabling a synapse clears output while retaining its hidden neuron state", () => {
  const model = new SpikelingModel({
    initialisation: "desktop",
    controls: {
      synapse1: { enabled: true, patchCurrent: 45, gain: 15 },
    },
  });
  model.run(140);
  const hiddenBefore = model.getState().synapse1.neuron;

  model.updateControls({ synapse1: { enabled: false } });
  const disabled = model.step();
  const hiddenAfter = model.getState().synapse1.neuron;

  assert.equal(disabled.synapse1Vm, 0);
  assert.equal(disabled.synapse1Current, 0);
  assert.deepEqual(hiddenAfter, hiddenBefore);
});

test("portable seeded noise is reproducible and reset restores the exact sequence", () => {
  const options = {
    seed: 123456,
    controls: {
      main: { noiseLevel: 30 },
      synapse1: { enabled: true, noiseLevel: 20 },
    },
  };
  const first = new SpikelingModel(options);
  const second = new SpikelingModel(options);

  const expected = first.run(32);
  assert.deepEqual(second.run(32), expected);
  first.reset();
  assert.deepEqual(first.run(32), expected);
  assert.equal(typeof DEFAULT_RANDOM_SEED, "number");
});

test("a prescribed Gaussian sequence can be injected for deterministic experiments", () => {
  const model = new SpikelingModel({
    randomSource: new SequenceRandomSource([1, -2, 0.5]),
    controls: { main: { noiseLevel: 8 } },
  });

  assert.deepEqual(
    model.run(4).map((sample) => sample.totalCurrent),
    [2, -4, 1, 2],
  );
});

test("seed and sample validation rejects invalid values", () => {
  assert.throws(() => new SeededRandomSource(0), RangeError);
  assert.throws(() => new SeededRandomSource(0x100000000), RangeError);
  assert.throws(() => new SequenceRandomSource([]), TypeError);
  assert.throws(
    () =>
      new SpikelingModel({
        controls: { stimulus: { mode: "custom", customSamples: [] } },
      }),
    RangeError,
  );
  assert.throws(
    () =>
      new SpikelingModel({
        controls: { stimulus: { customSamples: [Number.NaN] } },
      }),
    TypeError,
  );
  assert.throws(
    () =>
      new SpikelingModel({
        controls: { stimulus: { mode: "invalid" as "custom" } },
      }),
    TypeError,
  );
  assert.throws(
    () => new SpikelingModel({ initialisation: "invalid" as "desktop" }),
    TypeError,
  );
});

test("switching to a custom stimulus starts a new trigger-aligned sequence", () => {
  const model = new SpikelingModel();
  model.run(5);
  model.updateControls({
    stimulus: { mode: "custom", customSamples: [4, 8] },
  });

  const first = model.step();
  assert.equal(first.stimulus, 4);
  assert.equal(first.trigger, 1);

  model.updateControls({ stimulus: { customSamples: [9, 3] } });
  const replaced = model.step();
  assert.equal(replaced.stimulus, 9);
  assert.equal(replaced.trigger, 1);
});

test("reset and run reject incompatible or invalid scientific inputs", () => {
  const externalRandom = new SpikelingModel({
    randomSource: new SequenceRandomSource([1]),
  });
  assert.throws(() => externalRandom.reset({ seed: 123 }), TypeError);

  const model = new SpikelingModel();
  assert.throws(
    () => model.reset({ initialisation: "invalid" as "desktop" }),
    TypeError,
  );

  const safe = new SpikelingModel();
  assert.throws(() => safe.run(-1), RangeError);
  assert.throws(() => safe.run(0.5), RangeError);
  assert.deepEqual(safe.run(0), []);
});

test("reset preserves selected controls while restarting at their preset resting voltage", () => {
  const model = new SpikelingModel({
    controls: { main: { presetId: 14, patchCurrent: 20 } },
  });
  model.run(40);
  model.reset();

  const state = model.getState();
  assert.equal(state.stepIndex, 0);
  assert.equal(state.main.neuron.v, -64);
  assert.equal(model.getControls().main.patchCurrent, 20);
});

test("every preset produces finite states over a representative run", () => {
  for (const preset of NEURON_PRESETS) {
    const model = new SpikelingModel({
      controls: { main: { presetId: preset.id, patchCurrent: 12 } },
    });
    const samples = model.run(400);
    for (const sample of samples) {
      assert.ok(
        Number.isFinite(sample.mainVm) && Number.isFinite(sample.mainRecovery),
        "Preset " + preset.label + " produced a non-finite state.",
      );
    }
  }
});
