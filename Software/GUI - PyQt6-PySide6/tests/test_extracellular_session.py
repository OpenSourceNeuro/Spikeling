import csv
import json
from dataclasses import replace
from pathlib import Path
from threading import Event as ThreadEvent
from uuid import uuid4

import numpy as np
import pytest

from spikeling_gui.features.extracellular.acquisition import (
    Acquisition, AcquisitionBlock, BroadbandBlock, Capture, Clock, Discontinuity, Epoch,
    Event, InputBlock, ProcessedBlock, SampleSpan,
)
from spikeling_gui.features.extracellular.legacy_import import LegacyRecording, MERGED_MARKER
from spikeling_gui.features.extracellular.recording_schema import SessionError, digest
from spikeling_gui.features.extracellular.session_reader import SessionReader, partial_sessions
from spikeling_gui.features.extracellular.session_writer import SessionWriter

SETTINGS = (
    ("source", (False, (True, False), (True, True, False), None)),
    ("synthetic", ("template", ((1, 2, 3, 4),) * 3, (), 0.0)),
    ("processing", (False, 300, 3000, None)),
    ("detection", (-30, 1, 1, 0, 1)),
    ("pacing", ("emulator", 1)),
)


def acquisition(source="emulator"):
    return Acquisition(uuid4(), source, 1)


def block(acq, first, n, tick=None, segment=0, epoch_id=0, effective=10, events=()):
    tick = 100 + first if tick is None else tick
    hardware = acq.source == "spikeling"
    span = SampleSpan(acq, segment, epoch_id, first, n, tick,
                      Clock.NOMINAL_MODEL if hardware else Clock.EMULATOR_TICK,
                      tick - 1 if hardware else None, 123456)
    rows = np.arange(first * 4, (first + n) * 4, dtype=np.float64).reshape(n, 4) / 7
    inputs = InputBlock(
        span, rows[:, :3].copy(), rows[:, 0].copy(), np.zeros(n),
        None if hardware else np.arange(tick, tick + n) / 10,
        None, (False, False, False) if hardware else (True, True, False), False,
    )
    typed = tuple(Event(kind, span, index, channel, "test_fixture", group)
                  for kind, index, channel, group in events)
    flags = np.zeros(n, dtype=np.uint8)
    for event in typed:
        if event.kind == "grouped_detection":
            flags[event.index - first] = 1
    settings = dict(SETTINGS)
    if hardware:
        settings["source"] = (None, None, (False, False, False), None)
        settings["pacing"] = ("board_requested", 1)
    return AcquisitionBlock(inputs, BroadbandBlock(span, rows),
                            ProcessedBlock(span, -rows, -30, flags, 0), typed,
                            Epoch(epoch_id, segment, effective, tuple(settings.items()),
                                  ("pacing",) if epoch_id else (), "test fixture"))


def finish(writer, status="complete"):
    writer.stop()
    writer.stop()
    assert writer.wait(10)
    assert writer.status == status, writer.error


def save(tmp_path, count=9):
    acq = acquisition()
    writer = SessionWriter(tmp_path / "test.spikeling", Capture(uuid4(), acq, 10), chunk_rows=4)
    expected = block(acq, 10, count)
    assert writer.offer(expected)
    finish(writer)
    return writer.target, expected


