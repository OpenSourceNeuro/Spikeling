// SPDX-License-Identifier: GPL-3.0-or-later

import type { DataSource, Unsubscribe } from "../data-source/DataSource.ts";
import { defaultControls } from "../model/controls.ts";
import { getPreset, NEURON_PRESETS } from "../model/presets.ts";
import type {
  ControlsPatch,
  NeuronPreset,
  SimulationControls,
  SimulationSample,
  SynapseControls,
  SynapsePatch,
} from "../model/types.ts";
import type { EngineSnapshot } from "../simulation/protocol.ts";
import type { TraceField } from "../visualisation/traces.ts";
import {
  SYNAPSE_CONTROL_SPECIFICATIONS,
  SYNAPSE_IDS,
  formatSynapseControlValue,
  getSynapseControlSpecification,
  synapticTimeConstantMs,
  validateSynapseControlValue,
  validateSynapseId,
} from "./synapse-specifications.ts";
import type {
  SynapseControlId,
  SynapseControlSpecification,
  SynapseId,
} from "./synapse-specifications.ts";

export interface SynapseTraceController {
  setTraceVisible(field: TraceField, visible: boolean): void;
}

export interface SynapseControlsOptions {
  readonly oscilloscope?: SynapseTraceController;
  readonly autoShowTraces?: boolean;
}

interface SynapseSliderElements {
  readonly specification: SynapseControlSpecification;
  readonly row: HTMLElement;
  readonly toggle: HTMLInputElement;
  readonly slider: HTMLInputElement;
  readonly output: HTMLOutputElement;
}

interface SynapseElements {
  readonly channel: SynapseId;
  readonly element: HTMLElement;
  readonly master: HTMLInputElement;
  readonly selector: HTMLSelectElement;
  readonly parameters: HTMLElement;
  readonly directCurrent: HTMLInputElement;
  readonly light: HTMLInputElement;
  readonly reading: HTMLElement;
  readonly controls: Map<SynapseControlId, SynapseSliderElements>;
  readonly enabled: Map<SynapseControlId, boolean>;
}

let synapseInstanceCount = 0;

function element<K extends keyof HTMLElementTagNameMap>(
  owner: Document,
  tag: K,
  className: string,
  text?: string,
): HTMLElementTagNameMap[K] {
  const created = owner.createElement(tag);
  created.className = className;
  if (text !== undefined) {
    created.textContent = text;
  }
  return created;
}

function channelNumber(channel: SynapseId): string {
  return channel === "synapse1" ? "1" : "2";
}

function photoControl(id: SynapseControlId): boolean {
  return id === "photoreceptorGain" || id === "photoreceptorDecay" || id === "photoreceptorRecovery";
}

function independentControl(id: SynapseControlId): boolean {
  return id === "gain" || id === "decay";
}

function scientificNumber(value: number, digits = 1): string {
  return value.toFixed(digits).replace("-", "−");
}

/** Two desktop-faithful auxiliary neurons and their independent signed synaptic outputs. */
export class SpikelingSynapseControls {
  readonly element: HTMLElement;

  private readonly owner: Document;
  private readonly source: DataSource;
  private readonly options: SynapseControlsOptions;
  private readonly instancePrefix: string;
  private readonly channels = new Map<SynapseId, SynapseElements>();
  private readonly subscriptions: Unsubscribe[] = [];
  private readonly error: HTMLElement;
  private current = defaultControls();
  private latestSample: SimulationSample | undefined;
  private disposed = false;

  constructor(host: HTMLElement, source: DataSource, options: SynapseControlsOptions = {}) {
    this.owner = host.ownerDocument;
    this.source = source;
    this.options = options;
    synapseInstanceCount += 1;
    this.instancePrefix = "spk-synapses-" + synapseInstanceCount + "-";
    this.element = element(this.owner, "section", "spk-controls spk-synapses");
    this.element.setAttribute("aria-label", "Virtual presynaptic neuron controls");

    for (const channel of SYNAPSE_IDS) {
      this.buildChannel(channel);
    }

    this.error = element(this.owner, "p", "spk-controls__error spk-synapses__error");
    this.error.setAttribute("role", "alert");
    this.element.append(this.error);
    host.append(this.element);

    this.synchronise(defaultControls(), true);
    this.subscriptions.push(
      source.subscribe((samples) => this.handleSamples(samples)),
      source.subscribeState((snapshot) => this.handleSnapshot(snapshot)),
      source.subscribeErrors((failure) => this.showError(failure)),
    );
  }

