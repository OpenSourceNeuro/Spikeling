"""Slider units and editable readouts for the imaging model."""

import math
from typing import NamedTuple

from PySide6.QtCore import QSignalBlocker

from spikeling_gui.features.imaging.presets import GECI
from spikeling_gui.widgets.sliders import SliderBinding


SAMPLE_INTERVAL = 0.1  # Model milliseconds per sample.
MODEL_FRAME_RATE_HZ = 1000.0 / SAMPLE_INTERVAL


class ImagingSliderSpec(NamedTuple):
    parameter: str
    counts_per_unit: int = 1
    model_scale: float = 1.0
    preset_key: str | None = None
    ticks: tuple[str, str, str] | None = None

    def display_value(self, position):
        return position / self.counts_per_unit

    def slider_position(self, value):
        return value * self.counts_per_unit


IMAGING_SLIDERS = {
    # The frame editor uses kHz and the scheduler uses Hz.
    "FrameRate": ImagingSliderSpec("frame_rate", 10000, 1000.0),
    "PMT": ImagingSliderSpec("PMT", model_scale=0.01),
    "Laser": ImagingSliderSpec("Laser", model_scale=0.01),
    "CalciumRise": ImagingSliderSpec("Ca_tau_rise_ms"),
    "CalciumDecay": ImagingSliderSpec("Ca_tau_decay_ms"),
    "CalciumJump": ImagingSliderSpec("SpikeRise", 100),
    "CalciumNoise": ImagingSliderSpec("NoiseScale", 10),
    "CalciumBaseline": ImagingSliderSpec("CalciumBaseline", 100),
    "kd": ImagingSliderSpec("DissociationConstant", 1000, preset_key="Kd_uM",
                            ticks=("1", "500", "1000")),
    "Hill": ImagingSliderSpec("HillCoef", 100, preset_key="hill_n",
                              ticks=("05", "075", "1")),
    "IndRise": ImagingSliderSpec("Ind_tau_rise_ms", preset_key="Ind_tau_rise_ms",
                                 ticks=("1", "2", "3")),
    "IndDecay": ImagingSliderSpec("Ind_tau_decay_ms", preset_key="Ind_tau_decay_ms",
                                  ticks=("1", "2", "3")),
    "DFF": ImagingSliderSpec("dff_max", 10, preset_key="dff_max", ticks=("1", "3", "2")),
    "FluoScale": ImagingSliderSpec("FluoScale", 10),
    "FluoOffset": ImagingSliderSpec("FluoOffset"),
    "FluoNoise": ImagingSliderSpec("FluoNoiseSigma", 5000),
    "PhotoShotNoise": ImagingSliderSpec("PhotoShotNoise", 1000000),
}
GECI_SLIDERS = {name: spec for name, spec in IMAGING_SLIDERS.items() if spec.preset_key}
GECI_RANGE_HEADROOM = 1.5


def bind_imaging_sliders(ui):
    """Bind the Designer sliders and editors before subscribing the model."""
    bindings = {}
    for name, spec in IMAGING_SLIDERS.items():
        prefix = f"Imaging_{name}"
        slider = getattr(ui, f"{prefix}_Slider")
        editor = getattr(ui, f"{prefix}_Readings")
        toggle = getattr(ui, f"{prefix}_toggleButton")
        if spec.preset_key:
            _expand_indicator_range(ui, prefix, slider, spec)
        binding = SliderBinding(
            slider=slider,
            editor=editor,
            active=toggle.isChecked(),
            disabled_text=None,
            disabled_editor_style=editor.styleSheet(),
            to_display=spec.display_value,
            to_slider=spec.slider_position,
            interval_ms=0,
        )
        toggle.toggled.connect(binding.set_active)
        bindings[name] = binding
    return bindings


def _expand_indicator_range(ui, prefix, slider, spec):
    """Allow headroom above the shipped presets and keep scale labels accurate."""
    positions = [spec.slider_position(preset[spec.preset_key]) for preset in GECI.values()]
    minimum = min(slider.minimum(), math.floor(min(positions)))
    maximum = max(slider.maximum(), math.ceil(max(positions) * GECI_RANGE_HEADROOM))
    if (minimum, maximum) == (slider.minimum(), slider.maximum()):
        return
    slider.setRange(minimum, maximum)
    for suffix, position in zip(spec.ticks, (minimum, (minimum + maximum) / 2, maximum)):
        label = getattr(ui, f"{prefix}_Value_{suffix}")
        label.setText(f"{spec.display_value(position):g}")


def apply_geci_defaults(bindings, preset):
    """Apply a preset as both the current value and the override reset value."""
    for name, spec in GECI_SLIDERS.items():
        binding = bindings[name]
        with QSignalBlocker(binding):
            binding.reconfigure(
                minimum=binding.slider.minimum(),
                maximum=binding.slider.maximum(),
                default_position=round(spec.slider_position(preset[spec.preset_key])),
            )
