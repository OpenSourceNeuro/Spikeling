// SPDX-License-Identifier: GPL-3.0-or-later

import assert from "node:assert/strict";
import test from "node:test";

import {
  EmulatorSource,
  RECORDING_CHUNK_SAMPLES,
  RecordingBuffer,
  SimulationEngine,
  SpikelingModel,
  SpikelingRecorder,
  SpikelingRecordingControls,
  createEmulatorWorkerRuntime,
  parseRecordingCsv,
  serialiseRecordingCsv,
} from "../src/index.ts";
import type {
  ControlsPatch,
  DataSource,
  EmulatorSourceWorker,
  EngineSnapshot,
  ErrorListener,
  MainToWorkerMessage,
  RecordingDownload,
  RecordingSample,
  RecordingSnapshot,
  SampleListener,
  SimulationSample,
  StateListener,
  Unsubscribe,
  WorkerToMainMessage,
} from "../src/index.ts";
import { readDevelopmentAsset } from "../tools/serve.mjs";
import { FakeDocument, FakeElement } from "./helpers/fake-dom.ts";
import { ManualScheduler } from "./helpers/manual-scheduler.ts";

class RecordingSource implements DataSource {
  readonly kind = "emulator";
  readonly scheduler = new ManualScheduler();
  readonly sampleListeners = new Set<SampleListener>();
  readonly stateListeners = new Set<StateListener>();
  readonly errorListeners = new Set<ErrorListener>();
  readonly engine: SimulationEngine;
  connected: boolean;

  constructor(connected = true) {
    this.connected = connected;
    this.engine = new SimulationEngine({
      modelOptions: { seed: 1099, controls: { main: { patchCurrent: 17, noiseLevel: 6 } } },
      scheduler: this.scheduler,
      onSamples: (samples) => this.emitSamples(samples),
      onState: (snapshot) => this.emitState(snapshot),
    });
  }

  async connect(): Promise<void> { this.connected = true; this.emitState(this.engine.getSnapshot()); }
  async disconnect(): Promise<void> { this.connected = false; this.engine.dispose(); }
  start(): void { this.engine.start(); }
  pause(): void { this.engine.pause(); }
  stop(): void { this.engine.stop(); }
  reset(): void { this.engine.reset(); }
  setSpeed(index: number): void { this.engine.setSpeed(index); }
  updateControls(patch: ControlsPatch): void { this.engine.updateControls(patch); }
  requestSnapshot(): void { this.emitState(this.engine.getSnapshot()); }
  latest(count?: number): SimulationSample[] { return this.engine.history.latest(count); }

  subscribe(listener: SampleListener): Unsubscribe {
    this.sampleListeners.add(listener);
    return () => this.sampleListeners.delete(listener);
  }

  subscribeState(listener: StateListener): Unsubscribe {
    this.stateListeners.add(listener);
    if (this.connected) listener(this.engine.getSnapshot());
    return () => this.stateListeners.delete(listener);
  }

  subscribeErrors(listener: ErrorListener): Unsubscribe {
    this.errorListeners.add(listener);
    return () => this.errorListeners.delete(listener);
  }

  run(count: number): SimulationSample[] {
    const samples = this.engine.model.run(count);
    this.engine.history.pushBatch(samples);
    this.emitSamples(samples);
    return samples;
  }

  emitSamples(samples: readonly SimulationSample[]): void {
    for (const listener of this.sampleListeners) listener(samples);
  }

  emitError(error: Error): void {
    for (const listener of this.errorListeners) listener(error);
  }

  private emitState(snapshot: EngineSnapshot): void {
    for (const listener of this.stateListeners) listener(snapshot);
  }
}

