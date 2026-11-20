"""Open direct-reference validation, detector diagnostics and load benchmarks."""
import argparse
from itertools import product
import json
from pathlib import Path
import resource
from time import perf_counter
import zipfile

import numpy as np
from scipy.signal import sosfilt
from scipy.spatial.transform import Rotation

from build_bank import Reference, TIME
from spikeling_gui.features.extracellular.offline_detection import Detector, detect_run
from spikeling_gui.features.extracellular.offline_processing import Processing, ProcessedRun, apply_reference
from spikeling_gui.features.extracellular.spatial_bank import BankError, SpatialBank

IDENTITY = np.eye(3)
R = 25 / np.sqrt(2)
TIP = R * np.array([[0,-1,0], [1,0,0], [0,1,0], [-1,0,0]])
POSES = {
    "A": TIP + [0, 0, 40],
    "B": Rotation.from_euler("x", 32, degrees=True).apply(TIP) + [15, 0, 40],
    "C": TIP + [0, 25, 20],
    "D": TIP + [30, 25, 20],
    "E": Rotation.from_euler("z", 15, degrees=True).apply(TIP) + [15, 25, 30],
}
SEEDS = tuple(range(192, 204))


def validation(bank, ref, finer, refined):
    rng = np.random.default_rng(375804)
    strata = {
        "near": [np.array(sign) * rng.uniform(10, 30, 3) for sign in product((-1, 1), repeat=3)],
        "far": [np.array(sign) * rng.uniform(39, 58, 3) for sign in product((-1, 1), repeat=3)],
        "interior": rng.uniform(-57, 57, (48, 3)),
        "faces_edges": [[0, 0, 45], [0, 15, 45], [0, 0, 60], [60, 60, 60], [60, -60, 15]],
    }
    result = {}
    for label, points in strata.items():
        estimates, supported = [], []
        for point in points:
            try:
                estimates.append(bank._lookup(point))
            except BankError:
                continue
            supported.append(point)
        item = {"tested": len(points), "supported": len(supported)}
        if supported:
            actual = ref.independent(supported)
            error = np.asarray(estimates) - actual
            per_position = abs(error).max(axis=1)
            relative = np.linalg.norm(error, axis=1) / np.linalg.norm(actual, axis=1)
            item.update(abs_uV_q50_q95_max=np.quantile(per_position, [.5,.95,1]).tolist(),
                        relative_q50_q95_max=np.quantile(relative, [.5,.95,1]).tolist(),
                        direct_agreement_uV=float(abs(actual - ref.direct(supported)).max()),
                        time_refinement_max_uV=float(abs(actual - finer.independent(supported)).max()),
                        space_time_refinement_max_uV=float(abs(actual - refined.independent(supported)).max()))
        result[label] = item
    return result


def characterise(wave):
    peaks = wave[np.argmax(abs(wave), axis=0), np.arange(4)]
    ranges = np.ptp(wave, axis=0)
    width = []
    for channel in wave.T:
        peak = np.argmax(abs(channel))
        relative = channel * np.sign(channel[peak]) >= abs(channel[peak]) / 2
        left = peak
        right = peak
        while left > 0 and relative[left-1]:
            left -= 1
        while right < len(channel)-1 and relative[right+1]:
            right += 1
        width.append((right-left+1)/10)
    return dict(peak_uV=peaks.tolist(), range_uV=ranges.tolist(), width_rows_ms=width,
                E1_E4_range_ratio=float(ranges[0]/ranges[3]),
                peak_time_ms=TIME[np.argmax(abs(wave), axis=0)].tolist())


