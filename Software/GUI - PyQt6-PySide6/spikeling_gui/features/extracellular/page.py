
########################################################################
#                          Libraries import                            #

from __future__ import annotations
from dataclasses import dataclass


from spikeling_gui.widgets.recording import prepare_recording
from spikeling_gui.appearance.dialogs import show_popup
from spikeling_gui.appearance.palette import DarkSolarized

@dataclass(frozen=True)
class SliderReadout:
    """
    Declarative binding between a parameter slider, its toggle and its readout.

    Attributes
    ----------
    slider, toggle, readout : str
        Widget attribute names on the generated UI object.
    reset_value : int
        Raw slider value restored when the toggle is switched off.
    display_scale : float
        Multiplier converting the raw slider value to the displayed quantity.
    colour_index : int
        Index into ``DarkSolarized`` for the readout text.
    """

    slider: str
    toggle: str
    readout: str
    reset_value: int
    display_scale: float
    colour_index: int


EXTRACELLULAR_CONTROLS = {
    "spread": SliderReadout(
        "ExtraCellular_Spread_Slider", "ExtraCellular_Spread_toggleButton",
        "ExtraCellular_Spread_Readings", reset_value=12, display_scale=0.1, colour_index=5),
    "baseline_noise": SliderReadout(
        "ExtraCellular_BaselineNoise_Slider", "ExtraCellular_BaselineNoise_toggleButton",
        "ExtraCellular_BaselineNoise_Readings", reset_value=5, display_scale=1.0, colour_index=4),
    "shared_noise": SliderReadout(
        "ExtraCellular_SharedNoise_Slider", "ExtraCellular_SharedNoise_toggleButton",
        "ExtraCellular_SharedNoise_Readings", reset_value=5, display_scale=1.0, colour_index=4),
    "hum_noise": SliderReadout(
        "ExtraCellular_HumNoise_Slider", "ExtraCellular_HumNoise_toggleButton",
        "ExtraCellular_HumNoise_Readings", reset_value=0, display_scale=1.0, colour_index=4),
}


class Scope():

    def __init__(self, parent):
        self.parent = parent
        self.ui = parent.ui

        # Local state flags (used by RecordButton gating)
        self.ExtraCellularConnectionFlag = False

    # ------------------------------------------------------------------
    # Page selection
    # ------------------------------------------------------------------
    def ShowPage(self):
        self.ui.mainbody_stackedWidget.setCurrentWidget(self.ui.page_ExtraCellular_Scope)


    # ------------------------------------------------------------------
    # Source selection: hardware vs emulator
    # ------------------------------------------------------------------
    def UpdateSource(self) -> None:
        """
        Push the source selection down to the graph.

        Only the data source is changed here. Re-running ``connect()`` on a
        combobox change would rebuild the four channel plots and clear the
        rolling buffers, discarding an in-flight recording.
        """
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
        self.tetrode_geometry = payload

        eg = getattr(self.parent, "extracellular_graph", None) or getattr(self.parent, "ExtracellularGraph", None)
        if eg is None:
            print("apply_tetrode_geometry: extracellular_graph not found on MainWindow")
            return

        if hasattr(eg, "apply_tetrode_geometry"):
            eg.apply_tetrode_geometry(payload)

    # ------------------------------------------------------------------
    # Data Recording Functions
    # ------------------------------------------------------------------            self.RecordFolderText()
    def RecordButton(self):
        button = self.ui.ExtraCellular_DataRecording_Record_pushButton
        if button.isChecked():
            if not getattr(self, 'ExtraCellularConnectionFlag', False):
                button.setChecked(False)
                show_popup(self.parent, Title="Spikeling not connected", Text="Connect to the hardware or GUI emulator data stream before recording.")
                return

            filename = self.ui.ExtraCellular_DataRecording_RecordFolder_value.text()
            path = prepare_recording(self.parent, filename, ("_meta.json",))
            if path is None:
                button.setChecked(False)
                return

            self.ui.ExtraCellular_recording_path = path
            button.setText("Stop Recording")
            button.setStyleSheet("color: rgb(250, 250, 250); background-color: rgb(50, 220, 47);")
        else:
            button.setText("Record")
            button.setStyleSheet("color: rgb(250, 250, 250); background-color: rgb(220, 50, 47);")

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
    def _refresh_readout(self, key: str) -> None:
        """
        Write the current slider value into its readout label.

        Parameters
        ----------
        key : str
            Entry in :data:`EXTRACELLULAR_CONTROLS`.
        """
        control = EXTRACELLULAR_CONTROLS[key]
        value = getattr(self.ui, control.slider).value() * control.display_scale
        text = f"{value:g}"

        label = getattr(self.ui, control.readout)
        label.setText(text)
        label.setStyleSheet(
            "color: rgb" + str(tuple(DarkSolarized[control.colour_index]))
            + "; font: 700 10pt;"
        )

    def _set_control_enabled(self, key: str) -> None:
        """
        Apply a toggle state to its slider and readout.

        Switching a control off restores the slider's reset value and blanks
        the readout, signalling that the parameter is no longer in play.

        Parameters
        ----------
        key : str
            Entry in :data:`EXTRACELLULAR_CONTROLS`.
        """
        control = EXTRACELLULAR_CONTROLS[key]
        slider = getattr(self.ui, control.slider)
        enabled = getattr(self.ui, control.toggle).isChecked()

        slider.setEnabled(enabled)
        if enabled:
            self._refresh_readout(key)
        else:
            slider.setValue(control.reset_value)
            getattr(self.ui, control.readout).setText("")

    # --- Thin wrappers preserving the names wired in the UI file ----------

    def ActivateSpatialFalloff(self): self._set_control_enabled("spread")
    def GetSpatialFalloff(self):      self._refresh_readout("spread")

    def ActivateBaselineNoise(self):  self._set_control_enabled("baseline_noise")
    def GetBaselineNoise(self):       self._refresh_readout("baseline_noise")

    def ActivateSharedNoise(self):    self._set_control_enabled("shared_noise")
    def GetSharedNoise(self):         self._refresh_readout("shared_noise")

    def ActivateHumNoise(self):       self._set_control_enabled("hum_noise")
    def GetHumNoise(self):            self._refresh_readout("hum_noise")
