"""Desktop Spikeling oscilloscope and simulation lifecycle."""

from dataclasses import dataclass
from math import copysign

from PySide6.QtCore import QTimer
import pyqtgraph as pg

import numpy as np

from spikeling_gui.appearance.dialogs import show_popup
from spikeling_gui.appearance.palette import DarkSolarized
from spikeling_gui.appearance.theme_manager import theme_manager
from spikeling_gui.plotting.graph_core import RingBuffer, apply_scope_timebase, configure_scope
from spikeling_gui import speed_model as speed
from spikeling_gui.stimulus_schedule import NO_STEP, save_step_channels
from spikeling_gui.recording_metadata import RecordingMetadata, stp_parameters, write_recording

from .models import CURRENT_TO_NA, IntrinsicPharmacology, Synapse, VoltageClamp, izhikevich

# --- Speed control ---------------------------------------------------------
# STEPS_PER_UPDATE_BY_SLIDER, REALTIME_STEPS_PER_UPDATE and GUI_TICK_MS have
# moved to speed_model, which the hardware page shares. The old denominator
# of 10000 was 20x the correct GUI_TICK_MS / dt = 500, so every emulator
# speed was reported twenty times too slow.
GUI_TICK_MS = int(speed.GUI_TICK_MS)

# --- Display / buffering ---------------------------------------------------
EMULATOR_SAMPLE_INTERVAL_MS = 0.1       # integration step, matches firmware dt
EMULATOR_TIME_WINDOW_MS = 5000          # rolling buffer length
EMULATOR_TIME_WINDOW_DISPLAY_MS = 500   # initial visible x-range
N_EMULATOR_CHANNELS = 8

# --- Photodiode model ------------------------------------------------------
PHOTODIODE_DECAY_SCALE = 100000.0
PHOTODIODE_RECOVERY_SCALE = 1000.0

# --- Plot y-ranges ---------------------------------------------------------
VM_MIN_MV, VM_MAX_MV = -90, 30
CURRENT_MIN, CURRENT_MAX = -100, 100


@dataclass(slots=True)
class EmulatorUISnapshot:
    """Freeze UI parameters for one oscilloscope update."""

    izh: tuple
    aux_parameters: tuple
    stim_strength: float
    stim_period: int
    stim_as_light: bool
    stim_as_current: bool
    patch_clamp: float
    voltage_clamp: bool
    active_membrane: bool
    noise_sigma: float
    photo_gain: float
    photo_decay: float
    photo_recovery: float
    syn_enabled: tuple
    syn_patch_clamp: tuple
    syn_noise_sigma: tuple
    syn_gain: tuple
    syn_decay: tuple
    syn_as_current: tuple
    syn_as_light: tuple
    syn_photo_gain: tuple
    syn_photo_decay: tuple
    syn_photo_recovery: tuple
    block: tuple
    pharmacology: bool
    nmda: bool
    probabilities: tuple
    sites: tuple

    @classmethod
    def from_controls(cls, controls):
        ui = controls.ui

        def read(name):
            return float(getattr(ui, f"Emulator_{name}_slider").value())

        def aux_read(name, scale=1):
            return tuple(read(f"AuxiliaryNeuron{channel}_{name}") / scale for channel in (1, 2))

        def aux_checked(name):
            return tuple(getattr(ui, f"EmulatorSyn{channel}_{name}_toggleButton").isChecked()
                         for channel in (1, 2))

        block, pharmacology, nmda, probabilities, sites = controls.pharmacology()
        return cls(
            izh=(ui.Emulator_a, ui.Emulator_b, ui.Emulator_c, ui.Emulator_d),
            aux_parameters=tuple(tuple(getattr(ui, f"Emulator_{key}{channel}") for key in "abcd")
                                 for channel in (1, 2)),
            stim_strength=read("StimStr"),
            stim_period=int(510 - 5 * read("StimFre")),
            stim_as_light=ui.EmulatorStimChoiceLight_toggleButton.isChecked(),
            stim_as_current=ui.EmulatorStimChoiceCurrent_toggleButton.isChecked(),
            patch_clamp=read("PatchClamp"),
            voltage_clamp=controls.voltage_clamp,
            active_membrane=controls.active_membrane,
            noise_sigma=read("Noise") * (25 / 100) * (14 / 15) * 0.5,
            photo_gain=read("PR_PhotoGain"),
            photo_decay=read("PR_Decay") / PHOTODIODE_DECAY_SCALE,
            photo_recovery=read("PR_Recovery") / PHOTODIODE_RECOVERY_SCALE,
            syn_enabled=aux_checked("Synapse"),
            syn_patch_clamp=aux_read("PatchClamp"),
            syn_noise_sigma=aux_read("Noise", 60 / 7),
            syn_gain=(read("Synapse1") * 0.25, read("Synapse2") * 0.25),
            syn_decay=(read("Synapse1_Decay") / 1000, read("Synapse2_Decay") / 1000),
            syn_as_current=aux_checked("StimDC"),
            syn_as_light=aux_checked("StimLight"),
            syn_photo_gain=aux_read("PR_PhotoGain"),
            syn_photo_decay=aux_read("PR_Decay", PHOTODIODE_DECAY_SCALE),
            syn_photo_recovery=aux_read("PR_Recovery", PHOTODIODE_RECOVERY_SCALE),
            block=block, pharmacology=pharmacology, nmda=nmda,
            probabilities=probabilities, sites=sites,
        )


