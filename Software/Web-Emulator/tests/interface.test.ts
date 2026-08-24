// SPDX-License-Identifier: GPL-3.0-or-later

import assert from "node:assert/strict";
import test from "node:test";

import {
  EmulatorSource,
  MOBILE_MEDIA_QUERY,
  REDUCED_MOTION_MEDIA_QUERY,
  SimulationEngine,
  SpikelingEmulator,
  SpikelingModel,
  TABLET_MEDIA_QUERY,
  createEmulatorWorkerRuntime,
  parseRecordingCsv,
} from "../src/index.ts";
import type {
  ControlsPatch,
  DataSource,
  EmulatorInterfaceOptions,
  EmulatorPanel,
  EmulatorSourceWorker,
  EngineSnapshot,
  ErrorListener,
  MainToWorkerMessage,
  MediaQueryAdapter,
  RecordingDownload,
  SampleListener,
  SimulationSample,
  StateListener,
  Unsubscribe,
  WorkerToMainMessage,
} from "../src/index.ts";
import { readDevelopmentAsset } from "../tools/serve.mjs";
import { ManualAnimationFrames } from "./helpers/fake-canvas.ts";
import { FakeDocument, FakeElement } from "./helpers/fake-dom.ts";
import { ManualScheduler } from "./helpers/manual-scheduler.ts";

class ControlledSource implements DataSource {
  readonly kind = "emulator";
  readonly scheduler = new ManualScheduler();
  readonly sampleListeners = new Set<SampleListener>();
  readonly stateListeners = new Set<StateListener>();
  readonly errorListeners = new Set<ErrorListener>();
  readonly engine: SimulationEngine;
  connected: boolean;
  failure: unknown;

  constructor(connected = true) {
    this.connected = connected;
    this.engine = new SimulationEngine({
      modelOptions: { seed: 7272, controls: { main: { patchCurrent: 15 } } },
      scheduler: this.scheduler,
      onSamples: (samples) => {
        for (const listener of this.sampleListeners) listener(samples);
      },
      onState: (snapshot) => {
        for (const listener of this.stateListeners) listener(snapshot);
      },
    });
  }

  async connect(): Promise<void> {
    this.connected = true;
    for (const listener of this.stateListeners) listener(this.engine.getSnapshot());
  }

  async disconnect(): Promise<void> { this.connected = false; this.engine.dispose(); }
  start(): void { if (this.failure !== undefined) throw this.failure; this.engine.start(); }
  pause(): void { this.engine.pause(); }
  stop(): void { this.engine.stop(); }
  reset(): void { this.engine.reset(); }
  setSpeed(index: number): void { this.engine.setSpeed(index); }
  updateControls(patch: ControlsPatch): void { this.engine.updateControls(patch); }
  requestSnapshot(): void { for (const listener of this.stateListeners) listener(this.engine.getSnapshot()); }
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

  emitError(error: Error): void {
    for (const listener of this.errorListeners) listener(error);
  }
}

class FakeMediaQuery implements MediaQueryAdapter {
  matches: boolean;
  readonly listeners = new Set<() => void>();

  constructor(matches: boolean) { this.matches = matches; }
  addEventListener(_type: "change", listener: () => void): void { this.listeners.add(listener); }
  removeEventListener(_type: "change", listener: () => void): void { this.listeners.delete(listener); }

  update(matches: boolean): void {
    if (matches === this.matches) return;
    this.matches = matches;
    for (const listener of this.listeners) listener();
  }
}

class ResponsiveEnvironment {
  width: number;
  reduced: boolean;
  readonly queries = new Map<string, FakeMediaQuery>();

  constructor(width = 1_280, reduced = false) {
    this.width = width;
    this.reduced = reduced;
  }

  readonly factory = (query: string): FakeMediaQuery => {
    const matches = query === TABLET_MEDIA_QUERY ? this.width <= 1_024
      : query === MOBILE_MEDIA_QUERY ? this.width <= 767 : this.reduced;
    const media = new FakeMediaQuery(matches);
    this.queries.set(query, media);
    return media;
  };