class RecordingWorker implements EmulatorSourceWorker {
  readonly scheduler = new ManualScheduler();
  private readonly listeners = new Set<(event: { readonly data: WorkerToMainMessage }) => void>();
  private readonly runtime = createEmulatorWorkerRuntime({
    scheduler: this.scheduler,
    postMessage: (message, transfer) => {
      const cloned = structuredClone(message, { transfer: transfer === undefined ? [] : [...transfer] });
      for (const listener of this.listeners) listener({ data: cloned });
    },
  });

  postMessage(message: MainToWorkerMessage): void { this.runtime.handleMessage(message); }
  addEventListener(_type: "message", listener: (event: { readonly data: WorkerToMainMessage }) => void): void {
    this.listeners.add(listener);
  }
  removeEventListener(_type: "message", listener: (event: { readonly data: WorkerToMainMessage }) => void): void {
    this.listeners.delete(listener);
  }
  terminate(): Promise<number> { this.runtime.dispose(); return Promise.resolve(0); }
}

function recorded(sample: SimulationSample, timeMs = sample.timeMs): RecordingSample {
  return {
    timeMs,
    mainVm: sample.mainVm,
    stimulus: sample.stimulus,
    totalCurrent: sample.totalCurrent,
    synapse1Vm: sample.synapse1Vm,
    synapse1Current: sample.synapse1Current,
    synapse2Vm: sample.synapse2Vm,
    synapse2Current: sample.synapse2Current,
    trigger: sample.trigger,
  };
}

function mount(options: { maxSamples?: number; connected?: boolean } = {}): {
  source: RecordingSource;
  recorder: SpikelingRecorder;
  panel: SpikelingRecordingControls;
  host: FakeElement;
  downloads: RecordingDownload[];
} {
  const source = new RecordingSource(options.connected);
  const recorder = new SpikelingRecorder(source, { maxSamples: options.maxSamples ?? 128, chunkSamples: 8 });
  const owner = new FakeDocument();
  const host = owner.createHost();
  const downloads: RecordingDownload[] = [];
  const panel = new SpikelingRecordingControls(host as unknown as HTMLElement, recorder, {
    now: () => new Date("2026-08-23T12:34:56.789Z"),
    download: (download) => downloads.push(download),
  });
  return { source, recorder, panel, host, downloads };
}

function action(host: FakeElement, name: string): FakeElement {
  const found = host.findAll((element) => element.dataset.action === name)[0];
  assert.ok(found);
  return found;
}

function classElement(host: FakeElement, name: string): FakeElement {
  const found = host.findAll((element) => element.className.split(" ").includes(name))[0];
  assert.ok(found);
  return found;
}

test("recording chunks allocate lazily, remain bounded and never overwrite", () => {
  const first = recorded(new SpikelingModel().step());
  const buffer = new RecordingBuffer(5, 2);
  assert.equal(RECORDING_CHUNK_SAMPLES, 1_024);
  assert.equal(buffer.length, 0);
  assert.equal(buffer.allocatedBytes, 0);
  assert.equal(buffer.maximumBytes, 5 * 9 * 8);
  for (let index = 0; index < 5; index += 1) {
    assert.equal(buffer.push({ ...first, timeMs: index * 0.1 }), true);
  }
  assert.equal(buffer.allocatedBytes, buffer.maximumBytes);
  assert.equal(buffer.push(first), false);
  assert.equal(buffer.at(0)?.timeMs, 0);
  assert.equal(buffer.at(-1)?.timeMs, 0.4);
  assert.equal(buffer.at(5), undefined);
  assert.equal(buffer.at(-6), undefined);
  assert.equal(buffer.samples().length, 5);
  assert.throws(() => buffer.at(1.5), /integer/);
  buffer.clear();
  assert.equal(buffer.length, 0);
  assert.equal(buffer.allocatedBytes, 0);
});

test("recording buffers reject invalid capacity, chunk size, finite values and triggers", () => {
  const first = recorded(new SpikelingModel().step());
  assert.throws(() => new RecordingBuffer(0), /positive safe integer/);
  assert.throws(() => new RecordingBuffer(10, 0), /positive safe integer/);
  const buffer = new RecordingBuffer(2);
  assert.throws(() => buffer.push({ ...first, mainVm: Infinity }), /finite/);
  assert.throws(() => buffer.push({ ...first, trigger: 2 as 0 | 1 }), /zero or one/);
  assert.equal(buffer.allocatedBytes, 0);
});