  getControls(channel: SynapseId): SynapseControls {
    return structuredClone(this.current[validateSynapseId(channel)]);
  }

  isSynapseEnabled(channel: SynapseId): boolean {
    return this.current[validateSynapseId(channel)].enabled;
  }

  isControlEnabled(channel: SynapseId, id: SynapseControlId): boolean {
    getSynapseControlSpecification(channel, id);
    return this.channels.get(channel)!.enabled.get(id) ?? false;
  }

  setSynapseEnabled(channel: SynapseId, active: boolean): void {
    const references = this.channel(channel);
    references.master.checked = active;

    if (active) {
      this.applyPatch(channel, { enabled: true });
      return;
    }

    for (const id of [
      "injectedCurrent",
      "noiseLevel",
      "photoreceptorGain",
      "photoreceptorDecay",
      "photoreceptorRecovery",
    ] as const) {
      references.enabled.set(id, false);
    }

    this.applyPatch(channel, {
      enabled: false,
      patchCurrent: 0,
      noiseLevel: 0,
      directCurrentEnabled: false,
      lightEnabled: false,
      photoreceptor: { gain: 0, decaySlider: 100, recoverySlider: 25 },
    });
  }

  selectPreset(channel: SynapseId, identifier: number): void {
    const references = this.channel(channel);
    const preset = getPreset(identifier);
    for (const id of ["photoreceptorGain", "photoreceptorDecay", "photoreceptorRecovery"] as const) {
      references.enabled.set(id, false);
    }
    references.selector.value = String(preset.id);
    this.updateParameters(references, preset);
    this.applyPatch(channel, {
      presetId: preset.id,
      photoreceptor: { gain: 0, decaySlider: 100, recoverySlider: 25 },
    });
  }

  setControlEnabled(channel: SynapseId, id: SynapseControlId, active: boolean): void {
    const references = this.channel(channel);
    const specification = getSynapseControlSpecification(channel, id);
    if (active && !independentControl(id) && !this.current[channel].enabled) {
      throw new RangeError("Enable Synapse " + channelNumber(channel) + " before adjusting its auxiliary neuron.");
    }
    if (active && photoControl(id) && !this.current[channel].lightEnabled) {
      throw new RangeError("Enable light stimulation before adjusting photoreceptor controls.");
    }

    const slider = references.controls.get(id)!;
    references.enabled.set(id, active);
    slider.toggle.checked = active;
    if (!active) {
      slider.slider.value = String(specification.defaultValue);
      this.updateSlider(references, slider, specification.defaultValue);
    }

    this.updateAvailability(references);
    this.applyPatch(channel, this.controlPatch(id, Number(slider.slider.value)));
  }

  setControlValue(channel: SynapseId, id: SynapseControlId, value: number): void {
    const references = this.channel(channel);
    const valid = validateSynapseControlValue(channel, id, value);
    const slider = references.controls.get(id)!;
    slider.slider.value = String(valid);
    this.updateSlider(references, slider, valid);
    this.applyPatch(channel, this.controlPatch(id, valid));
  }

  setDirectCurrentEnabled(channel: SynapseId, active: boolean): void {
    this.requireActive(channel, "direct current stimulation");
    const references = this.channel(channel);
    references.directCurrent.checked = active;
    this.applyPatch(channel, { directCurrentEnabled: active });
  }

  setLightEnabled(channel: SynapseId, active: boolean): void {
    this.requireActive(channel, "light stimulation");
    const references = this.channel(channel);
    references.light.checked = active;
    if (active) {
      this.applyPatch(channel, { lightEnabled: true });
      return;
    }

    for (const id of ["photoreceptorGain", "photoreceptorDecay", "photoreceptorRecovery"] as const) {
      references.enabled.set(id, false);
    }
    this.applyPatch(channel, {
      lightEnabled: false,
      photoreceptor: { gain: 0, decaySlider: 100, recoverySlider: 25 },
    });
  }

  dispose(): void {
    if (this.disposed) {
      return;
    }
    this.disposed = true;
    for (const unsubscribe of this.subscriptions) {
      unsubscribe();
    }
    this.element.remove();
  }

