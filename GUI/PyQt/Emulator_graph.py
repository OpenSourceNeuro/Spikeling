
########################################################################
#                          Libraries import                            #

from PySide6.QtCore import QTimer
import pyqtgraph as pg

import collections
import numpy as np
import pandas as pd

import Settings
import Imaging_graph


Emulator_downsampling = 10
Emulator_sampleinterval = 0.1
Emulator_timewindow = 5000
Emulator_timewindowdisplay = 500
penwidth = 1

def EmulatorPlot(self):
    if self.ui.Emulator_Connect_pushButton.isChecked():
        SetInitParameters(self)
        SetPlotCurve(self)
        SetPlot(self)

        # QTimer for emulator GUI updates
        self.timer = QTimer()
        self.timer.timeout.connect(lambda: UpdatePlot(self))
        self.timer.start(50)

    else:
        self.ui.Emulator_Connect_pushButton.setText("Start Spikeling Emulator")
        self.ui.Emulator_Connect_pushButton.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[14])) + ";\n"
                                                          "background-color: rgb" + str(tuple(Settings.DarkSolarized[2])) + ";\n"
                                                          "border: 1px solid rgb" + str(tuple(Settings.DarkSolarized[14])) + ";\n"
                                                          "border-radius: 10px;"
                                                          )
        if hasattr(self, "timer"):
            self.timer.stop()
        self.ui.Emulator_Oscilloscope_widget.clear()
        if hasattr(self, "Emulator_CurrentPlots"):
            self.Emulator_CurrentPlots.clear()
        self.ui.EmulatorConnectedFlag = False


    # -----------------------------------------------------------------
    # Nested update function: runs at each QTimer tick
    # -----------------------------------------------------------------
    def UpdatePlot(self):
        """
        Advance the emulator and update the graph.

        The Emulator_Speed_slider (0–5) controls how many simulation
        timesteps (dt = 0.1 ms) we execute for each QTimer tick.
        """

        # 1) Map slider value -> how many simulation steps per GUI update
        speed_step = self.ui.Emulator_Speed_slider.value()

        steps_per_update_lookup = [10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000]
        steps_per_update = steps_per_update_lookup[speed_step]
        DT_Display = round(steps_per_update / 10000, 3)
        self.ui.Emulator_Speed_value.setText("x " + str(DT_Display))

        # 2) Run several simulation steps before we redraw
        imaging_batch = []  # list of 9-field packets for imaging

        # Resolve imaging_graph once per tick
        imaging_graph = getattr(self, "imaging_graph", None)
        imaging_enabled = (
                imaging_graph is not None
                and getattr(self, "ImagingConnectionFlag", False)
                and imaging_graph.source_mode == "emulator"
        )

        for _ in range(steps_per_update):
            vec8 = GetData(self)  # [Vm0, Stim, Itot, Vm1, ISyn1, Vm2, ISyn2, Trigger]
            self.ui.Emulator_Data = vec8

            BuffData(self)
            SavePlotData(self)

            if imaging_enabled:
                # 9-field: [t_ms, Vm0, Stim, Itot, Vm1, ISyn1, Vm2, ISyn2, Trigger]
                pkt9 = [self.Emulator_sim_time_ms] + list(vec8)
                imaging_batch.append(pkt9)

        # 3) Plot only once per GUI update (using the latest buffer contents)
        PlotCurve(self)

        # 4) Forward the whole batch once per GUI tick
        if imaging_batch:
            imaging_graph.on_emulator_data(imaging_batch)

    # Read Serial and return data array (7)
    def GetData(self):

        # Get Izhikevich variables
        ################################################################
        Emulator_a = self.ui.Emulator_a
        Emulator_b = self.ui.Emulator_b
        Emulator_c = self.ui.Emulator_c
        Emulator_d = self.ui.Emulator_d


        # Generate Vm
        ################################################################

        self.Emulator_v = self.Emulator_v + self.Emulator_timestep_ms * ( 0.04 * self.Emulator_v * self.Emulator_v + 5.0 * self.Emulator_v + 140.0 - self.Emulator_u + self.Emulator_TotalCurrent_Data )
        self.Emulator_u = self.Emulator_u + self.Emulator_timestep_ms * ( Emulator_a * (Emulator_b * self.Emulator_v - self.Emulator_u) )

        if self.Emulator_v >= self.Emulator_v_thresh:
            self.Emulator_v = Emulator_c
            self.Emulator_u = self.Emulator_u + Emulator_d

        if self.Emulator_v < self.Emulator_v_min:
            self.Emulator_v = self.Emulator_v_min

        if self.Emulator_v >= 0:
            self.Emulator_v = self.Emulator_v_peak

        self.Emulator_Vm_Data = self.Emulator_v


        # Generate Stimulus State
        ################################################################

        self.Emulator_Trigger = 0

        use_custom_stim = (
                self.ui.EmulatorStimCus_toggleButton.isChecked()
                and hasattr(self.ui, "Emulatordf_yStim")
                and len(self.ui.Emulatordf_yStim) > 0
        )

        if use_custom_stim:
            if getattr(self.ui, "StimCus_Flag", False):
                self.EmulatorCusStimCounter = 0
                self.Emulator_Trigger = 1
                self.ui.StimCus_Flag = False

            # Safe wrap-around
            if self.EmulatorCusStimCounter >= len(self.ui.Emulatordf_yStim):
                self.EmulatorCusStimCounter = 0
                self.Emulator_Trigger = 1

            self.EmulatorStimCusValue = self.ui.Emulatordf_yStim[self.EmulatorCusStimCounter]
            self.EmulatorCusStimCounter += 1

            self.Emulator_Stimulus_Data = float(self.EmulatorStimCusValue)

        else:
            # Fallback to internal square-pulse generator
            self.Emulator_StimulusStrength_Value = self.ui.Emulator_StimStrSlider.value()
            self.Emulator_StimulusFrequency_Value = self.ui.Emulator_StimFre_slider.value() * (-1)

            if self.Emulator_StimCounter < self.Emulator_StimSteps / 2:
                self.Emulator_Stimulus_Data = self.Emulator_StimulusStrength_Value
            else:
                self.Emulator_Stimulus_Data = 0.0

            self.Emulator_StimCounter += 1

            if self.Emulator_StimCounter >= self.Emulator_StimSteps:
                self.Emulator_StimCounter = 0
                self.Emulator_Trigger = 1
                self.Emulator_StimSteps = int(np.round(self.Emulator_Stim_DutyCycle * (10 ** ( self.Emulator_StimulusFrequency_Value / 100.0))))


        #Generate TotalCurrent Input
        ################################################################

        #PatchClamp
        self.Emulator_InputCurrent_Value = self.ui.Emulator_PatchClamp_slider.value()


        #Noise
        self.Emulator_NoiseSlider = self.ui.Emulator_Noise_slider.value()
        self.Emulator_Noise_Value = np.random.normal(0, self.Emulator_NoiseSlider/4)


        #Photodiode
        if self.ui.EmulatorStimChoiceLight_toggleButton.isChecked():
            self.Emulator_I_Photodiode = self.Emulator_Stimulus_Data/25

            self.Emulator_Photodiode_Gain = self.ui.Emulator_PR_PhotoGain_slider.value()
            if self.Emulator_Photodiode_Gain >= 0:
                self.Emulator_Photodiode_Polarity = 1
            else:
                self.Emulator_Photodiode_Polarity = -1

            self.Emulator_Photodiode_Value = self.Emulator_I_Photodiode * self.Emulator_Photodiode_Gain/0.5 * self.Photodiode_Recovery

            if self.Photodiode_Recovery > 0.0:
                self.Photodiode_Recovery  -= self.Emulator_Photodiode_Polarity * self.Photodiode_Decay_value * self.Emulator_Photodiode_Value
            if self.Photodiode_Recovery < 0.0:
                self.Photodiode_Recovery = 0.0

            if self.Photodiode_Recovery < 1.0:
                self.Photodiode_Recovery += self.Photodiode_Recovery_value

            self.Photodiode_Decay_value = self.ui.Emulator_PR_Decay_slider.value() / 100000.0

            self.Photodiode_Recovery_value = self.ui.Emulator_PR_Recovery_slider.value() / 1000.0


        else:
            self.Emulator_Photodiode_Value = 0.0



        # Direct Current
        ################################################################
        if self.ui.EmulatorStimChoiceCurrent_toggleButton.isChecked():
            self.Emulator_DirectCurrent_Value = self.Emulator_Stimulus_Data
        else:
            self.Emulator_DirectCurrent_Value = 0.0






        ################################################################
        ################################################################
        # Synapse 1
        ################################################################
        ################################################################

        if self.ui.EmulatorSyn1_Synapse_toggleButton.isChecked():

            # Get Izhikevich variables
            ################################################################
            Emulator_a1 = self.ui.Emulator_a1
            Emulator_b1 = self.ui.Emulator_b1
            Emulator_c1 = self.ui.Emulator_c1
            Emulator_d1 = self.ui.Emulator_d1


            # PatchClamp
            ################################################################
            self.Emulator_Syn1_PatchClampCurrent_Value = self.ui.Emulator_Syn1_PatchClamp_slider.value()

            # Noise
            ################################################################

            self.Emulator_Syn1_NoiseSlider_Value = self.ui.Emulator_Syn1_Noise_slider.value()
            self.Emulator_Syn1_NoiseCurrent_Value = np.random.normal(0, self.Emulator_Syn1_NoiseSlider_Value / 4)

            # Generate Vm for synapse 1
            ################################################################

            self.Emulator_v1 = self.Emulator_v1 + self.Emulator_timestep_ms * (0.04 * self.Emulator_v1 * self.Emulator_v1 + 5.0 * self.Emulator_v1 + 140.0 - self.Emulator_u1 + self.Emulator_TotalCurrent1_Data)
            self.Emulator_u1 = self.Emulator_u1 + self.Emulator_timestep_ms * (Emulator_a1 * (Emulator_b1 * self.Emulator_v1 - self.Emulator_u1))

            if self.Emulator_v1 >= self.Emulator_v_thresh:
                self.Emulator_v1 = Emulator_c1
                self.Emulator_u1 = self.Emulator_u1 + Emulator_d1

            if self.Emulator_v1 < self.Emulator_v_min:
                self.Emulator_v1 = self.Emulator_v_min

            if self.Emulator_v1 >= 0:
                self.Emulator_v1 = self.Emulator_v_peak
                self.Emulator_Spike1 = True

            self.Emulator_Vm_Data1 = self.Emulator_v1

            # DirectCurrent Input for Synapse 1
            #################################################################
            if self.ui.EmulatorSyn1_StimDC_toggleButton.isChecked():
                self.Emulator_Syn1_DirectCurrent_Value = self.Emulator_Stimulus_Data
            else:
                self.Emulator_Syn1_DirectCurrent_Value = 0.0

            # Light Stimulation for Synapse 1
            #################################################################
            if self.ui.EmulatorSyn1_StimLight_toggleButton.isChecked():

                self.EmulatorSyn1_I_Photodiode = self.Emulator_Stimulus_Data / 25

                self.EmulatorSyn1_Photodiode_Gain = self.ui.Emulator_Syn1_PR_PhotoGain_slider.value()
                if self.EmulatorSyn1_Photodiode_Gain >= 0:
                    self.EmulatorSyn1_Photodiode_Polarity = 1
                else:
                    self.EmulatorSyn1_Photodiode_Polarity = -1

                self.EmulatorSyn1_Photodiode_Value = self.EmulatorSyn1_I_Photodiode * self.EmulatorSyn1_Photodiode_Gain / 0.5 * self.EmulatorSyn1_Photodiode_Recovery

                if self.EmulatorSyn1_Photodiode_Recovery > 0.0:
                    self.EmulatorSyn1_Photodiode_Recovery -= self.EmulatorSyn1_Photodiode_Polarity * self.EmulatorSyn1_Photodiode_Decay_value * self.EmulatorSyn1_Photodiode_Value
                if self.EmulatorSyn1_Photodiode_Recovery < 0.0:
                    self.EmulatorSyn1_Photodiode_Recovery = 0.0

                if self.EmulatorSyn1_Photodiode_Recovery < 1.0:
                    self.EmulatorSyn1_Photodiode_Recovery += self.EmulatorSyn1_Photodiode_Recovery_value

                self.EmulatorSyn1_Photodiode_Decay_value = self.ui.Emulator_Syn1_PR_Decay_slider.value() / 100000.0
                self.EmulatorSyn1_Photodiode_Recovery_value = self.ui.Emulator_Syn1_PR_Recovery_slider.value() / 1000.0

            else:
                self.EmulatorSyn1_Photodiode_Value = 0.0


            # Collect variables for synapse 1
            ################################################################
            self.Emulator_Syn1_Gain = self.ui.Emulator_Synapse1_slider.value()
            self.Emulator_Syn1_Decay = self.ui.Emulator_Synapse1_Decay_slider.value() / 1000.0


            # When a spike comes from synapse 1
            ################################################################
            if self.Emulator_Spike1 == True:
                self.Emulator_Syn1Input_Data += self.Emulator_Syn1_Gain
                self.Emulator_Spike1 = False

            self.Emulator_Syn1Input_Data *= self.Emulator_Syn1_Decay

            self.Emulator_TotalCurrent1_Data = self.Emulator_Syn1_PatchClampCurrent_Value + self.Emulator_Syn1_NoiseCurrent_Value + self.Emulator_Syn1_DirectCurrent_Value + self.EmulatorSyn1_Photodiode_Value


        else:
            self.Emulator_Vm_Data1 = 0.0
            self.Emulator_Syn1Input_Data = 0.0

        ################################################################
        ################################################################
        # Synapse 2
        ################################################################
        ################################################################

        if self.ui.EmulatorSyn2_Synapse_toggleButton.isChecked():

            # Get Izhikevich variables
            ################################################################
            Emulator_a2 = self.ui.Emulator_a2
            Emulator_b2 = self.ui.Emulator_b2
            Emulator_c2 = self.ui.Emulator_c2
            Emulator_d2 = self.ui.Emulator_d2

            # PatchClamp for synapse 2
            ################################################################
            self.Emulator_Syn2_PatchClampCurrent_Value = self.ui.Emulator_Syn2_PatchClamp_slider.value()

            # Noise for synapse 2
            ################################################################
            self.Emulator_Syn2_NoiseSlider_Value = self.ui.Emulator_Syn2_Noise_slider.value()
            self.Emulator_Syn2_NoiseCurrent_Value = np.random.normal(0, self.Emulator_Syn2_NoiseSlider_Value / 4)


            # Generate Vm for synapse 2
            ################################################################

            self.Emulator_v2 = self.Emulator_v2 + self.Emulator_timestep_ms * (0.04 * self.Emulator_v2 * self.Emulator_v2 + 5.0 * self.Emulator_v2 + 140.0 - self.Emulator_u2 + self.Emulator_TotalCurrent2_Data)
            self.Emulator_u2 = self.Emulator_u2 + self.Emulator_timestep_ms * (Emulator_a2 * (Emulator_b2 * self.Emulator_v2 - self.Emulator_u2))

            if self.Emulator_v2 >= self.Emulator_v_thresh:
                self.Emulator_v2 = Emulator_c2
                self.Emulator_u2 = self.Emulator_u2 + Emulator_d2

            if self.Emulator_v2 < self.Emulator_v_min:
                self.Emulator_v2 = self.Emulator_v_min

            if self.Emulator_v2 >= 0:
                self.Emulator_v2 = self.Emulator_v_peak
                self.Emulator_Spike2 = True

            self.Emulator_Vm_Data2 = self.Emulator_v2

            # DirectCurrent Input for Synapse 2
            #################################################################
            if self.ui.EmulatorSyn2_StimDC_toggleButton.isChecked():
                self.Emulator_Syn2_DirectCurrent_Value = self.Emulator_Stimulus_Data
            else:
                self.Emulator_Syn2_DirectCurrent_Value = 0.0

            # Light Stimulation for Synapse 2
            #################################################################
            if self.ui.EmulatorSyn2_StimLight_toggleButton.isChecked():

                self.EmulatorSyn2_I_Photodiode = self.Emulator_Stimulus_Data / 25

                self.EmulatorSyn2_Photodiode_Gain = self.ui.Emulator_Syn2_PR_PhotoGain_slider.value()
                if self.EmulatorSyn2_Photodiode_Gain >= 0:
                    self.EmulatorSyn2_Photodiode_Polarity = 1
                else:
                    self.EmulatorSyn2_Photodiode_Polarity = -1

                self.EmulatorSyn2_Photodiode_Value = self.EmulatorSyn2_I_Photodiode * self.EmulatorSyn2_Photodiode_Gain / 0.5 * self.EmulatorSyn2_Photodiode_Recovery

                if self.EmulatorSyn2_Photodiode_Recovery > 0.0:
                    self.EmulatorSyn2_Photodiode_Recovery -= self.EmulatorSyn2_Photodiode_Polarity * self.EmulatorSyn2_Photodiode_Decay_value * self.EmulatorSyn2_Photodiode_Value
                if self.EmulatorSyn2_Photodiode_Recovery < 0.0:
                    self.EmulatorSyn2_Photodiode_Recovery = 0.0

                if self.EmulatorSyn2_Photodiode_Recovery < 1.0:
                    self.EmulatorSyn2_Photodiode_Recovery += self.EmulatorSyn2_Photodiode_Recovery_value

                self.EmulatorSyn2_Photodiode_Decay_value = self.ui.Emulator_Syn2_PR_Decay_slider.value() / 100000.0
                self.EmulatorSyn2_Photodiode_Recovery_value = self.ui.Emulator_Syn2_PR_Recovery_slider.value() / 1000.0


            else:
                self.EmulatorSyn2_Photodiode_Value = 0.0

            # Collect variables for synapse 2
            ################################################################
            self.Emulator_Syn2_Gain = self.ui.Emulator_Synapse2_slider.value()
            self.Emulator_Syn2Decay = self.ui.Emulator_Synapse2_Decay_slider.value() / 1000.0


            # When a spike comes from synapse 2
            ################################################################
            if self.Emulator_Spike2 == True:
                self.Emulator_Syn2Input_Data += self.Emulator_Syn2_Gain
                self.Emulator_Spike2 = False

            self.Emulator_Syn2Input_Data *= self.Emulator_Syn2_Decay

            self.Emulator_TotalCurrent2_Data = self.Emulator_Syn2_PatchClampCurrent_Value + self.Emulator_Syn2_NoiseCurrent_Value + self.Emulator_Syn2_DirectCurrent_Value + self.EmulatorSyn2_Photodiode_Value


        else:
            self.Emulator_Vm_Data2 = 0.0
            self.Emulator_Syn2Input_Data = 0.0




        self.Emulator_TotalCurrent_Data = self.Emulator_InputCurrent_Value + self.Emulator_Noise_Value + self.Emulator_Photodiode_Value + self.Emulator_DirectCurrent_Value + self.Emulator_Syn1Input_Data + self.Emulator_Syn2Input_Data




        self.ui.Emulator_data = []
        self.ui.Emulator_data.append(self.Emulator_Vm_Data)
        self.ui.Emulator_data.append(self.Emulator_Stimulus_Data)
        self.ui.Emulator_data.append(self.Emulator_TotalCurrent_Data)
        self.ui.Emulator_data.append(self.Emulator_Vm_Data1)
        self.ui.Emulator_data.append(self.Emulator_Syn1Input_Data)
        self.ui.Emulator_data.append(self.Emulator_Vm_Data2)
        self.ui.Emulator_data.append(self.Emulator_Syn2Input_Data)
        self.ui.Emulator_data.append(self.Emulator_Trigger)

        # advance simulation clock by one integration step
        self.Emulator_sim_time_ms += self.Emulator_timestep_ms  # 0.1 ms

        return [
            self.Emulator_Vm_Data,
            self.Emulator_Stimulus_Data,
            self.Emulator_TotalCurrent_Data,
            self.Emulator_Vm_Data1,
            self.Emulator_Syn1Input_Data,
            self.Emulator_Vm_Data2,
            self.Emulator_Syn2Input_Data,
            self.Emulator_Trigger,
        ]

    # Append latest serial data point into buffer deque
    def BuffData(self):
        self.Emulator_databuffer0.append(self.ui.Emulator_Data[0])
        self.Emulator_databuffer1.append(self.ui.Emulator_Data[1])
        self.Emulator_databuffer2.append(self.ui.Emulator_Data[2])
        self.Emulator_databuffer3.append(self.ui.Emulator_Data[3])
        self.Emulator_databuffer4.append(self.ui.Emulator_Data[4])
        self.Emulator_databuffer5.append(self.ui.Emulator_Data[5])
        self.Emulator_databuffer6.append(self.ui.Emulator_Data[6])
        self.Emulator_databuffer7.append(self.ui.Emulator_Data[7])



    # If checked, plot latest buffer data points
    def PlotCurve(self):
        if self.ui.Emulator_VmCheckbox.isChecked():
            self.Emulator_y0[:] = self.Emulator_databuffer0
            self.Emulator_curve0.setData(self.Emulator_x, self.Emulator_y0)
            self.Emulator_curve0.setVisible(True)
        else:
            self.Emulator_curve0.setVisible(False)

        if self.ui.Emulator_StimulusCheckbox.isChecked():
            self.Emulator_y1[:] = self.Emulator_databuffer1
            self.Emulator_curve1.setData(self.Emulator_x, self.Emulator_y1)
            self.Emulator_curve1.setVisible(True)
        else:
            self.Emulator_curve1.setVisible(False)

        if self.ui.Emulator_InputCurrentCheckbox.isChecked():
            self.Emulator_y2[:] = self.Emulator_databuffer2
            self.Emulator_curve2.setData(self.Emulator_x, self.Emulator_y2)
            self.Emulator_curve2.setVisible(True)
        else:
            self.Emulator_curve2.setVisible(False)

        if self.ui.Emulator_Syn1VmCheckbox.isChecked():
            self.Emulator_y3[:] = self.Emulator_databuffer3
            self.Emulator_curve3.setData(self.Emulator_x, self.Emulator_y3)
            self.Emulator_curve3.setVisible(True)
        else:
            self.Emulator_curve3.setVisible(False)

        if self.ui.Emulator_Syn1InputCheckbox.isChecked():
            self.Emulator_y4[:] = self.Emulator_databuffer4
            self.Emulator_curve4.setData(self.Emulator_x, self.Emulator_y4)
            self.Emulator_curve4.setVisible(True)
        else:
            self.Emulator_curve4.setVisible(False)

        if self.ui.Emulator_Syn2VmCheckbox.isChecked():
            self.Emulator_y5[:] = self.Emulator_databuffer5
            self.Emulator_curve5.setData(self.Emulator_x, self.Emulator_y5)
            self.Emulator_curve5.setVisible(True)
        else:
            self.Emulator_curve5.setVisible(False)

        if self.ui.Emulator_Syn2InputCheckbox.isChecked():
            self.Emulator_y6[:] = self.Emulator_databuffer6
            self.Emulator_curve6.setData(self.Emulator_x, self.Emulator_y6)
            self.Emulator_curve6.setVisible(True)
        else:
            self.Emulator_curve6.setVisible(False)




