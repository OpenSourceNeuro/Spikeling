"""Qt Designer-bound comparison of independent fluorescence recordings.

Never applies GECI models to saved Vm. The two acquisitions are loaded from
separate three-file sets, with model neural references excluded from analysis.
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
from PySide6.QtCore import QObject, Qt
from PySide6.QtWidgets import QFileDialog, QTableWidgetItem
from pyqtgraph.exporters import ImageExporter

from spikeling_gui.appearance.dialogs import themed_message_box
from spikeling_gui.appearance.theme_manager import theme_manager
from spikeling_gui.paths import recordings_directory, save_dialog_directory

from .recording import ImagingRecordingError, load_imaging_recording
from .compare import ComparisonSettings, compare_recordings


TABLE_HEADINGS = ('Measurement', 'Reference', 'Comparison', 'Comparison − reference')


def _number(value):
    if value is None or not isinstance(value, (int, float, np.integer, np.floating)) or not np.isfinite(value):
        return '—'
    return f'{value:.5g}'


def _file_sha(path: Path) -> str:
    digest = sha256()
    with path.open('rb') as stream:
        for part in iter(lambda: stream.read(1024*1024), b''):
            digest.update(part)
    return digest.hexdigest()


def _with_gaps(x, y, gaps):
    breaks = np.flatnonzero(gaps)
    return np.insert(x, breaks, np.nan), np.insert(y, breaks, np.nan)


class ImagingCompareView(QObject):
    def __init__(self, page):
        super().__init__(page)
        self.page = page
        self.window = page.window
        self.ui = page.ui
        self.other = None
        self.result = None
        self._reference_source = None
        u = self.ui
        u.ImagingAnalysis_compare_loadButton.clicked.connect(self.load_comparison)
        u.ImagingAnalysis_compare_clearButton.clicked.connect(self.clear_comparison)
        u.ImagingAnalysis_compare_calculateButton.clicked.connect(self.calculate)
        u.ImagingAnalysis_compare_exportButton.clicked.connect(self.export_data)
        u.ImagingAnalysis_compare_imageButton.clicked.connect(self.export_images)
        u.ImagingAnalysis_compare_neuronCombo.currentIndexChanged.connect(self.draw)
        u.ImagingAnalysis_compare_sourceCombo.currentIndexChanged.connect(self._method_changed)
        u.ImagingAnalysis_compare_modeCombo.currentIndexChanged.connect(self._method_changed)
        u.ImagingAnalysis_compare_anchorCombo.currentIndexChanged.connect(self._method_changed)
        u.ImagingAnalysis_compare_differenceDirectionCombo.currentIndexChanged.connect(self.invalidate)
        for name in ('thresholdEdit', 'periodEdit', 'preEdit', 'percentileEdit'):
            getattr(u, 'ImagingAnalysis_compare_' + name).textEdited.connect(self.invalidate)
        for name in ('stimulusCheck', 'differenceCheck', 'semCheck'):
            getattr(u, 'ImagingAnalysis_compare_' + name).toggled.connect(self.draw)
        self.plots = (u.ImagingAnalysis_compare_stimulusPlot,
                      u.ImagingAnalysis_compare_signalPlot,
                      u.ImagingAnalysis_compare_differencePlot)
        for plot in self.plots:
            theme_manager.set_plot_background_role(plot, 'panel_background')
            plot.showGrid(x=True, y=True, alpha=.2)
            plot.getAxis('left').setWidth(70)
            plot.setDownsampling(auto=True, mode='peak')
            plot.setClipToView(True)
        self.plots[0].setXLink(self.plots[1])
        self.plots[2].setXLink(self.plots[1])
        table = u.ImagingAnalysis_compare_metricsTable
        table.setColumnCount(len(TABLE_HEADINGS))
        table.setHorizontalHeaderLabels(TABLE_HEADINGS)
        table.setSortingEnabled(False)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setStretchLastSection(True)
        # If the independent processing recipe changes, a previously calculated
        # processed comparison cannot silently persist.
        p = 'ImagingAnalysis_processing_'
        for name in ('baselineMethodCombo','backgroundMethodCombo','filterMethodCombo'):
            getattr(u, p+name).currentIndexChanged.connect(self._processing_modified)
        for name in ('percentileEdit','baselineStartEdit','baselineEndEdit','baselineWindowEdit',
                     'backgroundValueEdit','bleachWindowEdit','filterWindowEdit'):
            getattr(u, p+name).textEdited.connect(self._processing_modified)
        u.ImagingAnalysis_processing_bleachCheck.toggled.connect(self._processing_modified)
        self._method_changed()
        self.reset()
        theme_manager.themeChanged.connect(self.refresh_theme)

    def _method_changed(self, *_):
        u = self.ui
        cycles = u.ImagingAnalysis_compare_modeCombo.currentIndex() == 0
        has_anchor = u.ImagingAnalysis_compare_modeCombo.currentIndex() != 1
        u.ImagingAnalysis_compare_anchorCombo.setEnabled(has_anchor)
        u.ImagingAnalysis_compare_thresholdEdit.setEnabled(has_anchor and
                                                          u.ImagingAnalysis_compare_anchorCombo.currentIndex() == 1)
        u.ImagingAnalysis_compare_periodEdit.setEnabled(cycles)
        u.ImagingAnalysis_compare_preEdit.setEnabled(cycles)
        u.ImagingAnalysis_compare_percentileEdit.setEnabled(
            u.ImagingAnalysis_compare_sourceCombo.currentIndex() == 1)
        self.invalidate()

    def _processing_modified(self, *_):
        if self.ui.ImagingAnalysis_compare_sourceCombo.currentIndex() == 2:
            self.invalidate()

    def reset(self):
        """A new reference recording invalidates comparison identity and results."""
        self.other = None
        self._reference_source = None
        self.ui.ImagingAnalysis_compare_comparisonLabel.setText('No comparison recording loaded')
        self.invalidate(force=True)

    def clear_comparison(self):
        self.other = None
        self.ui.ImagingAnalysis_compare_comparisonLabel.setText('No comparison recording loaded')
        self.invalidate(force=True)

    def invalidate(self, *_, force=False):
        if self.result is None and not force:
            return
        self.result = None
        u = self.ui
        u.ImagingAnalysis_compare_exportButton.setEnabled(False)
        u.ImagingAnalysis_compare_imageButton.setEnabled(False)
        u.ImagingAnalysis_compare_metricsTable.setRowCount(0)
        u.ImagingAnalysis_compare_detailsText.setPlainText('')
        for plot in self.plots:
            plot.clear()
        u.ImagingAnalysis_compare_summaryLabel.setText(
            'Select a second independent imaging recording and calculate the comparison.')
        self._refresh_availability()

    def _refresh_availability(self):
        reference = self.page.recording
        u = self.ui
        u.ImagingAnalysis_compare_referenceLabel.setText(
            reference.source.name if reference is not None else 'No reference (load one in Recording)')
        u.ImagingAnalysis_compare_loadButton.setEnabled(reference is not None)
        u.ImagingAnalysis_compare_calculateButton.setEnabled(reference is not None and self.other is not None)
        u.ImagingAnalysis_compare_clearButton.setEnabled(self.other is not None)

    def load_comparison(self):
        reference = self.page.recording
        if reference is None:
            return
        filename, _ = QFileDialog.getOpenFileName(
            self.window, 'Select an independently acquired imaging recording',
            save_dialog_directory(recordings_directory()),
            'Imaging recordings (*.csv);;All files (*)')
        if not filename:
            return
        try:
            other = load_imaging_recording(filename)
            if other.source.resolve() == reference.source.resolve():
                raise ValueError('Choose a different acquisition from the reference recording.')
            # A renamed copy of the same frame CSV is not an independent experiment.
            if _file_sha(other.frames_source) == _file_sha(reference.frames_source):
                raise ValueError('Both fluorescence frame files are identical. Record a separate experiment.')
        except (OSError, ValueError, ImagingRecordingError) as exc:
            themed_message_box(self.window, 'Cannot load comparison recording', str(exc)).exec()
            return
        self.other = other
        self.ui.ImagingAnalysis_compare_comparisonLabel.setText(other.source.name)
        self.ui.ImagingAnalysis_compare_comparisonLabel.setToolTip(str(other.source))
        self.invalidate(force=True)

    def _settings(self):
        u = self.ui
        def number(name):
            return float(getattr(u, 'ImagingAnalysis_compare_'+name).text().strip())
        manual = u.ImagingAnalysis_compare_periodEdit.text().strip()
        return ComparisonSettings(
            source=('recorded','empirical','processed','raw')[u.ImagingAnalysis_compare_sourceCombo.currentIndex()],
            mode=('cycles','elapsed','first_anchor')[u.ImagingAnalysis_compare_modeCombo.currentIndex()],
            anchor_source=('trigger','stimulus')[u.ImagingAnalysis_compare_anchorCombo.currentIndex()],
            stimulus_threshold=number('thresholdEdit'),
            pre_ms=number('preEdit'),
            period_ms=float(manual) if manual else None,
            baseline_percentile=number('percentileEdit'),
            difference_direction=('reference_minus_comparison','comparison_minus_reference')[
                u.ImagingAnalysis_compare_differenceDirectionCombo.currentIndex()],
        )

    def calculate(self):
        rec = self.page.recording
        other = self.other
        if rec is None or other is None:
            return
        try:
            settings = self._settings()
            processing = (self.page.processing_view._settings()
                          if settings.source == 'processed' else None)
            result = compare_recordings(rec, other, settings, processing)
        except (ValueError, TypeError, IndexError, OverflowError) as exc:
            self.invalidate(force=True)
            self.ui.ImagingAnalysis_compare_summaryLabel.setText('Comparison unavailable: '+str(exc))
            return
        self.result = result
        self._reference_source = rec.source.resolve()
        self.ui.ImagingAnalysis_compare_exportButton.setEnabled(True)
        self.ui.ImagingAnalysis_compare_imageButton.setEnabled(True)
        self.ui.ImagingAnalysis_compare_summaryLabel.setText(
            f'Independent acquisitions: {rec.source.name} vs {other.source.name} · '
            f'{settings.source} · {settings.mode} · {len(result.warnings)} caution(s)')
        self.ui.ImagingAnalysis_compare_summaryLabel.setToolTip('\n'.join(result.warnings))
        self._draw_details()
        self.draw(reset_range=True)

    def _draw_details(self):
        r = self.result
        if r is None:
            return
        a, b = r.reference.recording, r.comparison.recording
        lines = [
            'REFERENCE  |  COMPARISON',
            f'File: {a.source.name}  |  {b.source.name}',
            f'Indicator: {a.metadata.get("indicator_name", "Unknown")}  |  {b.metadata.get("indicator_name", "Unknown")}',
            f'Observation model: {a.metadata.get("fluorescence_model", "Unknown")}  |  {b.metadata.get("fluorescence_model", "Unknown")}',
            f'Camera frame rate: {a.nominal_frame_rate_hz:g} Hz  |  {b.nominal_frame_rate_hz:g} Hz',
            f'Optical frames: {a.n_frames:,}  |  {b.n_frames:,}',
            f'Source: {a.source_kind}  |  {b.source_kind}',
            f'Frame gaps: {int(a.frame_gap_before.sum())}  |  {int(b.frame_gap_before.sum())}',
            'CAUTIONS:',
        ]
        lines.extend('• '+str(w) for w in r.warnings)
        if not r.warnings:
            lines.append('No additional warnings detected; verify comparability of stimulus protocols.')
        self.ui.ImagingAnalysis_compare_detailsText.setPlainText('\n'.join(lines))

    def _trace(self, plot, x, y, gaps, role, *, comparator=False):
        sx, sy = _with_gaps(np.asarray(x), np.asarray(y), np.asarray(gaps))
        curve = theme_manager.themed_plot(plot, sx, sy, role, width_scale=1.35, connect='finite')
        if comparator:
            # Persist the dashed comparison style on dark/light theme changes.
            theme_manager.tag_item(curve, role, 1.35, style=Qt.PenStyle.DashLine)
            curve.setPen(theme_manager.pen(role, 1.35, style=Qt.PenStyle.DashLine))
        return curve

    def draw(self, *_, reset_range=False):
        r = self.result
        for plot in self.plots:
            plot.clear()
        if r is None:
            return
        u = self.ui
        neuron = u.ImagingAnalysis_compare_neuronCombo.currentIndex()
        neuron = min(max(neuron, 0), 2)
        unit = r.units
        ref, cmp = r.reference, r.comparison
        fluo_role = f'imaging_fluo{neuron+1}'
        show_stimulus = u.ImagingAnalysis_compare_stimulusCheck.isChecked()
        show_diff = u.ImagingAnalysis_compare_differenceCheck.isChecked() and r.difference_x_ms.size > 0
        self.plots[0].setVisible(show_stimulus)
        self.plots[2].setVisible(show_diff)
        if show_stimulus:
            self._trace(self.plots[0], ref.stimulus_x_ms, ref.stimulus[:, neuron],
                        ref.stimulus_gap_before, 'imaging_stimulus')
            self._trace(self.plots[0], cmp.stimulus_x_ms, cmp.stimulus[:, neuron],
                        cmp.stimulus_gap_before, 'analysis_loop', comparator=True)
        self._trace(self.plots[1], ref.x_ms, ref.y[:, neuron], ref.gap_before, fluo_role)
        self._trace(self.plots[1], cmp.x_ms, cmp.y[:, neuron], cmp.gap_before,
                    'analysis_loop', comparator=True)
        if u.ImagingAnalysis_compare_semCheck.isChecked() and r.settings.mode == 'cycles':
            for condition, role in ((ref, fluo_role), (cmp, 'analysis_loop')):
                mean = condition.y[:, neuron]
                sem = condition.sem[:, neuron]
                # No uncertainty line where fewer than two cycles contributed.
                supported = condition.counts[:, neuron] >= 2
                for sign in (-1, 1):
                    y = np.where(supported, mean+sign*sem, np.nan)
                    self._trace(self.plots[1], condition.x_ms, y,
                                condition.gap_before, role, comparator=True)
        if show_diff:
            nan_gaps = np.zeros(len(r.difference_x_ms), dtype=bool)
            self._trace(self.plots[2], r.difference_x_ms,
                        r.difference[:, neuron], nan_gaps, 'neuron_current')
        time_name = ('Time from stimulus-cycle onset (ms)' if r.settings.mode == 'cycles' else
                     'Time from first observed anchor (ms)' if r.settings.mode == 'first_anchor' else
                     'Elapsed time from first camera frame (ms)')
        self.plots[0].setTitle('Stimulus: reference (solid), comparison (dashed)',
                               color=theme_manager.active_colour('text_primary'), size='9pt')
        self.plots[1].setTitle(f'Neuron {neuron+1}: reference (solid), comparison (dashed) — {unit}',
                               color=theme_manager.active_colour('text_primary'), size='9pt')
        direction_label=('Reference − comparison' if r.settings.difference_direction == 'reference_minus_comparison'
                         else 'Comparison − reference')
        self.plots[2].setTitle(f'{direction_label} — {unit}',
                               color=theme_manager.active_colour('text_primary'), size='9pt')
        bottom = self.plots[2] if show_diff else self.plots[1]
        for plot in self.plots:
            plot.setLabel('bottom', time_name if plot is bottom else '')
            plot.getAxis('bottom').setStyle(showValues=plot is bottom)
            plot.enableAutoRange(axis='y')
        table = u.ImagingAnalysis_compare_metricsTable
        rows = r.metrics_rows(neuron)
        table.setRowCount(len(rows))
        for i, (name, a, b) in enumerate(rows):
            delta = ((a - b if r.settings.difference_direction == 'reference_minus_comparison' else b - a)
                     if isinstance(a, (float,int)) and isinstance(b, (float,int))
                     and np.isfinite(a) and np.isfinite(b) else None)
            for j, val in enumerate((name, _number(a), _number(b), _number(delta))):
                item = QTableWidgetItem(str(val))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(i, j, item)
        table.setHorizontalHeaderLabels((TABLE_HEADINGS[0], TABLE_HEADINGS[1], TABLE_HEADINGS[2],
            'Reference − comparison' if r.settings.difference_direction == 'reference_minus_comparison'
            else 'Comparison − reference'))
        table.resizeColumnsToContents()
        if reset_range:
            self.plots[1].enableAutoRange(axis='x')
        theme_manager.style_traces()

    def refresh_theme(self, *_):
        if self.result is not None:
            self.draw()

    def _export_stem(self):
        return f'{self.page.recording.source.stem}_vs_{self.other.source.stem}_imaging'

    def export_data(self):
        r = self.result
        if r is None:
            return
        filename, _ = QFileDialog.getSaveFileName(
            self.window, 'Save independent imaging comparison',
            str(recordings_directory() / (self._export_stem()+'.csv')), 'CSV files (*.csv)')
        if not filename:
            return
        target = Path(filename)
        if target.suffix.lower() != '.csv':
            target = target.with_suffix('.csv')
        outputs = (target,
                   target.with_name(target.stem+'_difference.csv'),
                   target.with_name(target.stem+'_metrics.csv'),
                   target.with_name(target.stem+'_provenance.json'))
        inputs = tuple(path.resolve() for rec in (r.reference.recording, r.comparison.recording)
                       for path in (rec.source, rec.frames_source, rec.metadata_source))
        if len({p.resolve() for p in outputs}) != len(outputs) or any(
            p.exists() or p.resolve() in inputs for p in outputs):
            themed_message_box(self.window, 'Cannot export comparison',
                               'Choose unused output filenames outside the original recording trio.').exec()
            return
        try:
            records = []
            for condition in (r.reference, r.comparison):
                for neuron in range(3):
                    for at, value, sem, count in zip(
                            condition.x_ms, condition.y[:, neuron],
                            condition.sem[:, neuron], condition.counts[:, neuron]):
                        records.append((condition.label, condition.recording.source.name,
                                        neuron+1, at, value, sem, count, r.units))
            signal = pd.DataFrame.from_records(records, columns=(
                'Condition','Recording','Neuron','Aligned time (ms)',
                'Optical signal','SEM','Contributing cycles','Units'))
            difference = pd.DataFrame({'Aligned time (ms)': r.difference_x_ms,
                                       **{f'Neuron {i+1} comparison minus reference ({r.units})':
                                          r.difference[:, i] for i in range(3)}})
            metrics = []
            for neuron in range(3):
                for label, a, b in r.metrics_rows(neuron):
                    metrics.append({'Neuron': neuron+1, 'Metric':label,
                                    'Reference':a, 'Comparison':b,
                                    'Difference (selected direction)':(
                                        (a-b if r.settings.difference_direction == 'reference_minus_comparison' else b-a)
                                        if isinstance(a,(int,float)) and isinstance(b,(int,float))
                                        and np.isfinite(a) and np.isfinite(b) else None)})
            details = {
                'schema': 'Spikeling independent imaging comparison v1',
                'analysed_at_iso': datetime.now().astimezone().isoformat(timespec='seconds'),
                'processing_is_independent_for_each_recording': True,
                'settings': r.settings.as_dict(), 'units': r.units,
                'raw_fluorescence_difference_disabled': r.settings.source == 'raw',
                'inputs': {
                    condition.label: {
                        'source_files_sha256': {
                            p.name: _file_sha(p) for p in (condition.recording.source,
                                condition.recording.frames_source,condition.recording.metadata_source)},
                        'metadata': condition.recording.metadata,
                        'processing': condition.processing,
                        'cycle_counts': condition.cycles,
                        'excluded_cycles': condition.exclusions,
                        'frame_gaps': int(condition.recording.frame_gap_before.sum()),
                    } for condition in (r.reference, r.comparison)
                },
                'warnings': list(r.warnings),
                'interpretation': ('Comparisons concern independent optical observations. '
                    'Indicator kinetics, baseline, stimulus protocol, sampling and nonlinearity '
                    'limit inference about underlying spike counts.'),
            }
            target.parent.mkdir(parents=True, exist_ok=True)
            with TemporaryDirectory(dir=target.parent) as temp:
                staged = tuple(Path(temp)/path.name for path in outputs)
                signal.to_csv(staged[0], index=False)
                difference.to_csv(staged[1], index=False)
                pd.DataFrame(metrics).to_csv(staged[2], index=False)
                staged[3].write_text(json.dumps(details, ensure_ascii=False, indent=2,
                                                 allow_nan=False, default=str), encoding='utf-8')
                published = []
                try:
                    for src, dst in zip(staged, outputs):
                        if dst.exists():
                            raise FileExistsError(f'Export file already exists: {dst.name}')
                        src.replace(dst)
                        published.append(dst)
                except OSError:
                    for dst in reversed(published):
                        dst.unlink(missing_ok=True)
                    raise
        except (OSError, ValueError, TypeError) as exc:
            themed_message_box(self.window, 'Cannot export comparison', str(exc)).exec()

    def export_images(self):
        if self.result is None:
            return
        folder = QFileDialog.getExistingDirectory(
            self.window, 'Select folder for comparison plots',
            save_dialog_directory(recordings_directory()))
        if not folder:
            return
        destination = Path(folder)
        try:
            for suffix, plot in zip(('stimulus','signal','difference'), self.plots):
                if plot.isVisible():
                    filename = destination / f'{self._export_stem()}_{suffix}.png'
                    if filename.exists():
                        raise FileExistsError(f'Graph already exists: {filename.name}')
                    ImageExporter(plot.getPlotItem()).export(str(filename))
        except (OSError, RuntimeError, ValueError) as exc:
            themed_message_box(self.window, 'Cannot export comparison graphs', str(exc)).exec()
