"""Independent-acquisition comparison for three one-pixel calcium-imaging channels.

Only recorded optical frames are compared. Model Vm, calcium and neural event
reference columns are intentionally never read by this module.

The two recordings have independent camera clocks. We either express each
recording relative to its own start, anchor to its first observed stimulus,
or average complete stimulus cycles *within* each recording before comparing
means. Interpolation for an optional difference curve never bridges a camera
acquisition gap or missing fluorescence frame.
"""
from __future__ import annotations

from dataclasses import dataclass, fields
from pathlib import Path

import numpy as np

from .align import (_interp_camera, _sample_gaps, align_imaging_cycles,
                    find_anchors, mean_sem)
from .processing import ProcessingSettings, process_imaging_recording


SOURCES = ('recorded', 'empirical', 'processed', 'raw')
MODES = ('cycles', 'elapsed', 'first_anchor')


@dataclass(frozen=True)
class ComparisonSettings:
    source: str = 'recorded'
    mode: str = 'cycles'
    anchor_source: str = 'trigger'
    stimulus_threshold: float = 0.0
    pre_ms: float = 0.0
    period_ms: float | None = None
    baseline_percentile: float = 20.0
    difference_direction: str = 'reference_minus_comparison'

    def as_dict(self):
        return {field.name: getattr(self, field.name) for field in fields(self)}


@dataclass(frozen=True)
class ConditionResult:
    label: str
    recording: object
    x_ms: np.ndarray                         # optical camera times / averaged cycle bins
    y: np.ndarray                            # (n time bins, 3) optical response
    gap_before: np.ndarray                   # acquisition discontinuities / NaN bins
    sem: np.ndarray                          # SEM for cycle means only; else all NaN
    counts: np.ndarray                       # per-bin contributing cycles, or 0/1 for raw
    stimulus_x_ms: np.ndarray
    stimulus: np.ndarray                     # one per neuron, (n stimulus bins, 3)
    stimulus_gap_before: np.ndarray
    cycles: tuple[int, int, int]
    exclusions: tuple[int, int, int]
    metrics: tuple[dict, dict, dict]
    processing: dict | None = None


@dataclass(frozen=True)
class ComparisonResult:
    settings: ComparisonSettings
    reference: ConditionResult
    comparison: ConditionResult
    difference_x_ms: np.ndarray
    difference: np.ndarray                   # (n common bins, 3), signed per declared direction
    units: str
    warnings: tuple[str, ...]

    def metrics_rows(self, neuron: int) -> tuple[tuple[str, object, object], ...]:
        a, b = self.reference.metrics[neuron], self.comparison.metrics[neuron]
        rows = (
            ('Baseline', a['baseline'], b['baseline']),
            ('Peak above baseline', a['peak_delta'], b['peak_delta']),
            ('Peak time from anchor (ms)' if self.settings.mode != 'elapsed' else 'Peak time from start (ms)',
             a['peak_time_ms'], b['peak_time_ms']),
            ('Positive AUC (unit·ms)', a['auc_positive'], b['auc_positive']),
            ('Mean signal', a['mean'], b['mean']),
            ('Valid response bins', a['valid_bins'], b['valid_bins']),
            ('Accepted cycles', self.reference.cycles[neuron], self.comparison.cycles[neuron]),
            ('Excluded cycles', self.reference.exclusions[neuron], self.comparison.exclusions[neuron]),
            ('Nominal camera rate (Hz)', self.reference.recording.nominal_frame_rate_hz,
             self.comparison.recording.nominal_frame_rate_hz),
        )
        return rows


