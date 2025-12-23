from PySide6.QtWidgets import QSlider, QStyleOptionSlider, QStyle
from PySide6.QtGui import QPainter, QPen, QPalette
from PySide6.QtCore import Qt, QPoint


class TickSlider(QSlider):
    def __init__(self, *args, num_ticks: int = 0, **kwargs):
        super().__init__(*args, **kwargs)
        self._num_ticks = max(0, int(num_ticks))

    def set_num_ticks(self, n: int):
        self._num_ticks = max(0, int(n))
        self.update()

    def num_ticks(self) -> int:
        return self._num_ticks

    def paintEvent(self, event):
        # Let Qt draw groove + handle using your stylesheet
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

        # Values corresponding to each tick
        if count == 1:
            values = [min_v]
        else:
            span = max_v - min_v
            values = [
                min_v + round(span * i / (count - 1))
                for i in range(count)
            ]

        # Use groove to define vertical placement
        groove = self.style().subControlRect(
            QStyle.CC_Slider, opt, QStyle.SC_SliderGroove, self
        )
        y_below_1 = groove.bottom() + 2
        y_below_2 = y_below_1 + 4
        y_above_1 = groove.top() - 2
        y_above_2 = y_above_1 - 4

        if self.orientation() == Qt.Horizontal:
            for value in values:
                # Ask style where the handle is for this value
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
    """
    Replace ui.<slider_attr_name> (a designer-created QSlider) by a TickSlider
    with custom groove/fill colors, optional handle image, and a given number
    of ticks across the slider.

    Example:
        configure_styled_slider(
            self.ui,
            "Spikeling_StimFre_slider",
            groove_color="#001E26",
            fill_color="#268BD2",
            num_ticks=11,
            handle_image=":/resources/resources/Handle.png",
        )
    """

    old = getattr(ui, slider_attr_name)
    parent = old.parent()
    layout = parent.layout()
    idx = layout.indexOf(old)

    # New slider instance
    s = TickSlider(parent, num_ticks=num_ticks)
    s.setOrientation(old.orientation())
    s.setRange(old.minimum(), old.maximum())
    s.setSingleStep(old.singleStep())
    s.setPageStep(old.pageStep())
    s.setValue(old.value())
    s.setEnabled(old.isEnabled())

    # Configure tick position (we use our own tick painting)
    if num_ticks > 0:
        s.setTickPosition(QSlider.TicksBelow)
    else:
        s.setTickPosition(QSlider.NoTicks)

    # Build stylesheet from parameters
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

    s.setStyleSheet(f"""
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
            border-radius: {height // 2}px;
            margin: 0px {margin_h}px;
            margin-right: -2px;          
        }}
        QSlider::add-page:horizontal {{
            background: {groove_color};
            border-radius: {height // 2}px;
            margin: 0px {margin_h}px;
        }}
        {handle_part}
    """)

    # Swap into layout in the same position
    layout.insertWidget(idx, s)
    old.hide()
    old.deleteLater()

    # Update ui reference
    setattr(ui, slider_attr_name, s)

    return s