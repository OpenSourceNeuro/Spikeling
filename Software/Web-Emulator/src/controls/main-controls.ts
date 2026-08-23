// SPDX-License-Identifier: GPL-3.0-or-later

import type { DataSource, Unsubscribe } from "../data-source/DataSource.ts";
import { defaultControls } from "../model/controls.ts";
import { getPreset, NEURON_PRESETS } from "../model/presets.ts";
import type { ControlsPatch, NeuronPreset, SimulationControls } from "../model/types.ts";
import type { EngineSnapshot } from "../simulation/protocol.ts";
import {
  MAX_CUSTOM_STIMULUS_BYTES,
  MAX_CUSTOM_STIMULUS_SAMPLES,
  parseCustomStimulusCsv,
  parseCustomStimulusFile,
} from "../stimulus/custom-csv.ts";
import type {
  CustomStimulusOptions,
  LocalStimulusFile,
  ParsedCustomStimulus,
} from "../stimulus/custom-csv.ts";
import { renderStimulusPreview } from "../stimulus/preview.ts";
import {
  MAIN_CONTROL_SPECIFICATIONS,
  formatMainControlValue,
  getMainControlSpecification,
  validateMainControlValue,
} from "./specifications.ts";
import type { DesktopControlSpecification, MainControlId } from "./specifications.ts";

interface SliderElements {
  readonly specification: DesktopControlSpecification;
  readonly row: HTMLElement;
  readonly toggle: HTMLInputElement;
  readonly slider: HTMLInputElement;
  readonly output: HTMLOutputElement;
  readonly alwaysEnabled: boolean;
}

export interface MainNeuronControlsOptions extends CustomStimulusOptions {
  readonly devicePixelRatio?: () => number;
  readonly compact?: boolean;
  readonly stimulusHost?: HTMLElement;
}

let controlsInstanceCount = 0;

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

function formattedNumber(value: number): string {
  return String(value).replace("-", "−");
}

/** Desktop-faithful main-neuron controls talking only to the DataSource seam. */
export class SpikelingMainControls {
  readonly element: HTMLElement;

  private readonly owner: Document;
  private readonly source: DataSource;
  private readonly instancePrefix: string;
  private readonly options: MainNeuronControlsOptions;
  private readonly controls = new Map<MainControlId, SliderElements>();
  private readonly enabled = new Map<MainControlId, boolean>();
  private readonly auxiliaryElements: HTMLElement[] = [];
  private readonly subscriptions: Unsubscribe[] = [];
  private readonly neuronSelect: HTMLSelectElement;
  private readonly parameters: HTMLElement;
  private readonly directCurrent: HTMLInputElement;
  private readonly light: HTMLInputElement;
  private readonly customToggle: HTMLInputElement;
  private readonly fileInput: HTMLInputElement;
  private readonly customStatus: HTMLElement;
  private readonly preview: HTMLCanvasElement;
  private readonly errorMessage: HTMLElement;
  private currentControls = defaultControls();
  private customSignature = "";
  private importedSamples: readonly number[] = [];
  private disposed = false;

