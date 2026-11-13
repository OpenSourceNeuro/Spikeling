"""Detection, review and measurement of individual stimulus steps."""

from dataclasses import dataclass, replace

import numpy as np

from .recording import trigger_onsets


@dataclass(frozen=True)
class Step:
    number: int
    onset_ms: float
    offset_ms: float
    amplitude: float | None
    series: int | None
    position: int | None
    preceding_off_ms: float | None = None
    issue: str = ""


@dataclass(frozen=True)
class Sweep:
    step: Step
    baseline_start_ms: float
    recovery_end_ms: float
    baseline_clipped: bool
    recovery_clipped: bool


def detect_steps(recording, baseline, tolerance, minimum_ms, expected_ms=None):
    """Detect plateaux departing from the stated baseline in either direction."""
    signal = recording.stimulus
    time = recording.time_ms
    interval = recording.nominal_step_ms
    delta = signal - baseline
    state = np.where(delta > tolerance, 1, np.where(delta < -tolerance, -1, 0))
    state[~np.isfinite(signal)] = 2
    onsets = trigger_onsets(recording)
    changes = np.flatnonzero((state[1:] != state[:-1]) | recording.gap_before[1:]) + 1
    boundaries = np.unique(np.r_[0, changes, onsets, len(time)])
    starts = set(onsets)
    candidates = []
    positions = {}
    for start, stop in zip(boundaries[:-1], boundaries[1:]):
        if state[start] not in (-1, 1):
            continue
        start_known = start in starts or (
            start > 0 and state[start - 1] == 0 and not recording.gap_before[start]
        )
        stop_known = stop < len(time) and state[stop] == 0 and not recording.gap_before[stop]
        onset = float(time[start])
        offset = float(time[stop] if stop_known else time[stop - 1] + interval)
        duration = offset - onset
        epsilon = interval * 1e-6
        if duration + epsilon < minimum_ms and start_known and stop_known:
            continue
        amplitude = float(np.median(delta[start:stop]))
        series_index = int(np.searchsorted(onsets, start, side="right"))
        positions[series_index] = positions.get(series_index, 0) + 1
        issue = ""
        if not start_known or not stop_known:
            issue = "Incomplete or unobserved edge"
        elif np.ptp(delta[start:stop]) > 2 * tolerance:
            issue = "Stimulus is not a stable plateau"
        elif expected_ms is not None and abs(duration - expected_ms) > interval + epsilon:
            issue = "Duration differs from expected"
        candidates.append(Step(
            len(candidates) + 1, onset, offset, amplitude, series_index or None,
            positions[series_index] if series_index else None, issue=issue,
        ))
    return with_preceding_intervals(candidates)


def manual_steps(recording, baseline, first_offset, on_ms, off_ms, count, anchor, pause):
    """Repeat the entered schedule at cycle markers or an explicit first anchor."""
    time = recording.time_ms
    interval = recording.nominal_step_ms
    tolerance = interval * 1e-6
    recording_end = time[-1] + interval
    onsets = trigger_onsets(recording)
    if onsets.size:
        anchors = time[onsets]
    else:
        if not time[0] <= anchor < recording_end:
            raise ValueError("First series anchor must lie within the recording.")
        period = first_offset + (on_ms + off_ms) * count + pause
        series_count = int(np.ceil((recording_end - anchor) / period))
        if series_count * count > len(time) * 2:
            raise ValueError("The entered schedule is shorter than the sampling interval.")
        anchors = anchor + np.arange(series_count) * period
    if on_ms < interval - tolerance:
        raise ValueError("Step on-time must cover at least one sample.")
    candidates = []
    for series, base in enumerate(anchors, 1):
        next_anchor = anchors[series] if series < len(anchors) else recording_end
        for position in range(1, count + 1):
            onset = float(base + first_offset + (position - 1) * (on_ms + off_ms))
            if onset >= next_anchor - tolerance:
                break
            offset = onset + on_ms
            left, right = sample_bounds(recording, onset, offset)
            samples = recording.stimulus[left:right]
            complete = offset <= next_anchor + tolerance and onset >= time[0] - tolerance
            issue = ""
            if not complete or not window_available(recording, left, right, recording.stimulus):
                issue = "Incomplete step or missing data"
            amplitude = float(np.median(samples) - baseline) if samples.size and np.isfinite(samples).all() else None
            candidates.append(Step(
                len(candidates) + 1, onset, offset, amplitude, series, position, issue=issue,
            ))
    return with_preceding_intervals(candidates)


