from dataclasses import replace
from hashlib import sha256
import json
from threading import Event
from types import SimpleNamespace

import numpy as np
import pytest

from spikeling_gui.features.extracellular.analysis_measurements import measure, spectrum
from spikeling_gui.features.extracellular.analysis_comparison import EventAnchor, match_events
from spikeling_gui.features.extracellular.offline_analysis import Recipe, analyse, compare, compare_source, export_analysis
from spikeling_gui.features.extracellular.offline_detection import Detector, detect_run
from spikeling_gui.features.extracellular.offline_processing import ProcessedRun, Processing
from spikeling_gui.features.extracellular.waveform_analysis import WaveformSettings, extract_waveforms

from test_extracellular_offline_processing import make_session


def run(samples, first=20, epoch=0, warmup=0):
    values = np.zeros((len(samples), 4))
    values[:, 0] = samples
    return ProcessedRun(first, 0, epoch, first + 10, "emulator_model_tick",
                        (np.arange(len(samples)) + first + 10) / 10,
                        values, np.zeros((len(samples), 3), dtype=bool), warmup)


def test_threshold_equality_refractory_and_anchored_merge():
    data = run([0, -10, 0, -14, 0, -10, 0, 0, 0, -11, 0, -22])
    data.values_uV[1, 1] = -10
    data.values_uV[4, 2] = -10
    data.values_uV[5, 3] = -10
    groups = detect_run(data, Detector(-10, .4, .4), 10000, "test")
    assert [group.sample for group in groups] == [21, 25, 29]
    assert [(item.contact, item.sample) for item in groups[0].crossings] == [
        ("E1", 21), ("E2", 21), ("E3", 24)]
    assert [(item.contact, item.sample) for item in groups[1].crossings] == [("E1", 25), ("E4", 25)]
    assert [group.sample for group in detect_run(data, Detector(-15), 10000, "strong")] == [31]


def test_no_boundary_crossing_missing_rows_or_duplicates():
    first = run([-30, -20, 0, -30, 0], warmup=1)
    second = run([-30, -30, 0, -30, 0], first=25, epoch=1)
    groups = tuple(group for item in (first, second) for group in detect_run(item, Detector(), 10000, "test"))
    assert [group.sample for group in groups] == [23, 28]
    assert len({group.id for group in groups}) == 2
    assert not detect_run(run([0, 0, 0]), Detector(), 10000, "none")
    second.values_uV[1, 2] = np.nan
    with pytest.raises(ValueError, match="finite"):
        detect_run(second, Detector(), 10000, "bad")


def test_waveforms_count_selection_mean_and_boundary_exclusions():
    a = run([0, -22, 0, 0, -30, 0, 0, -40, 0, 0, -50], warmup=1)
    b = run([0, -100, 0, -20, 0], first=31, epoch=1)
    a.values_uV[:, 1:] = np.tile([1., 2., 3.], (len(a.time_ms), 1))
    groups = tuple(group for item in (a, b)
                   for group in detect_run(item, Detector(-15, 0, .1, ("E1",)), 10000, "test"))
    selected = WaveformSettings(.2, .1, 1, 2, 4)
    waves = extract_waveforms((a, b), groups, selected, 10000)
    assert waves.selected_count == 4
    assert len(waves.event_ids) == 2 and len(waves.excluded) == 2
    assert len(waves.snippets) == 1
    np.testing.assert_allclose(waves.times_ms, [-.2, -.1, 0, .1])
    np.testing.assert_array_equal(waves.mean_uV, (a.values_uV[5:9] + b.values_uV[1:5]) / 2)


def anchor(name, tick, *, epoch=0, channel="main"):
    return EventAnchor(name, tick, tick, tick / 10, 0, epoch, channel, "fixture")


def test_one_to_one_optimal_matching_and_collisions():
    a = [anchor("late", 13), anchor("early", 9), anchor("coincident", 13, channel="aux1"),
         anchor("different_epoch", 100, epoch=1)]
    b = [anchor("B1", 11), anchor("B2", 14), anchor("B3", 100)]
    found = match_events(a, b, .2, 10000)
    assert [(x.tick, y.tick) for x, y in found.pairs] == [(9, 11), (13, 14)]
    assert [v.id for v in found.ambiguous_right] == ["B1", "B2"]
    assert {v.id for v in found.left_only} >= {"different_epoch"}
    assert [v.id for v in found.right_only] == ["B3"]
    closest = match_events((anchor("far", 9), anchor("near", 11)), (anchor("B", 11),), .2, 10000)
    assert closest.pairs[0][0].id == "near"
    with pytest.raises(ValueError, match="tolerance"):
        match_events(a, b, -1, 10000)


