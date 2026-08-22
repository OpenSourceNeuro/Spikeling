// SPDX-License-Identifier: GPL-3.0-or-later

import { TIMESTEP_MS } from "../model/izhikevich.ts";

/** The existing desktop emulator advances its model every 50 wall-clock ms. */
export const DESKTOP_UPDATE_INTERVAL_MS = 50;

/** Source-audited model-step counts for the desktop's ten speed positions. */
export const DESKTOP_STEPS_PER_UPDATE = [
  10, 20, 50, 100, 200, 500, 1_000, 2_000, 5_000, 10_000,
] as const;

export const DEFAULT_SPEED_INDEX = 2;

export interface SimulationSpeed {
  readonly index: number;
  readonly stepsPerUpdate: number;
  readonly stepsPerSecond: number;
  readonly simulatedMillisecondsPerUpdate: number;
  readonly realtimeMultiplier: number;
  readonly desktopLabelMultiplier: number;
}

/**
 * The desktop's x0.001..x1 label is not a wall-clock multiplier. Preserve the
 * historical label separately and expose the scientifically correct ratio.
 */
export function getSimulationSpeed(index: number): SimulationSpeed {
  if (
    !Number.isInteger(index) ||
    index < 0 ||
    index >= DESKTOP_STEPS_PER_UPDATE.length
  ) {
    throw new RangeError("Simulation speed must be an integer between 0 and 9.");
  }

  const stepsPerUpdate = DESKTOP_STEPS_PER_UPDATE[index];
  const simulatedMillisecondsPerUpdate = stepsPerUpdate * TIMESTEP_MS;

  return {
    index,
    stepsPerUpdate,
    stepsPerSecond: stepsPerUpdate * (1_000 / DESKTOP_UPDATE_INTERVAL_MS),
    simulatedMillisecondsPerUpdate,
    realtimeMultiplier:
      simulatedMillisecondsPerUpdate / DESKTOP_UPDATE_INTERVAL_MS,
    desktopLabelMultiplier: stepsPerUpdate / 10_000,
  };
}
