// SPDX-License-Identifier: GPL-3.0-or-later

import type { StimulusControls, StimulusResult, StimulusState } from "./types.ts";

export const INITIAL_STIMULUS_PERIOD_STEPS = 1000;
export const STIMULUS_DUTY_CYCLE_STEPS = 500;
export const MINIMUM_STIMULUS_PERIOD_OFFSET = 10;

export function createStimulusState(): StimulusState {
  return {
    counter: 0,
    steps: INITIAL_STIMULUS_PERIOD_STEPS,
    triggerPending: false,
    customIndex: 0,
    customResetPending: true,
  };
}

export function stepStimulus(
  state: StimulusState,
  controls: StimulusControls,
): StimulusResult {
  if (controls.mode === "custom" && controls.customSamples.length > 0) {
    let trigger: 0 | 1 = 0;

    if (state.customResetPending) {
      state.customIndex = 0;
      state.customResetPending = false;
      trigger = 1;
    }

    if (state.customIndex >= controls.customSamples.length) {
      state.customIndex = 0;
      trigger = 1;
    }

    const value = controls.customSamples[state.customIndex];
    state.customIndex += 1;
    return { value, trigger };
  }

  const trigger: 0 | 1 = state.triggerPending ? 1 : 0;
  state.triggerPending = false;

  const halfPeriod = Math.floor(state.steps / 2);
  const value = state.counter < halfPeriod ? controls.strength : 0;

  state.counter += 1;
  if (state.counter >= state.steps) {
    state.counter = 0;
    state.triggerPending = true;

    const frequency = Math.max(
      -100,
      Math.min(100, Math.trunc(-controls.frequencySlider)),
    );

    state.steps = Math.max(
      1,
      Math.trunc(
        STIMULUS_DUTY_CYCLE_STEPS +
          (frequency * STIMULUS_DUTY_CYCLE_STEPS) / 100 +
          MINIMUM_STIMULUS_PERIOD_OFFSET,
      ),
    );
  }

  return { value, trigger };
}
