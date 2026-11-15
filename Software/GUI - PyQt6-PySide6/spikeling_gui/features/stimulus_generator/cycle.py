"""Shared sample grid, input validation and preview for custom stimuli."""

from decimal import Decimal, DecimalException

import numpy as np
import pandas as pd
from PySide6.QtWidgets import QFileDialog

from spikeling_gui.appearance.dialogs import show_popup
from spikeling_gui.appearance.theme_manager import theme_manager
from spikeling_gui.stimulus_schedule import VOLTAGE_RANGE
from spikeling_gui.paths import data_directory, save_dialog_directory


STEP_MS = 0.1
MAX_SAMPLES = 6_000_000
MAX_PREVIEW_TRANSITIONS = 100_000


def read_integer(editor, scale, label, limit):
    try:
        value = Decimal(editor.text().strip()) * scale
    except DecimalException as error:
        raise ValueError(f"Enter a valid {label}.") from error
    if not value.is_finite() or abs(value) > limit or value != value.to_integral_value():
        raise ValueError(f"Enter a valid {label} within the supported range.")
    return int(value)


def read_duration(editor, label):
    duration = read_integer(editor, 10, f"{label} in multiples of 0.1 ms", MAX_SAMPLES)
    if duration < 0:
        raise ValueError(f"{label.capitalize()} must be zero or greater.")
    return duration


def read_pre_stimulus(ui):
    duration = read_duration(ui.StimulusGenerator_PreDuration_edit, "pre-stimulus duration")
    level = read_integer(ui.StimulusGenerator_PreLevel_edit, 1, "pre-stimulus level in whole percent", 100)
    return duration, level


def check_cycle_size(sample_count):
    if not 1 <= sample_count <= MAX_SAMPLES:
        raise ValueError("One loop must last between 0.1 ms and 600 seconds.")


def stimulus_frame(samples):
    trigger = np.zeros(len(samples), dtype=np.int8)
    trigger[0] = 1
    return pd.DataFrame({"Stim": samples, "Trigger": trigger})


def draw_cycle(window, samples, onsets=None, *, voltage=False):
    plot = window.ui.StimulusGenerator_Oscilloscope_widget
    plot.clear()
    plot.setLabel("left", "Command voltage" if voltage else "Stimulus", units="mV" if voltage else "%")
    plot.setLabel("bottom", "Model time", units="ms")
    theme_manager.set_plot_background_role(plot, "panel_background")
    transitions = np.r_[0, np.flatnonzero(np.diff(samples)) + 1, len(samples)]
    time = transitions[:MAX_PREVIEW_TRANSITIONS + 1] * STEP_MS
    theme_manager.themed_plot(plot, time, samples[transitions[:len(time) - 1]],
                              "neuron_stimulus", stepMode="center")
    title = f"{len(samples) * STEP_MS:g} ms per loop"
    if len(time) < len(transitions):
        title += f" · Preview of first {time[-1]:g} ms"
    if onsets is not None:
        theme_manager.themed_plot(plot, onsets * STEP_MS, samples[onsets],
                                  "text_primary", symbol="o", symbol_size=5)
        title += " · Dots mark step onsets"
    plot.setTitle(title)
    plot.setXRange(0, time[-1], padding=0.02)
    plot.setYRange(*(VOLTAGE_RANGE if voltage else (-100, 100)), padding=0.04)
    theme_manager.style_traces()


def save_cycle(window, build_frame):
    path, _ = QFileDialog.getSaveFileName(
        window, "Save stimulus", save_dialog_directory(data_directory("Stimuli")), "CSV files (*.csv)",
    )
    if not path:
        return False
    if not path.lower().endswith(".csv"):
        path += ".csv"
    try:
        build_frame().to_csv(path, index=False)
    except (OSError, ValueError) as error:
        show_popup(window, "Cannot save stimulus", str(error))
        return False
    return True