def photodiode_step(stimulus, gain, recovery, decay_rate, recovery_rate):
    """
    Advance the adapting photodiode model by one step.

    The photocurrent is scaled by a slowly adapting availability term that is
    depleted in proportion to the emitted current and relaxes back to unity,
    reproducing the light adaptation of the Spikeling photodetector front end.

    Parameters
    ----------
    stimulus : float
        Stimulus state (%).
    gain : float
        Signed photodiode gain; the sign sets ON vs OFF polarity.
    recovery : float
        Current availability in ``[0, 1]``.
    decay_rate, recovery_rate : float
        Depletion and relaxation rates, already slider-scaled.

    Returns
    -------
    current : float
        Photodiode current for this step (a.u.).
    recovery : float
        Updated availability.
    """
    polarity = 1.0 if gain >= 0.0 else -1.0
    current = 0.01 * stimulus * gain * recovery

    if recovery > 0.0:
        recovery -= polarity * decay_rate * current
    if recovery < 0.0:
        recovery = 0.0
    if recovery < 1.0:
        recovery += recovery_rate

    return current, recovery


def EmulatorPlot(self):
    """
    Start or stop the emulator from the connect button.

    Parameters
    ----------
    self : object
        Main window owning ``self.ui`` and the emulator runtime state.
    """
    if self.ui.Emulator_Connect_pushButton.isChecked():
        if not FinishRecording(self):
            self.ui.Emulator_Connect_pushButton.setChecked(False)
            return
        SetInitParameters(self)
        SetPlotCurve(self)
        SetPlot(self)

        self.Emulator_timer = QTimer(self)
        self.Emulator_timer.timeout.connect(lambda: UpdatePlot(self))
        self.Emulator_timer.start(GUI_TICK_MS)
        return

    self.ui.Emulator_Connect_pushButton.setText("Start Spikeling Emulator")
    self.ui.Emulator_Connect_pushButton.setStyleSheet(
        "color: rgb" + str(tuple(DarkSolarized[14])) + ";\n"
        "background-color: rgb" + str(tuple(DarkSolarized[2])) + ";\n"
        "border: 1px solid rgb" + str(tuple(DarkSolarized[14])) + ";\n"
        "border-radius: 10px;"
    )

    if hasattr(self, "Emulator_timer"):
        self.Emulator_timer.stop()
        self.Emulator_timer.deleteLater()
    FinishRecording(self)

    timebase = getattr(self, "Emulator_timebase", None)
    if timebase is not None:
        timebase.stop()
        self.Emulator_timebase = None

    self.ui.Emulator_Oscilloscope_widget.clear()
    self.ui.Emulator_Oscilloscope_widget.getAxis("right").unlinkFromView()
    for view in (self.Emulator_CurrentPlots, self.Emulator_StimulusPlots):
        view.clear()
        view.setXLink(None)
        if view.scene() is not None:
            view.scene().removeItem(view)
    self.Emulator_CurrentPlots = None
    self.Emulator_StimulusPlots = None

    self.ui.EmulatorConnectedFlag = False
    self.emulator_controls.stop_playback()


