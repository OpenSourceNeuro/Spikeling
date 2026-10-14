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
from PySide6.QtCore import QObject, QTimer
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


class ScopeTimebase(QObject):
    """
    Latch holding an oscilloscope at its intended time window until the user pans.

    A one-shot deferral cannot pin the x-range reliably: the event that
    overrides it has no bounded arrival time. On the emulator page the right
    menu animates its width for 200 ms after the page is shown, and the first
    GUI tick pushes 50 000-point arrays into the curves 50 ms after start.
    Either can schedule an autorange pass long after a ``singleShot(0)``
    callback has run.

    This object instead monitors ``sigRangeChanged`` and restores the
    requested window whenever something widens it, then disarms itself
    permanently on the first ``sigRangeChangedManually`` so that deliberate
    panning and zooming behave normally.

    Parameters
    ----------
    view_box : pyqtgraph.ViewBox
        Monitored view box.
    x_min : float
        Left edge of the intended window (negative, milliseconds).
    tolerance : float, optional
        Fractional width mismatch tolerated before snapping back. Guards
        against an enforcement loop driven by floating-point noise.

    Attributes
    ----------
    armed : bool
        ``False`` once the user has interacted; no further correction occurs.

    Notes
    -----
    The instance must be retained by the caller. A ``QObject`` whose only
    reference is a signal connection is garbage collected, which silently
    drops the enforcement.
    """

    def __init__(self, view_box, x_min: float, tolerance: float = 0.01) -> None:
        super().__init__()
        self._view_box = view_box
        self._x_min = float(x_min)
        self._tolerance = float(tolerance)
        self._applying = False
        self.armed = True

        view_box.sigRangeChanged.connect(self._on_range_changed)
        view_box.sigRangeChangedManually.connect(self.release)

    def apply(self) -> None:
        """Force the view back to the intended window."""
        if self._applying:
            return
        self._applying = True
        try:
            self._view_box.enableAutoRange(axis=pg.ViewBox.XAxis, enable=False)
            self._view_box.setXRange(self._x_min, 0.0, padding=0.0)
        except RuntimeError:
            self.release()          # widget destroyed
        finally:
            self._applying = False

    def release(self, *_) -> None:
        """Stop enforcing; the user now owns the x-axis."""
        self.armed = False

    def stop(self) -> None:
        """Disarm and detach from the view box, e.g. when tearing down a page."""
        self.release()
        for signal in (self._view_box.sigRangeChanged,
                       self._view_box.sigRangeChangedManually):
            try:
                signal.disconnect(self._on_range_changed)
            except (RuntimeError, TypeError):
                pass
            try:
                signal.disconnect(self.release)
            except (RuntimeError, TypeError):
                pass

    def _on_range_changed(self, *_) -> None:
        """Snap back if the visible width drifted from the requested one."""
        if not self.armed or self._applying:
            return
        try:
            (left, right), _ = self._view_box.viewRange()
        except RuntimeError:
            self.release()
            return

        expected = abs(self._x_min)
        actual = abs(right - left)
        if expected <= 0.0:
            return
        if abs(actual - expected) / expected > self._tolerance:
            self.apply()


def apply_scope_timebase(plot_item, window_ms, display_ms,
                         y_range=None) -> ScopeTimebase:
    """
    Pin an oscilloscope to an exact initial time window.

    Three failure modes are addressed together, because each silently changes
    the apparent sweep speed of a trace:

    1. ``ViewBox`` autoranges on the x-axis by default, and the curve arrays
       span the whole rolling buffer. An autorange pass that runs after the
       explicit range call snaps the view to the full buffer length.
    2. ``setRange`` without ``padding`` falls back to ``suggestPadding``,
       which scales as ``1/sqrt(width_px)`` clipped to ``[0.02, 0.1]``, so a
       250 ms request renders as 275-300 ms depending on widget width.
    3. The disturbing event may arrive arbitrarily late: menu animations and
       the first bulk ``setData`` both outlive a next-iteration deferral.

    Parameters
    ----------
    plot_item : pyqtgraph.PlotItem
        Target plot item.
    window_ms : float
        Full rolling-buffer length (ms); becomes the pan limit.
    display_ms : float
        Initially visible window (ms); must not exceed ``window_ms``.
    y_range : tuple of float, optional
        ``(low, high)`` applied with zero padding and autorange disabled.

    Returns
    -------
    ScopeTimebase
        Active latch. **Must be stored by the caller**, otherwise it is
        garbage collected and enforcement is lost.

    Examples
    --------
    >>> self._timebase = apply_scope_timebase(plot_item, 5000, 500,
    ...                                       y_range=(-90, 30))
    """
    view_box = plot_item.getViewBox()
    x_min = -abs(float(min(display_ms, window_ms)))

    view_box.enableAutoRange(axis=pg.ViewBox.XAxis, enable=False)
    view_box.setLimits(xMin=-abs(float(window_ms)), xMax=0.0)

    if y_range is not None:
        view_box.enableAutoRange(axis=pg.ViewBox.YAxis, enable=False)
        view_box.setYRange(float(y_range[0]), float(y_range[1]), padding=0.0)

    latch = ScopeTimebase(view_box, x_min)
    latch.apply()
    QTimer.singleShot(0, latch.apply)
    return latch
