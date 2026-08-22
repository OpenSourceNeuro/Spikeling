// SPDX-License-Identifier: GPL-3.0-or-later

import { TIMESTEP_MS } from "../model/izhikevich.ts";

export type MainControlId =
  | "stimulusFrequency"
  | "stimulusStrength"
  | "injectedCurrent"
  | "noiseLevel"
  | "photoreceptorGain"
  | "photoreceptorDecay"
  | "photoreceptorRecovery";

export type ControlAccent = "stimulus" | "cell";

export interface DesktopControlSpecification {
  readonly id: MainControlId;
  readonly desktopWidget: string;
  readonly label: string;
  readonly minimum: number;
  readonly maximum: number;
  readonly step: number;
  readonly tickInterval: number;
  readonly defaultValue: number;
  readonly enabledByDefault: boolean;
  readonly accent: ControlAccent;
  readonly unit: string;
}

/** Source-pinned to generated UI_Spikeling.py and its emulator controller. */
export const MAIN_CONTROL_SPECIFICATIONS: readonly DesktopControlSpecification[] =
  Object.freeze([
    {
      id: "stimulusFrequency",
      desktopWidget: "Emulator_StimFre_slider",
      label: "Stimulus frequency",
      minimum: -100,
      maximum: 100,
      step: 1,
      tickInterval: 20,
      defaultValue: 0,
      enabledByDefault: false,
      accent: "stimulus",
      unit: "Hz",
    },
    {
      id: "stimulusStrength",
      desktopWidget: "Emulator_StimStrSlider",
      label: "Stimulus strength",
      minimum: -100,
      maximum: 100,
      step: 1,
      tickInterval: 20,
      defaultValue: 0,
      enabledByDefault: false,
      accent: "stimulus",
      unit: "%",
    },
    {
      id: "injectedCurrent",
      desktopWidget: "Emulator_PatchClamp_slider",
      label: "Injected current",
      minimum: -100,
      maximum: 100,
      step: 1,
      tickInterval: 20,
      defaultValue: 0,
      enabledByDefault: false,
      accent: "cell",
      unit: "a.u.",
    },
    {
      id: "noiseLevel",
      desktopWidget: "Emulator_Noise_slider",
      label: "Noise level",
      minimum: 0,
      maximum: 100,
      step: 1,
      tickInterval: 10,
      defaultValue: 0,
      enabledByDefault: false,
      accent: "cell",
      unit: "%",
    },
    {
      id: "photoreceptorGain",
      desktopWidget: "Emulator_PR_PhotoGain_slider",
      label: "Photo-gain",
      minimum: -100,
      maximum: 100,
      step: 1,
      tickInterval: 20,
      defaultValue: 0,
      enabledByDefault: false,
      accent: "cell",
      unit: "%",
    },
    {
      id: "photoreceptorDecay",
      desktopWidget: "Emulator_PR_Decay_slider",
      label: "Photo decay λ",
      minimum: 10,
      maximum: 125,
      step: 1,
      tickInterval: 10,
      defaultValue: 100,
      enabledByDefault: false,
      accent: "cell",
      unit: "ms⁻¹",
    },
    {
      id: "photoreceptorRecovery",
      desktopWidget: "Emulator_PR_Recovery_slider",
      label: "Photo recovery λ",
      minimum: 1,
      maximum: 100,
      step: 1,
      tickInterval: 10,
      defaultValue: 25,
      enabledByDefault: false,
      accent: "cell",
      unit: "ms⁻¹",
    },
  ]);

export function getMainControlSpecification(id: MainControlId): DesktopControlSpecification {
  const specification = MAIN_CONTROL_SPECIFICATIONS.find((candidate) => candidate.id === id);
  if (specification === undefined) {
    throw new RangeError("Unknown main-neuron control: " + String(id));
  }
  return specification;
}

export function validateMainControlValue(id: MainControlId, value: number): number {
  const specification = getMainControlSpecification(id);
  if (
    !Number.isInteger(value) ||
    value < specification.minimum ||
    value > specification.maximum
  ) {
    throw new RangeError(
      specification.label +
        " must be an integer from " +
        specification.minimum +
        " to " +
        specification.maximum +
        ".",
    );
  }
  return value;
}

/** Desktop UI formula: round(10000 / (500 + (-slider * 500 / 100) + 10)). */
export function stimulusFrequencyHz(slider: number): number {
  validateMainControlValue("stimulusFrequency", slider);
  const periodSteps = 500 + (-slider * 500) / 100 + 10;
  return 1_000 / (periodSteps * TIMESTEP_MS);
}

export function photoreceptorDecayRate(slider: number): number {
  return validateMainControlValue("photoreceptorDecay", slider) / 100_000;
}

export function photoreceptorRecoveryRate(slider: number): number {
  return validateMainControlValue("photoreceptorRecovery", slider) / 1_000;
}

export function gaussianNoiseStandardDeviation(slider: number): number {
  return validateMainControlValue("noiseLevel", slider) / 4;
}

export function formatMainControlValue(id: MainControlId, slider: number): string {
  validateMainControlValue(id, slider);
  switch (id) {
    case "stimulusFrequency":
      return Math.round(stimulusFrequencyHz(slider)) + " Hz";
    case "stimulusStrength":
    case "photoreceptorGain":
      return slider + "%";
    case "injectedCurrent":
      return slider + " a.u.";
    case "noiseLevel":
      return slider + "% · σ " + gaussianNoiseStandardDeviation(slider) + " a.u.";
    case "photoreceptorDecay":
      return photoreceptorDecayRate(slider) + " ms⁻¹";
    case "photoreceptorRecovery":
      return photoreceptorRecoveryRate(slider) + " ms⁻¹";
  }
}