def recording_settings(controls, state, period, playing):
    ui = controls.ui
    if playing:
        stimulus = {
            "kind": "custom", "name": ui.Emulator_CustomStimulus_StimLabel.text(),
            "samples_per_loop": len(controls.samples), "loops": controls.playback_loops,
            "step_ms": EMULATOR_SAMPLE_INTERVAL_MS,
        }
    else:
        stimulus = {"kind": "square", "period_ms": period * EMULATOR_SAMPLE_INTERVAL_MS,
                    "strength_percent": state.stim_strength}
    stimulus.update({"soma_current": state.stim_as_current, "soma_light": state.stim_as_light,
                     "aux_current": state.syn_as_current, "aux_light": state.syn_as_light})
    return {
        "clamp": {
            "mode": "VC" if state.voltage_clamp else "CC",
            "membrane_model": ("active" if state.active_membrane else "passive") if state.voltage_clamp else None,
            "holding_voltage_mv": state.patch_clamp if state.voltage_clamp else None,
            "injected_current_au": None if state.voltage_clamp else state.patch_clamp,
        },
        "neuron_parameters": state.izh,
        "aux_neuron_parameters": state.aux_parameters,
        "stimulus": stimulus,
        "drugs": controls.recording_drugs(),
        "synaptic_stp": {
            str(i + 1): {
                "enabled": state.syn_enabled[i],
                "mode": getattr(ui, f"Emulator_Synapse{i + 1}_STP_comboBox").currentIndex(),
                **stp_parameters(controls.stp_settings(i)),
            } for i in range(2)
        },
        "release_seed": controls.release_seed,
        "probabilistic_release": {
            str(i + 1): {"probability": state.probabilities[i], "sites": state.sites[i]} for i in range(2)
        },
    }


def UpdatePlot(self):
    """
    Advance the emulator by one GUI tick and refresh the oscilloscope.

    The speed slider indexes the ladder shared with the hardware page, so the
    same position yields the same displayed factor on both. Fractional step
    counts (2.5 per tick at ``x 0.005``) are carried by
    :class:`speed_model.FractionalStepScheduler` rather than truncated, which
    would otherwise run the model up to 20 % slow.
    """
    setting = speed.setting_for_index(self.ui.Emulator_Speed_slider.value())
    steps_per_update = self._emulator_step_scheduler.take(
        setting.emulator_steps_per_tick)
    self.ui.Emulator_Speed_value.setText(setting.label)

    # --- Once-per-tick UI sampling and RNG ------------------------------
    controls = self.emulator_controls
    ui_state = EmulatorUISnapshot.from_controls(controls)
    SyncModelSettings(self, ui_state)

    noise_block = self._emulator_rng.standard_normal((steps_per_update, 3))
    noise_block *= np.array([ui_state.noise_sigma,
                             ui_state.syn_noise_sigma[0],
                             ui_state.syn_noise_sigma[1]], dtype=float)

    # --- Downstream consumers -------------------------------------------
    imaging_graph = getattr(self, "imaging_graph", None)
    imaging_enabled = (imaging_graph is not None
                       and getattr(self, "ImagingConnectionFlag", False)
                       and imaging_graph.source_mode == "emulator")

    extracellular_graph = getattr(self, "extracellular_graph", None)
    extracellular_enabled = (extracellular_graph is not None
                             and getattr(self, "ExtraCellularConnectionFlag", False)
                             and extracellular_graph.source_mode == "emulator")

    forward_batch = [] if (imaging_enabled or extracellular_enabled) else None

    # --- Integration loop -------------------------------------------------
    recording_channels = self._emulator_recording_channels if self.recordflag else None
    previous_stimulus = None
    for noise in noise_block.tolist():
        if recording_channels is not None:
            playing = controls.playback_index is not None
            period = self.Emulator_StimSteps
            schedule = (playing, period)
            if schedule != previous_stimulus:
                self._emulator_recording_metadata.observe(
                    len(self.EmulatorData[1]), recording_settings(controls, ui_state, period, playing),
                )
                previous_stimulus = schedule
        vec8 = GetData(self, ui_state, noise, recording_channels)
        self.ui.Emulator_Data = vec8

        for channel in range(N_EMULATOR_CHANNELS):
            self.Emulator_buffers[channel].append(vec8[channel])

        if self.recordflag:
            for channel in range(N_EMULATOR_CHANNELS):
                self.EmulatorData[channel + 1].append(vec8[channel])

        if forward_batch is not None:
            forward_batch.append([self.Emulator_sim_time_ms] + vec8)

    if self.recordflag:
        count = len(self.EmulatorData[1])
        self.ui.Emulator_DataRecording_Record_label.setText(
            f"Recording · {count:,} samples · {count * EMULATOR_SAMPLE_INTERVAL_MS / 1000:.2f} s"
        )
    if controls.playback_finished:
        controls.stop_playback()
    PlotCurve(self)

    if forward_batch:
        if imaging_enabled:
            imaging_graph.on_emulator_data(forward_batch, soma_clamped=ui_state.voltage_clamp)
        if extracellular_enabled:
            extracellular_graph.on_emulator_data(forward_batch, soma_clamped=ui_state.voltage_clamp)