test("recorder exposes truthful timestep, scientific rate and wall-clock throughput", () => {
  const source = new RecordingSource();
  const recorder = new SpikelingRecorder(source, { maxSamples: 25 });
  const snapshot = recorder.getSnapshot();
  assert.equal(snapshot.lifecycle, "idle");
  assert.equal(snapshot.sampleIntervalMs, 0.1);
  assert.equal(snapshot.scientificSampleRateHz, 10_000);
  assert.equal(snapshot.recordingSampleRateHz, 10_000);
  assert.equal(snapshot.wallClockStepsPerSecond, 1_000);
  assert.equal(snapshot.maximumBytes, 25 * 9 * 8);
  source.setSpeed(5);
  assert.equal(recorder.getSnapshot().wallClockStepsPerSecond, 10_000);
  recorder.dispose();
});

test("unconnected sources report unknown wall-clock speed until their first snapshot", async () => {
  const source = new RecordingSource(false);
  const recorder = new SpikelingRecorder(source);
  assert.equal(recorder.getSnapshot().wallClockStepsPerSecond, undefined);
  await source.connect();
  assert.equal(recorder.getSnapshot().wallClockStepsPerSecond, 1_000);
  recorder.dispose();
});

test("start captures every source sample at original Float64 precision", () => {
  const source = new RecordingSource();
  const recorder = new SpikelingRecorder(source, { maxSamples: 100 });
  source.run(5);
  recorder.start();
  const scientific = source.run(35);
  assert.deepEqual(recorder.samples(), scientific.map((sample, index) => recorded(sample, index * 0.1)));
  assert.equal(recorder.getSnapshot().durationMs, 3.5);
  recorder.stop();
  assert.deepEqual(parseRecordingCsv(recorder.exportCsv()).samples, recorder.samples());
  recorder.dispose();
});

test("recording begins at desktop-local zero even after simulation time has advanced", () => {
  const source = new RecordingSource();
  source.run(20);
  const recorder = new SpikelingRecorder(source, { maxSamples: 10 });
  recorder.start();
  source.run(3);
  assert.deepEqual(recorder.samples().map((sample) => sample.timeMs), [0, 0.1, 0.2]);
});

test("recording automatically stops at capacity without dropping initial samples", () => {
  const source = new RecordingSource();
  const recorder = new SpikelingRecorder(source, { maxSamples: 4, chunkSamples: 3 });
  recorder.start();
  const samples = source.run(10);
  assert.equal(recorder.getSnapshot().lifecycle, "full");
  assert.deepEqual(recorder.samples(), samples.slice(0, 4).map((sample, index) => recorded(sample, index * 0.1)));
  assert.equal(recorder.getSnapshot().allocatedBytes, 4 * 9 * 8);
  assert.equal(parseRecordingCsv(recorder.exportCsv()).samples.length, 4);
  source.run(5);
  assert.equal(recorder.samples().length, 4);
});

test("pause retains the armed recorder and resume preserves scientific continuity", () => {
  const source = new RecordingSource();
  const recorder = new SpikelingRecorder(source, { maxSamples: 200 });
  recorder.start();
  source.start();
  source.scheduler.advance(50);
  source.pause();
  assert.equal(recorder.getSnapshot().lifecycle, "recording");
  assert.equal(recorder.getSnapshot().simulationLifecycle, "paused");
  source.scheduler.advance(100);
  assert.equal(recorder.getSnapshot().sampleCount, 50);
  source.start();
  source.scheduler.advance(50);
  assert.equal(recorder.getSnapshot().sampleCount, 100);
  assert.equal(recorder.samples().at(-1)?.timeMs, 9.9);
});

