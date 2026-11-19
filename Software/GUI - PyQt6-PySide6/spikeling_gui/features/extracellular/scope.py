"""
Real-time extracellular / tetrode simulation for Spikeling.
Ground-truth Vm(t) + detected spike times -> 4-channel extracellular recording -> display / recording.

Reduced forward model used here
1) Template mode
   spike times -> canonical extracellular spike template -> geometric projection on 4 tetrode contacts
2) dV/dT mode
   smoothed dVm/dt around detected spikes -> geometric projection on 4 tetrode contacts
3) Recording chain
   clean signal + independent baseline noise + shared/common noise + 50 Hz hum
   -> optional CAR (common average reference) -> display bandpass

Core references
1) Gold et al., 2006, Journal of Neurophysiology
   "On the Origin of the Extracellular Action Potential Waveform: A Modeling Study"
   (Extracellular spike waveform depends on source geometry and electrode position)
2) Henze et al., 2000, Journal of Neurophysiology
   "Intracellular Features Predicted by Extracellular Recordings in the Hippocampus In Vivo"
   (Simultaneous intra/extracellular recordings motivate derivative-like educational mode)
3) Harris et al., 2000, Journal of Neurophysiology
   "Accuracy of Tetrode Spike Separation as Determined by Simultaneous Intracellular and
   Extracellular Measurements"
   (Tetrode logic: the same unit appears differently across the 4 contacts)

Important modeling note
- This is intentionally a reduced pedagogical forward model.
- It is NOT a full morphology-based extracellular forward solution.
- The goal is to expose the user to the main tetrode concepts:
    * waveform is not the same as intracellular Vm
    * geometry changes channel amplitudes
    * noise / hum / reference matter
    * multi-contact differences enable spike sorting

Data format:
Incoming packet (8 or 9 elements):
[Vm0, Stim, Itot, Vm1, ISyn1, Vm2, ISyn2, Trigger]
or
[timestamp, Vm0, Stim, Itot, Vm1, ISyn1, Vm2, ISyn2, Trigger]

Notes on units:
- Time is handled internally in milliseconds.
- Vm is assumed to be in mV, as elsewhere in Spikeling.
- Extracellular traces are displayed / recorded in pedagogical microvolt-like units (µV).
"""

from pathlib import Path
import csv
import json
import os
import shutil
from tempfile import mkdtemp

from PySide6.QtCore import QObject, QTimer, Qt
from PySide6.QtWidgets import QSizePolicy, QVBoxLayout
import pyqtgraph as pg
import numpy as np
import pandas as pd
import collections
from typing import Tuple

from scipy.signal import butter, sosfilt

from spikeling_gui.appearance.palette import DarkSolarized
from spikeling_gui.appearance.theme_manager import (EXTRACELLULAR_CHANNEL_KEYS, theme_manager)
from spikeling_gui.hardware.serial_manager import serial_manager
from spikeling_gui.plotting.graph_core import RingBuffer, configure_scope
from spikeling_gui.hardware.protocol import parse_spikeling_packet


SAMPLE_INTERVAL = 0.1
TIME_WINDOW = 2000
TIME_WINDOW_DISPLAY = 500
PEN_WIDTH = 1

N_NEURONS = 3
N_CHANNELS = 4
FS_HZ = 1000.0 / SAMPLE_INTERVAL
NYQUIST_HZ = 0.5 * FS_HZ
MAX_PACKETS_PER_TICK = 5000

# Overlay tuning
EVENT_MERGE_WINDOW_MS = 0.4
EVENT_MARKER_HEADROOM = 0.08
DETECTION_SIGMA_MULTIPLIER = 4.5
DETECTION_THRESHOLD_FLOOR_UV = 15.0

CHANNEL_COLORS = [
    (38, 139, 210), (42, 161, 152), (133, 153, 0), (108, 113, 196),
]

# Default tetrode used until a geometry file is loaded: 4 contacts on a 25 um
# square, the standard bundled-wire arrangement, in the electrode plane (um).
DEFAULT_CONTACT_POSITIONS_UM = np.array(
    [[-12.5, -12.5], [12.5, -12.5], [12.5, 12.5], [-12.5, 12.5]], dtype=float
)

# Default source placement: three units at plausible recording distances,
# deliberately asymmetric so each contact sees a distinct amplitude profile
# (this is what makes spike sorting a meaningful exercise).
DEFAULT_SOURCE_POSITIONS_UM = np.array(
    [[30.0, 10.0], [-20.0, 45.0], [55.0, -35.0]], dtype=float
)

# Guard against the 1/d singularity when a source sits on a contact.
MIN_SOURCE_CONTACT_DISTANCE_UM = 5.0

# Distance at which a unit gain is assigned; sets the overall amplitude scale.
REFERENCE_DISTANCE_UM = 25.0
DEFAULT_SPATIAL_FALLOFF = 1.2

# Per-unit amplitude scaling. Real units differ in soma size and spike
# amplitude, so identical projections would make the sorting exercise trivial.
SOURCE_RELATIVE_GAIN = np.array([1.00, 0.90, 0.80], dtype=float)

# Neuron keys used by Tetrode.py in its saved distance matrix.
TETRODE_NEURON_KEYS = ("main", "aux1", "aux2")
TETRODE_CONTACT_KEYS = ("E1", "E2", "E3", "E4")

# --- Shared channel scaling ------------------------------------------------
# All four contacts share one y-range: the amplitude ratio across contacts is
# the sorting cue, so per-channel autoscaling would hide it.
Y_MIN_UV = -40.0
Y_MAX_UV = 80.0
Y_RANGE_HEADROOM = 1.15        # multiplier applied above the observed peak

# --- Channel plot geometry -------------------------------------------------
# Every contact must render into an identical pixel rectangle: equal y-ranges
# are useless if the data areas differ in height, because the apparent
# amplitude is microvolts per pixel, not microvolts.
AXIS_LEFT_WIDTH_PX = 64     # fixed so tick-label width cannot shift the plots
AXIS_BOTTOM_HEIGHT_PX = 10  # identical tick-only axis on all contacts

# =============================================================================
# ExtraCellularGraph
# =============================================================================