def GetData(self, state, noise, recording_channels=None):
    """Advance the two presynaptic cells, their synapses, and the soma by 0.1 ms."""
    dt = EMULATOR_SAMPLE_INTERVAL_MS
    stimulus_sample = self.emulator_controls.next_sample()
    scheduled = NO_STEP
    if stimulus_sample is None:
        period = self.Emulator_StimSteps
        counter = self.Emulator_StimCounter
        stimulus = state.stim_strength if counter < period // 2 else 0.0
        trigger = counter == 0
        self.Emulator_StimCounter = (counter + 1) % period
        if self.Emulator_StimCounter == 0:
            self.Emulator_StimSteps = state.stim_period
    else:
        stimulus, trigger, scheduled = stimulus_sample

    stimulus = float(stimulus) if abs(stimulus) >= 5 else 0.0
    # The virtual current cable uses the same DAC span and ADC deadband.
    input_counts = copysign(max(0, round(abs(stimulus) * 2047 / 100) - 273), stimulus)
    direct_current = input_counts * 0.1
    self.Emulator_Photodiode_Value = 0.0
    if state.stim_as_light:
        self.Emulator_Photodiode_Value, self.Photodiode_Recovery = photodiode_step(
            max(0, stimulus), state.photo_gain, self.Photodiode_Recovery,
            state.photo_decay, state.photo_recovery,
        )

    voltage = self.Emulator_v
    presynaptic_vm = []
    presynaptic_events = [0, 0] if recording_channels is not None else None
    currents = []
    conductance = weighted_reversal = 0.0
    for channel, synapse in enumerate(self._emulator_synapses):
        if not state.syn_enabled[channel]:
            if self._emulator_syn_connected[channel]:
                synapse.clear_currents()
                synapse.high = False
                synapse.configure_stp(self.emulator_controls.stp_settings(channel))
            self._emulator_syn_connected[channel] = False
            presynaptic_vm.append(0.0)
            currents.append(0.0)
            continue

        self._emulator_syn_connected[channel] = True
        v, u, recovery = self._emulator_aux_state[channel]
        photo = 0.0
        if state.syn_as_light[channel]:
            photo, recovery = photodiode_step(
                max(0, stimulus), state.syn_photo_gain[channel], recovery,
                state.syn_photo_decay[channel], state.syn_photo_recovery[channel],
            )
        current = (state.syn_patch_clamp[channel] + noise[channel + 1] + photo
                   + (direct_current if state.syn_as_current[channel] else 0))
        v, u, spike = izhikevich(v, u, current, state.aux_parameters[channel], dt)
        self._emulator_aux_state[channel] = v, u, recovery
        presynaptic_vm.append(30.0 if spike else v)
        if presynaptic_events is not None:
            presynaptic_events[channel] = int(spike and not synapse.high)

        current, g, ge = synapse.step(
            spike, state.syn_gain[channel], state.syn_decay[channel],
            self.Emulator_sim_time_ms, dt, voltage, state.block,
            state.pharmacology, state.nmda, state.probabilities[channel], state.sites[channel],
        )
        currents.append(current)
        conductance += g
        weighted_reversal += ge

    external = self.Emulator_Photodiode_Value + noise[0]
    direct = direct_current if state.stim_as_current else 0.0
    if state.voltage_clamp:
        command = max(-110, min(80, state.patch_clamp + (input_counts * 70 / 2047 if state.stim_as_current else 0)))
        inward = external + (0 if state.nmda else sum(currents))
        voltage, measured_current = self._emulator_clamp.step(
            voltage, command, dt, inward * CURRENT_TO_NA, conductance * CURRENT_TO_NA,
            weighted_reversal * CURRENT_TO_NA, state.active_membrane, state.block,
        )
        a, b, _, _ = state.izh
        self.Emulator_u += dt * a * (b * voltage - self.Emulator_u)
        if state.pharmacology:
            self._emulator_intrinsic.hold(voltage, dt)
        displayed_vm = voltage
        currents = [current * CURRENT_TO_NA for current in currents]
    else:
        command = state.patch_clamp + direct
        measured_current = state.patch_clamp + direct + external + sum(currents)
        if state.pharmacology:
            voltage, self.Emulator_u, spike = self._emulator_intrinsic.step(
                voltage, self.Emulator_u, measured_current, state.izh, dt, state.block,
            )
        else:
            voltage, self.Emulator_u, spike = izhikevich(
                voltage, self.Emulator_u, measured_current, state.izh, dt,
            )
        displayed_vm = 30.0 if spike else voltage

    if recording_channels is not None:
        for target, value in zip(recording_channels, (command, *presynaptic_events, *scheduled)):
            target.append(value)
    self.Emulator_v = voltage
    self.Emulator_sim_time_ms += dt
    return [
        displayed_vm, stimulus, measured_current,
        presynaptic_vm[0], currents[0], presynaptic_vm[1], currents[1], float(trigger),
    ]


