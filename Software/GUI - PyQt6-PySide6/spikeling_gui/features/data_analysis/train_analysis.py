"""Response amplitude and response detection across a presynaptic train."""

from dataclasses import dataclass

import numpy as np

from .comparison import PROXY, Trial, pulse_events
from .sweep_analysis import sample_bounds, window_available


@dataclass
class PulseResponse:
    number: int
    onset: float
    baseline_start: float
    response_end: float
    amplitude: float | None
    success: bool | None
    recovery: bool

    def metrics(self):
        return {
            "Response amplitude": self.amplitude,
            "Response probability (%)": 100 * self.success if self.success is not None else None,
            "Successful response amplitude": self.amplitude if self.success else None,
        }


def measure_pulse(recording, signal, number, onset, baseline_start, response_end, threshold, recovery):
    lo, on = sample_bounds(recording, baseline_start, onset)
    _, hi = sample_bounds(recording, onset, response_end)
    amplitude, success = None, None
    if window_available(recording, lo, on, signal) and window_available(recording, on, hi, signal):
        delta = signal[on:hi] - np.mean(signal[lo:on])
        amplitude = float(delta[np.argmax(np.abs(delta))])
        success = abs(amplitude) >= threshold
    return PulseResponse(number, onset, baseline_start, response_end, amplitude, success, recovery)


def train_trials(condition, settings, stimulus, signal, unit):
    rec = condition.recording
    events = pulse_events(rec, settings, stimulus)
    if not events:
        return [], 0
    times = np.asarray([event.onset_ms for event in events])
    groups = np.split(np.arange(len(events)), np.flatnonzero(np.diff(times) > settings.pair_interval + 1e-9) + 1)
    trials, excluded = [], 0
    used = set()
    for group_index, group in enumerate(groups):
        if group_index in used:
            continue
        if len(group) < 3:
            excluded += 1
            continue
        pulse_indices = list(group)
        if settings.probe_limit is not None and group_index + 1 < len(groups):
            candidate = groups[group_index + 1]
            gap = times[candidate[0]] - times[group[-1]]
            if len(candidate) == 1 and gap <= settings.probe_limit + 1e-9:
                pulse_indices.append(candidate[0])
                used.add(group_index + 1)
        pulses = [events[i] for i in pulse_indices]
        probe = len(pulse_indices) > len(group)
        start = pulses[0].onset_ms - settings.pre
        end = pulses[-1].onset_ms + settings.window
        if (any(p.issue for p in pulses) or not condition.start <= start < end <= condition.end
                or (pulse_indices[0] > 0 and start < times[pulse_indices[0] - 1] + settings.window)
                or (pulse_indices[-1] + 1 < len(times) and end > times[pulse_indices[-1] + 1])):
            excluded += 1
            continue
        # A gap in the input can hide events and change the apparent pulse count.
        left, right = sample_bounds(rec, start, end)
        if not window_available(rec, left, right, stimulus):
            excluded += 1
            continue
        responses = []
        previous_end = start
        for i, pulse in enumerate(pulses):
            onset = pulse.onset_ms
            baseline = max(onset - settings.pre, previous_end)
            next_onset = pulses[i + 1].onset_ms if i + 1 < len(pulses) else end
            response_end = min(onset + settings.window, next_onset)
            # An overlapping response window or unavailable baseline cannot be
            # scored reliably, so keep the pulse with undefined measurements.
            if response_end < onset + settings.window - 1e-9:
                responses.append(PulseResponse(i + 1, onset, baseline, response_end, None, None, False))
            else:
                responses.append(measure_pulse(
                    rec, signal, i + 1, onset, baseline, response_end, settings.response_floor,
                    probe and i == len(pulses) - 1,
                ))
            previous_end = response_end
        gaps = tuple(float(b.onset_ms - a.onset_ms) for a, b in zip(pulses, pulses[1:]))
        key = (len(group), int(probe), *gaps)
        if settings.source == PROXY:
            key += tuple(p.amplitude for p in pulses)
            key += tuple(p.offset_ms - p.onset_ms for p in pulses)
        label = f"{len(group)} pulses · " + "/".join(f"{gap:g}" for gap in gaps[:len(group) - 1]) + " ms"
        if probe:
            label += f" · probe after {gaps[-1]:g} ms"
        trials.append(Trial(
            condition, pulses[0].onset_ms, end, start, end, key, label, {}, signal, stimulus, unit,
            pulses=tuple(responses),
        ))
    return trials, excluded


def train_tolerance(key, settings):
    count, probe = key[:2]
    pulses = int(count + probe)
    times = [settings.time_tolerance] * (pulses - 1)
    if settings.source == PROXY:
        times.extend([settings.amplitude_tolerance] * pulses)
        times.extend([settings.time_tolerance] * pulses)
    return np.asarray([0, 0, *times])
