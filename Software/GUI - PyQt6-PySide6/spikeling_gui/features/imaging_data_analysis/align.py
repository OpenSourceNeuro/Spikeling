"""Stimulus-locked loop alignment for one-pixel fluorescence acquisitions.

Optical traces are *only* resampled from actual camera frames.  Trigger and
stimulus timing comes from the higher-rate source/model samples.  This module
has no Qt dependency and never edits an acquisition or its metadata.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class AlignedImagingCycles:
    """Aligned optical repetitions, with NaN for unsupported camera bins."""
    time_ms: np.ndarray                # relative to trigger/stimulus onset
    starts_ms: np.ndarray              # accepted absolute onset times
    response: np.ndarray               # (n accepted loops, n relative bins)
    stimulus: np.ndarray               # same shape, held from model samples
    duration_ms: float
    frame_step_ms: float
    anchor_source: str
    n_candidates: int
    excluded_irregular: int
    excluded_incomplete: int
    excluded_frame_gaps: int

    @property
    def n_cycles(self) -> int:
        return len(self.starts_ms)

    @property
    def n_excluded(self) -> int:
        return self.n_candidates - self.n_cycles


def mean_sem(rows: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Column-wise mean, SD, SEM and contributing counts; never hide missing bins."""
    rows = np.asarray(rows, dtype=float)
    if rows.ndim != 2:
        raise ValueError('Expected a matrix of aligned cycles')
    counts = np.isfinite(rows).sum(axis=0)
    total = np.nansum(rows, axis=0)
    mean = np.divide(total, counts, out=np.full(rows.shape[1], np.nan), where=counts > 0)
    deviations = np.where(np.isfinite(rows), rows - mean, 0.0)
    var = np.divide((deviations * deviations).sum(axis=0), counts - 1,
                    out=np.full(rows.shape[1], np.nan), where=counts > 1)
    sd = np.sqrt(var)
    sem = np.divide(sd, np.sqrt(counts), out=np.full_like(sd, np.nan), where=counts > 1)
    return mean, sd, sem, counts


def _source_step_ms(rec) -> float:
    """Use the source acquisition cadence, not the simulator integration dt."""
    t = rec.sample_time_ms
    typical = float(np.median(np.diff(t)))
    if rec.metadata.get('source') == 'spikeling':
        expected = rec.metadata.get('board_packet_period_ms_nominal')
    else:
        expected = rec.metadata.get('sample_interval_ms_fallback')
    try:
        expected = float(expected)
    except (TypeError, ValueError):
        expected = typical
    return expected if np.isfinite(expected) and expected > 0 else typical


def _sample_gaps(rec) -> np.ndarray:
    t = rec.sample_time_ms
    dt = _source_step_ms(rec)
    gaps = np.zeros(len(t), dtype=bool)
    if len(t) > 1:
        # Some Phase-1 recordings use the model integration step even when the
        # hardware delivers a slower, regular packet stream. Do not treat every
        # regular 2-ms hardware packet as a 0.1-ms acquisition discontinuity.
        typical = float(np.median(np.diff(t)))
        gaps[1:] = np.diff(t) > max(dt, typical) * 1.5 + 1e-8
    return gaps


def find_anchors(rec, source: str = 'trigger', stimulus_threshold: float = 0.0) -> np.ndarray:
    """Return observed start times; never infer a loop by replaying Vm data."""
    if source not in ('trigger', 'stimulus'):
        raise ValueError('Select Trigger or Stimulus rising edges')
    if not np.isfinite(stimulus_threshold):
        raise ValueError('Stimulus threshold must be finite')
    values = rec.trigger if source == 'trigger' else rec.stimulus
    values = np.asarray(values, dtype=float)
    active = np.isfinite(values) & (values >= .5 if source == 'trigger'
                                    else values > stimulus_threshold)
    gaps = _sample_gaps(rec)
    indices = np.flatnonzero(active[1:] & ~active[:-1] & ~gaps[1:]) + 1
    # One-sample trigger markers at index zero are legitimate. A stimulus
    # already high at time zero may instead be a truncated pre-existing pulse.
    if source == 'trigger' and active[0] and len(active) > 1 and not active[1] and not gaps[1]:
        indices = np.r_[0, indices]
    return rec.sample_time_ms[indices]


