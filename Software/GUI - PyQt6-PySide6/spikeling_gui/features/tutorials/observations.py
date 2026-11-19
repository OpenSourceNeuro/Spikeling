"""Pure, bounded interpretation of tutorial evidence; no Qt or hardware actions.

Hardware actions are never inferred from model outputs. An observed spike is
identified as a stream event only; it does not establish why it occurred.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import math


@dataclass
class SpikeEvidence:
    threshold_mv: float = 20.0
    count: int = 0
    _previous_vm: float | None = None

    @property
    def seen(self) -> bool:
        return self.count > 0

    def observe(self, sample) -> bool:
        """Count an upward threshold crossing in the first channel (Vm)."""
        try:
            vm = float(sample[0])
        except (TypeError, ValueError, IndexError, KeyError):
            return False
        if not math.isfinite(vm):
            return False
        crossed = vm >= self.threshold_mv and (
            self._previous_vm is not None and self._previous_vm < self.threshold_mv
        )
        self._previous_vm = vm
        if crossed:
            self.count += 1
        return crossed


@dataclass
class RecordingEvidence:
    """Evidence of a newly observed record→stop→successful save cycle."""
    started: bool = False
    saved: bool = False

    def observe(self, *, active: bool, pending: bool, path, label: str) -> bool:
        if active:
            self.started = True
        elif self.started and not pending and path is not None:
            # The existing recording controller sets a Saved label only after
            # export_data_to_csv succeeds. Its no-sample and failed paths do not.
            try:
                valid_file = Path(path).is_file()
            except (TypeError, OSError, ValueError):
                valid_file = False
            self.saved = self.saved or (valid_file and "saved" in label.casefold())
        return self.saved


def response_is_substantive(text: str) -> bool:
    """A low-friction prompt guard; not an automated scientific assessment."""
    return len(text.strip()) >= 8
