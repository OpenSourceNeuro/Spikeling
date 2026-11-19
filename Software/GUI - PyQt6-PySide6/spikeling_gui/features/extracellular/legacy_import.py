"""Read historical processed extracellular CSVs and explicit stage exports."""
import csv
from itertools import islice
from pathlib import Path

import numpy as np

from .acquisition import CONTACTS
from .recording_schema import STREAMS, SessionError, integer, load_json, require

MERGED_MARKER = "sample_aligned_merged_detection_v1"
LEGACY_CONTACTS = {f"Ch{i} (uV)": channel for i, channel in enumerate(CONTACTS, 1)}


class LegacyRecording:
    """Scan the source without modifying it or retaining its sample rows."""

    def __init__(self, path):
        self.path = Path(path)
        self.metadata = {}
        self.diagnostic = ""
        self.recovered = False
        try:
            for name in (self.path.stem + "_meta.json", self.path.stem + ".metadata.json"):
                sidecar = self.path.with_name(name)
                if sidecar.is_file():
                    self.metadata = load_json(sidecar)
                    require(isinstance(self.metadata, dict), "Invalid CSV metadata")
                    break
            with self.path.open(encoding="utf-8-sig", newline="") as file:
                reader = csv.reader(file)
                self.header = next(reader, [])
                require(len(self.header) == len(set(self.header)) and "Time (ms)" in self.header,
                        "Missing or ambiguous extracellular CSV header")
                explicit = {f"{channel} (uV)": channel for channel in CONTACTS}
                present = [column for column in explicit if column in self.header]
                if present and self.metadata.get("stage") in (
                        STREAMS["broadband"]["stage"], STREAMS["processed"]["stage"]):
                    self.columns = {explicit[column]: column for column in present}
                    self.stage = ("broadband" if self.metadata["stage"] == STREAMS["broadband"]["stage"]
                                  else "processed")
                    require(self.metadata.get("units") == "µV"
                            and set(self.metadata.get("channels", [])) == self.columns.keys()
                            and {"Accepted index", "Segment"} <= set(self.header),
                            "Explicit export metadata disagrees with its CSV")
                    self.explicit_index = True
                else:
                    require(all(column in self.header for column in LEGACY_CONTACTS),
                            "CSV is missing the four historical extracellular contact columns")
                    self.columns = {channel: column for column, channel in LEGACY_CONTACTS.items()}
                    self.stage = "processed"
                    self.explicit_index = False
                self.time_column = self.header.index("Time (ms)")
                self.merged_events_available = ("Event" in self.header
                                                and self.metadata.get("event_column") == MERGED_MARKER)
                self.launch_columns = [f"GT Spike{i}" for i in range(1, 4)
                                       if f"GT Spike{i}" in self.header]
                self.sample_count = self.first_index = self.segment_count = 0
                previous_time, previous_segment, previous_index = None, None, None
                for index, segment, values in self._parsed_rows(reader):
                    if previous_index is None:
                        self.first_index = index
                    else:
                        require(index == previous_index + 1, "Non-consecutive CSV sample indices")
                        require(segment >= previous_segment, "CSV segments moved backwards")
                    if segment != previous_segment:
                        self.segment_count += 1
                    else:
                        require(values[self.time_column] > previous_time, "CSV model times moved backwards")
                    previous_segment, previous_time, previous_index = segment, values[self.time_column], index
                    self.sample_count += 1
            self.end_index = self.first_index + self.sample_count
            if "sample_count" in self.metadata:
                require(self.metadata["sample_count"] == self.sample_count, "CSV sample count mismatch")
        except (OSError, csv.Error, TypeError, ValueError, OverflowError) as error:
            raise SessionError(f"Cannot open extracellular CSV: {error}") from error

    def _parsed_rows(self, reader, start=0):
        index_col = self.header.index("Accepted index") if self.explicit_index else None
        segment_col = self.header.index("Segment") if self.explicit_index else None
        ignored = None if self.merged_events_available or "Event" not in self.header else self.header.index("Event")
        for offset, row in enumerate(reader, start):
            require(len(row) == len(self.header), f"Malformed CSV sample {offset}")
            index = integer(int(row[index_col]), "CSV accepted index") if index_col is not None else offset
            segment = integer(int(row[segment_col]), "CSV segment") if segment_col is not None else 0
            values = tuple(float(field) if i != ignored else 0.0 for i, field in enumerate(row))
            require(np.isfinite(values).all(), f"Non-finite CSV sample {offset}")
            if self.merged_events_available:
                require(values[self.header.index("Event")] in (0.0, 1.0), "Invalid merged event flag")
            yield index, segment, values

    @property
    def stages(self):
        return (self.stage,)

    @property
    def summary(self):
        return {
            "status": "validated CSV", "source": self.metadata.get("source") or "unknown",
            "samples": self.sample_count, "channels": tuple(self.columns), "segments": self.segment_count,
            "boundaries": "unverified", "epochs": "unavailable", "clock": self.metadata.get("time_basis") or "unknown",
            "upstream_continuity": "unverified", "merged_events": self.merged_events_available,
            "native_truth": False, "launch_proxy_columns": self.launch_columns,
            "reference": self.metadata.get("car_enabled", "unknown"),
            "bandpass_low_hz": self.metadata.get("bandpass_low_hz", "unknown"),
            "bandpass_high_hz": self.metadata.get("bandpass_high_hz", "unknown"),
            "first_index": self.first_index, "end_index": self.end_index,
        }

    def iter_interval(self, stage, start=None, stop=None, channels=None, *, time_ms=None):
        require(stage in self.stages, "Signal stage unavailable in this CSV")
        start = self.first_index if start is None else start
        stop = self.end_index if stop is None else stop
        integer(start, "interval start", self.first_index, self.end_index)
        integer(stop, "interval stop", start, self.end_index)
        channels = tuple(self.columns) if channels is None else channels
        require(all(channel in self.columns for channel in channels), "Unknown CSV channel")
        selection = [self.header.index(self.columns[channel]) for channel in channels]
        if time_ms is not None:
            require(len(time_ms) == 2 and np.isfinite(time_ms).all()
                    and time_ms[0] <= time_ms[1], "Invalid time interval")
        with self.path.open(encoding="utf-8-sig", newline="") as file:
            reader = csv.reader(file)
            require(next(reader, []) == self.header, "CSV header changed since validation")
            rows = islice(reader, start - self.first_index, stop - self.first_index)
            times, values = [], []
            first, segment = None, None
            for index, current_segment, row in self._parsed_rows(rows, start):
                time = row[self.time_column]
                included = time_ms is None or time_ms[0] <= time <= time_ms[1]
                if times and (not included or len(times) == 4096 or current_segment != segment):
                    yield first, segment, np.array(times), np.array(values)
                    times, values = [], []
                if included:
                    if not times:
                        first, segment = index, current_segment
                    times.append(time)
                    values.append([row[column] for column in selection])
            if times:
                yield first, segment, np.array(times), np.array(values)

    def iter_flags(self):
        """Yield recorded launch proxies and verified merged flags by row."""
        columns = [self.header.index(name) for name in self.launch_columns]
        merged = self.header.index("Event") if self.merged_events_available else None
        with self.path.open(encoding="utf-8-sig", newline="") as file:
            reader = csv.reader(file)
            require(next(reader, []) == self.header, "CSV header changed since validation")
            for index, segment, row in self._parsed_rows(reader):
                yield index, segment, tuple(bool(row[i]) for i in columns), (bool(row[merged]) if merged is not None else None)
