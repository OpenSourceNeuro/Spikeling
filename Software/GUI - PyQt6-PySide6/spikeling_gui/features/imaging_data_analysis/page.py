"""Imaging Data Analysis: recording overview for single-pixel optical recordings.

All page widgets live in UI_Spikeling.ui; this controller only wires them and
renders saved recordings. Other analysis tabs are intentionally placeholders.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QButtonGroup, QFileDialog
from pyqtgraph.exporters import ImageExporter

from spikeling_gui.appearance.dialogs import themed_message_box
from spikeling_gui.appearance.theme_manager import theme_manager
from spikeling_gui.paths import recordings_directory, save_dialog_directory

from .recording import ImagingRecordingError, load_imaging_recording
from .align_view import ImagingAlignView
from .processing_view import ImagingProcessingView
from .transients_view import ImagingTransientsView
from .inference_view import ImagingInferenceView
from .compare_view import ImagingCompareView


NAVIGATION = (
    "ImagingAnalysis_navRecording",
    "ImagingAnalysis_navProcessing",
    "ImagingAnalysis_navAlign",
    "ImagingAnalysis_navTransients",
    "ImagingAnalysis_navInference",
    "ImagingAnalysis_navCompare",
)
PLOT_NAMES = (
    "ImagingAnalysis_recording_stimulusPlot",
    "ImagingAnalysis_recording_fluorescencePlot",
    "ImagingAnalysis_recording_dffPlot",
    "ImagingAnalysis_recording_calciumPlot",
    "ImagingAnalysis_recording_voltagePlot",
)


def _split_at_gaps(x: np.ndarray, y: np.ndarray, gap_before: np.ndarray):
    """Prevent drawing false straight lines through acquisition discontinuities."""
    cuts = np.flatnonzero(gap_before)
    return np.insert(x, cuts, np.nan), np.insert(y, cuts, np.nan)


class ImagingDataAnalysisPage(QObject):
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.ui = window.ui
        self.recording = None
        self.tabs = QButtonGroup(self.ui.page_Imaging_DataAnalysis)
        self.tabs.setExclusive(True)
        for index, name in enumerate(NAVIGATION):
            button = getattr(self.ui, name)
            self.tabs.addButton(button, index)
        self.tabs.idClicked.connect(self.open_tab)
        self.ui.ImagingAnalysis_recording_loadButton.clicked.connect(self.load)
        self.ui.ImagingAnalysis_recording_neuronCombo.currentIndexChanged.connect(self.draw)
        self.ui.ImagingAnalysis_recording_referenceCheck.toggled.connect(self.draw)
        self.ui.ImagingAnalysis_recording_metadataButton.clicked.connect(self.show_metadata)
        self.ui.ImagingAnalysis_recording_backButton.clicked.connect(self.show_overview)
        self.ui.ImagingAnalysis_recording_exportButton.clicked.connect(self.export_graphs)
        self.ui.ImagingAnalysis_recording_metadataButton.setEnabled(False)
        self.ui.ImagingAnalysis_recording_exportButton.setEnabled(False)
        self.ui.ImagingAnalysis_recording_neuronCombo.setEnabled(False)
        self.ui.ImagingAnalysis_recording_referenceCheck.setEnabled(False)
        self.ui.ImagingAnalysis_recording_referenceCheck.setChecked(False)
        self.ui.ImagingAnalysis_recording_fileLabel.setText("No imaging recording loaded")
        self.ui.ImagingAnalysis_recording_summaryLabel.setText(
            "Load a three-file imaging recording (.csv, _frames.csv, _meta.json)."
        )
        self._plots = [getattr(self.ui, name) for name in PLOT_NAMES]
        for index, widget in enumerate(self._plots):
            theme_manager.set_plot_background_role(widget, "panel_background")
            widget.showGrid(x=True, y=True, alpha=0.22)
            widget.getAxis("left").setWidth(55)
            widget.setDownsampling(auto=True, mode="peak")
            if index != 1:
                widget.setXLink(self._plots[1])
        self._plots[3].hide()
        self._plots[4].hide()
        self.processed_recording = None
        self.processing_view = ImagingProcessingView(self)
        self.align_view = ImagingAlignView(self)
        self.transients_view = ImagingTransientsView(self)
        self.inference_view = ImagingInferenceView(self)
        self.compare_view = ImagingCompareView(self)
        self.open_tab(0)
        theme_manager.themeChanged.connect(self.refresh_theme)

    def show_page(self):
        self.ui.mainbody_stackedWidget.setCurrentWidget(self.ui.page_Imaging_DataAnalysis)
        self.open_tab(self.ui.ImagingAnalysis_stack.currentIndex())

    def open_tab(self, index):
        if not 0 <= index < len(NAVIGATION):
            index = 0
        self.ui.ImagingAnalysis_stack.setCurrentIndex(index)
        button = self.tabs.button(index)
        if button is not None:
            button.setChecked(True)

    def show_overview(self):
        self.ui.ImagingAnalysis_recordingStack.setCurrentWidget(
            self.ui.ImagingAnalysis_recordingOverviewPage
        )

    def show_metadata(self):
        if self.recording is None:
            return
        self.ui.ImagingAnalysis_recording_metadataText.setPlainText(
            json.dumps(self.recording.metadata, ensure_ascii=False, indent=2)
        )
        self.ui.ImagingAnalysis_recordingStack.setCurrentWidget(
            self.ui.ImagingAnalysis_recordingMetadataPage
        )

    def load(self):
        filename, _ = QFileDialog.getOpenFileName(
            self.window, "Open imaging recording", save_dialog_directory(recordings_directory()),
            "Imaging recordings (*.csv);;All files (*)",
        )
        if not filename:
            return
        try:
            recording = load_imaging_recording(filename)
        except (OSError, ValueError, ImagingRecordingError) as error:
            themed_message_box(self.window, "Cannot load imaging recording", str(error)).exec()
            return
        self.recording = recording
        self.ui.ImagingAnalysis_recording_fileLabel.setText(recording.source.name)
        self.ui.ImagingAnalysis_recording_fileLabel.setToolTip(str(recording.source))
        parts = [
            f"{recording.n_frames:,} frames",
            f"{recording.n_samples:,} model samples",
            f"{recording.nominal_frame_rate_hz:g} Hz (nominal)",
            str(recording.metadata.get("indicator_name", "Unknown indicator")),
            str(recording.metadata.get("source", "Unknown source")),
        ]
        if recording.warnings:
            parts.append(f"{len(recording.warnings)} acquisition notice(s)")
        self.ui.ImagingAnalysis_recording_summaryLabel.setText(" · ".join(parts))
        self.ui.ImagingAnalysis_recording_summaryLabel.setToolTip("\n".join(recording.warnings))
        self.ui.ImagingAnalysis_recording_metadataButton.setEnabled(True)
        self.ui.ImagingAnalysis_recording_neuronCombo.setEnabled(True)
        self.ui.ImagingAnalysis_recording_referenceCheck.setEnabled(True)
        self.ui.ImagingAnalysis_recording_exportButton.setEnabled(recording.n_frames > 0)
        self.ui.ImagingAnalysis_recording_referenceCheck.setChecked(False)
        self.processing_view.reset()
        self.align_view.reset()
        self.transients_view.reset()
        self.inference_view.reset()
        self.compare_view.reset()
        self.open_tab(0)
        self.show_overview()
        self.draw()
        if recording.n_frames:
            self._plots[1].setXRange(recording.frame_time_ms[0],
                                      recording.frame_time_ms[-1] if recording.n_frames > 1
                                      else recording.frame_time_ms[0] + 100, padding=0.015)

    def _draw_trace(self, plot, x, values, gaps, role, label):
        plot.setTitle(label, color=theme_manager.active_colour("text_primary"), size="9pt")
        if x.size:
            gx, gy = _split_at_gaps(x, values, gaps)
            theme_manager.themed_plot(plot, gx, gy, role, connect="finite")
        plot.enableAutoRange(axis="y")

    def draw(self, *_):
        rec = self.recording
        for plot in self._plots:
            plot.clear()
        if rec is None:
            return
        neuron = self.ui.ImagingAnalysis_recording_neuronCombo.currentIndex()
        neuron = max(0, min(2, neuron))
        ref = self.ui.ImagingAnalysis_recording_referenceCheck.isChecked()
        self._plots[3].setVisible(ref)
        self._plots[4].setVisible(ref)
        self._draw_trace(self._plots[0], rec.sample_time_ms, rec.stimulus,
                         rec.sample_gap_before, "imaging_stimulus", "Stimulus (model samples)")
        self._draw_trace(self._plots[1], rec.frame_time_ms,
                         rec.frame_fluorescence_au[:, neuron], rec.frame_gap_before,
                         f"imaging_fluo{neuron + 1}", "Measured fluorescence (a.u.)")
        self._draw_trace(self._plots[2], rec.frame_time_ms,
                         rec.recorded_dff_percent[:, neuron], rec.frame_gap_before,
                         f"imaging_fluo{neuron + 1}", "Recorded ΔF/F₀ (%) — simulator normalisation")
        if ref:
            self._draw_trace(self._plots[3], rec.sample_time_ms, rec.calcium_um[:, neuron],
                             rec.sample_gap_before, f"imaging_calcium{neuron + 1}",
                             "Model reference: intracellular calcium (µM)")
            self._draw_trace(self._plots[4], rec.sample_time_ms, rec.voltage_mv[:, neuron],
                             rec.sample_gap_before, f"imaging_vm{neuron + 1}",
                             "Model reference: membrane voltage (mV)")
            indices = np.flatnonzero(rec.reference_events[:, neuron] != 0)
            if indices.size:
                marker_y = rec.voltage_mv[indices, neuron]
                theme_manager.themed_plot(
                    self._plots[4], rec.sample_time_ms[indices], marker_y,
                    "analysis_spike_rate", symbol="o", symbol_size=5,
                )
        last_shown = self._plots[4 if ref else 2]
        for widget in self._plots:
            widget.setLabel("bottom", "Time (ms)" if widget is last_shown else "")
            widget.getAxis("bottom").setStyle(showValues=widget is last_shown)
        theme_manager.style_traces()

    def refresh_theme(self, *_):
        if self.recording is not None:
            self.draw()

    def export_graphs(self):
        if self.recording is None:
            return
        self.show_overview()
        path = QFileDialog.getExistingDirectory(
            self.window, "Export imaging recording graphs",
            save_dialog_directory(recordings_directory()),
        )
        if not path:
            return
        folder = Path(path)
        try:
            for plot, suffix in zip(self._plots,
                                    ("stimulus", "fluorescence", "dff", "calcium_reference", "vm_reference")):
                if plot.isVisible():
                    ImageExporter(plot.getPlotItem()).export(
                        str(folder / f"{self.recording.source.stem}_{suffix}.png")
                    )
        except (OSError, RuntimeError, ValueError) as error:
            themed_message_box(self.window, "Cannot export imaging graphs", str(error)).exec()
