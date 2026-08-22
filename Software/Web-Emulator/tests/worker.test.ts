// SPDX-License-Identifier: GPL-3.0-or-later

import assert from "node:assert/strict";
import test from "node:test";
import { Worker } from "node:worker_threads";

import {
  EmulatorSource,
  SAMPLE_WIDTH,
  SpikelingModel,
  createEmulatorWorkerRuntime,
  unpackSamples,
} from "../src/index.ts";
import type {
  EmulatorSourceWorker,
  EngineSnapshot,
  MainToWorkerMessage,
  SimulationSample,
  WorkerToMainMessage,
} from "../src/index.ts";
import { ManualScheduler } from "./helpers/manual-scheduler.ts";

type MessageListener = (event: { readonly data: WorkerToMainMessage }) => void;

class InProcessWorker implements EmulatorSourceWorker {
  readonly scheduler = new ManualScheduler();
  readonly received: MainToWorkerMessage[] = [];
  readonly listeners = new Set<MessageListener>();
  terminated = false;

  private readonly runtime = createEmulatorWorkerRuntime({
    scheduler: this.scheduler,
    postMessage: (message, transfer) => {
      const cloned = structuredClone(message, {
        transfer: transfer === undefined ? [] : [...transfer],
      });
      this.emit(cloned);
    },
  });

  postMessage(message: MainToWorkerMessage): void {
    this.received.push(message);
    this.runtime.handleMessage(message);
  }

  addEventListener(_type: "message", listener: MessageListener): void {
    this.listeners.add(listener);
  }

  removeEventListener(_type: "message", listener: MessageListener): void {
    this.listeners.delete(listener);
  }

  terminate(): Promise<number> {
    this.terminated = true;
    this.runtime.dispose();
    return Promise.resolve(0);
  }

  emit(message: WorkerToMainMessage): void {
    for (const listener of this.listeners) {
      listener({ data: message });
    }
  }
}

function workerMessage(
  worker: Worker,
  predicate: (message: WorkerToMainMessage) => boolean,
): Promise<WorkerToMainMessage> {
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      worker.off("message", listener);
      reject(new Error("Timed out waiting for the real emulator worker."));
    }, 3_000);

    function listener(message: WorkerToMainMessage): void {
      if (predicate(message)) {
        clearTimeout(timeout);
        worker.off("message", listener);
        resolve(message);
      }
    }

    worker.on("message", listener);
  });
}

test("the worker rejects commands before initialisation and malformed commands", () => {
  const messages: WorkerToMainMessage[] = [];
  const runtime = createEmulatorWorkerRuntime({
    postMessage: (message) => messages.push(message),
  });

  runtime.handleMessage({ type: "start" });
  assert.equal(messages[0].type, "error");
  if (messages[0].type === "error") {
    assert.match(messages[0].message, /Initialise/);
  }

  runtime.handleMessage({ type: "initialise", speedIndex: 99 });
  assert.equal(messages.at(-1)?.type, "error");

  runtime.handleMessage({ type: "unknown" } as unknown as MainToWorkerMessage);
  assert.equal(messages.at(-1)?.type, "error");

  runtime.dispose();
  runtime.dispose();
});

test("the worker emits state changes and transferable full-resolution batches", () => {
  const scheduler = new ManualScheduler();
  const messages: WorkerToMainMessage[] = [];
  const transfers: ArrayBuffer[][] = [];
  const runtime = createEmulatorWorkerRuntime({
    scheduler,
    postMessage: (message, transfer) => {
      messages.push(message);
      transfers.push(transfer === undefined ? [] : [...transfer]);
    },
  });

  runtime.handleMessage({
    type: "initialise",
    options: { seed: 919, controls: { main: { patchCurrent: 22 } } },
    historyCapacity: 20,
    speedIndex: 1,
    maxStepsPerSlice: 7,
  });
  const ready = messages[0];
  assert.equal(ready.type, "ready");
  if (ready.type === "ready") {
    assert.equal(ready.snapshot.historyCapacity, 20);
    assert.equal(ready.snapshot.controls.main.patchCurrent, 22);
  }

  runtime.handleMessage({ type: "start" });
  scheduler.advance(50);
  const batches = messages.filter((message) => message.type === "samples");
  assert.deepEqual(
    batches.map((message) => (message.type === "samples" ? message.count : 0)),
    [7, 7, 6],
  );

  const expected = new SpikelingModel({
    seed: 919,
    controls: { main: { patchCurrent: 22 } },
  }).run(20);
  const actual = batches.flatMap((message) =>
    message.type === "samples"
      ? unpackSamples(new Float64Array(message.buffer))
      : [],
  );
  assert.deepEqual(actual, expected);
  assert.equal(
    transfers.filter((transfer) => transfer.length === 1).length,
    3,
  );
  const last = batches.at(-1);
  assert.ok(last && last.type === "samples");
  assert.equal(last.firstTimeMs, 1.4000000000000001);
  assert.equal(last.lastTimeMs, 1.9000000000000001);

  runtime.dispose();
  assert.equal(scheduler.pending, 0);
});

