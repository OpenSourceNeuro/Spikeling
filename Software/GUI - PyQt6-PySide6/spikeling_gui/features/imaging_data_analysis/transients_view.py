"""Qt Designer-bound view for saved one-pixel imaging transient measurements.

Visible controls are declared in UI_Spikeling.ui, never constructed here.
The view only connects controls, draws recorded/processed optical data and
exports reproducible results. Calcium transients are NOT inferred spikes.
"""
from __future__ import annotations

from dataclasses import fields
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd
from PySide6.QtCore import QObject, QSignalBlocker, Qt
from PySide6.QtWidgets import QFileDialog, QTableWidgetItem
from pyqtgraph.exporters import ImageExporter

from spikeling_gui.appearance.dialogs import themed_message_box
from spikeling_gui.appearance.theme_manager import theme_manager
from spikeling_gui.paths import recordings_directory, save_dialog_directory

from .align import _sample_gaps
from .transients import TransientSettings, detect_transients


TABLE_COLUMNS = (
    'Event', 'Onset (ms)', 'Peak (ms)', 'Amplitude (%)', 'Width ½ prom. (ms)',
    'Rise 10–90 (ms)', 'Decay 1/e (ms)', 'AUC (%·ms)',
    'Stimulus latency (ms)', 'Notes',
)


def _fmt(value, digits=4):
    return '—' if value is None or not np.isfinite(value) else f'{value:.{digits}g}'


def _separate(x, y, gaps):
    cuts = np.flatnonzero(gaps)
    return np.insert(x, cuts, np.nan), np.insert(y, cuts, np.nan)


def _file_digest(path: Path) -> str:
    digest = sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


