
########################################################################
#                          Libraries import                            #

from __future__ import annotations
from dataclasses import dataclass
from PySide6.QtCore import QSignalBlocker


from spikeling_gui.widgets.recording import prepare_recording, recording_path, style_recording_button
from spikeling_gui.appearance.dialogs import show_popup
from spikeling_gui.widgets.sliders import SliderBinding

from .recording_schema import SUFFIX

LEGACY_RECORDING_INDEX = 0

@dataclass(frozen=True)
class SliderReadout:
    """
    Declarative binding between a parameter slider, its toggle and its readout.

    Attributes
    ----------
    slider, toggle, readout : str
        Widget attribute names on the generated UI object.
    reset_value : int
        Raw default restored when the slider is disabled.
    display_scale : float
        Multiplier converting the raw slider value to the displayed quantity.
    """

    slider: str
    toggle: str
    readout: str
    reset_value: int
    display_scale: float


EXTRACELLULAR_CONTROLS = {
    "spread": SliderReadout(
        "ExtraCellular_Spread_Slider", "ExtraCellular_Spread_toggleButton",
        "ExtraCellular_Spread_Readings", reset_value=12, display_scale=0.1),
    "baseline_noise": SliderReadout(
        "ExtraCellular_BaselineNoise_Slider", "ExtraCellular_BaselineNoise_toggleButton",
        "ExtraCellular_BaselineNoise_Readings", reset_value=2, display_scale=1.0),
    "shared_noise": SliderReadout(
        "ExtraCellular_SharedNoise_Slider", "ExtraCellular_SharedNoise_toggleButton",
        "ExtraCellular_SharedNoise_Readings", reset_value=2, display_scale=1.0),
    "hum_noise": SliderReadout(
        "ExtraCellular_HumNoise_Slider", "ExtraCellular_HumNoise_toggleButton",
        "ExtraCellular_HumNoise_Readings", reset_value=0, display_scale=1.0),
}


