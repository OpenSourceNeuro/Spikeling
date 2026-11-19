"""Bounded background writer for immutable Phase 1a acquisition blocks."""
from collections import deque
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from threading import Condition, Thread

import numpy as np

from spikeling_gui.version import __version__

from .acquisition import Discontinuity
from .session_reader import SessionReader
from .recording_schema import (
    EVENT_DATASETS, EVENT_STREAMS, FORMAT, MANIFEST, MAX_JSON, MAX_ROWS, STREAMS, SUFFIX, VERSION,
    atomic_file, canonical, data_name, decode, digest, publish_directory, record_name, require, sync_directory, write_json,
)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


class SessionWriter:
    """One owner thread handles I/O. The producer never waits for disk."""

    def __init__(self, target, capture, *, chunk_rows=4096, queue_blocks=16, include_truth=False,
                 start_context=None):
        if not 1 <= chunk_rows <= MAX_ROWS or not 1 <= queue_blocks <= 128:
            raise ValueError("Invalid session buffer capacity")
        self.target = Path(target).absolute()
        if self.target.suffix != SUFFIX:
            raise ValueError(f"Session destination must end in {SUFFIX}")
        self.partial = self.target.with_name(f"{self.target.name}.{capture.id.hex}.partial")
        self.capture = capture
        self.chunk_rows = chunk_rows
        self.queue_blocks = queue_blocks
        self.include_truth = include_truth
        self.committed_end = self.accepted_end = capture.first_index
        self.high_water = 0
        self.status = "recording"
        self.error = ""
        self._queue = deque()
        self._condition = Condition()
        self._stop_reason = None
        self._rejected_end = None
        self._pending = []
        self._pending_rows = 0
        self._epoch = None
        self._thread = Thread(target=self._run, name="Extracellular session writer", daemon=True)
        self._manifest = {
            "format": FORMAT, "version": VERSION, "required_features": [],
            "application": {"name": "Spikeling", "version": __version__, "build": None},
            "capture_id": str(capture.id), "acquisition": asdict(capture.acquisition),
            "designation": "synthetic extracellular acquisition",
            "clock_domain": "model_time", "nominal_model_rate_hz": 10000,
            "native_truth": include_truth, "event_datasets": EVENT_DATASETS,
            "source_capabilities": {
                "physical_device_id": None, "native_model_ticks": capture.acquisition.source == "emulator",
                "device_timestamps": capture.acquisition.device_timestamps,
            },
            "hardware_upstream_continuity": "unknown" if capture.acquisition.source == "spikeling" else None,
            "processing_initial_state": ("capture boundary snapshot"
                                         if start_context is not None else "unavailable"),
            "capture_start_processing": start_context,
            "license": None, "started_utc": utc_now(), "stopped_utc": None,
            "status": "partial", "stop_reason": None, "first_index": capture.first_index,
            "end_index": capture.first_index, "record_count": 0, "streams": STREAMS,
            "random_seed": None, "chunk_rows": chunk_rows, "failure": None,
        }
        self._thread.start()

    def offer(self, item):
        with self._condition:
            if self._stop_reason is not None or self.status != "recording":
                return False
            if isinstance(item, Discontinuity):
                start = end = item.next_index
                acquisition = item.acquisition
            else:
                span = item.inputs.span
                start, end = span.first_index, span.first_index + span.count
                acquisition = span.acquisition
            if (acquisition != self.capture.acquisition or start != self.accepted_end
                    or end - start > MAX_ROWS):
                self._fail_locked("Incompatible or oversized acquisition block", end)
                return False
            if len(self._queue) == self.queue_blocks:
                self._fail_locked("Storage could not keep up (writer queue full)", end)
                return False
            self._queue.append(item)
            self.high_water = max(self.high_water, len(self._queue))
            self.accepted_end = end
            self._condition.notify()
            return True

    def _fail_locked(self, reason, rejected_end):
        self.error = reason
        self._rejected_end = rejected_end
        self._stop_reason = reason
        self.status = "finalising"
        self._condition.notify()

    def stop(self, reason="Stopped"):
        with self._condition:
            if self.status == "recording" and self._stop_reason is None:
                self._stop_reason = reason
                self.status = "finalising"
                self._condition.notify()

    def wait(self, timeout=None):
        self._thread.join(timeout)
        return not self._thread.is_alive()

    def _run(self):
        try:
            if self.target.exists() or self.target.is_symlink():
                raise FileExistsError(f"Session already exists: {self.target.name}")
            self.partial.mkdir()
            self._checkpoint()
            self._validator = SessionReader(self.partial, strict_partial=True)
            while True:
                with self._condition:
                    self._condition.wait_for(lambda: self._queue or self._stop_reason is not None)
                    if not self._queue:
                        break
                    item = self._queue.popleft()
                if isinstance(item, Discontinuity):
                    self._flush()
                    self._commit({"kind": "boundary", "evidence": asdict(item)})
                else:
                    self._append(item)
            self._flush()
            if not self.error:
                # Verify on the writer thread before publishing any final path.
                SessionReader(self.partial, strict_partial=True)
            self._manifest.update(stopped_utc=utc_now(), stop_reason=self._stop_reason)
            if self.error:
                self._write_failure()
                self.status = "failed"
            else:
                self._publish()
        except Exception as error:
            with self._condition:
                self.error = str(error)
                self._queue.clear()
                self.status = "finalising"
                self._stop_reason = self._stop_reason or self.error
            if self.partial.is_dir() and (self.partial / MANIFEST).is_file():
                try:
                    self._write_failure()
                except (OSError, ValueError):
                    pass
            self.status = "failed"
        finally:
            self._pending.clear()

    def _checkpoint(self):
        write_json(self.partial / MANIFEST, self._manifest)

    def _write_failure(self):
        # A separate failure note leaves the last successful checkpoint intact.
        write_json(self.partial / "failure.json", {
            "error": self.error, "stop_reason": self._stop_reason,
            "stopped_utc": utc_now(), "accepted_end": self.accepted_end,
            "committed_end": self.committed_end, "rejected_end": self._rejected_end,
        })

    def _publish(self):
        self._manifest["status"] = "complete"
        self._checkpoint()
        publish_directory(self.partial, self.target)
        self.status = "complete"
        try:
            sync_directory(self.target.parent)
        except OSError as error:
            self.error = f"Session published, but directory sync failed: {error}"

    def _append(self, block):
        span = block.inputs.span
        require(block.broadband.span == block.processed.span == span, "Misaligned stream spans")
        require(block.epoch.id == span.epoch and block.epoch.segment == span.segment
                and block.epoch.first_index <= span.first_index, "Misaligned epoch")
        if self._epoch != block.epoch:
            self._flush()
            if self._epoch is not None:
                require(block.epoch.id > self._epoch.id, "Epoch moved backwards or changed in place")
            self._epoch = block.epoch
            write_json(self.partial / f"epoch-{span.epoch:019d}.json", asdict(block.epoch))
        start = 0
        while start < span.count:
            size = min(self.chunk_rows - self._pending_rows, span.count - start)
            self._pending.append((block, start, start + size))
            self._pending_rows += size
            start += size
            if self._pending_rows == self.chunk_rows:
                self._flush()

    def _flush(self):
        if not self._pending:
            return
        ordinal = self._manifest["record_count"]
        stages = {key: [] for key in STREAMS}
        spans = []
        events, truth = [], []
        for block, start, end in self._pending:
            inputs, processed = block.inputs, block.processed
            span = inputs.span
            rows = slice(start, end)
            first = span.first_index + start
            tick = span.first_tick + start
            stages["broadband"].append(block.broadband.contacts_uV[rows])
            stages["processed"].append(processed.contacts_uV[rows])
            stages["observations"].append(np.column_stack(
                (inputs.vm_mV[rows], inputs.stimulus_pct[rows], inputs.trigger[rows])))
            if inputs.source_t_ms is None:
                scale = 1000 * span.acquisition.tick_period_seconds[0] / span.acquisition.tick_period_seconds[1]
                times = np.arange(tick, tick + end - start, dtype=np.int64) * scale
            else:
                times = inputs.source_t_ms[rows]
            stages["model_time"].append(times[:, None])
            spans.append({
                "first_index": first, "count": end - start, "first_tick": tick,
                "clock": span.clock.value, "segment": span.segment, "epoch": span.epoch,
                "receive_ordinal": None if span.first_receive_ordinal is None else span.first_receive_ordinal + start,
                "host_observed_ns": span.host_observed_ns,
                "threshold_uV": processed.threshold_uV, "warmup_rows": max(0, min(end, processed.warmup_rows) - start),
                "native_available": list(inputs.native_available), "soma_clamped": inputs.soma_clamped
                if span.acquisition.source == "emulator" else None,
            })
            merged = np.zeros(end - start, dtype=np.uint8)
            for event in block.events:
                require(event.span == span and span.first_index <= event.index < span.first_index + span.count,
                        "Misaligned event")
                if not first <= event.index < first + end - start:
                    continue
                if event.kind == "grouped_detection":
                    merged[event.index - first] = 1
                is_truth = event.kind == "native_model_spike"
                if is_truth and not self.include_truth:
                    continue
                entry = {
                    "id": event.id, "kind": event.kind, "channel": event.channel,
                    "stream": EVENT_STREAMS[event.kind], "sample": event.index,
                    "segment": span.segment, "epoch": span.epoch, "provenance": event.provenance,
                    "group_id": event.group_id,
                    "group_before_capture": event.group_id is not None and event.group_id[1] < self.capture.first_index,
                }
                (truth if is_truth else events).append(entry)
            require(np.array_equal(merged, processed.merged_flags[rows]),
                    "Live merged flags disagree with typed detections")
        files = {}
        for stage, arrays in stages.items():
            data = np.concatenate(arrays, axis=0)
            require(data.dtype.kind == "f" and data.dtype.itemsize == 8, "Signal must be float64")
            data = data.astype("<f8", copy=False)
            path = self.partial / data_name(ordinal, stage)
            atomic_file(path, lambda file: np.save(file, data, allow_pickle=False))
            files[stage] = {"sha256": digest(path, data.nbytes + 4096), "shape": list(data.shape)}
        for stage, entries in (("events", events), ("truth", truth)):
            if stage == "truth" and not self.include_truth:
                continue
            path = self.partial / data_name(ordinal, stage)
            def write_events(file):
                for entry in entries:
                    file.write(canonical(entry) + b"\n")
            atomic_file(path, write_events)
            files[stage] = {"sha256": digest(path, MAX_JSON), "count": len(entries)}
        self._commit({"kind": "chunk", "first_index": self.committed_end,
                      "count": self._pending_rows, "spans": spans, "files": files,
                      "epoch_sha256": digest(self.partial / f"epoch-{self._epoch.id:019d}.json", MAX_JSON)})
        self._pending.clear()
        self._pending_rows = 0

    def _commit(self, record):
        sequence = self._manifest["record_count"]
        record["sequence"] = sequence
        record["end_index"] = self.committed_end + record.get("count", 0)
        write_json(self.partial / record_name(sequence), record)
        self._validator.accept_checkpoint_record(decode(canonical(record)))
        self._manifest.update(record_count=sequence + 1, end_index=record["end_index"])
        self._checkpoint()
        self.committed_end = record["end_index"]
