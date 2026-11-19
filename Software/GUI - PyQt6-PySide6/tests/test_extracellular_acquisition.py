"""Acquisition identity and provenance through Scope and the emulator."""
import collections
from unittest.mock import patch

import numpy as np
import pytest
from PySide6.QtWidgets import QApplication

from spikeling_gui.features.emulator import scope as emulator
from spikeling_gui.features.extracellular import scope
from spikeling_gui.features.extracellular.acquisition import Clock, Discontinuity
from spikeling_gui.features.extracellular.input_adapters import InputAdapter
from spikeling_gui.main_window import MainWindow


BOARD = [-65, 0, 0, -70, 0, -75, 0, 0]


def packet(tick, *, vm=-65, trigger=0):
    return [tick / 10, vm, *BOARD[1:-1], trigger]


def test_hardware_stall_loss_and_bad_rows():
    times = iter([0, 1, 2, 15, 16])
    adapter = InputAdapter(clock=lambda: next(times))
    queue = collections.deque(maxlen=3)
    for row in (BOARD, BOARD, BOARD, BOARD, BOARD[:-1]):
        adapter.enqueue(queue, row)
    result = list(adapter.hardware(queue, stall_ns=10))
    assert adapter.high_water == 3
    assert adapter.capacity_lost == 2
    assert adapter.rejected == 1
    assert adapter.local_losses == 3
    lost, first, stall, second, invalid = result
    assert lost.local_lost == 2
    assert first.first_ordinal == 2 and first.first_tick == 3
    assert first.clock == Clock.NOMINAL_MODEL
    assert stall.host_stall_ns == 13 and stall.missing_model_steps is None
    assert second.first_ordinal == 3
    assert invalid.next_index == 2


def test_emulator_rejects_conflicts_and_identifies_exact_gap():
    adapter = InputAdapter(clock=lambda: 123)
    rows = [packet(100), packet(101), packet(101), packet(105), packet(105, vm=-20),
            packet(11), [float("nan"), *BOARD], packet(12)]
    items = list(adapter.emulator(rows))
    assert adapter.duplicates == 1
    assert adapter.rejected == 2
    assert adapter.accepted == 5
    breaks = [item for item in items if isinstance(item, Discontinuity)]
    assert [item.next_index for item in breaks] == [2, 3, 3, 4]
    assert breaks[0].missing_model_steps == 3
    assert breaks[0].previous_tick == 101 and breaks[0].next_tick == 105
    assert breaks[2].reason == "Emulator clock reversed"
    assert not list(adapter.emulator([]))
    bad = list(adapter.emulator([packet(13)], flags=[[1, 0]]))
    assert bad[0].reason == "Misaligned emulator data"
    assert adapter.accepted == 5


@pytest.fixture(scope="module")
def window():
    app = QApplication.instance() or QApplication([])
    result = MainWindow()
    yield result
    result.extracellular_graph.disconnect()
    result.close()
    app.processEvents()


@pytest.fixture
def graph(window):
    graph = window.extracellular_graph
    graph.set_source_mode("emulator")
    window.ui.Emulator_Connect_pushButton.setChecked(True)
    graph.connect()
    graph._rx_timer.stop()
    yield graph
    graph.stop_recording(retry=True)
    graph.disconnect()
    window.ui.Emulator_Connect_pushButton.setChecked(False)


def test_physical_queue_combines_eviction_and_trim(graph):
    graph.set_source_mode("spikeling")
    graph._rx_queue = collections.deque(maxlen=5)
    try:
        for _ in range(8):
            graph.on_data_received(BOARD)
        with patch.object(scope, "MAX_PACKETS_PER_TICK", 2):
            graph._process_rx_queue()
            first = graph.latest_block.inputs.span
            graph._process_rx_queue()
        second = graph.latest_block.inputs.span
        assert (first.first_receive_ordinal, second.first_receive_ordinal) == (3, 6)
        assert second.first_index == 2 and second.segment != first.segment
        assert graph.dropped_packets == 4
        assert graph.last_discontinuity.local_lost == 1
        assert first.acquisition == second.acquisition
        assert graph.latest_block.processed.warmup_rows == 2
    finally:
        graph._rx_queue = collections.deque(maxlen=20000)


