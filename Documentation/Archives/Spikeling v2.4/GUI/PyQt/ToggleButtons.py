
########################################################################
#                          Libraries import                            #

from PySide6.QtCore import Qt
from py_toggle import PyToggle
import Settings
import Page_Imaging_ImagingSimulation



########################################################################
#                         Generate Toggle Buttons                      #
########################################################################

def Buttons(self):

    # Generate toggle buttons for Spikeling Page
    self.ui.PatchClamp_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[11]),
                                               circle_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[15]),
                                               active_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[4])
                                               )
    self.ui.Noise_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[11]),
                                          circle_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[15]),
                                          active_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[4])
                                          )
    self.ui.PhotoGain_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[11]),
                                              circle_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[15]),
                                              active_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[4])
                                              )
    self.ui.PhotoDecay_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[11]),
                                               circle_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[15]),
                                               active_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[4])
                                               )
    self.ui.PhotoRecovery_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[11]),
                                                  circle_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[15]),
                                                  active_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[4])
                                                  )
    self.ui.StimFre_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[11]),
                                            circle_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[15]),
                                            active_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[5])
                                            )
    self.ui.StimStr_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[11]),
                                            circle_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[15]),
                                            active_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[5])
                                            )
    self.ui.StimCus_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[11]),
                                            circle_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[15]),
                                            active_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[5])
                                            )
    self.ui.Synapse1_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[11]),
                                             circle_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[15]),
                                             active_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[7])
                                             )
    self.ui.Synapse1Decay_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[11]),
                                                  circle_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[15]),
                                                  active_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[7])
                                                  )
    self.ui.Synapse2_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[11]),
                                             circle_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[15]),
                                             active_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[10])
                                             )
    self.ui.Synapse2Decay_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[11]),
                                                  circle_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[15]),
                                                  active_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[10])
                                                  )
    self.ui.Spikeling_PatchClamp_toggle_layout.addWidget(self.ui.PatchClamp_toggleButton)
    self.ui.Spikeling_PatchClamp_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Spikeling_Noise_toggle_layout.addWidget(self.ui.Noise_toggleButton)
    self.ui.Spikeling_Noise_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Spikeling_Synapse1_toggle_layout.addWidget(self.ui.Synapse1_toggleButton)
    self.ui.Spikeling_Synapse1_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Spikeling_Synapse1_Decay_toggle_layout.addWidget(self.ui.Synapse1Decay_toggleButton)
    self.ui.Spikeling_Synapse1_Decay_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Spikeling_Synapse2_toggle_layout.addWidget(self.ui.Synapse2_toggleButton)
    self.ui.Spikeling_Synapse2_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Spikeling_Synapse2_Decay_toggle_layout.addWidget(self.ui.Synapse2Decay_toggleButton)
    self.ui.Spikeling_Synapse2_Decay_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

    self.ui.Spikeling_StimFre_toggle_layout.addWidget(self.ui.StimFre_toggleButton)
    self.ui.Spikeling_StimFre_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Spikeling_StimStr_toggle_layout.addWidget(self.ui.StimStr_toggleButton)
    self.ui.Spikeling_StimStr_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Spikeling_CustomStimulus_toggle_layout.addWidget(self.ui.StimCus_toggleButton)
    self.ui.Spikeling_CustomStimulus_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Spikeling_PR_toggle_layout.addWidget(self.ui.PhotoGain_toggleButton)
    self.ui.Spikeling_PR_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Spikeling_PRDecay_Toggle_layout.addWidget(self.ui.PhotoDecay_toggleButton)
    self.ui.Spikeling_PRDecay_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.SpikelingPRRecovery_toggle_layout.addWidget(self.ui.PhotoRecovery_toggleButton)
    self.ui.SpikelingPRRecovery_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)



    # Generate toggle buttons for Emulator Page
    self.ui.EmulatorPatchClamp_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[11]),
                                                       circle_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[15]),
                                                       active_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[4])
                                                       )
    self.ui.EmulatorNoise_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[11]),
                                                  circle_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[15]),
                                                  active_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[4])
                                          )
    self.ui.EmulatorPhotoGain_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[11]),
                                                      circle_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[15]),
                                                      active_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[4])
                                              )
    self.ui.EmulatorPhotoDecay_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[11]),
                                                       circle_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[15]),
                                                       active_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[4])
                                               )
    self.ui.EmulatorPhotoRecovery_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[11]),
                                                          circle_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[15]),
                                                          active_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[4])
                                                  )
    self.ui.EmulatorStimChoiceCurrent_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[11]),
                                                              circle_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[15]),
                                                              active_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[5])
                                                          )
    self.ui.EmulatorStimChoiceLight_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[11]),
                                                              circle_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[15]),
                                                              active_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[4])
                                                                )
    self.ui.EmulatorStimFre_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[11]),
                                                    circle_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[15]),
                                                    active_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[5])
                                            )
    self.ui.EmulatorStimStr_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[11]),
                                                    circle_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[15]),
                                                    active_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[5])
                                            )
    self.ui.EmulatorStimCus_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[11]),
                                                    circle_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[15]),
                                                    active_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[5])
                                            )


    self.ui.EmulatorSynapse1_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[11]),
                                                     circle_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[15]),
                                                     active_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[7])
                                             )
    self.ui.EmulatorSynapse1Decay_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[11]),
                                                          circle_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[15]),
                                                          active_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[7])
                                                  )
    self.ui.EmulatorSyn1_Synapse_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[11]),
                                                         circle_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[15]),
                                                         active_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[6])
                                                          )
    self.ui.EmulatorSyn1_PatchClamp_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[11]),
                                                            circle_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[15]),
                                                            active_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[4])
                                                         )
    self.ui.EmulatorSyn1_Noise_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[11]),
                                                       circle_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[15]),
                                                       active_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[4])
                                                         )
    self.ui.EmulatorSyn1_StimDC_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[11]),
                                                        circle_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[15]),
                                                        active_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[5])
                                                         )
    self.ui.EmulatorSyn1_StimLight_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[11]),
                                                           circle_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[15]),
                                                           active_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[4])
                                                        )
    self.ui.EmulatorSyn1_PhotoGain_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[11]),
                                                           circle_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[15]),
                                                           active_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[4])
                                                           )
    self.ui.EmulatorSyn1_PhotoDecay_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[11]),
                                                           circle_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[15]),
                                                           active_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[4])
                                                           )
    self.ui.EmulatorSyn1_PhotoRecovery_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[11]),
                                                           circle_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[15]),
                                                           active_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[4])
                                                           )


    self.ui.EmulatorSyn2_Synapse_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[11]),
                                                         circle_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[15]),
                                                         active_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[8])
                                                         )
    self.ui.EmulatorSyn2_PatchClamp_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[11]),
                                                            circle_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[15]),
                                                            active_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[4])
                                                            )
    self.ui.EmulatorSyn2_Noise_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[11]),
                                                       circle_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[15]),
                                                       active_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[4])
                                                       )
    self.ui.EmulatorSyn2_StimDC_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[11]),
                                                        circle_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[15]),
                                                        active_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[5])
                                                        )
    self.ui.EmulatorSyn2_StimLight_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[11]),
                                                           circle_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[15]),
                                                           active_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[4])
                                                           )
    self.ui.EmulatorSynapse2_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[11]),
                                                     circle_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[15]),
                                                     active_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[10])
                                             )
    self.ui.EmulatorSynapse2Decay_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[11]),
                                                          circle_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[15]),
                                                          active_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[10])
                                                  )
    self.ui.EmulatorSyn2_PhotoGain_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[11]),
                                                           circle_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[15]),
                                                           active_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[4])
                                                           )
    self.ui.EmulatorSyn2_PhotoDecay_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[11]),
                                                            circle_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[15]),
                                                            active_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[4])
                                                            )
    self.ui.EmulatorSyn2_PhotoRecovery_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[11]),
                                                               circle_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[15]),
                                                               active_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[4])
                                                                )

    self.ui.Emulator_PatchClamp_toggle_layout.addWidget(self.ui.EmulatorPatchClamp_toggleButton)
    self.ui.Emulator_PatchClamp_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Emulator_Noise_toggle_layout.addWidget(self.ui.EmulatorNoise_toggleButton)
    self.ui.Emulator_Noise_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Emulator_Synapse1_toggle_layout.addWidget(self.ui.EmulatorSynapse1_toggleButton)
    self.ui.Emulator_Synapse1_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Emulator_Synapse1_Decay_toggle_layout.addWidget(self.ui.EmulatorSynapse1Decay_toggleButton)
    self.ui.Emulator_Synapse1_Decay_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Emulator_Synapse2_toggle_layout.addWidget(self.ui.EmulatorSynapse2_toggleButton)
    self.ui.Emulator_Synapse2_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Emulator_Synapse2_Decay_toggle_layout.addWidget(self.ui.EmulatorSynapse2Decay_toggleButton)
    self.ui.Emulator_Synapse2_Decay_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

    self.ui.Emulator_StimChoice_Current_layout.addWidget(self.ui.EmulatorStimChoiceCurrent_toggleButton)
    self.ui.Emulator_StimChoice_Current_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Emulator_StimChoice_Light_layout.addWidget(self.ui.EmulatorStimChoiceLight_toggleButton)
    self.ui.Emulator_StimChoice_Light_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

    self.ui.Emulator_StimFre_toggle_layout.addWidget(self.ui.EmulatorStimFre_toggleButton)
    self.ui.Emulator_StimFre_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Emulator_StimStr_toggle_layout.addWidget(self.ui.EmulatorStimStr_toggleButton)
    self.ui.Emulator_StimStr_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Emulator_CustomStimulus_toggle_layout.addWidget(self.ui.EmulatorStimCus_toggleButton)
    self.ui.Emulator_CustomStimulus_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Emulator_PR_toggle_layout.addWidget(self.ui.EmulatorPhotoGain_toggleButton)
    self.ui.Emulator_PR_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Emulator_PRDecay_Toggle_layout.addWidget(self.ui.EmulatorPhotoDecay_toggleButton)
    self.ui.Emulator_PRDecay_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.EmulatorPRRecovery_toggle_layout.addWidget(self.ui.EmulatorPhotoRecovery_toggleButton)
    self.ui.EmulatorPRRecovery_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

    self.ui.Emulator_Syn1_Mode_Toggle_layout.addWidget(self.ui.EmulatorSyn1_Synapse_toggleButton)
    self.ui.Emulator_Syn1_Mode_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Emulator_Syn1_PatchClamp_Toggle_layout.addWidget(self.ui.EmulatorSyn1_PatchClamp_toggleButton)
    self.ui.Emulator_Syn1_PatchClamp_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.EmulatorSyn1_PatchClamp_toggleButton.setEnabled(False)
    self.ui.Emulator_Syn1_Noise_Toggle_layout.addWidget(self.ui.EmulatorSyn1_Noise_toggleButton)
    self.ui.Emulator_Syn1_Noise_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.EmulatorSyn1_Noise_toggleButton.setEnabled(False)
    self.ui.Emulator_Syn1_Stimulus_DC_Toggle_layout.addWidget(self.ui.EmulatorSyn1_StimDC_toggleButton)
    self.ui.Emulator_Syn1_Stimulus_DC_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.EmulatorSyn1_StimDC_toggleButton.setEnabled(False)
    self.ui.Emulator_Syn1_Stimulus_Light_Toggle_layout.addWidget(self.ui.EmulatorSyn1_StimLight_toggleButton)
    self.ui.Emulator_Syn1_Stimulus_Light_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.EmulatorSyn1_StimLight_toggleButton.setEnabled(False)
    self.ui.Emulator_Syn1_PhotoGain_toggle_layout.addWidget(self.ui.EmulatorSyn1_PhotoGain_toggleButton)
    self.ui.Emulator_Syn1_PhotoGain_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.EmulatorSyn1_PhotoGain_toggleButton.setEnabled(False)
    self.ui.Emulator_Syn1_PhotoDecay_toggle_layout.addWidget(self.ui.EmulatorSyn1_PhotoDecay_toggleButton)
    self.ui.Emulator_Syn1_PhotoDecay_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.EmulatorSyn1_PhotoDecay_toggleButton.setEnabled(False)
    self.ui.Emulator_Syn1_PhotoRecovery_toggle_layout.addWidget(self.ui.EmulatorSyn1_PhotoRecovery_toggleButton)
    self.ui.Emulator_Syn1_PhotoRecovery_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.EmulatorSyn1_PhotoRecovery_toggleButton.setEnabled(False)

    self.ui.Emulator_Syn2_Mode_Toggle_layout.addWidget(self.ui.EmulatorSyn2_Synapse_toggleButton)
    self.ui.Emulator_Syn2_Mode_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Emulator_Syn2_PatchClamp_Toggle_layout.addWidget(self.ui.EmulatorSyn2_PatchClamp_toggleButton)
    self.ui.Emulator_Syn2_PatchClamp_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.EmulatorSyn2_PatchClamp_toggleButton.setEnabled(False)
    self.ui.Emulator_Syn2_Noise_Toggle_layout.addWidget(self.ui.EmulatorSyn2_Noise_toggleButton)
    self.ui.Emulator_Syn2_Noise_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.EmulatorSyn2_Noise_toggleButton.setEnabled(False)
    self.ui.Emulator_Syn2_Stimulus_DC_Toggle_layout.addWidget(self.ui.EmulatorSyn2_StimDC_toggleButton)
    self.ui.Emulator_Syn2_Stimulus_DC_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.EmulatorSyn2_StimDC_toggleButton.setEnabled(False)
    self.ui.Emulator_Syn2_Stimulus_Light_Toggle_layout.addWidget(self.ui.EmulatorSyn2_StimLight_toggleButton)
    self.ui.Emulator_Syn2_Stimulus_Light_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.EmulatorSyn2_StimLight_toggleButton.setEnabled(False)
    self.ui.Emulator_Syn2_PhotoGain_toggle_layout.addWidget(self.ui.EmulatorSyn2_PhotoGain_toggleButton)
    self.ui.Emulator_Syn2_PhotoGain_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.EmulatorSyn2_PhotoGain_toggleButton.setEnabled(False)
    self.ui.Emulator_Syn2_PhotoDecay_toggle_layout.addWidget(self.ui.EmulatorSyn2_PhotoDecay_toggleButton)
    self.ui.Emulator_Syn2_PhotoDecay_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.EmulatorSyn2_PhotoDecay_toggleButton.setEnabled(False)
    self.ui.Emulator_Syn2_PhotoRecovery_toggle_layout.addWidget(self.ui.EmulatorSyn2_PhotoRecovery_toggleButton)
    self.ui.Emulator_Syn2_PhotoRecovery_toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.EmulatorSyn2_PhotoRecovery_toggleButton.setEnabled(False)



    # Generate toggle buttons for Imaging Page
    self.ui.Imaging_FrameRate_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[11]),
                                                      circle_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[15]),
                                                      active_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[4])
                                                      )
    self.ui.Imaging_PMT_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[11]),
                                                circle_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[15]),
                                                active_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[4])
                                                )
    self.ui.Imaging_Laser_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[11]),
                                                  circle_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[15]),
                                                  active_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[4])
                                                  )

    self.ui.Imaging_CalciumDecay_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[11]),
                                                         circle_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[15]),
                                                         active_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[10])
                                                         )
    self.ui.Imaging_CalciumJump_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[11]),
                                                        circle_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[15]),
                                                        active_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[10])
                                                        )
    self.ui.Imaging_CalciumNoise_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[11]),
                                                         circle_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[15]),
                                                         active_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[10])
                                                         )
    self.ui.Imaging_CalciumBaseline_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[11]),
                                                            circle_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[15]),
                                                            active_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[10])
                                                            )

    self.ui.Imaging_kd_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[11]),
                                               circle_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[15]),
                                               active_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[4])
                                               )
    self.ui.Imaging_Hill_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[11]),
                                                 circle_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[15]),
                                                 active_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[4])
                                                 )
    self.ui.Imaging_PhotoShotNoise_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[11]),
                                                           circle_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[15]),
                                                           active_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[4])
                                                           )
    self.ui.Imaging_FluoNoise_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[11]),
                                                      circle_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[15]),
                                                      active_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[4])
                                                      )
    self.ui.Imaging_FluoScale_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[11]),
                                                      circle_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[15]),
                                                      active_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[4])
                                                      )
    self.ui.Imaging_FluoOffset_toggleButton = PyToggle(bg_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[11]),
                                                       circle_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[15]),
                                                       active_color='#%02x%02x%02x' % tuple(Settings.DarkSolarized[4])
                                                       )

    self.ui.Imaging_FrameRate_Toggle_layout.addWidget(self.ui.Imaging_FrameRate_toggleButton)
    self.ui.Imaging_FrameRate_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Imaging_PMT_Toggle_layout.addWidget(self.ui.Imaging_PMT_toggleButton)
    self.ui.Imaging_PMT_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Imaging_Laser_Toggle_layout.addWidget(self.ui.Imaging_Laser_toggleButton)
    self.ui.Imaging_Laser_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

    self.ui.Imaging_CalciumDecay_Toggle_layout.addWidget(self.ui.Imaging_CalciumDecay_toggleButton)
    self.ui.Imaging_CalciumDecay_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Imaging_CalciumJump_Toggle_layout.addWidget(self.ui.Imaging_CalciumJump_toggleButton)
    self.ui.Imaging_CalciumJump_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Imaging_CalciumNoise_Toggle_layout.addWidget(self.ui.Imaging_CalciumNoise_toggleButton)
    self.ui.Imaging_CalciumNoise_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Imaging_CalciumBaseline_Toggle_layout.addWidget(self.ui.Imaging_CalciumBaseline_toggleButton)
    self.ui.Imaging_CalciumBaseline_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

    self.ui.Imaging_kd_Toggle_layout.addWidget(self.ui.Imaging_kd_toggleButton)
    self.ui.Imaging_kd_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Imaging_Hill_Toggle_layout.addWidget(self.ui.Imaging_Hill_toggleButton)
    self.ui.Imaging_Hill_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Imaging_PhotoShotNoise_Toggle_layout.addWidget(self.ui.Imaging_PhotoShotNoise_toggleButton)
    self.ui.Imaging_PhotoShotNoise_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Imaging_FluoNoise_Toggle_layout.addWidget(self.ui.Imaging_FluoNoise_toggleButton)
    self.ui.Imaging_FluoNoise_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Imaging_FluoScale_Toggle_layout.addWidget(self.ui.Imaging_FluoScale_toggleButton)
    self.ui.Imaging_FluoScale_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.ui.Imaging_FluoOffset_Toggle_layout.addWidget(self.ui.Imaging_FluoOffset_toggleButton)
    self.ui.Imaging_FluoOffset_Toggle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)


