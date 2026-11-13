"""
Shared simulation-speed model for the Spikeling hardware and emulator.

Both pages advertise the same quantity, the *speed factor*

$$ s = \\\\frac{\\\\Delta t_{\\\\text{model}}}{\\\\Delta t_{\\\\text{wall}}} $$

the number of simulated milliseconds produced per millisecond of wall-clock
time. ``s = 1`` is biological real time, ``s = 0.05`` is twenty times slower
than life, which is the regime where a 1 ms action potential is actually
visible on screen.

The two back ends reach that factor by different means, which is why they
previously disagreed:

* **Hardware** sets the firmware loop period, ``DT`` in microseconds, so
  $ s = \\\\Delta t_{\\\\text{model}} / \\\\mathrm{DT} $.
* **Emulator** sets how many fixed 0.1 ms Euler steps run per 50 ms GUI tick,
  so $ s = n_{\\\\text{steps}} \\\\, \\\\Delta t_{\\\\text{model}} / T_{\\\\text{tick}} $.

Deriving both from a single table of factors makes the displayed number
identical by construction, and makes the slider index mean the same thing on
both pages.

Notes
-----
The emulator's former ``REALTIME_STEPS_PER_UPDATE = 10000`` was twenty times
the correct ``GUI_TICK_MS / MODEL_DT_MS = 500``, so every emulator speed was
reported twenty times too slow, and the top slider positions requested
200 000 integration steps per second, which Python cannot deliver: the timer
simply overran and the GUI stopped responding.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple


# --- Physical constants ----------------------------------------------------
MODEL_DT_MS = 0.1          # Izhikevich integration step, firmware and emulator
MODEL_DT_US = MODEL_DT_MS * 1000.0
GUI_TICK_MS = 50.0         # emulator QTimer period

#: Integration steps per GUI tick corresponding to biological real time.
REALTIME_STEPS_PER_TICK = GUI_TICK_MS / MODEL_DT_MS      # 500.0

#: Shortest firmware loop period that the 500 kBaud link can sustain.
#: A 16-byte payload plus a 2-byte header is 180 bit-times, so the serial
#: layer saturates near 360 us; 200 us is the firmware floor already in use.
HARDWARE_MIN_DT_US = 200

#: Speed ladder shared by both pages. Indices 0-6 are reachable on hardware;
#: 7-8 are emulator-only, kept so long synthetic recordings can still be
#: produced faster than real time.
SPEED_FACTORS: Tuple[float, ...] = (
    0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0,
)

#: Shared start-up position, matching the hardware default of ``x 0.05``.
DEFAULT_SPEED_INDEX = 3


@dataclass(frozen=True)
class SpeedSetting:
    """
    One rung of the shared speed ladder.

    Attributes
    ----------
    index : int
        Slider position.
    factor : float
        Simulated milliseconds per wall-clock millisecond.
    firmware_dt_us : int or None
        Loop period sent as ``DT <value>``, or ``None`` when the rung is
        faster than the serial link can sustain and is therefore
        emulator-only.
    """

    index: int
    factor: float
    firmware_dt_us: Optional[int]

    @property
    def emulator_steps_per_tick(self) -> float:
        """
        Integration steps per GUI tick, possibly fractional.

        Returns a float on purpose: ``0.005x`` is 2.5 steps per tick, and
        rounding it to 2 or 3 would bias the emulator clock by up to 20 %.
        :class:`FractionalStepScheduler` carries the remainder instead.
        """
        return self.factor * REALTIME_STEPS_PER_TICK

    @property
    def available_on_hardware(self) -> bool:
        """Whether the board can run at this factor."""
        return self.firmware_dt_us is not None

    @property
    def label(self) -> str:
        """Text for the ``*_Speed_value`` label, identical on both pages."""
        return format_speed_label(self.factor)


def _build_ladder() -> Tuple[SpeedSetting, ...]:
    """Derive the firmware period of every rung from its speed factor."""
    rungs = []
    for index, factor in enumerate(SPEED_FACTORS):
        dt_us = int(round(MODEL_DT_US / factor))
        rungs.append(SpeedSetting(
            index=index,
            factor=factor,
            firmware_dt_us=dt_us if dt_us >= HARDWARE_MIN_DT_US else None,
        ))
    return tuple(rungs)


SPEED_LADDER: Tuple[SpeedSetting, ...] = _build_ladder()

#: Highest slider index the board can honour.
HARDWARE_MAX_INDEX = max(s.index for s in SPEED_LADDER if s.available_on_hardware)
EMULATOR_MAX_INDEX = SPEED_LADDER[-1].index


def format_speed_label(factor: float) -> str:
    """
    Render a speed factor for display.

    Parameters
    ----------
    factor : float
        Simulated milliseconds per wall-clock millisecond.

    Returns
    -------
    str
        For example ``'x 0.05'``. ``:g`` is used so 0.005 does not become
        ``0.01`` and 1.0 does not become ``1.000``.
    """
    return f"x {factor:g}"


def clamp_index(index: int, hardware: bool = False) -> int:
    """
    Constrain a slider position to the usable range.

    Parameters
    ----------
    index : int
        Raw slider value.
    hardware : bool, optional
        Clamp to the fastest rung the board can sustain.

    Returns
    -------
    int
        Valid index into :data:`SPEED_LADDER`.
    """
    upper = HARDWARE_MAX_INDEX if hardware else EMULATOR_MAX_INDEX
    return max(0, min(int(index), upper))


def setting_for_index(index: int, hardware: bool = False) -> SpeedSetting:
    """
    Resolve a slider position to its :class:`SpeedSetting`.

    Replaces the former if/elif chain, which had no ``else`` branch and left
    ``self.Speed`` undefined for any index above 6.

    Parameters
    ----------
    index : int
        Raw slider value; clamped rather than rejected.
    hardware : bool, optional
        Restrict to rungs the board can reach.

    Returns
    -------
    SpeedSetting
        Always a valid rung.
    """
    return SPEED_LADDER[clamp_index(index, hardware)]


class FractionalStepScheduler:
    """
    Emit whole integration steps while honouring a fractional target rate.

    At ``0.005x`` the emulator owes 2.5 steps per 50 ms tick. Truncating to 2
    would run the model 20 % slow and silently desynchronise it from the
    hardware trace it is meant to be compared against. Carrying the remainder
    alternates 2 and 3 steps, so the long-run mean is exact.

    Examples
    --------
    >>> scheduler = FractionalStepScheduler()
    >>> [scheduler.take(2.5) for _ in range(4)]
    [2, 3, 2, 3]
    """

    __slots__ = ("_carry",)

    def __init__(self) -> None:
        self._carry = 0.0

    def take(self, steps_per_tick: float) -> int:
        """
        Return the whole steps owed this tick and bank the remainder.

        Parameters
        ----------
        steps_per_tick : float
            Target rate, from :attr:`SpeedSetting.emulator_steps_per_tick`.

        Returns
        -------
        int
            Steps to integrate now.
        """
        total = self._carry + float(steps_per_tick)
        whole = int(total)
        self._carry = total - whole
        return whole

    def reset(self) -> None:
        """Discard the banked remainder, on emulator restart."""
        self._carry = 0.0


def configure_speed_slider(slider, label, hardware: bool) -> SpeedSetting:
    """
    Put one speed slider on the shared ladder and show its label.

    Parameters
    ----------
    slider : PySide6.QtWidgets.QSlider
        ``Spikeling_Speed_slider`` or ``Emulator_Speed_slider``.
    label : PySide6.QtWidgets.QLabel
        Matching ``*_Speed_value`` label.
    hardware : bool
        ``True`` to cap the range at :data:`HARDWARE_MAX_INDEX`.

    Returns
    -------
    SpeedSetting
        The rung the slider was left on.
    """
    upper = HARDWARE_MAX_INDEX if hardware else EMULATOR_MAX_INDEX

    was_blocked = slider.blockSignals(True)
    slider.setRange(0, upper)
    slider.setSingleStep(1)
    slider.setPageStep(1)
    slider.setValue(DEFAULT_SPEED_INDEX)
    slider.blockSignals(was_blocked)

    if hasattr(slider, "set_num_ticks"):
        slider.set_num_ticks(upper + 1)

    setting = SPEED_LADDER[DEFAULT_SPEED_INDEX]
    if label is not None:
        label.setText(setting.label)
    return setting


def apply_speed_sliders(ui) -> None:
    """
    Put both speed sliders on the shared ladder at the same start-up rung.

    Call once during window construction, *before* the ``valueChanged``
    handlers are connected, so seeding the default position cannot emit a
    serial write to a port that is not open yet.

    Parameters
    ----------
    ui : object
        Generated Qt UI object.
    """
    configure_speed_slider(getattr(ui, "Spikeling_Speed_slider", None),
                           getattr(ui, "Spikeling_Speed_value", None),
                           hardware=True)
    configure_speed_slider(getattr(ui, "Emulator_Speed_slider", None),
                           getattr(ui, "Emulator_Speed_value", None),
                           hardware=False)
