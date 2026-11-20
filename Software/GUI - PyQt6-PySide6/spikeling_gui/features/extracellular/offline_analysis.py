"""Reproducible offline analysis and derivative export."""
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path

import numpy as np

from .acquisition import CONTACTS, NEURONS
from .analysis_comparison import Agreement, EventAnchor, match_events, validate_tolerance
from .offline_detection import Detector, detect_run
from .offline_processing import ALGORITHM, NOTCH_Q, POLE_DECAY, WARMUP_MS, Processing, process_interval
from .recording_schema import canonical
from .session_reader import SessionReader
from .waveform_analysis import Waveforms, WaveformSettings, extract_waveforms


@dataclass(frozen=True)
class Recipe:
    processing: Processing = Processing()
    detector: Detector = Detector()
    waveform: WaveformSettings = WaveformSettings()


@dataclass(frozen=True)
class Analysis:
    id: str
    recipe: Recipe
    capture_id: str
    acquisition_id: str
    start: int
    stop: int
    rate: int
    recovered: bool
    live_initial_state: str
    samples_sha256: str
    runs: tuple
    groups: tuple
    waveforms: Waveforms

    @property
    def warmup_rows(self):
        return sum(run.warmup for run in self.runs)

    @property
    def identity(self):
        return self.capture_id, self.acquisition_id, self.start, self.stop, self.samples_sha256


@dataclass(frozen=True)
class SourceAgreement:
    stream: str
    available: bool
    eligible_rows: int
    excluded_detections: int
    events: tuple
    agreement: Agreement | None


def analyse(reader, start, stop, recipe, cancel=None):
    """Read a bounded interval, validate settings and never consult source truth."""
    if not isinstance(reader, SessionReader):
        raise ValueError("Offline processing requires a validated broadband session.")
    rate = reader.manifest["nominal_model_rate_hz"]
    recipe.detector.validate()
    recipe.waveform.window(rate)
    capture_id = reader.manifest["capture_id"]
    acquisition_id = reader.manifest["acquisition"]["id"]
    digest = sha256()
    runs = tuple(process_interval(reader, start, stop, recipe.processing, cancel, digest))
    if cancel is not None and cancel.is_set():
        return None
    if sum(len(run.time_ms) for run in runs) != stop - start:
        raise ValueError("The validated source no longer covers the selected interval.")
    fingerprint = digest.hexdigest()
    boundaries = tuple((run.first, run.end, run.segment, run.epoch, run.tick, run.clock) for run in runs)
    identity = sha256(canonical((ALGORITHM, capture_id, acquisition_id, start, stop,
                                  fingerprint, boundaries, asdict(recipe)))).hexdigest()
    groups = tuple(group for run in runs for group in detect_run(run, recipe.detector, rate, identity))
    waveforms = extract_waveforms(runs, groups, recipe.waveform, rate, cancel)
    if waveforms is None:
        return None
    return Analysis(identity, recipe, capture_id, acquisition_id, start, stop, rate, reader.recovered,
                    reader.manifest["processing_initial_state"], fingerprint, runs, groups, waveforms)


def compare(left, right, tolerance_ms, cancel=None):
    if left.identity != right.identity:
        raise ValueError("Both recipes must use the same recording, broadband bytes and accepted interval.")
    # A shorter warm-up in one condition must not create unmatched counts in
    # samples that the other condition could not test.

    def keys(result):
        return [(run.first, run.end, run.segment, run.epoch, run.tick, run.clock) for run in result.runs]

    if keys(left) != keys(right):
        raise ValueError("The recording's scientific boundaries changed between runs.")
    common_start = {(run.segment, run.epoch): run.first + run.warmup + 1 for run in left.runs}
    for run in right.runs:
        key = run.segment, run.epoch
        common_start[key] = max(common_start[key], run.first + run.warmup + 1)
    a = tuple(event for event in left.groups if event.sample >= common_start[event.key])
    b = tuple(event for event in right.groups if event.sample >= common_start[event.key])
    agreement = match_events(a, b, tolerance_ms, left.rate, cancel)
    return None if agreement is None else (agreement, len(left.groups) - len(a), len(right.groups) - len(b))


