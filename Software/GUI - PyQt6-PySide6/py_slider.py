# py_slider.py

from PySide6.QtWidgets import QSlider, QStyleOptionSlider, QStyle
from PySide6.QtGui import QPainter, QPen, QPalette
from PySide6.QtCore import Qt, QPoint


def _slider_qss(groove_color: str, fill_color: str, handle_image: str | None,
                height: int, margin_h: int) -> str:
    handle_part = ""
    if handle_image:
        handle_part = f"""
        QSlider::handle:horizontal {{
            image: url({handle_image});
            width: 20px;
            height: 20px;
            margin-top: -7px;
            margin-bottom: -7px;
            margin-left: -1px;
            margin-right: 0px;
        }}
        """

    return f"""
        QSlider::groove:horizontal {{
            height: {height}px;
            background: {groove_color};
            border-radius: {height // 2}px;
            margin: 0px {margin_h}px;
        }}
        QSlider::sub-page:horizontal {{
            background: {fill_color};
            border-radius: {height // 2}px;
            margin: 0px {margin_h}px;
            margin-right: -2px;
        }}
        QSlider::sub-page:horizontal:disabled {{
            background: #93A1A1;
        }}
        QSlider::add-page:horizontal {{
            background: {groove_color};
            border-radius: {height // 2}px;
            margin: 0px {margin_h}px;
        }}
        {handle_part}
    """


class TickSlider(QSlider):
    def __init__(self, *args, num_ticks: int = 0, **kwargs):
        super().__init__(*args, **kwargs)
        self._num_ticks = max(0, int(num_ticks))

        # Store style params so we can update later
        self._groove_color = "#000000"
        self._fill_color = "#ffffff"
        self._handle_image = None
        self._height = 6
        self._margin_h = 10

    def apply_style(self, *, groove_color: str, fill_color: str,
                    handle_image: str | None, height: int, margin_h: int) -> None:
        self._groove_color = groove_color
        self._fill_color = fill_color
        self._handle_image = handle_image
        self._height = height
        self._margin_h = margin_h
        self.setStyleSheet(_slider_qss(groove_color, fill_color, handle_image, height, margin_h))
        self.update()

    def set_fill_color(self, fill_color: str) -> None:
        self._fill_color = fill_color
        self.setStyleSheet(_slider_qss(self._groove_color, self._fill_color,
                                       self._handle_image, self._height, self._margin_h))
        self.update()

    def set_num_ticks(self, n: int):
        self._num_ticks = max(0, int(n))
        self.update()

    def num_ticks(self) -> int:
        return self._num_ticks

    def paintEvent(self, event):
        super().paintEvent(event)

        if self.tickPosition() == QSlider.NoTicks or self._num_ticks <= 0:
            return

        opt = QStyleOptionSlider()
        self.initStyleOption(opt)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(self.palette().color(QPalette.Light))
        painter.setPen(pen)

        min_v = self.minimum()
        max_v = self.maximum()
        count = self._num_ticks

        if count == 1:
            values = [min_v]
        else:
            span = max_v - min_v
            values = [min_v + round(span * i / (count - 1)) for i in range(count)]

        groove = self.style().subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderGroove, self)
        y_below_1 = groove.bottom() + 2
        y_below_2 = y_below_1 + 4
        y_above_1 = groove.top() - 2
        y_above_2 = y_above_1 - 4

        if self.orientation() == Qt.Horizontal:
            for value in values:
                opt.sliderPosition = value
                opt.sliderValue = value
                handle_rect = self.style().subControlRect(
                    QStyle.CC_Slider, opt, QStyle.SC_SliderHandle, self
                )
                x = handle_rect.center().x()

                if self.tickPosition() in (QSlider.TicksBelow, QSlider.TicksBothSides):
                    painter.drawLine(QPoint(x, y_below_1), QPoint(x, y_below_2))
                if self.tickPosition() in (QSlider.TicksAbove, QSlider.TicksBothSides):
                    painter.drawLine(QPoint(x, y_above_1), QPoint(x, y_above_2))

        painter.end()


def configure_styled_slider(
        ui,
        slider_attr_name: str,
        groove_color: str,
        fill_color: str,
        num_ticks: int = 0,
        handle_image: str | None = None,
        height: int = 6,
        margin_h: int = 10,
):
    old = getattr(ui, slider_attr_name)
    parent = old.parent()
    layout = parent.layout()
    idx = layout.indexOf(old)

    s = TickSlider(parent, num_ticks=num_ticks)

    # Keep identity/behaviour consistent
    s.setObjectName(old.objectName())   # helpful if you ever move to global QSS selectors
    s.setOrientation(old.orientation())
    s.setRange(old.minimum(), old.maximum())
    s.setSingleStep(old.singleStep())
    s.setPageStep(old.pageStep())
    s.setValue(old.value())
    s.setEnabled(old.isEnabled())

    if num_ticks > 0:
        s.setTickPosition(QSlider.TicksBelow)
    else:
        s.setTickPosition(QSlider.NoTicks)

    # Apply initial style and remember params for later updates
    s.apply_style(
        groove_color=groove_color,
        fill_color=fill_color,
        handle_image=handle_image,
        height=height,
        margin_h=margin_h,
    )

    layout.insertWidget(idx, s)
    old.hide()
    old.deleteLater()

    setattr(ui, slider_attr_name, s)
    return s


# Optional convenience function (useful from MainWindow/theme code)
def set_slider_fill_color(ui, slider_attr_name: str, fill_color: str) -> None:
    s = getattr(ui, slider_attr_name)
    if hasattr(s, "set_fill_color"):
        s.set_fill_color(fill_color)
    else:
        # Fallback: if it's not your TickSlider for some reason
        qss = s.styleSheet()
        # If you want a robust fallback, rebuild QSS instead of string replace.
        s.setStyleSheet(qss)
        s.update()
