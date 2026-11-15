"""Qt actions for the Stimulus Generator page."""

from spikeling_gui.appearance.dialogs import show_popup
from spikeling_gui.appearance.theme_manager import theme_manager

from .binary_noise import read_noise
from .cycle import draw_cycle, save_cycle, stimulus_frame
from .intensity_steps import read_steps, read_voltage_steps
from .waveforms import read_chirp, read_periodic


VOLTAGE_MODE_INDEX = 5


def ShowPage(self):
    ui = self.ui
    ui.mainbody_stackedWidget.setCurrentWidget(ui.page_StimulusGenerator)
    ChangeStimulusParameter(self)
    ChangeChirpParameter(self)


def ChangeStimulusParameter(self):
    ui = self.ui
    index = ui.StimulusGenerator_Selection_comboBox.currentIndex()
    voltage = index == VOLTAGE_MODE_INDEX
    ui.StimulusGenerator_Parameter_stackedWidget.setCurrentIndex(index)
    ui.StimulusGenerator_PreLevel_label.setVisible(not voltage)
    ui.StimulusGenerator_PreLevel_edit.setVisible(not voltage)
    plot = ui.StimulusGenerator_Oscilloscope_widget
    plot.clear()
    plot.setTitle("")
    plot.showGrid(x=True, y=True)
    plot.setLabel("left", "Command voltage" if voltage else "Stimulus", units="mV" if voltage else "%")
    plot.setLabel("bottom", "Model time", units="ms")
    theme_manager.set_plot_background_role(plot, "panel_background")


def ChangeChirpParameter(self):
    ui = self.ui
    amplitude_ramp = ui.Chirp_comboBox.currentIndex() == 2
    ui.Chirp_Frequency_Value.setEnabled(amplitude_ramp)
    ui.Chirp_StartFrequency_Value.setEnabled(not amplitude_ramp)
    ui.Chirp_EndFrequency_Value.setEnabled(not amplitude_ramp)


def build_cycle(window):
    ui = window.ui
    index = ui.StimulusGenerator_Selection_comboBox.currentIndex()
    if index in (0, VOLTAGE_MODE_INDEX):
        steps = read_voltage_steps(window) if index == VOLTAGE_MODE_INDEX else read_steps(window)
        return steps.samples, steps
    if index in (1, 2):
        return read_periodic(ui, triangle=index == 2), None
    if index == 3:
        return read_chirp(ui), None
    return read_noise(window), None


def preview_cycle(window, *, save=False):
    try:
        samples, steps = build_cycle(window)
    except ValueError as error:
        show_popup(window, "Invalid stimulus settings", str(error))
        return
    if save and not save_cycle(window, steps.frame if steps is not None else lambda: stimulus_frame(samples)):
        return
    draw_cycle(window, samples, steps.onsets if steps is not None else None,
               voltage=steps is not None and steps.voltage)


class StimulusGenerator:
    def DrawStimulus(self):
        preview_cycle(self)

    def SaveStimulus(self):
        preview_cycle(self, save=True)
