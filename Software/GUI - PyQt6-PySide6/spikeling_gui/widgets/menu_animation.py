"""Width animations shared by the navigation and feature panels."""

from PySide6 import QtCore
from PySide6.QtCore import QPropertyAnimation

from spikeling_gui.appearance.theme_manager import theme_manager



########################################################################
#                       Toggle Button Animations                       #
########################################################################

animation_speed = 200
leftMenu_min = 40
leftMenu_max = 180
centerMenu_min = 0
centerMenu_max = 200
spikecenterMenu_min = 0
spikecenterMenu_max = 200
spikerightMenu_min = 40
spikerightMenu_max = 200

def toggleMenu(self, menu, standard, maxWidth, duration, pushButton, icon_min, icon_max, enable):
    if enable:
        #Get width
        width = menu.width()

        #Extend
        if width == standard:
            widthExtended = maxWidth
            theme_manager.set_widget_artwork(pushButton, icon_max)
        #Retract
        else:
            widthExtended = standard
            theme_manager.set_widget_artwork(pushButton, icon_min)

        #Animation
        self.animation = QPropertyAnimation(menu, b"minimumWidth")
        self.animation.setDuration(duration)
        self.animation.setStartValue(width)
        self.animation.setEndValue(widthExtended)
        self.animation.setEasingCurve(QtCore.QEasingCurve.InOutQuart)
        self.animation.start()

def expandMenu(self, menu, standard, maxWidth, duration, enable):
    if enable:
        width = menu.width()
        if width == standard:
            #Animation
            self.animation = QPropertyAnimation(menu, b"minimumWidth")
            self.animation.setDuration(duration)
            self.animation.setStartValue(standard)
            self.animation.setEndValue(maxWidth)
            self.animation.setEasingCurve(QtCore.QEasingCurve.InOutQuart)
            self.animation.start()

def collapseMenu(self, menu, standard, maxWidth, duration, enable):
    if enable:
        width = menu.width()
        if width == maxWidth:
            #Animation
            self.animation = QPropertyAnimation(menu, b"minimumWidth")
            self.animation.setDuration(duration)
            self.animation.setStartValue(maxWidth)
            self.animation.setEndValue(standard)
            self.animation.setEasingCurve(QtCore.QEasingCurve.InOutQuart)
            self.animation.start()


