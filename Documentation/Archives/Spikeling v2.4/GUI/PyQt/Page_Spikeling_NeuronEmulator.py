
########################################################################
#                          Libraries import                            #

from PySide6.QtWidgets import QFileDialog
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize, QFileInfo

import os
import numpy as np
import pandas as pd

from Izhikevich_parameters import IzhikevichNeurons

import Settings, NavigationButtons


class Emulator():

    def ShowPage(self):
        self.ui.Emulator_rightMenuContainer.setMinimumSize(QSize(NavigationButtons.spikerightMenu_max, 16777215))
        self.ui.mainbody_stackedWidget.setCurrentWidget(self.ui.page_102)
        self.ui.Emulator_Oscilloscope_widget.setBackground(Settings.DarkSolarized[0])
        self.ui.Emulator_CustomStimulus_display.setBackground(Settings.DarkSolarized[0])
        NavigationButtons.toggleMenu(self, self.ui.Emulator_rightMenuContainer, NavigationButtons.spikerightMenu_min, NavigationButtons.spikerightMenu_max, NavigationButtons.animation_speed,
                                     self.ui.Emulator_rightMenuSubContainer_pushButton, self.icon_SpikelingMenuRight, self.icon_SpikelingDropMenuRight, True)



    # Data Recording Functions
    def BrowseRecordFolder(self):
        FolderName = QFileDialog.getExistingDirectory(caption = 'Hey! Select the folder where your experiment will be saved',
                                                      dir = ".\Recordings")
        if FolderName:
            self.Emulator_DataRecording_SelectRecordFolder_label.setText(FolderName)
            self.Emulator_DataRecording_RecordFolder_value.setEnabled(True)
            self.Emulator_DataRecording_RecordFolder_value.setPlaceholderText("Enter a file name")
            self.EmulatorRecordFolderFlag = True


    def RecordFolderText(self):
        FolderName = self.ui.Emulator_DataRecording_SelectRecordFolder_label.text()
        FileName = self.ui.Emulator_DataRecording_RecordFolder_value.text()
        self.ui.Emulator_SelectedFolderLabel.setText(FolderName + '/' + FileName)


    def RecordButton(self):
        ConnectionFlag = False
        FolderFlag = False
        FileFlag = False

        if self.ui.Emulator_DataRecording_Record_pushButton.isChecked():

            if self.EmulatorConnectionFlag == False:
                self.ui.Emulator_DataRecording_Record_pushButton.setChecked(False)
                Settings.show_popup(self,
                                    Title="Emulator not started",
                                    Text="Spikeling emulator data stream first needs to be started by clicking on the - Start Spikeling Emulator - button")
            else:
                ConnectionFlag = True


            if self.ui.EmulatorRecordFolderFlag == True:
                FolderFlag = True

            else:
                self.ui.Emulator_DataRecording_Record_pushButton.setChecked(False)
                Settings.show_popup(self,
                                    Title = "Error: no folder selected",
                                    Text = "Select a folder where to record your data by clicking on the - browse directory - button")


            if self.ui.Emulator_DataRecording_RecordFolder_value.text():
                FileFlag = True

            else:
                self.ui.Emulator_DataRecording_Record_pushButton.setChecked(False)
                Settings.show_popup(self,
                                    Title="Error: no file selected",
                                    Text="Select a file where to record your data by clicking on the - browse directory - button")


            if ConnectionFlag == True and FolderFlag == True and FileFlag == True:
                if self.ui.Emulator_DataRecording_Record_pushButton.isChecked():
                    self.ui.Emulator_DataRecording_Record_pushButton.setText("Stop Recording")
                    self.ui.Emulator_DataRecording_Record_pushButton.setStyleSheet("color: rgb(250, 250, 250);\n"
                                                                                    "background-color: rgb(50, 220, 47);")

        else:
            self.ui.Emulator_DataRecording_Record_pushButton.setText("Record")
            self.ui.Emulator_DataRecording_Record_pushButton.setStyleSheet("color: rgb(250, 250, 250);\n"
                                                                            "background-color: rgb(220, 50, 47);")


    # Stimulus Frequency
    def ActivateStimFre(self):
            if self.ui.EmulatorStimFre_toggleButton.isChecked():
                    self.EmulatorStim_DutyCycle = 500
                    self.EmulatorStim_MinCycle = 10
                    self.ui.Emulator_StimFre_slider.setEnabled(True)
                    self.EmulatorStimFreValue = self.ui.Emulator_StimFre_slider.value()*(-1)
                    self.setTextEmulatorStimFre = str(int(np.around(10000/(self.EmulatorStim_DutyCycle + (self.EmulatorStimFreValue*self.EmulatorStim_DutyCycle/100) + self.EmulatorStim_MinCycle))))
                    self.ui.Emulator_StimFre_readings.setText(self.setTextEmulatorStimFre)
                    self.ui.Emulator_StimFre_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[5])) + "; font: 700 10pt;")

            else:
                    self.ui.Spikeling_StimFre_slider.setEnabled(False)
                    self.ui.Spikeling_StimFre_slider.setValue(0)
                    self.ui.Spikeling_StimFre_readings.setText('')


    def GetStimFreSliderValue(self):
            self.EmulatorStimFreValue = self.ui.Emulator_StimFre_slider.value()*(-1)
            self.setTextEmulatorStimFre = str(int(np.around(10000/(self.EmulatorStim_DutyCycle + (self.EmulatorStimFreValue*self.EmulatorStim_DutyCycle/100) + self.EmulatorStim_MinCycle))))
            self.ui.Emulator_StimFre_readings.setText(self.setTextEmulatorStimFre)
            self.ui.Emulator_StimFre_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[5])) + "; font: 700 10pt;")


    # Stimulus Strength
    def ActivateStimStr(self):
            if self.ui.EmulatorStimStr_toggleButton.isChecked():
                    self.ui.Emulator_StimStrSlider.setEnabled(True)
                    self.EmulatorStimStrValue = self.ui.Emulator_StimStrSlider.value()
                    self.ui.Emulator_StimStr_readings.setText(str(self.EmulatorStimStrValue))
                    self.ui.Emulator_StimStr_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[5])) + "; font: 700 10pt;")

            else:
                    self.ui.Emulator_StimStrSlider.setEnabled(False)
                    self.ui.Emulator_StimStrSlider.setValue(0)
                    self.ui.Emulator_StimStr_readings.setText('')


    def GetStimStrSliderValue(self):
            self.EmulatorStimStrValue = self.ui.Emulator_StimStrSlider.value()
            self.ui.Emulator_StimStr_readings.setText(str(self.EmulatorStimStrValue))
            self.ui.Emulator_StimStr_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[5])) + "; font: 700 10pt;")


    # Custom Stimulus
    def ActivateCustomStimulus(self):
            if self.ui.EmulatorStimCus_toggleButton.isChecked():
                self.ui.StimCus_Flag = True
            else:
                self.ui.StimCus_Flag = False



    def LoadStimulus(self):
        FileName, _ = QFileDialog.getOpenFileName(self,
                                               caption='Select a custom stimulus',
                                               dir="./Stimuli",
                                               filter='csv files (*.csv)'
                                               )
        self.filename = os.path.splitext(os.path.basename(QFileInfo(FileName).fileName()))[0]
        self.ui.Emulator_CustomStimulus_StimLabel.setText(self.filename)

        Df = pd.read_csv(FileName)
        self.Emulatordf_Stim = Df["Stim"]

        self.Emulatordf_xStim = np.linspace(0, len(self.Emulatordf_Stim)/10 - 1, len(self.Emulatordf_Stim))

        self.ui.Emulatordf_yStim = np.zeros(len(self.Emulatordf_Stim))
        self.ui.Emulatordf_yStim = self.Emulatordf_Stim

        self.ui.Emulator_CustomStimulus_display.clear()
        self.ui.Emulator_Oscilloscope_widget.showGrid(x=False, y=False)
        self.ui.Emulator_CustomStimulus_display.plot(x=self.Emulatordf_xStim, y=self.ui.Emulatordf_yStim, pen=(Settings.DarkSolarized[5]))



    # PhotoGain
    def ActivatePhotoGain(self):
            if self.ui.EmulatorPhotoGain_toggleButton.isChecked():
                    self.ui.Emulator_PR_PhotoGain_slider.setEnabled(True)
                    self.EmulatorPhotoGain = self.ui.Emulator_PR_PhotoGain_slider.value()
                    self.ui.Emulator_PR_Photogain_readings.setText(str(self.EmulatorPhotoGain))
                    self.ui.Emulator_PR_Photogain_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")
            else:
                    self.ui.Emulator_PR_PhotoGain_slider.setEnabled(False)
                    self.ui.Emulator_PR_PhotoGain_slider.setValue(0)
                    self.ui.Emulator_PR_Photogain_readings.setText("")


    def GetPhotoGain(self):
            self.EmulatorPhotoGain = self.ui.Emulator_PR_PhotoGain_slider.value()
            self.ui.Emulator_PR_Photogain_readings.setText(str(self.EmulatorPhotoGain))
            self.ui.Emulator_PR_Photogain_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")



    # PhotoDecay
    def ActivatePRDecay(self):
            if self.ui.EmulatorPhotoDecay_toggleButton.isChecked():
                    self.ui.Emulator_PR_Decay_slider.setEnabled(True)
                    self.EmulatorPhotoDecay = self.ui.Emulator_PR_Decay_slider.value()
                    self.ui.Emulator_PR_Decay_readings.setText(str(self.EmulatorPhotoDecay/100000))
                    self.ui.Emulator_PR_Decay_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")


            else:
                    self.ui.Emulator_PR_Decay_slider.setEnabled(False)
                    self.ui.Emulator_PR_Decay_slider.setValue(100)
                    self.ui.Emulator_PR_Decay_readings.setText("")



    def GetPRDecay(self):
            self.EmulatorPhotoDecay = self.ui.Emulator_PR_Decay_slider.value()
            self.ui.Emulator_PR_Decay_readings.setText(str(self.EmulatorPhotoDecay/100000))
            self.ui.Emulator_PR_Decay_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")


    # PhotoRecovery
    def ActivatePRRecovery(self):
            if self.ui.EmulatorPhotoRecovery_toggleButton.isChecked():
                    self.ui.Emulator_PR_Recovery_slider.setEnabled(True)
                    self.EmulatorPhotoRecovery = self.ui.Emulator_PR_Recovery_slider.value()
                    self.ui.Emulator_PR_Recovery_readings.setText(str(self.EmulatorPhotoRecovery/1000))
                    self.ui.Emulator_PR_Recovery_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")

            else:
                    self.ui.Emulator_PR_Recovery_slider.setEnabled(False)
                    self.ui.Emulator_PR_Recovery_slider.setValue(25)
                    self.ui.Emulator_PR_Recovery_readings.setText("")



    def GetPRRecovery(self):
            self.EmulatorPhotoRecovery = self.ui.Emulator_PR_Recovery_slider.value()
            self.ui.Emulator_PR_Recovery_readings.setText(str(self.EmulatorPhotoRecovery/1000))
            self.ui.Emulator_PR_Recovery_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")



    # PatchClamp
    def ActivateInjectedCurrent(self):
            if self.ui.EmulatorPatchClamp_toggleButton.isChecked():
                    self.ui.Emulator_PatchClamp_slider.setEnabled(True)
                    self.EmulatorInjectedCurrent = self.ui.Emulator_PatchClamp_slider.value()
                    self.ui.Emulator_PatchClamp_reading.setText(str(self.EmulatorInjectedCurrent))
                    self.ui.Emulator_PatchClamp_reading.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")


            else:
                    self.ui.Emulator_PatchClamp_slider.setEnabled(False)
                    self.ui.Emulator_PatchClamp_slider.setValue(0)
                    self.ui.Emulator_PatchClamp_reading.setText("")



    def GetInjectedCurrent(self):
            self.EmulatorInjectedCurrent = self.ui.Emulator_PatchClamp_slider.value()
            self.ui.Emulator_PatchClamp_reading.setText(str(self.EmulatorInjectedCurrent))
            self.ui.Emulator_PatchClamp_reading.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")



    # NoiseLevel
    def ActivateNoiseLevel(self):
            if self.ui.EmulatorNoise_toggleButton.isChecked():
                    self.ui.Emulator_Noise_slider.setEnabled(True)
                    self.Emulator_Noise = self.ui.Emulator_Noise_slider.value()
                    self.ui.Emulator_Noise_readings.setText(str(self.Emulator_Noise))
                    self.ui.Emulator_Noise_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")

            else:
                    self.ui.Emulator_Noise_slider.setEnabled(False)
                    self.Emulator_Noise = 0
                    self.ui.Emulator_Noise_slider.setValue(0)
                    self.ui.Emulator_Noise_readings.setText("")


    def GetNoiseLevel(self):
            self.Emulator_Noise = self.ui.Emulator_Noise_slider.value()
            self.ui.Emulator_Noise_readings.setText(str(self.Emulator_Noise))
            self.ui.Emulator_Noise_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")




    # Synapse1Gain
    def ActivateSynapticGain1(self):
            if self.ui.EmulatorSynapse1_toggleButton.isChecked():
                    self.ui.Emulator_Synapse1_slider.setEnabled(True)
                    self.EmulatorSynapse1Gain = self.ui.Emulator_Synapse1_slider.value()
                    self.ui.Emulator_Synapse1_readings.setText(str(self.EmulatorSynapse1Gain))
                    self.ui.Emulator_Synapse1_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[7])) + "; font: 700 10pt;")


            else:
                    self.ui.Emulator_Synapse1_slider.setEnabled(False)
                    self.ui.Emulator_Synapse1_slider.setValue(0)
                    self.ui.Emulator_Synapse1_readings.setText("")



    def GetSynapticGain1(self):
            self.EmulatorSynapse1Gain = self.ui.Emulator_Synapse1_slider.value()
            self.ui.Emulator_Synapse1_readings.setText(str(self.EmulatorSynapse1Gain))
            self.ui.Emulator_Synapse1_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[7])) + "; font: 700 10pt;")



    # Synapse1Decay
    def ActivateSynapseDecay1(self):
            if self.ui.EmulatorSynapse1Decay_toggleButton.isChecked():
                    self.ui.Emulator_Synapse1_Decay_slider.setEnabled(True)
                    self.EmulatorSynapse1Decay = self.ui.Emulator_Synapse1_Decay_slider.value()
                    self.ui.Emulator_Synapse1_Decay_readings.setText(str(self.EmulatorSynapse1Decay/1000))
                    self.ui.Emulator_Synapse1_Decay_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[7])) + "; font: 700 10pt;")


            else:
                    self.ui.Emulator_Synapse1_Decay_slider.setEnabled(False)
                    self.ui.Emulator_Synapse1_Decay_slider.setValue(995)
                    self.ui.Emulator_Synapse1_Decay_readings.setText("")



    def GetSynapticDecay1(self):
            self.EmulatorSynapse1Decay = self.ui.Emulator_Synapse1_Decay_slider.value()
            self.ui.Emulator_Synapse1_Decay_readings.setText(str(self.EmulatorSynapse1Decay/1000))
            self.ui.Emulator_Synapse1_Decay_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[7])) + "; font: 700 10pt;")



    # Synapse2Gain
    def ActivateSynapticGain2(self):
            if self.ui.EmulatorSynapse2_toggleButton.isChecked():
                    self.ui.Emulator_Synapse2_slider.setEnabled(True)
                    self.EmulatorSynapse2Gain = self.ui.Emulator_Synapse2_slider.value()
                    self.ui.Emulator_Synapse2_readings.setText(str(self.EmulatorSynapse2Gain))
                    self.ui.Emulator_Synapse2_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[10])) + "; font: 700 10pt;")


            else:
                    self.ui.Emulator_Synapse2_slider.setEnabled(False)
                    self.ui.Emulator_Synapse2_slider.setValue(0)
                    self.ui.Emulator_Synapse2_readings.setText("")


    def GetSynapticGain2(self):
            self.EmulatorSynapse2Gain = self.ui.Emulator_Synapse2_slider.value()
            self.ui.Emulator_Synapse2_readings.setText(str(self.EmulatorSynapse2Gain))
            self.ui.Emulator_Synapse2_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[10])) + "; font: 700 10pt;")


    # Synapse1Decay
    def ActivateSynapseDecay2(self):
            if self.ui.EmulatorSynapse2Decay_toggleButton.isChecked():
                    self.ui.Emulator_Synapse2_Decay_slider.setEnabled(True)
                    self.EmulatorSynapse2Decay = self.ui.Emulator_Synapse2_Decay_slider.value()
                    self.ui.Emulator_Synapse2_Decay_readings.setText(str(self.EmulatorSynapse2Decay/1000))
                    self.ui.Emulator_Synapse2_Decay_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[10])) + "; font: 700 10pt;")


            else:
                    self.ui.Emulator_Synapse2_Decay_slider.setEnabled(False)
                    self.ui.Emulator_Synapse2_Decay_slider.setValue(990)
                    self.ui.Emulator_Synapse2_Decay_readings.setText("")



    def GetSynapticDecay2(self):
            self.EmulatorSynapse2Decay = self.ui.Emulator_Synapse2_Decay_slider.value()
            self.ui.Emulator_Synapse2_Decay_readings.setText(str(self.EmulatorSynapse2Decay/1000))
            self.ui.Emulator_Synapse2_Decay_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[10])) + "; font: 700 10pt;")



    def SelectNeuronMode(self):
        self.Emulatorneuron_mode_index = self.ui.Emulator_NeuronModeComboBox.currentIndex()

        if self.Emulatorneuron_mode_index == 1:
            self.ui.Emulator_a = IzhikevichNeurons[0][0]
            self.ui.Emulator_b = IzhikevichNeurons[0][1]
            self.ui.Emulator_c = IzhikevichNeurons[0][2]
            self.ui.Emulator_d = IzhikevichNeurons[0][3]

        if self.Emulatorneuron_mode_index == 2:
            self.ui.Emulator_a = IzhikevichNeurons[1][0]
            self.ui.Emulator_b = IzhikevichNeurons[1][1]
            self.ui.Emulator_c = IzhikevichNeurons[1][2]
            self.ui.Emulator_d = IzhikevichNeurons[1][3]

        if self.Emulatorneuron_mode_index == 3:
            self.ui.Emulator_a = IzhikevichNeurons[2][0]
            self.ui.Emulator_b = IzhikevichNeurons[2][1]
            self.ui.Emulator_c = IzhikevichNeurons[2][2]
            self.ui.Emulator_d = IzhikevichNeurons[2][3]

        if self.Emulatorneuron_mode_index == 4:
            self.ui.Emulator_a = IzhikevichNeurons[3][0]
            self.ui.Emulator_b = IzhikevichNeurons[3][1]
            self.ui.Emulator_c = IzhikevichNeurons[3][2]
            self.ui.Emulator_d = IzhikevichNeurons[3][3]

        if self.Emulatorneuron_mode_index == 5:
            self.ui.Emulator_a = IzhikevichNeurons[4][0]
            self.ui.Emulator_b = IzhikevichNeurons[4][1]
            self.ui.Emulator_c = IzhikevichNeurons[4][2]
            self.ui.Emulator_d = IzhikevichNeurons[4][3]

        if self.Emulatorneuron_mode_index == 6:
            self.ui.Emulator_a = IzhikevichNeurons[5][0]
            self.ui.Emulator_b = IzhikevichNeurons[5][1]
            self.ui.Emulator_c = IzhikevichNeurons[5][2]
            self.ui.Emulator_d = IzhikevichNeurons[5][3]

        if self.Emulatorneuron_mode_index == 7:
            self.ui.Emulator_a = IzhikevichNeurons[6][0]
            self.ui.Emulator_b = IzhikevichNeurons[6][1]
            self.ui.Emulator_c = IzhikevichNeurons[6][2]
            self.ui.Emulator_d = IzhikevichNeurons[6][3]

        if self.Emulatorneuron_mode_index == 8:
            self.ui.Emulator_a = IzhikevichNeurons[7][0]
            self.ui.Emulator_b = IzhikevichNeurons[7][1]
            self.ui.Emulator_c = IzhikevichNeurons[7][2]
            self.ui.Emulator_d = IzhikevichNeurons[7][3]

        if self.Emulatorneuron_mode_index == 9:
            self.ui.Emulator_a = IzhikevichNeurons[8][0]
            self.ui.Emulator_b = IzhikevichNeurons[8][1]
            self.ui.Emulator_c = IzhikevichNeurons[8][2]
            self.ui.Emulator_d = IzhikevichNeurons[8][3]

        if self.Emulatorneuron_mode_index == 10:
            self.ui.Emulator_a = IzhikevichNeurons[9][0]
            self.ui.Emulator_b = IzhikevichNeurons[9][1]
            self.ui.Emulator_c = IzhikevichNeurons[9][2]
            self.ui.Emulator_d = IzhikevichNeurons[9][3]

        if self.Emulatorneuron_mode_index == 11:
            self.ui.Emulator_a = IzhikevichNeurons[10][0]
            self.ui.Emulator_b = IzhikevichNeurons[10][1]
            self.ui.Emulator_c = IzhikevichNeurons[10][2]
            self.ui.Emulator_d = IzhikevichNeurons[10][3]

        if self.Emulatorneuron_mode_index == 12:
            self.ui.Emulator_a = IzhikevichNeurons[11][0]
            self.ui.Emulator_b = IzhikevichNeurons[11][1]
            self.ui.Emulator_c = IzhikevichNeurons[11][2]
            self.ui.Emulator_d = IzhikevichNeurons[11][3]

        if self.Emulatorneuron_mode_index <= 12:
            self.ui.Emulator_PR_PhotoGain_slider.setEnabled(True)
            self.ui.Emulator_PR_PhotoGain_slider.setValue(0)
            self.ui.Emulator_PR_PhotoGain_slider.setEnabled(False)

            self.ui.Emulator_PR_Decay_slider.setEnabled(True)
            self.ui.Emulator_PR_Decay_slider.setValue(0.001)
            self.ui.Emulator_PR_Decay_slider.setEnabled(False)

            self.ui.Emulator_PR_Recovery_slider.setEnabled(True)
            self.ui.Emulator_PR_Recovery_slider.setValue(0.025)
            self.ui.Emulator_PR_Recovery_slider.setEnabled(False)

            self.ui.Emulator_Synapse1_slider.setEnabled(True)
            self.ui.Emulator_Synapse1_slider.setValue(0)
            self.ui.Emulator_Synapse1_slider.setEnabled(False)

            self.ui.Emulator_Synapse1_Decay_slider.setEnabled(True)
            self.ui.Emulator_Synapse1_Decay_slider.setValue(0.995)
            self.ui.Emulator_Synapse1_Decay_slider.setEnabled(False)

            self.ui.Emulator_Synapse2_slider.setEnabled(True)
            self.ui.Emulator_Synapse2_slider.setValue(0)
            self.ui.Emulator_Synapse2_slider.setEnabled(False)

            self.ui.Emulator_Synapse2_Decay_slider.setEnabled(True)
            self.ui.Emulator_Synapse2_Decay_slider.setValue(0.995)
            self.ui.Emulator_Synapse2_Decay_slider.setEnabled(False)


        if self.Emulatorneuron_mode_index > 12:
            if self.Emulatorneuron_mode_index > 12:
                self.ui.Emulator_a = self.ui.EmulatorImportNeuron[self.Emulatorneuron_mode_index - 13][0]
                self.ui.Emulator_b = self.ui.EmulatorImportNeuron[self.Emulatorneuron_mode_index - 13][1]
                self.ui.Emulator_c = self.ui.EmulatorImportNeuron[self.Emulatorneuron_mode_index - 13][2]
                self.ui.Emulator_d = self.ui.EmulatorImportNeuron[self.Emulatorneuron_mode_index - 13][3]


            self.Emulator_Photodiode_Gain = self.ui.EmulatorImportNeuron[self.Emulatorneuron_mode_index - 13][4]
            self.ui.Emulator_PR_PhotoGain_slider.setEnabled(True)
            self.ui.Emulator_PR_PhotoGain_slider.setValue(self.Emulator_Photodiode_Gain)
            self.ui.Emulator_PR_PhotoGain_slider.setEnabled(False)

            self.Photodiode_Decay_value = self.ui.EmulatorImportNeuron[self.Emulatorneuron_mode_index - 13][5]
            self.ui.Emulator_PR_Decay_slider.setEnabled(True)
            self.ui.Emulator_PR_Decay_slider.setValue(self.Photodiode_Decay_value)
            self.ui.Emulator_PR_Decay_slider.setEnabled(False)

            self.Photodiode_Recovery_value = self.ui.EmulatorImportNeuron[self.Emulatorneuron_mode_index - 13][6]
            self.ui.Emulator_PR_Recovery_slider.setEnabled(True)
            self.ui.Emulator_PR_Recovery_slider.setValue(self.Photodiode_Recovery_value)
            self.ui.Emulator_PR_Recovery_slider.setEnabled(False)


            self.Emulator_Syn1_Gain = self.ui.EmulatorImportNeuron[self.Emulatorneuron_mode_index - 13][7]
            self.ui.Emulator_Synapse1_slider.setEnabled(True)
            self.ui.Emulator_Synapse1_slider.setValue(self.Emulator_Syn1_Gain)
            self.ui.Emulator_Synapse1_slider.setEnabled(False)

            self.Emulator_Syn1Decay = self.ui.EmulatorImportNeuron[self.Emulatorneuron_mode_index - 13][8]
            self.ui.Emulator_Synapse1_Decay_slider.setEnabled(True)
            self.ui.Emulator_Synapse1_Decay_slider.setValue(self.Emulator_Syn1Decay)
            self.ui.Emulator_Synapse1_Decay_slider.setEnabled(False)


            self.Emulator_Syn2_Gain = self.ui.EmulatorImportNeuron[self.Emulatorneuron_mode_index - 13][9]
            self.ui.Emulator_Synapse2_slider.setEnabled(True)
            self.ui.Emulator_Synapse2_slider.setValue(self.Emulator_Syn2_Gain)
            self.ui.Emulator_Synapse2_slider.setEnabled(False)

            self.Emulator_Syn2Decay = self.ui.EmulatorImportNeuron[self.Emulatorneuron_mode_index - 13][10]
            self.ui.Emulator_Synapse2_Decay_slider.setEnabled(True)
            self.ui.Emulator_Synapse2_Decay_slider.setValue(self.Emulator_Syn2Decay)
            self.ui.Emulator_Synapse2_Decay_slider.setEnabled(False)





    def BrowseNeuron(self):
        FileName, _= QFileDialog.getOpenFileName(caption='Select Neuron',
                                                 dir="./Neurons",
                                                 filter='csv files (*.csv)')

        Df = pd.read_csv(FileName)
        self.Emulatordf_Neuron_a = Df["a"]
        self.Emulatordf_Neuron_b = Df["b"]
        self.Emulatordf_Neuron_c = Df["c"]
        self.Emulatordf_Neuron_d = Df["d"]

        self.Emulatordf_Neuron_PGain = Df["PhotoGain (%)"]
        self.Emulatordf_Neuron_PDecay = Df["PhotoDecay (1/ms)"]
        self.Emulatordf_Neuron_PRecovery = Df["PhotoRecovery (1/ms)"]

        self.Emulatordf_Neuron_Syn1Gain = Df["Syn1 Gain (%)"]
        self.Emulatordf_Neuron_Syn1Decay = Df["Syn1 Decay (1/ms)"]

        self.Emulatordf_Neuron_Syn2Gain = Df["Syn2 Gain (%)"]
        self.Emulatordf_Neuron_Syn2Decay = Df["Syn2 Decay (1/ms)"]

        self.EmulatorParametersNeuron = [self.Emulatordf_Neuron_a[0],
                                         self.Emulatordf_Neuron_b[0],
                                         self.Emulatordf_Neuron_c[0],
                                         self.Emulatordf_Neuron_d[0],
                                         self.Emulatordf_Neuron_PGain[0],
                                         self.Emulatordf_Neuron_PDecay[0],
                                         self.Emulatordf_Neuron_PRecovery[0],
                                         self.Emulatordf_Neuron_Syn1Gain[0],
                                         self.Emulatordf_Neuron_Syn1Decay[0],
                                         self.Emulatordf_Neuron_Syn2Gain[0],
                                         self.Emulatordf_Neuron_Syn2Decay[0]
                                         ]
        self.ui.EmulatorImportNeuron.append(self.EmulatorParametersNeuron)


        self.ui.Emulator_NeuronModeComboBox.addItem('')
        self.Emulatorneuron_count = self.ui.Emulator_NeuronModeComboBox.count()
        self.Emulatorfilename = os.path.splitext(os.path.basename(QFileInfo(FileName).fileName()))[0]
        self.ui.Emulator_NeuronModeComboBox.setItemText(self.Emulatorneuron_count-1, self.Emulatorfilename)
        self.ui.Emulator_NeuronModeComboBox.setCurrentIndex(self.Emulatorneuron_count-1)