test("simulation stop and reset preserve captured recordings and prevent mixed timelines", () => {
  for (const transport of ["stop", "reset"] as const) {
    const source = new RecordingSource();
    const recorder = new SpikelingRecorder(source, { maxSamples: 100 });
    recorder.start();
    source.start();
    source.scheduler.advance(50);
    source[transport]();
    assert.equal(recorder.getSnapshot().lifecycle, "stopped");
    assert.equal(recorder.getSnapshot().sampleCount, 50);
    source.run(5);
    assert.equal(recorder.getSnapshot().sampleCount, 50);
  }
});

test("discontinuous source timestamps stop capture instead of inventing missing samples", () => {
  const source = new RecordingSource();
  const recorder = new SpikelingRecorder(source, { maxSamples: 20 });
  recorder.start();
  const first = source.run(2);
  source.emitSamples([{ ...first[1], timeMs: 0.9 }]);
  assert.equal(recorder.getSnapshot().lifecycle, "stopped");
  assert.equal(recorder.getSnapshot().sampleCount, 2);
  assert.match(recorder.getSnapshot().error ?? "", /discontinuous/);
});

test("source failures stop recording while retaining all captured scientific values", () => {
  const source = new RecordingSource();
  const recorder = new SpikelingRecorder(source, { maxSamples: 10 });
  recorder.start();
  source.run(3);
  source.emitError(new Error("Worker connection failed"));
  assert.equal(recorder.getSnapshot().lifecycle, "stopped");
  assert.equal(recorder.getSnapshot().error, "Worker connection failed");
  assert.equal(recorder.samples().length, 3);
});

test("restarting recording clears earlier sessions and duplicate transport calls are safe", () => {
  const source = new RecordingSource();
  const recorder = new SpikelingRecorder(source, { maxSamples: 10 });
  recorder.stop();
  recorder.start();
  source.run(3);
  recorder.start();
  assert.equal(recorder.samples().length, 3);
  recorder.stop();
  recorder.stop();
  recorder.start();
  assert.equal(recorder.samples().length, 0);
  source.run(2);
  assert.equal(recorder.samples()[0].timeMs, 0);
});

test("clear releases allocated memory and resets origin, filename and error state", () => {
  const source = new RecordingSource();
  const recorder = new SpikelingRecorder(source, { maxSamples: 10 });
  recorder.start();
  source.run(3);
  source.emitError(new Error("old failure"));
  recorder.clear();
  assert.equal(recorder.getSnapshot().lifecycle, "idle");
  assert.equal(recorder.getSnapshot().allocatedBytes, 0);
  assert.equal(recorder.getSnapshot().error, undefined);
  assert.equal(recorder.getSnapshot().origin, "live");
});

test("recording subscriptions receive immediate and batched lifecycle snapshots", () => {
  const source = new RecordingSource();
  const recorder = new SpikelingRecorder(source, { maxSamples: 10 });
  const snapshots: RecordingSnapshot[] = [];
  const unsubscribe = recorder.subscribe((snapshot) => snapshots.push(snapshot));
  recorder.start();
  source.emitSamples([]);
  source.run(3);
  recorder.stop();
  assert.deepEqual(snapshots.map((snapshot) => snapshot.lifecycle), ["idle", "recording", "recording", "stopped"]);
  unsubscribe();
  recorder.clear();
  assert.equal(snapshots.length, 4);
});

test("export and import cannot replace a currently running scientific recording", async () => {
  const source = new RecordingSource();
  const recorder = new SpikelingRecorder(source, { maxSamples: 10 });
  recorder.start();
  const sample = recorded(source.run(1)[0]);
  const content = serialiseRecordingCsv([sample]);
  assert.throws(() => recorder.exportCsv(), /Stop recording/);
  assert.throws(() => recorder.importCsv(content), /Stop recording/);
  await assert.rejects(recorder.importFile({ name: "x.csv", size: content.length, text: async () => content }), /Stop recording/);
});

