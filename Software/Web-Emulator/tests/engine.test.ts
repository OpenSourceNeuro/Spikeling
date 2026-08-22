// SPDX-License-Identifier: GPL-3.0-or-later

import assert from "node:assert/strict";
import test from "node:test";

import {
  DEFAULT_HISTORY_CAPACITY,
  DEFAULT_SPEED_INDEX,
  DEFAULT_VISIBLE_SAMPLES,
  DESKTOP_STEPS_PER_UPDATE,
  DESKTOP_UPDATE_INTERVAL_MS,
  SAMPLE_COLUMNS,
  SAMPLE_WIDTH,
  SampleRingBuffer,
  SimulationEngine,
  SpikelingModel,
  TIMESTEP_MS,
  getSimulationSpeed,
  packSamples,
  unpackSamples,
} from "../src/index.ts";
import type { EngineSnapshot, SimulationSample } from "../src/index.ts";
import { ManualScheduler } from "./helpers/manual-scheduler.ts";

test("all ten source-audited desktop speed settings expose honest wall-clock ratios", () => {
  assert.deepEqual(DESKTOP_STEPS_PER_UPDATE, [
    10, 20, 50, 100, 200, 500, 1_000, 2_000, 5_000, 10_000,
  ]);
  assert.equal(DESKTOP_UPDATE_INTERVAL_MS, 50);
  assert.equal(DEFAULT_SPEED_INDEX, 2);

  const multipliers = DESKTOP_STEPS_PER_UPDATE.map(
    (_, index) => getSimulationSpeed(index).realtimeMultiplier,
  );
  assert.deepEqual(multipliers, [0.02, 0.04, 0.1, 0.2, 0.4, 1, 2, 4, 10, 20]);
  assert.equal(getSimulationSpeed(5).stepsPerSecond, 10_000);
  assert.equal(getSimulationSpeed(5).simulatedMillisecondsPerUpdate, 50);
  assert.equal(getSimulationSpeed(0).desktopLabelMultiplier, 0.001);
  assert.equal(getSimulationSpeed(9).desktopLabelMultiplier, 1);

  for (const invalid of [-1, 10, 1.5, Number.NaN, Number.POSITIVE_INFINITY]) {
    assert.throws(() => getSimulationSpeed(invalid), RangeError);
  }
});

test("history allocations are fixed-width Float64 buffers with desktop-sized windows", () => {
  const history = new SampleRingBuffer();
  assert.equal(DEFAULT_HISTORY_CAPACITY, 50_000);
  assert.equal(DEFAULT_VISIBLE_SAMPLES, 5_000);
  assert.equal(SAMPLE_COLUMNS.length, 12);
  assert.equal(SAMPLE_WIDTH, 12);
  assert.equal(history.capacity, 50_000);
  assert.equal(history.allocatedBytes, 4_800_000);
  assert.equal(history.length, 0);
  assert.equal(history.totalWritten, 0);
  assert.deepEqual(history.latest(), []);

  for (const invalid of [0, -1, 1.2, Number.NaN]) {
    assert.throws(() => new SampleRingBuffer(invalid), RangeError);
  }
});

test("a circular history overwrites the oldest samples in chronological order", () => {
  const model = new SpikelingModel({ seed: 345 });
  const samples = model.run(7);
  const history = new SampleRingBuffer(4);

  history.pushBatch(samples.slice(0, 2));
  assert.deepEqual(history.latest(), samples.slice(0, 2));
  assert.deepEqual(history.at(-1), samples[1]);
  assert.equal(history.at(-3), undefined);
  assert.equal(history.at(2), undefined);

  history.pushBatch(samples.slice(2));
  assert.equal(history.length, 4);
  assert.equal(history.totalWritten, 7);
  assert.deepEqual(history.latest(), samples.slice(-4));
  assert.deepEqual(history.latest(2), samples.slice(-2));
  assert.deepEqual(history.latest(100), samples.slice(-4));
  assert.deepEqual(history.latest(0), []);
  assert.deepEqual(history.at(0), samples[3]);
  assert.deepEqual(history.at(-4), samples[3]);
  assert.throws(() => history.at(0.5), RangeError);
  assert.throws(() => history.latest(-1), RangeError);
  assert.throws(() => history.latest(1.5), RangeError);

  history.clear();
  assert.equal(history.length, 0);
  assert.equal(history.totalWritten, 0);
  assert.equal(history.allocatedBytes, 4 * 12 * 8);
  assert.deepEqual(history.latest(), []);
});