def PlotCurve(self):
    """
    Push the visible rolling buffers to their curves.

    Reads go straight from the ``RingBuffer`` contiguous views, avoiding the
    per-redraw deque-to-array copy of 7 x 50 000 samples.
    """
    ui = self.ui
    channels = (
        (ui.Emulator_VmCheckbox, self.Emulator_curve0, 0),
        (ui.Emulator_StimulusCheckbox, self.Emulator_curve1, 1),
        (ui.Emulator_InputCurrentCheckbox, self.Emulator_curve2, 2),
        (ui.Emulator_Syn1VmCheckbox, self.Emulator_curve3, 3),
        (ui.Emulator_Syn1InputCheckbox, self.Emulator_curve4, 4),
        (ui.Emulator_Syn2VmCheckbox, self.Emulator_curve5, 5),
        (ui.Emulator_Syn2InputCheckbox, self.Emulator_curve6, 6),
    )
    for checkbox, curve, index in channels:
        visible = checkbox.isChecked()
        curve.setVisible(visible)
        if visible:
            curve.setData(self.Emulator_x, self.Emulator_buffers[index].data)


def UpdateViews(self):
    """Keep the right-axis current ViewBox aligned with the main ViewBox."""
    main_vb = self.ui.Emulator_Oscilloscope_widget.getViewBox()
    for view in (self.Emulator_CurrentPlots, self.Emulator_StimulusPlots):
        if view is not None:
            view.setGeometry(main_vb.sceneBoundingRect())
            view.linkedViewChanged(main_vb, view.XAxis)


def ConfigureCurrentAxis(self, voltage_clamp):
    scope = self.ui.Emulator_Oscilloscope_widget
    scope.setLabel("right", "Clamp Current" if voltage_clamp else "Current Input",
                   units="nA" if voltage_clamp else "a.u.")
    self.ui.Emulator_InputCurrentCheckbox.setText("Clamp Current" if voltage_clamp else "Input Current")
    currents = getattr(self, "Emulator_CurrentPlots", None)
    if currents is not None:
        currents.setYRange(*((-20, 20) if voltage_clamp else (CURRENT_MIN, CURRENT_MAX)), padding=0)
        scope.setYRange(VM_MIN_MV, 80 if voltage_clamp else VM_MAX_MV, padding=0)