test("desktop-compatible CSV imports replace recording only after complete validation", () => {
  const source = new RecordingSource();
  const recorder = new SpikelingRecorder(source, { maxSamples: 10 });
  recorder.start();
  const previous = source.run(2);
  recorder.stop();
  assert.throws(() => recorder.importCsv("bad"), /nine exact/);
  assert.deepEqual(recorder.samples(), previous.map((sample, index) => recorded(sample, index * 0.1)));
  const model = new SpikelingModel({ seed: 900 });
  const imported = model.run(3).map((sample) => recorded(sample));
  recorder.importCsv(serialiseRecordingCsv(imported), "old-desktop.csv");
  assert.deepEqual(recorder.samples(), imported);
  assert.equal(recorder.getSnapshot().origin, "imported");
  assert.equal(recorder.getSnapshot().filename, "old-desktop.csv");
  assert.equal(recorder.getSnapshot().lifecycle, "stopped");
});

test("async file import rejects races where recording begins during local file reading", async () => {
  const source = new RecordingSource();
  const recorder = new SpikelingRecorder(source, { maxSamples: 10 });
  const content = serialiseRecordingCsv([recorded(new SpikelingModel().step())]);
  const promise = recorder.importFile({
    name: "desktop.csv",
    size: content.length,
    text: async () => { recorder.start(); return content; },
  });
  await assert.rejects(promise, /Stop recording/);
  assert.equal(recorder.getSnapshot().lifecycle, "recording");
});

test("disposing the recorder unsubscribes, frees memory and rejects later operations", () => {
  const source = new RecordingSource();
  const recorder = new SpikelingRecorder(source, { maxSamples: 10 });
  recorder.start();
  source.run(2);
  recorder.dispose();
  recorder.dispose();
  assert.equal(source.sampleListeners.size, 0);
  assert.equal(source.stateListeners.size, 0);
  assert.equal(source.errorListeners.size, 0);
  assert.equal(recorder.getSnapshot().allocatedBytes, 0);
  assert.throws(() => recorder.start(), /disposed/);
  assert.throws(() => recorder.stop(), /disposed/);
  assert.throws(() => recorder.clear(), /disposed/);
  assert.throws(() => recorder.subscribe(() => {}), /disposed/);
});

test("real worker-backed transferable batches record every sample regardless of display history", async () => {
  const worker = new RecordingWorker();
  const source = new EmulatorSource({
    workerFactory: () => worker,
    historyCapacity: 7,
    speedIndex: 1,
    maxStepsPerSlice: 6,
    simulation: { seed: 3030, controls: { main: { patchCurrent: 22, noiseLevel: 9 } } },
  });
  const recorder = new SpikelingRecorder(source, { maxSamples: 100, chunkSamples: 5 });
  await source.connect();
  recorder.start();
  source.start();
  worker.scheduler.advance(100);
  recorder.stop();
  const expected = new SpikelingModel({ seed: 3030, controls: { main: { patchCurrent: 22, noiseLevel: 9 } } }).run(40);
  assert.equal(source.latest().length, 7);
  assert.deepEqual(recorder.samples(), expected.map((sample) => recorded(sample)));
  assert.deepEqual(parseRecordingCsv(recorder.exportCsv()).samples, recorder.samples());
  recorder.dispose();
  await source.disconnect();
});

test("recording controls expose keyboard-native transport, local input and honest rates", () => {
  const { host, recorder } = mount({ connected: false });
  assert.equal(action(host, "start").disabled, false);
  assert.equal(action(host, "stop").disabled, true);
  assert.equal(action(host, "download").disabled, true);
  assert.equal(action(host, "clear").disabled, true);
  assert.equal(classElement(host, "spk-recording__file").accept, ".csv,text/csv");
  assert.match(classElement(host, "spk-recording__status").textContent, /no files are uploaded/);
  assert.match(classElement(host, "spk-recording__rates").textContent, /10,000 samples\/s of simulation time/);
  assert.match(classElement(host, "spk-recording__rates").textContent, /waiting for simulation/);
  recorder.dispose();
});

