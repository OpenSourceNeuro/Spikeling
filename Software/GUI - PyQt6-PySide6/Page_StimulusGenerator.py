
########################################################################
#                          Libraries import                            #

from PySide6.QtWidgets import QFileDialog

import numpy as np
import pandas as pd
from scipy import signal

from Parameters_Settings import DarkSolarized



def ShowPage(self):
    self.ui.mainbody_stackedWidget.setCurrentWidget(self.ui.page_501)
    self.ui.StimulusGenerator_Parameter_stackedWidget.setCurrentIndex(0)
    self.ui.StimulusGenerator_Selection_comboBox.setCurrentIndex(0)
    self.ui.StimulusGenerator_Oscilloscope_widget.clear()
    StimulusGenerator.SetGraph(self)

def ChangeStimulusParameter(self):
    self.StimulusIndex = self.ui.StimulusGenerator_Selection_comboBox.currentIndex()
    self.ui.StimulusGenerator_Parameter_stackedWidget.setCurrentIndex(self.StimulusIndex)

def ChangeChirpParameter(self):
    self.ChirpIndex = self.ui.Chirp_comboBox.currentIndex()

    if self.ChirpIndex == 0:
        self.ui.Chirp_Frequency_Value.setEnabled(False)
        self.ui.Chirp_Frequency_Value.setStyleSheet("background-color: rgb(80, 110, 117)" + ";\n"
                                                    "border : none;"
                                                    )
        self.ui.Chirp_StartFrequency_Value.setEnabled(True)
        self.ui.Chirp_StartFrequency_Value.setStyleSheet("background-color: rgb" + str(tuple(DarkSolarized[2])) + ";\n"
                                                         "border: 2px solid rgb" + str(tuple(DarkSolarized[14])) + ";\n"
                                                         )
        self.ui.Chirp_EndFrequency_Value.setEnabled(True)
        self.ui.Chirp_EndFrequency_Value.setStyleSheet("background-color: rgb" + str(tuple(DarkSolarized[2])) + ";\n"
                                                       "border: 2px solid rgb" + str(tuple(DarkSolarized[14])) + ";\n"
                                                       )
    if self.ChirpIndex == 1:
        self.ui.Chirp_Frequency_Value.setEnabled(False)
        self.ui.Chirp_Frequency_Value.setStyleSheet("background-color: rgb(80, 110, 117)" + ";\n"
                                                    "border : none;"
                                                    )
        self.ui.Chirp_StartFrequency_Value.setEnabled(True)
        self.ui.Chirp_StartFrequency_Value.setStyleSheet("background-color: rgb" + str(tuple(DarkSolarized[2])) + ";\n"
                                                         "border: 2px solid rgb" + str(tuple(DarkSolarized[14])) + ";\n"
                                                         )
        self.ui.Chirp_EndFrequency_Value.setEnabled(True)
        self.ui.Chirp_EndFrequency_Value.setStyleSheet("background-color: rgb" + str(tuple(DarkSolarized[2])) + ";\n"
                                                       "border: 2px solid rgb" + str(tuple(DarkSolarized[14])) + ";\n"
                                                       )
    if self.ChirpIndex == 2:
        self.ui.Chirp_Frequency_Value.setEnabled(True)
        self.ui.Chirp_Frequency_Value.setStyleSheet("background-color: rgb" + str(tuple(DarkSolarized[2])) + ";\n"
                                                    "border: 2px solid rgb" + str(tuple(DarkSolarized[14])) + ";\n"
                                                    )
        self.ui.Chirp_StartFrequency_Value.setEnabled(False)
        self.ui.Chirp_StartFrequency_Value.setStyleSheet("background-color: rgb(80, 110, 117)" + ";\n"
                                                         "border : none;"
                                                         )
        self.ui.Chirp_EndFrequency_Value.setEnabled(False)
        self.ui.Chirp_EndFrequency_Value.setStyleSheet("background-color: rgb(80, 110, 117)" + ";\n"
                                                       "border : none;"
                                                       )


