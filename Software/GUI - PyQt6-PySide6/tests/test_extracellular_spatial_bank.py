import hashlib
import json
from pathlib import Path
import shutil

import numpy as np
import pytest

from spikeling_gui.features.extracellular.spatial_bank import BankError, SpatialBank, world_to_cell
from tools.extracellular_reference.make_fixture import voltage

ASSET = Path(__file__).resolve().parent / "fixtures/extracellular/analytic-regression-v1"
POSE = np.array([[.4, .7, .8], [2, 2, 2], [0, 0, 0], [1, -1.5, 1.5]])
I = np.eye(3)


def open_bank(path=ASSET):
    return SpatialBank(path, allow_provisional=True)


def test_node_interior_and_face():
    bank = open_bank()
    expected = voltage(POSE).T
    actual = bank.evaluate_pose("main", [0]*3, I, POSE)
    assert actual.dtype == np.float64
    np.testing.assert_allclose(actual, expected, atol=1e-14, rtol=0)
    np.testing.assert_array_equal(bank.time_ms, [-.2, -.1, 0., .1, .2])
    actual[:] = 0
    np.testing.assert_allclose(bank.evaluate_pose("main", [0]*3, I, POSE), expected, atol=1e-14, rtol=0)
    assert open_bank().manifest_sha256 == bank.manifest_sha256
    with pytest.raises(BankError, match="not approved"):
        SpatialBank(ASSET)


def test_mask_and_extrapolation():
    bank = open_bank()
    for point, text in (([-.01, -1, -1], "Unsupported"), ([2.01, 0, 0], "Outside")):
        pose = POSE.copy()
        pose[1] = point
        with pytest.raises(BankError, match=f"aux2 / E2.*{text}"):
            bank.evaluate_pose("aux2", [0]*3, I, pose)
    # Exactly x=0 belongs to the positive-side stencil.
    np.testing.assert_array_equal(bank._lookup([0, -2, -2]), voltage([[0, -2, -2]])[0])


def test_rotations_and_contact_order():
    bank = open_bank()
    r = np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1]])
    s = np.array([9., 12., -3.])
    np.testing.assert_allclose(world_to_cell(POSE @ r.T + s, s, r), POSE)
    np.testing.assert_allclose(bank.evaluate_pose("main", s, r, POSE @ r.T+s), voltage(POSE).T,
                               atol=1e-14, rtol=0)
    q = abs(POSE)
    rotated_probe = q @ r.T
    np.testing.assert_allclose(bank.evaluate_pose("main", s, I, rotated_probe+s),
                               voltage(rotated_probe).T, atol=1e-14, rtol=0)
    with pytest.raises(BankError, match="proper rotation"):
        world_to_cell(POSE, s, -I)


@pytest.mark.parametrize("problem", ["missing", "checksum", "version", "nonfinite", "shape", "dtype", "pickle"])
def test_corruption(tmp_path, problem):
    directory = shutil.copytree(ASSET, tmp_path / ASSET.name)
    manifest = directory / "manifest.json"
    data = json.loads(manifest.read_text())
    path = directory / "voltage_uV.npy"
    if problem == "missing":
        path.unlink()
    elif problem == "checksum":
        path.write_bytes(path.read_bytes()[:-1]+b"\xff")
    elif problem == "version":
        data["version"] = 2
    else:
        field = np.load(path)
        if problem == "nonfinite":
            field[0, 0, 0, 0] = np.nan
        elif problem == "shape":
            field = field[:-1]
        elif problem == "dtype":
            field = field.astype(">f4")
        else:
            field = field.astype(object)
        np.save(path, field)
        data["files"][path.name] = dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                                       bytes=path.stat().st_size)
    manifest.write_text(json.dumps(data))
    with pytest.raises(BankError):
        open_bank(directory)


def test_reference_preserves_real_differential_voltage():
    from spikeling_gui.features.extracellular.offline_processing import Processing, apply_reference

    bank = open_bank()
    config = Processing("car", bandpass=None)
    symmetric = bank.evaluate_pose("main", [0]*3, I, np.repeat(POSE[:1], 4, axis=0))
    np.testing.assert_array_equal(apply_reference(symmetric, config), 0)
    distinct = bank.evaluate_pose("main", [0]*3, I, POSE)
    residual = apply_reference(distinct, config)
    np.testing.assert_allclose(residual.sum(axis=1), 0, atol=1e-14)
    assert np.max(abs(residual)) > 1


def test_launch_fixture_is_consistent():
    fixture = json.loads((ASSET.parent / "phase3c-launches-v1.json").read_text())
    expected = fixture["expected_rows"]
    boundaries = fixture["segment_boundaries"] + [len(expected)]
    kernels = fixture["kernel_by_pose"]
    actual = np.zeros_like(expected)
    for tick, _ in fixture["launches_tick_source"]:
        pose_name = [pose for effective, pose in fixture["pose_changes"] if effective <= tick][-1]
        next_boundary = min(b for b in boundaries if b > tick)
        end = min(next_boundary, tick + len(kernels[pose_name]))
        actual[tick:end] += kernels[pose_name][:end-tick]
    np.testing.assert_array_equal(actual, expected)
    assert all(sum(schedule) == len(expected) for schedule in fixture["block_schedules_rows"])


def test_line_integral_units_and_current_sign():
    # 1 nA uniformly distributed from z=-10 to +10 µm, observed 20 µm away.
    # Exact transfer is asinh(10/20)/(10 µm), times the SI unit conversion.
    from tools.extracellular_reference.build_bank import Reference

    reference = Reference.__new__(Reference)
    reference.segments = np.array([[[0, 0, -10], [0, 0, 10]]])
    reference.resampled = np.array([[1., -1.]])
    expected = (1000 / (4 * np.pi * .3)) * np.arcsinh(.5) / 10
    np.testing.assert_allclose(reference.independent([[20, 0, 0]]), [[expected, -expected]],
                               atol=1e-12, rtol=0)
