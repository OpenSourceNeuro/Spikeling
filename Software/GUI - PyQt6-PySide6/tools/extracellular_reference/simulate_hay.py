"""Reproduce Hay ModelDB 139653 currents. Run in a fresh process per recipe."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

import numpy as np

MODEL_COMMIT = "50a4aab3ce5c295ad16a134c5d9261b7cc3fbe58"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--dt", type=float, default=.025)
    parser.add_argument("--refine", action="store_true")
    parser.add_argument("--weight", type=float, default=.09)
    args = parser.parse_args()
    model, output = args.model.resolve(), args.output.resolve()
    head = subprocess.check_output(["git", "-C", model, "rev-parse", "HEAD"], text=True).strip()
    if head != MODEL_COMMIT or subprocess.check_output(
        ["git", "-C", model, "status", "--porcelain", "--untracked-files=no"], text=True
    ):
        raise ValueError("Expected the pinned, unmodified ModelDB source")
    inputs = [*sorted(model.glob("mod/*.mod")),
              *(model / path for path in ("models/L5PCtemplate.hoc", "models/L5PCbiophys3.hoc",
                                           "morphologies/cell1.asc"))]
    hashes = {p.relative_to(model).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
    os.chdir(model)
    from neuron import h, __version__ as neuron_version

    if neuron_version != "9.0.1":
        raise ValueError("Hay recipe requires NEURON 9.0.1")

    for name in ("stdrun.hoc", "import3d.hoc", "models/L5PCbiophys3.hoc", "models/L5PCtemplate.hoc"):
        h.load_file(name)
    cell = h.L5PCtemplate("morphologies/cell1.asc")
    sections = list(cell.all)
    if args.refine:
        # Transfer fitted densities from the original segment centres when splitting by three.
        for sec in sections:
            sec.nseg *= 3
    h.define_shape()
    soma = cell.soma[0]
    axon = cell.axon[0]
    origin = np.array([np.interp(.5 * soma.L, [soma.arc3d(i) for i in range(soma.n3d())],
                                  [getattr(soma, axis)(i) for i in range(soma.n3d())])
                       for axis in ("x3d", "y3d", "z3d")])
    # Model has two synthetic 30 µm sections. Fix a declared geometric embedding
    # in imported coordinates. It is a forward-model assumption, not reconstructed axon.
    for index in range(2):
        sec = cell.axon[index]
        sec.pt3dclear()
        for level in (index, index + 1):
            sec.pt3dadd(*(origin + np.array([0., -30. * level, 0.])), 1.)
    endpoints, radii, segments, axon_segments = [], [], [], []
    axonal = list(cell.axonal)
    for sec in sections:
        arc = np.array([sec.arc3d(i) for i in range(sec.n3d())])
        xyz = np.array([[getattr(sec, axis)(i) for i in range(sec.n3d())]
                        for axis in ("x3d", "y3d", "z3d")])
        for seg in sec:
            margin = .5 / sec.nseg
            distances = sec.L * np.array([seg.x - margin, seg.x + margin])
            ends = np.array([np.interp(distances, arc, row) for row in xyz]).T
            samples = (arc >= distances[0]) & (arc <= distances[1])
            diameters = np.array([sec.diam3d(i) for i in range(sec.n3d())])
            chord = ends[1] - ends[0]
            if not np.linalg.norm(chord):
                raise ValueError(f"Zero-length segment chord in {sec.name()}")
            # Expand the exclusion envelope to contain the original pt3d centreline.
            relative = xyz[:, samples].T - ends[0]
            fraction = np.clip(relative @ chord / (chord @ chord), 0, 1)
            deviation = np.linalg.norm(relative - fraction[:, None] * chord, axis=1)
            radius = .5 * max(seg.diam, np.interp(distances, arc, diameters).max(),
                              diameters[samples].max(initial=0))
            endpoints.append(ends - origin)
            radii.append(radius + deviation.max(initial=0))
            segments.append(seg)
            if sec in axonal:
                axon_segments.append(len(segments) - 1)
    h.celsius = 34
    h.CVode().active(0)
    h.CVode().use_fast_imem(1)
    h.dt = args.dt
    syn = h.Exp2Syn(soma(.5))
    syn.tau1, syn.tau2, syn.e = .1, .6, 0
    nc = h.NetCon(None, syn)
    nc.weight[0] = args.weight
    h.finitialize(-80)
    h.continuerun(350)
    nc.event(360)
    times, vm, vax, currents = [], [], [], []
    while h.t < 390:
        times.append(h.t)
        vm.append(soma(.5).v)
        vax.append(axon(.5).v)
        currents.append([seg.i_membrane_ for seg in segments])
        h.fadvance()
    times, vm, vax, currents = map(np.asarray, (times, vm, vax, currents))
    def landmarks(voltage):
        indices = np.flatnonzero((voltage[:-1] < 0) & (voltage[1:] >= 0))
        return [(times[k] - voltage[k] * (times[k + 1] - times[k]) /
                 (voltage[k + 1] - voltage[k])) for k in indices]

    metadata = dict(compiler=subprocess.check_output(["g++", "--version"], text=True).splitlines()[0], commit=head, source_sha256=hashes, neuron=neuron_version,
                    numpy=np.__version__, temperature_C=34, synapse_weight_uS=args.weight,
                    dt_ms=args.dt, refined=args.refine, soma_events_ms=landmarks(vm),
                    axon_events_ms=landmarks(vax), axon_segments=axon_segments)
    if not np.isfinite(currents).all() or not metadata["soma_events_ms"]:
        raise ValueError(f"Expected a somatic event. Observed {metadata['soma_events_ms']}")
    np.savez(output, time_ms=times, soma_mV=vm, axon_mV=vax, currents_nA=currents,
             endpoints_um=endpoints, radii_um=radii, metadata=json.dumps(metadata, sort_keys=True))
    print({key: val for key, val in metadata.items() if key != "source_sha256"},
          "segments", len(segments), "current imbalance (nA)", abs(currents.sum(axis=1)).max())


if __name__ == "__main__":
    main()
