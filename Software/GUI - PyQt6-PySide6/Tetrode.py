from __future__ import annotations

import math
import sys
import types
from dataclasses import dataclass

from PySide6.QtCore import QObject, QPoint, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (QApplication, QWidget, QGraphicsDropShadowEffect, QFrame, QGraphicsItem, QGraphicsObject, QGraphicsScene, QGraphicsView, QLabel, QMainWindow, QVBoxLayout,)


# ---------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------
BASE1 = QColor(190, 205, 205)
BASE03 = QColor(0, 43, 54)
BASE02 = QColor(7, 54, 66)

PROBE = QColor(238, 232, 213)
AXIS = QColor(181, 137, 0, 210)
GRID_MINOR = QColor(147, 161, 161, 55)
GRID_MAJOR = QColor(190, 205, 205, 110)
DISTANCE = QColor(38, 139, 210, 170)


# ---------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------
@dataclass
class ItemDefaults:
    x: float
    y: float
    z: float


# ---------------------------------------------------------------------
# Scene with background grid
# ---------------------------------------------------------------------
class GeometryScene(QGraphicsScene):
    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.grid_size = 1.0
        self.major_every = 5

    def set_grid_size(self, grid_size: float) -> None:
        self.grid_size = max(1.0, float(grid_size))
        self.invalidate(self.sceneRect(), QGraphicsScene.BackgroundLayer)

    def drawBackground(self, painter: QPainter, rect: QRectF) -> None:  # noqa: N802
        super().drawBackground(painter, rect)

        grid = max(1.0, self.grid_size)
        left = math.floor(rect.left() / grid) * grid
        top = math.floor(rect.top() / grid) * grid

        minor_lines = []
        major_lines = []

        x = left
        while x <= rect.right():
            line = (QPointF(x, rect.top()), QPointF(x, rect.bottom()))
            if int(round(x / grid)) % self.major_every == 0:
                major_lines.append(line)
            else:
                minor_lines.append(line)
            x += grid

        y = top
        while y <= rect.bottom():
            line = (QPointF(rect.left(), y), QPointF(rect.right(), y))
            if int(round(y / grid)) % self.major_every == 0:
                major_lines.append(line)
            else:
                minor_lines.append(line)
            y += grid

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, False)

        painter.setPen(QPen(GRID_MINOR, 0))
        for p1, p2 in minor_lines:
            painter.drawLine(p1, p2)

        painter.setPen(QPen(GRID_MAJOR, 0))
        for p1, p2 in major_lines:
            painter.drawLine(p1, p2)

        painter.setPen(QPen(AXIS, 0))
        painter.drawLine(QPointF(0.0, rect.top()), QPointF(0.0, rect.bottom()))
        painter.drawLine(QPointF(rect.left(), 0.0), QPointF(rect.right(), 0.0))

        painter.restore()


# ---------------------------------------------------------------------
# Custom view
# ---------------------------------------------------------------------
class GeometryView(QGraphicsView):
    mouseScenePositionChanged = Signal(float, float)
    zoomChanged = Signal(float)
    viewResized = Signal()

    def __init__(self, parent: QFrame | None = None) -> None:
        super().__init__(parent)
        self._zoom = 1.0
        self._panning = False
        self._pan_start = QPoint()

        self.setRenderHint(QPainter.Antialiasing, True)
        self.setRenderHint(QPainter.TextAntialiasing, True)
        self.setFrameShape(QFrame.NoFrame)
        self.setDragMode(QGraphicsView.NoDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setMouseTracking(True)

    def reset_zoom(self) -> None:
        self.resetTransform()
        self._zoom = 1.0
        self.zoomChanged.emit(self._zoom)

    def wheelEvent(self, event) -> None:  # noqa: N802
        zoom_factor = 1.15
        factor = zoom_factor if event.angleDelta().y() > 0 else (1.0 / zoom_factor)

        new_zoom = self._zoom * factor
        if 0.20 <= new_zoom <= 8.0:
            self.scale(factor, factor)
            self._zoom = new_zoom
            self.zoomChanged.emit(self._zoom)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MiddleButton:
            self._panning = True
            self._pan_start = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        scene_pos = self.mapToScene(event.pos())
        self.mouseScenePositionChanged.emit(scene_pos.x(), scene_pos.y())

        if self._panning:
            delta = event.pos() - self._pan_start
            self._pan_start = event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MiddleButton:
            self._panning = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)

# ---------------------------------------------------------------------
# UI promoted-widget compatibility shim
# ---------------------------------------------------------------------
# UI_Tetrode.py was generated from a .ui file where Tetrode_graphicsView
# is promoted to GeometryView and therefore tries to do:
#     from geometry_view import GeometryView
#
# We provide that module dynamically here so UI_Tetrode.py can import it
# without needing a separate geometry_view.py file.
geometry_view_module = types.ModuleType("geometry_view")
geometry_view_module.GeometryView = GeometryView
sys.modules["geometry_view"] = geometry_view_module

from UI_Tetrode import Ui_Tetrode


