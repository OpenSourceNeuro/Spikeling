// SPDX-License-Identifier: GPL-3.0-or-later

import { getPreset } from "./presets.ts";
import type {
  CellControls,
  CellPatch,
  ControlsPatch,
  PhotoreceptorControls,
  SimulationControls,
  SynapseControls,
  SynapsePatch,
} from "./types.ts";

function defaultPhotoreceptor(): PhotoreceptorControls {
  return { gain: 0, decaySlider: 100, recoverySlider: 25 };
}

function defaultCell(): CellControls {
  return {
    presetId: 1,
    patchCurrent: 0,
    noiseLevel: 0,
    directCurrentEnabled: false,
    lightEnabled: false,
    photoreceptor: defaultPhotoreceptor(),
  };
}

function defaultSynapse(decaySlider: number): SynapseControls {
  return {
    ...defaultCell(),
    enabled: false,
    gain: 0,
    decaySlider,
  };
}

export function defaultControls(): SimulationControls {
  return {
    main: defaultCell(),
    synapse1: defaultSynapse(995),
    synapse2: defaultSynapse(990),
    stimulus: {
      mode: "internal",
      strength: 0,
      frequencySlider: 0,
      customSamples: [],
    },
  };
}

function mergeCell(base: CellControls, patch: CellPatch = {}): CellControls {
  return {
    ...base,
    ...patch,
    photoreceptor: {
      ...base.photoreceptor,
      ...patch.photoreceptor,
    },
  };
}

function mergeSynapse(
  base: SynapseControls,
  patch: SynapsePatch = {},
): SynapseControls {
  return {
    ...base,
    ...patch,
    photoreceptor: {
      ...base.photoreceptor,
      ...patch.photoreceptor,
    },
  };
}

function integerInRange(
  name: string,
  value: number,
  minimum: number,
  maximum: number,
): void {
  if (!Number.isInteger(value) || value < minimum || value > maximum) {
    throw new RangeError(
      name + " must be an integer from " + minimum + " to " + maximum + ".",
    );
  }
}

function validatePhotoreceptor(
  name: string,
  controls: PhotoreceptorControls,
): void {
  integerInRange(name + ".gain", controls.gain, -100, 100);
  integerInRange(name + ".decaySlider", controls.decaySlider, 10, 125);
  integerInRange(name + ".recoverySlider", controls.recoverySlider, 1, 100);
}

function validateCell(
  name: string,
  controls: CellControls,
  minimumPatch: number,
  maximumPatch: number,
): void {
  getPreset(controls.presetId);
  integerInRange(name + ".patchCurrent", controls.patchCurrent, minimumPatch, maximumPatch);
  integerInRange(name + ".noiseLevel", controls.noiseLevel, 0, 100);
  validatePhotoreceptor(name + ".photoreceptor", controls.photoreceptor);
}

function validateSynapse(name: string, controls: SynapseControls): void {
  // Correct the desktop UI defect: its labels promise -50..50, but Qt exposed
  // 0..100. The browser model accepts the intended signed range.
  validateCell(name, controls, -50, 50);
  integerInRange(name + ".gain", controls.gain, -100, 100);
  integerInRange(name + ".decaySlider", controls.decaySlider, 975, 1000);
}

export function mergeControls(
  base: SimulationControls,
  patch: ControlsPatch = {},
): SimulationControls {
  const result: SimulationControls = {
    main: mergeCell(base.main, patch.main),
    synapse1: mergeSynapse(base.synapse1, patch.synapse1),
    synapse2: mergeSynapse(base.synapse2, patch.synapse2),
    stimulus: {
      ...base.stimulus,
      ...patch.stimulus,
      customSamples: [
        ...(patch.stimulus?.customSamples ?? base.stimulus.customSamples),
      ],
    },
  };

  validateCell("main", result.main, -100, 100);
  validateSynapse("synapse1", result.synapse1);
  validateSynapse("synapse2", result.synapse2);
  integerInRange("stimulus.strength", result.stimulus.strength, -100, 100);
  integerInRange(
    "stimulus.frequencySlider",
    result.stimulus.frequencySlider,
    -100,
    100,
  );

  if (result.stimulus.mode !== "internal" && result.stimulus.mode !== "custom") {
    throw new TypeError("stimulus.mode must be internal or custom.");
  }
  if (result.stimulus.customSamples.some((value) => !Number.isFinite(value))) {
    throw new TypeError("Custom stimulus samples must all be finite numbers.");
  }
  if (result.stimulus.mode === "custom" && result.stimulus.customSamples.length === 0) {
    throw new RangeError("A custom stimulus must contain at least one sample.");
  }

  return result;
}
