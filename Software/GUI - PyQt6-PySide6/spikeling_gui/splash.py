# SPDX-License-Identifier: GPL-3.0-or-later

from PySide6.QtCore import QDate, QLocale, Qt, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QMainWindow

from spikeling_gui.appearance.theme_manager import theme_manager
from spikeling_gui.ui.generated.UI_SplashScreen import Ui_SplashScreen
from spikeling_gui.version import RELEASE_DATE, __version__


########################################################################
#                      SplashScreen window class                       #
########################################################################

counter = 0
class SplashScreen(QMainWindow):
    def __init__(self, main_window_factory):
        super().__init__()
        self._main_window_factory = main_window_factory
        self._progress_value = 0

        self.ui = Ui_SplashScreen()
        self.ui.setupUi(self)
        theme_manager.set_widget_artwork(self.ui.label, "SpikyLogo.png")
        theme_manager.set_widget_artwork(self.ui.Sussex_Logo, "SN-Logo.png")
        theme_manager.set_widget_artwork(self.ui.TReND_Logo, "CaMinA.png")

        heading = self.ui.label_3
        release_date = QDate.fromString(RELEASE_DATE, Qt.DateFormat.ISODate)
        date_text = QLocale().toString(release_date, "MMM yyyy")

        heading.setText(
            heading.text()
            .replace("{version}", __version__)
            .replace("{release_date}", date_text)
        )

        # Remove title bar
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Drop shadow effect
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(20)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(0)
        self.shadow.setColor(QColor(0, 0, 0, 60))
        self.ui.SplashFrame.setGraphicsEffect(self.shadow)

        # QTimer - Start
        self.timer = QTimer()
        self.timer.timeout.connect(self.progress)
        # Timer in milliseconds
        self.timer.start(20)


        # Change Texts
        QTimer.singleShot(1000, lambda: self.ui.Status_Label.setText("<strong>Loading</strong> Database"))
        QTimer.singleShot(2000, lambda: self.ui.Status_Label.setText("<strong>Loading</strong> User interface"))

        ## Display
        ########################################################################
        self.show()

    def progress(self):
        self.ui.Loading_ProgressBar.setValue(self._progress_value)

        if self._progress_value > 100:
            self.timer.stop()
            self.main = self._main_window_factory()
            self.main.show()
            self.close()
            return

        self._progress_value += 1
