"""CSV recordings and time-domain analysis shared by the analysis views."""

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from spikeling_gui.paths import data_directory
from spikeling_gui.stimulus_schedule import (
    STEP_COLUMNS, VOLTAGE_LOOP_COLUMN, VOLTAGE_STEP_DURATION, VOLTAGE_STEP_LEVEL, VOLTAGE_STEP_ONSET,
)
from spikeling_gui.recording_metadata import read_metadata, stream_digest


NEURON_NAMES = ("Spikeling", "AuxNeuron1", "AuxNeuron2")
VOLTAGE_COLUMNS = ("Spikeling Vm (mV)", "Synapse 1 Vm (mV)", "Synapse 2 Vm (mV)")
TIME_COLUMN = "Time (ms)"
STIMULUS_COLUMN = "Stimulus (%)"
TRIGGER_COLUMN = "Trigger"
GAP_FACTOR = 1.5
OPTIONAL_COLUMNS = {
    **dict(zip(("step_onset", "step_level", "step_duration"), STEP_COLUMNS)),
    "voltage_loop_start": VOLTAGE_LOOP_COLUMN,
    "voltage_step_level": VOLTAGE_STEP_LEVEL,
    "voltage_step_onset": VOLTAGE_STEP_ONSET,
    "voltage_step_duration": VOLTAGE_STEP_DURATION,
    "command_current": "Command current (a.u.)",
    "command_voltage": "Command voltage (mV)",
    "presynaptic_events": "Presynaptic events",
    "presynaptic_events_1": "Presynaptic events 1",
    "presynaptic_events_2": "Presynaptic events 2",
}


@dataclass(frozen=True)
class Recording:
    source: Path
    recording_id: str
    clamp_mode: str
    time_ms: np.ndarray
    stimulus: np.ndarray
    trigger: np.ndarray
    voltage: tuple[np.ndarray, ...]
    current: tuple[np.ndarray, ...]
    current_columns: tuple[str, ...]
    nominal_step_ms: float
    gap_before: np.ndarray
    extra_channels: dict[str, np.ndarray] = field(default_factory=dict)
    acquisition: dict | None = None
    acquisition_warning: str = ""

    def metadata(self):
        return {
            "Recording ID": self.recording_id,
            "Recording": self.source.name,
            "Clamp mode": self.clamp_mode,
            "Acquisition source": self.acquisition["source"] if self.acquisition else None,
            "Acquisition timebase": self.acquisition["timebase"]["kind"] if self.acquisition else None,
        }


@dataclass(frozen=True)
class SpikeAnalysis:
    threshold_mv: float
    indices: tuple[np.ndarray, ...]
    rates_hz: tuple[np.ndarray, ...]


@dataclass(frozen=True)
class Cycles:
    duration_ms: float
    time_ms: np.ndarray
    starts_ms: np.ndarray
    stimulus: np.ndarray
    voltage: tuple[np.ndarray, ...]
    current: tuple[np.ndarray, ...]
    rates_hz: tuple[np.ndarray, ...] | None
    spike_times_ms: tuple[tuple[np.ndarray, ...], ...] | None
    excluded: int
    protocol_aligned: bool = False


def load_recording(source):
    source = Path(source)
    with source.open("rb") as handle:
        digest = stream_digest(handle)
        handle.seek(0)
        frame = pd.read_csv(handle)

    if "Clamp current (nA)" in frame and "Total Current Input (a.u.)" in frame:
        raise ValueError("The recording contains both current-clamp and voltage-clamp headers.")
    vc = "Clamp current (nA)" in frame
    unit = "nA" if vc else "a.u."
    current = (
        "Clamp current (nA)" if vc else "Total Current Input (a.u.)",
        f"Synapse 1 Input ({unit})",
        f"Synapse 2 Input ({unit})",
    )
    columns = (TIME_COLUMN, STIMULUS_COLUMN, TRIGGER_COLUMN, *VOLTAGE_COLUMNS, *current)
    missing = [column for column in columns if column not in frame]
    if missing:
        raise ValueError("Missing recording columns: " + ", ".join(missing))

    optional = {role: name for role, name in OPTIONAL_COLUMNS.items() if name in frame}
    values = {}
    for column in (*columns, *optional.values()):
        try:
            data = pd.to_numeric(frame[column], errors="raise").to_numpy(dtype=float)
        except (TypeError, ValueError) as error:
            raise ValueError(f"{column} contains non-numeric values.") from error
        if np.isinf(data).any():
            raise ValueError(f"{column} contains infinite values.")
        values[column] = data

    time = values[TIME_COLUMN]
    steps = np.diff(time)
    if time.size < 2 or not np.isfinite(time).all() or not np.all(steps > 0):
        raise ValueError("Time (ms) must contain at least two finite, strictly increasing samples.")
    step = float(np.median(steps))
    mode = "VC" if vc else "CC"
    acquisition, warning = read_metadata(source, digest, len(time), mode)
    return Recording(
        source, digest, mode, time,
        values[STIMULUS_COLUMN], values[TRIGGER_COLUMN],
        tuple(values[column] for column in VOLTAGE_COLUMNS),
        tuple(values[column] for column in current), current, step,
        np.r_[False, steps > GAP_FACTOR * step],
        {role: values[name] for role, name in optional.items()},
        acquisition, warning,
    )


