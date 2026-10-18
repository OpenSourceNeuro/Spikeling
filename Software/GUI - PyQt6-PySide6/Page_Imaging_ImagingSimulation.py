
########################################################################
#                          Libraries import                            #

from PySide6.QtWidgets import QFileDialog
from PySide6.QtCore import QSize

import Parameters_Settings as Settings
import Parameters_NavigationButtons as NavigationButtons
import Graph_Imaging
from Graph_Imaging import GECI_SLIDER_SPECS



class Imaging():

    def __init__(self, parent):
        self.parent = parent
        self.ui = parent.ui


    # ------------------------------------------------------------------
    # Page selection
    # ------------------------------------------------------------------
    def ShowPage(self):
        self.ui.Imaging_rightMenuContainer.setMinimumSize(QSize(NavigationButtons.spikerightMenu_max, 16777215))
        self.ui.Imaging_Oscilloscope_widget.setBackground(Settings.DarkSolarized[0])
        self.ui.mainbody_stackedWidget.setCurrentWidget(self.ui.page_201)
        NavigationButtons.toggleMenu(self, self.ui.Imaging_rightMenuContainer, NavigationButtons.spikerightMenu_min,
                                     NavigationButtons.spikerightMenu_max, NavigationButtons.animation_speed,
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

        # 0 -> Spikeling hardware, 1 -> Emulator
        idx = self.ui.Imaging_Source_comboBox.currentIndex()
        mode = "emulator" if idx == 1 else "spikeling"
        imaging_graph.set_source_mode(mode)

        # Connect or disconnect according to button state
        if self.ui.Imaging_ConnectButton.isChecked():
            imaging_graph.connect()
        else:
            imaging_graph.disconnect()


    # ------------------------------------------------------------------
    # Data Recording Functions
    # ------------------------------------------------------------------
    def BrowseRecordFolder(self):
        FolderName = QFileDialog.getExistingDirectory(
            caption='Hey! Select the folder where your experiment will be saved',
            dir="./Recordings")
        if FolderName:
            self.ui.Imaging_DataRecording_SelectRecordFolder_label.setText(FolderName)
            self.ui.Imaging_DataRecording_RecordFolder_value.setEnabled(True)
            self.ui.Imaging_DataRecording_RecordFolder_value.setPlaceholderText("Enter a file name")
            self.ImagingFolderFlag = True


    def RecordFolderText(self):
        FolderName = self.ui.Imaging_DataRecording_SelectRecordFolder_label.text()
        FileName = self.ui.Imaging_DataRecording_RecordFolder_value.text()
        self.ui.Imaging_SelectedFolderLabel.setText(FolderName + '/' + FileName)

    def RecordButton(self):
        """
        Start/stop recording Imaging data.

        Conditions to start recording:
          - Imaging is connected (to hardware OR emulator)
          - A folder has been selected
          - A file name has been entered
        """

        # User is trying to START recording
        if self.ui.Imaging_DataRecording_Record_pushButton.isChecked():
            # 1) Check Imaging is connected
            if not getattr(self, "ImagingConnectionFlag", False):
                self.ui.Imaging_DataRecording_Record_pushButton.setChecked(False)
                Settings.show_popup(self, Title="Error: Spikeling not connected",
                                          Text=("Spikeling data stream first needs to be connected. "
                                          "Check that a spikeling is running on either the neuron "
                                          "interface or the neuron emulator tab."))
                return

            # 2) Check folder is selected
            if not getattr(self, "ImagingFolderFlag", False):
                self.ui.Imaging_DataRecording_Record_pushButton.setChecked(False)
                Settings.show_popup(self, Title="Error: no folder selected",
                                          Text=("Select a folder where to record your data by clicking on "
                                                "the - browse directory - button."))
                return

            # 3) Check file name is provided
            if not self.ui.Imaging_DataRecording_RecordFolder_value.text():
                self.ui.Imaging_DataRecording_Record_pushButton.setChecked(False)
                Settings.show_popup(self, Title="Error: no file selected",
                                        Text=("Select a file where to record your data by entering a name "
                                              "in the file name field."))
                return

            # 4) All conditions OK -> enter recording mode
            self.ui.Imaging_DataRecording_Record_pushButton.setText("Stop Recording")
            self.ui.Imaging_DataRecording_Record_pushButton.setStyleSheet("color: rgb(250, 250, 250);\n"
                                                                          "background-color: rgb(50, 220, 47);")

        # User is STOPPING recording
        else:
            self.ui.Imaging_DataRecording_Record_pushButton.setText("Record")
            self.ui.Imaging_DataRecording_Record_pushButton.setStyleSheet("color: rgb(250, 250, 250);\n"
                                                                          "background-color: rgb(220, 50, 47);")

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

        # If you plot ΔF/F0, baseline reference depends on the observation model
        if getattr(ig, "use_dff", False):
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


    # ------------------------------------------------------------------
    # Imaging Parameters
    # ------------------------------------------------------------------

    # Frame Rate
    def ActivateFrameRate(self, checked: bool = None):
        if self.ui.Imaging_FrameRate_toggleButton.isChecked():
            self.ui.Imaging_FrameRate_Slider.setEnabled(True)
            self.FrameRateValue = self.ui.Imaging_FrameRate_Slider.value()
            self.ui.Imaging_FrameRate_Readings.setText(str(self.FrameRateValue/10) )
            self.ui.Imaging_FrameRate_Readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")
        else:
            self.ui.Imaging_FrameRate_Slider.setEnabled(False)
            self.ui.Imaging_FrameRate_Slider.setValue(100)
            self.ui.Imaging_FrameRate_Readings.setText('')

    def GetFrameRate(self):
        self.FrameRateValue = self.ui.Imaging_FrameRate_Slider.value()
        self.ui.Imaging_FrameRate_Readings.setText(str(self.FrameRateValue/10))
        self.ui.Imaging_FrameRate_Readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")


    # PMT
    def ActivatePMT(self):
        if self.ui.Imaging_PMT_toggleButton.isChecked():
            self.ui.Imaging_PMT_Slider.setEnabled(True)
            self.PMTValue = self.ui.Imaging_PMT_Slider.value()
            self.ui.Imaging_PMT_Readings.setText(str(self.PMTValue))
            self.ui.Imaging_PMT_Readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")
        else:
            self.ui.Imaging_PMT_Slider.setEnabled(False)
            self.ui.Imaging_PMT_Slider.setValue(100)
            self.ui.Imaging_PMT_Readings.setText('')

    def GetPMT(self):
        self.PMTValue = self.ui.Imaging_PMT_Slider.value()
        self.ui.Imaging_PMT_Readings.setText(str(self.PMTValue))
        self.ui.Imaging_PMT_Readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")


    # Laser
    def ActivateLaser(self):
        if self.ui.Imaging_Laser_toggleButton.isChecked():
            self.ui.Imaging_Laser_Slider.setEnabled(True)
            self.LaserValue = self.ui.Imaging_Laser_Slider.value()
            self.ui.Imaging_Laser_Readings.setText(str(self.LaserValue))
            self.ui.Imaging_Laser_Readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")
        else:
            self.ui.Imaging_Laser_Slider.setEnabled(False)
            self.ui.Imaging_Laser_Slider.setValue(100)
            self.ui.Imaging_Laser_Readings.setText('')

    def GetLaser(self):
        self.LaserValue = self.ui.Imaging_Laser_Slider.value()
        self.ui.Imaging_Laser_Readings.setText(str(self.LaserValue))
        self.ui.Imaging_Laser_Readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")


    # ------------------------------------------------------------------
    # Calcium parameters
    # ------------------------------------------------------------------

    # CalciumRise
    def ActivateCalciumRise(self):
        if self.ui.Imaging_CalciumRise_toggleButton.isChecked():
            self.ui.Imaging_CalciumRise_Slider.setEnabled(True)
            self.CalciumRiseValue = self.ui.Imaging_CalciumRise_Slider.value()
            self.ui.Imaging_CalciumRise_Readings.setText(str(self.CalciumRiseValue))
            self.ui.Imaging_CalciumRise_Readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[10])) + "; font: 700 10pt;")
        else:
            self.ui.Imaging_CalciumRise_Slider.setEnabled(False)
            self.ui.Imaging_CalciumRise_Slider.setValue(20)
            self.ui.Imaging_CalciumRise_Readings.setText('')

    def GetCalciumRise(self):
        self.CalciumRiseValue = self.ui.Imaging_CalciumRise_Slider.value()
        self.ui.Imaging_CalciumRise_Readings.setText(str(self.CalciumRiseValue))
        self.ui.Imaging_CalciumRise_Readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[10])) + "; font: 700 10pt;")


    # CalciumDecay
    def ActivateCalciumDecay(self):
        if self.ui.Imaging_CalciumDecay_toggleButton.isChecked():
            self.ui.Imaging_CalciumDecay_Slider.setEnabled(True)
            self.CalciumDecayValue = self.ui.Imaging_CalciumDecay_Slider.value()
            self.ui.Imaging_CalciumDecay_Readings.setText(str(self.CalciumDecayValue))
            self.ui.Imaging_CalciumDecay_Readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[10])) + "; font: 700 10pt;")
        else:
            self.ui.Imaging_CalciumDecay_Slider.setEnabled(False)
            self.ui.Imaging_CalciumDecay_Slider.setValue(200)
            self.ui.Imaging_CalciumDecay_Readings.setText('')

    def GetCalciumDecay(self):
        self.CalciumDecayValue = self.ui.Imaging_CalciumDecay_Slider.value()
        self.ui.Imaging_CalciumDecay_Readings.setText(str(self.CalciumDecayValue))
        self.ui.Imaging_CalciumDecay_Readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[10])) + "; font: 700 10pt;")


    # CalciumJump
    def ActivateCalciumJump(self):
        if self.ui.Imaging_CalciumJump_toggleButton.isChecked():
            self.ui.Imaging_CalciumJump_Slider.setEnabled(True)
            self.CalciumJumpValue = self.ui.Imaging_CalciumJump_Slider.value()
            self.ui.Imaging_CalciumJump_Readings.setText(str(self.CalciumJumpValue/100))
            self.ui.Imaging_CalciumJump_Readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[10])) + "; font: 700 10pt;")
        else:
            self.ui.Imaging_CalciumJump_Slider.setEnabled(False)
            self.ui.Imaging_CalciumJump_Slider.setValue(1)
            self.ui.Imaging_CalciumJump_Readings.setText('')

    def GetCalciumJump(self):
        self.CalciumJumpValue = self.ui.Imaging_CalciumJump_Slider.value()
        self.ui.Imaging_CalciumJump_Readings.setText(str(self.CalciumJumpValue/100))
        self.ui.Imaging_CalciumJump_Readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[10])) + "; font: 700 10pt;")


    # CalciumNoise
    def ActivateCalciumNoise(self):
        if self.ui.Imaging_CalciumNoise_toggleButton.isChecked():
            self.ui.Imaging_CalciumNoise_Slider.setEnabled(True)
            self.CalciumNoiseValue = self.ui.Imaging_CalciumNoise_Slider.value()
            self.ui.Imaging_CalciumNoise_Readings.setText(str(self.CalciumNoiseValue/10))
            self.ui.Imaging_CalciumNoise_Readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[10])) + "; font: 700 10pt;")
        else:
            self.ui.Imaging_CalciumNoise_Slider.setEnabled(False)
            self.ui.Imaging_CalciumNoise_Slider.setValue(0)
            self.ui.Imaging_CalciumNoise_Readings.setText('')

    def GetCalciumNoise(self):
        self.CalciumNoiseValue = self.ui.Imaging_CalciumNoise_Slider.value()
        self.ui.Imaging_CalciumNoise_Readings.setText(str(self.CalciumNoiseValue/10))
        self.ui.Imaging_CalciumNoise_Readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[10])) + "; font: 700 10pt;")


    # CalciumBaseline
    def ActivateCalciumBaseline(self):
        if self.ui.Imaging_CalciumBaseline_toggleButton.isChecked():
            self.ui.Imaging_CalciumBaseline_Slider.setEnabled(True)
            self.CalciumBaselineValue = self.ui.Imaging_CalciumBaseline_Slider.value()
            self.ui.Imaging_CalciumBaseline_Readings.setText(str(self.CalciumBaselineValue/100))
            self.ui.Imaging_CalciumBaseline_Readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[10])) + "; font: 700 10pt;")
        else:
            self.ui.Imaging_CalciumBaseline_Slider.setEnabled(False)
            self.ui.Imaging_CalciumBaseline_Slider.setValue(5)
            self.ui.Imaging_CalciumBaseline_Readings.setText('')

    def GetCalciumBaseline(self):
        self.CalciumBaselineValue = self.ui.Imaging_CalciumBaseline_Slider.value()
        self.ui.Imaging_CalciumBaseline_Readings.setText(str(self.CalciumBaselineValue/100))
        self.ui.Imaging_CalciumBaseline_Readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[10])) + "; font: 700 10pt;")


    # ------------------------------------------------------------------
    # Fluorescence parameters
    # ------------------------------------------------------------------

    # Indicator affinity Kd (µM)
    def Activatekd(self):
        """Toggle the Kd slider; default comes from the GECI preset table."""
        toggle_indicator_slider(self.ui, "Imaging_kd_toggleButton",
                                "Imaging_kd_Slider", "Imaging_kd_Readings")

    def Getkd(self):
        """Display Kd in µM, decoded through the shared slider encoding."""
        refresh_indicator_readout(self.ui, "Imaging_kd_Slider",
                                  "Imaging_kd_Readings")

    # Cooperativity (Hill coefficient n)
    def ActivateHill(self):
        """Toggle the Hill-coefficient slider."""
        toggle_indicator_slider(self.ui, "Imaging_Hill_toggleButton",
                                "Imaging_Hill_Slider", "Imaging_Hill_Readings")

    def GetHill(self):
        """Display the dimensionless Hill coefficient."""
        refresh_indicator_readout(self.ui, "Imaging_Hill_Slider",
                                  "Imaging_Hill_Readings")

    # Indicator rise time constant (ms)
    def ActivateIndRise(self):
        """Toggle the indicator rise-τ slider."""
        toggle_indicator_slider(self.ui, "Imaging_IndRise_toggleButton",
                                "Imaging_IndRise_Slider", "Imaging_IndRise_Readings")

    def GetIndRise(self):
        """Display the indicator rise time constant in ms."""
        refresh_indicator_readout(self.ui, "Imaging_IndRise_Slider",
                                  "Imaging_IndRise_Readings")

    # Indicator decay time constant (ms)
    def ActivateIndDecay(self):
        """Toggle the indicator decay-τ slider."""
        toggle_indicator_slider(self.ui, "Imaging_IndDecay_toggleButton",
                                "Imaging_IndDecay_Slider", "Imaging_IndDecay_Readings")

    def GetIndDecay(self):
        """Display the indicator decay time constant in ms."""
        refresh_indicator_readout(self.ui, "Imaging_IndDecay_Slider",
                                  "Imaging_IndDecay_Readings")

    # Dynamic range (max ΔF/F0 at saturation)
    def ActivateDFF(self):
        """Toggle the ΔF/F0max slider."""
        toggle_indicator_slider(self.ui, "Imaging_DFF_toggleButton",
                                "Imaging_DFF_Slider", "Imaging_DFF_Readings")

    def GetDFF(self):
        """Display the saturation amplitude ΔF/F0max."""
        refresh_indicator_readout(self.ui, "Imaging_DFF_Slider",
                                  "Imaging_DFF_Readings")

    # Brightness / Gain
    def ActivateFluoScale(self):
        if self.ui.Imaging_FluoScale_toggleButton.isChecked():
            self.ui.Imaging_FluoScale_Slider.setEnabled(True)
            self.FluoScaleValue = self.ui.Imaging_FluoScale_Slider.value()
            self.ui.Imaging_FluoScale_Readings.setText(str(self.FluoScaleValue / 10))
            self.ui.Imaging_FluoScale_Readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")
        else:
            self.ui.Imaging_FluoScale_Slider.setEnabled(False)
            self.ui.Imaging_FluoScale_Slider.setValue(50)
            self.ui.Imaging_FluoScale_Readings.setText('')

    def GetFluoScale(self):
        self.FluoScaleValue = self.ui.Imaging_FluoScale_Slider.value()
        self.ui.Imaging_FluoScale_Readings.setText(str(self.FluoScaleValue / 10))
        self.ui.Imaging_FluoScale_Readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")


    # Detector baseline (Fluorescence Offset)
    def ActivateFluoOffset(self):
        if self.ui.Imaging_FluoOffset_toggleButton.isChecked():
            self.ui.Imaging_FluoOffset_Slider.setEnabled(True)
            self.FluoOffsetValue = self.ui.Imaging_FluoOffset_Slider.value()
            self.ui.Imaging_FluoOffset_Readings.setText(str(self.FluoOffsetValue))
            self.ui.Imaging_FluoOffset_Readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")
        else:
            self.ui.Imaging_FluoOffset_Slider.setEnabled(False)
            self.ui.Imaging_FluoOffset_Slider.setValue(1)
            self.ui.Imaging_FluoOffset_Readings.setText('')

    def GetFluoOffset(self):
        self.FluoOffsetValue = self.ui.Imaging_FluoOffset_Slider.value()
        self.ui.Imaging_FluoOffset_Readings.setText(str(self.FluoOffsetValue))
        self.ui.Imaging_FluoOffset_Readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")


    # Fluorescence Noise
    def ActivateFluoNoise(self):
        if self.ui.Imaging_FluoNoise_toggleButton.isChecked():
            self.ui.Imaging_FluoNoise_Slider.setEnabled(True)
            self.FluoNoiseValue = self.ui.Imaging_FluoNoise_Slider.value()
            self.ui.Imaging_FluoNoise_Readings.setText(str(self.FluoNoiseValue / 10))
            self.ui.Imaging_FluoNoise_Readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")
        else:
            self.ui.Imaging_FluoNoise_Slider.setEnabled(False)
            self.ui.Imaging_FluoNoise_Slider.setValue(20)
            self.ui.Imaging_FluoNoise_Readings.setText('')

    def GetFluoNoise(self):
        self.FluoNoiseValue = self.ui.Imaging_FluoNoise_Slider.value()
        self.ui.Imaging_FluoNoise_Readings.setText(str(self.FluoNoiseValue / 10))
        self.ui.Imaging_FluoNoise_Readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")


    # Photon Shot Noise
    def ActivatePhotoShotNoise(self):
        if self.ui.Imaging_PhotoShotNoise_toggleButton.isChecked():
            self.ui.Imaging_PhotoShotNoise_Slider.setEnabled(True)
            self.PSNValue = self.ui.Imaging_PhotoShotNoise_Slider.value()
            self.ui.Imaging_PhotoShotNoise_Readings.setText(str(self.PSNValue / 1000000))
            self.ui.Imaging_PhotoShotNoise_Readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")
        else:
            self.ui.Imaging_PhotoShotNoise_Slider.setEnabled(False)
            self.ui.Imaging_PhotoShotNoise_Slider.setValue(200)
            self.ui.Imaging_PhotoShotNoise_Readings.setText('')

    def GetPhotoShotNoise(self):
        self.PSNValue = self.ui.Imaging_PhotoShotNoise_Slider.value()
        self.ui.Imaging_PhotoShotNoise_Readings.setText(str(self.PSNValue / 1000000))
        self.ui.Imaging_PhotoShotNoise_Readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")