def UpdateRecordingState(self):
    """Open a local sample buffer once the recording button has accepted a path."""
    if self.ui.Emulator_DataRecording_Record_pushButton.isChecked() and not self.recordflag:
        self.Emulator_RecordingPath = self.ui.Emulator_recording_path
        self._emulator_recording_vc = self.emulator_controls.voltage_clamp
        self._emulator_recording_channels = [[] for _ in range(6)]
        self._emulator_recording_metadata = RecordingMetadata(
            "emulator", "VC" if self._emulator_recording_vc else "CC", EMULATOR_SAMPLE_INTERVAL_MS,
            "emulator_integration_step", "settings applied at the recorded sample boundary",
        )
        self.recordflag = True


def FinishRecording(self):
    """Save accepted samples atomically, retaining the buffer if saving fails."""
    button = self.ui.Emulator_DataRecording_Record_pushButton
    self.recordflag = False
    button.setChecked(False)
    button.setText("Record")
    file_editor = self.ui.Emulator_DataRecording_File_lineEdit
    folder_button = self.ui.Emulator_DataRecording_Folder_pushButton
    if not getattr(self, "EmulatorData", None) or not self.EmulatorData[1]:
        file_editor.setEnabled(True)
        folder_button.setEnabled(True)
        return True

    path = self.Emulator_RecordingPath
    try:
        vc = self._emulator_recording_vc
        unit = "nA" if vc else "a.u."
        current_label = "Clamp current" if vc else "Total Current Input"
        columns = [
            "Spikeling Vm (mV)", "Stimulus (%)", f"{current_label} ({unit})",
            "Synapse 1 Vm (mV)", f"Synapse 1 Input ({unit})",
            "Synapse 2 Vm (mV)", f"Synapse 2 Input ({unit})", "Trigger",
        ]
        count = len(self.EmulatorData[1])
        frame = {"Time (ms)": np.arange(count, dtype=float) * EMULATOR_SAMPLE_INTERVAL_MS}
        frame.update(zip(columns, self.EmulatorData[1:]))
        command = "Command voltage (mV)" if vc else "Command current (a.u.)"
        event1, event2 = "Presynaptic events 1", "Presynaptic events 2"
        if any(len(values) != count for values in self._emulator_recording_channels):
            raise ValueError("Recorded command and event channels have different sample counts.")
        frame.update(zip((command, event1, event2), self._emulator_recording_channels))
        channels = {
            command: {"units": "mV" if vc else "a.u.", "clock": "Time (ms)",
                      "meaning": "voltage clamp setpoint" if vc else "patch plus direct stimulus current"},
            event1: {"encoding": "rising_edge_flag", "clock": "Time (ms)", "synapse": 1},
            event2: {"encoding": "rising_edge_flag", "clock": "Time (ms)", "synapse": 2},
        }
        save_step_channels(frame, channels, self._emulator_recording_channels[3:],
                           "scheduled step at emulator integration sample")
        write_recording(path, frame, self._emulator_recording_metadata, channels)
    except (OSError, ValueError, TypeError) as error:
        self.ui.Emulator_DataRecording_Record_label.setText("Recording could not be saved")
        button.setText("Retry save")
        show_popup(self, "Error saving file", f"Could not save emulator recording to {path}.\n{error}")
        return False

    for row in (*self.EmulatorData, *self._emulator_recording_channels):
        row.clear()
    self.ui.Emulator_DataRecording_Record_label.setText(f"Saved {count:,} samples")
    file_editor.setEnabled(True)
    folder_button.setEnabled(True)
    return True


def SyncModelSettings(self, state):
    """Apply local settings only at a sample boundary."""
    controls = self.emulator_controls
    revisions = tuple(controls.stp_revision)
    for channel, synapse in enumerate(self._emulator_synapses):
        if revisions[channel] != self._emulator_stp_revision[channel]:
            synapse.configure_stp(controls.stp_settings(channel))
        if controls.release_seed_revision != self._emulator_release_revision:
            synapse.reseed(controls.release_seed)
        if state.nmda != self._emulator_nmda:
            synapse.clear_receptors()
        elif state.pharmacology and not self._emulator_pharmacology:
            synapse.released_current = synapse.legacy_current
    for channel, revision in enumerate(controls.aux_revision):
        if revision != self._emulator_aux_revision[channel]:
            voltage = controls.aux_rest[channel]
            self._emulator_aux_state[channel] = voltage, voltage * state.aux_parameters[channel][1], 1.0
            self._emulator_aux_revision[channel] = revision
    self._emulator_stp_revision = revisions
    self._emulator_release_revision = controls.release_seed_revision
    self._emulator_nmda = state.nmda
    if state.pharmacology and not self._emulator_pharmacology:
        self._emulator_intrinsic = IntrinsicPharmacology(self.Emulator_v)
    self._emulator_pharmacology = state.pharmacology

    if controls.neuron_revision != self._emulator_neuron_revision:
        self.Emulator_v = controls.rest_voltage
        self.Emulator_u = state.izh[1] * self.Emulator_v
        self._emulator_intrinsic = IntrinsicPharmacology(self.Emulator_v)
        self._emulator_clamp = VoltageClamp(self.Emulator_v)
        self._emulator_neuron_revision = controls.neuron_revision
    if controls.membrane_revision != self._emulator_membrane_revision:
        self._emulator_clamp = VoltageClamp(self.Emulator_v)
        self._emulator_membrane_revision = controls.membrane_revision


