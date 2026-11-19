
########################################################################
#                          Libraries import                            #

from PySide6 import QtWidgets
from PySide6.QtCore import QSize
from PySide6.QtWidgets import QSlider

from spikeling_gui.features.extracellular.tetrode_window import TetrodeGeometryWindow

from spikeling_gui.widgets.recording import configure_recording_folder, style_recording_button
from spikeling_gui.appearance.theme_manager import theme_manager
from spikeling_gui.widgets.sliders import SliderBinding
from spikeling_gui.features.neuron_interface import page as Page_Spikeling_NeuronInterface
from spikeling_gui.features.emulator import page as Page_Spikeling_NeuronEmulator
from spikeling_gui.features.imaging import page as Page_Imaging_ImagingSimulation
from spikeling_gui.features.extracellular.page import Scope as ExtracellularPage
from spikeling_gui.features.imaging.scope import ImagingGraph
from spikeling_gui.features.imaging_data_analysis.page import ImagingDataAnalysisPage
from spikeling_gui.features.extracellular.recording_page import RecordingPage
from spikeling_gui.features.extracellular.scope import ExtraCellularGraph
from spikeling_gui.features.stimulus_generator import page as Page_StimulusGenerator
from spikeling_gui.features.neuron_generator import page as Page_NeuronGenerator
from spikeling_gui.features.electrophysiology_data_analysis import page as Page_Spikeling_DataAnalysis
from spikeling_gui.widgets.menu_animation import (animation_speed, centerMenu_max, centerMenu_min, collapseMenu, expandMenu, leftMenu_max, leftMenu_min, spikecenterMenu_max, spikecenterMenu_min, spikerightMenu_max, spikerightMenu_min, toggleMenu)
from spikeling_gui.features.emulator import scope as emulator_scope
from spikeling_gui.features.emulator.controls import EmulatorControls
from spikeling_gui.features.neuron_interface.scope import SpikelingGraph
from spikeling_gui.features.neuron_interface.short_term_plasticity import SynapseSTPControl
from spikeling_gui.features.about.page import ShowPage as show_about_page

from spikeling_gui.hardware.serial_manager import serial_manager


########################################################################
#                      Opening auxilliary windows                      #
########################################################################

def openTetrodeWindow(self):
    self.tetrode_window.show()
    self.tetrode_window.raise_()
    self.tetrode_window.activateWindow()

########################################################################
#                           Button Functions                           #
########################################################################

