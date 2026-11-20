"""Spikeling tutorials: Phase 2A action-aware, scientifically careful guidance.

No tutorial starts, stops or modifies scientific experiments. Qt changes here
are limited to tutorial widgets and, at the user's request, page navigation.
Hardware actions are self-reported unless a genuinely observable signal exists.
"""
from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, Qt, QTimer
from PySide6.QtGui import QPainter, QPen
from PySide6.QtWidgets import QApplication, QDialog, QListWidgetItem, QMessageBox, QSizeGrip, QHBoxLayout, QWidget

from spikeling_gui.appearance.theme_manager import theme_manager
from spikeling_gui.features.tutorials.catalogue import TUTORIALS, get_tutorial
from spikeling_gui.features.tutorials.observations import (
    RecordingEvidence, SpikeEvidence, response_is_substantive,
)
from spikeling_gui.features.tutorials.progress import TutorialProgress
from spikeling_gui.features.tutorials.targets import WidgetTargetResolver
from spikeling_gui.hardware.connection_supervisor import ConnectionState
from spikeling_gui.hardware.serial_manager import serial_manager
from spikeling_gui.ui.generated.UI_TutorialCatalogue import Ui_TutorialCatalogue
from spikeling_gui.ui.generated.UI_TutorialPanel import Ui_TutorialPanel


