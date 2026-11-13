"""Exposure-normalised spike timing for a group of aligned trials."""

from dataclasses import dataclass

import numpy as np

from .sweep_analysis import sample_bounds


@dataclass
class SpikeRow:
    label: str
    recording_id: str
    onset_ms: float
    active_ms: float
    events: np.ndarray
    support: np.ndarray
    intervals: np.ndarray


def spike_row(recording, indices, neuron, label, start, onset, offset, end):
    """Preserve observed support and omit intervals that cross a missing segment."""
    time = recording.time_ms
    left, right = sample_bounds(recording, start, end)
    observed = np.flatnonzero(np.isfinite(recording.voltage[neuron][left:right])) + left
    breaks = (np.diff(observed) > 1) | recording.gap_before[observed[1:]]
    segments = np.split(observed, np.flatnonzero(breaks) + 1)
    support, events, isi = [], [], []
    for segment in segments:
        if not len(segment):
            continue
        first, last = segment[0], segment[-1]
        # The final finite sample contributes at most one nominal sample interval.
        upper = time[last] + recording.nominal_step_ms
        if last + 1 < len(time):
            upper = min(upper, time[last + 1])
        low, high = max(start, time[first]), min(end, upper)
        if high <= low:
            continue
        support.append((low - onset, high - onset))
        a, b = np.searchsorted(indices, [first, last + 1])
        detected = time[indices[a:b]]
        eps = recording.nominal_step_ms * 1e-6
        detected = detected[(detected >= low - eps) & (detected < high - eps)]
        relative = detected - onset
        relative[np.abs(relative) < eps] = 0
        events.extend(relative)
        active = detected[(detected >= onset - eps) & (detected < offset - eps)]
        isi.extend((number, duration) for number, duration in enumerate(np.diff(active), 1))
    return SpikeRow(label, recording.recording_id, onset, offset - onset, np.asarray(events),
                    np.asarray(support).reshape(-1, 2), np.asarray(isi).reshape(-1, 2))


def psth(rows, edges):
    """Return counts, observed milliseconds, and number of contributing trials."""
    count = np.zeros(len(edges) - 1, dtype=int)
    exposure = np.zeros(len(edges) - 1)
    contributors = np.zeros(len(edges) - 1, dtype=int)
    for row in rows:
        bins = np.searchsorted(edges, row.events, side="right") - 1
        valid = (bins >= 0) & (bins < len(count))
        np.add.at(count, bins[valid], 1)
        observed = np.zeros_like(exposure)
        for start, end in row.support:
            first = max(0, np.searchsorted(edges, start, side="right") - 1)
            last = min(len(observed), np.searchsorted(edges, end, side="left"))
            observed[first:last] += np.maximum(
                0, np.minimum(end, edges[first + 1:last + 1]) - np.maximum(start, edges[first:last]),
            )
        exposure += observed
        contributors += observed > 1e-9
    rate = np.divide(count * 1000, exposure, out=np.full_like(exposure, np.nan), where=exposure > 1e-9)
    return count, exposure, contributors, rate


def timing_edges(groups, width):
    support = [pair for _, rows in groups for row in rows for pair in row.support]
    if not support:
        raise ValueError("The selected sweeps have no observed voltage samples.")
    start = min(0, min(pair[0] for pair in support))
    end = max(pair[1] for pair in support)
    before, after = int(np.ceil(-start / width)), int(np.ceil(end / width))
    if before + after > 10000:
        raise ValueError("Increase the bin width to display at most 10,000 bins.")
    return np.arange(-before, max(1, after) + 1) * width


def isi_edges(groups, width):
    end = max((duration for _, rows in groups for row in rows for _, duration in row.intervals), default=0)
    bins = max(1, int(np.ceil(end / width)))
    if bins > 10000:
        raise ValueError("Increase the ISI bin width to display at most 10,000 bins.")
    return np.arange(bins + 1) * width
