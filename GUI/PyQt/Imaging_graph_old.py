"""
Imaging Graph Module

Real‑time imaging simulation (calcium + fluorescence) for Spikeling.

Based on Spike Inference from Calcium Imaging Using Sequential Monte Carlo Methods, Vogelstein et al., Biophysical Journal, 2009.
Biophys J. 2009 Jul 22;97(2):636–655. doi: 10.1016/j.bpj.2008.08.005

Responsibilities:
1. Receive Vm data from hardware or emulator
2. Simulate calcium dynamics and fluorescence readout
3. Maintain rolling buffers for oscilloscope‑style plotting
4. Plot signals efficiently using PyQtGraph
5. Optionally record imaging data to CSV

Data format:
Incoming packet (8 or 9 elements):
[Vm0, Stim, Itot, Vm1, ISyn1, Vm2, ISyn2, Trigger]
or
[timestamp, Vm0, Stim, Itot, Vm1, ISyn1, Vm2, ISyn2, Trigger]
"""

from PySide6.QtCore import QObject
import pyqtgraph as pg
import numpy as np
import pandas as pd
import collections
from decimal import Decimal
from typing import List, Tuple

import Settings
import GECI_parameters
from serial_manager import serial_manager


# =============================================================================
# Constants
# =============================================================================


SAMPLE_INTERVAL = 0.1          # ms per incoming sample (for x‑axis + CSV)
TIME_WINDOW = 5000             # ms
TIME_WINDOW_DISPLAY = 500
PEN_WIDTH = 1
STIM_MIN = -100
STIM_MAX = 100

N_NEURONS = 3                # primary + two auxiliaries


# =============================================================================
# ImagingGraph
# =============================================================================