class TargetHighlight(QWidget):
    """A visually unobtrusive, mouse-transparent outline around a live control."""

    def __init__(self, target: QWidget):
        super().__init__(target)
        self._target = target
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        target.installEventFilter(self)
        self.setGeometry(target.rect())
        self.show()
        self.raise_()

    @property
    def target(self):
        return self._target

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(self.palette().highlight().color(), 2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(self.rect().adjusted(2, 2, -3, -3), 5, 5)

    def eventFilter(self, watched, event):
        if watched is self._target:
            if event.type() in (QEvent.Type.Resize, QEvent.Type.Move):
                self.setGeometry(self._target.rect())
            elif event.type() == QEvent.Type.PaletteChange:
                self.update()
        return False

    def detach(self):
        if self._target is not None:
            try:
                self._target.removeEventFilter(self)
            except RuntimeError:
                pass  # Target was deleted during page rebuilding.
            self._target = None
        self.hide()
        self.deleteLater()


class TutorialController(QObject):
    """Owns the tutorial UI; reads existing Spikeling state via narrow adapters."""

    def __init__(self, host):
        super().__init__(host)
        self.host = host
        self.progress = TutorialProgress()
        self.targets = WidgetTargetResolver(host)
        self._previous_page = host.ui.mainbody_stackedWidget.currentWidget()
        self._active = None
        self._step_index = 0
        self._done_steps = set()
        self._skipped_steps = set()
        self._evidence_kind = {}
        self._highlight = None
        self._closing_completed = False
        self._populating_response = False
        self._spike_evidence = SpikeEvidence()
        self._recording_evidence = RecordingEvidence()
        self._sample_connected = False
        self._last_failure = ""

        self.catalogue_page = QWidget(host.ui.mainbody_stackedWidget)
        self.catalogue_ui = Ui_TutorialCatalogue()
        self.catalogue_ui.setupUi(self.catalogue_page)
        host.ui.mainbody_stackedWidget.addWidget(self.catalogue_page)

        self.panel = QDialog(host)
        # Match Spikeling's frameless window chrome; the header remains draggable.
        self.panel.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        self.panel.setWindowModality(Qt.WindowModality.NonModal)
        self.panel_ui = Ui_TutorialPanel()
        self.panel_ui.setupUi(self.panel)
        theme_manager.bind(window=self.panel)
        self._panel_drag_offset = None
        for drag_target in (self.panel_ui.headerCard, self.panel_ui.tutorialTitle,
                            self.panel_ui.stepCount):
            drag_target.installEventFilter(self)
        grip_layout = QHBoxLayout(self.panel_ui.resizeGripHost)
        grip_layout.setContentsMargins(0, 0, 0, 0)
        grip_layout.addWidget(QSizeGrip(self.panel_ui.resizeGripHost))
        self.panel_ui.titleCloseButton.clicked.connect(self.panel.reject)

        ui = self.catalogue_ui
        ui.searchEdit.textChanged.connect(self._populate_catalogue)
        ui.categoryButtons.buttonClicked.connect(self._populate_catalogue)
        ui.tutorialList.currentItemChanged.connect(self._selected_tutorial_changed)
        ui.tutorialList.itemDoubleClicked.connect(lambda *_: self.start_selected())
        ui.startButton.clicked.connect(self.start_selected)
        ui.closeButton.clicked.connect(self.close_catalogue)

        host.ui.NeuronTutorial_pushButton.clicked.connect(self.show_catalogue)
        host.ui.mainbody_stackedWidget.currentChanged.connect(self._context_changed)
        panel = self.panel_ui
        panel.hintButton.clicked.connect(self.show_hint)
        panel.verifyButton.clicked.connect(self.verify_step)
        panel.backButton.clicked.connect(self.go_back)
        panel.nextButton.clicked.connect(self.go_forward)
        panel.skipButton.clicked.connect(self.skip_step)
        panel.showControlButton.clicked.connect(self.show_relevant_control)
        panel.manualObservationButton.clicked.connect(self.confirm_visual_observation)
        panel.reflectionEdit.textChanged.connect(self._on_response_changed)
        panel.attestationCheck.toggled.connect(self._refresh_state)
        self.panel.finished.connect(self._panel_finished)

        # Poll only while a tutorial is visible. Never poll at model frequency.
        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(350)
        self._poll_timer.timeout.connect(self._poll_state)
        self._populate_catalogue()

    def eventFilter(self, watched, event):
        """Allow moving the non-modal guide by its custom header only."""
        if watched in (self.panel_ui.headerCard, self.panel_ui.tutorialTitle,
                       self.panel_ui.stepCount):
            if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
                self._panel_drag_offset = event.globalPosition().toPoint() - self.panel.frameGeometry().topLeft()
                return True
            if (event.type() == QEvent.Type.MouseMove and self._panel_drag_offset is not None
                    and event.buttons() & Qt.MouseButton.LeftButton):
                self.panel.move(event.globalPosition().toPoint() - self._panel_drag_offset)
                return True
            if event.type() == QEvent.Type.MouseButtonRelease and self._panel_drag_offset is not None:
                self._panel_drag_offset = None
                return True
        return super().eventFilter(watched, event)

    def show_catalogue(self):
        if self._active is not None and self.panel.isVisible():
            self.panel.reject()
        stack = self.host.ui.mainbody_stackedWidget
        if stack.currentWidget() is not self.catalogue_page:
            self._previous_page = stack.currentWidget()
        self._populate_catalogue()
        stack.setCurrentWidget(self.catalogue_page)
        self._remove_highlight()

    def close_catalogue(self):
        if self.host.ui.mainbody_stackedWidget.currentWidget() is self.catalogue_page:
            previous = self._previous_page
            if previous is not None and previous is not self.catalogue_page:
                self.host.ui.mainbody_stackedWidget.setCurrentWidget(previous)

    def _populate_catalogue(self, *_):
        ui = self.catalogue_ui
        selected = self._selected_id()
        term = ui.searchEdit.text().strip().casefold()
        category = ui.categoryButtons.checkedButton().property("tutorialModule")
        ui.tutorialList.blockSignals(True)
        ui.tutorialList.clear()
        for tutorial in TUTORIALS:
            if category and category != tutorial.module:
                continue
            if term not in (tutorial.title + " " + tutorial.description + " " + tutorial.id).casefold():
                continue
            check = "✓  " if self.progress.is_complete(tutorial.id) else ""
            item = QListWidgetItem(f"{check}{tutorial.title}  [{tutorial.id}]")
            item.setData(Qt.ItemDataRole.UserRole, tutorial.id)
            ui.tutorialList.addItem(item)
            if tutorial.id == selected:
                ui.tutorialList.setCurrentItem(item)
        ui.tutorialList.blockSignals(False)
        if ui.tutorialList.currentItem() is None and ui.tutorialList.count():
            ui.tutorialList.setCurrentRow(0)
        self._selected_tutorial_changed()

    def _selected_id(self):
        item = self.catalogue_ui.tutorialList.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _selected_tutorial_changed(self, *_):
        tutorial = get_tutorial(self._selected_id())
        ui = self.catalogue_ui
        if tutorial is None:
            ui.nameLabel.setText(self.tr("No tutorials match your search"))
            ui.descriptionText.clear()
            ui.metaLabel.clear()
            ui.statusLabel.clear()
            ui.startButton.setText(self.tr("Start tutorial"))
            ui.startButton.setEnabled(False)
            return
        ui.startButton.setEnabled(True)
        ui.nameLabel.setText(tutorial.title)
        ui.metaLabel.setText(
            f"{tutorial.module} · About {tutorial.duration_minutes} min · "
            + ("Physical board required" if tutorial.requires_hardware else "No board required")
        )
        ui.descriptionText.setPlainText(
            tutorial.description + "\n\n"
            "Perform real actions in the existing interface. Your predictions and "
            "observations are saved locally in tutorial preferences, not experimental data. "
            "The guide never changes scientific settings on your behalf."
        )
        saved = self.progress.get_resume()
        ui.statusLabel.setText(
            "Completed" if self.progress.is_complete(tutorial.id) else
            "Partially completed — progress available" if saved and saved[0] == tutorial.id else
            "Not yet completed"
        )
        ui.startButton.setText("Resume tutorial" if saved and saved[0] == tutorial.id else "Start tutorial")

    def _recording_active(self):
        graph = getattr(self.host, "spikeling_graph", None)
        imaging = getattr(self.host, "imaging_graph", None)
        return bool(
            (graph is not None and getattr(graph, "record_flag", False))
            or getattr(self.host, "recordflag", False)
            or (imaging is not None and getattr(imaging, "record_flag", False))
        )

    def start_selected(self):
        tutorial = get_tutorial(self._selected_id())
        if tutorial is None:
            return
        if self._recording_active():
            QMessageBox.information(
                self.host, "Recording in progress",
                "Stop and save the current recording before starting a tutorial. "
                "Experimental settings and data have not been changed.",
            )
            return
        page = getattr(self.host.ui, tutorial.page, None)
        if page is None:
            QMessageBox.warning(self.host, "Tutorial unavailable", "The required GUI page was not found.")
            return
        self._active = tutorial
        self._step_index = 0
        self._done_steps.clear()
        self._skipped_steps.clear()
        self._evidence_kind.clear()
        saved = self.progress.get_resume()
        if saved and saved[0] == tutorial.id:
            self._step_index = next((i for i, s in enumerate(tutorial.steps) if s.id == saved[1]), 0)
        self.host.ui.mainbody_stackedWidget.setCurrentWidget(page)
        self.panel_ui.tutorialTitle.setText(tutorial.title)
        self.panel.setWindowTitle(f"Spikeling tutorial — {tutorial.title}")
        self.panel.show()
        self.panel.raise_()
        self._position_panel()
        self._poll_timer.start()
        self._render_step()

    def _position_panel(self):
        """Open beside the application if there is room; do not move it thereafter."""
        screen = self.host.screen() or QApplication.primaryScreen()
        if screen is None:
            return
        available = screen.availableGeometry()
        outer = self.host.frameGeometry()
        x = outer.right() + 8
        if x + self.panel.width() > available.right():
            x = outer.right() - self.panel.width() - 12
        x = max(available.left(), min(x, available.right() - self.panel.width()))
        # Align the tutorial top border with the Spikeling window, not 55 px below it.
        # Keep screen-edge clamping for smaller desktops.
        y = max(available.top(), min(outer.top(), available.bottom() - self.panel.height()))
        self.panel.move(x, y)

    def _current_step(self):
        return self._active.steps[self._step_index] if self._active else None

    def _on_module_page(self):
        return bool(self._active and self.host.ui.mainbody_stackedWidget.currentWidget()
                    is getattr(self.host.ui, self._active.page, None))

    def _board_connected(self):
        graph = getattr(self.host, "spikeling_graph", None)
        supervisor = getattr(graph, "supervisor", None)
        return bool(supervisor and supervisor.state == ConnectionState.CONNECTED)

    def _cc_ready(self):
        ui = self.host.ui
        mode = getattr(ui, "PatchClampMode_toggleButton", None)
        override = getattr(ui, "PatchClamp_toggleButton", None)
        return bool(self._board_connected() and mode is not None and override is not None
                    and not mode.isChecked() and not override.isChecked())

    def _disconnect_sample_observer(self):
        if self._sample_connected:
            try:
                serial_manager.sample_received.disconnect(self._on_sample_received)
            except (TypeError, RuntimeError):
                pass
            self._sample_connected = False

    def _on_sample_received(self, values, _command_mv=None):
        # O(1) and attached only during the specific spike-observation step.
        if self._active is not None and self._on_module_page() and self._board_connected():
            self._spike_evidence.observe(values)

    def _render_step(self):
        self._disconnect_sample_observer()
        self._remove_highlight()
        step = self._current_step()
        if step is None:
            return
        self._spike_evidence = SpikeEvidence()
        self._recording_evidence = RecordingEvidence()
        self._last_failure = ""
        ui = self.panel_ui
        ui.stepCount.setText(f"Step {self._step_index + 1} of {len(self._active.steps)}")
        ui.progressBar.setValue(round(100 * self._step_index / len(self._active.steps)))
        ui.stepTitle.setText(step.title)
        ui.instructionText.setText(step.instruction)
        labels = {"predict": "Predict before observing", "observe": "Observe and describe evidence",
                  "explain": "Explain the experimental result"}
        ui.phaseLabel.setText(labels.get(step.response_kind, "Carry out the indicated task"))
        ui.reflectionPrompt.setText(step.prompt)
        ui.reflectionCard.setVisible(bool(step.prompt))
        ui.reflectionPrompt.setVisible(bool(step.prompt))
        ui.reflectionEdit.setVisible(bool(step.prompt))
        self._populating_response = True
        try:
            ui.reflectionEdit.setPlainText(self.progress.get_response(self._active.id, step.id))
        finally:
            self._populating_response = False
        ui.confirmationCard.setVisible(bool(step.confirmation))
        ui.attestationCheck.setVisible(bool(step.confirmation))
        ui.confirmationDetails.setText(step.confirmation)
        ui.attestationCheck.setText("I confirm I completed this action")
        ui.attestationCheck.setChecked(False)
        ui.hintLabel.setText(step.hint)
        ui.hintLabel.setVisible(False)
        ui.hintButton.setEnabled(bool(step.hint))
        ui.verifyButton.setText("Confirm this step" if step.completion == "manual" else "Check current state")
        ui.backButton.setEnabled(self._step_index > 0)
        ui.skipButton.setEnabled(True)
        ui.nextButton.setText("Finish" if self._step_index == len(self._active.steps) - 1 else "Continue")
        ui.manualObservationButton.setVisible(step.completion == "spike_seen")
        ui.manualObservationButton.setToolTip(
            "Manual confirmation is labelled as self-reported, never as an electronically detected spike."
        )
        if step.completion == "spike_seen":
            serial_manager.sample_received.connect(self._on_sample_received)
            self._sample_connected = True
        self.progress.save_resume(self._active.id, step.id)
        ui.stepScrollArea.verticalScrollBar().setValue(0)
        self._context_changed()

    def _remember_response(self):
        step = self._current_step()
        if step is not None and step.prompt:
            self.progress.save_response(self._active.id, step.id,
                                        self.panel_ui.reflectionEdit.toPlainText())

    def _on_response_changed(self):
        if self._populating_response or self._active is None:
            return
        step = self._current_step()
        if step and step.require_response and not response_is_substantive(
                self.panel_ui.reflectionEdit.toPlainText()):
            self._done_steps.discard(step.id)
        self._refresh_state()

    def _prerequisites_ready(self, step):
        if not self._on_module_page():
            return False
        # Do not let a disconnected board masquerade as a completed live
        # experiment. A previously saved recording remains an exception.
        if self._active.requires_hardware and step.completion != "recording_saved":
            if not self._board_connected():
                return False
            # After setup, CI-specific learning activities must remain in CC
            # with the physical potentiometer enabled. GUI state is not a
            # firmware acknowledgement, so the user must still observe Vm.
            if self._active.id == "NI-04" and self._step_index >= 3:
                return self._cc_ready()
        return True

    def _condition(self, step):
        kind = step.completion
        if kind == "manual":
            return True
        if kind == "board_connected":
            return self._board_connected()
        if kind == "vm_visible":
            widget = getattr(self.host.ui, "Spikeling_VmCheckbox", None)
            return bool(widget and widget.isChecked())
        if kind == "cc_ready":
            return self._cc_ready()
        if kind == "spike_seen":
            return self._spike_evidence.seen
        if kind == "recording_saved":
            return self._recording_evidence.saved
        if kind == "emulator_running":
            return bool(getattr(self.host.ui, "EmulatorConnectedFlag", False))
        if kind == "recording_loaded":
            return getattr(self.host, "analysis_recording", None) is not None
        return False

    def _user_requirements_met(self, step):
        if step.require_response and not response_is_substantive(
                self.panel_ui.reflectionEdit.toPlainText()):
            return False
        if step.confirmation and not self.panel_ui.attestationCheck.isChecked():
            return False
        return True

    def _poll_state(self):
        if self._active is None or not self.panel.isVisible():
            return
        step = self._current_step()
        if step.completion == "recording_saved":
            graph = getattr(self.host, "spikeling_graph", None)
            if graph is not None:
                status_label = getattr(self.host.ui, "Spikeling_DataRecording_Record_label", None)
                recording_mode = getattr(graph, "_recording_mode_at_start", None)
                recording_in_cc = bool(recording_mode is not None and not recording_mode[0])
                self._recording_evidence.observe(
                    active=bool(getattr(graph, "record_flag", False)) and recording_in_cc,
                    pending=bool(getattr(graph, "_recording_save_pending", False)),
                    path=getattr(graph, "_current_save_path", None),
                    label=status_label.text() if status_label is not None else "",
                )
        self._refresh_state()

    def _context_changed(self, *_):
        self._refresh_state()

    def _refresh_state(self, *_):
        if self._active is None or not self.panel.isVisible():
            self._remove_highlight()
            return
        step = self._current_step()
        ui = self.panel_ui
        self._update_highlight(step)
        active_page = self._on_module_page()
        available = self._prerequisites_ready(step)
        response_ready = self._user_requirements_met(step)
        condition_ready = self._condition(step) if available else False
        already_done = step.id in self._done_steps
        manual_step = step.completion == "manual"

        # Condition-based steps can become complete automatically, but this
        # never silently advances the tutorial or performs a scientific action.
        if available and condition_ready and response_ready and not manual_step:
            self._done_steps.add(step.id)
            self._skipped_steps.discard(step.id)
            self._evidence_kind.setdefault(step.id, "stream" if step.completion == "spike_seen"
                                           else "application_state")
            already_done = True
        ui.verifyButton.setEnabled(available and not already_done and
                                   response_ready and (manual_step or condition_ready))
        ui.nextButton.setEnabled(available and already_done and response_ready)
        ui.manualObservationButton.setEnabled(available and response_ready and not already_done)
        ui.manualObservationButton.setVisible(step.completion == "spike_seen" and not already_done)

        if not active_page:
            status = "You are on another page. Select Show relevant controls to return."
        elif self._active.requires_hardware and not self._board_connected() and step.completion != "recording_saved":
            status = "Board disconnected. Reconnect before confirming this step; no settings were changed."
        elif (self._active.id == "NI-04" and self._step_index >= 3
              and step.completion != "recording_saved" and not self._cc_ready()):
            status = "Return to CC and disable the GUI patch-clamp override before continuing."
        elif already_done:
            method = self._evidence_kind.get(step.id, "manual")
            status = (
                "Confirmed by your observation (not device-verified). Continue when ready."
                if method == "manual_observation" else
                "Application state or stream event observed. Continue when ready."
                if method != "manual" else
                "Your response/action is confirmed by you. Continue when ready."
            )
        elif not response_ready:
            status = "Write a short response and tick the confirmation box if shown."
        elif step.completion == "cc_ready" and not condition_ready:
            status = "Choose CC and turn OFF the GUI patch-clamp override; then centre the physical knob."
        elif step.completion == "spike_seen" and not condition_ready:
            status = "No spike detected in the stream since this step began. You may confirm a visible spike manually."
        elif step.completion == "recording_saved" and not condition_ready:
            status = "Start a new recording, stop it and wait for the file to be saved."
        elif not condition_ready:
            status = "Required state not yet detected. Check the relevant control."
        elif manual_step:
            status = "Perform the task and select Confirm this step. Physical actions are self-reported."
        else:
            status = "Required state observed. Select Check current state or Continue."
        if self._last_failure and not already_done:
            status = self._last_failure + " " + status
        ui.stateLabel.setText(status)

    def _update_highlight(self, step):
        ui = self.panel_ui
        if not self._on_module_page():
            self._remove_highlight()
            ui.targetLabel.setText("The active tutorial is on a different page.")
            ui.showControlButton.setVisible(True)
            ui.showControlButton.setText("Return to tutorial module")
            return
        target = self.targets.resolve(step.target)
        visible = self.targets.visible(step.target)
        if visible:
            if self._highlight is None or self._highlight.target is not target:
                self._remove_highlight()
                self._highlight = TargetHighlight(target)
            ui.targetLabel.setText("The relevant control is outlined in the live interface.")
        else:
            self._remove_highlight()
            ui.targetLabel.setText(
                "The relevant control is in a hidden parameters panel."
                if target is not None else
                "Follow the instructions in the live interface; this step has no specific target."
            )
        reveal = not visible and self.targets.can_reveal(step.panel)
        ui.showControlButton.setVisible(reveal)
        ui.showControlButton.setText("Show relevant controls")

    def _remove_highlight(self):
        if self._highlight is not None:
            self._highlight.detach()
            self._highlight = None

    def show_relevant_control(self):
        step = self._current_step()
        if step is None:
            return
        if not self._on_module_page():
            page = getattr(self.host.ui, self._active.page, None)
            if page is not None:
                self.host.ui.mainbody_stackedWidget.setCurrentWidget(page)
        if step.panel and not self.targets.visible(step.target):
            self.targets.reveal(step.panel)
        # Panel opening may animate; follow up once the layout settles.
        QTimer.singleShot(300, self._context_changed)

    def show_hint(self):
        step = self._current_step()
        if step and step.hint:
            self.panel_ui.hintLabel.setVisible(not self.panel_ui.hintLabel.isVisible())

    def verify_step(self):
        step = self._current_step()
        if step is None or not self._prerequisites_ready(step):
            return
        if not self._user_requirements_met(step):
            self._last_failure = "Complete the requested reflection and confirmation first."
        elif self._condition(step):
            self._done_steps.add(step.id)
            self._skipped_steps.discard(step.id)
            self._evidence_kind[step.id] = ("manual" if step.completion == "manual"
                                            else "stream" if step.completion == "spike_seen"
                                            else "application_state")
            self._last_failure = ""
            self._remember_response()
        else:
            self._last_failure = "The required condition has not been observed."
        self._refresh_state()

    def confirm_visual_observation(self):
        """Explicit fallback if stream sampling did not capture a visible spike."""
        step = self._current_step()
        if (step is None or step.completion != "spike_seen"
                or not self._prerequisites_ready(step) or not self._user_requirements_met(step)):
            return
        self._done_steps.add(step.id)
        self._skipped_steps.discard(step.id)
        self._evidence_kind[step.id] = "manual_observation"
        self._last_failure = ""
        self._remember_response()
        self._refresh_state()

    def go_back(self):
        if self._active is not None and self._step_index:
            self._remember_response()
            self._step_index -= 1
            self._render_step()

    def skip_step(self):
        step = self._current_step()
        if step is not None:
            self._remember_response()
            self._skipped_steps.add(step.id)
            self._done_steps.discard(step.id)
            self._advance()

    def go_forward(self):
        step = self._current_step()
        if (step and self._prerequisites_ready(step) and step.id in self._done_steps
                and self._user_requirements_met(step)):
            self._remember_response()
            self._advance()

    def _advance(self):
        if self._active is None:
            return
        if self._step_index + 1 < len(self._active.steps):
            self._step_index += 1
            self._render_step()
            return
        tutorial_id = self._active.id
        skipped = [s.id for s in self._active.steps if s.id in self._skipped_steps]
        if skipped:
            self.progress.save_resume(tutorial_id, skipped[0])
            QMessageBox.information(
                self.panel, "Tutorial not yet complete",
                "Some steps were skipped. Your tutorial remains unfinished; "
                "you can resume at the first skipped step later.",
            )
        else:
            self.progress.mark_complete(tutorial_id)
        self._closing_completed = True
        self.panel.accept()
        self.show_catalogue()
        self._closing_completed = False

    def _panel_finished(self, *_):
        if self._active is not None:
            self._remember_response()
        self._poll_timer.stop()
        self._disconnect_sample_observer()
        self._remove_highlight()
        self._active = None
        self._done_steps.clear()
        self._skipped_steps.clear()
        self._evidence_kind.clear()
        if not self._closing_completed:
            self._populate_catalogue()