test("worker control, speed, snapshot, pause, reset, stop and reinitialise work", () => {
  const scheduler = new ManualScheduler();
  const messages: WorkerToMainMessage[] = [];
  const runtime = createEmulatorWorkerRuntime({
    scheduler,
    postMessage: (message) => messages.push(message),
  });

  runtime.handleMessage({ type: "initialise", speedIndex: 0 });
  runtime.handleMessage({ type: "set-speed", index: 1 });
  runtime.handleMessage({ type: "update-controls", patch: { main: { patchCurrent: 31 } } });
  runtime.handleMessage({ type: "start" });
  scheduler.advance(50);
  runtime.handleMessage({ type: "snapshot" });
  const snapshot = messages.at(-1);
  assert.ok(snapshot && snapshot.type === "snapshot");
  assert.equal(snapshot.snapshot.stepIndex, 20);
  assert.equal(snapshot.snapshot.controls.main.patchCurrent, 31);

  runtime.handleMessage({ type: "pause" });
  const paused = messages.at(-1);
  assert.ok(paused && paused.type === "state");
  assert.equal(paused.snapshot.lifecycle, "paused");

  runtime.handleMessage({ type: "reset", options: { seed: 334 } });
  const reset = messages.at(-1);
  assert.ok(reset && reset.type === "state");
  assert.equal(reset.snapshot.stepIndex, 0);

  runtime.handleMessage({ type: "stop" });
  const stopped = messages.at(-1);
  assert.ok(stopped && stopped.type === "state");
  assert.equal(stopped.snapshot.lifecycle, "stopped");

  runtime.handleMessage({ type: "initialise", speedIndex: 3 });
  const ready = messages.at(-1);
  assert.ok(ready && ready.type === "ready");
  assert.equal(ready.snapshot.speed.index, 3);

  runtime.handleMessage({ type: "dispose" });
  runtime.handleMessage({ type: "snapshot" });
  assert.equal(messages.at(-1)?.type, "error");
});

test("EmulatorSource connects once and exposes batches through the DataSource seam", async () => {
  const worker = new InProcessWorker();
  const states: EngineSnapshot[] = [];
  const batches: SimulationSample[][] = [];
  const source = new EmulatorSource({
    workerFactory: () => worker,
    historyCapacity: 15,
    speedIndex: 1,
    maxStepsPerSlice: 8,
    simulation: { seed: 100, controls: { main: { noiseLevel: 4 } } },
  });

  assert.equal(source.kind, "emulator");
  assert.equal(source.getSnapshot(), undefined);
  assert.throws(() => source.start(), /Connect/);
  source.subscribeState((snapshot) => states.push(snapshot));
  source.subscribe((samples) => batches.push([...samples]));

  const first = source.connect();
  const second = source.connect();
  assert.equal(first, second);
  await first;
  assert.equal(source.getSnapshot()?.lifecycle, "idle");
  assert.equal(states.length, 1);

  source.start();
  worker.scheduler.advance(50);
  assert.deepEqual(batches.map((samples) => samples.length), [8, 8, 4]);
  assert.equal(source.history.length, 15);
  assert.equal(source.latest()[0].timeMs, 0.5);
  assert.equal(source.latest(2).length, 2);

  source.updateControls({ main: { patchCurrent: 45 } });
  source.setSpeed(0);
  source.requestSnapshot();
  assert.equal(source.getSnapshot()?.controls.main.patchCurrent, 45);
  assert.equal(source.getSnapshot()?.speed.index, 0);

  source.pause();
  assert.equal(source.getSnapshot()?.lifecycle, "paused");
  source.reset({ seed: 101 });
  assert.equal(source.getSnapshot()?.lifecycle, "idle");
  assert.equal(source.history.length, 0);
  source.start();
  worker.scheduler.advance(50);
  assert.equal(source.history.length, 10);
  source.stop();
  assert.equal(source.history.length, 0);
  assert.equal(source.getSnapshot()?.lifecycle, "stopped");

  await source.disconnect();
  assert.equal(worker.terminated, true);
  assert.equal(worker.listeners.size, 0);
  assert.equal(source.getSnapshot(), undefined);
  await source.disconnect();
});