def SetInitParameters(self):
    """Start a new model session with the selected controls."""
    controls = self.emulator_controls
    self.ui.EmulatorConnectedFlag = True
    self.recordflag = False
    self.Emulator_sim_time_ms = 0.0
    self.Emulator_RecordingPath = None
    self.ui.Emulator_Oscilloscope_widget.clear()
    self.ui.Emulator_Connect_pushButton.setText("Stop Spikeling Emulator")
    self.ui.Emulator_Connect_pushButton.setStyleSheet(
        f"color: rgb{tuple(DarkSolarized[3])}; "
        f"background-color: rgb{tuple(DarkSolarized[11])}; "
        f"border: 1px solid rgb{tuple(DarkSolarized[14])}; border-radius: 10px;"
    )
    self._emulator_rng = np.random.default_rng()
    self._emulator_step_scheduler = speed.FractionalStepScheduler()
    self.Emulator_v = controls.rest_voltage
    self.Emulator_u = self.ui.Emulator_b * self.Emulator_v
    self.Emulator_StimCounter = 0
    self.Emulator_StimSteps = 510 - 5 * self.ui.Emulator_StimFre_slider.value()
    self.Photodiode_Recovery = 1.0
    self._emulator_aux_state = [(v, v * b, 1.0) for v, b in
                                zip(controls.aux_rest, (self.ui.Emulator_b1, self.ui.Emulator_b2))]
    self._emulator_aux_revision = list(controls.aux_revision)
    self._emulator_syn_connected = [False, False]
    self._emulator_synapses = [Synapse(i, controls.release_seed) for i in range(2)]
    self._emulator_clamp = VoltageClamp(self.Emulator_v)
    self._emulator_intrinsic = IntrinsicPharmacology(self.Emulator_v)
    self._emulator_stp_revision = (-1, -1)
    self._emulator_release_revision = controls.release_seed_revision
    self._emulator_membrane_revision = controls.membrane_revision
    self._emulator_neuron_revision = controls.neuron_revision
    self._emulator_pharmacology = False
    self._emulator_nmda = False
    controls.refresh_playback()


def SetPlotCurve(self):
    """
    Allocate the rolling display buffers and the recording accumulators.

    One ``RingBuffer`` per stream replaces the previous deque plus staging
    array pair, halving memory traffic per redraw.
    """
    self._bufsize = int(EMULATOR_TIME_WINDOW_MS / EMULATOR_SAMPLE_INTERVAL_MS)

    self.Emulator_buffers = [RingBuffer(self._bufsize) for _ in range(N_EMULATOR_CHANNELS)]
    self.Emulator_x = np.linspace(-EMULATOR_TIME_WINDOW_MS, 0.0, self._bufsize)

    # Index 0 is reserved for the reconstructed time axis at export time.
    self.EmulatorData = [[] for _ in range(N_EMULATOR_CHANNELS + 1)]