  resize(width: number): void {
    this.width = width;
    this.queries.get(TABLET_MEDIA_QUERY)?.update(width <= 1_024);
    this.queries.get(MOBILE_MEDIA_QUERY)?.update(width <= 767);
  }

  reduceMotion(reduced: boolean): void {
    this.reduced = reduced;
    this.queries.get(REDUCED_MOTION_MEDIA_QUERY)?.update(reduced);
  }
}

class InProcessWorker implements EmulatorSourceWorker {
  readonly scheduler = new ManualScheduler();
  private readonly listeners = new Set<(event: { readonly data: WorkerToMainMessage }) => void>();
  private readonly runtime = createEmulatorWorkerRuntime({
    scheduler: this.scheduler,
    postMessage: (message, transfer) => {
      const clone = structuredClone(message, { transfer: transfer === undefined ? [] : [...transfer] });
      for (const listener of this.listeners) listener({ data: clone });
    },
  });
  postMessage(message: MainToWorkerMessage): void { this.runtime.handleMessage(message); }
  addEventListener(_type: "message", listener: (event: { readonly data: WorkerToMainMessage }) => void): void { this.listeners.add(listener); }
  removeEventListener(_type: "message", listener: (event: { readonly data: WorkerToMainMessage }) => void): void { this.listeners.delete(listener); }
  terminate(): Promise<number> { this.runtime.dispose(); return Promise.resolve(0); }
}

function mount({ width = 1_280, reduced = false, connected = true, options = {} }: {
  width?: number;
  reduced?: boolean;
  connected?: boolean;
  options?: EmulatorInterfaceOptions;
} = {}): {
  source: ControlledSource;
  document: FakeDocument;
  host: FakeElement;
  emulator: SpikelingEmulator;
  environment: ResponsiveEnvironment;
  frames: ManualAnimationFrames;
} {
  const source = new ControlledSource(connected);
  const document = new FakeDocument();
  const host = document.createHost();
  const environment = new ResponsiveEnvironment(width, reduced);
  const frames = new ManualAnimationFrames();
  const emulator = new SpikelingEmulator(host as unknown as HTMLElement, source, {
    ...options,
    oscilloscope: { frameScheduler: frames, ...options.oscilloscope },
    recorder: { maxSamples: 200, ...options.recorder },
    mediaQueryFactory: environment.factory,
  });
  return { source, document, host, emulator, environment, frames };
}

function find(host: FakeElement, predicate: (element: FakeElement) => boolean): FakeElement {
  const found = host.findAll(predicate)[0];
  assert.ok(found);
  return found;
}

function byClass(host: FakeElement, name: string): FakeElement {
  return find(host, (element) => element.className.split(" ").includes(name));
}

function transport(host: FakeElement, name: string): FakeElement {
  return find(host, (element) => element.className === "spk-emulator__button" && element.dataset.action === name);
}

function panel(host: FakeElement, name: EmulatorPanel): FakeElement {
  return find(host, (element) => element.tagName === "details" && element.dataset.panel === name);
}

test("standalone shell mounts all existing scientific components behind one scoped root", () => {
  const { host, emulator } = mount();
  const root = byClass(host, "spk-emulator");
  assert.equal(root.tagName, "section");
  assert.equal(root.attributes.get("aria-label"), "Interactive Spikeling neuronal emulator");
  assert.equal(root.dataset.layout, "desktop");
  assert.equal(root.dataset.motion, "standard");
  assert.ok(emulator.oscilloscope);
  assert.ok(emulator.controls);
  assert.ok(emulator.synapses);
  assert.ok(emulator.recorder);
  assert.ok(emulator.recording);
});