class ImagingGraph(QObject):
    """
    Controller class for microscopy‑style imaging simulation and plotting.
    """

    # -------------------------------------------------------------------------
    # Initialization & Lifecycle
    # -------------------------------------------------------------------------

    def __init__(self, parent):
        super().__init__(parent)

        self.parent = parent
        self.ui = parent.ui

        # --- Data source control ---
        self.source_mode = "spikeling"   # "spikeling", "emulator", "none"
        self.last_valid_data = None
        self._t_last_ms = None
        self._t_abs_ms = 0.0  # fallback clock for hardware (no timestamp)

        # --- Imaging state ---
        self._imaging_params = {}
        self.SpikeThreshold = -20
        self._frame_phase_ms = 0.0
        self.FrameTime_buffer = None
        self.Fluo_frame_buffers = None
        self.indicator_name = "Generic"
        self.IndicatorSat = np.zeros(N_NEURONS)  # filtered saturation state (0..1)
        self.use_dff = False  # ΔF/F0 plotting toggle
        self.F0 = np.ones(N_NEURONS, dtype=float)  # baseline fluorescence per neuron
        self.calciumVB = None
        self.calciumAxis = None

        # --- load indicator preset  ---
        self.Kd_uM = 0.150  # dissociation constant (µM)
        self.hill_n = 4  # Hill coefficient
        self.tau_rise = 50
        self.tau_decay = 400
        self.dff_max = 3.0  # ΔF/F0 at saturation

        self.CalciumData = np.full(N_NEURONS, 0.1)
        self.FluoData = np.zeros(N_NEURONS)
        self.VmData = np.zeros(N_NEURONS)

        self.StimData = 0.0
        self.TriggerData = 0.0

        # --- Plot state ---
        self._plots_ready = False
        self._plot_decimator = 0
        self._plot_every = 1
        self.secondaryVB = None

        # --- Recording ---
        self.record_flag = False
        self.imaging_data = [[] for _ in range(12)]

        # --- Signals ---
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

        # Start at steady state for baseline calcium
        Cb = self._imaging_params.get("CalciumBaseline", 0.1)
        Sat0 = self._hill_saturation(Cb, self._imaging_params)
        self.IndicatorSat[:] = Sat0
        self.CalciumData[:] = Cb

        # Initialize fluorescence to baseline (no noise) so the first frame is not random
        gain = self._imaging_params["Laser"] * self._imaging_params["PMT"] * self._imaging_params["FluoScale"]
        offset = self._imaging_params["FluoOffset"]
        F0 = offset + gain * (1.0 + self.dff_max * Sat0)
        self.FluoData[:] = F0

        self._update_F0_from_baseline()

    def disconnect(self):
        """Deactivate imaging pipeline."""
        self.cleanup()
        self._update_connect_button(False)
        self.parent.ImagingConnectionFlag = False


    # -------------------------------------------------------------------------
    # Data Entry Points
    # -------------------------------------------------------------------------

    def on_data_received(self, data: list) -> None:
        """Handle incoming hardware packets."""
        if self.source_mode == "spikeling":
            self._consume_vector(data)
        else:
            return


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
        1. Validate & parse incoming packet
        2. Update calcium + fluorescence model
        3. Append data to rolling buffers
        4. Handle recording logic
        5. Redraw plots (decimated)
        """
        if not self.parent.ImagingConnectionFlag:
            return
        if data is None or len(data) < 8:
            return

        parsed = self._parse_packet(data)
        if parsed is None:
            return

        t_ms, vm1, stim, vm2, vm3, trig = parsed

        if self._t_last_ms is None:
            dt_ms = SAMPLE_INTERVAL
        else:
            dt_ms = t_ms - self._t_last_ms

        # --- sanity clamp dt_ms (must be milliseconds) ---
        if (not np.isfinite(dt_ms)) or (dt_ms <= 0.0) or (dt_ms > 1000.0):
            dt_ms = SAMPLE_INTERVAL

        self._t_last_ms = t_ms


        # --- advance model using dt_ms ---
        self._update_model(vm1, stim, vm2, vm3, trig, dt_ms)

        # --- append buffers (including time) ---
        self._append_buffers(t_ms)

        self._handle_recording()

        # ---- plot optionally ----
        if not plot or not self._plots_ready:
            return

        self._plot_decimator += 1
        if self._plot_decimator >= self._plot_every:
            self._plot_decimator = 0
            self._update_plots()


    def _consume_batch(self, batch):
        if not self.parent.ImagingConnectionFlag:
            return

        for pkt in batch:
            self._consume_vector(pkt, plot=False)

        # Plot once after ingesting the whole batch
        if self._plots_ready:
            self._update_plots()

    # -------------------------------------------------------------------------
    # Packet Parsing
    # -------------------------------------------------------------------------

    def _score_mapping(self, vals, idxs: Tuple[int, int, int, int, int]):
        """Heuristic score for packet mappings."""
        try:
            vm1, stim, vm2, vm3, trig = [vals[i] for i in idxs]
        except Exception:
            return -1, None

        score = 0
        for v in (vm1, vm2, vm3):
            if np.isfinite(v) and -200 <= v <= 200:
                score += 1
        if np.isfinite(stim) and -200 <= stim <= 200:
            score += 1
        if np.isfinite(trig) and -0.5 <= trig <= 1.5:
            score += 1

        return score, (vm1, stim, vm2, vm3, trig)

    def _parse_packet(self, data: list):
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
            # no timestamp -> cannot infer emulator dt correctly if downsampled
            # treat as sequential samples at SAMPLE_INTERVAL
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
        geci = GECI_parameters.GECI
        preset = geci.get(name) or geci.get("Generic")
        if preset is None:
            raise ValueError("GECI preset dictionary has no 'Generic' fallback.")

        self.indicator_name = name if name in geci else "Generic"

        # Store on self
        self.Kd_uM     = float(preset["Kd_uM"])
        self.hill_n    = float(preset["hill_n"])
        self.tau_rise  = float(preset["tau_rise_ms"])
        self.tau_decay = float(preset["tau_decay_ms"])
        self.dff_max   = float(preset["dff_max"])

        # Drive the model parameters directly (authoritative)
        p = self._imaging_params
        p["DissociationConstant"] = self.Kd_uM
        p["HillCoef"] = self.hill_n

        if update_ui:
            kd_val = int(round(self.Kd_uM * 10.0))  # slider encodes 0.1..10 µM as value/10
            hill_val = int(round(self.hill_n * 100.0))  # slider encodes n as value/100

            self.ui.Imaging_kd_Slider.setValue(
                max(self.ui.Imaging_kd_Slider.minimum(),
                    min(self.ui.Imaging_kd_Slider.maximum(), kd_val))
            )
            self.ui.Imaging_Hill_Slider.setValue(
                max(self.ui.Imaging_Hill_Slider.minimum(),
                    min(self.ui.Imaging_Hill_Slider.maximum(), hill_val))
            )


    def _update_model(self, vm1, stim, vm2, vm3, trigger, dt_ms):
        """Update calcium and fluorescence model for all neurons."""
        self.VmData[:] = (vm1, vm2, vm3)
        self.StimData = stim
        self.TriggerData = trigger

        if not self._imaging_params:
            return
        p = self._imaging_params

        # --- frame timing (Hz -> period in ms) ---
        frame_period_ms = 1000.0 / max(1.0, p["frame_rate"])
        self._frame_phase_ms += dt_ms
        new_frame = False
        while self._frame_phase_ms >= frame_period_ms:
            self._frame_phase_ms -= frame_period_ms
            new_frame = True

        # compute per-neuron continuous state
        frame_fluo = [None] * N_NEURONS  # will hold only if new_frame

        for i in range(N_NEURONS):
            spike = self._detect_spike(self.VmData[i], self.Vm_buffers[i][-1])

            # calcium dynamics
            self.CalciumData[i] = self._update_calcium(self.CalciumData[i], spike, p, dt_ms)

            # saturation from calcium (0..1)
            Sat_inf = self._hill_saturation(self.CalciumData[i], p)

            # indicator kinetics on saturation
            self.IndicatorSat[i] = self._update_indicator_sat(
                self.IndicatorSat[i], Sat_inf, dt_ms, self.tau_rise, self.tau_decay
            )

            # only sample fluorescence on frames
            if new_frame:
                frame_fluo[i] = self._sat_to_fluorescence(self.IndicatorSat[i], p, self.dff_max)

         # commit the frame (timestamped) observation
        if new_frame:
            t_frame_ms = self._t_last_ms - self._frame_phase_ms
            self.FrameTime_buffer.append(t_frame_ms)
            for i in range(N_NEURONS):
                self.FluoData[i] = frame_fluo[i]  # update displayed “last observed”
                self.Fluo_frame_buffers[i].append(frame_fluo[i])  # store discrete camera samples
        # else: FluoData remains held automatically



    def _detect_spike(self, vm_now, vm_prev):
        """Threshold‑crossing spike detection."""
        return 1 if (vm_now >= self.SpikeThreshold and vm_prev < self.SpikeThreshold) else 0


    def _update_calcium(self, C, spike, p, dt_ms):
        """
            dt_ms is milliseconds.
            p["CalciumDecay"] is lambda in 1/ms.
            Noise is scaled with sqrt(dt_s) where dt_s is seconds.
        """
        dt_ms = float(dt_ms)
        if (not np.isfinite(dt_ms)) or (dt_ms <= 0.0):
            dt_ms = SAMPLE_INTERVAL

        # 1) decay term: lambda (1/ms) * dt_ms (ms)  -> dimensionless
        lambda_ms = p["CalciumDecay"]  # 1/ms
        # Discrete-time exponential decay toward baseline
        decay = np.exp(-lambda_ms * dt_ms)

        # baseline relaxation
        Cb = p["CalciumBaseline"]
        C = C * decay + Cb * (1.0 - decay)

        # Spike-driven increment
        C += p["SpikeRise"] * spike

        # 2) noise term: convert once to seconds for sqrt(Δ)
        dt_s = dt_ms / 1000.0
        C += p["NoiseScale"] * np.sqrt(dt_s) * np.random.normal()
        return max(C, 0.0)


    def _hill_saturation(self, C, p):
        n = p["HillCoef"]
        Kd = p["DissociationConstant"]  # µM
        Ca_n = C ** n
        Kd_n = Kd ** n
        denom = Ca_n + Kd_n
        return Ca_n / denom if denom > 0 else 0.0


    def _update_indicator_sat(self, Sat_prev, Sat_inf, dt_ms, tau_rise_ms, tau_decay_ms):
        # piecewise time constant: different rise vs decay
        tau = tau_rise_ms if Sat_inf > Sat_prev else tau_decay_ms
        tau = max(1e-6, float(tau))
        a = 1.0 - np.exp(-float(dt_ms) / tau)
        return Sat_prev + a * (Sat_inf - Sat_prev)


    def _sat_to_fluorescence(self, Sat, p, dff_max):
        """
        Realistic mapping:
           - Sat in [0..1]
           - mean fluorescence uses ΔF/F0 scaling (dynamic range)
           - noise added only at frame times
           """
        gain = p["Laser"] * p["PMT"] * p["FluoScale"]
        offset = p["FluoOffset"]

        # mean fluorescence: F = F0*(1 + dff_max*Sat)
        F_mean = offset + gain * (1.0 + dff_max * Sat)

        sigma_floor = p.get("FluoNoiseSigma", 0.0)
        sigma_shot = np.sqrt(max(0.0, p["PhotoShotNoise"] * max(F_mean, 0.0)))
        sigma = np.sqrt(sigma_floor ** 2 + sigma_shot ** 2)
        return F_mean + sigma * np.random.normal()


    def _update_F0_from_baseline(self) -> None:
        """
        Recompute F0 from the CURRENT baseline calcium and CURRENT gain/offset.
        We do NOT include noise in F0.
        """
        if not self._imaging_params:
            return
        p = self._imaging_params

        Cb = float(p.get("CalciumBaseline", 0.1))
        Sat0 = self._hill_saturation(Cb, p)

        gain = float(p.get("Laser", 1.0)) * float(p.get("PMT", 1.0)) * float(p.get("FluoScale", 1.0))
        offset = float(p.get("FluoOffset", 0.0))

        # expected baseline fluorescence (no noise)
        F0 = offset + gain * (1.0 + float(self.dff_max) * Sat0)

        # one value per neuron (same baseline model for now)
        self.F0[:] = F0

    def ActivateDf(self, checked=None) -> None:
        """
        Toggle ΔF/F0 plotting for fluorescence curves.
        Works with either:
          - a direct call ActivateDf()
          - a Qt signal passing checked(bool): toggled.connect(ActivateDf)
        """
        if checked is None:
            s = self.sender()
            if s is not None and hasattr(s, "isChecked"):
                checked = s.isChecked()
            else:
                # fallback: just toggle
                checked = not getattr(self, "use_dff", False)

        self.use_dff = bool(checked)

        if self.use_dff:
            # define F0 at toggle time so the mapping is stable and meaningful
            self._update_F0_from_baseline()
            # Optional: update axis label to match what you plot
            ax_left = self.ui.Imaging_Oscilloscope_widget.getPlotItem().getAxis("left")
            if self.use_dff:
                ax_left.setLabel("ΔF/F0", units="")
            else:
                ax_left.setLabel("Fluorescence", units="a.u.")

        # force immediate redraw
        if getattr(self, "_plots_ready", False):
            self._update_plots()

    # -------------------------------------------------------------------------
    # Buffers
    # -------------------------------------------------------------------------

    def _initialize_buffers(self):
        """Create rolling buffers for all plotted variables."""
        self._bufsize = int(TIME_WINDOW / SAMPLE_INTERVAL)

        self.Time_buffer = collections.deque([0.0] * self._bufsize, self._bufsize)

        self.Imagingx = (
            np.arange(self._bufsize) - (self._bufsize - 1)
        ) * SAMPLE_INTERVAL

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

        # --- Frame-sampled fluorescence buffers (for plotting like a camera) ---
        # Use slider max as a safe bound for how many frame samples fit in TIME_WINDOW
        max_fps = max(1, self.ui.Imaging_FrameRate_Slider.maximum())
        self._frame_bufsize = int(TIME_WINDOW * max_fps / 1000.0) + 10  # frames in window + margin

        self.FrameTime_buffer = collections.deque(maxlen=self._frame_bufsize)
        self.Fluo_frame_buffers = [
            collections.deque(maxlen=self._frame_bufsize) for _ in range(N_NEURONS)
        ]

        # Reset frame phase when (re)connecting
        self._frame_phase_ms = 0.0

    def _append_buffers(self, t_ms):
        self.Time_buffer.append(t_ms)
        self.Stim_buffer.append(self.StimData)
        self.Trigger_buffer.append(self.TriggerData)
        for i in range(N_NEURONS):
            self.Calcium_buffers[i].append(self.CalciumData[i])
            self.Fluo_buffers[i].append(self.FluoData[i])
            self.Vm_buffers[i].append(self.VmData[i])

    # -------------------------------------------------------------------------
    # Plotting
    # -------------------------------------------------------------------------

    def _initialize_plot(self):
        """
        Stable multi-axis setup without re-layout of PlotItem internals.

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

        # ---- Ensure built-in axes are visible and labelled ----
        pi.showAxis("right")  # IMPORTANT: right axis is hidden by default
        ax_left = pi.getAxis("left")
        ax_right = pi.getAxis("right")
        ax_bottom = pi.getAxis("bottom")

        ax_bottom.enableAutoSIPrefix(False)
        ax_bottom.setLabel("Time", units="ms")

        # Left axis label depends on ΔF/F0 toggle
        if getattr(self, "use_dff", False):
            ax_left.setLabel("ΔF/F0", units="")
        else:
            ax_left.setLabel("Fluorescence", units="a.u.")

        ax_right.setLabel("Stimulus / Vm", units="a.u. / mV")

        # ---- Main ViewBox (fluorescence) ----
        vb = pi.getViewBox()
        vb.enableAutoRange(axis=pg.ViewBox.XAxis, enable=False)
        vb.setXRange(-TIME_WINDOW_DISPLAY, 0, padding=0)
        vb.setLimits(xMin=-TIME_WINDOW, xMax=0)
        vb.enableAutoRange(axis=pg.ViewBox.YAxis, enable=True)
        vb.setMouseEnabled(x=True, y=False)

        # ---- Remove any previously-added extra axis / viewboxes (important on reconnect) ----
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

        # ---- Secondary ViewBox on built-in RIGHT axis (Vm + Stim) ----
        self.secondaryVB = pg.ViewBox()
        self.secondaryVB.setXLink(vb)
        pw.scene().addItem(self.secondaryVB)
        ax_right.linkToView(self.secondaryVB)
        self.secondaryVB.setRange(yRange=[STIM_MIN, STIM_MAX])

        # ---- Extra RIGHT axis for Calcium (new column), with its own ViewBox ----
        self.calciumAxis = pg.AxisItem("right")
        self.calciumAxis.setLabel("Calcium", units="µM")

        # Put it to the right of the built-in right axis.
        # Default plot layout uses row=2 for Y axes; col=2 is built-in right axis.
        # We add our extra axis at col=3.
        pi.layout.addItem(self.calciumAxis, 2, 3)

        self.calciumVB = pg.ViewBox()
        self.calciumVB.setXLink(vb)
        pw.scene().addItem(self.calciumVB)
        self.calciumAxis.linkToView(self.calciumVB)
        self.calciumVB.enableAutoRange(axis=pg.ViewBox.YAxis, enable=True)

        # ---- Keep added ViewBoxes aligned to the main ViewBox geometry ----
        def update_views():
            rect = vb.sceneBoundingRect()

            self.secondaryVB.setGeometry(rect)
            self.secondaryVB.linkedViewChanged(vb, self.secondaryVB.XAxis)

            self.calciumVB.setGeometry(rect)
            self.calciumVB.linkedViewChanged(vb, self.calciumVB.XAxis)

        vb.sigResized.connect(update_views)
        vb.sigRangeChanged.connect(lambda *_: update_views())
        update_views()

        # ---- Create curves ----
        x = self.Imagingx

        # Fluorescence curves go to the MAIN PlotItem (vb)
        self.Fluocurve1 = pw.plot(
            x, np.zeros_like(x),
            pen=pg.mkPen(Settings.DarkSolarized[4], width=PEN_WIDTH, cosmetic=True)
        )
        self.Fluocurve2 = pw.plot(
            x, np.zeros_like(x),
            pen=pg.mkPen([0, 255, 133], width=PEN_WIDTH, cosmetic=True)
        )
        self.Fluocurve3 = pw.plot(
            x, np.zeros_like(x),
            pen=pg.mkPen([133, 255, 0], width=PEN_WIDTH, cosmetic=True)
        )

        # Calcium curves go to calciumVB (extra right axis)
        self.Calciumcurve1 = pg.PlotCurveItem(
            x, np.zeros_like(x),
            pen=pg.mkPen(Settings.DarkSolarized[10], width=PEN_WIDTH, cosmetic=True)
        )
        self.Calciumcurve2 = pg.PlotCurveItem(
            x, np.zeros_like(x),
            pen=pg.mkPen(Settings.DarkSolarized[9], width=PEN_WIDTH, cosmetic=True)
        )
        self.Calciumcurve3 = pg.PlotCurveItem(
            x, np.zeros_like(x),
            pen=pg.mkPen(Settings.DarkSolarized[7], width=PEN_WIDTH, cosmetic=True)
        )
        self.calciumVB.addItem(self.Calciumcurve1)
        self.calciumVB.addItem(self.Calciumcurve2)
        self.calciumVB.addItem(self.Calciumcurve3)

        # Vm curves go to secondaryVB (built-in right axis)
        self.Vmcurve1 = pg.PlotCurveItem(
            x, np.zeros_like(x),
            pen=pg.mkPen(Settings.DarkSolarized[3], width=PEN_WIDTH, cosmetic=True)
        )
        self.Vmcurve2 = pg.PlotCurveItem(
            x, np.zeros_like(x),
            pen=pg.mkPen(Settings.DarkSolarized[6], width=PEN_WIDTH, cosmetic=True)
        )
        self.Vmcurve3 = pg.PlotCurveItem(
            x, np.zeros_like(x),
            pen=pg.mkPen(Settings.DarkSolarized[8], width=PEN_WIDTH, cosmetic=True)
        )
        self.secondaryVB.addItem(self.Vmcurve1)
        self.secondaryVB.addItem(self.Vmcurve2)
        self.secondaryVB.addItem(self.Vmcurve3)

        # Stim curve also on secondaryVB
        self.Stimcurve = pg.PlotCurveItem(
            x, np.zeros_like(x),
            pen=pg.mkPen(Settings.DarkSolarized[5], width=PEN_WIDTH, cosmetic=True)
        )
        self.secondaryVB.addItem(self.Stimcurve)

        self._plots_ready = True

    def _update_plots(self):
        """
        Update all plot curves based on checkbox visibility.
        Buffers → numpy arrays → PyQtGraph curves.
        """

        ui = self.ui
        t_arr = np.asarray(self.Time_buffer, dtype=float)
        x = t_arr - t_arr[-1]  # last point at 0 ms, older negative

        # --- Calcium ---
        calcium_checks = [
            ui.Imaging_Calcium1_Checkbox,
            ui.Imaging_Calcium2_Checkbox,
            ui.Imaging_Calcium3_Checkbox,
        ]

        calcium_curves = [
            self.Calciumcurve1,
            self.Calciumcurve2,
            self.Calciumcurve3,
        ]

        for i in range(N_NEURONS):
            visible = calcium_checks[i].isChecked()
            calcium_curves[i].setVisible(visible)
            if visible:
                calcium_curves[i].setData(x, list(self.Calcium_buffers[i]))

        # --- Fluorescence ---
        fluo_checks = [
            ui.Imaging_Fluorescence1_Checkbox,
            ui.Imaging_Fluorescence2_Checkbox,
            ui.Imaging_Fluorescence3_Checkbox,
        ]

        fluo_curves = [
            self.Fluocurve1,
            self.Fluocurve2,
            self.Fluocurve3,
        ]

        for i in range(N_NEURONS):
            visible = fluo_checks[i].isChecked()
            fluo_curves[i].setVisible(visible)
            if not visible:
                continue

            y = np.asarray(self.Fluo_buffers[i], dtype=float)

            if self.use_dff:
                # Offset-correct ΔF/F0 (more realistic and avoids tiny DFF when offset is large)
                offset = float(self._imaging_params.get("FluoOffset", 0.0))

                y_sig = y - offset
                f0_sig = float(self.F0[i]) - offset
                f0_sig = max(1e-12, f0_sig)  # avoid divide by zero

                y = (y_sig - f0_sig) / f0_sig

            fluo_curves[i].setData(x, y)

        # --- Vm ---
        vm_checks = [
            ui.Imaging_Vm1_Checkbox,
            ui.Imaging_Vm2_Checkbox,
            ui.Imaging_Vm3_Checkbox,
        ]

        vm_curves = [
            self.Vmcurve1,
            self.Vmcurve2,
            self.Vmcurve3,
        ]

        for i in range(N_NEURONS):
            visible = vm_checks[i].isChecked()
            vm_curves[i].setVisible(visible)
            if visible:
                vm_curves[i].setData(x, list(self.Vm_buffers[i]))

        # --- Stimulus ---
        visible = ui.Imaging_Stimulus_Checkbox.isChecked()
        self.Stimcurve.setVisible(visible)
        if visible:
            self.Stimcurve.setData(x, list(self.Stim_buffer))


    # -------------------------------------------------------------------------
    # Recording
    # -------------------------------------------------------------------------

    def _handle_recording(self):
        """Manage recording buffers and CSV export."""
        if not self.ui.Imaging_DataRecording_Record_pushButton.isChecked() and self.record_flag:
            self._export_csv()
            self.record_flag = False
            for row in self.imaging_data:
                row.clear()

        if self.ui.Imaging_DataRecording_Record_pushButton.isChecked():
            self.record_flag = True


    def _export_csv(self):
        """Write recorded imaging data to CSV."""
        t = np.arange(len(self.imaging_data[1])) * Decimal(str(SAMPLE_INTERVAL))
        df = pd.DataFrame({"Time (ms)": t})
        df.to_csv(f"{self.ui.Imaging_SelectedFolderLabel.text()}.csv", index=False)


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
            p["frame_rate"] = max(1, ui.Imaging_FrameRate_Slider.value())
            p["PMT"] = ui.Imaging_PMT_Slider.value() / 100.0
            p["Laser"] = ui.Imaging_Laser_Slider.value() / 100.0

            p["CalciumDecay"] = ui.Imaging_CalciumDecay_Slider.value() / 10000.0
            p["SpikeRise"] = ui.Imaging_CalciumJump_Slider.value() /100.0
            p["CalciumBaseline"] = ui.Imaging_CalciumBaseline_Slider.value() / 100.0
            p["NoiseScale"] = ui.Imaging_CalciumNoise_Slider.value() / 10.0

            p["FluoScale"] = ui.Imaging_FluoScale_Slider.value() / 10.0
            p["FluoOffset"] = ui.Imaging_FluoOffset_Slider.value()
            p["FluoNoiseSigma"] = ui.Imaging_FluoNoise_Slider.value() / 5000.0
            p["HillCoef"] = ui.Imaging_Hill_Slider.value() / 100.0
            p["PhotoShotNoise"] = ui.Imaging_PhotoShotNoise_Slider.value() / 1e6
            p["DissociationConstant"] = ui.Imaging_kd_Slider.value() / 10.0

            if getattr(self, "use_dff", False):
                self._update_F0_from_baseline()

        # Initial cache
        update()

        # Explicit slider connections (Ui_Spikeling is not a QObject!)
        sliders = [
            ui.Imaging_FrameRate_Slider,
            ui.Imaging_PMT_Slider,
            ui.Imaging_Laser_Slider,
            ui.Imaging_CalciumDecay_Slider,
            ui.Imaging_CalciumJump_Slider,
            ui.Imaging_CalciumBaseline_Slider,
            ui.Imaging_CalciumNoise_Slider,
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
        if getattr(self, "calciumVB", None):
            self.calciumVB.setParentItem(None)
            self.calciumVB = None
        self.calciumAxis = None

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