def test_events_and_capture_share_sample_identity(graph, tmp_path):
    with patch.object(graph, "_apply_bandpass_block", side_effect=[
        np.array([[0, 0, 0, 0], [-100, 0, 0, 0]], dtype=float),
        np.array([[-100, -100, 0, 0]], dtype=float),
    ]):
        graph.on_emulator_data([packet(10), packet(11, vm=30)], ticks=[10, 11],
                               events=[[0, 0, 0], [1, 1, 1]], aux_enabled=(True, False))
        first = graph.latest_block
        path = tmp_path / "midgroup.csv"
        assert graph.start_recording(path)
        graph.on_emulator_data([packet(12, vm=-65, trigger=1)], ticks=[12],
                               events=[[0, 0, 0]], aux_enabled=(True, False))
    second = graph.latest_block
    group = next(event for event in first.events if event.kind == "grouped_detection")
    crossing = next(event for event in second.events if event.kind == "contact_crossing")
    assert crossing.channel == "E2" and crossing.group_id == group.id
    assert [event.channel for event in first.events if event.kind == "native_model_spike"] == ["aux1", "main"]
    assert [event.channel for event in first.events if event.kind == "waveform_launch"] == ["main"]
    assert second.inputs.span is second.broadband.span is second.processed.span
    assert second.processed.merged_flags.tolist() == [0]
    assert graph.capture.id != graph.acquisition.id
    assert graph.capture.first_index == crossing.index == 2
    assert graph.capture.end_index == 3
    assert graph.stop_recording()
    assert path.read_text().splitlines()[-1].endswith(",0")


def test_gap_primes_comparators_and_finishes_legacy_capture(graph, tmp_path):
    graph.on_emulator_data([packet(1)], ticks=[1])
    path = tmp_path / "gap.csv"
    assert graph.start_recording(path)
    graph.on_emulator_data([packet(2), packet(6, vm=30, trigger=1)], ticks=[2, 6])
    assert graph.recording_state == "saved"
    assert len(path.read_text().splitlines()) == 2
    assert graph.last_discontinuity.missing_model_steps == 3
    assert not graph.latest_block.events
    assert graph.latest_block.inputs.span.first_index == 2
    assert graph.latest_block.processed.warmup_rows == 1
    assert np.count_nonzero(np.isfinite(graph.Time_buffer.data)) == 1


def test_car_epoch_drains_old_hardware_rows(graph):
    graph.set_source_mode("spikeling")
    blocks = []
    with patch.object(graph, "_publish_acquisition_block", side_effect=blocks.append):
        graph.on_data_received(BOARD)
        graph.CAR(True)
        graph.on_data_received(BOARD)
        graph._process_rx_queue()
    graph.CAR(False)
    assert [block.epoch.first_index for block in blocks] == [0, 1]
    assert dict(blocks[0].epoch.settings)["processing"][0] is False
    assert dict(blocks[1].epoch.settings)["processing"][0] is True
    assert blocks[1].processed.warmup_rows == 1


def test_car_does_not_change_published_broadband(graph):
    result = []
    rows = [packet(tick, vm=30 if tick == 2 else -65) for tick in range(1, 90)]
    for referenced in (False, True):
        graph.disconnect()
        graph.CAR(referenced)
        graph.connect()
        graph._rx_timer.stop()
        graph.on_emulator_data(rows)
        result.append(graph.latest_block)
    graph.CAR(False)
    np.testing.assert_array_equal(result[0].broadband.contacts_uV, result[1].broadband.contacts_uV)
    assert np.any(result[0].processed.contacts_uV != result[1].processed.contacts_uV)
    assert not result[0].broadband.contacts_uV.flags.writeable