test("neuron panel exposes only mode, always-active current input and always-active noise", () => {
  const { host, emulator } = mount();
  const main = panel(host, "main");
  assert.equal(main.children[0].textContent, "Neuron Parameters");
  assert.deepEqual(
    main.findAll((element) => element.className === "spk-controls__heading").map((heading) => heading.textContent),
    ["Neuron mode", "Current input", "Noise"],
  );
  assert.equal(main.findAll((element) => element.tagName === "label" && element.textContent === "Neuron mode").length, 0);
  for (const [identifier, label] of [["injectedCurrent", "Current input (a.u.)"], ["noiseLevel", "Noise (%)"]] as const) {
    const row = find(main, (element) => element.dataset.control === identifier);
    const inputs = row.findAll((element) => element.tagName === "input");
    assert.equal(inputs.length, 1);
    assert.equal(inputs[0].type, "range");
    assert.equal(inputs[0].disabled, false);
    assert.equal(inputs[0].attributes.get("aria-label"), label);
    assert.equal(row.findAll((element) => element.className === "spk-controls__control-label").length, 0);
    const scale = find(row, (element) => element.className === "spk-controls__scale");
    assert.equal(scale.attributes.get("aria-hidden"), "true");
    assert.deepEqual(
      scale.children.map((marker) => marker.textContent),
      identifier === "injectedCurrent" ? ["-100", "0", "100"] : ["0%", "100%"],
    );
    emulator.controls.setControlEnabled(identifier, false);
    assert.equal(emulator.controls.isEnabled(identifier), true);
  }
  assert.equal(main.findAll((element) => element.textContent === "Photoreceptor").length, 0);
  assert.equal(host.findAll((element) => element.dataset.panel === "recording").length, 0);
  assert.equal(host.findAll((element) => element.className.split(" ").includes("spk-recording")).length, 0);
});

test("stimulus panel keeps only current routing and always-active labelled waveform sliders", () => {
  const { host, emulator } = mount();
  const main = panel(host, "main");
  const stimulus = panel(host, "stimulus");
  assert.equal(stimulus.children[0].textContent, "Stimulus Parameters");
  assert.equal(main.findAll((element) => element.dataset.control === "stimulusFrequency").length, 0);
  assert.equal(stimulus.findAll((element) => element.className === "spk-controls__heading").length, 0);
  assert.equal(stimulus.findAll((element) => element.className === "spk-controls__custom").length, 0);
  assert.equal(stimulus.findAll((element) => element.attributes.get("aria-label") === "Light stimulation").length, 0);
  assert.equal(stimulus.findAll((element) => element.attributes.get("aria-label") === "Use custom stimulus").length, 0);

  const routing = find(stimulus, (element) => element.attributes.get("aria-label") === "Apply current stimulation");
  assert.equal(routing.type, "checkbox");

  for (const [id, label] of [
    ["stimulusFrequency", "Stimulus frequency"],
    ["stimulusStrength", "Stimulus strength"],
  ] as const) {
    const row = find(stimulus, (element) => element.dataset.control === id);
    const inputs = row.findAll((element) => element.tagName === "input");
    assert.equal(inputs.length, 1);
    assert.equal(inputs[0].type, "range");
    assert.equal(inputs[0].disabled, false);
    assert.equal(row.findAll((element) => element.className === "spk-controls__control-label")[0].textContent, label);
    assert.equal(row.findAll((element) => element.className === "spk-controls__scale").length, 0);
    emulator.controls.setControlEnabled(id, false);
    assert.equal(emulator.controls.isEnabled(id), true);
  }
});

test("speed and oscilloscope share one instrument column alongside consistently titled panels", () => {
  const { host } = mount();
  const workspace = byClass(host, "spk-emulator__workspace");
  const instrument = byClass(host, "spk-emulator__instrument");
  const controls = byClass(host, "spk-emulator__transport");
  const title = byClass(host, "spk-emulator__transport-title");
  const oscilloscope = byClass(host, "spk-emulator__oscilloscope");

  assert.equal(instrument.parent, workspace);
  assert.deepEqual(instrument.children, [controls, oscilloscope]);
  assert.equal(title.textContent, "Simulation speed");
  assert.equal(byClass(host, "spk-emulator__speed").attributes.get("aria-label"), "Simulation speed");
  assert.deepEqual(
    [panel(host, "main"), panel(host, "stimulus"), panel(host, "synapses")].map((section) => section.children[0].textContent),
    ["Neuron Parameters", "Stimulus Parameters", "Synapses"],
  );
});

