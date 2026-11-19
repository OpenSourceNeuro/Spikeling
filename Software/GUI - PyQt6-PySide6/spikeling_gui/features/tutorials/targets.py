"""Resolve live UI controls and reveal only their navigation container.

Never clicks scientific toggles, starts recordings or changes model parameters.
Dynamic PyToggle objects are registered on ``host.ui`` after UI setup.
"""
from __future__ import annotations

from PySide6.QtWidgets import QWidget, QAbstractButton


class WidgetTargetResolver:
    def __init__(self, host):
        self.host = host

    def resolve(self, object_name: str | None) -> QWidget | None:
        if not object_name:
            return None
        widget = getattr(self.host.ui, object_name, None)
        if not isinstance(widget, QWidget):
            widget = self.host.findChild(QWidget, object_name)
        return widget if isinstance(widget, QWidget) else None

    def visible(self, object_name: str | None) -> bool:
        widget = self.resolve(object_name)
        return bool(widget and widget.isVisible() and widget.width() >= 10 and widget.height() >= 10)

    def can_reveal(self, panel_name: str | None) -> bool:
        return isinstance(self.resolve(panel_name), QAbstractButton)

    def reveal(self, panel_name: str | None) -> bool:
        button = self.resolve(panel_name)
        if not isinstance(button, QAbstractButton) or not button.isEnabled():
            return False
        button.click()  # GUI navigation only, never scientific parameter toggles.
        return True
