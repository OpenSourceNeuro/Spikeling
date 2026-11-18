"""Matching and measurement for two-condition recording comparisons."""

from dataclasses import dataclass, replace

import numpy as np

from .recording import detect_spikes, presynaptic_event_indices
from .sweep_analysis import (
    Step, command_windows, detect_steps, measure_sweep, review_windows, sample_bounds, scheduled_steps,
    window_available,
)


CC = "CC pharmacology"
VC = "VC pharmacology"
STP = "STP paired pulse"
TRAIN = "STP train"
STIM = "Recorded stimulus (%)"
COMMAND = "Recorded clamp command"
EVENT = "Recorded presynaptic events"
EVENT_1 = "Presynaptic events · Synapse 1"
EVENT_2 = "Presynaptic events · Synapse 2"
EVENT_SOURCES = (EVENT, EVENT_1, EVENT_2)
PROXY = "Stimulus pulses as input events"
SIGNALS = {
    (CC, COMMAND): ("command_current", "Command current (a.u.)"),
    (VC, COMMAND): ("command_voltage", "Command voltage (mV)"),
    (STP, EVENT): ("presynaptic_events", "Presynaptic events"),
    (TRAIN, EVENT): ("presynaptic_events", "Presynaptic events"),
    **{(preset, source): (f"presynaptic_events_{channel}", f"Presynaptic events {channel}")
       for preset in (STP, TRAIN) for channel, source in enumerate((EVENT_1, EVENT_2), 1)},
}
METRICS = {
    CC: ("Spike count", "Rate (Hz)", "First-spike latency (ms)", "Spiked (%)"),
    VC: ("Peak inward ΔI (nA)", "Peak outward ΔI (nA)", "Late mean current (nA)",
         "Peak change (nA)"),
    STP: ("Response 1", "Response 2", "Paired-pulse ratio"),
    TRAIN: ("Response amplitude", "Response probability (%)", "Successful response amplitude"),
}


@dataclass
class Condition:
    label: str
    recording: object
    start: float
    end: float
    reviewed: tuple | None = None
    provenance: str = "CSV · detected steps"
    reviewed_baseline: float = 0
    reviewed_source: str = STIM


@dataclass
class Settings:
    preset: str
    source: str
    baseline: float = 0
    amplitude_tolerance: float = 0.5
    time_tolerance: float = 0.5
    minimum_step: float = 2
    pre: float = 10
    window: float = 5
    threshold: float = -20
    pair_interval: float = 100
    ratio_floor: float = 0.1
    neuron: int = 0
    current_response: bool = False
    match_history: bool = False
    response_floor: float = 0.1
    probe_limit: float | None = None


@dataclass
class Trial:
    condition: Condition
    onset: float
    offset: float
    start: float
    end: float
    key: tuple
    label: str
    metrics: dict
    signal: np.ndarray
    stimulus: np.ndarray
    response_unit: str
    second_onset: float | None = None
    review: str = ""
    pulses: tuple = ()


def source_signal(recording, settings):
    if settings.source in (STIM, PROXY):
        return recording.stimulus, "Stimulus (%)"
    role, label = SIGNALS[(settings.preset, settings.source)]
    values = recording.extra_channels.get(role)
    if values is None or not np.isfinite(values).any():
        raise ValueError(f"{recording.source.name} has no usable {label} channel. Select an available input source.")
    return values, label


def response_signal(recording, settings):
    if settings.preset == VC or (settings.preset in (STP, TRAIN) and settings.current_response):
        return recording.current[settings.neuron], "nA" if recording.clamp_mode == "VC" else "a.u."
    return recording.voltage[settings.neuron], "mV"