def test_round_trip_multiple_chunks_epochs_gaps_and_event_references(tmp_path):
    acq = acquisition()
    capture = Capture(uuid4(), acq, 10)
    writer = SessionWriter(tmp_path / "roundtrip.spikeling", capture, chunk_rows=4, include_truth=True)
    early_group = (acq.id, 9, "grouped_detection", None)
    group = (acq.id, 13, "grouped_detection", None)
    first = block(acq, 10, 5, events=(
        ("contact_crossing", 10, "E1", early_group),
        ("native_model_spike", 11, "main", None),
        ("grouped_detection", 13, None, None),
        ("contact_crossing", 13, "E2", group),
        ("contact_crossing", 14, "E3", group),
    ))
    changed = block(acq, 15, 3, epoch_id=1, effective=15)
    gap = Discontinuity("Missing emulator steps", 18, missing_model_steps=5,
                        previous_tick=117, next_tick=123, acquisition=acq, segment=0)
    continued = block(acq, 18, 3, tick=123, segment=1, epoch_id=2, effective=18)
    for item in (first, changed, gap, continued):
        assert writer.offer(item)
    finish(writer)
    reader = SessionReader(writer.target)
    assert reader.summary["samples"] == 11 and reader.summary["segments"] == 2
    assert reader.summary["epochs"] == 3 and reader.summary["boundaries"] == 1
    assert reader.manifest["capture_id"] == str(capture.id)
    assert reader.manifest["acquisition"]["id"] == str(acq.id)
    expected = np.concatenate([item.broadband.contacts_uV for item in (first, changed, continued)])
    results = list(reader.iter_interval("broadband"))
    np.testing.assert_array_equal(np.concatenate([item[3] for item in results]), expected)
    assert [idx for idx, _, _, _ in results] == [10, 14, 15, 18]
    assert results[-1][2][0] == 12.3 and results[-1][1] == 1
    np.testing.assert_array_equal(
        np.concatenate([item[3] for item in reader.iter_interval("processed", 13, 19, ("E4", "E2"))]),
        -expected[3:9, [3, 1]],
    )
    assert next(data for kind, data in reader.iter_metadata() if kind == "boundary")["missing_model_steps"] == 5
    events = list(reader.iter_events())
    assert len(events) == 4 and events[0]["group_before_capture"]
    assert events[-1]["group_id"] == [str(acq.id), 13, "grouped_detection", None]
    assert [event["sample"] for event in reader.iter_events(truth=True)] == [11]
    exported = tmp_path / "interval.csv"
    reader.export_csv(exported, "broadband", 13, 19, ("E4", "E2"))
    legacy = LegacyRecording(exported)
    assert legacy.stages == ("broadband",) and legacy.summary["segments"] == 2
    results = list(legacy.iter_interval("broadband", 16, 19, ("E4", "E2")))
    np.testing.assert_array_equal(np.concatenate([item[3] for item in results]), expected[6:9, [3, 1]])


def test_private_native_truth_omitted_and_hardware_continuity_qualified(tmp_path):
    acq = acquisition("spikeling")
    writer = SessionWriter(tmp_path / "board.spikeling", Capture(uuid4(), acq, 100))
    assert writer.offer(block(acq, 100, 2, tick=900))
    assert writer.offer(Discontinuity("Hardware queue loss", 102, local_lost=3, acquisition=acq, segment=0))
    assert writer.offer(block(acq, 102, 2, tick=905, segment=1, epoch_id=1, effective=102))
    finish(writer)
    reader = SessionReader(writer.target)
    assert not reader.manifest["native_truth"]
    assert reader.summary["upstream_continuity"] == "unknown"
    assert not list(reader.iter_events(truth=True))
    boundary = next(data for kind, data in reader.iter_metadata() if kind == "boundary")
    assert boundary["local_lost"] == 3 and boundary["missing_model_steps"] is None
    assert not list(writer.target.glob("*truth*"))


def test_empty_capture_and_existing_destination(tmp_path):
    target = tmp_path / "empty.spikeling"
    capture = Capture(uuid4(), acquisition(), 23)
    writer = SessionWriter(target, capture)
    finish(writer)
    assert SessionReader(target).sample_count == 0
    original = (target / "manifest.json").read_bytes()
    duplicate = SessionWriter(target, replace(capture, id=uuid4()))
    finish(duplicate, "failed")
    assert "already exists" in duplicate.error
    assert (target / "manifest.json").read_bytes() == original


def test_publish_refuses_a_destination_created_after_record_start(tmp_path, monkeypatch):
    publish = SessionWriter._publish

    def collide(writer):
        writer.target.mkdir()
        publish(writer)

    monkeypatch.setattr(SessionWriter, "_publish", collide)
    acq = acquisition()
    writer = SessionWriter(tmp_path / "late.spikeling", Capture(uuid4(), acq, 10))
    assert writer.offer(block(acq, 10, 3))
    finish(writer, "failed")
    assert not list(writer.target.iterdir())
    recovered = SessionReader(writer.partial)
    assert recovered.recovered and recovered.sample_count == 3