@pytest.mark.parametrize("native", [False, True])
def test_independent_recipes_export_and_source_provenance(tmp_path, native):
    reader, _ = make_session(tmp_path, truth=native)
    before = {p: sha256(p.read_bytes()).digest() for p in reader.directory.iterdir()}
    plain = Recipe(Processing(bandpass=None))
    cancellation = Event()
    cancellation.set()
    assert analyse(reader, 10, 400, plain, cancellation) is None
    a = analyse(reader, 10, 400, plain)
    b = analyse(reader, 10, 400, replace(plain, processing=Processing("car")))
    assert a.id != b.id and a.identity == b.identity
    again = analyse(reader, 10, 400, plain)
    assert a.id == again.id and a.groups == again.groups
    results = compare(a, b, 1)
    assert all(np.array_equal(first.values_uV, second.values_uV) for first, second in zip(a.runs, again.runs))
    proxy = compare_source(reader, a, "waveform_launch", 1)
    truth = compare_source(reader, a, "native_model_spike", 1)
    assert truth.available is native and proxy.available
    assert proxy.events[0].id != truth.events[0].id if native else not truth.events
    with pytest.raises(ValueError, match="outside"):
        export_analysis(reader.directory / "derivative.json", reader.directory, a)
    destination = tmp_path / "derivative.json"
    export_analysis(destination, reader.directory, a, b, 1, results, proxy)
    exported = json.loads(destination.read_text(encoding="utf-8"))
    assert exported["broadband_sha256"] == a.samples_sha256
    assert exported["source_comparison"]["stream"] == "waveform_launch"
    assert all(sha256(path.read_bytes()).digest() == digest for path, digest in before.items())


def test_crossing_at_file_chunk_start_keeps_previous_sample(tmp_path):
    from uuid import uuid4

    from spikeling_gui.features.extracellular.acquisition import BroadbandBlock, Capture
    from spikeling_gui.features.extracellular.session_reader import SessionReader
    from spikeling_gui.features.extracellular.session_writer import SessionWriter
    from test_extracellular_session import acquisition, block, finish

    acq = acquisition()
    writer = SessionWriter(tmp_path / "chunk-start.spikeling", Capture(uuid4(), acq, 10),
                           chunk_rows=5)
    item = block(acq, 10, 12)
    values = np.zeros((12, 4))
    values[5, 0] = -30
    values[5, 1] = -40
    assert writer.offer(replace(item, broadband=BroadbandBlock(item.inputs.span, values)))
    finish(writer)
    result = analyse(SessionReader(writer.target), 10, 22, Recipe(Processing(bandpass=None)))
    assert len(result.groups) == 1
    assert result.groups[0].sample == 15
    assert [c.contact for c in result.groups[0].crossings] == ["E1", "E2"]
    assert not result.waveforms.event_ids and len(result.waveforms.excluded) == 1


def test_polarity_records_signed_threshold_and_shares_contact_refractory():
    data = run([0, -15, 15, 0, 15])
    both = Detector(15, .2, 0, ("E1",), "both")
    groups = detect_run(data, both, 10000, "both")
    assert [(g.sample, g.crossings[0].threshold_uV) for g in groups] == [(21, -15), (24, 15)]
    assert groups[-1].crossings[0].provenance == "offline_positive_threshold"
    positive = replace(both, polarity="positive")
    assert [g.sample for g in detect_run(data, positive, 10000, "pos")] == [22, 24]


def test_measurements_and_spectrum_use_common_settled_rows():
    samples = 10 * np.sin(2 * np.pi * 50 * np.arange(15000) / 10000)
    waveforms = SimpleNamespace(mean_uV=np.array([[0] * 4, [2] * 4]), event_ids=("a",))
    a = SimpleNamespace(runs=(run(samples, warmup=0),), rate=10000, waveforms=waveforms)
    b = SimpleNamespace(runs=(run(samples / 2, warmup=100),), rate=10000, waveforms=waveforms)
    assert not measure(a, b, (20, 30))["baseline_available"]
    measurements = measure(a, b, (120, 320))
    np.testing.assert_allclose(measurements["b"]["baseline_rms_uV"][0], 5 / np.sqrt(2))
    assert measurements["b"]["mean_waveform_peak_to_peak_uV"] == [2] * 4
    start, stop, f, power_a, power_b = spectrum(a, b, 0)
    assert (start, stop) == (120, 15020)
    assert f[power_b.argmax()] == pytest.approx(50, abs=f[1])
    np.testing.assert_allclose(power_b, power_a / 4)
