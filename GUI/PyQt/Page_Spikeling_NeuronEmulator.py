
########################################################################
#                          Libraries import                            #

from PySide6.QtWidgets import QFileDialog
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
        FolderName = QFileDialog.getExistingDirectory(
            caption='Hey! Select the folder where your experiment will be saved',
            dir="./Recordings")
        if FolderName:
            self.ui.Emulator_DataRecording_SelectRecordFolder_label.setText(FolderName)
            self.ui.Emulator_DataRecording_RecordFolder_value.setEnabled(True)
            self.ui.Emulator_DataRecording_RecordFolder_value.setPlaceholderText("Enter a file name")
            self.ui.EmulatorRecordFolderFlag = True


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
                    self.EmulatorStimFreValue = self.ui.Emulator_StimFre_slider.value()
                    Steps = int(np.round(1000 * (10 ** ( -self.EmulatorStimFreValue / 100.0))))
                    self.setTextEmulatorStimFre = str(int(np.around(10000/ Steps)))
                    self.ui.Emulator_StimFre_readings.setText(self.setTextEmulatorStimFre)
                    self.ui.Emulator_StimFre_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[5])) + "; font: 700 10pt;")

            else:
                    self.ui.Emulator_StimFre_slider.setEnabled(False)
                    self.ui.Emulator_StimFre_slider.setValue(0)
                    self.ui.Emulator_StimFre_readings.setText('')


    def GetStimFreSliderValue(self):
            self.EmulatorStimFreValue = self.ui.Emulator_StimFre_slider.value()
            Steps = int(np.round(1000 * (10 ** (-self.EmulatorStimFreValue / 100.0))))
            self.setTextEmulatorStimFre = str(int(np.around(10000 / Steps)))
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
        self.ui.Emulator_CustomStimulus_display.showGrid(x=False, y=False)
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



    # Helper: set Emulator_a/b/c/d from IzhikevichNeurons
    # Helper: set Emulator_a/b/c/d from IzhikevichNeurons
    def _set_izhikevich_emulator_from_index(self, idx_zero_based: int) -> None:
        """idx_zero_based is 0-based index into IzhikevichNeurons."""
        if 0 <= idx_zero_based < len(IzhikevichNeurons):
            a, b, c, d = IzhikevichNeurons[idx_zero_based]
            self.ui.Emulator_a = float(a)
            self.ui.Emulator_b = float(b)
            self.ui.Emulator_c = float(c)
            self.ui.Emulator_d = float(d)


    def SelectNeuronMode(self):
            """
            Set emulator neuron parameters from the current selection.

            Combo box mapping:
              index 0  -> (usually "Select neuron" / no selection)
              index 1–20 -> built-in IzhikevichNeurons[0..19]
              index >= 21 -> imported neurons stored in self.ui.EmulatorImportNeuron
            """
            idx = self.ui.Emulator_NeuronModeComboBox.currentIndex()
            self.Emulatorneuron_mode_index = idx

            # Nothing selected (first entry)
            if idx <= 0:
                return

            # -------------------------------------------------
            # 1) Built-in neurons (indices 1..12)
            # -------------------------------------------------
            if 1 <= idx <= 20:
                zero_based = idx - 1
                # Set a, b, c, d from IzhikevichNeurons
                self._set_izhikevich_emulator_from_index(zero_based)

                # Reset PR + synapse sliders to default "off" values
                # Photodiode
                self.ui.Emulator_PR_PhotoGain_slider.setEnabled(True)
                self.ui.Emulator_PR_PhotoGain_slider.setValue(0)
                self.ui.Emulator_PR_PhotoGain_slider.setEnabled(False)

                self.ui.Emulator_PR_Decay_slider.setEnabled(True)
                self.ui.Emulator_PR_Decay_slider.setValue(100)
                self.ui.Emulator_PR_Decay_slider.setEnabled(False)

                self.ui.Emulator_PR_Recovery_slider.setEnabled(True)
                self.ui.Emulator_PR_Recovery_slider.setValue(25)
                self.ui.Emulator_PR_Recovery_slider.setEnabled(False)

                # Synapse 1
                self.ui.Emulator_Synapse1_slider.setEnabled(True)
                self.ui.Emulator_Synapse1_slider.setValue(0)
                self.ui.Emulator_Synapse1_slider.setEnabled(False)

                self.ui.Emulator_Synapse1_Decay_slider.setEnabled(True)
                self.ui.Emulator_Synapse1_Decay_slider.setValue(995)
                self.ui.Emulator_Synapse1_Decay_slider.setEnabled(False)

                # Synapse 2
                self.ui.Emulator_Synapse2_slider.setEnabled(True)
                self.ui.Emulator_Synapse2_slider.setValue(0)
                self.ui.Emulator_Synapse2_slider.setEnabled(False)

                self.ui.Emulator_Synapse2_Decay_slider.setEnabled(True)
                self.ui.Emulator_Synapse2_Decay_slider.setValue(995)
                self.ui.Emulator_Synapse2_Decay_slider.setEnabled(False)

                return

            # -------------------------------------------------
            # 2) Imported neurons (indices >= 13)
            #    self.ui.EmulatorImportNeuron is filled from CSV:
            #    [a, b, c, d,
            #     PhotoGain, PhotoDecay, PhotoRecovery,
            #     Syn1Gain, Syn1Decay,
            #     Syn2Gain, Syn2Decay]
            # -------------------------------------------------
            import_idx = idx - 21  # index in EmulatorImportNeuron list

            try:
                neuron_params = self.ui.EmulatorImportNeuron[import_idx]
            except (AttributeError, IndexError):
                # No imported neuron data for this index
                return

            # a, b, c, d
            self.ui.Emulator_a = neuron_params[0]
            self.ui.Emulator_b = neuron_params[1]
            self.ui.Emulator_c = neuron_params[2]
            self.ui.Emulator_d = neuron_params[3]

            # Photodiode gain & kinetics
            self.Emulator_Photodiode_Gain = neuron_params[4]
            self.ui.Emulator_PR_PhotoGain_slider.setEnabled(True)
            self.ui.Emulator_PR_PhotoGain_slider.setValue(self.Emulator_Photodiode_Gain)
            self.ui.Emulator_PR_PhotoGain_slider.setEnabled(False)

            self.Photodiode_Decay_value = neuron_params[5]
            self.ui.Emulator_PR_Decay_slider.setEnabled(True)
            self.ui.Emulator_PR_Decay_slider.setValue(self.Photodiode_Decay_value)
            self.ui.Emulator_PR_Decay_slider.setEnabled(False)

            self.Photodiode_Recovery_value = neuron_params[6]
            self.ui.Emulator_PR_Recovery_slider.setEnabled(True)
            self.ui.Emulator_PR_Recovery_slider.setValue(self.Photodiode_Recovery_value)
            self.ui.Emulator_PR_Recovery_slider.setEnabled(False)

            # Synapse 1 gain & decay
            self.Emulator_Syn1_Gain = neuron_params[7]
            self.ui.Emulator_Synapse1_slider.setEnabled(True)
            self.ui.Emulator_Synapse1_slider.setValue(self.Emulator_Syn1_Gain)
            self.ui.Emulator_Synapse1_slider.setEnabled(False)

            self.Emulator_Syn1Decay = neuron_params[8]
            self.ui.Emulator_Synapse1_Decay_slider.setEnabled(True)
            self.ui.Emulator_Synapse1_Decay_slider.setValue(self.Emulator_Syn1Decay)
            self.ui.Emulator_Synapse1_Decay_slider.setEnabled(False)

            # Synapse 2 gain & decay
            self.Emulator_Syn2_Gain = neuron_params[9]
            self.ui.Emulator_Synapse2_slider.setEnabled(True)
            self.ui.Emulator_Synapse2_slider.setValue(self.Emulator_Syn2_Gain)
            self.ui.Emulator_Synapse2_slider.setEnabled(False)

            self.Emulator_Syn2Decay = neuron_params[10]
            self.ui.Emulator_Synapse2_Decay_slider.setEnabled(True)
            self.ui.Emulator_Synapse2_Decay_slider.setValue(self.Emulator_Syn2Decay)
            self.ui.Emulator_Synapse2_Decay_slider.setEnabled(False)



    def BrowseNeuron(self):
        FileName, _= QFileDialog.getOpenFileName(caption='Select Neuron',
                                                 dir="./Neurons",
                                                 filter='csv files (*.csv)')
        if not FileName:
            return  # user cancelled

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



    def _set_izhikevich_syn1_from_index(self, idx_zero_based: int) -> None:
        """
        Set (a1, b1, c1, d1) and PR sliders for Synapse 1
        from either a built-in Izhikevich neuron or an imported neuron.

        idx_zero_based:
            0–20  -> built-in IzhikevichNeurons[0..19]
            21+   -> imported neurons in self.ui.EmulatorSyn1_ImportNeuron[0..]
        """
        if idx_zero_based < 0:
            return

        # --- Built-in neurons: indices 0..20 (combo indices 1..20) ---
        if idx_zero_based < 20:
            try:
                a, b, c, d = IzhikevichNeurons[idx_zero_based]
            except IndexError:
                return

            self.ui.Emulator_a1 = float(a)
            self.ui.Emulator_b1 = float(b)
            self.ui.Emulator_c1 = float(c)
            self.ui.Emulator_d1 = float(d)

            # Reset Syn1 photodiode to defaults (as in your original code)
            self.ui.Emulator_Syn1_PR_PhotoGain_slider.setEnabled(True)
            self.ui.Emulator_Syn1_PR_PhotoGain_slider.setValue(0)
            self.ui.Emulator_Syn1_PR_PhotoGain_slider.setEnabled(False)

            self.ui.Emulator_Syn1_PR_Decay_slider.setEnabled(True)
            self.ui.Emulator_Syn1_PR_Decay_slider.setValue(100)
            self.ui.Emulator_Syn1_PR_Decay_slider.setEnabled(False)

            self.ui.Emulator_Syn1_PR_Recovery_slider.setEnabled(True)
            self.ui.Emulator_Syn1_PR_Recovery_slider.setValue(25)
            self.ui.Emulator_Syn1_PR_Recovery_slider.setEnabled(False)
            return

        # --- Imported neurons: indices 20+ (combo indices 21+) ---
        imported_index = idx_zero_based - 20
        imported_list = getattr(self.ui, "EmulatorSyn1_ImportNeuron", None)
        if not imported_list or imported_index >= len(imported_list):
            return

        (a, b, c, d,
         pr_gain, pr_decay, pr_recovery,
         syn1_gain, syn1_decay,
         syn2_gain, syn2_decay) = imported_list[imported_index]

        self.ui.Emulator_a1 = float(a)
        self.ui.Emulator_b1 = float(b)
        self.ui.Emulator_c1 = float(c)
        self.ui.Emulator_d1 = float(d)

        # Apply imported photo parameters to the sliders
        self.ui.Emulator_Syn1_PR_PhotoGain_slider.setEnabled(True)
        self.ui.Emulator_Syn1_PR_PhotoGain_slider.setValue(pr_gain)
        self.ui.Emulator_Syn1_PR_PhotoGain_slider.setEnabled(False)

        self.ui.Emulator_Syn1_PR_Decay_slider.setEnabled(True)
        self.ui.Emulator_Syn1_PR_Decay_slider.setValue(pr_decay)
        self.ui.Emulator_Syn1_PR_Decay_slider.setEnabled(False)

        self.ui.Emulator_Syn1_PR_Recovery_slider.setEnabled(True)
        self.ui.Emulator_Syn1_PR_Recovery_slider.setValue(pr_recovery)
        self.ui.Emulator_Syn1_PR_Recovery_slider.setEnabled(False)

    def SelectNeuronMode(self):
        """
        Called when Emulator_Syn1_Mode_comboBox changes.

        Combo index mapping:
            0   -> placeholder / '---'
            1–20 -> built-in IzhikevichNeurons[0..20]
            21+  -> imported neurons in self.ui.EmulatorSyn1_ImportNeuron
        """
        self.EmulatorSyn1_neuron_mode_index = self.ui.Emulator_Syn1_Mode_comboBox.currentIndex()

        # Index 0 is usually a 'blank' / default entry: keep current parameters
        if self.EmulatorSyn1_neuron_mode_index <= 0:
            return

        idx_zero_based = self.EmulatorSyn1_neuron_mode_index - 1
        self._set_izhikevich_syn1_from_index(idx_zero_based)



    def BrowseNeuron(self):
        FileName, _= QFileDialog.getOpenFileName(caption='Select Neuron',
                                                 dir="./Neurons",
                                                 filter='csv files (*.csv)')

        if not FileName:
            return  # user cancelled

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
            self.ui.Emulator_Syn2_PR_Decay_readings.setText(str(self.EmulatorSyn2PhotoDecay/100000))
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
                    self.EmulatorSyn2_Noise = 0
                    self.ui.Emulator_Syn2_Noise_slider.setValue(0)
                    self.ui.Emulator_Syn2_Noise_readings.setText("")


    def GetNoiseLevel(self):
            self.EmulatorSyn2_Noise = self.ui.Emulator_Syn2_Noise_slider.value()
            self.ui.Emulator_Syn2_Noise_readings.setText(str(self.EmulatorSyn2_Noise))
            self.ui.Emulator_Syn2_Noise_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")



    def _set_izhikevich_syn2_from_index(self, idx_zero_based: int) -> None:
        """
        Set (a2, b2, c2, d2) and PR sliders for Synapse 2
        from either a built-in Izhikevich neuron or an imported neuron.

        idx_zero_based:
            0–19  -> built-in IzhikevichNeurons[0..19]
            20+   -> imported neurons in self.ui.EmulatorSyn2_ImportNeuron[0..]
        """
        if idx_zero_based < 0:
            return

        # --- Built-in neurons: indices 0..19 (combo indices 1..20) ---
        if idx_zero_based < 20:
            try:
                a, b, c, d = IzhikevichNeurons[idx_zero_based]
            except IndexError:
                return

            self.ui.Emulator_a2 = float(a)
            self.ui.Emulator_b2 = float(b)
            self.ui.Emulator_c2 = float(c)
            self.ui.Emulator_d2 = float(d)

            # Reset Syn2 photodiode to defaults (as in your original code)
            self.ui.Emulator_Syn2_PR_PhotoGain_slider.setEnabled(True)
            self.ui.Emulator_Syn2_PR_PhotoGain_slider.setValue(0)
            self.ui.Emulator_Syn2_PR_PhotoGain_slider.setEnabled(False)

            self.ui.Emulator_Syn2_PR_Decay_slider.setEnabled(True)
            self.ui.Emulator_Syn2_PR_Decay_slider.setValue(100)
            self.ui.Emulator_Syn2_PR_Decay_slider.setEnabled(False)

            self.ui.Emulator_Syn2_PR_Recovery_slider.setEnabled(True)
            self.ui.Emulator_Syn2_PR_Recovery_slider.setValue(25)
            self.ui.Emulator_Syn2_PR_Recovery_slider.setEnabled(False)
            return

        # --- Imported neurons: indices 20+ (combo indices 21+) ---
        imported_index = idx_zero_based - 20
        imported_list = getattr(self.ui, "EmulatorSyn2_ImportNeuron", None)
        if not imported_list or imported_index >= len(imported_list):
            return

        (a, b, c, d,
         pr_gain, pr_decay, pr_recovery,
         syn1_gain, syn1_decay,
         syn2_gain, syn2_decay) = imported_list[imported_index]

        self.ui.Emulator_a2 = float(a)
        self.ui.Emulator_b2 = float(b)
        self.ui.Emulator_c2 = float(c)
        self.ui.Emulator_d2 = float(d)

        # Apply imported photo parameters
        self.ui.Emulator_Syn2_PR_PhotoGain_slider.setEnabled(True)
        self.ui.Emulator_Syn2_PR_PhotoGain_slider.setValue(pr_gain)
        self.ui.Emulator_Syn2_PR_PhotoGain_slider.setEnabled(False)

        self.ui.Emulator_Syn2_PR_Decay_slider.setEnabled(True)
        self.ui.Emulator_Syn2_PR_Decay_slider.setValue(pr_decay)
        self.ui.Emulator_Syn2_PR_Decay_slider.setEnabled(False)

        self.ui.Emulator_Syn2_PR_Recovery_slider.setEnabled(True)
        self.ui.Emulator_Syn2_PR_Recovery_slider.setValue(pr_recovery)
        self.ui.Emulator_Syn2_PR_Recovery_slider.setEnabled(False)

    def SelectNeuronMode(self):
        """
        Called when Emulator_Syn2_Mode_comboBox changes.

        Combo index mapping:
            0     -> placeholder / '---'
            1–20  -> built-in IzhikevichNeurons[0..19]
            21+   -> imported neurons in self.ui.EmulatorSyn2_ImportNeuron
        """
        self.EmulatorSyn2_neuron_mode_index = self.ui.Emulator_Syn2_Mode_comboBox.currentIndex()

        # Index 0 is usually a 'blank' / default entry: keep current parameters
        if self.EmulatorSyn2_neuron_mode_index <= 0:
            return

        idx_zero_based = self.EmulatorSyn2_neuron_mode_index - 1
        self._set_izhikevich_syn2_from_index(idx_zero_based)



    def BrowseNeuron(self):
        FileName, _= QFileDialog.getOpenFileName(caption='Select Neuron',
                                                 dir="./Neurons",
                                                 filter='csv files (*.csv)')

        if not FileName:
            return  # user cancelled

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
        self.ui.EmulatorSyn2_ImportNeuron.append(self.EmulatorParametersNeuron)


        self.ui.Emulator_Syn2_Mode_comboBox.addItem('')
        self.Emulatorneuron_count = self.ui.Emulator_Syn2_Mode_comboBox.count()
        self.Emulatorfilename = os.path.splitext(os.path.basename(QFileInfo(FileName).fileName()))[0]
        self.ui.Emulator_Syn2_Mode_comboBox.setItemText(self.Emulatorneuron_count-1, self.Emulatorfilename)
        self.ui.Emulator_Syn2_Mode_comboBox.setCurrentIndex(self.Emulatorneuron_count-1)

