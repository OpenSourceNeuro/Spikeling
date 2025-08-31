
########################################################################
#                          Libraries import                            #

from PySide6.QtWidgets import QFileDialog
from PySide6.QtCore import QSize

import Settings, NavigationButtons



class Imaging():

    def ShowPage(self):
        self.ui.Imaging_rightMenuContainer.setMinimumSize(QSize(NavigationButtons.spikerightMenu_max, 16777215))
        self.ui.Imaging_Oscilloscope_widget.setBackground(Settings.DarkSolarized[0])
        self.ui.mainbody_stackedWidget.setCurrentWidget(self.ui.page_201)
        NavigationButtons.toggleMenu(self, self.ui.Imaging_rightMenuContainer, NavigationButtons.spikerightMenu_min,
                                     NavigationButtons.spikerightMenu_max, NavigationButtons.animation_speed,
                                     self.ui.Imaging_rightMenuSubContainer_pushButton, self.icon_SpikelingMenuRight,
                                     self.icon_SpikelingDropMenuRight, True)


    # Data Recording Functions
    def BrowseRecordFolder(self):
        FolderName = QFileDialog.getExistingDirectory(
            caption='Hey! Select the folder where your experiment will be saved',
            dir=".\Recordings")
        if FolderName:
            self.Imaging_DataRecording_SelectRecordFolder_label.setText(FolderName)
            self.Imaging_DataRecording_RecordFolder_value.setEnabled(True)
            self.Imaging_DataRecording_RecordFolder_value.setPlaceholderText("Enter a file name")
            self.ImagingFolderFlag = True


    def RecordFolderText(self):
        FolderName = self.ui.Imaging_DataRecording_SelectRecordFolder_label.text()
        FileName = self.ui.Imaging_DataRecording_RecordFolder_value.text()
        self.ui.Imaging_SelectedFolderLabel.setText(FolderName + '/' + FileName)


    def RecordButton(self):
        ConnectionFlag = False
        FolderFlag = False
        FileFlag = False

        if self.ImagingConnectionFlag == False:
            self.ui.Imaging_DataRecording_Record_pushButton.setChecked(False)
            Settings.show_popup(self,
                                Title="Error: Spikeling not connected",
                                Text="Spikeling data stream first needs to be connected. Check that a spikeling is running on either the neuron interface or the neuron emulator tab")
        else:
            ConnectionFlag = True

        if self.ui.ImagingFolderFlag == True:
            FolderFlag = True

        else:
            self.ui.Imaging_DataRecording_Record_pushButton.setChecked(False)
            Settings.show_popup(self,
                                Title="Error: no folder selected",
                                Text="Select a folder where to record your data by clicking on the - browse directory - button")

        if self.ui.Imaging_DataRecording_RecordFolder_value.text():
            FileFlag = True
        else:
            self.ui.Imaging_DataRecording_Record_pushButton.setChecked(False)
            Settings.show_popup(self,
                                Title="Error: no file selected",
                                Text="Select a file where to record your data by clicking on the - browse directory - button")

        if ConnectionFlag == True and FolderFlag == True and FileFlag == True:
            if self.ui.Imaging_DataRecording_Record_pushButton.isChecked():
                self.ui.Imaging_DataRecording_Record_pushButton.setText("Stop Recording")
                self.ui.Imaging_DataRecording_Record_pushButton.setStyleSheet("color: rgb(250, 250, 250);\n"
                                                                                      "background-color: rgb(50, 220, 47);")

            else:
                self.ui.Imaging_DataRecording_Record_pushButton.setChecked(False)
                self.ui.Imaging_DataRecording_Record_pushButton.setText("Record")
                self.ui.Imaging_DataRecording_Record_pushButton.setStyleSheet("color: rgb(250, 250, 250);\n"
                                                                                      "background-color: rgb(220, 50, 47);")

    # FrameRate
    def ActivateFrameRate(self):
            if self.ui.Imaging_FrameRate_toggleButton.isChecked():
                    self.ui.Imaging_FrameRate_Slider.setEnabled(True)
                    self.FrameRateValue = self.ui.Imaging_FrameRate_Slider.value()
                    self.ui.Imaging_FrameRate_Readings.setText(str(self.FrameRateValue))
                    self.ui.Imaging_FrameRate_Readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")
            else:
                    self.ui.Imaging_FrameRate_Slider.setEnabled(False)
                    self.ui.Imaging_FrameRate_Slider.setValue(250)
                    self.ui.Imaging_FrameRate_Readings.setText('')

    def GetFrameRate(self):
            self.FrameRateValue = self.ui.Imaging_FrameRate_Slider.value()
            self.ui.Imaging_FrameRate_Readings.setText(str(self.FrameRateValue))
            self.ui.Imaging_FrameRate_Readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")
            self.FrameRate = self.FrameRateValue

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
            self.PMT = self.PMTValue/100

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
            self.Laser = self.LaserValue/100




    # CalciumDecay
    def ActivateCalciumDecay(self):
            if self.ui.Imaging_CalciumDecay_toggleButton.isChecked():
                    self.ui.Imaging_CalciumDecay_Slider.setEnabled(True)
                    self.CalciumDecayValue = self.ui.Imaging_CalciumDecay_Slider.value()
                    self.ui.Imaging_CalciumDecay_Readings.setText(str(self.CalciumDecayValue/10000))
                    self.ui.Imaging_CalciumDecay_Readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[10])) + "; font: 700 10pt;")
            else:
                    self.ui.Imaging_CalciumDecay_Slider.setEnabled(False)
                    self.ui.Imaging_CalciumDecay_Slider.setValue(50)
                    self.ui.Imaging_CalciumDecay_Readings.setText('')

    def GetCalciumDecay(self):
            self.CalciumDecayValue = self.ui.Imaging_CalciumDecay_Slider.value()
            self.ui.Imaging_CalciumDecay_Readings.setText(str(self.CalciumDecayValue/10000))
            self.ui.Imaging_CalciumDecay_Readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[10])) + "; font: 700 10pt;")
            self.CalciumDecay = self.CalciumDecayValue/10000

    # CalciumJump
    def ActivateCalciumJump(self):
            if self.ui.Imaging_CalciumJump_toggleButton.isChecked():
                    self.ui.Imaging_CalciumJump_Slider.setEnabled(True)
                    self.CalciumJumpValue = self.ui.Imaging_CalciumJump_Slider.value()
                    self.ui.Imaging_CalciumJump_Readings.setText(str(self.CalciumJumpValue))
                    self.ui.Imaging_CalciumJump_Readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[10])) + "; font: 700 10pt;")
            else:
                    self.ui.Imaging_CalciumJump_Slider.setEnabled(False)
                    self.ui.Imaging_CalciumJump_Slider.setValue(5)
                    self.ui.Imaging_CalciumJump_Readings.setText('')

    def GetCalciumJump(self):
            self.CalciumJumpValue = self.ui.Imaging_CalciumJump_Slider.value()
            self.ui.Imaging_CalciumJump_Readings.setText(str(self.CalciumJumpValue))
            self.ui.Imaging_CalciumJump_Readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[10])) + "; font: 700 10pt;")
            self.SpikeConcentrationRise = self.CalciumJumpValue

    # CalciumNoise
    def ActivateCalciumNoise(self):
            if self.ui.Imaging_CalciumNoise_toggleButton.isChecked():
                    self.ui.Imaging_CalciumNoise_Slider.setEnabled(True)
                    self.CalciumNoiseValue = self.ui.Imaging_CalciumNoise_Slider.value()
                    self.ui.Imaging_CalciumNoise_Readings.setText(str(self.CalciumNoiseValue/10))
                    self.ui.Imaging_CalciumNoise_Readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[10])) + "; font: 700 10pt;")
            else:
                    self.ui.Imaging_CalciumNoise_Slider.setEnabled(False)
                    self.ui.Imaging_CalciumNoise_Slider.setValue(10)
                    self.ui.Imaging_CalciumNoise_Readings.setText('')

    def GetCalciumNoise(self):
            self.CalciumNoiseValue = self.ui.Imaging_CalciumNoise_Slider.value()
            self.ui.Imaging_CalciumNoise_Readings.setText(str(self.CalciumNoiseValue/10))
            self.ui.Imaging_CalciumNoise_Readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[10])) + "; font: 700 10pt;")
            self.NoiseScale = self.CalciumNoiseValue / 10

    # CalciumBaseline
    def ActivateCalciumBaseline(self):
            if self.ui.Imaging_CalciumBaseline_toggleButton.isChecked():
                    self.ui.Imaging_CalciumBaseline_Slider.setEnabled(True)
                    self.CalciumBaselineValue = self.ui.Imaging_CalciumBaseline_Slider.value()
                    self.ui.Imaging_CalciumBaseline_Readings.setText(str(self.CalciumBaselineValue/100))
                    self.ui.Imaging_CalciumBaseline_Readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[10])) + "; font: 700 10pt;")
            else:
                    self.ui.Imaging_CalciumBaseline_Slider.setEnabled(False)
                    self.ui.Imaging_CalciumBaseline_Slider.setValue(10)
                    self.ui.Imaging_CalciumBaseline_Readings.setText('')

    def GetCalciumBaseline(self):
            self.CalciumBaselineValue = self.ui.Imaging_CalciumBaseline_Slider.value()
            self.ui.Imaging_CalciumBaseline_Readings.setText(str(self.CalciumBaselineValue/100))
            self.ui.Imaging_CalciumBaseline_Readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[10])) + "; font: 700 10pt;")
            self.CalciumBaseline = self.CalciumBaselineValue /100




    # Dissociation constant kd
    def Activatekd(self):
            if self.ui.Imaging_kd_toggleButton.isChecked():
                    self.ui.Imaging_kd_Slider.setEnabled(True)
                    self.kdValue = self.ui.Imaging_kd_Slider.value()
                    self.ui.Imaging_kd_Readings.setText(str(self.kdValue*10))
                    self.ui.Imaging_kd_Readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")
            else:
                    self.ui.Imaging_kd_Slider.setEnabled(False)
                    self.ui.Imaging_kd_Slider.setValue(20)
                    self.ui.Imaging_kd_Readings.setText('')

    def Getkd(self):
            self.kdValue = self.ui.Imaging_kd_Slider.value()
            self.ui.Imaging_kd_Readings.setText(str(self.kdValue*10))
            self.ui.Imaging_kd_Readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")
            self.DissociationConstant = self.kdValue * 10

    # Affinity (Hill constant)
    def ActivateHill(self):
            if self.ui.Imaging_Hill_toggleButton.isChecked():
                    self.ui.Imaging_Hill_Slider.setEnabled(True)
                    self.HillValue = self.ui.Imaging_Hill_Slider.value()
                    self.ui.Imaging_Hill_Readings.setText(str(self.HillValue/100))
                    self.ui.Imaging_Hill_Readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")
            else:
                    self.ui.Imaging_Hill_Slider.setEnabled(False)
                    self.ui.Imaging_Hill_Slider.setValue(100)
                    self.ui.Imaging_Hill_Readings.setText('')

    def GetHill(self):
            self.HillValue = self.ui.Imaging_Hill_Slider.value()
            self.ui.Imaging_Hill_Readings.setText(str(self.HillValue/10))
            self.ui.Imaging_Hill_Readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")
            self.HillCoef = self.HillValue /100

    # Photon Shot Noise
    def ActivatePhotoShotNoise(self):
        if self.ui.Imaging_PhotoShotNoise_toggleButton.isChecked():
            self.ui.Imaging_PhotoShotNoise_Slider.setEnabled(True)
            self.PSNValue = self.ui.Imaging_PhotoShotNoise_Slider.value()
            self.ui.Imaging_PhotoShotNoise_Readings.setText(str(self.PSNValue / 10000 / 100))
            self.ui.Imaging_PhotoShotNoise_Readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")
        else:
            self.ui.Imaging_PhotoShotNoise_Slider.setEnabled(False)
            self.ui.Imaging_PhotoShotNoise_Slider.setValue(400)
            self.ui.Imaging_PhotoShotNoise_Readings.setText('')

    def GetPhotoShotNoise(self):
        self.PSNValue = self.ui.Imaging_PhotoShotNoise_Slider.value()
        self.ui.Imaging_PhotoShotNoise_Readings.setText(str(self.PSNValue / 10000 / 100))
        self.ui.Imaging_PhotoShotNoise_Readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")
        self.PhotoShotNoise = self.PSNValue / 10000 / 100

    # Fluorescence Noise
    def ActivateFluoNoise(self):
            if self.ui.Imaging_FluoNoise_toggleButton.isChecked():
                    self.ui.Imaging_FluoNoise_Slider.setEnabled(True)
                    self.FluoNoiseValue = self.ui.Imaging_FluoNoise_Slider.value()
                    self.ui.Imaging_FluoNoise_Readings.setText(str(self.FluoNoiseValue/10))
                    self.ui.Imaging_FluoNoise_Readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")
            else:
                    self.ui.Imaging_FluoNoise_Slider.setEnabled(False)
                    self.ui.Imaging_FluoNoise_Slider.setValue(10)
                    self.ui.Imaging_FluoNoise_Readings.setText('')

    def GetFluoNoise(self):
            self.FluoNoiseValue = self.ui.Imaging_FluoNoise_Slider.value()
            self.ui.Imaging_FluoNoise_Readings.setText(str(self.FluoNoiseValue/10))
            self.ui.Imaging_FluoNoise_Readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")
            self.FluoNoiseScale = self.FluoNoiseValue /10

    # Fluorescence Scale
    def ActivateFluoScale(self):
            if self.ui.Imaging_FluoScale_toggleButton.isChecked():
                    self.ui.Imaging_FluoScale_Slider.setEnabled(True)
                    self.FluoScaleValue = self.ui.Imaging_FluoScale_Slider.value()
                    self.ui.Imaging_FluoScale_Readings.setText(str(self.FluoScaleValue/10))
                    self.ui.Imaging_FluoScale_Readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")
            else:
                    self.ui.Imaging_FluoScale_Slider.setEnabled(False)
                    self.ui.Imaging_FluoScale_Slider.setValue(10)
                    self.ui.Imaging_FluoScale_Readings.setText('')

    def GetFluoScale(self):
            self.FluoScaleValue = self.ui.Imaging_FluoScale_Slider.value()
            self.ui.Imaging_FluoScale_Readings.setText(str(self.FluoScaleValue/10))
            self.ui.Imaging_FluoScale_Readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")
            self.FluoScale = self.FluoScaleValue /10

    # Fluorescence Offset
    def ActivateFluoOffset(self):
            if self.ui.Imaging_FluoOffset_toggleButton.isChecked():
                    self.ui.Imaging_FluoOffset_Slider.setEnabled(True)
                    self.FluoOffsetValue = self.ui.Imaging_FluoOffset_Slider.value()
                    self.ui.Imaging_FluoOffset_Readings.setText(str(self.FluoOffsetValue))
                    self.ui.Imaging_FluoOffset_Readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")
            else:
                    self.ui.Imaging_FluoOffset_Slider.setEnabled(False)
                    self.ui.Imaging_FluoOffset_Slider.setValue(5)
                    self.ui.Imaging_FluoOffset_Readings.setText('')

    def GetFluoOffset(self):
            self.FluoOffsetValue = self.ui.Imaging_FluoOffset_Slider.value()
            self.ui.Imaging_FluoOffset_Readings.setText(str(self.FluoOffsetValue))
            self.ui.Imaging_FluoOffset_Readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")
            self.FluoOffset = self.FluoOffsetValue


    def ActivateFluoSat(self):
            if self.ui.Imaging_Saturation_toggleButton.isChecked():
                self.ui.Imaging_FluoSat_Label.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])))
                self.ui.Imaging_kd_frame.setStyleSheet("background-color: rgb" + str(tuple(Settings.DarkSolarized[1])))
                self.ui.Imaging_Saturation_Line.setStyleSheet("background-color: rgb" + str(tuple(Settings.DarkSolarized[0])))
                self.ui.Imaging_Hill_frame.setStyleSheet("background-color: rgb" + str(tuple(Settings.DarkSolarized[1])))
                self.ui.Imaging_Saturation_Line2.setStyleSheet("background-color: rgb" + str(tuple(Settings.DarkSolarized[0])))
                self.ui.Imaging_PhotoShotNoise_frame.setStyleSheet("background-color: rgb" + str(tuple(Settings.DarkSolarized[1])))
                self.ui.Imaging_kd_toggleButton.setEnabled(True)
                self.ui.Imaging_Hill_toggleButton.setEnabled(True)
                self.ui.Imaging_PhotoShotNoise_toggleButton.setEnabled(True)
                self.SaturationFlag = True
                self.FluoNoiseScale = self.ui.Imaging_FluoNoise_Slider.value() / 10
            else:
                self.ui.Imaging_FluoSat_Label.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[14])))
                self.ui.Imaging_kd_frame.setStyleSheet("background-color: rgb(80, 96, 100)")
                self.ui.Imaging_Saturation_Line.setStyleSheet("background-color: rgb(80, 96, 100)")
                self.ui.Imaging_Hill_frame.setStyleSheet("background-color: rgb(80, 96, 100)")
                self.ui.Imaging_Saturation_Line2.setStyleSheet("background-color: rgb(80, 96, 100)")
                self.ui.Imaging_PhotoShotNoise_frame.setStyleSheet("background-color: rgb(80, 96, 100)")
                self.ui.Imaging_kd_toggleButton.setEnabled(False)
                self.ui.Imaging_Hill_toggleButton.setEnabled(False)
                self.ui.Imaging_PhotoShotNoise_toggleButton.setEnabled(False)
                self.ui.Imaging_kd_toggleButton.setChecked(False)
                self.ui.Imaging_Hill_toggleButton.setChecked(False)
                self.ui.Imaging_PhotoShotNoise_toggleButton.setChecked(False)
                self.SaturationFlag = False
                self.FluoNoiseScale = self.ui.Imaging_FluoNoise_Slider.value() / 10



