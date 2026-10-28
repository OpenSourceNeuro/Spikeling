"""
Short-term synaptic plasticity for the Spikeling desktop emulator.

This event-driven, classroom-oriented Tsodyks-Markram simplification matches
the microcontroller implementation in Firmware/Spikeling_V3/STP_functions.h.
Mode 0 is the unchanged static synapse; the first event after selecting a
mode has a multiplier of 1.0. Synaptic-current decay remains independent.
"""

from dataclasses import dataclass
from math import exp

# Mode names intentionally match the integer values used in serial commands.
OFF, FACILITATION, DEPRESSION, COMBINED = range(4)

# Resting utilisation, facilitation time (ms), recovery time (ms).
PRESETS = {
    OFF: (1.0, 0.0, 0.0),
    FACILITATION: (0.15, 500.0, 0.0),
    DEPRESSION: (0.40, 0.0, 800.0),
    COMBINED: (0.25, 500.0, 600.0),
}


@dataclass
class STPState:
    """Maintain one synapse's transient utilisation and resource availability."""

    mode: int = OFF
    u: float = 1.0
    x: float = 1.0
    last_event_ms: float = 0.0
    has_event: bool = False

    def set_mode(self, mode: int) -> None:
        """Change the selected preset and clear its transient event history."""
        if mode not in PRESETS:
            raise ValueError(f"Invalid STP mode: {mode}")
        self.mode = mode
        self.u = PRESETS[mode][0]
        self.x = 1.0
        self.last_event_ms = 0.0
        self.has_event = False

    def spike_multiplier(self, time_ms: float, mode: int) -> float:
        """Return the multiplicative current increment for one presynaptic spike.

        Timing is based on the emulator's simulated time, not Qt GUI ticks.
        All state updates are event-driven; no costly work is required on
        integration steps without a presynaptic spike.
        """
        if mode != self.mode:
            self.set_mode(mode)
        if mode == OFF:
            return 1.0

        baseline, tau_fac, tau_rec = PRESETS[mode]
        if self.has_event:
            elapsed_ms = max(0.0, time_ms - self.last_event_ms)
            self.u = (baseline + (self.u - baseline) * exp(-elapsed_ms / tau_fac)
                      if tau_fac > 0.0 else baseline)
            self.x = (1.0 - (1.0 - self.x) * exp(-elapsed_ms / tau_rec)
                      if tau_rec > 0.0 else 1.0)

        multiplier = (self.u / baseline) * self.x
        if tau_rec > 0.0:
            self.x *= 1.0 - self.u
        if tau_fac > 0.0:
            self.u += baseline * (1.0 - self.u)

        self.last_event_ms = time_ms
        self.has_event = True
        return multiplier
