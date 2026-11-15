"""Step schedules carried from a custom stimulus into a recording."""

import numpy as np
import pandas as pd


STEP_COLUMNS = ("Scheduled step onset", "Scheduled step level (%)", "Scheduled step duration (samples)")
VOLTAGE_LOOP_COLUMN = "Voltage protocol loop start"
VOLTAGE_COLUMN = "Command voltage (mV)"
VOLTAGE_STEP_ONSET = "Scheduled voltage step onset"
VOLTAGE_STEP_DURATION = "Scheduled voltage step duration (samples)"
VOLTAGE_STEP_LEVEL = "Scheduled step voltage (mV)"
VOLTAGE_RANGE = (-110, 80)
NO_STEP = (0, np.nan, np.nan)


def read_step_schedule(frame, samples):
    """Decode step markers, including the original uniform step-generator format."""
    if "Step onset" not in frame:
        return {}
    flags = pd.to_numeric(frame["Step onset"], errors="raise").to_numpy()
    if not np.isin(flags, (0, 1)).all():
        raise ValueError("Step onset must contain only 0 and 1.")
    starts = np.flatnonzero(flags)
    if not len(starts):
        return {}
    limits = np.r_[starts[1:], len(samples)]

    if "Step duration (samples)" in frame:
        durations = pd.to_numeric(frame["Step duration (samples)"], errors="raise").to_numpy()[starts]
    else:
        # Older files mark onset only. Infer a common duration from visible steps.
        transitions = np.r_[np.flatnonzero(np.diff(samples)) + 1, len(samples)]
        visible = starts[(starts == 0) | (samples[starts] != samples[np.maximum(starts - 1, 0)])]
        widths = np.unique(transitions[np.searchsorted(transitions, visible, side="right")] - visible)
        if len(widths) != 1:
            raise ValueError("Step duration is ambiguous. Re-save this protocol in Stimulus Generator.")
        durations = np.full(len(starts), widths[0])

    if (not np.isfinite(durations).all() or np.any(durations != np.floor(durations))
            or np.any(durations < 1) or np.any(durations > limits - starts)):
        raise ValueError("Each marked step needs a valid duration within its cycle.")
    return {
        int(start): (1, float(samples[start]), int(duration))
        for start, duration in zip(starts, durations)
    }


def save_step_channels(frame, channels, samples, description, *, voltage=False):
    """Add optional scheduled events to the same sample rows as the traces."""
    if any(samples[0]):
        if any(len(values) != len(frame["Time (ms)"]) for values in samples):
            raise ValueError("Recorded step channels have different sample counts.")
        onset, level, duration = STEP_COLUMNS
        if voltage:
            onset, level, duration = VOLTAGE_STEP_ONSET, VOLTAGE_STEP_LEVEL, VOLTAGE_STEP_DURATION
        frame.update(zip((onset, level, duration), samples))
        channels[onset] = {"meaning": description, "encoding": "sample_flag"}
        channels[level] = {"meaning": "scheduled command at step onset", "units": "mV" if voltage else "%"}
        channels[duration] = {"meaning": "programmed step duration", "units": "samples"}
