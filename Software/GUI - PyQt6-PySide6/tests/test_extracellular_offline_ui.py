import shutil
from threading import Event
from time import monotonic, sleep

import pytest
from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtWidgets import QApplication

from spikeling_gui.features.extracellular import analysis_page
from spikeling_gui.features.extracellular.phase2_practical import create_session, verify
from spikeling_gui.main_window import MainWindow


def wait(app, complete):
    deadline = monotonic() + 20
    while not complete() and monotonic() < deadline:
        app.processEvents()
        sleep(0.008)
    assert complete()


@pytest.fixture(scope="module")
def practical(tmp_path_factory):
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    reader = create_session(window, tmp_path_factory.mktemp("practical") / "car.spikeling")
    window.ui.ExtraCellularSpikes_pushButton.click()
    yield app, window, reader
    window.close()


def open_reader(app, page, path):
    page.open_path(path)
    wait(app, lambda: page.result is None)


def wait_for_analysis(app, panel):
    wait(app, lambda: panel.job is None and panel.pending is None)


def test_practical_exact_measurements_and_visible_workflow(practical):
    app, window, reader = practical
    measured = verify(reader)
    assert (measured["A_detections"], measured["B_detections"], measured["native_source_events"]) == (8, 0, 8)
    page = window.extracellular_recording_page
    open_reader(app, page, reader.directory / "manifest.json")
    ui, panel = page.ui, page.analysis
    assert ui.runButton.isEnabled() and ui.sourceCombo.currentData() == ""
    assert ui.sourceCombo.findData("native_model_spike") >= 0
    ui.pageStack.setCurrentWidget(ui.processingTab)
    ui.bandpassCheck.setChecked(False)
    ui.referenceCombo.setCurrentIndex(0)
    ui.runButton.click()
    wait_for_analysis(app, panel)
    assert len(panel.current.groups) == 8 and panel.source is None
    assert ui.pinButton.isEnabled()
    ui.pinButton.click()
    wait_for_analysis(app, panel)

    ui.referenceCombo.setCurrentIndex(1)
    ui.runButton.click()
    wait_for_analysis(app, panel)
    assert len(panel.current.groups) == 0 and len(panel.reference.waveforms.event_ids) == 8
    assert len(panel.comparison[0].left_only) == 8
    assert ui.analysisExportButton.isEnabled()
    ui.pageStack.setCurrentWidget(ui.comparisonTab)
    ui.sourceCombo.setCurrentIndex(ui.sourceCombo.findData("native_model_spike"))
    panel._source_changed()
    wait_for_analysis(app, panel)
    assert len(panel.source.events) == 8
    ui.pageStack.setCurrentWidget(ui.processingTab)
    assert panel.plots.marks[2].getData()[0].size == 8
    QCoreApplication.sendEvent(page, QEvent(QEvent.Type.LanguageChange))
    assert ui.sourceCombo.currentData() == "native_model_spike"
    ui.sourceCombo.setCurrentIndex(0)
    panel._source_changed()
    wait_for_analysis(app, panel)
    assert panel.source is None
    assert panel.plots.marks[2].getData()[0] is None or panel.plots.marks[2].getData()[0].size == 0


def test_latest_job_wins_and_legacy_recovered_and_corrupt_inputs(practical, tmp_path, monkeypatch):
    app, window, reader = practical
    page = window.extracellular_recording_page
    panel, ui = page.analysis, page.ui
    partial = tmp_path / "teaching.partial"
    shutil.copytree(reader.directory, partial)
    open_reader(app, page, partial / "manifest.json")
    assert panel.reader.recovered and "Recovered" in ui.analysisSelection.text()
    ui.referenceCombo.setCurrentIndex(0)
    ui.bandpassCheck.setChecked(False)
    ui.thresholdEdit.setText("-15")
    started, release = Event(), Event()
    real = analysis_page.analyse

    def delayed(reader, start, stop, recipe, cancel):
        if recipe.detector.threshold_uV == -15:
            started.set()
            assert release.wait(10)
        return real(reader, start, stop, recipe)

    monkeypatch.setattr(analysis_page, "analyse", delayed)
    panel.run()
    try:
        assert started.wait(5)
        ui.thresholdEdit.setText("-10000")
        panel.run()
    finally:
        release.set()
    wait_for_analysis(app, panel)
    assert panel.current.recipe.detector.threshold_uV == -10000
    assert not panel.current.groups

    path = tmp_path / "legacy.csv"
    path.write_text("Time (ms),Ch1 (uV),Ch2 (uV),Ch3 (uV),Ch4 (uV)\n0,0,0,0,0\n0.1,1,2,3,4\n")
    open_reader(app, page, path)
    assert not ui.runButton.isEnabled() and "broadband session" in ui.analysisSelection.text()
    corrupt = tmp_path / "corrupt.spikeling"
    shutil.copytree(reader.directory, corrupt)
    (corrupt / "manifest.json").write_text("{")
    open_reader(app, page, corrupt / "manifest.json")
    assert not ui.runButton.isEnabled() and "Recording error" in ui.statusLabel.text()


