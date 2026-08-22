// SPDX-License-Identifier: GPL-3.0-or-later

import assert from "node:assert/strict";
import test from "node:test";

import {
  SAMPLE_WIDTH,
  SimulationEngine,
  SpikelingModel,
  getSimulationSpeed,
} from "../src/index.ts";
import { ManualScheduler } from "./helpers/manual-scheduler.ts";

test("maximum desktop speed remains interruptible and preserves full-resolution parity", (context) => {
  const scheduler = new ManualScheduler();
  const slices: number[] = [];
  const options = {
    seed: 420,
    controls: {
      main: { noiseLevel: 8, directCurrentEnabled: true },
      synapse1: { enabled: true, patchCurrent: 33 },
      synapse2: { enabled: true, patchCurrent: 39 },
    },
  };
  const engine = new SimulationEngine({
    scheduler,
    speedIndex: 9,
    maxStepsPerSlice: 250,
    modelOptions: options,
    onSamples: (samples) => slices.push(samples.length),
  });

  engine.start();
  const started = performance.now();
  scheduler.advance(50);
  const elapsed = performance.now() - started;
  const expected = new SpikelingModel(options).run(10_000);

  assert.equal(engine.history.length, 10_000);
  assert.equal(slices.length, 40);
  assert.ok(slices.every((length) => length <= 250));
  assert.deepEqual(engine.history.at(0), expected[0]);
  assert.deepEqual(engine.history.at(4_999), expected[4_999]);
  assert.deepEqual(engine.history.at(-1), expected.at(-1));
  assert.ok(elapsed < 3_000, "10,000 full scientific steps took " + elapsed + " ms");

  context.diagnostic(
    "Maximum speed: 10,000 samples in " +
      elapsed.toFixed(1) +
      " ms; " +
      Math.round(10_000 / (elapsed / 1_000)).toLocaleString("en-GB") +
      " samples/s; 40 interruptible slices; target " +
      getSimulationSpeed(9).stepsPerSecond.toLocaleString("en-GB") +
      " samples/s.",
  );
});

test("extended maximum-speed simulation keeps memory and history strictly bounded", (context) => {
  const scheduler = new ManualScheduler();
  const engine = new SimulationEngine({
    scheduler,
    speedIndex: 9,
    historyCapacity: 5_000,
    maxStepsPerSlice: 250,
  });
  engine.start();

  const started = performance.now();
  for (let tick = 0; tick < 7; tick += 1) {
    scheduler.advance(50);
  }
  const elapsed = performance.now() - started;
  const snapshot = engine.getSnapshot();

  assert.equal(snapshot.stepIndex, 70_000);
  assert.equal(snapshot.retainedSamples, 5_000);
  assert.equal(engine.history.totalWritten, 70_000);
  assert.equal(snapshot.historyBytes, 5_000 * SAMPLE_WIDTH * 8);
  assert.equal(engine.history.at(0)?.timeMs, 6_500);
  assert.equal(engine.history.at(-1)?.timeMs, 6_999.900000000001);
  assert.ok(elapsed < 8_000, "70,000 bounded steps took " + elapsed + " ms");

  context.diagnostic(
    "Bounded run: 70,000 samples in " +
      elapsed.toFixed(1) +
      " ms; retained 5,000; fixed history " +
      snapshot.historyBytes.toLocaleString("en-GB") +
      " bytes.",
  );
});

test("background suspension cannot queue unbounded scientific catch-up work", () => {
  const scheduler = new ManualScheduler();
  const engine = new SimulationEngine({
    scheduler,
    speedIndex: 9,
    maxCatchUpTicks: 2,
    maxStepsPerSlice: 250,
  });

  engine.start();
  scheduler.elapse(60_000);
  scheduler.runNext();
  const firstSlice = engine.getSnapshot();
  assert.equal(firstSlice.stepIndex, 250);
  assert.equal(firstSlice.pendingSteps, 19_750);
  assert.equal(firstSlice.droppedSteps, 11_980_000);
  scheduler.flush();
  assert.equal(engine.getSnapshot().stepIndex, 20_000);
  assert.equal(scheduler.pending, 1);
});
