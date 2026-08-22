// SPDX-License-Identifier: GPL-3.0-or-later

import type { PhotoreceptorControls, PhotoreceptorState } from "./types.ts";

export function createPhotoreceptorState(): PhotoreceptorState {
  return {
    recovery: 1,
    decay: 0.001,
    recoveryRate: 0.025,
  };
}

/**
 * Preserve the desktop ordering: use the previous decay/recovery coefficients
 * for this sample, then refresh those coefficients from the current controls.
 */
export function stepPhotoreceptor(
  state: PhotoreceptorState,
  stimulus: number,
  controls: PhotoreceptorControls,
): number {
  const polarity = controls.gain >= 0 ? 1 : -1;
  const current = (stimulus / 25) * (controls.gain / 0.5) * state.recovery;

  if (state.recovery > 0) {
    state.recovery -= polarity * state.decay * current;
  }
  if (state.recovery < 0) {
    state.recovery = 0;
  }
  if (state.recovery < 1) {
    state.recovery += state.recoveryRate;
  }

  state.decay = controls.decaySlider / 100000;
  state.recoveryRate = controls.recoverySlider / 1000;

  return current;
}
