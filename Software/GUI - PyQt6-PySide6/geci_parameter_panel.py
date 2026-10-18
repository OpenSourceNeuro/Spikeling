"""
Comparative parameter gauges for the calcium-indicator hover preview.

Each of the five indicator parameters is drawn as a bar whose fill encodes the
position of the hovered indicator inside the span covered by the whole
``Parameters_GECI.GECI`` library. Reading five bars is a constant-time visual
comparison, whereas the previous single-line caption required the user to
remember the numbers of the previously hovered entry.

Kd and the indicator time constants span more than a decade across the library
and are therefore placed on a logarithmic axis; the Hill coefficient and the
saturation amplitude are linear.
"""

from __future__ import annotations

import math
from typing import NamedTuple, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QGridLayout, QLabel, QSizePolicy, QWidget

import Parameters_GECI
import Parameters_Settings as Settings

BAR_HEIGHT_PX = 6
MINIMUM_VISIBLE_FRACTION = 0.03
NAME_COLUMN_PX = 38
VALUE_COLUMN_PX = 62


class ParameterAxis(NamedTuple):
    """
    Display specification of one indicator parameter.

    Attributes
    ----------
    preset_key : str
        Key into a ``Parameters_GECI.GECI`` entry.
    label : str
        Short row caption.
    unit : str
        Unit appended to the numeric read-out.
    decimals : int
        Digits shown, matched to the resolution of the corresponding slider.
    scale : {'log', 'linear'}
        Axis used to map the value onto the bar.
    colour : tuple of int
        RGB pen colour of the fill.
    """

    preset_key: str
    label: str
    unit: str
    decimals: int
    scale: str
    colour: tuple


GECI_PARAMETER_AXES: tuple[ParameterAxis, ...] = (
    ParameterAxis("Kd_uM", "Kd", "µM", 3, "log", tuple(Settings.DarkSolarized[5])),
    ParameterAxis("hill_n", "n", "", 2, "linear", tuple(Settings.DarkSolarized[7])),
    ParameterAxis("dff_max", "ΔF/F₀", "", 1, "linear", tuple(Settings.DarkSolarized[4])),
    ParameterAxis("Ind_tau_rise_ms", "τ rise", "ms", 0, "log", tuple(Settings.DarkSolarized[8])),
    ParameterAxis("Ind_tau_decay_ms", "τ decay", "ms", 0, "log", tuple(Settings.DarkSolarized[10])),
)


def parameter_library_spans(presets: Optional[dict] = None) -> dict:
    """
    Compute the min/max of every parameter over the indicator library.

    Parameters
    ----------
    presets : dict, optional
        Indicator table; defaults to ``Parameters_GECI.GECI``.

    Returns
    -------
    dict
        ``{preset_key: (minimum, maximum)}`` in physical units.
    """
    presets = Parameters_GECI.GECI if presets is None else presets
    spans = {}
    for axis in GECI_PARAMETER_AXES:
        values = [float(entry[axis.preset_key]) for entry in presets.values()
                  if axis.preset_key in entry]
        spans[axis.preset_key] = (min(values), max(values)) if values else (0.0, 1.0)
    return spans


def normalised_position(value: float, low: float, high: float, scale: str) -> float:
    """
    Map ``value`` onto ``[0, 1]`` within the library span.

    Parameters
    ----------
    value : float
        Parameter value of the hovered indicator.
    low, high : float
        Library extrema for that parameter.
    scale : {'log', 'linear'}
        Axis type.

    Returns
    -------
    float
        Fill fraction, clamped so the lowest indicator still shows a sliver.

    Notes
    -----
    On a logarithmic axis the fraction is

    $$f = \\\\frac{\\\\log v - \\\\log v_{\\\\min}}{\\\\log v_{\\\\max} - \\\\log v_{\\\\min}}$$

    which keeps high-affinity indicators (Kd ≈ 0.14 µM) visually separated
    instead of collapsing them against the left edge.
    """
    if high <= low:
        return 0.5
    if scale == "log":
        value, low, high = (max(v, 1e-12) for v in (value, low, high))
        fraction = (math.log(value) - math.log(low)) / (math.log(high) - math.log(low))
    else:
        fraction = (value - low) / (high - low)
    return min(1.0, max(MINIMUM_VISIBLE_FRACTION, fraction))


