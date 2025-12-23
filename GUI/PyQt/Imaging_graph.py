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
from decimal import Decimal
from typing import Tuple

import Settings
import GECI_parameters
from serial_manager import serial_manager


# =============================================================================
# Constants
# =============================================================================

SAMPLE_INTERVAL = 0.1          # ms per incoming sample (fallback if packet lacks timestamp)
TIME_WINDOW = 2000             # ms total rolling buffer
TIME_WINDOW_DISPLAY = 500      # ms visible in oscilloscope x-range
PEN_WIDTH = 1
STIM_MIN = -100
STIM_MAX = 100

N_NEURONS = 3                  # primary + two auxiliaries


# =============================================================================
# ImagingGraph
# =============================================================================

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
        self.last_valid_data = None
        self._t_last_ms = None
        self._t_abs_ms = 0.0             # fallback clock when hardware provides no timestamp

        # -------------------------
        # Imaging / Model state
        # -------------------------
        self._imaging_params = {}

        # Spike detection parameters
        self.SpikeThreshold = -20.0      # mV; threshold for upward crossing
        self.SpikeRefractory_ms = 3.0    # ms; refractory window after detected spike
        self._t_last_spike_ms = np.full(N_NEURONS, -1e12, dtype=float)  # per neuron last spike time

        # Frame sampling state (camera sampling)
        self._frame_phase_ms = 0.0
        self.FrameTime_buffer = None
        self.Fluo_frame_buffers = None

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
        self._plot_decimator = 0
        self._plot_every = 1
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
        # Columns (kept simple and explicit):
        # t, stim, trig, vm1..3, ca1..3, F1..3
        self._rec = {
            "t_ms": [],
            "stim": [],
            "trig": [],
            "vm1": [], "vm2": [], "vm3": [],
            "ca1_uM": [], "ca2_uM": [], "ca3_uM": [],
            "F1": [], "F2": [], "F3": [],
        }

        # Signals
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
        """Activate imaging pipeline."""
        self._initialize_buffers()
        self._initialize_plot()
        self._connect_parameters()
        self.apply_indicator_preset("Generic", update_ui=True)
        self._update_connect_button(True)

        self.parent.ImagingConnectionFlag = True
        self.bleach_B = 1.0

        # Initialize to steady baseline:
        # - Calcium kernel internal states start at 0 so Ca(t)=Cb initially.
        self._ca_xd[:] = 0.0
        self._ca_xdr[:] = 0.0

        Cb = float(self._imaging_params.get("CalciumBaseline", 0.1))  # µM
        self.CalciumData[:] = Cb

        # Initialize “indicator saturation/bound fraction” to its baseline equilibrium
        Sat0 = self._indicator_equilibrium_saturation(Cb, self._imaging_params)
        self.IndicatorSat[:] = Sat0

        # If kinetic binding is enabled, initialize bound state to equilibrium value.
        # (This avoids a transient “startup shock” in fluorescence.)
        if self.binding_enabled:
            self._S_bound[:] = Sat0 * self._S_tot  # S_b = frac * S_tot

        # Initialize fluorescence to baseline with NO noise so first frame is stable.
        F0 = self._baseline_fluorescence_from_C(Cb, self._imaging_params)
        self.FluoData[:] = F0

        # Set F0 reference for ΔF/F plotting (same for all neurons here)
        self._update_F0_from_baseline()

        self._rx_queue.clear()
        self._rx_timer.start()

    def disconnect(self):
        """Deactivate imaging pipeline."""
        self.cleanup()
        self._update_connect_button(False)
        self.parent.ImagingConnectionFlag = False

    # -------------------------------------------------------------------------
    # Data Entry Points
    # -------------------------------------------------------------------------

    def _process_rx_queue(self):
        if self.source_mode != "spikeling" or not self.parent.ImagingConnectionFlag:
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
        if not self.parent.ImagingConnectionFlag:
            return

        self._rx_queue.append(data)

    def on_emulator_data(self, data: list) -> None:
        """Handle incoming emulator list of packets."""
        if isinstance(data, list) and data and isinstance(data[0], (list, tuple, np.ndarray)):
            self._consume_batch(data)
        else:
            self._consume_vector(data)

    # -------------------------------------------------------------------------
    # Main Imaging Pipeline
    # -------------------------------------------------------------------------

    def _consume_vector(self, data, plot=True):
        """
        Central imaging update pipeline.

        Steps:
        1) Validate & parse incoming packet
        2) Update calcium + fluorescence model
        3) Append data to rolling buffers
        4) Handle recording logic
        5) Redraw plots (decimated)
        """
        if not self.parent.ImagingConnectionFlag:
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

        # Advance model (includes frame sampling)
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
        if not self.parent.ImagingConnectionFlag:
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
    # Imaging Model
    # -------------------------------------------------------------------------

    def apply_indicator_preset(self, name: str, update_ui: bool = True) -> None:
        """
        Load a GECI preset from GECI_parameters.GECI.

        Expected preset keys:
          - Kd_uM
          - hill_n
          - Ind_tau_rise_ms      (indicator on / rise, ms)
          - Ind_tau_decay_ms     (indicator off / decay, ms)
          - dff_max          (max ΔF/F0 at saturation)

    Note: cellular calcium kinetics are controlled by the CalciumRise/CalciumDecay sliders
          and are NOT part of the GECI preset.
        """
        geci = GECI_parameters.GECI
        preset = geci.get(name) or geci.get("Generic")
        if preset is None:
            raise ValueError("GECI preset dictionary has no 'Generic' fallback.")

        self.indicator_name = name if name in geci else "Generic"

        # --- indicator chemistry ---
        self.Kd_uM = float(preset["Kd_uM"])
        self.hill_n = float(preset["hill_n"])
        self.dff_max = float(preset["dff_max"])
        self.Ind_tau_rise_ms = float(preset.get("Ind_tau_rise_ms", 50.0))
        self.Ind_tau_decay_ms = float(preset.get("Ind_tau_decay_ms", 300.0))

        # Push into live parameter dictionary so model uses it
        p = self._imaging_params
        p["DissociationConstant"] = self.Kd_uM
        p["HillCoef"] = self.hill_n
        p["dff_max"] = self.dff_max
        p["Ind_tau_rise_ms"] = self.Ind_tau_rise_ms
        p["Ind_tau_decay_ms"] = self.Ind_tau_decay_ms

        # UI update (kept from original; safe-clamped)
        if update_ui:
            # Existing UI updates
            kd_val = int(round(self.Kd_uM * 10.0))
            hill_val = int(round(self.hill_n * 100.0))
            self.ui.Imaging_kd_Slider.setValue(
                max(self.ui.Imaging_kd_Slider.minimum(),
                    min(self.ui.Imaging_kd_Slider.maximum(), kd_val))
            )
            self.ui.Imaging_Hill_Slider.setValue(
                max(self.ui.Imaging_Hill_Slider.minimum(),
                    min(self.ui.Imaging_Hill_Slider.maximum(), hill_val))
            )

            # NEW: if you added these sliders in the UI
            if hasattr(self.ui, "Imaging_DFF_Slider"):
                # choose your encoding; example assumes slider directly stores dff_max*10
                self.ui.Imaging_DFF_Slider.setValue(int(round(self.dff_max * 10.0)))

            if hasattr(self.ui, "Imaging_IndRise_Slider"):
                self.ui.Imaging_IndRise_Slider.setValue(int(round(self.Ind_tau_rise_ms)))

            if hasattr(self.ui, "Imaging_IndDecay_Slider"):
                self.ui.Imaging_IndDecay_Slider.setValue(int(round(self.Ind_tau_decay_ms)))

        # If we are currently using ΔF/F, refresh baseline reference because Kd/n may have changed.
        if self.use_dff:
            self._update_F0_from_baseline()


    def SelectGECI(self):
        name = self.ui.Imaging_GECI_comboBox.currentText()  # e.g. "Generic"
        p = GECI_parameters.GECI.get(name, GECI_parameters.GECI["Generic"])

        Kd_uM = float(p["Kd_uM"])
        hill_n = float(p["hill_n"])
        tau_rise = float(p.get("Ind_tau_rise_ms", 50.0))
        tau_decay = float(p.get("Ind_tau_decay_ms", 300.0))
        dff_max = float(p["dff_max"])

        self.ui.Imaging_GECI_ReadingsKd_Value.setText(f"{Kd_uM:.3f}")
        self.ui.Imaging_GECI_ReadingsKd_Value.setStyleSheet("color: rgb(250, 250, 250);")
        self.ui.Imaging_GECI_ReadingsAffinity_Value.setText(f"{hill_n:.2f}")
        self.ui.Imaging_GECI_ReadingsAffinity_Value.setStyleSheet("color: rgb(250, 250, 250);")
        self.ui.Imaging_GECI_ReadingsDFF_Value.setText(f"{dff_max:.1f}")
        self.ui.Imaging_GECI_ReadingsDFF_Value.setStyleSheet("color: rgb(250, 250, 250);")
        self.ui.Imaging_GECI_ReadingsRise_Value.setText(f"{tau_rise:.0f}")
        self.ui.Imaging_GECI_ReadingsRise_Value.setStyleSheet("color: rgb(250, 250, 250);")
        self.ui.Imaging_GECI_ReadingsDecay_Value.setText(f"{tau_decay:.0f}")
        self.ui.Imaging_GECI_ReadingsDecay_Value.setStyleSheet("color: rgb(250, 250, 250);")


    def _apply_GECI(self):
        """
        Writes the selected indicator and its key parameters to UI labels.
        """
        p = self._imaging_params
        Kd_uM = float(self.ui.Imaging_GECI_ReadingsKd_Value.text())
        hill_n = float(self.ui.Imaging_GECI_ReadingsAffinity_Value.text())
        dff_max = float(self.ui.Imaging_GECI_ReadingsDFF_Value.text())
        tau_rise = float(self.ui.Imaging_GECI_ReadingsRise_Value.text())
        tau_decay = float(self.ui.Imaging_GECI_ReadingsDecay_Value.text())
        p["DissociationConstant"]= Kd_uM
        p["HillCoef"] = hill_n
        p["dff_max"] = tau_rise
        p["Ind_tau_rise_ms"] = tau_decay
        p["Ind_tau_decay_ms"] = dff_max

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


    def _update_model(self, vm1, stim, vm2, vm3, trigger, t_ms, dt_ms):
        """
        Update calcium and fluorescence model for all neurons.

          - Calcium is updated at every incoming sample (dt_ms)
          - Fluorescence is only *observed* on camera frames (frame_rate) and held constant between frames.

        Model steps per neuron i:
          1) spike_i  = detect_spike(Vm_i, Vm_prev_i, t_ms)
          2) Ca_i     = update_calcium(i, spike_i, dt_ms)
          3) Sat_i    = update_indicator_sat(i, Ca_i, dt_ms) equilibrium Hill/sigmoid or kinetic ODE
          4) If new frame: F_i = sat_to_fluorescence(Ca_i, Sat_i, ...)
        """
        self.VmData[:] = (vm1, vm2, vm3)
        self.StimData = stim
        self.TriggerData = trigger

        if not self._imaging_params:
            return
        p = self._imaging_params

        self._update_photobleach(dt_ms, p)

        # ------------------------------------------------------------
        # Frame timing: frame_rate [Hz] -> period [ms]
        # ------------------------------------------------------------
        frame_period_ms = 1000.0 / max(1.0, float(p.get("frame_rate", 10)))
        self._frame_phase_ms += float(dt_ms)

        new_frame = (self._frame_phase_ms >= frame_period_ms)
        if new_frame:
            n_frames = int(self._frame_phase_ms // frame_period_ms)
            self._frame_phase_ms -= n_frames * frame_period_ms

        # Will hold fluorescence computed at this frame (only valid if new_frame=True)
        frame_fluo = [None] * N_NEURONS

        for i in range(N_NEURONS):
            # Vm_prev from buffer (last appended sample) if available; else use current
            vm_prev = self.Vm_buffers[i][-1] if hasattr(self, "Vm_buffers") and len(self.Vm_buffers[i]) else self.VmData[i]

            # 1) Spike detection (threshold crossing + refractory)
            spike = self._detect_spike(vm_now=self.VmData[i], vm_prev=vm_prev, t_ms=t_ms, neuron_index=i)

            # 2) Calcium transient (Wei rise/decay kernel; separate τrise and τdecay)
            self.CalciumData[i] = self._update_calcium(neuron_index=i, spike=spike, p=p, dt_ms=dt_ms)

            # 3) Indicator saturation / bound fraction (equilibrium Hill or sigmoid, OR kinetic binding ODE)
            self.IndicatorSat[i] = self._update_indicator_sat(
                neuron_index=i,
                Ca_uM=self.CalciumData[i],
                p=p,
                dt_ms=dt_ms
            )

            # 4) Fluorescence observation (sampled at frame times)
            if new_frame:
                frame_fluo[i] = self._sat_to_fluorescence(
                    neuron_index=i,
                    Ca_uM=self.CalciumData[i],
                    Sat=self.IndicatorSat[i],
                    p=p
                )

        # Commit a new camera sample
        if new_frame:
            # Frame time is the boundary time (approx): current time minus remaining phase
            t_frame_ms = float(t_ms) - float(self._frame_phase_ms)
            self.FrameTime_buffer.append(t_frame_ms)
            for i in range(N_NEURONS):
                self.FluoData[i] = float(frame_fluo[i])
                self.Fluo_frame_buffers[i].append(float(frame_fluo[i]))
        # Else: FluoData is held between frames by design (camera sampling effect).

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

        # Spike amplitude per event (µM)
        self.spikerise = float(p.get("SpikeRise", 0.1))  # slider value already scaled in _connect_parameters

        # Baseline calcium (µM)
        Cb = float(p.get("CalciumBaseline", 0.1))

        i = neuron_index

        # Update internal kernel states
        self._ca_xd[i] = self._ca_xd[i] * exp_d + self.spikerise * float(spike)
        self._ca_xdr[i] = self._ca_xdr[i] * exp_dr + self.spikerise * float(spike)

        # Construct calcium concentration
        C = Cb + (self._ca_xd[i] - self._ca_xdr[i])

        # Internal calcium noise (Gaussian)
        # We reuse existing slider "NoiseScale" semantics, scaled by sqrt(dt_s).
        self.Ca_noise_uM = float(p.get("NoiseScale", 0.0))
        if self.Ca_noise_uM > 0:
            dt_s = dt_ms / 1000.0
            C += self.Ca_noise_uM * np.sqrt(dt_s) * np.random.normal()

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

        return float(F_mean + sigma * np.random.normal())

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
        """
        if not self._imaging_params:
            return
        p = self._imaging_params

        Cb = float(p.get("CalciumBaseline", 0.1))
        F0 = self._baseline_fluorescence_from_C(Cb, p)

        self.F0[:] = float(F0)

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
        ax_left = self.ui.Imaging_Oscilloscope_widget.getPlotItem().getAxis("left")
        if self.use_dff:
            ax_left.setLabel("ΔF/F0", units="%")
        else:
            ax_left.setLabel("Fluorescence", units="a.u.")

        # Force redraw
        if self._plots_ready:
            self._update_plots()

    # -------------------------------------------------------------------------
    # Buffers
    # -------------------------------------------------------------------------

    def _initialize_buffers(self):
        """Create rolling buffers for all plotted variables."""
        self._bufsize = int(TIME_WINDOW / SAMPLE_INTERVAL)

        self.Time_buffer = collections.deque([0.0] * self._bufsize, self._bufsize)
        self.Imagingx = (np.arange(self._bufsize) - (self._bufsize - 1)) * SAMPLE_INTERVAL

        self.Stim_buffer = collections.deque([0.0] * self._bufsize, self._bufsize)
        self.Trigger_buffer = collections.deque([0.0] * self._bufsize, self._bufsize)

        self.Calcium_buffers = [
            collections.deque([0.0] * self._bufsize, self._bufsize)
            for _ in range(N_NEURONS)
        ]
        self.Fluo_buffers = [
            collections.deque([0.0] * self._bufsize, self._bufsize)
            for _ in range(N_NEURONS)
        ]
        self.Vm_buffers = [
            collections.deque([0.0] * self._bufsize, self._bufsize)
            for _ in range(N_NEURONS)
        ]

        # Frame-sampled buffers
        max_fps = max(1, self.ui.Imaging_FrameRate_Slider.maximum()*100)
        self._frame_bufsize = int(TIME_WINDOW * max_fps / 1000.0) + 10
        self.FrameTime_buffer = collections.deque(maxlen=self._frame_bufsize)
        self.Fluo_frame_buffers = [collections.deque(maxlen=self._frame_bufsize) for _ in range(N_NEURONS)]

        # Reset frame phase and spike refractory state
        self._frame_phase_ms = 0.0
        self._t_last_spike_ms[:] = -1e12

    def _append_buffers(self, t_ms):
        """Append latest model states to rolling buffers."""
        self.Time_buffer.append(float(t_ms))
        self.Stim_buffer.append(float(self.StimData))
        self.Trigger_buffer.append(float(self.TriggerData))

        for i in range(N_NEURONS):
            self.Calcium_buffers[i].append(float(self.CalciumData[i]))
            self.Fluo_buffers[i].append(float(self.FluoData[i]))
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
        pi.showAxis("right")

        ax_left = pi.getAxis("left")
        ax_right = pi.getAxis("right")
        ax_bottom = pi.getAxis("bottom")

        ax_bottom.enableAutoSIPrefix(False)
        ax_bottom.setLabel("Time", units="ms")

        if self.use_dff:
            ax_left.setLabel("ΔF/F0", units="")
        else:
            ax_left.setLabel("Fluorescence", units="a.u.")
        ax_right.setLabel("Stimulus / Vm", units="a.u. / mV")

        # Main ViewBox
        vb = pi.getViewBox()
        self._mainVB = vb
        vb.enableAutoRange(axis=pg.ViewBox.XAxis, enable=False)
        vb.setXRange(-TIME_WINDOW_DISPLAY, 0, padding=0)
        vb.setLimits(xMin=-TIME_WINDOW, xMax=0)
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
        vb.sigResized.connect(self.update_views)
        vb.sigRangeChanged.connect(lambda *_: self.update_views())
        self.update_views()

        # Curves
        x = self.Imagingx

        # Fluorescence curves on main VB
        self.Fluocurve1 = pw.plot(x, np.zeros_like(x),
                                 pen=pg.mkPen(Settings.DarkSolarized[4], width=PEN_WIDTH, cosmetic=True))
        self.Fluocurve2 = pw.plot(x, np.zeros_like(x),
                                 pen=pg.mkPen([0, 255, 133], width=PEN_WIDTH, cosmetic=True))
        self.Fluocurve3 = pw.plot(x, np.zeros_like(x),
                                 pen=pg.mkPen([133, 255, 0], width=PEN_WIDTH, cosmetic=True))

        # Calcium curves on calciumVB
        self.Calciumcurve1 = pg.PlotCurveItem(x, np.zeros_like(x),
                                              pen=pg.mkPen(Settings.DarkSolarized[10], width=PEN_WIDTH, cosmetic=True))
        self.Calciumcurve2 = pg.PlotCurveItem(x, np.zeros_like(x),
                                              pen=pg.mkPen(Settings.DarkSolarized[9], width=PEN_WIDTH, cosmetic=True))
        self.Calciumcurve3 = pg.PlotCurveItem(x, np.zeros_like(x),
                                              pen=pg.mkPen(Settings.DarkSolarized[7], width=PEN_WIDTH, cosmetic=True))
        self.calciumVB.addItem(self.Calciumcurve1)
        self.calciumVB.addItem(self.Calciumcurve2)
        self.calciumVB.addItem(self.Calciumcurve3)

        # Vm curves on secondaryVB
        self.Vmcurve1 = pg.PlotCurveItem(x, np.zeros_like(x),
                                         pen=pg.mkPen(Settings.DarkSolarized[3], width=PEN_WIDTH, cosmetic=True))
        self.Vmcurve2 = pg.PlotCurveItem(x, np.zeros_like(x),
                                         pen=pg.mkPen(Settings.DarkSolarized[6], width=PEN_WIDTH, cosmetic=True))
        self.Vmcurve3 = pg.PlotCurveItem(x, np.zeros_like(x),
                                         pen=pg.mkPen(Settings.DarkSolarized[8], width=PEN_WIDTH, cosmetic=True))
        self.secondaryVB.addItem(self.Vmcurve1)
        self.secondaryVB.addItem(self.Vmcurve2)
        self.secondaryVB.addItem(self.Vmcurve3)

        # Stim curve on secondaryVB
        self.Stimcurve = pg.PlotCurveItem(x, np.zeros_like(x),
                                          pen=pg.mkPen(Settings.DarkSolarized[5], width=PEN_WIDTH, cosmetic=True))
        self.secondaryVB.addItem(self.Stimcurve)

        self._plots_ready = True

    def update_views(self):
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
        t_arr = np.asarray(self.Time_buffer, dtype=float)
        x = t_arr - t_arr[-1]  # last point at 0 ms, older negative

        # Calcium
        calcium_checks = [ui.Imaging_Calcium1_Checkbox, ui.Imaging_Calcium2_Checkbox, ui.Imaging_Calcium3_Checkbox]
        calcium_curves = [self.Calciumcurve1, self.Calciumcurve2, self.Calciumcurve3]

        for i in range(N_NEURONS):
            visible = calcium_checks[i].isChecked()
            calcium_curves[i].setVisible(visible)
            if visible:
                calcium_curves[i].setData(x, list(self.Calcium_buffers[i]))

        # Fluorescence (or ΔF/F0)
        fluo_checks = [ui.Imaging_Fluorescence1_Checkbox, ui.Imaging_Fluorescence2_Checkbox, ui.Imaging_Fluorescence3_Checkbox]
        fluo_curves = [self.Fluocurve1, self.Fluocurve2, self.Fluocurve3]

        for i in range(N_NEURONS):
            visible = fluo_checks[i].isChecked()
            fluo_curves[i].setVisible(visible)
            if not visible:
                continue

            y = np.asarray(self.Fluo_buffers[i], dtype=float)

            if self.use_dff:
                # Offset-corrected ΔF/F0 (kept from your original approach)
                offset = float(self._imaging_params.get("FluoOffset", 0.0))
                y_sig = y - offset
                f0_sig = float(self.F0[i]) - offset
                f0_sig = max(1e-12, f0_sig)
                y = 100 * (y_sig - f0_sig) / f0_sig

            fluo_curves[i].setData(x, y)

        # Vm
        vm_checks = [ui.Imaging_Vm1_Checkbox, ui.Imaging_Vm2_Checkbox, ui.Imaging_Vm3_Checkbox]
        vm_curves = [self.Vmcurve1, self.Vmcurve2, self.Vmcurve3]

        for i in range(N_NEURONS):
            visible = vm_checks[i].isChecked()
            vm_curves[i].setVisible(visible)
            if visible:
                vm_curves[i].setData(x, list(self.Vm_buffers[i]))

        # Stimulus
        visible = ui.Imaging_Stimulus_Checkbox.isChecked()
        self.Stimcurve.setVisible(visible)
        if visible:
            self.Stimcurve.setData(x, list(self.Stim_buffer))

    # -------------------------------------------------------------------------
    # Recording
    # -------------------------------------------------------------------------

    def _handle_recording(self):
        """
        Manage record toggle and export on stop.

        Behavior:
          - When the record button transitions from checked -> unchecked, export CSV and clear.
          - When checked, record_flag is True and samples are appended in _record_sample().
        """
        if (not self.ui.Imaging_DataRecording_Record_pushButton.isChecked()) and self.record_flag:
            # Stop event -> export and reset
            self._export_csv()
            self.record_flag = False
            for k in self._rec:
                self._rec[k].clear()

        if self.ui.Imaging_DataRecording_Record_pushButton.isChecked():
            self.record_flag = True

    def _record_sample(self, t_ms: float) -> None:
        """Append the latest sample to recording buffers (cheap list appends)."""
        self._rec["t_ms"].append(float(t_ms))
        self._rec["stim"].append(float(self.StimData))
        self._rec["trig"].append(float(self.TriggerData))

        self._rec["vm1"].append(float(self.VmData[0]))
        self._rec["vm2"].append(float(self.VmData[1]))
        self._rec["vm3"].append(float(self.VmData[2]))

        self._rec["ca1_uM"].append(float(self.CalciumData[0]))
        self._rec["ca2_uM"].append(float(self.CalciumData[1]))
        self._rec["ca3_uM"].append(float(self.CalciumData[2]))

        self._rec["F1"].append(float(self.FluoData[0]))
        self._rec["F2"].append(float(self.FluoData[1]))
        self._rec["F3"].append(float(self.FluoData[2]))

    def _export_csv(self):
        """Write recorded imaging data to CSV."""
        if len(self._rec["t_ms"]) == 0:
            return

        df = pd.DataFrame({
            "Time (ms)": self._rec["t_ms"],
            "Stim": self._rec["stim"],
            "Trigger": self._rec["trig"],
            "Vm1 (mV)": self._rec["vm1"],
            "Vm2 (mV)": self._rec["vm2"],
            "Vm3 (mV)": self._rec["vm3"],
            "Ca1 (uM)": self._rec["ca1_uM"],
            "Ca2 (uM)": self._rec["ca2_uM"],
            "Ca3 (uM)": self._rec["ca3_uM"],
            "F1 (a.u.)": self._rec["F1"],
            "F2 (a.u.)": self._rec["F2"],
            "F3 (a.u.)": self._rec["F3"],
        })

        path = f"{self.ui.Imaging_SelectedFolderLabel.text()}.csv"
        df.to_csv(path, index=False)

    # -------------------------------------------------------------------------
    # UI Helpers
    # -------------------------------------------------------------------------

    def _connect_parameters(self):
        """
        Cache imaging parameter values from sliders and keep them updated.
        """
        if getattr(self, "_params_connected", False):
            return
        self._params_connected = True

        ui = self.ui
        p = self._imaging_params

        def update(_=None):
            # Camera parameters
            p["frame_rate"] = max(1, ui.Imaging_FrameRate_Slider.value()*100)
            p["PMT"] = ui.Imaging_PMT_Slider.value() / 100.0
            p["Laser"] = ui.Imaging_Laser_Slider.value() / 100.0

            # Calcium parameters (µM)
            # Baseline
            p["CalciumBaseline"] = ui.Imaging_CalciumBaseline_Slider.value() / 100.0

            # Spike amplitude per event (µM)
            p["SpikeRise"] = ui.Imaging_CalciumJump_Slider.value() / 100.0

            # Internal calcium noise magnitude (µM * sqrt(s))
            p["NoiseScale"] = ui.Imaging_CalciumNoise_Slider.value() / 10.0

            # τdecay_ms: default from preset
            p["Ca_tau_decay_ms"] = float(ui.Imaging_CalciumDecay_Slider.value())

            # τrise_ms: default from preset
            p["Ca_tau_rise_ms"] = float(ui.Imaging_CalciumRise_Slider.value())

            # Fluorescence / imaging gain parameters
            p["FluoScale"] = ui.Imaging_FluoScale_Slider.value() / 10.0
            p["FluoOffset"] = ui.Imaging_FluoOffset_Slider.value()

            # Additive noise floor + shot noise factor
            p["FluoNoiseSigma"] = ui.Imaging_FluoNoise_Slider.value() / 5000.0
            p["PhotoShotNoise"] = ui.Imaging_PhotoShotNoise_Slider.value() / 1e6

            # Indicator saturation parameters (µM)
            p["HillCoef"] = ui.Imaging_Hill_Slider.value() / 100.0
            p["DissociationConstant"] = ui.Imaging_kd_Slider.value() / 10.0

            # Indicator kinetics (ms)
            p["Ind_tau_rise_ms"] = float(ui.Imaging_IndRise_Slider.value())
            p["Ind_tau_decay_ms"] = float(ui.Imaging_IndDecay_Slider.value())

            # Indicator dynamics max ΔF/F0
            p["dff_max"] = float(ui.Imaging_DFF_Slider.value()) / 10.0

            # Optional sigmoid params (kept configurable via dict even if no UI exists yet)
            p["Sig_k"] = float(getattr(self, "sig_k", 10.0))
            p["Sig_c_half_uM"] = float(getattr(self, "sig_c_half_uM", 0.15))

            # Optional linear params (Vogelstein-like)
            p["Lin_alpha"] = float(p.get("Lin_alpha", 1.0))
            p["Lin_beta"] = float(p.get("Lin_beta", 0.0))

            # Optional binding kinetics params (Pham-like), if/when you expose them in UI
            p["Bind_S_tot"] = float(p.get("Bind_S_tot", self._S_tot))
            p["Bind_n"] = float(p.get("Bind_n", self._bind_n))
            p["Bind_k_on"] = float(p.get("Bind_k_on", self._k_on))
            p["Bind_k_off"] = float(p.get("Bind_k_off", self._k_off))

            # PMT
            p["PMT_excess_noise_sigma"] = float(getattr(self, "pmt_excess_noise_sigma", 0.02))
            p["PMT_excess_noise_gamma"] = float(getattr(self, "pmt_excess_noise_gamma", 2.0))

            # If we are plotting ΔF/F, keep F0 synchronized with baseline settings
            if self.use_dff:
                self._update_F0_from_baseline()

        # Initial cache fill
        update()

        # Slider connections (explicit because Ui class is not a QObject)
        sliders = [
            ui.Imaging_FrameRate_Slider,
            ui.Imaging_PMT_Slider,
            ui.Imaging_Laser_Slider,
            ui.Imaging_CalciumDecay_Slider,
            ui.Imaging_CalciumJump_Slider,
            ui.Imaging_CalciumBaseline_Slider,
            ui.Imaging_CalciumNoise_Slider,
            ui.Imaging_IndRise_Slider,
            ui.Imaging_IndDecay_Slider,
            ui.Imaging_DFF_Slider,
            ui.Imaging_FluoScale_Slider,
            ui.Imaging_FluoOffset_Slider,
            ui.Imaging_FluoNoise_Slider,
            ui.Imaging_Hill_Slider,
            ui.Imaging_PhotoShotNoise_Slider,
            ui.Imaging_kd_Slider,
        ]
        for slider in sliders:
            slider.valueChanged.connect(update)

    def _update_connect_button(self, connected: bool):
        """Update connect button appearance."""
        if connected:
            self.ui.Imaging_ConnectButton.setText("Connected")
            self.ui.Imaging_ConnectButton.setStyleSheet(
                f"color: rgb{tuple(Settings.DarkSolarized[3])};\n"
                f"background-color: rgb{tuple(Settings.DarkSolarized[11])};\n"
                f"border: 1px solid rgb{tuple(Settings.DarkSolarized[14])};\n"
                f"border-radius: 10px;"
            )
        else:
            self.ui.Imaging_ConnectButton.setText("Connect Imaging screen to Spikeling screen")
            self.ui.Imaging_ConnectButton.setStyleSheet(
                f"color: rgb{tuple(Settings.DarkSolarized[14])};\n"
                f"background-color: rgb{tuple(Settings.DarkSolarized[2])};\n"
                f"border: 1px solid rgb{tuple(Settings.DarkSolarized[14])};\n"
                f"border-radius: 10px;"
            )

    # -------------------------------------------------------------------------
    # Cleanup
    # -------------------------------------------------------------------------

    def cleanup(self):
        """Reset imaging state and clear plots."""
        self.last_valid_data = None
        self.ui.Imaging_Oscilloscope_widget.clear()
        self.bleach_B = 1.0

        # Reset plot objects
        self._plots_ready = False
        self._mainVB = None

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

        # Reset timing and model states
        self._t_last_ms = None
        self._frame_phase_ms = 0.0
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