def presynaptic_event_indices(recording, role):
    """Decode a synapse event channel, including older emulator high-state exports."""
    flags = recording.extra_channels[role]
    valid = np.isfinite(flags)
    high = valid & (flags > 0)
    metadata = recording.acquisition or {}
    channels = metadata.get("channels")
    descriptor = channels.get(OPTIONAL_COLUMNS[role], {}) if isinstance(channels, dict) else {}
    if (metadata.get("source") == "emulator" and isinstance(descriptor, dict)
            and descriptor.get("encoding") == "sample_flag"):
        return np.flatnonzero(high[1:] & valid[:-1] & ~high[:-1] & ~recording.gap_before[1:]) + 1
    return np.flatnonzero(high)


def detect_spikes(recording, threshold_mv):
    if not np.isfinite(threshold_mv):
        raise ValueError("Enter a finite voltage threshold in mV.")
    indices = []
    rates = []
    time = recording.time_ms
    for vm in recording.voltage:
        valid_edge = (
            np.isfinite(vm[:-1]) & np.isfinite(vm[1:]) & ~recording.gap_before[1:]
        )
        events = np.flatnonzero(
            valid_edge & (vm[:-1] <= threshold_mv) & (vm[1:] > threshold_mv)
        ) + 1
        rate = np.full(time.size, np.nan)
        breaks = np.r_[0, np.cumsum(~valid_edge)]
        for first, second in zip(events[:-1], events[1:]):
            if breaks[first] == breaks[second]:
                rate[first:second] = 1000.0 / (time[second] - time[first])
        indices.append(events)
        rates.append(rate)
    return SpikeAnalysis(threshold_mv, tuple(indices), tuple(rates))


def trigger_onsets(recording):
    trigger = recording.trigger
    # Legacy files can start exactly on their one-sample cycle marker.
    starts_on_marker = trigger[0] == 1 and trigger[1] == 0 and not recording.gap_before[1]
    onsets = np.flatnonzero(
        (trigger[1:] == 1) & np.isfinite(trigger[:-1]) & (trigger[:-1] != 1)
        & ~recording.gap_before[1:]
    ) + 1
    return np.r_[0, onsets] if starts_on_marker else onsets


def custom_step_cycles(recording):
    """Match a saved board step protocol to observed triggers and stimulus pulses."""
    metadata = recording.acquisition or {}
    if metadata.get("source") != "board":
        return None
    protocols = set()
    for snapshot in metadata.get("settings_at_sample", []):
        stimulus = snapshot.get("settings", {}).get("stimulus", {})
        if stimulus.get("kind") == "custom":
            name = stimulus.get("name")
            size = stimulus.get("samples_per_loop")
            interval = stimulus.get("nominal_step_ms")
            if (isinstance(name, str) and name and Path(name).name == name
                    and isinstance(size, int) and size > 0
                    and isinstance(interval, (int, float)) and np.isfinite(interval) and interval > 0):
                protocols.add((name, size, interval))
    if len(protocols) != 1:
        return None

    name, size, interval = protocols.pop()
    if not np.isclose(interval, recording.nominal_step_ms, rtol=1e-6):
        return None
    filename = name if name.lower().endswith(".csv") else f"{name}.csv"
    try:
        protocol = pd.read_csv(data_directory("Stimuli") / filename, usecols=["Stim", "Trigger"])
        values = np.asarray(protocol["Stim"], dtype=float)
        triggers = np.asarray(protocol["Trigger"], dtype=float)
    except (OSError, ValueError):
        return None
    if (len(values) != size or not np.isfinite(values).all()
            or not np.array_equal(np.flatnonzero(triggers), [0])):
        return None

    def pulse_edges(signal):
        active = np.isfinite(signal) & (signal != 0)
        edges = np.diff(np.r_[False, active, False].astype(int))
        return np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)

    expected_starts, expected_stops = pulse_edges(values)
    if not len(expected_starts):
        return None
    levels = values[expected_starts]
    if any(np.any(values[start:stop] != level)
           for start, stop, level in zip(expected_starts, expected_stops, levels)):
        return None

    def matches_plateau(start, stop, level):
        # Ignore the filter settling and release when checking the pulse level.
        trim = (stop - start) // 4
        middle = recording.stimulus[start + trim:stop - trim]
        return np.all(np.abs(middle - level) <= 0.5)

    # Host playback advances on received packets. Allow small onset differences
    # and a longer falling edge from the board's stimulus filter.
    onset_tolerance_ms = 2.0
    recovery_tolerance_ms = 3.0
    time = recording.time_ms
    duration = size * interval
    if expected_stops[-1] * interval > duration - recovery_tolerance_ms:
        return None
    observed_starts, observed_stops = pulse_edges(recording.stimulus)
    observed_times = time[observed_starts]
    matches = []
    for anchor in trigger_onsets(recording):
        cycle_end = time[anchor] + duration
        first = np.searchsorted(observed_starts, anchor)
        last = np.searchsorted(observed_times, cycle_end - onset_tolerance_ms)
        if last - first != len(levels):
            continue
        starts, stops = observed_starts[first:last], observed_stops[first:last]
        if stops[-1] >= len(time):
            continue
        if (np.any(np.abs(time[starts] - time[anchor] - expected_starts * interval) > onset_tolerance_ms)
                or np.any(np.abs(time[stops] - time[anchor] - expected_stops * interval) > recovery_tolerance_ms)):
            continue
        if any(np.any(recording.gap_before[start:stop + 1])
               or not matches_plateau(start, stop, level)
               for start, stop, level in zip(starts, stops, levels)):
            continue
        matches.append((anchor, starts, stops))
    if not matches:
        return None
    return duration, (expected_stops - expected_starts) * interval, matches


