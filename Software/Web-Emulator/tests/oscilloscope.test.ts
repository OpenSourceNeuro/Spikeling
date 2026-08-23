// SPDX-License-Identifier: GPL-3.0-or-later

import assert from "node:assert/strict";
import test from "node:test";

import {
  EmulatorSource,
  SampleRingBuffer,
  SimulationEngine,
  SpikelingModel,
  SpikelingOscilloscope,
  createEmulatorWorkerRuntime,
} from "../src/index.ts";
import type {
  ControlsPatch,
  DataSource,
  EmulatorSourceWorker,
  EngineSnapshot,
  ErrorListener,
  MainToWorkerMessage,
  SampleListener,
  SimulationLifecycle,
  SimulationSample,
  StateListener,
  Unsubscribe,
  WorkerToMainMessage,
} from "../src/index.ts";
import { FakeCanvasElement, FakeDocument, FakeElement } from "./helpers/fake-dom.ts";
import { ManualAnimationFrames } from "./helpers/fake-canvas.ts";
import { ManualScheduler } from "./helpers/manual-scheduler.ts";

class StubDataSource implements DataSource {
  readonly kind = "emulator";
  readonly history = new SampleRingBuffer(6_000);
  readonly sampleListeners = new Set<SampleListener>();
  readonly stateListeners = new Set<StateListener>();
  readonly errorListeners = new Set<ErrorListener>();
  private readonly initialSnapshot = new SimulationEngine({ historyCapacity: 6_000 }).getSnapshot();

  async connect(): Promise<void> {}
  async disconnect(): Promise<void> {}
  start(): void {}
  pause(): void {}
  stop(): void {}
  reset(): void {}
  setSpeed(_index: number): void {}
  updateControls(_patch: ControlsPatch): void {}
  requestSnapshot(): void {}

  subscribe(listener: SampleListener): Unsubscribe {
    this.sampleListeners.add(listener);
    return () => this.sampleListeners.delete(listener);
  }

  subscribeState(listener: StateListener): Unsubscribe {
    this.stateListeners.add(listener);
    return () => this.stateListeners.delete(listener);
  }

  subscribeErrors(listener: ErrorListener): Unsubscribe {
    this.errorListeners.add(listener);
    return () => this.errorListeners.delete(listener);
  }

  latest(count?: number): SimulationSample[] {
    return this.history.latest(count);
  }

  emitSamples(samples: readonly SimulationSample[]): void {
    this.history.pushBatch(samples);
    for (const listener of this.sampleListeners) {
      listener(samples);
    }
  }

  emitState(lifecycle: SimulationLifecycle, stepIndex = this.history.totalWritten): void {
    if (stepIndex === 0 && lifecycle !== "running") {
      this.history.clear();
    }

    const snapshot: EngineSnapshot = {
      ...this.initialSnapshot,
      lifecycle,
      stepIndex,
      retainedSamples: this.history.length,
    };
    for (const listener of this.stateListeners) {
      listener(snapshot);
    }
  }
}

function mount(source: DataSource, options: Record<string, unknown> = {}): {
  document: FakeDocument;
  host: FakeElement;
  frames: ManualAnimationFrames;
  instrument: SpikelingOscilloscope;
  canvas: FakeCanvasElement;
} {
  const document = new FakeDocument();
  const host = document.createHost();
  const frames = new ManualAnimationFrames();
  const instrument = new SpikelingOscilloscope(
    host as unknown as HTMLElement,
    source,
    { frameScheduler: frames, ...options },
  );
  return { document, host, frames, instrument, canvas: document.canvases[0] };
}

test("instrument mounts a semantic, accessible oscilloscope with seven native trace checkboxes", () => {
  const source = new StubDataSource();
  const { document, host, instrument, canvas } = mount(source);

  assert.equal(host.children.length, 1);
  assert.equal(instrument.element.className, "spk-oscilloscope");
  assert.equal(host.children[0].attributes.get("aria-label"), "Spikeling neuronal oscilloscope");
  assert.equal(canvas.attributes.get("role"), "img");
  assert.match(canvas.attributes.get("aria-label") ?? "", /membrane potential/);

  const checkboxes = host.findAll((element) => element.tagName === "input");
  assert.equal(checkboxes.length, 7);
  assert.ok(checkboxes.every((input) => input.type === "checkbox"));
  assert.ok(checkboxes.every((input) => input.attributes.has("aria-label")));
  assert.deepEqual(checkboxes.slice(0, 3).map((input) => input.checked), [true, true, true]);
  assert.deepEqual(checkboxes.slice(3).map((input) => input.checked), [false, false, false, false]);

  const statuses = host.findAll((element) => element.attributes.get("role") === "status");
  assert.equal(statuses.length, 1);
  assert.equal(statuses[0].attributes.get("aria-live"), "polite");
  assert.equal(statuses[0].textContent, "Ready");
  assert.equal(document.visibilityListeners.size, 1);
});

test("worker batches are painted only on independent coalesced animation frames", () => {
  const source = new StubDataSource();
  const { host, frames, instrument } = mount(source);
  const model = new SpikelingModel({ controls: { main: { patchCurrent: 18 } } });

  source.emitState("running", 0);
  source.emitSamples(model.run(40));
  source.emitSamples(model.run(60));
  assert.equal(frames.pending, 1);
  assert.equal(instrument.getStatistics()?.sourceSamples, 0);
  frames.advance(16.6);
  assert.equal(instrument.getStatistics()?.sourceSamples, 100);
  assert.equal(instrument.getStatistics()?.enabledTraces, 3);

  const reading = host.findAll((element) => element.className === "spk-oscilloscope__readings")[0];
  assert.match(reading.textContent, /Running · Vm .* mV · Input 18\.0 a\.u\./);
  assert.equal(frames.pending, 0);
});