def _verify_settings(s: ComparisonSettings):
    if s.source not in SOURCES:
        raise ValueError('Unknown optical comparison signal')
    if s.mode not in MODES:
        raise ValueError('Unknown alignment mode')
    if s.difference_direction not in ('reference_minus_comparison', 'comparison_minus_reference'):
        raise ValueError('Select a valid difference direction')
    if s.anchor_source not in ('trigger', 'stimulus'):
        raise ValueError('Choose trigger or stimulus rise as anchor')
    values = (s.stimulus_threshold, s.pre_ms, s.baseline_percentile)
    if not all(np.isfinite(x) for x in values):
        raise ValueError('Comparison settings must be finite')
    if not 0 <= s.baseline_percentile <= 100:
        raise ValueError('Baseline percentile must be 0–100')
    if s.pre_ms < 0:
        raise ValueError('Pre-onset window cannot be negative')
    if s.period_ms is not None and not (np.isfinite(s.period_ms) and s.period_ms > 0):
        raise ValueError('Manual cycle period must be finite and positive')


def _empirical_dff(rec, percentile: float) -> np.ndarray:
    """Per-channel, per-contiguous-segment empirical F0; no hidden offset."""
    raw = np.asarray(rec.frame_fluorescence_au, dtype=float)
    gaps = np.asarray(rec.frame_gap_before, dtype=bool)
    out = np.full_like(raw, np.nan)
    for neuron in range(3):
        valid = np.flatnonzero(np.isfinite(raw[:, neuron]))
        if not valid.size:
            raise ValueError(f'Neuron {neuron + 1}: no valid optical frames')
        splits = np.flatnonzero((np.diff(valid) != 1) | gaps[valid[1:]]) + 1
        for seg in np.split(valid, splits):
            f0 = float(np.percentile(raw[seg, neuron], percentile))
            if f0 <= 1e-10:
                raise ValueError(f'Neuron {neuron + 1}: empirical F0 is not positive')
            out[seg, neuron] = 100.0 * (raw[seg, neuron] - f0) / f0
    return out


def _optical_data(rec, s: ComparisonSettings, processing_settings: ProcessingSettings | None):
    if s.source == 'recorded':
        return np.asarray(rec.recorded_dff_percent, dtype=float), None
    if s.source == 'raw':
        return np.asarray(rec.frame_fluorescence_au, dtype=float), None
    if s.source == 'empirical':
        return _empirical_dff(rec, s.baseline_percentile), {
            'method': 'percentile per uninterrupted camera segment',
            'percentile': s.baseline_percentile, 'background_correction': 'none',
        }
    if processing_settings is None:
        raise ValueError('Select processing parameters before comparing processed signals')
    processed = process_imaging_recording(rec, processing_settings)
    return np.asarray(processed.dff_percent, dtype=float), {
        'method': 'same phase-3 processing recipe applied independently to both records',
        'parameters': processed.parameters(), 'warnings': list(processed.warnings),
    }


def _metrics(x: np.ndarray, y: np.ndarray, gaps: np.ndarray,
             baseline_percentile: float, mode: str):
    good = np.isfinite(y) & np.isfinite(x)
    if not good.any():
        return {'baseline': None, 'peak_delta': None, 'peak_time_ms': None,
                'auc_positive': None, 'mean': None, 'valid_bins': 0}
    baseline_samples = y[good & (x < 0)]
    if mode != 'elapsed' and baseline_samples.size >= 3:
        baseline = float(np.median(baseline_samples))
    else:
        baseline = float(np.percentile(y[good], baseline_percentile))
    response_mask = good & ((x >= 0) if mode != 'elapsed' else np.ones(x.shape, dtype=bool))
    if not response_mask.any():
        response_mask = good
    response_idx = np.flatnonzero(response_mask)
    peak = int(response_idx[np.argmax(y[response_idx])])
    shifted = y - baseline
    # Never calculate an area across a camera gap, a NaN or the time before an anchor.
    valid_pairs = (response_mask[1:] & response_mask[:-1] & ~gaps[1:]
                   & (np.diff(x) > 0))
    dt = np.diff(x)
    area = float(np.sum(.5 * (np.maximum(0, shifted[1:])
                                + np.maximum(0, shifted[:-1]))[valid_pairs] * dt[valid_pairs]))
    return {'baseline': baseline, 'peak_delta': float(shifted[peak]),
            'peak_time_ms': float(x[peak]), 'auc_positive': area,
            'mean': float(np.mean(y[response_idx])), 'valid_bins': int(response_mask.sum())}


