"""Validate a session and read only the requested chunks into memory."""
import csv
from bisect import bisect_right
import os
import re
from pathlib import Path
from uuid import UUID

import numpy as np

from .acquisition import CONTACTS, NEURONS, Clock
from .recording_schema import (
    EVENT_DATASETS, EVENT_STREAMS, FORMAT, MANIFEST, MAX_JSON, MAX_ROWS, STREAMS, SUFFIX, VERSION,
    SessionError, canonical, data_name, decode, digest, integer, load_json, local_file,
    record_name, require,
)


class SessionReader:
    """A validated snapshot. Partial directories are opened read-only."""

    def __init__(self, directory, *, strict_partial=False):
        self.directory = Path(directory).resolve()
        self.diagnostic = ""
        self.failure = None
        self.gap_count = self.segment_count = self.epoch_count = 0
        self.extra_files = 0
        self._last_span = self._last_time = self._last_group = self._last_epoch = None
        self._pending_boundary = False
        try:
            self.manifest = self._json(MANIFEST)
            self._validate_manifest()
            self.recovered = self.directory.name.endswith(".partial")
            self.first_index = self.end_index = self.manifest["first_index"]
            self.record_count = 0
            self._validate_records(strict_partial)
            if self.recovered and (self.directory / "failure.json").exists():
                try:
                    failure = self._json("failure.json")
                    require(isinstance(failure, dict), "Invalid failure note")
                    self.failure = failure
                except (OSError, ValueError, RecursionError) as error:
                    self.diagnostic = (self.diagnostic + f" Failure note unavailable: {error}").strip()
        except (OSError, TypeError, ValueError, KeyError, OverflowError, RecursionError) as error:
            raise SessionError(f"Cannot open extracellular session: {error}") from error

    def _json(self, name):
        return load_json(local_file(self.directory, name))

    def _validate_manifest(self):
        m = self.manifest
        require(m["format"] == FORMAT, "Unsupported recording format")
        require(type(m["version"]["major"]) is int and m["version"]["major"] == VERSION["major"],
                "Unsupported schema major version. Open with a compatible Spikeling release.")
        integer(m["version"]["minor"], "schema minor version")
        require(m["required_features"] == [], "Unsupported required session features")
        for value in (m["capture_id"], m["acquisition"]["id"]):
            require(str(UUID(value)) == value, "Invalid recording identity")
        source = m["acquisition"]["source"]
        require(source in ("emulator", "spikeling"), "Unknown recording source")
        integer(m["acquisition"]["generation"], "source generation")
        require(m["acquisition"]["tick_period_seconds"] == [1, 10000]
                and m["acquisition"]["device_timestamps"] is False, "Incompatible clock definition")
        require(m["hardware_upstream_continuity"] == ("unknown" if source == "spikeling" else None),
                "Invalid hardware continuity claim")
        require(m["clock_domain"] == "model_time"
                and m["designation"] == "synthetic extracellular acquisition", "Invalid scientific provenance")
        require(m["streams"] == STREAMS, "Incompatible stream descriptors or channel order")
        require(m["nominal_model_rate_hz"] == 10000 and m["event_datasets"] == EVENT_DATASETS,
                "Incompatible model rate or event dataset schema")
        require(m["source_capabilities"]["device_timestamps"] is False
                and m["source_capabilities"]["native_model_ticks"] is (source == "emulator"),
                "Incompatible source capabilities")
        integer(m["chunk_rows"], "chunk rows", 1, MAX_ROWS)
        integer(m["first_index"], "first sample index")
        integer(m["end_index"], "end sample index", m["first_index"])
        integer(m["record_count"], "committed record count")
        if self.directory.name.endswith(".partial"):
            require(m["status"] in ("partial", "complete"), "Invalid checkpoint status")
        else:
            require(self.directory.suffix == SUFFIX and m["status"] == "complete",
                    "Unpublished session is missing its partial-directory marker")
        require(type(m["native_truth"]) is bool and isinstance(m["application"]["version"], str)
                and isinstance(m["processing_initial_state"], str) and isinstance(m["started_utc"], str),
                "Invalid application or processing metadata")
        if m["status"] == "complete":
            require(isinstance(m["stopped_utc"], str) and isinstance(m["stop_reason"], str),
                    "Missing completion provenance")

    def _array(self, sequence, stage, descriptor):
        path = local_file(self.directory, data_name(sequence, stage))
        require(descriptor.keys() == {"shape", "sha256"}, "Unexpected numerical file descriptor")
        shape = descriptor["shape"]
        require(isinstance(shape, list) and len(shape) == 2, "Invalid numerical shape")
        count = integer(shape[0], "file rows", 1, self.manifest["chunk_rows"])
        width = len(STREAMS[stage]["channels"])
        require(shape[1] == width and type(shape[1]) is int, "Invalid numerical channel count")
        require(digest(path, count * width * 8 + 4096) == descriptor["sha256"],
                f"Checksum mismatch for {path.name}")
        # mmap checks the declared layout before materialising any data. This
        # includes files with adversarial NPY headers claiming huge shapes.
        with path.open("rb") as file:
            require(file.read(6) == b"\x93NUMPY", f"Not a NumPy array: {path.name}")
        array = np.load(path, allow_pickle=False, mmap_mode="r", max_header_size=4096)
        require(array.shape == tuple(shape) and array.dtype.str == "<f8"
                and array.flags.c_contiguous and np.isfinite(array).all(),
                f"Incompatible dtype, shape or samples in {path.name}")
        require(array.offset + array.nbytes == path.stat().st_size, f"Unexpected bytes in {path.name}")
        return array

    def _events(self, sequence, stage, descriptor):
        path = local_file(self.directory, data_name(sequence, stage))
        require(digest(path, MAX_JSON) == descriptor["sha256"], f"Checksum mismatch for {path.name}")
        require(descriptor.keys() == {"count", "sha256"}, "Unexpected event file descriptor")
        count = integer(descriptor["count"], "event count", 0, self.manifest["chunk_rows"] * 20)
        with path.open("rb") as file:
            for _ in range(count):
                line = file.readline(MAX_JSON + 1)
                require(line.endswith(b"\n"), f"Truncated event dataset {path.name}")
                yield decode(line)
            require(file.read(1) == b"", f"Unexpected events in {path.name}")

    def _validate_records(self, strict_partial):
        m = self.manifest
        for sequence in range(m["record_count"]):
            try:
                self.accept_checkpoint_record(self._json(record_name(sequence)))
            except (OSError, TypeError, ValueError, KeyError, IndexError, OverflowError, RecursionError) as error:
                if not self.recovered or strict_partial:
                    raise SessionError(f"Invalid checkpoint record {sequence}: {error}") from error
                self.diagnostic = f"Recovered validated prefix before record {sequence}: {error}"
                break
        if self.record_count == m["record_count"]:
            require(self.end_index == m["end_index"], "Checkpoint end index does not match records")
        if self.recovered:
            with os.scandir(self.directory) as entries:
                for entry in entries:
                    number = re.match(r"^(\d{12})(?:[.-])", entry.name)
                    epoch = re.match(r"^epoch-(\d{19})\.json$", entry.name)
                    if (entry.name.endswith(".tmp") or (number and int(number[1]) >= self.record_count)
                            or (epoch and int(epoch[1]) > (-1 if self._last_epoch is None else self._last_epoch["id"]))):
                        self.extra_files += 1

    def accept_checkpoint_record(self, record):
        """Validate one new journal entry using constant-size continuity state."""
        require(record["sequence"] == self.record_count, "Record order mismatch")
        if record["kind"] == "boundary":
            evidence = record["evidence"]
            require(record["end_index"] == evidence["next_index"] == self.end_index
                    and evidence["acquisition"] == self.manifest["acquisition"]
                    and isinstance(evidence["reason"], str), "Misaligned discontinuity")
            integer(evidence["segment"], "boundary segment")
            integer(evidence["local_lost"], "locally lost rows")
            for key in ("missing_model_steps", "host_stall_ns", "previous_tick", "next_tick",
                        "next_receive_ordinal"):
                if evidence[key] is not None:
                    integer(evidence[key], key)
            if evidence["previous_receive_ordinal"] is not None:
                integer(evidence["previous_receive_ordinal"], "previous receive ordinal", -1)
            self.gap_count += 1
            self._pending_boundary = True
            self._last_group = None
        else:
            (self._last_span, self._last_time, self._last_group, self._last_epoch,
             segment_delta, epoch_delta) = self._check_chunk(
                self.record_count, record, self._last_span, self._last_time,
                self._last_group, self._last_epoch, self._pending_boundary,
            )
            self.segment_count += segment_delta
            self.epoch_count += epoch_delta
            self.end_index = record["end_index"]
            self._pending_boundary = False
        self.record_count += 1

    def _check_epoch_settings(self, epoch):
        settings = dict(epoch["settings"])
        require(set(settings) == {"source", "synthetic", "processing", "detection", "pacing"}
                and len(settings) == len(epoch["settings"])
                and set(epoch["changed"]) <= settings.keys(), "Invalid settings categories")
        source = settings["source"]
        hardware = self.manifest["acquisition"]["source"] == "spikeling"
        require(isinstance(source, list) and len(source) == 4
                and type(source[0]) is (type(None) if hardware else bool),
                "Invalid epoch clamp provenance")
        synthetic = settings["synthetic"]
        require(isinstance(synthetic, list) and len(synthetic) in (4, 5)
                and synthetic[0] in ("template", "dvdt"), "Invalid synthetic generator")
        distances = np.asarray(synthetic[1])
        require(distances.shape == (3, 4) and distances.dtype.kind in "fiu"
                and (distances >= 0).all(), "Invalid source-to-contact geometry")
        if len(synthetic) == 5 and synthetic[4] is not None:
            neurons, contacts = (np.asarray(points) for points in synthetic[4])
            require(neurons.shape in ((3, 2), (3, 3)) and contacts.shape == (4, neurons.shape[1])
                    and neurons.dtype.kind in "fiu" and contacts.dtype.kind in "fiu",
                    "Invalid source or contact coordinates")
            with np.errstate(over="ignore", invalid="ignore"):
                calculated = np.linalg.norm(neurons[:, None, :] - contacts[None, :, :], axis=2)
            require(np.allclose(calculated, distances, rtol=0, atol=1e-6),
                    "Source and contact coordinates disagree with distances")
        car, low, high, sos = settings["processing"]
        bypass = low is None and high is None and sos is None
        bandpass = type(low) in (float, int) and type(high) in (float, int) and 0 < low < high < 5000
        require(type(car) is bool and (bypass or bandpass), "Invalid reference or bandpass recipe")
        if sos is not None:
            coefficients = np.asarray(sos)
            require(coefficients.ndim == 2 and coefficients.shape[1] == 6
                    and coefficients.shape[0] > 0 and coefficients.dtype.kind in "fiu"
                    and (coefficients[:, 3] == 1).all(), "Invalid causal filter coefficients")
        detection = settings["detection"]
        require(len(detection) == 5 and all(type(value) in (float, int) for value in detection),
                "Invalid detector settings")
        pacing = settings["pacing"]
        require(len(pacing) == 2 and pacing[0] == ("board_requested" if hardware else "emulator"),
                "Invalid pacing provenance")

    def _check_chunk(self, sequence, record, previous, previous_time, last_group, old_epoch, boundary):
        count = integer(record["count"], "chunk row count", 1, self.manifest["chunk_rows"])
        first = self.end_index
        require(record["kind"] == "chunk" and record["first_index"] == first
                and record["end_index"] == first + count, "Inconsistent chunk sample range")
        files = record["files"]
        expected = {*STREAMS, "events"}
        if self.manifest["native_truth"]:
            expected.add("truth")
        require(files.keys() == expected, "Missing or unsupported chunk datasets")
        time = None
        for stage in STREAMS:
            array = self._array(sequence, stage, files[stage])
            require(len(array) == count, "Conflicting chunk row count")
            if stage == "model_time":
                time = array[:, 0]
        spans = record["spans"]
        require(isinstance(spans, list) and 0 < len(spans) <= count, "Missing chunk spans")
        epoch_id = integer(spans[0]["epoch"], "epoch ID")
        epoch_path = local_file(self.directory, f"epoch-{epoch_id:019d}.json")
        require(digest(epoch_path, MAX_JSON) == record["epoch_sha256"], "Epoch checksum mismatch")
        epoch = load_json(epoch_path)
        require(epoch["id"] == epoch_id and isinstance(epoch["reason"], str)
                and isinstance(epoch["settings"], list)
                and isinstance(epoch["changed"], list), "Invalid configuration epoch")
        self._check_epoch_settings(epoch)
        effective = integer(epoch["first_index"], "effective sample index")
        new_epoch = old_epoch is None or old_epoch["id"] != epoch_id
        require(effective <= first and (old_epoch is None or not new_epoch or
                (epoch_id > old_epoch["id"] and effective == first)), "Misaligned settings boundary")
        if not new_epoch:
            require(epoch == old_epoch, "Epoch changed in place")
        segment = integer(spans[0]["segment"], "segment ID")
        new_segment = previous is None or segment != previous["segment"]
        require(epoch["segment"] == segment, "Epoch belongs to a different segment")
        require(previous is None or (segment >= previous["segment"] and new_segment == boundary),
                "Segment changed without a recorded boundary")
        if new_segment:
            last_group = None
        elif new_epoch and any(key in epoch["changed"] for key in ("processing", "detection", "source")):
            last_group = None

        offset = 0
        for span in spans:
            rows = integer(span["count"], "span row count", 1, count)
            tick = integer(span["first_tick"], "model tick")
            clock = Clock(span["clock"])
            hardware = self.manifest["acquisition"]["source"] == "spikeling"
            require((clock == Clock.NOMINAL_MODEL) == hardware, "Clock does not match source")
            require(span["first_index"] == first + offset and span["segment"] == segment
                    and span["epoch"] == epoch_id and offset + rows <= count, "Invalid span sample range")
            require((hardware and type(span["receive_ordinal"]) is int and span["receive_ordinal"] >= 0)
                    or (not hardware and span["receive_ordinal"] is None), "Invalid board receive ordinal")
            if span["host_observed_ns"] is not None:
                integer(span["host_observed_ns"], "host observation")
            require(type(span["threshold_uV"]) in (float, int)
                    and type(span["soma_clamped"]) is (type(None) if hardware else bool)
                    and len(span["native_available"]) == 3
                    and all(type(value) is bool for value in span["native_available"]), "Invalid span state")
            require((not hardware or not any(span["native_available"]))
                    and (not span["soma_clamped"] or not span["native_available"][0]),
                    "Invalid native event availability")
            integer(span["warmup_rows"], "warm-up row count", 0, rows)
            times = time[offset:offset + rows]
            integer(tick + rows - 1, "final model tick")
            expected_time = (tick + np.arange(rows, dtype=np.int64)) / 10
            require(np.all(np.diff(times) > 0) and np.all(np.abs(times - expected_time) <= 0.001000001),
                    "Model times disagree with ticks")
            if previous is not None and previous["segment"] == segment:
                require(tick == previous["first_tick"] + previous["count"]
                        and clock.value == previous["clock"]
                        and times[0] > previous_time, "Non-contiguous tick sequence inside a segment")
                if hardware:
                    require(span["receive_ordinal"] == previous["receive_ordinal"] + previous["count"],
                            "Non-contiguous receive ordinals inside a segment")
            previous, previous_time = span, times[-1]
            offset += rows
        require(offset == count, "Incomplete span coverage")
        events = list(self._events(sequence, "events", files["events"]))
        if "truth" in files:
            truth = list(self._events(sequence, "truth", files["truth"]))
            require(all(event["kind"] == "native_model_spike" for event in truth),
                    "Truth dataset contains non-native events")
            events.extend(truth)
        last_group = self._check_events(events, first, count, segment, epoch_id, last_group,
                                        files["events"]["count"], spans)
        return previous, previous_time, last_group, epoch, int(new_segment), int(new_epoch)

    def _check_events(self, events, first, count, segment, epoch, last_group, public_count, spans):
        require(all(event["kind"] != "native_model_spike" for event in events[:public_count]),
                "Native truth found in the public event dataset")
        acquisition_id = self.manifest["acquisition"]["id"]
        seen = set()
        span_starts = [span["first_index"] for span in spans]
        opening_crossings = set()
        groups = set()
        for event in sorted(events, key=lambda event: (
                event["sample"], event["kind"] != "grouped_detection")):
            kind, channel, sample = event["kind"], event["channel"], event["sample"]
            integer(sample, "event sample", first, first + count - 1)
            require(EVENT_STREAMS[kind] == event["stream"] and event["segment"] == segment
                    and event["epoch"] == epoch and isinstance(event["provenance"], str)
                    and bool(event["provenance"]), "Invalid event provenance")
            channels = (CONTACTS if kind == "contact_crossing" else
                        NEURONS if kind in ("native_model_spike", "waveform_launch") else (None,))
            identity = (acquisition_id, sample, kind, channel)
            require(channel in channels and event["id"] == list(identity)
                    and identity not in seen, "Invalid or duplicate event identity")
            seen.add(identity)
            if kind == "native_model_spike":
                span = spans[bisect_right(span_starts, sample) - 1]
                require(span["native_available"][NEURONS.index(channel)], "Unavailable native event source")
            if kind == "grouped_detection":
                last_group = list(identity)
                groups.add(sample)
            group = event["group_id"]
            if kind == "contact_crossing":
                require(isinstance(group, list) and len(group) == 4 and group[0] == acquisition_id
                        and group[2:] == ["grouped_detection", None], "Invalid group reference")
                group_index = integer(group[1], "group sample", 0, sample)
                external = group_index < self.first_index
                require(event["group_before_capture"] is external
                        and (external and last_group is None or group == last_group),
                        "Broken grouped-detection reference")
                if sample == group_index:
                    opening_crossings.add(sample)
            else:
                require(group is None and event["group_before_capture"] is False,
                        "Unexpected group reference")
        require(groups <= opening_crossings, "Grouped detection is missing its initiating crossing")
        return last_group

    @property
    def sample_count(self):
        return self.end_index - self.first_index

    @property
    def stages(self):
        return ("broadband", "processed")

    @property
    def summary(self):
        return {
            "status": "recovered/incomplete" if self.recovered else "complete",
            "source": self.manifest["acquisition"]["source"], "samples": self.sample_count,
            "channels": CONTACTS, "segments": self.segment_count, "boundaries": self.gap_count,
            "epochs": self.epoch_count, "clock": self.manifest["clock_domain"],
            "upstream_continuity": self.manifest["hardware_upstream_continuity"],
            "native_truth_in_companion": self.manifest["native_truth"],
            "device_timestamps": False,
            "first_index": self.first_index, "end_index": self.end_index,
            "ignored_files": self.extra_files,
            "diagnostic": self.diagnostic,
            "stop_reason": ((self.failure or {}).get("stop_reason") or self.manifest["stop_reason"]
                            or ("interrupted before publication" if self.recovered else None)),
            "processing_initial_state": self.manifest["processing_initial_state"],
        }

    def _records(self, start):
        # The journal end indices are monotonic, including zero-row boundaries.
        lo, hi = 0, self.record_count
        while lo < hi:
            middle = (lo + hi) // 2
            if self._json(record_name(middle))["end_index"] <= start:
                lo = middle + 1
            else:
                hi = middle
        for sequence in range(lo, self.record_count):
            yield sequence, self._json(record_name(sequence))

    def iter_interval(self, stage, start=None, stop=None, channels=None, *, time_ms=None,
                      with_spans=False):
        """Yield (first index, segment, model ms, values), optionally with clipped spans."""
        require(stage in STREAMS, "Signal stage unavailable")
        available = STREAMS[stage]["channels"]
        channels = available if channels is None else channels
        require(all(channel in available for channel in channels), "Unknown channel selection")
        selection = [available.index(channel) for channel in channels]
        start = self.first_index if start is None else start
        stop = self.end_index if stop is None else stop
        integer(start, "interval start", self.first_index, self.end_index)
        integer(stop, "interval stop", start, self.end_index)
        if time_ms is not None:
            require(len(time_ms) == 2 and np.isfinite(time_ms).all()
                    and time_ms[0] <= time_ms[1], "Invalid time interval")
        for sequence, record in self._records(start):
            if record["kind"] != "chunk":
                continue
            first = record["first_index"]
            if first >= stop:
                break
            lo, hi = max(start - first, 0), min(stop - first, record["count"])
            if time_ms is not None:
                initial, final = record["spans"][0], record["spans"][-1]
                if (initial["first_tick"] / 10 - 0.001000001 > time_ms[1]
                        or (final["first_tick"] + final["count"] - 1) / 10 + 0.001000001 < time_ms[0]):
                    continue
            model_time = self._array(sequence, "model_time", record["files"]["model_time"])
            times = model_time[lo:hi, 0]
            if time_ms is not None:
                left = np.searchsorted(times, time_ms[0])
                # Include the last timestamp when it equals the requested end.
                right = np.searchsorted(times, time_ms[1], side="right")
                lo, hi = lo + int(left), lo + int(right)
                times = times[left:right]
            if times.size:
                matrix = (model_time if stage == "model_time" else
                          self._array(sequence, stage, record["files"][stage]))
                result = first + lo, record["spans"][0]["segment"], times.copy(), matrix[lo:hi, selection]
                if with_spans:
                    spans = []
                    for span in record["spans"]:
                        original = span["first_index"]
                        begin = max(original, first + lo)
                        end = min(original + span["count"], first + hi)
                        if begin < end:
                            skip = begin - original
                            ordinal = span["receive_ordinal"]
                            spans.append(dict(span, first_index=begin, count=end - begin,
                                              first_tick=span["first_tick"] + skip,
                                              receive_ordinal=None if ordinal is None else ordinal + skip,
                                              warmup_rows=max(0, min(end - begin, span["warmup_rows"] - skip))))
                    yield (*result, spans)
                else:
                    yield result

    def iter_metadata(self):
        """Yield each effective epoch once, with chunk spans and interruptions."""
        last_epoch = None
        for sequence in range(self.record_count):
            record = self._json(record_name(sequence))
            if record["kind"] == "chunk":
                epoch = record["spans"][0]["epoch"]
                if epoch != last_epoch:
                    yield "epoch", self._json(f"epoch-{epoch:019d}.json")
                    last_epoch = epoch
                yield "spans", record["spans"]
            else:
                yield "boundary", record["evidence"]

    def iter_events(self, *, truth=False, start=None, stop=None):
        """Stream public or explicitly requested truth events within accepted bounds."""
        stage = "truth" if truth else "events"
        start = self.first_index if start is None else start
        stop = self.end_index if stop is None else stop
        integer(start, "event interval start", self.first_index, self.end_index)
        integer(stop, "event interval stop", start, self.end_index)
        for sequence, record in self._records(start):
            if record["kind"] != "chunk":
                continue
            if record["first_index"] >= stop:
                break
            if stage in record["files"]:
                for event in self._events(sequence, stage, record["files"][stage]):
                    if start <= event["sample"] < stop:
                        yield event

    def export_csv(self, destination, stage, start=None, stop=None, channels=CONTACTS):
        require(stage in self.stages, "Select an extracellular signal stage")
        destination = Path(destination)
        sidecar = destination.with_name(destination.stem + "_meta.json")
        require(not sidecar.exists(), "Export metadata already exists")
        with destination.open("x", encoding="utf-8", newline="") as file:
            try:
                writer = csv.writer(file)
                writer.writerow(["Accepted index", "Segment", "Time (ms)", *[f"{ch} (uV)" for ch in channels]])
                for first, segment, times, values in self.iter_interval(stage, start, stop, channels):
                    writer.writerows((first + i, segment, time, *row)
                                     for i, (time, row) in enumerate(zip(times, values)))
                metadata = canonical({
                    "stage": STREAMS[stage]["stage"], "units": "µV", "channels": channels,
                    "capture_id": self.manifest["capture_id"], "time_basis": "model_time",
                    "source": self.manifest["acquisition"]["source"],
                })
                with sidecar.open("xb") as metadata_file:
                    try:
                        metadata_file.write(metadata)
                        metadata_file.flush()
                        os.fsync(metadata_file.fileno())
                    except OSError:
                        metadata_file.close()
                        sidecar.unlink()
                        raise
            except Exception:
                file.close()
                destination.unlink()
                raise


def partial_sessions(directory):
    """Find unpublished session candidates without modifying any files."""
    return (path for path in Path(directory).glob("*.spikeling.*.partial")
            if path.is_dir() and (path / MANIFEST).is_file())