test("public synapse panels omit photoreceptors and retain one renamed stimulus switch", () => {
  const { host } = mount();
  const synapses = panel(host, "synapses");

  for (const number of ["1", "2"] as const) {
    const channel = find(synapses, (element) =>
      element.className.includes("spk-synapses__channel") && element.dataset.synapse === "synapse" + number);
    assert.deepEqual(
      channel.findAll((element) => element.className === "spk-synapses__subheading").map((heading) => heading.textContent),
      ["Synaptic output", "Auxiliary cell input", "Stimulus"],
    );
    assert.equal(channel.findAll((element) => element.textContent === "Photoreceptor").length, 0);
    assert.equal(channel.findAll((element) =>
      element.attributes.get("aria-label") === "Synapse " + number + " light stimulation").length, 0);
    const current = find(channel, (element) =>
      element.attributes.get("aria-label") === "Synapse " + number + " Apply current stimulation");
    assert.equal(current.type, "checkbox");
    assert.equal(channel.findAll((element) =>
      element.className === "spk-controls__toggle-label" && element.textContent === "Apply current stimulation").length, 1);
  }
});

test("scientific scope clearly distinguishes educational simulation from biological recordings", () => {
  const { host } = mount();
  const scope = byClass(host, "spk-emulator__scope");
  assert.match(scope.textContent, /Izhikevich educational model/);
  assert.match(scope.textContent, /not a biological preparation/);
  assert.match(scope.textContent, /not a research-grade|research-grade electrophysiology recorder/);
});

test("simulation transport contains genuinely labelled native buttons and six truthful speeds", () => {
  const { host } = mount();
  for (const name of ["start", "pause", "stop", "reset"]) {
    const button = transport(host, name);
    assert.equal(button.tagName, "button");
    assert.equal(button.type, "button");
    assert.match(button.attributes.get("aria-label") ?? "", /simulation/);
  }
  const speed = byClass(host, "spk-emulator__speed");
  assert.equal(speed.tagName, "select");
  assert.equal(speed.children.length, 6);
  assert.deepEqual(speed.children.map((option) => option.textContent), [
    "0.025× real time · 250 samples/s",
    "0.05× real time · 500 samples/s",
    "0.1× real time · 1,000 samples/s",
    "0.25× real time · 2,500 samples/s",
    "0.5× real time · 5,000 samples/s",
    "1× real time · 10,000 samples/s",
  ]);
  assert.equal(speed.attributes.get("aria-describedby"), byClass(host, "spk-emulator__scope").id);
});

test("unconnected transport is semantically disabled until a genuine source snapshot arrives", async () => {
  const { host, source } = mount({ connected: false });
  for (const action of ["start", "pause", "stop", "reset"]) {
    assert.equal(transport(host, action).disabled, true);
  }
  assert.equal(byClass(host, "spk-emulator__speed").disabled, true);
  await source.connect();
  assert.equal(transport(host, "start").disabled, false);
  assert.equal(transport(host, "pause").disabled, true);
  assert.equal(transport(host, "stop").disabled, true);
  assert.equal(transport(host, "reset").disabled, false);
});