def _condition(rec, label: str, settings: ComparisonSettings,
               processing_settings: ProcessingSettings | None) -> ConditionResult:
    if rec.n_frames < 3:
        raise ValueError(f'{label}: at least three acquired optical frames are needed')
    signals, processing = _optical_data(rec, settings, processing_settings)
    if signals.shape != (rec.n_frames, 3):
        raise ValueError(f'{label}: expected three optical channels')
    if settings.mode == 'cycles':
        aligned = []
        for neuron in range(3):
            try:
                cycle = align_imaging_cycles(
                    rec, neuron=neuron,
                    signal='fluorescence' if settings.source == 'raw' else 'dff',
                    source=settings.anchor_source,
                    stimulus_threshold=settings.stimulus_threshold,
                    pre_ms=settings.pre_ms, period_ms=settings.period_ms,
                    frame_values=signals,
                )
            except ValueError as exc:
                raise ValueError(f'{label}, neuron {neuron + 1}: {exc}') from exc
            aligned.append(cycle)
        # All channels have a common frame clock and settings. Their accepted
        # repetitions can differ when a channel has nonfinite samples.
        grid = aligned[0].time_ms
        if any(not np.array_equal(row.time_ms, grid) for row in aligned[1:]):
            raise ValueError(f'{label}: channel alignment grids disagree')
        means, sems, counts, stimuli = [], [], [], []
        for cycle in aligned:
            mean, _, sem, count = mean_sem(cycle.response)
            stim, _, _, _ = mean_sem(cycle.stimulus)
            means.append(mean)
            sems.append(sem)
            counts.append(count)
            stimuli.append(stim)
        y = np.column_stack(means)
        sem = np.column_stack(sems)
        n = np.column_stack(counts)
        stim = np.column_stack(stimuli)
        gaps = np.zeros(len(grid), dtype=bool)
        # Interior missing bins break plotted lines and any comparison interpolation.
        gap_stim = np.zeros(len(grid), dtype=bool)
        cycles = tuple(c.n_cycles for c in aligned)
        excluded = tuple(c.n_excluded for c in aligned)
        time = grid
        stim_time = grid
    else:
        time = np.asarray(rec.frame_time_ms, dtype=float).copy()
        stim_time = np.asarray(rec.sample_time_ms, dtype=float).copy()
        if settings.mode == 'elapsed':
            anchor = time[0]
        else:
            anchors = find_anchors(rec, settings.anchor_source, settings.stimulus_threshold)
            if not anchors.size:
                raise ValueError(f'{label}: no {settings.anchor_source} anchor found')
            anchor = float(anchors[0])
        time -= anchor
        stim_time -= anchor
        y = signals.copy()
        gaps = np.asarray(rec.frame_gap_before, dtype=bool).copy()
        stim = np.tile(np.asarray(rec.stimulus, dtype=float)[:, None], (1, 3))
        gap_stim = _sample_gaps(rec)
        sem = np.full_like(y, np.nan)
        n = np.isfinite(y).astype(int)
        cycles = (0, 0, 0)
        excluded = (0, 0, 0)
    metrics = tuple(_metrics(time, y[:, neuron], gaps, settings.baseline_percentile,
                             settings.mode) for neuron in range(3))
    return ConditionResult(label, rec, time, y, gaps, sem, n,
                           stim_time, stim, gap_stim, cycles, excluded,
                           metrics, processing)


