"""Create a compact signed field and hand-specified launch fixture for regression."""
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

from spikeling_gui.features.extracellular.spatial_bank import FILES, FORMAT


def voltage(points):
    x, y, z = np.moveaxis(np.asarray(points), -1, 0)
    return np.stack((-x + y*z, 2*x - y + z, -3*z + x*y, y - x*z, z + x*y), axis=-1)


def write_fixture(directory):
    directory = Path(directory)
    directory.mkdir(parents=True)
    axis = np.array([-2., 0., 2.], dtype="<f8")
    grid = np.stack(np.meshgrid(axis, axis, axis, indexing="ij"), axis=-1)
    valid = np.ones((2, 2, 2), dtype=bool)
    valid[0, 0, 0] = False
    files = {}
    for name, array in zip(FILES, (axis, axis, axis, (np.arange(5, dtype="<f8")-2)/10,
                                    voltage(grid).astype("<f4"), valid)):
        path = directory / name
        with path.open("xb") as stream:
            np.save(stream, array, allow_pickle=False)
        files[name] = dict(sha256=sha256(path.read_bytes()).hexdigest(), bytes=path.stat().st_size)
    metadata = dict(format=FORMAT, version=1, id=directory.name, status="provisional", files=files,
                    units=dict(space="µm", time="ms", voltage="µV"), reference="infinity",
                    rate_hz=10000, conductivity_S_m=.3, landmark_index=2,
                    model={"id": "analytic-trilinear-fixture"},
                    frame={"origin": "arbitrary", "axes": "right-handed XYZ"},
                    generator={"id": "make_fixture.py"}, resampling={"method": "none"},
                    licensing={"asset": "original mathematical fixture, repository terms"},
                    support={"rule": "one masked cell"}, calibration={"status": "test only"})
    (directory / "manifest.json").write_text(json.dumps(metadata, indent=2, sort_keys=True)+"\n")


if __name__ == "__main__":
    import sys

    write_fixture(sys.argv[1])