def Buttons(self):

    # Navigation buttons
    self.icon_SpikelingDropMenuRight = "DropMenuRight.png"
    self.icon_SpikelingMenuRight = "MenuRight.png"


    # Main Menu Container
    self.icon_DropMenuLeft = "DropMenuLeft.png"
    self.icon_MenuLeft = "MenuLeft.png"
    self.ui.centerMenuContainer.setMaximumSize(QSize(0, 16777215))
    self.ui.leftMenuContainer.setMinimumSize(QSize(leftMenu_max, 16777215))
    self.ui.menu_pushButton.clicked.connect(lambda: toggleMenu(self, self.ui.leftMenuContainer, leftMenu_min, leftMenu_max, animation_speed,
                                                            self.ui.menu_pushButton, self.icon_MenuLeft, self.icon_DropMenuLeft, True))


    # Left Menu Container
    self.ui.SpikelingMenu_pushButton.clicked.connect(lambda: expandMenu(self, self.ui.centerMenuContainer, centerMenu_min, centerMenu_max, animation_speed, True))
    self.ui.SpikelingMenu_pushButton.clicked.connect(lambda: self.ui.centerMenuSubContainer_menu_stackedwidget.setCurrentWidget(self.ui.Spikeling_SubMenu_page))

    self.ui.ImagingMenu_pushButton.clicked.connect(lambda:  expandMenu(self, self.ui.centerMenuContainer, centerMenu_min, centerMenu_max, animation_speed, True))
    self.ui.ImagingMenu_pushButton.clicked.connect(lambda: self.ui.centerMenuSubContainer_menu_stackedwidget.setCurrentWidget(self.ui.Imaging_SubMenu_page))

    self.ui.Tetrode_pushButton.clicked.connect(lambda:  expandMenu(self, self.ui.centerMenuContainer, centerMenu_min, centerMenu_max, animation_speed, True))
    self.ui.Tetrode_pushButton.clicked.connect(lambda: self.ui.centerMenuSubContainer_menu_stackedwidget.setCurrentWidget(self.ui.ExtraCellular_SubMenu_page))

    self.ui.NeuronGeneratorMenu_pushButton.clicked.connect(lambda: collapseMenu(self, self.ui.centerMenuContainer, centerMenu_min, centerMenu_max, animation_speed, True))
    self.ui.NeuronGeneratorMenu_pushButton.clicked.connect(lambda: Page_NeuronGenerator.ShowPage(self))

    self.ui.StimuluGeneratorMenu_pushButton.clicked.connect(lambda: Page_StimulusGenerator.ShowPage(self))
    self.ui.StimuluGeneratorMenu_pushButton.clicked.connect(lambda: collapseMenu(self, self.ui.centerMenuContainer, centerMenu_min, centerMenu_max, animation_speed, True))


    self.ui.centerMenuSubContainer_exit_pushButton.clicked.connect(lambda: collapseMenu(self, self.ui.centerMenuContainer, centerMenu_min, centerMenu_max, animation_speed, True))

    self.ui.SettingsMenu_pushButton.clicked.connect(lambda: collapseMenu(self, self.ui.centerMenuContainer, centerMenu_min, centerMenu_max, animation_speed, True))

    self.ui.AboutMenu_pushButton.clicked.connect(lambda: collapseMenu(self, self.ui.centerMenuContainer, centerMenu_min, centerMenu_max, animation_speed, True))

    self.ui.GitHubMenu_pushButton.clicked.connect(lambda: collapseMenu(self, self.ui.centerMenuContainer, centerMenu_min, centerMenu_max, animation_speed, True))


    # Right Menu Container
    # Spikeling parameters navigation button
    self.ui.Spikeling_CenterMenuContainer.setMaximumSize(QSize(0, 16777215))
    self.ui.Spikeling_rightMenuContainer.setMinimumSize(QSize(spikerightMenu_max, 16777215))
    self.ui.Spikeling_rightMenuSubContainer_pushButton.clicked.connect(lambda: toggleMenu(self, self.ui.Spikeling_rightMenuContainer, spikerightMenu_min, spikerightMenu_max, animation_speed,
                                                                                          self.ui.Spikeling_rightMenuSubContainer_pushButton, self.icon_SpikelingMenuRight, self.icon_SpikelingDropMenuRight, True))
    self.ui.Spikeling_StimulusParameter_pushButton.clicked.connect(lambda: expandMenu(self, self.ui.Spikeling_CenterMenuContainer, spikecenterMenu_min, spikecenterMenu_max, animation_speed, True))
    self.ui.Spikeling_NeuronParameter_pushButton.clicked.connect(lambda: expandMenu(self, self.ui.Spikeling_CenterMenuContainer, spikecenterMenu_min, spikecenterMenu_max, animation_speed, True))
    self.ui.Spikeling_PharmacologyParameter_pushButton.clicked.connect(lambda: expandMenu(self, self.ui.Spikeling_CenterMenuContainer, spikecenterMenu_min, spikecenterMenu_max,animation_speed, True))
    self.ui.Spikeling_Synapse1Parameter_pushButton.clicked.connect(lambda: expandMenu(self, self.ui.Spikeling_CenterMenuContainer, spikecenterMenu_min, spikecenterMenu_max,animation_speed, True))
    self.ui.Spikeling_Synapse2Parameter_pushButton.clicked.connect(lambda: expandMenu(self, self.ui.Spikeling_CenterMenuContainer, spikecenterMenu_min, spikecenterMenu_max,animation_speed, True))
    self.ui.Spikeling_parameter_exit_pushButton.clicked.connect(lambda: collapseMenu(self, self.ui.Spikeling_CenterMenuContainer, spikecenterMenu_min, spikecenterMenu_max, animation_speed, True))


    # Emulator parameters navigation button
    emulator_panel_width = self.ui.Emulator_CenterMenuContainer.maximumWidth()
    self.ui.Emulator_CenterMenuContainer.setMaximumSize(QSize(0, 16777215))
    self.ui.Emulator_rightMenuContainer.setMinimumSize(QSize(spikerightMenu_max, 16777215))
    self.ui.Emulator_rightMenuSubContainer_pushButton.clicked.connect(lambda: toggleMenu(self, self.ui.Emulator_rightMenuContainer, spikerightMenu_min, spikerightMenu_max,animation_speed,
                                                                                         self.ui.Emulator_rightMenuSubContainer_pushButton, self.icon_SpikelingMenuRight, self.icon_SpikelingDropMenuRight, True))
    emulator_panels = (
        (self.ui.Emulator_StimulusParameter_pushButton, self.ui.Emulator_StimulusParameter_page),
        (self.ui.Emulator_NeuronParameter_pushButton, self.ui.Emulator_NeuronParameter_page),
        (self.ui.Emulator_PharmacologyParameter_pushButton, self.ui.Emulator_PharmacologyParameter_page),
        (self.ui.Emulator_Synapse1Parameter_pushButton, self.ui.Emulator_Synapse1Parameter_page),
        (self.ui.Emulator_Synapse2Parameter_pushButton, self.ui.Emulator_Synapse2Parameter_page),
        (self.ui.Emulator_AuxiliaryNeuron1Parameter_pushButton, self.ui.Emulator_AuxiliaryNeuron1Parameter_page),
        (self.ui.Emulator_AuxiliaryNeuron2Parameter_pushButton, self.ui.Emulator_AuxiliaryNeuron2Parameter_page),
    )

    def show_emulator_panel(page):
        self.ui.Emulator_parameter_stackedwidget.setCurrentWidget(page)
        expandMenu(
            self, self.ui.Emulator_CenterMenuContainer,
            spikecenterMenu_min, emulator_panel_width, animation_speed, True,
        )

    for button, page in emulator_panels:
        button.clicked.connect(lambda checked=False, panel=page: show_emulator_panel(panel))
    self.ui.Emulator_parameter_exit_pushButton.clicked.connect(lambda: collapseMenu(self, self.ui.Emulator_CenterMenuContainer, spikecenterMenu_min, emulator_panel_width, animation_speed, True))



    # Imaging  parameters navigation button
    self.ui.Imaging_CenterMenuContainer.setMaximumSize(QSize(0, 16777215))
    self.ui.Imaging_rightMenuContainer.setMinimumSize(QSize(0, 16777215))
    self.ui.Imaging_rightMenuSubContainer_pushButton.clicked.connect(lambda: toggleMenu(self, self.ui.Imaging_rightMenuContainer, spikerightMenu_min, spikerightMenu_max, animation_speed,
                                                                                        self.ui.Imaging_rightMenuSubContainer_pushButton, self.icon_SpikelingMenuRight, self.icon_SpikelingDropMenuRight, True))
    self.ui.Imaging_ImagingParameter_pushButton.clicked.connect(lambda: expandMenu(self, self.ui.Imaging_CenterMenuContainer, spikecenterMenu_min, spikecenterMenu_max, animation_speed, True))
    self.ui.Imaging_CalciumParameter_pushButton.clicked.connect(lambda: expandMenu(self, self.ui.Imaging_CenterMenuContainer, spikecenterMenu_min, spikecenterMenu_max, animation_speed, True))
    self.ui.Imaging_FluoParameter_pushButton.clicked.connect(lambda: expandMenu(self, self.ui.Imaging_CenterMenuContainer, spikecenterMenu_min, spikecenterMenu_max, animation_speed, True))
    self.ui.Imaging_parameter_exit_pushButton.clicked.connect(lambda: collapseMenu(self, self.ui.Imaging_CenterMenuContainer, spikecenterMenu_min, spikecenterMenu_max, animation_speed, True))


