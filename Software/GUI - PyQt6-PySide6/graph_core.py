"""
Shared primitives for the Spikeling real-time graph modules.

Centralises the four concerns that were previously re-implemented in
Graph_Emulator, Graph_Spikeling, Graph_Imaging and Graph_ExtraCellular:
rolling buffers, packet parsing, oscilloscope configuration and CSV paths.
"""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple, Optional, Sequence

import numpy as np
import pyqtgraph as pg


# =============================================================================
# Rolling buffer
# =============================================================================

class RingBuffer:
    """
    Fixed-capacity rolling buffer with O(1) append and O(1) contiguous read.

    Samples are stored twice in a doubled backing array so the chronologically
    ordered window is always a contiguous slice. This removes the
    ``np.asarray(deque)`` / ``list(deque)`` conversion that dominates redraw
    cost when plotting long oscilloscope windows.

    Parameters
    ----------
    capacity : int
        Number of samples retained in the rolling window.
    n_channels : int, optional
        Number of interleaved channels. ``1`` yields a 1-D view, ``>1`` yields
        a ``(capacity, n_channels)`` view.
    fill : float, optional
        Initial value of every sample.
    dtype : numpy.dtype, optional
        Storage dtype.

    Attributes
    ----------
    capacity : int
        Retained window length.
    data : numpy.ndarray
        Chronological view, oldest sample first.
    latest : numpy.ndarray or float
        Most recently appended sample.

    Examples
    --------
    >>> buf = RingBuffer(4)
    >>> buf.extend([1.0, 2.0, 3.0, 4.0, 5.0])
    >>> buf.data
    array([2., 3., 4., 5.])
    """

    __slots__ = ("capacity", "n_channels", "_store", "_head")

    def __init__(self, capacity: int, n_channels: int = 1,
                 fill: float = 0.0, dtype=float) -> None:
        self.capacity = int(capacity)
        self.n_channels = int(n_channels)
        shape = (2 * self.capacity,) if n_channels == 1 else (2 * self.capacity, n_channels)
        self._store = np.full(shape, fill, dtype=dtype)
        self._head = 0

    def append(self, value) -> None:
        """Append one sample (scalar, or a length ``n_channels`` sequence)."""
        self._store[self._head] = value
        self._store[self._head + self.capacity] = value
        self._head = (self._head + 1) % self.capacity

    def extend(self, values) -> None:
        """Append a block shaped ``(n,)`` or ``(n, n_channels)``."""
        block = np.asarray(values, dtype=self._store.dtype)
        if block.size == 0:
            return
        n = block.shape[0]
        if n >= self.capacity:
            block = block[-self.capacity:]
            n = self.capacity
        end = self._head + n
        if end <= self.capacity:
            self._store[self._head:end] = block
            self._store[self._head + self.capacity:end + self.capacity] = block
            self._head = end % self.capacity
        else:
            split = self.capacity - self._head
            self.extend(block[:split])
            self.extend(block[split:])

    def fill_with(self, value: float = 0.0) -> None:
        """Reset every sample to ``value`` and rewind the write head."""
        self._store[...] = value
        self._head = 0

    @property
    def data(self) -> np.ndarray:
        """Chronological view of the window, oldest sample first."""
        return self._store[self._head:self._head + self.capacity]

    @property
    def latest(self):
        """Most recently appended sample."""
        return self._store[self._head + self.capacity - 1]


# =============================================================================
# Packet parsing
# =============================================================================

class SpikelingSample(NamedTuple):
    """
    One decoded Spikeling stream sample.

    Attributes
    ----------
    t_ms : float or None
        Device timestamp in milliseconds, or ``None`` for 8-field packets that
        carry no clock.
    vm0, vm1, vm2 : float
        Membrane potentials of the soma and the two synaptic neurons (mV).
    stim : float
        Stimulus state (%).
    itot : float
        Total somatic input current (a.u.).
    isyn1, isyn2 : float
        Synaptic input currents (a.u.).
    trigger : float
        Stimulus trigger flag.
    """

    t_ms: Optional[float]
    vm0: float
    stim: float
    itot: float
    vm1: float
    isyn1: float
    vm2: float
    isyn2: float
    trigger: float


def parse_spikeling_packet(data: Sequence) -> Optional[SpikelingSample]:
    """
    Decode an 8-field (no clock) or 9-field (timestamped) Spikeling packet.

    Parameters
    ----------
    data : sequence
        Raw packet, either ``[Vm0, Stim, Itot, Vm1, ISyn1, Vm2, ISyn2, Trigger]``
        or that vector prefixed by a millisecond timestamp.

    Returns
    -------
    SpikelingSample or None
        ``None`` if the packet is malformed or too short.
    """
    if data is None:
        return None
    try:
        vals = [float(x) for x in data]
    except (TypeError, ValueError):
        return None

    if len(vals) >= 9:
        return SpikelingSample(vals[0], vals[1], vals[2], vals[3],
                               vals[4], vals[5], vals[6], vals[7], vals[8])
    if len(vals) >= 8:
        return SpikelingSample(None, vals[0], vals[1], vals[2],
                               vals[3], vals[4], vals[5], vals[6], vals[7])
    return None


# =============================================================================
# Plot / path helpers
# =============================================================================

def configure_scope(plot_item, downsample_mode: str = "peak") -> None:
    """
    Apply the standard oscilloscope render settings to a PlotItem.

    Peak-preserving downsampling plus view clipping means the renderer only
    rasterises the samples actually visible in the current x-range, instead of
    the full multi-second buffer. Spike peaks are preserved by ``mode='peak'``.

    Parameters
    ----------
    plot_item : pyqtgraph.PlotItem
        Target plot item.
    downsample_mode : {'peak', 'mean', 'subsample'}, optional
        Decimation strategy; ``'peak'`` is required for spike traces.
    """
    plot_item.setDownsampling(auto=True, mode=downsample_mode)
    plot_item.setClipToView(True)


def safe_reconnect(signal, slot) -> None:
    """
    Connect ``slot`` to ``signal`` exactly once, dropping any prior connection.

    Qt signals owned by long-lived widgets accumulate one extra connection per
    reconnect cycle, so a resize handler ends up running N times after N
    connect/disconnect cycles.

    Parameters
    ----------
    signal : PySide6.QtCore.SignalInstance
        Signal to rebind.
    slot : callable
        Receiver.
    """
    try:
        signal.disconnect(slot)
    except (RuntimeError, TypeError):
        pass
    signal.connect(slot)


def resolve_csv_path(base: str) -> Optional[Path]:
    """
    Build a ``.csv`` path from a user-supplied base name.

    Uses string concatenation rather than :meth:`pathlib.Path.with_suffix`,
    which would truncate a version-like stem (``rec_v1.2`` -> ``rec_v1.csv``).

    Parameters
    ----------
    base : str
        Base path from the UI label, with or without a ``.csv`` suffix.

    Returns
    -------
    pathlib.Path or None
        Resolved path with parent directories created, or ``None`` if blank.
    """
    base = str(base).strip()
    if not base:
        return None
    if base.lower().endswith(".csv"):
        base = base[:-4]
    path = Path(base + ".csv")
    if str(path.parent) not in ("", "."):
        path.parent.mkdir(parents=True, exist_ok=True)
    return path
