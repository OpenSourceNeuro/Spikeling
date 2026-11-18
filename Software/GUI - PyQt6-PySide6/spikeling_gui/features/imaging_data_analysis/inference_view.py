"""Qt Designer-bound inference UI; measured fluorescence is blind to reference events.

All visible widgets are defined in the editable UI_Spikeling.ui. This class
only binds their behaviour, paints results and exports provenance.
"""
from __future__ import annotations

from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd
import pyqtgraph as pg
from PySide6.QtCore import QObject, QSignalBlocker, Qt
from PySide6.QtWidgets import QApplication, QFileDialog, QTableWidgetItem
from pyqtgraph.exporters import ImageExporter

from spikeling_gui.appearance.dialogs import themed_message_box
from spikeling_gui.appearance.theme_manager import theme_manager
from spikeling_gui.paths import recordings_directory, save_dialog_directory

from .inference import InferenceSettings, infer_activity, validate_activity


TABLE_COLUMNS = (
    'No.', 'Inferred time (ms)', 'Innovation (ΔF/F₀ %)',
    'Reference status', 'Reference time (ms)', 'Time error (ms)',
)


def _fmt(value, precision=4):
    return '—' if value is None or not np.isfinite(value) else f'{value:.{precision}g}'


def _plot_with_gaps(plot, time, values, gaps, role):
    cuts = np.flatnonzero(gaps)
    x = np.insert(time, cuts, np.nan)
    y = np.insert(values, cuts, np.nan)
    theme_manager.themed_plot(plot, x, y, role, connect='finite')


def _file_digest(path: Path) -> str:
    result = sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            result.update(block)
    return result.hexdigest()