def test_saturation_drains_accepted_prefix_and_reports_loss(tmp_path, monkeypatch):
    entered, release = ThreadEvent(), ThreadEvent()
    checkpoint = SessionWriter._checkpoint

    def blocked(writer):
        if not entered.is_set():
            entered.set()
            assert release.wait(5)
        checkpoint(writer)

    monkeypatch.setattr(SessionWriter, "_checkpoint", blocked)
    acq = acquisition()
    writer = SessionWriter(tmp_path / "overflow.spikeling", Capture(uuid4(), acq, 10),
                           chunk_rows=4, queue_blocks=1)
    assert entered.wait(5)
    try:
        assert writer.offer(block(acq, 10, 5))
        assert not writer.offer(block(acq, 15, 5))
    finally:
        release.set()
    finish(writer, "failed")
    assert not writer.target.exists()
    partial, = partial_sessions(tmp_path)
    reader = SessionReader(partial)
    assert reader.recovered and reader.sample_count == 5
    assert reader.failure["rejected_end"] == 20 and reader.failure["committed_end"] == 15


@pytest.mark.parametrize("failure", ["ENOSPC", "checkpoint", "finalisation", "denied"])
def test_failure_retains_last_checkpoint(tmp_path, monkeypatch, failure):
    import spikeling_gui.features.extracellular.session_writer as storage

    if failure == "ENOSPC":
        write = storage.atomic_file
        def fail(path, callback):
            if path.name == "000000000001-broadband.npy":
                raise OSError(28, "No space left on device")
            return write(path, callback)
        monkeypatch.setattr(storage, "atomic_file", fail)
    elif failure == "checkpoint":
        checkpoint = SessionWriter._checkpoint
        def fail(writer):
            if writer._manifest["record_count"] == 2:
                raise OSError("Interrupted manifest replacement")
            checkpoint(writer)
        monkeypatch.setattr(SessionWriter, "_checkpoint", fail)
    elif failure == "finalisation":
        def fail(writer):
            raise PermissionError("Could not publish session")
        monkeypatch.setattr(SessionWriter, "_publish", fail)
    else:
        mkdir = Path.mkdir
        def fail(path, *args, **kwargs):
            if path.suffix == ".partial":
                raise PermissionError("Access denied")
            return mkdir(path, *args, **kwargs)
        monkeypatch.setattr(Path, "mkdir", fail)

    acq = acquisition()
    writer = SessionWriter(tmp_path / "failure.spikeling", Capture(uuid4(), acq, 10), chunk_rows=4)
    writer.offer(block(acq, 10, 9))
    finish(writer, "failed")
    assert not writer.target.exists()
    if failure == "denied":
        assert not writer.partial.exists()
        return
    reader = SessionReader(writer.partial)
    assert reader.recovered and reader.failure["error"]
    assert reader.sample_count == (9 if failure == "finalisation" else 4)
    if failure == "checkpoint":
        assert reader.extra_files >= 1


@pytest.mark.parametrize("case", ["major", "missing", "checksum", "shape", "dtype", "json",
                                  "unsafe", "tick", "range", "event", "nonfinite", "event_reference"])
def test_validation_rejects_inconsistent_sessions(tmp_path, case):
    target, _ = save(tmp_path)
    manifest = target / "manifest.json"
    name = target / "000000000000.json"
    record = json.loads(name.read_text("utf-8"))
    if case in ("major", "nonfinite"):
        m = json.loads(manifest.read_text("utf-8"))
        if case == "major":
            m["version"]["major"] = 9
        else:
            m["random_seed"] = float("inf")
        manifest.write_text(json.dumps(m), "utf-8")
    elif case == "json":
        name.write_text("{", "utf-8")
    elif case in ("tick", "range"):
        if case == "tick":
            record["spans"][0]["first_tick"] += 1
        else:
            record["end_index"] += 1
        name.write_text(json.dumps(record), "utf-8")
    elif case in ("event", "event_reference"):
        events = target / "000000000000-events.jsonl"
        if case == "event":
            events.write_text('{"id":', "utf-8")
        else:
            source = json.loads(manifest.read_text("utf-8"))["acquisition"]["id"]
            event = {
                "id": [source, 11, "contact_crossing", "E1"], "kind": "contact_crossing",
                "sample": 11, "segment": 0, "epoch": 0, "channel": "E1", "stream": "processed",
                "provenance": "test_fixture", "group_id": [source, 10, "grouped_detection", None],
                "group_before_capture": False,
            }
            events.write_text(json.dumps(event) + "\n", "utf-8")
        record["files"]["events"] = {"count": 1, "sha256": digest(events, 4096)}
        name.write_text(json.dumps(record), "utf-8")
    else:
        data = target / "000000000000-broadband.npy"
        if case == "unsafe":
            outside = tmp_path / "outside.npy"
            data.rename(outside)
            try:
                data.symlink_to(outside)
            except OSError:
                pytest.skip("Symbolic links unavailable for this Windows account")
        elif case == "missing":
            data.unlink()
        elif case == "checksum":
            with data.open("ab") as file:
                file.write(b"x")
        else:
            if case == "shape":
                np.save(data, np.ones((1, 4)))
            else:
                np.save(data, np.ones((4, 4), dtype="<f4"))
            record["files"]["broadband"]["sha256"] = digest(data, 4096)
            name.write_text(json.dumps(record), "utf-8")
    with pytest.raises(SessionError):
        SessionReader(target)


