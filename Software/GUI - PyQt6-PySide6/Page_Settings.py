"""
Settings page: user-editable application theme.

Interaction model
-----------------
Every control edits the *pending* theme held by :data:`theme_manager` and
nothing else. The interface keeps its current appearance until **Apply** is
pressed, so dragging the thickness slider or trying ten background colours
costs nothing: no style sheet is rebuilt and no curve is re-penned.

Feedback is therefore local to this page: each swatch paints itself with its
pending colour, and :class:`TracePreview` draws a sample spike with the
pending width and colour.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QColorDialog, QComboBox, QFileDialog, QFrame, QGridLayout, QGroupBox,
    QHBoxLayout, QLabel, QPushButton, QScrollArea, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget,
)

from Parameters_Sliders import TickSlider
from theme_manager import (
    SECTIONS, THEME_ROLES, TRACE_WIDTH_MAX, TRACE_WIDTH_MIN, TRACE_WIDTH_STEP,
    ThemeRole, contrast_of, mix, theme_manager,
)


SWATCH_SIZE = (116, 28)
ACTION_BUTTON_SIZE = (150, 34)
SWATCHES_PER_ROW = 3
PREVIEW_SIZE = (150, 34)

# The slider is integer-valued; this converts a tick index to a pen width.
WIDTH_SLIDER_SCALE = 1.0 / TRACE_WIDTH_STEP

# Normalised sample waveform: baseline, fast depolarisation, after-
# hyperpolarisation, recovery. Drawn so the chosen thickness is judged on a
# spike rather than on a straight line, where a thick pen always looks fine.
SAMPLE_SPIKE = (
    (0.00, 0.72), (0.22, 0.70), (0.30, 0.74), (0.38, 0.06),
    (0.46, 0.96), (0.56, 0.68), (0.70, 0.71), (1.00, 0.70),
)


class TracePreview(QWidget):
    """
    Live sample of the pending trace colour and thickness.

    Parameters
    ----------
    manager : theme_manager.ThemeManager
        Theme owner queried for the pending values on every repaint.
    role_key : str, optional
        Role supplying the preview colour.
    parent : PySide6.QtWidgets.QWidget, optional
        Qt parent.
    """

    def __init__(self, manager, role_key: str = "neuron_vm", parent=None) -> None:
        super().__init__(parent)
        self.manager = manager
        self.role_key = role_key
        self.setFixedSize(*PREVIEW_SIZE)
        self.setToolTip("Preview of the selected trace thickness")

    def paintEvent(self, event) -> None:  # noqa: N802
        """Draw the framed sample spike with the pending pen."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        background = self.manager.active_colour("window_background")
        border = mix(background, self.manager.active_colour("text_primary"), 0.30)

        painter.setPen(QPen(QColor(border), 1))
        painter.setBrush(QColor(background))
        painter.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 5, 5)

        inset_x, inset_y = 8.0, 6.0
        usable_w = self.width() - 2 * inset_x
        usable_h = self.height() - 2 * inset_y

        points = [
            QPointF(inset_x + x * usable_w, inset_y + y * usable_h)
            for x, y in SAMPLE_SPIKE
        ]

        pen = QPen(QColor(self.manager.colour(self.role_key)))
        pen.setWidthF(self.manager.trace_width)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawPolyline(points)
        painter.end()


class ColourSwatchButton(QPushButton):
    """
    Button showing a pending colour and opening a picker when clicked.

    Parameters
    ----------
    role : theme_manager.ThemeRole
        Role edited by this button.
    manager : theme_manager.ThemeManager
        Theme owner notified of the new colour.
    parent : PySide6.QtWidgets.QWidget, optional
        Qt parent.
    """

    def __init__(self, role: ThemeRole, manager, parent=None) -> None:
        super().__init__(parent)
        self.role = role
        self.manager = manager
        self.setFixedSize(*SWATCH_SIZE)
        self.setCursor(Qt.PointingHandCursor)
        self.clicked.connect(self._pick_colour)
        self.refresh()

    def refresh(self) -> None:
        """Repaint the swatch from the manager's pending colour."""
        colour = self.manager.colour(self.role.key)
        self.setText(colour.upper())
        self.setStyleSheet(
            f"background-color: {colour};"
            f"color: {contrast_of(colour)};"
            f"border: 1px solid rgba(128, 128, 128, 140);"
            f"border-radius: 5px; font: 700 9pt 'Courier New';"
        )

    def _pick_colour(self) -> None:
        """Open a modal colour dialog and stage the selection."""
        initial = QColor(self.manager.colour(self.role.key))
        chosen = QColorDialog.getColor(initial, self, f"Select: {self.role.label}")
        if chosen.isValid():
            self.manager.set_colour(self.role.key, chosen.name())
            self.refresh()