  private buildChannel(channel: SynapseId): void {
    const number = channelNumber(channel);
    const root = element(this.owner, "section", "spk-controls__group spk-synapses__channel");
    root.dataset.synapse = channel;
    root.setAttribute("aria-label", "Synapse " + number + " and auxiliary neuron " + number);

    const heading = element(this.owner, "div", "spk-synapses__heading");
    const title = element(this.owner, "h3", "spk-synapses__title", "Synapse " + number);
    const activation = element(this.owner, "label", "spk-synapses__activation");
    const master = element(this.owner, "input", "spk-controls__toggle");
    master.type = "checkbox";
    master.setAttribute("aria-label", "Enable Synapse " + number);
    activation.append(master, element(this.owner, "span", "spk-synapses__activation-label", "Active"));
    heading.append(title, activation);
    root.append(heading);

    const selectorLabel = element(this.owner, "label", "spk-controls__select-label", "Auxiliary neuron " + number + " mode");
    const selector = element(this.owner, "select", "spk-controls__select");
    selector.id = this.instancePrefix + channel + "-mode";
    selectorLabel.htmlFor = selector.id;
    selector.setAttribute("aria-label", "Synapse " + number + " neuron mode");
    for (const preset of NEURON_PRESETS) {
      const option = element(this.owner, "option", "", preset.label);
      option.value = String(preset.id);
      selector.append(option);
    }
    selector.value = "1";
    const parameters = element(this.owner, "dl", "spk-controls__parameters");
    root.append(selectorLabel, selector, parameters);

    const output = this.subgroup(root, "Synaptic output", "channel");
    const cell = this.subgroup(root, "Auxiliary cell input", "cell");
    const routing = this.subgroup(root, "Stimulus routing", "cell");
    const directCurrent = this.toggle(routing, "Synapse " + number + " direct current stimulation", "stimulus");
    const light = this.toggle(routing, "Synapse " + number + " light stimulation", "cell");
    const photo = this.subgroup(root, "Photoreceptor", "cell");
    const reading = element(this.owner, "p", "spk-synapses__reading", "Inactive · output 0.0 a.u.");
    reading.setAttribute("aria-live", "off");

    const references: SynapseElements = {
      channel,
      element: root,
      master,
      selector,
      parameters,
      directCurrent,
      light,
      reading,
      controls: new Map(),
      enabled: new Map(),
    };
    this.channels.set(channel, references);

    for (const id of ["gain", "decay"] as const) {
      this.addSlider(references, output, id);
    }
    for (const id of ["injectedCurrent", "noiseLevel"] as const) {
      this.addSlider(references, cell, id);
    }
    for (const id of ["photoreceptorGain", "photoreceptorDecay", "photoreceptorRecovery"] as const) {
      this.addSlider(references, photo, id);
    }

    root.append(reading);
    this.element.append(root);
    this.updateParameters(references, getPreset(1));

    master.addEventListener("change", () => this.setSynapseEnabled(channel, master.checked));
    selector.addEventListener("change", () => this.selectPreset(channel, Number(selector.value)));
    directCurrent.addEventListener("change", () => this.setDirectCurrentEnabled(channel, directCurrent.checked));
    light.addEventListener("change", () => this.setLightEnabled(channel, light.checked));
  }

  private subgroup(parent: HTMLElement, title: string, accent: "channel" | "cell"): HTMLElement {
    const group = element(this.owner, "section", "spk-synapses__subgroup");
    group.dataset.accent = accent;
    group.append(element(this.owner, "h4", "spk-synapses__subheading", title));
    parent.append(group);
    return group;
  }

  private toggle(parent: HTMLElement, label: string, accent: "stimulus" | "cell"): HTMLInputElement {
    const wrapper = element(this.owner, "label", "spk-controls__toggle-row");
    wrapper.dataset.accent = accent;
    const control = element(this.owner, "input", "spk-controls__toggle");
    control.type = "checkbox";
    control.setAttribute("aria-label", label);
    const visible = label.replace(/^Synapse [12] /, "");
    wrapper.append(control, element(this.owner, "span", "spk-controls__toggle-label", visible));
    parent.append(wrapper);
    return control;
  }

