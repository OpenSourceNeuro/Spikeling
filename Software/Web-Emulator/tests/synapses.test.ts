// SPDX-License-Identifier: GPL-3.0-or-later

import assert from "node:assert/strict";
import test from "node:test";

import {
  EmulatorSource,
  MAIN_CONTROL_SPECIFICATIONS,
  NEURON_PRESETS,
  SYNAPSE_CONTROL_SPECIFICATIONS,
  SYNAPSE_IDS,
  SimulationEngine,
  SpikelingMainControls,
  SpikelingModel,
  SpikelingOscilloscope,
  SpikelingSynapseControls,
  createEmulatorWorkerRuntime,
  defaultControls,
  formatSynapseControlValue,
  getSynapseControlSpecification,
  synapticRetentionFactor,
  synapticTimeConstantMs,
  validateSynapseControlValue,
  validateSynapseId,
} from "../src/index.ts";
import type {
  ControlsPatch,
  DataSource,
  EmulatorSourceWorker,
  EngineSnapshot,
  ErrorListener,
  MainToWorkerMessage,
  SampleListener,
  SimulationSample,
  StateListener,
  SynapseControlId,
  SynapseControlsOptions,
  SynapseId,
  TraceField,
  Unsubscribe,
  WorkerToMainMessage,
} from "../src/index.ts";
import { readDevelopmentAsset } from "../tools/serve.mjs";
import { ManualAnimationFrames } from "./helpers/fake-canvas.ts";
import { FakeDocument, FakeElement } from "./helpers/fake-dom.ts";
import { ManualScheduler } from "./helpers/manual-scheduler.ts";

class SynapseDataSource implements DataSource {
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
      modelOptions: { controls: initial, seed: 8675309 },
      scheduler: this.scheduler,
      onSamples: (samples) => this.emitSamples(samples),
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

  run(count: number): SimulationSample[] {
    const samples = this.engine.model.run(count);
    this.engine.history.pushBatch(samples);
    this.emitSamples(samples);
    return samples;
  }