test("start, pause, resume, stop and reset update accessible state without relying on colour", () => {
  const { host, source } = mount();
  transport(host, "start").dispatch("click");
  assert.equal(source.engine.getSnapshot().lifecycle, "running");
  assert.match(byClass(host, "spk-emulator__status").textContent, /Running/);
  assert.equal(transport(host, "start").disabled, true);
  assert.equal(transport(host, "pause").disabled, false);
  transport(host, "pause").dispatch("click");
  assert.match(byClass(host, "spk-emulator__status").textContent, /Paused/);
  assert.equal(transport(host, "start").disabled, false);
  assert.equal(transport(host, "stop").disabled, false);
  transport(host, "start").dispatch("click");
  transport(host, "stop").dispatch("click");
  assert.match(byClass(host, "spk-emulator__status").textContent, /Stopped/);
  transport(host, "reset").dispatch("click");
  assert.match(byClass(host, "spk-emulator__status").textContent, /Ready/);
});

test("simulation speed selector displays the genuine wall-clock target independently of sampling", () => {
  const { host, source, emulator } = mount();
  const speed = byClass(host, "spk-emulator__speed");
  assert.equal(speed.value, "2");
  speed.value = "5";
  speed.dispatch("change");
  assert.equal(source.engine.getSnapshot().speed.stepsPerSecond, 10_000);
  assert.match(byClass(host, "spk-emulator__status").textContent, /1× real time · 10,000 samples\/s/);
  assert.match(byClass(emulator.recording.element as unknown as FakeElement, "spk-recording__rates").textContent, /10,000 samples\/s of simulation time/);
});

test("speed and graph remain the first scientific workspace items at every viewport width", () => {
  for (const width of [1_440, 1_024, 767, 360]) {
    const { host } = mount({ width });
    const workspace = byClass(host, "spk-emulator__workspace");
    assert.equal(workspace.children[0].className, "spk-emulator__instrument");
    assert.deepEqual(
      workspace.children[0].children.map((element) => element.className),
      ["spk-emulator__transport", "spk-emulator__oscilloscope"],
    );
    assert.deepEqual(workspace.children.slice(1).map((element) => element.dataset.panel), ["main", "stimulus", "synapses"]);
  }
});

test("desktop and tablet preserve expanded panels while mobile starts with native accordions", () => {
  for (const [width, layout, open] of [[1_280, "desktop", true], [768, "tablet", true], [767, "mobile", false]] as const) {
    const { emulator, host } = mount({ width });
    assert.equal(emulator.getLayout(), layout);
    assert.equal(byClass(host, "spk-emulator").dataset.layout, layout);
    for (const name of ["main", "stimulus", "synapses"] as const) {
      assert.equal(emulator.isPanelOpen(name), open);
      assert.equal(panel(host, name).children[0].attributes.get("aria-expanded"), String(open));
    }
  }
});

test("native details summaries control labelled regions without replacing keyboard semantics", () => {
  const { host } = mount();
  for (const name of ["main", "stimulus", "synapses"] as const) {
    const details = panel(host, name);
    const summary = details.children[0];
    const content = details.children[1];
    assert.equal(details.tagName, "details");
    assert.equal(summary.tagName, "summary");
    assert.equal(content.attributes.get("role"), "region");
    assert.equal(content.attributes.get("aria-labelledby"), summary.id);
    assert.equal(summary.attributes.get("aria-controls"), content.id);
    details.open = false;
    details.dispatch("toggle");
    assert.equal(summary.attributes.get("aria-expanded"), "false");
  }
});

test("public panel controls synchronise accessible expanded state and reject unknown panels", () => {
  const { host, emulator } = mount();
  emulator.setPanelOpen("main", false);
  assert.equal(emulator.isPanelOpen("main"), false);
  assert.equal(panel(host, "main").children[0].attributes.get("aria-expanded"), "false");
  emulator.setPanelOpen("main", true);
  assert.equal(emulator.isPanelOpen("main"), true);
  assert.throws(() => emulator.isPanelOpen("other" as EmulatorPanel), /Unknown emulator control panel/);
});

