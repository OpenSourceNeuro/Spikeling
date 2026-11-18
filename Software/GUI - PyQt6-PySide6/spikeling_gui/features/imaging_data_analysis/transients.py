"""Calcium-fluorescence transient detection and descriptive kinetics.

This module uses saved camera-frame ΔF/F0, never model Vm, Ca or native spike
flags. It does not equate fluorescence peaks with individual action potentials.
An event is an operationally detected fluorescence transient, not a spike.

All features are measured within *observed* continuous camera segments.
Discontinuities and NaN values are never interpolated through or treated as
physiological recovery. Stimulus association uses recorded onset times only.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Any

import numpy as np
from scipy.signal import find_peaks, peak_widths

from .align import find_anchors


@dataclass(frozen=True)
class TransientSettings:
    source: str = 'recorded'  # recorded, processed
    min_prominence_percent: float = 5.0
    min_amplitude_percent: float = 5.0
    min_width_ms: float = 20.0
    min_separation_ms: float = 150.0
    baseline_window_ms: float = 200.0
    response_source: str = 'trigger'  # none, trigger, stimulus
    stimulus_threshold: float = 0.0
    response_window_ms: float = 500.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Transient:
    neuron: int
    onset_ms: float | None
    peak_ms: float
    recovery_ms: float | None
    peak_dff_percent: float
    baseline_dff_percent: float
    amplitude_percent: float
    prominence_percent: float
    fwhm_ms: float
    rise_10_90_ms: float | None
    decay_1e_ms: float | None
    auc_percent_ms: float | None
    stimulus_onset_ms: float | None = None
    response_latency_ms: float | None = None
    notes: str = ''

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TransientResult:
    settings: TransientSettings
    signal_source: str
    time_ms: np.ndarray
    dff_percent: np.ndarray   # (frames, 3)
    gaps_before: np.ndarray
    events: tuple[Transient, ...]
    metrics: tuple[dict[str, Any], ...]  # one per neuron
    stimulus_onsets_ms: np.ndarray
    response_trials: tuple[dict[str, Any], ...]
    warnings: tuple[str, ...]

    def for_neuron(self, neuron: int) -> tuple[Transient, ...]:
        return tuple(e for e in self.events if e.neuron == neuron + 1)


def _segments(valid: np.ndarray, gaps_before: np.ndarray) -> list[np.ndarray]:
    """Get contiguous finite camera-frame runs, never crossing an acquisition gap."""
    indices = np.flatnonzero(valid)
    if indices.size == 0:
        return []
    split = np.flatnonzero((np.diff(indices) != 1) | gaps_before[indices[1:]]) + 1
    return [part for part in np.split(indices, split) if len(part)]


def _interp_fractional_time(t: np.ndarray, index: float) -> float:
    return float(np.interp(index, np.arange(len(t), dtype=float), t))


def _rise_crossing(t: np.ndarray, y: np.ndarray, left: int, peak: int,
                   level: float) -> float | None:
    """Last upward level crossing before the peak; interpolate adjacent frames."""
    for k in range(peak, left, -1):
        if y[k - 1] <= level < y[k]:
            fraction = (level - y[k - 1]) / (y[k] - y[k - 1])
            return float(t[k - 1] + fraction * (t[k] - t[k - 1]))
    return None


def _fall_crossing(t: np.ndarray, y: np.ndarray, peak: int,
                   level: float) -> float | None:
    for k in range(peak + 1, len(y)):
        if y[k] <= level < y[k - 1]:
            fraction = (y[k - 1] - level) / (y[k - 1] - y[k])
            return float(t[k - 1] + fraction * (t[k] - t[k - 1]))
    return None


def _auc(t: np.ndarray, y: np.ndarray, baseline: float,
         onset: float | None, recovery: float | None) -> float | None:
    if onset is None or recovery is None or recovery <= onset:
        return None
    inside = (t > onset) & (t < recovery)
    x = np.r_[onset, t[inside], recovery]
    values = np.interp(x, t, y)
    return float(np.trapezoid(np.maximum(values - baseline, 0.0), x))


def _validate(recording, processed, settings: TransientSettings) -> np.ndarray:
    if settings.source not in ('recorded', 'processed'):
        raise ValueError('Choose recorded or processed ΔF/F₀')
    if settings.response_source not in ('none', 'trigger', 'stimulus'):
        raise ValueError('Choose None, Trigger or Stimulus onsets for association')
    values = (
        settings.min_prominence_percent, settings.min_amplitude_percent,
        settings.min_width_ms, settings.min_separation_ms,
        settings.baseline_window_ms, settings.stimulus_threshold,
        settings.response_window_ms,
    )
    if not all(np.isfinite(x) for x in values):
        raise ValueError('Transient parameters must be finite')
    if any(x < 0 for x in values[:4]):
        raise ValueError('Amplitude, prominence, width and separation cannot be negative')
    if settings.baseline_window_ms <= 0:
        raise ValueError('Local baseline window must be positive')
    if settings.response_window_ms <= 0:
        raise ValueError('Post-stimulus response window must be positive')
    if recording.n_frames < 3:
        raise ValueError('At least three acquired camera frames are required')
    if settings.source == 'processed':
        if processed is None:
            raise ValueError('Apply signal processing in the Processing tab first')
        signal = np.asarray(processed.dff_percent, dtype=float)
        if not np.array_equal(processed.time_ms, recording.frame_time_ms):
            raise ValueError('Processed signal is not aligned with this acquisition')
    else:
        signal = np.asarray(recording.recorded_dff_percent, dtype=float)
    if (signal.shape != (recording.n_frames, 3)
            or np.isinf(signal).any()
            or len(recording.frame_gap_before) != recording.n_frames):
        raise ValueError('Expected three valid camera-frame ΔF/F₀ channels')
    if (not np.isfinite(recording.frame_time_ms).all()
            or np.any(np.diff(recording.frame_time_ms) <= 0)):
        raise ValueError('Camera-frame time must be finite and strictly increasing')
    return signal


def _channel_events(t: np.ndarray, y: np.ndarray, gaps: np.ndarray,
                    settings: TransientSettings, neuron: int) -> tuple[Transient, ...]:
    candidates: list[Transient] = []
    for ids in _segments(np.isfinite(y), gaps):
        if len(ids) < 3:
            continue
        clock = t[ids]
        values = y[ids]
        peaks, props = find_peaks(values, prominence=settings.min_prominence_percent)
        if len(peaks) == 0:
            continue
        widths, _, left_ips, right_ips = peak_widths(values, peaks, rel_height=0.5)
        # A minimum width is measured against *real* camera-frame times, not
        # simply number of frames, to remain valid for irregular acquisition.
        for j, peak in enumerate(peaks):
            width_ms = (_interp_fractional_time(clock, float(right_ips[j]))
                        - _interp_fractional_time(clock, float(left_ips[j])))
            if width_ms + 1e-9 < settings.min_width_ms:
                continue
            pre = (clock >= clock[peak] - settings.baseline_window_ms) & (clock < clock[peak])
            previous = values[pre]
            if len(previous) < 2:
                continue  # local baseline cannot be estimated reliably
            baseline = float(np.percentile(previous, 20.0))
            amplitude = float(values[peak] - baseline)
            if amplitude <= 0 or amplitude + 1e-9 < settings.min_amplitude_percent:
                continue
            # Find the rise relative to the local baseline; restrict the search
            # to SciPy's prominence left base to avoid an earlier event.
            left = int(props['left_bases'][j])
            t10 = _rise_crossing(clock, values, left, int(peak), baseline + .1 * amplitude)
            t90 = _rise_crossing(clock, values, left, int(peak), baseline + .9 * amplitude)
            recovery = _fall_crossing(clock, values, int(peak), baseline + .1 * amplitude)
            t1e = _fall_crossing(clock, values, int(peak), baseline + amplitude / np.e)
            notes = []
            if t10 is None or t90 is None:
                notes.append('rise not fully resolved')
            if recovery is None:
                notes.append('recovery not observed before segment end')
            if t1e is None:
                notes.append('1/e decay not observed')
            candidates.append(Transient(
                neuron=neuron + 1,
                onset_ms=t10,
                peak_ms=float(clock[peak]),
                recovery_ms=recovery,
                peak_dff_percent=float(values[peak]),
                baseline_dff_percent=baseline,
                amplitude_percent=amplitude,
                prominence_percent=float(props['prominences'][j]),
                fwhm_ms=max(0.0, float(width_ms)),
                rise_10_90_ms=(max(0.0, t90 - t10) if t10 is not None and t90 is not None else None),
                decay_1e_ms=(max(0.0, t1e - clock[peak]) if t1e is not None else None),
                auc_percent_ms=_auc(clock, values, baseline, t10, recovery),
                notes='; '.join(notes),
            ))
    # Perform refractory/minimum-separation selection by prominence instead of
    # using a frame-count threshold (which would assume a constant frame rate).
    accepted: list[Transient] = []
    for event in sorted(candidates, key=lambda event: event.prominence_percent, reverse=True):
        if any(abs(event.peak_ms - keep.peak_ms) < settings.min_separation_ms
               for keep in accepted):
            continue
        accepted.append(event)
    return tuple(sorted(accepted, key=lambda event: event.peak_ms))


def _observation_duration_ms(t: np.ndarray, y: np.ndarray,
                             gaps: np.ndarray) -> float:
    return float(sum(t[part[-1]] - t[part[0]] for part in
                     _segments(np.isfinite(y), gaps) if len(part) >= 2))


def _associated_trials(recording, signal: np.ndarray, events: list[Transient],
                       settings: TransientSettings) -> tuple[list[Transient], tuple[dict, ...], np.ndarray]:
    if settings.response_source == 'none':
        return events, (), np.array([], dtype=float)
    onset_times = find_anchors(recording, settings.response_source,
                              settings.stimulus_threshold)
    t = np.asarray(recording.frame_time_ms)
    gaps = np.asarray(recording.frame_gap_before, dtype=bool)
    nominal_dt = 1000.0 / recording.nominal_frame_rate_hz
    trials: list[dict[str, Any]] = []
    accepted_starts: dict[int, list[float]] = {1: [], 2: [], 3: []}
    for anchor in onset_times:
        end = anchor + settings.response_window_ms
        ids = np.flatnonzero((t >= anchor - 1e-8) & (t <= end + 1e-8))
        globally_complete = (
            len(ids) >= 2
            and t[ids[0]] - anchor <= nominal_dt * 1.5 + 1e-8
            and end - t[ids[-1]] <= nominal_dt * 1.5 + 1e-8
            and not np.any(gaps[ids[1:]])
            and not gaps[ids[0]]  # a discontinuity at the first frame invalidates boundary support
        )
        for neuron in (1, 2, 3):
            usable = bool(globally_complete and np.isfinite(signal[ids, neuron - 1]).all())
            if usable:
                accepted_starts[neuron].append(float(anchor))
            trials.append({
                'neuron': neuron, 'stimulus_onset_ms': float(anchor),
                'window_end_ms': float(end), 'usable': usable,
                'responded': False, 'event_count': 0,
                'first_latency_ms': None, 'first_amplitude_percent': None,
            })
    # Choose the latest usable preceding onset for an event; overlapping
    # response windows cannot count one transient as several responses.
    updated: list[Transient] = []
    for event in events:
        if event.onset_ms is None:
            updated.append(event)
            continue
        matching = [start for start in accepted_starts[event.neuron]
                    if start <= event.onset_ms <= start + settings.response_window_ms]
        if not matching:
            updated.append(event)
            continue
        start = max(matching)
        updated.append(replace(event, stimulus_onset_ms=start,
                               response_latency_ms=event.onset_ms - start))
    per_trial: dict[tuple[int, float], list[Transient]] = {}
    for event in updated:
        if event.stimulus_onset_ms is not None:
            per_trial.setdefault((event.neuron, event.stimulus_onset_ms), []).append(event)
    for trial in trials:
        hits = per_trial.get((trial['neuron'], trial['stimulus_onset_ms']), [])
        if hits:
            first = min(hits, key=lambda event: event.onset_ms)
            trial['responded'] = True
            trial['event_count'] = len(hits)
            trial['first_latency_ms'] = first.response_latency_ms
            trial['first_amplitude_percent'] = first.amplitude_percent
    return updated, tuple(trials), onset_times


def detect_transients(recording, settings: TransientSettings,
                      processed=None) -> TransientResult:
    """Detect and describe optical transients in each of three sampled traces."""
    signal = _validate(recording, processed, settings)
    t = np.asarray(recording.frame_time_ms, dtype=float)
    gaps = np.asarray(recording.frame_gap_before, dtype=bool)
    all_events: list[Transient] = []
    for neuron in range(3):
        all_events.extend(_channel_events(t, signal[:, neuron], gaps, settings, neuron))
    associated, trials, onsets = _associated_trials(recording, signal, all_events, settings)
    metrics: list[dict[str, Any]] = []
    warnings: list[str] = []
    for neuron in (1, 2, 3):
        found = [e for e in associated if e.neuron == neuron]
        duration = _observation_duration_ms(t, signal[:, neuron - 1], gaps)
        measured = [e for e in found if e.rise_10_90_ms is not None and e.decay_1e_ms is not None]
        quality = {
            'neuron': neuron,
            'events': len(found),
            'valid_observed_duration_s': duration / 1000.0,
            'transient_rate_hz': (len(found) * 1000.0 / duration if duration > 0 else None),
            'mean_amplitude_percent': (float(np.mean([e.amplitude_percent for e in found]))
                                       if found else None),
            'mean_fwhm_ms': (float(np.mean([e.fwhm_ms for e in found])) if found else None),
            'complete_kinetics_events': len(measured),
            'mean_rise_10_90_ms': (float(np.mean([e.rise_10_90_ms for e in measured]))
                                  if measured else None),
            'mean_decay_1e_ms': (float(np.mean([e.decay_1e_ms for e in measured]))
                                 if measured else None),
        }
        mine = [trial for trial in trials if trial['neuron'] == neuron and trial['usable']]
        quality.update({
            'usable_stimulus_windows': len(mine),
            'excluded_stimulus_windows': sum(not trial['usable'] for trial in trials
                                             if trial['neuron'] == neuron),
            'stimulus_associated_events': sum(e.stimulus_onset_ms is not None for e in found),
            'trial_response_fraction': (sum(trial['responded'] for trial in mine) / len(mine)
                                        if mine else None),
            'mean_response_latency_ms': (
                float(np.mean([trial['first_latency_ms'] for trial in mine if trial['responded']]))
                if any(trial['responded'] for trial in mine) else None
            ),
            'mean_first_response_amplitude_percent': (
                float(np.mean([trial['first_amplitude_percent'] for trial in mine if trial['responded']]))
                if any(trial['responded'] for trial in mine) else None
            ),
        })
        metrics.append(quality)
        if len(found) == 0:
            warnings.append(f'Neuron {neuron}: no transients passed the chosen detection criteria')
    if settings.response_source != 'none' and onsets.size == 0:
        warnings.append('No observed stimulus/trigger onset markers; association unavailable')
    return TransientResult(settings, settings.source, t.copy(), signal.copy(), gaps.copy(),
                           tuple(sorted(associated, key=lambda e: (e.neuron, e.peak_ms))),
                           tuple(metrics), np.asarray(onsets, dtype=float), trials,
                           tuple(warnings))
