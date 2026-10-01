"""
Spikeling emulator: software Izhikevich model driving the emulator oscilloscope.

The emulator integrates up to three Izhikevich neurons (one soma plus two
presynaptic units) with forward Euler at a fixed 0.1 ms step, matching the
firmware so that emulator and hardware traces are directly comparable:

$$v_{k+1} = v_k + \\\\Delta t\\\\,(0.04 v_k^2 + 5 v_k + 140 - u_k + I_k)$$
$$u_{k+1} = u_k + \\\\Delta t\\\\, a\\\\,(b\\\\,v_{k+1} - u_k)$$

Architecture note
-----------------
All Qt widget reads and all random draws are hoisted out of the integration
loop: the UI is sampled once per GUI tick into an ``EmulatorUISnapshot`` and
the Gaussian current noise for the whole tick is drawn as a single block.
At the maximum speed setting this removes ~3 x 10^5 Python/Qt boundary
crossings and ~3 x 10^4 scalar RNG calls per tick.

Reference
---------
Izhikevich, 2003, IEEE Transactions on Neural Networks
"Simple Model of Spiking Neurons"
"""

from dataclasses import dataclass

from PySide6.QtCore import QTimer
import pyqtgraph as pg

import numpy as np
import pandas as pd

import Parameters_Settings as Settings
from graph_core import RingBuffer, configure_scope, resolve_csv_path, safe_reconnect


# --- Display / buffering ---------------------------------------------------
EMULATOR_SAMPLE_INTERVAL_MS = 0.1       # integration step, matches firmware dt
EMULATOR_TIME_WINDOW_MS = 5000          # rolling buffer length
EMULATOR_TIME_WINDOW_DISPLAY_MS = 500   # initial visible x-range
PEN_WIDTH = 1
N_EMULATOR_CHANNELS = 8

# --- Speed control ---------------------------------------------------------
# Integration steps executed per 50 ms GUI tick, indexed by the speed slider.
STEPS_PER_UPDATE_BY_SLIDER = (10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000)
# Steps per tick corresponding to "x 1.0" wall-clock speed (50 ms / 0.1 ms * 20).
REALTIME_STEPS_PER_UPDATE = 10000
GUI_TICK_MS = 50

# --- Izhikevich bounds -----------------------------------------------------
V_THRESHOLD_MV = 30.0
V_PEAK_MV = 30.0
V_MIN_MV = -110.0

# --- Photodiode model ------------------------------------------------------
PHOTODIODE_STIM_SCALE = 25.0     # stimulus (%) -> photocurrent (a.u.)
PHOTODIODE_GAIN_SCALE = 0.5      # slider gain normalisation
PHOTODIODE_DECAY_SCALE = 100000.0
PHOTODIODE_RECOVERY_SCALE = 1000.0

# --- Stimulus generator ----------------------------------------------------
STIM_DUTY_CYCLE_STEPS = 500
STIM_DUTY_CYCLE_MIN_STEPS = 10

# --- Plot y-ranges ---------------------------------------------------------
VM_MIN_MV, VM_MAX_MV = -90, 30
CURRENT_MIN, CURRENT_MAX = -100, 100


