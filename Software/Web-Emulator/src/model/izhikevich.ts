// SPDX-License-Identifier: GPL-3.0-or-later

import type { IntegrationResult, NeuronPreset, NeuronState } from "./types.ts";

export const TIMESTEP_MS = 0.1;
export const RESET_THRESHOLD_MV = 30;
export const DISPLAY_PEAK_MV = 30;
export const MINIMUM_POTENTIAL_MV = -110;

/**
 * Match Graph_Emulator.py exactly: update v first, use that v for u, reset
 * before the display-peak rule, and clamp the lower membrane potential.
 */
export function integrateNeuron(
  state: NeuronState,
  preset: NeuronPreset,
): IntegrationResult {
  let v =
    state.v +
    TIMESTEP_MS *
      (0.04 * state.v * state.v +
        5 * state.v +
        140 -
        state.u +
        state.totalCurrent);

  let u = state.u + TIMESTEP_MS * (preset.a * (preset.b * v - state.u));

  if (v >= RESET_THRESHOLD_MV) {
    v = preset.c;
    u += preset.d;
  }

  if (v < MINIMUM_POTENTIAL_MV) {
    v = MINIMUM_POTENTIAL_MV;
  }

  let spiked = false;
  if (v >= 0) {
    v = DISPLAY_PEAK_MV;
    spiked = true;
  }

  return { v, u, spiked };
}
