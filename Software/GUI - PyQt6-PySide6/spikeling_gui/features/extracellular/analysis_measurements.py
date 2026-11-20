"""Comparable measurements over settled rows of a saved recording."""
import numpy as np
from scipy.signal import periodogram


def settled_blocks(reference, current):
    """Yield aligned A and B blocks without bridging gaps or filter resets."""
    a_runs = reference.runs if reference is not None else (None,) * len(current.runs)
    for left, right in zip(a_runs, current.runs):
        skip = max(left.warmup if left is not None else 0, right.warmup)
        if skip < len(right.values_uV):
            yield (right.first + skip, right.end,
                   None if left is None else left.values_uV[skip:], right.values_uV[skip:])


def measure(reference, current, baseline=None):
    """Return per-contact RMS and peak-to-peak of each recipe's mean waveform."""
    row = None
    if baseline is not None:
        start, stop = baseline
        row = next(((a, b, start - first, stop - first)
                    for first, end, a, b in settled_blocks(reference, current)
                    if first <= start < stop <= end), None)
    result = {"baseline_interval": baseline, "baseline_available": row is not None}
    for index, (name, analysis) in enumerate((("a", reference), ("b", current))):
        if analysis is None:
            continue
        waveform = analysis.waveforms
        values = None if row is None else row[index][row[2]:row[3]]
        result[name] = {
            "baseline_rms_uV": None if values is None else np.sqrt(np.mean(values ** 2, axis=0)).tolist(),
            "mean_waveform_peak_to_peak_uV": (None if waveform.mean_uV is None
                                             else np.ptp(waveform.mean_uV, axis=0).tolist()),
            "waveform_count": len(waveform.event_ids),
        }
    return result


def spectrum(reference, current, contact):
    """Return a Hann periodogram from the longest common settled block."""
    block = max(settled_blocks(reference, current), key=lambda item: item[1] - item[0], default=None)
    if block is None or block[1] - block[0] < current.rate / 2:
        return None
    start, stop, left, right = block
    frequency, power = periodogram(right[:, contact], fs=current.rate, window="hann")
    baseline = None if left is None else periodogram(left[:, contact], fs=current.rate, window="hann")[1]
    return start, stop, frequency, baseline, power
