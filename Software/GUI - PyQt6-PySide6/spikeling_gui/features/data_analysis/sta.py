"""Spike-triggered stimulus averages with within-segment circular controls."""

from dataclasses import dataclass

import numpy as np


@dataclass
class TriggeredAverage:
    lags_ms: np.ndarray
    average: np.ndarray
    event_count: int
    used_count: int
    control_mean: np.ndarray | None
    control_low: np.ndarray | None
    control_high: np.ndarray | None
    shuffled_spikes: int
    shuffle_count: int


def spike_triggered_average(recording, stimulus, events, lookback_ms, shuffles=20, seed=0):
    """Average complete sample-aligned histories, including the spike sample."""
    step = recording.nominal_step_ms
    if not np.isfinite(lookback_ms) or lookback_ms < step:
        raise ValueError(f"Look-back must be at least one sample ({step:g} ms).")
    if lookback_ms >= len(stimulus) * step:
        raise ValueError("The look-back window is longer than the recording.")
    history = int(round(lookback_ms / step))
    width = history + 1
    if width > len(stimulus):
        raise ValueError("The look-back window is longer than the recording.")
    if not 0 <= shuffles <= 200:
        raise ValueError("Use 0 to disable the control or up to 200 shuffles.")

    # Every eligible history must have finite stimulus samples and a continuous,
    # near-regular time axis. Discrete stimulus values are never interpolated.
    missing = np.r_[0, np.cumsum(~np.isfinite(stimulus))]
    intervals = np.diff(recording.time_ms)
    irregular = recording.gap_before[1:] | ~np.isclose(intervals, step, rtol=.01, atol=1e-9)
    edge_breaks = np.r_[0, np.cumsum(irregular)]
    end = np.arange(history, len(stimulus))
    start = end - history
    eligible = np.zeros(len(stimulus), dtype=bool)
    eligible[end] = (missing[end + 1] == missing[start]) & (edge_breaks[end] == edge_breaks[start])
    events = np.asarray(events, dtype=int)
    kept = events[eligible[events]]
    if not len(kept):
        raise ValueError("No spikes have a complete stimulus history. Try a shorter look-back or review spike detection.")
    if width * len(kept) * (1 + shuffles) > 200_000_000:
        raise ValueError("This calculation is large. Shorten the look-back or reduce the number of shuffles.")

    windows = np.lib.stride_tricks.sliding_window_view(stimulus, width)
    batch = max(1, 1_000_000 // width)

    def mean_at(indices):
        total = np.zeros(width)
        for i in range(0, len(indices), batch):
            total += np.sum(windows[indices[i:i + batch] - history], axis=0)
        return total / len(indices)

    average = mean_at(kept)
    control_mean = control_low = control_high = None
    shuffled_spikes = 0
    shuffle_count = 0
    if shuffles:
        # Rotate spikes within each continuous span of eligible positions, so
        # every control uses the same number of windows from each span.
        changes = np.diff(np.r_[False, eligible, False].astype(np.int8))
        starts = np.flatnonzero(changes == 1)
        stops = np.flatnonzero(changes == -1)
        span = np.searchsorted(starts, kept, side="right") - 1
        lower = starts[span]
        lengths = stops[span] - lower
        can_shift = lengths > 1
        shuffled_spikes = int(can_shift.sum())
        if shuffled_spikes:
            rng = np.random.default_rng(seed)
            controls = np.empty((shuffles, width))
            lengths_per_span = stops - starts
            occupied = np.unique(span[can_shift])
            for i in range(shuffles):
                shifts = np.zeros(len(starts), dtype=int)
                shifts[occupied] = rng.integers(1, lengths_per_span[occupied])
                shifted = lower + (kept - lower + shifts[span]) % lengths
                controls[i] = mean_at(shifted)
            control_mean = np.mean(controls, axis=0)
            control_low, control_high = np.quantile(controls, [.025, .975], axis=0)
            shuffle_count = shuffles

    return TriggeredAverage(
        np.arange(-history, 1) * step, average, len(events), len(kept),
        control_mean, control_low, control_high, shuffled_spikes, shuffle_count,
    )