def with_preceding_intervals(steps):
    result = []
    previous = None
    for step in steps:
        interval = None
        if previous is not None and not previous.issue:
            interval = max(0.0, step.onset_ms - previous.offset_ms)
        result.append(replace(step, preceding_off_ms=interval))
        previous = step
    return result


def review_windows(recording, steps, pre_ms, post_ms):
    time = recording.time_ms
    end = time[-1] + recording.nominal_step_ms
    epsilon = recording.nominal_step_ms * 1e-6
    sweeps = []
    for index, step in enumerate(steps):
        earlier = steps[index - 1].offset_ms if index else time[0]
        later = steps[index + 1].onset_ms if index + 1 < len(steps) else end
        desired_start = step.onset_ms - pre_ms
        desired_end = step.offset_ms + post_ms
        start = min(step.onset_ms, max(time[0], earlier, desired_start))
        stop = max(step.offset_ms, min(end, later, desired_end))
        sweeps.append(Sweep(
            step, start, stop, start > desired_start + epsilon, stop < desired_end - epsilon,
        ))
    return sweeps


def sample_bounds(recording, start, end):
    # A tiny tolerance keeps boundaries stable when manual timing is added to
    # decimal CSV timestamps. Active windows include onset and exclude offset.
    eps = recording.nominal_step_ms * 1e-6
    return tuple(np.searchsorted(recording.time_ms, [start - eps, end - eps]))


def window_available(recording, left, right, signal):
    return (
        right > left and np.isfinite(signal[left:right]).all()
        and not recording.gap_before[left:right].any()
        and (right == len(signal) or not recording.gap_before[right])
    )


def measure_sweep(recording, sweep, neuron, signal, spikes, late_ms):
    step = sweep.step
    lo, hi = sample_bounds(recording, step.onset_ms, step.offset_ms)
    baseline_lo, _ = sample_bounds(recording, sweep.baseline_start_ms, step.onset_ms)
    late_start = max(step.onset_ms, step.offset_ms - late_ms)
    late_lo, _ = sample_bounds(recording, late_start, step.offset_ms)
    metrics = {}
    if step.issue:
        return metrics
    if window_available(recording, baseline_lo, lo, signal):
        metrics["baseline"] = float(np.mean(signal[baseline_lo:lo]))
    if window_available(recording, lo, hi, signal):
        active = signal[lo:hi]
        if "baseline" in metrics:
            changes = active - metrics["baseline"]
            metrics["peak"] = float(changes[np.argmax(np.abs(changes))])
            metrics["peak_inward"] = float(np.min(changes))
            metrics["peak_outward"] = float(np.max(changes))
        if window_available(recording, late_lo, hi, signal):
            metrics["late"] = float(np.mean(signal[late_lo:hi]))
    if spikes is not None and window_available(recording, lo, hi, recording.voltage[neuron]):
        events = spikes.indices[neuron]
        first, last = np.searchsorted(events, [lo, hi])
        count = int(last - first)
        metrics["count"] = count
        metrics["rate"] = count * 1000 / (step.offset_ms - step.onset_ms)
        if count:
            metrics["latency"] = max(0.0, float(recording.time_ms[events[first]] - step.onset_ms))
    return metrics


def matching_sweeps(sweeps, selected, amplitude_tolerance, time_tolerance):
    """Return the selected condition's amplitude and duration group."""
    step = selected.step
    return [
        candidate for candidate in sweeps
        if step.amplitude is not None and candidate.step.amplitude is not None
        and abs(candidate.step.amplitude - step.amplitude) <= amplitude_tolerance
        and abs(
            (candidate.step.offset_ms - candidate.step.onset_ms)
            - (step.offset_ms - step.onset_ms)
        ) <= time_tolerance
    ]
