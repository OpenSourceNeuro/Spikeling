"""Build periodic and chirp stimuli on the custom playback grid."""

import math

import numpy as np
from scipy import signal

from .cycle import STEP_MS, check_cycle_size, read_duration, read_integer, read_pre_stimulus


def read_frequency(editor, label, *, allow_zero=False):
    try:
        value = float(editor.text())
    except ValueError:
        value = math.nan
    if not math.isfinite(value) or not 0 <= value < 500 / STEP_MS or (value == 0 and not allow_zero):
        qualifier = "zero or greater" if allow_zero else "positive"
        raise ValueError(f"{label.capitalize()} must be {qualifier} and below {500 / STEP_MS:g} Hz.")
    return value


def read_level(editor, label):
    return read_integer(editor, 1, f"{label} in whole percent", 100)


def quantise(waveform):
    if np.any(np.abs(waveform) > 100 + 1e-9):
        raise ValueError("Stimulus levels must stay between −100% and 100%. Check amplitude and mean level.")
    return np.rint(waveform).astype(np.int16)


def read_periodic(ui, triangle):
    prefix = "TriangleWave" if triangle else "SineWave"
    pre, pre_level = read_pre_stimulus(ui)
    active = read_duration(getattr(ui, f"{prefix}_StimOn_Value"), "stimulus duration")
    off = read_duration(getattr(ui, f"{prefix}_StimOff_Value"), "off duration")
    off_level = read_level(getattr(ui, f"{prefix}_IntOff_Value"), "off level")
    frequency = read_frequency(getattr(ui, f"{prefix}_Frequency_Value"), "frequency")
    amplitude = read_level(getattr(ui, f"{prefix}_Amplitude_Value"), "amplitude")
    mean = read_level(getattr(ui, f"{prefix}_Mean_Value"), "mean level")
    if active == 0 or amplitude < 0:
        raise ValueError("Stimulus duration must be positive and amplitude must be zero or greater.")
    if abs(mean) + amplitude > 100:
        raise ValueError("Mean level plus waveform amplitude must fit within −100% and 100%.")
    check_cycle_size(pre + active + off)

    phase = 2 * np.pi * frequency * np.arange(active) * STEP_MS / 1000
    carrier = signal.sawtooth(phase - 3 * np.pi / 2, width=0.5) if triangle else np.sin(phase)
    return np.concatenate((np.full(pre, pre_level, dtype=np.int16), quantise(mean + amplitude * carrier),
                           np.full(off, off_level, dtype=np.int16)))


def read_chirp(ui):
    pre, pre_level = read_pre_stimulus(ui)
    on = read_duration(ui.Chirp_PreChirpOn_Duration_Value, "conditioning on duration")
    off = read_duration(ui.Chirp_PreChirpOff_Duration_Value, "conditioning off duration")
    mid = read_duration(ui.Chirp_PreChirpMid_Duration, "conditioning midpoint duration")
    active = read_duration(ui.Chirp_Duration_Value, "chirp duration")
    on_level = read_level(ui.Chirp_PreChirpOn_Amplitude_Value, "conditioning on level")
    off_level = read_level(ui.Chirp_PreChirpOff_Amplitude_Value, "conditioning off level")
    mean = read_level(ui.Chirp_PreChirpMid_Amplitude, "midpoint level")
    peak_to_peak = read_integer(ui.Chirp_Amplitude_Value, 1, "chirp amplitude in whole percent", 200)
    if active == 0 or peak_to_peak < 0:
        raise ValueError("Chirp duration must be positive and amplitude must be zero or greater.")
    if abs(mean) + peak_to_peak / 2 > 100:
        raise ValueError("Midpoint level plus half the chirp amplitude must fit within −100% and 100%.")
    check_cycle_size(pre + on + off + mid + active)

    duration_s = active * STEP_MS / 1000
    time = np.arange(active) * STEP_MS / 1000
    mode = ui.Chirp_comboBox.currentIndex()
    if mode == 2:
        frequency = read_frequency(ui.Chirp_Frequency_Value, "frequency")
        wave = time / duration_s * np.sin(2 * np.pi * frequency * time)
    else:
        linear = mode == 0
        start = read_frequency(ui.Chirp_StartFrequency_Value, "start frequency", allow_zero=linear)
        end = read_frequency(ui.Chirp_EndFrequency_Value, "end frequency", allow_zero=linear)
        if start == end == 0:
            raise ValueError("At least one sweep frequency must be greater than zero.")
        method = "linear" if linear else "logarithmic"
        wave = signal.chirp(time, start, duration_s, end, method=method, phi=-90)
    prefix = [np.full(count, level, dtype=np.int16) for count, level in
              ((pre, pre_level), (on, on_level), (off, off_level), (mid, mean))]
    return np.concatenate((*prefix, quantise(mean + peak_to_peak / 2 * wave)))
