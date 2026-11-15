# SPDX-License-Identifier: GPL-3.0-or-later

from PySide6 import QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMainWindow, QSizeGrip

from spikeling_gui import navigation as NavigationButtons
from spikeling_gui.ui.generated.UI_Spikeling import Ui_Spikeling

from spikeling_gui.appearance.artwork import ARTWORK_PROPERTY, MAIN_ARTWORK
from spikeling_gui.appearance.dialogs import themed_message_box
from spikeling_gui.appearance.theme_manager import theme_manager
from spikeling_gui.features.emulator.scope import FinishRecording
from spikeling_gui.features.extracellular.tetrode_window import TetrodeGeometryWindow
from spikeling_gui.features.settings.page import SettingsPage
from spikeling_gui.paths import resource_path
from spikeling_gui.updates.page import GitHubPage
from spikeling_gui.version import __version__
from spikeling_gui.widgets import sliders as Sliders
from spikeling_gui.widgets import toggle_buttons as ToggleButtons


GlobalState = 0


class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.ui = Ui_Spikeling()
        self.ui.setupUi(self)
        for name, filename in MAIN_ARTWORK.items():
            widget = getattr(self.ui, name, None)
            if widget is not None:
                widget.setProperty(ARTWORK_PROPERTY, filename)

        for widget in (self.ui.appTitle_pushButton, self.ui.mainbody_header_text):
            widget.setText(widget.text().replace("{version}", __version__))

        self.setWindowIcon(QIcon(str(resource_path("resources", "Spikeling.ico"))))

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
                theme_manager.set_widget_artwork(self.ui.expand_pushButton, "Reduce.png")

                # Set global to 1
                GlobalState = 1
                self.ui.expand_pushButton.setToolTip("Restore")

            else:
                GlobalState = 0
                self.showNormal()
                theme_manager.set_widget_artwork(self.ui.expand_pushButton, "Expand.png")
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
        from spikeling_gui import speed_model
        speed_model.apply_speed_sliders(self.ui)


        # Generate toggle buttons
        ToggleButtons.Buttons(self)

        # Generate Navigation Buttons associated with Spikeling functions
        NavigationButtons.Buttons(self)

        # Theme: register every window so inline style sheets, plot canvases and
        # animated toggles are all re-themed, then expose the Settings controller.
        self.settings_page = SettingsPage(self, theme_manager)

        theme_manager.bind(app=QApplication.instance(), main_window=self)
        theme_manager.bind(window=self.tetrode_window)
        theme_manager.repaint()

        self.github_page = GitHubPage(self)

        self.spikeling_graph.supervisor.manual_action_required.connect(
            self._show_connection_warning
        )

        from spikeling_gui.features.imaging.protein_hover import GeciHoverController

        self.geci_hover = GeciHoverController(self.ui.Imaging_GECI_comboBox, self)

        self.SerialFlag = False

        self.EmulatorConnectionFlag = False
        self.ui.StimCus_Flag = False
        self.ui.EmulatorConnectedFlag = False

        self.ImagingConnectionFlag = False

        self.MultipleImagingConnectionFlag = False

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

    def _show_connection_warning(self, text: str) -> None:
        themed_message_box(
            self,
            self.tr("Spikeling not responding"),
            text,
            QtWidgets.QMessageBox.Icon.Information,
        ).exec()

    def closeEvent(self, event):
        if not FinishRecording(self):
            event.ignore()
            return

        graph = getattr(self, "spikeling_graph", None)

        if graph is not None:
            if not graph.stop_recording(reason="Window closed"):
                # Retain the window and its unsaved recording.
                event.ignore()
                return

        controller = getattr(self, "custom_stimulus_controller", None)
        if controller is not None and controller.running and controller.voltage:
            controller.stop()
        super().closeEvent(event)