def SavePlotData(self):
    # Stop recording -> write out CSV
    if (not self.ui.Emulator_DataRecording_Record_pushButton.isChecked()
            and getattr(self, "recordflag", False)):

        if len(self.EmulatorData[1]) == 0:
            self.recordflag = False
            return

        n = len(self.EmulatorData[1])
        Dataset = np.empty((9, n), dtype=float)

        # time axis
        Dataset[0] = np.arange(n, dtype=float) * Emulator_sampleinterval

        for j in range(1, 9):
            Dataset[j] = np.array(self.EmulatorData[j], dtype=float)

        df = pd.DataFrame({
            'Time (ms)': Dataset[0],
            'Spikeling Vm (mV)': Dataset[1],
            'Stimulus (%)': Dataset[2],
            'Total Current Input (a.u.)': Dataset[3],
            'Synapse 1 Vm (mV)': Dataset[4],
            'Synapse 1 Input (a.u.)': Dataset[5],
            'Synapse 2 Vm (mV)': Dataset[6],
            'Synapse 2 Input (a.u.)': Dataset[7],
            'Trigger': Dataset[8],
        })

        self.Emulator_RecordingFileName = str(self.ui.Emulator_SelectedFolderLabel.text())
        df.to_csv(self.Emulator_RecordingFileName + ".csv", index=False)

        # reset state
        self.recordflag = False
        for row in self.EmulatorData:
            row.clear()

    # While recording, append latest values
    if self.ui.Emulator_DataRecording_Record_pushButton.isChecked():
        self.recordflag = True
        self.EmulatorData[1].append(self.Emulator_databuffer0[-1])
        self.EmulatorData[2].append(self.Emulator_databuffer1[-1])
        self.EmulatorData[3].append(self.Emulator_databuffer2[-1])
        self.EmulatorData[4].append(self.Emulator_databuffer3[-1])
        self.EmulatorData[5].append(self.Emulator_databuffer4[-1])
        self.EmulatorData[6].append(self.Emulator_databuffer5[-1])
        self.EmulatorData[7].append(self.Emulator_databuffer6[-1])
        self.EmulatorData[8].append(self.Emulator_databuffer7[-1])


