// SPDX-License-Identifier: GPL-3.0-or-later

import assert from "node:assert/strict";
import test from "node:test";

import {
  CUSTOM_STIMULUS_LIMITS,
  CustomStimulusError,
  EmulatorSource,
  MAIN_CONTROL_SPECIFICATIONS,
  NEURON_PRESETS,
  SimulationEngine,
  SpikelingMainControls,
  createEmulatorWorkerRuntime,
  defaultControls,
  formatMainControlValue,
  gaussianNoiseStandardDeviation,
  getMainControlSpecification,
  photoreceptorDecayRate,
  photoreceptorRecoveryRate,
  stimulusFrequencyHz,
  validateMainControlValue,
} from "../src/index.ts";
import type {
  ControlsPatch,
  DataSource,
  EmulatorSourceWorker,
  EngineSnapshot,
  ErrorListener,
  MainControlId,
  MainToWorkerMessage,
  MainNeuronControlsOptions,
  SampleListener,
  SimulationSample,
  StateListener,
  Unsubscribe,
  WorkerToMainMessage,
} from "../src/index.ts";
import { FakeCanvasElement, FakeDocument, FakeElement } from "./helpers/fake-dom.ts";
import { ManualScheduler } from "./helpers/manual-scheduler.ts";
import { readDevelopmentAsset } from "../tools/serve.mjs";

class ControlledDataSource implements DataSource {
  readonly kind = "emulator";
  readonly scheduler = new ManualScheduler();
  readonly patches: ControlsPatch[] = [];
  readonly sampleListeners = new Set<SampleListener>();
  readonly stateListeners = new Set<StateListener>();
  readonly errorListeners = new Set<ErrorListener>();
  readonly engine: SimulationEngine;
  connected: boolean;

  constructor(initial: ControlsPatch = {}, connected = true) {
    this.connected = connected;
    this.engine = new SimulationEngine({
      modelOptions: { controls: initial, seed: 123456 },
      scheduler: this.scheduler,
      onSamples: (samples) => {
        for (const listener of this.sampleListeners) {
          listener(samples);
        }
      },
      onState: (snapshot) => this.emitState(snapshot),
    });
  }

  async connect(): Promise<void> {
    this.connected = true;
    this.emitState(this.engine.getSnapshot());
  }

  async disconnect(): Promise<void> {
    this.connected = false;
    this.engine.dispose();
  }

  start(): void { this.engine.start(); }
  pause(): void { this.engine.pause(); }
  stop(): void { this.engine.stop(); }
  reset(): void { this.engine.reset(); }
  setSpeed(index: number): void { this.engine.setSpeed(index); }

  updateControls(patch: ControlsPatch): void {
    this.patches.push(structuredClone(patch));
    this.engine.updateControls(patch);
  }

  requestSnapshot(): void {
    this.emitState(this.engine.getSnapshot());
  }

  subscribe(listener: SampleListener): Unsubscribe {
    this.sampleListeners.add(listener);
    return () => this.sampleListeners.delete(listener);
  }

  subscribeState(listener: StateListener): Unsubscribe {
    this.stateListeners.add(listener);
    if (this.connected) {
      listener(this.engine.getSnapshot());
    }
    return () => this.stateListeners.delete(listener);
  }

  subscribeErrors(listener: ErrorListener): Unsubscribe {
    this.errorListeners.add(listener);
    return () => this.errorListeners.delete(listener);
  }

  latest(count?: number): SimulationSample[] {
    return this.engine.history.latest(count);
  }

  emitError(error: Error): void {
    for (const listener of this.errorListeners) {
      listener(error);
    }
  }

  private emitState(snapshot: EngineSnapshot): void {
    for (const listener of this.stateListeners) {
      listener(snapshot);
    }
  }
}

function mount(initial: ControlsPatch = {}, options: MainNeuronControlsOptions = {}): {
  source: ControlledDataSource;
  document: FakeDocument;
  host: FakeElement;
  panel: SpikelingMainControls;
  preview: FakeCanvasElement;
} {
  const source = new ControlledDataSource(initial);
  const document = new FakeDocument();
  const host = document.createHost();
  const panel = new SpikelingMainControls(host as unknown as HTMLElement, source, options);
  return { source, document, host, panel, preview: document.canvases[0] };
}

