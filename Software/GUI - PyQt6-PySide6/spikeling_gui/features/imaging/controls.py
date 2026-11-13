"""Physical units, ranges and defaults for the GECI sliders."""

from typing import NamedTuple, Optional, Tuple

from spikeling_gui.features.imaging.presets import GECI



class GeciSliderSpec(NamedTuple):
    """
    Encoding and admissible span of one fluorescence-tab slider.

    Attributes
    ----------
    preset_key : str
        Key into a ``GECI`` entry.
    counts_per_unit : float
        Slider counts per physical unit. Sets the quantisation step: at
        ``1000`` counts/µM a Kd of 0.144 µM is representable exactly, at the
        previous ``10`` counts/µM it collapsed onto 0.1 µM.
    fallback : float
        Value used when a preset omits ``preset_key``.
    floor_units, ceiling_units : float
        Hard bounds in physical units. The applied range is widened further
        whenever a preset, or the requested headroom, exceeds them, so no
        indicator can ever be truncated by the widget.
    """

    preset_key: str
    counts_per_unit: float
    fallback: float
    floor_units: float
    ceiling_units: float


# Slider ranges are derived from the preset table, never hard-coded in the .ui
GECI_SLIDER_SPECS: dict[str, GeciSliderSpec] = {
    "Imaging_kd_Slider":       GeciSliderSpec("Kd_uM",           1000.0,   0.200, 0.001,    5.0),
    "Imaging_Hill_Slider":     GeciSliderSpec("hill_n",           100.0,   2.000, 0.100,   10.0),
    "Imaging_DFF_Slider":      GeciSliderSpec("dff_max",           10.0,  20.000, 0.000,  100.0),
    "Imaging_IndRise_Slider":  GeciSliderSpec("Ind_tau_rise_ms",    1.0,  50.000, 1.000, 1000.0),
    "Imaging_IndDecay_Slider": GeciSliderSpec("Ind_tau_decay_ms",   1.0, 300.000, 1.000, 3000.0),
}

# Digits shown next to each slider, matched to its quantisation step
GECI_READOUT_DECIMALS: dict[str, int] = {
    "Imaging_kd_Slider": 3,
    "Imaging_Hill_Slider": 2,
    "Imaging_DFF_Slider": 1,
    "Imaging_IndRise_Slider": 0,
    "Imaging_IndDecay_Slider": 0,
}


def format_slider_units(ui, slider_name: str) -> str:
    """
    Render a fluorescence slider as a physical-unit string.

    Parameters
    ----------
    ui : object
        Generated Ui object.
    slider_name : str
        Attribute name of the slider.

    Returns
    -------
    str
        Value formatted with the precision declared in
        :data:`GECI_READOUT_DECIMALS`.
    """
    decimals = GECI_READOUT_DECIMALS.get(slider_name, 2)
    return f"{slider_units(ui, slider_name):.{decimals}f}"


def reset_slider_to_default(ui, slider_name: str, silent: bool = False) -> float:
    """
    Return a fluorescence slider to the preset-table default.

    Replaces the raw-count defaults previously written by the ``Activate*``
    handlers (``setValue(15)``, ``setValue(100)``, …), which encoded the old
    divisors and would now mean 0.015 µM or 1.00 instead of 0.200 µM / 2.00.

    Parameters
    ----------
    ui : object
        Generated Ui object.
    slider_name : str
        Attribute name of the slider.
    silent : bool, optional
        Suppress ``valueChanged``. Leave ``False`` so the imaging parameter
        cache follows the reset.

    Returns
    -------
    float
        Default value in physical units.
    """
    spec = GECI_SLIDER_SPECS[slider_name]
    slider = getattr(ui, slider_name, None)
    if slider is None:
        return spec.fallback
    if silent:
        return set_slider_units(slider, spec, spec.fallback)
    counts = int(round(spec.fallback * spec.counts_per_unit))
    slider.setValue(max(slider.minimum(), min(slider.maximum(), counts)))
    return float(slider.value()) / spec.counts_per_unit

