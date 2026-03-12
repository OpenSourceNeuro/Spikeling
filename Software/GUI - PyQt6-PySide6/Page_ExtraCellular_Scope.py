
########################################################################
#                          Libraries import                            #

from __future__ import annotations
from PySide6.QtWidgets import QFileDialog

import Parameters_Settings as Settings



class Scope():

    def __init__(self, parent):
        self.parent = parent
        self.ui = parent.ui

        # Local state flags (used by RecordButton gating)
        self.ExtraCellularFolderFlag = False
        self.ExtraCellularConnectionFlag = False

        # Last tetrode geometry saved from the auxiliary tetrode window
        self.tetrode_geometry = None
        self.tetrode_distance_matrix_um = {}
        self.tetrode_contacts_um = []


    # ------------------------------------------------------------------
    # Page selection
    # ------------------------------------------------------------------
    def ShowPage(self):
        self.ui.mainbody_stackedWidget.setCurrentWidget(self.ui.page_301)


    # ------------------------------------------------------------------
    # Source selection: hardware vs emulator
    # ------------------------------------------------------------------
    def UpdateSource(self):
        """
        Push UI selection down to parent.extracellular_graph.set_source_mode().
        """
        extracellular_graph = getattr(self.parent, "extracellular_graph", None)
        if extracellular_graph is None:
            print("UpdateSource: extracellular_graph not found on MainWindow")
            return

        # 0 -> Spikeling hardware, 1 -> Emulator
        idx = self.ui.ExtraCellular_Source_comboBox.currentIndex()
        mode = "emulator" if idx == 1 else "spikeling"
        extracellular_graph.set_source_mode(mode)

        # Connect or disconnect according to button state
        if self.ui.ExtraCellular_ConnectButton.isChecked():
            extracellular_graph.connect()
        else:
            extracellular_graph.disconnect()

    def apply_tetrode_geometry(self, payload: dict) -> None:
        self.tetrode_geometry = payload

        eg = getattr(self.parent, "extracellular_graph", None) or getattr(self.parent, "ExtracellularGraph", None)
        if eg is None:
            print("apply_tetrode_geometry: extracellular_graph not found on MainWindow")
            return

        if hasattr(eg, "apply_tetrode_geometry"):
            eg.apply_tetrode_geometry(payload)

        print("Extracellular tetrode geometry updated.")

    # ------------------------------------------------------------------
    # Data Recording Functions
    # ------------------------------------------------------------------
    def BrowseRecordFolder(self):
        FolderName = QFileDialog.getExistingDirectory(
            caption='Hey! Select the folder where your experiment will be saved',
            dir="./Recordings")
        if FolderName:
            self.ui.ExtraCellular_DataRecording_SelectRecordFolder_label.setText(FolderName)
            self.ui.ExtraCellular_DataRecording_RecordFolder_value.setEnabled(True)
            self.ui.ExtraCellular_DataRecording_RecordFolder_value.setPlaceholderText("Enter a file name")
            self.ExtraCellularFolderFlag = True


    def RecordFolderText(self):
        FolderName = self.ui.ExtraCellular_DataRecording_SelectRecordFolder_label.text()
        FileName = self.ui.ExtraCellular_DataRecording_RecordFolder_value.text()
        self.ui.ExtraCellular_SelectedFolderLabel.setText(FolderName + '/' + FileName)

    def RecordButton(self):
        """
        Start/stop recording Imaging data.

        Conditions to start recording:
          - ExtraCellular is connected (to hardware OR emulator)
          - A folder has been selected
          - A file name has been entered
        """

        # User is trying to START recording
        if self.ui.ExtraCellular_DataRecording_Record_pushButton.isChecked():
            # 1) Check ExtraCellular Scope is connected
            if not getattr(self, "ExtraCellularConnectionFlag", False):
                self.ui.ExtraCellular_DataRecording_Record_pushButton.setChecked(False)
                Settings.show_popup(self, Title="Error: Spikeling not connected",
                                          Text=("Spikeling data stream first needs to be connected. "
                                          "Check that a spikeling is running on either the neuron "
                                          "interface or the neuron emulator tab."))
                return

            # 2) Check folder is selected
            if not getattr(self, "ExtraCellularFolderFlag", False):
                self.ui.ExtraCellular_DataRecording_Record_pushButton.setChecked(False)
                Settings.show_popup(self, Title="Error: no folder selected",
                                          Text=("Select a folder where to record your data by clicking on "
                                                "the - browse directory - button."))
                return

            # 3) Check file name is provided
            if not self.ui.ExtraCellular_DataRecording_RecordFolder_value.text():
                self.ui.ExtraCellular_DataRecording_Record_pushButton.setChecked(False)
                Settings.show_popup(self, Title="Error: no file selected",
                                        Text=("Select a file where to record your data by entering a name "
                                              "in the file name field."))
                return

            # 4) All conditions OK -> enter recording mode
            self.ui.ExtraCellular_DataRecording_Record_pushButton.setText("Stop Recording")
            self.ui.ExtraCellular_DataRecording_Record_pushButton.setStyleSheet("color: rgb(250, 250, 250);\n"
                                                                          "background-color: rgb(50, 220, 47);")

        # User is STOPPING recording
        else:
            self.ui.ExtraCellular_DataRecording_Record_pushButton.setText("Record")
            self.ui.ExtraCellular_DataRecording_Record_pushButton.setStyleSheet("color: rgb(250, 250, 250);\n"
                                                                          "background-color: rgb(220, 50, 47);")

    # ------------------------------------------------------------------
    # Signal mode selection: single toggle
    #   unchecked -> "template"
    #   checked   -> "dvdt"
    # ------------------------------------------------------------------
    def _ensure_signal_mode_toggle_guard(self):
        """Internal one-time init for recursion guard."""
        if not hasattr(self, "_updating_signal_mode_toggle"):
            self._updating_signal_mode_toggle = False

    def _apply_signal_mode(self, mode: str) -> None:
        """
        mode:
          - "template"
          - "dvdt"
        """
        eg = getattr(self.parent, "extracellular_graph", None) or getattr(self.parent, "ExtracellularGraph", None)
        if eg is None:
            return

        # Prefer explicit API if present
        if hasattr(eg, "set_signal_mode"):
            eg.set_signal_mode(mode)
        else:
            # Fallback attribute
            eg.signal_mode = mode

            # Redraw if possible
            if hasattr(eg, "_update_plots"):
                eg._update_plots()
            elif hasattr(eg, "update"):
                eg.update()

        # Optional: update the toggle label so user knows what "ON" means
        # (keep if you like; otherwise remove)
        try:
            if mode == "dvdt":
                self.ui.ExtraCellular_Mode_Template_label.setStyleSheet("color: rgb(190, 205, 205); font-weight: normal;")
                self.ui.ExtraCellular_Mode_dVdT_label.setStyleSheet("color: rgb(42, 161, 152); font-weight: bold;")
            else:
                self.ui.ExtraCellular_Mode_Template_label.setStyleSheet("color: rgb(38, 139, 210); font-weight: bold;")
                self.ui.ExtraCellular_Mode_dVdT_label.setStyleSheet("color: rgb(190, 205, 205); font-weight: normal;")
        except Exception:
            pass

    def SignalMode_toggleButton(self, checked: bool):
        """
        Single toggle mapping:
          checked   -> dV/dT
          unchecked -> Template
        """
        self._ensure_signal_mode_toggle_guard()
        if self._updating_signal_mode_toggle:
            return

        mode = "dvdt" if checked else "template"
        self._apply_signal_mode(mode)


    # ------------------------------------------------------------------
    # Electrode Parameters
    # ------------------------------------------------------------------



    # Spatial Falloff
    def ActivateSpatialFalloff(self):
        if self.ui.ExtraCellular_Spread_toggleButton.isChecked():
            self.ui.ExtraCellular_Spread_Slider.setEnabled(True)
            self.ExtraCellular_SpreadValue = self.ui.ExtraCellular_Spread_Slider.value()
            self.ui.ExtraCellular_Spread_Readings.setText(str(self.ExtraCellular_SpreadValue/10))
            self.ui.ExtraCellular_Spread_Readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[5])) + "; font: 700 10pt;")
        else:
            self.ui.ExtraCellular_Spread_Slider.setEnabled(False)
            self.ui.ExtraCellular_Spread_Slider.setValue(12)
            self.ui.ExtraCellular_Spread_Readings.setText('')

    def GetSpatialFalloff(self):
        self.ExtraCellular_SpreadValue = self.ui.ExtraCellular_Spread_Slider.value()
        self.ui.ExtraCellular_Spread_Readings.setText(str(self.ExtraCellular_SpreadValue/10))
        self.ui.ExtraCellular_Spread_Readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[5])) + "; font: 700 10pt;")


    # ------------------------------------------------------------------
    # Noise parameters
    # ------------------------------------------------------------------

    # Baseline Noise
    def ActivateBaselineNoise(self):
        if self.ui.ExtraCellular_BaselineNoise_toggleButton.isChecked():
            self.ui.ExtraCellular_BaselineNoise_Slider.setEnabled(True)
            self.ExtraCellular_BaselineNoiseValue = self.ui.ExtraCellular_BaselineNoise_Slider.value()
            self.ui.ExtraCellular_BaselineNoise_Readings.setText(str(self.ExtraCellular_BaselineNoiseValue))
            self.ui.ExtraCellular_BaselineNoise_Readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")
        else:
            self.ui.ExtraCellular_BaselineNoise_Slider.setEnabled(False)
            self.ui.ExtraCellular_BaselineNoise_Slider.setValue(5)
            self.ui.ExtraCellular_BaselineNoise_Readings.setText('')

    def GetBaselineNoise(self):
        self.ExtraCellular_BaselineNoiseValue = self.ui.ExtraCellular_BaselineNoise_Slider.value()
        self.ui.ExtraCellular_BaselineNoise_Readings.setText(str(self.ExtraCellular_BaselineNoiseValue))
        self.ui.ExtraCellular_BaselineNoise_Readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")


    # Shared Noise
    def ActivateSharedNoise(self):
        if self.ui.ExtraCellular_SharedNoise_toggleButton.isChecked():
            self.ui.ExtraCellular_SharedNoise_Slider.setEnabled(True)
            self.ExtraCellular_SharedNoiseValue = self.ui.ExtraCellular_SharedNoise_Slider.value()
            self.ui.ExtraCellular_SharedNoise_Readings.setText(str(self.ExtraCellular_SharedNoiseValue))
            self.ui.ExtraCellular_SharedNoise_Readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")
        else:
            self.ui.ExtraCellular_SharedNoise_Slider.setEnabled(False)
            self.ui.ExtraCellular_SharedNoise_Slider.setValue(5)
            self.ui.ExtraCellular_SharedNoise_Readings.setText('')

    def GetSharedNoise(self):
        self.ExtraCellular_SharedNoiseValue = self.ui.ExtraCellular_SharedNoise_Slider.value()
        self.ui.ExtraCellular_SharedNoise_Readings.setText(str(self.ExtraCellular_SharedNoiseValue))
        self.ui.ExtraCellular_SharedNoise_Readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")


    # 50Hz Hum
    def ActivateHumNoise(self):
        if self.ui.ExtraCellular_HumNoise_toggleButton.isChecked():
            self.ui.ExtraCellular_HumNoise_Slider.setEnabled(True)
            self.ExtraCellular_HumNoiseValue = self.ui.ExtraCellular_HumNoise_Slider.value()
            self.ui.ExtraCellular_HumNoise_Readings.setText(str(self.ExtraCellular_HumNoiseValue))
            self.ui.ExtraCellular_HumNoise_Readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")
        else:
            self.ui.ExtraCellular_HumNoise_Slider.setEnabled(False)
            self.ui.ExtraCellular_HumNoise_Slider.setValue(0)
            self.ui.ExtraCellular_HumNoise_Readings.setText('')

    def GetHumNoise(self):
        self.ExtraCellular_HumNoiseValue = self.ui.ExtraCellular_HumNoise_Slider.value()
        self.ui.ExtraCellular_HumNoise_Readings.setText(str(self.ExtraCellular_HumNoiseValue))
        self.ui.ExtraCellular_HumNoise_Readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")