  emitSamples(samples: readonly SimulationSample[]): void {
    for (const listener of this.sampleListeners) {
      listener(samples);
    }
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

function mount(initial: ControlsPatch = {}, options: SynapseControlsOptions = {}): {
  source: SynapseDataSource;
  document: FakeDocument;
  host: FakeElement;
  panel: SpikelingSynapseControls;
} {
  const source = new SynapseDataSource(initial);
  const document = new FakeDocument();
  const host = document.createHost();
  const panel = new SpikelingSynapseControls(host as unknown as HTMLElement, source, options);
  return { source, document, host, panel };
}

function channelElement(host: FakeElement, channel: SynapseId): FakeElement {
  const found = host.findAll(
    (element) => element.className.includes("spk-synapses__channel") && element.dataset.synapse === channel,
  )[0];
  assert.ok(found, "Missing " + channel + " panel");
  return found;
}

function sliderElements(host: FakeElement, channel: SynapseId, id: SynapseControlId): {
  row: FakeElement;
  toggle: FakeElement;
  slider: FakeElement;
  output: FakeElement;
} {
  const row = host.findAll((element) => element.dataset.synapse === channel && element.dataset.control === id)[0];
  assert.ok(row, "Missing " + channel + " " + id);
  const inputs = row.findAll((element) => element.tagName === "input");
  return {
    row,
    toggle: inputs[0],
    slider: inputs[1],
    output: row.findAll((element) => element.tagName === "output")[0],
  };
}

function accessible(host: FakeElement, label: string): FakeElement {
  const found = host.findAll((element) => element.attributes.get("aria-label") === label)[0];
  assert.ok(found, "Missing accessible element " + label);
  return found;
}

test("two desktop synapses retain audited controls, signed patch-current correction and independent decay defaults", () => {
  assert.deepEqual(SYNAPSE_IDS, ["synapse1", "synapse2"]);

  for (const channel of SYNAPSE_IDS) {
    assert.deepEqual(
      SYNAPSE_CONTROL_SPECIFICATIONS[channel].map((control) => [control.id, control.minimum, control.maximum]),
      [
        ["gain", -100, 100],
        ["decay", 975, 1000],
        ["injectedCurrent", -50, 50],
        ["noiseLevel", 0, 100],
        ["photoreceptorGain", -100, 100],
        ["photoreceptorDecay", 10, 125],
        ["photoreceptorRecovery", 1, 100],
      ],
    );
    assert.ok(SYNAPSE_CONTROL_SPECIFICATIONS[channel].every((control) => control.step === 1 && !control.enabledByDefault));
  }

  assert.equal(getSynapseControlSpecification("synapse1", "decay").defaultValue, 995);
  assert.equal(getSynapseControlSpecification("synapse2", "decay").defaultValue, 990);
  assert.equal(getSynapseControlSpecification("synapse1", "gain").desktopWidget, "Emulator_Synapse1_slider");
  assert.equal(getSynapseControlSpecification("synapse2", "injectedCurrent").desktopWidget, "Emulator_Syn2_PatchClamp_slider");
  assert.equal(getSynapseControlSpecification("synapse2", "decay").tickInterval, 2);
});

test("synaptic decay readouts distinguish per-step retention from a physical time constant", () => {
  assert.equal(synapticRetentionFactor(975), 0.975);
  assert.equal(synapticRetentionFactor(995), 0.995);
  assert.equal(synapticRetentionFactor(1000), 1);
  assert.ok(Math.abs(synapticTimeConstantMs(995) - 19.949958228835612) < 1e-12);
  assert.ok(Math.abs(synapticTimeConstantMs(990) - 9.94991624734221) < 1e-12);
  assert.equal(synapticTimeConstantMs(1000), Number.POSITIVE_INFINITY);
  assert.equal(formatSynapseControlValue("synapse1", "decay", 995), "0.995 / step");
  assert.equal(formatSynapseControlValue("synapse2", "decay", 990), "0.990 / step");
});

test("all synaptic and auxiliary controls expose signed values, genuine noise and photoreceptor coefficients", () => {
  assert.equal(formatSynapseControlValue("synapse1", "gain", -35), "-35%");
  assert.equal(formatSynapseControlValue("synapse1", "injectedCurrent", -50), "-50 a.u.");
  assert.equal(formatSynapseControlValue("synapse2", "noiseLevel", 33), "33% · σ 8.25 a.u.");
  assert.equal(formatSynapseControlValue("synapse2", "photoreceptorGain", -80), "-80%");
  assert.equal(formatSynapseControlValue("synapse1", "photoreceptorDecay", 100), "0.001 ms⁻¹");
  assert.equal(formatSynapseControlValue("synapse2", "photoreceptorRecovery", 25), "0.025 ms⁻¹");
});

test("unknown synapses, controls and out-of-range values fail before changing scientific state", () => {
  assert.throws(() => validateSynapseId("synapse3" as SynapseId), /Unknown Spikeling synapse/);
  assert.throws(() => getSynapseControlSpecification("synapse1", "missing" as SynapseControlId), /Unknown synapse control/);
  for (const value of [-51, 51, 0.5, Number.NaN, Number.POSITIVE_INFINITY]) {
    assert.throws(() => validateSynapseControlValue("synapse1", "injectedCurrent", value), RangeError);
  }
  assert.throws(() => synapticRetentionFactor(974), RangeError);
  assert.throws(() => synapticRetentionFactor(1001), RangeError);

  const { source, panel } = mount();
  assert.throws(() => panel.setControlValue("synapse1", "injectedCurrent", 51), RangeError);
  assert.equal(source.patches.length, 0);
});

test("synapse component mounts two semantic, independently labelled auxiliary-neuron panels", () => {
  const { source, host, panel } = mount();
  assert.equal(host.children.length, 1);
  assert.equal(panel.element.className, "spk-controls spk-synapses");
  assert.equal(panel.element.attributes.get("aria-label"), "Virtual presynaptic neuron controls");
  assert.equal(source.sampleListeners.size, 1);
  assert.equal(source.stateListeners.size, 1);

  for (const channel of SYNAPSE_IDS) {
    const number = channel === "synapse1" ? "1" : "2";
    const section = channelElement(host, channel);
    assert.equal(section.dataset.active, "false");
    assert.equal(accessible(section, "Enable Synapse " + number).type, "checkbox");
    const select = accessible(section, "Synapse " + number + " neuron mode");
    assert.equal(select.tagName, "select");
    assert.deepEqual(select.children.map((option) => option.textContent), NEURON_PRESETS.map((preset) => preset.label));

    for (const specification of SYNAPSE_CONTROL_SPECIFICATIONS[channel]) {
      const { toggle, slider, output } = sliderElements(host, channel, specification.id);
      assert.equal(toggle.type, "checkbox");
      assert.equal(slider.type, "range");
      assert.equal(slider.min, String(specification.minimum));
      assert.equal(slider.max, String(specification.maximum));
      assert.equal(slider.step, "1");
      assert.equal(slider.value, String(specification.defaultValue));
      assert.equal(slider.disabled, true);
      assert.equal(output.attributes.get("for"), slider.id);
      assert.ok(slider.attributes.has("aria-label"));
      assert.ok(slider.attributes.has("aria-valuetext"));
    }
  }
});

test("gain and decay remain configurable independently while auxiliary neurons are disabled", () => {
  const { source, host, panel } = mount();
  for (const channel of SYNAPSE_IDS) {
    assert.equal(sliderElements(host, channel, "gain").toggle.disabled, false);
    assert.equal(sliderElements(host, channel, "decay").toggle.disabled, false);
    assert.equal(sliderElements(host, channel, "injectedCurrent").toggle.disabled, true);
  }

  panel.setControlEnabled("synapse1", "gain", true);
  panel.setControlValue("synapse1", "gain", -60);
  panel.setControlEnabled("synapse2", "decay", true);
  panel.setControlValue("synapse2", "decay", 975);
  assert.equal(source.engine.model.getControls().synapse1.gain, -60);
  assert.equal(source.engine.model.getControls().synapse2.decaySlider, 975);
  assert.equal(source.engine.model.getControls().synapse1.enabled, false);
});

test("native master activation enables auxiliary inputs but keeps photoreceptors gated by light", () => {
  const { source, host, panel } = mount();
  const master = accessible(host, "Enable Synapse 1");
  master.checked = true;
  master.dispatch("change");

  assert.equal(panel.isSynapseEnabled("synapse1"), true);
  assert.equal(source.engine.model.getControls().synapse1.enabled, true);
  assert.equal(channelElement(host, "synapse1").dataset.active, "true");
  assert.equal(sliderElements(host, "synapse1", "injectedCurrent").toggle.disabled, false);
  assert.equal(sliderElements(host, "synapse1", "noiseLevel").toggle.disabled, false);
  assert.equal(sliderElements(host, "synapse1", "photoreceptorGain").toggle.disabled, true);
  assert.equal(accessible(host, "Synapse 1 direct current stimulation").disabled, false);
  assert.equal(accessible(host, "Synapse 1 light stimulation").disabled, false);
  assert.equal(panel.isSynapseEnabled("synapse2"), false);
});

test("inactive synapses reject auxiliary current, noise, light and direct-current activation", () => {
  const { source, panel } = mount();
  assert.throws(() => panel.setControlEnabled("synapse1", "injectedCurrent", true), /Enable Synapse 1/);
  assert.throws(() => panel.setControlEnabled("synapse2", "noiseLevel", true), /Enable Synapse 2/);
  assert.throws(() => panel.setDirectCurrentEnabled("synapse1", true), /before direct current/);
  assert.throws(() => panel.setLightEnabled("synapse2", true), /before light stimulation/);
  assert.equal(source.patches.length, 0);
});

test("signed auxiliary patch sliders correct the Qt 0–100 defect for both channels", () => {
  const { source, host, panel } = mount();
  for (const [channel, current] of [["synapse1", -50], ["synapse2", 50]] as const) {
    panel.setSynapseEnabled(channel, true);
    panel.setControlEnabled(channel, "injectedCurrent", true);
    const slider = sliderElements(host, channel, "injectedCurrent");
    slider.slider.value = String(current);
    slider.slider.dispatch("input");
    assert.equal(source.engine.model.getControls()[channel].patchCurrent, current);
    assert.equal(slider.output.textContent, current + " a.u.");
  }
});

test("switching an auxiliary slider off restores its exact desktop default", () => {
  const { source, panel } = mount();
  panel.setSynapseEnabled("synapse1", true);
  panel.setLightEnabled("synapse1", true);

  for (const [id, value, expected] of [
    ["gain", -70, 0],
    ["decay", 978, 995],
    ["injectedCurrent", -35, 0],
    ["noiseLevel", 40, 0],
    ["photoreceptorGain", 25, 0],
    ["photoreceptorDecay", 60, 100],
    ["photoreceptorRecovery", 80, 25],
  ] as const) {
    panel.setControlEnabled("synapse1", id, true);
    panel.setControlValue("synapse1", id, value);
    panel.setControlEnabled("synapse1", id, false);
    const state = source.engine.model.getControls().synapse1;
    const actual =
      id === "gain" ? state.gain :
      id === "decay" ? state.decaySlider :
      id === "injectedCurrent" ? state.patchCurrent :
      id === "noiseLevel" ? state.noiseLevel :
      id === "photoreceptorGain" ? state.photoreceptor.gain :
      id === "photoreceptorDecay" ? state.photoreceptor.decaySlider :
      state.photoreceptor.recoverySlider;
    assert.equal(actual, expected);
  }

  panel.setControlEnabled("synapse2", "decay", true);
  panel.setControlValue("synapse2", "decay", 1000);
  panel.setControlEnabled("synapse2", "decay", false);
  assert.equal(source.engine.model.getControls().synapse2.decaySlider, 990);
});

test("native gain toggles and slider fills preserve signed inhibitory settings", () => {
  const { source, host, panel } = mount();
  const gain = sliderElements(host, "synapse2", "gain");
  gain.toggle.checked = true;
  gain.toggle.dispatch("change");
  assert.equal(panel.isControlEnabled("synapse2", "gain"), true);
  gain.slider.value = "-60";
  gain.slider.dispatch("input");
  assert.equal(source.engine.model.getControls().synapse2.gain, -60);
  assert.equal(gain.slider.style.values.get("--spk-fill"), "20%");
  assert.equal(gain.output.textContent, "-60%");
});

test("synaptic retention readouts expose the equivalent time constant to assistive technologies", () => {
  const { host, panel } = mount();
  panel.setControlEnabled("synapse1", "decay", true);
  let decay = sliderElements(host, "synapse1", "decay");
  assert.equal(decay.output.textContent, "0.995 / step");
  assert.equal(decay.output.attributes.get("title"), "τ 19.95 ms");
  assert.equal(decay.slider.attributes.get("aria-valuetext"), "0.995 / step; τ 19.95 ms");

  panel.setControlValue("synapse1", "decay", 1000);
  decay = sliderElements(host, "synapse1", "decay");
  assert.equal(decay.output.attributes.get("title"), "no decay");
  assert.equal(decay.slider.attributes.get("aria-valuetext"), "1.000 / step; no decay");
});

test("all twenty presynaptic modes update independent a, b, c, d and resting-voltage displays", () => {
  const { source, host, panel } = mount();
  for (const preset of NEURON_PRESETS) {
    panel.selectPreset("synapse1", preset.id);
    const values = channelElement(host, "synapse1").findAll(
      (element) => element.className === "spk-controls__parameter-value",
    );
    assert.deepEqual(values.map((element) => element.textContent), [
      String(preset.a).replace("-", "−"),
      String(preset.b).replace("-", "−"),
      String(preset.c).replace("-", "−") + " mV",
      String(preset.d).replace("-", "−"),
      String(preset.restingPotential).replace("-", "−") + " mV",
    ]);
  }
  assert.equal(source.engine.model.getControls().synapse1.presetId, 20);
  assert.equal(source.engine.model.getControls().synapse2.presetId, 1);

  const selector = accessible(host, "Synapse 2 neuron mode");
  selector.value = "11";
  selector.dispatch("change");
  assert.equal(source.engine.model.getControls().synapse2.presetId, 11);
  assert.equal(source.engine.model.getControls().synapse1.presetId, 20);
});

test("changing one presynaptic mode resets only its photoreceptor while preserving neuronal state", () => {
  const { source, panel } = mount({
    synapse1: {
      enabled: true,
      patchCurrent: 38,
      gain: 25,
      decaySlider: 985,
      lightEnabled: true,
      photoreceptor: { gain: 15, decaySlider: 77, recoverySlider: 60 },
    },
    synapse2: { presetId: 9, gain: -44, decaySlider: 975 },
  });
  source.run(25);
  const hidden = source.engine.model.getState().synapse1.neuron;
  const step = source.engine.model.getState().stepIndex;

  panel.selectPreset("synapse1", 14);
  const controls = source.engine.model.getControls();
  assert.deepEqual(source.engine.model.getState().synapse1.neuron, hidden);
  assert.equal(source.engine.model.getState().stepIndex, step);
  assert.equal(controls.synapse1.presetId, 14);
  assert.equal(controls.synapse1.patchCurrent, 38);
  assert.equal(controls.synapse1.gain, 25);
  assert.equal(controls.synapse1.decaySlider, 985);
  assert.deepEqual(controls.synapse1.photoreceptor, { gain: 0, decaySlider: 100, recoverySlider: 25 });
  assert.equal(controls.synapse2.presetId, 9);
  assert.equal(controls.synapse2.gain, -44);
});

test("direct-current stimulation is routed independently to each presynaptic neuron", () => {
  const { source, host, panel } = mount({ stimulus: { strength: 21 } });
  panel.setSynapseEnabled("synapse1", true);
  panel.setSynapseEnabled("synapse2", true);
  const direct = accessible(host, "Synapse 1 direct current stimulation");
  direct.checked = true;
  direct.dispatch("change");

  source.run(1);
  assert.equal(source.engine.model.getState().synapse1.neuron.totalCurrent, 21);
  assert.equal(source.engine.model.getState().synapse2.neuron.totalCurrent, 0);

  panel.setDirectCurrentEnabled("synapse2", true);
  source.run(1);
  assert.equal(source.engine.model.getState().synapse1.neuron.totalCurrent, 21);
  assert.equal(source.engine.model.getState().synapse2.neuron.totalCurrent, 21);
});

test("photoreceptor controls become available only when their own light stimulation is enabled", () => {
  const { source, host, panel } = mount();
  panel.setSynapseEnabled("synapse1", true);
  assert.throws(() => panel.setControlEnabled("synapse1", "photoreceptorGain", true), /Enable light stimulation/);

  const light = accessible(host, "Synapse 1 light stimulation");
  light.checked = true;
  light.dispatch("change");
  for (const id of ["photoreceptorGain", "photoreceptorDecay", "photoreceptorRecovery"] as const) {
    assert.equal(sliderElements(host, "synapse1", id).toggle.disabled, false);
  }
  panel.setControlEnabled("synapse1", "photoreceptorGain", true);
  panel.setControlValue("synapse1", "photoreceptorGain", -45);
  panel.setControlEnabled("synapse1", "photoreceptorDecay", true);
  panel.setControlValue("synapse1", "photoreceptorDecay", 65);
  panel.setControlEnabled("synapse1", "photoreceptorRecovery", true);
  panel.setControlValue("synapse1", "photoreceptorRecovery", 89);
  assert.deepEqual(source.engine.model.getControls().synapse1.photoreceptor, {
    gain: -45,
    decaySlider: 65,
    recoverySlider: 89,
  });
  assert.deepEqual(source.engine.model.getControls().synapse2.photoreceptor, defaultControls().synapse2.photoreceptor);
});

test("turning off light atomically disables its three photo controls and restores desktop defaults", () => {
  const { source, host, panel } = mount({
    synapse2: {
      enabled: true,
      lightEnabled: true,
      photoreceptor: { gain: 44, decaySlider: 55, recoverySlider: 66 },
    },
  });

  panel.setLightEnabled("synapse2", false);
  assert.equal(source.engine.model.getControls().synapse2.lightEnabled, false);
  assert.deepEqual(source.engine.model.getControls().synapse2.photoreceptor, {
    gain: 0,
    decaySlider: 100,
    recoverySlider: 25,
  });
  for (const id of ["photoreceptorGain", "photoreceptorDecay", "photoreceptorRecovery"] as const) {
    assert.equal(panel.isControlEnabled("synapse2", id), false);
    assert.equal(sliderElements(host, "synapse2", id).toggle.disabled, true);
  }
});

test("independent presynaptic photoreceptors transform the shared stimulus without cross-talk", () => {
  const { source, panel } = mount({ stimulus: { strength: 30 } });
  panel.setSynapseEnabled("synapse1", true);
  panel.setSynapseEnabled("synapse2", true);
  panel.setLightEnabled("synapse1", true);
  panel.setLightEnabled("synapse2", true);
  panel.setControlEnabled("synapse1", "photoreceptorGain", true);
  panel.setControlEnabled("synapse2", "photoreceptorGain", true);
  panel.setControlValue("synapse1", "photoreceptorGain", 50);
  panel.setControlValue("synapse2", "photoreceptorGain", -50);
  source.run(3);

  const state = source.engine.model.getState();
  assert.ok(state.synapse1.neuron.totalCurrent > 0);
  assert.ok(state.synapse2.neuron.totalCurrent < 0);
  assert.equal(state.synapse1.neuron.totalCurrent, -state.synapse2.neuron.totalCurrent);
});

test("noise sliders retain independent seeded Gaussian scales in both auxiliary neurons", () => {
  const { source, panel } = mount();
  panel.setSynapseEnabled("synapse1", true);
  panel.setSynapseEnabled("synapse2", true);
  panel.setControlEnabled("synapse1", "noiseLevel", true);
  panel.setControlEnabled("synapse2", "noiseLevel", true);
  panel.setControlValue("synapse1", "noiseLevel", 20);
  panel.setControlValue("synapse2", "noiseLevel", 60);

  const direct = new SpikelingModel({ controls: source.engine.model.getControls(), seed: 8675309 });
  const actual = source.run(30);
  const expected = direct.run(30);
  assert.deepEqual(actual, expected);
  assert.notEqual(source.engine.model.getState().synapse1.neuron.totalCurrent, source.engine.model.getState().synapse2.neuron.totalCurrent);
});

test("positive and negative synaptic gains produce excitatory and inhibitory main-neuron inputs", () => {
  const { source, panel } = mount();
  for (const [channel, gain, current] of [["synapse1", 30, 45], ["synapse2", -24, 43]] as const) {
    panel.setSynapseEnabled(channel, true);
    panel.setControlEnabled(channel, "gain", true);
    panel.setControlValue(channel, "gain", gain);
    panel.setControlEnabled(channel, "injectedCurrent", true);
    panel.setControlValue(channel, "injectedCurrent", current);
  }

  const samples = source.run(900);
  assert.ok(samples.some((sample) => sample.synapse1Current > 0));
  assert.ok(samples.some((sample) => sample.synapse2Current < 0));
  assert.ok(samples.some((sample) => sample.synapse1Current !== 0 && sample.synapse2Current !== 0));
  for (const sample of samples) {
    assert.ok(Math.abs(sample.totalCurrent - sample.synapse1Current - sample.synapse2Current) < 1e-10);
  }
});

test("two active synapses sum currents algebraically without changing fixed integration timing", () => {
  const { source, panel } = mount({ main: { patchCurrent: 4 } });
  panel.setSynapseEnabled("synapse1", true);
  panel.setSynapseEnabled("synapse2", true);
  panel.setControlEnabled("synapse1", "gain", true);
  panel.setControlEnabled("synapse2", "gain", true);
  panel.setControlValue("synapse1", "gain", 17);
  panel.setControlValue("synapse2", "gain", -13);
  panel.setControlEnabled("synapse1", "injectedCurrent", true);
  panel.setControlEnabled("synapse2", "injectedCurrent", true);
  panel.setControlValue("synapse1", "injectedCurrent", 48);
  panel.setControlValue("synapse2", "injectedCurrent", 46);
  const samples = source.run(700);

  for (const [index, sample] of samples.entries()) {
    assert.equal(sample.timeMs, index * 0.1);
    assert.ok(Math.abs(sample.totalCurrent - (4 + sample.synapse1Current + sample.synapse2Current)) < 1e-10);
  }
});

test("Synapse 2 uses its own selected decay rather than the desktop's hard-coded 0.995 defect", () => {
  const { source, panel } = mount();
  panel.setSynapseEnabled("synapse2", true);
  panel.setControlEnabled("synapse2", "gain", true);
  panel.setControlValue("synapse2", "gain", 20);
  panel.setControlEnabled("synapse2", "injectedCurrent", true);
  panel.setControlValue("synapse2", "injectedCurrent", 45);
  panel.setControlEnabled("synapse2", "decay", true);
  panel.setControlValue("synapse2", "decay", 980);

  const firstSpike = source.run(700).find((sample) => sample.synapse2Current !== 0);
  assert.ok(firstSpike);
  assert.equal(firstSpike.synapse2Current, 20 * 0.98);
  assert.notEqual(firstSpike.synapse2Current, 20 * 0.995);
});

test("changing Synapse 2 decay does not alter Synapse 1 dynamics or selected retention", () => {
  const initial: ControlsPatch = {
    synapse1: { enabled: true, patchCurrent: 42, gain: 15, decaySlider: 987 },
    synapse2: { enabled: true, patchCurrent: 44, gain: -9, decaySlider: 990 },
  };
  const { source, panel } = mount(initial);
  const direct = new SpikelingModel({ controls: initial, seed: 8675309 });
  panel.setControlEnabled("synapse2", "decay", true);
  panel.setControlValue("synapse2", "decay", 975);
  direct.updateControls({ synapse2: { decaySlider: 975 } });

  assert.deepEqual(source.run(400), direct.run(400));
  assert.equal(source.engine.model.getControls().synapse1.decaySlider, 987);
});

test("maximum-retention synapses do not decay between presynaptic spikes", () => {
  const { source, panel } = mount();
  panel.setSynapseEnabled("synapse1", true);
  panel.setControlEnabled("synapse1", "gain", true);
  panel.setControlValue("synapse1", "gain", 12);
  panel.setControlEnabled("synapse1", "decay", true);
  panel.setControlValue("synapse1", "decay", 1000);
  panel.setControlEnabled("synapse1", "injectedCurrent", true);
  panel.setControlValue("synapse1", "injectedCurrent", 45);

  const samples = source.run(600);
  const index = samples.findIndex((sample) => sample.synapse1Current !== 0);
  assert.ok(index >= 0);
  assert.equal(samples[index].synapse1Current, 12);
  assert.equal(samples[index + 1].synapse1Current, 12);
});

test("disabling a presynaptic neuron clears output while retaining hidden voltage and recovery state", () => {
  const { source, panel } = mount();
  panel.setSynapseEnabled("synapse1", true);
  panel.setControlEnabled("synapse1", "gain", true);
  panel.setControlValue("synapse1", "gain", 25);
  panel.setControlEnabled("synapse1", "decay", true);
  panel.setControlValue("synapse1", "decay", 985);
  panel.setControlEnabled("synapse1", "injectedCurrent", true);
  panel.setControlValue("synapse1", "injectedCurrent", 45);
  source.run(250);
  const hidden = source.engine.model.getState().synapse1.neuron;

  panel.setSynapseEnabled("synapse1", false);
  assert.deepEqual(source.engine.model.getState().synapse1.neuron, hidden);
  const sample = source.run(1)[0];
  assert.equal(sample.synapse1Vm, 0);
  assert.equal(sample.synapse1Current, 0);
  assert.deepEqual(source.engine.model.getState().synapse1.neuron, hidden);
  assert.equal(source.engine.model.getControls().synapse1.gain, 25);
  assert.equal(source.engine.model.getControls().synapse1.decaySlider, 985);
});

test("master deactivation resets auxiliary routing/noise/photo settings but retains independent output controls", () => {
  const { source, host, panel } = mount({
    synapse2: {
      enabled: true,
      gain: -31,
      decaySlider: 977,
      patchCurrent: -23,
      noiseLevel: 42,
      directCurrentEnabled: true,
      lightEnabled: true,
      photoreceptor: { gain: -18, decaySlider: 44, recoverySlider: 80 },
    },
  });

  const master = accessible(host, "Enable Synapse 2");
  master.checked = false;
  master.dispatch("change");
  const controls = source.engine.model.getControls().synapse2;
  assert.equal(controls.enabled, false);
  assert.equal(controls.patchCurrent, 0);
  assert.equal(controls.noiseLevel, 0);
  assert.equal(controls.directCurrentEnabled, false);
  assert.equal(controls.lightEnabled, false);
  assert.deepEqual(controls.photoreceptor, { gain: 0, decaySlider: 100, recoverySlider: 25 });
  assert.equal(controls.gain, -31);
  assert.equal(controls.decaySlider, 977);
  assert.equal(panel.isControlEnabled("synapse2", "injectedCurrent"), false);
  assert.equal(panel.isControlEnabled("synapse2", "photoreceptorGain"), false);
  assert.equal(sliderElements(host, "synapse2", "injectedCurrent").toggle.disabled, true);
});

test("connected-source snapshots restore active channel settings without overwriting independent defaults", () => {
  const { host, panel } = mount({
    synapse1: {
      enabled: true,
      presetId: 18,
      gain: 22,
      decaySlider: 976,
      patchCurrent: -19,
      noiseLevel: 12,
      lightEnabled: true,
      photoreceptor: { gain: 55, decaySlider: 80 },
    },
    synapse2: { gain: -27, decaySlider: 1000 },
  });

  assert.equal(panel.isSynapseEnabled("synapse1"), true);
  assert.equal(panel.getControls("synapse1").presetId, 18);
  assert.equal(panel.isControlEnabled("synapse1", "injectedCurrent"), true);
  assert.equal(panel.isControlEnabled("synapse1", "photoreceptorGain"), true);
  assert.equal(panel.isControlEnabled("synapse2", "gain"), true);
  assert.equal(panel.isControlEnabled("synapse2", "decay"), true);
  assert.equal(sliderElements(host, "synapse1", "injectedCurrent").slider.value, "-19");
  assert.equal(sliderElements(host, "synapse2", "decay").output.textContent, "1.000 / step");
});

test("disconnected panels initialise safely and reconcile channel state after source connection", async () => {
  const source = new SynapseDataSource({ synapse2: { enabled: true, patchCurrent: 23 } }, false);
  const host = new FakeDocument().createHost();
  const panel = new SpikelingSynapseControls(host as unknown as HTMLElement, source);
  assert.equal(panel.isSynapseEnabled("synapse2"), false);
  await source.connect();
  assert.equal(panel.isSynapseEnabled("synapse2"), true);
  assert.equal(panel.getControls("synapse2").patchCurrent, 23);
});

test("external worker snapshots update only the targeted synaptic controls", () => {
  const { source, host, panel } = mount();
  source.updateControls({ synapse1: { gain: 44, decaySlider: 982 }, synapse2: { gain: -55 } });
  assert.equal(panel.getControls("synapse1").gain, 44);
  assert.equal(sliderElements(host, "synapse1", "gain").output.textContent, "44%");
  assert.equal(sliderElements(host, "synapse1", "decay").output.textContent, "0.982 / step");
  assert.equal(sliderElements(host, "synapse2", "gain").output.textContent, "-55%");
  assert.equal(panel.getControls("synapse2").decaySlider, 990);
});

test("live scientific readings track genuine presynaptic membrane voltage and signed output", () => {
  const { source, host } = mount({ synapse1: { enabled: true, patchCurrent: 45, gain: -20 } });
  const reading = channelElement(host, "synapse1").findAll(
    (element) => element.className === "spk-synapses__reading",
  )[0];
  assert.equal(reading.textContent, "Ready · Vm — mV · output 0.0 a.u.");
  const samples = source.run(500);
  const last = samples.at(-1)!;
  assert.match(reading.textContent, /^Vm −?[\d.]+ mV · output −?[\d.]+ a\.u\.$/);
  assert.match(reading.textContent, new RegExp(last.synapse1Current.toFixed(2).replace("-", "−").replace(".", "\\.")));
  source.emitSamples([]);
  assert.match(reading.textContent, /^Vm /);

  source.stop();
  assert.match(reading.textContent, /Ready · Vm — mV/);
});

test("enabling or disabling channels reveals only their matching oscilloscope voltage/current traces", () => {
  const source = new SynapseDataSource();
  const document = new FakeDocument();
  const scopeHost = document.createHost();
  const frames = new ManualAnimationFrames();
  const scope = new SpikelingOscilloscope(scopeHost as unknown as HTMLElement, source, { frameScheduler: frames });
  const host = document.createHost();
  const panel = new SpikelingSynapseControls(host as unknown as HTMLElement, source, { oscilloscope: scope });

  assert.equal(scope.isTraceVisible("synapse1Vm"), false);
  assert.equal(scope.isTraceVisible("synapse1Current"), false);
  panel.setSynapseEnabled("synapse1", true);
  assert.equal(scope.isTraceVisible("synapse1Vm"), true);
  assert.equal(scope.isTraceVisible("synapse1Current"), true);
  assert.equal(scope.isTraceVisible("synapse2Vm"), false);

  panel.setSynapseEnabled("synapse2", true);
  assert.equal(scope.isTraceVisible("synapse2Vm"), true);
  assert.equal(scope.isTraceVisible("synapse2Current"), true);
  panel.setSynapseEnabled("synapse1", false);
  assert.equal(scope.isTraceVisible("synapse1Vm"), false);
  assert.equal(scope.isTraceVisible("synapse1Current"), false);
  assert.equal(scope.isTraceVisible("synapse2Vm"), true);
  assert.equal(scope.isTraceVisible("synapse2Current"), true);
});

test("automatic trace changes can be disabled while preserving manual oscilloscope ownership", () => {
  const calls: Array<[TraceField, boolean]> = [];
  const scope = { setTraceVisible: (field: TraceField, visible: boolean) => calls.push([field, visible]) };
  const { panel } = mount({}, { oscilloscope: scope, autoShowTraces: false });
  panel.setSynapseEnabled("synapse1", true);
  panel.setSynapseEnabled("synapse2", true);
  assert.deepEqual(calls, []);
});

test("initially active worker synapses reveal their matching traces immediately", () => {
  const calls: Array<[TraceField, boolean]> = [];
  const scope = { setTraceVisible: (field: TraceField, visible: boolean) => calls.push([field, visible]) };
  mount({ synapse2: { enabled: true } }, { oscilloscope: scope });
  assert.deepEqual(calls, [["synapse2Vm", true], ["synapse2Current", true]]);
});

test("main-neuron and both synapse panels coexist without cross-channel state mutation", () => {
  const source = new SynapseDataSource();
  const document = new FakeDocument();
  const mainHost = document.createHost();
  const synapseHost = document.createHost();
  const main = new SpikelingMainControls(mainHost as unknown as HTMLElement, source);
  const synapses = new SpikelingSynapseControls(synapseHost as unknown as HTMLElement, source);

  main.selectPreset(12);
  main.setControlEnabled("injectedCurrent", true);
  main.setControlValue("injectedCurrent", 28);
  synapses.setSynapseEnabled("synapse1", true);
  synapses.selectPreset("synapse1", 17);
  synapses.setControlEnabled("synapse1", "injectedCurrent", true);
  synapses.setControlValue("synapse1", "injectedCurrent", -11);
  synapses.setSynapseEnabled("synapse2", true);
  synapses.selectPreset("synapse2", 9);

  const controls = source.engine.model.getControls();
  assert.equal(controls.main.presetId, 12);
  assert.equal(controls.main.patchCurrent, 28);
  assert.equal(controls.synapse1.presetId, 17);
  assert.equal(controls.synapse1.patchCurrent, -11);
  assert.equal(controls.synapse2.presetId, 9);
  assert.equal(controls.synapse2.patchCurrent, 0);
  assert.equal(MAIN_CONTROL_SPECIFICATIONS.length, 7);
  assert.equal(source.stateListeners.size, 2);
});

test("rapid two-channel parameter changes never reset scientific simulation time", () => {
  const { source, panel } = mount();
  panel.setSynapseEnabled("synapse1", true);
  panel.setSynapseEnabled("synapse2", true);
  panel.setControlEnabled("synapse1", "injectedCurrent", true);
  panel.setControlEnabled("synapse2", "injectedCurrent", true);
  source.start();
  source.scheduler.advance(50);
  const step = source.engine.getSnapshot().stepIndex;

  for (let index = 0; index < 300; index += 1) {
    panel.setControlValue("synapse1", "injectedCurrent", (index % 101) - 50);
    panel.setControlValue("synapse2", "injectedCurrent", 50 - (index % 101));
  }

  assert.equal(source.engine.getSnapshot().stepIndex, step);
  assert.equal(source.engine.getSnapshot().lifecycle, "running");
  assert.equal(source.engine.model.getControls().synapse1.patchCurrent, (299 % 101) - 50);
  assert.equal(source.engine.model.getControls().synapse2.patchCurrent, 50 - (299 % 101));
});

test("worker-backed synapses produce simultaneous signed full-resolution traces through the existing protocol", async () => {
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
  const source = new EmulatorSource({ workerFactory: () => worker, speedIndex: 5 });
  const host = new FakeDocument().createHost();
  const panel = new SpikelingSynapseControls(host as unknown as HTMLElement, source);
  await source.connect();

  for (const [channel, gain, current, decay] of [["synapse1", 20, 45, 995], ["synapse2", -15, 44, 980]] as const) {
    panel.setSynapseEnabled(channel, true);
    panel.setControlEnabled(channel, "gain", true);
    panel.setControlValue(channel, "gain", gain);
    panel.setControlEnabled(channel, "injectedCurrent", true);
    panel.setControlValue(channel, "injectedCurrent", current);
    panel.setControlEnabled(channel, "decay", true);
    panel.setControlValue(channel, "decay", decay);
  }

  source.start();
  scheduler.advance(50);
  const samples = source.latest();
  assert.equal(samples.length, 500);
  assert.ok(samples.some((sample) => sample.synapse1Current > 0));
  assert.ok(samples.some((sample) => sample.synapse2Current < 0));
  assert.equal(source.getSnapshot()?.controls.synapse2.decaySlider, 980);
  assert.ok(samples.every((sample, index) => sample.timeMs === index * 0.1));

  panel.dispose();
  await source.disconnect();
});

test("local preview serves independently scoped cyan/magenta Phase 5 styles and native modules", async () => {
  const page = await readDevelopmentAsset("/");
  const stylesheet = await readDevelopmentAsset("/src/styles/synapses.css");
  const module = await readDevelopmentAsset("/src/controls/synapse-controls.ts");

  assert.equal(page.status, 200);
  assert.match(page.content, /Local Phase 7 preview/);
  assert.match(page.content, /id="emulator"/);
  assert.match(page.content, /src\/styles\/synapses\.css/);
  assert.equal(stylesheet.status, 200);
  assert.match(stylesheet.contentType, /^text\/css/);
  assert.match(stylesheet.content, /#2aa198/i);
  assert.match(stylesheet.content, /#d33682/i);
  assert.match(stylesheet.content, /max-width: 700px/);
  assert.doesNotMatch(stylesheet.content, /(?:^|\n)\s*(?:html|body|\*)\s*\{/);
  assert.equal(module.status, 200);
  assert.match(module.contentType, /^text\/javascript/);
  assert.match(module.content, /class SpikelingSynapseControls/);
});

test("source errors are reported accessibly and cleared by a subsequent valid synapse update", () => {
  const { source, host, panel } = mount();
  const alert = host.findAll((element) => element.attributes.get("role") === "alert")[0];
  source.emitError(new Error("Synaptic worker failure"));
  assert.equal(alert.textContent, "Synaptic worker failure");
  panel.setControlEnabled("synapse1", "gain", true);
  assert.equal(alert.textContent, "");
});

test("returned synaptic control snapshots cannot mutate worker-owned state", () => {
  const { source, panel } = mount({ synapse2: { gain: -23 } });
  const copied = panel.getControls("synapse2");
  copied.gain = 99;
  assert.equal(panel.getControls("synapse2").gain, -23);
  assert.equal(source.engine.model.getControls().synapse2.gain, -23);
});

test("synapse panel disposal is idempotent and removes sample, state and error subscriptions", () => {
  const { source, host, panel } = mount();
  assert.equal(source.sampleListeners.size, 1);
  assert.equal(source.stateListeners.size, 1);
  assert.equal(source.errorListeners.size, 1);

  panel.dispose();
  panel.dispose();
  assert.equal(host.children.length, 0);
  assert.equal(source.sampleListeners.size, 0);
  assert.equal(source.stateListeners.size, 0);
  assert.equal(source.errorListeners.size, 0);
});
