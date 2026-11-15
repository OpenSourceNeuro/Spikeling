
########################################################################
#                          Libraries import                            #

from PySide6.QtCore import QSize

from spikeling_gui.appearance.palette import DarkSolarized
from spikeling_gui.widgets import menu_animation


class Imaging():

    def __init__(self, parent):
        self.parent = parent
        self.ui = parent.ui


    # ------------------------------------------------------------------
    # Page selection
    # ------------------------------------------------------------------
    def ShowPage(self):
        self.ui.Imaging_rightMenuContainer.setMinimumSize(QSize(menu_animation.spikerightMenu_max, 16777215))
        self.ui.Imaging_Oscilloscope_widget.setBackground(DarkSolarized[0])
        self.ui.mainbody_stackedWidget.setCurrentWidget(self.ui.page_Imaging_ImagingSimulation)
        menu_animation.toggleMenu(self, self.ui.Imaging_rightMenuContainer, menu_animation.spikerightMenu_min,
                                     menu_animation.spikerightMenu_max, menu_animation.animation_speed,
                                     self.ui.Imaging_rightMenuSubContainer_pushButton, self.icon_SpikelingMenuRight,
                                     self.icon_SpikelingDropMenuRight, True)


    # ------------------------------------------------------------------
    # Source selection: hardware vs emulator
    # ------------------------------------------------------------------
    def UpdateSource(self):
        """
        Push UI selection down to imaging_graph.set_source_mode().
        """
        imaging_graph = getattr(self, "imaging_graph", None)
        if imaging_graph is None:
            print("UpdateSource: imaging_graph not found on MainWindow")
            return

        mode = self.ui.Imaging_Source_comboBox.currentData()
        imaging_graph.select_source(mode, self.ui.Imaging_ConnectButton.isChecked())


    # ------------------------------------------------------------------
    # Saturation mode selection
    # ------------------------------------------------------------------
    def _ensure_model_toggle_guard(self):
        """Internal one-time init for recursion guard."""
        if not hasattr(self, "_updating_model_toggles"):
            self._updating_model_toggles = False

    def _apply_saturation_mode(self, mode: str) -> None:
        """
        mode:
          - "linear"   -> Vogelstein-like linear observation
          - "hill"     -> equilibrium Hill saturation
          - "sigmoid"  -> logistic (sigmoid) saturation
        """
        # Try common attribute names without assuming your exact wiring
        ig = getattr(self.parent, "imaging_graph", None) or getattr(self.parent, "ImagingGraph", None)
        if ig is None:
            return

        ig.fluorescence_model = mode

        ig._update_F0_from_baseline()

        # Force immediate redraw so user sees the change right away
        if getattr(ig, "_plots_ready", False):
            ig._update_plots()

    def Linear_toggleButton(self, checked: bool):
        """
        Exclusive selection: Linear observation.
        User cannot uncheck it directly; must select another mode.
        """
        self._ensure_model_toggle_guard()
        if self._updating_model_toggles:
            return

        # Prevent all-off: if user tries to turn OFF the active mode, turn it back ON.
        if not checked:
            self._updating_model_toggles = True
            try:
                self.ui.Imaging_Linear_toggleButton.setChecked(True)
            finally:
                self._updating_model_toggles = False
            return

        # Checked ON -> turn others OFF
        self._updating_model_toggles = True
        try:
            self.ui.Imaging_Equilibrium_toggleButton.setChecked(False)
            self.ui.Imaging_Logistic_toggleButton.setChecked(False)
        finally:
            self._updating_model_toggles = False

        # Link to model
        self._apply_saturation_mode("linear")

    def Equilibrium_toggleButton(self, checked: bool):
        """
        Exclusive selection: equilibrium Hill saturation.
        """
        self._ensure_model_toggle_guard()
        if self._updating_model_toggles:
            return

        if not checked:
            self._updating_model_toggles = True
            try:
                self.ui.Imaging_Equilibrium_toggleButton.setChecked(True)
            finally:
                self._updating_model_toggles = False
            return

        self._updating_model_toggles = True
        try:
            self.ui.Imaging_Linear_toggleButton.setChecked(False)
            self.ui.Imaging_Logistic_toggleButton.setChecked(False)
        finally:
            self._updating_model_toggles = False

        self._apply_saturation_mode("hill")

    def Logistic_toggleButton(self, checked: bool):
        """
        Exclusive selection: logistic (sigmoid) saturation.
        """
        self._ensure_model_toggle_guard()
        if self._updating_model_toggles:
            return

        if not checked:
            self._updating_model_toggles = True
            try:
                self.ui.Imaging_Logistic_toggleButton.setChecked(True)
            finally:
                self._updating_model_toggles = False
            return

        self._updating_model_toggles = True
        try:
            self.ui.Imaging_Linear_toggleButton.setChecked(False)
            self.ui.Imaging_Equilibrium_toggleButton.setChecked(False)
        finally:
            self._updating_model_toggles = False

        self._apply_saturation_mode("sigmoid")
