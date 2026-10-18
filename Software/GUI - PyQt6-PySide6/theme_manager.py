"""
User-configurable colour theme and trace styling for the Spikeling GUI.

Scope
-----
Three independent colour surfaces are themed together:

1. **Interface** - window, panels, buttons and text. Driven by the application
   style sheet, a :class:`~PySide6.QtGui.QPalette`, and a substitution pass
   over the *inline* style sheets baked into the generated ``UI_*.py`` files
   (inline sheets win over the application sheet, so the pass is mandatory).
2. **Traces** - one colour per plotted signal, grouped per acquisition page
   (neuron interface / emulator, imaging, extracellular tetrode).
3. **Trace thickness** - a single pen width shared by every oscilloscope.

Mechanisms
----------
``Parameters_Settings.DarkSolarized`` is rewritten **in place**, so modules
that format colours from it at curve-construction time follow the theme.
Already-constructed curves are restyled by resolving each role's declared
target attribute on the live graph controllers, which avoids the colour
collisions that a purely colour-keyed substitution would create (the
extracellular channel 1 blue and the stimulus blue are the same literal but
must remain independently editable).

Persistence uses :class:`~PySide6.QtCore.QSettings`, so a theme survives an
application restart. Edits are staged and previewed live; only
:meth:`ThemeManager.apply_and_save` commits them to disk.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from PySide6.QtCore import QObject, QSettings, Signal
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QWidget

import Parameters_Settings as Settings


PALETTE_SIZE = 21
ORGANISATION = "Spikeling"
APPLICATION = "Spikeling GUI"
SETTINGS_KEY = "appearance/theme"

OSH_LOGO_RGB = [0, 153, 176]

# Trace pen width, in device-independent pixels.
DEFAULT_TRACE_WIDTH = 1.5
TRACE_WIDTH_MIN = 0.5
TRACE_WIDTH_MAX = 6.0
TRACE_WIDTH_STEP = 0.5

# Graph modules whose module-level ``PEN_WIDTH`` is kept in sync, so curves
# created after a width change are born with the right thickness.
PEN_WIDTH_MODULES = (
    "Graph_Spikeling", "Graph_Emulator", "Graph_Imaging", "Graph_ExtraCellular",
)

# Exact palette shipped with the project. The literals written into the
# generated UI files come from this table, so it is the matching key for the
# style-sheet substitution pass and must never be derived or mutated.
FACTORY_PALETTE: Tuple[Tuple[int, int, int], ...] = (
    (0, 30, 38), (0, 43, 54), (7, 54, 66),
    (220, 50, 47), (133, 153, 0), (38, 139, 210),
    (203, 75, 22), (42, 161, 152), (181, 137, 0), (108, 113, 196), (211, 54, 130),
    (88, 110, 117), (101, 123, 131), (131, 148, 150), (190, 205, 205),
    (238, 232, 213), (253, 246, 227),
    (0, 153, 176),
    (80, 110, 117),
    (168, 179, 179), (184, 193, 193),
)


# =============================================================================
# Roles
# =============================================================================
# =============================================================================
# Roles
# =============================================================================

SECTION_INTERFACE = "Interface"
SECTION_NEURON = "Neuron interface & emulator"
SECTION_IMAGING = "Imaging"
SECTION_EXTRACELLULAR = "Extracellular tetrode"
SECTION_ANALYSIS = "Data analysis"

SECTIONS: Tuple[str, ...] = (
    SECTION_INTERFACE, SECTION_NEURON, SECTION_IMAGING,
    SECTION_EXTRACELLULAR, SECTION_ANALYSIS,
)

# =============================================================================
# Plot item tagging
# =============================================================================
# Dynamically rebuilt plots (data analysis) cannot be reached by attribute
# path, so each item carries its role as a plain Python attribute instead.
TRACE_ROLE_ATTR = "_theme_role"
TRACE_WIDTH_SCALE_ATTR = "_theme_width_scale"
TRACE_MARKER_ATTR = "_theme_marker_only"
TRACE_STYLE_ATTR = "_theme_pen_style"

# Per-widget canvas override, so the analysis panels can keep the slightly
# lighter background that distinguishes them from the live oscilloscopes.
PLOT_BACKGROUND_ATTR = "_theme_background_role"

@dataclass(frozen=True)
class CurveTarget:
    """
    Location of one live plot item owned by a graph controller.

    Resolving a curve by *attribute path* rather than by its current colour is
    what keeps visually identical traces independently editable: the
    extracellular contact 1 pen and the stimulus pen ship with the same blue
    literal, but they belong to different roles and must not move together.

    Parameters
    ----------
    owner : str
        ``'window'`` for the main window itself, otherwise the attribute name
        of the controller held on it, one of ``'spikeling_graph'``,
        ``'imaging_graph'`` or ``'extracellular_graph'``.
    attribute : str
        Attribute holding the plot item on that owner.
    index : int, optional
        Element to take when ``attribute`` resolves to a list of items.

    Examples
    --------
    >>> CurveTarget("imaging_graph", "Fluocurve1")
    >>> CurveTarget("extracellular_graph", "channel_curves", 0)
    """

    owner: str
    attribute: str
    index: Optional[int] = None


@dataclass(frozen=True)
class ThemeRole:
    """
    One user-editable colour of the theme.

    A role binds a human-facing label to three optional consumers: a slot of
    the legacy ``Parameters_Settings.DarkSolarized`` palette, a set of live
    pyqtgraph items, and the shared trace-width setting. Roles with
    ``palette_index=None`` are deliberately decoupled from the legacy palette,
    which has fewer slots than the interface has distinguishable signals.

    Parameters
    ----------
    key : str
        Stable identifier used in the persisted JSON payload and in the
        preset dictionaries. Never rename an existing key: a saved theme is
        matched against it, and an unknown key silently falls back to the
        preset value.
    label : str
        Human-readable name shown next to the swatch on the Settings page.
    section : str
        Settings-page grouping, one of :data:`SECTIONS`.
    palette_index : int, optional
        Slot written into ``Parameters_Settings.DarkSolarized`` by
        :func:`build_palette`. ``None`` for roles that must stay independent
        of the legacy palette.
    targets : tuple of CurveTarget, optional
        Live plot items restyled by :meth:`ThemeManager.style_traces` on every
        repaint. Empty for pure interface roles.
    follows_width : bool, optional
        Whether the shared trace-thickness slider applies to this role.
        ``False`` keeps annotation items such as the detection-threshold line
        hairline, so thickening the signal traces does not turn a reference
        marker into a visual obstruction.

    Notes
    -----
    Frozen so that a role can be used as a dictionary key and so the module
    level :data:`THEME_ROLES` table cannot be mutated accidentally by a page
    controller holding a reference to one of its entries.

    Examples
    --------
    >>> ThemeRole("window_background", "Window background",
    ...           SECTION_INTERFACE, palette_index=0)
    >>> ThemeRole("imaging_fluo1", "Fluorescence 1", SECTION_IMAGING,
    ...           targets=(CurveTarget("imaging_graph", "Fluocurve1"),))
    """

    key: str
    label: str
    section: str
    palette_index: Optional[int] = None
    targets: Tuple[CurveTarget, ...] = field(default_factory=tuple)
    follows_width: bool = True


def _neuron_targets(index: int) -> Tuple[CurveTarget, ...]:
    """
    Return the emulator and hardware curves sharing one neuron channel.

    The emulator page and the hardware page plot the same eight-channel
    stream, so a single role drives both and the two scopes stay comparable
    at a glance.

    Parameters
    ----------
    index : int
        Channel index, ``0`` to ``6``, matching the ``curve{index}`` naming
        used by ``Graph_Spikeling`` and ``Graph_Emulator``.

    Returns
    -------
    tuple of CurveTarget
        The emulator curve followed by the hardware curve.
    """
    return (
        CurveTarget("window", f"Emulator_curve{index}"),
        CurveTarget("spikeling_graph", f"curve{index}"),
    )
# Palette slots 0-20 are the legacy ``Parameters_Settings.DarkSolarized``
# table. Only roles that a page reads back through that table declare a
# ``palette_index``; the rest are plot-only and stay independent of it,
# because the interface distinguishes more signals than the table has slots.
#
# ``palette_index`` is always passed by keyword: the positional form was a
# standing trap once ``section`` was inserted ahead of it.
THEME_ROLES: Tuple[ThemeRole, ...] = (
    # --- Interface --------------------------------------------------------
    ThemeRole("window_background", "Window background", SECTION_INTERFACE,
              palette_index=0),
    ThemeRole("panel_background", "Panel background", SECTION_INTERFACE,
              palette_index=1),
    ThemeRole("surface", "Buttons / surfaces", SECTION_INTERFACE,
              palette_index=2),
    ThemeRole("text_primary", "Primary text", SECTION_INTERFACE,
              palette_index=14),
    ThemeRole("text_muted", "Muted text / inactive", SECTION_INTERFACE,
              palette_index=11),

    # --- Neuron interface & emulator --------------------------------------
    # One role drives both scopes: they plot the same eight-channel stream,
    # so divergent colours would defeat side-by-side comparison.
    ThemeRole("neuron_vm", "Membrane potential", SECTION_NEURON,
              palette_index=3, targets=_neuron_targets(0)),
    ThemeRole("neuron_stimulus", "Stimulus", SECTION_NEURON,
              palette_index=5, targets=_neuron_targets(1)),
    ThemeRole("neuron_current", "Total input current", SECTION_NEURON,
              palette_index=4, targets=_neuron_targets(2)),
    ThemeRole("neuron_syn1_vm", "Synapse 1 Vm", SECTION_NEURON,
              palette_index=6, targets=_neuron_targets(3)),
    ThemeRole("neuron_syn1_input", "Synapse 1 input", SECTION_NEURON,
              palette_index=7, targets=_neuron_targets(4)),
    ThemeRole("neuron_syn2_vm", "Synapse 2 Vm", SECTION_NEURON,
              palette_index=8, targets=_neuron_targets(5)),
    ThemeRole("neuron_syn2_input", "Synapse 2 input", SECTION_NEURON,
              palette_index=10, targets=_neuron_targets(6)),

    # --- Imaging ----------------------------------------------------------
    ThemeRole("imaging_fluo1", "Fluorescence 1", SECTION_IMAGING,
              targets=(CurveTarget("imaging_graph", "Fluocurve1"),)),
    ThemeRole("imaging_fluo2", "Fluorescence 2", SECTION_IMAGING,
              targets=(CurveTarget("imaging_graph", "Fluocurve2"),)),
    ThemeRole("imaging_fluo3", "Fluorescence 3", SECTION_IMAGING,
              targets=(CurveTarget("imaging_graph", "Fluocurve3"),)),
    ThemeRole("imaging_calcium1", "Calcium 1", SECTION_IMAGING,
              targets=(CurveTarget("imaging_graph", "Calciumcurve1"),)),
    ThemeRole("imaging_calcium2", "Calcium 2", SECTION_IMAGING,
              targets=(CurveTarget("imaging_graph", "Calciumcurve2"),)),
    ThemeRole("imaging_calcium3", "Calcium 3", SECTION_IMAGING,
              targets=(CurveTarget("imaging_graph", "Calciumcurve3"),)),
    ThemeRole("imaging_vm1", "Vm 1", SECTION_IMAGING,
              targets=(CurveTarget("imaging_graph", "Vmcurve1"),)),
    ThemeRole("imaging_vm2", "Vm 2", SECTION_IMAGING,
              targets=(CurveTarget("imaging_graph", "Vmcurve2"),)),
    ThemeRole("imaging_vm3", "Vm 3", SECTION_IMAGING,
              targets=(CurveTarget("imaging_graph", "Vmcurve3"),)),
    ThemeRole("imaging_stimulus", "Stimulus", SECTION_IMAGING,
              targets=(CurveTarget("imaging_graph", "Stimcurve"),)),

    # --- Extracellular tetrode --------------------------------------------
    ThemeRole("extra_ch1", "Contact 1", SECTION_EXTRACELLULAR,
              targets=(CurveTarget("extracellular_graph", "channel_curves", 0),)),
    ThemeRole("extra_ch2", "Contact 2", SECTION_EXTRACELLULAR,
              targets=(CurveTarget("extracellular_graph", "channel_curves", 1),)),
    ThemeRole("extra_ch3", "Contact 3", SECTION_EXTRACELLULAR,
              targets=(CurveTarget("extracellular_graph", "channel_curves", 2),)),
    ThemeRole("extra_ch4", "Contact 4", SECTION_EXTRACELLULAR,
              targets=(CurveTarget("extracellular_graph", "channel_curves", 3),)),

    # --- Data analysis ----------------------------------------------------
    # Tag-driven roles: the analysis page rebuilds its curves on every button
    # press, so they are reached through ``_theme_role`` item tags rather than
    # through a fixed attribute path. Signal colours (Vm, currents, stimulus)
    # are deliberately *not* duplicated here: an analysis trace must be the
    # same colour as the live trace it was recorded from.
    ThemeRole("analysis_spike_rate", "Spike rate", SECTION_ANALYSIS),
    ThemeRole("analysis_loop", "Single repetitions", SECTION_ANALYSIS),

    # Annotation line: excluded from the thickness slider so widening the
    # signal traces never turns the reference marker into an obstruction.
    ThemeRole("extra_threshold", "Detection threshold", SECTION_EXTRACELLULAR,
              targets=tuple(CurveTarget("extracellular_graph",
                                        "channel_threshold_lines", k)
                            for k in range(4)),
              follows_width=False),
)

ROLES_BY_KEY: Dict[str, ThemeRole] = {role.key: role for role in THEME_ROLES}

# Extracellular contact colours, mirrored into ``Graph_ExtraCellular`` so the
# four stacked plots are *built* with the themed colours on the next connect.
EXTRACELLULAR_CHANNEL_KEYS = ("extra_ch1", "extra_ch2", "extra_ch3", "extra_ch4")


# =============================================================================
# Presets
# =============================================================================

DARK_THEME: Dict[str, str] = {
    "window_background": "#001E26",
    "panel_background": "#002B36",
    "surface": "#073642",
    "text_primary": "#BECDCD",
    "text_muted": "#586E75",

    "neuron_vm": "#DC322F",
    "neuron_stimulus": "#268BD2",
    "neuron_current": "#859900",
    "neuron_syn1_vm": "#CB4B16",
    "neuron_syn1_input": "#2AA198",
    "neuron_syn2_vm": "#B58900",
    "neuron_syn2_input": "#D33682",

    "imaging_fluo1": "#859900",
    "imaging_fluo2": "#00FF85",
    "imaging_fluo3": "#85FF00",
    "imaging_calcium1": "#D33682",
    "imaging_calcium2": "#6C71C4",
    "imaging_calcium3": "#2AA198",
    "imaging_vm1": "#DC322F",
    "imaging_vm2": "#CB4B16",
    "imaging_vm3": "#B58900",
    "imaging_stimulus": "#268BD2",

    "extra_ch1": "#268BD2",
    "extra_ch2": "#2AA198",
    "extra_ch3": "#859900",
    "extra_ch4": "#6C71C4",
    "extra_threshold": "#B58900",

    "analysis_spike_rate": "#BECDCD",
    "analysis_loop": "#586E75",
}

LIGHT_THEME: Dict[str, str] = {
    "window_background": "#FDF6E3",
    "panel_background": "#EEE8D5",
    "surface": "#DDD6C1",
    "text_primary": "#073642",
    "text_muted": "#8A9A9A",

    "neuron_vm": "#C32C29",
    "neuron_stimulus": "#1C6FA8",
    "neuron_current": "#6B7A00",
    "neuron_syn1_vm": "#B5410F",
    "neuron_syn1_input": "#1E8880",
    "neuron_syn2_vm": "#9B7600",
    "neuron_syn2_input": "#B82E6F",

    "imaging_fluo1": "#5F6C00",
    "imaging_fluo2": "#00A355",
    "imaging_fluo3": "#5F9E00",
    "imaging_calcium1": "#B82E6F",
    "imaging_calcium2": "#5A5FB0",
    "imaging_calcium3": "#1E8880",
    "imaging_vm1": "#C32C29",
    "imaging_vm2": "#B5410F",
    "imaging_vm3": "#9B7600",
    "imaging_stimulus": "#1C6FA8",

    "extra_ch1": "#1C6FA8",
    "extra_ch2": "#1E8880",
    "extra_ch3": "#6B7A00",
    "extra_ch4": "#5A5FB0",
    "extra_threshold": "#9B7600",

    "analysis_spike_rate": "#3C5054",
    "analysis_loop": "#A8B3B3",
}

PRESETS: Dict[str, Dict[str, str]] = {"dark": DARK_THEME, "light": LIGHT_THEME}
DEFAULT_MODE = "dark"


# =============================================================================
# Colour helpers
# =============================================================================

def to_rgb(colour) -> List[int]:
    """Convert a colour string or sequence to an ``[r, g, b]`` list."""
    if isinstance(colour, (list, tuple)):
        return [int(colour[0]), int(colour[1]), int(colour[2])]
    qcolour = QColor(colour)
    if not qcolour.isValid():
        qcolour = QColor("#000000")
    return [qcolour.red(), qcolour.green(), qcolour.blue()]


def to_hex(colour) -> str:
    """Convert a colour string or ``(r, g, b)`` sequence to ``'#RRGGBB'``."""
    r, g, b = to_rgb(colour)
    return QColor(r, g, b).name()


def mix(colour_a, colour_b, weight: float) -> str:
    """
    Linearly interpolate two colours in sRGB.

    Parameters
    ----------
    colour_a, colour_b : str or sequence of int
        Endpoint colours.
    weight : float
        ``0`` returns ``colour_a``, ``1`` returns ``colour_b``.

    Returns
    -------
    str
        ``'#RRGGBB'``.
    """
    a, b = QColor(to_hex(colour_a)), QColor(to_hex(colour_b))
    t = min(max(float(weight), 0.0), 1.0)
    return QColor(
        round(a.red() + (b.red() - a.red()) * t),
        round(a.green() + (b.green() - a.green()) * t),
        round(a.blue() + (b.blue() - a.blue()) * t),
    ).name()


def is_dark(colour) -> bool:
    """Return ``True`` when a colour needs a light foreground on top of it."""
    return QColor(to_hex(colour)).lightnessF() < 0.5


def contrast_of(colour) -> str:
    """Return a readable foreground colour for the given background."""
    return "#F5F7F7" if is_dark(colour) else "#0B2B33"

def _validate_theme_roles() -> None:
    """
    Check the role table at import time.

    Catches the three mistakes that are otherwise only visible as a confusing
    failure deep inside :func:`build_palette` or :meth:`ThemeManager.load`:
    a positional argument landing in the wrong field, a duplicated palette
    slot, and a preset that does not cover every role.

    Raises
    ------
    TypeError
        If a role carries a non-integer ``palette_index``, which is what
        happens when the table is written against an outdated field order.
    ValueError
        If two roles claim the same palette slot, if a slot is out of range,
        or if a preset is missing a role key.
    """
    seen_slots: Dict[int, str] = {}

    for role in THEME_ROLES:
        if role.section not in SECTIONS:
            raise ValueError(
                f"Role '{role.key}' declares unknown section {role.section!r}. "
                f"Expected one of {SECTIONS}. Arguments are "
                f"(key, label, section, palette_index=...)."
            )

        if role.palette_index is None:
            continue

        if not isinstance(role.palette_index, int) or isinstance(role.palette_index, bool):
            raise TypeError(
                f"Role '{role.key}' has palette_index={role.palette_index!r}, "
                f"which is not an int. The field order is "
                f"(key, label, section, palette_index); pass the slot by "
                f"keyword, e.g. ThemeRole('{role.key}', '{role.label}', "
                f"{role.section!r}, palette_index=0)."
            )

        if not 0 <= role.palette_index < PALETTE_SIZE:
            raise ValueError(
                f"Role '{role.key}' targets palette slot {role.palette_index}, "
                f"outside the valid range 0..{PALETTE_SIZE - 1}."
            )

        previous = seen_slots.get(role.palette_index)
        if previous is not None:
            raise ValueError(
                f"Roles '{previous}' and '{role.key}' both claim palette slot "
                f"{role.palette_index}; one would silently overwrite the other."
            )
        seen_slots[role.palette_index] = role.key

    for preset_name, preset in PRESETS.items():
        missing = [role.key for role in THEME_ROLES if role.key not in preset]
        if missing:
            raise ValueError(
                f"Preset '{preset_name}' is missing colours for: "
                f"{', '.join(missing)}."
            )


def build_palette(colours: Dict[str, str]) -> List[List[int]]:
    """
    Expand the editable roles into the full 21-slot legacy palette.

    Slots not exposed on the Settings page (intermediate greys, the toggle
    knob, disabled frames) are *derived* from the window, panel, text and
    muted roles. One formula therefore serves a dark and a light base: the
    toggle knob is pulled towards white on a dark window and towards near
    black on a light one, so it never disappears into its own track.

    Parameters
    ----------
    colours : dict
        ``{role_key: '#RRGGBB'}`` covering every entry of :data:`THEME_ROLES`.

    Returns
    -------
    list of list of int
        Palette compatible with ``Parameters_Settings.DarkSolarized``, with
        all :data:`PALETTE_SIZE` slots populated.

    Raises
    ------
    KeyError
        If ``colours`` omits a role key, which would otherwise leave a slot
        black and silently wreck the contrast of one widget family.
    """
    missing = [role.key for role in THEME_ROLES if role.key not in colours]
    if missing:
        raise KeyError(f"build_palette is missing colours for: {', '.join(missing)}")

    window = colours["window_background"]
    panel = colours["panel_background"]
    text = colours["text_primary"]
    muted = colours["text_muted"]
    knob = contrast_of(window)

    palette: List[Optional[List[int]]] = [None] * PALETTE_SIZE

    for role in THEME_ROLES:
        if role.palette_index is not None:
            palette[role.palette_index] = to_rgb(colours[role.key])

    # Slot 9 has no interface owner. The imaging secondary indicator is its
    # only semantic user, so it keeps the slot defined for legacy readers.
    palette[9] = to_rgb(colours["imaging_calcium2"])

    palette[12] = to_rgb(mix(muted, text, 0.33))
    palette[13] = to_rgb(mix(muted, text, 0.66))
    palette[15] = to_rgb(mix(window, knob, 0.92))
    palette[16] = to_rgb(mix(window, knob, 0.98))
    palette[17] = list(OSH_LOGO_RGB)
    palette[18] = to_rgb(mix(panel, window, 0.50))
    palette[19] = to_rgb(mix(muted, text, 0.80))
    palette[20] = to_rgb(mix(muted, text, 0.90))

    unset = [index for index, value in enumerate(palette) if value is None]
    if unset:
        raise ValueError(f"Palette slots left undefined by the role table: {unset}")

    return [list(entry) for entry in palette]


_validate_theme_roles()


# =============================================================================
# Inline style sheet re-theming
# =============================================================================

_RGBA_PATTERN = re.compile(
    r"rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*(?:,\s*([\d.]+)\s*)?\)"
)
_HEX_PATTERN = re.compile(r"#([0-9a-fA-F]{6})\b")

_SOURCE_PROPERTY = "_theme_source_qss"
_OUTPUT_PROPERTY = "_theme_output_qss"


class WidgetRetheme:
    """
    Rewrite factory colour literals inside inline widget style sheets.

    Each widget's *original* sheet is cached in a dynamic Qt property the
    first time it is seen, so repeated theme changes re-derive from the
    pristine source instead of compounding substitutions. A sheet replaced at
    runtime by application code (record buttons, patch-clamp mode switches) is
    detected by comparing against the previously produced output and is
    re-cached rather than silently reverted.

    Parameters
    ----------
    palette : sequence of sequence of int
        Active 21-slot palette.
    extra : dict, optional
        Additional ``(r, g, b) -> '#RRGGBB'`` overrides applied on top of the
        factory-palette mapping.
    """

    def __init__(self, palette, extra: Optional[Dict[Tuple[int, int, int], str]] = None) -> None:
        self._lookup: Dict[Tuple[int, int, int], str] = {
            tuple(rgb): to_hex(palette[index]) for index, rgb in enumerate(FACTORY_PALETTE)
        }
        if extra:
            self._lookup.update({tuple(key): value for key, value in extra.items()})

    def substitute(self, stylesheet: str) -> str:
        """
        Return ``stylesheet`` with every known colour literal remapped.

        Parameters
        ----------
        stylesheet : str
            Source QSS fragment.

        Returns
        -------
        str
            Re-themed QSS; ``rgba(...)`` alpha components are preserved.
        """
        def replace_rgb(match: re.Match) -> str:
            key = (int(match.group(1)), int(match.group(2)), int(match.group(3)))
            target = self._lookup.get(key)
            if target is None:
                return match.group(0)
            r, g, b = to_rgb(target)
            alpha = match.group(4)
            return f"rgba({r}, {g}, {b}, {alpha})" if alpha else f"rgb({r}, {g}, {b})"

        def replace_hex(match: re.Match) -> str:
            value = match.group(1)
            key = (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16))
            target = self._lookup.get(key)
            return target.upper() if target else match.group(0)

        return _HEX_PATTERN.sub(replace_hex, _RGBA_PATTERN.sub(replace_rgb, stylesheet))

    def apply_to_tree(self, root: QWidget) -> None:
        """
        Re-theme ``root`` and every descendant carrying an inline style sheet.

        Parameters
        ----------
        root : PySide6.QtWidgets.QWidget
            Subtree to process, typically a top-level window.
        """
        for widget in [root] + root.findChildren(QWidget):
            try:
                current = widget.styleSheet()
            except RuntimeError:          # underlying C++ object deleted
                continue

            source = widget.property(_SOURCE_PROPERTY)
            produced = widget.property(_OUTPUT_PROPERTY)

            if source is None or (produced is not None and current != produced):
                source = current
                widget.setProperty(_SOURCE_PROPERTY, source)

            if not source:
                continue

            output = self.substitute(source)
            if output != current:
                widget.setStyleSheet(output)
            widget.setProperty(_OUTPUT_PROPERTY, output)

# =============================================================================
# Staged state
# =============================================================================

@dataclass
class ThemeState:
    """
    A complete, self-contained description of the appearance.

    Two instances are held at all times: the *active* one, which is painted
    and persisted, and the *pending* one, which the Settings page edits. The
    separation is what allows an explicit Apply step: nothing in the running
    interface reads the pending state, so editing it is free.

    Attributes
    ----------
    mode : str
        ``'dark'``, ``'light'`` or ``'custom'``.
    colours : dict
        ``{role_key: '#RRGGBB'}`` covering every entry of :data:`THEME_ROLES`.
    trace_width : float
        Pen width in pixels shared by every oscilloscope trace.
    """

    mode: str
    colours: Dict[str, str]
    trace_width: float

    def copy(self) -> "ThemeState":
        """Return an independent copy, safe to mutate."""
        return ThemeState(self.mode, dict(self.colours), self.trace_width)

    def matches(self, other: "ThemeState") -> bool:
        """Return ``True`` when two states are visually identical."""
        return (
            self.mode == other.mode
            and self.colours == other.colours
            and abs(self.trace_width - other.trace_width) < 1e-9
        )

    def to_payload(self) -> dict:
        """Return the JSON-serialisable form written to disk."""
        return {
            "mode": self.mode,
            "trace_width": self.trace_width,
            "colours": self.colours,
        }


def default_state(mode: str = DEFAULT_MODE) -> ThemeState:
    """Build a :class:`ThemeState` from one of the built-in presets."""
    preset = PRESETS.get(mode, DARK_THEME)
    return ThemeState(mode if mode in PRESETS else DEFAULT_MODE,
                      dict(preset), DEFAULT_TRACE_WIDTH)


# =============================================================================
# Theme manager
# =============================================================================

class ThemeManager(QObject):
    """
    Single source of truth for the application colours and trace width.

    Two-stage model
    ---------------
    Editing methods (:meth:`set_colour`, :meth:`set_mode`,
    :meth:`set_trace_width`, :meth:`import_from`) mutate the **pending** state
    only and emit :attr:`pendingChanged`. They never touch a widget, which is
    why dragging the thickness slider is now instantaneous: a repaint rebuilds
    the global style sheet, walks every widget for inline-sheet substitution
    and re-pens every curve, work that must not run once per slider tick.

    :meth:`apply_and_save` promotes the pending state to **active**, persists
    it and triggers exactly one repaint. The Settings page previews the
    pending values locally — swatch fills and a sample trace — so the user
    still sees their choices before committing them.

    Parameters
    ----------
    organisation, application : str, optional
        :class:`~PySide6.QtCore.QSettings` scope used for persistence.
    parent : PySide6.QtCore.QObject, optional
        Qt parent.

    Attributes
    ----------
    themeChanged : Signal(str, dict)
        Emitted with ``(mode, colours)`` after the active theme is repainted.
    pendingChanged : Signal(bool)
        Emitted on every staged edit, carrying the current dirty flag.
    """

    themeChanged = Signal(str, dict)
    pendingChanged = Signal(bool)

    def __init__(self, organisation: str = ORGANISATION,
                 application: str = APPLICATION, parent=None) -> None:
        super().__init__(parent)
        self._settings = QSettings(organisation, application)
        self._active: ThemeState = default_state()
        self._pending: ThemeState = self._active.copy()

        self._app = None
        self._main_window: Optional[QWidget] = None
        self._windows: List[QWidget] = []
        self._toggles: List[Tuple[object, int, int, int]] = []

        self.load()

    # ------------------------------------------------------------------
    # Pending state (read by the Settings page)
    # ------------------------------------------------------------------

    @property
    def mode(self) -> str:
        """Pending preset name: ``'dark'``, ``'light'`` or ``'custom'``."""
        return self._pending.mode

    @property
    def colours(self) -> Dict[str, str]:
        """Copy of the pending ``{role_key: '#RRGGBB'}`` mapping."""
        return dict(self._pending.colours)

    @property
    def trace_width(self) -> float:
        """Pending pen width, in pixels."""
        return self._pending.trace_width

    @property
    def is_dirty(self) -> bool:
        """``True`` when the pending state differs from the active one."""
        return not self._pending.matches(self._active)

    def colour(self, role_key: str) -> str:
        """Return the pending colour of one role."""
        return self._pending.colours.get(role_key, "#000000")

    # ------------------------------------------------------------------
    # Active state (read by every renderer)
    # ------------------------------------------------------------------

    @property
    def active_mode(self) -> str:
        """Preset name currently painted and stored."""
        return self._active.mode

    @property
    def active_trace_width(self) -> float:
        """Pen width currently painted and stored, in pixels."""
        return self._active.trace_width

    def active_colour(self, role_key: str) -> str:
        """Return the painted colour of one role, for interface chrome."""
        return self._active.colours.get(role_key, "#000000")

    def palette(self) -> List[List[int]]:
        """Return the 21-slot legacy palette built from the active state."""
        return build_palette(self._active.colours)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def load(self) -> None:
        """
        Restore the stored theme, falling back to the dark preset.

        A partial or malformed payload is repaired role by role rather than
        discarded, so adding a role in a later version cannot invalidate a
        user's saved palette.
        """
        payload = self._settings.value(SETTINGS_KEY, "")
        data: dict = {}
        if payload:
            try:
                data = json.loads(payload)
            except (TypeError, ValueError):
                data = {}

        self._active = self._state_from_payload(data, default_state())
        self._pending = self._active.copy()
        self._push_palette()
        self._patch_module_constants()

    def apply_and_save(self) -> None:
        """Promote the pending state to active, persist it and repaint once."""
        self._active = self._pending.copy()
        self._settings.setValue(
            SETTINGS_KEY, json.dumps(self._active.to_payload(), indent=2))
        self._settings.sync()
        self.repaint()
        self.pendingChanged.emit(False)

    def export_to(self, path: str) -> None:
        """
        Write the pending state to a standalone ``.json`` file.

        The pending state is exported rather than the active one so that
        "tweak, export, share" works without first committing the theme to
        the local machine.
        """
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(self._pending.to_payload(), handle, indent=2)

    def import_from(self, path: str) -> None:
        """
        Stage a theme written by :meth:`export_to`.

        The file is loaded into the pending state only; :meth:`apply_and_save`
        still has to run, so an imported theme can be inspected in the
        Settings page and rejected without ever repainting the interface.
        """
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)

        self._pending = self._state_from_payload(data, self._pending)
        self.pendingChanged.emit(self.is_dirty)

    def _state_from_payload(self, data: dict, fallback: ThemeState) -> ThemeState:
        """
        Build a :class:`ThemeState` from a persisted or imported payload.

        Parameters
        ----------
        data : dict
            Raw payload; may be empty, partial or malformed.
        fallback : ThemeState
            State supplying any colour the payload does not define.

        Returns
        -------
        ThemeState
            Fully populated state.
        """
        mode = str(data.get("mode", fallback.mode))
        colours = dict(PRESETS.get(mode, fallback.colours))
        stored = data.get("colours", {}) or {}

        for role in THEME_ROLES:
            value = stored.get(role.key)
            if value and QColor(value).isValid():
                colours[role.key] = to_hex(value)
            elif role.key not in colours:
                colours[role.key] = fallback.colours.get(role.key, "#000000")

        if mode not in PRESETS and mode != "custom":
            mode = DEFAULT_MODE

        return ThemeState(mode, colours,
                          self._clamp_width(data.get("trace_width", fallback.trace_width)))

    @staticmethod
    def _clamp_width(value) -> float:
        """Coerce a stored width to the supported range."""
        try:
            width = float(value)
        except (TypeError, ValueError):
            return DEFAULT_TRACE_WIDTH
        return min(max(width, TRACE_WIDTH_MIN), TRACE_WIDTH_MAX)

    # ------------------------------------------------------------------
    # Staged mutation (no repaint)
    # ------------------------------------------------------------------

    def set_mode(self, mode: str) -> None:
        """Stage a built-in preset without repainting."""
        mode = str(mode).strip().lower()
        if mode not in PRESETS:
            return
        self._pending = ThemeState(mode, dict(PRESETS[mode]), self._pending.trace_width)
        self.pendingChanged.emit(self.is_dirty)

    def set_colour(self, role_key: str, colour: str) -> None:
        """
        Stage one role colour without repainting.

        The mode flips to ``'custom'`` immediately, so the selector stops
        advertising a preset the pending palette no longer matches, even
        though nothing has been applied yet.
        """
        if role_key not in ROLES_BY_KEY:
            return
        qcolour = QColor(colour)
        if not qcolour.isValid():
            return

        self._pending.colours[role_key] = qcolour.name()
        self._pending.mode = "custom"
        self.pendingChanged.emit(self.is_dirty)

    def set_trace_width(self, width: float) -> None:
        """Stage a new pen width without repainting."""
        width = self._clamp_width(width)
        if abs(width - self._pending.trace_width) < 1e-9:
            return
        self._pending.trace_width = width
        self.pendingChanged.emit(self.is_dirty)

    def discard_changes(self) -> None:
        """Drop every staged edit and return to the applied theme."""
        self._pending = self._active.copy()
        self.pendingChanged.emit(False)

    def reset(self) -> None:
        """Stage the factory dark theme and apply it immediately."""
        self._pending = default_state()
        self.apply_and_save()

    # ------------------------------------------------------------------
    # Painting
    # ------------------------------------------------------------------

    def bind(self, app=None, window=None, main_window=None) -> None:
        """
        Register the targets restyled on every repaint.

        Parameters
        ----------
        app : PySide6.QtWidgets.QApplication, optional
            Target of the global style sheet and :class:`QPalette`.
        window : PySide6.QtWidgets.QWidget, optional
            Top-level widget scanned for inline sheets, plots and toggles.
            Call once per window (main, advanced parameters, tetrode).
        main_window : PySide6.QtWidgets.QWidget, optional
            Window owning the graph controllers; also registered as a window.
        """
        if app is not None:
            self._app = app
        if main_window is not None:
            self._main_window = main_window
            window = window or main_window
        if window is not None and window not in self._windows:
            self._windows.append(window)
            self._register_toggles(window)

    def repaint(self, app=None, window=None, main_window=None) -> None:
        """
        Push the **active** theme everywhere and notify listeners.

        Parameters
        ----------
        app, window, main_window : optional
            Same meaning as in :meth:`bind`; supplying them also binds them.
        """
        self.bind(app, window, main_window)
        self._push_palette()
        self._patch_module_constants()

        if self._app is not None:
            self._app.setStyleSheet(self.stylesheet())
            self._app.setPalette(self.qpalette())

        retheme = WidgetRetheme(Settings.DarkSolarized, self._extra_literals())
        for widget in list(self._windows):
            try:
                retheme.apply_to_tree(widget)
            except RuntimeError:
                self._windows.remove(widget)

        self._restyle_plot_widgets()
        self._restyle_toggles()
        self.style_traces()

        self.themeChanged.emit(self._active.mode, dict(self._active.colours))

    # Backwards-compatible alias used by the start-up wiring.
    apply = repaint

    def _push_palette(self) -> None:
        """Rewrite ``Parameters_Settings.DarkSolarized`` in place."""
        Settings.DarkSolarized[:] = self.palette()

    def _extra_literals(self) -> Dict[Tuple[int, int, int], str]:
        """Map non-palette literals used by the pages onto theme colours."""
        return {
            (250, 250, 250): contrast_of(self._active.colours["neuron_vm"]),
        }

    def _patch_module_constants(self) -> None:
        """
        Mirror the active theme into the graph modules' constants.

        Curves are constructed from these constants, so patching them means a
        page connected *after* an apply is already correct without relying on
        the per-module hook.
        """
        for name in PEN_WIDTH_MODULES:
            module = sys.modules.get(name)
            if module is not None:
                module.PEN_WIDTH = self._active.trace_width

        extracellular = sys.modules.get("Graph_ExtraCellular")
        if extracellular is not None and hasattr(extracellular, "CHANNEL_COLORS"):
            extracellular.CHANNEL_COLORS[:] = [
                tuple(to_rgb(self._active.colours[key]))
                for key in EXTRACELLULAR_CHANNEL_KEYS
            ]

    # ------------------------------------------------------------------
    # Global style sheet and palette
    # ------------------------------------------------------------------

    def qpalette(self) -> QPalette:
        """
        Build the :class:`QPalette` used by non-stylable native elements.

        Returns
        -------
        PySide6.QtGui.QPalette
            Palette covering window, base, text, button and highlight roles.
        """
        c = self._active.colours
        accent = QColor(c["neuron_stimulus"])
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(c["window_background"]))
        palette.setColor(QPalette.WindowText, QColor(c["text_primary"]))
        palette.setColor(QPalette.Base, QColor(c["panel_background"]))
        palette.setColor(QPalette.AlternateBase, QColor(c["surface"]))
        palette.setColor(QPalette.Text, QColor(c["text_primary"]))
        palette.setColor(QPalette.PlaceholderText, QColor(c["text_muted"]))
        palette.setColor(QPalette.Button, QColor(c["surface"]))
        palette.setColor(QPalette.ButtonText, QColor(c["text_primary"]))
        palette.setColor(QPalette.ToolTipBase, QColor(c["panel_background"]))
        palette.setColor(QPalette.ToolTipText, QColor(c["text_primary"]))
        palette.setColor(QPalette.Highlight, accent)
        palette.setColor(QPalette.HighlightedText, QColor(contrast_of(accent.name())))
        palette.setColor(QPalette.Disabled, QPalette.Text, QColor(c["text_muted"]))
        palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(c["text_muted"]))
        palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(c["text_muted"]))
        return palette

    def stylesheet(self) -> str:
        """
        Build the application-wide QSS for the active palette.

        Notes
        -----
        :class:`~PySide6.QtWidgets.QGroupBox` derives from
        :class:`~PySide6.QtWidgets.QFrame`, so the transparent-frame rule also
        matches it and, at equal selector specificity, Qt lets the last rule
        win. The group-box rules are therefore written with an attribute
        selector (``QGroupBox[themeBox="true"]``), which outranks a plain type
        selector and guarantees the border and title are drawn.

        Returns
        -------
        str
            Style sheet covering the generic widget classes. Widgets carrying
            an inline sheet are handled by :class:`WidgetRetheme`.
        """
        c = self._active.colours
        window = c["window_background"]
        panel = c["panel_background"]
        surface = c["surface"]
        text = c["text_primary"]
        muted = c["text_muted"]
        accent = c["neuron_stimulus"]
        on_accent = contrast_of(accent)
        hover = mix(surface, text, 0.18)
        pressed = mix(surface, text, 0.32)
        border = mix(panel, text, 0.30)

        return f"""
        QWidget {{ background-color: {window}; color: {text}; }}
        QMainWindow, QDialog, QMessageBox, QInputDialog, QFileDialog {{
            background-color: {window}; color: {text};
        }}
        QFrame, QStackedWidget, QScrollArea, QTabWidget::pane {{
            background-color: transparent; color: {text};
        }}
        QLabel {{ background-color: transparent; color: {text}; }}
        QToolTip {{
            background-color: {panel}; color: {text};
            border: 1px solid {border}; padding: 4px;
        }}
        QPushButton {{
            background-color: {surface}; color: {text};
            border: 1px solid {border}; border-radius: 6px; padding: 4px 10px;
        }}
        QPushButton:hover {{ background-color: {hover}; }}
        QPushButton:pressed {{ background-color: {pressed}; }}
        QPushButton:checked {{ background-color: {accent}; color: {on_accent}; }}
        QPushButton:disabled {{ color: {muted}; border-color: {muted}; }}
        QComboBox, QLineEdit, QSpinBox, QDoubleSpinBox, QPlainTextEdit, QTextEdit {{
            background-color: {panel}; color: {text};
            border: 1px solid {border}; border-radius: 5px; padding: 2px 6px;
            selection-background-color: {accent}; selection-color: {on_accent};
        }}
        QComboBox QAbstractItemView {{
            background-color: {panel}; color: {text};
            selection-background-color: {accent}; selection-color: {on_accent};
            border: 1px solid {border};
        }}
        QGroupBox[themeBox="true"] {{
            background-color: {panel};
            border: 1px solid {border};
            border-radius: 8px;
            margin-top: 16px;
            padding: 14px 12px 12px 12px;
        }}
        QGroupBox[themeBox="true"]::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 14px; padding: 2px 8px;
            background-color: {surface};
            border: 1px solid {border};
            border-radius: 5px;
            color: {text};
            font: 700 10pt;
        }}
        QScrollBar:vertical, QScrollBar:horizontal {{
            background: {panel}; border: none; width: 10px; height: 10px;
        }}
        QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{
            background: {muted}; border-radius: 5px; min-height: 24px; min-width: 24px;
        }}
        QScrollBar::add-line, QScrollBar::sub-line {{ height: 0px; width: 0px; }}
        QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
        QCheckBox, QRadioButton {{ background-color: transparent; color: {text}; }}
        QHeaderView::section, QTableView, QListView, QTreeView {{
            background-color: {panel}; color: {text}; border: 1px solid {border};
        }}
        QMenu {{ background-color: {panel}; color: {text}; border: 1px solid {border}; }}
        QMenu::item:selected {{ background-color: {accent}; color: {on_accent}; }}
        """

    # ------------------------------------------------------------------
    # Live restyling: plots, traces, toggles
    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    # Themed pens, brushes and item tagging
    # ------------------------------------------------------------------

    def pen(self, role_key: str, width_scale: float = 1.0, style=None):
        """
        Build a pyqtgraph pen for one role at the active width.

        Parameters
        ----------
        role_key : str
            Entry of :data:`THEME_ROLES`.
        width_scale : float, optional
            Multiplier on the global trace width. Used to emphasise a mean
            trace over the individual repetitions drawn behind it, so the
            contrast between them survives any thickness setting.
        style : PySide6.QtCore.Qt.PenStyle, optional
            Dash pattern; solid when omitted.

        Returns
        -------
        pyqtgraph.functions.mkPen
            Cosmetic pen, so the stroke width stays constant under zoom.
        """
        import pyqtgraph as pg

        role = ROLES_BY_KEY.get(role_key)
        base = self._active.trace_width if (role is None or role.follows_width) else 1.0
        pen = pg.mkPen(self.active_colour(role_key),
                       width=max(0.1, base * float(width_scale)), cosmetic=True)
        if style is not None:
            pen.setStyle(style)
        return pen

    def brush(self, role_key: str):
        """Build a pyqtgraph brush for one role."""
        import pyqtgraph as pg
        return pg.mkBrush(self.active_colour(role_key))

    def tag_item(self, item, role_key: str, width_scale: float = 1.0,
                 marker_only: bool = False, style=None):
        """
        Mark a plot item so later theme changes can restyle it.

        Parameters
        ----------
        item : pyqtgraph.GraphicsObject
            Curve, scatter or line to tag.
        role_key : str
            Entry of :data:`THEME_ROLES`.
        width_scale : float, optional
            Multiplier on the global trace width.
        marker_only : bool, optional
            ``True`` for symbol-only items. The line pen is then left
            untouched: calling ``setPen`` on an item created with ``pen=None``
            would join every marker with a spurious connecting line.
        style : PySide6.QtCore.Qt.PenStyle, optional
            Dash pattern to preserve across restyles.

        Returns
        -------
        pyqtgraph.GraphicsObject
            The same item, for call chaining.
        """
        setattr(item, TRACE_ROLE_ATTR, role_key)
        setattr(item, TRACE_WIDTH_SCALE_ATTR, float(width_scale))
        setattr(item, TRACE_MARKER_ATTR, bool(marker_only))
        if style is not None:
            setattr(item, TRACE_STYLE_ATTR, style)
        return item

    def themed_plot(self, plot_widget, x, y, role_key: str, width_scale: float = 1.0,
                    symbol: Optional[str] = None, symbol_size: int = 5, **kwargs):
        """
        Plot a curve or marker set already bound to a theme role.

        Parameters
        ----------
        plot_widget : pyqtgraph.PlotWidget
            Destination widget.
        x, y : array_like
            Sample coordinates.
        role_key : str
            Entry of :data:`THEME_ROLES` supplying colour and width.
        width_scale : float, optional
            Multiplier on the global trace width.
        symbol : str, optional
            pyqtgraph symbol code. When given, the item is drawn as markers
            only, with no connecting line.
        symbol_size : int, optional
            Marker size in pixels.
        **kwargs
            Forwarded to :meth:`pyqtgraph.PlotWidget.plot`, e.g.
            ``connect='finite'``.

        Returns
        -------
        pyqtgraph.PlotDataItem
            The tagged item.
        """
        colour = self.active_colour(role_key)

        if symbol is not None:
            item = plot_widget.plot(x=x, y=y, pen=None, symbol=symbol,
                                    symbolSize=symbol_size,
                                    symbolBrush=self.brush(role_key),
                                    symbolPen=colour, **kwargs)
            return self.tag_item(item, role_key, width_scale, marker_only=True)

        item = plot_widget.plot(x=x, y=y, pen=self.pen(role_key, width_scale), **kwargs)
        return self.tag_item(item, role_key, width_scale)

    def set_plot_background_role(self, plot_widget, role_key: str) -> None:
        """
        Bind a plot canvas to a background role other than the window colour.

        Parameters
        ----------
        plot_widget : pyqtgraph.PlotWidget
            Target widget.
        role_key : str
            Interface role supplying the canvas colour, typically
            ``'panel_background'``.
        """
        setattr(plot_widget, PLOT_BACKGROUND_ATTR, role_key)
        plot_widget.setBackground(QColor(self.active_colour(role_key)))

    # ------------------------------------------------------------------
    # Live restyling: plots, traces, toggles
    # ------------------------------------------------------------------

    def _restyle_plot_widgets(self) -> None:
        """
        Recolour every pyqtgraph canvas, axis line and tick label.

        The axis pen must follow the theme as well as the canvas: a light
        background keeping the default light axis pen leaves the time base
        invisible. A widget tagged through :meth:`set_plot_background_role`
        keeps its own canvas role, so the analysis panels stay visually
        separated from the live oscilloscopes in both modes.
        """
        try:
            import pyqtgraph as pg
        except ImportError:
            return

        default_background = self.active_colour("window_background")
        foreground = QColor(self.active_colour("text_primary"))
        pg.setConfigOption("background", QColor(default_background))
        pg.setConfigOption("foreground", foreground)

        for window in self._windows:
            try:
                plot_widgets = window.findChildren(pg.PlotWidget)
            except RuntimeError:
                continue

            for plot_widget in plot_widgets:
                role_key = getattr(plot_widget, PLOT_BACKGROUND_ATTR, None)
                colour = self.active_colour(role_key) if role_key else default_background
                plot_widget.setBackground(QColor(colour))

                plot_item = plot_widget.getPlotItem()
                for side in ("left", "bottom", "right", "top"):
                    axis = plot_item.getAxis(side)
                    if axis is None:
                        continue
                    axis.setPen(pg.mkPen(foreground))
                    axis.setTextPen(pg.mkPen(foreground))

    def _apply_role_to_item(self, item) -> None:
        """
        Restyle one tagged plot item from its recorded role.

        Parameters
        ----------
        item : pyqtgraph.GraphicsObject
            Item previously passed to :meth:`tag_item`.
        """
        import pyqtgraph as pg

        role_key = getattr(item, TRACE_ROLE_ATTR, None)
        if role_key is None or role_key not in ROLES_BY_KEY:
            return

        scale = float(getattr(item, TRACE_WIDTH_SCALE_ATTR, 1.0))
        marker_only = bool(getattr(item, TRACE_MARKER_ATTR, False))
        colour = self.active_colour(role_key)

        try:
            if marker_only:
                if hasattr(item, "setSymbolBrush"):
                    item.setSymbolBrush(pg.mkBrush(colour))
                    item.setSymbolPen(pg.mkPen(colour))
                elif hasattr(item, "setBrush"):
                    item.setBrush(pg.mkBrush(colour))
                    item.setPen(pg.mkPen(colour))
            else:
                item.setPen(self.pen(role_key, scale,
                                     getattr(item, TRACE_STYLE_ATTR, None)))
        except (AttributeError, RuntimeError, TypeError):
            return

    def style_traces(self) -> None:
        """
        Apply the active colours and pen width to every live plot item.

        Two complementary mechanisms are used, because the project builds
        plots in two different ways:

        1. **Declared targets** - curves the graph controllers keep as named
           attributes (the four oscilloscopes). Resolved by attribute path,
           which keeps visually identical traces independently editable.
        2. **Tagged items** - curves rebuilt on demand by the analysis page,
           which hold no stable attribute and are found by walking the
           registered windows for items carrying ``_theme_role``.

        Safe to call at any time: unresolved targets and untagged items are
        skipped, so graph modules can call it at the end of plot construction.
        """
        try:
            import pyqtgraph as pg
        except ImportError:
            return

        width = self._active.trace_width

        for role in THEME_ROLES:
            if not role.targets:
                continue

            pen_width = width if role.follows_width else 1.0
            colour = self._active.colours[role.key]

            for target in role.targets:
                item = self._resolve_target(target)
                if item is None:
                    continue
                pen = pg.mkPen(colour, width=pen_width, cosmetic=True)
                style = getattr(item, TRACE_STYLE_ATTR, None)
                if style is not None:
                    pen.setStyle(style)
                try:
                    item.setPen(pen)
                except (AttributeError, RuntimeError, TypeError):
                    continue

        for window in list(self._windows):
            try:
                plot_widgets = window.findChildren(pg.PlotWidget)
            except RuntimeError:
                continue
            for plot_widget in plot_widgets:
                for item in list(plot_widget.getPlotItem().items):
                    self._apply_role_to_item(item)


    def _resolve_owner(self, owner: str):
        """Return the object holding a curve target, or ``None``."""
        if self._main_window is None:
            return None
        if owner == "window":
            return self._main_window
        return getattr(self._main_window, owner, None)

    def _resolve_target(self, target: CurveTarget):
        """Return the live plot item of a target, or ``None`` if absent."""
        owner = self._resolve_owner(target.owner)
        if owner is None:
            return None

        item = getattr(owner, target.attribute, None)
        if item is None:
            return None
        if target.index is None:
            return item

        try:
            return item[target.index]
        except (IndexError, KeyError, TypeError):
            return None

    def _register_toggles(self, window: QWidget) -> None:
        """
        Record which palette slot each animated toggle currently uses.

        Colours are reverse-mapped against the factory palette, so the toggles
        created by ``Parameters_ToggleButtons.Buttons`` can be recoloured later
        without annotating every construction site.

        Parameters
        ----------
        window : PySide6.QtWidgets.QWidget
            Root widget to scan.
        """
        try:
            from Parameters_ToggleButtons import PyToggle
        except ImportError:
            return

        index_of: Dict[str, int] = {}
        for index, rgb in enumerate(FACTORY_PALETTE):
            index_of.setdefault(to_hex(rgb).lower(), index)

        for toggle in window.findChildren(PyToggle):
            self._toggles.append((
                toggle,
                index_of.get(to_hex(toggle._bg_color).lower(), 11),
                index_of.get(to_hex(toggle._active_color).lower(), 4),
                index_of.get(to_hex(toggle._circle_color).lower(), 15),
            ))

    def _restyle_toggles(self) -> None:
        """Re-apply the palette to every registered animated toggle."""
        palette = Settings.DarkSolarized
        alive: List[Tuple[object, int, int, int]] = []

        for toggle, bg_index, active_index, circle_index in self._toggles:
            try:
                toggle.apply_style(
                    bg_color=to_hex(palette[bg_index]),
                    active_color=to_hex(palette[active_index]),
                    circle_color=to_hex(palette[circle_index]),
                )
            except RuntimeError:          # underlying C++ object deleted
                continue
            alive.append((toggle, bg_index, active_index, circle_index))

        self._toggles = alive


# Module-level singleton, mirroring the ``serial_manager`` pattern used
# elsewhere in the project. Import this rather than instantiating the class.
theme_manager = ThemeManager()