class ExtraCellularGraph(QObject):
    """
    Controller class for extracellular / tetrode simulation and plotting.
    The public method layout intentionally mirrors Graph_Imaging.py so the
    project keeps one consistent architecture across simulation pages.
    """

    # -------------------------------------------------------------------------
    # Initialization & Lifecycle
    # -------------------------------------------------------------------------

    def __init__(self, parent):
        super().__init__(parent)

        self.parent = parent
        self.ui = parent.ui

        # ------------------------------------------------------------------
        # Data source control
        # ------------------------------------------------------------------
        # "spikeling" : live stream from the board
        # "emulator"  : packets coming from the GUI emulator
        # "none"      : inactive / disconnected state
        self.source_mode = "spikeling"
        self._t_abs_ms = 0.0  # fallback clock if packets arrive without timestamp

        # ------------------------------------------------------------------
        # Reduced extracellular forward-model parameter cache
        # ------------------------------------------------------------------
        # This dict is refreshed from the GUI sliders / toggles in
        # _connect_parameters() and then read by the model update code.
        self._extracellular_params = {}

        # ------------------------------------------------------------------
        # Optional geometry override coming from Tetrode.py
        # ------------------------------------------------------------------
        # If absent, the graph falls back to the legacy hidden 2D didactic model.
        self.tetrode_geometry = None
        self.geometry_source = "default"
        self._init_geometry()

        self.tetrode_distance_matrix_um = {}
        self.tetrode_contacts_um = []
        self._use_saved_tetrode_geometry = False

        # ------------------------------------------------------------------
        # Ground-truth spike detection from the incoming intracellular Vm
        # ------------------------------------------------------------------
        # These spikes drive:
        #   - Template mode waveform launches
        #   - dV/dT mode gating windows
        self.SpikeThreshold = -20.0  # mV, upward-crossing threshold on Vm
        self.SpikeRefractory_ms = 3.0  # ms, per source neuron refractory
        self._t_last_spike_ms = np.full(N_NEURONS, -1e12, dtype=float)

        # ------------------------------------------------------------------
        # Detection on the final extracellular channels (display overlays only)
        # ------------------------------------------------------------------
        # This is not the forward model itself; it is only used to place
        # threshold / spikes / event markers on the scope page.
        self.DetectRefractory_ms = 0.6
        self._t_last_detect_ms = np.full(N_CHANNELS, -1e12, dtype=float)
        self._last_event_ms = -1e12
        self._prev_channel_sample = np.zeros(N_CHANNELS, dtype=float)
        self.DetectionThreshold_uV = -25.0

        # ------------------------------------------------------------------
        # Signal mode / reference mode
        # ------------------------------------------------------------------
        self.signal_mode = "template"  # "template" or "dvdt"
        self.car_enabled = False

        # ------------------------------------------------------------------
        # Hidden geometry constants for the reduced tetrode model
        # ------------------------------------------------------------------
        # The 4 tetrode contacts are placed in a simple square arrangement.
        # The user controls only:
        #   - source distance
        #   - orientation
        #   - spatial falloff
        # while these hidden constants keep the model stable and didactic.
        self._tetrode_spacing_um = 18.0
        self._distance_floor_um = 5.0
        self._reference_distance_um = 50.0

        # Hidden source-cluster offsets for the 3 incoming Spikeling Vm streams.
        # Source 0 = main source controlled by the user.
        # Sources 1 and 2 = auxiliary units offset in space to create distinct
        # multichannel tetrode patterns.
        self._source_cluster_offsets_um = np.array([
            [0.0, 0.0],
            [38.0, 18.0],
            [-28.0, 32.0],
        ], dtype=float)
        self._init_geometry()


        # Per-source hidden gain factors so the 3 units are not identical.
        self._source_gain = np.array([1.00, 0.90, 0.80], dtype=float)

        # ------------------------------------------------------------------
        # Template-mode waveform parameters
        # ------------------------------------------------------------------
        # Canonical negative-first biphasic extracellular spike template.
        self.TemplateAmplitude_uV = 120.0
        self.TemplateSigmaNeg_ms = 0.18
        self.TemplateSigmaPos_ms = 0.28
        self.TemplateDelta_ms = 0.32
        self.TemplateBeta = 0.55

        self._template_time_ms = None
        self._template_waveform = None

        # One active-template list per source neuron.
        # Each list stores currently "ringing" template events that are still
        # contributing to the extracellular waveform.
        self._active_templates = [list() for _ in range(N_NEURONS)]
        self._build_template_waveform()

        # ------------------------------------------------------------------
        # dV/dT-mode parameters
        # ------------------------------------------------------------------
        # The derivative mode uses a lightly smoothed Vm derivative, gated around
        # detected intracellular spikes so subthreshold Vm does not create fake
        # extracellular events everywhere.
        self.dvdt_smooth_tau_ms = 0.20
        self.dvdt_scale_uV_per_mVms = 24.0
        self.dvdt_gate_ms = 1.8

        self._dvdt_vm_smooth = np.zeros(N_NEURONS, dtype=float)
        self._dvdt_gate_remaining_ms = np.zeros(N_NEURONS, dtype=float)

        # ------------------------------------------------------------------
        # Bandpass filter state
        # ------------------------------------------------------------------
        # The displayed / recorded extracellular channels are filtered according to
        # the selected UI preset (spike band or slower band).
        self.bandpass_name = "300 - 3000 Hz"
        self.bandpass_low_hz = 300.0
        self.bandpass_high_hz = 3000.0
        self._filter_sos = None
        # self._filter_zi = None

        # ------------------------------------------------------------------
        # Noise / hum state
        # ------------------------------------------------------------------
        self._hum_phase_rad = 0.0
        self._rng = np.random.default_rng()

        # ------------------------------------------------------------------
        # Continuous latest sample values
        # ------------------------------------------------------------------
        # VmData         : latest intracellular ground-truth Vm values (mV)
        # SourceWaveData : latest clean per-source extracellular contribution
        # ExtraData      : latest final 4-channel tetrode signal (µV-like units)

        # Explicit previous-sample Vm; decoupled from the display buffers
        self._vm_prev = np.zeros(N_NEURONS, dtype=float)

        # Cached geometry and block-filter state
        self._projection_matrix_cache = None
        self._filter_zi_block = None

        # Overflow accounting (packet loss was previously silent)
        self.dropped_packets = 0

        self.VmData = np.zeros(N_NEURONS, dtype=float)
        self.StimData = 0.0
        self.TriggerData = 0.0
        self.SourceWaveData = np.zeros(N_NEURONS, dtype=float)
        self.ExtraData = np.zeros(N_CHANNELS, dtype=float)
        self.GroundTruthSpikeData = np.zeros(N_NEURONS, dtype=int)
        self.ChannelSpikeData = np.zeros(N_CHANNELS, dtype=int)
        self.EventData = 0

        # ------------------------------------------------------------------
        # Overlay buffers
        # ------------------------------------------------------------------
        # These store threshold-crossing markers and merged multichannel events
        # in absolute time so the scope page can draw overlay symbols.
        self._channel_spike_marks = [collections.deque() for _ in range(N_CHANNELS)]
        self._event_marks = collections.deque()

        # ------------------------------------------------------------------
        # Plot state
        # ------------------------------------------------------------------
        # The old version used one PlotWidget / one PlotItem / one threshold line.
        # The new version uses 4 stacked PlotWidgets, one per tetrode contact.
        self._plots_ready = False
        self.time_axis_widget = None
        self._syncing_x_range = False
        self.source_plots = []
        self.ui.ExtraCellular_AutoRange_pushButton.toggled.connect(self._update_shared_y_range)
        theme_manager.themeChanged.connect(self._refresh_overlay_theme)
        for checkbox in (*self._channel_checkboxes(), self.ui.Extracellular_Tetrode_Vm_checkBox,
                         self.ui.Extracellular_Tetrode_Stimulus_checkBox,
                         self.ui.Extracellular_Tetrode_Threshold_checkBox,
                         self.ui.Extracellular_Tetrode_Spikes_checkBox,
                         self.ui.Extracellular_Tetrode_Events_checkBox):
            checkbox.toggled.connect(self._update_plots)

        # Host/container layout inside ExtraCellular_Oscilloscope_widget
        self._plot_host_layout = None

        # Per-channel plotting objects
        self.channel_plot_widgets = []
        self.channel_plot_items = []
        self.channel_viewboxes = []
        self.channel_curves = []
        self.channel_threshold_lines = []
        self.channel_spike_scatters = []
        self.channel_event_scatters = []

        # Compatibility aliases for code paths that still expect Ch1curve...Ch4curve
        self.Ch1curve = None
        self.Ch2curve = None
        self.Ch3curve = None
        self.Ch4curve = None

        # Shared x-axis template for the rolling display window
        self.ExtraCellularx = np.arange(-TIME_WINDOW + SAMPLE_INTERVAL,
                                        SAMPLE_INTERVAL,
                                        SAMPLE_INTERVAL)

        # ------------------------------------------------------------------
        # RX queue / timer
        # ------------------------------------------------------------------
        # Hardware packets are accumulated in a queue and processed in bursts so
        # the serial callback stays light and the GUI updates at a steady cadence.
        self._rx_queue = collections.deque(maxlen=20000)  # ~2 s at 10 kHz
        self._rx_timer = QTimer(self)
        self._rx_timer.setInterval(16)  # ~60 Hz redraw cadence
        self._rx_timer.timeout.connect(self._process_rx_queue)

        # ------------------------------------------------------------------
        # Recording state
        # ------------------------------------------------------------------
        # Same general recording architecture as Graph_Imaging.py.
        self.recording_state = "idle"
        self.recording_detail = ""
        self.recording_stop_reason = ""
        self.recording_path = None
        self.source_generation = 0
        self._rec = {
            "t_ms": [],
            "stim": [],
            "trig": [],
            "vm1": [], "vm2": [], "vm3": [],
            "gt_spike1": [], "gt_spike2": [], "gt_spike3": [],
            "ch1_uV": [], "ch2_uV": [], "ch3_uV": [], "ch4_uV": [],
            "threshold_uV": [],
            "event": [],
        }

        # ------------------------------------------------------------------
        # Serial stream hook
        # ------------------------------------------------------------------
        # The graph listens continuously, but samples are only consumed when the
        # extracellular page is actually connected.
        serial_manager.data_received.connect(self.on_data_received)
        serial_manager.connection_changed.connect(self.on_hardware_connection_changed)

    # -------------------------------------------------------------------------
    # Source Selection
    # -------------------------------------------------------------------------

    def set_source_mode(self, mode: str) -> None:
        """Select driving data source."""
        if mode not in ("spikeling", "emulator", "none"):
            mode = "spikeling"
        if mode == self.source_mode:
            return
        self.stop_recording("Source changed")
        self.source_generation += 1
        self.source_mode = mode
        self._rx_queue.clear()
        if getattr(self.parent, "ExtraCellularConnectionFlag", False):
            self._initialize_buffers()
            self._reset_filter_state()

    def on_hardware_connection_changed(self, connected):
        if not connected and self.source_mode == "spikeling":
            self.disconnect("Hardware disconnected")

    def on_emulator_stopped(self):
        if self.source_mode == "emulator":
            self.disconnect("Emulator stopped")

    def source_ready(self):
        if not getattr(self.parent, "ExtraCellularConnectionFlag", False):
            return False
        if self.source_mode == "spikeling":
            return serial_manager.is_open
        return self.source_mode == "emulator" and self.ui.Emulator_Connect_pushButton.isChecked()

    # -------------------------------------------------------------------------
    # Connect / Disconnect
    # -------------------------------------------------------------------------

    def connect(self):
        """Activate the extracellular pipeline."""
        if getattr(self.parent, "ExtraCellularConnectionFlag", False):
            return
        self.source_generation += 1
        self._initialize_buffers()  # calls _reset_model_state internally
        self._initialize_plot()
        self._connect_parameters()
        self._update_connect_button(True)
        self._reset_filter_state()
        self._invalidate_geometry_cache()
        self.dropped_packets = 0
        self._fs_warning_issued = False

        self._rx_queue.clear()
        self._rx_timer.start()

        self.parent.ExtraCellularConnectionFlag = True

    def disconnect(self, reason="Scope disconnected"):
        """Finalise captured samples before dropping the live pipeline."""
        self.stop_recording(reason)
        if not getattr(self.parent, "ExtraCellularConnectionFlag", False):
            return
        self.source_generation += 1
        self.parent.ExtraCellularConnectionFlag = False
        self.cleanup()
        self.ui.ExtraCellular_ConnectButton.setChecked(False)
        self._update_connect_button(False)

    # -------------------------------------------------------------------------
    # Data Entry Points
    # -------------------------------------------------------------------------


    def on_data_received(self, data: list) -> None:
        if self.source_mode != "spikeling":
            return
        if not getattr(self.parent, "ExtraCellularConnectionFlag", False):
            return

        self._rx_queue.append(data)

    def _process_rx_queue(self):
        """Drain the hardware packet queue at the GUI refresh cadence."""
        if self.source_mode != "spikeling" or not getattr(self.parent, "ExtraCellularConnectionFlag", False):
            self._rx_queue.clear()
            return

        n = min(len(self._rx_queue), MAX_PACKETS_PER_TICK)
        if n == 0:
            return

        packets = [self._rx_queue.popleft() for _ in range(n)]

        overflow = len(self._rx_queue) - MAX_PACKETS_PER_TICK
        if overflow > 0:
            self.dropped_packets += overflow
            for _ in range(overflow):
                self._rx_queue.popleft()

        self._consume_packets(packets)

    def on_emulator_data(self, data: list, *, soma_clamped=False) -> None:
        """Handle one emulator packet or a batch of packets."""
        if self.source_mode != "emulator":
            return
        if isinstance(data, list) and data and isinstance(data[0], (list, tuple, np.ndarray)):
            self._consume_packets(data, soma_clamped=soma_clamped)
        else:
            self._consume_packets([data], soma_clamped=soma_clamped)

    def _consume_packets(self, packets, *, soma_clamped=False) -> None:
        """
        Run the full extracellular pipeline over a block of packets.

        Splitting the pipeline into a per-sample generation stage and a
        per-block filtering/detection stage is what makes the block bandpass
        and the vectorised threshold crossing possible. A capture receives the
        finalised block and its sample-aligned event flags together.

        Parameters
        ----------
        packets : sequence
            Raw 8- or 9-field Spikeling packets in chronological order.
        """
        if not getattr(self.parent, "ExtraCellularConnectionFlag", False):
            return
        if not self._extracellular_params:
            return

        staged = self._generate_raw_block(packets, soma_clamped=soma_clamped)
        if staged is None:
            return

        self._finalize_block(*staged)

        if self._plots_ready:
            self._update_plots()

    def _update_shared_y_range(self, fit):
        """Fit the displayed time interval once across all contacts, or reset."""
        button = self.ui.ExtraCellular_AutoRange_pushButton
        button.setText(self.tr("Reset Y range") if fit else self.tr("Auto Range (all contacts)"))
        if not self._plots_ready:
            return

        low, high = Y_MIN_UV, Y_MAX_UV
        if fit:
            view = self.time_axis_widget.getViewBox()
            start, end = view.viewRange()[0]
            time = self.Time_buffer.data
            visible = (time - time[-1] >= start) & (time - time[-1] <= end)
            peaks = [abs(self.DetectionThreshold_uV)]
            for buffer in self.Extra_buffers:
                values = buffer.data[visible]
                finite = values[np.isfinite(values)]
                if finite.size:
                    peaks.append(float(np.max(np.abs(finite))))
            target = max(abs(Y_MIN_UV), max(peaks) * Y_RANGE_HEADROOM)
            low, high = -target, target

        for plot in self.channel_plot_widgets:
            plot.setYRange(low, high, padding=0)
        self._update_plots()

    def _generate_raw_block(self, packets, *, soma_clamped=False):
        """
        Build the unfiltered tetrode block from a run of incoming packets.

        Pipeline per sample
        -------------------
        1. Detect ground-truth spikes on the three intracellular Vm traces.
        2. Advance the per-source extracellular waveform surrogate
           (canonical template, or gated Vm derivative).
        3. Project the sources onto the 4 contacts with the cached geometry.

        Contamination (independent baseline noise, shared noise, 50 Hz hum)
        and the optional common average reference are then applied to the
        whole block at once.

        Parameters
        ----------
        packets : sequence
            Raw Spikeling packets.

        Returns
        -------
        tuple or None
            ``(t, stim, trig, vm, ground_truth, raw_uV)`` arrays, or ``None``
            if no packet decoded.
        """
        p = self._extracellular_params
        n = len(packets)

        t_arr = np.empty(n, dtype=float)
        stim_arr = np.empty(n, dtype=float)
        trig_arr = np.empty(n, dtype=float)
        vm_arr = np.empty((n, N_NEURONS), dtype=float)
        gt_arr = np.zeros((n, N_NEURONS), dtype=np.int8)
        raw = np.empty((n, N_CHANNELS), dtype=float)

        projection = self._projection_matrix(p).T          # (N_CHANNELS, N_NEURONS)
        source = np.zeros(N_NEURONS, dtype=float)
        count = 0

        for packet in packets:
            sample = parse_spikeling_packet(packet)
            if sample is None:
                continue

            if sample.t_ms is None:
                self._t_fallback_ms = getattr(self, "_t_fallback_ms", 0.0) + SAMPLE_INTERVAL
                t_ms = self._t_fallback_ms
            else:
                t_ms = sample.t_ms

            dt_ms = SAMPLE_INTERVAL if self._t_last_ms is None else (t_ms - self._t_last_ms)
            if (not np.isfinite(dt_ms)) or (dt_ms <= 0.0) or (dt_ms > 1000.0):
                dt_ms = SAMPLE_INTERVAL
            self._t_last_ms = t_ms

            vms = (sample.vm0, sample.vm1, sample.vm2)
            for i in range(N_NEURONS):
                spike = 0 if i == 0 and soma_clamped else self._detect_spike(vms[i], self._vm_prev[i], t_ms, i)
                self._vm_prev[i] = vms[i]
                gt_arr[count, i] = spike
                if self.signal_mode == "dvdt":
                    source[i] = self._dvdt_source_step(i, vms[i], spike, dt_ms)
                else:
                    source[i] = self._template_source_step(i, spike)

            t_arr[count] = t_ms
            stim_arr[count] = sample.stim
            trig_arr[count] = sample.trigger
            vm_arr[count] = vms
            raw[count] = projection @ source
            count += 1

        if count == 0:
            return None

        t_arr, stim_arr, trig_arr = t_arr[:count], stim_arr[:count], trig_arr[:count]
        vm_arr, gt_arr, raw = vm_arr[:count], gt_arr[:count], raw[:count]

        sigma_base = float(p.get("baseline_noise_uV", 5.0))
        sigma_shared = float(p.get("shared_noise_uV", 5.0))
        amplitude_hum = float(p.get("hum_noise_uV", 0.0))

        if sigma_base > 0.0:
            raw += self._rng.normal(scale=sigma_base, size=raw.shape)
        if sigma_shared > 0.0:
            raw += self._rng.normal(scale=sigma_shared, size=(count, 1))
        if amplitude_hum != 0.0:
            raw += amplitude_hum * np.sin(
                2.0 * np.pi * 50.0 * (t_arr / 1000.0) + self._hum_phase_rad
            )[:, None]

        if self.car_enabled:
            raw -= raw.mean(axis=1, keepdims=True)

        if not self._fs_warning_issued and count > 1:
            measured_fs = 1000.0 / float(np.median(np.diff(t_arr)))
            if abs(measured_fs - FS_HZ) / FS_HZ > 0.05:
                print(f"[ExtraCellular] Stream is {measured_fs:.0f} Hz but the bandpass "
                      f"is designed for {FS_HZ:.0f} Hz; cutoffs are scaled accordingly.")
                self._fs_warning_issued = True

        return t_arr, stim_arr, trig_arr, vm_arr, gt_arr, raw

    def _finalize_block(self, t_arr, stim_arr, trig_arr, vm_arr, gt_arr, raw):
        """
        Filter, detect and buffer one block of tetrode samples.

        Parameters
        ----------
        t_arr, stim_arr, trig_arr : numpy.ndarray
            Per-sample time (ms), stimulus and trigger.
        vm_arr, gt_arr : numpy.ndarray
            Per-sample intracellular Vm (mV) and ground-truth spike flags.
        raw : numpy.ndarray
            Unfiltered tetrode block of shape ``(n, N_CHANNELS)``, in µV.
        """
        self._update_detection_threshold(self._extracellular_params)
        filtered = self._apply_bandpass_block(raw)

        events = self._detect_block_crossings(t_arr, filtered)

        # Latest-sample state for downstream readers
        self.VmData[:] = vm_arr[-1]
        self.StimData = float(stim_arr[-1])
        self.TriggerData = float(trig_arr[-1])
        self.GroundTruthSpikeData[:] = gt_arr[-1]
        self.ExtraData[:] = filtered[-1]

        # Rolling buffers (vectorised)
        self.Time_buffer.extend(t_arr)
        self.Stim_buffer.extend(stim_arr)
        self.Trigger_buffer.extend(trig_arr)
        self.Threshold_buffer.extend(
            np.full(t_arr.size, self.DetectionThreshold_uV, dtype=float)
        )
        for i in range(N_NEURONS):
            self.Vm_buffers[i].extend(vm_arr[:, i])
        for k in range(N_CHANNELS):
            self.Extra_buffers[k].extend(filtered[:, k])

        if self.recording_active:
            self._record_block(t_arr, stim_arr, trig_arr, vm_arr, gt_arr, filtered, events)

    def _detect_block_crossings(self, t_arr, channels_uV) -> np.ndarray:
        """
        Locate downward threshold crossings over a whole block.

        Crossings are found with a vectorised comparison and the refractory
        rule is then applied only to the handful of candidate indices, instead
        of running the full per-sample comparison chain in Python.

        Parameters
        ----------
        t_arr : numpy.ndarray
            Sample times in milliseconds.
        channels_uV : numpy.ndarray
            Filtered tetrode block of shape ``(n, N_CHANNELS)``.
        """
        threshold = float(self.DetectionThreshold_uV)
        crossings = []
        events = np.zeros(len(t_arr), dtype=np.uint8)
        self.ChannelSpikeData[:] = 0

        for k in range(N_CHANNELS):
            trace = channels_uV[:, k]
            previous = np.concatenate(([self._prev_channel_sample[k]], trace[:-1]))
            candidates = np.flatnonzero((previous > threshold) & (trace <= threshold))

            for index in candidates:
                t_ms = float(t_arr[index])
                if (t_ms - self._t_last_detect_ms[k]) < self.DetectRefractory_ms:
                    continue
                self._t_last_detect_ms[k] = t_ms
                self.ChannelSpikeData[k] = 1
                self._channel_spike_marks[k].append((t_ms, float(trace[index])))
                crossings.append((t_ms, index))

            self._prev_channel_sample[k] = float(trace[-1])

        self.EventData = 0
        for t_ms, index in sorted(crossings):
            if (t_ms - self._last_event_ms) >= EVENT_MERGE_WINDOW_MS:
                self._last_event_ms = t_ms
                self.EventData = 1
                self._event_marks.append(t_ms)
                events[index] = 1

        t_min = float(t_arr[-1]) - float(TIME_WINDOW)
        for k in range(N_CHANNELS):
            marks = self._channel_spike_marks[k]
            while marks and marks[0][0] < t_min:
                marks.popleft()
        while self._event_marks and self._event_marks[0] < t_min:
            self._event_marks.popleft()
        return events

    # -------------------------------------------------------------------------
    # Extracellular Model
    # -------------------------------------------------------------------------

    def SignalMode(self, checked=None) -> None:
        """
        Toggle signal mode from the UI switch.
        Compatible with Qt toggled(bool) and with direct calls.

        unchecked -> template
        checked   -> dV/dT
        """
        if checked is None:
            s = self.sender()
            if s is not None and hasattr(s, "isChecked"):
                checked = s.isChecked()
            else:
                checked = self.ui.ExtraCellular_SignalMode_toggleButton.isChecked()

        self.set_signal_mode("dvdt" if bool(checked) else "template")

    def set_signal_mode(self, mode: str) -> None:
        """
        Explicit API used by the page helper or internally.

        Important:
        Switching between Template and dV/dT should not leave the display filled
        with stale samples from the previous mode. So we reset the mode-specific
        dynamic state and clear the displayed extracellular buffers.
        """
        mode = (mode or "template").strip().lower()
        if mode not in ("template", "dvdt"):
            mode = "template"

        # Nothing to do
        if mode == self.signal_mode:
            return

        self.signal_mode = mode

        # --------------------------------------------------------------
        # Reset only the dynamic state that is mode-dependent
        # --------------------------------------------------------------
        self._dvdt_vm_smooth[:] = 0.0
        self._dvdt_gate_remaining_ms[:] = 0.0
        self._active_templates = [list() for _ in range(N_NEURONS)]

        self.SourceWaveData[:] = 0.0
        self.ExtraData[:] = 0.0
        self.ChannelSpikeData[:] = 0
        self.EventData = 0

        self._channel_spike_marks = [collections.deque() for _ in range(N_CHANNELS)]
        self._event_marks = collections.deque()

        # --------------------------------------------------------------
        # Clear the displayed extracellular traces so the new mode is
        # visible immediately instead of waiting for the old buffer to
        # scroll out of the time window.
        # --------------------------------------------------------------
        if hasattr(self, "Extra_buffers"):
            for buffer in self.Extra_buffers:
                buffer.fill_with(0.0)
        if hasattr(self, "Threshold_buffer"):
            self.Threshold_buffer.fill_with(float(self.DetectionThreshold_uV))

        # of magnitude in amplitude.

        # Keep time / Vm buffers intact, but redraw the traces immediately
        if self._plots_ready:
            self._update_plots()

    def CAR(self, checked=None) -> None:
        """
        Toggle common average reference (CAR).
        Connected from the page toggle but also called from _connect_parameters().
        """
        if checked is None:
            s = self.sender()
            if s is not None and hasattr(s, "isChecked"):
                checked = s.isChecked()
            else:
                checked = self.ui.ExtraCellular_CAR_toggleButton.isChecked()

        self.car_enabled = bool(checked)

    def _build_template_waveform(self) -> None:
        """
        Precompute the canonical extracellular spike template used in Template mode.

        The waveform is negative-first and biphasic:
            w(t) = A * [ -exp(-t^2 / 2σn²) + β exp(-(t-Δ)^2 / 2σp²) ]

        The template is normalized so its peak absolute value equals TemplateAmplitude_uV.
        """
        t = np.arange(-0.6, 1.6 + SAMPLE_INTERVAL, SAMPLE_INTERVAL, dtype=float)
        neg = -np.exp(-0.5 * (t / max(1e-9, self.TemplateSigmaNeg_ms)) ** 2)
        pos = self.TemplateBeta * np.exp(
            -0.5 * ((t - self.TemplateDelta_ms) / max(1e-9, self.TemplateSigmaPos_ms)) ** 2
        )
        w = neg + pos
        peak = max(1e-12, float(np.max(np.abs(w))))
        w = (self.TemplateAmplitude_uV / peak) * w

        self._template_time_ms = t
        self._template_waveform = w.astype(float)

    def _get_contact_positions(self) -> np.ndarray:
        """
        Return 4 tetrode contact coordinates in µm around the tetrode center.
        We use a simple square geometry because this is a didactic model.
        """
        s = 0.5 * float(self._tetrode_spacing_um)
        return np.array([
            [-s, -s],
            [+s, -s],
            [-s, +s],
            [+s, +s],
        ], dtype=float)

    # -------------------------------------------------------------------------
    # Geometry
    # -------------------------------------------------------------------------

    def _init_geometry(self) -> None:
        """
        Install the default tetrode geometry.

        Called once at construction so the projection matrix is always
        well-defined, including before the user saves a layout from the
        tetrode window.
        """
        self.distance_matrix_um = self._distances_from_positions(
            DEFAULT_SOURCE_POSITIONS_UM, DEFAULT_CONTACT_POSITIONS_UM
        )
        self.geometry_source = "default"
        self._invalidate_geometry_cache()

    @staticmethod
    def _distances_from_positions(sources_um, contacts_um) -> np.ndarray:
        """Compute the 3 × 4 Euclidean distance matrix in micrometres."""
        sources = np.asarray(sources_um, dtype=float)
        contacts = np.asarray(contacts_um, dtype=float)
        if (sources.ndim != 2 or sources.shape[0] != N_NEURONS
                or sources.shape[1] not in (2, 3)
                or contacts.shape != (N_CHANNELS, sources.shape[1])):
            raise ValueError("Expected three sources and four contacts in the same 2D or 3D space.")
        with np.errstate(over="ignore", invalid="ignore"):
            distances = np.linalg.norm(sources[:, None, :] - contacts[None, :, :], axis=2)
        if not np.isfinite(distances).all():
            raise ValueError("Source-contact distances must be finite.")
        return distances

    @classmethod
    def _parse_geometry_payload(cls, payload):
        """Read a named matrix and/or a complete layout in micrometres.

        The current layout has neurons[main/aux1/aux2] and
        tetrode.contacts_um, each with x_um, y_um and z_um. E1–E4 define
        channel order irrespective of list order. Each index, if present,
        must agree with its name. Complete older x/y/z layouts under
        neurons_um are also accepted.
        """
        if not isinstance(payload, dict):
            raise ValueError("Expected a geometry mapping.")

        matrix = None
        if "distance_matrix_um" in payload:
            saved = payload["distance_matrix_um"]
            matrix = np.array([
                [float(saved[source][contact]) for contact in TETRODE_CONTACT_KEYS]
                for source in TETRODE_NEURON_KEYS
            ])
            if not np.isfinite(matrix).all() or (matrix < 0).any():
                raise ValueError("Source-contact distances must be finite and nonnegative.")

        if matrix is None or any(key in payload for key in ("neurons", "neurons_um", "tetrode")):
            legacy = "neurons" not in payload and "neurons_um" in payload
            neurons = payload["neurons_um" if legacy else "neurons"]
            contacts = {}
            for entry in payload["tetrode"]["contacts_um"]:
                name = entry["name"]
                if (name not in TETRODE_CONTACT_KEYS or name in contacts
                        or entry.get("index", int(name[1:])) != int(name[1:])):
                    raise ValueError("Contacts must uniquely identify E1–E4 in channel order.")
                contacts[name] = entry
            axes = ("x", "y", "z") if legacy else ("x_um", "y_um", "z_um")
            calculated = cls._distances_from_positions(
                [[float(neurons[key][axis]) for axis in axes] for key in TETRODE_NEURON_KEYS],
                [[float(contacts[key][axis]) for axis in axes] for key in TETRODE_CONTACT_KEYS],
            )
            if matrix is None:
                return calculated
            if not np.allclose(matrix, calculated, rtol=0, atol=1e-6):
                raise ValueError("Geometry coordinates and distances disagree.")
        return matrix

    def apply_tetrode_geometry(self, payload: dict) -> bool:
        """Keep the last valid layout if any required geometry data are invalid."""
        try:
            matrix = self._parse_geometry_payload(payload)
        except (KeyError, TypeError, ValueError, OverflowError):
            return False

        if not np.array_equal(matrix, self.distance_matrix_um):
            self.stop_recording("Geometry changed")
        self.distance_matrix_um = matrix
        self.tetrode_geometry = payload
        self.geometry_source = "tetrode_window"
        self._invalidate_geometry_cache()
        return True

    def set_geometry_from_positions(self, contacts_um, sources_um) -> None:
        """Install a complete explicit geometry or raise before changing state."""
        matrix = self._distances_from_positions(sources_um, contacts_um)
        if not np.array_equal(matrix, self.distance_matrix_um):
            self.stop_recording("Geometry changed")
        self.distance_matrix_um = matrix
        self.geometry_source = "explicit_positions"
        self._invalidate_geometry_cache()

    def _compute_projection_matrix(self, p: dict) -> np.ndarray:
        """
        Build the source-to-contact geometric gain matrix.

        Extracellular spike amplitude falls off with distance from the soma.
        The exponent is exposed as ``spatial_falloff`` so students can
        interpolate between the point-source monopole limit (exponent 1) and
        the steeper decay observed in dense tissue (exponent 2 or above):

        $$g_{ik} = G_i \\\\left(\\\\frac{d_{\\\\mathrm{ref}}}{d_{ik}}\\\\right)^{\\\\alpha}$$

        Parameters
        ----------
        p : dict
            Live extracellular parameter cache; reads ``spatial_falloff`` and,
            optionally, ``reference_distance_um``.

        Returns
        -------
        numpy.ndarray
            Gain matrix of shape ``(N_NEURONS, N_CHANNELS)``.

        Notes
        -----
        Cached by :meth:`_projection_matrix`; invalidate with
        :meth:`_invalidate_geometry_cache` whenever the geometry or the falloff
        exponent changes.

        References
        ----------
        Gold et al., 2006, Journal of Neurophysiology, "On the Origin of the
        Extracellular Action Potential Waveform: A Modeling Study".
        """
        alpha = max(0.1, float(p.get("spatial_falloff", DEFAULT_SPATIAL_FALLOFF)))
        d_ref = float(p.get("reference_distance_um", REFERENCE_DISTANCE_UM))

        distances = np.maximum(self.distance_matrix_um, MIN_SOURCE_CONTACT_DISTANCE_UM)
        gains = (d_ref / distances) ** alpha
        gains *= SOURCE_RELATIVE_GAIN[:N_NEURONS, None]
        return np.clip(gains, 0.0, 6.0)

    def _get_saved_contact_names(self):
        """
        Return the saved tetrode contact names in channel order.
        Falls back to E1..E4 if the payload is incomplete.
        """
        if self.tetrode_contacts_um:
            names = []
            for k, contact in enumerate(self.tetrode_contacts_um[:N_CHANNELS]):
                names.append(str(contact.get("name", f"E{k + 1}")))
            if len(names) == N_CHANNELS:
                return names

        return [f"E{k + 1}" for k in range(N_CHANNELS)]

    def _compute_projection_matrix_from_saved_geometry(self, p: dict) -> np.ndarray:
        """
        Compute source -> channel geometric gains from the saved 3D tetrode payload.

        The tetrode window already computed the full neuron->contact 3D distances.
        Here we only convert those distances into gains using the same reduced
        pedagogical law already used by the legacy model.
        """
        gamma = float(p.get("spatial_falloff", 1.2))
        gamma = max(0.1, gamma)

        contact_names = self._get_saved_contact_names()
        neuron_keys = ["main", "aux1", "aux2"]

        A = np.zeros((N_NEURONS, N_CHANNELS), dtype=float)

        for j, neuron_key in enumerate(neuron_keys):
            per_contact = self.tetrode_distance_matrix_um.get(neuron_key, {}) or {}

            for k, contact_name in enumerate(contact_names):
                r_um = float(per_contact.get(contact_name, self._reference_distance_um))
                r_um = max(r_um, float(self._distance_floor_um))

                gain = self._source_gain[j] * (float(self._reference_distance_um) / r_um) ** gamma
                A[j, k] = gain

        return np.clip(A, 0.0, 6.0)

    def _compute_projection_matrix_legacy(self, p: dict) -> np.ndarray:
        """
        Legacy hidden 2D didactic geometry used when no saved tetrode geometry
        has been provided yet.
        """
        contacts = self._get_contact_positions()  # (4, 2)
        sources = self._get_source_positions(p)  # (3, 2)

        gamma = float(p.get("spatial_falloff", 1.2))
        gamma = max(0.1, gamma)

        diff = sources[:, None, :] - contacts[None, :, :]
        r = np.linalg.norm(diff, axis=2)
        r = np.maximum(r, float(self._distance_floor_um))

        g = (float(self._reference_distance_um) / r) ** gamma
        g *= self._source_gain[:, None]

        return np.clip(g, 0.0, 6.0)

    def _template_source_step(self, neuron_index: int, spike: int) -> float:
        """
        Advance template-mode source generator for one neuron.

        Every detected intracellular spike starts one copy of the precomputed EAP template.
        Multiple nearby spikes may overlap, so active kernels are kept in a list.
        """
        if spike:
            self._active_templates[neuron_index].append(0)

        if not self._active_templates[neuron_index]:
            return 0.0

        y = 0.0
        new_active = []
        last_idx = len(self._template_waveform) - 1

        for idx in self._active_templates[neuron_index]:
            if 0 <= idx <= last_idx:
                y += float(self._template_waveform[idx])
                idx += 1
                if idx <= last_idx:
                    new_active.append(idx)

        self._active_templates[neuron_index] = new_active
        return float(y)

    def _dvdt_source_step(self, neuron_index: int, vm_now: float, spike: int, dt_ms: float) -> float:
        """
        Advance dV/dT-mode source generator for one neuron.

        Educational implementation:
        1) Lightly smooth intracellular Vm with a one-pole low-pass
        2) Compute signed derivative surrogate: q(t) = -K * dVm/dt
        3) Gate the derivative around detected spike times so slow subthreshold fluctuations
           do not generate a fake extracellular trace
        """
        tau = max(1e-6, float(self.dvdt_smooth_tau_ms))
        alpha = 1.0 - np.exp(-float(dt_ms) / tau)

        prev_s = float(self._dvdt_vm_smooth[neuron_index])
        new_s = prev_s + alpha * (float(vm_now) - prev_s)
        self._dvdt_vm_smooth[neuron_index] = new_s

        dvdt_mV_per_ms = (new_s - prev_s) / max(1e-9, float(dt_ms))
        q = -float(self.dvdt_scale_uV_per_mVms) * dvdt_mV_per_ms

        if spike:
            self._dvdt_gate_remaining_ms[neuron_index] = float(self.dvdt_gate_ms)
        else:
            self._dvdt_gate_remaining_ms[neuron_index] = max(
                0.0,
                float(self._dvdt_gate_remaining_ms[neuron_index]) - float(dt_ms)
            )

        gate = 1.0 if self._dvdt_gate_remaining_ms[neuron_index] > 0.0 else 0.0
        return float(gate * q)

    def _detect_spike(self, vm_now: float, vm_prev: float, t_ms: float, neuron_index: int) -> int:
        """
        Detect ground-truth spikes from intracellular Vm with upward threshold crossing.
        This is the same architectural role as in Graph_Imaging.py.
        """
        crossed_up = (vm_prev < self.SpikeThreshold) and (vm_now >= self.SpikeThreshold)
        if not crossed_up:
            return 0

        if (t_ms - self._t_last_spike_ms[neuron_index]) < self.SpikeRefractory_ms:
            return 0

        self._t_last_spike_ms[neuron_index] = float(t_ms)
        return 1

    def _bandpass_limits_from_ui(self) -> Tuple[float, float]:
        """Map UI preset selection to low/high cutoff frequencies in Hz."""
        idx = int(self.ui.ExtraCellular_Bandpass_comboBox.currentIndex())
        if idx == 1:
            return 100.0, 5000.0
        if idx == 2:
            return 1.0, 300.0
        return 300.0, 3000.0

    def _design_bandpass(self, f_low_hz: float, f_high_hz: float) -> None:
        """
        Design a stable IIR display filter and allocate streaming states.

        Note:
        The 100-5000 Hz preset reaches the nominal Nyquist at 10 kHz sampling.
        We clamp the upper cutoff slightly below Nyquist for filter-design stability,
        while keeping the pedagogical preset meaning unchanged.
        """
        fl = max(0.1, float(f_low_hz))
        fh = min(float(f_high_hz), 0.95 * NYQUIST_HZ)

        if fh <= fl:
            fh = min(max(fl * 1.5, fl + 1.0), 0.95 * NYQUIST_HZ)

        self._filter_sos = butter(3, [fl, fh], btype="bandpass", fs=FS_HZ, output="sos")
        self.bandpass_low_hz = fl
        self.bandpass_high_hz = fh
        self._filter_zi_block = None

    def _reset_filter_state(self) -> None:
        """Reset the streaming filter with the current UI preset."""
        fl, fh = self._bandpass_limits_from_ui()
        self._design_bandpass(fl, fh)
        self._filter_zi_block = None

    def _invalidate_geometry_cache(self) -> None:
        """
        Drop the cached source -> contact gain matrix.

        Called whenever the spatial falloff slider moves or a new tetrode
        geometry is applied. The matrix is otherwise constant across the ~10^4
        samples of one GUI tick, so recomputing the pairwise distances per
        sample is pure overhead.
        """
        self._projection_matrix_cache = None

    def _projection_matrix(self, p: dict) -> np.ndarray:
        """
        Return the cached source -> channel geometric gain matrix.

        Parameters
        ----------
        p : dict
            Live extracellular parameter cache.

        Returns
        -------
        numpy.ndarray
            Gain matrix of shape ``(N_NEURONS, N_CHANNELS)``.
        """
        if self._projection_matrix_cache is None:
            self._projection_matrix_cache = self._compute_projection_matrix(p)
        return self._projection_matrix_cache

    def _make_filter_state(self) -> np.ndarray:
        """
        Allocate the streaming second-order-section delay state.

        SciPy expects ``zi`` with shape ``(n_sections, 2) + x.shape`` minus the
        filtered axis, i.e. ``(n_sections, 2, N_CHANNELS)`` when a
        ``(n_samples, N_CHANNELS)`` block is filtered along axis 0.

        The state is initialised to zeros rather than to
        :func:`scipy.signal.sosfilt_zi`, which returns the steady state for a
        unit DC step. That is inappropriate for a spike-band filter: its DC
        gain is essentially zero, and the extracellular trace is zero-mean and
        starts from rest, so a resting filter is the correct boundary
        condition and avoids a startup transient.

        Returns
        -------
        numpy.ndarray
            Zero-initialised delay state of shape ``(n_sections, 2, N_CHANNELS)``.
        """
        n_sections = self._filter_sos.shape[0]
        return np.zeros((n_sections, 2, N_CHANNELS), dtype=float)

    def _apply_bandpass_block(self, raw_block_uV: np.ndarray) -> np.ndarray:
        """
        Filter a whole tick of tetrode samples in a single SciPy call.

        The per-sample variant issued ``N_CHANNELS`` ``sosfilt`` calls per
        sample (4 x 10^4 calls per emulator tick), each re-validating its
        arguments. Filtering along the time axis is numerically identical
        because the section delay states carry over between blocks.

        Parameters
        ----------
        raw_block_uV : numpy.ndarray
            Unfiltered block of shape ``(n_samples, N_CHANNELS)``, in µV.

        Returns
        -------
        numpy.ndarray
            Band-limited block with the same shape as the input.
        """
        block = np.atleast_2d(np.asarray(raw_block_uV, dtype=float))
        if self._filter_sos is None or block.size == 0:
            return block

        if self._filter_zi_block is None:
            self._filter_zi_block = self._make_filter_state()

        filtered, self._filter_zi_block = sosfilt(
            self._filter_sos, block, axis=0, zi=self._filter_zi_block
        )
        return filtered

    def _update_detection_threshold(self, p: dict) -> None:
        """
        Update the displayed/detection threshold from the current noise settings.

        This threshold is intentionally simple and pedagogical.
        It is not meant to be a full robust-noise estimator yet; its role here is to
        drive the Scope page overlays until the dedicated Spikes page implements richer
        detection controls.
        """
        sigma_base = float(p.get("baseline_noise_uV", 5.0))
        sigma_shared = float(p.get("shared_noise_uV", 5.0))
        a_hum = float(p.get("hum_noise_uV", 0.0))

        # Approximate combined contamination magnitude.
        sigma_eff = np.sqrt(sigma_base ** 2 + sigma_shared ** 2 + (a_hum / np.sqrt(2.0)) ** 2)
        self.DetectionThreshold_uV = -max(
            DETECTION_THRESHOLD_FLOOR_UV,
            DETECTION_SIGMA_MULTIPLIER * float(sigma_eff),
        )


    # -------------------------------------------------------------------------
    # Buffers
    # -------------------------------------------------------------------------

    def _initialize_buffers(self):
        """Create rolling buffers for all plotted variables."""
        self._bufsize = int(TIME_WINDOW / SAMPLE_INTERVAL)

        self.Time_buffer = RingBuffer(self._bufsize, fill=np.nan)
        self.ExtraCellularx = (np.arange(self._bufsize) - (self._bufsize - 1)) * SAMPLE_INTERVAL

        self.Stim_buffer = RingBuffer(self._bufsize)
        self.Trigger_buffer = RingBuffer(self._bufsize)
        self.Threshold_buffer = RingBuffer(self._bufsize, fill=self.DetectionThreshold_uV)
        self.Vm_buffers = [RingBuffer(self._bufsize) for _ in range(N_NEURONS)]
        self.Extra_buffers = [RingBuffer(self._bufsize) for _ in range(N_CHANNELS)]

        # Reset detection / source states
        self._reset_model_state()

    def _append_buffers(self, t_ms):
        """Append latest model states to rolling buffers."""
        self.Time_buffer.append(float(t_ms))
        self.Stim_buffer.append(float(self.StimData))
        self.Trigger_buffer.append(float(self.TriggerData))
        self.Threshold_buffer.append(float(self.DetectionThreshold_uV))

        for i in range(N_NEURONS):
            self.Vm_buffers[i].append(float(self.VmData[i]))
        for k in range(N_CHANNELS):
            self.Extra_buffers[k].append(float(self.ExtraData[k]))

    def _reset_model_state(self) -> None:
        """Reset all dynamic state variables used by the forward model."""
        self._t_last_ms = None
        self._t_fallback_ms = 0.0
        self._t_last_spike_ms[:] = -1e12
        self._t_last_detect_ms[:] = -1e12
        self._last_event_ms = -1e12
        self._prev_channel_sample[:] = 0.0

        self._vm_prev[:] = 0.0
        self._dvdt_vm_smooth[:] = 0.0
        self._dvdt_gate_remaining_ms[:] = 0.0
        self._active_templates = [list() for _ in range(N_NEURONS)]

        self.SourceWaveData[:] = 0.0
        self.GroundTruthSpikeData[:] = 0
        self.ChannelSpikeData[:] = 0
        self.EventData = 0
        self.ExtraData[:] = 0.0
        self.VmData[:] = 0.0
        self.StimData = 0.0
        self.TriggerData = 0.0

        self._channel_spike_marks = [collections.deque() for _ in range(N_CHANNELS)]
        self._event_marks = collections.deque()
        self._hum_phase_rad = float(self._rng.uniform(0.0, 2.0 * np.pi))

        # of magnitude in amplitude.

    # -------------------------------------------------------------------------
    # Plotting
    # -------------------------------------------------------------------------

    def _initialize_plot(self):
        """
        Build 4 stacked extracellular channel plots.
        Each channel gets its own PlotWidget and its own Y axis.
        All plots share the same time axis.
        """

        host = self.ui.ExtraCellular_Oscilloscope_widget

        # --------------------------------------------------------------
        # Force a vertical host layout even if an older/generated UI file
        # left a different layout on the oscilloscope container.
        # --------------------------------------------------------------
        old_layout = host.layout()

        if old_layout is not None:
            # Remove all previous child widgets first
            while old_layout.count():
                item = old_layout.takeAt(0)
                w = item.widget()
                if w is not None:
                    w.deleteLater()

            # If the existing layout is NOT vertical, discard it
            if not isinstance(old_layout, QVBoxLayout):
                old_layout.deleteLater()
                old_layout = None

        # If there is no usable vertical layout, create one now
        if old_layout is None:
            old_layout = QVBoxLayout()
            old_layout.setContentsMargins(0, 0, 0, 0)
            old_layout.setSpacing(2)
            host.setLayout(old_layout)
        else:
            # Make sure margins / spacing are what we want
            old_layout.setContentsMargins(0, 0, 0, 0)
            old_layout.setSpacing(2)

        self._plot_host_layout = old_layout

        self.channel_plot_widgets = []
        self.channel_plot_items = []
        self.channel_curves = []
        self.channel_threshold_lines = []
        self.channel_spike_scatters = []
        self.channel_event_scatters = []

        x = self.ExtraCellularx

        for k in range(N_CHANNELS):
            pw = pg.PlotWidget(host)
            theme_manager.set_plot_background_role(pw, "window_background")
            pw.setAntialiasing(True)
            pw.showGrid(x=True, y=True)

            pi = pw.getPlotItem()
            vb = pi.getViewBox()

            # --- Identical axis footprints -----------------------------
            # Both axes are pinned to fixed sizes so the four data areas are
            # pixel-identical. Without this the bottom axis on the last plot
            # steals ~40 px of signal height from that channel alone.
            left_axis = pi.getAxis("left")
            left_axis.setLabel(f"Ch{k + 1}", units="µV")
            left_axis.enableAutoSIPrefix(False)
            left_axis.setWidth(AXIS_LEFT_WIDTH_PX)

            bottom_axis = pi.getAxis("bottom")
            bottom_axis.enableAutoSIPrefix(False)

            bottom_axis.setStyle(showValues=False)
            bottom_axis.setHeight(AXIS_BOTTOM_HEIGHT_PX)

            # --- Ranges ------------------------------------------------
            vb.enableAutoRange(axis=pg.ViewBox.XAxis, enable=False)
            vb.setXRange(-TIME_WINDOW_DISPLAY, 0, padding=0)
            vb.setLimits(xMin=-TIME_WINDOW, xMax=0)

            # Apply the same fixed voltage limits to all four contacts.
            vb.enableAutoRange(axis=pg.ViewBox.YAxis, enable=False)
            vb.setYRange(Y_MIN_UV, Y_MAX_UV, padding=0)
            vb.setMouseEnabled(x=True, y=False)
            pi.setMenuEnabled(False)
            pi.hideButtons()

            curve = pw.plot(
                x,
                np.zeros_like(x),
                pen=theme_manager.pen(EXTRACELLULAR_CHANNEL_KEYS[k]),
            )

            thr_line = pg.InfiniteLine(
                angle=0,
                movable=False,
                pen=pg.mkPen(theme_manager.active_colour("text_muted"), width=1, style=Qt.DashLine)
            )
            pi.addItem(thr_line, ignoreBounds=True)

            spike_scatter = pg.ScatterPlotItem(symbol="|", size=9, pxMode=True)
            event_scatter = pg.ScatterPlotItem(size=9, pxMode=True)
            pi.addItem(spike_scatter, ignoreBounds=True)
            pi.addItem(event_scatter)

            old_layout.addWidget(pw)

            self.channel_plot_widgets.append(pw)
            self.channel_plot_items.append(pi)
            self.channel_curves.append(curve)
            self.channel_threshold_lines.append(thr_line)
            self.channel_spike_scatters.append(spike_scatter)
            self.channel_event_scatters.append(event_scatter)

        # Equal stretch so no channel is allocated a taller widget than another.
        for k in range(N_CHANNELS):
            old_layout.setStretch(k, 1)
            self.channel_plot_widgets[k].setSizePolicy(
                QSizePolicy.Expanding, QSizePolicy.Expanding
            )
            self.channel_plot_widgets[k].setMinimumHeight(0)

        # Source signals use separate vertical axes from the µV contacts.
        self.source_plots = []
        for checkbox, source, label, units, role in (
            (self.ui.Extracellular_Tetrode_Vm_checkBox, "Vm",
             self.tr("Soma Vm"), "mV", "neuron_vm"),
            (self.ui.Extracellular_Tetrode_Stimulus_checkBox, "Stim",
             self.tr("Stimulus"), "%", "neuron_stimulus"),
        ):
            plot = pg.PlotWidget(host)
            theme_manager.set_plot_background_role(plot, "window_background")
            plot.getAxis("left").setWidth(AXIS_LEFT_WIDTH_PX)
            plot.setLabel("left", label, units=units)
            plot.getAxis("left").enableAutoSIPrefix(False)
            plot.getAxis("bottom").setStyle(showValues=False)
            plot.getAxis("bottom").setHeight(AXIS_BOTTOM_HEIGHT_PX)
            plot.setMenuEnabled(False)
            plot.hideButtons()
            view = plot.getViewBox()
            view.setMouseEnabled(x=True, y=False)
            view.setLimits(xMin=-TIME_WINDOW, xMax=0)
            view.setXRange(-TIME_WINDOW_DISPLAY, 0, padding=0)
            curve = theme_manager.themed_plot(plot, x, np.zeros_like(x), role)
            old_layout.addWidget(plot, 1)
            self.source_plots.append((plot, curve, checkbox, source))

        # Give the shared axis its own row with the same horizontal inset.
        # Its ViewBox is only an anchor for the time scale.
        footer = pg.PlotWidget(host)
        theme_manager.set_plot_background_role(footer, "window_background")
        footer.setMenuEnabled(False)
        footer.hideButtons()
        footer.getAxis("left").setWidth(AXIS_LEFT_WIDTH_PX)
        footer.getAxis("left").setOpacity(0)
        axis = footer.getAxis("bottom")
        axis.enableAutoSIPrefix(False)
        axis.setLabel(self.tr("Time"), units="ms")
        footer.setFixedHeight(2 * footer.fontMetrics().height() + 14)
        view = footer.getViewBox()
        view.setMouseEnabled(x=False, y=False)
        view.setXRange(-TIME_WINDOW_DISPLAY, 0, padding=0)
        old_layout.addWidget(footer)
        self.time_axis_widget = footer

        for plot in (*self.channel_plot_widgets, *(item[0] for item in self.source_plots)):
            plot.getViewBox().sigXRangeChanged.connect(self._sync_x_range)

        # Keep old names for compatibility if other methods expect them
        self.Ch1curve = self.channel_curves[0]
        self.Ch2curve = self.channel_curves[1]
        self.Ch3curve = self.channel_curves[2]
        self.Ch4curve = self.channel_curves[3]

        self._plots_ready = True
        self.ui.ExtraCellular_AutoRange_pushButton.setEnabled(True)
        self._update_plots()

    def _sync_x_range(self, source, bounds):
        if not self._plots_ready or self._syncing_x_range:
            return
        self._syncing_x_range = True
        try:
            for plot in (*self.channel_plot_widgets, *(item[0] for item in self.source_plots),
                         self.time_axis_widget):
                view = plot.getViewBox()
                if view is not source:
                    view.setXRange(*bounds, padding=0)
        finally:
            self._syncing_x_range = False

    def _channel_checkboxes(self):
        return (
            self.ui.Extracellular_Tetrode_Ch1_checkBox,
            self.ui.Extracellular_Tetrode_Ch2_checkBox,
            self.ui.Extracellular_Tetrode_Ch3_checkBox,
            self.ui.Extracellular_Tetrode_Ch4_checkBox,
        )

    def _update_plots(self):
        if not self._plots_ready:
            return
        ui = self.ui
        t_arr = self.Time_buffer.data
        # Ring-buffer padding is not a sampled zero-voltage or stimulus trace.
        valid_time = np.isfinite(t_arr)
        x = t_arr[valid_time] - t_arr[-1]

        visible_channels = [k for k, check in enumerate(self._channel_checkboxes()) if check.isChecked()]
        for plot, curve, checkbox, source in self.source_plots:
            plot.setVisible(checkbox.isChecked())
            if checkbox.isChecked():
                values = self.Vm_buffers[0].data if source == "Vm" else self.Stim_buffer.data
                curve.setData(x, values[valid_time])
        self.time_axis_widget.setVisible(
            bool(visible_channels) or any(item[2].isChecked() for item in self.source_plots)
        )

        show_thr = ui.Extracellular_Tetrode_Threshold_checkBox.isChecked()
        show_spikes = ui.Extracellular_Tetrode_Spikes_checkBox.isChecked()
        show_events = ui.Extracellular_Tetrode_Events_checkBox.isChecked()

        for k in range(N_CHANNELS):
            pw = self.channel_plot_widgets[k]
            pw.setVisible(k in visible_channels)
            if k not in visible_channels:
                continue

            curve = self.channel_curves[k]
            thr_line = self.channel_threshold_lines[k]
            spike_scatter = self.channel_spike_scatters[k]
            event_scatter = self.channel_event_scatters[k]

            curve.setData(x, self.Extra_buffers[k].data[valid_time])

            thr_line.setVisible(show_thr)
            thr_line.setPos(float(self.DetectionThreshold_uV))

            spike_scatter.setVisible(show_spikes)
            if show_spikes and self._channel_spike_marks[k]:
                marks = np.asarray(self._channel_spike_marks[k], dtype=float)
                colour = theme_manager.active_colour(EXTRACELLULAR_CHANNEL_KEYS[k])
                # Spike ticks encode timing. Keep them above the waveform
                # and below the merged-event markers as the range changes.
                y_min, y_max = pw.getViewBox().viewRange()[1]
                tick_y = y_min + 0.85 * (y_max - y_min)
                spike_scatter.setData(
                    x=marks[:, 0] - t_arr[-1],
                    y=np.full(len(marks), tick_y),
                    brush=pg.mkBrush(colour),
                    pen=pg.mkPen(colour),
                )
            else:
                spike_scatter.setData([])

            # Event markers sit at a fixed height in the shared range, so they
            # stay aligned across channels instead of tracking each trace.
            event_scatter.setVisible(show_events)
            if show_events and self._event_marks:
                events = np.asarray(self._event_marks, dtype=float) - t_arr[-1]
                y_min, y_max = pw.getViewBox().viewRange()[1]
                y_event = y_min + 0.95 * (y_max - y_min)
                colour = theme_manager.active_colour("text_primary")
                event_scatter.setData(
                    x=events, y=np.full(events.size, y_event), symbol="t", size=8,
                    brush=pg.mkBrush(colour),
                    pen=pg.mkPen(colour),
                )
            else:
                event_scatter.setData([])

    # -------------------------------------------------------------------------
    # Recording
    # -------------------------------------------------------------------------

    def _refresh_overlay_theme(self, *_):
        colour = theme_manager.active_colour("text_muted")
        for line in self.channel_threshold_lines:
            line.setPen(pg.mkPen(colour, width=1, style=Qt.DashLine))
        self._update_plots()

    @property
    def recording_active(self):
        return self.recording_state in ("armed", "recording")

    def _set_recording_state(self, state, detail=""):
        self.recording_state = state
        self.recording_detail = detail
        self.parent.extracellular_page.refresh_recording()

    @staticmethod
    def _output_paths(path):
        return path, path.with_name(path.stem + "_meta.json")

    @classmethod
    def _output_identity(cls, path):
        identities = []
        for output in cls._output_paths(path):
            try:
                info = output.stat()
            except FileNotFoundError:
                identities.append(None)
            else:
                identities.append((info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns))
        return tuple(identities)

    def start_recording(self, path):
        if self.recording_state not in ("idle", "saved", "empty") or not self.source_ready():
            return False
        # Process the pre-click hardware backlog for display/detector continuity
        # while capture is still idle. Only later processed blocks are recorded.
        while self.source_mode == "spikeling" and self._rx_queue:
            self._process_rx_queue()
        self.recording_path = path
        self._recording_targets = self._output_identity(path)
        self._rec_dropped_at_start = self.dropped_packets
        self._rec_metadata = {
            "signal_mode": self.signal_mode,
            "car_enabled": bool(self.car_enabled),
            "bandpass_low_hz": float(self.bandpass_low_hz),
            "bandpass_high_hz": float(self.bandpass_high_hz),
            "sample_rate_hz": float(FS_HZ),
            "source": self.source_mode,
            "time_basis": "model_time",
            "distance_matrix_um": self.distance_matrix_um.tolist(),
            "params": dict(self._extracellular_params),
            "event_column": "sample_aligned_merged_detection_v1",
        }
        self.recording_stop_reason = ""
        self._set_recording_state("armed")
        return True

    def stop_recording(self, reason="Stopped", *, retry=False, path=None):
        if self.recording_state == "saving":
            return False
        if self.recording_state == "error" and not retry:
            return False
        if not self.recording_active and self.recording_state != "error":
            return True
        if self.recording_active:
            self.recording_stop_reason = reason
            self._rec_metadata["stop_reason"] = reason
            self._rec_metadata["dropped_packets"] = self.dropped_packets - self._rec_dropped_at_start
        count = len(self._rec["t_ms"])
        if not count:
            self._set_recording_state("empty", reason)
            return True

        self._set_recording_state("saving")
        try:
            if path is not None and path != self.recording_path:
                self._recording_targets = self._output_identity(path)
                self.recording_path = path
            self._export_csv()
        except (OSError, ValueError, csv.Error) as error:
            self._set_recording_state("error", str(error))
            return False
        for values in self._rec.values():
            values.clear()
        self._set_recording_state("saved", self.tr("%1 samples").replace("%1", f"{count:,}"))
        return True

    def _record_block(self, t_arr, stim_arr, trig_arr, vm_arr, gt_arr, filtered, events) -> None:
        """
        Append a whole block to the recording buffers.

        ``signal_mode`` is no longer stored per sample: it was a constant
        string replicated ~6 x 10^5 times per recorded minute. It is written
        once into the metadata sidecar instead.
        """
        self._rec["t_ms"].extend(t_arr.tolist())
        self._rec["stim"].extend(stim_arr.tolist())
        self._rec["trig"].extend(trig_arr.tolist())

        for i, key in enumerate(("vm1", "vm2", "vm3")):
            self._rec[key].extend(vm_arr[:, i].tolist())
        for i, key in enumerate(("gt_spike1", "gt_spike2", "gt_spike3")):
            self._rec[key].extend(gt_arr[:, i].tolist())
        for k, key in enumerate(("ch1_uV", "ch2_uV", "ch3_uV", "ch4_uV")):
            self._rec[key].extend(filtered[:, k].tolist())

        self._rec["threshold_uV"].extend(
            [float(self.DetectionThreshold_uV)] * t_arr.size
        )
        self._rec["event"].extend(events.tolist())
        if self.recording_state == "armed":
            self._set_recording_state("recording")

    def _export_csv(self):
        """
        Write the recorded extracellular session to CSV plus a metadata sidecar.

        """
        path, sidecar = self._output_paths(self.recording_path)
        frame = pd.DataFrame({
            "Time (ms)": self._rec["t_ms"],
            "Stim": self._rec["stim"],
            "Trigger": self._rec["trig"],
            "Vm1 (mV)": self._rec["vm1"],
            "Vm2 (mV)": self._rec["vm2"],
            "Vm3 (mV)": self._rec["vm3"],
            "GT Spike1": self._rec["gt_spike1"],
            "GT Spike2": self._rec["gt_spike2"],
            "GT Spike3": self._rec["gt_spike3"],
            "Ch1 (uV)": self._rec["ch1_uV"],
            "Ch2 (uV)": self._rec["ch2_uV"],
            "Ch3 (uV)": self._rec["ch3_uV"],
            "Ch4 (uV)": self._rec["ch4_uV"],
            "Threshold (uV)": self._rec["threshold_uV"],
            "Event": self._rec["event"],
        })
        metadata = dict(self._rec_metadata, sample_count=len(frame))
        stage = Path(mkdtemp(prefix=".extracellular-", dir=path.parent))
        staged_csv, staged_json = stage / "samples.csv", stage / "metadata.json"
        backup = stage / "previous.csv"
        preserve_backup = False
        try:
            with staged_csv.open("w", encoding="utf-8", newline="") as handle:
                frame.to_csv(handle, index=False)
                handle.flush()
                os.fsync(handle.fileno())
            with staged_json.open("w", encoding="utf-8") as handle:
                json.dump(metadata, handle, indent=2, allow_nan=False)
                handle.flush()
                os.fsync(handle.fileno())

            with staged_csv.open(encoding="utf-8", newline="") as handle:
                rows = csv.reader(handle)
                header = next(rows, None)
                sample_count = 0
                for row in rows:
                    if len(row) != len(frame.columns):
                        raise ValueError("Staged CSV contains a malformed sample row.")
                    sample_count += 1
            with staged_json.open(encoding="utf-8") as handle:
                verified_metadata = json.load(handle)
            if (header != list(frame.columns) or sample_count != len(frame)
                    or verified_metadata != metadata):
                raise ValueError("Staged recording failed validation.")

            if self._output_identity(path) != self._recording_targets:
                raise FileExistsError("Destination changed since confirmation. Use a different filename.")
            if path.exists():
                shutil.copy2(path, backup)
            os.replace(staged_csv, path)
            try:
                os.replace(staged_json, sidecar)
            except OSError:
                try:
                    if backup.exists():
                        os.replace(backup, path)
                    else:
                        path.unlink()
                    self._recording_targets = self._output_identity(path)
                except OSError as rollback_error:
                    preserve_backup = True
                    raise OSError(
                        f"CSV was published but metadata and rollback failed. "
                        f"Recovery files are in {stage}. Save to a different filename. "
                        f"{rollback_error}"
                    ) from rollback_error
                raise
        finally:
            if not preserve_backup:
                shutil.rmtree(stage, ignore_errors=True)

    # -------------------------------------------------------------------------
    # UI Helpers
    # -------------------------------------------------------------------------

    def _connect_parameters(self):
        """
        Cache extracellular parameter values from the scope page and keep them updated.

        Just like in Graph_Imaging.py, the graph owns the live model dictionary and keeps
        it synchronized with the UI widgets.
        """
        if getattr(self, "_params_connected", False):
            return
        self._params_connected = True

        ui = self.ui
        p = self._extracellular_params

        def update(_=None):
            # Geometry
            p["spatial_falloff"] = float(ui.ExtraCellular_Spread_Slider.value()) / 10.0
            self._invalidate_geometry_cache()

            # Noise / contamination
            # A cleared readout label means the parameter is out of play, so the
            # toggle must actually zero the contribution rather than leave the
            # slider's reset value active.
            p["baseline_noise_uV"] = (
                float(ui.ExtraCellular_BaselineNoise_Slider.value())
                if ui.ExtraCellular_BaselineNoise_toggleButton.isChecked() else 0.0
            )
            p["shared_noise_uV"] = (
                float(ui.ExtraCellular_SharedNoise_Slider.value())
                if ui.ExtraCellular_SharedNoise_toggleButton.isChecked() else 0.0
            )
            p["hum_noise_uV"] = (
                float(ui.ExtraCellular_HumNoise_Slider.value())
                if ui.ExtraCellular_HumNoise_toggleButton.isChecked() else 0.0
            )

            # Bandpass preset
            fl, fh = self._bandpass_limits_from_ui()
            p["bandpass_low_hz"] = fl
            p["bandpass_high_hz"] = fh
            self.bandpass_name = str(ui.ExtraCellular_Bandpass_comboBox.currentText()).strip()

            # Toggle-driven states
            self.set_signal_mode("dvdt" if ui.ExtraCellular_SignalMode_toggleButton.isChecked() else "template")
            self.CAR(ui.ExtraCellular_CAR_toggleButton.isChecked())

            # Rebuild filter only when the preset changed
            if (
                self._filter_sos is None or
                abs(fl - self.bandpass_low_hz) > 1e-9 or
                abs(min(fh, 0.95 * NYQUIST_HZ) - self.bandpass_high_hz) > 1e-9
            ):
                self._design_bandpass(fl, fh)

            self._update_detection_threshold(p)

        # Initial cache fill
        update()

        # Slider + combo connections
        widgets = [
            ui.ExtraCellular_Spread_Slider,
            ui.ExtraCellular_BaselineNoise_Slider,
            ui.ExtraCellular_SharedNoise_Slider,
            ui.ExtraCellular_HumNoise_Slider,
            ui.ExtraCellular_Bandpass_comboBox,
            ui.ExtraCellular_SignalMode_toggleButton,
            ui.ExtraCellular_CAR_toggleButton,
            ui.ExtraCellular_BaselineNoise_toggleButton,
            ui.ExtraCellular_SharedNoise_toggleButton,
            ui.ExtraCellular_HumNoise_toggleButton,
            ui.ExtraCellular_Spread_toggleButton,
        ]

        for w in widgets:
            if hasattr(w, "valueChanged"):
                w.valueChanged.connect(update)
            elif hasattr(w, "currentIndexChanged"):
                w.currentIndexChanged.connect(update)
            elif hasattr(w, "toggled"):
                w.toggled.connect(update)

    def _update_connect_button(self, connected: bool):
        """Update connect button appearance."""
        if connected:
            self.ui.ExtraCellular_ConnectButton.setText("Connected")
            self.ui.ExtraCellular_ConnectButton.setStyleSheet(
                f"color: rgb{tuple(DarkSolarized[3])};\n"
                f"background-color: rgb{tuple(DarkSolarized[11])};\n"
                f"border: 1px solid rgb{tuple(DarkSolarized[14])};\n"
                f"border-radius: 10px;"
            )
        else:
            self.ui.ExtraCellular_ConnectButton.setText("Connect Tetrode recording to Spikeling")
            self.ui.ExtraCellular_ConnectButton.setStyleSheet(
                f"color: rgb{tuple(DarkSolarized[14])};\n"
                f"background-color: rgb{tuple(DarkSolarized[2])};\n"
                f"border: 1px solid rgb{tuple(DarkSolarized[14])};\n"
                f"border-radius: 10px;"
            )

    # -------------------------------------------------------------------------
    # Cleanup
    # -------------------------------------------------------------------------

    def cleanup(self):

        host = self.ui.ExtraCellular_Oscilloscope_widget
        layout = host.layout()
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                w = item.widget()
                if w is not None:
                    w.deleteLater()

        self.channel_plot_widgets = []
        self.channel_plot_items = []
        self.channel_curves = []
        self.channel_threshold_lines = []
        self.channel_spike_scatters = []
        self.channel_event_scatters = []

        self.time_axis_widget = None
        self.source_plots = []
        self._plots_ready = False
        self.ui.ExtraCellular_AutoRange_pushButton.setChecked(False)
        self.ui.ExtraCellular_AutoRange_pushButton.setEnabled(False)

        self._reset_model_state()
        self._filter_sos = None
        self._filter_zi_block = None
        self._projection_matrix_cache = None

        if hasattr(self, "_rx_timer"):
            self._rx_timer.stop()
        self._rx_queue.clear()