test("source subscriptions can be removed and current state is replayed immediately", async () => {
  const worker = new InProcessWorker();
  const source = new EmulatorSource({ workerFactory: () => worker, speedIndex: 0 });
  await source.connect();

  let sampleNotifications = 0;
  let stateNotifications = 0;
  let errorNotifications = 0;
  const stopSamples = source.subscribe(() => {
    sampleNotifications += 1;
  });
  const stopStates = source.subscribeState(() => {
    stateNotifications += 1;
  });
  const stopErrors = source.subscribeErrors(() => {
    errorNotifications += 1;
  });
  assert.equal(stateNotifications, 1);

  stopSamples();
  stopStates();
  stopErrors();
  source.start();
  worker.scheduler.advance(50);
  worker.emit({ type: "error", message: "ignored listener" });
  assert.equal(sampleNotifications, 0);
  assert.equal(stateNotifications, 1);
  assert.equal(errorNotifications, 0);

  await source.disconnect();
});

test("source rejects malformed worker batch sizes and forwards worker errors", async () => {
  const worker = new InProcessWorker();
  const source = new EmulatorSource({ workerFactory: () => worker });
  const errors: Error[] = [];
  source.subscribeErrors((error) => errors.push(error));
  await source.connect();

  worker.emit({
    type: "samples",
    count: 2,
    firstTimeMs: 0,
    lastTimeMs: 0.1,
    buffer: new Float64Array(SAMPLE_WIDTH).buffer,
  });
  worker.emit({ type: "error", message: "explicit worker failure" });
  assert.equal(errors.length, 2);
  assert.match(errors[0].message, /malformed/);
  assert.equal(errors[1].message, "explicit worker failure");
  assert.equal(source.history.length, 0);

  await source.disconnect();
});

test("source connection rejects worker initialisation errors", async () => {
  const worker = new InProcessWorker();
  const source = new EmulatorSource({ workerFactory: () => worker, speedIndex: 99 });

  await assert.rejects(source.connect(), /between 0 and 9/);
  await source.disconnect();
});

test("the production browser-worker entry runs in a real isolated worker thread", async (context) => {
  const worker = new Worker(new URL("./helpers/node-worker.ts", import.meta.url));
  context.after(async () => {
    await worker.terminate();
  });

  const readyPromise = workerMessage(worker, (message) => message.type === "ready");
  worker.postMessage({
    type: "initialise",
    speedIndex: 0,
    options: { seed: 876, controls: { main: { patchCurrent: 19 } } },
  } satisfies MainToWorkerMessage);
  const ready = await readyPromise;
  assert.ok(ready.type === "ready");
  assert.equal(ready.snapshot.controls.main.patchCurrent, 19);

  const samplePromise = workerMessage(worker, (message) => message.type === "samples");
  worker.postMessage({ type: "start" } satisfies MainToWorkerMessage);
  const batch = await samplePromise;
  assert.ok(batch.type === "samples");
  assert.equal(batch.count, 10);
  assert.equal(batch.buffer.byteLength, 10 * SAMPLE_WIDTH * 8);

  const expected = new SpikelingModel({
    seed: 876,
    controls: { main: { patchCurrent: 19 } },
  }).run(10);
  assert.deepEqual(unpackSamples(new Float64Array(batch.buffer)), expected);

  const pausePromise = workerMessage(
    worker,
    (message) => message.type === "state" && message.snapshot.lifecycle === "paused",
  );
  worker.postMessage({ type: "pause" } satisfies MainToWorkerMessage);
  const paused = await pausePromise;
  assert.ok(paused.type === "state");
  assert.equal(paused.snapshot.stepIndex, 10);
});