def compare_source(reader, result, stream, tolerance_ms, cancel=None):
    """Match separately requested evidence. Native truth is opt-in at the caller."""
    validate_tolerance(tolerance_ms)
    if stream not in ("native_model_spike", "waveform_launch"):
        raise ValueError("Choose a supported source-event stream.")
    if (reader.manifest["capture_id"], reader.manifest["acquisition"]["id"]) != result.identity[:2]:
        raise ValueError("Source events must come from the analysed recording.")
    native = stream == "native_model_spike"
    if native and not reader.manifest["native_truth"]:
        return SourceAgreement(stream, False, 0, len(result.groups), (), None)

    runs = {(run.segment, run.epoch): run for run in result.runs}
    available_rows = {
        key: (np.any(run.native_available, axis=1) if native else np.ones(len(run.time_ms), dtype=bool))
        for key, run in runs.items()
    }
    for key, run in runs.items():
        available_rows[key][:run.warmup + 1] = False
    events = []
    for event in reader.iter_events(truth=native, start=result.start, stop=result.stop):
        if cancel is not None and cancel.is_set():
            return None
        if event["kind"] != stream:
            continue
        key = event["segment"], event["epoch"]
        run = runs[key]
        row = event["sample"] - run.first
        if (available_rows[key][row] and
                (not native or run.native_available[row, NEURONS.index(event["channel"])])):
            events.append(EventAnchor(tuple(event["id"]), event["sample"], run.tick + row,
                                      float(run.time_ms[row]), *key, event["channel"], event["provenance"]))
    eligible_rows = sum(int(np.count_nonzero(mask)) for mask in available_rows.values())
    if not eligible_rows:
        return SourceAgreement(stream, False, eligible_rows, len(result.groups), (), None)
    eligible_groups = tuple(group for group in result.groups
                            if available_rows[group.key][group.sample - runs[group.key].first])
    agreement = match_events(events, eligible_groups, tolerance_ms, result.rate, cancel)
    if agreement is None:
        return None
    return SourceAgreement(stream, True, eligible_rows, len(result.groups) - len(eligible_groups),
                           tuple(events), agreement)


def _agreement_data(agreement):
    return {
        "matched": [(a.id, b.id) for a, b in agreement.pairs],
        "left_only": [event.id for event in agreement.left_only],
        "right_only": [event.id for event in agreement.right_only],
        "ambiguous_right": [event.id for event in agreement.ambiguous_right],
    }


def _analysis_data(result):
    waveform = result.waveforms
    return {
        "id": result.id, "recipe": asdict(result.recipe), "excluded_warmup_rows": result.warmup_rows,
        "runs": [{"start": run.first, "stop": run.end, "segment": run.segment, "epoch": run.epoch,
                  "first_tick": run.tick, "clock": run.clock, "warmup": run.warmup}
                 for run in result.runs],
        "groups": [asdict(group) for group in result.groups],
        "waveforms": {
            "event_ids": waveform.event_ids, "displayed_ids": waveform.displayed_ids,
            "excluded": waveform.excluded, "time_ms": waveform.times_ms.tolist(),
            "mean_uV": None if waveform.mean_uV is None else waveform.mean_uV.tolist(),
        },
    }


def export_analysis(path, source_directory, result, reference=None, tolerance_ms=None,
                    comparison=None, source=None, *, measurements=None):
    """Write a derivative JSON outside the immutable acquisition directory."""
    path = Path(path).resolve()
    if path.is_relative_to(Path(source_directory).resolve()):
        raise ValueError("Save the derivative outside the source session directory.")
    data = {
        "format": "spikeling.extracellular.analysis", "algorithm": ALGORITHM,
        "capture_id": result.capture_id, "acquisition_id": result.acquisition_id,
        "accepted_interval": [result.start, result.stop], "recovered_prefix": result.recovered,
        "source_stage": "synthetic_broadband_pre_reference", "broadband_sha256": result.samples_sha256,
        "channels": CONTACTS, "voltage_unit": "µV", "model_rate_hz": result.rate,
        "recorded_live_initial_state": result.live_initial_state,
        "filter": {"family": "Butterworth", "prototype_order": 3, "overall_order": 6,
                   "notch_q": NOTCH_Q, "order": ["reference", "notch", "bandpass"],
                   "phase": "causal", "initial_state": "zero",
                   "minimum_warmup_ms": WARMUP_MS, "pole_decay_envelope": POLE_DECAY, "reset": "interval, segment, epoch, clock or missing samples"},
        "analysis_b": _analysis_data(result),
    }
    if comparison is not None:
        agreement, excluded_a, excluded_b = comparison
        data.update(analysis_a=_analysis_data(reference), matching_tolerance_ms=tolerance_ms,
                    comparison=dict(_agreement_data(agreement), warmup_only_a=excluded_a,
                                    warmup_only_b=excluded_b))
    if measurements is not None:
        data["measurements"] = measurements
    if source is not None:
        data["source_comparison"] = {
            "stream": source.stream, "available": source.available, "eligible_rows": source.eligible_rows,
            "tolerance_ms": tolerance_ms, "excluded_detections": source.excluded_detections,
            "events": [asdict(event) for event in source.events],
            "agreement": None if source.agreement is None else _agreement_data(source.agreement),
        }
    payload = canonical(data)
    with path.open("xb") as handle:
        handle.write(payload + b"\n")