def align_cycles(recording, spikes=None):
    """Align complete stimulus cycles with a clearly identifiable period."""
    time = recording.time_ms
    onsets = trigger_onsets(recording)
    protocol = custom_step_cycles(recording)
    step = recording.nominal_step_ms
    if protocol is not None:
        duration, _, matches = protocol
        onsets = np.array([anchor for anchor, _, _ in matches])
        start_times = time[onsets]
        interval_ms = np.diff(start_times)
    else:
        if onsets.size < 2:
            raise ValueError("Two observed trigger onsets are needed to estimate the cycle duration.")
        start_times = time[onsets]
        interval_ms = np.diff(start_times)
        # Intervals within one sample of a candidate period support that estimate.
        # Use sorted bounds so this remains inexpensive on recordings with many cycles.
        ordered = np.sort(interval_ms)
        left = np.searchsorted(ordered, ordered - step, side="left")
        right = np.searchsorted(ordered, ordered + step, side="right")
        support = right - left
        best = np.flatnonzero(support == support.max())
        if ordered[best[-1]] - ordered[best[0]] > step:
            raise ValueError("Trigger intervals have no clear repeated duration.")
        central = best[len(best) // 2]
        duration = float(np.median(ordered[left[central]:right[central]]))
    samples = max(1, int(round(duration / step)))
    relative = np.arange(samples, dtype=float) * (duration / samples)
    kept = []
    ends = []
    gaps = np.r_[0, np.cumsum(recording.gap_before)]

    for i, start in enumerate(onsets):
        if protocol is None and i + 1 < len(onsets) and abs(interval_ms[i] - duration) > step:
            continue
        end = time[start] + duration
        # The last recorded sample supports at most one nominal sample interval.
        if end > time[-1] + step + step * 1e-6:
            continue
        if protocol is None and i + 1 < len(onsets) and time[onsets[i + 1]] < end - step * 1e-6:
            if time[start] + relative[-1] >= time[onsets[i + 1]] - step * 1e-6:
                continue
        target = time[start] + relative
        last = int(np.searchsorted(time, target[-1] - step * 1e-6))
        if i + 1 < len(onsets) and last >= onsets[i + 1]:
            if protocol is None:
                continue
            last = onsets[i + 1] - 1
        if last >= len(time) or gaps[last + 1] != gaps[start + 1]:
            continue
        kept.append(start)
        ends.append(min(end, start_times[i + 1]) if i + 1 < len(onsets) else end)

    if not kept:
        raise ValueError("No complete cycles with a continuous time axis were found.")
    starts = time[kept]
    targets = starts[:, None] + relative
    # Map a common relative grid onto recorded samples. Stimulus and rate are held
    # at their recorded values, and voltage/current are interpolated locally.
    held = np.searchsorted(time, targets + step * 1e-6, side="right") - 1

    exact = np.abs(time[held] - targets) <= step * 1e-6
    targets[exact] = time[held[exact]]

    valid = targets < np.asarray(ends)[:, None] - step * 1e-6

    def continuous(values):
        return np.where(valid, np.interp(targets, time, values, left=np.nan, right=np.nan), np.nan)

    spike_times = None
    rates = None
    if spikes is not None:
        rates = tuple(np.where(valid, rate[held], np.nan) for rate in spikes.rates_hz)
        spike_times = tuple(
            tuple(
                events[np.searchsorted(events, start):np.searchsorted(events, end - step * 1e-6)] - start
                for start, end in zip(starts, ends)
            )
            for events in (time[indices] for indices in spikes.indices)
        )
    return Cycles(
        duration, relative, starts, np.where(valid, recording.stimulus[held], np.nan),
        tuple(continuous(trace) for trace in recording.voltage),
        tuple(continuous(trace) for trace in recording.current),
        rates, spike_times, len(onsets) - len(kept), protocol is not None,
    )