# ----------------------------------------------------------------------
# Indicator-chemistry sliders (shared Kd / Hill / ΔF/F0max / τ handlers)
# ----------------------------------------------------------------------

READOUT_STYLE = ("color: rgb" + str(tuple(Settings.DarkSolarized[4]))
                 + "; font: 700 10pt;")


def refresh_indicator_readout(ui, slider_name: str, label_name: str) -> None:
    """
    Display one indicator slider in physical units.

    Module-level rather than a method because the ``Activate*``/``Get*``
    handlers are connected as unbound functions receiving the main window as
    ``self``, so instance helpers of :class:`Imaging` are unreachable from them.

    Parameters
    ----------
    ui : object
        Generated Ui object.
    slider_name, label_name : str
        Attribute names of the slider and of its read-out label.
    """
    label = getattr(ui, label_name, None)
    if label is None:
        return
    label.setText(Graph_Imaging.format_slider_units(ui, slider_name))
    label.setStyleSheet(READOUT_STYLE)


def toggle_indicator_slider(ui, toggle_name: str, slider_name: str,
                            label_name: str) -> None:
    """
    Enable one indicator slider, or disable it and restore its default.

    Parameters
    ----------
    ui : object
        Generated Ui object.
    toggle_name, slider_name, label_name : str
        Attribute names of the :class:`PyToggle`, the slider and the label.
    """
    enabled = getattr(ui, toggle_name).isChecked()
    getattr(ui, slider_name).setEnabled(enabled)

    if enabled:
        refresh_indicator_readout(ui, slider_name, label_name)
        return

    Graph_Imaging.reset_slider_to_default(ui, slider_name)
    label = getattr(ui, label_name, None)
    if label is not None:
        label.setText('')
