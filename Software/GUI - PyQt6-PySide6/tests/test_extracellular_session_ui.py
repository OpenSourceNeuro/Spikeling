from time import monotonic, sleep
from unittest.mock import patch

import numpy as np
import pytest
from PySide6.QtWidgets import QApplication
from scipy.signal import sosfilt

from spikeling_gui.features.extracellular.session_reader import SessionReader
from spikeling_gui.main_window import MainWindow


@pytest.fixture(scope="module")
def gui():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    yield app, window
    window.close()


@pytest.fixture
def graph(gui):
    _, window = gui
    graph = window.extracellular_graph
    graph.set_source_mode("emulator")
    window.ui.Emulator_Connect_pushButton.setChecked(True)
    graph.connect()
    graph._rx_timer.stop()
    yield graph
    graph.stop_recording()
    if graph.session_recording.writer is not None:
        assert graph.session_recording.writer.wait(10)
        graph.session_recording.poll()
    graph.disconnect()
    window.ui.Emulator_Connect_pushButton.setChecked(False)


def feed(graph, first_tick, count):
    ticks = list(range(first_tick, first_tick + count))
    rows = [[tick / 10, 30 if tick % 70 == 10 else -70, (tick % 20 < 8) * 50,
             0, -65, 0, -60, 0, int(tick % 20 == 0)] for tick in ticks]
    graph.on_emulator_data(rows, ticks=ticks, events=[[int(tick % 70 == 10), 0, 0] for tick in ticks])
    return graph.latest_block


def test_scope_recording_button_exact_capture_epochs_gap_and_overview(gui, graph, tmp_path):
    app, window = gui
    controls = window.ui
    target = tmp_path / "capture.spikeling"
    feed(graph, 1, 20)
    zi = graph._filter_zi_block.copy()
    controls.ExtraCellular_RecordingFormat_comboBox.setCurrentIndex(1)
    controls.ExtraCellular_DataRecording_RecordFolder_value.setText("capture")
    button = controls.ExtraCellular_DataRecording_Record_pushButton
    with patch("spikeling_gui.features.extracellular.page.recording_path", return_value=target.with_suffix(".csv")):
        button.click()
    np.testing.assert_array_equal(graph._filter_zi_block, zi)
    first = feed(graph, 21, 79)
    graph.CAR(True)
    second = feed(graph, 100, 70)
    third = feed(graph, 175, 36)
    writer = graph.session_recording.writer
    button.click()
    assert graph.recording_state == "saving" and not button.isEnabled()
    assert writer.wait(10), writer.error
    graph.session_recording.poll()
    assert graph.recording_state == "saved", writer.error
    assert all(not values for values in graph._rec.values())
    result = SessionReader(target)
    assert result.first_index == 20 and result.summary["segments"] == 2
    assert result.epoch_count == 3
    context = result.manifest["capture_start_processing"]
    assert context["filter_zi"] == zi.tolist()
    replay, _ = sosfilt(np.asarray(context["filter_sos"]), first.broadband.contacts_uV,
                        axis=0, zi=np.asarray(context["filter_zi"]))
    np.testing.assert_array_equal(replay, first.processed.contacts_uV)
    assert not result.manifest["native_truth"]
    expected_events = [event for block in (first, second, third) for event in block.events
                       if event.kind != "native_model_spike"]
    assert [event["id"] for event in result.iter_events()] == [
        [str(event.id[0]), *event.id[1:]] for event in expected_events
    ]
    expected = np.concatenate([block.broadband.contacts_uV for block in (first, second, third)])
    np.testing.assert_array_equal(
        np.concatenate([item[3] for item in result.iter_interval("broadband")]), expected
    )

    controls.ExtraCellularSpikes_pushButton.click()
    page = window.extracellular_recording_page
    assert controls.mainbody_stackedWidget.currentWidget() is page
    page.open_path(target / "manifest.json")
    deadline = monotonic() + 10
    while page.result is not None and monotonic() < deadline:
        app.processEvents()
        sleep(0.01)
    assert page.reader is not None and page.result is None
    assert page.ui.stageCombo.count() == 2
    assert "complete" in page.ui.statusLabel.text().lower()
    x, y = page.axes[0][1].getData()
    np.testing.assert_array_equal(y[np.isfinite(x)], expected[:, 0])
    assert np.count_nonzero(~np.isfinite(x)) == 1
    graph.CAR(False)
    controls.ExtraCellular_RecordingFormat_comboBox.setCurrentIndex(0)


@pytest.mark.parametrize("reason", ["emulator_stop", "source_switch", "board_unplug", "window_close"])
def test_session_terminates_on_existing_lifecycle_hooks(gui, graph, tmp_path, reason):
    _, window = gui
    target = tmp_path / f"{reason}.spikeling"
    board = reason == "board_unplug"
    if board:
        graph.set_source_mode("spikeling")
    with patch.object(graph, "source_ready", return_value=True):
        assert graph.start_session_recording(target)
    if board:
        for _ in range(20):
            graph.on_data_received([-60, 0, 0, -60, 0, -60, 0, 0])
        graph._process_rx_queue()
    else:
        feed(graph, 1, 20)
    writer = graph.session_recording.writer
    if reason == "emulator_stop":
        graph.on_emulator_stopped()
    elif reason == "source_switch":
        graph.set_source_mode("spikeling")
    elif reason == "board_unplug":
        graph.on_hardware_connection_changed(False)
    else:
        from PySide6.QtGui import QCloseEvent
        event = QCloseEvent()
        window.closeEvent(event)
        assert not event.isAccepted()
        assert graph.session_recording.close_requested
        # Keep this shared test window alive after verifying asynchronous close.
        graph.session_recording.close_requested = False
    assert writer.wait(10), writer.error
    graph.session_recording.poll()
    assert writer.status == "complete", writer.error
    session = SessionReader(target)
    assert session.sample_count == 20
    assert session.manifest["stop_reason"] in {
        "Emulator stopped", "Source changed", "Hardware disconnected", "Window closed"
    }