class Scope():

    def __init__(self, parent):
        self.parent = parent
        self.ui = parent.ui


    # ------------------------------------------------------------------
    # Page selection
    # ------------------------------------------------------------------
    def ShowPage(self):
        self.ui.ExtraCellular_CAR_toggleButton.setToolTip(self.parent.tr(
            "Subtract the four-contact mean. Shared noise and shared neuronal signal can cancel; identical contacts become zero. The neuron continues to run."))
        self.ui.ExtraCellular_AutoRange_pushButton.setToolTip(self.parent.tr(
            "Fit the current visible interval using one voltage scale for all four contacts. Refit after changing CAR. Reset restores the standard range."))
        self.ui.Extracellular_Tetrode_Threshold_checkBox.setToolTip(self.parent.tr(
            "Show the fixed negative threshold on the processed trace. A crossing is a candidate event."))
        self.ui.mainbody_stackedWidget.setCurrentWidget(self.ui.page_ExtraCellular_Scope)


    # ------------------------------------------------------------------
    # Source selection: hardware vs emulator
    # ------------------------------------------------------------------
    def UpdateSource(self) -> None:
        """Apply a source change at a recording boundary."""
        extracellular_graph = getattr(self.parent, "extracellular_graph", None)
        if extracellular_graph is None:
            print("UpdateSource: extracellular_graph not found on MainWindow")
            return

        # 0 -> Spikeling hardware, 1 -> Emulator
        mode = "emulator" if self.ui.ExtraCellular_Source_comboBox.currentIndex() == 1 else "spikeling"
        extracellular_graph.set_source_mode(mode)

    def ToggleConnection(self, checked: bool | None = None) -> None:
        """
        Start or stop the extracellular pipeline from the connect button.

        The current source selection is applied first, so a session always
        begins in the mode shown by the combobox.

        Parameters
        ----------
        checked : bool, optional
            State supplied by ``QAbstractButton.toggled``. When omitted the
            button is queried directly, which allows programmatic calls.
        """
        extracellular_graph = getattr(self.parent, "extracellular_graph", None)
        if extracellular_graph is None:
            print("ToggleConnection: extracellular_graph not found on MainWindow")
            return

        if checked is None:
            checked = self.ui.ExtraCellular_ConnectButton.isChecked()

        self.UpdateSource()

        if checked:
            extracellular_graph.connect()
        else:
            extracellular_graph.disconnect()

    def apply_tetrode_geometry(self, payload: dict) -> None:
        eg = getattr(self.parent, "extracellular_graph", None) or getattr(self.parent, "ExtracellularGraph", None)
        if eg is None:
            print("apply_tetrode_geometry: extracellular_graph not found on MainWindow")
            return

        if eg.apply_tetrode_geometry(payload):
            self.tetrode_geometry = payload

    # ------------------------------------------------------------------
    # Data Recording Functions
    # ------------------------------------------------------------------            self.RecordFolderText()
    def RecordButton(self):
        graph = self.parent.extracellular_graph
        self.refresh_recording()
        if graph.recording_active:
            graph.stop_recording()
            return

        filename = self.ui.ExtraCellular_DataRecording_RecordFolder_value.text()
        if graph.recording_state == "error":
            if filename == self._recording_filename:
                graph.stop_recording(retry=True)
                return
            path = prepare_recording(self.parent, filename, ("_meta.json",))
            if path is not None:
                self._recording_filename = filename
                graph.stop_recording(retry=True, path=path)
            return

        generation = graph.source_generation
        if not graph.source_ready():
            self._show_source_required()
            return
        use_session = self.ui.ExtraCellular_RecordingFormat_comboBox.currentIndex() != LEGACY_RECORDING_INDEX
        if use_session:
            try:
                name = filename.strip()
                if name.lower().endswith(SUFFIX):
                    name = name[:-len(SUFFIX)]
                path = recording_path(name).with_suffix(SUFFIX)
                if path.exists() or path.is_symlink():
                    raise FileExistsError(self.parent.tr("Session already exists. Choose a new filename."))
            except (OSError, ValueError) as error:
                show_popup(self.parent, Title=self.parent.tr("Cannot start recording"), Text=str(error))
                return
        else:
            path = prepare_recording(self.parent, filename, ("_meta.json",))
        if path is None:
            return
        if graph.source_generation != generation or not graph.source_ready():
            self._show_source_required()
            return
        try:
            start = graph.start_session_recording if use_session else graph.start_recording
            if start(path):
                self._recording_filename = filename
        except OSError as error:
            show_popup(self.parent, Title=self.parent.tr("Cannot start recording"), Text=str(error))

    def _show_source_required(self):
        show_popup(
            self.parent, Title=self.parent.tr("Extracellular source unavailable"),
            Text=self.parent.tr("Connect the Scope and start the selected hardware or emulator source."),
        )

    def refresh_acquisition_status(self):
        graph = self.parent.extracellular_graph
        button = self.ui.ExtraCellular_ConnectButton
        tr = self.parent.tr
        if graph.acquisition is None:
            message = summary = tr("Acquisition stopped")
        else:
            if graph.acquisition.source == "spikeling":
                summary = tr("Nominal model time")
                message = tr("Nominal model time. Board packet continuity is unknown.")
                if graph._input_adapter.local_losses:
                    message += " " + tr("Local rows lost: %1").replace("%1", str(graph._input_adapter.local_losses))
            else:
                summary = tr("Emulator model time")
                message = tr("Emulator model time, independent of playback speed.")
            if graph.input_stalled:
                status = tr("Stalled")
            elif graph.latest_block is None:
                status = tr("Waiting")
            else:
                status = tr("Receiving")
            summary += " · " + status
            message += " " + status
            if graph.last_discontinuity is not None:
                message += " " + tr(graph.last_discontinuity.reason)
        if button.toolTip() != message:
            self.ui.ExtraCellular_AcquisitionStatus_label.setText(summary)
            button.setToolTip(message)
            button.setAccessibleDescription(message)

    def refresh_recording(self):
        graph = self.parent.extracellular_graph
        state = graph.recording_state
        locked = graph.recording_active or state == "saving"
        scientific_locked = locked and graph.session_recording.writer is None
        self.ui.ExtraCellular_RecordingFormat_comboBox.setEnabled(not locked and state != "error")
        tr = self.parent.tr
        button = self.ui.ExtraCellular_DataRecording_Record_pushButton
        button.setChecked(graph.recording_active)
        button.setEnabled(state != "saving")
        label = {"armed": tr("Stop recording"), "recording": tr("Stop recording"),
                 "saving": tr("Saving…"), "error": tr("Retry save")}.get(state, tr("Save recording"))
        button.setText(label)
        style_recording_button(button, graph.recording_active)

        filename = self.ui.ExtraCellular_DataRecording_Record_label_2
        path = graph.recording_path
        show_filename = path is not None and state not in ("idle", "empty")
        filename.setText(path.name if show_filename else "")
        filename.setToolTip(str(path) if show_filename else "")

        status = self.ui.ExtraCellular_SelectedFolderLabel
        status.setText({
            "armed": tr("Armed · waiting for samples"),
            "recording": tr("Recording"),
            "saving": tr("Finalising session…") if graph.session_recording.writer else tr("Saving recording…"),
            "saved": tr("Saved") + " · " + graph.recording_detail,
            "empty": tr("Stopped · no samples recorded"),
            "error": tr("Save failed · samples retained"),
            "session_failed": tr("Session failed · see details"),
        }.get(state, tr("Ready to record")))
        reason = graph.recording_stop_reason
        if reason in ("Hardware disconnected", "Emulator stopped"):
            interruption = {
                "Hardware disconnected": tr("Hardware disconnected"),
                "Emulator stopped": tr("Emulator stopped"),
            }[reason]
            status.setText(interruption + " · " + status.text())
        status.setToolTip(graph.recording_detail)
        button.setToolTip(
            tr("Correct the destination or enter another filename, then retry saving.")
            + "\n" + graph.recording_detail if state == "error" else
            graph.recording_detail if state == "session_failed" else ""
        )

        for widget in (
            self.ui.ExtraCellular_DataRecording_RecordFolder_value,
            self.ui.ExtraCellular_DataRecording_RecordFolderDir_pushButton,
        ):
            widget.setEnabled(not locked)
        for widget in (
            self.ui.ExtraCellular_SignalMode_toggleButton,
            self.ui.ExtraCellular_CAR_toggleButton,
            self.ui.ExtraCellular_HumPickup_comboBox,
            self.ui.ExtraCellular_Bandpass_comboBox,
            self.ui.ExtraCellular_Cutoffs_frame,
            self.ui.ExtraCellular_Threshold_edit,
            self.ui.ExtraCellular_Tetrode_pushButton,
            self.parent.tetrode_window,
        ):
            widget.setEnabled(not scientific_locked)
        for control in EXTRACELLULAR_CONTROLS.values():
            toggle = getattr(self.ui, control.toggle)
            toggle.setEnabled(not scientific_locked)
            editable = not scientific_locked and toggle.isChecked()
            getattr(self.ui, control.slider).setEnabled(editable)
            editor = getattr(self.ui, control.readout)
            with QSignalBlocker(editor):
                editor.setEnabled(editable)

    def _apply_signal_mode(self, mode: str) -> None:
        """
        mode:
          - "template"
          - "dvdt"
        """
        eg = getattr(self.parent, "extracellular_graph", None) or getattr(self.parent, "ExtracellularGraph", None)
        if eg is None:
            return

        # Prefer explicit API if present
        if hasattr(eg, "set_signal_mode"):
            eg.set_signal_mode(mode)
        else:
            # Fallback attribute
            eg.signal_mode = mode

            # Redraw if possible
            if hasattr(eg, "_update_plots"):
                eg._update_plots()
            elif hasattr(eg, "update"):
                eg.update()

        # Optional: update the toggle label so user knows what "ON" means
        # (keep if you like; otherwise remove)
        try:
            if mode == "dvdt":
                self.ui.ExtraCellular_Mode_Template_label.setStyleSheet("color: rgb(190, 205, 205); font-weight: normal;")
                self.ui.ExtraCellular_Mode_dVdT_label.setStyleSheet("color: rgb(42, 161, 152); font-weight: bold;")
            else:
                self.ui.ExtraCellular_Mode_Template_label.setStyleSheet("color: rgb(38, 139, 210); font-weight: bold;")
                self.ui.ExtraCellular_Mode_dVdT_label.setStyleSheet("color: rgb(190, 205, 205); font-weight: normal;")
        except Exception:
            pass

    def SignalMode_toggleButton(self, checked: bool):
        """
        Single toggle mapping:
          checked   -> dV/dT
          unchecked -> Template
        """

        mode = "dvdt" if checked else "template"
        self._apply_signal_mode(mode)


    # ------------------------------------------------------------------
    # Electrode Parameters
    # ------------------------------------------------------------------
    def bind_sliders(self):
        self.slider_bindings = {}
        for key, control in EXTRACELLULAR_CONTROLS.items():
            toggle = getattr(self.ui, control.toggle)
            editor = getattr(self.ui, control.readout)
            scale = control.display_scale
            default = f"{control.reset_value * scale:g}"
            binding = SliderBinding(
                slider=getattr(self.ui, control.slider),
                editor=editor,
                active=toggle.isChecked(),
                default_position=control.reset_value,
                disabled_text=self.parent.tr("Default %1").replace("%1", default),
                disabled_editor_style=editor.styleSheet(),
                to_display=lambda value, scale=scale: value * scale,
                to_slider=lambda value, scale=scale: value / scale,
                interval_ms=0,
            )
            toggle.toggled.connect(binding.set_active)
            self.slider_bindings[key] = binding
