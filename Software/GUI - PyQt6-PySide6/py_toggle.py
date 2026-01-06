# py_toggle.py
# Custom animated toggle switch for PySide6 (QCheckBox subclass)

from __future__ import annotations

import re
from typing import Optional

from PySide6.QtCore import QEasingCurve, Property, QPropertyAnimation, QPoint, QRect, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QCheckBox


class PyToggle(QCheckBox):
    """
    Animated toggle switch (QCheckBox) rendered as a rounded track + moving circle.

    Runtime theme updates:
        - set_bg_color(...)
        - set_active_color(...)
        - set_circle_color(...)
        - apply_style(...)
    """

    def __init__(
        self,
        width: int = 40,
        height: int = 14,
        border: int = 1,
        bg_color: str = "color: rgb(108, 113, 196)",  # kept for backward compatibility
        circle_color: str = "#DDD",
        active_color: str = "00BCff",                  # kept for backward compatibility
        animation_curve: QEasingCurve.Type = QEasingCurve.OutBounce,
        animation_duration_ms: int = 500,
        parent=None,
    ):
        super().__init__(parent)

        # Geometry / interaction
        self.setFixedSize(width, height)
        self.setCursor(Qt.PointingHandCursor)
        self.border = int(border)

        # Colors (normalized to something QColor can parse reliably)
        self._bg_color = self._normalize_color(bg_color)
        self._circle_color = self._normalize_color(circle_color)
        self._active_color = self._normalize_color(active_color)

        # Animation
        self._circle_position = float(self.border)
        self.animation = QPropertyAnimation(self, b"circle_position", self)
        self.animation.setEasingCurve(animation_curve)
        self.animation.setDuration(int(animation_duration_ms))

        # State
        self.stateChanged.connect(self.start_transition)

    # -----------------------
    # Runtime styling API
    # -----------------------

    @staticmethod
    def _normalize_color(c: str) -> str:
        """
        Accepts "#RRGGBB", "RRGGBB", "rgb(r,g,b)", QColor names, and strings like:
            "color: rgb(...)" or "background-color: ..."
        Returns a normalized string that QColor(...) can parse.
        """
        if c is None:
            return "#000000"

        s = str(c).strip().rstrip(";").strip()

        # Handle "color: rgb(...)" / "background-color: ..." patterns
        if ":" in s and s.lower().startswith(("color:", "background:", "background-color:")):
            s = s.split(":", 1)[1].strip().rstrip(";").strip()

        # Handle bare hex without '#'
        if re.fullmatch(r"[0-9a-fA-F]{6}", s):
            s = "#" + s

        return s

    def set_bg_color(self, color: str) -> None:
        self._bg_color = self._normalize_color(color)
        self.update()

    def set_active_color(self, color: str) -> None:
        self._active_color = self._normalize_color(color)
        self.update()

    def set_circle_color(self, color: str) -> None:
        self._circle_color = self._normalize_color(color)
        self.update()

    def apply_style(
        self,
        *,
        bg_color: Optional[str] = None,
        active_color: Optional[str] = None,
        circle_color: Optional[str] = None,
    ) -> None:
        if bg_color is not None:
            self._bg_color = self._normalize_color(bg_color)
        if active_color is not None:
            self._active_color = self._normalize_color(active_color)
        if circle_color is not None:
            self._circle_color = self._normalize_color(circle_color)
        self.update()

    # -----------------------
    # Animated property
    # -----------------------

    @Property(float)
    def circle_position(self) -> float:
        return float(self._circle_position)

    @circle_position.setter
    def circle_position(self, pos: float) -> None:
        self._circle_position = float(pos)
        self.update()

    def start_transition(self, value: int) -> None:
        self.animation.stop()

        if value:  # checked
            self.animation.setEndValue(self.width() - self.height())
        else:      # unchecked
            self.animation.setEndValue(self.border)

        self.animation.start()

    # -----------------------
    # Interaction / painting
    # -----------------------

    def hitButton(self, pos: QPoint) -> bool:
        # Full widget clickable area
        return self.contentsRect().contains(pos)

    def paintEvent(self, e) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen)

        rect = QRect(0, 0, self.width(), self.height())
        radius = self.height() / 2

        # Track color depends on checked state
        track_color = self._active_color if self.isChecked() else self._bg_color

        # Draw track
        p.setBrush(QColor(track_color))
        p.drawRoundedRect(0, 0, rect.width(), rect.height(), radius, radius)

        # Draw circle
        p.setBrush(QColor(self._circle_color))
        d = self.height() - 2 * self.border
        p.drawEllipse(int(self._circle_position), self.border, d, d)

        p.end()