  constructor(host: HTMLElement, source: DataSource, options: MainNeuronControlsOptions = {}) {
    this.owner = host.ownerDocument;
    this.source = source;
    this.options = options;
    controlsInstanceCount += 1;
    this.instancePrefix = "spk-main-" + controlsInstanceCount + "-";
    this.element = element(this.owner, "section", "spk-controls");
    this.element.setAttribute("aria-label", options.compact ? "Main neuron controls" : "Main neuron and stimulus controls");

    const neuron = this.group(options.compact ? "Neuron mode" : "Neuron parameters", "neuron");
    this.neuronSelect = element(this.owner, "select", "spk-controls__select");
    this.neuronSelect.id = this.instancePrefix + "neuron-mode";
    if (options.compact) {
      this.neuronSelect.setAttribute("aria-label", "Neuron mode");
    } else {
      const selectorLabel = element(this.owner, "label", "spk-controls__select-label", "Neuron mode");
      selectorLabel.htmlFor = this.neuronSelect.id;
      neuron.append(selectorLabel);
    }
    for (const preset of NEURON_PRESETS) {
      const choice = element(this.owner, "option", "", preset.label);
      choice.value = String(preset.id);
      this.neuronSelect.append(choice);
    }
    this.neuronSelect.value = "1";
    this.neuronSelect.addEventListener("change", () => this.selectPreset(Number(this.neuronSelect.value)));
    this.parameters = element(this.owner, "dl", "spk-controls__parameters");
    neuron.append(this.neuronSelect, this.parameters);

    if (options.compact) {
      const input = this.group("Current input", "cell");
      this.addSlider(input, "injectedCurrent", { alwaysEnabled: true, label: "Current input" });
      const noise = this.group("Noise", "cell");
      this.addSlider(noise, "noiseLevel", { alwaysEnabled: true, label: "Noise" });
    }

    let stimulusParent = this.element;
    if (options.stimulusHost !== undefined) {
      stimulusParent = element(this.owner, "section", "spk-controls");
      stimulusParent.setAttribute("aria-label", "Stimulus controls");
      options.stimulusHost.append(stimulusParent);
      this.auxiliaryElements.push(stimulusParent);
    }
    const stimulus = this.group("Stimulus parameters", "stimulus", stimulusParent);
    const routing = element(this.owner, "div", "spk-controls__routing");
    this.directCurrent = this.standaloneToggle(routing, "Direct current stimulation", "stimulus");
    this.light = this.standaloneToggle(routing, "Light stimulation", "cell");
    this.directCurrent.addEventListener("change", () => {
      this.applyPatch({ main: { directCurrentEnabled: this.directCurrent.checked } });
    });
    this.light.addEventListener("change", () => {
      this.applyPatch({ main: { lightEnabled: this.light.checked } });
    });
    stimulus.append(routing);
    this.addSlider(stimulus, "stimulusFrequency");
    this.addSlider(stimulus, "stimulusStrength");

    const custom = element(this.owner, "div", "spk-controls__custom");
    this.customToggle = this.standaloneToggle(custom, "Use custom stimulus", "stimulus");
    this.customToggle.disabled = true;
    this.customToggle.addEventListener("change", () => this.setCustomStimulusEnabled(this.customToggle.checked));
    const fileLabel = element(this.owner, "label", "spk-controls__file-label", "Load custom stimulus (.csv)");
    this.fileInput = element(this.owner, "input", "spk-controls__file");
    this.fileInput.id = this.instancePrefix + "custom-file";
    this.fileInput.type = "file";
    this.fileInput.accept = ".csv,text/csv";
    fileLabel.htmlFor = this.fileInput.id;
    this.fileInput.addEventListener("change", () => {
      const selected = this.fileInput.files?.[0];
      if (selected !== undefined) {
        void this.loadCustomStimulusFile(selected).catch((failure) => this.showError(failure));
      }
    });
    this.customStatus = element(this.owner, "p", "spk-controls__custom-status", "No custom stimulus loaded.");
    this.customStatus.setAttribute("role", "status");
    this.customStatus.setAttribute("aria-live", "polite");
    this.preview = element(this.owner, "canvas", "spk-controls__preview");
    this.preview.setAttribute("role", "img");
    this.preview.setAttribute("aria-label", "Imported custom stimulus preview.");
    custom.append(fileLabel, this.fileInput, this.customStatus, this.preview);
    stimulus.append(custom);

    if (!options.compact) {
      const input = this.group("Cell input", "cell");
      this.addSlider(input, "injectedCurrent");
      this.addSlider(input, "noiseLevel");
    }

    const photo = options.compact
      ? element(this.owner, "div", "spk-controls__legacy-photoreceptor")
      : this.group("Photoreceptor", "cell");
    this.addSlider(photo, "photoreceptorGain");
    this.addSlider(photo, "photoreceptorDecay");
    this.addSlider(photo, "photoreceptorRecovery");

    this.errorMessage = element(this.owner, "p", "spk-controls__error");
    this.errorMessage.setAttribute("role", "alert");
    this.element.append(this.errorMessage);
    host.append(this.element);

    this.updatePresetParameters(getPreset(1));
    this.drawPreview([]);
    this.syncControls(defaultControls(), true);
    this.subscriptions.push(
      source.subscribeState((snapshot) => this.handleSnapshot(snapshot)),
      source.subscribeErrors((failure) => this.showError(failure)),
    );
  }

