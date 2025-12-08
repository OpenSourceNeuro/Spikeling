
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
from Spikeling_UI import Ui_Spikeling
from Spikeling_SplashScreen import Ui_SplashScreen
from Neuron_Parameters import Ui_AdvancedParameters

# Import Functions and navigation buttons
import ToggleButtons, NavigationButtons

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
        self.setWindowIcon(QIcon("Spikeling.ico"))

        self.aux_window = QtWidgets.QMainWindow()
        self.ui_aux = Ui_AdvancedParameters()
        self.ui_aux.setupUi(self.aux_window)

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
                maximize_restore(self)

            # If left-clicked, move window
            if event.buttons() == Qt.LeftButton:
                self.move(self.pos() + event.globalPosition().toPoint() - self.dragPos)
                self.dragPos = event.globalPosition().toPoint()
                event.accept()

        # Custom Navigation bar movement
        self.ui.header_widget.mouseMoveEvent = moveWindow

        # Generate toggle buttons
        ToggleButtons.Buttons(self)

        # Generate Navigation Buttons associated with Spikeling functions
        NavigationButtons.Buttons(self)

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
    app.setWindowIcon(QIcon("Spikeling.ico"))
    window = SplashScreen()
    sys.exit(app.exec())