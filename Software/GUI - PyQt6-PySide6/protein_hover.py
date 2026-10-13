"""
Rotating protein preview shown when hovering a calcium indicator.

Frames are pre-rendered PNG turntables (see ``tools/render_geci_turntable.py``)
played back by a single :class:`~PySide6.QtCore.QTimer`, so the preview costs
one ``setPixmap`` per tick and adds no 3D dependency to the application.
"""

from __future__ import annotations

from collections import OrderedDict
from pathlib import Path

from PySide6.QtCore import QEvent, QModelIndex, QObject, QPoint, Qt, QTimer
from PySide6.QtGui import QGuiApplication, QPixmap
from PySide6.QtWidgets import QComboBox, QFrame, QLabel, QVBoxLayout, QWidget

import Parameters_GECI
import Parameters_Settings as Settings
from Parameters_GECI_Structures import GECI_STRUCTURES

from resource_path import application_resource_root

SPRITE_ROOT = application_resource_root() / "resources" / "geci"
FRAME_INTERVAL_MS = 100
HOVER_DWELL_MS = 250
PREVIEW_SIZE_PX = 220



SPRITE_CACHE_SIZE = 3


class TurntableSpriteCache:
    """
    Lazily loaded, LRU-bounded store of per-indicator turntable frames.

    A 36-frame 440x440 RGBA turntable occupies roughly 28 MB once decoded, so
    all indicators are never resident simultaneously.

    Parameters
    ----------
    root : pathlib.Path
        Directory holding one subdirectory of ``frame_*.png`` per indicator.
    capacity : int
        Number of decoded turntables kept in memory.
    """

    def __init__(self, root: Path = SPRITE_ROOT, capacity: int = SPRITE_CACHE_SIZE) -> None:
        self.root = Path(root)
        self.capacity = int(capacity)
        self._cache: OrderedDict[str, list[QPixmap]] = OrderedDict()

    def frames(self, geci_name: str) -> list[QPixmap]:
        """Return the frame list for ``geci_name``, loading it on first use."""
        if geci_name in self._cache:
            self._cache.move_to_end(geci_name)
            return self._cache[geci_name]

        directory = self.root / geci_name
        paths = sorted(directory.glob("frame_*.png"))
        if not paths:
            print(f"[resources] no turntable frames under {directory}")
        frames: list[QPixmap] = []
        for path in paths:
            pixmap = QPixmap(str(path))
            if pixmap.isNull():
                continue
            pixmap = pixmap.scaled(PREVIEW_SIZE_PX * 2, PREVIEW_SIZE_PX * 2,
                                   Qt.KeepAspectRatio, Qt.SmoothTransformation)
            pixmap.setDevicePixelRatio(2.0)
            frames.append(pixmap)

        self._cache[geci_name] = frames
        while len(self._cache) > self.capacity:
            self._cache.popitem(last=False)
        return frames


