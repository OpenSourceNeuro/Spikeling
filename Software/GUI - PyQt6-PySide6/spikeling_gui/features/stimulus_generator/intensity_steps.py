"""Build, preview and save one cycle of an intensity-step protocol."""

from dataclasses import dataclass

import numpy as np
from spikeling_gui.stimulus_schedule import VOLTAGE_COLUMN, VOLTAGE_RANGE

from .cycle import MAX_SAMPLES, STEP_MS, read_duration, read_integer, read_pre_stimulus, stimulus_frame


MAX_STEPS = 1000


@dataclass
class StepCycle:
    samples: np.ndarray
    onsets: np.ndarray
    duration: int
    voltage: bool = False

    def frame(self):
        frame = stimulus_frame(self.samples)
        if self.voltage:
            frame = frame.rename(columns={"Stim": VOLTAGE_COLUMN})
        step_onset = np.zeros(len(self.samples), dtype=np.int8)
        step_onset[self.onsets] = 1
        duration = np.zeros(len(self.samples), dtype=np.int32)
        duration[self.onsets] = self.duration
        frame["Step onset"] = step_onset
        frame["Step duration (samples)"] = duration
        return frame


def build_step_cycle(count, first, increment, on, between, between_level, pre, pre_level,
                     post, post_level, *, voltage=False):
    """Construct one cycle. Durations are integer sample counts on the playback grid."""
    if not 1 <= count <= MAX_STEPS:
        raise ValueError(f"Enter a step count from 1 to {MAX_STEPS}.")
    if on < 1 or min(between, pre, post) < 0:
        raise ValueError("Step duration must be positive. Baseline and gap durations can be zero.")

    levels = first + increment * np.arange(count)
    levels = np.round(levels, 2) if voltage else levels
    low, high = VOLTAGE_RANGE if voltage else (-100, 100)
    if (np.min(levels) < low or np.max(levels) > high
            or not all(low <= level <= high for level in (pre_level, between_level, post_level))):
        units = "mV" if voltage else "%"
        raise ValueError(f"Every level must be between {low} and {high} {units}.")

    total = pre + count * on + (count - 1) * between + post
    if total > MAX_SAMPLES:
        raise ValueError(f"One cycle can last at most {MAX_SAMPLES * STEP_MS / 1000:g} seconds.")

    samples = np.full(total, between_level, dtype=float if voltage else np.int16)
    samples[:pre] = pre_level
    samples[total - post:] = post_level
    onsets = pre + np.arange(count) * (on + between)
    for start, level in zip(onsets, levels):
        samples[start:start + on] = level
    return StepCycle(np.round(samples, 2) if voltage else samples, onsets, on, voltage)


def read_steps(window):
    ui = window.ui
    pre, pre_level = read_pre_stimulus(ui)
    return build_step_cycle(
        count=read_integer(ui.Step_Number_Value, 1, "step count", MAX_STEPS),
        first=read_integer(ui.Step_First_Value, 1, "first step level in whole percent", 100),
        increment=read_integer(ui.Step_Increment_Value, 1, "step increment in whole percent", 200),
        on=read_duration(ui.Step_On_Value, "step duration"),
        between=read_duration(ui.Step_Off_Value, "time between steps"),
        between_level=read_integer(ui.Step_OffInt_Value, 1, "level between steps in whole percent", 100),
        pre=pre,
        pre_level=pre_level,
        post=read_duration(ui.Step_Inter_Value, "post-stimulus duration"),
        post_level=read_integer(ui.Step_InterInt_Value, 1, "post-stimulus level in whole percent", 100),
    )


def read_voltage_steps(window):
    ui = window.ui
    hold = read_integer(ui.StimulusGenerator_VoltageHold_edit, 100, "holding voltage (mV)", 11000) / 100
    return build_step_cycle(
        count=read_integer(ui.StimulusGenerator_VoltageCount_edit, 1, "step count", MAX_STEPS),
        first=read_integer(ui.StimulusGenerator_VoltageFirst_edit, 100, "first step voltage (mV)", 11000) / 100,
        increment=read_integer(ui.StimulusGenerator_VoltageIncrement_edit, 100,
                               "voltage increment (mV)", 19000) / 100,
        on=read_duration(ui.StimulusGenerator_VoltageOn_edit, "step duration"),
        between=read_duration(ui.StimulusGenerator_VoltageGap_edit, "time between steps"),
        between_level=hold,
        pre=read_duration(ui.StimulusGenerator_PreDuration_edit, "pre-stimulus duration"),
        pre_level=hold,
        post=read_duration(ui.StimulusGenerator_VoltagePost_edit, "post-stimulus duration"),
        post_level=hold,
        voltage=True,
    )