function byControl(host: FakeElement, id: MainControlId): {
  row: FakeElement;
  toggle: FakeElement;
  slider: FakeElement;
  output: FakeElement;
} {
  const row = host.findAll((candidate) => candidate.dataset.control === id)[0];
  const inputs = row.findAll((candidate) => candidate.tagName === "input");
  return {
    row,
    toggle: inputs[0],
    slider: inputs[1],
    output: row.findAll((candidate) => candidate.tagName === "output")[0],
  };
}

function byAriaLabel(host: FakeElement, label: string): FakeElement {
  const found = host.findAll((candidate) => candidate.attributes.get("aria-label") === label)[0];
  assert.ok(found, "Missing accessible control " + label);
  return found;
}

test("all desktop main-neuron sliders retain their audited signed ranges and off defaults", () => {
  assert.deepEqual(
    MAIN_CONTROL_SPECIFICATIONS.map((control) => [control.id, control.minimum, control.maximum, control.defaultValue, control.tickInterval]),
    [
      ["stimulusFrequency", -100, 100, 0, 20],
      ["stimulusStrength", -100, 100, 0, 20],
      ["injectedCurrent", -100, 100, 0, 20],
      ["noiseLevel", 0, 100, 0, 10],
      ["photoreceptorGain", -100, 100, 0, 20],
      ["photoreceptorDecay", 10, 125, 100, 10],
      ["photoreceptorRecovery", 1, 100, 25, 10],
    ],
  );
  assert.ok(MAIN_CONTROL_SPECIFICATIONS.every((control) => control.step === 1 && !control.enabledByDefault));
  assert.equal(getMainControlSpecification("stimulusFrequency").desktopWidget, "Emulator_StimFre_slider");
});

test("desktop frequency readout preserves the nonlinear 10–1000 Hz conversion", () => {
  assert.ok(Math.abs(stimulusFrequencyHz(-100) - 10000 / 1010) < 1e-12);
  assert.ok(Math.abs(stimulusFrequencyHz(0) - 10000 / 510) < 1e-12);
  assert.equal(stimulusFrequencyHz(100), 1000);
  assert.equal(formatMainControlValue("stimulusFrequency", -100), "10 Hz");
  assert.equal(formatMainControlValue("stimulusFrequency", 0), "20 Hz");
  assert.equal(formatMainControlValue("stimulusFrequency", 100), "1000 Hz");
});

test("photoreceptor and noise readouts display genuine model coefficients and Gaussian scale", () => {
  assert.equal(photoreceptorDecayRate(100), 0.001);
  assert.equal(photoreceptorDecayRate(10), 0.0001);
  assert.equal(photoreceptorRecoveryRate(25), 0.025);
  assert.equal(gaussianNoiseStandardDeviation(100), 25);
  assert.equal(formatMainControlValue("photoreceptorDecay", 125), "0.00125 ms⁻¹");
  assert.equal(formatMainControlValue("photoreceptorRecovery", 1), "0.001 ms⁻¹");
  assert.equal(formatMainControlValue("noiseLevel", 37), "37% · σ 9.25 a.u.");
  assert.equal(formatMainControlValue("stimulusStrength", -20), "-20%");
  assert.equal(formatMainControlValue("photoreceptorGain", 50), "50%");
  assert.equal(formatMainControlValue("injectedCurrent", -12), "-12 a.u.");
});

test("invalid controls and scientifically unsafe slider values fail before source updates", () => {
  assert.throws(() => getMainControlSpecification("invalid" as MainControlId), /Unknown main-neuron control/);
  for (const value of [-101, 101, 1.2, Number.NaN, Number.POSITIVE_INFINITY]) {
    assert.throws(() => validateMainControlValue("injectedCurrent", value), RangeError);
  }
  assert.throws(() => validateMainControlValue("noiseLevel", -1), RangeError);
  assert.throws(() => validateMainControlValue("photoreceptorDecay", 9), RangeError);
  assert.throws(() => validateMainControlValue("photoreceptorRecovery", 0), RangeError);

  const { source, panel } = mount();
  assert.throws(() => panel.setControlValue("injectedCurrent", 101), RangeError);
  assert.equal(source.patches.length, 0);
});