class ParameterBar(QWidget):
    """
    Single rounded gauge rendering one fill fraction.

    Painted directly rather than styled through ``QProgressBar`` so the fill
    keeps sub-pixel precision and the widget costs one ``update`` per hover.

    Parameters
    ----------
    colour : tuple of int
        RGB fill colour.
    parent : QWidget, optional
        Owner widget.
    """

    def __init__(self, colour: tuple, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._colour = QColor(*colour)
        self._groove = QColor(*Settings.DarkSolarized[2])
        self._fraction = 0.0
        self.setFixedHeight(BAR_HEIGHT_PX)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_fraction(self, fraction: float) -> None:
        """Set the fill fraction in ``[0, 1]`` and schedule a repaint."""
        self._fraction = min(1.0, max(0.0, float(fraction)))
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)

        radius = self.height() / 2.0
        painter.setBrush(self._groove)
        painter.drawRoundedRect(self.rect(), radius, radius)

        filled = self.width() * self._fraction
        if filled >= 1.0:
            painter.setBrush(self._colour)
            painter.drawRoundedRect(0, 0, int(filled), self.height(), radius, radius)
        painter.end()


class GeciParameterPanel(QWidget):
    """
    Five-row comparison chart of one indicator against the whole library.

    Parameters
    ----------
    width_px : int
        Fixed width, normally the width of the turntable render.
    presets : dict, optional
        Indicator table; defaults to ``Parameters_GECI.GECI``.
    parent : QWidget, optional
        Owner widget.
    """

    def __init__(self, width_px: int, presets: Optional[dict] = None,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._presets = Parameters_GECI.GECI if presets is None else presets
        self._spans = parameter_library_spans(self._presets)
        self.setFixedWidth(width_px)
        self.setAttribute(Qt.WA_TranslucentBackground)

        grid = QGridLayout(self)
        grid.setContentsMargins(0, 2, 0, 0)
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(4)

        self._bars: dict[str, ParameterBar] = {}
        self._values: dict[str, QLabel] = {}

        for row, axis in enumerate(GECI_PARAMETER_AXES):
            name = QLabel(axis.label, self)
            name.setFixedWidth(NAME_COLUMN_PX)
            name.setStyleSheet(
                f"color: rgb{tuple(Settings.DarkSolarized[14])};"
                f"font: 400 8pt; background: transparent;")

            bar = ParameterBar(axis.colour, self)
            low, high = self._spans[axis.preset_key]
            bar.setToolTip(f"library range {low:g} – {high:g} {axis.unit}".strip())

            value = QLabel("", self)
            value.setFixedWidth(VALUE_COLUMN_PX)
            value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            value.setStyleSheet(
                f"color: rgb{axis.colour}; font: 700 8pt; background: transparent;")

            grid.addWidget(name, row, 0)
            grid.addWidget(bar, row, 1)
            grid.addWidget(value, row, 2)

            self._bars[axis.preset_key] = bar
            self._values[axis.preset_key] = value

        self._legend = QLabel("position within GECI library (log: Kd, τ)", self)
        self._legend.setAlignment(Qt.AlignCenter)
        self._legend.setStyleSheet(
            f"color: rgb{tuple(Settings.DarkSolarized[11])};"
            f"font: 400 7pt; background: transparent;")
        grid.addWidget(self._legend, len(GECI_PARAMETER_AXES), 0, 1, 3)

    def set_indicator(self, geci_name: str) -> None:
        """
        Update every gauge to the parameters of ``geci_name``.

        Unknown names blank the chart rather than falling back to ``Generic``,
        so a missing preset is visible instead of being misread as real data.
        """
        preset = self._presets.get(geci_name)
        for axis in GECI_PARAMETER_AXES:
            bar = self._bars[axis.preset_key]
            label = self._values[axis.preset_key]

            if preset is None or axis.preset_key not in preset:
                bar.set_fraction(0.0)
                label.setText("—")
                continue

            value = float(preset[axis.preset_key])
            low, high = self._spans[axis.preset_key]
            bar.set_fraction(normalised_position(value, low, high, axis.scale))
            label.setText(f"{value:.{axis.decimals}f} {axis.unit}".strip())