# ---------------------------------------------------------------------
# Neuron item
# ---------------------------------------------------------------------
class NeuronItem(QGraphicsObject):
    positionChanged = Signal(float, float)
    clicked = Signal(str)

    def __init__(
        self,
        name: str,
        png_path: str | None = None,
            anchor_x_px: float | None = None,
            anchor_y_px: float | None = None,
        image_size: float = 64.0,
        parent: QGraphicsItem | None = None,
    ) -> None:
        super().__init__(parent)
        self.name = name
        self.depth_z = 0.0
        self.show_label = True
        self.snap_to_grid = False
        self.grid_size = 1.0

        self.png_path = png_path
        self.image_size = image_size
        self.image_opacity = 0.75
        self.pixmap = QPixmap(png_path) if png_path else QPixmap()

        if not self.pixmap.isNull():
            self.anchor_x_px = float(anchor_x_px) if anchor_x_px is not None else self.pixmap.width() / 2.0
            self.anchor_y_px = float(anchor_y_px) if anchor_y_px is not None else self.pixmap.height() / 2.0
        else:
            self.anchor_x_px = 0.0
            self.anchor_y_px = 0.0

        self.setFlags(
            QGraphicsItem.ItemIsMovable
            | QGraphicsItem.ItemIsSelectable
            | QGraphicsItem.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)

    def boundingRect(self) -> QRectF:  # noqa: N802
        if not self.pixmap.isNull():
            original_w = self.pixmap.width()
            original_h = self.pixmap.height()

            scale = self.image_size / max(original_w, original_h)
            draw_w = original_w * scale
            draw_h = original_h * scale

            anchor_x = self.anchor_x_px * scale
            anchor_y = self.anchor_y_px * scale

            left = -anchor_x
            top = -anchor_y
            right = draw_w - anchor_x
            bottom = draw_h - anchor_y

            extra_bottom = 26.0 if self.show_label else 8.0
            return QRectF(left - 8, top - 8, (right - left) + 16, (bottom - top) + extra_bottom + 16)

        half = self.image_size / 2.0
        extra = 26.0 if self.show_label else 10.0
        return QRectF(-half - 8, -half - 8, self.image_size + 16, self.image_size + extra + 16)

    def paint(self, painter: QPainter, option, widget=None) -> None:
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        half = self.image_size / 2.0
        target_rect = QRectF(-half, -half, self.image_size, self.image_size)

        if not self.pixmap.isNull():
            original_w = self.pixmap.width()
            original_h = self.pixmap.height()

            scale = self.image_size / max(original_w, original_h)
            draw_w = original_w * scale
            draw_h = original_h * scale

            anchor_x = self.anchor_x_px * scale
            anchor_y = self.anchor_y_px * scale

            target_rect = QRectF(-anchor_x, -anchor_y, draw_w, draw_h)

            painter.setOpacity(self.image_opacity)
            painter.drawPixmap(target_rect, self.pixmap, self.pixmap.rect())
            painter.setOpacity(1.0)

            if self.isSelected():
                painter.setPen(QPen(PROBE, 1.5, Qt.DashLine))
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(QPointF(0.0, 0.0), 60, 60)

            if self.show_label:
                painter.setPen(QPen(BASE1, 1))
                font = QFont()
                font.setPointSize(12)
                font.setBold(True)
                painter.setFont(font)

                text_y = target_rect.top() + 8
                text_rect = QRectF(target_rect.left() - 20, text_y, max(160.0, target_rect.width() + 40.0), 24.0)
                painter.drawText(text_rect, Qt.AlignCenter, self.name)


        else:
            half = self.image_size / 2.0
            painter.setPen(QPen(BASE1.darker(130), 2))
            painter.setBrush(QBrush(BASE1))
            painter.drawEllipse(QPointF(0.0, 0.0), half, half)

        painter.restore()


    def set_depth(self, z_value: float) -> None:
        self.depth_z = float(z_value)
        self.setToolTip(f"{self.name}\nX={self.x():.1f}, Y={self.y():.1f}, Z={self.depth_z:.1f}")
        self.update()

    def set_show_label(self, state: bool) -> None:
        self.show_label = bool(state)
        self.update()

    def itemChange(self, change, value):  # noqa: N802, ANN001
        if change == QGraphicsItem.ItemPositionChange and self.snap_to_grid and self.grid_size > 0:
            pos = value
            snapped_x = round(pos.x() / self.grid_size) * self.grid_size
            snapped_y = round(pos.y() / self.grid_size) * self.grid_size
            return QPointF(snapped_x, snapped_y)

        if change == QGraphicsItem.ItemPositionHasChanged:
            self.setToolTip(f"{self.name}\nX={self.x():.1f}, Y={self.y():.1f}, Z={self.depth_z:.1f}")
            self.positionChanged.emit(self.x(), self.y())

        return super().itemChange(change, value)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        self.clicked.emit(self.name)
        super().mousePressEvent(event)


# ---------------------------------------------------------------------
# Tetrode item
# ---------------------------------------------------------------------
import math
from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QGraphicsItem, QGraphicsObject