def SetInitParameters(self):
    self.ui.EmulatorConnectedFlag = True
    self.recordflag = False
    self.Trigger = 0
    self.Emulator_sim_time_ms = 0.0
    self.ui.Emulator_Oscilloscope_widget.clear()
    if self.ui.Emulator_Connect_pushButton.isChecked():
        self.ui.Emulator_Connect_pushButton.setText("Stop Spikeling Emulator")
        self.ui.Emulator_Connect_pushButton.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[3])) + ";\n"
                                                          "background-color: rgb" + str(tuple(Settings.DarkSolarized[11])) + ";\n"
                                                          "border: 1px solid rgb" + str(tuple(Settings.DarkSolarized[14])) + ";\n"
                                                          "border-radius: 10px;"
                                                           )
    else:
        self.ui.Emulator_Connect_pushButton.setText("Start Spikeling Emulator")
        self.ui.Emulator_Connect_pushButton.setStyleSheet("color: rgb" + str(tuple(Settings.DarkSolarized[14])) + ";\n"
                                                          "background-color: rgb" + str(tuple(Settings.DarkSolarized[2])) + ";\n"
                                                          "border: 1px solid rgb" + str(tuple(Settings.DarkSolarized[14])) + ";\n"
                                                          "border-radius: 10px;"
                                                           )

    self.ui.Emulator_a = 0.02
    self.ui.Emulator_b = 0.2
    self.ui.Emulator_c = -65.0
    self.ui.Emulator_d = 8.0

    self.Emulator_v = -65.0
    self.Emulator_u = 0.0
    self.Emulator_timestep_ms = 0.1
    self.Emulator_v_thresh = 30.0
    self.Emulator_v_peak = 30.0
    self.Emulator_v_min = -110
    self.Emulator_v_max = 100

    self.Emulator_TotalCurrent_Data = 0.0

    self.Emulator_Stimulus_Data = 0.0
    self.Emulator_StimCounter = 0
    self.Emulator_StimSteps = 1000
    self.Emulator_Stim_DutyCycle = 1000

    self.Emulator_NoiseSlider = 0.0
    self.Emulator_Noise_Value = 0.0

    self.Emulator_Trigger = 0

    self.Emulator_Photodiode_Value = 0
    self.Emulator_I_Photodiode = 0
    self.Emulator_Photodiode_Gain = 0
    self.Emulator_Photodiode_Polarity = 1
    self.Photodiode_Recovery = 1.0
    self.Photodiode_Recovery_value = 0.025
    self.Photodiode_Decay_value = 0.001

    self.ui.Emulator_a1 = 0.02
    self.ui.Emulator_b1 = 0.2
    self.ui.Emulator_c1 = -65.0
    self.ui.Emulator_d1 = 8.0
    self.Emulator_Vm_Data1 = 0.0
    self.Emulator_v1 = -65.0
    self.Emulator_u1 = 0.0
    self.Emulator_Syn1_PatchClampCurrent_Value = 0.0
    self.Emulator_TotalCurrent1_Data = 0.0
    self.EmulatorSyn1_Photodiode_Value = 0
    self.EmulatorSyn1_I_Photodiode = 0
    self.EmulatorSyn1_Photodiode_Gain = 0
    self.EmulatorSyn1_Photodiode_Polarity = 1
    self.EmulatorSyn1_Photodiode_Recovery = 1.0
    self.EmulatorSyn1_Photodiode_Recovery_value = 0.025
    self.EmulatorSyn1_Photodiode_Decay_value = 0.001
    self.Emulator_Spike1 = False
    self.Emulator_Syn1Input_Data = 0.0
    self.Emulator_Syn1_Gain = 0.0
    self.Emulator_Syn1_Decay = 0.995


    self.ui.Emulator_a2 = 0.02
    self.ui.Emulator_b2 = 0.2
    self.ui.Emulator_c2 = -65.0
    self.ui.Emulator_d2 = 8.0
    self.Emulator_Vm_Data2 = 0.0
    self.Emulator_v2 = -65.0
    self.Emulator_u2 = 0.0
    self.Emulator_Syn2_PatchClampCurrent_Value = 0.0
    self.Emulator_TotalCurrent2_Data = 0.0
    self.EmulatorSyn2_Photodiode_Value = 0
    self.EmulatorSyn2_I_Photodiode = 0
    self.EmulatorSyn2_Photodiode_Gain = 0
    self.EmulatorSyn2_Photodiode_Polarity = 1
    self.EmulatorSyn2_Photodiode_Recovery = 1.0
    self.EmulatorSyn2_Photodiode_Recovery_value = 0.025
    self.EmulatorSyn2_Photodiode_Decay_value = 0.001
    self.Emulator_Spike2 = False
    self.Emulator_Syn2Input_Data = 0.0
    self.Emulator_Syn2_Gain = 0.0
    self.Emulator_Syn2_Decay = 0.995