test("control panel mounts native, labelled inputs and all 20 source-pinned neuron modes", () => {
  const { host, document, panel } = mount();
  assert.equal(host.children.length, 1);
  assert.equal(panel.element.className, "spk-controls");
  assert.equal(panel.element.attributes.get("aria-label"), "Main neuron and stimulus controls");

  const options = host.findAll((element) => element.tagName === "option" && element.parent?.tagName === "select");
  assert.deepEqual(options.map((option) => option.textContent), NEURON_PRESETS.map((preset) => preset.label));
  assert.equal(options.length, 20);

  for (const specification of MAIN_CONTROL_SPECIFICATIONS) {
    const { row, toggle, slider, output } = byControl(host, specification.id);
    assert.equal(toggle.type, "checkbox");
    assert.equal(slider.type, "range");
    assert.equal(slider.min, String(specification.minimum));
    assert.equal(slider.max, String(specification.maximum));
    assert.equal(slider.step, "1");
    assert.equal(slider.disabled, true);
    assert.equal(toggle.checked, false);
    assert.equal(row.dataset.disabled, "true");
    assert.ok(slider.attributes.has("aria-label"));
    assert.ok(slider.attributes.has("aria-valuetext"));
    assert.equal(output.attributes.get("for"), slider.id);
  }

  const preview = document.canvases[0];
  assert.equal(preview.attributes.get("role"), "img");
  assert.match(preview.attributes.get("aria-label") ?? "", /stimulus preview/);
  assert.equal(host.findAll((element) => element.attributes.get("role") === "status").length, 1);
  assert.equal(host.findAll((element) => element.attributes.get("role") === "alert").length, 1);
});

test("an already-connected data source synchronises initial controls without reverting to defaults", () => {
  const { host, panel } = mount({
    main: { presetId: 11, patchCurrent: -22, lightEnabled: true, photoreceptor: { decaySlider: 80 } },
    stimulus: { strength: 34, frequencySlider: -55 },
  });

  assert.equal(panel.getControls().main.presetId, 11);
  assert.equal(panel.getControls().main.patchCurrent, -22);
  assert.equal(panel.isEnabled("injectedCurrent"), true);
  assert.equal(panel.isEnabled("photoreceptorDecay"), true);
  assert.equal(panel.isEnabled("stimulusStrength"), true);
  assert.equal(byControl(host, "injectedCurrent").slider.disabled, false);
  assert.equal(byControl(host, "stimulusFrequency").slider.value, "-55");
  assert.equal(byAriaLabel(host, "Light stimulation").checked, true);
});

test("disconnected panels initialise safely and synchronise when the source later connects", async () => {
  const source = new ControlledDataSource({ main: { patchCurrent: 19 } }, false);
  const host = new FakeDocument().createHost();
  const panel = new SpikelingMainControls(host as unknown as HTMLElement, source);
  assert.equal(panel.getControls().main.patchCurrent, 0);
  await source.connect();
  assert.equal(panel.getControls().main.patchCurrent, 19);
  assert.equal(panel.isEnabled("injectedCurrent"), true);
});

test("enabling native sliders permits live values and switching off restores desktop defaults", () => {
  const { source, host, panel } = mount();
  const current = byControl(host, "injectedCurrent");

  current.toggle.checked = true;
  current.toggle.dispatch("change");
  assert.equal(panel.isEnabled("injectedCurrent"), true);
  assert.equal(current.slider.disabled, false);

  current.slider.value = "-38";
  current.slider.dispatch("input");
  assert.equal(source.engine.model.getControls().main.patchCurrent, -38);
  assert.equal(current.output.textContent, "-38 a.u.");
  assert.equal(current.slider.style.values.get("--spk-fill"), "31%");

  current.toggle.checked = false;
  current.toggle.dispatch("change");
  assert.equal(panel.isEnabled("injectedCurrent"), false);
  assert.equal(source.engine.model.getControls().main.patchCurrent, 0);
  assert.equal(current.slider.disabled, true);
});