test("trace visibility is keyboard-native and updates without altering source samples", () => {
  const source = new StubDataSource();
  const { host, instrument } = mount(source);
  const samples = new SpikelingModel().run(10);
  source.emitSamples(samples);

  instrument.setTraceVisible("synapse1Current", true);
  assert.equal(instrument.isTraceVisible("synapse1Current"), true);
  assert.equal(instrument.getStatistics()?.enabledTraces, 4);
  assert.deepEqual(source.latest(), samples);

  const inputs = host.findAll((element) => element.tagName === "input");
  inputs[0].checked = false;
  inputs[0].dispatch("change");
  assert.equal(instrument.isTraceVisible("mainVm"), false);
  assert.equal(instrument.getStatistics()?.enabledTraces, 3);
  assert.deepEqual(source.latest(), samples);
});

test("pause retains the final frame, stop clears readings, and restart resumes cleanly", () => {
  const source = new StubDataSource();
  const { host, frames, instrument } = mount(source);
  const samples = new SpikelingModel({ controls: { main: { patchCurrent: 15 } } }).run(25);
  source.emitState("running");
  source.emitSamples(samples);
  frames.advance();

  source.emitState("paused", samples.length);
  assert.equal(instrument.renderLoop.running, false);
  assert.equal(instrument.getStatistics()?.sourceSamples, 25);
  assert.equal(frames.pending, 0);
  const status = host.findAll((element) => element.className === "spk-oscilloscope__status")[0];
  assert.equal(status.textContent, "Paused");
  assert.equal(status.dataset.state, "paused");

  source.emitState("stopped", 0);
  assert.equal(instrument.getStatistics()?.sourceSamples, 0);
  const readings = host.findAll((element) => element.className === "spk-oscilloscope__readings")[0];
  assert.match(readings.textContent, /Stopped · Vm — mV/);

  source.emitState("running", 0);
  assert.equal(instrument.renderLoop.running, true);
  assert.equal(frames.pending, 1);
});

test("resize observer recalculates high-DPI geometry and avoids work after disposal", () => {
  const source = new StubDataSource();
  let resize: (() => void) | undefined;
  let observed: Element | undefined;
  let disconnected = false;
  const { host, document, instrument, canvas } = mount(source, {
    devicePixelRatio: () => 2,
    resizeObserverFactory: (callback: () => void) => {
      resize = callback;
      return {
        observe(element: Element): void {
          observed = element;
        },
        disconnect(): void {
          disconnected = true;
        },
      };
    },
  });

  assert.equal(observed, canvas);
  assert.equal(canvas.width, 1_600);
  canvas.cssWidth = 375;
  canvas.cssHeight = 280;
  resize?.();
  assert.equal(canvas.width, 750);
  assert.equal(canvas.height, 560);
  assert.equal(instrument.renderer.getLayout().compact, true);

  instrument.dispose();
  instrument.dispose();
  assert.equal(disconnected, true);
  assert.equal(host.children.length, 0);
  assert.equal(source.sampleListeners.size, 0);
  assert.equal(source.stateListeners.size, 0);
  assert.equal(document.visibilityListeners.size, 0);
  canvas.cssWidth = 900;
  resize?.();
  assert.equal(canvas.width, 750);
});

test("document visibility suspends oscilloscope paints without discarding worker samples", () => {
  const source = new StubDataSource();
  const { document, frames, instrument } = mount(source);
  source.emitState("running");
  document.setHidden(true);
  assert.equal(frames.pending, 0);

  source.emitSamples(new SpikelingModel().run(12));
  assert.equal(source.history.length, 12);
  assert.equal(frames.pending, 0);

  document.setHidden(false);
  assert.equal(frames.pending, 1);
  frames.advance();
  assert.equal(instrument.getStatistics()?.sourceSamples, 12);
});

test("oscilloscope reads at most one desktop-sized visible history window", () => {
  const source = new StubDataSource();
  const { frames, instrument } = mount(source);
  source.emitState("running");
  source.emitSamples(new SpikelingModel().run(6_000));
  frames.advance();

  assert.equal(source.history.length, 6_000);
  assert.equal(instrument.getStatistics()?.sourceSamples, 5_001);
  assert.equal(source.history.totalWritten, 6_000);
});

test("real EmulatorSource batches feed the oscilloscope without simulator coupling", async () => {
  const simulationScheduler = new ManualScheduler();
  const listeners = new Set<(event: { readonly data: WorkerToMainMessage }) => void>();
  const runtime = createEmulatorWorkerRuntime({
    scheduler: simulationScheduler,
    postMessage: (message, transfer) => {
      const cloned = structuredClone(message, { transfer: transfer ? [...transfer] : [] });
      for (const listener of listeners) {
        listener({ data: cloned });
      }
    },
  });
  const worker: EmulatorSourceWorker = {
    postMessage(message: MainToWorkerMessage): void {
      runtime.handleMessage(message);
    },
    addEventListener(_type, listener): void {
      listeners.add(listener);
    },
    removeEventListener(_type, listener): void {
      listeners.delete(listener);
    },
    terminate(): void {
      runtime.dispose();
    },
  };
  const source = new EmulatorSource({
    workerFactory: () => worker,
    speedIndex: 1,
    simulation: { controls: { main: { patchCurrent: 22 } } },
  });
  const { frames, instrument } = mount(source);
  await source.connect();
  source.start();
  simulationScheduler.advance(50);

  assert.equal(source.history.length, 25);
  assert.equal(frames.pending, 1);
  frames.advance();
  assert.equal(instrument.getStatistics()?.sourceSamples, 25);
  assert.equal(source.latest(1)[0].totalCurrent, 22);

  instrument.dispose();
  await source.disconnect();
});