class EmulatorSyn1 ():

    def ActivateSynapse(self):
            if self.ui.EmulatorSyn1_Synapse_toggleButton.isChecked():
                self.ui.EmulatorSyn1_PatchClamp_toggleButton.setEnabled(True)
                self.ui.EmulatorSyn1_Noise_toggleButton.setEnabled(True)
                self.ui.EmulatorSyn1_StimDC_toggleButton.setEnabled(True)
                self.ui.EmulatorSyn1_StimLight_toggleButton.setEnabled(True)
                self.ui.Emulator_Syn1_Noise_frame.setStyleSheet("background-color: rgb" + str(tuple(Settings.DarkSolarized[1])))
                self.ui.Emulator_Syn1_PatchClamp_frame.setStyleSheet("background-color: rgb" + str(tuple(Settings.DarkSolarized[1])))
                self.ui.Emulator_Syn1_Stimulus_frame.setStyleSheet("background-color: rgb" + str(tuple(Settings.DarkSolarized[1])))
                self.ui.Emulator_Syn1_bottom_line.setStyleSheet("background-color: rgb" + str(tuple(Settings.DarkSolarized[0])))
                self.ui.Emulator_Syn1_middle_line.setStyleSheet("background-color: rgb" + str(tuple(Settings.DarkSolarized[0])))

            else:
                self.ui.EmulatorSyn1_PatchClamp_toggleButton.setEnabled(False)
                self.ui.EmulatorSyn1_Noise_toggleButton.setEnabled(False)
                self.ui.EmulatorSyn1_StimDC_toggleButton.setEnabled(False)
                self.ui.EmulatorSyn1_StimLight_toggleButton.setEnabled(False)
                self.ui.EmulatorSyn1_PatchClamp_toggleButton.setChecked(False)
                self.ui.EmulatorSyn1_Noise_toggleButton.setChecked(False)
                self.ui.EmulatorSyn1_StimDC_toggleButton.setChecked(False)
                self.ui.EmulatorSyn1_StimLight_toggleButton.setChecked(False)
                self.ui.Emulator_Syn1_Noise_frame.setStyleSheet("background-color: rgb" + str(tuple(Settings.DarkSolarized[18])))
                self.ui.Emulator_Syn1_PatchClamp_frame.setStyleSheet("background-color: rgb" + str(tuple(Settings.DarkSolarized[18])))
                self.ui.Emulator_Syn1_Stimulus_frame.setStyleSheet("background-color: rgb" + str(tuple(Settings.DarkSolarized[18])))
                self.ui.Emulator_Syn1_bottom_line.setStyleSheet("background-color: rgb" + str(tuple(Settings.DarkSolarized[18])))
                self.ui.Emulator_Syn1_middle_line.setStyleSheet("background-color: rgb" + str(tuple(Settings.DarkSolarized[18])))

    def ActivatePhotoParameters(self):
        if self.ui.EmulatorSyn1_StimLight_toggleButton.isChecked():
            self.ui.EmulatorSyn1_PhotoGain_toggleButton.setEnabled(True)
            self.ui.EmulatorSyn1_PhotoDecay_toggleButton.setEnabled(True)
            self.ui.EmulatorSyn1_PhotoRecovery_toggleButton.setEnabled(True)
            self.ui.Emulator_Syn1_PhotoDiode_frame.setStyleSheet("background-color: rgb" + str(tuple(Settings.DarkSolarized[1])))

        else:
            self.ui.EmulatorSyn1_PhotoGain_toggleButton.setEnabled(False)
            self.ui.EmulatorSyn1_PhotoDecay_toggleButton.setEnabled(False)
            self.ui.EmulatorSyn1_PhotoRecovery_toggleButton.setEnabled(False)
            self.ui.EmulatorSyn1_PhotoGain_toggleButton.setChecked(False)
            self.ui.EmulatorSyn1_PhotoDecay_toggleButton.setChecked(False)
            self.ui.EmulatorSyn1_PhotoRecovery_toggleButton.setChecked(False)
            self.ui.Emulator_Syn1_PhotoDiode_frame.setStyleSheet("background-color: rgb" + str(tuple(Settings.DarkSolarized[18])))


    # PhotoGain
    def ActivatePhotoGain(self):
            if self.ui.EmulatorSyn1_PhotoGain_toggleButton.isChecked():
                    self.ui.Emulator_Syn1_PR_PhotoGain_slider.setEnabled(True)
                    self.EmulatorSyn1PhotoGain = self.ui.Emulator_Syn1_PR_PhotoGain_slider.value()
                    self.ui.Emulator_Syn1_PR_Photogain_readings.setText(str(self.EmulatorSyn1PhotoGain))
                    self.ui.Emulator_Syn1_PR_Photogain_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")
            else:
                    self.ui.Emulator_Syn1_PR_PhotoGain_slider.setEnabled(False)
                    self.ui.Emulator_Syn1_PR_PhotoGain_slider.setValue(0)
                    self.ui.Emulator_Syn1_PR_Photogain_readings.setText("")


    def GetPhotoGain(self):
            self.EmulatorSyn1PhotoGain = self.ui.Emulator_Syn1_PR_PhotoGain_slider.value()
            self.ui.Emulator_Syn1_PR_Photogain_readings.setText(str(self.EmulatorSyn1PhotoGain))
            self.ui.Emulator_Syn1_PR_Photogain_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")



    # PhotoDecay
    def ActivatePRDecay(self):
            if self.ui.EmulatorSyn1_PhotoDecay_toggleButton.isChecked():
                    self.ui.Emulator_Syn1_PR_Decay_slider.setEnabled(True)
                    self.EmulatorSyn1PhotoDecay = self.ui.Emulator_Syn1_PR_Decay_slider.value()
                    self.ui.Emulator_Syn1_PR_Decay_readings.setText(str(self.EmulatorSyn1PhotoDecay/100000))
                    self.ui.Emulator_Syn1_PR_Decay_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")


            else:
                    self.ui.Emulator_Syn1_PR_Decay_slider.setEnabled(False)
                    self.ui.Emulator_Syn1_PR_Decay_slider.setValue(100)
                    self.ui.Emulator_Syn1_PR_Decay_readings.setText("")



    def GetPRDecay(self):
            self.EmulatorSyn1PhotoDecay = self.ui.Emulator_Syn1_PR_Decay_slider.value()
            self.ui.Emulator_Syn1_PR_Decay_readings.setText(str(self.EmulatorSyn1PhotoDecay/100000))
            self.ui.Emulator_Syn1_PR_Decay_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")


    # PhotoRecovery
    def ActivatePRRecovery(self):
            if self.ui.EmulatorSyn1_PhotoRecovery_toggleButton.isChecked():
                    self.ui.Emulator_Syn1_PR_Recovery_slider.setEnabled(True)
                    self.EmulatorSyn1PhotoRecovery = self.ui.Emulator_Syn1_PR_Recovery_slider.value()
                    self.ui.Emulator_Syn1_PR_Recovery_readings.setText(str(self.EmulatorSyn1PhotoRecovery/1000))
                    self.ui.Emulator_Syn1_PR_Recovery_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")

            else:
                    self.ui.Emulator_Syn1_PR_Recovery_slider.setEnabled(False)
                    self.ui.Emulator_Syn1_PR_Recovery_slider.setValue(25)
                    self.ui.Emulator_Syn1_PR_Recovery_readings.setText("")



    def GetPRRecovery(self):
            self.EmulatorSyn1PhotoRecovery = self.ui.Emulator_Syn1_PR_Recovery_slider.value()
            self.ui.Emulator_Syn1_PR_Recovery_readings.setText(str(self.EmulatorSyn1PhotoRecovery/1000))
            self.ui.Emulator_Syn1_PR_Recovery_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")



    # PatchClamp
    def ActivateInjectedCurrent(self):
            if self.ui.EmulatorSyn1_PatchClamp_toggleButton.isChecked():
                    self.ui.Emulator_Syn1_PatchClamp_slider.setEnabled(True)
                    self.EmulatorSyn1InjectedCurrent = self.ui.Emulator_Syn1_PatchClamp_slider.value()
                    self.ui.Emulator_Syn1_PatchClamp_readings.setText(str(self.EmulatorSyn1InjectedCurrent))
                    self.ui.Emulator_Syn1_PatchClamp_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")


            else:
                    self.ui.Emulator_Syn1_PatchClamp_slider.setEnabled(False)
                    self.ui.Emulator_Syn1_PatchClamp_slider.setValue(0)
                    self.ui.Emulator_Syn1_PatchClamp_readings.setText("")



    def GetInjectedCurrent(self):
            self.EmulatorSyn1InjectedCurrent = self.ui.Emulator_Syn1_PatchClamp_slider.value()
            self.ui.Emulator_Syn1_PatchClamp_readings.setText(str(self.EmulatorSyn1InjectedCurrent))
            self.ui.Emulator_Syn1_PatchClamp_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")



    # NoiseLevel
    def ActivateNoiseLevel(self):
            if self.ui.EmulatorSyn1_Noise_toggleButton.isChecked():
                    self.ui.Emulator_Syn1_Noise_slider.setEnabled(True)
                    self.EmulatorSyn1_Noise = self.ui.Emulator_Syn1_Noise_slider.value()
                    self.ui.Emulator_Syn1_Noise_readings.setText(str(self.EmulatorSyn1_Noise))
                    self.ui.Emulator_Syn1_Noise_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")

            else:
                    self.ui.Emulator_Syn1_Noise_slider.setEnabled(False)
                    self.EmulatorSyn1_Noise = 0
                    self.ui.Emulator_Syn1_Noise_slider.setValue(0)
                    self.ui.Emulator_Syn1_Noise_readings.setText("")


    def GetNoiseLevel(self):
            self.EmulatorSyn1_Noise = self.ui.Emulator_Syn1_Noise_slider.value()
            self.ui.Emulator_Syn1_Noise_readings.setText(str(self.EmulatorSyn1_Noise))
            self.ui.Emulator_Syn1_Noise_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")



    def SelectNeuronMode(self):
        self.EmulatorSyn1_neuron_mode_index = self.ui.Emulator_Syn1_Mode_comboBox.currentIndex()

        if self.EmulatorSyn1_neuron_mode_index == 1:
            self.ui.Emulator_a1 = IzhikevichNeurons[0][0]
            self.ui.Emulator_b1 = IzhikevichNeurons[0][1]
            self.ui.Emulator_c1 = IzhikevichNeurons[0][2]
            self.ui.Emulator_d1 = IzhikevichNeurons[0][3]

        if self.EmulatorSyn1_neuron_mode_index == 2:
            self.ui.Emulator_a1 = IzhikevichNeurons[1][0]
            self.ui.Emulator_b1 = IzhikevichNeurons[1][1]
            self.ui.Emulator_c1 = IzhikevichNeurons[1][2]
            self.ui.Emulator_d1 = IzhikevichNeurons[1][3]

        if self.EmulatorSyn1_neuron_mode_index == 3:
            self.ui.Emulator_a1 = IzhikevichNeurons[2][0]
            self.ui.Emulator_b1 = IzhikevichNeurons[2][1]
            self.ui.Emulator_c1 = IzhikevichNeurons[2][2]
            self.ui.Emulator_d1 = IzhikevichNeurons[2][3]

        if self.EmulatorSyn1_neuron_mode_index == 4:
            self.ui.Emulator_a1 = IzhikevichNeurons[3][0]
            self.ui.Emulator_b1 = IzhikevichNeurons[3][1]
            self.ui.Emulator_c1 = IzhikevichNeurons[3][2]
            self.ui.Emulator_d1 = IzhikevichNeurons[3][3]

        if self.EmulatorSyn1_neuron_mode_index == 5:
            self.ui.Emulator_a1 = IzhikevichNeurons[4][0]
            self.ui.Emulator_b1 = IzhikevichNeurons[4][1]
            self.ui.Emulator_c1 = IzhikevichNeurons[4][2]
            self.ui.Emulator_d1 = IzhikevichNeurons[4][3]

        if self.EmulatorSyn1_neuron_mode_index == 6:
            self.ui.Emulator_a1 = IzhikevichNeurons[5][0]
            self.ui.Emulator_b1 = IzhikevichNeurons[5][1]
            self.ui.Emulator_c1 = IzhikevichNeurons[5][2]
            self.ui.Emulator_d1 = IzhikevichNeurons[5][3]

        if self.EmulatorSyn1_neuron_mode_index == 7:
            self.ui.Emulator_a1 = IzhikevichNeurons[6][0]
            self.ui.Emulator_b1 = IzhikevichNeurons[6][1]
            self.ui.Emulator_c1 = IzhikevichNeurons[6][2]
            self.ui.Emulator_d1 = IzhikevichNeurons[6][3]

        if self.EmulatorSyn1_neuron_mode_index == 8:
            self.ui.Emulator_a1 = IzhikevichNeurons[7][0]
            self.ui.Emulator_b1 = IzhikevichNeurons[7][1]
            self.ui.Emulator_c1 = IzhikevichNeurons[7][2]
            self.ui.Emulator_d1 = IzhikevichNeurons[7][3]

        if self.EmulatorSyn1_neuron_mode_index == 9:
            self.ui.Emulator_a1 = IzhikevichNeurons[8][0]
            self.ui.Emulator_b1 = IzhikevichNeurons[8][1]
            self.ui.Emulator_c1 = IzhikevichNeurons[8][2]
            self.ui.Emulator_d1 = IzhikevichNeurons[8][3]

        if self.EmulatorSyn1_neuron_mode_index == 10:
            self.ui.Emulator_a1 = IzhikevichNeurons[9][0]
            self.ui.Emulator_b1 = IzhikevichNeurons[9][1]
            self.ui.Emulator_c1 = IzhikevichNeurons[9][2]
            self.ui.Emulator_d1 = IzhikevichNeurons[9][3]

        if self.EmulatorSyn1_neuron_mode_index == 11:
            self.ui.Emulator_a1 = IzhikevichNeurons[10][0]
            self.ui.Emulator_b1 = IzhikevichNeurons[10][1]
            self.ui.Emulator_c1 = IzhikevichNeurons[10][2]
            self.ui.Emulator_d1 = IzhikevichNeurons[10][3]

        if self.EmulatorSyn1_neuron_mode_index == 12:
            self.ui.Emulator_a1 = IzhikevichNeurons[11][0]
            self.ui.Emulator_b1 = IzhikevichNeurons[11][1]
            self.ui.Emulator_c1 = IzhikevichNeurons[11][2]
            self.ui.Emulator_d1 = IzhikevichNeurons[11][3]

        if self.EmulatorSyn1_neuron_mode_index <= 12:
            self.ui.Emulator_Syn1_PR_PhotoGain_slider.setEnabled(True)
            self.ui.Emulator_Syn1_PR_PhotoGain_slider.setValue(0)
            self.ui.Emulator_Syn1_PR_PhotoGain_slider.setEnabled(False)

            self.ui.Emulator_Syn1_PR_Decay_slider.setEnabled(True)
            self.ui.Emulator_Syn1_PR_Decay_slider.setValue(0.001)
            self.ui.Emulator_Syn1_PR_Decay_slider.setEnabled(False)

            self.ui.Emulator_Syn1_PR_Recovery_slider.setEnabled(True)
            self.ui.Emulator_Syn1_PR_Recovery_slider.setValue(0.025)
            self.ui.Emulator_Syn1_PR_Recovery_slider.setEnabled(False)



        if self.EmulatorSyn1_neuron_mode_index > 12:
            if self.EmulatorSyn1_neuron_mode_index > 12:
                self.ui.Emulator_a1 = self.ui.EmulatorSyn1_ImportNeuron[self.EmulatorSyn1_neuron_mode_index - 13][0]
                self.ui.Emulator_b1 = self.ui.EmulatorSyn1_ImportNeuron[self.EmulatorSyn1_neuron_mode_index - 13][1]
                self.ui.Emulator_c1 = self.ui.EmulatorSyn1_ImportNeuron[self.EmulatorSyn1_neuron_mode_index - 13][2]
                self.ui.Emulator_d1 = self.ui.EmulatorSyn1_ImportNeuron[self.EmulatorSyn1_neuron_mode_index - 13][3]


            self.EmulatorSyn1_Photodiode_Gain = self.ui.EmulatorSyn1_ImportNeuron[self.EmulatorSyn1_neuron_mode_index - 13][4]
            self.ui.Emulator_Syn1_PR_PhotoGain_slider.setEnabled(True)
            self.ui.Emulator_Syn1_PR_PhotoGain_slider.setValue(self.EmulatorSyn1_Photodiode_Gain)
            print(self.EmulatorSyn1_Photodiode_Gain)
            self.ui.Emulator_Syn1_PR_PhotoGain_slider.setEnabled(False)

            self.Syn1_Photodiode_Decay_value = self.ui.EmulatorSyn1_ImportNeuron[self.EmulatorSyn1_neuron_mode_index - 13][5]
            self.ui.Emulator_Syn1_PR_Decay_slider.setEnabled(True)
            self.ui.Emulator_Syn1_PR_Decay_slider.setValue(self.Syn1_Photodiode_Decay_value)
            print(self.Syn1_Photodiode_Decay_value)
            self.ui.Emulator_Syn1_PR_Decay_slider.setEnabled(False)

            self.Syn1_Photodiode_Recovery_value = self.ui.EmulatorSyn1_ImportNeuron[self.EmulatorSyn1_neuron_mode_index - 13][6]
            self.ui.Emulator_Syn1_PR_Recovery_slider.setEnabled(True)
            self.ui.Emulator_Syn1_PR_Recovery_slider.setValue(self.Syn1_Photodiode_Recovery_value)
            self.ui.Emulator_Syn1_PR_Recovery_slider.setEnabled(False)






    def BrowseNeuron(self):
        FileName, _= QFileDialog.getOpenFileName(caption='Select Neuron',
                                                 dir="./Neurons",
                                                 filter='csv files (*.csv)')

        Df = pd.read_csv(FileName)
        self.Emulatordf_Neuron_a = Df["a"]
        self.Emulatordf_Neuron_b = Df["b"]
        self.Emulatordf_Neuron_c = Df["c"]
        self.Emulatordf_Neuron_d = Df["d"]

        self.Emulatordf_Neuron_PGain = Df["PhotoGain (%)"]
        self.Emulatordf_Neuron_PDecay = Df["PhotoDecay (1/ms)"]
        self.Emulatordf_Neuron_PRecovery = Df["PhotoRecovery (1/ms)"]

        self.Emulatordf_Neuron_Syn1Gain = Df["Syn1 Gain (%)"]
        self.Emulatordf_Neuron_Syn1Decay = Df["Syn1 Decay (1/ms)"]

        self.Emulatordf_Neuron_Syn2Gain = Df["Syn2 Gain (%)"]
        self.Emulatordf_Neuron_Syn2Decay = Df["Syn2 Decay (1/ms)"]

        self.EmulatorParametersNeuron = [self.Emulatordf_Neuron_a[0],
                                         self.Emulatordf_Neuron_b[0],
                                         self.Emulatordf_Neuron_c[0],
                                         self.Emulatordf_Neuron_d[0],
                                         self.Emulatordf_Neuron_PGain[0],
                                         self.Emulatordf_Neuron_PDecay[0],
                                         self.Emulatordf_Neuron_PRecovery[0],
                                         self.Emulatordf_Neuron_Syn1Gain[0],
                                         self.Emulatordf_Neuron_Syn1Decay[0],
                                         self.Emulatordf_Neuron_Syn2Gain[0],
                                         self.Emulatordf_Neuron_Syn2Decay[0]
                                         ]
        self.ui.EmulatorSyn1_ImportNeuron.append(self.EmulatorParametersNeuron)


        self.ui.Emulator_Syn1_Mode_comboBox.addItem('')
        self.Emulatorneuron_count = self.ui.Emulator_Syn1_Mode_comboBox.count()
        self.Emulatorfilename = os.path.splitext(os.path.basename(QFileInfo(FileName).fileName()))[0]
        self.ui.Emulator_Syn1_Mode_comboBox.setItemText(self.Emulatorneuron_count-1, self.Emulatorfilename)
        self.ui.Emulator_Syn1_Mode_comboBox.setCurrentIndex(self.Emulatorneuron_count-1)