@dataclass(slots=True)
class EmulatorUISnapshot:
    """
    Immutable snapshot of every emulator control, read once per GUI tick.

    Sampling the controls once per tick rather than once per integration step
    is physiologically indistinguishable, because the fastest possible slider
    movement is orders of magnitude slower than one 50 ms tick.

    Attributes
    ----------
    izh, izh_syn1, izh_syn2 : tuple of float
        Izhikevich ``(a, b, c, d)`` parameters for the soma and both synapses.
    stim_strength : float
        Square-pulse amplitude (%).
    stim_frequency : float
        Square-pulse frequency index, clamped to ``[-100, 100]``.
    stim_custom_enabled : bool
        Whether a user-loaded waveform overrides the internal generator.
    stim_custom_wave : sequence of float or None
        The loaded waveform, or ``None`` when unavailable or empty.
    stim_as_light, stim_as_current : bool
        Somatic stimulus routing.
    patch_clamp, noise_sigma : float
        Somatic injected current (a.u.) and noise standard deviation.
    photo_gain, photo_decay, photo_recovery : float
        Somatic photodiode gain and adaptation rates, already slider-scaled.
    syn_enabled, syn_patch_clamp, syn_noise_sigma, syn_gain, syn_decay : tuple
        Per-synapse parameters, indexed ``[0] -> synapse 1``.
    syn_as_current, syn_as_light : tuple of bool
        Per-synapse stimulus routing.
    syn_photo_gain, syn_photo_decay, syn_photo_recovery : tuple of float
        Per-synapse photodiode parameters.
    """

    izh: tuple
    izh_syn1: tuple
    izh_syn2: tuple

    stim_strength: float
    stim_frequency: float
    stim_custom_enabled: bool
    stim_custom_wave: object
    stim_as_light: bool
    stim_as_current: bool

    patch_clamp: float
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

    @classmethod
    def from_ui(cls, ui) -> "EmulatorUISnapshot":
        """
        Read every emulator widget exactly once.

        Parameters
        ----------
        ui : object
            Generated Qt UI object owning the emulator widgets.

        Returns
        -------
        EmulatorUISnapshot
            Frozen parameter set valid for the current GUI tick.
        """
        wave = getattr(ui, "Emulatordf_yStim", None)
        if wave is not None and len(wave) == 0:
            wave = None

        return cls(
            izh=(ui.Emulator_a, ui.Emulator_b, ui.Emulator_c, ui.Emulator_d),
            izh_syn1=(ui.Emulator_a1, ui.Emulator_b1, ui.Emulator_c1, ui.Emulator_d1),
            izh_syn2=(ui.Emulator_a2, ui.Emulator_b2, ui.Emulator_c2, ui.Emulator_d2),

            stim_strength=float(ui.Emulator_StimStrSlider.value()),
            stim_frequency=float(max(-100, min(100, -ui.Emulator_StimFre_slider.value()))),
            stim_custom_enabled=bool(ui.EmulatorStimCus_toggleButton.isChecked()),
            stim_custom_wave=wave,
            stim_as_light=bool(ui.EmulatorStimChoiceLight_toggleButton.isChecked()),
            stim_as_current=bool(ui.EmulatorStimChoiceCurrent_toggleButton.isChecked()),

            patch_clamp=float(ui.Emulator_PatchClamp_slider.value()),
            noise_sigma=float(ui.Emulator_Noise_slider.value()) / 4.0,
            photo_gain=float(ui.Emulator_PR_PhotoGain_slider.value()),
            photo_decay=float(ui.Emulator_PR_Decay_slider.value()) / PHOTODIODE_DECAY_SCALE,
            photo_recovery=float(ui.Emulator_PR_Recovery_slider.value()) / PHOTODIODE_RECOVERY_SCALE,

            syn_enabled=(bool(ui.EmulatorSyn1_Synapse_toggleButton.isChecked()),
                         bool(ui.EmulatorSyn2_Synapse_toggleButton.isChecked())),
            syn_patch_clamp=(float(ui.Emulator_Syn1_PatchClamp_slider.value()),
                             float(ui.Emulator_Syn2_PatchClamp_slider.value())),
            syn_noise_sigma=(float(ui.Emulator_Syn1_Noise_slider.value()) / 4.0,
                             float(ui.Emulator_Syn2_Noise_slider.value()) / 4.0),
            syn_gain=(float(ui.Emulator_Synapse1_slider.value()),
                      float(ui.Emulator_Synapse2_slider.value())),
            syn_decay=(float(ui.Emulator_Synapse1_Decay_slider.value()) / 1000.0,
                       float(ui.Emulator_Synapse2_Decay_slider.value()) / 1000.0),
            syn_as_current=(bool(ui.EmulatorSyn1_StimDC_toggleButton.isChecked()),
                            bool(ui.EmulatorSyn2_StimDC_toggleButton.isChecked())),
            syn_as_light=(bool(ui.EmulatorSyn1_StimLight_toggleButton.isChecked()),
                          bool(ui.EmulatorSyn2_StimLight_toggleButton.isChecked())),
            syn_photo_gain=(float(ui.Emulator_Syn1_PR_PhotoGain_slider.value()),
                            float(ui.Emulator_Syn2_PR_PhotoGain_slider.value())),
            syn_photo_decay=(float(ui.Emulator_Syn1_PR_Decay_slider.value()) / PHOTODIODE_DECAY_SCALE,
                             float(ui.Emulator_Syn2_PR_Decay_slider.value()) / PHOTODIODE_DECAY_SCALE),
            syn_photo_recovery=(float(ui.Emulator_Syn1_PR_Recovery_slider.value()) / PHOTODIODE_RECOVERY_SCALE,
                                float(ui.Emulator_Syn2_PR_Recovery_slider.value()) / PHOTODIODE_RECOVERY_SCALE),
        )


