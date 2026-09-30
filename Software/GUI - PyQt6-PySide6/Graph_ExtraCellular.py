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

from PySide6.QtCore import QObject, QTimer, Qt
from PySide6.QtWidgets import QVBoxLayout
import pyqtgraph as pg
import numpy as np
import pandas as pd
import collections
from typing import Tuple

from scipy.signal import butter, sosfilt

import Parameters_Settings as Settings
from serial_manager import serial_manager
from graph_core import RingBuffer, configure_scope, parse_spikeling_packet, resolve_csv_path


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

# Per-unit amplitude scaling. Real units differ in soma size and spike
# amplitude, so identical projections would make the sorting exercise trivial.
SOURCE_RELATIVE_GAIN = np.array([1.00, 0.90, 0.80], dtype=float)

# Neuron keys used by Tetrode.py in its saved distance matrix.
TETRODE_NEURON_KEYS = ("main", "aux1", "aux2")

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
        self.record_flag = False
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

    # -------------------------------------------------------------------------
    # Source Selection
    # -------------------------------------------------------------------------

    def set_source_mode(self, mode: str) -> None:
        """Select driving data source."""
        if mode not in ("spikeling", "emulator", "none"):
            mode = "spikeling"
        self.source_mode = mode

    # -------------------------------------------------------------------------
    # Connect / Disconnect
    # -------------------------------------------------------------------------

    def connect(self):
        """Activate the extracellular pipeline."""
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

        if hasattr(self.parent, "extracellular_page"):
            self.parent.extracellular_page.ExtraCellularConnectionFlag = True
        self.parent.ExtraCellularConnectionFlag = True
        self._fs_warning_issued = False

    def disconnect(self):
        """Deactivate extracellular pipeline."""
        self.cleanup()
        self._update_connect_button(False)

        if hasattr(self.parent, "extracellular_page"):
            self.parent.extracellular_page.ExtraCellularConnectionFlag = False
        self.parent.ExtraCellularConnectionFlag = False

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

    def on_emulator_data(self, data: list) -> None:
        """Handle one emulator packet or a batch of packets."""
        if isinstance(data, list) and data and isinstance(data[0], (list, tuple, np.ndarray)):
            self._consume_packets(data)
        else:
            self._consume_packets([data])

    def _consume_packets(self, packets) -> None:
        """
        Run the full extracellular pipeline over a block of packets.

        Splitting the pipeline into a per-sample generation stage and a
        per-block filtering/detection stage is what makes the block bandpass
        and the vectorised threshold crossing possible; the record state and
        the redraw are also evaluated once per block instead of once per sample.

        Parameters
        ----------
        packets : sequence
            Raw 8- or 9-field Spikeling packets in chronological order.
        """
        if not getattr(self.parent, "ExtraCellularConnectionFlag", False):
            return
        if not self._extracellular_params:
            return

        staged = self._generate_raw_block(packets)
        if staged is None:
            return

        self._handle_recording()
        self._finalize_block(*staged)

        if self._plots_ready:
            self._update_plots()

    def _generate_raw_block(self, packets):
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
                spike = self._detect_spike(vms[i], self._vm_prev[i], t_ms, i)
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

        self._detect_block_crossings(t_arr, filtered)

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

        if self.record_flag:
            self._record_block(t_arr, stim_arr, trig_arr, vm_arr, gt_arr, filtered)

    def _detect_block_crossings(self, t_arr, channels_uV) -> None:
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
        event_times = []
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
                event_times.append(t_ms)

            self._prev_channel_sample[k] = float(trace[-1])

        self.EventData = 0
        for t_ms in sorted(event_times):
            if (t_ms - self._last_event_ms) >= EVENT_MERGE_WINDOW_MS:
                self._last_event_ms = t_ms
                self.EventData = 1
                self._event_marks.append(t_ms)

        t_min = float(t_arr[-1]) - float(TIME_WINDOW)
        for k in range(N_CHANNELS):
            marks = self._channel_spike_marks[k]
            while marks and marks[0][0] < t_min:
                marks.popleft()
        while self._event_marks and self._event_marks[0] < t_min:
            self._event_marks.popleft()

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
        """
        Compute Euclidean source-to-contact distances.

        Parameters
        ----------
        sources_um : array_like
            Source coordinates of shape ``(N_NEURONS, d)`` with ``d`` of 2 or 3.
        contacts_um : array_like
            Contact coordinates of shape ``(N_CHANNELS, d)``.

        Returns
        -------
        numpy.ndarray
            Distance matrix of shape ``(N_NEURONS, N_CHANNELS)``, in micrometres,
            floored at :data:`MIN_SOURCE_CONTACT_DISTANCE_UM`.

        Raises
        ------
        ValueError
            If the two arrays do not share the same spatial dimensionality.
        """
        sources = np.atleast_2d(np.asarray(sources_um, dtype=float))
        contacts = np.atleast_2d(np.asarray(contacts_um, dtype=float))

        if sources.shape[1] != contacts.shape[1]:
            raise ValueError(
                f"Source and contact coordinates must share a dimensionality; "
                f"got {sources.shape[1]}D sources and {contacts.shape[1]}D contacts."
            )

        deltas = sources[:, None, :] - contacts[None, :, :]
        distances = np.linalg.norm(deltas, axis=2)
        return np.maximum(distances, MIN_SOURCE_CONTACT_DISTANCE_UM)

    def apply_tetrode_geometry(self, payload: dict) -> None:
        """
        Install the layout saved by the tetrode window.

        The payload is the authoritative geometry description, so its
        precomputed 3D ``distance_matrix_um`` is preferred over any 2D
        coordinate list: the tetrode window already accounts for contact depth,
        which a planar projection would discard.

        Parameters
        ----------
        payload : dict
            Saved tetrode description. Recognised keys:

            ``distance_matrix_um``
                ``{neuron_key: {contact_name: distance_um}}``, the preferred
                route.
            ``tetrode``
                ``{"contacts_um": [{"index": int, "name": str,
                "x": float, "y": float, "z": float}, ...]}``, used both to
                order the contacts and as a coordinate fallback.
            ``neurons_um``
                Optional ``{neuron_key: {"x": .., "y": .., "z": ..}}`` used with
                the contact coordinates when no distance matrix is present.

        Notes
        -----
        Silently ignores a malformed payload and keeps the previous geometry,
        because losing the electrode layout mid-recording is worse than
        continuing with a stale one.
        """
        if not isinstance(payload, dict):
            return

        contact_names = self._contact_names_from_payload(payload)

        matrix = self._distance_matrix_from_payload(payload, contact_names)
        if matrix is None:
            matrix = self._distance_matrix_from_payload_positions(payload, contact_names)
        if matrix is None:
            return

        self.distance_matrix_um = matrix
        self.tetrode_geometry = payload
        self.geometry_source = "tetrode_window"
        self._invalidate_geometry_cache()

    def set_geometry_from_positions(self, contacts_um, sources_um) -> None:
        """
        Install a geometry directly from coordinate arrays.

        Convenience entry point for scripted setups and unit tests; the GUI
        path goes through :meth:`apply_tetrode_geometry`.

        Parameters
        ----------
        contacts_um : array_like
            Contact coordinates of shape ``(N_CHANNELS, d)``.
        sources_um : array_like
            Source coordinates of shape ``(N_NEURONS, d)``.

        Raises
        ------
        ValueError
            If either array has the wrong number of rows.
        """
        contacts = np.atleast_2d(np.asarray(contacts_um, dtype=float))
        sources = np.atleast_2d(np.asarray(sources_um, dtype=float))

        if contacts.shape[0] != N_CHANNELS:
            raise ValueError(f"Expected {N_CHANNELS} contacts, got {contacts.shape[0]}.")
        if sources.shape[0] != N_NEURONS:
            raise ValueError(f"Expected {N_NEURONS} sources, got {sources.shape[0]}.")

        self.distance_matrix_um = self._distances_from_positions(sources, contacts)
        self.geometry_source = "explicit_positions"
        self._invalidate_geometry_cache()

    @staticmethod
    def _contact_names_from_payload(payload: dict) -> list:
        """
        Resolve contact names in channel order.

        Parameters
        ----------
        payload : dict
            Saved tetrode description.

        Returns
        -------
        list of str
            Contact names, ordered by their saved index, padded with ``E1..E4``
            if the payload is incomplete.
        """
        contacts = (payload.get("tetrode", {}) or {}).get("contacts_um", []) or []
        try:
            contacts = sorted(contacts, key=lambda c: int(c.get("index", 999)))
        except (TypeError, ValueError):
            pass

        names = [str(c.get("name", f"E{k + 1}")) for k, c in enumerate(contacts[:N_CHANNELS])]
        names += [f"E{k + 1}" for k in range(len(names), N_CHANNELS)]
        return names

    def _distance_matrix_from_payload(self, payload: dict, contact_names) -> np.ndarray:
        """
        Read the precomputed 3D distance matrix from a saved payload.

        Parameters
        ----------
        payload : dict
            Saved tetrode description.
        contact_names : sequence of str
            Contact names in channel order.

        Returns
        -------
        numpy.ndarray or None
            Distance matrix of shape ``(N_NEURONS, N_CHANNELS)``, or ``None``
            if the payload carries no usable matrix.
        """
        saved = payload.get("distance_matrix_um") or {}
        if not saved:
            return None

        matrix = np.full((N_NEURONS, N_CHANNELS), REFERENCE_DISTANCE_UM, dtype=float)
        for i, neuron_key in enumerate(TETRODE_NEURON_KEYS[:N_NEURONS]):
            per_contact = saved.get(neuron_key) or {}
            for k, contact_name in enumerate(contact_names):
                try:
                    matrix[i, k] = float(per_contact[contact_name])
                except (KeyError, TypeError, ValueError):
                    continue

        return np.maximum(matrix, MIN_SOURCE_CONTACT_DISTANCE_UM)

    def _distance_matrix_from_payload_positions(self, payload: dict, contact_names) -> np.ndarray:
        """
        Derive distances from explicit coordinates when no matrix was saved.

        Parameters
        ----------
        payload : dict
            Saved tetrode description.
        contact_names : sequence of str
            Contact names in channel order, used only for diagnostics.

        Returns
        -------
        numpy.ndarray or None
            Distance matrix of shape ``(N_NEURONS, N_CHANNELS)``, or ``None``
            if coordinates for either side are missing.
        """
        contacts = (payload.get("tetrode", {}) or {}).get("contacts_um", []) or []
        neurons = payload.get("neurons_um") or {}
        if len(contacts) < N_CHANNELS or not neurons:
            return None

        def coordinates(entry):
            return [float(entry.get(axis, 0.0)) for axis in ("x", "y", "z")]

        try:
            contact_xyz = np.array([coordinates(c) for c in contacts[:N_CHANNELS]], dtype=float)
            source_xyz = np.array(
                [coordinates(neurons.get(key, {})) for key in TETRODE_NEURON_KEYS[:N_NEURONS]],
                dtype=float,
            )
        except (TypeError, ValueError):
            return None

        return self._distances_from_positions(source_xyz, contact_xyz)

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
        alpha = max(0.1, float(p.get("spatial_falloff", 2.0)))
        d_ref = float(p.get("reference_distance_um", REFERENCE_DISTANCE_UM))

        gains = (d_ref / self.distance_matrix_um) ** alpha
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

        self.Time_buffer = RingBuffer(self._bufsize)
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
            pw.setBackground(Settings.DarkSolarized[0])
            pw.setAntialiasing(True)
            pw.showGrid(x=True, y=True)

            pi = pw.getPlotItem()
            configure_scope(pi)
            vb = pi.getViewBox()

            pi.getAxis("left").setLabel(f"Ch{k + 1}", units="µV")
            pi.getAxis("bottom").enableAutoSIPrefix(False)

            if k == N_CHANNELS - 1:
                pi.getAxis("bottom").setLabel("Time", units="ms")
            else:
                pi.getAxis("bottom").setStyle(showValues=False)

            vb.enableAutoRange(axis=pg.ViewBox.XAxis, enable=False)
            vb.setXRange(-TIME_WINDOW_DISPLAY, 0, padding=0)
            vb.setLimits(xMin=-TIME_WINDOW, xMax=0)
            vb.enableAutoRange(axis=pg.ViewBox.YAxis, enable=True)
            vb.setMouseEnabled(x=True, y=False)

            # Link X axes to the first plot
            if k > 0:
                pw.setXLink(self.channel_plot_widgets[0])

            curve = pw.plot(
                x,
                np.zeros_like(x),
                pen=pg.mkPen(CHANNEL_COLORS[k], width=PEN_WIDTH, cosmetic=True)
            )

            thr_line = pg.InfiniteLine(
                angle=0,
                movable=False,
                pen=pg.mkPen(Settings.DarkSolarized[8], width=1, style=pg.QtCore.Qt.DashLine)
            )
            pi.addItem(thr_line)

            spike_scatter = pg.ScatterPlotItem(size=7, pxMode=True)
            event_scatter = pg.ScatterPlotItem(size=9, pxMode=True)
            pi.addItem(spike_scatter)
            pi.addItem(event_scatter)

            old_layout.addWidget(pw)

            self.channel_plot_widgets.append(pw)
            self.channel_plot_items.append(pi)
            self.channel_curves.append(curve)
            self.channel_threshold_lines.append(thr_line)
            self.channel_spike_scatters.append(spike_scatter)
            self.channel_event_scatters.append(event_scatter)

        # Keep old names for compatibility if other methods expect them
        self.Ch1curve = self.channel_curves[0]
        self.Ch2curve = self.channel_curves[1]
        self.Ch3curve = self.channel_curves[2]
        self.Ch4curve = self.channel_curves[3]

        self._plots_ready = True

    def _update_plots(self):
        ui = self.ui
        t_arr = self.Time_buffer.data
        x = t_arr - t_arr[-1]

        checks = [
            ui.Extracellular_Tetrode_Ch1_checkBox,
            ui.Extracellular_Tetrode_Ch2_checkBox,
            ui.Extracellular_Tetrode_Ch3_checkBox,
            ui.Extracellular_Tetrode_Ch4_checkBox,
        ]

        show_thr = ui.Extracellular_Tetrode_Threshold_checkBox.isChecked()
        show_spikes = ui.Extracellular_Tetrode_Spikes_checkBox.isChecked()
        show_events = ui.Extracellular_Tetrode_Events_checkBox.isChecked()

        for k in range(N_CHANNELS):
            pw = self.channel_plot_widgets[k]
            curve = self.channel_curves[k]
            thr_line = self.channel_threshold_lines[k]
            spike_scatter = self.channel_spike_scatters[k]
            event_scatter = self.channel_event_scatters[k]

            visible = checks[k].isChecked()
            pw.setVisible(visible)

            if not visible:
                continue

            y = self.Extra_buffers[k].data
            curve.setData(x, y)

            # Threshold line for this channel
            thr_line.setVisible(show_thr)
            thr_line.setPos(float(self.DetectionThreshold_uV))

            # Channel-specific spike markers
            spike_scatter.setVisible(show_spikes)
            if show_spikes and self._channel_spike_marks[k]:
                marks = np.asarray(self._channel_spike_marks[k], dtype=float)
                spike_scatter.setData(
                    x=marks[:, 0] - t_arr[-1], y=marks[:, 1], symbol="o", size=6,
                    brush=pg.mkBrush(CHANNEL_COLORS[k]), pen=pg.mkPen(CHANNEL_COLORS[k]),
                )
            else:
                spike_scatter.setData([])

            # Event markers copied to each visible subplot
            event_scatter.setVisible(show_events)
            if show_events and self._event_marks:
                span = max(10.0, float(np.ptp(y))) if y.size else 100.0
                y_event = (float(np.max(y)) if y.size else 0.0) + EVENT_MARKER_HEADROOM * span
                events = np.asarray(self._event_marks, dtype=float) - t_arr[-1]
                event_scatter.setData(
                    x=events, y=np.full(events.size, y_event), symbol="t", size=8,
                    brush=pg.mkBrush(Settings.DarkSolarized[10]),
                    pen=pg.mkPen(Settings.DarkSolarized[10]),
                )
            else:
                event_scatter.setData([])

    # -------------------------------------------------------------------------
    # Recording
    # -------------------------------------------------------------------------

    def _handle_recording(self):
        """
        Manage record toggle and export on stop.
        This keeps the same architecture as Graph_Imaging.py.
        """
        checked = bool(self.ui.ExtraCellular_DataRecording_Record_pushButton.isChecked())

        # Start edge: OFF -> ON
        if checked and (not self.record_flag):
            self.record_flag = True
            self._rec_signal_mode = str(self.signal_mode)
            self._rec_dropped_at_start = int(self.dropped_packets)

            if not hasattr(self, "_rec") or not isinstance(self._rec, dict):
                self._rec = {}

            for k in [
                "t_ms", "stim", "trig",
                "vm1", "vm2", "vm3",
                "gt_spike1", "gt_spike2", "gt_spike3",
                "ch1_uV", "ch2_uV", "ch3_uV", "ch4_uV",
                "threshold_uV", "event",
            ]:
                self._rec.setdefault(k, [])
                self._rec[k].clear()
            return

        # Stop edge: ON -> OFF
        if (not checked) and self.record_flag:
            self._export_csv()
            self.record_flag = False
            try:
                for k in self._rec:
                    self._rec[k].clear()
            except Exception:
                pass
            return

    def _record_block(self, t_arr, stim_arr, trig_arr, vm_arr, gt_arr, filtered) -> None:
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
        self._rec["event"].extend([0] * t_arr.size)

    def _export_csv(self):
        """
        Write the recorded extracellular session to CSV plus a metadata sidecar.

        Uses :func:`graph_core.resolve_csv_path`, which appends rather than
        replaces the suffix: ``rec_v1.2`` no longer becomes ``rec_v1.csv``.
        """
        if (not hasattr(self, "_rec")) or (len(self._rec.get("t_ms", [])) == 0):
            return

        path = resolve_csv_path(self.ui.ExtraCellular_SelectedFolderLabel.text())
        if path is None:
            return

        pd.DataFrame({
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
        }).to_csv(path, index=False)

        import json
        meta = {
            "signal_mode": getattr(self, "_rec_signal_mode", self.signal_mode),
            "car_enabled": bool(self.car_enabled),
            "bandpass_low_hz": float(self.bandpass_low_hz),
            "bandpass_high_hz": float(self.bandpass_high_hz),
            "sample_rate_hz": float(FS_HZ),
            "dropped_packets": int(self.dropped_packets - getattr(self, "_rec_dropped_at_start", 0)),
            "params": {k: float(v) for k, v in self._extracellular_params.items()},
        }
        with open(str(path.with_suffix("")) + "_meta.json", "w", encoding="utf-8") as handle:
            json.dump(meta, handle, indent=2)

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
                f"color: rgb{tuple(Settings.DarkSolarized[3])};\n"
                f"background-color: rgb{tuple(Settings.DarkSolarized[11])};\n"
                f"border: 1px solid rgb{tuple(Settings.DarkSolarized[14])};\n"
                f"border-radius: 10px;"
            )
        else:
            self.ui.ExtraCellular_ConnectButton.setText("Connect Tetrode recording to Spikeling")
            self.ui.ExtraCellular_ConnectButton.setStyleSheet(
                f"color: rgb{tuple(Settings.DarkSolarized[14])};\n"
                f"background-color: rgb{tuple(Settings.DarkSolarized[2])};\n"
                f"border: 1px solid rgb{tuple(Settings.DarkSolarized[14])};\n"
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

        self._plots_ready = False

        self._reset_model_state()
        self._filter_sos = None
        self._filter_zi_block = None
        self._projection_matrix_cache = None

        if hasattr(self, "_rx_timer"):
            self._rx_timer.stop()
        self._rx_queue.clear()
