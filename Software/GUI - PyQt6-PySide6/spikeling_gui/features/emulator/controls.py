# SPDX-License-Identifier: GPL-3.0-or-later
"""Bind the emulator controls to local simulation settings."""

from pathlib import Path

import numpy as np
import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import QFileDialog

from spikeling_gui.appearance.dialogs import show_popup
from spikeling_gui.appearance.palette import DarkSolarized
from spikeling_gui.features.neuron_interface.probabilistic_release import edit_release_settings
from spikeling_gui.features.neuron_interface.short_term_plasticity import PRESETS, edit_stp_settings
from spikeling_gui.neuron_presets import IzhikevichNeurons
from spikeling_gui.neuron_csv import NEURON_COLUMNS, read_neuron_csv
from spikeling_gui.paths import data_directory
from spikeling_gui.stimulus_schedule import NO_STEP, read_step_schedule
from spikeling_gui.recording_metadata import drug_setting
from spikeling_gui.widgets.sliders import SliderBinding

from . import scope
from .models import RELEASE_SEED, drug_block

# Firmware drug index order. Positions provide the same precision as the device controls.
DRUGS = (
    ("TTX", 10, 1, "TTX (nM)"),
    ("TEA", 100, 2, "TEA (mM)"),
    ("Apamin", 10, 1, "Apamin (nM)"),
    ("4AP", 100, 2, "4-AP (mM)"),
    ("NBQX", 100, 2, "NBQX (µM)"),
    ("Gabazine", 100, 2, "Gabazine (µM)"),
    ("APV", 10, 1, "APV (µM)"),
    ("GVIA", 10, 1, "ω-GVIA (nM)"),
)


NEURON_DEFAULTS = (0, 100, 25, 0, 995, 0, 990)
PRESET_SLIDERS = ("PR_PhotoGain", "PR_Decay", "PR_Recovery", "Synapse1",
                  "Synapse1_Decay", "Synapse2", "Synapse2_Decay")


