"""Contact crossings and first-crossing-anchored extracellular groups."""
from dataclasses import dataclass
from math import isfinite

import numpy as np

from .acquisition import CONTACTS
from .offline_processing import contacts_valid


@dataclass(frozen=True)
class Detector:
    threshold_uV: float = -15.0
    refractory_ms: float = 0.6
    grouping_ms: float = 0.4
    contacts: tuple = CONTACTS
    polarity: str = "negative"

    def validate(self):
        if self.polarity != "negative" or not isfinite(self.threshold_uV) or self.threshold_uV >= 0:
            raise ValueError("Enter a finite negative threshold in µV.")
        if not contacts_valid(self.contacts, 1):
            raise ValueError("Select one or more detection contacts.")
        if not all(isfinite(value) and value >= 0 for value in (self.refractory_ms, self.grouping_ms)):
            raise ValueError("Refractory and grouping windows must be finite and non-negative.")


@dataclass(frozen=True)
class Crossing:
    sample: int
    tick: int
    time_ms: float
    contact: str
    segment: int
    epoch: int
    threshold_uV: float
    recipe_id: str
    provenance: str = "offline_negative_threshold"


@dataclass(frozen=True)
class Group:
    id: str
    sample: int
    tick: int
    time_ms: float
    segment: int
    epoch: int
    crossings: tuple[Crossing, ...]

    @property
    def key(self):
        return self.segment, self.epoch


def detect_run(run, config, rate, recipe_id):
    """Return contacts and groups from one contiguous, effective epoch."""
    config.validate()
    signal = run.values_uV
    if not np.isfinite(signal).all():
        raise ValueError("Detection requires finite samples within a validated run.")
    crossings = []
    ms_per_tick = 1000.0 / rate
    # Prime the comparison with the first eligible sample. A signal that is
    # already below threshold at a reset boundary is not a measured crossing.
    lo = run.warmup
    if len(signal) <= lo + 1:
        return ()
    for contact in config.contacts:
        trace = signal[lo:, CONTACTS.index(contact)]
        candidates = np.flatnonzero((trace[:-1] > config.threshold_uV)
                                    & (trace[1:] <= config.threshold_uV)) + lo + 1
        previous = None
        for row in candidates:
            row = int(row)
            if previous is not None and (row - previous) < config.refractory_ms / ms_per_tick - 1e-9:
                continue
            previous = row
            crossings.append(Crossing(run.first + row, run.tick + row, float(run.time_ms[row]),
                                      contact, run.segment, run.epoch, config.threshold_uV, recipe_id))
    groups = []
    members = []
    for contact in sorted(crossings, key=lambda item: (item.sample, item.contact)):
        if members and contact.tick != members[0].tick and (
                contact.tick - members[0].tick >= config.grouping_ms / ms_per_tick - 1e-9):
            groups.append(_group(members))
            members = []
        members.append(contact)
    if members:
        groups.append(_group(members))
    return tuple(groups)


def _group(members):
    first = members[0]
    return Group(f"{first.recipe_id}:{first.segment}:{first.epoch}:{first.sample}",
                 first.sample, first.tick, first.time_ms, first.segment, first.epoch, tuple(members))
