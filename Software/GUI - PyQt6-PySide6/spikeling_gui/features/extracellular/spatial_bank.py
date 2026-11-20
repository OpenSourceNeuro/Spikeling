"""Read-only extracellular voltage fields, independent of Qt and acquisition."""
from collections import OrderedDict
from hashlib import sha256
from itertools import product
from pathlib import Path
import re

import numpy as np

from .acquisition import CONTACTS
from .recording_schema import decode, digest

FORMAT = "spikeling.spatial_eap"
FILES = ("x_um.npy", "y_um.npy", "z_um.npy", "time_ms.npy", "voltage_uV.npy", "valid.npy")
MAX_BYTES = 256 * 1024**2
CORNERS = tuple(product((0, 1), repeat=3))


class BankError(ValueError):
    """The field or requested pose cannot be used."""


def require(condition, reason):
    if not condition:
        raise BankError(reason)


def world_to_cell(contacts_um, soma_um, rotation):
    """Return E1–E4 contact rows in the right-handed cell frame."""
    contacts, soma, matrix = (np.asarray(value, dtype=np.float64)
                              for value in (contacts_um, soma_um, rotation))
    require(contacts.shape == (4, 3) and soma.shape == (3,) and matrix.shape == (3, 3)
            and all(np.isfinite(value).all() for value in (contacts, soma, matrix)),
            "Expected finite E1–E4 positions, soma and 3-D rotation")
    require(np.allclose(matrix.T @ matrix, np.eye(3), atol=1e-10, rtol=0)
            and abs(np.linalg.det(matrix) - 1) <= 1e-10, "Expected a proper rotation")
    return (contacts - soma) @ matrix


class SpatialBank:
    """One immutable field. Lookup q is in µm; output is float64 in µV."""

    def __init__(self, directory, *, allow_provisional=False):
        self.directory = Path(directory)
        self._cache = OrderedDict()
        try:
            self._load(allow_provisional)
        except (OSError, ValueError, TypeError, KeyError, OverflowError) as exc:
            raise BankError(f"{self.directory.name}: {exc}") from exc

    def _load(self, allow_provisional):
        manifest = self.directory / "manifest.json"
        with manifest.open("rb") as stream:
            raw = stream.read(1024**2 + 1)
        require(len(raw) <= 1024**2, "Manifest too large")
        meta = decode(raw)
        require(meta["format"] == FORMAT and type(meta["version"]) is int and meta["version"] == 1,
                "Unsupported bank format or version")
        require(isinstance(meta["id"], str) and meta["id"] == self.directory.name,
                "Bank identifier does not match its directory")
        require(meta["status"] == "approved" or (allow_provisional and meta["status"] == "provisional"),
                "Bank is not approved")
        require(meta["units"] == {"space": "µm", "time": "ms", "voltage": "µV"}
                and meta["reference"] == "infinity" and meta["rate_hz"] == 10000,
                "Unexpected reference, units or sample rate")
        require(type(meta["conductivity_S_m"]) in (int, float) and meta["conductivity_S_m"] > 0,
                "Invalid conductivity")
        for key in ("model", "frame", "generator", "resampling", "licensing", "calibration", "support"):
            require(isinstance(meta[key], dict) and bool(meta[key]), f"Missing {key} provenance")
        require(set(meta["files"]) == set(FILES), "Unexpected file inventory")
        arrays = []
        for index, name in enumerate(FILES):
            path = self.directory / name
            entry = meta["files"][name]
            size = path.stat().st_size
            require(not path.is_symlink() and 0 < size <= MAX_BYTES and size == entry["bytes"],
                    f"Wrong size or path for {name}")
            require(re.fullmatch("[0-9a-f]{64}", entry["sha256"])
                    and digest(path, MAX_BYTES) == entry["sha256"], f"Checksum mismatch for {name}")
            data = np.load(path, mmap_mode="r", allow_pickle=False)
            dtype = ("<f8", "<f8", "<f8", "<f8", "<f4", "|b1")[index]
            require(data.dtype.str == dtype and data.ndim == (1 if index < 4 else 4 if index == 4 else 3)
                    and data.offset + data.nbytes == size and data.flags.c_contiguous,
                    f"Unexpected dtype, dimensions or layout for {name}")
            for rows in np.array_split(data, max(1, (data.nbytes + 2**20 - 1) // 2**20)):
                require(np.isfinite(rows).all(), f"Nonfinite values in {name}")
            arrays.append(data)
        self.axes = tuple(arrays[:3])
        self.time_ms, self._voltage, self._valid = arrays[3:]
        require(all(len(axis) >= 2 and (axis[1:] > axis[:-1]).all() for axis in self.axes),
                "Spatial axes must increase strictly")
        shape = tuple(map(len, self.axes))
        require(self._voltage.shape == (*shape, len(self.time_ms))
                and self._valid.shape == tuple(n - 1 for n in shape) and self._valid.any(),
                "Inconsistent waveform shape or empty support")
        landmark = meta["landmark_index"]
        require(type(landmark) is int and 0 < landmark < len(self.time_ms) - 1
                and np.allclose(self.time_ms, (np.arange(len(self.time_ms)) - landmark) / 10,
                                atol=1e-12, rtol=0), "Invalid time grid or landmark")
        self.id, self.status = meta["id"], meta["status"]
        self.landmark_index = landmark
        self.manifest_sha256 = sha256(raw).hexdigest()

    def _lookup(self, q):
        base, fraction = [], []
        for axis, value in zip(self.axes, q):
            require(axis[0] <= value <= axis[-1], "Outside spatial grid")
            # Interior faces belong to the positive-side cell, outer maximum to the last cell.
            i = min(np.searchsorted(axis, value, side="right") - 1, len(axis) - 2)
            base.append(i)
            fraction.append((value - axis[i]) / (axis[i + 1] - axis[i]))
        require(self._valid[tuple(base)], "Unsupported interpolation cell")
        result = np.zeros(len(self.time_ms), dtype=np.float64)
        for corner in CORNERS:
            weight = np.prod([f if c else 1 - f for f, c in zip(fraction, corner)])
            index = tuple(i + c for i, c in zip(base, corner))
            result += weight * self._voltage[index].astype(np.float64)
        return result

    def evaluate_pose(self, source_id, soma_um, rotation, contacts_um):
        """Evaluate one source's pose. Return a writable [time,E1–E4] copy."""
        try:
            points = world_to_cell(contacts_um, soma_um, rotation)
        except (ValueError, TypeError) as exc:
            raise BankError(f"{source_id}: {exc}") from exc
        key = points.tobytes()
        if key not in self._cache:
            traces = []
            for label, point in zip(CONTACTS, points):
                try:
                    traces.append(self._lookup(point))
                except BankError as exc:
                    raise BankError(f"{source_id} / {label} at {point.tolist()} µm: {exc}") from exc
            self._cache[key] = np.stack(traces, axis=1)
            if len(self._cache) > 16:
                self._cache.popitem(last=False)
        self._cache.move_to_end(key)
        return self._cache[key].copy()