def _difference(ref: ConditionResult, cmp: ConditionResult, direction: str) -> tuple[np.ndarray, np.ndarray]:
    """Declared subtraction direction, only on mutually observed optical bins."""
    a, b = ref.x_ms, cmp.x_ms
    first = max(float(a[0]), float(b[0]))
    last = min(float(a[-1]), float(b[-1]))
    if first >= last:
        return np.array([]), np.empty((0, 3))
    steps = [float(np.median(np.diff(x))) for x in (a, b)]
    step = max(steps)
    if not np.isfinite(step) or step <= 0:
        raise ValueError('Cannot determine a common camera sampling interval')
    # A sparse shared grid cannot imply finer temporal precision than either
    # acquisition. Cap output sizes for long recordings.
    step = max(step, (last - first) / 10000)
    time = np.arange(first, last + step * 1e-6, step)
    result = np.full((len(time), 3), np.nan)
    for neuron in range(3):
        left = _interp_camera(a, ref.y[:, neuron], ref.gap_before, time)
        right = _interp_camera(b, cmp.y[:, neuron], cmp.gap_before, time)
        valid = np.isfinite(left) & np.isfinite(right)
        if direction == 'reference_minus_comparison':
            result[valid, neuron] = left[valid] - right[valid]
        else:
            result[valid, neuron] = right[valid] - left[valid]
    return time, result


def compare_recordings(reference, comparison, settings: ComparisonSettings,
                       processing_settings: ProcessingSettings | None = None) -> ComparisonResult:
    """Compare two acquisitions using identical declared analysis parameters.

    Stored ΔF/F0 and even identically processed ΔF/F0 are sensitive to
    indicator kinetics, noise and F0 definition; comparison does not establish
    equal underlying spike counts. Model-reference channels are never used.
    """
    _verify_settings(settings)
    if Path(reference.source).resolve() == Path(comparison.source).resolve():
        raise ValueError('Select an independently acquired comparison recording')
    units = 'a.u.' if settings.source == 'raw' else 'ΔF/F₀ (%)'
    left = _condition(reference, 'Reference', settings, processing_settings)
    right = _condition(comparison, 'Comparison', settings, processing_settings)
    notes = []
    for rec in (reference, comparison):
        for issue in rec.warnings:
            notes.append(f'{rec.source.name}: {issue}')
    a = reference.metadata
    b = comparison.metadata
    if a.get('indicator_name') != b.get('indicator_name'):
        notes.append('Indicators differ: optical kinetics, brightness and saturation prevent direct spike-count equivalence.')
    if a.get('fluorescence_model') != b.get('fluorescence_model'):
        notes.append('Fluorescence response models differ; even equal neural activity may give different optical signals.')
    if reference.nominal_frame_rate_hz != comparison.nominal_frame_rate_hz:
        notes.append('Frame rates differ: comparison resolution is limited by the slower camera acquisition.')
    if settings.source == 'recorded':
        if a.get('normalisation') != b.get('normalisation'):
            notes.append('Stored ΔF/F₀ uses each experiment’s model baseline/offset; definitions or values differ.')
        notes.append('Stored ΔF/F₀ uses simulator normalisation, not a common empirical baseline.')
    if settings.source == 'raw':
        notes.append('Raw fluorescence units are uncalibrated; subtraction across recordings is disabled.')
        time, delta = np.array([]), np.empty((0, 3))
    else:
        time, delta = _difference(left, right, settings.difference_direction)
        if not np.isfinite(delta).any():
            notes.append('No mutually observed optical bins are available for a meaningful subtraction.')
    # A changed stimulation protocol is itself a difference in conditions.
    # These simple peak/duty comparisons are screening checks, not full
    # waveform-equivalence tests; the plots always display both stimuli.
    try:
        first = np.asarray(left.stimulus[:, 0], dtype=float)
        second = np.asarray(right.stimulus[:, 0], dtype=float)
        v1, v2 = first[np.isfinite(first)], second[np.isfinite(second)]
        if v1.size and v2.size and (
            abs(float(np.max(v1))-float(np.max(v2))) > .5
            or abs(float(np.mean(v1))-float(np.mean(v2))) > 1.
        ):
            notes.append('Recorded stimulus level or duty cycle differs; compare experimental protocols before attributing optical changes.')
    except (TypeError, ValueError):
        pass
    if settings.mode == 'cycles' and left.cycles != right.cycles:
        notes.append('Accepted stimulus-cycle counts differ; compare response uncertainty and exclusions.')
    return ComparisonResult(settings, left, right, time, delta, units,
                            tuple(dict.fromkeys(notes)))
