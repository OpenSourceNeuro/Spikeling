from hashlib import sha256

import numpy as np
import pytest
from scipy.signal import sosfilt

from spikeling_gui.features.extracellular.acquisition import Capture, Discontinuity
from spikeling_gui.features.extracellular.offline_processing import Processing, apply_reference, process_interval
from spikeling_gui.features.extracellular.session_reader import SessionReader
from spikeling_gui.features.extracellular.session_writer import SessionWriter

from test_extracellular_session import acquisition, block, finish
from uuid import uuid4


def make_session(tmp_path, *, truth=False):
    source = acquisition()
    writer = SessionWriter(tmp_path / "offline.spikeling", Capture(uuid4(), source, 10),
                           chunk_rows=41, include_truth=truth)
    gap = Discontinuity("fixture gap", 260, missing_model_steps=20,
                        previous_tick=359, next_tick=380, acquisition=source, segment=0)
    blocks = [
        block(source, 10, 130, events=(("native_model_spike", 30, "main", None),
                                       ("waveform_launch", 30, "main", None))),
        block(source, 140, 120, epoch_id=1, effective=140),
        block(source, 260, 140, tick=380, segment=1, epoch_id=2, effective=260),
    ]
    for item in (*blocks[:2], gap, blocks[2]):
        assert writer.offer(item)
    finish(writer)
    return SessionReader(writer.target), blocks


def test_reference_identity_car_and_original_unchanged():
    original = np.array([[1., 3., 7., 9.], [-1., 5., 0., 12.]])
    copy = original.copy()
    identity = apply_reference(original, Processing(bandpass=None))
    assert not np.shares_memory(original, identity)
    np.testing.assert_array_equal(identity, original)
    car = apply_reference(original, Processing("car", ("E1", "E2"), None))
    np.testing.assert_array_equal(car, [[-1, 1, 5, 7], [-3, 3, -2, 10]])
    np.testing.assert_array_equal(original, copy)


@pytest.mark.parametrize("band", [(0, 3000), (3000, 100), (300, 5000), (float("nan"), 100)])
def test_filter_rejects_invalid_bounds(band):
    with pytest.raises(ValueError, match="Bandpass"):
        Processing(bandpass=band).design(10000)


@pytest.mark.parametrize("channels", [(), ("E1",), ("E1", "E1"), ("E2", "E1")])
def test_car_rejects_invalid_contacts(channels):
    with pytest.raises(ValueError, match="CAR"):
        apply_reference(np.ones((2, 4)), Processing("car", channels, None))


def test_chunk_state_epoch_reset_and_exact_broadband(tmp_path):
    reader, blocks = make_session(tmp_path)
    original = {file: sha256(file.read_bytes()).digest() for file in reader.directory.iterdir()}
    result = list(process_interval(reader, 25, 385, Processing()))
    assert [(item.first, item.end, item.epoch, item.segment, item.tick) for item in result] == [
        (25, 140, 0, 0, 125), (140, 260, 1, 0, 240), (260, 385, 2, 1, 380),
    ]
    sos = Processing().design(10000)
    shapes = [slice(15, None), slice(None), slice(0, 125)]
    for run, source, section in zip(result, blocks, shapes):
        expected = sosfilt(sos, source.broadband.contacts_uV[section], axis=0)
        np.testing.assert_array_equal(run.values_uV, expected)
        assert run.warmup == 100 and not run.values_uV.flags.writeable
    identity = list(process_interval(reader, 25, 385, Processing(bandpass=None)))
    for run, source, section in zip(identity, blocks, shapes):
        np.testing.assert_array_equal(run.values_uV, source.broadband.contacts_uV[section])
        assert run.warmup == 0
    assert all(sha256(path.read_bytes()).digest() == digest for path, digest in original.items())
    assert all(np.array_equal(a.values_uV, b.values_uV)
               for a, b in zip(result, process_interval(reader, 25, 385, Processing())))


def test_narrow_filters_extend_warmup(tmp_path):
    reader, _ = make_session(tmp_path)
    result = list(process_interval(reader, 10, 400, Processing(bandpass=(1, 100))))
    assert all(run.warmup == len(run.time_ms) for run in result)


def test_single_reference_and_mains_notch():
    from scipy.signal import sosfreqz

    samples = np.array([[2, 3, 4, 6], [1, 2, 3, 4]], dtype=float)
    recipe = Processing("single", ("E2",), None, 50)
    np.testing.assert_array_equal(apply_reference(samples, recipe), samples - samples[:, 1:2])
    _, response = sosfreqz(recipe.design(10000), worN=[40, 50, 60], fs=10000)
    assert abs(response[1]) < 1e-8
    assert abs(response[0]) > .95 and abs(response[2]) > .95