  private addSlider(references: SynapseElements, parent: HTMLElement, id: SynapseControlId): void {
    const specification = getSynapseControlSpecification(references.channel, id);
    const row = element(this.owner, "div", "spk-controls__control");
    row.dataset.control = id;
    row.dataset.synapse = references.channel;
    row.dataset.accent = specification.accent === "channel" ? references.channel : "cell";
    const header = element(this.owner, "div", "spk-controls__control-header");
    const target = element(this.owner, "label", "spk-controls__enable");
    const toggle = element(this.owner, "input", "spk-controls__toggle");
    toggle.type = "checkbox";
    toggle.checked = specification.enabledByDefault;
    toggle.setAttribute(
      "aria-label",
      "Enable Synapse " + channelNumber(references.channel) + " " + specification.label.toLowerCase(),
    );
    target.append(toggle);
    references.enabled.set(id, specification.enabledByDefault);

    const slider = element(this.owner, "input", "spk-controls__range");
    slider.type = "range";
    slider.id = this.instancePrefix + references.channel + "-" + id;
    slider.min = String(specification.minimum);
    slider.max = String(specification.maximum);
    slider.step = String(specification.step);
    slider.value = String(specification.defaultValue);
    slider.disabled = true;
    slider.setAttribute(
      "aria-label",
      "Synapse " + channelNumber(references.channel) + " " + specification.label + " (" + specification.unit + ")",
    );

    const label = element(this.owner, "label", "spk-controls__control-label", specification.label);
    label.htmlFor = slider.id;
    const output = element(this.owner, "output", "spk-controls__value");
    output.setAttribute("for", slider.id);
    header.append(target, label, output);

    const ticks = element(this.owner, "datalist", "spk-controls__ticks");
    ticks.id = slider.id + "-ticks";
    for (let value = specification.minimum; value <= specification.maximum; value += specification.tickInterval) {
      const option = element(this.owner, "option", "");
      option.value = String(value);
      ticks.append(option);
    }
    slider.setAttribute("list", ticks.id);
    row.append(header, slider, ticks);
    parent.append(row);

    const controls = { specification, row, toggle, slider, output };
    references.controls.set(id, controls);
    this.updateSlider(references, controls, specification.defaultValue);

    toggle.addEventListener("change", () => this.setControlEnabled(references.channel, id, toggle.checked));
    slider.addEventListener("input", () => this.setControlValue(references.channel, id, Number(slider.value)));
  }

  private updateSlider(references: SynapseElements, controls: SynapseSliderElements, value: number): void {
    controls.output.textContent = formatSynapseControlValue(references.channel, controls.specification.id, value);
    const percent =
      ((value - controls.specification.minimum) /
        (controls.specification.maximum - controls.specification.minimum)) *
      100;
    controls.slider.style.setProperty("--spk-fill", percent + "%");

    let description = controls.output.textContent;
    if (controls.specification.id === "decay") {
      const time = synapticTimeConstantMs(value);
      const detail = Number.isFinite(time) ? "τ " + time.toFixed(2) + " ms" : "no decay";
      controls.output.setAttribute("title", detail);
      description += "; " + detail;
    }
    controls.slider.setAttribute("aria-valuetext", description);
  }

  private updateParameters(references: SynapseElements, preset: NeuronPreset): void {
    references.parameters.replaceChildren();
    for (const [label, value, unit] of [
      ["a", preset.a, ""],
      ["b", preset.b, ""],
      ["c", preset.c, "mV"],
      ["d", preset.d, ""],
      ["Vrest", preset.restingPotential, "mV"],
    ] as const) {
      references.parameters.append(
        element(this.owner, "dt", "spk-controls__parameter-name", label),
        element(
          this.owner,
          "dd",
          "spk-controls__parameter-value",
          String(value).replace("-", "−") + (unit ? " " + unit : ""),
        ),
      );
    }
  }

  private controlPatch(id: SynapseControlId, value: number): SynapsePatch {
    switch (id) {
      case "gain": return { gain: value };
      case "decay": return { decaySlider: value };
      case "injectedCurrent": return { patchCurrent: value };
      case "noiseLevel": return { noiseLevel: value };
      case "photoreceptorGain": return { photoreceptor: { gain: value } };
      case "photoreceptorDecay": return { photoreceptor: { decaySlider: value } };
      case "photoreceptorRecovery": return { photoreceptor: { recoverySlider: value } };
    }
  }

  private controlValue(id: SynapseControlId, controls: SynapseControls): number {
    switch (id) {
      case "gain": return controls.gain;
      case "decay": return controls.decaySlider;
      case "injectedCurrent": return controls.patchCurrent;
      case "noiseLevel": return controls.noiseLevel;
      case "photoreceptorGain": return controls.photoreceptor.gain;
      case "photoreceptorDecay": return controls.photoreceptor.decaySlider;
      case "photoreceptorRecovery": return controls.photoreceptor.recoverySlider;
    }
  }