class TetrodeItem(QGraphicsObject):
    positionChanged = Signal(float, float)
    clicked = Signal(str)

    def __init__(self, contact_spacing: float = 25.0, parent: QGraphicsItem | None = None) -> None:
        super().__init__(parent)
        self.contact_spacing = float(contact_spacing)   # actual inter-contact spacing in µm
        self.site_radius = 10.0                          # visual radius of each contact
        self.depth_z = 0.0
        self.show_label = True
        self.snap_to_grid = False
        self.grid_size = 20.0
        self.contact_colors = [
            QColor(38, 139, 210),  # E1
            QColor(42, 161, 152),  # E2
            QColor(133, 153, 0),  # E3
            QColor(108, 113, 196),  # E4
        ]

        self.setFlags(
            QGraphicsItem.ItemIsMovable
            | QGraphicsItem.ItemIsSelectable
            | QGraphicsItem.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)

    def contact_radius_from_center(self) -> float:
        # For 4 contacts at 90° around center:
        # nearest-neighbor spacing d = r * sqrt(2)
        # therefore r = d / sqrt(2)
        return self.contact_spacing / math.sqrt(2.0)

    def boundingRect(self) -> QRectF:  # noqa: N802
        r = self.contact_radius_from_center() + self.site_radius + 18.0
        extra_bottom = 26.0 if self.show_label else 8.0
        return QRectF(-r, -r, 2 * r, 2 * r + extra_bottom)

    def site_positions_local(self) -> list[tuple[float, float]]:
        r = self.contact_radius_from_center()
        return [
            (0.0, -r),   # top
            (r, 0.0),    # right
            (0.0, r),    # bottom
            (-r, 0.0),   # left
        ]

    def site_positions_scene(self) -> list[QPointF]:
        return [self.mapToScene(QPointF(x, y)) for x, y in self.site_positions_local()]

    def set_contact_spacing(self, spacing_um: float) -> None:
        self.prepareGeometryChange()
        self.contact_spacing = max(1.0, float(spacing_um))
        self.setToolTip(
            f"Tetrode\n"
            f"X={self.x():.1f}, Y={self.y():.1f}, Z={self.depth_z:.1f}\n"
            f"Contact spacing={self.contact_spacing:.1f} µm"
        )
        self.update()

    def set_depth(self, z_value: float) -> None:
        self.depth_z = float(z_value)
        self.setToolTip(
            f"Tetrode\n"
            f"X={self.x():.1f}, Y={self.y():.1f}, Z={self.depth_z:.1f}\n"
            f"Contact spacing={self.contact_spacing:.1f} µm"
        )
        self.update()

    def set_show_label(self, state: bool) -> None:
        self.show_label = bool(state)
        self.update()

    def paint(self, painter: QPainter, option, widget=None) -> None:  # noqa: ANN001
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)

        r = self.contact_radius_from_center()

        # Crosshair
        painter.setPen(QPen(QColor(238, 232, 213), 2))
        cross = max(10.0, r * 0.5)
        painter.drawLine(QPointF(-cross, 0.0), QPointF(cross, 0.0))
        painter.drawLine(QPointF(0.0, -cross), QPointF(0.0, cross))

        # Dashed guide ring
        painter.setPen(QPen(QColor(190, 205, 205, 130), 2.5, Qt.DashLine))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(0.0, 0.0), r, r)

        # Contact sites
        for i, (px, py) in enumerate(self.site_positions_local()):
            color = self.contact_colors[i] if i < len(self.contact_colors) else QColor(0, 43, 54)
            painter.setPen(QPen(color.darker(140), 1.5))
            painter.setBrush(QBrush(color))
            painter.drawEllipse(QPointF(px, py), self.site_radius, self.site_radius)

        painter.setPen(QPen(PROBE, 1.5))

        # Selection halo
        if self.isSelected():
            painter.setPen(QPen(QColor(181, 137, 0), 1.5, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QPointF(0.0, 0.0), r + 8.0, r + 8.0)

        # Label
        if self.show_label:
            painter.setPen(QPen(QColor(190, 205, 205), 1))
            font = QFont()
            font.setPointSize(12)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(QRectF(-70, r + 10, 140, 20), Qt.AlignCenter, "Tetrode")

        painter.restore()

    def itemChange(self, change, value):  # noqa: N802, ANN001
        if change == QGraphicsItem.ItemPositionChange and self.snap_to_grid and self.grid_size > 0:
            pos = value
            snapped_x = round(pos.x() / self.grid_size) * self.grid_size
            snapped_y = round(pos.y() / self.grid_size) * self.grid_size
            return QPointF(snapped_x, snapped_y)

        if change == QGraphicsItem.ItemPositionHasChanged:
            self.positionChanged.emit(self.x(), self.y())

        return super().itemChange(change, value)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        self.clicked.emit("Tetrode")
        super().mousePressEvent(event)


class ScaleBarOverlay(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.bar_length_px = 100
        self.label_text = "100 µm"

        self.left_margin = 12
        self.right_margin = 12
        self.top_margin = 6
        self.bottom_margin = 6

        self.tick_height = 10
        self.bar_pen_width = 2
        self.text_gap = 6

        self.min_bar_length_px = 30
        self.max_bar_length_px = 260

        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self._update_widget_size()

    def _update_widget_size(self) -> None:
        font = self.font()
        font.setBold(True)
        font.setPointSize(10)

        fm = self.fontMetrics()
        text_width = fm.horizontalAdvance(self.label_text)
        text_height = fm.height()

        content_width = max(self.bar_length_px, text_width)
        width = self.left_margin + content_width + self.right_margin
        height = (
            self.top_margin
            + self.tick_height
            + self.text_gap
            + text_height
            + self.bottom_margin
        )

        self.resize(width, height)

    def set_scale(self, bar_length_px: int, label_text: str) -> None:
        self.bar_length_px = max(self.min_bar_length_px, min(int(bar_length_px), self.max_bar_length_px))
        self.label_text = label_text
        self._update_widget_size()
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)

        bar_left = self.left_margin
        bar_right = bar_left + self.bar_length_px
        bar_y = self.top_margin + self.tick_height / 2

        tick_half = self.tick_height / 2

        painter.setPen(QPen(QColor(190, 205, 205), self.bar_pen_width))
        painter.drawLine(QPointF(bar_left, bar_y), QPointF(bar_right, bar_y))
        painter.drawLine(QPointF(bar_left, bar_y - tick_half), QPointF(bar_left, bar_y + tick_half))
        painter.drawLine(QPointF(bar_right, bar_y - tick_half), QPointF(bar_right, bar_y + tick_half))

        font = painter.font()
        font.setBold(True)
        font.setPointSize(10)
        painter.setFont(font)
        painter.setPen(QPen(QColor(190, 205, 205), 1))

        text_y = self.top_margin + self.tick_height + self.text_gap
        text_rect = QRectF(
            0,
            text_y,
            self.width(),
            self.height() - text_y
        )
        painter.drawText(text_rect, Qt.AlignHCenter | Qt.AlignTop, self.label_text)
# ---------------------------------------------------------------------
# Main window/controller
# ---------------------------------------------------------------------
class TetrodeGeometryWindow(QMainWindow):
    geometrySaved = Signal(dict)
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.ui = Ui_Tetrode()
        self.ui.setupUi(self)

        # Remove title bar
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Drop shadow effect
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(20)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(0)
        self.shadow.setColor(QColor(0, 0, 0, 60))
        self.ui.Tetrode_Main_frame.setGraphicsEffect(self.shadow)

        self._syncing_controls = False
        self._distance_lines = []

        self._build_readout_panel()
        self._build_scene()
        self._build_grid_scale_overlay()
        self._build_scale_bar_overlay()
        self._connect_signals()
        self.reset_geometry()

        # Move window
        def moveWindow(event):
            # If left-clicked, move window
            if event.buttons() == Qt.LeftButton:
                self.move(self.pos() + event.globalPosition().toPoint() - self.dragPos)
                self.dragPos = event.globalPosition().toPoint()
                event.accept()

        # Custom Navigation bar movement
        self.ui.Tetrode_Header_widget.mouseMoveEvent = moveWindow


    def mousePressEvent(self, event):
        self.dragPos = event.globalPosition().toPoint()



    def _build_scale_bar_overlay(self) -> None:
        self.scale_bar_overlay = ScaleBarOverlay(self.ui.Tetrode_graphicsView.viewport())
        self.scale_bar_overlay.show()
        self._position_scale_bar_overlay()
        self._update_scale_bar_overlay()

    def _position_scale_bar_overlay(self) -> None:
        if not hasattr(self, "scale_bar_overlay"):
            return

        viewport = self.ui.Tetrode_graphicsView.viewport()
        margin = 12
        x = viewport.width() - self.scale_bar_overlay.width() - margin
        y = viewport.height() - self.scale_bar_overlay.height() - margin
        self.scale_bar_overlay.move(x, y)

    def _update_scale_bar_overlay(self) -> None:
        if not hasattr(self, "scale_bar_overlay"):
            return

        view = self.ui.Tetrode_graphicsView
        grid_um = self.ui.Tetrode_Parameters_View_GridSize_doubleSpinBox.value() / 10

        divisions = 100
        bar_um = grid_um * divisions

        p0 = view.mapFromScene(QPointF(0.0, 0.0))
        p1 = view.mapFromScene(QPointF(bar_um, 0.0))
        bar_length_px = abs(p1.x() - p0.x())

        self.scale_bar_overlay.set_scale(max(30, int(bar_length_px)), f"{bar_um:.0f} µm")

    # -------------------------------------------------------------
    # Readout
    # -------------------------------------------------------------
    def _build_readout_panel(self) -> None:
        self.readout_cursor = self._ensure_readout_value_label(
            "Tetrode_Parameters_Readout_Cursor_frame",
            "Tetrode_Parameters_Readout_Cursor_value_label",
            "X=0.0 µm   Y=0.0 µm",
        )

        self.readout_selected = self._ensure_readout_value_label(
            "Tetrode_Parameters_Readout_Selected_frame",
            "Tetrode_Parameters_Readout_Selected_value_label",
            "None",
        )

        self.readout_zoom = self._ensure_readout_value_label(
            "Tetrode_Parameters_Readout_Zoom_frame",
            "Tetrode_Parameters_Readout_Zoom_value_label",
            "100%",
        )

        self.readout_distance_n1 = self._ensure_readout_value_label(
            "Tetrode_Distance_Readout_Neuron1_frame",
            "Tetrode_Distance_Readout_Neuron1_value_label",
            "Main Neuron  ↔ Electrode:-- µm",
        )

        self.readout_distance_n2 = self._ensure_readout_value_label(
            "Tetrode_Distance_Readout_Neuron2_frame",
            "Tetrode_Distance_Readout_Neuron2_value_label",
            "Aux Neuron 1 ↔ Electrode:-- µm",
        )

        self.readout_distance_n3 = self._ensure_readout_value_label(
            "Tetrode_Distance_Readout_Neuron3_frame",
            "Tetrode_Distance_Readout_Neuron3_value_label",
            "Aux Neuron 2 ↔ Electrode:-- µm",
        )

    def _ensure_readout_value_label(self, frame_name: str, label_name: str, default_text: str) -> QLabel:
        frame = getattr(self.ui, frame_name, None)

        # If the Designer frame does not exist yet, create a hidden fallback label
        # so the app does not crash.
        if frame is None:
            label = QLabel(self)
            label.setObjectName(label_name)
            label.setText(default_text)
            label.hide()
            return label

        label = frame.findChild(QLabel, label_name)

        if label is None:
            label = QLabel(frame)
            label.setObjectName(label_name)
            label.setText(default_text)

            layout = frame.layout()
            if layout is None:
                layout = QVBoxLayout(frame)
                layout.setContentsMargins(4, 2, 4, 2)
                layout.setSpacing(0)

            layout.addWidget(label)

        label.setText(default_text)
        label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        label.setStyleSheet("color: rgb(190, 205, 205); background: transparent; border: none;")

        font = label.font()
        font.setBold(True)
        label.setFont(font)

        return label





    # -------------------------------------------------------------
    # Build scene/items
    # -------------------------------------------------------------
    def _build_scene(self) -> None:
        self.scene = GeometryScene(self)

        # Scene size in µm
        self.scene.setSceneRect(-550.0, -300.0, 800.0, 600.0)

        view = self.ui.Tetrode_graphicsView
        view.setScene(self.scene)
        view.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)

        self.neuron_defaults = {
            "Main Neuron": ItemDefaults(0.0, 0.0, 0.0),
            "Aux Neuron 1": ItemDefaults(-400.0, 150.0, 0.0),
            "Aux Neuron 2": ItemDefaults(-300.0, -150.0, 0.0),
            "Tetrode": ItemDefaults(0.0, 0.0, 10.0),
        }

        self.neuron_main = NeuronItem(
            "Main Neuron",
            png_path="resources/Spiky1.png",
            image_size=350.0,
            anchor_x_px=500,
            anchor_y_px=500,
        )

        self.neuron_aux1 = NeuronItem(
            "Aux Neuron 1",
            png_path="resources/Spiky2.png",
            image_size=350.0,
            anchor_x_px=500,
            anchor_y_px=500,
        )

        self.neuron_aux2 = NeuronItem(
            "Aux Neuron 2",
            png_path="resources/Spiky3.png",
            image_size=350.0,
            anchor_x_px=500,
            anchor_y_px=500,
        )

        self.tetrode_item = TetrodeItem(contact_spacing=25.0)

        for item in (self.neuron_main, self.neuron_aux1, self.neuron_aux2, self.tetrode_item):
            self.scene.addItem(item)

        # Start from a clean transform
        view.resetTransform()

        # First fit the whole scene
        view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

        # Then apply an additional 66% zoom factor
        view.scale(0.66, 0.66)

        # Keep the center on the probe/origin
        view.centerOn(0.0, 0.0)

        # If your custom GeometryView tracks zoom internally, update it too
        if hasattr(view, "_zoom"):
            view._zoom = 0.66
            if hasattr(view, "zoomChanged"):
                view.zoomChanged.emit(view._zoom)

        self.scene.update(self.scene.sceneRect())
        view.viewport().update()

    def _build_grid_scale_overlay(self) -> None:
        self.grid_scale_label = QLabel(self.ui.Tetrode_graphicsView.viewport())
        self.grid_scale_label.setObjectName("Tetrode_GridScale_label")
        self.grid_scale_label.setText("Grid: 1 µm/div")
        self.grid_scale_label.setStyleSheet("""
            QLabel {
                color: rgb(190, 205, 205);
                background-color: rgba(7, 54, 66, 180);
                border: 1px solid rgba(190, 205, 205, 90);
                border-radius: 6px;
                padding: 4px 8px;
            }
        """)
        self.grid_scale_label.adjustSize()
        self.grid_scale_label.move(12, 12)
        self.grid_scale_label.show()

    def _update_grid_scale_overlay(self) -> None:
        grid_um = self.ui.Tetrode_Parameters_View_GridSize_doubleSpinBox.value()
        self.grid_scale_label.setText(f"Grid: {grid_um:.0f} µm/div")
        self.grid_scale_label.adjustSize()

    # -------------------------------------------------------------
    # Signals
    # -------------------------------------------------------------
    def _connect_signals(self) -> None:
        view = self.ui.Tetrode_graphicsView
        view.mouseScenePositionChanged.connect(self._update_cursor_readout)
        view.zoomChanged.connect(self._update_zoom_readout)

        self.neuron_main.positionChanged.connect(
            lambda x, y: self._sync_item_to_spinboxes(
                self.ui.Tetrode_Parameters_Spikeling1_x_doubleSpinBox,
                self.ui.Tetrode_Parameters_Spikeling1_y_doubleSpinBox,
                x,
                y,
            )
        )
        self.neuron_aux1.positionChanged.connect(
            lambda x, y: self._sync_item_to_spinboxes(
                self.ui.Tetrode_Parameters_Spikeling2_x_doubleSpinBox,
                self.ui.Tetrode_Parameters_Spikeling2_y_doubleSpinBox,
                x,
                y,
            )
        )
        self.neuron_aux2.positionChanged.connect(
            lambda x, y: self._sync_item_to_spinboxes(
                self.ui.Tetrode_Parameters_Spikeling3_x_doubleSpinBox,
                self.ui.Tetrode_Parameters_Spikeling3_y_doubleSpinBox,
                x,
                y,
            )
        )
        self.tetrode_item.positionChanged.connect(
            lambda x, y: self._sync_item_to_spinboxes(
                self.ui.Tetrode_Parameters_Electrode_x_doubleSpinBox,
                self.ui.Tetrode_Parameters_Electrode_y_doubleSpinBox,
                x,
                y,
            )
        )

        for item in (self.neuron_main, self.neuron_aux1, self.neuron_aux2, self.tetrode_item):
            item.clicked.connect(self._update_selected_readout)

        # Controls -> scene
        self.ui.Tetrode_Parameters_Spikeling1_x_doubleSpinBox.valueChanged.connect(self._apply_controls_to_scene)
        self.ui.Tetrode_Parameters_Spikeling1_y_doubleSpinBox.valueChanged.connect(self._apply_controls_to_scene)
        self.ui.Tetrode_Parameters_Spikeling1_z_doubleSpinBox.valueChanged.connect(self._apply_controls_to_scene)

        self.ui.Tetrode_Parameters_Spikeling2_x_doubleSpinBox.valueChanged.connect(self._apply_controls_to_scene)
        self.ui.Tetrode_Parameters_Spikeling2_y_doubleSpinBox.valueChanged.connect(self._apply_controls_to_scene)
        self.ui.Tetrode_Parameters_Spikeling2_z_doubleSpinBox.valueChanged.connect(self._apply_controls_to_scene)

        self.ui.Tetrode_Parameters_Spikeling3_x_doubleSpinBox.valueChanged.connect(self._apply_controls_to_scene)
        self.ui.Tetrode_Parameters_Spikeling3_y_doubleSpinBox.valueChanged.connect(self._apply_controls_to_scene)
        self.ui.Tetrode_Parameters_Spikeling3_z_doubleSpinBox.valueChanged.connect(self._apply_controls_to_scene)

        self.ui.Tetrode_Parameters_Electrode_x_doubleSpinBox.valueChanged.connect(self._apply_controls_to_scene)
        self.ui.Tetrode_Parameters_Electrode_y_doubleSpinBox.valueChanged.connect(self._apply_controls_to_scene)
        self.ui.Tetrode_Parameters_Electrode_z_doubleSpinBox.valueChanged.connect(self._apply_controls_to_scene)
        self.ui.Tetrode_Parameters_Electrode_Spacing_doubleSpinBox.valueChanged.connect(self._apply_controls_to_scene)

        self.ui.Tetrode_Parameters_Electrode_Rotx_spinBox.valueChanged.connect(self._apply_controls_to_scene)
        self.ui.Tetrode_Parameters_Electrode_Roty_spinBox.valueChanged.connect(self._apply_controls_to_scene)
        self.ui.Tetrode_Parameters_Electrode_Rotz_spinBox.valueChanged.connect(self._apply_controls_to_scene)

        self.ui.Tetrode_Parameters_View_ShowLabels_checkBox.toggled.connect(self._apply_view_options)
        self.ui.Tetrode_Parameters_View_ShowDistance_checkBox.toggled.connect(self._apply_view_options)
        self.ui.Tetrode_Parameters_View_SnaToGrid_checkBox.toggled.connect(self._apply_view_options)
        self.ui.Tetrode_Parameters_View_GridSize_doubleSpinBox.valueChanged.connect(self._apply_view_options)

        self.ui.Tetrode_Parameters_View_Center_pushButton.clicked.connect(self._center_on_electrode)
        self.ui.Tetrode_Parameters_View_RFeset_pushButton.clicked.connect(self.reset_geometry)
        self.ui.Tetrode_Save_pushButton.clicked.connect(self._on_save_clicked)
        self.ui.Tetrode_Close_pushButton.clicked.connect(self.close)

        self.ui.Tetrode_graphicsView.viewResized.connect(self._position_scale_bar_overlay)

    # -------------------------------------------------------------
    # Reset
    # -------------------------------------------------------------
    def reset_geometry(self) -> None:
        self._syncing_controls = True
        try:
            self.ui.Tetrode_Parameters_Spikeling1_x_doubleSpinBox.setValue(self.neuron_defaults["Main Neuron"].x/10)
            self.ui.Tetrode_Parameters_Spikeling1_y_doubleSpinBox.setValue(self.neuron_defaults["Main Neuron"].y/10)
            self.ui.Tetrode_Parameters_Spikeling1_z_doubleSpinBox.setValue(self.neuron_defaults["Main Neuron"].z/10)

            self.ui.Tetrode_Parameters_Spikeling2_x_doubleSpinBox.setValue(self.neuron_defaults["Aux Neuron 1"].x/10)
            self.ui.Tetrode_Parameters_Spikeling2_y_doubleSpinBox.setValue(self.neuron_defaults["Aux Neuron 1"].y/10)
            self.ui.Tetrode_Parameters_Spikeling2_z_doubleSpinBox.setValue(self.neuron_defaults["Aux Neuron 1"].z/10)

            self.ui.Tetrode_Parameters_Spikeling3_x_doubleSpinBox.setValue(self.neuron_defaults["Aux Neuron 2"].x/10)
            self.ui.Tetrode_Parameters_Spikeling3_y_doubleSpinBox.setValue(self.neuron_defaults["Aux Neuron 2"].y/10)
            self.ui.Tetrode_Parameters_Spikeling3_z_doubleSpinBox.setValue(self.neuron_defaults["Aux Neuron 2"].z/10)

            self.ui.Tetrode_Parameters_Electrode_x_doubleSpinBox.setValue(self.neuron_defaults["Tetrode"].x/10)
            self.ui.Tetrode_Parameters_Electrode_y_doubleSpinBox.setValue(self.neuron_defaults["Tetrode"].y/10)
            self.ui.Tetrode_Parameters_Electrode_z_doubleSpinBox.setValue(self.neuron_defaults["Tetrode"].z/10)

            self.ui.Tetrode_Parameters_Electrode_Spacing_doubleSpinBox.setValue(25.0)
            self.ui.Tetrode_Parameters_Electrode_Rotx_spinBox.setValue(0)
            self.ui.Tetrode_Parameters_Electrode_Roty_spinBox.setValue(0)
            self.ui.Tetrode_Parameters_Electrode_Rotz_spinBox.setValue(0)

            self.ui.Tetrode_Parameters_View_GridSize_doubleSpinBox.setValue(1.0)
            self.ui.Tetrode_graphicsView.reset_zoom()
        finally:
            self._syncing_controls = False

        self._apply_view_options()
        self._apply_controls_to_scene()
        self._center_initial_view()
        self._update_selected_readout("None")

        self.scene.update(self.scene.sceneRect())
        self.ui.Tetrode_graphicsView.viewport().update()

    # -------------------------------------------------------------
    # Apply controls to items
    # -------------------------------------------------------------
    def _apply_controls_to_scene(self) -> None:
        if self._syncing_controls:
            return

        self._syncing_controls = True
        try:
            self.neuron_main.setPos(
                self.ui.Tetrode_Parameters_Spikeling1_x_doubleSpinBox.value()*10,
                self.ui.Tetrode_Parameters_Spikeling1_y_doubleSpinBox.value()*10,
            )
            self.neuron_main.set_depth(self.ui.Tetrode_Parameters_Spikeling1_z_doubleSpinBox.value()*10)

            self.neuron_aux1.setPos(
                self.ui.Tetrode_Parameters_Spikeling2_x_doubleSpinBox.value()*10,
                self.ui.Tetrode_Parameters_Spikeling2_y_doubleSpinBox.value()*10,
            )
            self.neuron_aux1.set_depth(self.ui.Tetrode_Parameters_Spikeling2_z_doubleSpinBox.value()*10)

            self.neuron_aux2.setPos(
                self.ui.Tetrode_Parameters_Spikeling3_x_doubleSpinBox.value()*10,
                self.ui.Tetrode_Parameters_Spikeling3_y_doubleSpinBox.value()*10,
            )
            self.neuron_aux2.set_depth(self.ui.Tetrode_Parameters_Spikeling3_z_doubleSpinBox.value()*10)

            self.tetrode_item.setPos(
                self.ui.Tetrode_Parameters_Electrode_x_doubleSpinBox.value()*10,
                self.ui.Tetrode_Parameters_Electrode_y_doubleSpinBox.value()*10,
            )
            self.tetrode_item.set_depth(self.ui.Tetrode_Parameters_Electrode_z_doubleSpinBox.value()*10)
            self.tetrode_item.set_contact_spacing(self.ui.Tetrode_Parameters_Electrode_Spacing_doubleSpinBox.value()*10)

            # For now only RotZ affects the 2D drawing.
            self.tetrode_item.setRotation(self.ui.Tetrode_Parameters_Electrode_Rotz_spinBox.value())
        finally:
            self._syncing_controls = False

        self._refresh_distance_lines()
        self._update_distance_readout()

    # -------------------------------------------------------------
    # View options
    # -------------------------------------------------------------
    def _snap_value_to_grid(self, value: float, grid_size: float) -> float:
        if grid_size <= 0:
            return value
        return round(value / grid_size) * grid_size

    def _snap_item_now(self, item) -> None:
        grid_size = self.ui.Tetrode_Parameters_View_GridSize_doubleSpinBox.value() * 10.0
        if grid_size <= 0:
            return

        x = self._snap_value_to_grid(item.x(), grid_size)
        y = self._snap_value_to_grid(item.y(), grid_size)
        item.setPos(x, y)

    def _apply_view_options(self) -> None:
        grid_size = self.ui.Tetrode_Parameters_View_GridSize_doubleSpinBox.value() * 10
        show_labels = self.ui.Tetrode_Parameters_View_ShowLabels_checkBox.isChecked()
        show_distance = self.ui.Tetrode_Parameters_View_ShowDistance_checkBox.isChecked()
        snap_to_grid = self.ui.Tetrode_Parameters_View_SnaToGrid_checkBox.isChecked()

        self.scene.set_grid_size(grid_size)

        for item in (self.neuron_main, self.neuron_aux1, self.neuron_aux2, self.tetrode_item):
            item.grid_size = grid_size
            item.snap_to_grid = snap_to_grid
            item.set_show_label(show_labels)

            if snap_to_grid:
                self._snap_item_now(item)

        self._refresh_distance_lines(force_show=show_distance)
        self._update_distance_readout()
        self._update_grid_scale_overlay()
        self._update_scale_bar_overlay()

    def _refresh_distance_lines(self, force_show: bool | None = None) -> None:
        for line_item in self._distance_lines:
            self.scene.removeItem(line_item)
        self._distance_lines.clear()

        show = (
            self.ui.Tetrode_Parameters_View_ShowDistance_checkBox.isChecked()
            if force_show is None
            else force_show
        )
        if not show:
            return

        pen = QPen(DISTANCE, 5, Qt.DashLine)
        probe_center = self.tetrode_item.scenePos()

        for neuron in (self.neuron_main, self.neuron_aux1, self.neuron_aux2):
            line = self.scene.addLine(
                probe_center.x(),
                probe_center.y(),
                neuron.scenePos().x(),
                neuron.scenePos().y(),
                pen,
            )
            line.setZValue(-10)
            self._distance_lines.append(line)

    # -------------------------------------------------------------
    # Sync dragged item -> controls
    # -------------------------------------------------------------
    def _sync_item_to_spinboxes(self, spin_x, spin_y, x_value: float, y_value: float) -> None:
        if self._syncing_controls:
            return

        self._syncing_controls = True
        try:
            spin_x.setValue(x_value / 10.0)
            spin_y.setValue(y_value / 10.0)
        finally:
            self._syncing_controls = False

        self._refresh_distance_lines()
        self._update_distance_readout()

    # -------------------------------------------------------------
    # Readout updates
    # -------------------------------------------------------------
    def _update_cursor_readout(self, x_value: float, y_value: float) -> None:
        self.readout_cursor.setText(f"Cursor: X={x_value/10:.1f} µm  Y={y_value/10:.1f} µm")

    def _update_zoom_readout(self, zoom_value: float) -> None:
        self.readout_zoom.setText(f"Zoom: {zoom_value * 100:.0f}%")
        self._update_scale_bar_overlay()
        self._position_scale_bar_overlay()

    def _update_selected_readout(self, name: str) -> None:
        self.readout_selected.setText(f"Selected: {name}")

    def _update_distance_readout(self) -> None:
        ex = self.tetrode_item.x()
        ey = self.tetrode_item.y()
        ez = self.tetrode_item.depth_z

        def distance_to(neuron) -> float:
            dx = neuron.x() - ex
            dy = neuron.y() - ey
            dz = neuron.depth_z - ez
            return math.sqrt(dx * dx + dy * dy + dz * dz)

        d1 = distance_to(self.neuron_main)
        d2 = distance_to(self.neuron_aux1)
        d3 = distance_to(self.neuron_aux2)

        self.readout_distance_n1.setText(f"Main Neuron  ↔ Electrode: {d1/10:.1f} µm")
        self.readout_distance_n2.setText(f"Aux Neuron 1 ↔ Electrode: {d2/10:.1f} µm")
        self.readout_distance_n3.setText(f"Aux Neuron 2 ↔ Electrode: {d3/10:.1f} µm")

    # -------------------------------------------------------------
    # Geometry export for extracellular model
    # -------------------------------------------------------------
    @staticmethod
    def _rotate_xyz(local_xyz: tuple[float, float, float], rx_deg: float, ry_deg: float, rz_deg: float) -> tuple[float, float, float]:
        """
        Rotate a local 3D vector by Rx, then Ry, then Rz.
        Angles are in degrees. Units are preserved (µm in / µm out).
        """
        x, y, z = local_xyz

        rx = math.radians(rx_deg)
        ry = math.radians(ry_deg)
        rz = math.radians(rz_deg)

        # Rx
        cy = math.cos(rx)
        sy = math.sin(rx)
        y, z = (y * cy - z * sy), (y * sy + z * cy)

        # Ry
        cy = math.cos(ry)
        sy = math.sin(ry)
        x, z = (x * cy + z * sy), (-x * sy + z * cy)

        # Rz
        cz = math.cos(rz)
        sz = math.sin(rz)
        x, y = (x * cz - y * sz), (x * sz + y * cz)

        return x, y, z

    def _get_neuron_positions_um(self) -> dict[str, dict]:
        return {
            "main": {
                "name": "Main Neuron",
                "x_um": float(self.ui.Tetrode_Parameters_Spikeling1_x_doubleSpinBox.value()),
                "y_um": float(self.ui.Tetrode_Parameters_Spikeling1_y_doubleSpinBox.value()),
                "z_um": float(self.ui.Tetrode_Parameters_Spikeling1_z_doubleSpinBox.value()),
            },
            "aux1": {
                "name": "Aux Neuron 1",
                "x_um": float(self.ui.Tetrode_Parameters_Spikeling2_x_doubleSpinBox.value()),
                "y_um": float(self.ui.Tetrode_Parameters_Spikeling2_y_doubleSpinBox.value()),
                "z_um": float(self.ui.Tetrode_Parameters_Spikeling2_z_doubleSpinBox.value()),
            },
            "aux2": {
                "name": "Aux Neuron 2",
                "x_um": float(self.ui.Tetrode_Parameters_Spikeling3_x_doubleSpinBox.value()),
                "y_um": float(self.ui.Tetrode_Parameters_Spikeling3_y_doubleSpinBox.value()),
                "z_um": float(self.ui.Tetrode_Parameters_Spikeling3_z_doubleSpinBox.value()),
            },
        }

    def _get_tetrode_center_um(self) -> dict[str, float]:
        return {
            "x_um": float(self.ui.Tetrode_Parameters_Electrode_x_doubleSpinBox.value()),
            "y_um": float(self.ui.Tetrode_Parameters_Electrode_y_doubleSpinBox.value()),
            "z_um": float(self.ui.Tetrode_Parameters_Electrode_z_doubleSpinBox.value()),
        }

    def get_contact_positions_um(self) -> list[dict]:
        """
        Return the 4 tetrode contact coordinates in world space (µm).
        Contact spacing is the nearest-neighbour spacing between contacts.
        """
        center = self._get_tetrode_center_um()
        spacing_um = float(self.ui.Tetrode_Parameters_Electrode_Spacing_doubleSpinBox.value())

        rx_deg = float(self.ui.Tetrode_Parameters_Electrode_Rotx_spinBox.value())
        ry_deg = float(self.ui.Tetrode_Parameters_Electrode_Roty_spinBox.value())
        rz_deg = float(self.ui.Tetrode_Parameters_Electrode_Rotz_spinBox.value())

        r_um = spacing_um / math.sqrt(2.0)

        local_contacts = [
            ("E1", (0.0, -r_um, 0.0)),
            ("E2", (r_um, 0.0, 0.0)),
            ("E3", (0.0, r_um, 0.0)),
            ("E4", (-r_um, 0.0, 0.0)),
        ]

        contacts = []
        for idx, (name, local_xyz) in enumerate(local_contacts, start=1):
            dx, dy, dz = self._rotate_xyz(local_xyz, rx_deg, ry_deg, rz_deg)
            contacts.append(
                {
                    "index": idx,
                    "name": name,
                    "x_um": center["x_um"] + dx,
                    "y_um": center["y_um"] + dy,
                    "z_um": center["z_um"] + dz,
                }
            )

        return contacts

    def get_distance_matrix_um(self) -> dict[str, dict[str, float]]:
        neurons = self._get_neuron_positions_um()
        contacts = self.get_contact_positions_um()

        matrix: dict[str, dict[str, float]] = {}

        for neuron_key, neuron in neurons.items():
            per_contact: dict[str, float] = {}
            for contact in contacts:
                dx = neuron["x_um"] - contact["x_um"]
                dy = neuron["y_um"] - contact["y_um"]
                dz = neuron["z_um"] - contact["z_um"]
                per_contact[contact["name"]] = math.sqrt(dx * dx + dy * dy + dz * dz)
            matrix[neuron_key] = per_contact

        return matrix

    def get_geometry_payload(self) -> dict:
        return {
            "neurons": self._get_neuron_positions_um(),
            "tetrode": {
                "center_um": self._get_tetrode_center_um(),
                "spacing_um": float(self.ui.Tetrode_Parameters_Electrode_Spacing_doubleSpinBox.value()),
                "rotation_deg": {
                    "x": float(self.ui.Tetrode_Parameters_Electrode_Rotx_spinBox.value()),
                    "y": float(self.ui.Tetrode_Parameters_Electrode_Roty_spinBox.value()),
                    "z": float(self.ui.Tetrode_Parameters_Electrode_Rotz_spinBox.value()),
                },
                "contacts_um": self.get_contact_positions_um(),
            },
            "distance_matrix_um": self.get_distance_matrix_um(),
        }

    def _on_save_clicked(self) -> None:
        payload = self.get_geometry_payload()
        self.geometrySaved.emit(payload)

        # Optional console trace while integrating
        print("Tetrode geometry saved:")
        print(payload)


    # -------------------------------------------------------------
    # View helpers
    # -------------------------------------------------------------
    def _center_initial_view(self) -> None:
        pos = self.tetrode_item.scenePos()
        self.ui.Tetrode_graphicsView.centerOn(pos.x() + 150.0, pos.y())

    def _ensure_item_inside_scene(self, item, margin: float = 200.0) -> None:
        wanted_rect = item.sceneBoundingRect().adjusted(-margin, -margin, margin, margin)
        current_rect = self.scene.sceneRect()
        if not current_rect.contains(wanted_rect):
            self.scene.setSceneRect(current_rect.united(wanted_rect))

    def _center_on_electrode(self) -> None:
        self._ensure_item_inside_scene(self.tetrode_item)
        self.ui.Tetrode_graphicsView.centerOn(self.tetrode_item.scenePos())
        self.ui.Tetrode_graphicsView.viewport().update()


# ---------------------------------------------------------------------
# Run standalone
# ---------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    window = TetrodeGeometryWindow()
    window.show()
    sys.exit(app.exec())