########################################################################
# Home Page - page_Home
    # Display Home page on start up
    self.ui.mainbody_stackedWidget.setCurrentWidget(self.ui.page_Home)
    self.ui.appTitle_pushButton.clicked.connect(lambda: self.ui.mainbody_stackedWidget.setCurrentWidget(self.ui.page_Home))

########################################################################
# Spikeling Neuron Interface Page

    # Display Page_Spikeling_NeuronInterface when spikeling button is clicked
    self.ui.Neuron_pushButton.clicked.connect(lambda: Page_Spikeling_NeuronInterface.Spikeling.ShowPage(self))

    # COM selection never opens a port; the graph supplies the live device list.
    self.ui.Spikeling_SelectPortComboBox.currentIndexChanged.connect(lambda: Page_Spikeling_NeuronInterface.Spikeling.ChangePort(self))

    # Modify the microcontroller loop time
    self.ui.Spikeling_Speed_slider.valueChanged.connect(lambda: Page_Spikeling_NeuronInterface.Spikeling.ChangeSpeed(self))

    # Create an instance of SpikelingGraph
    self.spikeling_graph = SpikelingGraph(self)

    # Connect the button to the instance method
    self.ui.Spikeling_ConnectButton.clicked.connect(lambda: self.spikeling_graph.connect_device()
                                                    if self.ui.Spikeling_ConnectButton.isChecked()
                                                    else self.spikeling_graph.disconnect_device())
    # Load previously conceived neurons
    self.ui.Spikeling_NeuronBrowsePushButton.clicked.connect(lambda: Page_Spikeling_NeuronInterface.Spikeling.BrowseNeuron(self))

    # Select Neuron Mode from the list and applied Izhikevich parameters:
    self.ui.ImportNeuron = []
    self.ui.Spikeling_NeuronMode_pushButton.clicked.connect(lambda: Page_Spikeling_NeuronInterface.Spikeling.SelectNeuronMode(self))

    # Deactivate buzzer sound
    self.ui.Sound_pushButton.clicked.connect(lambda: Page_Spikeling_NeuronInterface.Spikeling.ControlBuzzer(self))

    # Deactivate LED light
    self.ui.LED_pushButton.clicked.connect(lambda: Page_Spikeling_NeuronInterface.Spikeling.ControlLED(self))

    # Data recording
    self.spikeling_graph.configure_recording()
    configure_recording_folder(
        self, self.ui.Spikeling_DataRecording_Folder_lineEdit,
        self.ui.Spikeling_DataRecording_Folder_pushButton,
    )
    self.ui.Spikeling_DataRecording_Record_pushButton.setCheckable(True)
    self.ui.Spikeling_DataRecording_Record_pushButton.clicked.connect(self.spikeling_graph.handle_record_button)

    # Stimulation parameters
    self.ui.Spikeling_StimulusParameter_pushButton.clicked.connect(lambda: self.ui.Spikeling_parameter_stackedwidget.setCurrentWidget(self.ui.StimulusParameter_page))

    Page_Spikeling_NeuronInterface.Spikeling.ConfigureStimulusFrequency(self)
    Page_Spikeling_NeuronInterface.Spikeling.ConfigureStimulusStrength(self)
    Page_Spikeling_NeuronInterface.Spikeling.ConfigureCustomStimulus(self)


    # Neuron parameters
    self.ui.Spikeling_NeuronParameter_pushButton.clicked.connect(lambda: self.ui.Spikeling_parameter_stackedwidget.setCurrentWidget(self.ui.NeuronParameter_page))
    Page_Spikeling_NeuronInterface.Spikeling.ConfigurePatchClamp(self)
    Page_Spikeling_NeuronInterface.Spikeling.ConfigureNoise(self)
    Page_Spikeling_NeuronInterface.Spikeling.ConfigurePhotoreceptors(self)

    # Pharmacology parameters
    self.ui.Spikeling_PharmacologyParameter_pushButton.clicked.connect(lambda: self.ui.Spikeling_parameter_stackedwidget.setCurrentWidget(self.ui.PharmacologyParameter_page))
    Page_Spikeling_NeuronInterface.Spikeling.ConfigureDrugSliders(self)

    # Synapse1 parameters
    self.ui.Spikeling_Synapse1Parameter_pushButton.clicked.connect(lambda: self.ui.Spikeling_parameter_stackedwidget.setCurrentWidget(self.ui.Synapse1Parameter_page))
    Page_Spikeling_NeuronInterface.Spikeling.ConfigureSynapse1(self)

    # Synapse2 parameters
    self.ui.Spikeling_Synapse2Parameter_pushButton.clicked.connect(lambda: self.ui.Spikeling_parameter_stackedwidget.setCurrentWidget(self.ui.Synapse2Parameter_page))
    Page_Spikeling_NeuronInterface.Spikeling.ConfigureSynapse2(self)
    Page_Spikeling_NeuronInterface.Spikeling.ConfigureProbabilisticRelease(self)

    self.synapse_stp_controls = {}
    for synapse in (1, 2):
        prefix = f"Spikeling_Synapse{synapse}_STP"
        self.synapse_stp_controls[synapse] = SynapseSTPControl(
            synapse,
            getattr(self.ui, f"{prefix}_comboBox"),
            getattr(self.ui, f"{prefix}_Advanced_pushButton"),
            getattr(self.ui, f"{prefix}_Reset_pushButton"),
            self.spikeling_graph.supervisor,
        )

    ########################################################################
    # Spikeling Emulator Page

    # Display Page_Spikeling_NeuronEmulator when emulator button is clicked
    self.ui.NeuronEmulator_pushButton.clicked.connect(lambda: Page_Spikeling_NeuronEmulator.Emulator.ShowPage(self))

    # Start the Emulator
    self.ui.Emulator_Connect_pushButton.clicked.connect(lambda: emulator_scope.EmulatorPlot(self))

    self.emulator_controls = EmulatorControls(self)

    # Data Recording
    configure_recording_folder(
        self, self.ui.Emulator_DataRecording_Folder_lineEdit,
        self.ui.Emulator_DataRecording_Folder_pushButton,
    )
    self.ui.Emulator_DataRecording_Record_pushButton.setCheckable(True)
    self.ui.Emulator_DataRecording_Record_pushButton.clicked.connect(lambda: Page_Spikeling_NeuronEmulator.Emulator.RecordButton(self))


