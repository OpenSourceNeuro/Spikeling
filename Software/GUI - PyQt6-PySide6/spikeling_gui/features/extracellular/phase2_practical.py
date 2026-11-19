"""Generate the introductory practical using existing Spikeling models."""
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

import numpy as np

from .acquisition import Capture
from .offline_analysis import Recipe, analyse, compare, compare_source
from .offline_processing import Processing
from .session_reader import SessionReader
from .session_writer import SessionWriter

ROWS = 3200
MODEL_PARAMETERS = (.02, .2, -65, 8)
INJECTED_CURRENT = 10.0


def create_session(window, target):
    """Capture one firing soma equidistant from four contacts."""
    from ..emulator.models import IntrinsicPharmacology

    graph = window.extracellular_graph
    graph.set_source_mode("emulator")
    graph._rng = np.random.default_rng(17)
    graph.connect()
    graph._rx_timer.stop()
    graph.set_signal_mode("template")
    graph.CAR(False)
    graph.set_geometry_from_positions(
        [(-12.5, -12.5, 0), (12.5, -12.5, 0), (12.5, 12.5, 0), (-12.5, 12.5, 0)],
        [(0, 0, 15), (-20, 45, 10), (55, -35, 10)],
    )
    graph._extracellular_params.update(baseline_noise_uV=0, shared_noise_uV=0, hum_noise_uV=0)
    writer = SessionWriter(target, Capture(uuid4(), graph.acquisition, 0), include_truth=True)
    voltage = -65.0
    recovery = MODEL_PARAMETERS[1] * voltage
    model = IntrinsicPharmacology(voltage)
    try:
        for first in range(1, ROWS + 1, 400):
            ticks = list(range(first, min(first + 400, ROWS + 1)))
            packets, flags = [], []
            for tick in ticks:
                voltage, recovery, spike = model.step(voltage, recovery, INJECTED_CURRENT,
                                                      MODEL_PARAMETERS, 0.1, (0.0,) * 4)
                packets.append([tick / 10, 30.0 if spike else voltage, 0.0,
                                INJECTED_CURRENT, -65.0, 0.0, -65.0, 0.0, 0.0])
                flags.append([int(spike), 0, 0])
            graph.on_emulator_data(packets, ticks=ticks, events=flags, aux_enabled=(False, False),
                                   source_settings=("phase2_practical", MODEL_PARAMETERS, INJECTED_CURRENT))
            if not writer.offer(graph.latest_block):
                raise RuntimeError(writer.error or "Practical capture rejected an acquisition block.")
    finally:
        writer.stop("Phase 2 practical")
        graph.disconnect()
    if not writer.wait(20) or writer.status != "complete":
        raise RuntimeError(writer.error or "Practical session did not finish saving.")
    return SessionReader(target)


def verify(reader):
    before = {file.name: sha256(file.read_bytes()).digest() for file in reader.directory.iterdir()}
    recipe_a = Recipe(Processing(bandpass=None))
    recipe_b = replace(recipe_a, processing=Processing("car", bandpass=None))
    a, b = [analyse(reader, reader.first_index, reader.end_index, recipe) for recipe in (recipe_a, recipe_b)]
    agreement, _, _ = compare(a, b, 2.0)
    source_a, source_b = [compare_source(reader, result, "native_model_spike", 2.0) for result in (a, b)]
    if not (a.identity == b.identity and a.groups and not b.groups
            and len(source_a.agreement.pairs) == len(source_a.events) == len(a.groups)
            and source_a.events == source_b.events and len(agreement.left_only) == len(a.groups)
            and all(sha256((reader.directory / name).read_bytes()).digest() == digest
                    for name, digest in before.items())):
        raise RuntimeError("The measured teaching fixture did not reproduce the expected cancellation.")
    peaks = [max(float(np.max(np.abs(run.values_uV))) for run in result.runs) for result in (a, b)]
    return {
        "rows": reader.sample_count, "native_source_events": len(source_a.events),
        "A_detections": len(a.groups), "B_detections": len(b.groups), "A_source_matches": len(source_a.agreement.pairs),
        "B_source_only": len(source_b.agreement.left_only), "A_waveforms": len(a.waveforms.event_ids),
        "A_peak_uV": peaks[0], "B_peak_uV": peaks[1], "broadband_sha256": a.samples_sha256,
    }


def main():
    from argparse import ArgumentParser
    import json

    from PySide6.QtWidgets import QApplication

    from spikeling_gui.main_window import MainWindow

    parser = ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="New .spikeling directory under an existing folder")
    args = parser.parse_args()
    app = QApplication([])
    window = MainWindow()
    try:
        reader = create_session(window, args.output)
        print(json.dumps(verify(reader), indent=2))
    finally:
        window.close()
    app.processEvents()


if __name__ == "__main__":
    main()
