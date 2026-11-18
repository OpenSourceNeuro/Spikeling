"""Educational fluorescence-only nonnegative event inference and *separate* validation.

Three independent single-pixel channels. Inference uses *only* saved camera-frame
DeltaF/F0. Model sample Vm, calcium and native/threshold event flags are never
accessed by ``infer_activity``. Ground-truth/reference flags are accessed only
by ``validate_activity`` after explicit user action.

AR(1) kernel: exponential decay. AR(2)-like kernel: normalised difference of
rise/decay exponentials. A segment-wise nonnegative, L1-penalised least-squares
fit uses FISTA and exact linear-operator adjoints; this is *not* an OASIS or
statistically calibrated spike posterior. Sparse innovations are candidate
neural events, NOT verified spikes or their biological amplitude.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
from scipy.signal import find_peaks, lfilter


@dataclass(frozen=True)
class InferenceSettings:
    source: str = 'recorded'                 # recorded / processed
    model: str = 'ar1'                      # ar1 / ar2
    decay_ms: float = 300.0
    rise_ms: float = 50.0
    baseline_percentile: float = 20.0
    sparsity_penalty: float = 0.5           # objective L1 coefficient; ΔF/F0 percentage points
    event_threshold: float = 0.8           # inferred innovation, percentage points
    min_separation_ms: float = 70.0
    analysis_interval_ms: float = 20.0     # optional measured-frame coarsening, explicit
    max_iterations: int = 180

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class InferredEvent:
    neuron: int                              # 1, 2, 3
    time_ms: float
    innovation_percent: float
    frame_index: int

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class InferenceResult:
    settings: InferenceSettings
    time_ms: np.ndarray
    measured_dff_percent: np.ndarray
    reconstruction_percent: np.ndarray
    baseline_percent: np.ndarray
    innovations_percent: np.ndarray
    gaps_before: np.ndarray
    events: tuple[InferredEvent, ...]
    metrics: tuple[dict[str, Any], ...]
    warnings: tuple[str, ...]

    def for_neuron(self, neuron_index: int) -> tuple[InferredEvent, ...]:
        return tuple(event for event in self.events if event.neuron == neuron_index + 1)


@dataclass(frozen=True)
class ValidationResult:
    rows: tuple[dict[str, Any], ...]          # each inferred event, plus missed references
    metrics: tuple[dict[str, Any], ...]
    tolerance_ms: float
    bin_ms: float
    provenance: str
    warnings: tuple[str, ...]


def _validate_settings(settings: InferenceSettings, recording, processed) -> np.ndarray:
    if settings.source not in ('recorded', 'processed'):
        raise ValueError('Choose recorded or processed ΔF/F₀')
    if settings.model not in ('ar1', 'ar2'):
        raise ValueError('Choose AR(1) or AR(2)-like response')
    for name in ('decay_ms', 'rise_ms', 'baseline_percentile', 'sparsity_penalty',
                 'event_threshold', 'min_separation_ms', 'analysis_interval_ms'):
        if not np.isfinite(getattr(settings, name)):
            raise ValueError(f'{name} must be finite')
    if not 0 <= settings.baseline_percentile <= 100:
        raise ValueError('Baseline percentile must be between 0 and 100')
    if settings.decay_ms <= 0 or settings.rise_ms <= 0:
        raise ValueError('Rise and decay must be positive')
    if settings.model == 'ar2' and settings.rise_ms >= settings.decay_ms:
        raise ValueError('AR(2)-like model needs rise time shorter than decay time')
    if min(settings.sparsity_penalty, settings.event_threshold, settings.min_separation_ms) < 0:
        raise ValueError('Sparsity penalty, event threshold and separation must be non-negative')
    if settings.analysis_interval_ms <= 0:
        raise ValueError('Inference interval must be positive')
    if not isinstance(settings.max_iterations, int) or not 10 <= settings.max_iterations <= 2000:
        raise ValueError('Iterations must be an integer in 10–2000')
    if recording.n_frames < 3:
        raise ValueError('Inference requires at least three acquired camera frames')
    if settings.source == 'processed':
        if processed is None:
            raise ValueError('Apply processing first or select recorded ΔF/F₀')
        if not np.array_equal(np.asarray(processed.time_ms), recording.frame_time_ms):
            raise ValueError('Processed signal belongs to another acquisition')
        y = np.asarray(processed.dff_percent, dtype=float)
    else:
        y = np.asarray(recording.recorded_dff_percent, dtype=float)
    if y.shape != (recording.n_frames, 3) or np.isinf(y).any():
        raise ValueError('Expected three finite-or-NaN camera-frame ΔF/F₀ channels')
    if (len(recording.frame_gap_before) != recording.n_frames
            or not np.isfinite(recording.frame_time_ms).all()
            or np.any(np.diff(recording.frame_time_ms) <= 0)):
        raise ValueError('Invalid camera acquisition timing')
    return y


def _segments(valid: np.ndarray, gaps: np.ndarray) -> list[np.ndarray]:
    indices = np.flatnonzero(valid)
    if not indices.size:
        return []
    cuts = np.flatnonzero((np.diff(indices) != 1) | gaps[indices[1:]]) + 1
    return [part for part in np.split(indices, cuts) if len(part)]


class _Kernel:
    """Linear fluorescence kernel with true adjoint, including irregular frames."""

    def __init__(self, t: np.ndarray, settings: InferenceSettings):
        dt = np.diff(t)
        if not dt.size or np.any(dt <= 0):
            raise ValueError('Need increasing frame timestamps')
        self.uniform = bool(np.allclose(dt, np.median(dt), rtol=1e-5, atol=1e-6))
        decay_factors = np.exp(-dt / settings.decay_ms)
        self.decay = np.r_[0., decay_factors]
        if settings.model == 'ar2':
            rise_factors = np.exp(-dt / settings.rise_ms)
            self.rise = np.r_[0., rise_factors]
            t_peak = np.log(settings.decay_ms / settings.rise_ms) / (
                1.0 / settings.rise_ms - 1.0 / settings.decay_ms)
            peak = np.exp(-t_peak / settings.decay_ms) - np.exp(-t_peak / settings.rise_ms)
            self.scale = 1.0 / peak
        else:
            self.rise = None
            self.scale = 1.0

    @staticmethod
    def _forward(x: np.ndarray, a: np.ndarray, uniform: bool) -> np.ndarray:
        if uniform:
            return lfilter([1.0], [1.0, -a[1]], x)
        result = np.empty_like(x)
        last = 0.0
        for i, value in enumerate(x):
            last = value + a[i] * last
            result[i] = last
        return result

    @staticmethod
    def _adjoint(y: np.ndarray, a: np.ndarray, uniform: bool) -> np.ndarray:
        if uniform:
            return lfilter([1.0], [1.0, -a[1]], y[::-1])[::-1].copy()
        result = np.empty_like(y)
        last = 0.0
        for i in range(len(y) - 1, -1, -1):
            last = y[i] + (a[i + 1] * last if i + 1 < len(y) else 0.)
            result[i] = last
        return result

    def apply(self, s: np.ndarray) -> np.ndarray:
        z = self._forward(s, self.decay, self.uniform)
        if self.rise is not None:
            z = (z - self._forward(s, self.rise, self.uniform)) * self.scale
        return z

    def transpose(self, residual: np.ndarray) -> np.ndarray:
        z = self._adjoint(residual, self.decay, self.uniform)
        if self.rise is not None:
            z = (z - self._adjoint(residual, self.rise, self.uniform)) * self.scale
        return z


def _sparse_fit(t: np.ndarray, signal: np.ndarray, settings: InferenceSettings):
    """FISTA solve min_{s>=0} 0.5*||A s-y||² + lambda*sum(s)."""
    operator = _Kernel(t, settings)
    n = len(t)
    direction = np.full(n, 1. / np.sqrt(n))
    for _ in range(18):
        next_direction = operator.transpose(operator.apply(direction))
        length = np.linalg.norm(next_direction)
        if length < 1e-16:
            break
        direction = next_direction / length
    # Safety margin above the measured spectral norm; no dense convolution matrix.
    lipschitz = max(1e-8, float(direction @ operator.transpose(operator.apply(direction))) * 1.12)
    x = np.zeros(n, dtype=float)
    momentum = x.copy()
    step = 1.0
    target = np.asarray(signal, dtype=float)
    for _ in range(settings.max_iterations):
        gradient = operator.transpose(operator.apply(momentum) - target)
        updated = np.maximum(momentum - (gradient + settings.sparsity_penalty) / lipschitz, 0.0)
        if np.linalg.norm(updated - x) < 1e-5 * (1. + np.linalg.norm(x)):
            x = updated
            break
        previous = step
        step = (1 + np.sqrt(1 + 4 * previous * previous)) / 2
        momentum = updated + ((previous - 1) / step) * (updated - x)
        x = updated
    return x, operator.apply(x)


def _peak_indices(indices: np.ndarray, t: np.ndarray, values: np.ndarray,
                  threshold: float, separation_ms: float) -> list[int]:
    if len(indices) == 0:
        return []
    y = values[indices]
    # Pad so that the first/last observed frame can be identified as a peak.
    candidates = find_peaks(np.r_[0., y, 0.], height=max(0., threshold))[0] - 1
    candidates = [int(indices[i]) for i in candidates if y[i] > 0. and y[i] >= threshold]
    # Select strongest first, enforcing separation in *time*, not frame count.
    selected: list[int] = []
    for i in sorted(candidates, key=lambda i: -values[i]):
        if all(abs(t[i] - t[j]) >= separation_ms for j in selected):
            selected.append(i)
    return sorted(selected, key=lambda i: t[i])


def _analysis_indices(t: np.ndarray, min_interval_ms: float) -> np.ndarray:
    """Select observed frames only. Never interpolate or cross a camera gap."""
    if len(t) <= 3 or np.min(np.diff(t)) >= min_interval_ms - 1e-8:
        return np.arange(len(t))
    out = [0]
    for i in range(1, len(t)):
        if t[i] - t[out[-1]] >= min_interval_ms - 1e-8:
            out.append(i)
    if out[-1] != len(t) - 1:
        out.append(len(t) - 1)
    return np.asarray(out, dtype=int)


def infer_activity(recording, processed=None, settings: InferenceSettings | None = None) -> InferenceResult:
    """Infer optical innovations without *any* access to reference neural events."""
    settings = settings or InferenceSettings()
    measured = _validate_settings(settings, recording, processed)
    time = np.asarray(recording.frame_time_ms, dtype=float)
    gaps = np.asarray(recording.frame_gap_before, dtype=bool)
    prediction = np.full_like(measured, np.nan)
    baseline = np.full_like(measured, np.nan)
    innovations = np.full_like(measured, np.nan)
    all_events: list[InferredEvent] = []
    metrics: list[dict[str, Any]] = []
    warnings: list[str] = []
    if np.any(np.diff(time) < settings.analysis_interval_ms):
        warnings.append('Inference uses observed-frame subsampling for stability; event times are limited by the chosen inference interval')
    if gaps.any():
        warnings.append(f'{int(gaps.sum())} camera gap boundary/boundaries; fitted independently')
    for neuron in range(3):
        values = measured[:, neuron]
        segments = _segments(np.isfinite(values), gaps)
        valid_count = 0
        fit_count = 0
        analysis_count = 0
        for indices in segments:
            if len(indices) < 3:
                # No fit or reconstructed events in segments too short to resolve kinetics.
                warnings.append(f'Neuron {neuron+1}: skipped {len(indices)}-frame segment')
                continue
            ts = time[indices]
            ys = values[indices]
            b = float(np.percentile(ys, settings.baseline_percentile))
            take = _analysis_indices(ts, settings.analysis_interval_ms)
            coarse_impulses, _ = _sparse_fit(ts[take], (ys-b)[take], settings)
            impulses = np.zeros(len(ts), dtype=float)
            impulses[take] = coarse_impulses
            fitted = _Kernel(ts, settings).apply(impulses)
            baseline[indices, neuron] = b
            prediction[indices, neuron] = b + fitted
            innovations[indices, neuron] = impulses
            analysis_count += len(take)
            valid_count += len(indices)
            fit_count += 1
            for k in _peak_indices(indices, time, innovations[:, neuron],
                                   settings.event_threshold, settings.min_separation_ms):
                all_events.append(InferredEvent(neuron+1, float(time[k]),
                                                float(innovations[k, neuron]), int(k)))
        use = np.isfinite(prediction[:, neuron]) & np.isfinite(values)
        if np.any(use):
            residual = values[use] - prediction[use, neuron]
            rmse = float(np.sqrt(np.mean(residual**2)))
            variance = float(np.sum((values[use] - np.mean(values[use]))**2))
            r2 = None if variance <= 1e-12 else float(1. - np.sum(residual**2) / variance)
        else:
            rmse, r2 = None, None
        metrics.append({
            'neuron': neuron+1, 'fitted_frames': valid_count, 'segments_fitted': fit_count,
            'inferred_event_count': sum(e.neuron == neuron+1 for e in all_events),
            'analysis_frames': analysis_count, 'requested_analysis_interval_ms': settings.analysis_interval_ms,
            'reconstruction_rmse_percent': rmse, 'reconstruction_r2': r2,
        })
    if not all(m['segments_fitted'] for m in metrics):
        warnings.append('Some channels have insufficient finite camera frames for inference')
    return InferenceResult(settings, time.copy(), measured.copy(), prediction, baseline,
                           innovations, gaps.copy(), tuple(all_events), tuple(metrics), tuple(warnings))


def _one_to_one_match(estimated: np.ndarray, reference: np.ndarray, tolerance: float):
    """Nearest-first, strictly one-to-one assignment in a finite temporal window."""
    candidates = []
    for i, t in enumerate(estimated):
        lo = int(np.searchsorted(reference, t-tolerance))
        hi = int(np.searchsorted(reference, t+tolerance, side='right'))
        candidates.extend((abs(float(reference[j] - t)), i, j) for j in range(lo, hi))
    matched_est, matched_ref, matches = set(), set(), []
    for _, i, j in sorted(candidates):
        if i not in matched_est and j not in matched_ref:
            matched_est.add(i)
            matched_ref.add(j)
            matches.append((i, j))
    return matches, matched_est, matched_ref


def _observable_segments(result: InferenceResult, neuron: int):
    valid = np.isfinite(result.measured_dff_percent[:, neuron]) & np.isfinite(result.reconstruction_percent[:, neuron])
    return [result.time_ms[indices] for indices in _segments(valid, result.gaps_before)
            if len(indices) >= 2]


def _bin_rate_correlation(estimated: np.ndarray, reference: np.ndarray,
                          runs: list[np.ndarray], bin_ms: float) -> float | None:
    # Compare event counts only in fully observed, non-overlapping intervals.
    estimated_counts, reference_counts = [], []
    for t in runs:
        start, end = float(t[0]), float(t[-1])
        while start + bin_ms <= end + 1e-8:
            stop = start + bin_ms
            estimated_counts.append(int(np.count_nonzero((estimated >= start) & (estimated < stop))))
            reference_counts.append(int(np.count_nonzero((reference >= start) & (reference < stop))))
            start = stop
    if len(estimated_counts) < 3 or np.std(estimated_counts) == 0 or np.std(reference_counts) == 0:
        return None
    return float(np.corrcoef(estimated_counts, reference_counts)[0, 1])


def validate_activity(recording, inference: InferenceResult,
                      tolerance_ms: float = 100., bin_ms: float = 1000.) -> ValidationResult:
    """Reveal saved reference flags *only after* inference is frozen."""
    if not (np.isfinite(tolerance_ms) and tolerance_ms > 0 and np.isfinite(bin_ms) and bin_ms > 0):
        raise ValueError('Matching tolerance and rate bin must be positive and finite')
    if (not np.array_equal(inference.time_ms, recording.frame_time_ms)
            or inference.measured_dff_percent.shape != recording.recorded_dff_percent.shape):
        raise ValueError('Inference result does not correspond to this acquisition')
    flags = np.asarray(recording.reference_events)
    if flags.shape != (recording.n_samples, 3):
        raise ValueError('Missing three-channel saved reference event flags')
    reference_time = np.asarray(recording.sample_time_ms, dtype=float)
    if not len(reference_time) or not np.all(np.diff(reference_time) > 0):
        raise ValueError('Invalid saved reference event timestamps')
    provenance = ', '.join(recording.metadata.get('event_provenance', [])) or 'unspecified'
    rows: list[dict[str, Any]] = []
    metrics = []
    warnings = []
    if 'Vm threshold crossings' in provenance or recording.source_kind == 'spikeling':
        warnings.append('Hardware references can be Vm-threshold detections, not independently measured ground-truth spikes')
    if 'source events' not in provenance and 'Vm threshold crossings' not in provenance:
        warnings.append('Source reference-event provenance is not fully specified')
    for neuron in range(3):
        runs = _observable_segments(inference, neuron)
        all_ref = reference_time[np.flatnonzero(flags[:, neuron] != 0)]
        def observable(event_time):
            return any(t[0] - 1e-9 <= event_time <= t[-1] + 1e-9 for t in runs)
        ref = np.asarray([t for t in all_ref if observable(t)], dtype=float)
        estimated = np.asarray([e.time_ms for e in inference.for_neuron(neuron)], dtype=float)
        matches, matched_e, matched_r = _one_to_one_match(estimated, ref, tolerance_ms)
        index_matches = {i: j for i, j in matches}
        for i, t in enumerate(estimated):
            j = index_matches.get(i)
            rows.append({'neuron': neuron+1, 'estimated_ms': float(t),
                         'reference_ms': float(ref[j]) if j is not None else None,
                         'time_error_ms': float(t-ref[j]) if j is not None else None,
                         'classification': 'matched' if j is not None else 'unmatched inference'})
        for j, t in enumerate(ref):
            if j not in matched_r:
                rows.append({'neuron': neuron+1, 'estimated_ms': None,
                             'reference_ms': float(t), 'time_error_ms': None,
                             'classification': 'missed reference'})
        tp = len(matches)
        fp = len(estimated) - tp
        fn = len(ref) - tp
        precision = tp / (tp + fp) if tp+fp else None
        recall = tp / (tp + fn) if tp+fn else None
        f1 = 2*precision*recall/(precision+recall) if precision is not None and recall is not None and (precision+recall)>0 else (0. if precision is not None and recall is not None else None)
        errors = [float(estimated[i]-ref[j]) for i, j in matches]
        metrics.append({'neuron': neuron+1, 'matched': tp, 'false_positive': fp, 'false_negative': fn,
                        'estimated_count': len(estimated), 'observable_reference_count': len(ref),
                        'unobservable_reference_count': len(all_ref)-len(ref),
                        'precision': precision, 'recall': recall, 'f1': f1,
                        'median_absolute_timing_error_ms': float(np.median(np.abs(errors))) if errors else None,
                        'median_signed_timing_error_ms': float(np.median(errors)) if errors else None,
                        'binned_rate_correlation': _bin_rate_correlation(estimated, ref, runs, bin_ms)})
    return ValidationResult(tuple(rows), tuple(metrics), tolerance_ms, bin_ms,
                            provenance, tuple(warnings))
