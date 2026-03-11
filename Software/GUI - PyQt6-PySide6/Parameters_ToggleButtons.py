
########################################################################
#                          Libraries import                            #

from __future__ import annotations
from Parameters_Settings import DarkSolarized

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



########################################################################
#                         Generate Toggle Buttons                      #
########################################################################

def Buttons(self):

    # Generate toggle buttons for Spikeling Page
    self.ui.PatchClampMode_toggleButton = PyToggle(width = 75,
                                                   bg_color='#%02x%02x%02x' % tuple(DarkSolarized[4]),
                                                   circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                   active_color='#%02x%02x%02x' % tuple(DarkSolarized[3])
                                                   )
    self.ui.PatchClamp_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                               circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                               active_color='#%02x%02x%02x' % tuple(DarkSolarized[4])
                                               )
    self.ui.Noise_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                          circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                          active_color='#%02x%02x%02x' % tuple(DarkSolarized[4])
                                          )
    self.ui.PhotoGain_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                              circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                              active_color='#%02x%02x%02x' % tuple(DarkSolarized[4])
                                              )
    self.ui.PhotoDecay_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                               circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                               active_color='#%02x%02x%02x' % tuple(DarkSolarized[4])
                                               )
    self.ui.PhotoRecovery_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                  circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                  active_color='#%02x%02x%02x' % tuple(DarkSolarized[4])
                                                  )
    self.ui.StimFre_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                            circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                            active_color='#%02x%02x%02x' % tuple(DarkSolarized[5])
                                            )
    self.ui.StimStr_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                            circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                            active_color='#%02x%02x%02x' % tuple(DarkSolarized[5])
                                            )
    self.ui.StimCus_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                            circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                            active_color='#%02x%02x%02x' % tuple(DarkSolarized[5])
                                            )
    self.ui.Synapse1_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                             circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                             active_color='#%02x%02x%02x' % tuple(DarkSolarized[7])
                                             )
    self.ui.Synapse1Decay_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                  circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                  active_color='#%02x%02x%02x' % tuple(DarkSolarized[7])
                                                  )
    self.ui.Synapse2_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                             circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                             active_color='#%02x%02x%02x' % tuple(DarkSolarized[10])
                                             )
    self.ui.Synapse2Decay_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                  circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                  active_color='#%02x%02x%02x' % tuple(DarkSolarized[10])
                                                  )
    self.ui.Spikeling_PatchClampMode_toggle_layout.addWidget(self.ui.PatchClampMode_toggleButton)
    self.ui.Spikeling_PatchClampMode_toggle_layout.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
    self.ui.Spikeling_PatchClamp_toggle_layout.addWidget(self.ui.PatchClamp_toggleButton)
    self.ui.Spikeling_PatchClamp_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Spikeling_Noise_toggle_layout.addWidget(self.ui.Noise_toggleButton)
    self.ui.Spikeling_Noise_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Spikeling_Synapse1_toggle_layout.addWidget(self.ui.Synapse1_toggleButton)
    self.ui.Spikeling_Synapse1_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Spikeling_Synapse1_Decay_toggle_layout.addWidget(self.ui.Synapse1Decay_toggleButton)
    self.ui.Spikeling_Synapse1_Decay_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Spikeling_Synapse2_toggle_layout.addWidget(self.ui.Synapse2_toggleButton)
    self.ui.Spikeling_Synapse2_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Spikeling_Synapse2_Decay_toggle_layout.addWidget(self.ui.Synapse2Decay_toggleButton)
    self.ui.Spikeling_Synapse2_Decay_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

    self.ui.Spikeling_StimFre_toggle_layout.addWidget(self.ui.StimFre_toggleButton)
    self.ui.Spikeling_StimFre_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Spikeling_StimStr_toggle_layout.addWidget(self.ui.StimStr_toggleButton)
    self.ui.Spikeling_StimStr_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Spikeling_CustomStimulus_toggle_layout.addWidget(self.ui.StimCus_toggleButton)
    self.ui.Spikeling_CustomStimulus_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Spikeling_PR_toggle_layout.addWidget(self.ui.PhotoGain_toggleButton)
    self.ui.Spikeling_PR_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Spikeling_PRDecay_Toggle_layout.addWidget(self.ui.PhotoDecay_toggleButton)
    self.ui.Spikeling_PRDecay_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.SpikelingPRRecovery_toggle_layout.addWidget(self.ui.PhotoRecovery_toggleButton)
    self.ui.SpikelingPRRecovery_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)



    # Generate toggle buttons for Emulator Page
    self.ui.EmulatorPatchClamp_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                       circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                       active_color='#%02x%02x%02x' % tuple(DarkSolarized[4])
                                                       )
    self.ui.EmulatorNoise_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                  circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                  active_color='#%02x%02x%02x' % tuple(DarkSolarized[4])
                                          )
    self.ui.EmulatorPhotoGain_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                      circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                      active_color='#%02x%02x%02x' % tuple(DarkSolarized[4])
                                              )
    self.ui.EmulatorPhotoDecay_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                       circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                       active_color='#%02x%02x%02x' % tuple(DarkSolarized[4])
                                               )
    self.ui.EmulatorPhotoRecovery_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                          circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                          active_color='#%02x%02x%02x' % tuple(DarkSolarized[4])
                                                  )
    self.ui.EmulatorStimChoiceCurrent_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                              circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                              active_color='#%02x%02x%02x' % tuple(DarkSolarized[5])
                                                          )
    self.ui.EmulatorStimChoiceLight_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                              circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                              active_color='#%02x%02x%02x' % tuple(DarkSolarized[4])
                                                                )
    self.ui.EmulatorStimFre_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                    circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                    active_color='#%02x%02x%02x' % tuple(DarkSolarized[5])
                                            )
    self.ui.EmulatorStimStr_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                    circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                    active_color='#%02x%02x%02x' % tuple(DarkSolarized[5])
                                            )
    self.ui.EmulatorStimCus_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                    circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                    active_color='#%02x%02x%02x' % tuple(DarkSolarized[5])
                                            )


    self.ui.EmulatorSynapse1_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                     circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                     active_color='#%02x%02x%02x' % tuple(DarkSolarized[7])
                                             )
    self.ui.EmulatorSynapse1Decay_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                          circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                          active_color='#%02x%02x%02x' % tuple(DarkSolarized[7])
                                                  )
    self.ui.EmulatorSyn1_Synapse_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                         circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                         active_color='#%02x%02x%02x' % tuple(DarkSolarized[6])
                                                          )
    self.ui.EmulatorSyn1_PatchClamp_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                            circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                            active_color='#%02x%02x%02x' % tuple(DarkSolarized[4])
                                                         )
    self.ui.EmulatorSyn1_Noise_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                       circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                       active_color='#%02x%02x%02x' % tuple(DarkSolarized[4])
                                                         )
    self.ui.EmulatorSyn1_StimDC_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                        circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                        active_color='#%02x%02x%02x' % tuple(DarkSolarized[5])
                                                         )
    self.ui.EmulatorSyn1_StimLight_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                           circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                           active_color='#%02x%02x%02x' % tuple(DarkSolarized[4])
                                                        )
    self.ui.EmulatorSyn1_PhotoGain_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                           circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                           active_color='#%02x%02x%02x' % tuple(DarkSolarized[4])
                                                           )
    self.ui.EmulatorSyn1_PhotoDecay_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                           circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                           active_color='#%02x%02x%02x' % tuple(DarkSolarized[4])
                                                           )
    self.ui.EmulatorSyn1_PhotoRecovery_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                               circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                               active_color='#%02x%02x%02x' % tuple(DarkSolarized[4])
                                                           )


    self.ui.EmulatorSyn2_Synapse_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                         circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                         active_color='#%02x%02x%02x' % tuple(DarkSolarized[8])
                                                         )
    self.ui.EmulatorSyn2_PatchClamp_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                            circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                            active_color='#%02x%02x%02x' % tuple(DarkSolarized[4])
                                                            )
    self.ui.EmulatorSyn2_Noise_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                       circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                       active_color='#%02x%02x%02x' % tuple(DarkSolarized[4])
                                                       )
    self.ui.EmulatorSyn2_StimDC_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                        circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                        active_color='#%02x%02x%02x' % tuple(DarkSolarized[5])
                                                        )
    self.ui.EmulatorSyn2_StimLight_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                           circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                           active_color='#%02x%02x%02x' % tuple(DarkSolarized[4])
                                                           )
    self.ui.EmulatorSynapse2_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                     circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                     active_color='#%02x%02x%02x' % tuple(DarkSolarized[10])
                                                     )
    self.ui.EmulatorSynapse2Decay_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                          circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                          active_color='#%02x%02x%02x' % tuple(DarkSolarized[10])
                                                          )
    self.ui.EmulatorSyn2_PhotoGain_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                           circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                           active_color='#%02x%02x%02x' % tuple(DarkSolarized[4])
                                                           )
    self.ui.EmulatorSyn2_PhotoDecay_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                            circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                            active_color='#%02x%02x%02x' % tuple(DarkSolarized[4])
                                                            )
    self.ui.EmulatorSyn2_PhotoRecovery_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                               circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                               active_color='#%02x%02x%02x' % tuple(DarkSolarized[4])
                                                               )

    self.ui.Emulator_PatchClamp_toggle_layout.addWidget(self.ui.EmulatorPatchClamp_toggleButton)
    self.ui.Emulator_PatchClamp_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Emulator_Noise_toggle_layout.addWidget(self.ui.EmulatorNoise_toggleButton)
    self.ui.Emulator_Noise_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Emulator_Synapse1_toggle_layout.addWidget(self.ui.EmulatorSynapse1_toggleButton)
    self.ui.Emulator_Synapse1_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Emulator_Synapse1_Decay_toggle_layout.addWidget(self.ui.EmulatorSynapse1Decay_toggleButton)
    self.ui.Emulator_Synapse1_Decay_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Emulator_Synapse2_toggle_layout.addWidget(self.ui.EmulatorSynapse2_toggleButton)
    self.ui.Emulator_Synapse2_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Emulator_Synapse2_Decay_toggle_layout.addWidget(self.ui.EmulatorSynapse2Decay_toggleButton)
    self.ui.Emulator_Synapse2_Decay_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

    self.ui.Emulator_StimChoice_Current_layout.addWidget(self.ui.EmulatorStimChoiceCurrent_toggleButton)
    self.ui.Emulator_StimChoice_Current_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Emulator_StimChoice_Light_layout.addWidget(self.ui.EmulatorStimChoiceLight_toggleButton)
    self.ui.Emulator_StimChoice_Light_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

    self.ui.Emulator_StimFre_toggle_layout.addWidget(self.ui.EmulatorStimFre_toggleButton)
    self.ui.Emulator_StimFre_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Emulator_StimStr_toggle_layout.addWidget(self.ui.EmulatorStimStr_toggleButton)
    self.ui.Emulator_StimStr_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Emulator_CustomStimulus_toggle_layout.addWidget(self.ui.EmulatorStimCus_toggleButton)
    self.ui.Emulator_CustomStimulus_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Emulator_PR_toggle_layout.addWidget(self.ui.EmulatorPhotoGain_toggleButton)
    self.ui.Emulator_PR_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Emulator_PRDecay_Toggle_layout.addWidget(self.ui.EmulatorPhotoDecay_toggleButton)
    self.ui.Emulator_PRDecay_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.EmulatorPRRecovery_toggle_layout.addWidget(self.ui.EmulatorPhotoRecovery_toggleButton)
    self.ui.EmulatorPRRecovery_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

    self.ui.Emulator_Syn1_Mode_Toggle_layout.addWidget(self.ui.EmulatorSyn1_Synapse_toggleButton)
    self.ui.Emulator_Syn1_Mode_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Emulator_Syn1_PatchClamp_Toggle_layout.addWidget(self.ui.EmulatorSyn1_PatchClamp_toggleButton)
    self.ui.Emulator_Syn1_PatchClamp_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.EmulatorSyn1_PatchClamp_toggleButton.setEnabled(False)
    self.ui.Emulator_Syn1_Noise_Toggle_layout.addWidget(self.ui.EmulatorSyn1_Noise_toggleButton)
    self.ui.Emulator_Syn1_Noise_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.EmulatorSyn1_Noise_toggleButton.setEnabled(False)
    self.ui.Emulator_Syn1_Stimulus_DC_Toggle_layout.addWidget(self.ui.EmulatorSyn1_StimDC_toggleButton)
    self.ui.Emulator_Syn1_Stimulus_DC_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.EmulatorSyn1_StimDC_toggleButton.setEnabled(False)
    self.ui.Emulator_Syn1_Stimulus_Light_Toggle_layout.addWidget(self.ui.EmulatorSyn1_StimLight_toggleButton)
    self.ui.Emulator_Syn1_Stimulus_Light_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.EmulatorSyn1_StimLight_toggleButton.setEnabled(False)
    self.ui.Emulator_Syn1_PhotoGain_toggle_layout.addWidget(self.ui.EmulatorSyn1_PhotoGain_toggleButton)
    self.ui.Emulator_Syn1_PhotoGain_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.EmulatorSyn1_PhotoGain_toggleButton.setEnabled(False)
    self.ui.Emulator_Syn1_PhotoDecay_toggle_layout.addWidget(self.ui.EmulatorSyn1_PhotoDecay_toggleButton)
    self.ui.Emulator_Syn1_PhotoDecay_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.EmulatorSyn1_PhotoDecay_toggleButton.setEnabled(False)
    self.ui.Emulator_Syn1_PhotoRecovery_toggle_layout.addWidget(self.ui.EmulatorSyn1_PhotoRecovery_toggleButton)
    self.ui.Emulator_Syn1_PhotoRecovery_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.EmulatorSyn1_PhotoRecovery_toggleButton.setEnabled(False)

    self.ui.Emulator_Syn2_Mode_Toggle_layout.addWidget(self.ui.EmulatorSyn2_Synapse_toggleButton)
    self.ui.Emulator_Syn2_Mode_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Emulator_Syn2_PatchClamp_Toggle_layout.addWidget(self.ui.EmulatorSyn2_PatchClamp_toggleButton)
    self.ui.Emulator_Syn2_PatchClamp_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.EmulatorSyn2_PatchClamp_toggleButton.setEnabled(False)
    self.ui.Emulator_Syn2_Noise_Toggle_layout.addWidget(self.ui.EmulatorSyn2_Noise_toggleButton)
    self.ui.Emulator_Syn2_Noise_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.EmulatorSyn2_Noise_toggleButton.setEnabled(False)
    self.ui.Emulator_Syn2_Stimulus_DC_Toggle_layout.addWidget(self.ui.EmulatorSyn2_StimDC_toggleButton)
    self.ui.Emulator_Syn2_Stimulus_DC_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.EmulatorSyn2_StimDC_toggleButton.setEnabled(False)
    self.ui.Emulator_Syn2_Stimulus_Light_Toggle_layout.addWidget(self.ui.EmulatorSyn2_StimLight_toggleButton)
    self.ui.Emulator_Syn2_Stimulus_Light_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.EmulatorSyn2_StimLight_toggleButton.setEnabled(False)
    self.ui.Emulator_Syn2_PhotoGain_toggle_layout.addWidget(self.ui.EmulatorSyn2_PhotoGain_toggleButton)
    self.ui.Emulator_Syn2_PhotoGain_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.EmulatorSyn2_PhotoGain_toggleButton.setEnabled(False)
    self.ui.Emulator_Syn2_PhotoDecay_toggle_layout.addWidget(self.ui.EmulatorSyn2_PhotoDecay_toggleButton)
    self.ui.Emulator_Syn2_PhotoDecay_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.EmulatorSyn2_PhotoDecay_toggleButton.setEnabled(False)
    self.ui.Emulator_Syn2_PhotoRecovery_toggle_layout.addWidget(self.ui.EmulatorSyn2_PhotoRecovery_toggleButton)
    self.ui.Emulator_Syn2_PhotoRecovery_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.EmulatorSyn2_PhotoRecovery_toggleButton.setEnabled(False)



    # Generate toggle buttons for Imaging Page
    self.ui.Imaging_Df_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                               circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                               active_color='#%02x%02x%02x' % tuple(DarkSolarized[4])
                                               )
    self.ui.Imaging_Linear_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                   circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                   active_color='#%02x%02x%02x' % tuple(DarkSolarized[4])
                                                   )
    self.ui.Imaging_Equilibrium_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                        circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                        active_color='#%02x%02x%02x' % tuple(DarkSolarized[4])
                                                        )
    self.ui.Imaging_Logistic_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                     circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                     active_color='#%02x%02x%02x' % tuple(DarkSolarized[4])
                                                     )
    self.ui.Imaging_FrameRate_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                      circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                      active_color='#%02x%02x%02x' % tuple(DarkSolarized[4])
                                                      )
    self.ui.Imaging_PMT_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                active_color='#%02x%02x%02x' % tuple(DarkSolarized[4])
                                                )
    self.ui.Imaging_Laser_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                  circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                  active_color='#%02x%02x%02x' % tuple(DarkSolarized[4])
                                                  )

    self.ui.Imaging_CalciumRise_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                        circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                        active_color='#%02x%02x%02x' % tuple(DarkSolarized[10])
                                                         )
    self.ui.Imaging_CalciumDecay_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                         circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                         active_color='#%02x%02x%02x' % tuple(DarkSolarized[10])
                                                         )
    self.ui.Imaging_CalciumJump_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                        circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                        active_color='#%02x%02x%02x' % tuple(DarkSolarized[10])
                                                        )
    self.ui.Imaging_CalciumNoise_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                         circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                         active_color='#%02x%02x%02x' % tuple(DarkSolarized[10])
                                                         )
    self.ui.Imaging_CalciumBaseline_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                            circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                            active_color='#%02x%02x%02x' % tuple(DarkSolarized[10])
                                                            )

    self.ui.Imaging_IndRise_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                    circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                    active_color='#%02x%02x%02x' % tuple(DarkSolarized[4])
                                                    )
    self.ui.Imaging_IndDecay_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                    circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                    active_color='#%02x%02x%02x' % tuple(DarkSolarized[4])
                                                    )
    self.ui.Imaging_DFF_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                active_color='#%02x%02x%02x' % tuple(DarkSolarized[4])
                                                )
    self.ui.Imaging_kd_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                               circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                               active_color='#%02x%02x%02x' % tuple(DarkSolarized[4])
                                               )
    self.ui.Imaging_Hill_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                 circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                 active_color='#%02x%02x%02x' % tuple(DarkSolarized[4])
                                                 )
    self.ui.Imaging_PhotoShotNoise_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                           circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                           active_color='#%02x%02x%02x' % tuple(DarkSolarized[4])
                                                           )
    self.ui.Imaging_FluoNoise_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                      circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                      active_color='#%02x%02x%02x' % tuple(DarkSolarized[4])
                                                      )
    self.ui.Imaging_FluoScale_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                      circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                      active_color='#%02x%02x%02x' % tuple(DarkSolarized[4])
                                                      )
    self.ui.Imaging_FluoOffset_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                       circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                       active_color='#%02x%02x%02x' % tuple(DarkSolarized[4])
                                                       )

    self.ui.Imaging_Df_Toggle_layout.addWidget(self.ui.Imaging_Df_toggleButton)
    self.ui.Imaging_Df_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Imaging_Linear_Toggle_layout.addWidget(self.ui.Imaging_Linear_toggleButton)
    self.ui.Imaging_Linear_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Imaging_Equilibrium_Toggle_layout.addWidget(self.ui.Imaging_Equilibrium_toggleButton)
    self.ui.Imaging_Equilibrium_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Imaging_Equilibrium_toggleButton.setChecked(True)
    self.ui.Imaging_Logistic_Toggle_layout.addWidget(self.ui.Imaging_Logistic_toggleButton)
    self.ui.Imaging_Logistic_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Imaging_FrameRate_Toggle_layout.addWidget(self.ui.Imaging_FrameRate_toggleButton)
    self.ui.Imaging_FrameRate_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Imaging_PMT_Toggle_layout.addWidget(self.ui.Imaging_PMT_toggleButton)
    self.ui.Imaging_PMT_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Imaging_Laser_Toggle_layout.addWidget(self.ui.Imaging_Laser_toggleButton)
    self.ui.Imaging_Laser_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

    self.ui.Imaging_CalciumRise_Toggle_layout.addWidget(self.ui.Imaging_CalciumRise_toggleButton)
    self.ui.Imaging_CalciumRise_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Imaging_CalciumDecay_Toggle_layout.addWidget(self.ui.Imaging_CalciumDecay_toggleButton)
    self.ui.Imaging_CalciumDecay_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Imaging_CalciumJump_Toggle_layout.addWidget(self.ui.Imaging_CalciumJump_toggleButton)
    self.ui.Imaging_CalciumJump_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Imaging_CalciumNoise_Toggle_layout.addWidget(self.ui.Imaging_CalciumNoise_toggleButton)
    self.ui.Imaging_CalciumNoise_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Imaging_CalciumBaseline_Toggle_layout.addWidget(self.ui.Imaging_CalciumBaseline_toggleButton)
    self.ui.Imaging_CalciumBaseline_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

    self.ui.Imaging_kd_Toggle_layout.addWidget(self.ui.Imaging_kd_toggleButton)
    self.ui.Imaging_kd_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Imaging_Hill_Toggle_layout.addWidget(self.ui.Imaging_Hill_toggleButton)
    self.ui.Imaging_Hill_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Imaging_IndRise_Toggle_layout.addWidget(self.ui.Imaging_IndRise_toggleButton)
    self.ui.Imaging_IndRise_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Imaging_IndDecay_Toggle_layout.addWidget(self.ui.Imaging_IndDecay_toggleButton)
    self.ui.Imaging_IndDecay_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Imaging_DFF_Toggle_layout.addWidget(self.ui.Imaging_DFF_toggleButton)
    self.ui.Imaging_DFF_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Imaging_PhotoShotNoise_Toggle_layout.addWidget(self.ui.Imaging_PhotoShotNoise_toggleButton)
    self.ui.Imaging_PhotoShotNoise_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Imaging_FluoNoise_Toggle_layout.addWidget(self.ui.Imaging_FluoNoise_toggleButton)
    self.ui.Imaging_FluoNoise_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Imaging_FluoScale_Toggle_layout.addWidget(self.ui.Imaging_FluoScale_toggleButton)
    self.ui.Imaging_FluoScale_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Imaging_FluoOffset_Toggle_layout.addWidget(self.ui.Imaging_FluoOffset_toggleButton)
    self.ui.Imaging_FluoOffset_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)





