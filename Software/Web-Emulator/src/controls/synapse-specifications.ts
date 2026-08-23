// SPDX-License-Identifier: GPL-3.0-or-later

import { TIMESTEP_MS } from "../model/izhikevich.ts";
import {
  gaussianNoiseStandardDeviation,
  photoreceptorDecayRate,
  photoreceptorRecoveryRate,
} from "./specifications.ts";

export type SynapseId = "synapse1" | "synapse2";

export type SynapseControlId =
  | "gain"
  | "decay"
  | "injectedCurrent"
  | "noiseLevel"
  | "photoreceptorGain"
  | "photoreceptorDecay"
  | "photoreceptorRecovery";

export type SynapseControlAccent = "channel" | "cell";

export interface SynapseControlSpecification {
  readonly id: SynapseControlId;
  readonly desktopWidget: string;
  readonly label: string;
  readonly minimum: number;
  readonly maximum: number;
  readonly step: number;
  readonly tickInterval: number;
  readonly defaultValue: number;
  readonly enabledByDefault: boolean;
  readonly accent: SynapseControlAccent;
  readonly unit: string;
}

export const SYNAPSE_IDS: readonly SynapseId[] = Object.freeze(["synapse1", "synapse2"]);

function specificationsFor(channel: SynapseId): readonly SynapseControlSpecification[] {
  const number = channel === "synapse1" ? "1" : "2";
  const prefix = "Emulator_Syn" + number + "_";
  const synapsePrefix = "Emulator_Synapse" + number + "_";

  return Object.freeze([
    {
      id: "gain",
      desktopWidget: synapsePrefix + "slider",
      label: "Synaptic gain",
      minimum: -100,
      maximum: 100,
      step: 1,
      tickInterval: 20,
      defaultValue: 0,
      enabledByDefault: false,
      accent: "channel",
      unit: "%",
    },
    {
      id: "decay",
      desktopWidget: synapsePrefix + "Decay_slider",
      label: "Synaptic decay",
      minimum: 975,
      maximum: 1000,
      step: 1,
      tickInterval: 2,
      defaultValue: channel === "synapse1" ? 995 : 990,
      enabledByDefault: false,
      accent: "channel",
      unit: "retention / step",
    },
    {
      id: "injectedCurrent",
      desktopWidget: prefix + "PatchClamp_slider",
      label: "Injected current",
      minimum: -50,
      maximum: 50,
      step: 1,
      tickInterval: 10,
      defaultValue: 0,
      enabledByDefault: false,
      accent: "cell",
      unit: "a.u.",
    },
    {
      id: "noiseLevel",
      desktopWidget: prefix + "Noise_slider",
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
      desktopWidget: prefix + "PR_PhotoGain_slider",
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
      desktopWidget: prefix + "PR_Decay_slider",
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
      desktopWidget: prefix + "PR_Recovery_slider",
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
  ] as const);
}

/** Source-pinned desktop controls; auxiliary patch range intentionally fixes Qt's 0..100 defect. */
export const SYNAPSE_CONTROL_SPECIFICATIONS: Readonly<
  Record<SynapseId, readonly SynapseControlSpecification[]>
> = Object.freeze({
  synapse1: specificationsFor("synapse1"),
  synapse2: specificationsFor("synapse2"),
});

export function validateSynapseId(channel: SynapseId): SynapseId {
  if (channel !== "synapse1" && channel !== "synapse2") {
    throw new RangeError("Unknown Spikeling synapse: " + String(channel));
  }
  return channel;
}

export function getSynapseControlSpecification(
  channel: SynapseId,
  id: SynapseControlId,
): SynapseControlSpecification {
  const specifications = SYNAPSE_CONTROL_SPECIFICATIONS[validateSynapseId(channel)];
  const specification = specifications.find((candidate) => candidate.id === id);
  if (specification === undefined) {
    throw new RangeError("Unknown synapse control: " + String(id));
  }
  return specification;
}

export function validateSynapseControlValue(
  channel: SynapseId,
  id: SynapseControlId,
  value: number,
): number {
  const specification = getSynapseControlSpecification(channel, id);
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

/** Actual dimensionless fraction of synaptic current retained per 0.1 ms step. */
export function synapticRetentionFactor(slider: number): number {
  return validateSynapseControlValue("synapse1", "decay", slider) / 1_000;
}

/** Equivalent exponential time constant; a retention factor of one never decays. */
export function synapticTimeConstantMs(slider: number): number {
  const retained = synapticRetentionFactor(slider);
  return retained === 1 ? Number.POSITIVE_INFINITY : -TIMESTEP_MS / Math.log(retained);
}

export function formatSynapseControlValue(
  channel: SynapseId,
  id: SynapseControlId,
  slider: number,
): string {
  validateSynapseControlValue(channel, id, slider);
  switch (id) {
    case "gain":
    case "photoreceptorGain":
      return slider + "%";
    case "decay":
      return synapticRetentionFactor(slider).toFixed(3) + " / step";
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