def SetPlot(self):
    """
    Build the emulator oscilloscope: membrane potentials left, currents right.

    Peak-preserving downsampling and view clipping are enabled so the renderer
    only rasterises the samples inside the visible x-range rather than the
    full 50 000-sample buffer.
    """
    pw = self.ui.Emulator_Oscilloscope_widget
    plot_item = pw.getPlotItem()
    configure_scope(plot_item)

    trace_width = theme_manager.active_trace_width
    pw.showGrid(x=True, y=True)
    pw.setRange(xRange=[-EMULATOR_TIME_WINDOW_DISPLAY_MS, 0])
    pw.setRange(yRange=[VM_MIN_MV, VM_MAX_MV])
    plot_item.setMouseEnabled(x=True, y=False)
    plot_item.vb.setLimits(xMin=-EMULATOR_TIME_WINDOW_MS, xMax=0)
    pw.setLabel('left', 'Membrane potential', 'mV')
    pw.setLabel('bottom', 'time', 'ms')
    pw.setLabel('right', 'Current Input', 'a.u.')

    # Secondary ViewBox carrying the currents on the right axis
    self.Emulator_CurrentPlots = pg.ViewBox()
    pw.scene().addItem(self.Emulator_CurrentPlots)
    self.Emulator_CurrentPlots.setXLink(pw)
    self.Emulator_CurrentPlots.enableAutoRange(axis=pg.ViewBox.YAxis, enable=False)
    self.Emulator_StimulusPlots = pg.ViewBox()
    pw.scene().addItem(self.Emulator_StimulusPlots)
    self.Emulator_StimulusPlots.setXLink(pw)
    self.Emulator_StimulusPlots.setMouseEnabled(False, False)
    self.Emulator_StimulusPlots.enableAutoRange(axis=pg.ViewBox.YAxis, enable=False)
    self.Emulator_StimulusPlots.setYRange(-100, 100, padding=0)
    self.Emulator_CurrentPlots.setMouseEnabled(False, False)
    pw.getAxis("right").linkToView(self.Emulator_CurrentPlots)

    # The main ViewBox survives emulator restarts.
    if not hasattr(self, "_emulator_update_views"):
        self._emulator_update_views = lambda: UpdateViews(self)
        pw.getViewBox().sigResized.connect(self._emulator_update_views)

    zeros = np.zeros(self._bufsize, dtype=float)

    # Membrane potentials on the main ViewBox
    self.Emulator_curve0 = pw.plot(self.Emulator_x, zeros,
                                   pen=pg.mkPen(DarkSolarized[3], width=trace_width, cosmetic=True))
    self.Emulator_curve3 = pw.plot(self.Emulator_x, zeros,
                                   pen=pg.mkPen(DarkSolarized[6], width=trace_width, cosmetic=True))
    self.Emulator_curve5 = pw.plot(self.Emulator_x, zeros,
                                   pen=pg.mkPen(DarkSolarized[8], width=trace_width, cosmetic=True))

    # Stimulus and currents on the secondary ViewBox
    self.Emulator_curve1 = pg.PlotCurveItem(self.Emulator_x, zeros,
                                            pen=pg.mkPen(DarkSolarized[5], width=trace_width, cosmetic=True))
    self.Emulator_curve2 = pg.PlotCurveItem(self.Emulator_x, zeros,
                                            pen=pg.mkPen(DarkSolarized[4], width=trace_width, cosmetic=True))
    self.Emulator_curve4 = pg.PlotCurveItem(self.Emulator_x, zeros,
                                            pen=pg.mkPen(DarkSolarized[7], width=trace_width, cosmetic=True))
    self.Emulator_curve6 = pg.PlotCurveItem(self.Emulator_x, zeros,
                                            pen=pg.mkPen(DarkSolarized[10], width=trace_width, cosmetic=True))

    self.Emulator_StimulusPlots.addItem(self.Emulator_curve1)
    for curve in (self.Emulator_curve2, self.Emulator_curve4, self.Emulator_curve6):
        self.Emulator_CurrentPlots.addItem(curve)

    ConfigureCurrentAxis(self, self.emulator_controls.voltage_clamp)
    UpdateViews(self)

    # Armed last, once every curve is attached: the latch then observes the
    # autorange passes triggered by the right-menu animation and by the first
    # 50 000-sample setData, both of which outlive a next-iteration deferral.
    self.Emulator_timebase = apply_scope_timebase(
        plot_item, EMULATOR_TIME_WINDOW_MS, EMULATOR_TIME_WINDOW_DISPLAY_MS,
        y_range=(VM_MIN_MV, 80 if self.emulator_controls.voltage_clamp else VM_MAX_MV),
    )