class EmulatorControls:
    def __init__(self, host):
        self.host = host
        self.ui = ui = host.ui
        self.bindings = {}
        self.drugs = []
        self.releases = []
        self.release_seed = RELEASE_SEED
        self.release_seed_revision = 0
        self.stp_presets = [list(PRESETS), list(PRESETS)]
        self.stp_revision = [0, 0]
        self.samples = None
        self.playback_index = None
        self.step_schedule = {}
        self.playback_loops = 1
        self.stimulus_hold = 0
        self.stimulus_filtered = 0.0
        self.playback_finished = False
        self.membrane_revision = 0
        self.neuron_revision = 0
        self.rest_voltage = float(IzhikevichNeurons[0][4])
        self.aux_rest = [self.rest_voltage] * 2
        self.aux_revision = [0, 0]
        self.toggles = {}
        ui.Emulator_a, ui.Emulator_b, ui.Emulator_c, ui.Emulator_d = IzhikevichNeurons[0][:4]
        for channel in (1, 2):
            for parameter, value in zip("abcd", IzhikevichNeurons[0][:4]):
                setattr(ui, f"Emulator_{parameter}{channel}", value)

        main_selector = self.neuron_selector(0)
        for index in range(len(IzhikevichNeurons)):
            main_selector.setItemData(index, index)
        for channel in (1, 2):
            selector = self.neuron_selector(channel)
            prompt = selector.itemText(0)
            selector.clear()
            selector.addItem(prompt)
            for index in range(len(IzhikevichNeurons)):
                selector.addItem(main_selector.itemText(index), index)

        ui.EmulatorStimChoiceCurrent_toggleButton.setChecked(True)
        self.bind("StimFre", ui.EmulatorStimFre_toggleButton, 0,
                  display=lambda position: 10000 / (510 - 5 * position),
                  position=lambda hz: (510 - 10000 / hz) / 5 if hz > 0 else -1000,
                  format_value=lambda hz: f"{hz:.1f}", colour=5)
        self.bind("StimStr", ui.EmulatorStimStr_toggleButton, 0, colour=5)
        self.bind("PatchClamp", ui.EmulatorPatchClamp_toggleButton, 0, colour=4)
        self.bind("Noise", ui.EmulatorNoise_toggleButton, 0, colour=4)
        self.bind("PR_PhotoGain", ui.EmulatorPhotoGain_toggleButton, 0,
                  editor="PR_Photogain", colour=4)
        self.bind("PR_Decay", ui.EmulatorPhotoDecay_toggleButton, 100, scale=100000, colour=4)
        self.bind("PR_Recovery", ui.EmulatorPhotoRecovery_toggleButton, 25, scale=1000, colour=4)
        for channel, default, colour in ((1, 995, 7), (2, 990, 10)):
            self.bind(f"Synapse{channel}", getattr(ui, f"EmulatorSynapse{channel}_toggleButton"),
                      0, editor=f"Synapse{channel}_Gain", colour=colour)
            self.bind(f"Synapse{channel}_Decay",
                      getattr(ui, f"EmulatorSynapse{channel}Decay_toggleButton"),
                      default, scale=1000, colour=colour)
            self.configure_synapse(channel, colour)
            self.configure_auxiliary(channel)

        for key, scale, decimals, label in DRUGS:
            prefix = f"Pharmacology_{key}"
            getattr(ui, f"Emulator_{prefix}_Label").setText(label)
            toggle = getattr(ui, f"Emulator_{prefix}_toggleButton")
            binding = self.bind(prefix, toggle, 0, scale=scale, limits=(0, 1000), colour=8,
                                format_value=lambda value, places=decimals: f"{value:.{places}f}")
            self.drugs.append((toggle, binding, scale))

        ui.Emulator_Pharmacology_Clear_pushButton.setEnabled(True)
        ui.Emulator_Pharmacology_Clear_pushButton.clicked.connect(self.clear_drugs)
        ui.Emulator_PatchClampMode_toggleButton.toggled.connect(self.configure_clamp_mode)
        ui.Emulator_PatchClamp_MembraneModel_comboBox.currentIndexChanged.connect(
            self.membrane_changed
        )
        self.configure_clamp_mode(ui.Emulator_PatchClampMode_toggleButton.isChecked())
        ui.Emulator_NeuronBrowsePushButton.clicked.connect(lambda: self.browse_neuron(0))
        ui.Emulator_NeuronMode_pushButton.clicked.connect(lambda: self.select_neuron(0))

        editor = ui.Emulator_CustomStimulus_Loop_lineEdit
        editor.setValidator(QIntValidator(1, 1000000, editor))
        editor.setAlignment(Qt.AlignmentFlag.AlignCenter)
        editor.setText("1")
        ui.Emulator_CustomStimulus_Load_pushButton.clicked.connect(self.load_stimulus)
        ui.EmulatorStimCus_toggleButton.toggled.connect(self.toggle_playback)
        self.refresh_playback()

    def bind(self, key, toggle, default, *, editor=None, scale=1, colour=5,
             limits=None, display=None, position=None, format_value=lambda value: f"{value:g}"):
        slider = getattr(self.ui, f"Emulator_{key}_slider")
        reading = getattr(self.ui, f"Emulator_{editor or key}_readings")
        reading.setReadOnly(False)
        if limits:
            slider.setRange(*limits)
        slider.setValue(default)
        binding = SliderBinding(
            slider, reading, alignment=Qt.AlignmentFlag.AlignCenter,
            active=toggle.isChecked(), default_position=default, disabled_text="",
            active_editor_style=f"color: rgb{tuple(DarkSolarized[colour])}; font: 700 10pt;",
            to_display=display or (lambda value: value / scale),
            to_slider=position or (lambda value: value * scale),
            format_value=format_value,
        )
        toggle.toggled.connect(binding.set_active)
        self.bindings[key] = binding
        self.toggles[key] = toggle
        return binding

    def configure_clamp_mode(self, voltage_clamp):
        ui = self.ui
        minimum, maximum, default = (-110, 30, -70) if voltage_clamp else (-100, 100, 0)
        colour = "#DC322F" if voltage_clamp else "#859900"
        self.bindings["PatchClamp"].reconfigure(
            minimum=minimum, maximum=maximum, default_position=default,
            active_editor_style=f"color: {colour}; font: 700 10pt;",
        )
        ui.Emulator_PatchClamp_slider.set_fill_color(colour)
        ui.EmulatorPatchClamp_toggleButton.set_active_color(colour)
        ui.Emulator_CurrentClamp_label.setStyleSheet(
            "color: #586E75; font: 700 10pt;" if voltage_clamp else "color: #859900; font: 700 10pt;"
        )
        ui.Emulator_VoltageClamp_label.setStyleSheet(
            "color: #DC322F; font: 700 10pt;" if voltage_clamp else "color: #586E75; font: 700 10pt;"
        )
        ui.Emulator_PatchClamp_Label.setText(
            "Holding Voltage (mV)" if voltage_clamp else "Injected Current (a.u.)"
        )
        for key, value in zip(("min", "0", "max"), (minimum, (minimum + maximum) // 2, maximum)):
            getattr(ui, f"Emulator_PatchClamp_values_{key}").setText(str(value))
        ui.Emulator_PatchClamp_MembraneModel_comboBox.setEnabled(voltage_clamp)
        ui.Emulator_PatchClamp_MembraneModel_label.setStyleSheet(
            "color: #BECDCD;" if voltage_clamp else "color: #586E75;"
        )
        self.membrane_changed()

    def membrane_changed(self, *_):
        self.membrane_revision += 1
        self.ui.Emulator_InputCurrentCheckbox.setText(
            "Clamp Current" if self.voltage_clamp else "Input Current"
        )
        if getattr(self.ui, "EmulatorConnectedFlag", False):
            scope.FinishRecording(self.host)
            scope.ConfigureCurrentAxis(self.host, self.voltage_clamp)

    @property
    def voltage_clamp(self):
        return self.ui.Emulator_PatchClampMode_toggleButton.isChecked()

    @property
    def active_membrane(self):
        return self.ui.Emulator_PatchClamp_MembraneModel_comboBox.currentText().casefold() == "active"

    def configure_auxiliary(self, channel):
        ui = self.ui
        prefix = f"AuxiliaryNeuron{channel}"
        for key, toggle, default, scale in (
            ("PatchClamp", "PatchClamp", 0, 1),
            ("Noise", "Noise", 0, 1),
            ("PR_PhotoGain", "PhotoGain", 0, 1),
            ("PR_Decay", "PhotoDecay", 100, 100000),
            ("PR_Recovery", "PhotoRecovery", 25, 1000),
        ):
            self.bind(f"{prefix}_{key}", getattr(ui, f"EmulatorSyn{channel}_{toggle}_toggleButton"),
                      default, scale=scale, colour=4,
                      editor=f"{prefix}_PR_Photogain" if key == "PR_PhotoGain" else None,
                      limits=(-50, 50) if key == "PatchClamp" else None)

        connection = getattr(ui, f"EmulatorSyn{channel}_Synapse_toggleButton")
        current = getattr(ui, f"EmulatorSyn{channel}_StimDC_toggleButton")
        light = getattr(ui, f"EmulatorSyn{channel}_StimLight_toggleButton")

        def refresh(*_):
            connected = connection.isChecked()
            for widget in (current, light):
                widget.setEnabled(connected)
            for key in ("PatchClamp", "Noise", *PRESET_SLIDERS[:3]):
                available = connected and (key in ("PatchClamp", "Noise") or light.isChecked())
                toggle = self.toggles[f"{prefix}_{key}"]
                binding = self.bindings[f"{prefix}_{key}"]
                toggle.setEnabled(available)
                binding.slider.setEnabled(available and toggle.isChecked())
                binding.editor.setEnabled(available and toggle.isChecked())

        connection.toggled.connect(refresh)
        light.toggled.connect(refresh)
        getattr(ui, f"Emulator_{prefix}_Mode_Browse_pushButton").clicked.connect(
            lambda: self.browse_neuron(channel)
        )
        getattr(ui, f"Emulator_{prefix}_Mode_Apply_pushButton").clicked.connect(
            lambda: self.select_neuron(channel)
        )
        refresh()

    def neuron_selector(self, channel):
        if channel:
            return getattr(self.ui, f"Emulator_AuxiliaryNeuron{channel}_Mode_comboBox")
        return self.ui.Emulator_NeuronModeComboBox

    def browse_neuron(self, channel):
        path, _ = QFileDialog.getOpenFileName(
            self.host, "Select neuron", str(data_directory("Neurons")), "CSV files (*.csv)"
        )
        if not path:
            return
        try:
            parameters = read_neuron_csv(path)
        except (OSError, ValueError) as error:
            show_popup(self.host, "Cannot load neuron", str(error))
            return
        selector = self.neuron_selector(channel)
        selector.addItem(Path(path).stem, tuple(map(float, parameters)))
        selector.setCurrentIndex(selector.count() - 1)

    def select_neuron(self, channel):
        selected = self.neuron_selector(channel).currentData()
        if selected is None:
            return
        if isinstance(selected, int):
            parameters = IzhikevichNeurons[selected]
            rest = float(parameters[4])
            defaults = NEURON_DEFAULTS
        else:
            parameters = selected
            rest = -65.0
            defaults = (parameters[4], parameters[5] * 100000, parameters[6] * 1000,
                        parameters[7], parameters[8] * 1000, parameters[9], parameters[10] * 1000)
        suffix = str(channel) if channel else ""
        for parameter, value in zip("abcd", parameters):
            setattr(self.ui, f"Emulator_{parameter}{suffix}", float(value))
        if channel:
            self.aux_rest[channel - 1] = rest
            self.aux_revision[channel - 1] += 1
            keys = tuple(f"AuxiliaryNeuron{channel}_{key}" for key in PRESET_SLIDERS[:3])
        else:
            self.rest_voltage = rest
            self.neuron_revision += 1
            keys = PRESET_SLIDERS
        for key, value in zip(keys, defaults):
            binding = self.bindings[key]
            slider = binding.slider
            value = max(slider.minimum(), min(slider.maximum(), round(float(value))))
            binding.reconfigure(minimum=slider.minimum(), maximum=slider.maximum(),
                                default_position=value)

    def clear_drugs(self):
        for toggle, binding, _ in self.drugs:
            toggle.setChecked(False)
            binding.set_value(0)

    def recording_drugs(self):
        return [drug_setting(label, binding, scale)
                for (_, _, _, label), (_, binding, scale) in zip(DRUGS, self.drugs)]

    def pharmacology(self):
        concentrations = [binding.value / scale if binding.active else 0.0
                          for _, binding, scale in self.drugs]
        enabled = any(binding.active for _, binding, _ in self.drugs)
        probabilities = tuple(binding.value / 100 if binding.active else None
                              for binding, _ in self.releases)
        return (drug_block(concentrations), enabled or any(p is not None for p in probabilities),
                self.drugs[6][1].active, probabilities,
                tuple(sites for _, sites in self.releases))

    def configure_synapse(self, channel, colour):
        ui = self.ui
        prefix = f"Emulator_Synapse{channel}"
        index = channel - 1
        release = self.bind(f"Synapse{channel}_Release", getattr(ui, f"{prefix}_Release_toggleButton"),
                            35, scale=100, limits=(1, 100), colour=colour,
                            format_value=lambda probability: f"{probability:.2f}")
        self.releases.append((release, 4))
        advanced_release = getattr(ui, f"{prefix}_Release_Advanced_pushButton")
        advanced_release.setEnabled(True)
        advanced_release.clicked.connect(lambda: self.edit_release(channel))
        selector = getattr(ui, f"{prefix}_STP_comboBox")
        advanced = getattr(ui, f"{prefix}_STP_Advanced_pushButton")
        reset = getattr(ui, f"{prefix}_STP_Reset_pushButton")
        selector.setEnabled(True)
        selector.setCurrentIndex(0)

        def update(mode):
            advanced.setEnabled(mode > 0)
            reset.setEnabled(mode > 0)
            self.stp_revision[index] += 1

        selector.currentIndexChanged.connect(update)
        reset.clicked.connect(lambda: update(selector.currentIndex()))

        def edit():
            mode = selector.currentIndex()
            def apply(parameters):
                self.stp_presets[index][mode] = parameters
                update(mode)
                return True
            edit_stp_settings(selector, channel, mode, self.stp_presets[index][mode], apply)

        advanced.clicked.connect(edit)
        update(0)

    def stp_settings(self, index):
        selector = getattr(self.ui, f"Emulator_Synapse{index + 1}_STP_comboBox")
        return self.stp_presets[index][selector.currentIndex()]

    def edit_release(self, channel):
        binding, sites = self.releases[channel - 1]
        settings = edit_release_settings(self.host, channel, sites, self.release_seed)
        if settings is not None:
            sites, seed = settings
            self.releases[channel - 1] = binding, sites
            if seed != self.release_seed:
                self.release_seed = seed
                self.release_seed_revision += 1

    def load_stimulus(self):
        path, _ = QFileDialog.getOpenFileName(
            self.host, "Select a custom stimulus", str(data_directory("Stimuli")), "CSV files (*.csv)"
        )
        if not path:
            return
        try:
            frame = pd.read_csv(path)
            if "Stim" not in frame:
                raise ValueError("The CSV must contain a column named 'Stim'.")
            samples = pd.to_numeric(frame["Stim"], errors="raise").to_numpy(dtype=float)
            if not samples.size or not np.isfinite(samples).all():
                raise ValueError("The stimulus must contain finite samples.")
            if (np.abs(samples) > 100).any() or not np.allclose(samples, np.rint(samples), rtol=0, atol=1e-9):
                raise ValueError("Enter integer stimulus values between -100 and 100.")
            samples = np.rint(samples).astype(np.int16)
            step_schedule = read_step_schedule(frame, samples)
        except (OSError, ValueError) as error:
            show_popup(self.host, "Cannot load stimulus", str(error))
            return
        self.samples = samples
        self.step_schedule = step_schedule
        self.ui.Emulator_CustomStimulus_StimLabel.setText(Path(path).stem)
        preview = self.ui.Emulator_CustomStimulus_display
        preview.clear()
        preview.setLabel("bottom", "Model time", units="ms")
        preview.setLabel("left", "Stimulus", units="%")
        preview.plot(np.arange(samples.size) * 0.1, samples, pen=DarkSolarized[5])
        self.refresh_playback()

    def refresh_playback(self):
        ui = self.ui
        playing = self.playback_index is not None
        ui.EmulatorStimCus_toggleButton.setEnabled(
            playing or (self.samples is not None and getattr(ui, "EmulatorConnectedFlag", False))
        )
        ui.Emulator_CustomStimulus_Load_pushButton.setEnabled(not playing)
        ui.Emulator_CustomStimulus_Loop_lineEdit.setEnabled(not playing)
        ui.Emulator_CustomStimulus_Label.setText("Stop stimulus" if playing else "Apply stimulus")
        for toggle in (ui.EmulatorStimFre_toggleButton, ui.EmulatorStimStr_toggleButton):
            toggle.setEnabled(not playing)

    def toggle_playback(self, enabled):
        if not enabled:
            self.stop_playback()
            return
        editor = self.ui.Emulator_CustomStimulus_Loop_lineEdit
        if self.samples is None or not getattr(self.ui, "EmulatorConnectedFlag", False) or not editor.hasAcceptableInput():
            self.stop_playback()
            return
        self.ui.EmulatorStimFre_toggleButton.setChecked(False)
        self.ui.EmulatorStimStr_toggleButton.setChecked(False)
        self.playback_loops = editor.validator().locale().toInt(editor.text())[0]
        self.playback_index = 0
        self.playback_finished = False
        self.stimulus_hold = 0
        self.stimulus_filtered = 0.0
        self.refresh_playback()

    def next_sample(self):
        index = self.playback_index
        if index is None:
            return None
        cycle_index = index % len(self.samples)
        sample = int(self.samples[cycle_index])
        if abs(sample - self.stimulus_hold) > 2:
            self.stimulus_hold = sample
        self.stimulus_filtered += 0.25 * (self.stimulus_hold - self.stimulus_filtered)
        stimulus = round(self.stimulus_filtered)
        trigger = cycle_index == 0
        self.playback_index += 1
        if self.playback_index == len(self.samples) * self.playback_loops:
            self.playback_index = None
            self.playback_finished = True
        return stimulus, trigger, self.step_schedule.get(cycle_index, NO_STEP)

    def stop_playback(self):
        self.playback_index = None
        self.playback_finished = False
        if self.ui.EmulatorStimCus_toggleButton.isChecked():
            self.ui.EmulatorStimCus_toggleButton.setChecked(False)
            return
        self.refresh_playback()
