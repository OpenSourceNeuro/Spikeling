from PySide6.QtWidgets import QSlider, QStyleOptionSlider, QStyle, QLineEdit, QToolTip
from PySide6.QtGui import QPainter, QPen, QPalette
from PySide6.QtCore import Qt, QPoint, QObject, QSignalBlocker, QTimer, Signal, Slot
import math


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



class SliderBinding(QObject):
    """
    Synchronise an integer slider with an editable numeric reading.

    Features:
        - Configurable text alignment.
        - Separate active and disabled reading styles.
        - Hardware-control text when disabled.
        - Reset to the configured default when disabled.
        - Conversion between slider positions and displayed values.
        - Validation of typed values when editing finishes.
        - Limited application requests during continuous slider movement.
        - Immediate application of the final value on release or commit.
        - Silent reconfiguration for controls such as CC/VC.

    Serial communication remains outside this class.
    """

    valueChanged = Signal(int)
    applyRequested = Signal(int)
    disableRequested = Signal()

    def __init__(
        self,
        slider,
        editor,
        *,
        alignment=None,
        active=True,
        default_position=None,
        disabled_text="Knob control",
        active_editor_style=None,
        disabled_editor_style=(
            "color: rgb(88, 110, 117);"
            "font-size: 9pt;"
            "font-weight: 400;"
        ),
        to_display=float,
        to_slider=float,
        format_value=lambda value: f"{value:g}",
        interval_ms=40,
    ):
        """Create the binding without requesting a device update."""
        super().__init__(slider)

        if not isinstance(editor, QLineEdit):
            raise TypeError(
                "SliderBinding requires a QLineEdit reading."
            )

        # Validate on commit so invalid text can be restored.
        if editor.validator() is not None or editor.inputMask():
            raise ValueError(
                "Use SliderBinding without a QLineEdit "
                "validator or input mask."
            )

        if interval_ms < 0:
            raise ValueError(
                "interval_ms must be zero or positive."
            )

        self.slider = slider
        self.editor = editor

        # Preserve Designer alignment unless explicitly overridden.
        if alignment is not None:
            self.editor.setAlignment(alignment)

        if default_position is None:
            default_position = slider.value()

        self._default_position = self._validate_position(
            default_position,
            slider.minimum(),
            slider.maximum(),
        )

        self._disabled_text = disabled_text

        self._active_editor_style = (
            editor.styleSheet()
            if active_editor_style is None
            else active_editor_style
        )

        self._disabled_editor_style = disabled_editor_style
        self._displayed_active_state = None

        self._to_display = to_display
        self._to_slider = to_slider
        self._format_value = format_value

        self._active = bool(active)
        self._value = (
            slider.value()
            if self._active
            else self._default_position
        )
        self._pending = False

        # Hold only the latest requested value between timer events.
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(interval_ms)
        self._timer.timeout.connect(self.flush)

        # Update the reading continuously while dragging.
        self.slider.setTracking(True)

        # Initialise widgets before connecting interaction signals.
        with QSignalBlocker(self.slider), QSignalBlocker(self.editor):
            self.slider.setValue(self._value)
            self.slider.setEnabled(self._active)
            self.editor.setEnabled(self._active)
            self._refresh_editor()

        self.slider.valueChanged.connect(
            self._on_slider_changed
        )
        self.slider.sliderReleased.connect(self.flush)
        self.editor.editingFinished.connect(
            self._commit_editor
        )

    @staticmethod
    def _validate_position(position, minimum, maximum):
        """Return a valid integer slider position or raise ValueError."""
        try:
            number = float(position)
        except (TypeError, ValueError, OverflowError) as error:
            raise ValueError(
                "Slider position must be a finite integer."
            ) from error

        if not math.isfinite(number) or not number.is_integer():
            raise ValueError(
                "Slider position must be a finite integer."
            )

        position = int(number)

        if not minimum <= position <= maximum:
            raise ValueError(
                "Slider position is outside the slider range."
            )

        return position

    @property
    def value(self):
        """Return the accepted integer slider position."""
        return self._value

    @property
    def active(self):
        """Return whether GUI control is enabled."""
        return self._active

    def _refresh_editor(self):
        """Display the accepted value or hardware-control text."""
        if self._active:
            text = self._format_value(
                self._to_display(self._value)
            )
        else:
            text = self._disabled_text

        # Avoid reapplying styles on every slider movement.
        if self._displayed_active_state != self._active:
            style = (
                self._active_editor_style
                if self._active
                else self._disabled_editor_style
            )

            self.editor.setStyleSheet(style)
            self._displayed_active_state = self._active

        with QSignalBlocker(self.editor):
            self.editor.setText(text)
            self.editor.setModified(False)

    def set_value(self, position, *, send=False, immediate=False):
        """
        Set the slider position and synchronise the reading.

        send=False:
            Update locally and cancel any pending application request.

        send=True:
            Request application when the accepted value changes.

        immediate=True:
            Flush any pending application request immediately.
        """
        position = self._validate_position(
            position,
            self.slider.minimum(),
            self.slider.maximum(),
        )

        if not send:
            self.cancel_pending()

        changed = position != self._value
        self._value = position

        with QSignalBlocker(self.slider):
            self.slider.setValue(position)

        self._refresh_editor()

        if changed:
            self.valueChanged.emit(position)

        if send and self._active:
            if changed:
                self._pending = True

            if immediate or self._timer.interval() == 0:
                self.flush()

            elif self._pending and not self._timer.isActive():
                # Do not restart an active timer on every movement.
                self._timer.start()

    def reconfigure(
        self,
        *,
        minimum,
        maximum,
        default_position,
        active_editor_style=None,
    ):
        """
        Change the range, default and active style without applying.

        Resets the slider to the new default, preserves its active state
        and cancels requests pending from the previous configuration.

        valueChanged still informs application code of a changed value.
        """
        # QSlider uses signed 32-bit integer limits.
        integer_minimum = -2147483648
        integer_maximum = 2147483647

        minimum = self._validate_position(
            minimum,
            integer_minimum,
            integer_maximum,
        )

        maximum = self._validate_position(
            maximum,
            integer_minimum,
            integer_maximum,
        )

        if minimum > maximum:
            raise ValueError(
                "Slider minimum must not exceed maximum."
            )

        default_position = self._validate_position(
            default_position,
            minimum,
            maximum,
        )

        # Validate everything before changing existing widget state.
        self.cancel_pending()

        with QSignalBlocker(self.slider), QSignalBlocker(self.editor):
            self.slider.setRange(minimum, maximum)
            self._default_position = default_position

            if active_editor_style is not None:
                self._active_editor_style = active_editor_style

            # Refresh colour even if active state has not changed.
            self._displayed_active_state = None

            self.set_value(default_position, send=False)

    @Slot(int)
    def _on_slider_changed(self, position):
        """Update the reading and schedule application."""
        self.set_value(position, send=True)

    @Slot()
    def _commit_editor(self):
        """Validate typed input and apply the nearest slider position."""
        if not self._active:
            self._refresh_editor()
            return

        try:
            # Accept decimal points or decimal commas, without units
            # or thousands separators.
            text = self.editor.text().strip().replace(",", ".")
            displayed_value = float(text)

            if not math.isfinite(displayed_value):
                raise ValueError

            position = float(
                self._to_slider(displayed_value)
            )

            if (
                not math.isfinite(position)
                or not self.slider.minimum()
                <= position
                <= self.slider.maximum()
            ):
                raise ValueError

            position = round(position)

        except (ValueError, OverflowError):
            self._refresh_editor()

            first = self._format_value(
                self._to_display(self.slider.minimum())
            )
            last = self._format_value(
                self._to_display(self.slider.maximum())
            )

            QToolTip.showText(
                self.editor.mapToGlobal(
                    self.editor.rect().bottomLeft()
                ),
                f"Enter a number within the range {first} to {last}.",
                self.editor,
            )
            return

        self.set_value(
            position,
            send=True,
            immediate=True,
        )

    @Slot(bool)
    def set_active(self, active):
        """Switch between GUI control and hardware control."""
        active = bool(active)

        if active == self._active:
            return

        # Change state before disabling widgets can trigger focus events.
        self._active = active
        self.cancel_pending()

        with QSignalBlocker(self.editor):
            if not active:
                # Reset locally without requesting a value command.
                self.set_value(
                    self._default_position,
                    send=False,
                )

            self.slider.setEnabled(active)
            self.editor.setEnabled(active)
            self._refresh_editor()

        if active:
            self.applyRequested.emit(self._value)
        else:
            self.disableRequested.emit()

    @Slot()
    def flush(self):
        """Request application of the latest pending value once."""
        self._timer.stop()

        if not self._active or not self._pending:
            return

        self._pending = False
        self.applyRequested.emit(self._value)

    @Slot()
    def cancel_pending(self):
        """Discard any scheduled application request."""
        self._timer.stop()
        self._pending = False

    @Slot()
    def apply_current(self):
        """Explicitly apply the current value, even if unchanged."""
        self.cancel_pending()

        if self._active:
            self.applyRequested.emit(self._value)

