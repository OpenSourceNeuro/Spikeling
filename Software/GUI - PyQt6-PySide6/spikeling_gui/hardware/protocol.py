"""Decode samples from the Spikeling data stream."""

from __future__ import annotations

from typing import NamedTuple, Optional, Sequence


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