  private applyPatch(channel: SynapseId, patch: SynapsePatch): void {
    this.error.textContent = "";
    const update: ControlsPatch = channel === "synapse1" ? { synapse1: patch } : { synapse2: patch };
    this.source.updateControls(update);
  }

  private requireActive(channel: SynapseId, action: string): void {
    if (!this.current[validateSynapseId(channel)].enabled) {
      throw new RangeError("Enable Synapse " + channelNumber(channel) + " before " + action + ".");
    }
  }

  private channel(channel: SynapseId): SynapseElements {
    return this.channels.get(validateSynapseId(channel))!;
  }

  private handleSnapshot(snapshot: EngineSnapshot): void {
    if (snapshot.stepIndex === 0) {
      this.latestSample = undefined;
    }
    this.synchronise(snapshot.controls, false);
  }

  private handleSamples(samples: readonly SimulationSample[]): void {
    if (samples.length === 0) {
      return;
    }
    this.latestSample = samples[samples.length - 1];
    for (const channel of SYNAPSE_IDS) {
      this.updateReading(this.channel(channel));
    }
  }

  private synchronise(controls: SimulationControls, initialise: boolean): void {
    const previous = this.current;
    this.current = structuredClone(controls);

    for (const channel of SYNAPSE_IDS) {
      const references = this.channel(channel);
      const state = controls[channel];
      references.master.checked = state.enabled;
      references.element.dataset.active = String(state.enabled);
      references.selector.value = String(state.presetId);
      references.directCurrent.checked = state.directCurrentEnabled;
      references.light.checked = state.lightEnabled;
      this.updateParameters(references, getPreset(state.presetId));

      for (const specification of SYNAPSE_CONTROL_SPECIFICATIONS[channel]) {
        const slider = references.controls.get(specification.id)!;
        const value = this.controlValue(specification.id, state);
        if (!initialise && value !== specification.defaultValue) {
          references.enabled.set(specification.id, true);
        }
        slider.toggle.checked = references.enabled.get(specification.id) ?? false;
        slider.slider.value = String(value);
        this.updateSlider(references, slider, value);
      }

      this.updateAvailability(references);
      this.updateReading(references);
      if (!initialise && previous[channel].enabled !== state.enabled) {
        this.updateTraces(channel, state.enabled);
      }
    }
  }

  private updateAvailability(references: SynapseElements): void {
    const state = this.current[references.channel];
    references.directCurrent.disabled = !state.enabled;
    references.light.disabled = !state.enabled;

    for (const [id, controls] of references.controls) {
      const available = independentControl(id) || (state.enabled && (!photoControl(id) || state.lightEnabled));
      controls.toggle.disabled = !available;
      controls.slider.disabled = !available || !(references.enabled.get(id) ?? false);
      controls.row.dataset.disabled = String(controls.slider.disabled);
    }
  }

  private updateReading(references: SynapseElements): void {
    if (!this.current[references.channel].enabled) {
      references.reading.textContent = "Inactive · output 0.0 a.u.";
      return;
    }

    if (this.latestSample === undefined) {
      references.reading.textContent = "Ready · Vm — mV · output 0.0 a.u.";
      return;
    }

    const first = references.channel === "synapse1";
    const potential = first ? this.latestSample.synapse1Vm : this.latestSample.synapse2Vm;
    const current = first ? this.latestSample.synapse1Current : this.latestSample.synapse2Current;
    references.reading.textContent =
      "Vm " + scientificNumber(potential) + " mV · output " + scientificNumber(current, 2) + " a.u.";
  }

  private updateTraces(channel: SynapseId, visible: boolean): void {
    if (this.options.autoShowTraces === false || this.options.oscilloscope === undefined) {
      return;
    }
    const voltage = channel === "synapse1" ? "synapse1Vm" : "synapse2Vm";
    const current = channel === "synapse1" ? "synapse1Current" : "synapse2Current";
    this.options.oscilloscope.setTraceVisible(voltage, visible);
    this.options.oscilloscope.setTraceVisible(current, visible);
  }

  private showError(failure: unknown): void {
    this.error.textContent =
      failure instanceof Error ? failure.message : "The synapse controls encountered an unexpected error.";
  }
}