class ImagingTransientsView(QObject):
    def __init__(self, page):
        super().__init__(page)
        self.page = page
        self.window = page.window
        self.ui = page.ui
        self.result = None
        u = self.ui
        u.ImagingAnalysis_transients_calculateButton.clicked.connect(self.calculate)
        u.ImagingAnalysis_transients_exportButton.clicked.connect(self.export_csv)
        u.ImagingAnalysis_transients_imageButton.clicked.connect(self.export_images)
        u.ImagingAnalysis_transients_neuronCombo.currentIndexChanged.connect(self.draw)
        u.ImagingAnalysis_transients_markersCheck.toggled.connect(self.draw)
        u.ImagingAnalysis_transients_stimulusMarkersCheck.toggled.connect(self.draw)
        u.ImagingAnalysis_transients_signalCombo.currentIndexChanged.connect(self.invalidate)
        u.ImagingAnalysis_transients_responseSourceCombo.currentIndexChanged.connect(self._source_changed)
        for key in ('prominenceEdit', 'amplitudeEdit', 'widthEdit',
                    'separationEdit', 'baselineWindowEdit', 'thresholdEdit',
                    'responseWindowEdit'):
            getattr(u, 'ImagingAnalysis_transients_' + key).textEdited.connect(self.invalidate)
        self.plots = (u.ImagingAnalysis_transients_stimulusPlot,
                      u.ImagingAnalysis_transients_signalPlot)
        for plot in self.plots:
            theme_manager.set_plot_background_role(plot, 'panel_background')
            plot.showGrid(x=True, y=True, alpha=.22)
            plot.getAxis('left').setWidth(65)
            plot.setDownsampling(auto=True, mode='peak')
        self.plots[0].setXLink(self.plots[1])
        self.plots[1].setLabel('bottom', 'Acquisition time (ms)')
        table = u.ImagingAnalysis_transients_eventTable
        table.setColumnCount(len(TABLE_COLUMNS))
        table.setHorizontalHeaderLabels(TABLE_COLUMNS)
        table.setSortingEnabled(False)
        table.currentCellChanged.connect(self.focus_selected_event)
        self._source_changed()
        self.reset()
        theme_manager.themeChanged.connect(self.refresh_theme)

    def _source_changed(self, *_):
        stim = self.ui.ImagingAnalysis_transients_responseSourceCombo.currentIndex()
        self.ui.ImagingAnalysis_transients_thresholdEdit.setEnabled(stim == 2)
        self.ui.ImagingAnalysis_transients_responseWindowEdit.setEnabled(stim != 0)
        self.invalidate()

    def _update_processed_option(self):
        combo = self.ui.ImagingAnalysis_transients_signalCombo
        item = combo.model().item(1)
        enabled = getattr(self.page, 'processed_recording', None) is not None
        if item is not None:
            item.setEnabled(enabled)
        if not enabled and combo.currentIndex() == 1:
            with QSignalBlocker(combo):
                combo.setCurrentIndex(0)

    def reset(self):
        self.result = None
        self._update_processed_option()
        loaded = self.page.recording is not None
        u = self.ui
        for control in (u.ImagingAnalysis_transients_calculateButton,
                        u.ImagingAnalysis_transients_neuronCombo,
                        u.ImagingAnalysis_transients_signalCombo):
            control.setEnabled(loaded)
        u.ImagingAnalysis_transients_exportButton.setEnabled(False)
        u.ImagingAnalysis_transients_imageButton.setEnabled(False)
        u.ImagingAnalysis_transients_summaryLabel.setText(
            'Load a recording, choose detection thresholds, then Detect transients.'
        )
        u.ImagingAnalysis_transients_qualityLabel.setText(
            'Only camera-frame ΔF/F₀ is analysed. Detection of a calcium transient is not detection of a single spike.'
        )
        u.ImagingAnalysis_transients_eventTable.setRowCount(0)
        for plot in self.plots:
            plot.clear()

    def invalidate(self, *_):
        if self.result is not None:
            self.reset()
            self.ui.ImagingAnalysis_transients_summaryLabel.setText(
                'Detection settings or processed signal changed. Click Detect transients to recalculate.'
            )
        else:
            self._update_processed_option()

    def _settings(self):
        u = self.ui
        def number(key):
            return float(getattr(u, 'ImagingAnalysis_transients_' + key).text().strip())
        return TransientSettings(
            source=('recorded', 'processed')[u.ImagingAnalysis_transients_signalCombo.currentIndex()],
            min_prominence_percent=number('prominenceEdit'),
            min_amplitude_percent=number('amplitudeEdit'),
            min_width_ms=number('widthEdit'),
            min_separation_ms=number('separationEdit'),
            baseline_window_ms=number('baselineWindowEdit'),
            response_source=('none', 'trigger', 'stimulus')[u.ImagingAnalysis_transients_responseSourceCombo.currentIndex()],
            stimulus_threshold=number('thresholdEdit'),
            response_window_ms=number('responseWindowEdit'),
        )

    def calculate(self, *_):
        rec = self.page.recording
        if rec is None:
            return
        try:
            result = detect_transients(rec, self._settings(),
                                       processed=getattr(self.page, 'processed_recording', None))
        except (ValueError, TypeError, IndexError, OverflowError) as error:
            self.reset()
            self.ui.ImagingAnalysis_transients_summaryLabel.setText('Detection unavailable: ' + str(error))
            return
        self.result = result
        self.ui.ImagingAnalysis_transients_exportButton.setEnabled(True)
        self.ui.ImagingAnalysis_transients_imageButton.setEnabled(True)
        counts = ', '.join(f'neuron {n}: {result.metrics[n-1]["events"]}' for n in (1,2,3))
        self.ui.ImagingAnalysis_transients_summaryLabel.setText(
            f'{len(result.events)} detected calcium transients ({counts}) · '
            f'{result.signal_source} ΔF/F₀ · camera-frame timing · '
            f'{len(result.warnings)} notice(s)'
        )
        self.ui.ImagingAnalysis_transients_summaryLabel.setToolTip('\n'.join(result.warnings))
        self.draw(reset_range=True)

    def draw(self, *_, reset_range=False):
        if self.result is None:
            return
        u = self.ui
        rec = self.page.recording
        result = self.result
        neuron = u.ImagingAnalysis_transients_neuronCombo.currentIndex()
        if not 0 <= neuron <= 2:
            return
        stimulus_plot, signal_plot = self.plots
        stimulus_plot.clear()
        signal_plot.clear()
        sample_gaps = _sample_gaps(rec)
        x, y = _separate(rec.sample_time_ms, rec.stimulus, sample_gaps)
        theme_manager.themed_plot(stimulus_plot, x, y, 'imaging_stimulus', connect='finite')
        stimulus_plot.setTitle('Recorded stimulus and optional onset markers',
                               color=theme_manager.active_colour('text_primary'), size='9pt')
        if u.ImagingAnalysis_transients_stimulusMarkersCheck.isChecked() and len(result.stimulus_onsets_ms):
            import pyqtgraph as pg
            stimulus_plot.addItem(pg.ScatterPlotItem(
                x=result.stimulus_onsets_ms,
                y=np.zeros_like(result.stimulus_onsets_ms),
                pen=pg.mkPen(theme_manager.active_colour('imaging_stimulus')),
                brush=pg.mkBrush(theme_manager.active_colour('imaging_stimulus')),
                symbol='t1', size=7,
            ))
        tx, fy = _separate(result.time_ms, result.dff_percent[:, neuron], result.gaps_before)
        theme_manager.themed_plot(signal_plot, tx, fy, f'imaging_fluo{neuron+1}', connect='finite')
        events = result.for_neuron(neuron)
        label = ('Recorded' if result.signal_source == 'recorded' else 'Processed')
        signal_plot.setTitle(f'{label} ΔF/F₀ (%) — Neuron {neuron+1} · {len(events)} transients',
                             color=theme_manager.active_colour('text_primary'), size='9pt')
        if events and u.ImagingAnalysis_transients_markersCheck.isChecked():
            import pyqtgraph as pg
            signal_plot.addItem(pg.ScatterPlotItem(
                x=np.asarray([event.peak_ms for event in events]),
                y=np.asarray([event.peak_dff_percent for event in events]),
                pen=pg.mkPen(theme_manager.active_colour('analysis_spike_rate')),
                brush=pg.mkBrush(theme_manager.active_colour('analysis_spike_rate')),
                symbol='o', size=7,
            ))
            known = [event for event in events if event.onset_ms is not None]
            if known:
                signal_plot.addItem(pg.ScatterPlotItem(
                    x=np.asarray([event.onset_ms for event in known]),
                    y=np.asarray([event.baseline_dff_percent + event.amplitude_percent * .1 for event in known]),
                    pen=pg.mkPen(theme_manager.active_colour('imaging_stimulus')),
                    brush=pg.mkBrush(theme_manager.active_colour('imaging_stimulus')),
                    symbol='t', size=7,
                ))
        signal_plot.enableAutoRange(axis='y')
        stimulus_plot.enableAutoRange(axis='y')
        m = result.metrics[neuron]
        fraction = m['trial_response_fraction']
        association = (f'{m["usable_stimulus_windows"]} complete stimulus windows, '
                       f'{m["excluded_stimulus_windows"]} excluded, '
                       f'{_fmt(100. * fraction) if fraction is not None else "not estimable"}% with a transient, '
                       f'mean onset latency {_fmt(m["mean_response_latency_ms"])} ms' 
                       if result.settings.response_source != 'none' else 'Stimulus association disabled')
        u.ImagingAnalysis_transients_qualityLabel.setText(
            f'Neuron {neuron+1} · {m["events"]} events over '
            f'{_fmt(m["valid_observed_duration_s"])} observed s · '
            f'rate {_fmt(m["transient_rate_hz"])} transients/s · '
            f'mean amplitude {_fmt(m["mean_amplitude_percent"])}% · '
            f'mean width {_fmt(m["mean_fwhm_ms"])} ms · '
            + association
        )
        table = u.ImagingAnalysis_transients_eventTable
        table.setRowCount(len(events))
        for row, event in enumerate(events):
            fields = (
                str(row + 1), _fmt(event.onset_ms), _fmt(event.peak_ms),
                _fmt(event.amplitude_percent), _fmt(event.fwhm_ms),
                _fmt(event.rise_10_90_ms), _fmt(event.decay_1e_ms),
                _fmt(event.auc_percent_ms), _fmt(event.response_latency_ms), event.notes,
            )
            for col, value in enumerate(fields):
                item = QTableWidgetItem(value)
                if col < len(fields) - 1:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                table.setItem(row, col, item)
        if reset_range:
            signal_plot.setXRange(float(result.time_ms[0]), float(result.time_ms[-1]), padding=.015)
        theme_manager.style_traces()

    def focus_selected_event(self, row, _column, _old_row, _old_column):
        if self.result is None or row < 0:
            return
        events = self.result.for_neuron(self.ui.ImagingAnalysis_transients_neuronCombo.currentIndex())
        if row >= len(events):
            return
        event = events[row]
        half = max(200.0, 4. * event.fwhm_ms)
        self.plots[1].setXRange(event.peak_ms - half, event.peak_ms + half, padding=0)

    def refresh_theme(self, *_):
        if self.result is not None:
            self.draw()

    def _default_stem(self):
        return self.page.recording.source.stem + '_imaging_transients'

    def export_csv(self):
        result = self.result
        if result is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self.window, 'Export calcium transient measurements',
            str(recordings_directory() / (self._default_stem() + '.csv')),
            'CSV files (*.csv)',
        )
        if not path:
            return
        destination = Path(path)
        if destination.suffix.lower() != '.csv':
            destination = destination.with_suffix('.csv')
        details_path = destination.with_name(destination.stem + '_meta.json')
        rec = self.page.recording
        sources = (rec.source, rec.frames_source, rec.metadata_source)
        protected = {p.resolve() for p in sources}
        if (destination.resolve() in protected or details_path.resolve() in protected
                or destination.exists() or details_path.exists()):
            themed_message_box(
                self.window, 'Choose another export filename',
                'An input file or existing export would be overwritten. '
                'Use a new export name to preserve previous results.'
            ).exec()
            return
        event_rows = [e.to_dict() for e in result.events]
        columns = [field.name for field in fields(result.events[0])] if result.events else [
            'neuron','onset_ms','peak_ms','recovery_ms','peak_dff_percent',
            'baseline_dff_percent','amplitude_percent','prominence_percent','fwhm_ms',
            'rise_10_90_ms','decay_1e_ms','auc_percent_ms','stimulus_onset_ms',
            'response_latency_ms','notes',
        ]
        try:
            provenance = {
                'schema': 'Spikeling imaging calcium transients v1',
                'created_at_iso': datetime.now().astimezone().isoformat(timespec='seconds'),
                'source_recording': rec.source.name,
                'input_file_sha256': {p.name: _file_digest(p) for p in sources},
                'indicator': rec.metadata.get('indicator_name'),
                'signal': 'Recorded ΔF/F0' if result.signal_source == 'recorded' else 'Processed ΔF/F0',
                'settings': result.settings.to_dict(),
                'processing_parameters': (self.page.processed_recording.parameters()
                                          if result.signal_source == 'processed' else None),
                'metrics_by_neuron': list(result.metrics),
                'stimulus_response_trials': list(result.response_trials),
                'warnings': list(result.warnings),
                'method': ('Prominence-based calcium transient detection; relative amplitude, '
                           'rise (10–90%), decay-to-1/e, FWHM and AUC estimated on '
                           'observed camera frames, without crossing acquisition gaps'),
                'stimulus_association_not_causation': True,
                'calcium_transients_are_not_individual_spikes': True,
                'input_files_unchanged': True,
            }
            destination.parent.mkdir(parents=True, exist_ok=True)
            with TemporaryDirectory(dir=destination.parent) as tmp_path:
                temp = Path(tmp_path)
                event_temp = temp / destination.name
                details_temp = temp / details_path.name
                pd.DataFrame(event_rows, columns=columns).to_csv(event_temp, index=False)
                details_temp.write_text(json.dumps(provenance, indent=2, allow_nan=False), encoding='utf-8')
                event_temp.replace(destination)
                details_temp.replace(details_path)
        except (OSError, ValueError, TypeError) as error:
            themed_message_box(self.window, 'Cannot export transients', str(error)).exec()

    def export_images(self):
        if self.result is None:
            return
        folder = QFileDialog.getExistingDirectory(
            self.window, 'Export calcium transient analysis graphs',
            save_dialog_directory(recordings_directory()),
        )
        if not folder:
            return
        neuron = self.ui.ImagingAnalysis_transients_neuronCombo.currentIndex() + 1
        try:
            for suffix, plot in zip(('stimulus', 'dff_transients'), self.plots):
                ImageExporter(plot.getPlotItem()).export(
                    str(Path(folder) / f'{self._default_stem()}_neuron{neuron}_{suffix}.png')
                )
        except (OSError, ValueError, RuntimeError) as error:
            themed_message_box(self.window, 'Cannot export transient plots', str(error)).exec()