def infer_period_ms(anchors: np.ndarray, sample_step_ms: float) -> float:
    """Find the dominant repeated interval, rejecting ambiguous protocols."""
    anchors = np.asarray(anchors, dtype=float)
    if anchors.size < 3:
        raise ValueError('At least three observed loop onsets are required to infer a period. '
                         'Alternatively enter a known period manually.')
    intervals = np.diff(anchors)
    if np.any(~np.isfinite(intervals)) or np.any(intervals <= 0):
        raise ValueError('Loop onsets must be strictly increasing')
    tolerance = max(2.0 * sample_step_ms, .06 * float(np.median(intervals)))
    counts = np.array([np.sum(np.abs(intervals - value) <= tolerance)
                       for value in intervals])
    indices = np.flatnonzero(counts == counts.max())
    # Two equally supported, well-separated periods cannot be uniquely inferred.
    if np.ptp(intervals[indices]) > tolerance:
        raise ValueError('Trigger intervals have competing cycle durations. '
                         'Enter the known cycle period manually.')
    candidate = float(np.median(intervals[indices]))
    group = intervals[np.abs(intervals - candidate) <= tolerance]
    if group.size < 2:
        raise ValueError('No repeated cycle duration was found; enter the period manually.')
    return float(np.median(group))


def _interp_camera(t: np.ndarray, signal: np.ndarray, gap: np.ndarray,
                   target: np.ndarray) -> np.ndarray:
    """Interpolate only *within* contiguous camera-frame segments."""
    result = np.full(target.shape, np.nan, dtype=float)
    if t.size == 0:
        return result
    # gap[i] means a discontinuity *before* the still-valid frame i.
    # The frame at that boundary starts a new segment; it is not discarded.
    valid = np.isfinite(signal)
    starts = np.flatnonzero(valid & (np.r_[True, gap[1:]] | np.r_[True, ~valid[:-1]]))
    for start in starts:
        stop = start + 1
        while stop < len(t) and not gap[stop] and valid[stop]:
            stop += 1
        if stop - start == 1:
            exact = np.abs(target - t[start]) <= 1e-8
            result[exact] = signal[start]
        else:
            in_segment = (target >= t[start] - 1e-9) & (target <= t[stop - 1] + 1e-9)
            result[in_segment] = np.interp(target[in_segment], t[start:stop], signal[start:stop])
    return result


def _held_stimulus(t: np.ndarray, signal: np.ndarray, gaps: np.ndarray,
                   target: np.ndarray) -> np.ndarray:
    result = np.full(target.shape, np.nan, dtype=float)
    idx = np.searchsorted(t, target, side='right') - 1
    valid = (idx >= 0) & (idx < len(t)) & (target <= t[-1])
    if valid.any():
        at = idx[valid]
        # Value at at is valid until next sample unless a timebase interruption.
        next_idx = np.minimum(at + 1, len(t) - 1)
        okay = ~(gaps[next_idx] & (target[valid] > t[at] + 1e-8))
        rows = np.flatnonzero(valid)[okay]
        result[rows] = signal[idx[rows]]
    return result