@pytest.mark.parametrize("imaging,extracellular", [(True, False), (False, True), (True, True)])
def test_emulator_real_forwarding(window, imaging, extracellular):
    eg = window.extracellular_graph
    ig = window.imaging_graph
    eg.set_source_mode("emulator")
    ig.source_mode = "emulator"
    window.ui.Emulator_Connect_pushButton.setChecked(True)
    emulator.EmulatorPlot(window)
    window.Emulator_timer.stop()
    window.ImagingConnectionFlag = imaging
    window.ExtraCellularConnectionFlag = extracellular
    try:
        with patch.object(ig, "on_emulator_data") as optical, patch.object(eg, "on_emulator_data") as contacts:
            emulator.UpdatePlot(window)
        assert optical.called == imaging and contacts.called == extracellular
        if contacts.called:
            rows = [row for call in contacts.call_args_list for row in call.args[0]]
            ticks = [tick for call in contacts.call_args_list for tick in call.kwargs["ticks"]]
            flags = [flag for call in contacts.call_args_list for flag in call.kwargs["events"]]
            assert len(rows) == len(flags) == len(ticks) > 0
            assert ticks == list(range(1, window.Emulator_model_tick + 1))
            if imaging:
                assert optical.call_args.kwargs["events"] == flags
    finally:
        window.ImagingConnectionFlag = window.ExtraCellularConnectionFlag = False
        window.ui.Emulator_Connect_pushButton.setChecked(False)
        emulator.EmulatorPlot(window)


def test_emulator_midrun_vc_pacing_and_restart(window):
    graph = window.extracellular_graph
    ui = window.ui
    old_speed = ui.Emulator_Speed_slider.value()
    graph.set_source_mode("emulator")
    ui.Emulator_Connect_pushButton.setChecked(True)
    ui.Emulator_PatchClampMode_toggleButton.setChecked(True)
    ui.EmulatorSyn1_Synapse_toggleButton.setChecked(True)
    emulator.EmulatorPlot(window)
    window.Emulator_timer.stop()
    try:
        emulator.UpdatePlot(window)
        first_tick = window.Emulator_model_tick + 1
        graph.connect()
        graph._rx_timer.stop()
        emulator.UpdatePlot(window)
        first = graph.latest_block
        assert first.inputs.span.first_tick == first_tick
        assert first.inputs.span.first_index == 0
        assert first.inputs.soma_clamped
        assert first.inputs.native_available == (False, True, False)

        ui.Emulator_Speed_slider.setValue(
            ui.Emulator_Speed_slider.maximum() if old_speed != ui.Emulator_Speed_slider.maximum()
            else ui.Emulator_Speed_slider.minimum()
        )
        emulator.UpdatePlot(window)
        second = graph.latest_block
        assert second.epoch.changed == ("pacing",)
        assert second.inputs.span.first_tick == first_tick + first.inputs.span.count
        assert second.inputs.span.acquisition == first.inputs.span.acquisition

        ui.Emulator_Connect_pushButton.setChecked(False)
        emulator.EmulatorPlot(window)
        assert graph.acquisition is None
        ui.Emulator_Connect_pushButton.setChecked(True)
        emulator.EmulatorPlot(window)
        window.Emulator_timer.stop()
        graph.connect()
        graph._rx_timer.stop()
        emulator.UpdatePlot(window)
        assert graph.latest_block.inputs.span.first_tick == 1
        assert graph.acquisition.id != first.inputs.span.acquisition.id
    finally:
        graph.disconnect()
        ui.Emulator_Connect_pushButton.setChecked(False)
        emulator.EmulatorPlot(window)
        ui.Emulator_Speed_slider.setValue(old_speed)
        ui.Emulator_PatchClampMode_toggleButton.setChecked(False)
        ui.EmulatorSyn1_Synapse_toggleButton.setChecked(False)