########################################################################
# Spikeling Data Analysis - page 103
    # Display Page_Spikeling_DataAnalysis when data analysis button is clicked
    self.ui.NeuronDataAnalysis_pushButton.clicked.connect(lambda: Page_Spikeling_DataAnalysis.Spikeling103.ShowPage(self))


########################################################################
# Spikeling Tutorial - page 104
    # Display Page_Spikeling_Tutorial when Tutorial button is clicked



########################################################################
# Imaging Page - page201
    # Display page201 when imaging button is clicked
    self.ui.ImagingStimulation_pushButton.clicked.connect(lambda: Page_Imaging_ImagingSimulation.Imaging.ShowPage(self))
    self.imaging_analysis_page = ImagingDataAnalysisPage(self)
    self.ui.ImagingDataAnalysis_pushButton.clicked.connect(self.imaging_analysis_page.show_page)


    # Create an instance of ImagingGraph
    self.imaging_graph  = ImagingGraph(self)
    self.imaging_page = Page_Imaging_ImagingSimulation.Imaging(self)
    for index, source in enumerate(("spikeling", "emulator")):
        self.ui.Imaging_Source_comboBox.setItemData(index, source)

    # Connect the button to the instance method
    self.ui.Imaging_ConnectButton.clicked.connect(lambda: Page_Imaging_ImagingSimulation.Imaging.UpdateSource(self))

    # Update the Vm source for imaging
    self.ui.Imaging_Source_comboBox.currentIndexChanged.connect(lambda: Page_Imaging_ImagingSimulation.Imaging.UpdateSource(self))

    # Data Recording
    configure_recording_folder(
        self, self.ui.Imaging_DataRecording_Folder_lineEdit,
        self.ui.Imaging_DataRecording_Folder_pushButton,
    )
    self.ui.Imaging_DataRecording_File_lineEdit.setEnabled(True)
    self.ui.Imaging_DataRecording_Record_pushButton.setCheckable(True)
    self.ui.Imaging_DataRecording_Record_pushButton.clicked.connect(self.imaging_graph.on_record_clicked)
    self.ui.Imaging_DataRecording_File_lineEdit.setPlaceholderText("Enter a file name")
    self.ui.Emulator_DataRecording_File_lineEdit.setPlaceholderText("Enter a file name")
    self.ui.Emulator_DataRecording_Record_label.setText("Ready to record")
    self.ui.Emulator_DataRecording_Record_label_2.clear()
    self.ui.Imaging_DataRecording_Record_label.setText("Ready to record")
    self.ui.Imaging_DataRecording_Record_label_2.clear()
    for prefix in ("Emulator", "Imaging"):
        button = getattr(self.ui, f"{prefix}_DataRecording_Record_pushButton")
        label = getattr(self.ui, f"{prefix}_DataRecording_Record_label")
        label.setStyleSheet("color: rgb(220, 50, 47);")
        style_recording_button(button, False)
    theme_manager.themeChanged.connect(lambda *_: style_recording_button(
        self.ui.Emulator_DataRecording_Record_pushButton, bool(getattr(self, "recordflag", False))))
    theme_manager.themeChanged.connect(lambda *_: style_recording_button(
        self.ui.Imaging_DataRecording_Record_pushButton, self.imaging_graph.record_flag))

    # Imaging Parameters
    self.ui.Imaging_ImagingParameter_pushButton.clicked.connect(lambda: self.ui.Imaging_parameter_stackedWidget.setCurrentWidget(self.ui.Imaging_ImagingParameter_page))
    self.ui.Imaging_Df_toggleButton.toggled.connect(self.imaging_graph.ActivateDf)
    self.ui.Imaging_Linear_toggleButton.toggled.connect(self.imaging_page.Linear_toggleButton)
    self.ui.Imaging_Equilibrium_toggleButton.toggled.connect(self.imaging_page.Equilibrium_toggleButton)
    self.ui.Imaging_Logistic_toggleButton.toggled.connect(self.imaging_page.Logistic_toggleButton)
    # GECI selector + Apply button are wired by the controller itself
    self.imaging_graph.bind_geci_controls()
    self.imaging_graph.initialise_controls()

    # Calcium parameters
    self.ui.Imaging_CalciumParameter_pushButton.clicked.connect(lambda: self.ui.Imaging_parameter_stackedWidget.setCurrentWidget(self.ui.Imaging_CalciumParameter_page))

    # Fluorescence Parameters
    self.ui.Imaging_FluoParameter_pushButton.clicked.connect(lambda: self.ui.Imaging_parameter_stackedWidget.setCurrentWidget(self.ui.Imaging_FluoParameter_page))


