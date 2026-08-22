// SPDX-License-Identifier: GPL-3.0-or-later

import type { NeuronPreset } from "./types.ts";

function preset(
  id: number,
  key: string,
  label: string,
  a: number,
  b: number,
  c: number,
  d: number,
  restingPotential: number,
): NeuronPreset {
  return Object.freeze({ id, key, label, a, b, c, d, restingPotential });
}

export const NEURON_PRESETS: readonly NeuronPreset[] = Object.freeze([
  preset(1, "tonic-spiking", "Tonic Spiking", 0.02, 0.2, -65, 6, -70),
  preset(2, "phasic-spiking", "Phasic Spiking", 0.02, 0.25, -65, 6, -64),
  preset(3, "tonic-bursting", "Tonic Bursting", 0.02, 0.2, -50, 2, -70),
  preset(4, "phasic-bursting", "Phasic Bursting", 0.02, 0.25, -55, 0.05, -64),
  preset(5, "mixed-mode", "Mixed Mode", 0.02, 0.2, -55, 4, -70),
  preset(
    6,
    "spike-frequency-adaptation",
    "Spike Frequency Adaptation",
    0.01,
    0.22,
    -65,
    8,
    -70,
  ),
  preset(7, "class-1-excitability", "Class 1 Excitability", 0.02, -0.1, -55, 6, -60),
  preset(8, "class-2-excitability", "Class 2 Excitability", 0.2, 0.26, -65, 0, -64),
  preset(9, "spike-latency", "Spike Latency", 0.02, 0.2, -65, 6, -70),
  preset(
    10,
    "sub-threshold-oscillations",
    "Sub-threshold Oscillations",
    0.05,
    0.26,
    -60,
    0,
    -62,
  ),
  preset(11, "resonator", "Resonator", 0.1, 0.26, -60, -1, -62),
  preset(12, "integrator", "Integrator", 0.02, -0.1, -55, 6, -60),
  preset(13, "rebound-spike", "Rebound Spike", 0.03, 0.25, -60, 4, -64),
  preset(14, "rebound-burst", "Rebound Burst", 0.03, 0.25, -52, 0, -64),
  preset(
    15,
    "threshold-variability",
    "Threshold Variability",
    0.03,
    0.25,
    -60,
    4,
    -64,
  ),
  preset(16, "bistability", "Bistability", 0.1, 0.26, -60, 0, -61),
  preset(
    17,
    "depolarizing-after-potential",
    "Depolarizing after potential",
    1,
    0.2,
    -60,
    -21,
    -70,
  ),
  preset(18, "accommodation", "Accommodation", 0.02, 1, -55, 4, -65),
  preset(
    19,
    "inhibition-induced-spiking",
    "Inhibition Induced Spiking",
    0.02,
    1,
    -60,
    8,
    -63.8,
  ),
  preset(
    20,
    "inhibition-induced-bursting",
    "Inhibition Induced Bursting",
    0.026,
    -1,
    -45,
    -2,
    -63.8,
  ),
]);

export function getPreset(identifier: number | string): NeuronPreset {
  const found =
    typeof identifier === "number"
      ? NEURON_PRESETS.find((entry) => entry.id === identifier)
      : NEURON_PRESETS.find(
          (entry) => entry.key === identifier || entry.label === identifier,
        );

  if (found === undefined) {
    throw new RangeError("Unknown Spikeling neuron preset: " + String(identifier));
  }

  return found;
}