  getControls(): SimulationControls {
    return structuredClone(this.currentControls);
  }

  isEnabled(id: MainControlId): boolean {
    getMainControlSpecification(id);
    return this.enabled.get(id) ?? false;
  }

  selectPreset(identifier: number): void {
    const preset = getPreset(identifier);
    for (const id of ["photoreceptorGain", "photoreceptorDecay", "photoreceptorRecovery"] as const) {
      this.enabled.set(id, false);
    }
    this.neuronSelect.value = String(preset.id);
    this.updatePresetParameters(preset);
    this.applyPatch({
      main: {
        presetId: preset.id,
        photoreceptor: { gain: 0, decaySlider: 100, recoverySlider: 25 },
      },
    });
  }

  setControlEnabled(id: MainControlId, active: boolean): void {
    const specification = getMainControlSpecification(id);
    const controls = this.controls.get(id)!;
    const enabled = controls.alwaysEnabled || active;
    this.enabled.set(id, enabled);
    controls.toggle.checked = enabled;
    if (!enabled) {
      controls.slider.value = String(specification.defaultValue);
      this.updateSliderDisplay(controls, specification.defaultValue);
    }
    this.updateControlAvailability();
    this.applyPatch(this.patchForControl(id, Number(controls.slider.value)));
  }

  setControlValue(id: MainControlId, value: number): void {
    const valid = validateMainControlValue(id, value);
    const controls = this.controls.get(id)!;
    controls.slider.value = String(valid);
    this.updateSliderDisplay(controls, valid);
    this.applyPatch(this.patchForControl(id, valid));
  }

  async loadCustomStimulusFile(file: LocalStimulusFile): Promise<ParsedCustomStimulus> {
    const parsed = await parseCustomStimulusFile(file, this.options);
    this.installCustomStimulus(parsed, file.name);
    return parsed;
  }

  loadCustomStimulusText(content: string, name = "custom-stimulus.csv"): ParsedCustomStimulus {
    const parsed = parseCustomStimulusCsv(content, this.options);
    this.installCustomStimulus(parsed, name);
    return parsed;
  }

  setCustomStimulusEnabled(active: boolean): void {
    if (
      active &&
      this.currentControls.stimulus.customSamples.length === 0 &&
      this.importedSamples.length === 0
    ) {
      throw new RangeError("Load a valid stimulus CSV before enabling custom playback.");
    }
    this.customToggle.checked = active;
    this.applyPatch({ stimulus: { mode: active ? "custom" : "internal" } });
    this.updateControlAvailability();
  }

  dispose(): void {
    if (this.disposed) {
      return;
    }
    this.disposed = true;
    for (const unsubscribe of this.subscriptions) {
      unsubscribe();
    }
    for (const auxiliary of this.auxiliaryElements) {
      auxiliary.remove();
    }
    this.element.remove();
  }

  private group(title: string, accent: ControlAccentName, parent = this.element): HTMLElement {
    const section = element(this.owner, "section", "spk-controls__group");
    section.dataset.accent = accent;
    const heading = element(this.owner, "h3", "spk-controls__heading", title);
    section.append(heading);
    parent.append(section);
    return section;
  }

  private standaloneToggle(parent: HTMLElement, label: string, accent: ControlAccentName): HTMLInputElement {
    const wrapper = element(this.owner, "label", "spk-controls__toggle-row");
    wrapper.dataset.accent = accent;
    const input = element(this.owner, "input", "spk-controls__toggle");
    input.type = "checkbox";
    input.setAttribute("aria-label", label);
    const text = element(this.owner, "span", "spk-controls__toggle-label", label);
    wrapper.append(input, text);
    parent.append(wrapper);
    return input;
  }