def detection(wave, reference, threshold, sd):
    config = Processing(reference)
    starts = np.arange(700, 7000, 700)
    centres = starts + 30
    result = np.zeros(4, dtype=int)
    for seed in SEEDS:
        rng = np.random.default_rng(seed)
        rows = rng.normal(0, sd[0], (7200, 4)) + rng.normal(0, sd[1], (7200, 1))
        for start in starts:
            rows[start:start + len(wave)] += wave
        filtered = sosfilt(config.design(10000), apply_reference(rows, config), axis=0)
        run = ProcessedRun(0, 0, 0, 0, "pilot", np.arange(len(rows))/10, filtered,
                           np.ones((len(rows), 3), dtype=bool), 100)
        groups = detect_run(run, Detector(threshold_uV=threshold), 10000, "3B-open")
        ticks = np.array([g.tick for g in groups])
        counts = np.array([np.count_nonzero((ticks >= tick-10) & (ticks <= tick+20))
                           for tick in centres])
        matched = np.count_nonzero(counts)
        inside = counts.sum()
        result += [matched, len(centres)-matched, inside-matched, len(ticks)-inside]
    return dict(zip(("matches", "misses", "extra_in_window", "outside_windows"), result.tolist()))


def calibrate(args):
    started = perf_counter()
    bank = SpatialBank(args.bank, allow_provisional=True)
    load_ms = (perf_counter() - started)*1000
    ref, finer, refined = (Reference(path) for path in (args.reference,args.finer,args.refined))
    results = dict(validation=validation(bank, ref, finer, refined), poses={})
    positions = []
    for name, pose in POSES.items():
        try:
            signal = bank.evaluate_pose("main", np.zeros(3), IDENTITY, pose)
        except BankError as exc:
            results["poses"][name] = {"unsupported": str(exc)}
            continue
        positions.append(pose)
        actual = ref.independent(pose).T
        residual = apply_reference(signal, Processing("car"))
        candidates = {
            "none": characterise(signal),
            "car": characterise(residual),
            "differential_energy": float((residual**2).sum() / (signal**2).sum()),
            "bank_error_uV": float(abs(signal-actual).max()),
            "time_error_uV": float(abs(actual-finer.independent(pose).T).max()),
            "space_time_error_uV": float(abs(actual-refined.independent(pose).T).max()),
            "direct_metrics": characterise(actual),
            "refined_metrics": characterise(refined.independent(pose).T),
            "finer_time_metrics": characterise(finer.independent(pose).T),
            "detector": {},
        }
        for mode, threshold, sd in product(("none","car"), (-15., -8., -4.), ((0,0), (1,2), (5,5))):
            candidates["detector"][str((mode, threshold, sd))] = detection(signal, mode, threshold, sd)
        results["poses"][name] = candidates
    metrics = {"verified_load_ms": load_ms, "unpacked_bytes": sum(p.stat().st_size for p in args.bank.iterdir())}
    with zipfile.ZipFile(args.output.with_suffix(".zip"), "w", zipfile.ZIP_DEFLATED) as zipped:
        for p in sorted(args.bank.iterdir()):
            zipped.write(p, p.name)
    metrics["deflated_bytes"] = args.output.with_suffix(".zip").stat().st_size
    if positions:
        pose = positions[0]
        for count in (1, 4, 12):
            trials = []
            for _ in range(150):
                started = perf_counter()
                for point in np.tile(pose, (3, 1))[:count]:
                    bank._lookup(point)
                trials.append((perf_counter()-started)*1e6)
            metrics[f"uncached_{count}_contact_us_p50_p95"] = np.quantile(trials,[.5,.95]).tolist()
    metrics["peak_process_rss_KiB_linux"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    results["benchmarks"] = metrics
    results["bank_sha256"] = bank.manifest_sha256
    results["noise_only"] = {str((mode, threshold, sd)): detection(np.zeros((len(TIME),4)), mode, threshold, sd)
                             for mode, threshold, sd in product(("none","car"),(-15.,-8.,-4.),((1,2),(5,5)))}
    args.output.write_text(json.dumps(results, indent=2, sort_keys=True)+"\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("bank", "reference", "finer", "refined", "output"):
        parser.add_argument(key, type=Path)
    calibrate(parser.parse_args())