test("photoreceptor off toggles restore desktop gain, decay and recovery defaults", () => {
  const { source, panel } = mount();
  for (const [id, value, expected] of [
    ["photoreceptorGain", -44, 0],
    ["photoreceptorDecay", 32, 100],
    ["photoreceptorRecovery", 88, 25],
  ] as const) {
    panel.setControlEnabled(id, true);
    panel.setControlValue(id, value);
    panel.setControlEnabled(id, false);
    const photo = source.engine.model.getControls().main.photoreceptor;
    const actual = id === "photoreceptorGain" ? photo.gain : id === "photoreceptorDecay" ? photo.decaySlider : photo.recoverySlider;
    assert.equal(actual, expected);
  }
});

test("frequency and strength preserve signed raw desktop slider settings in the scientific model", () => {
  const { source, host, panel } = mount();
  panel.setControlEnabled("stimulusFrequency", true);
  panel.setControlEnabled("stimulusStrength", true);
  panel.setControlValue("stimulusFrequency", 100);
  panel.setControlValue("stimulusStrength", -65);

  assert.equal(source.engine.model.getControls().stimulus.frequencySlider, 100);
  assert.equal(source.engine.model.getControls().stimulus.strength, -65);
  assert.equal(byControl(host, "stimulusFrequency").output.textContent, "1000 Hz");
  assert.equal(byControl(host, "stimulusStrength").output.textContent, "-65%");
});

test("live noise controls forward raw desktop percentage and expose its true Gaussian deviation", () => {
  const { source, host, panel } = mount();
  panel.setControlEnabled("noiseLevel", true);
  panel.setControlValue("noiseLevel", 76);

  assert.equal(source.engine.model.getControls().main.noiseLevel, 76);
  assert.equal(byControl(host, "noiseLevel").output.textContent, "76% · σ 19 a.u.");

  panel.setControlEnabled("noiseLevel", false);
  assert.equal(source.engine.model.getControls().main.noiseLevel, 0);
});

test("direct-current and light stimulation are independently routed without altering other inputs", () => {
  const { source, host } = mount();
  const direct = byAriaLabel(host, "Direct current stimulation");
  const light = byAriaLabel(host, "Light stimulation");

  direct.checked = true;
  direct.dispatch("change");
  light.checked = true;
  light.dispatch("change");
  assert.equal(source.engine.model.getControls().main.directCurrentEnabled, true);
  assert.equal(source.engine.model.getControls().main.lightEnabled, true);

  direct.checked = false;
  direct.dispatch("change");
  assert.equal(source.engine.model.getControls().main.directCurrentEnabled, false);
  assert.equal(source.engine.model.getControls().main.lightEnabled, true);
});

test("all twenty presets update scientifically labelled a, b, c, d and resting-potential displays", () => {
  const { source, host, panel } = mount();
  for (const preset of NEURON_PRESETS) {
    panel.selectPreset(preset.id);
    const values = host.findAll((element) => element.className === "spk-controls__parameter-value");
    assert.equal(values.length, 5);
    assert.equal(values[0].textContent, String(preset.a).replace("-", "−"));
    assert.equal(values[1].textContent, String(preset.b).replace("-", "−"));
    assert.equal(values[2].textContent, String(preset.c).replace("-", "−") + " mV");
    assert.equal(values[3].textContent, String(preset.d).replace("-", "−"));
    assert.equal(values[4].textContent, String(preset.restingPotential).replace("-", "−") + " mV");
    assert.equal(source.engine.model.getControls().main.presetId, preset.id);
  }
});

