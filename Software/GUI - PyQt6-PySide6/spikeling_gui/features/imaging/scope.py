"""
Real-time imaging simulation (calcium + fluorescence) for Spikeling.
Vm(t) -> spike events -> calcium transient -> fluorescence indicator -> display (F or ΔF/F0)

Core references
1) Vogelstein et al., 2009, Biophysical Journal
   "Spike Inference from Calcium Imaging Using Sequential Monte Carlo Methods"
   (Linear fluorescence observation + 1st-order calcium decay model)
2) Wei et al., "Spike-to-Fluorescence (S2F)" forward model
   (Rise/decay calcium kernel + optional sigmoid / Hill nonlinearity)
3) Pham et al., kinetic binding formulation
   (Non-equilibrium indicator binding ODE vs equilibrium Hill saturation)

Data format:
Incoming packet (8 or 9 elements):
[Vm0, Stim, Itot, Vm1, ISyn1, Vm2, ISyn2, Trigger]
or
[timestamp, Vm0, Stim, Itot, Vm1, ISyn1, Vm2, ISyn2, Trigger]

Notes on units:
- Time is handled internally in milliseconds, except kinetic ODE uses seconds for dt_s.
- Calcium is handled in µM by default, matching typical Kd values entered by users.
- By enabling kinetic binding, the model converts calcium to µM internally for rate-law convenience,
  because typical kon values are expressed in (µM^-n * s^-1).
"""

from PySide6.QtCore import QObject, QTimer
import pyqtgraph as pg
import numpy as np
import pandas as pd
import collections
import datetime
import json
import math
from pathlib import Path
from shutil import copyfile
from tempfile import TemporaryDirectory
from time import monotonic

from spikeling_gui.appearance.palette import DarkSolarized
from spikeling_gui.appearance.dialogs import themed_message_box
from spikeling_gui.widgets.recording import prepare_recording, style_recording_button
from spikeling_gui.recording_metadata import stream_digest
from spikeling_gui.appearance.theme_manager import theme_manager
from spikeling_gui.features.imaging.controls import (
    GECI_SLIDERS, IMAGING_SLIDERS, MODEL_FRAME_RATE_HZ, SAMPLE_INTERVAL,
    apply_geci_defaults, bind_imaging_sliders,
)
from spikeling_gui.features.imaging.presets import GECI
from spikeling_gui.hardware.serial_manager import serial_manager
from spikeling_gui.plotting.graph_core import RingBuffer, configure_scope
from spikeling_gui.hardware.protocol import parse_spikeling_packet


TIME_WINDOW = 2000
TIME_WINDOW_DISPLAY = 1000
AUTO_RANGE_WINDOW_MS = 300.0
STIM_MIN, STIM_MAX = -100, 100
N_NEURONS = 3
MAX_PACKETS_PER_TICK = 5000

BOARD_PACKET_PERIOD_MS = 2.0
TRANSPORT_PAUSE_MS = 250.0
EMULATOR_GAP_MS = 5 * SAMPLE_INTERVAL
SAMPLE_COLUMNS = [
    "Time (ms)", "Stim", "Trigger", "Vm1 (mV)", "Vm2 (mV)", "Vm3 (mV)",
    "Ca1 (uM)", "Ca2 (uM)", "Ca3 (uM)", "F1 (a.u.)", "F2 (a.u.)", "F3 (a.u.)",
    "FrameIdx", "FrameTime (ms)", "Calcium event 1", "Calcium event 2", "Calcium event 3",
]
FRAME_COLUMNS = [
    "FrameIdx", "FrameTime (ms)", "NearestSampleIdx", "F1 (a.u.)", "F2 (a.u.)", "F3 (a.u.)",
    "SourceSampleTime (ms)", "DF/F0 1 (%)", "DF/F0 2 (%)", "DF/F0 3 (%)",
]
SIDECAR_SUFFIXES = ("_frames.csv", "_meta.json")

