"""In-memory identities for the extracellular acquisition pipeline.

Indices count accepted rows within an acquisition. Model ticks describe a
separate 0.1 ms clock. Hardware receive ordinals count observed callbacks.
"""
from dataclasses import dataclass
from enum import Enum
from typing import ClassVar
from uuid import UUID

import numpy as np


NEURONS = ("main", "aux1", "aux2")
CONTACTS = ("E1", "E2", "E3", "E4")


class Clock(Enum):
    NOMINAL_MODEL = "nominal_model_upstream_unknown"
    EMULATOR_TICK = "emulator_model_tick"
    EMULATOR_TIMESTAMP = "emulator_timestamp_derived_tick"


@dataclass(frozen=True)
class Stream:
    stage: str
    channels: tuple[str, ...]
    unit: str


NEURONAL = Stream("neuronal_input", NEURONS, "mV")
BROADBAND = Stream("synthetic_broadband_pre_reference", CONTACTS, "µV")
PROCESSED = Stream("processed_contacts", CONTACTS, "µV")


@dataclass(frozen=True)
class Acquisition:
    id: UUID
    source: str
    generation: int
    tick_period_seconds: tuple[int, int] = (1, 10000)
    device_timestamps: bool = False


@dataclass(frozen=True)
class SampleSpan:
    acquisition: Acquisition
    segment: int
    epoch: int
    first_index: int
    count: int
    first_tick: int
    clock: Clock
    first_receive_ordinal: int | None = None
    host_observed_ns: int | None = None

    def __post_init__(self):
        if self.count <= 0 or min(self.segment, self.epoch, self.first_index, self.first_tick) < 0:
            raise ValueError("A sample span needs a positive count and nonnegative indices")
        if self.first_index + self.count - 1 >= 2**63 or self.first_tick + self.count - 1 >= 2**63:
            raise ValueError("A sample span exceeds the signed 64-bit index domain")


def _publish(array, shape):
    if array.shape != shape or not array.flags.c_contiguous:
        raise ValueError("Array does not match its sample span")
    array.setflags(write=False)


@dataclass(frozen=True)
class InputBlock:
    stream: ClassVar[Stream] = NEURONAL
    span: SampleSpan
    vm_mV: np.ndarray
    stimulus_pct: np.ndarray
    trigger: np.ndarray
    source_t_ms: np.ndarray | None
    native_spikes: np.ndarray | None
    native_available: tuple[bool, bool, bool]
    soma_clamped: bool

    def __post_init__(self):
        count = self.span.count
        _publish(self.vm_mV, (count, 3))
        for array in (self.stimulus_pct, self.trigger, self.source_t_ms):
            if array is not None:
                _publish(array, (count,))
        if self.native_spikes is not None:
            _publish(self.native_spikes, (count, 3))


@dataclass(frozen=True)
class BroadbandBlock:
    stream: ClassVar[Stream] = BROADBAND
    span: SampleSpan
    contacts_uV: np.ndarray

    def __post_init__(self):
        _publish(self.contacts_uV, (self.span.count, 4))


@dataclass(frozen=True)
class ProcessedBlock:
    stream: ClassVar[Stream] = PROCESSED
    span: SampleSpan
    contacts_uV: np.ndarray
    threshold_uV: float
    merged_flags: np.ndarray
    warmup_rows: int

    def __post_init__(self):
        _publish(self.contacts_uV, (self.span.count, 4))
        _publish(self.merged_flags, (self.span.count,))


@dataclass(frozen=True)
class Discontinuity:
    reason: str
    next_index: int
    local_lost: int = 0
    missing_model_steps: int | None = None
    host_stall_ns: int | None = None
    previous_tick: int | None = None
    previous_receive_ordinal: int | None = None
    next_tick: int | None = None
    next_receive_ordinal: int | None = None
    acquisition: Acquisition | None = None
    segment: int | None = None


@dataclass(frozen=True)
class Epoch:
    id: int
    segment: int
    first_index: int
    settings: tuple
    changed: tuple[str, ...]
    reason: str


@dataclass(frozen=True)
class Event:
    kind: str
    span: SampleSpan
    index: int
    channel: str | None
    provenance: str
    group_id: tuple | None = None

    @property
    def id(self):
        return self.span.acquisition.id, self.index, self.kind, self.channel


@dataclass(frozen=True)
class AcquisitionBlock:
    inputs: InputBlock
    broadband: BroadbandBlock
    processed: ProcessedBlock
    events: tuple[Event, ...]
    epoch: Epoch


@dataclass(frozen=True)
class Capture:
    id: UUID
    acquisition: Acquisition
    first_index: int
    end_index: int | None = None
    stop_reason: str = ""
