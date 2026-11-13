"""Versioned, checksum-bound metadata for board and emulator recordings."""

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

import pandas as pd


SCHEMA_VERSION = 1


def metadata_path(path):
    return Path(path).with_suffix(".metadata.json")


def stream_digest(handle):
    digest = hashlib.sha256()
    for block in iter(lambda: handle.read(65536), b""):
        digest.update(block)
    return digest.hexdigest()


def stp_parameters(parameters):
    utilisation, facilitation, recovery = parameters
    return {"utilisation": float(utilisation), "facilitation_ms": int(facilitation),
            "recovery_ms": int(recovery)}


def drug_setting(label, binding, scale):
    name, units = label.rsplit(" (", 1)
    return {"name": name, "units": units.removesuffix(")"), "enabled": bool(binding.active),
            "concentration": float(binding.value) / scale if binding.active else 0.0}


class RecordingMetadata:
    def __init__(self, source, clamp_mode, step_ms, timebase, settings_provenance):
        self.source = source
        self.clamp_mode = clamp_mode
        self.step_ms = step_ms
        self.timebase = timebase
        self.settings_provenance = settings_provenance
        self.started_at = datetime.now(timezone.utc).isoformat()
        self.changes = []

    def observe(self, index, settings):
        if self.changes and self.changes[-1]["settings"] == settings:
            return
        entry = {"sample_index": index, "time_ms": index * self.step_ms, "settings": settings}
        if self.changes and self.changes[-1]["sample_index"] == index:
            self.changes[-1] = entry
        else:
            self.changes.append(entry)

    def document(self, checksum, sample_count, channels):
        return {
            "schema_version": SCHEMA_VERSION, "csv_sha256": checksum, "sample_count": sample_count,
            "source": self.source, "recording_started_utc": self.started_at, "clamp_mode": self.clamp_mode,
            "timebase": {"kind": self.timebase, "sample_interval_ms": self.step_ms},
            "settings_provenance": self.settings_provenance,
            "channels": channels,
            "settings_at_sample": [entry for entry in self.changes if entry["sample_index"] < sample_count],
        }


def write_recording(path, frame, metadata, channels=None):
    """Stage both files before replacement. A stale sidecar fails the digest check."""
    path = Path(path)
    channels = channels or {}
    temporary = []
    try:
        with NamedTemporaryFile(mode="w", encoding="utf-8", newline="", dir=path.parent,
                                prefix=f".{path.stem}_", suffix=".tmp", delete=False) as handle:
            csv_temp = Path(handle.name)
            temporary.append(csv_temp)
            pd.DataFrame(frame).to_csv(handle, index=False)
            handle.flush()
            os.fsync(handle.fileno())
        with csv_temp.open("rb") as handle:
            checksum = stream_digest(handle)
        document = metadata.document(checksum, len(frame["Time (ms)"]), channels)
        with NamedTemporaryFile(mode="w", encoding="utf-8", newline="", dir=path.parent,
                                prefix=f".{path.stem}_", suffix=".tmp", delete=False) as handle:
            json_temp = Path(handle.name)
            temporary.append(json_temp)
            json.dump(document, handle, ensure_ascii=False, indent=2, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        sidecar = metadata_path(path)
        backup = None
        if sidecar.is_file():
            with NamedTemporaryFile(dir=path.parent, prefix=f".{path.stem}_", suffix=".tmp",
                                    delete=False) as handle:
                backup = Path(handle.name)
                temporary.append(backup)
            os.replace(sidecar, backup)
        try:
            os.replace(csv_temp, path)
        except OSError:
            if backup is not None:
                # Restore the earlier pair when the CSV commit itself failed.
                temporary.remove(backup)
                os.replace(backup, sidecar)
            raise
        # A failed sidecar commit leaves the new CSV usable as a legacy file.
        # The earlier sidecar cannot be associated with it, even for identical CSV bytes.
        os.replace(json_temp, sidecar)
    finally:
        for name in temporary:
            try:
                name.unlink(missing_ok=True)
            except OSError:
                pass


def read_metadata(path, checksum, sample_count, clamp_mode):
    try:
        with metadata_path(path).open(encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError:
        return None, ""
    except (OSError, ValueError):
        return None, "Recording metadata could not be read."
    if not isinstance(data, dict) or data.get("schema_version") != SCHEMA_VERSION:
        return None, "Recording metadata uses an unsupported schema."
    if (data.get("csv_sha256") != checksum or data.get("sample_count") != sample_count
            or data.get("clamp_mode") != clamp_mode):
        return None, "Recording metadata does not match this CSV."
    if (data.get("source") not in ("board", "emulator")
            or not isinstance(data.get("timebase"), dict)
            or not isinstance(data["timebase"].get("kind"), str)
            or not isinstance(data.get("settings_at_sample"), list)):
        return None, "Recording metadata is incomplete."
    return data, ""