########################################################################
# Imaging Tutorial - page202
    # Display page202 when imaging button is clicked


########################################################################
# Imaging Data Analysis- page203
    # Display page201 when imaging button is clicked



########################################################################
# ExtraCellular Page - page301
    # Create an instance of ExtraCellularGraph
    self.extracellular_graph = ExtraCellularGraph(self)
    self.extracellular_page = ExtracellularPage(self)

    # Display page301 when extracellular button is clicked
    self.ui.ExtraCellularScope_pushButton.clicked.connect(self.extracellular_page.ShowPage)
    self.extracellular_recording_page = None

    def show_extracellular_recording():
        if self.extracellular_recording_page is None:
            self.extracellular_recording_page = RecordingPage(self)
            self.ui.mainbody_stackedWidget.addWidget(self.extracellular_recording_page)
        self.extracellular_recording_page.show_page()

    self.ui.ExtraCellularSpikes_pushButton.clicked.connect(show_extracellular_recording)

    # Bridge tetrode saved geometry -> extracellular scope page/controller
    self.tetrode_window = TetrodeGeometryWindow(self)
    self.tetrode_window.geometryChanged.connect(self.extracellular_page.apply_tetrode_geometry)

    # The constructor's reset_geometry() emission predates this connection,
    # so push the current layout explicitly to synchronise the graph.
    self.extracellular_page.apply_tetrode_geometry(self.tetrode_window.get_geometry_payload())

    # Connect the button to the instance method
    self.ui.ExtraCellular_ConnectButton.clicked.connect(lambda: self.extracellular_page.ToggleConnection())

    # Update the Vm source for ExtraCellular
    self.ui.ExtraCellular_Source_comboBox.currentIndexChanged.connect(lambda: self.extracellular_page.UpdateSource())

    # Data Recording
    configure_recording_folder(
        self, self.ui.ExtraCellular_DataRecording_Folder_lineEdit,
        self.ui.ExtraCellular_DataRecording_RecordFolderDir_pushButton,
    )
    self.ui.ExtraCellular_DataRecording_RecordFolder_value.setEnabled(True)
    self.ui.ExtraCellular_DataRecording_RecordFolder_value.setPlaceholderText("Enter a file name")
    self.ui.ExtraCellular_DataRecording_Record_pushButton.setCheckable(True)
    self.ui.ExtraCellular_DataRecording_Record_pushButton.clicked.connect(lambda: self.extracellular_page.RecordButton())
    self.extracellular_page.refresh_recording()
    theme_manager.themeChanged.connect(lambda *_: style_recording_button(
        self.ui.ExtraCellular_DataRecording_Record_pushButton, self.extracellular_graph.recording_active))

    # Open tetrode auxiliary window
    self.ui.ExtraCellular_Tetrode_pushButton.clicked.connect(lambda: openTetrodeWindow(self))

    # ExtraCellular Parameters
    self.ui.ExtraCellular_SignalMode_toggleButton.toggled.connect(self.extracellular_page.SignalMode_toggleButton)

    self.ui.ExtraCellular_Spread_toggleButton.toggled.connect(lambda: self.extracellular_page.ActivateSpatialFalloff())
    self.ui.ExtraCellular_Spread_Slider.valueChanged.connect(lambda: self.extracellular_page.GetSpatialFalloff())
    self.ui.ExtraCellular_BaselineNoise_toggleButton.toggled.connect(lambda: self.extracellular_page.ActivateBaselineNoise())
    self.ui.ExtraCellular_BaselineNoise_Slider.valueChanged.connect(lambda: self.extracellular_page.GetBaselineNoise())
    self.ui.ExtraCellular_SharedNoise_toggleButton.toggled.connect(lambda: self.extracellular_page.ActivateSharedNoise())
    self.ui.ExtraCellular_SharedNoise_Slider.valueChanged.connect(lambda: self.extracellular_page.GetSharedNoise())
    self.ui.ExtraCellular_HumNoise_toggleButton.toggled.connect(lambda: self.extracellular_page.ActivateHumNoise())
    self.ui.ExtraCellular_HumNoise_Slider.valueChanged.connect(lambda: self.extracellular_page.GetHumNoise())
    self.ui.ExtraCellular_CAR_toggleButton.toggled.connect(lambda: self.extracellular_graph.CAR())




    ########################################################################