class StimulusGenerator():

    def SetGraph(self):
        self.ui.StimulusGenerator_Oscilloscope_widget.showGrid(x=True, y=True)
        self.ui.StimulusGenerator_Oscilloscope_widget.setRange(yRange=[-100, 100])
        self.ui.StimulusGenerator_Oscilloscope_widget.setBackground(DarkSolarized[0])
        self.ui.StimulusGenerator_Oscilloscope_widget.setLabel('left', 'Stimulus Intensity', 'a.u.')
        self.ui.StimulusGenerator_Oscilloscope_widget.setLabel('bottom', 'time', 'ms')

    def DrawStimulus(self):
        self.StimulusIndex = self.ui.StimulusGenerator_Selection_comboBox.currentIndex()
        if self.StimulusIndex == 0:
            StimulusGenerator.IntensitySteps(self)
        if self.StimulusIndex == 1:
            StimulusGenerator.SineWave(self)
        if self.StimulusIndex == 2:
            StimulusGenerator.TriangularWave(self)
        if self.StimulusIndex == 3:
            StimulusGenerator.ChirpWave(self)


    def _ensure_csv_path(path: str) -> str:
        if not path:
            return ""
        return path if path.lower().endswith(".csv") else path + ".csv"


    def SaveStimulus(self):
        self.StimulusIndex = self.ui.StimulusGenerator_Selection_comboBox.currentIndex()
        if self.StimulusIndex == 0:
            StimulusGenerator.IntensityStepsSave(self)
        if self.StimulusIndex == 1:
            StimulusGenerator.SineWaveSave(self)
        if self.StimulusIndex == 2:
            StimulusGenerator.TriangularWaveSave(self)
        if self.StimulusIndex == 3:
            StimulusGenerator.ChirpWaveSave(self)


    def IntensitySteps(self):
        self.nStep = int(self.ui.Step_Number_Value.text())
        self.Increment = int(self.ui.Step_Increment_Value.text())
        self.FirstStep = int(self.ui.Step_First_Value.text())
        self.StepOn = int(self.ui.Step_On_Value.text())
        self.StepOff = int(self.ui.Step_Off_Value.text())
        self.iStepOff = int(self.ui.Step_OffInt_Value.text())
        self.tInter = int(self.ui.Step_Inter_Value.text())
        self.iInter = int(self.ui.Step_InterInt_Value.text())

        self.StepDur = self.StepOn + self.StepOff
        self.StimDur = self.StepDur * self.nStep + self.tInter
        self.xStep = np.zeros(self.StepDur)
        self.XStep = np.arange(self.StepDur)
        self.xStim = np.zeros(self.StimDur)
        self.XStim = np.arange(self.StimDur)

        self.ui.StimulusGenerator_Oscilloscope_widget.clear()

        for i in range(self.nStep):
            self.xStep[1 : self.StepOn] = self.FirstStep + i*self.Increment
            self.xStep[self.StepOn+1 :] = self.iStepOff
            self.xStim[i*self.StepDur : (i+1)*self.StepDur] = self.xStep[:]
            self.ui.StimulusGenerator_Oscilloscope_widget.plot(self.XStep, self.xStim[i*self.StepDur : (i+1)*self.StepDur], pen=(DarkSolarized[5]))


    def IntensityStepsSave(self):
        self.nStep = int(self.ui.Step_Number_Value.text())
        self.Increment = int(self.ui.Step_Increment_Value.text())
        self.FirstStep = int(self.ui.Step_First_Value.text())
        self.StepOn = int(self.ui.Step_On_Value.text())*10
        self.StepOff = int(self.ui.Step_Off_Value.text())*10
        self.iStepOff = int(self.ui.Step_OffInt_Value.text())
        self.tInter = int(self.ui.Step_Inter_Value.text())*10
        self.iInter = int(self.ui.Step_InterInt_Value.text())

        self.StepDur = self.StepOn + self.StepOff
        self.StimDur = self.StepDur * self.nStep + self.tInter
        self.nStim = np.zeros(self.StimDur)

        for i in range(self.nStep):
            self.nStim[i*self.StepDur : i*self.StepDur+self.StepOn] = self.FirstStep + i * self.Increment
            self.nStim[i*self.StepDur+self.StepOn : (i+1)*self.StepDur] = self.iStepOff
        self.nStim[self.StimDur-self.tInter : self.StimDur] = self.iInter

        self.nTrigger = np.zeros(self.StimDur)
        self.nTrigger[0] = 1

        FileName = QFileDialog.getSaveFileName(caption='Save Stimulus on screen',
                                               dir="./Stimuli",
                                               filter='csv files (*.csv)')

        self.dict_SineStim = { 'Stim': self.nStim, 'Trigger': self.nTrigger }
        self.df_SineStim = pd.DataFrame(self.dict_SineStim)

        self.df_SineStim.to_csv(FileName[0], index=False)

    def SineWave(self):
        self.Amplitude = int(self.ui.SineWave_Amplitude_Value.text())
        self.Frequency = int(self.ui.SineWave_Frequency_Value.text())
        self.Mean = int(self.ui.SineWave_Mean_Value.text())
        self.StimOn = int(self.ui.SineWave_StimOn_Value.text())
        self.StimOff = int(self.ui.SineWave_StimOff_Value.text())
        self.IntOff = int(self.ui.SineWave_IntOff_Value.text())

        self.StimDur = 2*self.StimOn + 2*self.StimOff
        self.nStim = np.zeros(self.StimDur)
        self.xStim = np.arange(self.StimDur)

        self.Sinex = np.arange(self.StimOn)
        self.Sinef = self.Frequency * self.StimOn / 1000
        self.Siney = np.sin(2 * np.pi * self.Sinef * self.Sinex / self.StimOn) * self.Amplitude + self.Mean

        self.nStim[0: self.StimOn] = self.Siney[0: self.StimOn]
        self.nStim[self.StimOn: self.StimOn + self.StimOff] = self.IntOff
        self.nStim[self.StimOn + self.StimOff: 2 * self.StimOn + self.StimOff] = self.Siney[0: self.StimOn]
        self.nStim[2 * self.StimOn + self.StimOff: 2 * self.StimOn + 2 * self.StimOff] = self.IntOff

        self.ui.StimulusGenerator_Oscilloscope_widget.clear()
        self.SineCurve = self.ui.StimulusGenerator_Oscilloscope_widget.plot(self.xStim, self.nStim, pen=(DarkSolarized[5]))


    def SineWaveSave(self):
        self.Amplitude = int(self.ui.SineWave_Amplitude_Value.text())
        self.Frequency = int(self.ui.SineWave_Frequency_Value.text())
        self.Mean = int(self.ui.SineWave_Mean_Value.text())
        self.StimOn = int(self.ui.SineWave_StimOn_Value.text())*10
        self.StimOff = int(self.ui.SineWave_StimOff_Value.text())*10
        self.IntOff = int(self.ui.SineWave_IntOff_Value.text())

        self.StimDur = self.StimOn + self.StimOff
        self.nStim = np.zeros(self.StimDur)
        self.xStim = np.arange(self.StimDur)

        self.Sinex = np.arange(self.StimOn)
        self.Sinef = self.Frequency * self.StimOn / 10000
        self.Siney = np.sin(2 * np.pi * self.Sinef * self.Sinex / self.StimOn) * self.Amplitude + self.Mean

        self.nStim[0: self.StimOn] = self.Siney[0: self.StimOn]
        self.nStim[self.StimOn: self.StimOn + self.StimOff] = self.IntOff

        self.nTrigger = np.zeros(self.StimDur)
        self.nTrigger[0] = 1


        FileName = QFileDialog.getSaveFileName(caption='Save Stimulus on screen',
                                               dir="./Stimuli",
                                               filter='csv files (*.csv)')

        self.dict_SineStim = { 'Stim': self.nStim, 'Trigger': self.nTrigger }
        self.df_SineStim = pd.DataFrame(self.dict_SineStim)

        self.df_SineStim.to_csv(FileName[0], index = False)



    def TriangularWave(self):
        self.StimOn = int(self.ui.TriangleWave_StimOn_Value.text())
        self.Frequency = int(self.ui.TriangleWave_Frequency_Value.text())
        self.Amplitude = int(self.ui.TriangleWave_Amplitude_Value.text())
        self.Mean = int(self.ui.TriangleWave_Mean_Value.text())
        self.StimOff = int(self.ui.TriangleWave_StimOff_Value.text())
        self.IntOff = int(self.ui.TriangleWave_IntOff_Value.text())

        self.StimDur = self.StimOn + self.StimOff
        self.xStim = np.linspace (0, self.StimOn, self.StimOn)
        self.f = self.Frequency / 1000 * self.xStim

        self.Triangle = signal.sawtooth( 2 * np.pi * self.f - np.pi*3/2, 0.5)

        self.nStim = np.zeros(2*self.StimDur)
        self.nStim[0: self.StimOn] = self.Amplitude*self.Triangle
        self.nStim[self.StimDur: self.StimDur+self.StimOn] = self.Amplitude*self.Triangle

        self.nStim[self.StimOn : self.StimDur] = self.IntOff
        self.nStim[self.StimDur + self.StimOn: 2*self.StimDur] = self.IntOff

        self.XStim = np.arange(2*self.StimDur)

        self.ui.StimulusGenerator_Oscilloscope_widget.clear()
        self.SineCurve = self.ui.StimulusGenerator_Oscilloscope_widget.plot(self.XStim, self.nStim, pen=(DarkSolarized[5]))


    def TriangularWaveSave(self):
        self.StimOn = int(self.ui.TriangleWave_StimOn_Value.text())*10
        self.Frequency = int(self.ui.TriangleWave_Frequency_Value.text())
        self.Amplitude = int(self.ui.TriangleWave_Amplitude_Value.text())
        self.Mean = int(self.ui.TriangleWave_Mean_Value.text())
        self.StimOff = int(self.ui.TriangleWave_StimOff_Value.text())*10
        self.IntOff = int(self.ui.TriangleWave_IntOff_Value.text())

        self.StimDur = self.StimOn + self.StimOff
        self.xStim = np.linspace(0, self.StimOn, self.StimOn)
        self.f = self.Frequency / 10000 * self.xStim

        self.Triangle = signal.sawtooth(2 * np.pi * self.f - np.pi * 3 / 2, 0.5)

        self.nStim = np.zeros(self.StimOn + self.StimOff)
        self.nStim[0: self.StimOn] = self.Amplitude * self.Triangle
        self.nStim[self.StimOn: self.StimDur] = self.IntOff

        self.nTrigger = np.zeros(self.StimDur)
        self.nTrigger[0] = 1

        FileName = QFileDialog.getSaveFileName(caption='Save Stimulus on screen',
                                               dir="./Stimuli",
                                               filter='csv files (*.csv)')

        self.dict_TriangleStim = { 'Stim': self.nStim, 'Trigger': self.nTrigger }
        self.df_TriangleStim = pd.DataFrame(self.dict_TriangleStim)

        self.df_TriangleStim.to_csv(FileName[0], index=False)



    def ChirpWave(self):
        self.ChirpAmplitude = int(self.ui.Chirp_Amplitude_Value.text())
        self.OnAmplitude = int(self.ui.Chirp_PreChirpOn_Amplitude_Value.text())
        self.OnDuration = int(self.ui.Chirp_PreChirpOn_Duration_Value.text())
        self.OffAmplitude = int(self.ui.Chirp_PreChirpOff_Amplitude_Value.text())
        self.OffDuration = int(self.ui.Chirp_PreChirpOff_Duration_Value.text())
        self.MidAmplitude = int(self.ui.Chirp_PreChirpMid_Amplitude.text())
        self.MidDuration = int(self.ui.Chirp_PreChirpMid_Duration.text())
        self.ChirpFrequency = int(self.ui.Chirp_Frequency_Value.text())/1000
        self.StartFrequency = int(self.ui.Chirp_StartFrequency_Value.text())/1000
        self.EndFrequency = int(self.ui.Chirp_EndFrequency_Value.text())/1000
        self.ChirpDuration = int(self.ui.Chirp_Duration_Value.text())

        self.StimDur = self.OnDuration + self.OffDuration + self.MidDuration + self.ChirpDuration

        self.ChirpTime = np.linspace(0, self.ChirpDuration, self.ChirpDuration)


        self.ChirpIndex = self.ui.Chirp_comboBox.currentIndex()

        if self.ChirpIndex == 0:
            self.ChirpModulation = np.linspace(self.StartFrequency, self.EndFrequency, self.ChirpDuration)
            self.ChirpSinusoid = np.sin(self.ChirpTime * self.ChirpModulation) * self.ChirpAmplitude/2 + self.MidAmplitude
            self.Chirp = np.around(self.ChirpSinusoid).astype(int)
            self.Modulation = np.zeros(self.StimDur)
            for i in range(self.ChirpDuration):
                self.Modulation[self.OnDuration + self.OffDuration + self.MidDuration + i] = self.ChirpModulation[i]/self.EndFrequency*100

        if self.ChirpIndex == 1:
            self.ChirpModulation = np.exp(np.linspace(self.StartFrequency*1000, np.log(self.EndFrequency*1000), self.ChirpDuration))/1000
            self.ChirpSinusoid = np.sin(self.ChirpTime * self.ChirpModulation) * self.ChirpAmplitude/2 + self.MidAmplitude
            self.Chirp = np.around(self.ChirpSinusoid).astype(int)
            self.Modulation = np.zeros(self.StimDur)
            for i in range(self.ChirpDuration):
                self.Modulation[self.OnDuration + self.OffDuration + self.MidDuration + i] = self.ChirpModulation[i] / self.EndFrequency * 100

        if self.ChirpIndex == 2:
            self.ChirpModulation = np.linspace(0, self.ChirpAmplitude/2, self.ChirpDuration)
            self.ChirpSinusoid = np.sin(self.ChirpTime * self.ChirpFrequency) * self.ChirpModulation + self.MidAmplitude
            self.Chirp = np.around(self.ChirpSinusoid).astype(int)
            self.Modulation = np.zeros(self.StimDur)
            for i in range(self.ChirpDuration):
                self.Modulation[self.OnDuration + self.OffDuration + self.MidDuration + i] = self.ChirpModulation[i] * 2


        self.XStim = np.arange(self.StimDur)
        self.nStim = np.zeros(self.StimDur)
        self.nChirp = np.zeros(self.StimDur)
        self.nStim[:self.OnDuration] = self.OnAmplitude
        self.nStim[self.OnDuration:self.OnDuration+self.OffDuration] = self.OffAmplitude
        self.nStim[self.OnDuration+self.OffDuration:self.OnDuration+self.OffDuration+self.MidDuration] = self.MidAmplitude

        for i in range (self.ChirpDuration):
            self.nStim[self.OnDuration+self.OffDuration+self.MidDuration+i] = self.Chirp[i]
            self.nChirp[self.OnDuration + self.OffDuration + self.MidDuration + i] = self.ChirpModulation[i]

        self.ui.StimulusGenerator_Oscilloscope_widget.clear()
        self.SineCurve = self.ui.StimulusGenerator_Oscilloscope_widget.plot(self.XStim, self.nStim,pen=(DarkSolarized[5]))
        self.ChirpCurve = self.ui.StimulusGenerator_Oscilloscope_widget.plot(self.XStim, self.Modulation,pen=(DarkSolarized[7]))


    def ChirpWaveSave(self):
        self.ChirpAmplitude = int(self.ui.Chirp_Amplitude_Value.text())
        self.OnAmplitude = int(self.ui.Chirp_PreChirpOn_Amplitude_Value.text())
        self.OnDuration = int(self.ui.Chirp_PreChirpOn_Duration_Value.text())
        self.OffAmplitude = int(self.ui.Chirp_PreChirpOff_Amplitude_Value.text())
        self.OffDuration = int(self.ui.Chirp_PreChirpOff_Duration_Value.text())
        self.MidAmplitude = int(self.ui.Chirp_PreChirpMid_Amplitude.text())
        self.MidDuration = int(self.ui.Chirp_PreChirpMid_Duration.text())

        # Keep the same unit conventions as ChirpWave():
        # UI frequency in Hz -> divide by 1000 so it combines with time in ms in your current formulation.
        self.ChirpFrequency = int(self.ui.Chirp_Frequency_Value.text()) / 1000
        self.StartFrequency = int(self.ui.Chirp_StartFrequency_Value.text()) / 1000
        self.EndFrequency = int(self.ui.Chirp_EndFrequency_Value.text()) / 1000

        self.ChirpDuration = int(self.ui.Chirp_Duration_Value.text())

        # Saved stimuli use *10 samples per ms elsewhere in the file
        self.OnDuration_s = self.OnDuration * 10
        self.OffDuration_s = self.OffDuration * 10
        self.MidDuration_s = self.MidDuration * 10
        self.ChirpDuration_s = self.ChirpDuration * 10

        self.StimDur = self.OnDuration_s + self.OffDuration_s + self.MidDuration_s + self.ChirpDuration_s

        # Time base for the chirp segment (same style as your current save attempt)
        self.ChirpTime = np.linspace(0, self.ChirpDuration, self.ChirpDuration_s)

        self.ChirpIndex = self.ui.Chirp_comboBox.currentIndex()

        # --- Generate chirp segment (match ChirpWave() modes, but at *10 sampling) ---
        if self.ChirpIndex == 0:
            # Linear frequency sweep
            self.ChirpModulation = np.linspace(self.StartFrequency, self.EndFrequency, self.ChirpDuration_s)
            self.ChirpSinusoid = np.sin(self.ChirpTime * self.ChirpModulation) * self.ChirpAmplitude/2 + self.MidAmplitude
            self.Chirp = np.around(self.ChirpSinusoid).astype(int)

        elif self.ChirpIndex == 1:
            # Exponential/log-like sweep (robust version)
            # If StartFrequency <= 0, fall back to linear to avoid log issues
            if self.StartFrequency > 0 and self.EndFrequency > 0:
                self.ChirpModulation = np.exp(
                    np.linspace(np.log(self.StartFrequency), np.log(self.EndFrequency), self.ChirpDuration_s)
                )
            else:
                self.ChirpModulation = np.linspace(self.StartFrequency, self.EndFrequency, self.ChirpDuration_s)

            self.ChirpSinusoid = np.sin(self.ChirpTime * self.ChirpModulation) * self.ChirpAmplitude/2 + self.MidAmplitude
            self.Chirp = np.around(self.ChirpSinusoid).astype(int)

        else:
            # Mode 2: amplitude modulation at fixed frequency
            self.ChirpModulation = np.linspace(0, self.ChirpAmplitude/2, self.ChirpDuration_s)
            self.ChirpSinusoid = np.sin(self.ChirpTime * self.ChirpFrequency) * self.ChirpModulation + self.MidAmplitude
            self.Chirp = np.around(self.ChirpSinusoid).astype(int)

        # --- Assemble full stimulus ---
        self.nStim = np.zeros(self.StimDur)
        self.nStim[:self.OnDuration_s] = self.OnAmplitude
        self.nStim[self.OnDuration_s : self.OnDuration_s + self.OffDuration_s] = self.OffAmplitude
        self.nStim[self.OnDuration_s + self.OffDuration_s : self.OnDuration_s + self.OffDuration_s + self.MidDuration_s] = self.MidAmplitude

        chirp_start = self.OnDuration_s + self.OffDuration_s + self.MidDuration_s
        self.nStim[chirp_start : chirp_start + self.ChirpDuration_s] = self.Chirp

        # Trigger (same convention as the others)
        self.nTrigger = np.zeros(self.StimDur)
        self.nTrigger[0] = 1

        FileName = QFileDialog.getSaveFileName(caption='Save Stimulus on screen',
                                               dir="./Stimuli",
                                               filter='csv files (*.csv)')


        self.dict_ChirpStim = {'Stim': self.nStim, 'Trigger': self.nTrigger}
        self.df_ChirpStim = pd.DataFrame(self.dict_ChirpStim)

        self.df_ChirpStim.to_csv(FileName[0], index=False)