test("transport buttons start, stop, clear and reflect bounded sample progress", () => {
  const { host, source, recorder } = mount();
  action(host, "start").dispatch("click");
  assert.equal(action(host, "start").disabled, true);
  assert.equal(action(host, "stop").disabled, false);
  source.run(5);
  assert.match(classElement(host, "spk-recording__statistics").textContent, /5 \/ 128 samples/);
  action(host, "stop").dispatch("click");
  assert.equal(action(host, "download").disabled, false);
  assert.match(classElement(host, "spk-recording__status").textContent, /stopped/);
  action(host, "clear").dispatch("click");
  assert.equal(recorder.getSnapshot().lifecycle, "idle");
});

test("recording controls explain capacity auto-stop and preserve available download", () => {
  const { host, source } = mount({ maxSamples: 2 });
  action(host, "start").dispatch("click");
  source.run(5);
  assert.match(classElement(host, "spk-recording__status").textContent, /capacity reached without overwriting/);
  assert.equal(action(host, "download").disabled, false);
  assert.equal(action(host, "stop").disabled, true);
});

test("paused simulation is clearly distinguished from stopped scientific recording", () => {
  const { host, source } = mount();
  source.start();
  action(host, "start").dispatch("click");
  source.scheduler.advance(50);
  source.pause();
  assert.match(classElement(host, "spk-recording__status").textContent, /simulation paused/);
});

test("CSV download uses a safe deterministic filename and remains entirely local", () => {
  const { host, source, downloads } = mount();
  action(host, "start").dispatch("click");
  source.run(3);
  action(host, "stop").dispatch("click");
  action(host, "download").dispatch("click");
  assert.equal(downloads.length, 1);
  assert.equal(downloads[0].filename, "spikeling-recording-2026-08-23T12-34-56-789Z.csv");
  assert.equal(downloads[0].mimeType, "text/csv;charset=utf-8");
  assert.equal(parseRecordingCsv(downloads[0].content).samples.length, 3);
});

test("default browser downloading creates, clicks and revokes an exclusively local Blob URL", async () => {
  class BrowserDocument extends FakeDocument {
    anchor: (FakeElement & { href: string; download: string; click(): void }) | undefined;
    clicks = 0;

    override createElement(tag: string): FakeElement {
      const node = super.createElement(tag);
      if (tag === "a") {
        const anchor = node as FakeElement & { href: string; download: string; click(): void };
        anchor.click = () => { this.clicks += 1; };
        this.anchor = anchor;
      }
      return node;
    }
  }

  const owner = new BrowserDocument();
  const source = new RecordingSource();
  const recorder = new SpikelingRecorder(source, { maxSamples: 10 });
  const panel = new SpikelingRecordingControls(owner.createHost() as unknown as HTMLElement, recorder);
  recorder.start();
  source.run(1);
  recorder.stop();

  const originalCreate = URL.createObjectURL;
  const originalRevoke = URL.revokeObjectURL;
  const revoked: string[] = [];
  let downloadedBlob: Blob | undefined;
  URL.createObjectURL = (blob) => { downloadedBlob = blob; return "blob:local-spikeling-recording"; };
  URL.revokeObjectURL = (url) => { revoked.push(url); };
  try {
    const download = panel.download();
    assert.match(download.filename, /^spikeling-recording-.*\.csv$/);
    assert.equal(owner.clicks, 1);
    assert.equal(owner.anchor?.href, "blob:local-spikeling-recording");
    assert.equal(owner.anchor?.download, download.filename);
    assert.ok(downloadedBlob instanceof Blob);
    assert.match(await downloadedBlob.text(), /^Time \(ms\),/);
    await new Promise<void>((resolve) => setTimeout(resolve, 0));
    assert.deepEqual(revoked, ["blob:local-spikeling-recording"]);
  } finally {
    URL.createObjectURL = originalCreate;
    URL.revokeObjectURL = originalRevoke;
    panel.dispose();
    recorder.dispose();
  }
});

