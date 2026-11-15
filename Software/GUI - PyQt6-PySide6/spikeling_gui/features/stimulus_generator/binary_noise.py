"""Seeded two-level stimulus on the custom playback sample grid."""

from dataclasses import dataclass

import numpy as np

from .cycle import MAX_SAMPLES, check_cycle_size, read_integer, read_pre_stimulus


@dataclass
class BinaryNoise:
    levels: np.ndarray
    hold_samples: int
    sample_count: int

    def samples(self):
        return np.repeat(self.levels, self.hold_samples)[:self.sample_count]


def generate_binary_noise(low, high, hold_samples, sample_count, seed):
    if not -100 <= low < high <= 100:
        raise ValueError("Enter integer levels from −100 to 100 with low below high.")
    if not 1 <= sample_count <= MAX_SAMPLES:
        raise ValueError("Duration must be between 0.0001 and 600 seconds.")
    if not 1 <= hold_samples <= sample_count:
        raise ValueError("Hold time must be at least 0.1 ms and fit within the stimulus.")
    if not 0 <= seed <= 2**32 - 1:
        raise ValueError("Enter a random seed from 0 to 4294967295.")
    holds = (sample_count + hold_samples - 1) // hold_samples
    rng = np.random.default_rng(seed)
    levels = np.where(rng.integers(0, 2, size=holds, dtype=np.int8), high, low).astype(np.int8)
    return BinaryNoise(levels, hold_samples, sample_count)


def read_noise(window):
    ui = window.ui
    pre, pre_level = read_pre_stimulus(ui)
    duration = read_integer(ui.StimulusGenerator_BinaryNoise_durationEdit, 10000,
                            "duration in multiples of 0.1 ms", MAX_SAMPLES)
    check_cycle_size(pre + duration)
    noise = generate_binary_noise(
        read_integer(ui.StimulusGenerator_BinaryNoise_lowEdit, 1, "low level in whole percent", 100),
        read_integer(ui.StimulusGenerator_BinaryNoise_highEdit, 1, "high level in whole percent", 100),
        read_integer(ui.StimulusGenerator_BinaryNoise_holdEdit, 10, "hold time in multiples of 0.1 ms", MAX_SAMPLES),
        duration,
        read_integer(ui.StimulusGenerator_BinaryNoise_seedEdit, 1, "integer seed", 2**32 - 1),
    )
    return np.concatenate((np.full(pre, pre_level, dtype=np.int16), noise.samples()))