test("transferable batches preserve every scientific field at full Float64 precision", () => {
  const model = new SpikelingModel({
    seed: 784,
    controls: {
      main: { noiseLevel: 10, directCurrentEnabled: true },
      synapse1: { enabled: true, patchCurrent: 35 },
      synapse2: { enabled: true, patchCurrent: 35 },
      stimulus: { mode: "custom", customSamples: [Math.PI, -Math.E, 0] },
    },
  });
  const original = model.run(30);
  const packed = packSamples(original);

  assert.ok(packed instanceof Float64Array);
  assert.equal(packed.length, original.length * SAMPLE_WIDTH);
  assert.deepEqual(unpackSamples(packed), original);
  assert.deepEqual(unpackSamples(packSamples([])), []);
  assert.throws(() => unpackSamples(new Float64Array(11)), RangeError);

  const malformed = packed.slice(0, SAMPLE_WIDTH);
  malformed[11] = 2;
  assert.throws(() => unpackSamples(malformed), RangeError);
});

test("simulation waits for its fixed tick and advances independently of rendering", () => {
  const scheduler = new ManualScheduler();
  const emitted: SimulationSample[] = [];
  const states: EngineSnapshot[] = [];
  const engine = new SimulationEngine({
    scheduler,
    speedIndex: 2,
    onSamples: (samples) => emitted.push(...samples),
    onState: (snapshot) => states.push(snapshot),
  });

  assert.equal(engine.getSnapshot().lifecycle, "idle");
  engine.start();
  engine.start();
  assert.equal(scheduler.pending, 1);
  assert.equal(states.length, 1);
  scheduler.advance(49);
  assert.equal(emitted.length, 0);
  scheduler.advance(1);
  assert.equal(emitted.length, 50);
  assert.equal(engine.getSnapshot().stepIndex, 50);
  assert.equal(engine.history.length, 50);
  assert.equal(emitted[0].timeMs, 0);
  assert.equal(emitted[49].timeMs, 49 * TIMESTEP_MS);
  scheduler.advance(50);
  assert.equal(emitted.length, 100);
});

test("each desktop speed produces exactly its documented fixed-tick sample count", () => {
  for (const [index, expected] of DESKTOP_STEPS_PER_UPDATE.entries()) {
    const scheduler = new ManualScheduler();
    const engine = new SimulationEngine({ scheduler, speedIndex: index });
    engine.start();
    scheduler.advance(DESKTOP_UPDATE_INTERVAL_MS);
    assert.equal(engine.getSnapshot().stepIndex, expected, "speed index " + index);
    engine.dispose();
  }
});

test("large model updates yield in bounded slices and accept controls between them", () => {
  const scheduler = new ManualScheduler();
  const slices: number[] = [];
  const engine = new SimulationEngine({
    scheduler,
    speedIndex: 9,
    maxStepsPerSlice: 125,
    onSamples: (samples) => slices.push(samples.length),
  });

  engine.start();
  scheduler.elapse(50);
  assert.equal(scheduler.runNext(), true);
  assert.deepEqual(slices, [125]);
  assert.equal(engine.getSnapshot().pendingSteps, 9_875);

  engine.updateControls({ main: { patchCurrent: 42 } });
  assert.equal(engine.getSnapshot().controls.main.patchCurrent, 42);
  assert.equal(scheduler.runNext(), true);
  assert.equal(engine.history.at(-1)?.totalCurrent, 42);

  scheduler.flush();
  assert.equal(engine.getSnapshot().stepIndex, 10_000);
  assert.equal(slices.length, 80);
  assert.ok(slices.every((length) => length <= 125));
});

test("pause cancels pending slices and resumes without losing scientific state", () => {
  const scheduler = new ManualScheduler();
  const engine = new SimulationEngine({
    scheduler,
    speedIndex: 9,
    maxStepsPerSlice: 200,
  });

  engine.pause();
  engine.start();
  scheduler.elapse(50);
  scheduler.runNext();
  assert.equal(engine.getSnapshot().stepIndex, 200);
  engine.pause();
  engine.pause();
  assert.equal(engine.getSnapshot().lifecycle, "paused");
  assert.equal(engine.getSnapshot().pendingSteps, 0);
  assert.equal(scheduler.pending, 0);
  scheduler.advance(5_000);
  assert.equal(engine.getSnapshot().stepIndex, 200);

  engine.setSpeed(0);
  engine.start();
  scheduler.advance(50);
  assert.equal(engine.getSnapshot().stepIndex, 210);
  assert.equal(engine.history.at(-1)?.timeMs, 209 * TIMESTEP_MS);
});

