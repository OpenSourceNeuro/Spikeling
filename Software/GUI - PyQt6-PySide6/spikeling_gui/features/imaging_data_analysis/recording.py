"""Validated one-pixel-per-neuron imaging time-series recordings.

Imaging acquisition writes three *associated* files:
    NAME.csv              : model samples and ground-truth/reference channels
    NAME_frames.csv       : frame-sampled fluorescence (student-facing data)
    NAME_meta.json        : acquisition model, timing and provenance

No deconvolution, baseline correction or analysis is performed by this loader.
It preserves raw data and makes acquisition problems explicit for later phases.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


SAMPLE_COLUMNS = (
    "Time (ms)", "Stim", "Trigger", "Vm1 (mV)", "Vm2 (mV)", "Vm3 (mV)",
    "Ca1 (uM)", "Ca2 (uM)", "Ca3 (uM)", "F1 (a.u.)", "F2 (a.u.)", "F3 (a.u.)",
    "FrameIdx", "FrameTime (ms)",
    "Calcium event 1", "Calcium event 2", "Calcium event 3",
)
FRAME_COLUMNS = (
    "FrameIdx", "FrameTime (ms)", "NearestSampleIdx",
    "F1 (a.u.)", "F2 (a.u.)", "F3 (a.u.)", "SourceSampleTime (ms)",
    "DF/F0 1 (%)", "DF/F0 2 (%)", "DF/F0 3 (%)",
)
FLUORESCENCE_COLUMNS = ("F1 (a.u.)", "F2 (a.u.)", "F3 (a.u.)")
DFF_COLUMNS = ("DF/F0 1 (%)", "DF/F0 2 (%)", "DF/F0 3 (%)")
CALCIUM_COLUMNS = ("Ca1 (uM)", "Ca2 (uM)", "Ca3 (uM)")
VOLTAGE_COLUMNS = ("Vm1 (mV)", "Vm2 (mV)", "Vm3 (mV)")
EVENT_COLUMNS = ("Calcium event 1", "Calcium event 2", "Calcium event 3")
SUPPORTED_SCHEMA = 2
N_NEURONS = 3  # Three independent, one-pixel optical readouts (not an image stack).


class ImagingRecordingError(ValueError):
    """The imaging acquisition is incomplete, inconsistent or malformed."""


@dataclass(frozen=True)
class ImagingRecording:
    """Raw validated acquisition, with explicitly distinct sample/frame clocks.

    Shape of channel matrices: (n_samples or n_frames, 3).
    The frame fluorescence is the observable used by student analysis.
    Vm, calcium and event flags are simulator reference/validation signals.
    """

    source: Path
    frames_source: Path
    metadata_source: Path
    samples: pd.DataFrame
    frames: pd.DataFrame
    metadata: dict[str, Any]
    sample_time_ms: np.ndarray
    frame_time_ms: np.ndarray
    source_sample_indices: np.ndarray
    stimulus: np.ndarray
    trigger: np.ndarray
    voltage_mv: np.ndarray
    calcium_um: np.ndarray
    reference_events: np.ndarray
    frame_fluorescence_au: np.ndarray
    recorded_dff_percent: np.ndarray
    sample_gap_before: np.ndarray
    frame_gap_before: np.ndarray
    warnings: tuple[str, ...]

    @property
    def n_samples(self) -> int:
        return len(self.sample_time_ms)

    @property
    def n_frames(self) -> int:
        return len(self.frame_time_ms)

    @property
    def source_kind(self) -> str:
        return str(self.metadata["source"])

    @property
    def nominal_frame_rate_hz(self) -> float:
        return float(self.metadata["imaging_params"]["frame_rate"])

    def summary(self) -> dict[str, Any]:
        """Safe, display-ready acquisition summary (not a processing result)."""
        return {
            "recording": self.source.name,
            "source": self.source_kind,
            "indicator": self.metadata.get("indicator_name", "Unknown"),
            "model": self.metadata.get("fluorescence_model", "Unknown"),
            "one_pixel_neurons": N_NEURONS,
            "samples": self.n_samples,
            "frames": self.n_frames,
            "nominal_frame_rate_hz": self.nominal_frame_rate_hz,
            "sample_gaps": int(self.sample_gap_before.sum()),
            "frame_gaps": int(self.frame_gap_before.sum()),
            "timing_interruptions": len(self.metadata.get("timing_interruptions", [])),
            "event_provenance": self.metadata.get("event_provenance", []),
            "warnings": list(self.warnings),
        }


def _paths(source: str | Path) -> tuple[Path, Path, Path]:
    path = Path(source).expanduser()
    if path.name.endswith("_frames.csv"):
        path = path.with_name(path.name[:-len("_frames.csv")] + ".csv")
    elif path.name.endswith("_meta.json"):
        path = path.with_name(path.name[:-len("_meta.json")] + ".csv")
    if path.suffix.lower() != ".csv":
        raise ImagingRecordingError("Select a recording CSV, *_frames.csv or *_meta.json file.")
    frames = path.with_name(path.stem + "_frames.csv")
    metadata = path.with_name(path.stem + "_meta.json")
    return path, frames, metadata


def _read_frame(path: Path, required: tuple[str, ...]) -> pd.DataFrame:
    try:
        frame = pd.read_csv(path)
    except (OSError, pd.errors.ParserError, UnicodeError) as exc:
        raise ImagingRecordingError(f"Cannot read {path.name}: {exc}") from exc
    missing = [name for name in required if name not in frame.columns]
    if missing:
        raise ImagingRecordingError(
            f"{path.name} is missing required columns: {', '.join(missing)}"
        )
    # Use numeric-only copies so no downstream processing receives strings.
    numeric = frame.copy()
    for name in required:
        try:
            numeric[name] = pd.to_numeric(frame[name], errors="raise")
        except (TypeError, ValueError) as exc:
            raise ImagingRecordingError(f"{path.name}: {name} must be numeric") from exc
        if np.isinf(numeric[name].to_numpy(dtype=float)).any():
            raise ImagingRecordingError(f"{path.name}: {name} contains infinity")
    return numeric


def _finite_increasing(values: np.ndarray, label: str, *, allow_empty: bool = False) -> None:
    if values.size == 0 and allow_empty:
        return
    if values.size == 0 or not np.isfinite(values).all():
        raise ImagingRecordingError(f"{label} must contain finite values")
    if values.size > 1 and not np.all(np.diff(values) > 0):
        raise ImagingRecordingError(f"{label} must be strictly increasing")


def _indices(values: pd.Series, label: str, lower: int, upper_exclusive: int) -> np.ndarray:
    items = values.to_numpy(dtype=float)
    if not np.isfinite(items).all() or not np.all(items == np.floor(items)):
        raise ImagingRecordingError(f"{label} must contain finite integer indices")
    if np.any(items < lower) or np.any(items >= upper_exclusive):
        raise ImagingRecordingError(f"{label} contains out-of-range indices")
    return items.astype(np.int64)


def _gaps(time: np.ndarray, expected_interval_ms: float) -> np.ndarray:
    gap = np.zeros(time.size, dtype=bool)
    if time.size > 1:
        gap[1:] = np.diff(time) > 1.5 * expected_interval_ms + 1e-8
    return gap


def _sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_imaging_recording(source: str | Path) -> ImagingRecording:
    """Load a three-file imaging acquisition without modifying the source files.

    Existing version-2 recordings without optional file hashes remain supported.
    Raises ImagingRecordingError for missing files, malformed data or contradictions.
    Nonfatal acquisition limitations are listed in ``warnings``.
    """
    sample_path, frame_path, meta_path = _paths(source)
    for path in (sample_path, frame_path, meta_path):
        if not path.is_file():
            raise ImagingRecordingError(f"Missing imaging acquisition file: {path.name}")
    try:
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ImagingRecordingError(f"Cannot read {meta_path.name}: {exc}") from exc
    if not isinstance(metadata, dict) or metadata.get("schema_version") != SUPPORTED_SCHEMA:
        raise ImagingRecordingError("Unsupported imaging metadata: expected schema_version 2")
    if metadata.get("source") not in ("spikeling", "emulator"):
        raise ImagingRecordingError("Imaging metadata has an unknown acquisition source")
    params = metadata.get("imaging_params")
    if not isinstance(params, dict):
        raise ImagingRecordingError("Imaging metadata has no imaging_params object")
    try:
        frame_rate = float(params["frame_rate"])
        fallback_step = float(metadata["sample_interval_ms_fallback"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ImagingRecordingError("Missing or invalid frame rate / sample interval") from exc
    if not (np.isfinite(frame_rate) and frame_rate > 0 and np.isfinite(fallback_step)
            and fallback_step > 0):
        raise ImagingRecordingError("Frame rate and sample interval must be positive and finite")

    samples = _read_frame(sample_path, SAMPLE_COLUMNS)
    frames = _read_frame(frame_path, FRAME_COLUMNS)
    n_samples = len(samples)
    n_frames = len(frames)
    if n_samples < 2:
        raise ImagingRecordingError("At least two model samples are required")
    if metadata.get("n_samples") != n_samples or metadata.get("n_frames") != n_frames:
        raise ImagingRecordingError("Metadata sample/frame counts do not match the CSV files")

    declarations = metadata.get("columns")
    if not isinstance(declarations, dict):
        raise ImagingRecordingError("Imaging metadata does not declare its CSV columns")
    for key, actual in (("samples_csv", SAMPLE_COLUMNS), ("frames_csv", FRAME_COLUMNS)):
        if declarations.get(key) != list(actual):
            raise ImagingRecordingError(f"Metadata {key} declaration does not match schema")

    sample_t = samples["Time (ms)"].to_numpy(dtype=float)
    frame_t = frames["FrameTime (ms)"].to_numpy(dtype=float)
    _finite_increasing(sample_t, "Model sample time")
    _finite_increasing(frame_t, "Camera frame time", allow_empty=True)

    frame_idx = _indices(frames["FrameIdx"], "FrameIdx in frames", 0, n_frames)
    if not np.array_equal(frame_idx, np.arange(n_frames)):
        raise ImagingRecordingError("Frame indices must be sequential and start at zero")
    sample_frame_idx = _indices(
        samples["FrameIdx"], "FrameIdx in samples", -1, max(1, n_frames)
    )
    if n_frames == 0 and np.any(sample_frame_idx != -1):
        raise ImagingRecordingError("Samples reference camera frames, but frames CSV is empty")
    reference_idx = _indices(
        frames["NearestSampleIdx"], "NearestSampleIdx", 0, n_samples
    )
    if reference_idx.size and not np.all(np.diff(reference_idx) > 0):
        raise ImagingRecordingError("Frame-to-sample indices must be strictly increasing")
    if reference_idx.size:
        source_t = frames["SourceSampleTime (ms)"].to_numpy(dtype=float)
        if not np.allclose(source_t, sample_t[reference_idx], atol=1e-6, rtol=0):
            raise ImagingRecordingError("Frame source sample timestamps do not match model samples")
    held_frame_t = samples["FrameTime (ms)"].to_numpy(dtype=float)
    associated = sample_frame_idx >= 0
    if associated.any():
        if not np.isfinite(held_frame_t[associated]).all():
            raise ImagingRecordingError("Valid sample FrameIdx has no finite frame timestamp")
        if not np.allclose(
            held_frame_t[associated], frame_t[sample_frame_idx[associated]], atol=1e-6, rtol=0
        ):
            raise ImagingRecordingError("Sample frame timestamps disagree with frames CSV")
    # The first sample that acquires each camera frame is recorded in frames.csv.
    if n_frames and not np.array_equal(sample_frame_idx[reference_idx], frame_idx):
        raise ImagingRecordingError("Frame-to-sample cross-reference does not agree")

    event_values = samples[list(EVENT_COLUMNS)].to_numpy(dtype=float)
    if not np.isfinite(event_values).all() or not np.isin(event_values, [0, 1]).all():
        raise ImagingRecordingError("Calcium event columns must contain 0/1 flags")

    warnings: list[str] = []
    hashes = metadata.get("file_sha256")
    if hashes is None:
        warnings.append("Legacy imaging recording: file hashes unavailable")
    elif not isinstance(hashes, dict):
        raise ImagingRecordingError("Invalid file_sha256 metadata")
    else:
        for key, path in (("samples_csv", sample_path), ("frames_csv", frame_path)):
            expected = hashes.get(key)
            if not isinstance(expected, str) or len(expected) != 64:
                raise ImagingRecordingError(f"Missing or invalid hash for {key}")
            if _sha256(path) != expected.lower():
                raise ImagingRecordingError(f"Checksum mismatch: {path.name} has changed")

    if not n_frames:
        warnings.append("Recording contains no camera frames")
    if metadata.get("timing_interruptions"):
        warnings.append("Acquisition reports timing interruptions")
    if len(set(metadata.get("event_provenance", []))) > 1:
        warnings.append("Mixed neural-event provenance; validate interpretation")

    sample_gaps = _gaps(sample_t, fallback_step)
    frame_gaps = _gaps(frame_t, 1000.0 / frame_rate)
    if sample_gaps.any():
        warnings.append(f"{sample_gaps.sum()} discontinuity/discontinuities in model samples")
    if frame_gaps.any():
        warnings.append(f"{frame_gaps.sum()} discontinuity/discontinuities in camera frames")

    return ImagingRecording(
        source=sample_path, frames_source=frame_path, metadata_source=meta_path,
        samples=samples, frames=frames, metadata=metadata,
        sample_time_ms=sample_t,
        frame_time_ms=frame_t,
        source_sample_indices=reference_idx,
        stimulus=samples["Stim"].to_numpy(dtype=float),
        trigger=samples["Trigger"].to_numpy(dtype=float),
        voltage_mv=samples[list(VOLTAGE_COLUMNS)].to_numpy(dtype=float),
        calcium_um=samples[list(CALCIUM_COLUMNS)].to_numpy(dtype=float),
        reference_events=event_values.astype(np.uint8),
        frame_fluorescence_au=frames[list(FLUORESCENCE_COLUMNS)].to_numpy(dtype=float),
        recorded_dff_percent=frames[list(DFF_COLUMNS)].to_numpy(dtype=float),
        sample_gap_before=sample_gaps,
        frame_gap_before=frame_gaps,
        warnings=tuple(warnings),
    )
