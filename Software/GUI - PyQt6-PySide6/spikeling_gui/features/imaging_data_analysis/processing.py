"""Reproducible processing of frame-sampled single-pixel imaging recordings.

No access to simulated Vm/Ca/event truth is used. All operations are applied
*only* to measured optical frames and strictly separated by acquisition gaps.
The original ImagingRecording and its source files are never mutated.

Pipeline: optical background subtraction -> optional rolling-envelope bleach
correction -> optional per-segment smoothing -> empirical F0 -> 100*(F-F0)/F0.
A long-window rolling percentile is a simple didactic bleach estimator, not a
physical photobleach fit; transients may bias it. Always retain raw fluorescence.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
import pandas as pd
from scipy.signal import savgol_filter


@dataclass(frozen=True)
class ProcessingSettings:
    baseline_method: str = 'percentile'  # percentile / rolling / fixed
    baseline_percentile: float = 20.0
    baseline_start_ms: float = 0.0
    baseline_end_ms: float = 1000.0
    baseline_window_ms: float = 1000.0
    background_method: str = 'none'     # none / metadata / manual
    background_au: float = 0.0
    bleach_correct: bool = False
    bleach_window_ms: float = 3000.0
    filter_method: str = 'none'         # none / mean / savgol
    filter_window_ms: float = 50.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProcessedImaging:
    settings: ProcessingSettings
    time_ms: np.ndarray
    background_au: np.ndarray             # per channel, shape (3,)
    corrected_f_au: np.ndarray            # background-subtracted and bleach corrected, (frames,3)
    fluorescence_au: np.ndarray           # above, optionally smoothed
    bleach_envelope_au: np.ndarray        # estimated envelope before correction; NaN if inactive
    bleach_factor: np.ndarray             # multiplicative correction; 1 if inactive
    baseline_au: np.ndarray               # empirical baseline matching processed signal
    dff_percent: np.ndarray               # 100*(fluorescence-baseline)/baseline
    gaps_before: np.ndarray               # original camera clock gap flags
    metrics: tuple[dict[str, Any], ...]    # per neuron, quality proxies
    warnings: tuple[str, ...]

    def parameters(self) -> dict[str, Any]:
        return {
            'settings': self.settings.to_dict(),
            'baseline_equation': '100 * (F_processed - F0_empirical) / F0_empirical',
            'processing_order': [
                'background subtraction',
                'optional rolling-percentile photobleaching envelope correction',
                'optional within-segment smoothing',
                'empirical baseline', 'DF/F0',
            ],
            'bleach_method': '20th percentile rolling envelope, segment-wise multiplicative detrending',
            'gap_policy': 'Never interpolate or filter across missing camera frames',
            'model_reference_used': False,
            'warnings': list(self.warnings),
        }


def _validate(settings: ProcessingSettings, rec) -> None:
    if settings.baseline_method not in ('percentile', 'rolling', 'fixed'):
        raise ValueError('Choose fixed, percentile, or rolling percentile baseline')
    if settings.background_method not in ('none', 'metadata', 'manual'):
        raise ValueError('Choose a valid optical background method')
    if settings.filter_method not in ('none', 'mean', 'savgol'):
        raise ValueError('Choose a valid noise filter')
    values = (settings.baseline_percentile, settings.baseline_start_ms,
              settings.baseline_end_ms, settings.baseline_window_ms,
              settings.background_au, settings.bleach_window_ms, settings.filter_window_ms)
    if not all(np.isfinite(v) for v in values):
        raise ValueError('Processing parameters must be finite numbers')
    if not 0 <= settings.baseline_percentile <= 100:
        raise ValueError('Baseline percentile must be between 0 and 100')
    if settings.baseline_method == 'fixed' and settings.baseline_end_ms <= settings.baseline_start_ms:
        raise ValueError('Fixed baseline end must be greater than start')
    if settings.baseline_method == 'rolling' and settings.baseline_window_ms <= 0:
        raise ValueError('Rolling baseline window must be positive')
    if settings.bleach_correct and settings.bleach_window_ms <= 0:
        raise ValueError('Bleaching envelope window must be positive')
    if settings.filter_method != 'none' and settings.filter_window_ms <= 0:
        raise ValueError('Filtering window must be positive')
    if rec.n_frames < 2:
        raise ValueError('At least two camera frames are needed for processing')
    if rec.frame_fluorescence_au.shape != (rec.n_frames, 3):
        raise ValueError('Expected three one-pixel fluorescence channels')
    if len(rec.frame_gap_before) != rec.n_frames:
        raise ValueError('Frame gap flags do not match recording')


def _continuous_segments(valid: np.ndarray, gaps: np.ndarray) -> list[np.ndarray]:
    """Contiguous *observed* frame indices, split on clock gaps or NaN frames."""
    indices = np.flatnonzero(valid)
    if not len(indices):
        return []
    split = np.flatnonzero((np.diff(indices) != 1) | gaps[indices[1:]]) + 1
    return [part for part in np.split(indices, split) if part.size]


def _window_n(window_ms: float, time_ms: np.ndarray, *, odd=False) -> int:
    if len(time_ms) < 2:
        return 1
    dt = float(np.median(np.diff(time_ms)))
    if not np.isfinite(dt) or dt <= 0:
        return 1
    samples = max(1, int(round(window_ms / dt)))
    if odd and samples % 2 == 0:
        samples += 1
    return samples


def _rolling_percentile(values: np.ndarray, window: int, percentile: float) -> np.ndarray:
    if window <= 1:
        return values.copy()
    return (pd.Series(values).rolling(window, center=True, min_periods=1)
            .quantile(percentile / 100.0).to_numpy(dtype=float))


def _noise_sd(signal: np.ndarray, segments: list[np.ndarray]) -> float:
    """Robust, approximate camera noise from within-segment first differences."""
    differences = [np.diff(signal[idx]) for idx in segments if len(idx) >= 3]
    if not differences:
        return float('nan')
    delta = np.concatenate(differences)
    delta = delta[np.isfinite(delta)]
    if not len(delta):
        return float('nan')
    mad = np.median(np.abs(delta - np.median(delta)))
    return float(1.4826 * mad / np.sqrt(2.0))


def _background(rec, settings) -> np.ndarray:
    if settings.background_method == 'none':
        return np.zeros(3, dtype=float)
    if settings.background_method == 'manual':
        return np.full(3, settings.background_au, dtype=float)
    norm = rec.metadata.get('normalisation', {})
    if not isinstance(norm, dict) or 'offset_a.u.' not in norm:
        raise ValueError('Recording metadata does not declare optical offset_a.u.')
    raw = np.asarray(norm['offset_a.u.'], dtype=float)
    if raw.size == 1:
        raw = np.full(3, float(raw.item()), dtype=float)
    if raw.shape != (3,) or not np.isfinite(raw).all():
        raise ValueError('Recorded optical offset must be finite (one or three values)')
    return raw


def process_imaging_recording(rec, settings: ProcessingSettings) -> ProcessedImaging:
    """Compute three independently processed optical channels on camera frames."""
    _validate(settings, rec)
    time = np.asarray(rec.frame_time_ms, dtype=float)
    raw = np.asarray(rec.frame_fluorescence_au, dtype=float)
    gaps = np.asarray(rec.frame_gap_before, dtype=bool)
    background = _background(rec, settings)
    result = raw - background[None, :]
    fluorescence = np.full_like(result, np.nan, dtype=float)
    corrected = np.full_like(result, np.nan, dtype=float)
    baseline = np.full_like(result, np.nan, dtype=float)
    dff = np.full_like(result, np.nan, dtype=float)
    envelope = np.full_like(result, np.nan, dtype=float)
    factor = np.full_like(result, np.nan, dtype=float)
    warnings = []
    metrics = []
    expected_step = 1000.0 / rec.nominal_frame_rate_hz
    dt = np.diff(time)
    good_dt = dt[~gaps[1:] & np.isfinite(dt) & (dt > 0)]
    effective_hz = float(1000.0 / np.median(good_dt)) if len(good_dt) else None
    estimated_missing = int(np.sum(np.maximum(0, np.rint(dt[gaps[1:]] / expected_step).astype(int) - 1)))

    for neuron in range(3):
        original = result[:, neuron]
        valid = np.isfinite(original)
        segments = _continuous_segments(valid, gaps)
        if not segments:
            warnings.append(f'Neuron {neuron + 1}: no valid camera-frame fluorescence')
            metrics.append({'neuron': neuron + 1, 'valid_frames': 0, 'missing_frames_estimated': estimated_missing,
                            'frame_gap_boundaries': int(gaps.sum()), 'effective_rate_hz': effective_hz,
                            'noise_sd_au': None, 'snr_proxy': None})
            continue
        if settings.baseline_method == 'fixed':
            selected = valid & (time >= settings.baseline_start_ms) & (time <= settings.baseline_end_ms)
            if not selected.any():
                raise ValueError(f'Neuron {neuron+1}: no camera frames inside fixed baseline window')
        for idx in segments:
            y = original[idx].copy()
            trend = np.full(len(y), np.nan)
            gain = np.ones(len(y), dtype=float)
            if settings.bleach_correct:
                win = _window_n(settings.bleach_window_ms, time[idx], odd=True)
                trend = _rolling_percentile(y, win, 20.0)
                initial = float(np.median(trend[:min(len(trend), max(3, win // 2))]))
                if initial <= 1e-10 or np.any(trend <= 1e-10):
                    raise ValueError(f'Neuron {neuron+1}: non-positive bleaching envelope; '
                                     'check background and optical signal')
                gain = initial / trend
                if np.any((gain < 0.2) | (gain > 5.0)):
                    warnings.append(f'Neuron {neuron+1}: bleaching gain capped to 0.2–5; inspect drift model')
                    gain = np.clip(gain, 0.2, 5.0)
                y *= gain
            corrected[idx, neuron] = y
            envelope[idx, neuron] = trend
            factor[idx, neuron] = gain
            if settings.filter_method == 'mean':
                win = _window_n(settings.filter_window_ms, time[idx], odd=True)
                y = pd.Series(y).rolling(win, center=True, min_periods=1).mean().to_numpy(dtype=float)
            elif settings.filter_method == 'savgol':
                win = _window_n(settings.filter_window_ms, time[idx], odd=True)
                win = min(win, len(idx) if len(idx) % 2 else len(idx)-1)
                if win >= 5:
                    y = savgol_filter(y, win, polyorder=2, mode='interp')
                else:
                    warnings.append(f'Neuron {neuron+1}: short segment not Savitzky–Golay filtered')
            fluorescence[idx, neuron] = y
        if settings.baseline_method == 'fixed':
            f0 = float(np.median(fluorescence[selected, neuron]))
            if f0 <= 1e-10:
                raise ValueError(f'Neuron {neuron+1}: fixed F0 is zero or negative; check background')
            baseline[valid, neuron] = f0
        else:
            for idx in segments:
                values = fluorescence[idx, neuron]
                if settings.baseline_method == 'percentile':
                    f0 = np.full(len(idx), float(np.percentile(values, settings.baseline_percentile)))
                else:
                    win = _window_n(settings.baseline_window_ms, time[idx], odd=True)
                    f0 = _rolling_percentile(values, win, settings.baseline_percentile)
                if not np.isfinite(f0).all() or np.any(f0 <= 1e-10):
                    raise ValueError(f'Neuron {neuron+1}: F0 is zero or negative; check background')
                baseline[idx, neuron] = f0
        dff[valid, neuron] = 100.0 * (
            fluorescence[valid, neuron] - baseline[valid, neuron]
        ) / baseline[valid, neuron]
        noise = _noise_sd(fluorescence[:, neuron], segments)
        delta_peak = float(np.nanmax(fluorescence[:, neuron] - baseline[:, neuron]))
        snr = float(delta_peak / noise) if np.isfinite(noise) and noise > 1e-12 else None
        metrics.append({
            'neuron': neuron + 1,
            'valid_frames': int(valid.sum()),
            'frame_gap_boundaries': int(gaps.sum()),
            'missing_frames_estimated': estimated_missing,
            'effective_rate_hz': effective_hz,
            'noise_sd_au': noise if np.isfinite(noise) else None,
            'snr_proxy': snr,
            'median_f0_au': float(np.nanmedian(baseline[:, neuron])),
            'peak_dff_percent': float(np.nanmax(dff[:, neuron])),
        })
    return ProcessedImaging(settings, time.copy(), background, corrected, fluorescence,
                            envelope, factor, baseline, dff, gaps.copy(), tuple(metrics),
                            tuple(dict.fromkeys(warnings)))