test("native preset selection resets only main photoreceptor settings and preserves neuron state", () => {
  const { source, host, panel } = mount({
    main: { patchCurrent: 19, photoreceptor: { gain: 20, decaySlider: 70, recoverySlider: 60 } },
    synapse1: { enabled: true, gain: -12, patchCurrent: -14 },
  });
  source.engine.model.run(12);
  const before = source.engine.model.getState();

  const select = host.findAll((element) => element.tagName === "select")[0];
  select.value = "20";
  select.dispatch("change");

  const after = source.engine.model.getState();
  const controls = source.engine.model.getControls();
  assert.equal(after.stepIndex, before.stepIndex);
  assert.deepEqual(after.main.neuron, before.main.neuron);
  assert.equal(controls.main.presetId, 20);
  assert.equal(controls.main.patchCurrent, 19);
  assert.deepEqual(controls.main.photoreceptor, { gain: 0, decaySlider: 100, recoverySlider: 25 });
  assert.deepEqual(controls.synapse1, { ...defaultControls().synapse1, enabled: true, gain: -12, patchCurrent: -14 });
  assert.equal(panel.isEnabled("photoreceptorGain"), false);
  assert.equal(panel.isEnabled("photoreceptorDecay"), false);
  assert.equal(panel.isEnabled("photoreceptorRecovery"), false);
});

test("live injected-current changes preserve desktop one-sample neuronal integration delay", () => {
  const { source, panel } = mount();
  source.engine.model.step();
  const before = source.engine.model.getState().main.neuron;
  panel.setControlEnabled("injectedCurrent", true);
  panel.setControlValue("injectedCurrent", 35);
  assert.deepEqual(source.engine.model.getState().main.neuron, before);

  const first = source.engine.model.step();
  const second = source.engine.model.step();
  assert.equal(first.totalCurrent, 35);
  assert.equal(second.totalCurrent, 35);
  assert.notEqual(second.mainVm, first.mainVm);
});

test("local CSV import draws a source-faithful preview without activating playback implicitly", () => {
  const { source, host, panel, preview } = mount({}, { devicePixelRatio: () => 2 });
  const initialStrokes = preview.context.strokes.length;
  const parsed = panel.loadCustomStimulusText("Stim,Trigger\n5,0\n-7,1\n2,0", "classroom.csv");

  assert.deepEqual(parsed.samples, [5, -7, 2]);
  assert.deepEqual(source.engine.model.getControls().stimulus.customSamples, [5, -7, 2]);
  assert.equal(source.engine.model.getControls().stimulus.mode, "internal");
  assert.ok(preview.context.strokes.length > initialStrokes);
  assert.equal(preview.width, 1600);

  const toggle = byAriaLabel(host, "Use custom stimulus");
  assert.equal(toggle.disabled, false);
  assert.equal(toggle.checked, false);
  const status = host.findAll((element) => element.attributes.get("role") === "status")[0];
  assert.match(status.textContent, /classroom\.csv · 3 samples · 0\.1 ms\/sample · 0\.3 ms/);
});

test("custom playback disables only internal-waveform controls and restores their values afterwards", () => {
  const { source, host, panel } = mount();
  panel.setControlEnabled("stimulusFrequency", true);
  panel.setControlValue("stimulusFrequency", 70);
  panel.setControlEnabled("stimulusStrength", true);
  panel.setControlValue("stimulusStrength", -25);
  panel.setControlEnabled("injectedCurrent", true);
  panel.loadCustomStimulusText("Stim\n4\n-2");

  const custom = byAriaLabel(host, "Use custom stimulus");
  custom.checked = true;
  custom.dispatch("change");
  assert.equal(source.engine.model.getControls().stimulus.mode, "custom");
  assert.equal(byControl(host, "stimulusFrequency").slider.disabled, true);
  assert.equal(byControl(host, "stimulusFrequency").toggle.disabled, true);
  assert.equal(byControl(host, "stimulusStrength").slider.disabled, true);
  assert.equal(byControl(host, "injectedCurrent").slider.disabled, false);

  assert.deepEqual(source.engine.model.run(5).map((sample) => sample.stimulus), [4, -2, 4, -2, 4]);

  custom.checked = false;
  custom.dispatch("change");
  assert.equal(source.engine.model.getControls().stimulus.mode, "internal");
  assert.equal(byControl(host, "stimulusFrequency").slider.disabled, false);
  assert.equal(byControl(host, "stimulusFrequency").slider.value, "70");
  assert.equal(byControl(host, "stimulusStrength").slider.value, "-25");
});

