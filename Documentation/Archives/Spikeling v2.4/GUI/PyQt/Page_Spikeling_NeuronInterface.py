
########################################################################
#                          Libraries import                            #

from PySide6.QtWidgets import QFileDialog
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize, QFileInfo

from serial_manager import serial_manager
import os
import numpy as np
import pandas as pd

import Settings, NavigationButtons
from Izhikevich_parameters import IzhikevichNeurons


# Use the global serial_manager instance
serial_port = serial_manager



class Spikeling():

    def ShowPage(self):
        self.ui.Spikeling_rightMenuContainer.setMinimumSize(QSize(NavigationButtons.spikerightMenu_max, 16777215))
        self.ui.Spikeling_Oscilloscope_widget.setBackground(Settings.DarkSolarized[0])
        self.ui.Spikeling_CustomStimulus_display.setBackground(Settings.DarkSolarized[0])
        self.ui.mainbody_stackedWidget.setCurrentWidget(self.ui.page_101)
        NavigationButtons.toggleMenu(self, self.ui.Spikeling_rightMenuContainer, NavigationButtons.spikerightMenu_min, NavigationButtons.spikerightMenu_max, NavigationButtons.animation_speed,
                                     self.ui.Spikeling_rightMenuSubContainer_pushButton, self.icon_SpikelingMenuRight, self.icon_SpikelingDropMenuRight, True)

    # Serial Port Functions
    def ChangePort(self):
        global serial_port
        self.COM = self.ui.Spikeling_SelectPortComboBox.currentText()
        self.BaudRate = Settings.BaudRate
        serial_port.configure_port(self.COM)
        if serial_port.open():
            serial_port.write('CON' + '\n')
        self.ui.Spikeling_ConnectButton.setChecked(False)


    # Control buzzer sound
    def ControlBuzzer(self):
        global serial_port
        icon_buzzer_off = QIcon()
        icon_buzzer_off.addFile(u":/resources/resources/SoundOFF.png", QSize(), QIcon.Normal, QIcon.Off)
        icon_buzzer_on = QIcon()
        icon_buzzer_on.addFile(u":/resources/resources/SoundON.png", QSize(), QIcon.Normal, QIcon.Off)
        if self.ui.Sound_pushButton.isChecked():
                self.ui.Sound_pushButton.setIcon(icon_buzzer_off)
                self.ui.Sound_pushButton.setText("Buzzer Off   ")
                if serial_port.is_open:
                        serial_port.write('BZ0' + '\n')
        else:
                self.ui.Sound_pushButton.setIcon(icon_buzzer_on)
                self.ui.Sound_pushButton.setText("Buzzer On   ")
                if serial_port.is_open:
                        serial_port.write('BZ1' + '\n')

    # Control LED light
    def ControlLED(self):
            global serial_port
            icon_LED_off = QIcon()
            icon_LED_off.addFile(u":/resources/resources/LEDOFF.png", QSize(), QIcon.Normal, QIcon.Off)
            icon_LED_on = QIcon()
            icon_LED_on.addFile(u":/resources/resources/LEDON.png", QSize(), QIcon.Normal, QIcon.Off)
            if self.ui.LED_pushButton.isChecked():
                    self.ui.LED_pushButton.setIcon(icon_LED_off)
                    self.ui.LED_pushButton.setText("LED Off   ")
                    if serial_port.is_open:
                            serial_port.write('LED0' + '\n')
            else:
                    self.ui.LED_pushButton.setIcon(icon_LED_on)
                    self.ui.LED_pushButton.setText("LED On   ")
                    if serial_port.is_open:
                            serial_port.write('LED1' + '\n')


    # Data Recording Functions
    def BrowseRecordFolder(self):
        FolderName = QFileDialog.getExistingDirectory(caption = 'Hey! Select the folder where your experiment will be saved',
                                      dir = ".\\Recordings")
        if FolderName:
            self.Spikeling_DataRecording_SelectRecordFolder_label.setText(FolderName)
            self.Spikeling_DataRecording_RecordFolder_value.setEnabled(True)
            self.Spikeling_DataRecording_RecordFolder_value.setPlaceholderText("Enter a file name")
            self.NeuronRecordFolderFlag = True


    def RecordFolderText(self):
        FolderName = self.ui.Spikeling_DataRecording_SelectRecordFolder_label.text()
        FileName = self.ui.Spikeling_DataRecording_RecordFolder_value.text()
        self.ui.Spikeling_SelectedFolderLabel.setText(FolderName + '/' + FileName + '   ')


    def RecordButton(self):
        SerialPortFlag = False
        FolderFlag = False
        FileFlag = False

        if self.ui.Spikeling_DataRecording_Record_pushButton.isChecked():

            if self.SerialFlag == False:
                self.ui.Spikeling_DataRecording_Record_pushButton.setChecked(False)
                Settings.show_popup(self,
                                    Title = "Error: Spikeling not connected",
                                    Text = "Spikeling first needs to be connected, then a COM port has to be selected and finally press the - Connect Spikeling Screen - button" )
            else:
                SerialPortFlag = True


            if self.ui.NeuronRecordFolderFlag == True:
                FolderFlag = True

            else:
                self.ui.Spikeling_DataRecording_Record_pushButton.setChecked(False)
                Settings.show_popup(self,
                                    Title = "Error: no folder selected",
                                    Text = "Select a folder where to record your data by clicking on the - browse directory - button")


            if self.ui.Spikeling_DataRecording_RecordFolder_value.text():
                FileFlag = True

            else:
                self.ui.Spikeling_DataRecording_Record_pushButton.setChecked(False)
                Settings.show_popup(self,
                                    Title="Error: no file selected",
                                    Text="Select a file where to record your data by clicking on the - browse directory - button")


            if SerialPortFlag == True and FolderFlag == True and FileFlag == True:
                if self.ui.Spikeling_DataRecording_Record_pushButton.isChecked():
                    self.ui.Spikeling_DataRecording_Record_pushButton.setText("Stop Recording")
                    self.ui.Spikeling_DataRecording_Record_pushButton.setStyleSheet("color: rgb(250, 250, 250);\n"
                                                                                    "background-color: rgb(50, 220, 47);")

        if self.ui.Spikeling_DataRecording_Record_pushButton.isChecked() == False:
                self.ui.Spikeling_DataRecording_Record_pushButton.setText("Record")
                self.ui.Spikeling_DataRecording_Record_pushButton.setStyleSheet("color: rgb(250, 250, 250);\n"
                                                                                    "background-color: rgb(220, 50, 47);")




    # Stimulus Frequency
    def ActivateStimFre(self):
            global serial_port
            if self.ui.StimFre_toggleButton.isChecked():
                    self.Stim_DutyCycle = 500
                    self.Stim_MinCycle = 10
                    self.ui.Spikeling_StimFre_slider.setEnabled(True)
                    self.StimFreValue = self.ui.Spikeling_StimFre_slider.value()*(-1)
                    self.setTextStimFre = str(int(np.around(10000/(self.Stim_DutyCycle + (self.StimFreValue*self.Stim_DutyCycle/100) + self.Stim_MinCycle))))
                    self.ui.Spikeling_StimFre_readings.setText(self.setTextStimFre)
                    self.ui.Spikeling_StimFre_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[5])) + "; font: 700 10pt;")
                    if serial_port.is_open:
                        serial_port.write('FR1 ' + str(self.StimFreValue) + '\n')
            else:
                    self.ui.Spikeling_StimFre_slider.setEnabled(False)
                    self.ui.Spikeling_StimFre_slider.setValue(0)
                    self.ui.Spikeling_StimFre_readings.setText('')
                    if serial_port.is_open:
                            serial_port.write('FR0' + '\n')

    def GetStimFreSliderValue(self):
            global serial_port
            self.StimFreValue = self.ui.Spikeling_StimFre_slider.value()*(-1)
            self.setTextStimFre = str(int(np.around(10000/(self.Stim_DutyCycle + (self.StimFreValue*self.Stim_DutyCycle/100) + self.Stim_MinCycle))))
            self.ui.Spikeling_StimFre_readings.setText(self.setTextStimFre)
            self.ui.Spikeling_StimFre_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[5])) + "; font: 700 10pt;")
            if serial_port.is_open:
                serial_port.write('FR1 ' + str(self.StimFreValue) + '\n')


    # Stimulus Strength
    def ActivateStimStr(self):
            global serial_port
            if self.ui.StimStr_toggleButton.isChecked():
                    self.ui.Spikeling_StimStrSlider.setEnabled(True)
                    self.StimStrValue = self.ui.Spikeling_StimStrSlider.value()
                    self.ui.Spikeling_StimStr_readings.setText(str(self.StimStrValue))
                    self.ui.Spikeling_StimStr_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[5])) + "; font: 700 10pt;")
                    if serial_port.is_open:
                        serial_port.write('ST1 ' + str(self.StimStrValue) + '\n')
            else:
                    self.ui.Spikeling_StimStrSlider.setEnabled(False)
                    self.ui.Spikeling_StimStrSlider.setValue(0)
                    self.ui.Spikeling_StimStr_readings.setText('')
                    if serial_port.is_open:
                            serial_port.write('ST0' + '\n')

    def GetStimStrSliderValue(self):
            global serial_port
            self.StimStrValue = self.ui.Spikeling_StimStrSlider.value()
            self.ui.Spikeling_StimStr_readings.setText(str(self.StimStrValue))
            self.ui.Spikeling_StimStr_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[5])) + "; font: 700 10pt;")
            if serial_port.is_open:
                serial_port.write('ST1 ' + str(self.StimStrValue) + '\n')


    # Custom Stimulus
    def ActivateCustomStimulus(self):
            global serial_port
            if self.ui.StimCus_toggleButton.isChecked():
                self.StimCounter = 0
                self.StimCusValue = self.ui.df_yStim[self.StimCounter]

                if serial_port.is_open:
                    serial_port.write('SC1 ' + str(self.StimCusValue) + '\n')
                    serial_port.write('TR' + '\n')

            else:
                if serial_port.is_open:
                    serial_port.write('SC0' + '\n')



    def LoadStimulus(self):
        FileName, _ = QFileDialog.getOpenFileName(self,
                                               caption='Select a custom stimulus',
                                               dir="./Stimuli",
                                               filter='csv files (*.csv)'
                                               )
        self.filename = os.path.splitext(os.path.basename(QFileInfo(FileName).fileName()))[0]
        self.ui.Spikeling_CustomStimulus_StimLabel.setText(self.filename)

        Df = pd.read_csv(FileName)
        self.ui.df_Stim = Df["Stim"]

        self.ui.df_xStim = np.linspace(0, len(self.ui.df_Stim)/10 - 1, len(self.ui.df_Stim))

        self.ui.df_yStim = np.zeros(len(self.ui.df_Stim))
        self.ui.df_yStim = self.ui.df_Stim

        self.ui.Spikeling_CustomStimulus_display.clear()
        self.ui.Spikeling_Oscilloscope_widget.showGrid(x=False, y=False)
        self.ui.Spikeling_CustomStimulus_display.plot(x=self.ui.df_xStim, y=self.ui.df_yStim, pen=(Settings.DarkSolarized[5]))



    # PhotoGain
    def ActivatePhotoGain(self):
            global serial_port
            if self.ui.PhotoGain_toggleButton.isChecked():
                    self.ui.Spikeling_PR_PhotoGain_slider.setEnabled(True)
                    self.PhotoGain = self.ui.Spikeling_PR_PhotoGain_slider.value()
                    self.ui.Spikeling_PR_Photogain_readings.setText(str(self.PhotoGain))
                    self.ui.Spikeling_PR_Photogain_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")
                    if serial_port.is_open:
                            serial_port.write('PG1 ' + str(self.PhotoGain) + '\n')
            else:
                    self.ui.Spikeling_PR_PhotoGain_slider.setEnabled(False)
                    self.ui.Spikeling_PR_PhotoGain_slider.setValue(0)
                    self.ui.Spikeling_PR_Photogain_readings.setText("")
                    if serial_port.is_open:
                            serial_port.write('PG0' + '\n')

    def GetPhotoGain(self):
            global serial_port
            self.PhotoGain = self.ui.Spikeling_PR_PhotoGain_slider.value()
            self.ui.Spikeling_PR_Photogain_readings.setText(str(self.PhotoGain))
            self.ui.Spikeling_PR_Photogain_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")
            if serial_port.is_open:
                    serial_port.write('PG1 ' + str(self.PhotoGain) + '\n')


    # PhotoDecay
    def ActivatePRDecay(self):
            global serial_port
            if self.ui.PhotoDecay_toggleButton.isChecked():
                    self.ui.Spikeling_PR_Decay_slider.setEnabled(True)
                    self.PhotoDecay = self.ui.Spikeling_PR_Decay_slider.value()
                    self.ui.Spikeling_PR_Decay_readings.setText(str(self.PhotoDecay/100000))
                    self.ui.Spikeling_PR_Decay_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")
                    if serial_port.is_open:
                            serial_port.write('PD1 ' + str(self.PhotoDecay/100000) + '\n')
            else:
                    self.ui.Spikeling_PR_Decay_slider.setEnabled(False)
                    self.ui.Spikeling_PR_Decay_slider.setValue(100)
                    self.ui.Spikeling_PR_Decay_readings.setText("")
                    if serial_port.is_open:
                            serial_port.write('PD0' + '\n')

    def GetPRDecay(self):
            global serial_port
            self.PhotoDecay = self.ui.Spikeling_PR_Decay_slider.value()
            self.ui.Spikeling_PR_Decay_readings.setText(str(self.PhotoDecay/100000))
            self.ui.Spikeling_PR_Decay_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")
            if serial_port.is_open:
                    serial_port.write('PD1 ' + str(self.PhotoDecay/100000) + '\n')


    # PhotoRecovery
    def ActivatePRRecovery(self):
            global serial_port
            if self.ui.PhotoRecovery_toggleButton.isChecked():
                    self.ui.Spikeling_PR_Recovery_slider.setEnabled(True)
                    self.PhotoRecovery = self.ui.Spikeling_PR_Recovery_slider.value()
                    self.ui.Spikeling_PR_Recovery_readings.setText(str(self.PhotoRecovery/1000))
                    self.ui.Spikeling_PR_Recovery_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")
                    if serial_port.is_open:
                            serial_port.write('PR1 ' + str(self.PhotoRecovery/1000) + '\n')
            else:
                    self.ui.Spikeling_PR_Recovery_slider.setEnabled(False)
                    self.ui.Spikeling_PR_Recovery_slider.setValue(25)
                    self.ui.Spikeling_PR_Recovery_readings.setText("")
                    if serial_port.is_open:
                            serial_port.write('PR0' + '\n')

    def GetPRRecovery(self):
            global serial_port
            self.PhotoRecovery = self.ui.Spikeling_PR_Recovery_slider.value()
            self.ui.Spikeling_PR_Recovery_readings.setText(str(self.PhotoRecovery/1000))
            self.ui.Spikeling_PR_Recovery_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")
            if serial_port.is_open:
                    serial_port.write('PR1 ' + str(self.PhotoRecovery/1000) + '\n')


    # PatchClamp
    def ActivateInjectedCurrent(self):
            global serial_port
            if self.ui.PatchClamp_toggleButton.isChecked():
                    self.ui.Spikeling_PatchClamp_slider.setEnabled(True)
                    self.InjectedCurrent = self.ui.Spikeling_PatchClamp_slider.value()
                    self.ui.Spikeling_PatchClamp_reading.setText(str(self.InjectedCurrent))
                    self.ui.Spikeling_PatchClamp_reading.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")
                    if serial_port.is_open:
                            serial_port.write('IC1 ' + str(self.InjectedCurrent) + '\n')
            else:
                    self.ui.Spikeling_PatchClamp_slider.setEnabled(False)
                    self.ui.Spikeling_PatchClamp_slider.setValue(0)
                    self.ui.Spikeling_PatchClamp_reading.setText("")
                    if serial_port.is_open:
                            serial_port.write('IC0' + '\n')

    def GetInjectedCurrent(self):
            global serial_port
            self.InjectedCurrent = self.ui.Spikeling_PatchClamp_slider.value()
            self.ui.Spikeling_PatchClamp_reading.setText(str(self.InjectedCurrent))
            self.ui.Spikeling_PatchClamp_reading.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")
            if serial_port.is_open:
                serial_port.write('IC1 ' + str(self.InjectedCurrent) + '\n')


    # NoiseLevel
    def ActivateNoiseLevel(self):
            global serial_port
            if self.ui.Noise_toggleButton.isChecked():
                    self.ui.Spikeling_Noise_slider.setEnabled(True)
                    self.NoiseValue = self.ui.Spikeling_Noise_slider.value()
                    self.Noise = np.random.normal(0, self.NoiseValue/2)
                    self.ui.Spikeling_Noise_readings.setText(str(self.NoiseValue))
                    self.ui.Spikeling_Noise_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")
                    if serial_port.is_open:
                        serial_port.write('NO1 ' + str(self.Noise) + '\n')
            else:
                    self.ui.Spikeling_Noise_slider.setEnabled(False)
                    self.ui.Spikeling_Noise_slider.setValue(0)
                    self.ui.Spikeling_Noise_readings.setText("")
                    if serial_port.is_open:
                            serial_port.write('NO0' + '\n')

    def GetNoiseLevel(self):
            global serial_port
            self.NoiseValue = self.ui.Spikeling_Noise_slider.value()
            self.Noise = np.random.normal(0, self.NoiseValue / 2)
            self.ui.Spikeling_Noise_readings.setText(str(self.NoiseValue))
            self.ui.Spikeling_Noise_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[4])) + "; font: 700 10pt;")
            if serial_port.is_open:
                serial_port.write('NO1 ' + str(self.Noise) + '\n')


    # Synapse1Gain
    def ActivateSynapticGain1(self):
            global serial_port
            if self.ui.Synapse1_toggleButton.isChecked():
                    self.ui.Spikeling_Synapse1_slider.setEnabled(True)
                    self.Synapse1Gain = self.ui.Spikeling_Synapse1_slider.value()
                    self.ui.Spikeling_Synapse1_readings.setText(str(self.Synapse1Gain))
                    self.ui.Spikeling_Synapse1_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[7])) + "; font: 700 10pt;")
                    if serial_port.is_open:
                        serial_port.write('SG11 ' + str(self.Synapse1Gain) + '\n')
            else:
                    self.ui.Spikeling_Synapse1_slider.setEnabled(False)
                    self.ui.Spikeling_Synapse1_slider.setValue(0)
                    self.ui.Spikeling_Synapse1_readings.setText("")
                    if serial_port.is_open:
                            serial_port.write('SG10' + '\n')

    def GetSynapticGain1(self):
            global serial_port
            self.Synapse1Gain = self.ui.Spikeling_Synapse1_slider.value()
            self.ui.Spikeling_Synapse1_readings.setText(str(self.Synapse1Gain))
            self.ui.Spikeling_Synapse1_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[7])) + "; font: 700 10pt;")
            if serial_port.is_open:
                serial_port.write('SG11 ' + str(self.Synapse1Gain) + '\n')


    # Synapse1Decay
    def ActivateSynapseDecay1(self):
            global serial_port
            if self.ui.Synapse1Decay_toggleButton.isChecked():
                    self.ui.Spikeling_Synapse1_Decay_slider.setEnabled(True)
                    self.Synapse1Decay = self.ui.Spikeling_Synapse1_Decay_slider.value()
                    self.ui.Spikeling_Synapse1_Decay_readings.setText(str(self.Synapse1Decay/1000))
                    self.ui.Spikeling_Synapse1_Decay_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[7])) + "; font: 700 10pt;")
                    if serial_port.is_open:
                        serial_port.write('SD11 ' + str(self.Synapse1Decay) + '\n')
            else:
                    self.ui.Spikeling_Synapse1_Decay_slider.setEnabled(False)
                    self.ui.Spikeling_Synapse1_Decay_slider.setValue(995)
                    self.ui.Spikeling_Synapse1_Decay_readings.setText("")
                    if serial_port.is_open:
                            serial_port.write('SD10' + '\n')

    def GetSynapticDecay1(self):
            global serial_port
            self.Synapse1Decay = self.ui.Spikeling_Synapse1_Decay_slider.value()
            self.ui.Spikeling_Synapse1_Decay_readings.setText(str(self.Synapse1Decay/1000))
            self.ui.Spikeling_Synapse1_Decay_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[7])) + "; font: 700 10pt;")
            if serial_port.is_open:
                serial_port.write('SD11 ' + str(self.Synapse1Decay) + '\n')


    # Synapse2Gain
    def ActivateSynapticGain2(self):
            global serial_port
            if self.ui.Synapse2_toggleButton.isChecked():
                    self.ui.Spikeling_Synapse2_slider.setEnabled(True)
                    self.Synapse2Gain = self.ui.Spikeling_Synapse2_slider.value()
                    self.ui.Spikeling_Synapse2_readings.setText(str(self.Synapse2Gain))
                    self.ui.Spikeling_Synapse2_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[10])) + "; font: 700 10pt;")
                    if serial_port.is_open:
                        serial_port.write('SG21 ' + str(self.Synapse2Gain) + '\n')
            else:
                    self.ui.Spikeling_Synapse2_slider.setEnabled(False)
                    self.ui.Spikeling_Synapse2_slider.setValue(0)
                    self.ui.Spikeling_Synapse2_readings.setText("")
                    if serial_port.is_open:
                            serial_port.write('SG20' + '\n')

    def GetSynapticGain2(self):
            global serial_port
            self.Synapse2Gain = self.ui.Spikeling_Synapse2_slider.value()
            self.ui.Spikeling_Synapse2_readings.setText(str(self.Synapse2Gain))
            self.ui.Spikeling_Synapse2_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[10])) + "; font: 700 10pt;")
            if serial_port.is_open:
                serial_port.write('SG21 ' + str(self.Synapse2Gain) + '\n')


    # Synapse1Decay
    def ActivateSynapseDecay2(self):
            global serial_port
            if self.ui.Synapse2Decay_toggleButton.isChecked():
                    self.ui.Spikeling_Synapse2_Decay_slider.setEnabled(True)
                    self.Synapse2Decay = self.ui.Spikeling_Synapse2_Decay_slider.value()
                    self.ui.Spikeling_Synapse2_Decay_readings.setText(str(self.Synapse2Decay/1000))
                    self.ui.Spikeling_Synapse2_Decay_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[10])) + "; font: 700 10pt;")
                    if serial_port.is_open:
                        serial_port.write('SD21 ' + str(self.Synapse2Decay) + '\n')
            else:
                    self.ui.Spikeling_Synapse2_Decay_slider.setEnabled(False)
                    self.ui.Spikeling_Synapse2_Decay_slider.setValue(990)
                    self.ui.Spikeling_Synapse2_Decay_readings.setText("")
                    if serial_port.is_open:
                            serial_port.write('SD20' + '\n')

    def GetSynapticDecay2(self):
            global serial_port
            self.Synapse2Decay = self.ui.Spikeling_Synapse2_Decay_slider.value()
            self.ui.Spikeling_Synapse2_Decay_readings.setText(str(self.Synapse2Decay/1000))
            self.ui.Spikeling_Synapse2_Decay_readings.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[10])) + "; font: 700 10pt;")
            if serial_port.is_open:
                serial_port.write('SD21 ' + str(self.Synapse2Decay) + '\n')


    def SelectNeuronMode(self):
            global serial_port
            self.neuron_mode_index = self.ui.Spikeling_NeuronModeComboBox.currentIndex()
            if self.neuron_mode_index == 1 and serial_port.is_open:
                serial_port.write('NEU ' + str(IzhikevichNeurons[0][0]) +  ' ' + str(IzhikevichNeurons[0][1]) + ' ' +  str(IzhikevichNeurons[0][2]) + ' ' + str(IzhikevichNeurons[0][3]) + ' ' + str(IzhikevichNeurons[0][4]) + '\n')
            if self.neuron_mode_index == 2 and serial_port.is_open:
                serial_port.write('NEU ' + str(IzhikevichNeurons[1][0]) +  ' ' + str(IzhikevichNeurons[1][1]) + ' ' +  str(IzhikevichNeurons[1][2]) + ' ' + str(IzhikevichNeurons[1][3]) + ' ' + str(IzhikevichNeurons[1][4]) + '\n')
            if self.neuron_mode_index == 3 and serial_port.is_open:
                serial_port.write('NEU ' + str(IzhikevichNeurons[2][0]) +  ' ' + str(IzhikevichNeurons[2][1]) + ' ' +  str(IzhikevichNeurons[2][2]) + ' ' + str(IzhikevichNeurons[2][3]) + ' ' + str(IzhikevichNeurons[2][4]) + '\n')
            if self.neuron_mode_index == 4 and serial_port.is_open:
                serial_port.write('NEU ' + str(IzhikevichNeurons[3][0]) +  ' ' + str(IzhikevichNeurons[3][1]) + ' ' +  str(IzhikevichNeurons[3][2]) + ' ' + str(IzhikevichNeurons[3][3]) + ' ' + str(IzhikevichNeurons[3][4]) + '\n')
            if self.neuron_mode_index == 5 and serial_port.is_open:
                serial_port.write('NEU ' + str(IzhikevichNeurons[4][0]) +  ' ' + str(IzhikevichNeurons[4][1]) + ' ' +  str(IzhikevichNeurons[4][2]) + ' ' + str(IzhikevichNeurons[4][3]) + ' ' + str(IzhikevichNeurons[4][4]) + '\n')
            if self.neuron_mode_index == 6 and serial_port.is_open:
                serial_port.write('NEU ' + str(IzhikevichNeurons[5][0]) +  ' ' + str(IzhikevichNeurons[5][1]) + ' ' +  str(IzhikevichNeurons[5][2]) + ' ' + str(IzhikevichNeurons[5][3]) + ' ' + str(IzhikevichNeurons[5][4]) + '\n')
            if self.neuron_mode_index == 7 and serial_port.is_open:
                serial_port.write('NEU ' + str(IzhikevichNeurons[6][0]) +  ' ' + str(IzhikevichNeurons[6][1]) + ' ' +  str(IzhikevichNeurons[6][2]) + ' ' + str(IzhikevichNeurons[6][3]) + ' ' + str(IzhikevichNeurons[6][4]) + '\n')
            if self.neuron_mode_index == 8 and serial_port.is_open:
                serial_port.write('NEU ' + str(IzhikevichNeurons[7][0]) +  ' ' + str(IzhikevichNeurons[7][1]) + ' ' +  str(IzhikevichNeurons[7][2]) + ' ' + str(IzhikevichNeurons[7][3]) + ' ' + str(IzhikevichNeurons[7][4]) + '\n')
            if self.neuron_mode_index == 9 and serial_port.is_open:
                serial_port.write('NEU ' + str(IzhikevichNeurons[8][0]) +  ' ' + str(IzhikevichNeurons[8][1]) + ' ' +  str(IzhikevichNeurons[8][2]) + ' ' + str(IzhikevichNeurons[8][3]) + ' ' + str(IzhikevichNeurons[8][4]) + '\n')
            if self.neuron_mode_index == 10 and serial_port.is_open:
                serial_port.write('NEU ' + str(IzhikevichNeurons[9][0]) +  ' ' + str(IzhikevichNeurons[9][1]) + ' ' +  str(IzhikevichNeurons[9][2]) + ' ' + str(IzhikevichNeurons[9][3]) + ' ' + str(IzhikevichNeurons[9][4]) + '\n')
            if self.neuron_mode_index == 11 and serial_port.is_open:
                serial_port.write('NEU ' + str(IzhikevichNeurons[10][0]) +  ' ' + str(IzhikevichNeurons[10][1]) + ' ' +  str(IzhikevichNeurons[10][2]) + ' ' + str(IzhikevichNeurons[10][3]) + ' ' + str(IzhikevichNeurons[10][4]) + '\n')
            if self.neuron_mode_index == 12 and serial_port.is_open:
                serial_port.write('NEU ' + str(IzhikevichNeurons[11][0]) +  ' ' + str(IzhikevichNeurons[11][1]) + ' ' +  str(IzhikevichNeurons[11][2]) + ' ' + str(IzhikevichNeurons[11][3]) + ' ' + str(IzhikevichNeurons[11][4]) + '\n')
            if self.neuron_mode_index > 12 and serial_port.is_open:
                self.a_Izhi = self.ui.ImportNeuron[self.neuron_mode_index-13][0]
                self.b_Izhi = self.ui.ImportNeuron[self.neuron_mode_index-13][1]
                self.c_Izhi = self.ui.ImportNeuron[self.neuron_mode_index-13][2]
                self.d_Izhi = self.ui.ImportNeuron[self.neuron_mode_index-13][3]
                serial_port.write('NEU ' + str(self.a_Izhi) + ' ' + str(self.b_Izhi) + ' ' + str(self.c_Izhi) + ' ' + str(self.d_Izhi) + ' ' + '99' + '\n')

                self.PGain = self.ui.ImportNeuron[self.neuron_mode_index - 13][4]
                serial_port.write('PG1 ' + str(self.PGain) + '\n')
                self.PDecay = self.ui.ImportNeuron[self.neuron_mode_index - 13][5]
                serial_port.write('PD1 ' + str(self.PDecay) + '\n')
                self.PRecovery = self.ui.ImportNeuron[self.neuron_mode_index - 13][6]
                serial_port.write('PR1 ' + str(self.PRecovery) + '\n')

                self.Syn1Gain = self.ui.ImportNeuron[self.neuron_mode_index - 13][7]
                serial_port.write('SG11 ' + str(self.Syn1Gain) + '\n')
                self.Syn1Decay = self.ui.ImportNeuron[self.neuron_mode_index - 13][8]
                serial_port.write('SD11 ' + str(self.Syn1Decay) + '\n')

                self.Syn2Gain = self.ui.ImportNeuron[self.neuron_mode_index - 13][9]
                serial_port.write('SG12 ' + str(self.Syn2Gain) + '\n')
                self.Syn2Decay = self.ui.ImportNeuron[self.neuron_mode_index - 13][10]
                serial_port.write('SD12 ' + str(self.Syn2Decay) + '\n')




    def BrowseNeuron(self):
        FileName, _= QFileDialog.getOpenFileName(caption='Select Neuron',
                                                 dir="./Neurons",
                                                 filter='csv files (*.csv)')

        Df = pd.read_csv(FileName)
        self.df_Neuron_a = Df["a"]
        self.df_Neuron_b = Df["b"]
        self.df_Neuron_c = Df["c"]
        self.df_Neuron_d = Df["d"]

        self.df_Neuron_PGain = Df["PhotoGain (%)"]
        self.df_Neuron_PDecay = Df["PhotoDecay (1/ms)"]
        self.df_Neuron_PRecovery = Df["PhotoRecovery (1/ms)"]

        self.df_Neuron_Syn1Gain = Df["Syn1 Gain (%)"]
        self.df_Neuron_Syn1Decay = Df["Syn1 Decay (1/ms)"]

        self.df_Neuron_Syn2Gain = Df["Syn2 Gain (%)"]
        self.df_Neuron_Syn2Decay = Df["Syn2 Decay (1/ms)"]

        self.ParametersNeuron = [self.df_Neuron_a[0],
                                 self.df_Neuron_b[0],
                                 self.df_Neuron_c[0],
                                 self.df_Neuron_d[0],
                                 self.df_Neuron_PGain[0],
                                 self.df_Neuron_PDecay[0],
                                 self.df_Neuron_PRecovery[0],
                                 self.df_Neuron_Syn1Gain[0],
                                 self.df_Neuron_Syn1Decay[0],
                                 self.df_Neuron_Syn2Gain[0],
                                 self.df_Neuron_Syn2Decay[0]
                                 ]
        self.ui.ImportNeuron.append(self.ParametersNeuron)


        self.ui.Spikeling_NeuronModeComboBox.addItem('')
        self.neuron_count = self.ui.Spikeling_NeuronModeComboBox.count()
        self.filename = os.path.splitext(os.path.basename(QFileInfo(FileName).fileName()))[0]
        self.ui.Spikeling_NeuronModeComboBox.setItemText(self.neuron_count-1, self.filename)
        self.ui.Spikeling_NeuronModeComboBox.setCurrentIndex(self.neuron_count-1)
