from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
import Settings

class PyToggle(QCheckBox):
    def __init__(
            self,
            width = 40,
            height = 14,
            border = 1,
            bg_color = "color: rgb(108, 113, 196)",
            circle_color = "#DDD",
            active_color = "00BCff",
            animation_curve = QEasingCurve.OutBounce
    ):
        QCheckBox.__init__(self)

        # Set default parameters
        self.setFixedSize(width, height)
        self.setCursor(Qt.PointingHandCursor)

        self.border = border

        # Set colours
        self._bg_color = bg_color
        self._circle_color = circle_color
        self._active_color = active_color

        # Create animation
        self._circle_position = self.border
        self.animation = QPropertyAnimation(self, b"circle_position", self)
        self.animation.setEasingCurve(animation_curve)
        self.animation.setDuration(500)

        # Connect state changed
        self.stateChanged.connect(self.start_transition)

    # Create new set and get properties
    @Property(float)
    def circle_position(self):
        return self._circle_position

    @circle_position.setter
    def circle_position(self, pos):
        self._circle_position = pos
        self.update()

    def start_transition(self, value):
        self.animation.stop()
        if value:
            self.animation.setEndValue(self.width() - self.height())
        else:
            self.animation.setEndValue(self.border)
        self.animation.start()

    # Set new hit area
    def hitButton(self, pos: QPoint):
        return self.contentsRect().contains(pos)

    # Draw new items
    def paintEvent(self, e):
        # set Painter
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # Set as no pen
        p.setPen(Qt.NoPen)

        # Draw rectangle that will contain the widget
        rect = QRect(0, 0, self.width(), self.height())

        # Check if .isChecked
        if not self.isChecked():
            # Draw background
            p.setBrush(QColor(self._bg_color))
            p.drawRoundedRect(0, 0, rect.width(), self.height(), self.height()/2, self.height()/2)

            # Draw circle
            p.setBrush(QColor(self._circle_color))
            p.drawEllipse(self._circle_position, self.border, self.height()-2*self.border, self.height()-2*self.border)

        else:
            # Draw background
            p.setBrush(QColor(self._active_color))
            p.drawRoundedRect(0, 0, rect.width(), self.height(), self.height()/2, self.height()/2)

            # Draw circle
            p.setBrush(QColor(self._circle_color))
            p.drawEllipse(self._circle_position, self.border, self.height()-2*self.border, self.height()-2*self.border)

        # End draw
        p.end()