def izhikevich_step(v, u, i_total, izh, dt_ms):
    """
    Advance one Izhikevich neuron by a single forward-Euler step.

    The recovery variable is updated from the *new* membrane potential
    (sequential / Gauss-Seidel ordering) to stay bit-comparable with the
    Spikeling firmware, which performs the same in-place update.

    Parameters
    ----------
    v, u : float
        Membrane potential (mV) and recovery variable.
    i_total : float
        Total input current (a.u.) applied during this step.
    izh : tuple of float
        Izhikevich ``(a, b, c, d)`` parameters.
    dt_ms : float
        Integration step in milliseconds.

    Returns
    -------
    v_next : float
        Updated membrane potential, reset and clamped.
    u_next : float
        Updated recovery variable.
    spiked : bool
        True on the step where the potential is rendered at its peak value.
    """
    a, b, c, d = izh

    v = v + dt_ms * (0.04 * v * v + 5.0 * v + 140.0 - u + i_total)
    u = u + dt_ms * (a * (b * v - u))

    if v >= V_THRESHOLD_MV:
        v = c
        u = u + d
    if v < V_MIN_MV:
        v = V_MIN_MV

    spiked = v >= 0.0
    if spiked:
        v = V_PEAK_MV

    return v, u, spiked


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
    current = (stimulus / PHOTODIODE_STIM_SCALE) * (gain / PHOTODIODE_GAIN_SCALE) * recovery

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
        SetInitParameters(self)
        SetPlotCurve(self)
        SetPlot(self)

        self.timer = QTimer()
        self.timer.timeout.connect(lambda: UpdatePlot(self))
        self.timer.start(GUI_TICK_MS)
        return

    self.ui.Emulator_Connect_pushButton.setText("Start Spikeling Emulator")
    self.ui.Emulator_Connect_pushButton.setStyleSheet(
        "color: rgb" + str(tuple(Settings.DarkSolarized[14])) + ";\n"
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
    self.recordflag = False


def UpdatePlot(self):
    """
    Advance the emulator by one GUI tick and refresh the oscilloscope.

    The speed slider selects how many 0.1 ms integration steps run per tick.
    Controls are sampled once, noise is drawn as one block, the recording
    state machine is evaluated once, and the scope is redrawn once, so the
    only per-step work is the model itself.
    """
    speed_step = min(self.ui.Emulator_Speed_slider.value(),
                     len(STEPS_PER_UPDATE_BY_SLIDER) - 1)
    steps_per_update = STEPS_PER_UPDATE_BY_SLIDER[speed_step]
    self.ui.Emulator_Speed_value.setText(
        "x " + str(round(steps_per_update / REALTIME_STEPS_PER_UPDATE, 3))
    )

    # --- Once-per-tick UI sampling and RNG ------------------------------
    ui_state = EmulatorUISnapshot.from_ui(self.ui)

    noise_block = self._emulator_rng.standard_normal((steps_per_update, 3))
    noise_block *= np.array([ui_state.noise_sigma,
                             ui_state.syn_noise_sigma[0],
                             ui_state.syn_noise_sigma[1]], dtype=float)

    # Consume the one-shot custom-stimulus restart flag once per tick.
    if getattr(self.ui, "StimCus_Flag", False):
        self.EmulatorCusStimCounter = 0
        self.Emulator_PendingStimTrigger = True
        self.ui.StimCus_Flag = False

    UpdateRecordingState(self)

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
    for step in range(steps_per_update):
        vec8 = GetData(self, ui_state, noise_block[step])
        self.ui.Emulator_Data = vec8

        for channel in range(N_EMULATOR_CHANNELS):
            self.Emulator_buffers[channel].append(vec8[channel])

        if self.recordflag:
            for channel in range(N_EMULATOR_CHANNELS):
                self.EmulatorData[channel + 1].append(vec8[channel])

        if forward_batch is not None:
            forward_batch.append([self.Emulator_sim_time_ms] + vec8)

    PlotCurve(self)

    if forward_batch:
        if imaging_enabled:
            imaging_graph.on_emulator_data(forward_batch)
        if extracellular_enabled:
            extracellular_graph.on_emulator_data(forward_batch)


def GetData(self, ui_state, noise_row):
    """
    Execute one emulator integration step.

    Order of operations
    -------------------
    1. Soma membrane potential, driven by the current accumulated last step.
    2. Stimulus waveform (custom file, or internal 50 % duty square pulse).
    3. Somatic photodiode and direct-current routing.
    4. Synapse 1: Izhikevich step, photodiode, post-synaptic current.
    5. Synapse 2: identical, with its own parameter set.
    6. Accumulate the total somatic current for the next step.

    Fixes relative to the pre-refactor implementation
    -------------------------------------------------
    - Synapse 2 decay now reads ``syn_decay[1]``; the slider previously wrote
      to a differently-spelled attribute and had no effect.
    - Photodiode adaptation rates are applied on the step they are read,
      instead of one step late.
    - Synaptic spike flags are cleared when a synapse is disabled, so
      re-enabling it no longer emits a phantom post-synaptic current.

    Parameters
    ----------
    self : object
        Main window holding the emulator state.
    ui_state : EmulatorUISnapshot
        Control values sampled once for the current GUI tick.
    noise_row : numpy.ndarray
        Pre-drawn Gaussian noise for this step, ordered
        ``[soma, synapse 1, synapse 2]`` (a.u.).

    Returns
    -------
    list of float
        ``[Vm0, Stim, Itot, Vm1, ISyn1, Vm2, ISyn2, Trigger]``.
    """
    dt = self.Emulator_timestep_ms

    # ------------------------------------------------------------------
    # 1) Soma membrane potential
    # ------------------------------------------------------------------
    self.Emulator_v, self.Emulator_u, _ = izhikevich_step(
        self.Emulator_v, self.Emulator_u, self.Emulator_TotalCurrent_Data,
        ui_state.izh, dt,
    )
    self.Emulator_Vm_Data = self.Emulator_v

    # ------------------------------------------------------------------
    # 2) Stimulus
    # ------------------------------------------------------------------
    self.Emulator_Trigger = 0

    if ui_state.stim_custom_enabled and ui_state.stim_custom_wave is not None:
        wave = ui_state.stim_custom_wave

        if self.Emulator_PendingStimTrigger:
            self.Emulator_Trigger = 1
            self.Emulator_PendingStimTrigger = False

        if self.EmulatorCusStimCounter >= len(wave):
            self.EmulatorCusStimCounter = 0
            self.Emulator_Trigger = 1

        self.Emulator_Stimulus_Data = float(wave[self.EmulatorCusStimCounter])
        self.EmulatorCusStimCounter += 1

    else:
        if self.Emulator_StimTriggerEnable:
            self.Emulator_Trigger = 1
            self.Emulator_StimTriggerEnable = False

        half_period = self.Emulator_StimSteps // 2
        self.Emulator_Stimulus_Data = (
            ui_state.stim_strength if self.Emulator_StimCounter < half_period else 0.0
        )

        self.Emulator_StimCounter += 1
        if self.Emulator_StimCounter >= self.Emulator_StimSteps:
            self.Emulator_StimCounter = 0
            self.Emulator_StimTriggerEnable = True
            steps = (self.Emulator_Stim_DutyCycle
                     + (ui_state.stim_frequency * self.Emulator_Stim_DutyCycle) / 100.0
                     + self.Emulator_Stim_DutyCycle_Min)
            self.Emulator_StimSteps = max(1, int(steps))

    stimulus = self.Emulator_Stimulus_Data

    # ------------------------------------------------------------------
    # 3) Somatic stimulus routing
    # ------------------------------------------------------------------
    if ui_state.stim_as_light:
        self.Emulator_Photodiode_Value, self.Photodiode_Recovery = photodiode_step(
            stimulus, ui_state.photo_gain, self.Photodiode_Recovery,
            ui_state.photo_decay, ui_state.photo_recovery,
        )
    else:
        self.Emulator_Photodiode_Value = 0.0

    direct_current = stimulus if ui_state.stim_as_current else 0.0

    # ------------------------------------------------------------------
    # 4) Synapse 1
    # ------------------------------------------------------------------
    if ui_state.syn_enabled[0]:
        self.Emulator_v1, self.Emulator_u1, spiked1 = izhikevich_step(
            self.Emulator_v1, self.Emulator_u1, self.Emulator_TotalCurrent1_Data,
            ui_state.izh_syn1, dt,
        )
        self.Emulator_Vm_Data1 = self.Emulator_v1

        if ui_state.syn_as_light[0]:
            photo1, self.EmulatorSyn1_Photodiode_Recovery = photodiode_step(
                stimulus, ui_state.syn_photo_gain[0],
                self.EmulatorSyn1_Photodiode_Recovery,
                ui_state.syn_photo_decay[0], ui_state.syn_photo_recovery[0],
            )
        else:
            photo1 = 0.0
        self.EmulatorSyn1_Photodiode_Value = photo1

        if spiked1:
            self.Emulator_Syn1Input_Data += ui_state.syn_gain[0]
        self.Emulator_Syn1Input_Data *= ui_state.syn_decay[0]

        self.Emulator_TotalCurrent1_Data = (
            ui_state.syn_patch_clamp[0]
            + noise_row[1]
            + (stimulus if ui_state.syn_as_current[0] else 0.0)
            + photo1
        )
    else:
        self.Emulator_Vm_Data1 = 0.0
        self.Emulator_Syn1Input_Data = 0.0
        self.Emulator_Spike1 = False

    # ------------------------------------------------------------------
    # 5) Synapse 2
    # ------------------------------------------------------------------
    if ui_state.syn_enabled[1]:
        self.Emulator_v2, self.Emulator_u2, spiked2 = izhikevich_step(
            self.Emulator_v2, self.Emulator_u2, self.Emulator_TotalCurrent2_Data,
            ui_state.izh_syn2, dt,
        )
        self.Emulator_Vm_Data2 = self.Emulator_v2

        if ui_state.syn_as_light[1]:
            photo2, self.EmulatorSyn2_Photodiode_Recovery = photodiode_step(
                stimulus, ui_state.syn_photo_gain[1],
                self.EmulatorSyn2_Photodiode_Recovery,
                ui_state.syn_photo_decay[1], ui_state.syn_photo_recovery[1],
            )
        else:
            photo2 = 0.0
        self.EmulatorSyn2_Photodiode_Value = photo2

        if spiked2:
            self.Emulator_Syn2Input_Data += ui_state.syn_gain[1]
        self.Emulator_Syn2Input_Data *= ui_state.syn_decay[1]   # BUGFIX

        self.Emulator_TotalCurrent2_Data = (
            ui_state.syn_patch_clamp[1]
            + noise_row[2]
            + (stimulus if ui_state.syn_as_current[1] else 0.0)
            + photo2
        )
    else:
        self.Emulator_Vm_Data2 = 0.0
        self.Emulator_Syn2Input_Data = 0.0
        self.Emulator_Spike2 = False

    # ------------------------------------------------------------------
    # 6) Total somatic current for the next step
    # ------------------------------------------------------------------
    self.Emulator_TotalCurrent_Data = (
        ui_state.patch_clamp
        + noise_row[0]
        + self.Emulator_Photodiode_Value
        + direct_current
        + self.Emulator_Syn1Input_Data
        + self.Emulator_Syn2Input_Data
    )

    self.Emulator_sim_time_ms += dt

    return [
        self.Emulator_Vm_Data,
        self.Emulator_Stimulus_Data,
        self.Emulator_TotalCurrent_Data,
        self.Emulator_Vm_Data1,
        self.Emulator_Syn1Input_Data,
        self.Emulator_Vm_Data2,
        self.Emulator_Syn2Input_Data,
        float(self.Emulator_Trigger),
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
    self.Emulator_CurrentPlots.setGeometry(main_vb.sceneBoundingRect())
    self.Emulator_CurrentPlots.linkedViewChanged(main_vb, self.Emulator_CurrentPlots.XAxis)


def UpdateRecordingState(self):
    """
    Handle the record-button edges once per GUI tick.

    Previously this ran per integration step (up to 10 000 ``isChecked()``
    calls per tick) and overwrote existing files silently. It now mirrors the
    confirm-overwrite flow already used by the Spikeling page.
    """
    checked = self.ui.Emulator_DataRecording_Record_pushButton.isChecked()

    if checked and not self.recordflag:
        path = resolve_csv_path(self.ui.Emulator_SelectedFolderLabel.text())
        if path is None:
            self.ui.Emulator_DataRecording_Record_pushButton.setChecked(False)
            Settings.show_popup(
                self, Title="Error: no file selected",
                Text="Select a destination file before recording emulator data.",
            )
            return

        if path.exists():
            action, new_path = Settings.confirm_overwrite(self, path)
            if action == "cancel":
                self.ui.Emulator_DataRecording_Record_pushButton.setChecked(False)
                return
            if action == "rename":
                path = new_path

        self.Emulator_RecordingPath = path
        for row in self.EmulatorData:
            row.clear()
        self.recordflag = True
        return

    if (not checked) and self.recordflag:
        ExportEmulatorCsv(self)
        self.recordflag = False
        for row in self.EmulatorData:
            row.clear()


def ExportEmulatorCsv(self):
    """
    Write the recorded emulator stream to CSV.

    The time axis is reconstructed as ``k * dt`` because the emulator clock is
    exact by construction; unlike the hardware stream, no sample can be lost.
    """
    n_samples = len(self.EmulatorData[1])
    path = getattr(self, "Emulator_RecordingPath", None)
    if n_samples == 0 or path is None:
        return

    columns = [
        'Spikeling Vm (mV)', 'Stimulus (%)', 'Total Current Input (a.u.)',
        'Synapse 1 Vm (mV)', 'Synapse 1 Input (a.u.)',
        'Synapse 2 Vm (mV)', 'Synapse 2 Input (a.u.)', 'Trigger',
    ]
    frame = {'Time (ms)': np.arange(n_samples, dtype=float) * EMULATOR_SAMPLE_INTERVAL_MS}
    frame.update({
        name: np.asarray(self.EmulatorData[j + 1], dtype=float)
        for j, name in enumerate(columns)
    })

    try:
        pd.DataFrame(frame).to_csv(path, index=False)
    except Exception as error:
        Settings.show_popup(
            self, Title="Error saving file",
            Text=f"Could not save emulator recording to {path}.\nError: {error}",
        )


def SetInitParameters(self):
    """Reset every emulator state variable to its cold-start value."""
    self.ui.EmulatorConnectedFlag = True
    self.recordflag = False
    self.Trigger = 0
    self.Emulator_sim_time_ms = 0.0
    self.Emulator_RecordingPath = None
    self.ui.Emulator_Oscilloscope_widget.clear()

    # Modern NumPy generator, ~4x faster than the legacy global RNG
    self._emulator_rng = np.random.default_rng()

    if self.ui.Emulator_Connect_pushButton.isChecked():
        self.ui.Emulator_Connect_pushButton.setText("Stop Spikeling Emulator")
        self.ui.Emulator_Connect_pushButton.setStyleSheet(
            "color: rgb" + str(tuple(Settings.DarkSolarized[3])) + ";\n"
            "background-color: rgb" + str(tuple(Settings.DarkSolarized[11])) + ";\n"
            "border: 1px solid rgb" + str(tuple(Settings.DarkSolarized[14])) + ";\n"
            "border-radius: 10px;"
        )
    else:
        self.ui.Emulator_Connect_pushButton.setText("Start Spikeling Emulator")
        self.ui.Emulator_Connect_pushButton.setStyleSheet(
            "color: rgb" + str(tuple(Settings.DarkSolarized[14])) + ";\n"
            "background-color: rgb" + str(tuple(Settings.DarkSolarized[2])) + ";\n"
            "border: 1px solid rgb" + str(tuple(Settings.DarkSolarized[14])) + ";\n"
            "border-radius: 10px;"
        )

    # --- Soma ---------------------------------------------------------
    self.ui.Emulator_a, self.ui.Emulator_b = 0.02, 0.2
    self.ui.Emulator_c, self.ui.Emulator_d = -65.0, 8.0

    self.Emulator_v, self.Emulator_u = -65.0, 0.0
    self.Emulator_timestep_ms = EMULATOR_SAMPLE_INTERVAL_MS
    self.Emulator_v_thresh = V_THRESHOLD_MV
    self.Emulator_v_peak = V_PEAK_MV
    self.Emulator_v_min = V_MIN_MV

    self.Emulator_Vm_Data = -65.0
    self.Emulator_TotalCurrent_Data = 0.0

    # --- Stimulus generator -------------------------------------------
    self.Emulator_Stimulus_Data = 0.0
    self.Emulator_StimCounter = 0
    self.Emulator_StimSteps = 1000
    self.Emulator_Stim_DutyCycle = STIM_DUTY_CYCLE_STEPS
    self.Emulator_Stim_DutyCycle_Min = STIM_DUTY_CYCLE_MIN_STEPS
    self.Emulator_Trigger = 0

    # Custom-stimulus and trigger state (previously uninitialised)
    self.EmulatorCusStimCounter = 0
    self.Emulator_PendingStimTrigger = False
    self.Emulator_StimTriggerEnable = False

    # --- Somatic photodiode -------------------------------------------
    self.Emulator_Photodiode_Value = 0.0
    self.Photodiode_Recovery = 1.0

    # --- Synapse 1 ------------------------------------------------------
    self.ui.Emulator_a1, self.ui.Emulator_b1 = 0.02, 0.2
    self.ui.Emulator_c1, self.ui.Emulator_d1 = -65.0, 8.0
    self.Emulator_v1, self.Emulator_u1 = -65.0, 0.0
    self.Emulator_Vm_Data1 = 0.0
    self.Emulator_TotalCurrent1_Data = 0.0
    self.Emulator_Syn1Input_Data = 0.0
    self.Emulator_Spike1 = False
    self.EmulatorSyn1_Photodiode_Value = 0.0
    self.EmulatorSyn1_Photodiode_Recovery = 1.0

    # --- Synapse 2 ------------------------------------------------------
    self.ui.Emulator_a2, self.ui.Emulator_b2 = 0.02, 0.2
    self.ui.Emulator_c2, self.ui.Emulator_d2 = -65.0, 8.0
    self.Emulator_v2, self.Emulator_u2 = -65.0, 0.0
    self.Emulator_Vm_Data2 = 0.0
    self.Emulator_TotalCurrent2_Data = 0.0
    self.Emulator_Syn2Input_Data = 0.0
    self.Emulator_Spike2 = False
    self.EmulatorSyn2_Photodiode_Value = 0.0
    self.EmulatorSyn2_Photodiode_Recovery = 1.0


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
    self.Emulator_CurrentPlots.setRange(yRange=[CURRENT_MIN, CURRENT_MAX])
    self.Emulator_CurrentPlots.setMouseEnabled(False, False)
    pw.getAxis("right").linkToView(self.Emulator_CurrentPlots)

    # A stable bound handler is required so repeated connect/disconnect cycles
    # do not stack duplicate geometry updates on sigResized.
    if not hasattr(self, "_emulator_update_views"):
        self._emulator_update_views = lambda: UpdateViews(self)
    safe_reconnect(pw.getViewBox().sigResized, self._emulator_update_views)

    zeros = np.zeros(self._bufsize, dtype=float)

    # Membrane potentials on the main ViewBox
    self.Emulator_curve0 = pw.plot(self.Emulator_x, zeros,
                                   pen=pg.mkPen(Settings.DarkSolarized[3], width=PEN_WIDTH, cosmetic=True))
    self.Emulator_curve3 = pw.plot(self.Emulator_x, zeros,
                                   pen=pg.mkPen(Settings.DarkSolarized[6], width=PEN_WIDTH, cosmetic=True))
    self.Emulator_curve5 = pw.plot(self.Emulator_x, zeros,
                                   pen=pg.mkPen(Settings.DarkSolarized[8], width=PEN_WIDTH, cosmetic=True))

    # Stimulus and currents on the secondary ViewBox
    self.Emulator_curve1 = pg.PlotCurveItem(self.Emulator_x, zeros,
                                            pen=pg.mkPen(Settings.DarkSolarized[5], width=PEN_WIDTH, cosmetic=True))
    self.Emulator_curve2 = pg.PlotCurveItem(self.Emulator_x, zeros,
                                            pen=pg.mkPen(Settings.DarkSolarized[4], width=PEN_WIDTH, cosmetic=True))
    self.Emulator_curve4 = pg.PlotCurveItem(self.Emulator_x, zeros,
                                            pen=pg.mkPen(Settings.DarkSolarized[7], width=PEN_WIDTH, cosmetic=True))
    self.Emulator_curve6 = pg.PlotCurveItem(self.Emulator_x, zeros,
                                            pen=pg.mkPen(Settings.DarkSolarized[10], width=PEN_WIDTH, cosmetic=True))

    for curve in (self.Emulator_curve1, self.Emulator_curve2,
                  self.Emulator_curve4, self.Emulator_curve6):
        self.Emulator_CurrentPlots.addItem(curve)

    UpdateViews(self)