class EmulatorSyn2 ():

    def ActivateSynapse(self):
            if self.ui.EmulatorSyn2_Synapse_toggleButton.isChecked():
                self.ui.EmulatorSyn2_PatchClamp_toggleButton.setEnabled(True)
                self.ui.EmulatorSyn2_Noise_toggleButton.setEnabled(True)
                self.ui.EmulatorSyn2_StimDC_toggleButton.setEnabled(True)
                self.ui.EmulatorSyn2_StimLight_toggleButton.setEnabled(True)
                self.ui.Emulator_Syn2_Noise_frame.setStyleSheet("background-color: rgb" + str(tuple(Settings.DarkSolarized[1])))
                self.ui.Emulator_Syn2_PatchClamp_frame.setStyleSheet("background-color: rgb" + str(tuple(Settings.DarkSolarized[1])))
                self.ui.Emulator_Syn2_Stimulus_frame.setStyleSheet("background-color: rgb" + str(tuple(Settings.DarkSolarized[1])))
                self.ui.Emulator_Syn2_bottom_line.setStyleSheet("background-color: rgb" + str(tuple(Settings.DarkSolarized[0])))
                self.ui.Emulator_Syn2_middle_line.setStyleSheet("background-color: rgb" + str(tuple(Settings.DarkSolarized[0])))

            else:
                self.ui.EmulatorSyn2_PatchClamp_toggleButton.setEnabled(False)
                self.ui.EmulatorSyn2_Noise_toggleButton.setEnabled(False)
                self.ui.EmulatorSyn2_StimDC_toggleButton.setEnabled(False)
                self.ui.EmulatorSyn2_StimLight_toggleButton.setEnabled(False)
                self.ui.EmulatorSyn2_PatchClamp_toggleButton.setChecked(False)
                self.ui.EmulatorSyn2_Noise_toggleButton.setChecked(False)
                self.ui.EmulatorSyn2_StimDC_toggleButton.setChecked(False)
                self.ui.EmulatorSyn2_StimLight_toggleButton.setChecked(False)
                self.ui.Emulator_Syn2_Noise_frame.setStyleSheet("background-color: rgb" + str(tuple(Settings.DarkSolarized[18])))
                self.ui.Emulator_Syn2_PatchClamp_frame.setStyleSheet("background-color: rgb" + str(tuple(Settings.DarkSolarized[18])))
                self.ui.Emulator_Syn2_Stimulus_frame.setStyleSheet("background-color: rgb" + str(tuple(Settings.DarkSolarized[18])))
                self.ui.Emulator_Syn2_bottom_line.setStyleSheet("background-color: rgb" + str(tuple(Settings.DarkSolarized[18])))
                self.ui.Emulator_Syn2_middle_line.setStyleSheet("background-color: rgb" + str(tuple(Settings.DarkSolarized[18])))

    def ActivatePhotoParameters(self):
        if self.ui.EmulatorSyn2_StimLight_toggleButton.isChecked():
            self.ui.EmulatorSyn2_PhotoGain_toggleButton.setEnabled(True)
            self.ui.EmulatorSyn2_PhotoDecay_toggleButton.setEnabled(True)
            self.ui.EmulatorSyn2_PhotoRecovery_toggleButton.setEnabled(True)
            self.ui.Emulator_Syn2_PhotoDiode_frame.setStyleSheet("background-color: rgb" + str(tuple(Settings.DarkSolarized[1])))

        else:
            self.ui.EmulatorSyn2_PhotoGain_toggleButton.setEnabled(False)
            self.ui.EmulatorSyn2_PhotoDecay_toggleButton.setEnabled(False)
            self.ui.EmulatorSyn2_PhotoRecovery_toggleButton.setEnabled(False)
            self.ui.EmulatorSyn2_PhotoGain_toggleButton.setChecked(False)
            self.ui.EmulatorSyn2_PhotoDecay_toggleButton.setChecked(False)
            self.ui.EmulatorSyn2_PhotoRecovery_toggleButton.setChecked(False)
            self.ui.Emulator_Syn2_PhotoDiode_frame.setStyleSheet("background-color: rgb" + str(tuple(Settings.DarkSolarized[18])))


    # PhotoGain
    def ActivatePhotoGain(self):
            if self.ui.EmulatorSyn2_PhotoGain_toggleButton.isChecked():
                    self.ui.Emulator_Syn2_PR_PhotoGain_slider.setEnabled(True)
                    self.EmulatorSyn2PhotoGain = self.ui.Emulator_Syn2_PR_PhotoGain_slider.value()
                    self.ui.Emulator_Syn2_PR_Photogain_readings.setText(str(self.EmulatorSyn2PhotoGain))
                    self.ui.Emulator_Syn2_PR_Photogain_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")
            else:
                    self.ui.Emulator_Syn2_PR_PhotoGain_slider.setEnabled(False)
                    self.ui.Emulator_Syn2_PR_PhotoGain_slider.setValue(0)
                    self.ui.Emulator_Syn2_PR_Photogain_readings.setText("")


    def GetPhotoGain(self):
            self.EmulatorSyn2PhotoGain = self.ui.Emulator_Syn2_PR_PhotoGain_slider.value()
            self.ui.Emulator_Syn2_PR_Photogain_readings.setText(str(self.EmulatorSyn2PhotoGain))
            self.ui.Emulator_Syn2_PR_Photogain_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")



    # PhotoDecay
    def ActivatePRDecay(self):
            if self.ui.EmulatorSyn2_PhotoDecay_toggleButton.isChecked():
                    self.ui.Emulator_Syn2_PR_Decay_slider.setEnabled(True)
                    self.EmulatorSyn2PhotoDecay = self.ui.Emulator_Syn2_PR_Decay_slider.value()
                    self.ui.Emulator_Syn2_PR_Decay_readings.setText(str(self.EmulatorSyn2PhotoDecay/100000))
                    self.ui.Emulator_Syn2_PR_Decay_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")


            else:
                    self.ui.Emulator_Syn2_PR_Decay_slider.setEnabled(False)
                    self.ui.Emulator_Syn2_PR_Decay_slider.setValue(100)
                    self.ui.Emulator_Syn2_PR_Decay_readings.setText("")



    def GetPRDecay(self):
            self.EmulatorSyn2PhotoDecay = self.ui.Emulator_Syn2_PR_Decay_slider.value()
            self.ui.Emulator_Syn2_PR_Decay_readings.setText(str(self.EmulatorSyn1PhotoDecay/100000))
            self.ui.Emulator_Syn2_PR_Decay_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")


    # PhotoRecovery
    def ActivatePRRecovery(self):
            if self.ui.EmulatorSyn2_PhotoRecovery_toggleButton.isChecked():
                    self.ui.Emulator_Syn2_PR_Recovery_slider.setEnabled(True)
                    self.EmulatorSyn2PhotoRecovery = self.ui.Emulator_Syn2_PR_Recovery_slider.value()
                    self.ui.Emulator_Syn2_PR_Recovery_readings.setText(str(self.EmulatorSyn2PhotoRecovery/1000))
                    self.ui.Emulator_Syn2_PR_Recovery_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")

            else:
                    self.ui.Emulator_Syn2_PR_Recovery_slider.setEnabled(False)
                    self.ui.Emulator_Syn2_PR_Recovery_slider.setValue(25)
                    self.ui.Emulator_Syn2_PR_Recovery_readings.setText("")



    def GetPRRecovery(self):
            self.EmulatorSyn2PhotoRecovery = self.ui.Emulator_Syn2_PR_Recovery_slider.value()
            self.ui.Emulator_Syn2_PR_Recovery_readings.setText(str(self.EmulatorSyn2PhotoRecovery/1000))
            self.ui.Emulator_Syn2_PR_Recovery_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")



    # PatchClamp
    def ActivateInjectedCurrent(self):
            if self.ui.EmulatorSyn2_PatchClamp_toggleButton.isChecked():
                    self.ui.Emulator_Syn2_PatchClamp_slider.setEnabled(True)
                    self.EmulatorSyn2InjectedCurrent = self.ui.Emulator_Syn2_PatchClamp_slider.value()
                    self.ui.Emulator_Syn2_PatchClamp_readings.setText(str(self.EmulatorSyn2InjectedCurrent))
                    self.ui.Emulator_Syn2_PatchClamp_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")


            else:
                    self.ui.Emulator_Syn2_PatchClamp_slider.setEnabled(False)
                    self.ui.Emulator_Syn2_PatchClamp_slider.setValue(0)
                    self.ui.Emulator_Syn2_PatchClamp_readings.setText("")



    def GetInjectedCurrent(self):
            self.EmulatorSyn2InjectedCurrent = self.ui.Emulator_Syn2_PatchClamp_slider.value()
            self.ui.Emulator_Syn2_PatchClamp_readings.setText(str(self.EmulatorSyn2InjectedCurrent))
            self.ui.Emulator_Syn2_PatchClamp_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")



    # NoiseLevel
    def ActivateNoiseLevel(self):
            if self.ui.EmulatorSyn2_Noise_toggleButton.isChecked():
                    self.ui.Emulator_Syn2_Noise_slider.setEnabled(True)
                    self.EmulatorSyn2_Noise = self.ui.Emulator_Syn2_Noise_slider.value()
                    self.ui.Emulator_Syn2_Noise_readings.setText(str(self.EmulatorSyn2_Noise))
                    self.ui.Emulator_Syn2_Noise_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")

            else:
                    self.ui.Emulator_Syn2_Noise_slider.setEnabled(False)
                    self.EmulatorSyn1_Noise = 0
                    self.ui.Emulator_Syn2_Noise_slider.setValue(0)
                    self.ui.Emulator_Syn2_Noise_readings.setText("")


    def GetNoiseLevel(self):
            self.EmulatorSyn2_Noise = self.ui.Emulator_Syn2_Noise_slider.value()
            self.ui.Emulator_Syn2_Noise_readings.setText(str(self.EmulatorSyn2_Noise))
            self.ui.Emulator_Syn2_Noise_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")



    def SelectNeuronMode(self):
        self.EmulatorSyn2_neuron_mode_index = self.ui.Emulator_Syn2_Mode_comboBox.currentIndex()

        if self.EmulatorSyn2_neuron_mode_index == 1:
            self.ui.Emulator_a2 = IzhikevichNeurons[0][0]
            self.ui.Emulator_b2 = IzhikevichNeurons[0][1]
            self.ui.Emulator_c2 = IzhikevichNeurons[0][2]
            self.ui.Emulator_d2 = IzhikevichNeurons[0][3]

        if self.EmulatorSyn2_neuron_mode_index == 2:
            self.ui.Emulator_a2 = IzhikevichNeurons[1][0]
            self.ui.Emulator_b2 = IzhikevichNeurons[1][1]
            self.ui.Emulator_c2 = IzhikevichNeurons[1][2]
            self.ui.Emulator_d2 = IzhikevichNeurons[1][3]

        if self.EmulatorSyn2_neuron_mode_index == 3:
            self.ui.Emulator_a2 = IzhikevichNeurons[2][0]
            self.ui.Emulator_b2 = IzhikevichNeurons[2][1]
            self.ui.Emulator_c2 = IzhikevichNeurons[2][2]
            self.ui.Emulator_d2 = IzhikevichNeurons[2][3]

        if self.EmulatorSyn2_neuron_mode_index == 4:
            self.ui.Emulator_a2 = IzhikevichNeurons[3][0]
            self.ui.Emulator_b2 = IzhikevichNeurons[3][1]
            self.ui.Emulator_c2 = IzhikevichNeurons[3][2]
            self.ui.Emulator_d2 = IzhikevichNeurons[3][3]

        if self.EmulatorSyn2_neuron_mode_index == 5:
            self.ui.Emulator_a2 = IzhikevichNeurons[4][0]
            self.ui.Emulator_b2 = IzhikevichNeurons[4][1]
            self.ui.Emulator_c2 = IzhikevichNeurons[4][2]
            self.ui.Emulator_d2 = IzhikevichNeurons[4][3]

        if self.EmulatorSyn2_neuron_mode_index == 6:
            self.ui.Emulator_a2 = IzhikevichNeurons[5][0]
            self.ui.Emulator_b2 = IzhikevichNeurons[5][1]
            self.ui.Emulator_c2 = IzhikevichNeurons[5][2]
            self.ui.Emulator_d2 = IzhikevichNeurons[5][3]

        if self.EmulatorSyn2_neuron_mode_index == 7:
            self.ui.Emulator_a2 = IzhikevichNeurons[6][0]
            self.ui.Emulator_b2 = IzhikevichNeurons[6][1]
            self.ui.Emulator_c2 = IzhikevichNeurons[6][2]
            self.ui.Emulator_d2 = IzhikevichNeurons[6][3]

        if self.EmulatorSyn2_neuron_mode_index == 8:
            self.ui.Emulator_a2 = IzhikevichNeurons[7][0]
            self.ui.Emulator_b2 = IzhikevichNeurons[7][1]
            self.ui.Emulator_c2 = IzhikevichNeurons[7][2]
            self.ui.Emulator_d2 = IzhikevichNeurons[7][3]

        if self.EmulatorSyn2_neuron_mode_index == 9:
            self.ui.Emulator_a2 = IzhikevichNeurons[8][0]
            self.ui.Emulator_b2 = IzhikevichNeurons[8][1]
            self.ui.Emulator_c2 = IzhikevichNeurons[8][2]
            self.ui.Emulator_d2 = IzhikevichNeurons[8][3]

        if self.EmulatorSyn2_neuron_mode_index == 10:
            self.ui.Emulator_a2 = IzhikevichNeurons[9][0]
            self.ui.Emulator_b2 = IzhikevichNeurons[9][1]
            self.ui.Emulator_c2 = IzhikevichNeurons[9][2]
            self.ui.Emulator_d2 = IzhikevichNeurons[9][3]

        if self.EmulatorSyn2_neuron_mode_index == 11:
            self.ui.Emulator_a2 = IzhikevichNeurons[10][0]
            self.ui.Emulator_b2 = IzhikevichNeurons[10][1]
            self.ui.Emulator_c2 = IzhikevichNeurons[10][2]
            self.ui.Emulator_d2 = IzhikevichNeurons[10][3]

        if self.EmulatorSyn2_neuron_mode_index == 12:
            self.ui.Emulator_a2 = IzhikevichNeurons[11][0]
            self.ui.Emulator_b2 = IzhikevichNeurons[11][1]
            self.ui.Emulator_c2 = IzhikevichNeurons[11][2]
            self.ui.Emulator_d2 = IzhikevichNeurons[11][3]

        if self.EmulatorSyn2_neuron_mode_index <= 12:
            self.ui.Emulator_Syn2_PR_PhotoGain_slider.setEnabled(True)
            self.ui.Emulator_Syn2_PR_PhotoGain_slider.setValue(0)
            self.ui.Emulator_Syn2_PR_PhotoGain_slider.setEnabled(False)

            self.ui.Emulator_Syn2_PR_Decay_slider.setEnabled(True)
            self.ui.Emulator_Syn2_PR_Decay_slider.setValue(0.001)
            self.ui.Emulator_Syn2_PR_Decay_slider.setEnabled(False)

            self.ui.Emulator_Syn2_PR_Recovery_slider.setEnabled(True)
            self.ui.Emulator_Syn2_PR_Recovery_slider.setValue(0.025)
            self.ui.Emulator_Syn2_PR_Recovery_slider.setEnabled(False)



        if self.EmulatorSyn2_neuron_mode_index > 12:
            if self.EmulatorSyn2_neuron_mode_index > 12:
                self.ui.Emulator_a2 = self.ui.EmulatorSyn2_ImportNeuron[self.EmulatorSyn2_neuron_mode_index - 13][0]
                self.ui.Emulator_b2 = self.ui.EmulatorSyn2_ImportNeuron[self.EmulatorSyn2_neuron_mode_index - 13][1]
                self.ui.Emulator_c2 = self.ui.EmulatorSyn2_ImportNeuron[self.EmulatorSyn2_neuron_mode_index - 13][2]
                self.ui.Emulator_d2 = self.ui.EmulatorSyn2_ImportNeuron[self.EmulatorSyn2_neuron_mode_index - 13][3]


            self.EmulatorSyn2_Photodiode_Gain = self.ui.EmulatorSyn2_ImportNeuron[self.EmulatorSyn2_neuron_mode_index - 13][4]
            self.ui.Emulator_Syn2_PR_PhotoGain_slider.setEnabled(True)
            self.ui.Emulator_Syn2_PR_PhotoGain_slider.setValue(self.EmulatorSyn2_Photodiode_Gain)
            self.ui.Emulator_Syn2_PR_PhotoGain_slider.setEnabled(False)

            self.Syn2_Photodiode_Decay_value = self.ui.EmulatorSyn2_ImportNeuron[self.EmulatorSyn2_neuron_mode_index - 13][5]
            self.ui.Emulator_Syn2_PR_Decay_slider.setEnabled(True)
            self.ui.Emulator_Syn2_PR_Decay_slider.setValue(self.Syn2_Photodiode_Decay_value)
            self.ui.Emulator_Syn2_PR_Decay_slider.setEnabled(False)

            self.Photodiode_Recovery_value = self.ui.EmulatorSyn2_ImportNeuron[self.EmulatorSyn2_neuron_mode_index - 13][6]
            self.ui.Emulator_Syn2_PR_Recovery_slider.setEnabled(True)
            self.ui.Emulator_Syn2_PR_Recovery_slider.setValue(self.Photodiode_Recovery_value)
            self.ui.Emulator_Syn2_PR_Recovery_slider.setEnabled(False)






    def BrowseNeuron(self):
        FileName, _= QFileDialog.getOpenFileName(caption='Select Neuron',
                                                 dir="./Neurons",
                                                 filter='csv files (*.csv)')

        Df = pd.read_csv(FileName)
        self.Emulatordf_Neuron_a = Df["a"]
        self.Emulatordf_Neuron_b = Df["b"]
        self.Emulatordf_Neuron_c = Df["c"]
        self.Emulatordf_Neuron_d = Df["d"]

        self.Emulatordf_Neuron_PGain = Df["PhotoGain (%)"]
        self.Emulatordf_Neuron_PDecay = Df["PhotoDecay (1/ms)"]
        self.Emulatordf_Neuron_PRecovery = Df["PhotoRecovery (1/ms)"]

        self.Emulatordf_Neuron_Syn1Gain = Df["Syn1 Gain (%)"]
        self.Emulatordf_Neuron_Syn1Decay = Df["Syn1 Decay (1/ms)"]

        self.Emulatordf_Neuron_Syn2Gain = Df["Syn2 Gain (%)"]
        self.Emulatordf_Neuron_Syn2Decay = Df["Syn2 Decay (1/ms)"]

        self.EmulatorParametersNeuron = [self.Emulatordf_Neuron_a[0],
                                         self.Emulatordf_Neuron_b[0],
                                         self.Emulatordf_Neuron_c[0],
                                         self.Emulatordf_Neuron_d[0],
                                         self.Emulatordf_Neuron_PGain[0],
                                         self.Emulatordf_Neuron_PDecay[0],
                                         self.Emulatordf_Neuron_PRecovery[0],
                                         self.Emulatordf_Neuron_Syn1Gain[0],
                                         self.Emulatordf_Neuron_Syn1Decay[0],
                                         self.Emulatordf_Neuron_Syn2Gain[0],
                                         self.Emulatordf_Neuron_Syn2Decay[0]
                                         ]
        self.ui.EmulatorSyn1_ImportNeuron.append(self.EmulatorParametersNeuron)


        self.ui.Emulator_Syn1_Mode_comboBox.addItem('')
        self.Emulatorneuron_count = self.ui.Emulator_Syn1_Mode_comboBox.count()
        self.Emulatorfilename = os.path.splitext(os.path.basename(QFileInfo(FileName).fileName()))[0]
        self.ui.Emulator_Syn1_Mode_comboBox.setItemText(self.Emulatorneuron_count-1, self.Emulatorfilename)
        self.ui.Emulator_Syn1_Mode_comboBox.setCurrentIndex(self.Emulatorneuron_count-1)