class ImagingGraph(QObject):
    """
    Controller class for microscopy-style imaging simulation and plotting.
    """

    # -------------------------------------------------------------------------
    # Initialization & Lifecycle
    # -------------------------------------------------------------------------

    def __init__(self, parent):
        super().__init__(parent)

        self.parent = parent
        self.ui = parent.ui

        # -------------------------
        # Data source control
        # -------------------------
        self.source_mode = "spikeling"   # "spikeling", "emulator", "none"
        self._t_last_ms = None
        self._last_input_ms = None
        self._last_clock_kind = None
        self._last_clamped = None
        self._next_frame_ms = None
        self._last_arrival = None
        self._ready = False
        # Previous-sample Vm, kept explicitly instead of peeking into the
        # display buffer, so spike detection is independent of plotting.
        self._vm_prev = np.zeros(N_NEURONS, dtype=float)
        self._rng = np.random.default_rng()

        # -------------------------
        # Imaging / Model state
        # -------------------------
        self._imaging_params = {}

        # Spike detection parameters
        self.SpikeThreshold = -20.0      # mV; threshold for upward crossing
        self.SpikeRefractory_ms = 3.0    # ms; refractory window after detected spike
        self._t_last_spike_ms = np.full(N_NEURONS, -1e12, dtype=float)  # per neuron last spike time

        # Indicator / preset selection
        self.indicator_name = "Generic"

        # Model selection flags (these may be driven by GUI later)
        # Allowed: "linear", "hill", "sigmoid"
        self.fluorescence_model = "hill"
        # Realism toggle: kinetic binding vs equilibrium Hill
        self.binding_enabled = False

        # Core “indicator state” variable:
        # - In equilibrium Hill/sigmoid: this is a fraction in [0..1] computed from calcium.
        # - In kinetic mode: this is the bound fraction state updated by an ODE.
        self.IndicatorSat = np.zeros(N_NEURONS, dtype=float)

        # Kinetic binding state (only used when binding_enabled=True)
        self._S_tot = 1.0                 # total indicator (arbitrary units)
        self._S_bound = np.zeros(N_NEURONS, dtype=float)  # bound amount (0..S_tot)
        self._bind_n = 2.0                # cooperativity/order
        self._k_on = 1.0                  # µM^-n * s^-1
        self._k_off = 1.0                 # s^-1

        # Wei-style calcium kernel internal states (O(1) implementation)
        # We maintain two decaying traces per neuron:
        #   x_d  ~ exp(-t/τd)
        #   x_dr ~ exp(-t/τdr) where τdr = (τd*τr)/(τd+τr)
        # and compute: Ca = Cb + (x_d - x_dr) + noise
        self._ca_xd = np.zeros(N_NEURONS, dtype=float)
        self._ca_xdr = np.zeros(N_NEURONS, dtype=float)

        # Default “effective kinetics”
        self.Ca_tau_rise_ms = 20.0        # ms (Wei kernel τrise)
        self.Ca_tau_decay_ms = 200.0      # ms (Wei kernel τdecay)
        self.spikerise = 0.010            # µM per spike event
        self.Ca_noise_uM = 0.01           # µM stddev of additive Gaussian noise
        self.Kd_uM = 0.150                 # µM dissociation constant
        self.hill_n = 4.0                 # Hill coefficient
        self.dff_max = 3.0                # max ΔF/F0 at full saturation
        self.Ind_tau_rise_ms = 50.0       # ms
        self.Ind_tau_decay_ms = 300.0     # ms

        # Sigmoid parameters (optional observation model)
        self.sig_k = 10.0                 # steepness in 1/µM (since Ca is in µM)
        self.sig_c_half_uM = 0.15         # half-activation (µM)

        # --- Photobleaching state (Laser > 100% causes bleaching) ---
        self.bleach_B = 1.0  # 1.0 = no bleach, <1 dims fluorescence
        self.bleach_B_min = 0.05  # do not go to zero (keeps display sane)

        # Rates in 1/s (tuned later)
        self.bleach_k = 0.20  # bleaching rate per "overdrive" unit
        self.recover_k = 0.05  # recovery rate per "underdrive" unit

        # PMT excess-noise model (didactic): adds extra background noise when PMT > 1.0
        self.pmt_excess_noise_sigma = 0.02  # a.u. at PMT=2 if gamma=2 (tune)
        self.pmt_excess_noise_gamma = 2.0  # superlinear growth vs excess gain

        # Continuous “latest sample” values (held at last update)
        self.CalciumData = np.full(N_NEURONS, 0.1, dtype=float)  # µM
        self.FluoData = np.zeros(N_NEURONS, dtype=float)         # a.u.
        self.VmData = np.zeros(N_NEURONS, dtype=float)           # mV

        self.StimData = 0.0
        self.TriggerData = 0.0

        # Plot state
        self._plots_ready = False
        self.secondaryVB = None
        self.calciumVB = None
        self.calciumAxis = None
        self._mainVB = None               # main PlotItem viewbox reference

        # Display choice
        self.use_dff = False              # ΔF/F0 plotting toggle
        self.F0 = np.ones(N_NEURONS, dtype=float)  # baseline fluorescence per neuron (for ΔF/F0 plotting)

        self._rx_queue = collections.deque(maxlen=20000)  # ~2 s at 10kHz
        self._rx_timer = QTimer(self)
        self._rx_timer.setInterval(16)  # ~60 Hz
        self._rx_timer.timeout.connect(self._process_rx_queue)

        # Recording
        self.record_flag = False
        self._save_pending = False
        self._recording_path = None

        serial_manager.data_received.connect(self.on_data_received)
        serial_manager.connection_changed.connect(self.on_hardware_connection_changed)

    # -------------------------------------------------------------------------
    # Source Selection
    # -------------------------------------------------------------------------

    def select_source(self, mode, enabled):
        if self.parent.ImagingConnectionFlag:
            if enabled and mode == self.source_mode:
                return
            self.disconnect(self.tr("Source changed") if enabled else self.tr("Disconnected"))
        self.source_mode = mode
        if enabled:
            self.connect()

    def connect(self):
        """Start a display session using the current controls."""
        self.ui.Imaging_ConnectButton.setChecked(True)
        self._initialize_buffers()
        self._initialize_plot()
        self._refresh_imaging_params()
        self._reset_model_state()
        self.parent.ImagingConnectionFlag = True
        self._ready = False
        self._set_source_status(self.tr("Waiting for source"))
        self._update_record_button()
        self._rx_timer.start()

    def disconnect(self, reason=None):
        """Stop and save the capture before dropping the session buffers."""
        self.parent.ImagingConnectionFlag = False
        self._ready = False
        self._rx_timer.stop()
        self._drain_hardware()
        self.cleanup()
        self.ui.Imaging_ConnectButton.setChecked(False)
        self._set_source_status(self.tr("Connect imaging to source"), reason)
        self.stop_recording(reason or self.tr("Disconnected"))
        self._update_record_button()

    def on_hardware_connection_changed(self, connected):
        if self.source_mode == "spikeling" and self.parent.ImagingConnectionFlag and not connected:
            self.disconnect(self.tr("Hardware source disconnected"))

    def on_emulator_stopped(self):
        if self.source_mode == "emulator" and self.parent.ImagingConnectionFlag:
            self.disconnect(self.tr("Emulator stopped"))

    def on_data_received(self, data):
        if self.source_mode != "spikeling" or not self.parent.ImagingConnectionFlag:
            return

        now = monotonic()
        gap_ms = 0.0 if self._last_arrival is None else (now - self._last_arrival) * 1000.0
        self._last_arrival = now
        transport_pause_ms = gap_ms if gap_ms > TRANSPORT_PAUSE_MS else 0.0
        discarded = 0
        if len(self._rx_queue) == self._rx_queue.maxlen:
            discarded = sum(1 + lost for _, _, lost, _ in self._rx_queue)
            self._rx_queue.clear()
        neuron_scope = getattr(self.parent, "spikeling_graph", None)
        clamped = bool(getattr(neuron_scope, "voltage_clamp_display", False))
        self._rx_queue.append((data, clamped, discarded, transport_pause_ms))

    def _process_rx_queue(self):
        if self.source_mode == "spikeling" and self.parent.ImagingConnectionFlag:
            if len(self._rx_queue) > 2 * MAX_PACKETS_PER_TICK:
                discard_count = len(self._rx_queue) - MAX_PACKETS_PER_TICK
                discarded = 0
                for _ in range(discard_count):
                    _, _, lost, _ = self._rx_queue.popleft()
                    discarded += 1 + lost
                packet, clamped, lost, pause = self._rx_queue.popleft()
                self._rx_queue.appendleft((packet, clamped, lost + discarded, pause))
            self._drain_hardware(MAX_PACKETS_PER_TICK)

    def _drain_hardware(self, limit=None):
        count = len(self._rx_queue) if limit is None else min(len(self._rx_queue), limit)
        for _ in range(count):
            packet, clamped, discarded, pause = self._rx_queue.popleft()
            self._consume_vector(packet, soma_clamped=clamped, discarded_packets=discarded,
                                 transport_pause_ms=pause)
        if count and self._plots_ready and self.parent.ImagingConnectionFlag:
            self._update_plots()

    def on_emulator_data(self, data, *, soma_clamped=False, events=None):
        if self.source_mode != "emulator" or not self.parent.ImagingConnectionFlag:
            return
        if not len(data):
            return
        packets = data if isinstance(data[0], (list, tuple, np.ndarray)) else [data]
        source_events = [None] * len(packets) if events is None else events
        for packet, spikes in zip(packets, source_events):
            self._consume_vector(packet, soma_clamped=soma_clamped, events=spikes)
        if self._plots_ready:
            self._update_plots()

    def _consume_vector(self, data, *, soma_clamped=False, events=None,
                        discarded_packets=0, transport_pause_ms=0.0):
        sample = parse_spikeling_packet(data)
        if sample is None or not all(math.isfinite(value) for value in sample[1:]):
            return
        hardware = self.source_mode == "spikeling"
        source_dt = SAMPLE_INTERVAL
        source_time = None if hardware else sample.t_ms
        if source_time is not None and not math.isfinite(source_time):
            return
        clock_kind = "timestamp" if source_time is not None else "nominal"
        interval = source_dt
        interruption = None
        if self._t_last_ms is not None:
            if discarded_packets:
                interval = (discarded_packets + 1) * source_dt
                interruption = "Hardware receive queue overrun"
            elif clock_kind != self._last_clock_kind:
                interruption = "Source clock changed"
            elif source_time is not None:
                delta = source_time - self._last_input_ms
                if delta <= 0:
                    interruption = "Source clock reset"
                else:
                    interval = delta
                    if delta > EMULATOR_GAP_MS:
                        interruption = "Missing samples"
        first = self._t_last_ms is None
        t_ms = 0.0 if first else self._t_last_ms + interval
        self._t_last_ms = t_ms
        self._last_clock_kind = clock_kind
        self._last_input_ms = source_time

        clamp_changed = self._last_clamped is not None and soma_clamped != self._last_clamped
        self._last_clamped = soma_clamped
        if clamp_changed and self.record_flag:
            self.stop_recording(self.tr("Clamp mode changed"), drain=False)

        rate = self._imaging_params["frame_rate"]
        follows_model = rate == MODEL_FRAME_RATE_HZ
        period_ms = 1000.0 / rate
        if not follows_model and (first or self._next_frame_ms is None):
            self._next_frame_ms = t_ms + period_ms
        if transport_pause_ms and self.record_flag:
            # USB delivery pauses need not indicate missing model samples.
            self._rec_meta["transport_pauses"].append(
                {"t_ms": t_ms, "host_pause_ms": transport_pause_ms}
            )
        if interruption:
            self._append_fluorescence_frame(t_ms, (np.nan,) * N_NEURONS, (np.nan,) * N_NEURONS)
            if not follows_model and not first and self._next_frame_ms <= t_ms:
                skipped = math.floor((t_ms - self._next_frame_ms) / period_ms) + 1
                self._next_frame_ms += skipped * period_ms
            self._reset_model_state()
            self._set_source_status(self.tr("Receiving · timing interrupted"), self.tr(interruption))
            if self.record_flag:
                self._rec_meta["timing_interruptions"].append(
                    {"t_ms": t_ms, "interval_ms": interval, "reason": interruption}
                )

        if not self._ready and self.parent.ImagingConnectionFlag:
            self._ready = True
            if not interruption:
                self._set_source_status(self.tr("Receiving"))
            self._update_record_button()

        frame_time = None
        if follows_model:
            frame_time = t_ms
        elif not interruption and t_ms + 1e-8 >= self._next_frame_ms:
            frame_time = self._next_frame_ms
            self._next_frame_ms += period_ms

        if first or interruption:
            self._vm_prev[:] = (sample.vm0, sample.vm1, sample.vm2)
            if interruption:
                events = (0, 0, 0) if events is not None else None
        elif clamp_changed:
            self._vm_prev[0] = sample.vm0
        spikes = self._update_model(
            sample.vm0, sample.stim, sample.vm1, sample.vm2, sample.trigger,
            t_ms, source_dt if interruption else interval, frame_time,
            soma_clamped=soma_clamped, events=events,
        )
        self._append_buffers(t_ms)
        if frame_time is not None:
            self._append_fluorescence_frame(t_ms, self.FluoData, self._frame_dff)
        if self.record_flag:
            self._record_sample(t_ms, frame_time, spikes, events is not None)

    def _reset_model_state(self):
        self._ca_xd.fill(0.0)
        self._ca_xdr.fill(0.0)
        self._t_last_spike_ms.fill(-1e12)
        self.bleach_B = 1.0
        baseline = self._imaging_params["CalciumBaseline"]
        self.CalciumData.fill(baseline)
        saturation = self._indicator_equilibrium_saturation(baseline, self._imaging_params)
        self.IndicatorSat.fill(saturation)
        self._S_bound.fill(saturation * self._S_tot)
        self._update_F0_from_baseline()
        self.FluoData[:] = self.F0
        self._has_frame = False
        self._frame_dff = np.full(N_NEURONS, np.nan)

    # -------------------------------------------------------------------------
    # Imaging Model
    # -------------------------------------------------------------------------

    def autorange_imaging_y(self) -> None:
        """Fit each optical axis to its enabled traces in the latest model time."""
        if not self._plots_ready or self._t_last_ms is None:
            return

        ui = self.ui
        fluo_checks = (
            ui.Imaging_Fluorescence1_Checkbox,
            ui.Imaging_Fluorescence2_Checkbox,
            ui.Imaging_Fluorescence3_Checkbox,
        )
        calcium_checks = (
            ui.Imaging_Calcium1_Checkbox,
            ui.Imaging_Calcium2_Checkbox,
            ui.Imaging_Calcium3_Checkbox,
        )
        frame_times, fluorescence = self._fluorescence_plot_data()
        sample_times = self.Time_buffer.data - self._t_last_ms
        calcium = (buffer.data for buffer in self.Calcium_buffers)
        self._fit_recent_y_range(self._mainVB, frame_times, fluorescence.T, fluo_checks)
        self._fit_recent_y_range(self.calciumVB, sample_times, calcium, calcium_checks)

    @staticmethod
    def _fit_recent_y_range(view, times, traces, checkboxes):
        # Allow round-off at the 300 ms boundary. Unfilled timestamps are NaN.
        recent = (times >= -AUTO_RANGE_WINDOW_MS - 1e-6) & (times <= 0.0)
        values = []
        for trace, checkbox in zip(traces, checkboxes):
            if checkbox.isChecked():
                ys = trace[recent]
                values.extend(ys[np.isfinite(ys)])
        if not values:
            return

        low, high = min(values), max(values)
        span = high - low
        pad = 0.05 * span if span > 1e-9 else max(0.05 * abs(low), 1e-3)
        view.enableAutoRange(axis=pg.ViewBox.YAxis, enable=False)
        view.setYRange(low - pad, high + pad, padding=0.0)

    def initialise_controls(self):
        self._slider_bindings = bind_imaging_sliders(self.ui)
        self.apply_indicator_preset("Generic")
        for binding in self._slider_bindings.values():
            binding.valueChanged.connect(self._refresh_imaging_params)
        self.SelectGECI()
        self.ui.Imaging_AutoRange_pushButton.clicked.connect(self.autorange_imaging_y)
        self._update_record_button()

    def apply_indicator_preset(self, name):
        if self.record_flag:
            return
        self.indicator_name = name if name in GECI else "Generic"
        apply_geci_defaults(self._slider_bindings, GECI[self.indicator_name])
        self._refresh_imaging_params()

    def _show_active_indicator(self):
        preset = GECI[self.indicator_name]
        modified = any(
            self._slider_bindings[name].value != round(spec.slider_position(preset[spec.preset_key]))
            for name, spec in GECI_SLIDERS.items()
        )
        status = self.tr("Active: %1 (modified)") if modified else self.tr("Active: %1")
        self.ui.Imaging_GECI_Active_label.setText(status.replace("%1", self.indicator_name))

    def _on_geci_apply_clicked(self, _checked=False):
        self.apply_indicator_preset(self.ui.Imaging_GECI_comboBox.currentText())

    def SelectGECI(self):
        """Preview the highlighted preset without changing the active state."""
        preset = GECI.get(self.ui.Imaging_GECI_comboBox.currentText(), GECI["Generic"])
        for name, value in (
            ("Kd", f"{preset['Kd_uM']:.3f}"),
            ("Affinity", f"{preset['hill_n']:.2f}"),
            ("DFF", f"{preset['dff_max']:.1f}"),
            ("Rise", f"{preset['Ind_tau_rise_ms']:.0f}"),
            ("Decay", f"{preset['Ind_tau_decay_ms']:.0f}"),
        ):
            getattr(self.ui, f"Imaging_GECI_Readings{name}_Value").setText(value)

    def _update_photobleach(self, dt_ms: float, p: dict) -> None:
        dt_s = max(0.0, float(dt_ms)) / 1000.0
        if dt_s <= 0:
            return

        L = float(p.get("Laser", 1.0))

        k_bleach = float(p.get("Bleach_k", getattr(self, "bleach_k", 0.20)))
        k_recover = float(p.get("Recover_k", getattr(self, "recover_k", 0.05)))

        over = max(0.0, L - 1.0)
        under = max(0.0, 1.0 - L)

        # Bleach only when Laser > 100%
        if over > 0.0 and k_bleach > 0.0:
            self.bleach_B *= float(np.exp(-k_bleach * over * dt_s))

        # Recover only when Laser < 100%
        if under > 0.0 and k_recover > 0.0:
            self.bleach_B += (1.0 - self.bleach_B) * float(1.0 - np.exp(-k_recover * under * dt_s))

        # Clamp
        self.bleach_B = float(np.clip(self.bleach_B, self.bleach_B_min, 1.0))


    def _update_model(self, vm1, stim, vm2, vm3, trigger, t_ms, dt_ms, frame_time,
                      *, soma_clamped=False, events=None):
        """Advance the model and return the three events that drove calcium."""
        self.VmData[:] = (vm1, vm2, vm3)
        self.StimData = stim
        self.TriggerData = trigger
        p = self._imaging_params
        self._update_photobleach(dt_ms, p)

        spikes = []
        for i, voltage in enumerate(self.VmData):
            if i == 0 and soma_clamped:
                spike = 0
            elif events is not None:
                spike = int(bool(events[i]))
            else:
                spike = self._detect_spike(voltage, self._vm_prev[i], t_ms, i)
            spikes.append(spike)
            self._vm_prev[i] = voltage
            self.CalciumData[i] = self._update_calcium(i, spike, p, dt_ms)
            self.IndicatorSat[i] = self._update_indicator_sat(i, self.CalciumData[i], p, dt_ms)
            if frame_time is not None:
                self.FluoData[i] = self._sat_to_fluorescence(
                    i, self.CalciumData[i], self.IndicatorSat[i], p
                )

        if frame_time is not None:
            self._has_frame = True
            self._frame_dff = self._normalised_fluorescence()
        return spikes

    def _detect_spike(self, vm_now: float, vm_prev: float, t_ms: float, neuron_index: int) -> int:
        """
        Threshold-crossing spike detection with refractory.

        Rule:
          spike = 1 if (vm_prev < Vth and vm_now >= Vth) and (t_ms - t_last_spike_ms >= refractory_ms)

        This is the “spike times from Vm threshold crossings” requirement.
        """
        crossed_up = (vm_prev < self.SpikeThreshold) and (vm_now >= self.SpikeThreshold)
        if not crossed_up:
            return 0

        # Refractory check (prevents double detection within the same spike waveform)
        if (t_ms - self._t_last_spike_ms[neuron_index]) < self.SpikeRefractory_ms:
            return 0

        self._t_last_spike_ms[neuron_index] = float(t_ms)
        return 1

    def _update_calcium(self, neuron_index: int, spike: int, p: dict, dt_ms: float) -> float:
        """
        Wei-style rise/decay calcium kernel (O(1) per update).

        Target continuous-time shape (Wei / S2F forward model concept):
            c(t) = Σ exp(-(t-tk)/τd) * (1 - exp(-(t-tk)/τr)) + n_i(t)

        Efficient identity:
            exp(-Δ/τd) * (1 - exp(-Δ/τr))
            = exp(-Δ/τd) - exp(-Δ*(1/τd + 1/τr))
            = exp(-Δ/τd) - exp(-Δ/τdr),
          where τdr = (τd*τr)/(τd+τr)

        Discrete implementation (per neuron):
            x_d  <- x_d  * exp(-dt/τd)  + A * spike
            x_dr <- x_dr * exp(-dt/τdr) + A * spike
            Ca   <- Cb + (x_d - x_dr) + noise

        Notes:
        - Units: Ca, Cb, A in µM; τ in ms; dt in ms.
        - noise is optional internal Gaussian; we scale by sqrt(dt_s) to keep dt-invariant magnitude.

        Source tag: Wei-style rise/decay kernel (S2F forward model family).
        """
        dt_ms = float(dt_ms)
        if (not np.isfinite(dt_ms)) or (dt_ms <= 0.0):
            dt_ms = SAMPLE_INTERVAL

        # Read effective kernel parameters (ms)
        tau_r = float(p.get("Ca_tau_rise_ms", self.Ca_tau_rise_ms))
        tau_d = float(p.get("Ca_tau_decay_ms", self.Ca_tau_decay_ms))

        # Clamp to avoid division by zero
        tau_r = max(1e-6, tau_r)
        tau_d = max(1e-6, tau_d)

        # τdr = (τd*τr)/(τd+τr)
        tau_dr = (tau_d * tau_r) / (tau_d + tau_r)

        # Exponential decay factors
        exp_d = np.exp(-dt_ms / tau_d)
        exp_dr = np.exp(-dt_ms / tau_dr)

        spike_amplitude_uM = float(p.get("SpikeRise", 0.1))
        baseline_uM = float(p.get("CalciumBaseline", 0.1))

        i = neuron_index
        self._ca_xd[i] = self._ca_xd[i] * exp_d + spike_amplitude_uM * float(spike)
        self._ca_xdr[i] = self._ca_xdr[i] * exp_dr + spike_amplitude_uM * float(spike)

        C = baseline_uM + (self._ca_xd[i] - self._ca_xdr[i])

        noise_uM = float(p.get("NoiseScale", 0.0))
        if noise_uM > 0.0:
            C += noise_uM * np.sqrt(dt_ms / 1000.0) * self._rng.standard_normal()

        return max(float(C), 0.0)


    def _two_tau_filter(self, y_prev: float, y_inf: float, dt_ms: float, tau_rise_ms: float,
                        tau_decay_ms: float) -> float:
        """
        Two-time-constant first-order filter:
            y <- y + (1 - exp(-dt/tau))*(y_inf - y)
        tau depends on direction (rise vs decay).
        """
        tau = float(tau_rise_ms) if (y_inf > y_prev) else float(tau_decay_ms)
        tau = max(1e-6, tau)
        a = 1.0 - np.exp(-float(dt_ms) / tau)
        return float(y_prev + a * (y_inf - y_prev))


    def _update_indicator_sat(self, neuron_index: int, Ca_uM: float, p: dict, dt_ms: float) -> float:
        """
        Update the indicator state (saturation / bound fraction) in [0..1].

        Modes:
          A) Equilibrium Hill saturation (default):
               Sat = Ca^n / (Ca^n + Kd^n)
             (equilibrium approximation; maps calcium to fraction bound)
             Source tag: Hill saturation used in common forward models including Vogelstein-style and S2F options.

          B) Optional sigmoid (logistic) nonlinearity:
               Sat = 1 / (1 + exp(-k*(Ca - c_half)))
             Then ΔF/F is typically Sat scaled by dff_max (see _sat_to_fluorescence).
             Source tag: S2F-style sigmoid observation option.

          C) Realism toggle: kinetic binding ODE (Pham-like):
               dS_b/dt = k_on*(S_tot - S_b)*Ca^n - k_off*S_b
               Sat = S_b / S_tot
             We integrate with Euler per dt (sufficient for small dt in GUI).
             Source tag: Pham-style non-equilibrium binding kinetics.

        Important: dt_ms is milliseconds; kinetic ODE uses seconds.
        """
        i = neuron_index
        Ca = max(0.0, float(Ca_uM))

        # ---- Kinetic binding toggle (non-equilibrium) ----
        if self.binding_enabled:
            # Convert dt to seconds for rate equation
            dt_s = max(1e-9, float(dt_ms) / 1000.0)

            # Pull kinetics parameters (can later be driven by GUI)
            S_tot = float(p.get("Bind_S_tot", self._S_tot))
            n = float(p.get("Bind_n", self._bind_n))
            k_on = float(p.get("Bind_k_on", self._k_on))
            k_off = float(p.get("Bind_k_off", self._k_off))

            S_tot = max(1e-12, S_tot)
            n = max(1e-12, n)

            # ODE terms:
            # forward = k_on * (S_tot - S_b) * Ca^n
            # backward = k_off * S_b
            forward = k_on * (S_tot - self._S_bound[i]) * (Ca ** n)
            backward = k_off * self._S_bound[i]

            # Euler update
            self._S_bound[i] += dt_s * (forward - backward)

            # Clamp to physical range
            self._S_bound[i] = min(max(self._S_bound[i], 0.0), S_tot)

            # Return bound fraction
            return float(self._S_bound[i] / S_tot)

        # ---- Equilibrium mapping (Hill or sigmoid) ----
        model = (self.fluorescence_model or "").lower().strip()

        if model == "sigmoid":
            k = float(p.get("Sig_k", self.sig_k))
            c_half = float(p.get("Sig_c_half_uM", self.sig_c_half_uM))
            Sat_inf = float(1.0 / (1.0 + np.exp(-k * (Ca - c_half))))
        else:
            Sat_inf = float(self._hill_saturation(Ca, p))

        # NEW: apply “effective indicator kinetics” (unless kinetic binding ODE is enabled)
        Sat_prev = float(self.IndicatorSat[i])
        tau_r = float(p.get("Ind_tau_rise_ms", getattr(self, "Ind_tau_rise_ms", 50.0)))
        tau_d = float(p.get("Ind_tau_decay_ms", getattr(self, "Ind_tau_decay_ms", 300.0)))

        Sat = self._two_tau_filter(Sat_prev, Sat_inf, dt_ms=float(dt_ms), tau_rise_ms=tau_r, tau_decay_ms=tau_d)

        # Clamp to [0..1]
        return float(min(max(Sat, 0.0), 1.0))

    def _hill_saturation(self, Ca_uM: float, p: dict) -> float:
        """
        Hill saturation:
            Sat(Ca) = Ca^n / (Ca^n + Kd^n)

        where:
          - Ca is calcium concentration (µM)
          - Kd is dissociation constant (µM)
          - n  is Hill coefficient (dimensionless)

        This is the equilibrium-binding approximation commonly used for GECIs.
        """
        n = float(p.get("HillCoef", self.hill_n))
        Kd = float(p.get("DissociationConstant", self.Kd_uM))
        n = max(1e-12, n)
        Kd = max(1e-12, Kd)

        Ca = max(0.0, float(Ca_uM))
        Ca_n = Ca ** n
        Kd_n = Kd ** n
        denom = Ca_n + Kd_n
        return (Ca_n / denom) if denom > 0 else 0.0

    def _sat_to_fluorescence(self, neuron_index: int, Ca_uM: float, Sat: float, p: dict) -> float:
        """
        Convert the current model state into a fluorescence observation on a camera frame.

        Imaging “gain chain” (kept from your original code for didactic control):
          gain   = Laser * PMT * FluoScale
          offset = FluoOffset

        Observation models:

        1) Linear (Vogelstein-like) observation:
              F = offset + gain * [ alpha*(Ca + beta) ]
           (This preserves the “linear” option; alpha/beta are UI-configurable if desired.)

        2) Saturating observation via Sat (Hill equilibrium, sigmoid, or kinetic bound fraction):
              ΔF/F0 = dff_max * Sat
              F     = offset + gain * (1 + ΔF/F0)

        Noise:
          - sigma_floor: additive Gaussian floor (FluoNoiseSigma)
          - sigma_shot:  shot noise approx proportional to sqrt(F_mean) (PhotoShotNoise)

        The final sample is:
            F = F_mean + N(0, sigma_total)

        Source tags:
        - Linear: Vogelstein-style linear observation option.
        - Saturating: Hill/sigmoid family used in forward models and your previous implementation.

        Photobleach:
        - Apply a multiplicative bleaching factor B(t) ONLY to the optical gain term.
        - Offset is not bleached (represents background / electronics).
        """
        # -------------------------
        # Gains
        # -------------------------
        laser = float(p.get("Laser", 1.0))
        pmt = float(p.get("PMT", 1.0))
        fs = float(p.get("FluoScale", 1.0))
        offset = float(p.get("FluoOffset", 0.0))

        gain = laser * pmt * fs

        # Photobleach factor
        B = float(getattr(self, "bleach_B", 1.0))
        gain_eff = gain * B

        model = (self.fluorescence_model or "").lower().strip()

        # -------------------------
        # Mean fluorescence
        # -------------------------
        if model == "linear":
            # F = offset + gain * [ alpha*(Ca + beta) ]
            alpha = float(p.get("Lin_alpha", 1.0))
            beta = float(p.get("Lin_beta", 0.0))
            F_mean = offset + gain_eff * (alpha * (float(Ca_uM) + beta))
            F_mean = max(0.0, F_mean)

        else:
            # ΔF/F0 = dff_max * Sat ; F = offset + gain * (1 + ΔF/F0)
            dff_max = float(p.get("dff_max", self.dff_max))
            dff = dff_max * float(Sat)
            F_mean = offset + gain_eff * (1.0 + dff)
            F_mean = max(0.0, F_mean)


        # -------------------------
        # Noise terms
        # -------------------------
        # Noise model (frame-sampled)
        sigma_floor = float(p.get("FluoNoiseSigma", 0.0))

        # Simple shot noise proxy (kept compatible with your previous slider meaning)
        shot_scale = float(p.get("PhotoShotNoise", 0.0))
        sigma_shot = shot_scale * np.sqrt(max(F_mean, 0.0))

        # NEW: PMT excess background noise (only when PMT > 1.0)
        excess = max(0.0, pmt - 1.0)
        sigma0 = float(p.get("PMT_excess_noise_sigma", getattr(self, "pmt_excess_noise_sigma", 0.02)))
        gamma = float(p.get("PMT_excess_noise_gamma", getattr(self, "pmt_excess_noise_gamma", 2.0)))

        # Additive “background” term that grows superlinearly with excess gain
        sigma_pmt = sigma0 * (excess ** gamma) * gain_eff

        # Combine independent noises
        sigma = np.sqrt(sigma_floor ** 2 + sigma_shot ** 2 + sigma_pmt**2)

        return float(F_mean + sigma * self._rng.standard_normal())

    # -------------------------------------------------------------------------
    # Baselines / ΔF/F0
    # -------------------------------------------------------------------------

    def _indicator_equilibrium_saturation(self, Ca_uM: float, p: dict) -> float:
        """
        Compute baseline saturation under the current NON-kinetic equilibrium mapping
        (used for initialization and baseline reference).

        If kinetic mode is enabled, we still use equilibrium here to initialize the ODE state.
        """
        if (self.fluorescence_model or "").lower().strip() == "sigmoid":
            k = float(p.get("Sig_k", self.sig_k))
            c_half = float(p.get("Sig_c_half_uM", self.sig_c_half_uM))
            Ca = max(0.0, float(Ca_uM))
            return float(1.0 / (1.0 + np.exp(-k * (Ca - c_half))))
        return float(self._hill_saturation(Ca_uM, p))

    def _baseline_fluorescence_from_C(self, Ca_uM: float, p: dict) -> float:
        """
        Compute expected baseline fluorescence (NO noise) at calcium=Ca_uM.

        This is used:
          - at connect() to initialize FluoData cleanly
          - by _update_F0_from_baseline() as reference for ΔF/F0 plotting
        """
        gain = float(p.get("Laser", 1.0)) * float(p.get("PMT", 1.0)) * float(p.get("FluoScale", 1.0))
        offset = float(p.get("FluoOffset", 0.0))
        model = (self.fluorescence_model or "").lower().strip()

        if model == "linear":
            alpha = float(p.get("Lin_alpha", 1.0))
            beta = float(p.get("Lin_beta", 0.0))
            return float(offset + gain * (alpha * (float(Ca_uM) + beta)))

        Sat0 = self._indicator_equilibrium_saturation(Ca_uM, p)
        dff_max = float(p.get("dff_max", self.dff_max))
        dff0 = dff_max * Sat0
        return float(offset + gain * (1.0 + dff0))

    def _update_F0_from_baseline(self) -> None:
        """
        Recompute F0 from the CURRENT baseline calcium and CURRENT gain/offset.
        We do NOT include noise in F0.

        This keeps ΔF/F0 stable and meaningful when the user changes:
          - Laser / PMT / FluoScale / FluoOffset
          - Kd / Hill n / dff_max / observation model

        Notes
        -----
        The photobleaching factor ``bleach_B`` is deliberately excluded, so a
        bleaching trace appears as a genuine downward drift in ΔF/F0 rather
        than being silently normalised away.

        """
        if not self._imaging_params:
            return
        p = self._imaging_params

        Cb = float(p.get("CalciumBaseline", 0.1))
        F0 = self._baseline_fluorescence_from_C(Cb, p)

        self.F0[:] = float(F0)
        self._update_fluorescence_axis()

    def _normalised_fluorescence(self):
        offset = self._imaging_params["FluoOffset"]
        baseline = self.F0 - offset
        return np.divide(
            100.0 * (self.FluoData - self.F0), baseline,
            out=np.full(N_NEURONS, np.nan), where=np.isfinite(baseline) & (baseline > 1e-12),
        )

    def _update_fluorescence_axis(self):
        axis = self.ui.Imaging_Oscilloscope_widget.getPlotItem().getAxis("left")
        if self.use_dff and not np.any(self.F0 - self._imaging_params["FluoOffset"] > 1e-12):
            axis.setLabel(self.tr("ΔF/F₀ unavailable"))
        elif self.use_dff:
            axis.setLabel("ΔF/F₀", units="%")
        else:
            axis.setLabel(self.tr("Fluorescence"), units="a.u.")

    def ActivateDf(self, checked=None) -> None:
        """
        Toggle ΔF/F0 plotting for fluorescence curves.
        Compatible with Qt toggled(bool) signals and direct calls.
        """
        if checked is None:
            s = self.sender()
            if s is not None and hasattr(s, "isChecked"):
                checked = s.isChecked()
            else:
                checked = not getattr(self, "use_dff", False)

        self.use_dff = bool(checked)

        # Update baseline reference at toggle time
        if self.use_dff:
            self._update_F0_from_baseline()

        # Update axis label to reflect mode
        self._update_fluorescence_axis()

        if self._plots_ready:
            self._mainVB.enableAutoRange(axis=pg.ViewBox.YAxis, enable=True)
            self._update_plots()

    # -------------------------------------------------------------------------
    # Buffers
    # -------------------------------------------------------------------------

    def _initialize_buffers(self):
        """Create rolling buffers for all plotted variables."""
        self._bufsize = int(TIME_WINDOW / SAMPLE_INTERVAL)

        self.Time_buffer = RingBuffer(self._bufsize, fill=np.nan)
        self.Imagingx = (np.arange(self._bufsize) - (self._bufsize - 1)) * SAMPLE_INTERVAL

        self.Stim_buffer = RingBuffer(self._bufsize)
        self.Trigger_buffer = RingBuffer(self._bufsize)
        self.Calcium_buffers = [RingBuffer(self._bufsize) for _ in range(N_NEURONS)]
        self.Vm_buffers = [RingBuffer(self._bufsize) for _ in range(N_NEURONS)]
        # At model rate retain the same two-second history as the voltage display.
        # Store time, raw fluorescence and ΔF/F₀ in one aligned ring.
        self._plot_frames = RingBuffer(self._bufsize, n_channels=1 + 2 * N_NEURONS)
        self._plot_frame_count = 0
        self._vm_prev.fill(0.0)

    def _append_buffers(self, t_ms):
        """Append latest model states to rolling buffers."""
        self.Time_buffer.append(float(t_ms))
        self.Stim_buffer.append(float(self.StimData))
        self.Trigger_buffer.append(float(self.TriggerData))

        for i in range(N_NEURONS):
            self.Calcium_buffers[i].append(float(self.CalciumData[i]))
            self.Vm_buffers[i].append(float(self.VmData[i]))

    # -------------------------------------------------------------------------
    # Plotting
    # -------------------------------------------------------------------------

    def _initialize_plot(self):
        """
        Stable multi-axis setup

        Axes:
          - Left  (built-in): Fluorescence or ΔF/F0
          - Right (built-in): Vm + Stim (secondaryVB)
          - Right (extra)   : Calcium (calciumVB)
        """
        pw = self.ui.Imaging_Oscilloscope_widget
        pw.clear()
        pw.setAntialiasing(True)
        pw.showGrid(x=True, y=True)

        pi = pw.getPlotItem()
        configure_scope(pi)

        pi.showAxis("right")

        ax_right = pi.getAxis("right")
        ax_bottom = pi.getAxis("bottom")

        ax_bottom.enableAutoSIPrefix(False)
        clock_label = (self.tr("Model time (nominal)") if self.source_mode == "spikeling"
                       else self.tr("Simulation time"))
        ax_bottom.setLabel(clock_label, units="ms")

        self._update_fluorescence_axis()

        ax_right.setLabel("Stimulus / Vm", units="a.u. / mV")

        # Main ViewBox
        vb = pi.getViewBox()
        self._mainVB = vb
        vb.enableAutoRange(axis=pg.ViewBox.XAxis, enable=False)
        self._set_imaging_time_window()
        vb.enableAutoRange(axis=pg.ViewBox.YAxis, enable=True)
        vb.setMouseEnabled(x=True, y=False)

        # Remove prior viewboxes/axes if reconnecting
        if getattr(self, "secondaryVB", None) is not None:
            try:
                pw.scene().removeItem(self.secondaryVB)
            except Exception:
                pass
            self.secondaryVB = None

        if getattr(self, "calciumVB", None) is not None:
            try:
                pw.scene().removeItem(self.calciumVB)
            except Exception:
                pass
            self.calciumVB = None

        if getattr(self, "calciumAxis", None) is not None:
            try:
                pi.layout.removeItem(self.calciumAxis)
            except Exception:
                pass
            self.calciumAxis = None

        # Secondary VB for Vm + Stim on built-in right axis
        self.secondaryVB = pg.ViewBox()
        self.secondaryVB.setXLink(vb)
        pw.scene().addItem(self.secondaryVB)
        ax_right.linkToView(self.secondaryVB)
        self.secondaryVB.setRange(yRange=[STIM_MIN, STIM_MAX])

        # Extra right axis for Calcium + its VB
        self.calciumAxis = pg.AxisItem("right")
        self.calciumAxis.setLabel("Calcium", units="µM")
        pi.layout.addItem(self.calciumAxis, 2, 3)

        self.calciumVB = pg.ViewBox()
        self.calciumVB.setXLink(vb)
        pw.scene().addItem(self.calciumVB)
        self.calciumAxis.linkToView(self.calciumVB)
        self.calciumVB.enableAutoRange(axis=pg.ViewBox.YAxis, enable=True)

        # Keep geometries aligned
        if getattr(self, "_viewbox_with_callbacks", None) is not vb:
            vb.sigResized.connect(self.update_views)
            vb.sigRangeChanged.connect(self.update_views)
            self._viewbox_with_callbacks = vb
        self.update_views()

        # Curves
        x = self.Imagingx
        trace_width = theme_manager.active_trace_width

        # Fluorescence curves on main VB
        self.Fluocurve1 = pw.plot(x, np.zeros_like(x),
                                 pen=pg.mkPen(DarkSolarized[4], width=trace_width, cosmetic=True))
        self.Fluocurve2 = pw.plot(x, np.zeros_like(x),
                                 pen=pg.mkPen([0, 255, 133], width=trace_width, cosmetic=True))
        self.Fluocurve3 = pw.plot(x, np.zeros_like(x),
                                 pen=pg.mkPen([133, 255, 0], width=trace_width, cosmetic=True))

        # Calcium curves on calciumVB
        self.Calciumcurve1 = pg.PlotCurveItem(x, np.zeros_like(x),
                                              pen=pg.mkPen(DarkSolarized[10], width=trace_width, cosmetic=True))
        self.Calciumcurve2 = pg.PlotCurveItem(x, np.zeros_like(x),
                                              pen=pg.mkPen(DarkSolarized[9], width=trace_width, cosmetic=True))
        self.Calciumcurve3 = pg.PlotCurveItem(x, np.zeros_like(x),
                                              pen=pg.mkPen(DarkSolarized[7], width=trace_width, cosmetic=True))
        self.calciumVB.addItem(self.Calciumcurve1)
        self.calciumVB.addItem(self.Calciumcurve2)
        self.calciumVB.addItem(self.Calciumcurve3)

        # Vm curves on secondaryVB
        self.Vmcurve1 = pg.PlotCurveItem(x, np.zeros_like(x),
                                         pen=pg.mkPen(DarkSolarized[3], width=trace_width, cosmetic=True))
        self.Vmcurve2 = pg.PlotCurveItem(x, np.zeros_like(x),
                                         pen=pg.mkPen(DarkSolarized[6], width=trace_width, cosmetic=True))
        self.Vmcurve3 = pg.PlotCurveItem(x, np.zeros_like(x),
                                         pen=pg.mkPen(DarkSolarized[8], width=trace_width, cosmetic=True))
        self.secondaryVB.addItem(self.Vmcurve1)
        self.secondaryVB.addItem(self.Vmcurve2)
        self.secondaryVB.addItem(self.Vmcurve3)

        # Stim curve on secondaryVB
        self.Stimcurve = pg.PlotCurveItem(x, np.zeros_like(x),
                                          pen=pg.mkPen(DarkSolarized[5], width=trace_width, cosmetic=True))
        self.secondaryVB.addItem(self.Stimcurve)

        self._plots_ready = True

    def _set_imaging_time_window(self):
        if self._mainVB is None:
            return
        period = 1000.0 / self._imaging_params["frame_rate"]
        window = max(TIME_WINDOW_DISPLAY, 3 * period)
        self._mainVB.setLimits(xMin=-max(TIME_WINDOW, window), xMax=0)
        self._mainVB.setXRange(-window, 0, padding=0)

    def _append_fluorescence_frame(self, t_ms, raw, dff):
        self._plot_frames.append((t_ms, *raw, *dff))
        self._plot_frame_count = min(self._plot_frame_count + 1, self._bufsize)

    def _fluorescence_plot_data(self):
        if not self._plot_frame_count:
            return np.empty(0), np.empty((0, N_NEURONS))
        frames = self._plot_frames.data[-self._plot_frame_count:]
        start = 1 + N_NEURONS if self.use_dff else 1
        return frames[:, 0] - self._t_last_ms, frames[:, start:start + N_NEURONS]

    def update_views(self, *_):
        """
        Keep extra ViewBoxes aligned to the main ViewBox geometry.
        This is called on resize/range changes.
        """
        if self._mainVB is None:
            return

        rect = self._mainVB.sceneBoundingRect()

        if self.secondaryVB is not None:
            self.secondaryVB.setGeometry(rect)
            self.secondaryVB.linkedViewChanged(self._mainVB, self.secondaryVB.XAxis)

        if self.calciumVB is not None:
            self.calciumVB.setGeometry(rect)
            self.calciumVB.linkedViewChanged(self._mainVB, self.calciumVB.XAxis)

    def _update_plots(self):
        """
        Update all plot curves based on checkbox visibility.
        Buffers -> numpy arrays -> PyQtGraph curves.
        """
        ui = self.ui
        t_arr = self.Time_buffer.data
        x = t_arr - t_arr[-1]

        # Calcium
        calcium_checks = [ui.Imaging_Calcium1_Checkbox, ui.Imaging_Calcium2_Checkbox, ui.Imaging_Calcium3_Checkbox]
        calcium_curves = [self.Calciumcurve1, self.Calciumcurve2, self.Calciumcurve3]

        for i in range(N_NEURONS):
            visible = calcium_checks[i].isChecked()
            calcium_curves[i].setVisible(visible)
            if visible:
                calcium_curves[i].setData(x, self.Calcium_buffers[i].data)

        # Fluorescence (or ΔF/F0)
        fluo_checks = [ui.Imaging_Fluorescence1_Checkbox, ui.Imaging_Fluorescence2_Checkbox, ui.Imaging_Fluorescence3_Checkbox]
        fluo_curves = [self.Fluocurve1, self.Fluocurve2, self.Fluocurve3]

        frame_x, frame_y = self._fluorescence_plot_data()
        for i, curve in enumerate(fluo_curves):
            visible = fluo_checks[i].isChecked()
            curve.setVisible(visible)
            if visible:
                curve.setData(frame_x, frame_y[:, i], connect="finite")

        # Vm
        vm_checks = [ui.Imaging_Vm1_Checkbox, ui.Imaging_Vm2_Checkbox, ui.Imaging_Vm3_Checkbox]
        vm_curves = [self.Vmcurve1, self.Vmcurve2, self.Vmcurve3]

        for i in range(N_NEURONS):
            visible = vm_checks[i].isChecked()
            vm_curves[i].setVisible(visible)
            if visible:
                vm_curves[i].setData(x, self.Vm_buffers[i].data)

        # Stimulus
        visible = ui.Imaging_Stimulus_Checkbox.isChecked()
        self.Stimcurve.setVisible(visible)
        if visible:
            self.Stimcurve.setData(x, self.Stim_buffer.data)

    # -------------------------------------------------------------------------
    # Recording
    # -------------------------------------------------------------------------

    def on_record_clicked(self):
        if self.record_flag:
            self.stop_recording(self.tr("Stopped"))
            return
        if not self._ready and not self._save_pending:
            self._update_record_button()
            return

        filename = self.ui.Imaging_DataRecording_File_lineEdit.text()
        source_at_click = self.source_mode
        if not self._save_pending or filename != self._recording_filename:
            path = prepare_recording(self.parent, filename, SIDECAR_SUFFIXES)
            if path is None:
                self._update_record_button()
                return
            self._recording_path = path
            self._recording_filename = filename
        if self._save_pending:
            self.stop_recording()
            return

        self._drain_hardware()
        self._samples = []
        self._frames = []
        self._last_recorded_frame_ms = None
        self._rec_meta = {
            "schema_version": 2,
            "recording_start_iso": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
            "source": self.source_mode,
            "clock": "board neuron model time (nominal)" if self.source_mode == "spikeling" else "emulator simulation",
            "neuron_model_step_ms": SAMPLE_INTERVAL,
            "sample_interval_ms_fallback": SAMPLE_INTERVAL,
            "board_packet_period_ms_nominal": (
                BOARD_PACKET_PERIOD_MS if self.source_mode == "spikeling" else None
            ),
            "soma_clamped": self._last_clamped,
            "spike_threshold_mV": self.SpikeThreshold,
            "spike_refractory_ms": self.SpikeRefractory_ms,
            "indicator_name": self.indicator_name,
            "fluorescence_model": self.fluorescence_model,
            "imaging_params": dict(self._imaging_params),
            "normalisation": {"method": "model baseline", "F0_a.u.": self.F0.tolist(),
                              "offset_a.u.": self._imaging_params["FluoOffset"]},
            "event_provenance": [],
            "sample_clock_kinds": [],
            "timing_interruptions": [],
            "transport_pauses": [],
            "columns": {"samples_csv": SAMPLE_COLUMNS, "frames_csv": FRAME_COLUMNS},
        }
        self.record_flag = True
        self.ui.Imaging_DataRecording_Record_label.setText(self.tr("Recording"))
        self.ui.Imaging_DataRecording_Record_label_2.setText(
            f"{self._recording_path.name} · {self.indicator_name} · {self.source_mode}"
        )
        self._update_record_button()

    def _update_record_button(self):
        button = self.ui.Imaging_DataRecording_Record_pushButton
        button.setChecked(self.record_flag)
        button.setEnabled(self._ready or self.record_flag or self._save_pending)
        label = self.tr("Record")
        if self.record_flag:
            label = self.tr("Stop recording")
        elif self._save_pending:
            label = self.tr("Retry save")
        button.setText(label)
        self.ui.Imaging_DataRecording_File_lineEdit.setEnabled(not self.record_flag)
        self.ui.Imaging_DataRecording_Folder_pushButton.setEnabled(not self.record_flag)
        self.ui.Imaging_parameter_stackedWidget.setEnabled(not self.record_flag)
        style_recording_button(button, self.record_flag)

    def stop_recording(self, reason=None, *, drain=True):
        if self.record_flag and drain:
            self._drain_hardware()
        if not self.record_flag and not self._save_pending:
            return True
        if self.record_flag:
            self._rec_meta["stop_reason"] = reason or self.tr("Stopped")
            self._rec_meta["recording_stop_iso"] = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
        self.record_flag = False
        status = self.ui.Imaging_DataRecording_Record_label
        count = len(self._samples)
        if not count:
            status.setText(self.tr("Stopped: no samples received"))
            self._update_record_button()
            return True
        try:
            self._export_csv()
        except (OSError, ValueError) as error:
            self._save_pending = True
            self._update_record_button()
            status.setText(self.tr("Save failed: samples retained"))
            themed_message_box(
                self.parent, self.tr("Imaging recording could not be saved"),
                self.tr("Samples are still in memory. Correct the destination or change the name, then click Retry save.")
                + "\n\n" + str(error),
            ).exec()
            return False
        self._save_pending = False
        self._samples.clear()
        self._frames.clear()
        self.ui.Imaging_DataRecording_Record_label_2.setText(self._recording_path.name)
        status.setText(self.tr("Saved %1 samples").replace("%1", f"{count:,}"))
        status.setToolTip(str(self._recording_path))
        self._update_record_button()
        return True

    def _record_sample(self, t_ms, frame_time, spikes, native_events):
        clocks = self._rec_meta["sample_clock_kinds"]
        if self._last_clock_kind not in clocks:
            clocks.append(self._last_clock_kind)
        provenance = "source events" if native_events else "Vm threshold crossings"
        if provenance not in self._rec_meta["event_provenance"]:
            self._rec_meta["event_provenance"].append(provenance)

        if not self._has_frame:
            self._last_recorded_frame_ms = None
        if frame_time is not None:
            self._frames.append((
                len(self._frames), frame_time, len(self._samples), *self.FluoData, t_ms, *self._frame_dff
            ))
            self._last_recorded_frame_ms = frame_time
        has_frame = self._last_recorded_frame_ms is not None
        held = self.FluoData if has_frame else (np.nan,) * N_NEURONS
        self._samples.append((
            t_ms, self.StimData, self.TriggerData, *self.VmData, *self.CalciumData, *held,
            len(self._frames) - 1 if has_frame else -1, self._last_recorded_frame_ms, *spikes
        ))

    def _export_csv(self):
        path = self._recording_path
        frames_path, meta_path = (path.with_name(path.stem + suffix) for suffix in SIDECAR_SUFFIXES)
        metadata = dict(self._rec_meta, n_samples=len(self._samples), n_frames=len(self._frames))
        with TemporaryDirectory(dir=path.parent) as staging:
            temporary = Path(staging)
            sample_tmp = temporary / path.name
            frame_tmp = temporary / frames_path.name
            meta_tmp = temporary / meta_path.name
            pd.DataFrame(self._samples, columns=SAMPLE_COLUMNS).to_csv(sample_tmp, index=False)
            pd.DataFrame(self._frames, columns=FRAME_COLUMNS).to_csv(frame_tmp, index=False)
            with sample_tmp.open("rb") as handle:
                samples_hash = stream_digest(handle)
            with frame_tmp.open("rb") as handle:
                frames_hash = stream_digest(handle)
            metadata["file_sha256"] = {
                "samples_csv": samples_hash, "frames_csv": frames_hash,
            }
            meta_tmp.write_text(json.dumps(metadata, indent=2, allow_nan=False), encoding="utf-8")
            files = ((sample_tmp, path), (frame_tmp, frames_path), (meta_tmp, meta_path))
            backups = {}
            for index, (_, destination) in enumerate(files):
                if destination.exists():
                    backup = temporary / f".previous-{index}"
                    copyfile(destination, backup)
                    backups[destination] = backup

            published = []
            try:
                # Publish metadata last and roll back any replacements if a later write fails.
                for staged, destination in files:
                    staged.replace(destination)
                    published.append(destination)
            except OSError:
                for destination in reversed(published):
                    if destination in backups:
                        backups[destination].replace(destination)
                    else:
                        destination.unlink()
                raise

    def _refresh_imaging_params(self):
        """Cache accepted slider values in the model's units."""
        p = self._imaging_params
        previous_rate = p.get("frame_rate")
        for name, spec in IMAGING_SLIDERS.items():
            p[spec.parameter] = spec.display_value(self._slider_bindings[name].value) * spec.model_scale
        if previous_rate != p["frame_rate"]:
            self._next_frame_ms = None
            self._set_imaging_time_window()

        p["Sig_k"] = self.sig_k
        p["Sig_c_half_uM"] = self.sig_c_half_uM
        p.setdefault("Lin_alpha", 1.0)
        p.setdefault("Lin_beta", 0.0)
        p.setdefault("Bind_S_tot", self._S_tot)
        p.setdefault("Bind_n", self._bind_n)
        p.setdefault("Bind_k_on", self._k_on)
        p.setdefault("Bind_k_off", self._k_off)
        p["PMT_excess_noise_sigma"] = self.pmt_excess_noise_sigma
        p["PMT_excess_noise_gamma"] = self.pmt_excess_noise_gamma
        self._update_F0_from_baseline()
        self._show_active_indicator()

    def _set_source_status(self, text, detail=None):
        self.ui.Imaging_ConnectButton.setText(text)
        clock = (self.tr("Board model time: 0.1 ms per sample. Nominal USB cadence: 2 ms per packet.")
                 if self.source_mode == "spikeling" else self.tr("Emulator simulation time"))
        self.ui.Imaging_ConnectButton.setToolTip(f"{detail} · {clock}" if detail else clock)

    def bind_geci_controls(self):
        self.ui.Imaging_GECI_comboBox.currentIndexChanged.connect(self.SelectGECI)
        self.ui.Imaging_GECI_pushButton.clicked.connect(self._on_geci_apply_clicked)

    def cleanup(self):
        """Reset imaging state and clear plots."""
        self.last_valid_data = None
        self.ui.Imaging_Oscilloscope_widget.clear()
        self.bleach_B = 1.0

        # Reset plot objects
        self._plots_ready = False
        self._mainVB = None
        self._vm_prev[:] = 0.0

        # Remove viewboxes/axes safely
        pi = self.ui.Imaging_Oscilloscope_widget.getPlotItem()

        if getattr(self, "secondaryVB", None) is not None:
            try:
                self.ui.Imaging_Oscilloscope_widget.scene().removeItem(self.secondaryVB)
            except Exception:
                pass
            self.secondaryVB = None

        if getattr(self, "calciumVB", None) is not None:
            try:
                self.ui.Imaging_Oscilloscope_widget.scene().removeItem(self.calciumVB)
            except Exception:
                pass
            self.calciumVB = None

        if getattr(self, "calciumAxis", None) is not None:
            try:
                pi.layout.removeItem(self.calciumAxis)
            except Exception:
                pass
            self.calciumAxis = None

        # Reset the source clock and frame schedule.
        self._t_last_ms = None
        self._last_input_ms = None
        self._last_clock_kind = None
        self._last_clamped = None
        self._next_frame_ms = None
        self._last_arrival = None
        self._t_last_spike_ms[:] = -1e12
        self._ca_xd[:] = 0.0
        self._ca_xdr[:] = 0.0
        self._S_bound[:] = 0.0
        self.IndicatorSat[:] = 0.0

        # Reset latest values
        self.CalciumData[:] = float(self._imaging_params.get("CalciumBaseline", 0.1)) if self._imaging_params else 0.1
        self.FluoData[:] = 0.0
        self.VmData[:] = 0.0
        self.StimData = 0.0
        self.TriggerData = 0.0

        if hasattr(self, "_rx_timer"):
            self._rx_timer.stop()
        self._rx_queue.clear()
