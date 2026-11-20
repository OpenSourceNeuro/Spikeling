"""Scientific regressions from the Phase 2 CAR audit."""
from collections import deque
from types import SimpleNamespace

import numpy as np
import pytest

from spikeling_gui.features.extracellular.scope import ExtraCellularGraph, Y_MIN_UV, Y_MAX_UV
from spikeling_gui.features.extracellular.offline_analysis import Recipe, analyse, compare_source
from spikeling_gui.features.extracellular.offline_processing import Processing
from test_extracellular_offline_processing import make_session


def detector():
    return SimpleNamespace(
        DetectionThreshold_uV=-15., DetectRefractory_ms=.6,
        _prev_channel_sample=np.zeros(4), _t_last_detect_ms=np.full(4, -1e12),
        ChannelSpikeData=np.zeros(4), _channel_spike_marks=[deque() for _ in range(4)],
        _last_event_ms=-1e12, _event_marks=deque(),
    )


@pytest.mark.parametrize('partition', [False, True])
def test_live_exact_refractory_and_group_expiry(partition):
    # These decimal timestamps formerly rounded below the expiry windows.
    times = 1000 + np.arange(15) / 10
    for same_contact, second in [(True, 8), (False, 6)]:
        graph = detector()
        values = np.zeros((15, 4))
        values[2, 0] = -20
        values[second, 0 if same_contact else 1] = -20
        boundaries = [0, 5, 15] if partition else [0, 15]
        events = []
        for start, stop in zip(boundaries, boundaries[1:]):
            events.extend(ExtraCellularGraph._detect_block_crossings(
                graph, times[start:stop], values[start:stop]))
        assert np.flatnonzero(events).tolist() == [2, second]
        assert sum(len(marks) for marks in graph._channel_spike_marks) == 2


@pytest.mark.parametrize('amplitude', [0., .01, 2.])
def test_shared_fit_reveals_residual_without_threshold_dominating(amplitude):
    plots = [SimpleNamespace(setYRange=lambda low, high, padding: ranges.append((low, high)))
             for _ in range(4)]
    ranges = []
    graph = SimpleNamespace(
        ui=SimpleNamespace(ExtraCellular_AutoRange_pushButton=SimpleNamespace(setText=lambda _: None)),
        tr=lambda text: text, _plots_ready=True,
        time_axis_widget=SimpleNamespace(getViewBox=lambda: SimpleNamespace(viewRange=lambda: [[-1, 0], [-40, 80]])),
        Time_buffer=SimpleNamespace(data=np.array([0., .1])),
        Extra_buffers=[SimpleNamespace(data=np.array([0., amplitude])) for _ in range(4)],
        DetectionThreshold_uV=-1000., channel_plot_widgets=plots, _update_plots=lambda: None,
    )
    ExtraCellularGraph._update_shared_y_range(graph, True)
    assert len(set(ranges)) == 1
    assert ranges[0][1] == pytest.approx(max(.1, amplitude * 1.15))
    assert ranges[0][0] == -ranges[0][1]
    ranges.clear()
    ExtraCellularGraph._update_shared_y_range(graph, False)
    assert ranges == [(Y_MIN_UV, Y_MAX_UV)] * 4


def test_silent_source_interval_is_available_evidence(tmp_path):
    reader, _ = make_session(tmp_path)
    # The fixture's launch lies at sample 30, outside this interval.
    result = analyse(reader, 40, 100, Recipe(Processing(bandpass=None)))
    evidence = compare_source(reader, result, 'waveform_launch', .5)
    assert evidence.available and evidence.eligible_rows == 59
    assert evidence.events == ()
    assert evidence.agreement is not None
    native = compare_source(reader, result, 'native_model_spike', .5)
    assert not native.available
