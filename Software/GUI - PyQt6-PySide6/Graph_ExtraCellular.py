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

from PySide6.QtCore import QObject, QTimer
import pyqtgraph as pg
import numpy as np
import pandas as pd
import collections
from decimal import Decimal
from typing import Tuple

from scipy.signal import butter, sosfilt, sosfilt_zi

import Parameters_Settings as Settings
from serial_manager import serial_manager


# =============================================================================
# Constants
# =============================================================================

SAMPLE_INTERVAL = 0.1          # ms per incoming sample (fallback if packet lacks timestamp)
TIME_WINDOW = 2000             # ms total rolling buffer
TIME_WINDOW_DISPLAY = 500      # ms visible in oscilloscope x-range
PEN_WIDTH = 1

N_NEURONS = 3                  # primary + two auxiliaries from Spikeling stream
N_CHANNELS = 4                 # tetrode contacts
FS_HZ = 1000.0 / SAMPLE_INTERVAL
NYQUIST_HZ = 0.5 * FS_HZ

# Channel colors matched to the UI labels
CHANNEL_COLORS = [
    (38, 139, 210),   # Ch1
    (42, 161, 152),   # Ch2
    (133, 153, 0),    # Ch3
    (108, 113, 196),  # Ch4
]


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
        self.last_valid_data = None
        self._t_last_ms = None
        self._t_abs_ms = 0.0  # fallback clock if packets arrive without timestamp

        # ------------------------------------------------------------------
        # Reduced extracellular forward-model parameter cache
        # ------------------------------------------------------------------
        # This dict is refreshed from the GUI sliders / toggles in
        # _connect_parameters() and then read by the model update code.
        self._extracellular_params = {}

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
        self._filter_zi = None

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
        self._plot_decimator = 0
        self._plot_every = 1

        # Kept for structural similarity / compatibility with Graph_Imaging.py
        # and with any other methods that may still inspect these attributes.
        self.secondaryVB = None
        self.calciumVB = None
        self.calciumAxis = None
        self._mainVB = None

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
            "signal_mode": [],
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
        """Activate extracellular pipeline."""
        self._initialize_buffers()
        self._initialize_plot()
        self._connect_parameters()
        self._update_connect_button(True)
        self._reset_model_state()
        self._reset_filter_state()

        self._rx_queue.clear()
        self._rx_timer.start()

        # Keep page-side record gating happy
        if hasattr(self.parent, "extracellular_page"):
            self.parent.extracellular_page.ExtraCellularConnectionFlag = True
        self.parent.ExtraCellularConnectionFlag = True

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

    def _process_rx_queue(self):
        if self.source_mode != "spikeling" or not getattr(self.parent, "ExtraCellularConnectionFlag", False):
            self._rx_queue.clear()
            return

        max_per_tick = 5000
        n = min(len(self._rx_queue), max_per_tick)

        for _ in range(n):
            pkt = self._rx_queue.popleft()
            self._consume_vector(pkt, plot=False)

        if self._plots_ready:
            self._update_plots()

        if len(self._rx_queue) > max_per_tick:
            while len(self._rx_queue) > max_per_tick:
                self._rx_queue.popleft()

    def on_data_received(self, data: list) -> None:
        if self.source_mode != "spikeling":
            return
        if not getattr(self.parent, "ExtraCellularConnectionFlag", False):
            return

        self._rx_queue.append(data)

    def on_emulator_data(self, data: list) -> None:
        """Handle incoming emulator list of packets."""
        if isinstance(data, list) and data and isinstance(data[0], (list, tuple, np.ndarray)):
            self._consume_batch(data)
        else:
            self._consume_vector(data)

    # -------------------------------------------------------------------------
    # Main Extracellular Pipeline
    # -------------------------------------------------------------------------

    def _consume_vector(self, data, plot=True):
        """
        Central extracellular update pipeline.

        Steps:
        1) Validate & parse incoming packet
        2) Update reduced extracellular forward model
        3) Append data to rolling buffers
        4) Handle recording logic
        5) Redraw plots (decimated)
        """
        if not getattr(self.parent, "ExtraCellularConnectionFlag", False):
            return
        if data is None or len(data) < 8:
            return

        parsed = self._parse_packet(data)
        if parsed is None:
            return

        t_ms, vm1, stim, vm2, vm3, trig = parsed

        # dt_ms computed from timestamps if present, otherwise fixed SAMPLE_INTERVAL
        if self._t_last_ms is None:
            dt_ms = SAMPLE_INTERVAL
        else:
            dt_ms = t_ms - self._t_last_ms

        # Sanity clamp dt_ms
        if (not np.isfinite(dt_ms)) or (dt_ms <= 0.0) or (dt_ms > 1000.0):
            dt_ms = SAMPLE_INTERVAL

        self._t_last_ms = t_ms

        # Advance reduced forward model
        self._update_model(vm1, stim, vm2, vm3, trig, t_ms, dt_ms)

        # Append rolling buffers (including time)
        self._append_buffers(t_ms)

        # Recording state machine + capture
        self._handle_recording()
        if self.record_flag:
            self._record_sample(t_ms)

        # Plot decimation
        if not plot or not self._plots_ready:
            return

        self._plot_decimator += 1
        if self._plot_decimator >= self._plot_every:
            self._plot_decimator = 0
            self._update_plots()

    def _consume_batch(self, batch):
        """Consume many packets (emulator) and plot once at end."""
        if not getattr(self.parent, "ExtraCellularConnectionFlag", False):
            return

        for pkt in batch:
            self._consume_vector(pkt, plot=False)

        if self._plots_ready:
            self._update_plots()

    # -------------------------------------------------------------------------
    # Packet Parsing
    # -------------------------------------------------------------------------

    def _parse_packet(self, data: list):
        """
        Parse packets in the two supported formats.

        Returns:
            (t_ms, vm1, stim, vm2, vm3, trig)
        """
        try:
            vals = [float(x) for x in data]
        except Exception:
            return None

        if len(vals) >= 9:
            # [t, Vm0, Stim, Itot, Vm1, ISyn1, Vm2, ISyn2, Trigger]
            t = vals[0]
            vm1 = vals[1]
            stim = vals[2]
            vm2 = vals[4]
            vm3 = vals[6]
            trig = vals[8]
            return (t, vm1, stim, vm2, vm3, trig)

        if len(vals) >= 8:
            # no timestamp -> sequential samples at SAMPLE_INTERVAL
            if not hasattr(self, "_t_fallback_ms"):
                self._t_fallback_ms = 0.0
            self._t_fallback_ms += SAMPLE_INTERVAL
            t = self._t_fallback_ms

            vm1 = vals[0]
            stim = vals[1]
            vm2 = vals[3]
            vm3 = vals[5]
            trig = vals[7]
            return (t, vm1, stim, vm2, vm3, trig)

        return None

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
            for k in range(N_CHANNELS):
                self.Extra_buffers[k].clear()
                self.Extra_buffers[k].extend([0.0] * self._bufsize)

        if hasattr(self, "Threshold_buffer"):
            self.Threshold_buffer.clear()
            self.Threshold_buffer.extend([float(self.DetectionThreshold_uV)] * self._bufsize)

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

    def _get_source_positions(self, p: dict) -> np.ndarray:
        """
        Compute hidden source coordinates for the 3 incoming neurons.

        User-facing controls:
        - Electrode distance (µm)
        - Orientation (deg)

        Implementation choice:
        - The main source is placed at the user-defined polar coordinate.
        - The 2 auxiliary sources are placed at fixed offsets relative to the main source.
        - The whole source cluster is rotated with the same orientation angle so the
          UI still has a clear geometrical meaning.
        """
        R = float(p.get("electrode_distance_um", 50.0))
        theta_deg = float(p.get("orientation_deg", 0.0))
        theta = np.deg2rad(theta_deg)

        base = np.array([R * np.cos(theta), R * np.sin(theta)], dtype=float)

        c = np.cos(theta)
        s = np.sin(theta)
        rot = np.array([[c, -s], [s, c]], dtype=float)

        offsets = (rot @ self._source_cluster_offsets_um.T).T
        positions = base[None, :] + offsets
        return positions

    def _compute_projection_matrix(self, p: dict) -> np.ndarray:
        """
        Compute source -> channel geometric gains.

        Reduced forward model:
            a_jk = gain_j * (r_ref / (r_jk + eps))^gamma

        where:
        - j = source neuron index
        - k = tetrode channel index
        - gamma is the user-controlled spatial falloff

        This preserves both:
        - absolute amplitude changes with distance
        - relative amplitude differences across channels
        """
        contacts = self._get_contact_positions()                  # (4, 2)
        sources = self._get_source_positions(p)                   # (3, 2)
        gamma = float(p.get("spatial_falloff", 1.2))
        gamma = max(0.1, gamma)

        # distances r_jk : shape (3, 4)
        diff = sources[:, None, :] - contacts[None, :, :]
        r = np.linalg.norm(diff, axis=2)
        r = np.maximum(r, float(self._distance_floor_um))

        g = (float(self._reference_distance_um) / r) ** gamma
        g *= self._source_gain[:, None]

        # Clip for numerical sanity when the source is very close to a contact.
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
        zi = sosfilt_zi(self._filter_sos)
        self._filter_zi = [zi.copy() for _ in range(N_CHANNELS)]
        self.bandpass_low_hz = fl
        self.bandpass_high_hz = fh

    def _reset_filter_state(self) -> None:
        """Reset the streaming filter with the current UI preset."""
        fl, fh = self._bandpass_limits_from_ui()
        self._design_bandpass(fl, fh)

    def _apply_bandpass(self, raw_channels_uV: np.ndarray) -> np.ndarray:
        """
        Sample-by-sample bandpass filtering.
        Each tetrode channel keeps its own SOS filter state.
        """
        if self._filter_sos is None or self._filter_zi is None:
            return np.asarray(raw_channels_uV, dtype=float)

        y = np.zeros(N_CHANNELS, dtype=float)
        for k in range(N_CHANNELS):
            out, self._filter_zi[k] = sosfilt(
                self._filter_sos,
                [float(raw_channels_uV[k])],
                zi=self._filter_zi[k]
            )
            y[k] = float(out[-1])
        return y

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

        # 4.5 sigma with a floor so the overlay remains meaningful at low-noise settings.
        self.DetectionThreshold_uV = -max(15.0, 4.5 * float(sigma_eff))

    def _update_detection_overlays(self, t_ms: float, channels_uV: np.ndarray) -> None:
        """
        Detect threshold-crossing markers on filtered extracellular traces.

        - Per-channel markers are used for the "Spikes" overlay.
        - Merged event times are used for the "Events" overlay.
        """
        thr = float(self.DetectionThreshold_uV)
        any_event = False
        self.ChannelSpikeData[:] = 0

        for k in range(N_CHANNELS):
            y_prev = float(self._prev_channel_sample[k])
            y_now = float(channels_uV[k])

            crossed_down = (y_prev > thr) and (y_now <= thr)
            refractory_ok = (t_ms - self._t_last_detect_ms[k]) >= self.DetectRefractory_ms

            if crossed_down and refractory_ok:
                self._t_last_detect_ms[k] = float(t_ms)
                self.ChannelSpikeData[k] = 1
                any_event = True
                self._channel_spike_marks[k].append((float(t_ms), y_now))

            self._prev_channel_sample[k] = y_now

        # Merge simultaneous channel detections into one event marker
        self.EventData = 0
        if any_event and (t_ms - self._last_event_ms) >= 0.4:
            self._last_event_ms = float(t_ms)
            self.EventData = 1
            self._event_marks.append(float(t_ms))

        # Drop old overlay marks outside the rolling time window
        t_min = float(t_ms) - float(TIME_WINDOW)
        for k in range(N_CHANNELS):
            dq = self._channel_spike_marks[k]
            while dq and dq[0][0] < t_min:
                dq.popleft()
        while self._event_marks and self._event_marks[0] < t_min:
            self._event_marks.popleft()

    def _update_model(self, vm1, stim, vm2, vm3, trigger, t_ms, dt_ms):
        """
        Update reduced extracellular forward model.

        Pipeline per sample:
          1) Detect spike times from the 3 incoming intracellular Vm traces
          2) Build per-source extracellular waveform surrogate
             - Template mode: canonical EAP template per detected spike
             - dV/dT mode: gated derivative-like waveform from intracellular Vm
          3) Project sources onto 4 tetrode contacts using geometry / distance falloff
          4) Add independent baseline noise + shared noise + 50 Hz hum
          5) Apply CAR if enabled
          6) Apply selected bandpass preset
          7) Update overlay detections (threshold / spikes / events)
        """
        self.VmData[:] = (vm1, vm2, vm3)
        self.StimData = stim
        self.TriggerData = trigger

        if not self._extracellular_params:
            return
        p = self._extracellular_params

        # 1) Ground-truth spike detection from intracellular Vm traces
        for i in range(N_NEURONS):
            vm_prev = self.Vm_buffers[i][-1] if hasattr(self, "Vm_buffers") and len(self.Vm_buffers[i]) else self.VmData[i]
            self.GroundTruthSpikeData[i] = self._detect_spike(
                vm_now=float(self.VmData[i]),
                vm_prev=float(vm_prev),
                t_ms=float(t_ms),
                neuron_index=i,
            )

        # 2) Per-source extracellular waveform surrogate
        for i in range(N_NEURONS):
            if self.signal_mode == "dvdt":
                self.SourceWaveData[i] = self._dvdt_source_step(
                    neuron_index=i,
                    vm_now=float(self.VmData[i]),
                    spike=int(self.GroundTruthSpikeData[i]),
                    dt_ms=float(dt_ms),
                )
            else:
                self.SourceWaveData[i] = self._template_source_step(
                    neuron_index=i,
                    spike=int(self.GroundTruthSpikeData[i]),
                )

        # 3) Geometry projection: sources -> 4 tetrode channels
        A = self._compute_projection_matrix(p)      # (3, 4)
        clean_channels = A.T @ self.SourceWaveData  # (4,)

        # 4) Noise / contamination block
        sigma_base = float(p.get("baseline_noise_uV", 5.0))
        sigma_shared = float(p.get("shared_noise_uV", 5.0))
        a_hum = float(p.get("hum_noise_uV", 0.0))

        baseline_noise = sigma_base * self._rng.normal(size=N_CHANNELS)
        shared_noise = sigma_shared * float(self._rng.normal())
        hum = a_hum * np.sin(2.0 * np.pi * 50.0 * (float(t_ms) / 1000.0) + float(self._hum_phase_rad))

        raw_channels = clean_channels + baseline_noise + shared_noise + hum

        # 5) Optional CAR
        if self.car_enabled:
            raw_channels = raw_channels - np.mean(raw_channels)

        # 6) Bandpass display / recording filter
        filtered_channels = self._apply_bandpass(raw_channels)
        self.ExtraData[:] = filtered_channels

        # 7) Overlays are computed on the filtered traces
        self._update_detection_threshold(p)
        self._update_detection_overlays(float(t_ms), filtered_channels)

    # -------------------------------------------------------------------------
    # Buffers
    # -------------------------------------------------------------------------

    def _initialize_buffers(self):
        """Create rolling buffers for all plotted variables."""
        self._bufsize = int(TIME_WINDOW / SAMPLE_INTERVAL)

        self.Time_buffer = collections.deque([0.0] * self._bufsize, self._bufsize)
        self.ExtraCellularx = (np.arange(self._bufsize) - (self._bufsize - 1)) * SAMPLE_INTERVAL

        self.Stim_buffer = collections.deque([0.0] * self._bufsize, self._bufsize)
        self.Trigger_buffer = collections.deque([0.0] * self._bufsize, self._bufsize)
        self.Threshold_buffer = collections.deque([self.DetectionThreshold_uV] * self._bufsize, self._bufsize)

        self.Vm_buffers = [
            collections.deque([0.0] * self._bufsize, self._bufsize)
            for _ in range(N_NEURONS)
        ]
        self.Extra_buffers = [
            collections.deque([0.0] * self._bufsize, self._bufsize)
            for _ in range(N_CHANNELS)
        ]

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
        from PySide6.QtWidgets import QVBoxLayout
        import pyqtgraph as pg

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

    def update_views(self):
        """
        Kept for structural symmetry with Graph_Imaging.py.
        No extra ViewBoxes are currently used on the extracellular scope page.
        """
        return

    def _update_plots(self):
        ui = self.ui
        t_arr = np.asarray(self.Time_buffer, dtype=float)
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

            y = np.asarray(self.Extra_buffers[k], dtype=float)
            curve.setData(x, y)

            # Threshold line for this channel
            thr_line.setVisible(show_thr)
            thr_line.setPos(float(self.DetectionThreshold_uV))

            # Channel-specific spike markers
            spike_scatter.setVisible(show_spikes)
            if show_spikes:
                spots = [{
                    "pos": (float(t_mark - t_arr[-1]), float(y_mark)),
                    "brush": pg.mkBrush(CHANNEL_COLORS[k]),
                    "pen": pg.mkPen(CHANNEL_COLORS[k]),
                    "symbol": "o",
                    "size": 6,
                } for t_mark, y_mark in self._channel_spike_marks[k]]
                spike_scatter.setData(spots)
            else:
                spike_scatter.setData([])

            # Event markers copied to each visible subplot
            event_scatter.setVisible(show_events)
            if show_events:
                if y.size:
                    y_top = float(np.max(y))
                    y_bot = float(np.min(y))
                    span = max(10.0, y_top - y_bot)
                    y_event = y_top + 0.08 * span
                else:
                    y_event = 20.0

                spots = [{
                    "pos": (float(t_evt - t_arr[-1]), float(y_event)),
                    "brush": pg.mkBrush(Settings.DarkSolarized[10]),
                    "pen": pg.mkPen(Settings.DarkSolarized[10]),
                    "symbol": "t",
                    "size": 8,
                } for t_evt in self._event_marks]
                event_scatter.setData(spots)
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

            if not hasattr(self, "_rec") or not isinstance(self._rec, dict):
                self._rec = {}

            for k in [
                "t_ms", "stim", "trig",
                "vm1", "vm2", "vm3",
                "gt_spike1", "gt_spike2", "gt_spike3",
                "ch1_uV", "ch2_uV", "ch3_uV", "ch4_uV",
                "threshold_uV", "event", "signal_mode",
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

    def _record_sample(self, t_ms: float) -> None:
        """Append the latest sample to recording buffers."""
        self._rec["t_ms"].append(float(t_ms))
        self._rec["stim"].append(float(self.StimData))
        self._rec["trig"].append(float(self.TriggerData))

        self._rec["vm1"].append(float(self.VmData[0]))
        self._rec["vm2"].append(float(self.VmData[1]))
        self._rec["vm3"].append(float(self.VmData[2]))

        self._rec["gt_spike1"].append(int(self.GroundTruthSpikeData[0]))
        self._rec["gt_spike2"].append(int(self.GroundTruthSpikeData[1]))
        self._rec["gt_spike3"].append(int(self.GroundTruthSpikeData[2]))

        self._rec["ch1_uV"].append(float(self.ExtraData[0]))
        self._rec["ch2_uV"].append(float(self.ExtraData[1]))
        self._rec["ch3_uV"].append(float(self.ExtraData[2]))
        self._rec["ch4_uV"].append(float(self.ExtraData[3]))

        self._rec["threshold_uV"].append(float(self.DetectionThreshold_uV))
        self._rec["event"].append(int(self.EventData))
        self._rec["signal_mode"].append(str(self.signal_mode))

    def _export_csv(self):
        """Write recorded extracellular data to CSV."""
        if (not hasattr(self, "_rec")) or (len(self._rec.get("t_ms", [])) == 0):
            return

        base = str(self.ui.ExtraCellular_SelectedFolderLabel.text()).strip()
        if not base:
            return

        if base.lower().endswith(".csv"):
            base = base[:-4]

        try:
            from pathlib import Path
            base_path = Path(base)
            if str(base_path.parent) not in ("", "."):
                base_path.parent.mkdir(parents=True, exist_ok=True)
            sample_csv_path = str(base_path.with_suffix(".csv"))
        except Exception:
            sample_csv_path = f"{base}.csv"

        df_samples = pd.DataFrame({
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
            "Signal Mode": self._rec["signal_mode"],
        })
        df_samples.to_csv(sample_csv_path, index=False)

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
            p["electrode_distance_um"] = float(ui.ExtraCellular_Distance_Slider.value())
            p["orientation_deg"] = float(ui.ExtraCellular_Orientation_Slider.value())
            p["spatial_falloff"] = float(ui.ExtraCellular_Spread_Slider.value()) / 10.0

            # Noise / contamination
            p["baseline_noise_uV"] = float(ui.ExtraCellular_BaselineNoise_Slider.value())
            p["shared_noise_uV"] = float(ui.ExtraCellular_SharedNoise_Slider.value())
            p["hum_noise_uV"] = float(ui.ExtraCellular_HumNoise_Slider.value())

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
            ui.ExtraCellular_Distance_Slider,
            ui.ExtraCellular_Orientation_Slider,
            ui.ExtraCellular_Spread_Slider,
            ui.ExtraCellular_BaselineNoise_Slider,
            ui.ExtraCellular_SharedNoise_Slider,
            ui.ExtraCellular_HumNoise_Slider,
            ui.ExtraCellular_Bandpass_comboBox,
            ui.ExtraCellular_SignalMode_toggleButton,
            ui.ExtraCellular_CAR_toggleButton,
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
        self.last_valid_data = None

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
        self._mainVB = None
        self.secondaryVB = None
        self.calciumVB = None
        self.calciumAxis = None

        self._reset_model_state()
        self._filter_sos = None
        self._filter_zi = None

        if hasattr(self, "_rx_timer"):
            self._rx_timer.stop()
        self._rx_queue.clear()