class ImagingInferenceView(QObject):
    def __init__(self, page):
        super().__init__(page)
        self.page = page
        self.window = page.window
        self.ui = page.ui
        self.result = None
        self.validation = None
        u = self.ui
        u.ImagingAnalysis_inference_calculateButton.clicked.connect(self.calculate)
        u.ImagingAnalysis_inference_validateButton.clicked.connect(self.toggle_validation)
        u.ImagingAnalysis_inference_exportButton.clicked.connect(self.export_csv)
        u.ImagingAnalysis_inference_imageButton.clicked.connect(self.export_images)
        u.ImagingAnalysis_inference_neuronCombo.currentIndexChanged.connect(self.draw)
        u.ImagingAnalysis_inference_modelCombo.currentIndexChanged.connect(self._model_changed)
        u.ImagingAnalysis_inference_signalCombo.currentIndexChanged.connect(self.invalidate)
        for key in ('decayEdit', 'riseEdit', 'baselineEdit', 'penaltyEdit',
                    'thresholdEdit', 'separationEdit', 'intervalEdit', 'iterationsEdit'):
            getattr(u, 'ImagingAnalysis_inference_' + key).textEdited.connect(self.invalidate)
        for key in ('toleranceEdit', 'binEdit'):
            getattr(u, 'ImagingAnalysis_inference_' + key).textEdited.connect(self.invalidate_validation)
        u.ImagingAnalysis_inference_markersCheck.toggled.connect(self.draw)
        u.ImagingAnalysis_inference_reconstructionCheck.toggled.connect(self.draw)
        self.plots = (u.ImagingAnalysis_inference_signalPlot,
                      u.ImagingAnalysis_inference_innovationPlot,
                      u.ImagingAnalysis_inference_validationPlot)
        for plot in self.plots:
            theme_manager.set_plot_background_role(plot, 'panel_background')
            plot.showGrid(x=True, y=True, alpha=.2)
            plot.getAxis('left').setWidth(60)
            plot.setDownsampling(auto=True, mode='peak')
        self.plots[1].setXLink(self.plots[0])
        self.plots[2].setXLink(self.plots[0])
        self.plots[1].setLabel('bottom', 'Camera time (ms)')
        table = u.ImagingAnalysis_inference_eventTable
        table.setColumnCount(len(TABLE_COLUMNS))
        table.setHorizontalHeaderLabels(TABLE_COLUMNS)
        table.setSortingEnabled(False)
        table.currentCellChanged.connect(self.focus_event)
        self._model_changed()
        self.reset()
        theme_manager.themeChanged.connect(self.refresh_theme)

    def _model_changed(self, *_):
        self.ui.ImagingAnalysis_inference_riseEdit.setEnabled(
            self.ui.ImagingAnalysis_inference_modelCombo.currentIndex() == 1)
        self.invalidate()

    def _update_processed(self):
        combo = self.ui.ImagingAnalysis_inference_signalCombo
        item = combo.model().item(1)
        available = getattr(self.page, 'processed_recording', None) is not None
        if item is not None:
            item.setEnabled(available)
        if not available and combo.currentIndex() == 1:
            with QSignalBlocker(combo):
                combo.setCurrentIndex(0)

    def reset(self):
        self.result = None
        self.validation = None
        self._update_processed()
        loaded = self.page.recording is not None
        u = self.ui
        for name in ('calculateButton', 'neuronCombo', 'signalCombo'):
            getattr(u, 'ImagingAnalysis_inference_' + name).setEnabled(loaded)
        for name in ('validateButton', 'exportButton', 'imageButton'):
            getattr(u, 'ImagingAnalysis_inference_' + name).setEnabled(False)
        u.ImagingAnalysis_inference_validateButton.setText('Reveal reference & validate')
        u.ImagingAnalysis_inference_summaryLabel.setText(
            'Load an imaging recording, choose a decay model and run fluorescence-only inference.')
        u.ImagingAnalysis_inference_qualityLabel.setText(
            'Inference estimates sparse optical innovations, not a calibrated action-potential count.')
        u.ImagingAnalysis_inference_validationLabel.setText(
            'Reference events are withheld until you explicitly reveal and validate.')
        u.ImagingAnalysis_inference_eventTable.setRowCount(0)
        for plot in self.plots:
            plot.clear()
        self.plots[2].setVisible(False)

    def invalidate(self, *_):
        if self.result is not None:
            self.reset()
            self.ui.ImagingAnalysis_inference_summaryLabel.setText(
                'Settings or processed data changed. Run inference again before validation.')
        else:
            self._update_processed()

    def invalidate_validation(self, *_):
        if self.validation is not None:
            self.validation = None
            self.ui.ImagingAnalysis_inference_validateButton.setText('Reveal reference & validate')
            self.ui.ImagingAnalysis_inference_validationLabel.setText(
                'Validation settings changed. Reference hidden; reveal again to recalculate metrics.')
            self.draw()

    def _settings(self):
        u = self.ui
        def number(name):
            return float(getattr(u, 'ImagingAnalysis_inference_' + name).text().strip())
        iterations = number('iterationsEdit')
        if not iterations.is_integer():
            raise ValueError('Iterations must be an integer')
        return InferenceSettings(
            source=('recorded', 'processed')[u.ImagingAnalysis_inference_signalCombo.currentIndex()],
            model=('ar1', 'ar2')[u.ImagingAnalysis_inference_modelCombo.currentIndex()],
            decay_ms=number('decayEdit'),
            rise_ms=number('riseEdit'),
            baseline_percentile=number('baselineEdit'),
            sparsity_penalty=number('penaltyEdit'),
            event_threshold=number('thresholdEdit'),
            min_separation_ms=number('separationEdit'),
            analysis_interval_ms=number('intervalEdit'),
            max_iterations=int(iterations),
        )

    def calculate(self, *_):
        rec = self.page.recording
        if rec is None:
            return
        try:
            settings = self._settings()
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            try:
                result = infer_activity(rec, getattr(self.page, 'processed_recording', None), settings)
            finally:
                QApplication.restoreOverrideCursor()
        except (ValueError, TypeError, IndexError, OverflowError) as error:
            self.reset()
            self.ui.ImagingAnalysis_inference_summaryLabel.setText('Inference unavailable: ' + str(error))
            return
        self.result = result
        self.validation = None
        self.ui.ImagingAnalysis_inference_validateButton.setText('Reveal reference & validate')
        self.ui.ImagingAnalysis_inference_validateButton.setEnabled(True)
        self.ui.ImagingAnalysis_inference_exportButton.setEnabled(True)
        self.ui.ImagingAnalysis_inference_imageButton.setEnabled(True)
        counts = ', '.join(f'N{k}: {result.metrics[k-1]["inferred_event_count"]}' for k in (1, 2, 3))
        model_label = 'AR(1)' if settings.model == 'ar1' else 'AR(2)-like'
        self.ui.ImagingAnalysis_inference_summaryLabel.setText(
            f'{len(result.events)} candidate events ({counts}) · {model_label} nonnegative '
            f'deconvolution · {settings.source} ΔF/F₀ · reference withheld.')
        self.ui.ImagingAnalysis_inference_summaryLabel.setToolTip('\n'.join(result.warnings))
        self.ui.ImagingAnalysis_inference_validationLabel.setText(
            'Reference withheld. Click Reveal reference & validate only after interpreting your inference.')
        self.draw(reset_range=True)

    def toggle_validation(self):
        if self.result is None:
            return
        if self.validation is not None:
            self.validation = None
            self.ui.ImagingAnalysis_inference_validateButton.setText('Reveal reference & validate')
            self.ui.ImagingAnalysis_inference_validationLabel.setText(
                'Reference hidden again. Any export made now excludes reference events and validation metrics.')
            self.draw()
            return
        try:
            tolerance = float(self.ui.ImagingAnalysis_inference_toleranceEdit.text().strip())
            bin_ms = float(self.ui.ImagingAnalysis_inference_binEdit.text().strip())
            validation = validate_activity(self.page.recording, self.result, tolerance, bin_ms)
        except (ValueError, TypeError, OverflowError) as error:
            themed_message_box(self.window, 'Cannot validate inferred events', str(error)).exec()
            return
        self.validation = validation
        self.ui.ImagingAnalysis_inference_validateButton.setText('Hide reference events')
        self.ui.ImagingAnalysis_inference_validationLabel.setText(
            'Reference revealed · ' + validation.provenance + ' · one-to-one matches within '
            + _fmt(validation.tolerance_ms) + ' ms. '
            + 'A marker may be a Vm-threshold estimate rather than independently measured truth.')
        self.ui.ImagingAnalysis_inference_validationLabel.setToolTip('\n'.join(validation.warnings))
        self.draw()

    def draw(self, *_, reset_range=False):
        if self.result is None:
            return
        u = self.ui
        res = self.result
        neuron = u.ImagingAnalysis_inference_neuronCombo.currentIndex()
        if neuron not in (0, 1, 2):
            return
        signal, innovations, comparison = self.plots
        for plot in self.plots:
            plot.clear()
        role = f'imaging_fluo{neuron+1}'
        _plot_with_gaps(signal, res.time_ms, res.measured_dff_percent[:, neuron],
                        res.gaps_before, 'analysis_loop')
        if u.ImagingAnalysis_inference_reconstructionCheck.isChecked():
            _plot_with_gaps(signal, res.time_ms, res.reconstruction_percent[:, neuron],
                            res.gaps_before, role)
        signal.setTitle('Recorded or processed ΔF/F₀ and fitted fluorescence',
                        color=theme_manager.active_colour('text_primary'), size='9pt')
        _plot_with_gaps(innovations, res.time_ms, res.innovations_percent[:, neuron],
                        res.gaps_before, role)
        innovations.setTitle('Non-negative inferred innovations (ΔF/F₀ percentage points)',
                             color=theme_manager.active_colour('text_primary'), size='9pt')
        events = res.for_neuron(neuron)
        if events and u.ImagingAnalysis_inference_markersCheck.isChecked():
            innovations.addItem(pg.ScatterPlotItem(
                x=np.asarray([e.time_ms for e in events]),
                y=np.asarray([e.innovation_percent for e in events]),
                pen=pg.mkPen(theme_manager.active_colour('analysis_spike_rate')),
                brush=pg.mkBrush(theme_manager.active_colour('analysis_spike_rate')),
                symbol='o', size=7))
        m = res.metrics[neuron]
        u.ImagingAnalysis_inference_qualityLabel.setText(
            f'Neuron {neuron+1} · {m["inferred_event_count"]} candidate event(s) · '
            f'{m["analysis_frames"]} optical frames used for inference '
            f'(from {res.time_ms.size} acquired) · reconstruction RMSE '
            f'{_fmt(m["reconstruction_rmse_percent"])}% · R² {_fmt(m["reconstruction_r2"])}.'
            + (' R² measures fluorescence fit, not spike accuracy.' if self.validation is None else ''))
        validation = self.validation
        comparison.setVisible(validation is not None)
        self.plots[1].setLabel('bottom', 'Camera time (ms)' if validation is None else '')
        if validation is not None:
            relevant = [r for r in validation.rows if r['neuron'] == neuron+1]
            ref = sorted({r['reference_ms'] for r in relevant if r['reference_ms'] is not None})
            comparison.setTitle('Reference (top) versus inferred events (bottom)',
                                color=theme_manager.active_colour('text_primary'), size='9pt')
            if ref:
                comparison.addItem(pg.ScatterPlotItem(
                    x=np.asarray(ref), y=np.ones(len(ref)),
                    pen=pg.mkPen(theme_manager.active_colour('neuron_vm')),
                    brush=pg.mkBrush(theme_manager.active_colour('neuron_vm')),
                    symbol='t1', size=7))
            if events:
                comparison.addItem(pg.ScatterPlotItem(
                    x=np.asarray([e.time_ms for e in events]),
                    y=np.zeros(len(events)),
                    pen=pg.mkPen(theme_manager.active_colour(role)),
                    brush=pg.mkBrush(theme_manager.active_colour(role)),
                    symbol='o', size=6))
            comparison.setYRange(-.5, 1.5, padding=0)
            comparison.setLabel('bottom', 'Camera time (ms)')
            vm = validation.metrics[neuron]
            u.ImagingAnalysis_inference_validationLabel.setText(
                f'Reference: {validation.provenance} · N{neuron+1}: '
                f'{vm["matched"]} matched, {vm["false_positive"]} unmatched inferences, '
                f'{vm["false_negative"]} missed references '
                f'({vm["unobservable_reference_count"]} outside fully observed frame segments) · '
                f'precision {_fmt(vm["precision"])} · recall {_fmt(vm["recall"])} · '
                f'F1 {_fmt(vm["f1"])} · median |timing error| '
                f'{_fmt(vm["median_absolute_timing_error_ms"])} ms · '
                f'rate correlation {_fmt(vm["binned_rate_correlation"])}.')
        rows = []
        if validation is None:
            rows = [('\u2014' if False else str(i+1), _fmt(e.time_ms), _fmt(e.innovation_percent),
                     'Reference withheld', '\u2014', '\u2014') for i, e in enumerate(events)]
        else:
            match_rows = [r for r in validation.rows if r['neuron'] == neuron+1]
            value_lookup = {e.time_ms: e.innovation_percent for e in events}
            for index, entry in enumerate(match_rows):
                rows.append((str(index+1), _fmt(entry['estimated_ms']),
                             _fmt(value_lookup.get(entry['estimated_ms'])) if entry['estimated_ms'] is not None else '\u2014',
                             entry['classification'], _fmt(entry['reference_ms']), _fmt(entry['time_error_ms'])))
        table = u.ImagingAnalysis_inference_eventTable
        table.setRowCount(len(rows))
        for row_i, values in enumerate(rows):
            for col, value in enumerate(values):
                cell = QTableWidgetItem(value)
                if col != 3:
                    cell.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                table.setItem(row_i, col, cell)
        for plot in self.plots:
            plot.enableAutoRange(axis='y')
        if reset_range and len(res.time_ms) > 1:
            signal.setXRange(float(res.time_ms[0]), float(res.time_ms[-1]), padding=.015)
        theme_manager.style_traces()

    def focus_event(self, row, _column, _old_row, _old_column):
        if self.result is None or row < 0:
            return
        item = self.ui.ImagingAnalysis_inference_eventTable.item(row, 1)
        if item is None:
            return
        try:
            t = float(item.text())
        except ValueError:
            return
        self.plots[0].setXRange(t - 500, t + 500, padding=0)

    def refresh_theme(self, *_):
        if self.result is not None:
            self.draw()

    def export_csv(self):
        if self.result is None:
            return
        rec = self.page.recording
        path, _ = QFileDialog.getSaveFileName(
            self.window, 'Export inferred neural activity',
            str(recordings_directory() / (rec.source.stem + '_imaging_inference.csv')),
            'CSV files (*.csv)')
        if not path:
            return
        destination = Path(path)
        if destination.suffix.lower() != '.csv':
            destination = destination.with_suffix('.csv')
        metadata_path = destination.with_name(destination.stem + '_meta.json')
        frames_path = destination.with_name(destination.stem + '_frames.csv')
        sources = (rec.source, rec.frames_source, rec.metadata_source)
        protected = {p.resolve() for p in sources}
        if (any(path.resolve() in protected for path in (destination, metadata_path, frames_path))
                or any(path.exists() for path in (destination, metadata_path, frames_path))):
            themed_message_box(self.window, 'Choose another export filename',
                'Source recordings and existing exported results cannot be overwritten.').exec()
            return
        values = [e.to_dict() for e in self.result.events]
        if self.validation is None:
            rows = [{**v, 'reference_status': 'withheld', 'reference_ms': None,
                     'time_error_ms': None} for v in values]
        else:
            # Validation rows include missed references with no inferred event.
            values_index = {(v['neuron'], v['time_ms']): v for v in values}
            rows = []
            for match in self.validation.rows:
                event = values_index.get((match['neuron'], match['estimated_ms']), {})
                rows.append({**event, 'neuron': match['neuron'],
                             'time_ms': match['estimated_ms'],
                             'reference_status': match['classification'],
                             'reference_ms': match['reference_ms'],
                             'time_error_ms': match['time_error_ms']})
        provenance = {
            'schema': 'Spikeling imaging spike inference v1',
            'created_at_iso': datetime.now().astimezone().isoformat(timespec='seconds'),
            'source_recording': rec.source.name,
            'input_file_sha256': {p.name: _file_digest(p) for p in sources},
            'indicator': rec.metadata.get('indicator_name'),
            'signal_source': self.result.settings.source,
            'method': ('Nonnegative L1-penalised least squares with AR(1) exponential decay '
                       'or AR(2)-like rise/decay kernel; FISTA; explicit observed-frame '
                       'subsampling for numerical stability; gap-separated analysis'),
            'settings': self.result.settings.to_dict(),
            'processing': self.page.processed_recording.parameters()
                          if self.result.settings.source == 'processed' else None,
            'metrics_by_neuron': list(self.result.metrics),
            'warnings': list(self.result.warnings),
            'reference_revealed': self.validation is not None,
            'reference_provenance': self.validation.provenance if self.validation else None,
            'validation_metrics': list(self.validation.metrics) if self.validation else None,
            'validation_tolerance_ms': self.validation.tolerance_ms if self.validation else None,
            'validation_bin_ms': self.validation.bin_ms if self.validation else None,
            'validation_warnings': list(self.validation.warnings) if self.validation else None,
            'model_reference_used_for_inference': False,
            'inferred_events_are_not_verified_spikes': True,
            'original_recording_unchanged': True,
            'inferred_frames_export': frames_path.name,
        }
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            with TemporaryDirectory(dir=destination.parent) as temp_dir:
                temp = Path(temp_dir)
                result_tmp = temp / destination.name
                metadata_tmp = temp / metadata_path.name
                frames_tmp = temp / frames_path.name
                columns = ('neuron', 'time_ms', 'innovation_percent', 'frame_index',
                           'reference_status', 'reference_ms', 'time_error_ms')
                pd.DataFrame(rows, columns=columns).to_csv(result_tmp, index=False)
                frame_columns = {'FrameTime (ms)': self.result.time_ms}
                for neuron in range(3):
                    suffix = f'Neuron {neuron+1}'
                    frame_columns[f'{suffix} measured DF/F0 (%)'] = self.result.measured_dff_percent[:, neuron]
                    frame_columns[f'{suffix} reconstructed DF/F0 (%)'] = self.result.reconstruction_percent[:, neuron]
                    frame_columns[f'{suffix} inferred innovation (%)'] = self.result.innovations_percent[:, neuron]
                pd.DataFrame(frame_columns).to_csv(frames_tmp, index=False)
                metadata_tmp.write_text(json.dumps(provenance, indent=2, allow_nan=False), encoding='utf-8')
                published = []
                try:
                    for staged, path in ((result_tmp, destination), (frames_tmp, frames_path),
                                         (metadata_tmp, metadata_path)):
                        staged.replace(path)
                        published.append(path)
                except OSError:
                    for path in reversed(published):
                        path.unlink(missing_ok=True)
                    raise
        except (OSError, ValueError, TypeError) as error:
            themed_message_box(self.window, 'Cannot export inference', str(error)).exec()
            return
        self.ui.ImagingAnalysis_inference_summaryLabel.setToolTip(f'Exported: {destination}')

    def export_images(self):
        if self.result is None:
            return
        folder = QFileDialog.getExistingDirectory(
            self.window, 'Export inference graphs',
            save_dialog_directory(recordings_directory()))
        if not folder:
            return
        dest = Path(folder)
        prefix = self.page.recording.source.stem + f'_inference_neuron{self.ui.ImagingAnalysis_inference_neuronCombo.currentIndex()+1}'
        files = [dest / f'{prefix}_fluorescence.png', dest / f'{prefix}_innovations.png']
        if self.validation is not None:
            files.append(dest / f'{prefix}_reference_comparison.png')
        if any(p.exists() for p in files):
            themed_message_box(self.window, 'Graph export already exists',
                               'Choose a different directory to preserve existing exported graphs.').exec()
            return
        try:
            for filename, plot in zip(files, self.plots):
                ImageExporter(plot.plotItem).export(str(filename))
        except (OSError, RuntimeError, ValueError) as error:
            themed_message_box(self.window, 'Cannot export inference plots', str(error)).exec()
