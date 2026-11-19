"""Adapt legacy serial rows and emulator steps without conflating clocks."""
from dataclasses import dataclass
from math import isfinite
from time import monotonic_ns

import numpy as np

from .acquisition import Clock, Discontinuity


@dataclass(frozen=True)
class AdaptedRows:
    rows: np.ndarray
    flags: np.ndarray | None
    clock: Clock
    first_tick: int
    first_ordinal: int | None
    host_ns: int | None


class InputAdapter:
    # Timestamp-only callers use binary64 milliseconds. This admits bounded
    # accumulation error while remaining well below half a model step.
    TIMESTAMP_TOLERANCE_MS = 0.001

    def __init__(self, clock=monotonic_ns):
        self.clock = clock
        self.reset()

    def reset(self):
        self.ordinal = 0
        self.last_ordinal = -1
        self.last_host_ns = None
        self.last_tick = None
        self.last_payload = None
        self.last_time_ms = None
        self.accepted = 0
        self.duplicates = 0
        self.rejected = 0
        self.capacity_lost = 0
        self.trimmed = 0
        self.high_water = 0

    @property
    def local_losses(self):
        return self.capacity_lost + self.trimmed + self.rejected

    def enqueue(self, queue, packet):
        if len(queue) == queue.maxlen:
            self.capacity_lost += 1
        queue.append((self.ordinal, self.clock(), packet))
        self.ordinal += 1
        self.high_water = max(self.high_water, len(queue))

    @staticmethod
    def _decode(packet, length):
        try:
            row = tuple(float(v) for v in packet)
        except (TypeError, ValueError, OverflowError):
            return None
        if len(row) == length and all(map(isfinite, row)):
            return row
        return None

    def hardware(self, batch, *, stall_ns):
        rows = []
        first = None
        for ordinal, host_ns, packet in batch:
            missing = ordinal - self.last_ordinal - 1
            stalled = (host_ns - self.last_host_ns
                       if self.last_host_ns is not None else 0)
            row = self._decode(packet, 8)
            if missing or stalled > stall_ns or row is None:
                if rows:
                    yield self._hardware_rows(rows, first)
                    rows = []
                if row is None:
                    self.rejected += 1
                yield Discontinuity(
                    "Malformed hardware input" if row is None else
                    "Hardware queue loss" if missing else "Hardware input resumed after host stall",
                    self.accepted, missing + int(row is None),
                    host_stall_ns=stalled if stalled > stall_ns else None,
                    previous_receive_ordinal=self.last_ordinal,
                    next_receive_ordinal=ordinal if row is not None else None,
                )
            self.last_ordinal, self.last_host_ns = ordinal, host_ns
            if row is not None:
                if not rows:
                    first = ordinal, host_ns
                rows.append(row)
                self.accepted += 1
        if rows:
            yield self._hardware_rows(rows, first)

    @staticmethod
    def _hardware_rows(rows, first):
        ordinal, host_ns = first
        return AdaptedRows(np.asarray(rows), None, Clock.NOMINAL_MODEL,
                           ordinal + 1, ordinal, host_ns)

    def emulator(self, batch, *, ticks=None, flags=None):
        provenance = Clock.EMULATOR_TICK if ticks is not None else Clock.EMULATOR_TIMESTAMP
        try:
            valid_ticks = (ticks is None or
                           (len(ticks) == len(batch) and
                            all(isinstance(t, (int, np.integer)) and 0 <= t < 2**63 for t in ticks)))
            if flags is not None:
                flags = np.asarray(flags)
                valid_flags = flags.shape == (len(batch), 3) and np.isin(flags, (0, 1)).all()
            else:
                valid_flags = True
        except (TypeError, ValueError):
            valid_ticks = valid_flags = False
        if not valid_ticks or not valid_flags:
            self.rejected += len(batch)
            if len(batch):
                yield Discontinuity("Misaligned emulator data", self.accepted, len(batch))
            return

        rows, event_rows = [], []
        first_tick = None
        host_ns = self.clock()
        for i, packet in enumerate(batch):
            row = self._decode(packet, 9)
            flag = tuple(flags[i]) if flags is not None else None
            tick = None
            if row is not None and 0 <= row[0] < (2**63 - 1) / 10:
                tick = int(ticks[i]) if ticks is not None else round(row[0] * 10)
                if abs(row[0] - tick / 10) > self.TIMESTAMP_TOLERANCE_MS:
                    tick = None
            previous = self.last_tick
            reason = None
            missing = None
            rejected = False
            if tick is None:
                reason, rejected = "Invalid emulator row or timestamp", True
            elif previous is not None:
                if tick == previous:
                    if (row, flag) == self.last_payload:
                        self.duplicates += 1
                        continue
                    reason, rejected = "Conflicting emulator duplicate", True
                elif tick < previous or row[0] <= self.last_time_ms:
                    reason = "Emulator clock reversed"
                elif tick > previous + 1:
                    reason, missing = "Missing emulator steps", tick - previous - 1
            if reason:
                if rows:
                    yield self._emulator_rows(rows, event_rows, provenance, first_tick, host_ns)
                    rows, event_rows = [], []
                self.rejected += int(rejected)
                yield Discontinuity(reason, self.accepted, int(rejected), missing,
                                    previous_tick=previous, next_tick=tick if not rejected else None)
            if rejected:
                continue
            if not rows:
                first_tick = tick
            rows.append(row)
            if flag is not None:
                event_rows.append(flag)
            self.accepted += 1
            self.last_tick, self.last_payload, self.last_time_ms = tick, (row, flag), row[0]
        if rows:
            yield self._emulator_rows(rows, event_rows, provenance, first_tick, host_ns)

    @staticmethod
    def _emulator_rows(rows, event_rows, clock, tick, host_ns):
        flags = np.asarray(event_rows, dtype=np.uint8) if event_rows else None
        return AdaptedRows(np.asarray(rows), flags, clock, tick, None, host_ns)
