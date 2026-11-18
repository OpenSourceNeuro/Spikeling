"""Group step measurements by protocol and input level."""

from dataclasses import dataclass

import numpy as np

from .sweep_analysis import Sweep, command_windows, sample_bounds, window_available


@dataclass
class SummaryPoint:
    row: int
    sweep: Sweep
    input_level: float
    holding: float | None
    duration_ms: float
    metrics: dict


def points_for_sweeps(recording, sweeps, measurements, include, command=None, tolerance=.05, *, measure_stimulus_change=False, settled_command=False):
    points, skipped = [], 0
    for row, (sweep, metrics) in enumerate(zip(sweeps, measurements)):
        if not include(sweep):
            continue
        step = sweep.step
        level = step.amplitude
        holding = None
        if measure_stimulus_change:
            left, on = sample_bounds(recording, sweep.baseline_start_ms, step.onset_ms)
            _, stop = sample_bounds(recording, step.onset_ms, step.offset_ms)
            signal = recording.stimulus
            if not (window_available(recording, left, on, signal)
                    and window_available(recording, on, stop, signal)):
                skipped += 1
                continue
            level = float(np.median(signal[on:stop]) - np.median(signal[left:on]))
        if command is not None:
            samples = command_windows(recording, sweep, command, settled=settled_command)
            if samples is None:
                skipped += 1
                continue
            before, active = samples
            if np.ptp(before) > tolerance or np.ptp(active) > tolerance:
                skipped += 1
                continue
            holding = float(np.median(before))
            level = float(np.median(active))
        if level is None:
            skipped += 1
            continue
        data = dict(metrics)
        if "count" in data:
            data["probability"] = 100.0 if data["count"] else 0.0
        if "late" in data and "baseline" in data:
            data["late_change"] = data["late"] - data["baseline"]
        points.append(SummaryPoint(row, sweep, level, holding, step.grouping_duration_ms, data))
    return points, skipped


def protocol_groups(points, time_tolerance, level_tolerance):
    """Separate pulse durations and, for measured commands, holding levels."""
    groups, holding_bounds = [], []
    for point in sorted(points, key=lambda p: (p.duration_ms, p.holding or 0)):
        hold = point.holding or 0
        for group, bounds in zip(groups, holding_bounds):
            lo, hi = min(bounds[0], hold), max(bounds[1], hold)
            if (point.duration_ms - group[0].duration_ms <= time_tolerance + 1e-9
                    and hi - lo <= level_tolerance + 1e-9):
                group.append(point)
                bounds[:] = [lo, hi]
                break
        else:
            groups.append([point])
            holding_bounds.append([hold, hold])
    return groups


def level_groups(points, tolerance):
    groups = []
    for point in sorted(points, key=lambda p: p.input_level):
        if groups and point.input_level - groups[-1][0].input_level <= tolerance + 1e-9:
            groups[-1].append(point)
        else:
            groups.append([point])
    return groups


def statistics(points, metric):
    values = [point.metrics[metric] for point in points if metric in point.metrics]
    return {
        "level": float(np.mean([p.input_level for p in points])),
        "n": len(points), "defined": len(values),
        "mean": float(np.mean(values)) if values else None,
        "sd": float(np.std(values, ddof=1)) if len(values) > 1 else None,
    }


def average_step_traces(recording, points, time_ms, signals):
    """Average aligned samples without interpolating across gaps or step edges."""
    totals = np.zeros((len(signals), len(time_ms)))
    counts = np.zeros(totals.shape, dtype=int)
    time = recording.time_ms
    epsilon = recording.nominal_step_ms * 1e-6
    for point in points:
        sweep = point.sweep
        onset = sweep.step.onset_ms
        for start, end in ((sweep.baseline_start_ms, onset),
                           (onset, sweep.step.offset_ms),
                           (sweep.step.offset_ms, sweep.recovery_end_ms)):
            left, right = sample_bounds(recording, start, end)
            relative = time[left:right] - onset
            if not relative.size:
                continue
            for index, signal in enumerate(signals):
                values = signal[left:right]
                valid = np.isfinite(values)
                breaks = np.flatnonzero(recording.gap_before[left+1:right]
                                        | ~valid[:-1] | ~valid[1:]) + 1
                for segment in np.split(np.arange(len(relative)), breaks):
                    if not valid[segment[0]]:
                        continue
                    lo = np.searchsorted(time_ms, relative[segment[0]] - epsilon)
                    hi = np.searchsorted(time_ms, relative[segment[-1]] + epsilon, side="right")
                    totals[index, lo:hi] += np.interp(time_ms[lo:hi], relative[segment], values[segment])
                    counts[index, lo:hi] += 1
    means = np.divide(totals, counts, out=np.full(totals.shape, np.nan), where=counts > 0)
    return means, counts