class RotatingProteinPreview(QWidget):
    """
    Frameless popup playing a protein turntable with a caption.

    Parameters
    ----------
    cache : TurntableSpriteCache
        Shared frame store.
    parent : QWidget, optional
        Owner widget; the popup is a top-level tool window regardless.
    """

    def __init__(self, cache: TurntableSpriteCache, parent: QWidget | None = None) -> None:
        super().__init__(parent, Qt.ToolTip | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        self._cache = cache
        self._frames: list[QPixmap] = []
        self._frame_index = 0

        container = QFrame(self)
        container.setObjectName("ProteinPreviewFrame")
        container.setStyleSheet(
            f"#ProteinPreviewFrame {{"
            f"background-color: rgba{tuple(Settings.DarkSolarized[1]) + (235,)};"
            f"border: 1px solid rgb{tuple(Settings.DarkSolarized[14])};"
            f"border-radius: 10px;}}"
        )

        self.image_label = QLabel(container)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setFixedSize(PREVIEW_SIZE_PX, PREVIEW_SIZE_PX)

        self.title_label = QLabel(container)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet(
            f"color: rgb{tuple(Settings.DarkSolarized[3])}; font: 700 11pt; background: transparent;")

        self.caption_label = QLabel(container)
        self.caption_label.setAlignment(Qt.AlignCenter)
        self.caption_label.setWordWrap(True)
        self.caption_label.setFixedWidth(PREVIEW_SIZE_PX)
        self.caption_label.setStyleSheet(
            f"color: rgb{tuple(Settings.DarkSolarized[14])}; font: 400 8pt; background: transparent;")

        inner = QVBoxLayout(container)
        inner.setContentsMargins(10, 8, 10, 8)
        inner.setSpacing(4)
        inner.addWidget(self.image_label)
        inner.addWidget(self.title_label)
        inner.addWidget(self.caption_label)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(container)

        self._timer = QTimer(self)
        self._timer.setInterval(FRAME_INTERVAL_MS)
        self._timer.timeout.connect(self._advance_frame)

    def show_indicator(self, geci_name: str, anchor: QPoint) -> None:
        """
        Display the turntable for ``geci_name`` near the global point ``anchor``.

        Falls back to a text-only card when no frames have been rendered, so a
        missing asset degrades gracefully instead of breaking the hover.
        """
        meta = GECI_STRUCTURES.get(geci_name)
        preset = Parameters_GECI.GECI.get(geci_name, {})

        self.title_label.setText(geci_name)
        kd = preset.get("Kd_uM")
        chemistry = f"Kd = {kd:.3f} µM · n = {preset.get('hill_n', 0):.1f}" if kd else ""
        caption = meta.caption if meta else "No structural data"
        scaffold = meta.scaffold if meta else ""
        self.caption_label.setText(f"{scaffold}<br>{caption}<br>{chemistry}")

        self._frames = self._cache.frames(geci_name)
        self._frame_index = 0

        if self._frames:
            self.image_label.setPixmap(self._frames[0])
            self._timer.start()
        else:
            self.image_label.clear()
            self.image_label.setText("structure\nunavailable")
            self._timer.stop()

        self.adjustSize()
        self.move(self._clamp_to_screen(anchor))
        self.show()

    def hide_preview(self) -> None:
        """Stop playback and hide the popup."""
        self._timer.stop()
        self.hide()

    def _advance_frame(self) -> None:
        if not self._frames:
            return
        self._frame_index = (self._frame_index + 1) % len(self._frames)
        self.image_label.setPixmap(self._frames[self._frame_index])

    def _clamp_to_screen(self, anchor: QPoint) -> QPoint:
        """Keep the popup fully visible on the screen containing ``anchor``."""
        screen = QGuiApplication.screenAt(anchor) or QGuiApplication.primaryScreen()
        available = screen.availableGeometry()
        x = min(anchor.x() + 18, available.right() - self.width() - 8)
        y = min(max(anchor.y() - self.height() // 2, available.top() + 8),
                available.bottom() - self.height() - 8)
        return QPoint(x, y)


class GeciHoverController(QObject):
    """
    Bind rotating previews to a GECI :class:`QComboBox`.

    Covers both interaction paths: hovering the closed combo previews the
    current selection, hovering a row of the open dropdown previews that row.

    Parameters
    ----------
    combo_box : QComboBox
        The indicator selector, e.g. ``ui.Imaging_GECI_comboBox``.
    parent : QObject, optional
        Owner, normally the main window.
    """

    def __init__(self, combo_box: QComboBox, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.combo_box = combo_box
        self.preview = RotatingProteinPreview(TurntableSpriteCache())
        self._pending_name = ""

        self._dwell_timer = QTimer(self)
        self._dwell_timer.setSingleShot(True)
        self._dwell_timer.setInterval(HOVER_DWELL_MS)
        self._dwell_timer.timeout.connect(self._show_pending)

        view = combo_box.view()
        view.setMouseTracking(True)
        view.entered.connect(self._on_row_entered)
        view.viewport().installEventFilter(self)
        combo_box.installEventFilter(self)

    def eventFilter(self, watched, event) -> bool:  # noqa: N802
        """Arm the preview on enter, cancel it on leave or dropdown close."""
        if watched is self.combo_box:
            if event.type() == QEvent.Enter:
                self._arm(self.combo_box.currentText())
            elif event.type() == QEvent.Leave:
                self._cancel()
        elif event.type() in (QEvent.Leave, QEvent.Hide, QEvent.MouseButtonPress):
            self._cancel()
        return super().eventFilter(watched, event)

    def _on_row_entered(self, index: QModelIndex) -> None:
        if index.isValid():
            self._arm(index.data(Qt.DisplayRole))

    def _arm(self, geci_name: str) -> None:
        if not geci_name or geci_name == self._pending_name:
            return
        self._pending_name = geci_name
        self._dwell_timer.start()

    def _show_pending(self) -> None:
        from PySide6.QtGui import QCursor
        if self._pending_name:
            self.preview.show_indicator(self._pending_name, QCursor.pos())

    def _cancel(self) -> None:
        self._dwell_timer.stop()
        self._pending_name = ""
        self.preview.hide_preview()