def SetPlotCurve(self):
    self._interval = Emulator_sampleinterval
    self._bufsize = int(Emulator_timewindow / Emulator_sampleinterval)

    self.Emulator_databuffer0 = collections.deque([0.0] * self._bufsize, self._bufsize)    # Set a double-ended queue 0.0 floats to self._bufsize entries, for a self._bufsize max length
    self.Emulator_databuffer1 = collections.deque([0.0] * self._bufsize, self._bufsize)
    self.Emulator_databuffer2 = collections.deque([0.0] * self._bufsize, self._bufsize)
    self.Emulator_databuffer3 = collections.deque([0.0] * self._bufsize, self._bufsize)
    self.Emulator_databuffer4 = collections.deque([0.0] * self._bufsize, self._bufsize)
    self.Emulator_databuffer5 = collections.deque([0.0] * self._bufsize, self._bufsize)
    self.Emulator_databuffer6 = collections.deque([0.0] * self._bufsize, self._bufsize)
    self.Emulator_databuffer7 = collections.deque([0.0] * self._bufsize, self._bufsize)


    self.Emulator_x = np.linspace(-Emulator_timewindow, 0.0, self._bufsize)            # Create arrays of self._bufsize length
    self.Emulator_y0 = np.zeros(self._bufsize, dtype=float)
    self.Emulator_y1 = np.zeros(self._bufsize, dtype=float)
    self.Emulator_y2 = np.zeros(self._bufsize, dtype=float)
    self.Emulator_y3 = np.zeros(self._bufsize, dtype=float)
    self.Emulator_y4 = np.zeros(self._bufsize, dtype=float)
    self.Emulator_y5 = np.zeros(self._bufsize, dtype=float)
    self.Emulator_y6 = np.zeros(self._bufsize, dtype=float)


    self.EmulatorData = []
    for _ in range(9):
        self.EmulatorData.append([])


