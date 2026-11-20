"""Build an offline candidate field from a preserved multicompartment run."""
import argparse
from hashlib import sha256
from itertools import product
from functools import lru_cache
import json
from pathlib import Path
import tempfile


import numpy as np
import scipy
from scipy.signal import butter, sosfiltfilt

from spikeling_gui.features.extracellular.recording_schema import publish_directory
from spikeling_gui.features.extracellular.spatial_bank import FILES, FORMAT

SIGMA = .3
# This box covers the soma and proximal sites only. It is explored, not approved.
LANDMARK = 30
TIME = (np.arange(101) - LANDMARK) / 10
CLEARANCE_UM = 5.


@lru_cache(maxsize=1)
def line_source():
    import lfpcalc

    expected = "11c99c3840ae46bafe197fa8ff3838d2f5a799ca08ae512f9ca46ad2c6f62534"
    if sha256(Path(lfpcalc.__file__).read_bytes()).hexdigest() != expected:
        raise ValueError("Expected lfpcalc.py from the pinned LFPyKit revision")
    return lfpcalc.calc_lfp_linesource


class Reference:
    def __init__(self, file):
        with np.load(file, allow_pickle=False) as model:
            self.meta = json.loads(model["metadata"].item())
            self.segments = model["endpoints_um"]
            self.radii = model["radii_um"]
            self.sha256 = sha256(Path(file).read_bytes()).hexdigest()
            event = self.meta["soma_events_ms"][0]
            if any(other <= event + TIME[-1] for other in self.meta["soma_events_ms"][1:]):
                raise ValueError("Second somatic spike within the reference crop")
            times = model["time_ms"] - event
            if times[0] > -8 or times[-1] < TIME[-1]:
                raise ValueError("Reference has incomplete baseline or crop")
            self.currents = model["currents_nA"].T
        baseline = self.currents[:, (times >= -8) & (times < -6)].mean(axis=1)
        self.currents -= baseline[:, None]
        sos = butter(6, 4000, fs=1000 / self.meta["dt_ms"], output="sos")
        filtered = sosfiltfilt(sos, self.currents, axis=1)
        self.resampled = np.array([np.interp(TIME, times, trace) for trace in filtered])

    def clearance(self, point):
        start, end = self.segments.transpose(1, 0, 2)
        delta = end - start
        fraction = np.clip(np.einsum("ij,ij->i", point - start, delta)
                           / np.einsum("ij,ij->i", delta, delta), 0., 1.)
        return np.min(np.linalg.norm(point - start - fraction[:, None] * delta, axis=1) - self.radii)

    def direct(self, points):
        # Only the pinned LFPyKit numerical forward routine is needed here.
        calculate = line_source()

        x, y, z = self.segments.transpose(2, 0, 1)
        coeff = [calculate(x, y, z, *p, SIGMA, np.full(len(x), 1e-8)) for p in points]
        return 1000 * np.array(coeff) @ self.resampled

    def independent(self, points):
        """Independent Gauss–Legendre integral of the finite line kernel."""
        nodes, weights = np.polynomial.legendre.leggauss(96)
        a, b = self.segments.transpose(1, 0, 2)
        sample = (.5 * (1 - nodes))[None, :, None] * a[:, None] + (
            .5 * (1 + nodes))[None, :, None] * b[:, None]
        inverse_distance = np.array([(.5 / np.linalg.norm(p - sample, axis=2)) @ weights
                                     for p in points])
        return (1000 / (4 * np.pi * SIGMA)) * inverse_distance @ self.resampled


def build(reference, output, step):
    axes = tuple(np.linspace(-60, 60, round(120 / step) + 1).astype("<f8") for _ in range(3))
    centres = tuple((axis[1:] + axis[:-1]) / 2 for axis in axes)
    half_diagonal = np.linalg.norm([np.max(np.diff(axis)) / 2 for axis in axes])
    valid = np.array([reference.clearance(p) >= CLEARANCE_UM + half_diagonal
                      for p in product(*centres)]).reshape(tuple(len(axis) for axis in centres))
    nodes = np.zeros(tuple(len(axis) for axis in axes), dtype=bool)
    for corner in product((0, 1), repeat=3):
        nodes[tuple(slice(i, i + n) for i, n in zip(corner, valid.shape))] |= valid
    x = np.column_stack([axis[index] for axis, index in zip(axes, np.nonzero(nodes))])
    field = np.zeros((*nodes.shape, len(TIME)), dtype="<f4")
    max_storage_error = 0.
    for start in range(0, len(x), 256):
        selected = slice(start, start + 256)
        samples = reference.direct(x[selected])
        rounded = samples.astype("<f4")
        field[tuple(index[selected] for index in np.nonzero(nodes))] = rounded
        max_storage_error = max(max_storage_error, float(abs(samples - rounded).max()))
    with tempfile.TemporaryDirectory(dir=output.parent) as temp:
        candidate = Path(temp) / output.name
        candidate.mkdir()
        inventory = {}
        for name, values in zip(FILES, (*axes, TIME.astype("<f8"), field, valid)):
            path = candidate / name
            np.save(path, values, allow_pickle=False)
            inventory[name] = dict(bytes=path.stat().st_size, sha256=sha256(path.read_bytes()).hexdigest())
        manifest = dict(
            format=FORMAT, version=1, id=output.name, status="provisional",
            units=dict(space="µm", time="ms", voltage="µV"), reference="infinity", rate_hz=10000,
            conductivity_S_m=SIGMA, landmark_index=LANDMARK, files=inventory,
            model=dict(accession="ModelDB 139653", morphology="cell1.asc", biophysics="L5PCbiophys3",
                       **reference.meta),
            frame=dict(origin="soma(0.5)", axes="imported right-handed Neurolucida XYZ",
                       axon="synthetic 60 µm stub along local -Y"),
            generator=dict(recipe="hay-linesource-v1", numpy=np.__version__, scipy=scipy.__version__,
                           lfpykit_commit="b729bc650fa060e3e86048e12344cd3fe8524250",
                           reference_sha256=reference.sha256),
            resampling=dict(baseline_ms=[-8,-6], lowpass_Hz=4000, order=6,
                            method="zero-phase Butterworth SOS, linear sampling on aligned grid",
                            crop_ms=[float(TIME[0]), float(TIME[-1])]),
            support=dict(clearance_um=CLEARANCE_UM, cube_um=[-60,60], grid_spacing_um=120/(len(axes[0])-1),
                         rule="cell-centre clearance from segment chords >= half diagonal plus clearance"),
            calibration=dict(revision="3B-provisional", valid_cells=int(valid.sum()),
                             storage_max_abs_error_uV=max_storage_error,
                             tail_abs_max_uV=float(abs(field[..., -1]).max()),
                             start_abs_max_uV=float(abs(field[..., 0]).max()), approved_poses=[]),
            licensing=dict(status="unresolved", release=False, citation="Hay et al. 2011, ModelDB 139653"),
        )
        (candidate / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
        publish_directory(candidate, output)
    print({k: v for k, v in manifest["calibration"].items()})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--step", type=float, choices=(5., 10.), default=5.)
    args = parser.parse_args()
    build(Reference(args.input), args.output, args.step)


if __name__ == "__main__":
    main()