def test_display_reduction_keeps_extrema_at_original_rows():
    import numpy as np

    x = np.arange(60)
    y = np.zeros(60)
    y[25], y[29] = -100, 200
    selected_x, selected_y = analysis_page._peak_points(x, y, 10)
    assert len(selected_x) < len(x)
    assert all(point in dict(zip(selected_x, selected_y)).items() for point in ((25, -100), (29, 200)))


def test_analysis_tabs_and_shared_trace_navigation(practical):
    app, window, reader = practical
    page = window.extracellular_recording_page
    open_reader(app, page, reader.directory / "manifest.json")
    ui, panel = page.ui, page.analysis
    assert [page.navigation.button(i).text() for i in range(ui.pageStack.count())] == [
        "Recording", "Processing", "Detection", "Waveforms", "Comparison", "Spectrum"]
    assert ui.navRecording.isChecked() and ui.analysisFooter.isHidden()
    ui.metadataButton.click()
    assert ui.recordingStack.currentWidget() is ui.recordingMetadata
    assert "before reference" in ui.metadata.toPlainText()
    ui.metadataBackButton.click()
    assert ui.recordingStack.currentWidget() is ui.recordingOverview
    ui.navDetection.click()
    assert ui.navDetection.isChecked() and not ui.navRecording.isChecked()
    assert not ui.analysisFooter.isHidden()
    assert ui.analysisPlotHost.parentWidget() is ui.detectionTab
    ui.pageStack.setCurrentWidget(ui.processingTab)
    assert ui.navProcessing.isChecked() and ui.analysisPlotHost.parentWidget() is ui.processingTab
    ui.referenceCombo.setCurrentIndex(1)
    ui.bandpassCheck.setChecked(False)
    panel.run()
    wait_for_analysis(app, panel)
    assert "exactly zero" in ui.comparisonDetails.toPlainText()
    assert "B contains 0 contact crossings" in ui.comparisonDetails.toPlainText()
    assert "{" not in ui.comparisonDetails.toPlainText()
    assert "not proof" in ui.detectionGuide.text()


def test_analysis_controls_and_measurements(practical):
    app, window, reader = practical
    page = window.extracellular_recording_page
    open_reader(app, page, reader.directory / "manifest.json")
    ui, panel = page.ui, page.analysis
    ui.bandpassCheck.setChecked(False)
    ui.referenceCombo.setCurrentIndex(0)
    ui.polarityCombo.setCurrentIndex(1)
    assert float(ui.thresholdEdit.text()) > 0
    ui.runButton.click()
    wait_for_analysis(app, panel)
    assert panel.current.recipe.detector.polarity == "positive"
    ui.baselineStartEdit.setText(str(panel.current.start))
    ui.baselineCountEdit.setText("2")
    assert ui.measurementTable.item(0, 2).text() != "—"

    ui.referenceCombo.setCurrentIndex(2)
    ui.singleReferenceCombo.setCurrentIndex(3)
    ui.notchCombo.setCurrentIndex(1)
    ui.runButton.click()
    wait_for_analysis(app, panel)
    assert panel.current.recipe.processing.reference_contacts == ("E4",)
    assert panel.current.recipe.processing.notch_hz == 50
    assert all(not run.values_uV[:, 3].any() for run in panel.current.runs)
    ui.pageStack.setCurrentWidget(ui.spectrumTab)
    assert panel.spectrum_plot is not None
    assert "0.5 s" in ui.spectrumStatus.text()