test("responsive resize transitions deliberately collapse mobile panels and reopen larger layouts", () => {
  const { host, emulator, environment } = mount({ width: 1_280 });
  environment.resize(1_024);
  assert.equal(emulator.getLayout(), "tablet");
  assert.equal(emulator.isPanelOpen("main"), true);
  environment.resize(767);
  assert.equal(emulator.getLayout(), "mobile");
  assert.equal(emulator.isPanelOpen("main"), false);
  emulator.setPanelOpen("main", true);
  environment.resize(768);
  assert.equal(emulator.getLayout(), "tablet");
  assert.equal(emulator.isPanelOpen("stimulus"), true);
  environment.resize(1_440);
  assert.equal(emulator.getLayout(), "desktop");
  assert.equal(byClass(host, "spk-emulator").dataset.layout, "desktop");
});

test("reduced-motion preference is observable without pausing the scientific oscilloscope", () => {
  const { host, source, emulator, environment, frames } = mount({ reduced: true });
  assert.equal(byClass(host, "spk-emulator").dataset.motion, "reduced");
  source.start();
  source.scheduler.advance(50);
  assert.equal(emulator.oscilloscope.renderLoop.running, true);
  assert.ok(frames.pending > 0);
  frames.advance();
  assert.equal(emulator.recorder.getSnapshot().recordingSampleRateHz, 10_000);
  environment.reduceMotion(false);
  assert.equal(byClass(host, "spk-emulator").dataset.motion, "standard");
});

test("unchanged media-query results do not churn layouts, panels or scientific samples", () => {
  const { emulator, environment, source } = mount();
  emulator.setPanelOpen("main", false);
  environment.resize(1_300);
  assert.equal(emulator.isPanelOpen("main"), false);
  assert.equal(source.engine.getSnapshot().stepIndex, 0);
});

test("application remains functional when a host environment has no matchMedia support", () => {
  const source = new ControlledSource();
  const owner = new FakeDocument();
  const host = owner.createHost();
  const app = new SpikelingEmulator(host as unknown as HTMLElement, source, {
    oscilloscope: { frameScheduler: new ManualAnimationFrames() },
    recorder: { maxSamples: 5 },
  });
  assert.equal(app.getLayout(), "desktop");
  app.dispose();
});

test("native browser matchMedia is used when no custom responsive adapter is supplied", () => {
  const source = new ControlledSource();
  const owner = new FakeDocument() as FakeDocument & {
    defaultView: { matchMedia(query: string): FakeMediaQuery };
  };
  const environment = new ResponsiveEnvironment(600, true);
  owner.defaultView = { matchMedia: (query) => environment.factory(query) };
  const host = owner.createHost();
  const app = new SpikelingEmulator(host as unknown as HTMLElement, source, {
    oscilloscope: { frameScheduler: new ManualAnimationFrames() },
    recorder: { maxSamples: 5 },
  });
  assert.equal(app.getLayout(), "mobile");
  assert.equal(byClass(host, "spk-emulator").dataset.motion, "reduced");
  environment.resize(1_200);
  assert.equal(app.getLayout(), "desktop");
  app.dispose();
});

test("each native input, button, select, summary and source link has an accessible name", () => {
  const { host } = mount();
  const labels = host.findAll((element) => element.tagName === "label");
  const interactives = host.findAll((element) => ["input", "button", "select", "summary", "a"].includes(element.tagName));
  assert.ok(interactives.length > 35);
  for (const element of interactives) {
    const labelledByAttribute = (element.attributes.get("aria-label") ?? "").length > 0;
    const labelledByText = element.textContent.length > 0;
    const labelledByExplicitLabel = element.id.length > 0 && labels.some((label) => label.htmlFor === element.id);
    let ancestor = element.parent;
    let labelledByAncestor = false;
    while (ancestor !== undefined) {
      if (ancestor.tagName === "label" && ancestor.textContent.length > 0) labelledByAncestor = true;
      ancestor = ancestor.parent;
    }
    assert.ok(labelledByAttribute || labelledByText || labelledByExplicitLabel || labelledByAncestor,
      "Unlabelled " + element.tagName + " " + element.className);
  }
});