class SettingsPage:
    """
    Controller for the appearance section of the Settings page.

    Parameters
    ----------
    parent : PySide6.QtWidgets.QMainWindow
        Main window owning ``self.ui``.
    manager : theme_manager.ThemeManager, optional
        Theme owner; defaults to the module singleton.
    """

    def __init__(self, parent, manager=theme_manager) -> None:
        self.parent = parent
        self.ui = parent.ui
        self.manager = manager

        self._swatches: Dict[str, ColourSwatchButton] = {}
        self._group_boxes: List[QGroupBox] = []
        self._mode_combo: Optional[QComboBox] = None
        self._width_slider: Optional[TickSlider] = None
        self._width_readout: Optional[QLabel] = None
        self._preview: Optional[TracePreview] = None
        self._apply_button: Optional[QPushButton] = None
        self._revert_button: Optional[QPushButton] = None
        self._status_label: Optional[QLabel] = None

        self._build_controls()
        self.manager.pendingChanged.connect(self._on_pending_changed)
        self.manager.themeChanged.connect(self._on_theme_applied)
        self._sync_controls()

    # ------------------------------------------------------------------
    # Page selection
    # ------------------------------------------------------------------

    def ShowPage(self) -> None:
        """Display the Settings page and refresh its controls."""
        self.ui.mainbody_stackedWidget.setCurrentWidget(self.ui.page_601)
        self._sync_controls()

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def _build_controls(self) -> None:
        """Create the appearance widgets inside ``page_601``."""
        page = self.ui.page_601
        layout = page.layout()
        if layout is None:
            layout = QVBoxLayout(page)
            layout.setContentsMargins(16, 16, 16, 16)
            layout.setSpacing(10)

        container = QWidget(page)
        container.setObjectName("Settings_Appearance_container")
        outer = QVBoxLayout(container)
        outer.setContentsMargins(4, 4, 4, 4)
        outer.setSpacing(16)

        outer.addWidget(self._build_header(container))
        outer.addWidget(self._build_action_box(container))
        outer.addWidget(self._build_width_box(container))
        for section in SECTIONS:
            outer.addWidget(self._build_colour_box(container, section))
        outer.addItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        scroll = QScrollArea(page)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(container)
        layout.addWidget(scroll)

    def _make_group_box(self, parent: QWidget, title: str, name: str) -> QGroupBox:
        """
        Create a framed section box.

        The ``themeBox`` dynamic property is what the application style sheet
        selects on: an attribute selector outranks the plain ``QFrame`` type
        selector that would otherwise make the box transparent, since
        :class:`QGroupBox` inherits from :class:`QFrame`.

        Parameters
        ----------
        parent : PySide6.QtWidgets.QWidget
            Qt parent.
        title : str
            Text shown in the box header.
        name : str
            Object name, used for styling and for tests.

        Returns
        -------
        PySide6.QtWidgets.QGroupBox
            Empty, registered group box.
        """
        box = QGroupBox(title, parent)
        box.setObjectName(name)
        box.setProperty("themeBox", "true")
        box.setFlat(False)
        self._group_boxes.append(box)
        return box

    def _build_header(self, parent: QWidget) -> QWidget:
        """Build the title row plus the light / dark selector."""
        frame = QFrame(parent)
        row = QHBoxLayout(frame)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)

        title = QLabel("Appearance", frame)
        title.setStyleSheet("font: 700 15pt; background: transparent;")
        row.addWidget(title)
        row.addStretch(1)

        row.addWidget(QLabel("Mode", frame))
        self._mode_combo = QComboBox(frame)
        self._mode_combo.addItem("Dark", userData="dark")
        self._mode_combo.addItem("Light", userData="light")
        self._mode_combo.addItem("Custom", userData="custom")
        self._mode_combo.setFixedWidth(140)
        self._mode_combo.activated.connect(self._on_mode_selected)
        row.addWidget(self._mode_combo)

        return frame

    def _build_action_box(self, parent: QWidget) -> QGroupBox:
        """Build the framed Apply / Revert / Reset / Import / Export box."""
        box = self._make_group_box(parent, "Theme actions",
                                   "Settings_ThemeActions_groupBox")
        column = QVBoxLayout(box)
        column.setContentsMargins(14, 18, 14, 14)
        column.setSpacing(8)

        row = QHBoxLayout()
        row.setSpacing(10)

        self._apply_button = self._make_action_button(box, "Apply", self.ApplyTheme)
        self._revert_button = self._make_action_button(box, "Revert", self.RevertTheme)
        row.addWidget(self._apply_button)
        row.addWidget(self._revert_button)
        row.addWidget(self._make_action_button(box, "Reset to default", self.ResetTheme))
        row.addWidget(self._make_action_button(box, "Import...", self.ImportTheme))
        row.addWidget(self._make_action_button(box, "Export...", self.ExportTheme))
        row.addStretch(1)
        column.addLayout(row)

        self._status_label = QLabel("", box)
        self._status_label.setStyleSheet("font: 700 9pt; background: transparent;")
        column.addWidget(self._status_label)

        return box

    def _build_width_box(self, parent: QWidget) -> QGroupBox:
        """Build the framed trace-thickness control and its preview."""
        box = self._make_group_box(parent, "Trace rendering",
                                   "Settings_TraceRendering_groupBox")
        row = QHBoxLayout(box)
        row.setContentsMargins(14, 18, 14, 14)
        row.setSpacing(12)

        row.addWidget(QLabel("Trace thickness", box))

        ticks = int(round((TRACE_WIDTH_MAX - TRACE_WIDTH_MIN) * WIDTH_SLIDER_SCALE)) + 1
        self._width_slider = TickSlider(box, num_ticks=ticks)
        self._width_slider.setOrientation(Qt.Horizontal)
        self._width_slider.setRange(
            int(round(TRACE_WIDTH_MIN * WIDTH_SLIDER_SCALE)),
            int(round(TRACE_WIDTH_MAX * WIDTH_SLIDER_SCALE)),
        )
        self._width_slider.setSingleStep(1)
        self._width_slider.setPageStep(1)
        self._width_slider.setMinimumWidth(240)
        self._width_slider.valueChanged.connect(self._on_width_changed)
        row.addWidget(self._width_slider)

        self._width_readout = QLabel("", box)
        self._width_readout.setFixedWidth(58)
        self._width_readout.setStyleSheet("font: 700 10pt; background: transparent;")
        row.addWidget(self._width_readout)

        self._preview = TracePreview(self.manager, "neuron_vm", box)
        row.addWidget(self._preview)

        row.addStretch(1)
        hint = QLabel("Applies to every oscilloscope once applied.", box)
        hint.setStyleSheet("font: 9pt; background: transparent;")
        row.addWidget(hint)

        return box

    def _build_colour_box(self, parent: QWidget, section: str) -> QGroupBox:
        """
        Build one framed grid of colour swatches.

        Parameters
        ----------
        parent : PySide6.QtWidgets.QWidget
            Qt parent.
        section : str
            Entry of :data:`theme_manager.SECTIONS` to render.

        Returns
        -------
        PySide6.QtWidgets.QGroupBox
            Populated group box.
        """
        box = self._make_group_box(
            parent, section, f"Settings_{section.split()[0]}_groupBox")

        grid = QGridLayout(box)
        grid.setContentsMargins(14, 18, 14, 14)
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(8)

        roles = [role for role in THEME_ROLES if role.section == section]
        for position, role in enumerate(roles):
            row, column = divmod(position, SWATCHES_PER_ROW)
            grid.addWidget(QLabel(role.label, box), row, column * 2)
            swatch = ColourSwatchButton(role, self.manager, box)
            self._swatches[role.key] = swatch
            grid.addWidget(swatch, row, column * 2 + 1)

        for column in range(SWATCHES_PER_ROW):
            grid.setColumnStretch(column * 2, 1)
        return box

    @staticmethod
    def _make_action_button(parent: QWidget, text: str, slot) -> QPushButton:
        """Create one uniformly sized action button."""
        button = QPushButton(text, parent)
        button.setMinimumSize(*ACTION_BUTTON_SIZE)
        button.setCursor(Qt.PointingHandCursor)
        button.clicked.connect(slot)
        return button

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_mode_selected(self, index: int) -> None:
        """Stage the preset chosen in the mode combo box."""
        mode = self._mode_combo.itemData(index)
        if mode in ("dark", "light"):
            self.manager.set_mode(mode)
            self._refresh_swatches()
        else:
            self._sync_mode_combo()

    def _on_width_changed(self, raw_value: int) -> None:
        """
        Stage the pen width and refresh only the local preview.

        Deliberately does *not* trigger a repaint: a full restyle per slider
        tick is what made the control unusable.
        """
        self.manager.set_trace_width(raw_value / WIDTH_SLIDER_SCALE)
        if self._width_readout is not None:
            self._width_readout.setText(f"{self.manager.trace_width:g} px")
        if self._preview is not None:
            self._preview.update()

    def _on_pending_changed(self, dirty: bool) -> None:
        """Update the dirty indicators without touching the whole page."""
        self._sync_mode_combo()
        self._sync_status(dirty)
        if self._preview is not None:
            self._preview.update()

    def _on_theme_applied(self, *_) -> None:
        """Re-sync everything after the active theme has been repainted."""
        self._sync_controls()

    # ------------------------------------------------------------------
    # Synchronisation
    # ------------------------------------------------------------------

    def _sync_controls(self) -> None:
        """Refresh every control from the manager's pending state."""
        self._refresh_swatches()
        self._sync_mode_combo()

        if self._width_slider is not None:
            self._width_slider.blockSignals(True)
            self._width_slider.setValue(
                int(round(self.manager.trace_width * WIDTH_SLIDER_SCALE)))
            self._width_slider.blockSignals(False)
            self._width_slider.apply_style(
                groove_color=self.manager.active_colour("window_background"),
                fill_color=self.manager.active_colour("neuron_stimulus"),
                handle_image=":/resources/resources/Handle.png",
                height=6,
                margin_h=10,
            )

        if self._width_readout is not None:
            self._width_readout.setText(f"{self.manager.trace_width:g} px")
        if self._preview is not None:
            self._preview.update()

        self._sync_status(self.manager.is_dirty)

    def _refresh_swatches(self) -> None:
        """Repaint every swatch from the pending palette."""
        for swatch in self._swatches.values():
            swatch.refresh()

    def _sync_mode_combo(self) -> None:
        """Select the entry matching the pending mode."""
        if self._mode_combo is None:
            return
        index = self._mode_combo.findData(self.manager.mode)
        self._mode_combo.blockSignals(True)
        self._mode_combo.setCurrentIndex(index if index >= 0 else 2)
        self._mode_combo.blockSignals(False)

    def _sync_status(self, dirty: bool) -> None:
        """Show whether staged edits are still waiting to be applied."""
        if self._status_label is not None:
            self._status_label.setText(
                "Unapplied changes - press Apply to update the interface"
                if dirty else "Theme applied and saved - restored on next launch"
            )

        accent = self.manager.active_colour("neuron_stimulus")
        if self._apply_button is not None:
            self._apply_button.setEnabled(dirty)
            self._apply_button.setStyleSheet(
                f"background-color: {accent}; color: {contrast_of(accent)};"
                f"border: 1px solid {accent}; border-radius: 6px; font: 700 10pt;"
                if dirty else ""
            )
        if self._revert_button is not None:
            self._revert_button.setEnabled(dirty)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def ApplyTheme(self) -> None:
        """Commit the staged theme: repaint the interface and persist it."""
        self.manager.apply_and_save()

    def RevertTheme(self) -> None:
        """Drop the staged edits and restore the applied theme."""
        self.manager.discard_changes()
        self._sync_controls()

    def ResetTheme(self) -> None:
        """Restore, apply and persist the factory dark theme."""
        self.manager.reset()
        self._sync_controls()

    def ExportTheme(self) -> None:
        """Write the staged theme to a user-selected ``.json`` file."""
        path, _ = QFileDialog.getSaveFileName(
            self.parent, "Save theme", "./spikeling_theme.json", "JSON files (*.json)")
        if path:
            self.manager.export_to(path)

    def ImportTheme(self) -> None:
        """Stage a theme from a user-selected ``.json`` file."""
        path, _ = QFileDialog.getOpenFileName(
            self.parent, "Load theme", ".", "JSON files (*.json)")
        if path:
            self.manager.import_from(path)
            self._sync_controls()


def ShowPage(self) -> None:
    """Display the Settings page from a ``MainWindow`` instance."""
    page = getattr(self, "settings_page", None)
    if page is not None:
        page.ShowPage()
    else:
        self.ui.mainbody_stackedWidget.setCurrentWidget(self.ui.page_601)