def condition_trials(condition, settings):
    rec = condition.recording
    if settings.preset in (CC, VC) and rec.clamp_mode != settings.preset[:2]:
        raise ValueError(f"{condition.label} requires a {settings.preset[:2]} recording.")
    stimulus, _ = source_signal(rec, settings)
    signal, unit = response_signal(rec, settings)
    if settings.preset == STP:
        return paired_trials(condition, settings, stimulus, signal, unit)
    if settings.preset == TRAIN:
        from .train_analysis import train_trials

        return train_trials(condition, settings, stimulus, signal, unit)
    reviewed = condition.reviewed is not None and settings.source == condition.reviewed_source
    use_voltage = settings.preset == VC and settings.source == COMMAND
    if reviewed:
        sweeps = condition.reviewed
    else:
        command = replace(rec, stimulus=stimulus)
        steps = None
        if use_voltage:
            steps = scheduled_steps(rec, 0, 0.5, settings.minimum_step, None, voltage=True)
        elif settings.source == STIM:
            steps = scheduled_steps(rec, settings.baseline, settings.amplitude_tolerance,
                                    settings.minimum_step, None)
        if steps is None:
            steps = detect_steps(command, settings.baseline, settings.amplitude_tolerance,
                                 settings.minimum_step)
        sweeps = review_windows(rec, steps, settings.pre, 0)
    spikes = detect_spikes(rec, settings.threshold) if settings.preset == CC else None
    result, excluded = [], 0
    for sweep in sweeps:
        step = sweep.step
        start = max(sweep.baseline_start_ms, step.onset_ms - settings.pre)
        if step.issue or not condition.start <= start < step.offset_ms <= condition.end:
            excluded += 1
            continue
        holding = settings.baseline
        scheduled_voltage = use_voltage and step.nominal_duration_ms is not None
        if scheduled_voltage:
            samples = command_windows(rec, sweep, stimulus, baseline_start=start, settled=True)
            if samples is None:
                excluded += 1
                continue
            before, active = samples
            if max(np.ptp(before), np.ptp(active)) > settings.amplitude_tolerance:
                excluded += 1
                continue
            holding = float(np.median(before))
            amplitude = float(np.median(active)) - holding
        elif settings.source == COMMAND:
            lo, hi = sample_bounds(rec, start, step.onset_ms)
            if not window_available(rec, lo, hi, stimulus):
                excluded += 1
                continue
            holding = float(np.median(stimulus[lo:hi]))
        elif reviewed:
            # Keep the baseline used for amplitude detection when taking a reviewed snapshot.
            holding = condition.reviewed_baseline
        if not scheduled_voltage:
            lo, hi = sample_bounds(rec, step.onset_ms, step.offset_ms)
            if not window_available(rec, lo, hi, stimulus):
                excluded += 1
                continue
            amplitude = float(np.median(stimulus[lo:hi])) - holding
            if settings.source == STIM and step.nominal_duration_ms is not None and not reviewed:
                amplitude = step.amplitude
        duration = step.grouping_duration_ms
        key = (amplitude, duration, holding)
        if settings.match_history:
            if step.position is None or step.preceding_off_ms is None:
                excluded += 1
                continue
            key += (step.position, step.preceding_off_ms)
        measure = measure_sweep(rec, replace(sweep, baseline_start_ms=start),
                                settings.neuron, signal, spikes, settings.window)
        names = METRICS[settings.preset]
        if settings.preset == CC:
            metrics = dict(zip(names, (measure.get("count"), measure.get("rate"),
                                       measure.get("latency"), 100 * (measure["count"] > 0) if "count" in measure else None)))
        else:
            metrics = {name: measure.get(key) for name, key in zip(names, ("peak_inward", "peak_outward", "late", "peak"))}
        result.append(Trial(condition, step.onset_ms, step.offset_ms, start, step.offset_ms, key,
                            f"{amplitude:g} · {duration:g} ms", metrics, signal, stimulus, unit))
    return result, excluded


def pulse_events(recording, settings, stimulus):
    if settings.source in (EVENT_1, EVENT_2):
        role, _ = SIGNALS[(settings.preset, settings.source)]
        times = recording.time_ms[presynaptic_event_indices(recording, role)]
        return [Step(index, time, time, None, None, None) for index, time in enumerate(times, 1)]
    if settings.source == EVENT:
        valid = np.isfinite(stimulus)
        rises = valid[1:] & valid[:-1] & ~recording.gap_before[1:] & (stimulus[1:] > 0) & (stimulus[:-1] <= 0)
        times = recording.time_ms[np.flatnonzero(rises) + 1]
        return [Step(index, time, time, None, None, None) for index, time in enumerate(times, 1)]
    detected = detect_steps(replace(recording, stimulus=stimulus), settings.baseline,
                            settings.amplitude_tolerance, settings.minimum_step)
    # Keep candidates with questionable edges in the sequence so they cannot
    # disappear and turn a train into an apparent pair.
    return detected


def paired_trials(condition, settings, stimulus, signal, unit):
    rec = condition.recording
    events = pulse_events(rec, settings, stimulus)
    if not events:
        return [], 0
    times = np.array([event.onset_ms for event in events])
    groups = np.split(np.arange(len(events)), np.flatnonzero(np.diff(times) > settings.pair_interval) + 1)
    result, excluded = [], 0
    for group in groups:
        if len(group) != 2:
            excluded += 1
            continue
        first, second = (events[index] for index in group)
        t1, t2 = first.onset_ms, second.onset_ms
        start, end = t1 - settings.pre, t2 + settings.window
        if first.issue or second.issue or not condition.start <= start < end <= condition.end:
            excluded += 1
            continue
        if group[0] and start < times[group[0] - 1] + settings.window:
            excluded += 1
            continue
        if group[-1] + 1 < len(times) and end > times[group[-1] + 1]:
            excluded += 1
            continue
        if t2 - t1 < settings.window:
            excluded += 1
            continue
        # Use a baseline immediately before each pulse, clipped to the available
        # inter-pulse interval. Response 2 is measured relative to that baseline.
        response = []
        for at, lower in ((t1, start), (t2, max(t1 + settings.window, t2 - settings.pre))):
            left, on = sample_bounds(rec, lower, at)
            _, stop = sample_bounds(rec, at, at + settings.window)
            if not (window_available(rec, left, on, signal) and window_available(rec, on, stop, signal)):
                response.append(None)
                continue
            change = signal[on:stop] - np.mean(signal[left:on])
            response.append(float(change[np.argmax(np.abs(change))]))
        a, b = response
        ratio = b / a if a is not None and b is not None and abs(a) >= settings.ratio_floor else None
        review = ""
        if a is None or b is None:
            review = "Response window or baseline unavailable"
        elif ratio is None:
            review = "Response 1 below ratio floor"
        interval = t2 - t1
        key = (interval,)
        if settings.source == PROXY:
            key += (first.amplitude, second.amplitude, first.offset_ms - t1, second.offset_ms - t2)
        result.append(Trial(condition, t1, end, start, end, key, f"{interval:g} ms",
                            dict(zip(METRICS[STP], (a, b, ratio))), signal, stimulus, unit, t2, review))
    return result, excluded


