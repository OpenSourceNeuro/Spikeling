"""Version 1 of the portable synthetic extracellular session format."""
import ctypes
import errno
import hashlib
import json
import math
import os
import sys
from dataclasses import asdict, is_dataclass
from pathlib import Path
from uuid import UUID

import numpy as np

from .acquisition import BROADBAND, CONTACTS, NEURONS, PROCESSED

FORMAT = "spikeling.extracellular"
VERSION = {"major": 1, "minor": 0}
SUFFIX = ".spikeling"
MANIFEST = "manifest.json"
MAX_ROWS = 8192
MAX_JSON = 16 * 1024 * 1024
STREAMS = {
    "broadband": {"stage": BROADBAND.stage, "channels": CONTACTS, "units": ("µV",) * 4},
    "processed": {"stage": PROCESSED.stage, "channels": CONTACTS, "units": ("µV",) * 4},
    "observations": {"stage": "neuronal_observations",
                     "channels": (*NEURONS, "stimulus", "trigger"),
                     "units": ("mV", "mV", "mV", "%", "flag")},
    "model_time": {"stage": "model_time", "channels": ("time",), "units": ("ms",)},
}
STREAMS = {key: {**value, "channels": list(value["channels"]), "units": list(value["units"]),
                 "dtype": "<f8", "layout": "samples_by_channels"}
           for key, value in STREAMS.items()}

EVENT_DATASETS = {
    "encoding": "utf-8-jsonl", "version": 1, "public": "events",
    "optional_native_truth": "truth",
}


EVENT_STREAMS = {
    "native_model_spike": "observations", "waveform_launch": "observations",
    "trigger_rise": "observations", "trigger_fall": "observations",
    "contact_crossing": "processed", "grouped_detection": "processed",
}


class SessionError(ValueError):
    """A session could not be safely interpreted."""


def require(condition, message):
    if not condition:
        raise SessionError(message)


def integer(value, name, minimum=0, maximum=2**63 - 1):
    require(type(value) is int and minimum <= value <= maximum, f"Invalid {name}")
    return value


def json_value(value):
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, np.generic):
        return value.item()
    if is_dataclass(value):
        return asdict(value)
    raise TypeError(f"Unsupported metadata value {type(value).__name__}")


def canonical(value):
    return json.dumps(value, default=json_value, allow_nan=False, ensure_ascii=False,
                      sort_keys=True, separators=(",", ":")).encode("utf-8")


def finite_float(token):
    result = float(token)
    require(math.isfinite(result), "Non-finite JSON metadata")
    return result


def unique_keys(pairs):
    result = dict(pairs)
    require(len(result) == len(pairs), "Duplicate JSON key")
    return result


def decode(data):
    return json.loads(data, parse_float=finite_float, parse_constant=finite_float,
                      object_pairs_hook=unique_keys)


def sync_directory(path):
    if os.name == "posix":
        fd = os.open(path, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


def publish_directory(source, target):
    """Atomically publish on the same filesystem without replacing a target."""
    if os.name == "nt":
        # Windows rename fails if the destination already exists.
        source.rename(target)
        return
    libc = ctypes.CDLL(None, use_errno=True)
    source_bytes, target_bytes = os.fsencode(source), os.fsencode(target)
    if sys.platform.startswith("linux") and hasattr(libc, "renameat2"):
        at_fdcwd, rename_noreplace = -100, 1
        result = libc.renameat2(at_fdcwd, source_bytes, at_fdcwd, target_bytes, rename_noreplace)
    elif sys.platform == "darwin" and hasattr(libc, "renamex_np"):
        rename_excl = 0x00000004
        result = libc.renamex_np(source_bytes, target_bytes, rename_excl)
    else:
        raise OSError(errno.ENOTSUP, "Atomic no-overwrite publication is unavailable", str(target))
    if result != 0:
        code = ctypes.get_errno()
        raise OSError(code, os.strerror(code), str(target))


def atomic_file(path, write):
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("xb") as file:
        write(file)
        file.flush()
        os.fsync(file.fileno())
    os.replace(temporary, path)
    sync_directory(path.parent)


def write_json(path, value):
    data = canonical(value)
    require(len(data) <= MAX_JSON, "Metadata exceeds the session format limit")
    atomic_file(path, lambda file: file.write(data))


def local_file(root, name):
    # Callers construct basenames from validated indices and fixed stream IDs.
    require(Path(name).name == name and "/" not in name and "\\" not in name,
            "Unsafe session file location")
    path = root / name
    require(path.is_file() and not path.is_symlink() and path.resolve().parent == root,
            f"Missing or unsafe session file {name}")
    return path


def load_json(path):
    with path.open("rb") as file:
        data = file.read(MAX_JSON + 1)
    require(len(data) <= MAX_JSON, f"Oversized metadata {path.name}")
    return decode(data)


def digest(path, size_limit):
    require(path.stat().st_size <= size_limit, f"Oversized session file {path.name}")
    with path.open("rb") as file:
        result = hashlib.sha256()
        for block in iter(lambda: file.read(65536), b""):
            result.update(block)
    return result.hexdigest()


def record_name(index):
    return f"{index:012d}.json"


def data_name(index, stage):
    extension = "jsonl" if stage in ("events", "truth") else "npy"
    return f"{index:012d}-{stage}.{extension}"
