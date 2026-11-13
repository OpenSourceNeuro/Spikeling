# SPDX-License-Identifier: GPL-3.0-or-later

import sys

if "--help" in sys.argv:
    print("Spikeling - GUI simulator while packaging with PyInstaller")
    sys.exit(0)

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from spikeling_gui.appearance.theme_manager import theme_manager
from spikeling_gui.main_window import MainWindow
from spikeling_gui.paths import resource_path
from spikeling_gui.preferences import initialise_language
from spikeling_gui.splash import SplashScreen


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    initialise_language(app)
    theme_manager.apply(app=app)
    app.setWindowIcon(QIcon(str(resource_path("resources", "Spikeling.ico"))))

    window = SplashScreen(MainWindow)
    sys.exit(app.exec())