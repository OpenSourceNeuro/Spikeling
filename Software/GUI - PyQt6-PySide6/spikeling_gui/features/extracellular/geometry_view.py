from __future__ import annotations

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QFrame, QGraphicsView



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
        if event.button() == Qt.MiddleButton and self.scene() is not None:
            # Give the view room to pan even when the whole scene fits.
            visible = self.mapToScene(self.viewport().rect()).boundingRect()
            margin_x = visible.width()
            margin_y = visible.height()
            pan_rect = visible.adjusted(-margin_x, -margin_y, margin_x, margin_y)
            self.setSceneRect(self.scene().sceneRect().united(pan_rect))
            self.centerOn(visible.center())

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

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self.viewResized.emit()