test("screen-reader live regions announce lifecycle changes without narrating every sample", () => {
  const { host, source, emulator } = mount();
  const status = byClass(host, "spk-emulator__status");
  assert.equal(status.attributes.get("role"), "status");
  assert.equal(status.attributes.get("aria-live"), "polite");
  assert.equal(status.attributes.get("aria-atomic"), "true");
  source.start();
  const announcement = status.textContent;
  source.scheduler.advance(50);
  assert.equal(status.textContent, announcement);
  assert.equal(byClass(host, "spk-oscilloscope__readings").attributes.get("aria-live"), "off");
  assert.equal(byClass(emulator.recording.element as unknown as FakeElement, "spk-recording__statistics").attributes.get("aria-live"), "off");
});

test("essential plot readings include text equivalents for voltage, current and stimulus", () => {
  const { host, source } = mount();
  source.start();
  source.scheduler.advance(50);
  const readings = byClass(host, "spk-oscilloscope__readings").textContent;
  assert.match(readings, /Vm .* mV/);
  assert.match(readings, /Input .* a\.u\./);
  assert.match(readings, /Stimulus/);
  assert.match(byClass(host, "spk-synapses__reading").textContent, /Vm|Inactive/);
});

test("every component shares one worker-independent source without resetting scientific state", () => {
  const { source, emulator } = mount();
  emulator.controls.setControlEnabled("injectedCurrent", true);
  emulator.controls.setControlValue("injectedCurrent", 21);
  emulator.synapses.setSynapseEnabled("synapse1", true);
  emulator.synapses.setControlEnabled("synapse1", "gain", true);
  emulator.synapses.setControlValue("synapse1", "gain", -25);
  emulator.recorder.start();
  source.start();
  source.scheduler.advance(50);
  assert.equal(source.engine.getSnapshot().stepIndex, 50);
  assert.equal(emulator.recorder.getSnapshot().sampleCount, 50);
  assert.equal(emulator.oscilloscope.isTraceVisible("synapse1Current"), true);
  assert.equal(source.engine.getSnapshot().controls.main.patchCurrent, 21);
  assert.equal(source.engine.getSnapshot().controls.synapse1.gain, -25);
});

test("recording and simulation transport remain independent within the responsive shell", () => {
  const { host, source, emulator } = mount();
  transport(host, "start").dispatch("click");
  source.scheduler.advance(50);
  assert.equal(emulator.recorder.getSnapshot().sampleCount, 0);
  emulator.recorder.start();
  source.scheduler.advance(50);
  emulator.recorder.stop();
  assert.equal(emulator.recorder.getSnapshot().sampleCount, 50);
  assert.equal(source.engine.getSnapshot().lifecycle, "running");
  transport(host, "pause").dispatch("click");
  assert.equal(parseRecordingCsv(emulator.recorder.exportCsv()).samples.length, 50);
});

test("source failures and transport exceptions appear as clear accessible text", () => {
  const { host, source } = mount();
  source.emitError(new Error("Worker connection interrupted"));
  assert.equal(byClass(host, "spk-emulator__error").textContent, "Worker connection interrupted");
  source.failure = new Error("Simulation cannot start");
  transport(host, "start").dispatch("click");
  assert.equal(byClass(host, "spk-emulator__error").textContent, "Simulation cannot start");
  source.failure = "unknown failure";
  transport(host, "start").dispatch("click");
  assert.equal(byClass(host, "spk-emulator__error").textContent, "Unable to update the emulator.");
  source.failure = undefined;
  transport(host, "start").dispatch("click");
  assert.equal(byClass(host, "spk-emulator__error").textContent, "");
});

test("verified open-source link is inspectable and optionally configurable", () => {
  const first = mount();
  assert.equal(byClass(first.host, "spk-emulator__source").href, "https://github.com/OpenSourceNeuro/Spikeling");
  const custom = mount({ options: { sourceUrl: "https://github.com/OpenSourceNeuro/Spikeling/tree/main" } });
  assert.equal(byClass(custom.host, "spk-emulator__source").href, "https://github.com/OpenSourceNeuro/Spikeling/tree/main");
});

