"""Seeded two-level stimulus on the custom playback sample grid."""

from dataclasses import dataclass
from decimal import Decimal, DecimalException

import numpy as np
import pandas as pd
from PySide6.QtWidgets import QFileDialog

from spikeling_gui.appearance.dialogs import show_popup
from spikeling_gui.appearance.theme_manager import theme_manager
from spikeling_gui.paths import data_directory, save_dialog_directory


STEP_MS = 0.1
MAX_SAMPLES = 6_000_000
PREVIEW_HOLDS = 20_000


@dataclass
class BinaryNoise:
    levels: np.ndarray
    hold_samples: int
    sample_count: int

    def frame(self):
        values = np.repeat(self.levels, self.hold_samples)[:self.sample_count]
        trigger = np.zeros(self.sample_count, dtype=np.int8)
        trigger[0] = 1
        return pd.DataFrame({"Stim": values, "Trigger": trigger})

    def preview(self):
        levels = self.levels[:PREVIEW_HOLDS]
        end = min(self.sample_count, len(levels) * self.hold_samples)
        boundaries = np.minimum(np.arange(len(levels) + 1) * self.hold_samples, end)
        return boundaries * STEP_MS, levels


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


def read_integer(editor, scale, label, limit):
    try:
        value = Decimal(editor.text().strip()) * scale
    except DecimalException as error:
        raise ValueError(f"Enter a valid {label}.") from error
    if not value.is_finite() or abs(value) > limit or value != value.to_integral_value():
        raise ValueError(f"Enter a valid {label} within the supported range.")
    return int(value)


def read_noise(window):
    ui = window.ui
    return generate_binary_noise(
        read_integer(ui.StimulusGenerator_BinaryNoise_lowEdit, 1, "low level in whole percent", 100),
        read_integer(ui.StimulusGenerator_BinaryNoise_highEdit, 1, "high level in whole percent", 100),
        read_integer(ui.StimulusGenerator_BinaryNoise_holdEdit, 10, "hold time in multiples of 0.1 ms", MAX_SAMPLES),
        read_integer(ui.StimulusGenerator_BinaryNoise_durationEdit, 10000, "duration in multiples of 0.0001 s", MAX_SAMPLES),
        read_integer(ui.StimulusGenerator_BinaryNoise_seedEdit, 1, "integer seed", 2**32 - 1),
    )


def preview_noise(window):
    try:
        stimulus = read_noise(window)
    except ValueError as error:
        show_popup(window, "Invalid binary noise settings", str(error))
        return
    x, levels = stimulus.preview()
    plot = window.ui.StimulusGenerator_Oscilloscope_widget
    plot.clear()
    plot.setLabel("left", "Stimulus", "%")
    plot.setLabel("bottom", "Time", "ms")
    title = ""
    if len(levels) < len(stimulus.levels):
        title = f"Preview of first {x[-1]:g} ms of {stimulus.sample_count * STEP_MS:g} ms"
    plot.setTitle(title)
    theme_manager.themed_plot(plot, x, levels, "neuron_stimulus", stepMode="center")
    plot.setXRange(0, x[-1], padding=0)
    plot.setYRange(-100, 100, padding=.02)
    theme_manager.style_traces()


def save_noise(window):
    try:
        stimulus = read_noise(window)
    except ValueError as error:
        show_popup(window, "Invalid binary noise settings", str(error))
        return
    path, _ = QFileDialog.getSaveFileName(
        window, "Save binary noise stimulus",
        save_dialog_directory(data_directory("Stimuli")), "CSV files (*.csv)",
    )
    if not path:
        return
    if not path.lower().endswith(".csv"):
        path += ".csv"
    try:
        stimulus.frame().to_csv(path, index=False)
    except (OSError, ValueError) as error:
        show_popup(window, "Cannot save binary noise stimulus", str(error))
