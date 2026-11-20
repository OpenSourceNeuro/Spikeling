"""Deterministic offline referencing and causal filtering of saved broadband."""
from dataclasses import dataclass
from math import ceil, isfinite, log

import numpy as np
from scipy.signal import butter, sos2zpk, sosfilt

from .acquisition import CONTACTS
from .session_reader import SessionReader

ALGORITHM = "spikeling-extracellular-offline-v1"
MAX_ANALYSIS_ROWS = 40_000
WARMUP_MS = 10.0
POLE_DECAY = 0.01


def contacts_valid(contacts, minimum):
    return (isinstance(contacts, tuple) and len(contacts) >= minimum
            and contacts == tuple(contact for contact in CONTACTS if contact in contacts))


@dataclass(frozen=True)
class Processing:
    reference: str = "none"
    reference_contacts: tuple = CONTACTS
    bandpass: tuple | None = (300.0, 3000.0)

    def design(self, rate):
        if self.reference not in ("none", "car"):
            raise ValueError("Choose None or common average reference.")
        if self.reference == "car" and not contacts_valid(self.reference_contacts, 2):
            raise ValueError("Choose at least two distinct reference contacts in E1–E4 order.")
        if self.bandpass is None:
            return None
        low, high = self.bandpass
        if not (isfinite(low) and isfinite(high) and 0 < low < high < rate / 2):
            raise ValueError(f"Bandpass limits must satisfy 0 < low < high < {rate / 2:g} Hz.")
        sos = butter(3, self.bandpass, btype="bandpass", fs=rate, output="sos")
        if not np.isfinite(sos).all() or _pole_radius(sos) >= 1:
            raise ValueError("The selected bandpass cannot be represented as a stable causal filter.")
        return sos


def _pole_radius(sos):
    _, poles, _ = sos2zpk(sos)
    return float(np.max(np.abs(poles)))


def warmup_rows(sos, rate):
    """Use the Scope minimum and extend it for slowly settling filters."""
    if sos is None:
        return 0
    radius = _pole_radius(sos)
    settle = ceil(log(POLE_DECAY) / log(radius)) if radius > 0 else 0
    return max(ceil(WARMUP_MS * rate / 1000), settle)


@dataclass(frozen=True)
class ProcessedRun:
    first: int
    segment: int
    epoch: int
    tick: int
    clock: str
    time_ms: np.ndarray
    values_uV: np.ndarray
    native_available: np.ndarray
    warmup: int

    @property
    def end(self):
        return self.first + len(self.time_ms)


def apply_reference(values, config):
    """Return an independent array in µV, retaining the E1–E4 order."""
    values = np.asarray(values, dtype=np.float64)
    if values.ndim != 2 or values.shape[1] != len(CONTACTS) or not np.isfinite(values).all():
        raise ValueError("Expected finite samples in E1–E4 order.")
    if config.reference == "none":
        return values.copy()
    if config.reference != "car" or not contacts_valid(config.reference_contacts, 2):
        raise ValueError("CAR requires at least two distinct reference contacts in E1–E4 order.")
    indices = [CONTACTS.index(contact) for contact in config.reference_contacts]
    return values - values[:, indices].mean(axis=1, keepdims=True)


def process_interval(reader, start, stop, config, cancel=None, digest=None):
    """Yield runs split at scientific boundaries, continuing across file chunks."""
    if not isinstance(reader, SessionReader):
        raise ValueError("Offline processing requires a validated broadband session.")
    if not reader.first_index <= start < stop <= reader.end_index or stop - start > MAX_ANALYSIS_ROWS:
        raise ValueError(f"Select 1–{MAX_ANALYSIS_ROWS:,} accepted rows inside the session.")
    rate = reader.manifest["nominal_model_rate_hz"]
    sos = config.design(rate)
    warmup = warmup_rows(sos, rate)
    parts, times, availability = [], [], []
    first_span = previous = None

    def complete():
        values = np.concatenate(parts)
        time = np.concatenate(times)
        native = np.concatenate(availability)
        for array in (values, time, native):
            array.setflags(write=False)
        return ProcessedRun(first_span["first_index"], first_span["segment"], first_span["epoch"],
                            first_span["first_tick"], first_span["clock"], time, values, native,
                            min(warmup, len(time)))

    for first, _, time, values, spans in reader.iter_interval("broadband", start, stop, with_spans=True):
        if digest is not None:
            digest.update(values.astype("<f8", copy=False).tobytes(order="C"))
        for span in spans:
            if cancel is not None and cancel.is_set():
                return
            if previous is None or not _continuous(previous, span):
                if previous is not None:
                    yield complete()
                parts, times, availability = [], [], []
                first_span = span
                zi = None if sos is None else np.zeros((len(sos), 2, len(CONTACTS)))
            offset = span["first_index"] - first
            section = slice(offset, offset + span["count"])
            signal = apply_reference(values[section], config)
            if sos is not None:
                signal, zi = sosfilt(sos, signal, axis=0, zi=zi)
            parts.append(signal)
            times.append(time[section])
            availability.append(np.broadcast_to(span["native_available"], (len(signal), 3)))
            previous = span
    if previous is not None:
        yield complete()


def _continuous(previous, following):
    return (previous["first_index"] + previous["count"] == following["first_index"]
            and previous["first_tick"] + previous["count"] == following["first_tick"]
            and all(previous[key] == following[key] for key in ("segment", "epoch", "clock")))
