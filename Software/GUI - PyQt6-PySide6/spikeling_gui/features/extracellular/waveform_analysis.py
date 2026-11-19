"""Extract event-centred multichannel snippets without padding invalid rows."""
from dataclasses import dataclass
from math import floor, isfinite

import numpy as np

from .acquisition import CONTACTS
from .offline_processing import MAX_ANALYSIS_ROWS


@dataclass(frozen=True)
class WaveformSettings:
    pre_ms: float = 1.0
    post_ms: float = 2.0
    max_snippets: int = 16
    first_group: int = 1
    group_count: int | None = None

    def window(self, rate):
        if not all(isfinite(value) and 0 <= value <= MAX_ANALYSIS_ROWS * (1000.0 / rate) for value in (self.pre_ms, self.post_ms)):
            raise ValueError("Waveform windows must be finite and non-negative.")
        before, after = (floor(value * rate / 1000 + 0.5) for value in (self.pre_ms, self.post_ms))
        if before + after < 1 or before + after + 1 > MAX_ANALYSIS_ROWS:
            raise ValueError("Choose a waveform window of at least two samples of at most 40,000 samples.")
        if not isinstance(self.max_snippets, int) or not 0 <= self.max_snippets <= 64:
            raise ValueError("Show between 0 and 64 individual waveforms.")
        if self.first_group < 1 or (self.group_count is not None and self.group_count < 1):
            raise ValueError("Waveform groups use positive indices and counts.")
        return before, after


@dataclass(frozen=True)
class Waveforms:
    times_ms: np.ndarray
    mean_uV: np.ndarray | None
    snippets: tuple[np.ndarray, ...]
    event_ids: tuple[str, ...]
    displayed_ids: tuple[str, ...]
    excluded: tuple[tuple[str, str], ...]
    selected_count: int


def extract_waveforms(runs, groups, settings, rate, cancel=None):
    """Average all valid selected groups and retain a bounded display subset."""
    before, after = settings.window(rate)
    times = np.arange(-before, after + 1) * (1000.0 / rate)
    total = np.zeros((len(times), len(CONTACTS)))
    begin = settings.first_group - 1
    end = None if settings.group_count is None else begin + settings.group_count
    selected = groups[begin:end]
    by_run = {(run.segment, run.epoch): run for run in runs}
    valid, excluded = [], []
    for group in selected:
        if cancel is not None and cancel.is_set():
            return None
        run = by_run[group.key]
        row = group.sample - run.first
        start, stop = row - before, row + after + 1
        if start < 0 or stop > len(run.time_ms):
            excluded.append((group.id, "interval_segment_or_epoch_boundary"))
        elif start < run.warmup:
            excluded.append((group.id, "filter_warmup"))
        else:
            total += run.values_uV[start:stop]
            valid.append((group.id, run.values_uV[start:stop]))
    count = min(settings.max_snippets, len(valid))
    display = np.linspace(0, len(valid) - 1, count, dtype=int)
    return Waveforms(times, total / len(valid) if valid else None,
                     tuple(valid[i][1] for i in display), tuple(event[0] for event in valid),
                     tuple(valid[i][0] for i in display), tuple(excluded), len(selected))
