# SPDX-License-Identifier: GPL-3.0-or-later

########################################################################
#                          Libraries import                            #

import sys

if "--help" in sys.argv:
    print("Spikeling - GUI simulator while packaging with PyInstaller")
    sys.exit(0)

from PySide6 import QtWidgets
from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QColor,QIcon
from PySide6.QtWidgets import QMainWindow, QGraphicsDropShadowEffect, QApplication, QSizeGrip

# Import GUI .ui file
from UI_Spikeling import Ui_Spikeling
from UI_SplashScreen import Ui_SplashScreen
from UI_NeuronParameters import Ui_AdvancedParameters
from Tetrode import TetrodeGeometryWindow

# Import Functions and navigation buttons
import Parameters_ToggleButtons as ToggleButtons
import Parameters_NavigationButtons as NavigationButtons
import Parameters_Sliders as Sliders
from resource_path import resource_path
from theme_manager import theme_manager
from Page_Settings import SettingsPage
from Page_GitHub import GitHubPage

GlobalState = 0



########################################################################
#                      SplashScreen window class                       #
########################################################################

counter = 0
class SplashScreen(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.ui = Ui_SplashScreen()
        self.ui.setupUi(self)

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

        global counter

        # Set value to progress bar
        self.ui.Loading_ProgressBar.setValue(counter)

        # Close splash screen and open GUI
        if counter > 100:
            # QTimer - Stop
            self.timer.stop()

            # Display Main Window
            self.main = MainWindow()
            self.main.show()

            # Close Splash Screen
            self.close()

        # Increase counter
        counter += 1



########################################################################
#                          Main window class                           #
########################################################################

class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.ui = Ui_Spikeling()
        self.ui.setupUi(self)

        self.setWindowIcon(QIcon(str(resource_path("Spikeling.ico"))))

        self.aux_window = QtWidgets.QMainWindow()
        self.ui_aux = Ui_AdvancedParameters()
        self.ui_aux.setupUi(self.aux_window)

        self.tetrode_window = TetrodeGeometryWindow(self)

        # Remove title bar
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)


        # Define Maximise/Restore function
        def maximise_restore(self):
            global GlobalState
            status = GlobalState

            # If not maximised
            if status == 0:
                self.showMaximized()
                self.ui.expand_pushButton.setIcon(self.icon_reduce)

                # Set global to 1
                GlobalState = 1
                self.ui.expand_pushButton.setToolTip("Restore")

            else:
                GlobalState = 0
                self.showNormal()
                self.ui.expand_pushButton.setIcon(self.icon_expand)
                self.resize(self.width() + 1, self.height() + 1)
                self.ui.expand_pushButton.setToolTip("Maximize")

        ## Return Status id window is maximised or restored
        def returnStatus():
            return GlobalState

        # Maximise / Restore
        self.ui.expand_pushButton.clicked.connect(lambda: maximise_restore(self))

        # Minimise / Restore
        self.ui.reduce_pushButton.clicked.connect(lambda: self.showMinimized())

        # Close
        self.ui.exit_pushButton.clicked.connect(lambda: self.close())

        # Custom Navigation bar buttons
        self.icon_expand = QIcon()
        self.icon_expand.addFile(u":/resources/resources/Expand.png", QSize(), QIcon.Normal, QIcon.Off)
        self.icon_reduce = QIcon()
        self.icon_reduce.addFile(u":/resources/resources/Reduce.png", QSize(), QIcon.Normal, QIcon.Off)

        # Create size grip to resize window
        self.sizegrip = QSizeGrip(self.ui.sizegrip)
        self.sizegrip.setToolTip("Resize Window")

        # Move window
        def moveWindow(event):
            # Restore before moving
            if returnStatus() == 1:
                maximise_restore(self)

            # If left-clicked, move window
            if event.buttons() == Qt.LeftButton:
                self.move(self.pos() + event.globalPosition().toPoint() - self.dragPos)
                self.dragPos = event.globalPosition().toPoint()
                event.accept()

        # Custom Navigation bar movement
        self.ui.header_widget.mouseMoveEvent = moveWindow

        # Replace sliders with TickSliders
        Sliders.configure_sliders(self)

        # Put both speed sliders on the shared ladder at the same rung. Runs
        # before NavigationButtons.Buttons connects valueChanged, so seeding
        # the default cannot emit a serial write to a closed port.
        import speed_model
        speed_model.apply_speed_sliders(self.ui)

        # Generate toggle buttons
        ToggleButtons.Buttons(self)

        # Generate Navigation Buttons associated with Spikeling functions
        NavigationButtons.Buttons(self)

        # Theme: register every window so inline style sheets, plot canvases and
        # animated toggles are all re-themed, then expose the Settings controller.
        self.settings_page = SettingsPage(self, theme_manager)

        theme_manager.bind(app=QApplication.instance(), window=self)
        theme_manager.bind(window=self.aux_window)
        theme_manager.bind(window=self.tetrode_window)
        theme_manager.repaint()

        self.settings_page = SettingsPage(self, theme_manager)
        self.github_page = GitHubPage(self)

        self.spikeling_graph.supervisor.manual_action_required.connect(
            lambda text: QtWidgets.QMessageBox.information(self, "Spikeling not responding", text)
        )

        from protein_hover import GeciHoverController

        self.geci_hover = GeciHoverController(self.ui.Imaging_GECI_comboBox, self)

        self.SerialFlag = False
        self.ui.NeuronRecordFolderFlag = False

        self.EmulatorConnectionFlag = False
        self.ui.EmulatorRecordFolderFlag = False
        self.ui.StimCus_Flag = False
        self.ui.EmulatorConnectedFlag = False

        self.ImagingConnectionFlag = False
        self.ui.ImagingRecordFolderFlag = False

        self.MultipleImagingConnectionFlag = False
        self.ui.MultipleImagingFolderFlag = False

        self.ui.Exercise1_OpeningFlag = True
        self.ui.Exercise2_OpeningFlag = True
        self.ui.Exercise3_OpeningFlag = True
        self.ui.Exercise4_OpeningFlag = True
        self.ui.Exercise5_OpeningFlag = True

    # Display
        self.show()
    ## GUI events
    def mousePressEvent(self, event):
        self.dragPos = event.globalPosition().toPoint()



########################################################################
## Execute GUI
########################################################################

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Fusion honours QPalette and QSS identically on all three platforms; the
    # native Windows style ignores the palette for most widgets, which would
    # leave the custom theme half-applied on the Windows build only.
    app.setStyle("Fusion")

    # Load the stored palette before any widget exists, so toggles, sliders
    # and plot pens are constructed with the user's colours and trace width.
    theme_manager.apply(app=app)

    app.setWindowIcon(QIcon(str(resource_path("Spikeling.ico"))))
    window = SplashScreen()
    sys.exit(app.exec())