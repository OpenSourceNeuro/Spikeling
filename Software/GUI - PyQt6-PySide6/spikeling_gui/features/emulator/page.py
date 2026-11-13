
########################################################################
#                          Libraries import                            #

from PySide6.QtCore import QSize

from spikeling_gui.widgets.recording import prepare_recording

from spikeling_gui.appearance.dialogs import show_popup
from spikeling_gui.appearance.palette import DarkSolarized
from spikeling_gui.widgets import menu_animation

from . import scope




class Emulator():

    def ShowPage(self):
        self.ui.Emulator_rightMenuContainer.setMinimumSize(QSize(menu_animation.spikerightMenu_max, 16777215))
        self.ui.mainbody_stackedWidget.setCurrentWidget(self.ui.page_Spikeling_NeuronEmulator)
        self.ui.Emulator_Oscilloscope_widget.setBackground(DarkSolarized[0])
        self.ui.Emulator_CustomStimulus_display.setBackground(DarkSolarized[0])
        menu_animation.toggleMenu(self, self.ui.Emulator_rightMenuContainer, menu_animation.spikerightMenu_min, menu_animation.spikerightMenu_max, menu_animation.animation_speed,
                                     self.ui.Emulator_rightMenuSubContainer_pushButton, self.icon_SpikelingMenuRight, self.icon_SpikelingDropMenuRight, True)



    # Data Recording Functions
    def RecordButton(self):
        button = self.ui.Emulator_DataRecording_Record_pushButton
        if not button.isChecked() or button.text() == "Retry save":
            scope.FinishRecording(self)
            return
        if not getattr(self.ui, "EmulatorConnectedFlag", False):
            button.setChecked(False)
            show_popup(self, "Spikeling not connected", "Start the Spikeling emulator before recording.")
            return
        filename = self.ui.Emulator_DataRecording_File_lineEdit
        path = prepare_recording(self, filename.text())
        if path is None:
            button.setChecked(False)
            return
        self.ui.Emulator_recording_path = path
        button.setText("Stop Recording")
        filename.setEnabled(False)
        self.ui.Emulator_DataRecording_Folder_pushButton.setEnabled(False)
        scope.UpdateRecordingState(self)