# Multiplicative margin above the most extreme preset, so a user can explore
# beyond the shipped indicators without the range being re-tuned by hand.
GECI_RANGE_HEADROOM = 1.5
GECI_SLIDER_TICKS = 11


def slider_units(ui, slider_name: str) -> float:
    """
    Read a fluorescence slider in physical units.

    Single decoding entry point: the ``/10``, ``/100`` divisors previously
    scattered across the parameter cache and the UI read-out handlers are
    replaced by the ``counts_per_unit`` field of :data:`GECI_SLIDER_SPECS`.

    Parameters
    ----------
    ui : object
        The generated Ui object holding the sliders.
    slider_name : str
        Attribute name of the slider, e.g. ``'Imaging_kd_Slider'``.

    Returns
    -------
    float
        Slider position converted to µM, ms or dimensionless units.
    """
    spec = GECI_SLIDER_SPECS[slider_name]
    slider = getattr(ui, slider_name, None)
    if slider is None:
        return spec.fallback
    return float(slider.value()) / spec.counts_per_unit


def set_slider_units(slider, spec: GeciSliderSpec, value_units: float) -> float:
    """
    Write a physical value into ``slider`` without emitting ``valueChanged``.

    Parameters
    ----------
    slider : PySide6.QtWidgets.QSlider
        Target slider, addressed in raw counts.
    spec : GeciSliderSpec
        Encoding of that slider.
    value_units : float
        Desired value in physical units.

    Returns
    -------
    float
        Value effectively stored, in physical units (identical to the request
        once :func:`configure_geci_slider_ranges` has run).
    """
    counts = int(round(value_units * spec.counts_per_unit))
    counts = max(slider.minimum(), min(slider.maximum(), counts))
    was_blocked = slider.blockSignals(True)
    slider.setValue(counts)
    slider.blockSignals(was_blocked)
    return counts / spec.counts_per_unit


def configure_geci_slider_ranges(ui, presets: Optional[dict] = None) -> dict:
    """
    Widen the fluorescence sliders so every GECI preset fits without clamping.

    For each slider the span is

    $$[\\min(\\text{floor}, \\min_i v_i),\\; \\max(\\text{ceiling}, \\gamma \\max_i v_i)]$$

    with $ v_i $ the value of preset $ i $ and $ \\gamma $ the headroom factor.
    The current position is preserved in physical units across the rescale.

    Parameters
    ----------
    ui : object
        Generated Ui object.
    presets : dict, optional
        Indicator table; defaults to ``GECI``.

    Returns
    -------
    dict
        ``{slider_name: (min_units, max_units)}`` actually applied.

    Notes
    -----
    Must be called **after** ``spikeling_gui.widgets.sliders.configure_sliders``: that
    helper replaces each widget by a :class:`TickSlider` and copies the range
    from the Qt Designer original, which would otherwise overwrite this one.
    """
    presets = GECI if presets is None else presets
    applied: dict[str, Tuple[float, float]] = {}

    for slider_name, spec in GECI_SLIDER_SPECS.items():
        slider = getattr(ui, slider_name, None)
        if slider is None:
            continue

        values = [float(p.get(spec.preset_key, spec.fallback)) for p in presets.values()]
        min_units = min([spec.floor_units] + values)
        max_units = max([spec.ceiling_units] + [GECI_RANGE_HEADROOM * v for v in values])

        previous_units = float(slider.value()) / spec.counts_per_unit

        was_blocked = slider.blockSignals(True)
        slider.setRange(int(round(min_units * spec.counts_per_unit)),
                        int(round(max_units * spec.counts_per_unit)))
        slider.setSingleStep(max(1, int(round(spec.counts_per_unit / 100.0))))
        slider.setPageStep(max(1, int(round(spec.counts_per_unit))))
        slider.setValue(int(round(min(max(previous_units, min_units), max_units)
                                  * spec.counts_per_unit)))
        slider.blockSignals(was_blocked)

        if hasattr(slider, "set_num_ticks"):
            slider.set_num_ticks(GECI_SLIDER_TICKS)

        applied[slider_name] = (min_units, max_units)

    return applied