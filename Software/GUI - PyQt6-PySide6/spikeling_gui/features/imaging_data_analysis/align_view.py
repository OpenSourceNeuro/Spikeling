"""Qt view for imaging stimulus-loop alignment and average fluorescence.

Widgets are authored entirely in UI_Spikeling.ui, not created here.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QFileDialog
from pyqtgraph.exporters import ImageExporter

from spikeling_gui.appearance.dialogs import themed_message_box
from spikeling_gui.appearance.theme_manager import theme_manager
from spikeling_gui.paths import recordings_directory, save_dialog_directory

from .align import align_imaging_cycles, mean_sem


class ImagingAlignView(QObject):
    """Present aligned single-pixel fluorescence cycles and their averages."""

    def __init__(self, analysis_page):
        super().__init__(analysis_page)
        self.page = analysis_page
        self.window = analysis_page.window
        self.ui = analysis_page.ui
        self.result = None
        self.ui.ImagingAnalysis_align_calculateButton.clicked.connect(self.calculate)
        self.ui.ImagingAnalysis_align_sourceCombo.currentIndexChanged.connect(self._source_changed)
        self.ui.ImagingAnalysis_align_neuronCombo.currentIndexChanged.connect(self.invalidate)
        self.ui.ImagingAnalysis_align_signalCombo.currentIndexChanged.connect(self.invalidate)
        for field in (self.ui.ImagingAnalysis_align_thresholdEdit,
                      self.ui.ImagingAnalysis_align_periodEdit,
                      self.ui.ImagingAnalysis_align_preEdit):
            field.textEdited.connect(self.invalidate)
        self.ui.ImagingAnalysis_align_repetitionsCheck.toggled.connect(self.draw)
        self.ui.ImagingAnalysis_align_exportButton.clicked.connect(self.export_csv)
        self.ui.ImagingAnalysis_align_imageButton.clicked.connect(self.export_image)
        self.plots = (
            self.ui.ImagingAnalysis_align_stimulusPlot,
            self.ui.ImagingAnalysis_align_responsePlot,
        )
        for plot in self.plots:
            theme_manager.set_plot_background_role(plot, 'panel_background')
            plot.showGrid(x=True, y=True, alpha=.22)
            plot.getAxis('left').setWidth(65)
            plot.setDownsampling(auto=True, mode='peak')
            plot.setLabel('bottom', 'Time from loop onset (ms)')
        self.plots[0].setXLink(self.plots[1])
        self.ui.ImagingAnalysis_align_repetitionsCheck.setChecked(True)
        self._source_changed()
        self.reset()
        theme_manager.themeChanged.connect(self.refresh_theme)

    def _update_processed_options(self):
        available = getattr(self.page, 'processed_recording', None) is not None
        combo = self.ui.ImagingAnalysis_align_signalCombo
        model = combo.model()
        for index in (2, 3):
            item = model.item(index) if hasattr(model, 'item') else None
            if item is not None:
                item.setEnabled(available)
        if not available and combo.currentIndex() >= 2:
            combo.setCurrentIndex(0)

    def _source_changed(self, *_):
        stimulus_source = self.ui.ImagingAnalysis_align_sourceCombo.currentIndex() == 1
        self.ui.ImagingAnalysis_align_thresholdEdit.setEnabled(stimulus_source)
        self.invalidate()

    def reset(self):
        self.result = None
        self._update_processed_options()
        self.ui.ImagingAnalysis_align_calculateButton.setEnabled(self.page.recording is not None)
        self.ui.ImagingAnalysis_align_exportButton.setEnabled(False)
        self.ui.ImagingAnalysis_align_imageButton.setEnabled(False)
        self.ui.ImagingAnalysis_align_neuronCombo.setEnabled(self.page.recording is not None)
        self.ui.ImagingAnalysis_align_signalCombo.setEnabled(self.page.recording is not None)
        self.ui.ImagingAnalysis_align_summaryLabel.setText(
            'Load a recording, choose an onset source, then select Align & average. '
            'Fluorescence is aligned using camera frames, not model time samples.'
        )
        for plot in self.plots:
            plot.clear()

    def invalidate(self, *_):
        if self.result is None:
            return
        self.reset()
        self.ui.ImagingAnalysis_align_summaryLabel.setText(
            'Alignment parameters changed. Click Align & average to recalculate.'
        )

    def calculate(self, *_):
        rec = self.page.recording
        if rec is None:
            return
        ui = self.ui
        try:
            source = ('trigger', 'stimulus')[ui.ImagingAnalysis_align_sourceCombo.currentIndex()]
            threshold = (float(ui.ImagingAnalysis_align_thresholdEdit.text().strip())
                         if source == 'stimulus' else 0.0)
            pre_ms = float(ui.ImagingAnalysis_align_preEdit.text().strip())
            raw_period = ui.ImagingAnalysis_align_periodEdit.text().strip()
            period = float(raw_period) if raw_period else None
            choice = ui.ImagingAnalysis_align_signalCombo.currentIndex()
            if choice not in (0, 1, 2, 3):
                raise ValueError('Unknown optical signal selection')
            processed = getattr(self.page, 'processed_recording', None)
            if choice >= 2 and processed is None:
                raise ValueError('Apply processing in the Processing tab first')
            signal = ('dff', 'fluorescence', 'dff', 'fluorescence')[choice]
            frame_values = (None if choice < 2 else
                            processed.dff_percent if choice == 2 else processed.fluorescence_au)
            self.result = align_imaging_cycles(
                rec, neuron=ui.ImagingAnalysis_align_neuronCombo.currentIndex(),
                signal=signal, source=source, stimulus_threshold=threshold,
                pre_ms=pre_ms, period_ms=period, frame_values=frame_values,
            )
        except (ValueError, IndexError, TypeError) as exc:
            self.result = None
            self.reset()
            ui.ImagingAnalysis_align_summaryLabel.setText('Alignment unavailable: ' + str(exc))
            return
        result = self.result
        details = (
            f'{result.n_cycles} included / {result.n_candidates} observed loop onsets · '
            f'period {result.duration_ms:g} ms · '
            f'camera-frame interval {result.frame_step_ms:g} ms · '
            f'{result.excluded_irregular} irregular · '
            f'{result.excluded_incomplete} incomplete / timebase interruptions · '
            f'{result.excluded_frame_gaps} insufficient camera coverage'
        )
        ui.ImagingAnalysis_align_summaryLabel.setText(details)
        ui.ImagingAnalysis_align_exportButton.setEnabled(True)
        ui.ImagingAnalysis_align_imageButton.setEnabled(True)
        self.draw(reset_range=True)

    def _plot(self, plot, rows, *, mean_role, title):
        result = self.result
        plot.clear()
        plot.setTitle(title, color=theme_manager.active_colour('text_primary'), size='9pt')
        if self.ui.ImagingAnalysis_align_repetitionsCheck.isChecked():
            x = np.tile(np.r_[result.time_ms, np.nan], len(rows))
            y = np.column_stack((rows, np.full(len(rows), np.nan))).ravel()
            theme_manager.themed_plot(plot, x, y, 'analysis_loop', connect='finite')
        avg, _, _, _ = mean_sem(rows)
        theme_manager.themed_plot(plot, result.time_ms, avg, mean_role,
                                  width_scale=2.0, connect='finite')
        plot.enableAutoRange(axis='y')

    def draw(self, *_, reset_range=False):
        if self.result is None:
            return
        result = self.result
        neuron = self.ui.ImagingAnalysis_align_neuronCombo.currentIndex()
        signal = self.ui.ImagingAnalysis_align_signalCombo.currentIndex()
        self._plot(self.plots[0], result.stimulus,
                   mean_role='imaging_stimulus', title='Stimulus — individual repetitions and mean')
        title = self.ui.ImagingAnalysis_align_signalCombo.currentText()
        self._plot(self.plots[1], result.response,
                   mean_role=f'imaging_fluo{neuron + 1}',
                   title=title + ' — individual repetitions and mean')
        if reset_range:
            self.plots[1].setXRange(result.time_ms[0], result.duration_ms, padding=.01)
        theme_manager.style_traces()

    def refresh_theme(self, *_):
        if self.result is not None:
            self.draw()

    def _default_stem(self):
        name = self.page.recording.source.stem
        neuron = self.ui.ImagingAnalysis_align_neuronCombo.currentIndex() + 1
        return f'{name}_neuron{neuron}_aligned'

    def export_csv(self):
        if self.result is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self.window, 'Export aligned imaging cycles',
            str(recordings_directory() / (self._default_stem() + '.csv')),
            'CSV files (*.csv)',
        )
        if not path:
            return
        destination = Path(path)
        if destination.suffix.lower() != '.csv':
            destination = destination.with_suffix('.csv')
        result = self.result
        response_mean, response_sd, response_sem, n_response = mean_sem(result.response)
        stim_mean, _, _, n_stim = mean_sem(result.stimulus)
        columns = {
            'Time from onset (ms)': result.time_ms,
            'Stimulus mean (%)': stim_mean,
            'Stimulus contributing loops': n_stim,
            'Response mean': response_mean,
            'Response SD': response_sd,
            'Response SEM': response_sem,
            'Response contributing loops': n_response,
        }
        for i, (s, f) in enumerate(zip(result.stimulus, result.response), start=1):
            columns[f'Stimulus loop {i} (%)'] = s
            columns[f'Response loop {i}'] = f
        try:
            with destination.open('w', encoding='utf-8', newline='') as handle:
                writer = csv.writer(handle)
                writer.writerow(columns.keys())
                writer.writerows(zip(*columns.values()))
            metadata_path = destination.with_name(destination.stem + '_meta.json')
            metadata = {
                'source_recording': self.page.recording.source.name,
                'indicator_name': self.page.recording.metadata.get('indicator_name'),
                'signal': self.ui.ImagingAnalysis_align_signalCombo.currentText(),
                'processing_parameters': (
                    self.page.processed_recording.parameters()
                    if self.ui.ImagingAnalysis_align_signalCombo.currentIndex() >= 2
                    and self.page.processed_recording is not None else None),
                'neuron': self.ui.ImagingAnalysis_align_neuronCombo.currentIndex() + 1,
                'alignment_source': result.anchor_source,
                'stimulus_threshold': (self.ui.ImagingAnalysis_align_thresholdEdit.text()
                                      if result.anchor_source == 'stimulus' else None),
                'pretrigger_ms': float(self.ui.ImagingAnalysis_align_preEdit.text()),
                'cycle_period_ms': result.duration_ms,
                'frame_step_ms': result.frame_step_ms,
                'observed_onsets': result.n_candidates,
                'included_cycles': result.n_cycles,
                'accepted_onsets_ms': result.starts_ms.tolist(),
                'excluded_irregular': result.excluded_irregular,
                'excluded_incomplete': result.excluded_incomplete,
                'excluded_insufficient_frame_coverage': result.excluded_frame_gaps,
                'method': 'Camera-frame interpolation restricted to contiguous acquisition segments',
                'input_files_unchanged': True,
            }
            metadata_path.write_text(json.dumps(metadata, indent=2, allow_nan=False), encoding='utf-8')
        except (OSError, ValueError) as exc:
            themed_message_box(self.window, 'Cannot export aligned data', str(exc)).exec()

    def export_image(self):
        if self.result is None:
            return
        folder = QFileDialog.getExistingDirectory(
            self.window, 'Export aligned imaging plots',
            save_dialog_directory(recordings_directory()),
        )
        if not folder:
            return
        try:
            for suffix, plot in zip(('stimulus', 'response'), self.plots):
                ImageExporter(plot.getPlotItem()).export(
                    str(Path(folder) / f'{self._default_stem()}_{suffix}.png')
                )
        except (OSError, RuntimeError, ValueError) as exc:
            themed_message_box(self.window, 'Cannot export alignment graphs', str(exc)).exec()