test("custom playback cannot be enabled until valid local samples exist", () => {
  const { source, panel } = mount();
  assert.throws(() => panel.setCustomStimulusEnabled(true), /Load a valid stimulus CSV/);
  assert.equal(source.patches.length, 0);
});

test("pre-existing worker custom samples synchronise their waveform and playback status", () => {
  const { host, panel } = mount({ stimulus: { mode: "custom", customSamples: [8, -3, 1] } });
  assert.equal(panel.getControls().stimulus.mode, "custom");
  assert.equal(byAriaLabel(host, "Use custom stimulus").checked, true);
  assert.equal(byAriaLabel(host, "Use custom stimulus").disabled, false);
  assert.equal(byControl(host, "stimulusFrequency").slider.disabled, true);
  const status = host.findAll((element) => element.attributes.get("role") === "status")[0];
  assert.equal(status.textContent, "3 samples · 0.1 ms/sample");
});

test("native local-file input accepts CSV and surfaces malformed content accessibly", async () => {
  const { source, host } = mount();
  const input = host.findAll((element) => element.type === "file")[0];
  assert.equal(input.accept, ".csv,text/csv");
  const content = "NoStim\n1";
  input.files = [{ name: "broken.csv", size: content.length, text: async () => content }];
  input.dispatch("change");
  await new Promise((resolve) => setImmediate(resolve));

  const alert = host.findAll((element) => element.attributes.get("role") === "alert")[0];
  assert.match(alert.textContent, /exact "Stim" column/);
  assert.deepEqual(source.engine.model.getControls().stimulus.customSamples, []);
});

test("successful local-file imports clear earlier source errors without network access", async () => {
  const { source, host, panel } = mount();
  const alert = host.findAll((element) => element.attributes.get("role") === "alert")[0];
  source.emitError(new Error("Earlier worker failure"));
  assert.equal(alert.textContent, "Earlier worker failure");

  let reads = 0;
  const parsed = await panel.loadCustomStimulusFile({
    name: "local.csv",
    size: 8,
    text: async () => {
      reads += 1;
      return "Stim\n9\n4";
    },
  });
  assert.equal(reads, 1);
  assert.deepEqual(parsed.samples, [9, 4]);
  assert.equal(alert.textContent, "");
});

test("custom CSV safety limits flow through the panel before any source patch", async () => {
  const { source, panel } = mount({}, { maxSamples: 2, maxBytes: 32 });
  assert.throws(
    () => panel.loadCustomStimulusText("Stim\n1\n2\n3"),
    (error: unknown) => error instanceof CustomStimulusError && error.code === "sample-limit",
  );
  await assert.rejects(
    panel.loadCustomStimulusFile({ name: "huge.csv", size: 33, text: async () => "Stim\n1" }),
    (error: unknown) => error instanceof CustomStimulusError && error.code === "file-size",
  );
  assert.equal(source.patches.length, 0);
  assert.deepEqual(CUSTOM_STIMULUS_LIMITS, { bytes: 8 * 1024 * 1024, samples: 250_000 });
});

test("snapshots from independent controls update visible slider values and routing", () => {
  const { source, host, panel } = mount();
  source.updateControls({
    main: { patchCurrent: 41, noiseLevel: 12, directCurrentEnabled: true },
    stimulus: { strength: -55 },
  });

  assert.equal(panel.getControls().main.patchCurrent, 41);
  assert.equal(byControl(host, "injectedCurrent").output.textContent, "41 a.u.");
  assert.equal(byControl(host, "noiseLevel").output.textContent, "12% · σ 3 a.u.");
  assert.equal(byControl(host, "stimulusStrength").output.textContent, "-55%");
  assert.equal(byAriaLabel(host, "Direct current stimulation").checked, true);
});