  private addSlider(
    parent: HTMLElement,
    id: MainControlId,
    options: { readonly alwaysEnabled?: boolean; readonly label?: string } = {},
  ): void {
    const specification = getMainControlSpecification(id);
    const labelText = options.label ?? specification.label;
    const alwaysEnabled = options.alwaysEnabled ?? false;
    const enabled = alwaysEnabled || specification.enabledByDefault;
    const row = element(this.owner, "div", "spk-controls__control");
    row.dataset.control = id;
    row.dataset.accent = specification.accent;
    const header = element(this.owner, "div", "spk-controls__control-header");

    const toggle = element(this.owner, "input", "spk-controls__toggle");
    toggle.type = "checkbox";
    toggle.checked = enabled;
    toggle.setAttribute("aria-label", "Enable " + labelText.toLowerCase());
    const toggleTarget = element(this.owner, "label", "spk-controls__enable");
    toggleTarget.append(toggle);
    this.enabled.set(id, enabled);

    const slider = element(this.owner, "input", "spk-controls__range");
    slider.type = "range";
    slider.id = this.instancePrefix + id;
    slider.min = String(specification.minimum);
    slider.max = String(specification.maximum);
    slider.step = String(specification.step);
    slider.value = String(specification.defaultValue);
    slider.disabled = !enabled;
    slider.setAttribute("aria-label", labelText + " (" + specification.unit + ")");

    const label = element(this.owner, "label", "spk-controls__control-label", labelText);
    label.htmlFor = slider.id;
    const output = element(this.owner, "output", "spk-controls__value");
    output.setAttribute("for", slider.id);
    if (alwaysEnabled) {
      row.dataset.alwaysEnabled = "true";
      header.append(label, output);
    } else {
      header.append(toggleTarget, label, output);
    }

    const ticks = element(this.owner, "datalist", "spk-controls__ticks");
    ticks.id = slider.id + "-ticks";
    for (let value = specification.minimum; value <= specification.maximum; value += specification.tickInterval) {
      const mark = element(this.owner, "option", "");
      mark.value = String(value);
      ticks.append(mark);
    }
    slider.setAttribute("list", ticks.id);
    row.append(header, slider, ticks);
    parent.append(row);

    const references = { specification, row, toggle, slider, output, alwaysEnabled };
    this.controls.set(id, references);
    this.updateSliderDisplay(references, specification.defaultValue);

    toggle.addEventListener("change", () => this.setControlEnabled(id, toggle.checked));
    slider.addEventListener("input", () => this.setControlValue(id, Number(slider.value)));
  }

  private updateSliderDisplay(elements: SliderElements, value: number): void {
    elements.output.textContent = formatMainControlValue(elements.specification.id, value);
    const percent =
      ((value - elements.specification.minimum) /
        (elements.specification.maximum - elements.specification.minimum)) *
      100;
    elements.slider.style.setProperty("--spk-fill", percent + "%");
    elements.slider.setAttribute("aria-valuetext", elements.output.textContent);
  }

  private patchForControl(id: MainControlId, value: number): ControlsPatch {
    switch (id) {
      case "stimulusFrequency":
        return { stimulus: { frequencySlider: value } };
      case "stimulusStrength":
        return { stimulus: { strength: value } };
      case "injectedCurrent":
        return { main: { patchCurrent: value } };
      case "noiseLevel":
        return { main: { noiseLevel: value } };
      case "photoreceptorGain":
        return { main: { photoreceptor: { gain: value } } };
      case "photoreceptorDecay":
        return { main: { photoreceptor: { decaySlider: value } } };
      case "photoreceptorRecovery":
        return { main: { photoreceptor: { recoverySlider: value } } };
    }
  }

  private controlValue(id: MainControlId, controls: SimulationControls): number {
    switch (id) {
      case "stimulusFrequency":
        return controls.stimulus.frequencySlider;
      case "stimulusStrength":
        return controls.stimulus.strength;
      case "injectedCurrent":
        return controls.main.patchCurrent;
      case "noiseLevel":
        return controls.main.noiseLevel;
      case "photoreceptorGain":
        return controls.main.photoreceptor.gain;
      case "photoreceptorDecay":
        return controls.main.photoreceptor.decaySlider;
      case "photoreceptorRecovery":
        return controls.main.photoreceptor.recoverySlider;
    }
  }

