"""Apply paired dark and light artwork to Qt widgets and stylesheets."""

import re

from PySide6.QtCore import QFile
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QAbstractButton, QLabel

from spikeling_gui.paths import resource_path


ARTWORK_PROPERTY = "_theme_artwork"
RESOURCE_PREFIX = ":/resources/resources/"
ARTWORK_URL = re.compile(
    r"""url\(\s*['"]?:/resources/resources/([^'"\s)]+\.png)['"]?\s*\)"""
)

# Designer stores QIcons as rendered objects, without a public source filename.
# Keep the artwork bindings here so the generated forms can be rebuilt normally.
MAIN_ARTWORK = {
    "reduce_pushButton": "Hide.png",
    "expand_pushButton": "Expand.png",
    "exit_pushButton": "Exit.png",
    "menu_pushButton": "DropMenuLeft.png",
    "SpikelingMenu_pushButton": "Neuron.png",
    "ImagingMenu_pushButton": "Imaging.png",
    "Tetrode_pushButton": "Tetrode_Spikes.png",
    "NeuronGeneratorMenu_pushButton": "NeuroGen.png",
    "StimuluGeneratorMenu_pushButton": "StimGen.png",
    "SettingsMenu_pushButton": "Tutorial.png",
    "AboutMenu_pushButton": "About.png",
    "GitHubMenu_pushButton": "GitHub.png",
    "centerMenuSubContainer_exit_pushButton": "DropMenuLeft.png",
    "Neuron_pushButton": "Neuron.png",
    "NeuronEmulator_pushButton": "Neuron.png",
    "NeuronDataAnalysis_pushButton": "DataAnalysis.png",
    "NeuronTutorial_pushButton": "Tutorial.png",
    "ImagingStimulation_pushButton": "Imaging.png",
    "ImagingDataAnalysis_pushButton": "DataAnalysis.png",
    "ImagingTutorial_pushButton": "Tutorial.png",
    "ExtraCellularScope_pushButton": "Scope.png",
    "ExtraCellularSpikes_pushButton": "Tetrode_Spikes.png",
    "ExtraCellularSorting_pushButton": "Tetrode_Sorting.png",
    "ExtraCellularTutorial_pushButton": "Tutorial.png",
    "LED_pushButton": "LEDON.png",
    "Sound_pushButton": "SoundON.png",
    "Spikeling_parameter_exit_pushButton": "DropMenuRight.png",
    "Spikeling_rightMenuSubContainer_pushButton": "MenuRight.png",
    "Spikeling_StimulusParameter_pushButton": "StimGen.png",
    "Spikeling_NeuronParameter_pushButton": "Neuron.png",
    "Spikeling_PharmacologyParameter_pushButton": "Pharmacology.png",
    "Spikeling_Synapse1Parameter_pushButton": "Synapse1.png",
    "Spikeling_Synapse2Parameter_pushButton": "Synapse2.png",
    "Emulator_parameter_exit_pushButton": "DropMenuRight.png",
    "Emulator_rightMenuSubContainer_pushButton": "MenuRight.png",
    "Emulator_StimulusParameter_pushButton": "StimGen.png",
    "Emulator_NeuronParameter_pushButton": "Neuron.png",
    "Emulator_PharmacologyParameter_pushButton": "Pharmacology.png",
    "Emulator_AuxiliaryNeuron1Parameter_pushButton": "Neuron_teal.png",
    "Emulator_Synapse1Parameter_pushButton": "Synapse1_teal.png",
    "Emulator_AuxiliaryNeuron2Parameter_pushButton": "Neuron_pink.png",
    "Emulator_Synapse2Parameter_pushButton": "Synapse2_pink.png",
    "Imaging_parameter_exit_pushButton": "DropMenuRight.png",
    "Imaging_rightMenuSubContainer_pushButton": "MenuRight.png",
    "Imaging_ImagingParameter_pushButton": "Imaging.png",
    "Imaging_CalciumParameter_pushButton": "Calcium.png",
    "Imaging_FluoParameter_pushButton": "LEDON.png",
    "Spikeling_StimFre_image": "StimFrequency.png",
    "Spikeling_StimStr_image": "StimStrenght.png",
    "Emulator_StimFre_image": "StimFrequency.png",
    "Emulator_StimStr_image": "StimStrenght.png",
    "NeuronGenerator_Izhik_image": "izhik.png",
    "mainbody_header_logo": "SpikyLogo.png",
    "OSN_logo": "SpikyLogo.png",
    "sussex_logo": "SN-Logo.png",
    "trend_logo": "CaMinA.png",
    "label": "SizeGrip.png",
}


def artwork_path(filename: str, light: bool) -> str:
    """Prefer the requested variant, using Qt resources or bundled loose files."""
    stem, dot, extension = filename.rpartition(".")
    light_name = f"{stem}_light{dot}{extension}"
    candidates = (light_name, filename) if light and dot else (filename,)
    for candidate in candidates:
        embedded = RESOURCE_PREFIX + candidate
        if QFile.exists(embedded):
            return embedded
        loose = resource_path("resources", candidate)
        if loose.is_file():
            return loose.as_posix()
    return RESOURCE_PREFIX + filename


def apply_artwork(widget, light: bool) -> None:
    filename = widget.property(ARTWORK_PROPERTY)
    if not filename:
        return
    path = artwork_path(filename, light)
    if isinstance(widget, QAbstractButton):
        widget.setIcon(QIcon(path))
    elif isinstance(widget, QLabel):
        widget.setPixmap(QPixmap(path))


def substitute_artwork(stylesheet: str, light: bool) -> str:
    return ARTWORK_URL.sub(
        lambda match: f'url("{artwork_path(match.group(1), light)}")',
        stylesheet,
    )