test("rapid slider interaction preserves every bounded scientific update without resetting time", () => {
  const { source, panel } = mount();
  source.start();
  source.scheduler.advance(50);
  const initialStep = source.engine.getSnapshot().stepIndex;
  panel.setControlEnabled("injectedCurrent", true);
  for (let index = 0; index < 500; index += 1) {
    panel.setControlValue("injectedCurrent", (index % 201) - 100);
  }

  assert.equal(source.patches.length, 501);
  assert.equal(source.engine.getSnapshot().stepIndex, initialStep);
  assert.equal(source.engine.model.getControls().main.patchCurrent, (499 % 201) - 100);
  assert.equal(source.engine.getSnapshot().lifecycle, "running");
});

test("returned control snapshots are defensive copies of worker-owned scientific state", () => {
  const { source, panel } = mount({ main: { patchCurrent: 14 } });
  const copy = panel.getControls();
  copy.main.patchCurrent = 88;
  assert.equal(panel.getControls().main.patchCurrent, 14);
  assert.equal(source.engine.model.getControls().main.patchCurrent, 14);
});

test("main-neuron controls drive the real worker protocol and retain full-resolution custom samples", async () => {
  const scheduler = new ManualScheduler();
  const listeners = new Set<(event: { readonly data: WorkerToMainMessage }) => void>();
  const runtime = createEmulatorWorkerRuntime({
    scheduler,
    postMessage: (message, transfer) => {
      const cloned = structuredClone(message, { transfer: transfer ? [...transfer] : [] });
      for (const listener of listeners) {
        listener({ data: cloned });
      }
    },
  });
  const worker: EmulatorSourceWorker = {
    postMessage(message: MainToWorkerMessage): void { runtime.handleMessage(message); },
    addEventListener(_type, listener): void { listeners.add(listener); },
    removeEventListener(_type, listener): void { listeners.delete(listener); },
    terminate(): void { runtime.dispose(); },
  };
  const source = new EmulatorSource({ workerFactory: () => worker, speedIndex: 0 });
  const host = new FakeDocument().createHost();
  const panel = new SpikelingMainControls(host as unknown as HTMLElement, source);
  await source.connect();

  panel.selectPreset(11);
  panel.setControlEnabled("injectedCurrent", true);
  panel.setControlValue("injectedCurrent", 18);
  panel.loadCustomStimulusText("Stim,Trigger\n7.125,0\n-2.75,1");
  panel.setCustomStimulusEnabled(true);
  source.start();
  scheduler.advance(50);

  assert.equal(source.getSnapshot()?.controls.main.presetId, 11);
  assert.equal(source.getSnapshot()?.controls.main.patchCurrent, 18);
  assert.equal(source.history.length, 10);
  assert.deepEqual(source.latest(4).map((sample) => sample.stimulus), [7.125, -2.75, 7.125, -2.75]);
  assert.deepEqual(source.latest(4).map((sample) => sample.trigger), [1, 0, 1, 0]);

  panel.dispose();
  await source.disconnect();
});

test("local development preview serves scoped Phase 4 controls and dependency-free browser modules", async () => {
  const page = await readDevelopmentAsset("/");
  const css = await readDevelopmentAsset("/src/styles/controls.css");
  const module = await readDevelopmentAsset("/src/controls/main-controls.ts");

  assert.equal(page.status, 200);
  assert.match(page.content, /Local Phase 5 preview/);
  assert.match(page.content, /src\/styles\/controls\.css/);
  assert.match(page.content, /id="controls"/);
  assert.equal(css.status, 200);
  assert.match(css.contentType, /^text\/css/);
  assert.match(css.content, /\.spk-controls/);
  assert.match(css.content, /prefers-reduced-motion/);
  assert.doesNotMatch(css.content, /(?:^|\n)\s*(?:html|body|\*)\s*\{/);
  assert.equal(module.status, 200);
  assert.match(module.contentType, /^text\/javascript/);
  assert.match(module.content, /class SpikelingMainControls/);
});

test("panel disposal is idempotent, removes its DOM and unsubscribes from worker state/errors", () => {
  const { source, host, panel } = mount();
  assert.equal(source.stateListeners.size, 1);
  assert.equal(source.errorListeners.size, 1);

  panel.dispose();
  panel.dispose();
  assert.equal(host.children.length, 0);
  assert.equal(source.stateListeners.size, 0);
  assert.equal(source.errorListeners.size, 0);
});