# Neuron Generator Page - page401
    # Display Page_NeuronGenerator when neuron button is clicked

    # Draw Neuron model based on parameters a, b, c & d
    self.ui.DisplayNeuron_pushButton.clicked.connect(lambda: Page_NeuronGenerator.NeuronGenerator.DrawNeuron(self))

    self.ui.AdvancedParameter_pushButton.clicked.connect(
        lambda: Page_NeuronGenerator.EditAdvancedParameters(self)
    )

    # Load Pre-selected neurons
    self.ui.LoadNeuron_comboBox.currentIndexChanged.connect(lambda: Page_NeuronGenerator.NeuronGenerator.LoadNeuron(self))
    self.ui.NeuronGenerator_open_button.clicked.connect(
        lambda: Page_NeuronGenerator.NeuronGenerator.OpenNeuron(self)
    )
    # Save current neuron
    self.ui.SaveNeuronPushButton.clicked.connect(lambda: Page_NeuronGenerator.NeuronGenerator.SaveNeuron(self))


########################################################################
# Stimulus Generator Page - page501
    # Display Page_StimulusGenerator
    self.ui.StimuluGeneratorMenu_pushButton.clicked.connect(lambda: Page_StimulusGenerator.ShowPage(self))
    # Change Stimulus parameter page
    self.ui.StimulusGenerator_Selection_comboBox.currentIndexChanged.connect(lambda: Page_StimulusGenerator.ChangeStimulusParameter(self))
    # Display stimulus generated
    self.ui.StimulusGenerator_Display_pushButton.clicked.connect(lambda: Page_StimulusGenerator.StimulusGenerator.DrawStimulus(self))
    # Save current stimulus
    self.ui.StimulusGenerator_Save_pushButton.clicked.connect(lambda: Page_StimulusGenerator.StimulusGenerator.SaveStimulus(self))
    # Adapt Chirp page parameters to current selection
    self.ui.Chirp_comboBox.currentIndexChanged.connect(lambda: Page_StimulusGenerator.ChangeChirpParameter(self))


    ########################################################################
    # Settings
    self.ui.SettingsMenu_pushButton.clicked.connect(lambda: self.settings_page.ShowPage())

    ########################################################################
# About - page701
    # Display Info page
    self.ui.AboutMenu_pushButton.clicked.connect(lambda: show_about_page(self))




########################################################################
# GitHub - page801
    # Display Git page
    self.ui.GitHubMenu_pushButton.clicked.connect(lambda: self.github_page.ShowPage())

    ########################################################################