  private applyPatch(patch: ControlsPatch): void {
    this.errorMessage.textContent = "";
    this.source.updateControls(patch);
  }

  private handleSnapshot(snapshot: EngineSnapshot): void {
    this.syncControls(snapshot.controls, false);
  }

  private syncControls(controls: SimulationControls, initialise: boolean): void {
    this.currentControls = structuredClone(controls);
    this.neuronSelect.value = String(controls.main.presetId);
    this.updatePresetParameters(getPreset(controls.main.presetId));
    this.directCurrent.checked = controls.main.directCurrentEnabled;
    this.light.checked = controls.main.lightEnabled;

    for (const specification of MAIN_CONTROL_SPECIFICATIONS) {
      const references = this.controls.get(specification.id)!;
      const value = this.controlValue(specification.id, controls);
      if (!initialise && value !== specification.defaultValue) {
        this.enabled.set(specification.id, true);
      }
      references.toggle.checked = this.enabled.get(specification.id) ?? false;
      references.slider.value = String(value);
      this.updateSliderDisplay(references, value);
    }

    const imported = controls.stimulus.customSamples;
    this.customToggle.disabled = imported.length === 0;
    this.customToggle.checked = controls.stimulus.mode === "custom";
    const signature = imported.length + ":" + imported[0] + ":" + imported[imported.length - 1];
    if (imported.length > 0 && signature !== this.customSignature) {
      this.customSignature = signature;
      this.drawPreview(imported);
      if (this.customStatus.textContent === "No custom stimulus loaded.") {
        this.customStatus.textContent =
          imported.length.toLocaleString("en-GB") + " samples · 0.1 ms/sample";
      }
    }
    this.updateControlAvailability();
  }

  private updateControlAvailability(): void {
    const custom = this.customToggle.checked;
    for (const [id, references] of this.controls) {
      const internalOnly = id === "stimulusFrequency" || id === "stimulusStrength";
      references.toggle.disabled = internalOnly && custom;
      references.slider.disabled = !(this.enabled.get(id) ?? false) || (internalOnly && custom);
      references.row.dataset.disabled = String(references.slider.disabled);
    }
  }

  private updatePresetParameters(preset: NeuronPreset): void {
    this.parameters.replaceChildren();
    for (const [label, value, unit] of [
      ["a", preset.a, ""],
      ["b", preset.b, ""],
      ["c", preset.c, "mV"],
      ["d", preset.d, ""],
      ["Vrest", preset.restingPotential, "mV"],
    ] as const) {
      const term = element(this.owner, "dt", "spk-controls__parameter-name", label);
      const definition = element(
        this.owner,
        "dd",
        "spk-controls__parameter-value",
        formattedNumber(value) + (unit ? " " + unit : ""),
      );
      this.parameters.append(term, definition);
    }
  }

  private installCustomStimulus(parsed: ParsedCustomStimulus, name: string): void {
    this.importedSamples = parsed.samples;
    this.customStatus.textContent =
      name +
      " · " +
      parsed.samples.length.toLocaleString("en-GB") +
      " samples · " +
      parsed.sampleIntervalMs +
      " ms/sample · " +
      parsed.durationMs.toFixed(1) +
      " ms";
    this.customToggle.disabled = false;
    this.customSignature =
      parsed.samples.length + ":" + parsed.samples[0] + ":" + parsed.samples[parsed.samples.length - 1];
    this.drawPreview(parsed.samples);
    this.applyPatch({ stimulus: { customSamples: [...parsed.samples] } });
  }

  private drawPreview(samples: readonly number[]): void {
    renderStimulusPreview(this.preview, samples, this.options.devicePixelRatio?.() ?? 1);
  }

  private showError(failure: unknown): void {
    this.errorMessage.textContent =
      failure instanceof Error ? failure.message : "The neuron controls encountered an unexpected error.";
  }
}

type ControlAccentName = "stimulus" | "cell" | "neuron";

export const CUSTOM_STIMULUS_LIMITS = Object.freeze({
  bytes: MAX_CUSTOM_STIMULUS_BYTES,
  samples: MAX_CUSTOM_STIMULUS_SAMPLES,
});