def SetPlot(self):
    self.ui.Emulator_Oscilloscope_widget.showGrid(x=True, y=True)
    self.ui.Emulator_Oscilloscope_widget.setRange(xRange=[-Emulator_timewindowdisplay, 0])
    self.ui.Emulator_Oscilloscope_widget.setRange(yRange=[-90, 30])
    self.ui.Emulator_Oscilloscope_widget.plotItem.setMouseEnabled(x=True, y=False)
    self.ui.Emulator_Oscilloscope_widget.plotItem.vb.setLimits(xMin=-Emulator_timewindow,xMax=0)
    self.ui.Emulator_Oscilloscope_widget.setLabel('left', 'Membrane potential', 'mV')
    self.ui.Emulator_Oscilloscope_widget.setLabel('bottom', 'time', 'ms')
    self.ui.Emulator_Oscilloscope_widget.setLabel('right', 'Current Input', 'a.u.')

    # Secondary ViewBox for currents
    self.Emulator_CurrentPlots = pg.ViewBox()
    pw = self.ui.Emulator_Oscilloscope_widget

    pw.scene().addItem(self.Emulator_CurrentPlots)
    self.Emulator_CurrentPlots.setXLink(pw)
    self.Emulator_CurrentPlots.setRange(yRange=[-100, 100])
    self.Emulator_CurrentPlots.setMouseEnabled(False, False)

    # Link right axis to the currents ViewBox
    pw.getAxis("right").linkToView(self.Emulator_CurrentPlots)

    # IMPORTANT: connect sigResized ONLY ONCE here
    vb = pw.getViewBox()
    vb.sigResized.connect(lambda: UpdateViews(self))

    self.Emulator_curve0 = self.ui.Emulator_Oscilloscope_widget.plot(self.Emulator_x, self.Emulator_y0, pen=pg.mkPen(Settings.DarkSolarized[3], width=penwidth))
    self.Emulator_curve0.clear()
    self.Emulator_curve3 = self.ui.Emulator_Oscilloscope_widget.plot(self.Emulator_x, self.Emulator_y3, pen=pg.mkPen(Settings.DarkSolarized[6], width=penwidth))
    self.Emulator_curve3.clear()
    self.Emulator_curve5 = self.ui.Emulator_Oscilloscope_widget.plot(self.Emulator_x, self.Emulator_y5, pen=pg.mkPen(Settings.DarkSolarized[8], width=penwidth))
    self.Emulator_curve5.clear()

    self.Emulator_curve1 = pg.PlotCurveItem(self.Emulator_x, self.Emulator_y1, pen=pg.mkPen(Settings.DarkSolarized[5], width=penwidth))
    self.Emulator_curve1.clear()
    self.Emulator_curve2 = pg.PlotCurveItem(self.Emulator_x, self.Emulator_y2, pen=pg.mkPen(Settings.DarkSolarized[4], width=penwidth))
    self.Emulator_curve2.clear()
    self.Emulator_curve4 = pg.PlotCurveItem(self.Emulator_x, self.Emulator_y4, pen=pg.mkPen(Settings.DarkSolarized[7], width=penwidth))
    self.Emulator_curve4.clear()
    self.Emulator_curve6 = pg.PlotCurveItem(self.Emulator_x, self.Emulator_y6, pen=pg.mkPen(Settings.DarkSolarized[10], width=penwidth))
    self.Emulator_curve6.clear()

    self.Emulator_CurrentPlots.addItem(self.Emulator_curve1)
    self.Emulator_CurrentPlots.addItem(self.Emulator_curve2)
    self.Emulator_CurrentPlots.addItem(self.Emulator_curve4)
    self.Emulator_CurrentPlots.addItem(self.Emulator_curve6)



def UpdateViews(self):
    self.Emulator_CurrentPlots.setGeometry(self.ui.Emulator_Oscilloscope_widget.getViewBox().sceneBoundingRect())
    self.Emulator_CurrentPlots.linkedViewChanged(self.ui.Emulator_Oscilloscope_widget.getViewBox(), self.Emulator_CurrentPlots.XAxis)