test("imported recordings surface the local filename and become immediately exportable", async () => {
  const { host, panel, recorder } = mount();
  const content = serialiseRecordingCsv([recorded(new SpikelingModel().step())]);
  await panel.importFile({ name: "desktop-export.csv", size: content.length, text: async () => content });
  assert.match(classElement(host, "spk-recording__status").textContent, /desktop-export\.csv/);
  assert.equal(action(host, "download").disabled, false);
  assert.equal(recorder.getSnapshot().origin, "imported");
});

test("imported content without a filename remains clearly identified as desktop-compatible", () => {
  const { host, recorder } = mount();
  recorder.importCsv(serialiseRecordingCsv([recorded(new SpikelingModel().step())]));
  assert.match(classElement(host, "spk-recording__status").textContent, /desktop-compatible recording/);
});

test("invalid imports and recorder errors are exposed through an accessible alert", async () => {
  const { host, panel, source } = mount();
  await panel.importFile({ name: "notes.txt", size: 1, text: async () => "x" });
  assert.match(classElement(host, "spk-recording__error").textContent, /\.csv/);
  source.emitError(new Error("Lost worker connection"));
  assert.equal(classElement(host, "spk-recording__error").textContent, "Lost worker connection");
});

test("synchronous transport failures and unknown thrown values become accessible errors", () => {
  const first = mount();
  first.recorder.dispose();
  action(first.host, "start").dispatch("click");
  assert.match(classElement(first.host, "spk-recording__error").textContent, /disposed/);

  const source = new RecordingSource();
  const recorder = new SpikelingRecorder(source, { maxSamples: 5 });
  const owner = new FakeDocument();
  const host = owner.createHost();
  new SpikelingRecordingControls(host as unknown as HTMLElement, recorder, {
    download: () => { throw "unexpected local failure"; },
  });
  recorder.start();
  source.run(1);
  recorder.stop();
  action(host, "download").dispatch("click");
  assert.equal(classElement(host, "spk-recording__error").textContent, "Unable to process the scientific recording.");
});

test("file-picker change imports local File.text content without a network request", async () => {
  const { host, recorder } = mount();
  const content = serialiseRecordingCsv([recorded(new SpikelingModel().step())]);
  const picker = classElement(host, "spk-recording__file");
  picker.files = [{ name: "picked.csv", size: content.length, text: async () => content }];
  picker.dispatch("change");
  await new Promise<void>((resolve) => setTimeout(resolve, 0));
  assert.equal(recorder.getSnapshot().filename, "picked.csv");
  picker.files = [];
  picker.dispatch("change");
});

test("recording controls cleanly dispose without owning or destroying the shared recorder", () => {
  const { host, panel, recorder, source } = mount();
  panel.dispose();
  panel.dispose();
  assert.equal(host.children.length, 0);
  recorder.start();
  source.run(2);
  assert.equal(recorder.samples().length, 2);
});

test("local Phase 6 preview serves scoped recording styles, native modules and no upload paths", async () => {
  const page = await readDevelopmentAsset("/");
  const stylesheet = await readDevelopmentAsset("/src/styles/recording.css");
  const module = await readDevelopmentAsset("/src/recording/recording-controls.ts");
  assert.match(page.content, /Local Phase 6 preview/);
  assert.match(page.content, /id="recording"/);
  assert.match(page.content, /src\/styles\/recording\.css/);
  assert.match(stylesheet.content, /\.spk-recording__progress/);
  assert.match(module.content, /class SpikelingRecordingControls/);
  assert.doesNotMatch(module.content, /\bfetch\s*\(|XMLHttpRequest|sendBeacon/);
});
