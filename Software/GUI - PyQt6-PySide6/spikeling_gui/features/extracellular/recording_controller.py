"""Qt lifecycle adapter for the extracellular session writer."""
from dataclasses import replace
from uuid import uuid4

from PySide6.QtCore import QObject, QTimer

from .acquisition import Capture
from .session_writer import SessionWriter


class SessionRecordingController(QObject):
    def __init__(self, graph):
        super().__init__(graph)
        self.graph = graph
        self.writer = None
        self.close_requested = False
        self.timer = QTimer(self, interval=50)
        self.timer.timeout.connect(self.poll)

    def start(self, path):
        graph = self.graph
        capture = Capture(uuid4(), graph.acquisition, graph._next_index)
        self.writer = SessionWriter(path, capture, start_context={
            "filter_sos": None if graph._filter_sos is None else graph._filter_sos.tolist(),
            "filter_zi": None if graph._filter_zi_block is None else graph._filter_zi_block.tolist(),
            "previous_group": graph._group_id,
            "last_group_time_ms": graph._last_event_ms,
            "last_contact_crossing_ms": graph._t_last_detect_ms.tolist(),
            "previous_contact_uV": graph._prev_channel_sample.tolist(),
            "prime_detector": graph._prime_detector,
            "warmup_rows": graph._warmup_rows,
        })
        graph.recording_path = path
        graph.recording_stop_reason = ""
        graph.capture = capture
        graph._set_recording_state("armed")
        self.timer.start()

    def offer(self, item):
        if self.writer is None:
            return
        if self.writer.offer(item):
            if self.graph.recording_state == "armed" and self.writer.accepted_end > self.writer.capture.first_index:
                self.graph._set_recording_state("recording")
            if self.writer.accepted_end > self.writer.capture.first_index:
                self.graph.capture = replace(self.graph.capture, end_index=self.writer.accepted_end)
        elif self.graph.recording_active:
            self.graph._set_recording_state("saving", self.writer.error)

    def stop(self, reason):
        if self.writer is None:
            return
        self.writer.stop(reason)
        if self.graph.recording_active:
            self.graph.recording_stop_reason = reason
            self.graph.capture = replace(self.graph.capture, stop_reason=reason)
            self.graph._set_recording_state("saving")

    def defer_close(self):
        """Keep the Qt loop alive until asynchronous finalisation has finished."""
        if self.writer is None:
            return False
        self.close_requested = True
        self.graph.disconnect(self.graph.tr("Window closed"))
        return True

    def poll(self):
        writer = self.writer
        if writer is None or writer.status not in ("complete", "failed") or not writer.wait(0):
            return
        self.timer.stop()
        self.writer = None
        count = writer.committed_end - writer.capture.first_index
        if writer.status == "complete":
            detail = self.graph.tr("%1 samples").replace("%1", f"{count:,}")
            if writer.error:
                detail += "\n" + writer.error
            self.graph._set_recording_state("saved", detail)
        else:
            detail = self.graph.tr("Committed rows: %1").replace("%1", f"{count:,}")
            destination = f"\n{writer.partial}" if writer.partial.exists() else ""
            self.graph._set_recording_state("session_failed", f"{writer.error}\n{detail}{destination}")
        if self.close_requested:
            self.close_requested = False
            if writer.status == "complete":
                QTimer.singleShot(0, self.graph.parent.close)
            else:
                self.graph.parent.extracellular_page.ShowPage()