# Generate toggle buttons for Imaging Page
    self.ui.ExtraCellular_SignalMode_toggleButton = PyToggle(width = 60,
                                                bg_color='#%02x%02x%02x' % tuple(DarkSolarized[5]),
                                               circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                               active_color='#%02x%02x%02x' % tuple(DarkSolarized[7]))
    self.ui.ExtraCellular_Distance_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                               circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                               active_color='#%02x%02x%02x' % tuple(DarkSolarized[5]))
    self.ui.ExtraCellular_Orientation_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                               circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                               active_color='#%02x%02x%02x' % tuple(DarkSolarized[5]))
    self.ui.ExtraCellular_Spread_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                               circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                               active_color='#%02x%02x%02x' % tuple(DarkSolarized[5]))
    self.ui.ExtraCellular_BaselineNoise_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                   circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                   active_color='#%02x%02x%02x' % tuple(DarkSolarized[4]))
    self.ui.ExtraCellular_SharedNoise_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                   circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                   active_color='#%02x%02x%02x' % tuple(DarkSolarized[4]))
    self.ui.ExtraCellular_HumNoise_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                   circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                   active_color='#%02x%02x%02x' % tuple(DarkSolarized[4]))
    self.ui.ExtraCellular_CAR_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(DarkSolarized[11]),
                                                   circle_color='#%02x%02x%02x' % tuple(DarkSolarized[15]),
                                                   active_color='#%02x%02x%02x' % tuple(DarkSolarized[4]))


    self.ui.ExtraCellular_SignalMode_Toggle_layout.addWidget(self.ui.ExtraCellular_SignalMode_toggleButton)
    self.ui.ExtraCellular_SignalMode_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.ExtraCellular_Distance_Toggle_layout.addWidget(self.ui.ExtraCellular_Distance_toggleButton)
    self.ui.ExtraCellular_Distance_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.ExtraCellular_Orientation_Toggle_layout.addWidget(self.ui.ExtraCellular_Orientation_toggleButton)
    self.ui.ExtraCellular_Orientation_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.ExtraCellular_Spread_Toggle_layout.addWidget(self.ui.ExtraCellular_Spread_toggleButton)
    self.ui.ExtraCellular_Spread_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.ExtraCellular_BaselineNoise_Toggle_layout.addWidget(self.ui.ExtraCellular_BaselineNoise_toggleButton)
    self.ui.ExtraCellular_BaselineNoise_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.ExtraCellular_SharedNoise_Toggle_layout.addWidget(self.ui.ExtraCellular_SharedNoise_toggleButton)
    self.ui.ExtraCellular_SharedNoise_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.ExtraCellular_HumNoise_Toggle_layout.addWidget(self.ui.ExtraCellular_HumNoise_toggleButton)
    self.ui.ExtraCellular_HumNoise_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.ExtraCellular_CAR_Toggle_layout.addWidget(self.ui.ExtraCellular_CAR_toggleButton)
    self.ui.ExtraCellular_CAR_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