def tolerances(settings):
    amp, time = settings.amplitude_tolerance, settings.time_tolerance
    if settings.preset == STP:
        return np.array([time] if settings.source in EVENT_SOURCES else [time, amp, amp, time, time])
    return np.array([amp, time, amp, 0, time] if settings.match_history else [amp, time, amp])


def matched_groups(reference, comparison, settings):
    if settings.preset == TRAIN:
        from .train_analysis import train_tolerance

        def tolerance(key):
            return train_tolerance(key, settings)
    else:
        fixed = tolerances(settings)

        def tolerance(key):
            return fixed

    def compatible(low, high):
        if settings.preset == TRAIN and np.any(low[:2] != high[:2]):
            return False
        return bool(np.all(high - low <= tolerance(low) + 1e-9))

    def group(trials):
        groups, bounds = [], []
        for trial in sorted(trials, key=lambda item: item.key):
            point = np.asarray(trial.key)
            for i, (low, high) in enumerate(bounds):
                if low.shape != point.shape:
                    continue
                lower, upper = np.minimum(low, point), np.maximum(high, point)
                if compatible(lower, upper):
                    groups[i].append(trial)
                    bounds[i] = lower, upper
                    break
            else:
                groups.append([trial])
                bounds.append((point, point))
        return groups, bounds

    left, left_bounds = group(reference)
    right, right_bounds = group(comparison)
    matches = [
        [j for j, (right_low, right_high) in enumerate(right_bounds)
         if left_low.shape == right_low.shape
         and compatible(np.minimum(left_low, right_low), np.maximum(left_high, right_high))]
        for left_low, left_high in left_bounds
    ]
    reverse = {j: sum(j in indices for indices in matches) for j in range(len(right))}
    accepted = [(left[i], right[js[0]]) for i, js in enumerate(matches) if len(js) == 1 and reverse[js[0]] == 1]
    left_used = {id(a) for a, _ in accepted}
    right_used = {id(b) for _, b in accepted}
    return accepted, [g for g in left if id(g) not in left_used], [g for g in right if id(g) not in right_used]


def trace(trial, values, display_window=None):
    rec = trial.condition.recording
    start, end = trial.start, trial.end
    if display_window is not None:
        left, right = display_window
        start = max(trial.condition.start, trial.onset + left)
        end = min(trial.condition.end, trial.onset + right + rec.nominal_step_ms)
    lo, hi = sample_bounds(rec, start, end)
    x = rec.time_ms[lo:hi] - trial.onset
    y = values[lo:hi]
    gaps = np.flatnonzero(rec.gap_before[lo:hi])
    return np.insert(x, gaps, np.nan), np.insert(y, gaps, np.nan)


def subtraction(reference, comparison, display_window=None):
    """Mean comparison minus mean reference on time supported by every trace."""
    traces = [trace(t, t.signal, display_window) for t in reference + comparison]
    if any(not np.isfinite(x).any() for x, _ in traces):
        return np.array([]), np.array([])
    start = max(np.nanmin(x) for x, _ in traces)
    stop = min(np.nanmax(x) for x, _ in traces)
    if stop <= start:
        return np.array([]), np.array([])
    step = max(t.condition.recording.nominal_step_ms for t in reference + comparison)
    grid = np.arange(start, stop + step * 1e-6, step)
    samples = []
    for x, y in traces:
        valid = np.flatnonzero(np.isfinite(x) & np.isfinite(y))
        segments = np.split(valid, np.flatnonzero(np.diff(valid) > 1) + 1)
        values = np.full(len(grid), np.nan)
        for part in segments:
            if not len(part):
                continue
            use = (grid >= x[part[0]] - step * 1e-6) & (grid <= x[part[-1]] + step * 1e-6)
            values[use] = np.interp(grid[use], x[part], y[part])
        samples.append(values)
    data = np.asarray(samples)
    return grid, np.mean(data[len(reference):], axis=0) - np.mean(data[:len(reference)], axis=0)

def difference_peak(time, current, start, end, sample_ms):
    """Find the signed minimum over a fully supported measurement window."""
    epsilon = sample_ms * 1e-6
    if not len(time) or time[0] > start + epsilon or time[-1] < end - sample_ms - epsilon:
        return None
    inside = np.flatnonzero((time >= start - epsilon) & (time <= end + epsilon))
    if not len(inside) or not np.isfinite(current[inside]).all():
        return None
    index = inside[np.argmin(current[inside])]
    return float(current[index]), float(time[index])