def test_partial_recovery_truncated_final_chunk_and_optional_manifest_fields(tmp_path):
    target, _ = save(tmp_path)
    manifest = target / "manifest.json"
    metadata = json.loads(manifest.read_text("utf-8"))
    metadata["version"]["minor"] = 11
    metadata["optional_future_annotation"] = "ignored"
    manifest.write_text(json.dumps(metadata), "utf-8")
    assert SessionReader(target).sample_count == 9
    partial = target.with_name(target.name + ".interrupted.partial")
    target.rename(partial)
    (partial / "000000000002-broadband.npy").write_bytes(b"broken")
    reader = SessionReader(partial)
    assert reader.recovered and reader.sample_count == 8
    assert reader.extra_files >= 1 and "record 2" in reader.diagnostic
    assert (partial / "000000000002-broadband.npy").read_bytes() == b"broken"


def test_historical_csv_marks_unverified_flags_and_missing_broadband(tmp_path):
    path = tmp_path / "old.csv"
    with path.open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Time (ms)", *(f"Ch{i} (uV)" for i in range(1, 5)), "GT Spike1", "Event"])
        writer.writerows([(0.1, 1, 2, 3, 4, 0, 0), (0.2, 5, 6, 7, 8, 1, 1)])
    old = LegacyRecording(path)
    assert old.stages == ("processed",)
    assert list(old.iter_flags())[-1][-2:] == ((True,), None)
    original = path.read_bytes()
    path.with_name("old_meta.json").write_text(json.dumps({"event_column": MERGED_MARKER}), "utf-8")
    corrected = LegacyRecording(path)
    assert list(corrected.iter_flags())[-1][-2:] == ((True,), True)
    assert path.read_bytes() == original


def test_large_window_access_read_does_not_materialise_other_chunks(tmp_path, monkeypatch):
    target, _ = save(tmp_path)
    reader = SessionReader(target)
    calls = []
    read = reader._array
    def track(sequence, *args):
        calls.append(sequence)
        return read(sequence, *args)
    monkeypatch.setattr(reader, "_array", track)
    first, _, time, rows = next(reader.iter_interval("broadband", 18, 19, ("E2",)))
    assert first == 18 and len(time) == 1 and rows.shape == (1, 1)
    assert calls == [2, 2]


def test_abrupt_subprocess_exit_recovers_last_durable_checkpoint(tmp_path):
    import subprocess
    import sys

    program = """
from pathlib import Path
import os
import sys
from time import monotonic, sleep
from uuid import uuid4
sys.path.insert(0, sys.argv[1])
from test_extracellular_session import acquisition, block, Capture, SessionWriter
source = acquisition()
writer = SessionWriter(Path(sys.argv[2]) / "abrupt.spikeling",
                       Capture(uuid4(), source, 10), chunk_rows=4)
assert writer.offer(block(source, 10, 5))
deadline = monotonic() + 7
while writer.committed_end != 14 and monotonic() < deadline:
    if writer.status == "failed":
        raise RuntimeError(writer.error)
    sleep(0.005)
assert writer.committed_end == 14
os._exit(0)
"""
    subprocess.run([sys.executable, "-c", program, str(Path(__file__).parent), str(tmp_path)],
                   check=True, capture_output=True, text=True, timeout=15)
    assert not (tmp_path / "abrupt.spikeling").exists()
    partial, = partial_sessions(tmp_path)
    reader = SessionReader(partial)
    assert reader.recovered and reader.sample_count == 4
    assert reader.summary["stop_reason"] == "interrupted before publication"