def align_imaging_cycles(rec, *, neuron: int = 0, signal: str = 'dff',
                         source: str = 'trigger', stimulus_threshold: float = 0.0,
                         pre_ms: float = 0.0, period_ms: float | None = None,
                         frame_values: np.ndarray | None = None) -> AlignedImagingCycles:
    """Align repeated stimulus cycles without treating model samples as camera frames.

    An irregular next anchor excludes that repetition. A final cycle without
    a known next anchor is accepted only if its full extent is recorded.
    Camera gaps remain NaNs; cycles with >20% unsupported fluorescence bins
    are excluded. The average uses each bin's actual contributing count.
    """
    if neuron not in (0, 1, 2):
        raise ValueError('Neuron index must be 0, 1, or 2')
    if signal not in ('fluorescence', 'dff'):
        raise ValueError('Choose fluorescence or recorded ΔF/F₀')
    if not np.isfinite(pre_ms) or pre_ms < 0:
        raise ValueError('Pre-trigger window must be a non-negative number of milliseconds')
    frame_step = 1000.0 / rec.nominal_frame_rate_hz
    if not np.isfinite(frame_step) or frame_step <= 0:
        raise ValueError('Frame rate must be finite and positive')
    if rec.n_frames < 2:
        raise ValueError('At least two camera frames are required for alignment')
    anchors = find_anchors(rec, source, stimulus_threshold)
    if anchors.size < 2:
        raise ValueError('At least two observed loop onsets are required. '
                         'Check the trigger source or choose stimulus rising edges.')
    sample_step = _source_step_ms(rec)
    if period_ms is None:
        duration = infer_period_ms(anchors, sample_step)
    else:
        duration = float(period_ms)
        if not np.isfinite(duration) or duration <= 0:
            raise ValueError('Cycle period must be finite and positive')
    if duration < 3 * frame_step:
        raise ValueError(f'Cycle duration ({duration:g} ms) is too short at '
                         f'{rec.nominal_frame_rate_hz:g} Hz. At least three camera bins are required.')
    if pre_ms > duration * 3:
        raise ValueError('Pre-trigger window is too long relative to the cycle')
    relative = np.arange(-pre_ms, duration - 1e-9, frame_step, dtype=float)
    if relative.size > 20000:
        raise ValueError('Too many alignment bins: reduce the period or increase frame rate')
    if relative.size < 3:
        raise ValueError('Not enough camera bins in the chosen alignment window')
    if frame_values is None:
        frame_signal = (rec.frame_fluorescence_au if signal == 'fluorescence'
                        else rec.recorded_dff_percent)[:, neuron]
    else:
        values = np.asarray(frame_values, dtype=float)
        if values.shape != (rec.n_frames, 3) or np.isinf(values).any():
            raise ValueError('Processed signal must contain three camera-frame channels without infinity')
        frame_signal = values[:, neuron]
    t_frame = rec.frame_time_ms
    t_sample = rec.sample_time_ms
    sample_gaps = _sample_gaps(rec)
    kept_starts, response_rows, stimulus_rows = [], [], []
    excluded_irregular = excluded_incomplete = excluded_frame_gaps = 0
    # Allow one optical frame of edge support, but never extrapolate; the
    # per-bin sample count exposes under-supported boundaries to the student.
    minimum_supported = max(3, int(np.ceil(.8 * len(relative))))
    for i, anchor in enumerate(anchors):
        if i + 1 < len(anchors):
            interval = anchors[i + 1] - anchor
            tol = max(2 * sample_step, .06 * duration)
            if abs(interval - duration) > tol:
                excluded_irregular += 1
                continue
        absolute = anchor + relative
        # Complete model-time acquisition extent is required. Missing optical
        # bins near the edges are retained as NaNs, not fabricated.
        if absolute[0] < t_sample[0] - 1e-8 or anchor + duration > t_sample[-1] + sample_step:
            excluded_incomplete += 1
            continue
        # A source interruption inside a repetition makes the stimulus and
        # anchor chronology unverifiable, so drop the entire repetition.
        lo = int(np.searchsorted(t_sample, absolute[0], side='left'))
        hi = int(np.searchsorted(t_sample, anchor + duration, side='left'))
        if np.any(sample_gaps[lo:min(len(t_sample), hi + 1)]):
            excluded_incomplete += 1
            continue
        response = _interp_camera(t_frame, frame_signal, rec.frame_gap_before, absolute)
        if np.isfinite(response).sum() < minimum_supported:
            excluded_frame_gaps += 1
            continue
        stimulus = _held_stimulus(t_sample, rec.stimulus, sample_gaps, absolute)
        kept_starts.append(float(anchor))
        response_rows.append(response)
        stimulus_rows.append(stimulus)
    if not kept_starts:
        raise ValueError(
            f'No usable complete cycles. Observed {len(anchors)} onsets; '
            f'{excluded_irregular} irregular, {excluded_incomplete} incomplete/timebase interruptions, '
            f'{excluded_frame_gaps} insufficient optical-frame coverage. '
            'Try shorter pre-trigger time or check acquisition gaps.'
        )
    return AlignedImagingCycles(
        relative, np.asarray(kept_starts), np.asarray(response_rows), np.asarray(stimulus_rows),
        duration, frame_step, source, len(anchors), excluded_irregular,
        excluded_incomplete, excluded_frame_gaps,
    )