test("multiple emulator instances use collision-free panel and form-control identifiers", () => {
  const first = mount();
  const second = mount();
  const one = first.host.findAll((element) => element.id.length > 0).map((element) => element.id);
  const two = second.host.findAll((element) => element.id.length > 0).map((element) => element.id);
  for (const identifier of one) {
    assert.equal(two.includes(identifier), false, "Duplicate embedding id: " + identifier);
  }
});

test("responsive shell accepts independent recording, synapse and download configuration", () => {
  const downloads: RecordingDownload[] = [];
  const { source, emulator } = mount({
    options: {
      recorder: { maxSamples: 7, chunkSamples: 3 },
      synapses: { autoShowTraces: false },
      recording: { download: (file) => downloads.push(file) },
    },
  });
  assert.equal(emulator.recorder.getSnapshot().maxSamples, 7);
  emulator.synapses.setSynapseEnabled("synapse1", true);
  assert.equal(emulator.oscilloscope.isTraceVisible("synapse1Current"), false);
  emulator.recorder.start();
  source.start();
  source.scheduler.advance(50);
  emulator.recording.download();
  assert.equal(downloads.length, 1);
  assert.equal(parseRecordingCsv(downloads[0].content).samples.length, 7);
});

test("actual transferable worker batches drive the entire responsive shell end to end", async () => {
  const worker = new InProcessWorker();
  const source = new EmulatorSource({
    workerFactory: () => worker,
    speedIndex: 1,
    historyCapacity: 10,
    maxStepsPerSlice: 7,
    simulation: { seed: 500, controls: { main: { patchCurrent: 19 } } },
  });
  const owner = new FakeDocument();
  const host = owner.createHost();
  const frames = new ManualAnimationFrames();
  const emulator = new SpikelingEmulator(host as unknown as HTMLElement, source, {
    oscilloscope: { frameScheduler: frames },
    recorder: { maxSamples: 50 },
  });
  await source.connect();
  emulator.recorder.start();
  transport(host, "start").dispatch("click");
  worker.scheduler.advance(50);
  frames.advance();
  assert.equal(emulator.recorder.getSnapshot().sampleCount, 25);
  assert.equal(source.latest().length, 10);
  assert.equal(emulator.recorder.samples()[0].mainVm, new SpikelingModel({ seed: 500, controls: { main: { patchCurrent: 19 } } }).step().mainVm);
  emulator.dispose();
  await source.disconnect();
});

test("shell disposal is idempotent and detaches every media, worker and component listener", () => {
  const { host, source, emulator, environment } = mount();
  assert.ok(source.sampleListeners.size > 0);
  assert.ok(source.stateListeners.size > 0);
  assert.ok(source.errorListeners.size > 0);
  emulator.dispose();
  emulator.dispose();
  assert.equal(host.children.length, 0);
  assert.equal(source.sampleListeners.size, 0);
  assert.equal(source.stateListeners.size, 0);
  assert.equal(source.errorListeners.size, 0);
  for (const media of environment.queries.values()) assert.equal(media.listeners.size, 0);
});

test("Phase 7 preview mounts only the embeddable application and serves scoped responsive assets", async () => {
  const page = await readDevelopmentAsset("/");
  const entry = await readDevelopmentAsset("/demo/main.ts");
  const component = await readDevelopmentAsset("/src/interface/emulator.ts");
  const stylesheet = await readDevelopmentAsset("/src/styles/emulator.css");
  assert.match(page.content, /Local Phase 7 preview/);
  assert.match(page.content, /id="emulator"/);
  assert.match(page.content, /src\/styles\/emulator\.css/);
  assert.match(entry.content, /new SpikelingEmulator/);
  assert.match(component.content, /class SpikelingEmulator/);
  assert.match(stylesheet.contentType, /^text\/css/);
  assert.doesNotMatch(entry.content, /\.innerHTML\s*=|document\.write\s*\(/);
});