test("stop cancels work and resets the model, history and pending scheduler", () => {
  const scheduler = new ManualScheduler();
  const engine = new SimulationEngine({
    scheduler,
    modelOptions: { controls: { main: { patchCurrent: 17 } } },
  });

  engine.start();
  scheduler.advance(50);
  const firstRun = engine.history.latest();
  engine.stop();
  assert.equal(engine.getSnapshot().lifecycle, "stopped");
  assert.equal(engine.getSnapshot().stepIndex, 0);
  assert.equal(engine.history.length, 0);
  assert.equal(engine.getSnapshot().controls.main.patchCurrent, 17);
  assert.equal(scheduler.pending, 0);

  engine.start();
  scheduler.advance(50);
  assert.deepEqual(engine.history.latest(), firstRun);
});

test("reset restores deterministic state and keeps an already-running engine active", () => {
  const scheduler = new ManualScheduler();
  const engine = new SimulationEngine({
    scheduler,
    speedIndex: 0,
    modelOptions: { seed: 871, controls: { main: { noiseLevel: 12 } } },
  });

  engine.start();
  scheduler.advance(50);
  const initial = engine.history.latest();
  engine.reset();
  assert.equal(engine.getSnapshot().lifecycle, "running");
  assert.equal(engine.history.length, 0);
  assert.equal(scheduler.pending, 1);
  scheduler.advance(50);
  assert.deepEqual(engine.history.latest(), initial);

  engine.pause();
  engine.reset({ seed: 872, initialisation: "desktop" });
  assert.equal(engine.getSnapshot().lifecycle, "idle");
  assert.equal(engine.getSnapshot().stepIndex, 0);
  assert.equal(engine.model.getState().main.neuron.v, -65);
  assert.equal(scheduler.pending, 0);
});

test("changing speed while running takes effect at the next simulation tick", () => {
  const scheduler = new ManualScheduler();
  const engine = new SimulationEngine({ scheduler, speedIndex: 0 });
  engine.start();
  scheduler.advance(50);
  assert.equal(engine.history.length, 10);
  engine.setSpeed(5);
  scheduler.advance(50);
  assert.equal(engine.history.length, 510);
  assert.equal(engine.getSnapshot().speed.realtimeMultiplier, 1);
  assert.throws(() => engine.setSpeed(10), RangeError);
});

test("background-tab catch-up is capped and reports explicitly discarded work", () => {
  const scheduler = new ManualScheduler();
  const engine = new SimulationEngine({
    scheduler,
    speedIndex: 1,
    maxCatchUpTicks: 3,
  });
  engine.start();
  scheduler.advance(500);

  assert.equal(engine.getSnapshot().stepIndex, 60);
  assert.equal(engine.getSnapshot().droppedSteps, 140);
  assert.equal(engine.getSnapshot().pendingSteps, 0);
  scheduler.advance(50);
  assert.equal(engine.getSnapshot().stepIndex, 80);
});

test("callbacks can pause an active slice without scheduling additional work", () => {
  const scheduler = new ManualScheduler();
  let engine: SimulationEngine;
  engine = new SimulationEngine({
    scheduler,
    speedIndex: 9,
    maxStepsPerSlice: 10,
    onSamples: () => engine.pause(),
  });

  engine.start();
  scheduler.advance(50);
  assert.equal(engine.getSnapshot().lifecycle, "paused");
  assert.equal(engine.getSnapshot().stepIndex, 10);
  assert.equal(scheduler.pending, 0);
});

test("scheduler failures pause safely and report errors without an infinite loop", () => {
  const scheduler = new ManualScheduler();
  const errors: Error[] = [];
  const engine = new SimulationEngine({
    scheduler,
    onSamples: () => {
      throw new Error("listener failure");
    },
    onError: (error) => errors.push(error),
  });

  engine.start();
  scheduler.advance(50);
  assert.equal(engine.getSnapshot().lifecycle, "paused");
  assert.equal(scheduler.pending, 0);
  assert.equal(errors.length, 1);
  assert.equal(errors[0].message, "listener failure");
});

test("engine configuration rejects invalid models, speeds and scheduler limits", () => {
  assert.throws(
    () =>
      new SimulationEngine({ model: new SpikelingModel(), modelOptions: { seed: 4 } }),
    TypeError,
  );
  assert.throws(() => new SimulationEngine({ speedIndex: -1 }), RangeError);
  assert.throws(() => new SimulationEngine({ maxStepsPerSlice: 0 }), RangeError);
  assert.throws(() => new SimulationEngine({ maxCatchUpTicks: 1.1 }), RangeError);
  assert.throws(() => new SimulationEngine({ historyCapacity: -1 }), RangeError);

  const existing = new SpikelingModel({ seed: 77 });
  const engine = new SimulationEngine({ model: existing, scheduler: new ManualScheduler() });
  assert.equal(engine.model, existing);
  engine.dispose();
  assert.equal(engine.getSnapshot().lifecycle, "stopped");
});