def configure_sliders(self):

    #######################################################
    # Neuron Interface
    configure_styled_slider(self.ui,
                            "Spikeling_Speed_slider",
                            groove_color="#586E75",
                            fill_color="#93A1A1",
                            num_ticks=11,
                            handle_image=":/resources/resources/Handle.png")

    # Stimulus Parameters
    configure_styled_slider(self.ui,
                            "Spikeling_StimFre_slider",
                            groove_color="#001E26",
                            fill_color="#268BD2",
                            num_ticks=11,
                            handle_image=":/resources/resources/Handle.png")
    configure_styled_slider(self.ui,
                            "Spikeling_StimStr_slider",
                            groove_color="#001E26",
                            fill_color="#268BD2",
                            num_ticks=11,
                            handle_image=":/resources/resources/Handle.png")

    # Neuron Parameters
    configure_styled_slider(self.ui,
                            "Spikeling_PatchClamp_slider",
                            groove_color="#001E26",
                            fill_color="#859900",
                            num_ticks=11,
                            handle_image=":/resources/resources/Handle.png")
    configure_styled_slider(self.ui,
                            "Spikeling_Noise_slider",
                            groove_color="#001E26",
                            fill_color="#859900",
                            num_ticks=11,
                            handle_image=":/resources/resources/Handle.png")
    configure_styled_slider(self.ui,
                            "Spikeling_PR_PhotoGain_slider",
                            groove_color="#001E26",
                            fill_color="#859900",
                            num_ticks=11,
                            handle_image=":/resources/resources/Handle.png")
    configure_styled_slider(self.ui,
                            "Spikeling_PR_Decay_slider",
                            groove_color="#001E26",
                            fill_color="#859900",
                            num_ticks=11,
                            handle_image=":/resources/resources/Handle.png")
    configure_styled_slider(self.ui,
                            "Spikeling_PR_Recovery_slider",
                            groove_color="#001E26",
                            fill_color="#859900",
                            num_ticks=11,
                            handle_image=":/resources/resources/Handle.png")

    # Pharmacology Parameters
    configure_styled_slider(self.ui,
                            "Spikeling_Pharmacology_TTX_slider",
                            groove_color="#001E26",
                            fill_color="#B58900")
    configure_styled_slider(self.ui,
                            "Spikeling_Pharmacology_TEA_slider",
                            groove_color="#001E26",
                            fill_color="#B58900")
    configure_styled_slider(self.ui,
                            "Spikeling_Pharmacology_4AP_slider",
                            groove_color="#001E26",
                            fill_color="#B58900")
    configure_styled_slider(self.ui,
                            "Spikeling_Pharmacology_Apamin_slider",
                            groove_color="#001E26",
                            fill_color="#B58900")
    configure_styled_slider(self.ui,
                            "Spikeling_Pharmacology_NBQX_slider",
                            groove_color="#001E26",
                            fill_color="#B58900")
    configure_styled_slider(self.ui,
                            "Spikeling_Pharmacology_APV_slider",
                            groove_color="#001E26",
                            fill_color="#B58900")
    configure_styled_slider(self.ui,
                            "Spikeling_Pharmacology_Gabazine_slider",
                            groove_color="#001E26",
                            fill_color="#B58900")
    configure_styled_slider(self.ui,
                            "Spikeling_Pharmacology_GVIA_slider",
                            groove_color="#001E26",
                            fill_color="#B58900")

    # Synapse1 Parameters
    configure_styled_slider(self.ui,
                            "Spikeling_Synapse1_slider",
                            groove_color="#001E26",
                            fill_color="#2AA198",
                            num_ticks=11,
                            handle_image=":/resources/resources/Handle.png")
    configure_styled_slider(self.ui,
                            "Spikeling_Synapse1_Decay_slider",
                            groove_color="#001E26",
                            fill_color="#2AA198",
                            num_ticks=15,
                            handle_image=":/resources/resources/Handle.png")

    # Synapse2 Parameters
    configure_styled_slider(self.ui,
                            "Spikeling_Synapse2_slider",
                            groove_color="#001E26",
                            fill_color="#D33682",
                            num_ticks=11,
                            handle_image=":/resources/resources/Handle.png")
    configure_styled_slider(self.ui,
                            "Spikeling_Synapse2_Decay_slider",
                            groove_color="#001E26",
                            fill_color="#D33682",
                            num_ticks=15,
                            handle_image=":/resources/resources/Handle.png")

    #######################################################
    # Neuron Emulator
    configure_styled_slider(self.ui,
                            "Emulator_Speed_slider",
                            groove_color="#586E75",
                            fill_color="#93A1A1",
                            num_ticks=11,
                            handle_image=":/resources/resources/Handle.png")

    configure_styled_slider(self.ui,
                            "Emulator_StimFre_slider",
                            groove_color="#001E26",
                            fill_color="#268BD2",
                            num_ticks=11,
                            handle_image=":/resources/resources/Handle.png")
    configure_styled_slider(self.ui,
                            "Emulator_StimStrSlider",
                            groove_color="#001E26",
                            fill_color="#268BD2",
                            num_ticks=11,
                            handle_image=":/resources/resources/Handle.png")
    configure_styled_slider(self.ui,
                            "Emulator_PR_PhotoGain_slider",
                            groove_color="#001E26",
                            fill_color="#859900",
                            num_ticks=11,
                            handle_image=":/resources/resources/Handle.png")
    configure_styled_slider(self.ui,
                            "Emulator_PR_Decay_slider",
                            groove_color="#001E26",
                            fill_color="#859900",
                            num_ticks=11,
                            handle_image=":/resources/resources/Handle.png")
    configure_styled_slider(self.ui,
                            "Emulator_PR_Recovery_slider",
                            groove_color="#001E26",
                            fill_color="#859900",
                            num_ticks=11,
                            handle_image=":/resources/resources/Handle.png")

    configure_styled_slider(self.ui,
                            "Emulator_PatchClamp_slider",
                            groove_color="#001E26",
                            fill_color="#859900",
                            num_ticks=11,
                            handle_image=":/resources/resources/Handle.png")
    configure_styled_slider(self.ui,
                            "Emulator_Noise_slider",
                            groove_color="#001E26",
                            fill_color="#859900",
                            num_ticks=11,
                            handle_image=":/resources/resources/Handle.png")
    configure_styled_slider(self.ui,
                            "Emulator_Synapse1_slider",
                            groove_color="#001E26",
                            fill_color="#2AA198",
                            num_ticks=11,
                            handle_image=":/resources/resources/Handle.png")
    configure_styled_slider(self.ui,
                            "Emulator_Synapse1_Decay_slider",
                            groove_color="#001E26",
                            fill_color="#2AA198",
                            num_ticks=15,
                            handle_image=":/resources/resources/Handle.png")
    configure_styled_slider(self.ui,
                            "Emulator_Synapse2_slider",
                            groove_color="#001E26",
                            fill_color="#D33682",
                            num_ticks=11,
                            handle_image=":/resources/resources/Handle.png")
    configure_styled_slider(self.ui,
                            "Emulator_Synapse2_Decay_slider",
                            groove_color="#001E26",
                            fill_color="#D33682",
                            num_ticks=15,
                            handle_image=":/resources/resources/Handle.png")

    configure_styled_slider(self.ui,
                            "Emulator_Syn1_PatchClamp_slider",
                            groove_color="#001E26",
                            fill_color="#859900",
                            num_ticks=15,
                            handle_image=":/resources/resources/Handle.png")
    configure_styled_slider(self.ui,
                            "Emulator_Syn1_Noise_slider",
                            groove_color="#001E26",
                            fill_color="#859900",
                            num_ticks=15,
                            handle_image=":/resources/resources/Handle.png")
    configure_styled_slider(self.ui,
                            "Emulator_Syn1_PR_PhotoGain_slider",
                            groove_color="#001E26",
                            fill_color="#859900",
                            num_ticks=15,
                            handle_image=":/resources/resources/Handle.png")
    configure_styled_slider(self.ui,
                            "Emulator_Syn1_PR_Decay_slider",
                            groove_color="#001E26",
                            fill_color="#859900",
                            num_ticks=15,
                            handle_image=":/resources/resources/Handle.png")
    configure_styled_slider(self.ui,
                            "Emulator_Syn1_PR_Recovery_slider",
                            groove_color="#001E26",
                            fill_color="#859900",
                            num_ticks=15,
                            handle_image=":/resources/resources/Handle.png")

    configure_styled_slider(self.ui,
                            "Emulator_Syn2_PatchClamp_slider",
                            groove_color="#001E26",
                            fill_color="#859900",
                            num_ticks=15,
                            handle_image=":/resources/resources/Handle.png")
    configure_styled_slider(self.ui,
                            "Emulator_Syn2_Noise_slider",
                            groove_color="#001E26",
                            fill_color="#859900",
                            num_ticks=15,
                            handle_image=":/resources/resources/Handle.png")
    configure_styled_slider(self.ui,
                            "Emulator_Syn2_PR_PhotoGain_slider",
                            groove_color="#001E26",
                            fill_color="#859900",
                            num_ticks=15,
                            handle_image=":/resources/resources/Handle.png")
    configure_styled_slider(self.ui,
                            "Emulator_Syn2_PR_Decay_slider",
                            groove_color="#001E26",
                            fill_color="#859900",
                            num_ticks=15,
                            handle_image=":/resources/resources/Handle.png")
    configure_styled_slider(self.ui,
                            "Emulator_Syn2_PR_Recovery_slider",
                            groove_color="#001E26",
                            fill_color="#859900",
                            num_ticks=15,
                            handle_image=":/resources/resources/Handle.png")





    configure_styled_slider(self.ui,
                            "Imaging_FrameRate_Slider",
                            groove_color="#001E26",
                            fill_color="#859900",
                            num_ticks=11,
                            handle_image=":/resources/resources/Handle.png")
    configure_styled_slider(self.ui,
                            "Imaging_PMT_Slider",
                            groove_color="#001E26",
                            fill_color="#859900",
                            num_ticks=11,
                            handle_image=":/resources/resources/Handle.png")
    configure_styled_slider(self.ui,
                            "Imaging_Laser_Slider",
                            groove_color="#001E26",
                            fill_color="#859900",
                            num_ticks=11,
                            handle_image=":/resources/resources/Handle.png")


    configure_styled_slider(self.ui,
                            "Imaging_CalciumRise_Slider",
                            groove_color="#001E26",
                            fill_color="#D33682",
                            num_ticks=11,
                            handle_image=":/resources/resources/Handle.png")
    configure_styled_slider(self.ui,
                            "Imaging_CalciumDecay_Slider",
                            groove_color="#001E26",
                            fill_color="#D33682",
                            num_ticks=11,
                            handle_image=":/resources/resources/Handle.png")
    configure_styled_slider(self.ui,
                            "Imaging_CalciumJump_Slider",
                            groove_color="#001E26",
                            fill_color="#D33682",
                            num_ticks=11,
                            handle_image=":/resources/resources/Handle.png")
    configure_styled_slider(self.ui,
                            "Imaging_CalciumNoise_Slider",
                            groove_color="#001E26",
                            fill_color="#D33682",
                            num_ticks=11,
                            handle_image=":/resources/resources/Handle.png")
    configure_styled_slider(self.ui,
                            "Imaging_CalciumBaseline_Slider",
                            groove_color="#001E26",
                            fill_color="#D33682",
                            num_ticks=11,
                            handle_image=":/resources/resources/Handle.png")


    configure_styled_slider(self.ui,
                            "Imaging_IndRise_Slider",
                            groove_color="#001E26",
                            fill_color="#859900",
                            num_ticks=11,
                            handle_image=":/resources/resources/Handle.png")
    configure_styled_slider(self.ui,
                            "Imaging_IndDecay_Slider",
                            groove_color="#001E26",
                            fill_color="#859900",
                            num_ticks=11,
                            handle_image=":/resources/resources/Handle.png")
    configure_styled_slider(self.ui,
                            "Imaging_FluoScale_Slider",
                            groove_color="#001E26",
                            fill_color="#859900",
                            num_ticks=11,
                            handle_image=":/resources/resources/Handle.png")
    configure_styled_slider(self.ui,
                            "Imaging_FluoScale_Slider",
                            groove_color="#001E26",
                            fill_color="#859900",
                            num_ticks=11,
                            handle_image=":/resources/resources/Handle.png")
    configure_styled_slider(self.ui,
                            "Imaging_FluoOffset_Slider",
                            groove_color="#001E26",
                            fill_color="#859900",
                            num_ticks=11,
                            handle_image=":/resources/resources/Handle.png")
    configure_styled_slider(self.ui,
                            "Imaging_FluoNoise_Slider",
                            groove_color="#001E26",
                            fill_color="#859900",
                            num_ticks=11,
                            handle_image=":/resources/resources/Handle.png")
    configure_styled_slider(self.ui,
                            "Imaging_kd_Slider",
                            groove_color="#001E26",
                            fill_color="#859900",
                            num_ticks=11,
                            handle_image=":/resources/resources/Handle.png")
    configure_styled_slider(self.ui,
                            "Imaging_Hill_Slider",
                            groove_color="#001E26",
                            fill_color="#859900",
                            num_ticks=11,
                            handle_image=":/resources/resources/Handle.png")
    configure_styled_slider(self.ui,
                            "Imaging_PhotoShotNoise_Slider",
                            groove_color="#001E26",
                            fill_color="#859900",
                            num_ticks=11,
                            handle_image=":/resources/resources/Handle.png")




    configure_styled_slider(self.ui,
                            "ExtraCellular_Spread_Slider",
                            groove_color="#001E26",
                            fill_color="#268BD2",
                            num_ticks=11,
                            handle_image=":/resources/resources/Handle.png")
    configure_styled_slider(self.ui,
                            "ExtraCellular_BaselineNoise_Slider",
                            groove_color="#001E26",
                            fill_color="#859900",
                            num_ticks=11,
                            handle_image=":/resources/resources/Handle.png")
    configure_styled_slider(self.ui,
                            "ExtraCellular_SharedNoise_Slider",
                            groove_color="#001E26",
                            fill_color="#859900",
                            num_ticks=11,
                            handle_image=":/resources/resources/Handle.png")
    configure_styled_slider(self.ui,
                            "ExtraCellular_HumNoise_Slider",
                            groove_color="#001E26",
                            fill_color="#859900",
                            num_ticks=11,
                            handle_image=":/resources/resources/Handle.png")