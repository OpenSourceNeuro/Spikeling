"""Imaging processing tab controller; all visible widgets are in Qt Designer."""
from __future__ import annotations

from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QFileDialog
from pyqtgraph.exporters import ImageExporter

from spikeling_gui.appearance.dialogs import themed_message_box
from spikeling_gui.appearance.theme_manager import theme_manager
from spikeling_gui.paths import recordings_directory, save_dialog_directory
from .processing import ProcessingSettings, process_imaging_recording


class ImagingProcessingView(QObject):
    def __init__(self, page):
        super().__init__(page)
        self.page = page
        self.window = page.window
        self.ui = page.ui
        self.result = None
        ui = self.ui
        ui.ImagingAnalysis_processing_calculateButton.clicked.connect(self.calculate)
        ui.ImagingAnalysis_processing_exportButton.clicked.connect(self.export_csv)
        ui.ImagingAnalysis_processing_imageButton.clicked.connect(self.export_images)
        ui.ImagingAnalysis_processing_neuronCombo.currentIndexChanged.connect(self.draw)
        for name in ('rawCheck', 'storedCheck', 'baselineCheck'):
            getattr(ui, 'ImagingAnalysis_processing_' + name).toggled.connect(self.draw)
        for name in ('baselineMethodCombo','backgroundMethodCombo','filterMethodCombo'):
            control = getattr(ui, 'ImagingAnalysis_processing_' + name)
            control.currentIndexChanged.connect(self._method_changed)
        for name in ('percentileEdit','baselineStartEdit','baselineEndEdit','baselineWindowEdit',
                     'backgroundValueEdit','bleachWindowEdit','filterWindowEdit'):
            getattr(ui, 'ImagingAnalysis_processing_' + name).textEdited.connect(self.invalidate)
        ui.ImagingAnalysis_processing_bleachCheck.toggled.connect(self._method_changed)
        self.plots = (ui.ImagingAnalysis_processing_fluorescencePlot,
                      ui.ImagingAnalysis_processing_dffPlot)
        for plot in self.plots:
            theme_manager.set_plot_background_role(plot, 'panel_background')
            plot.showGrid(x=True,y=True,alpha=.22)
            plot.getAxis('left').setWidth(65)
            plot.setDownsampling(auto=True,mode='peak')
        self.plots[0].setXLink(self.plots[1])
        self._method_changed()
        self.reset()
        theme_manager.themeChanged.connect(self.refresh_theme)

    def _method_changed(self, *_):
        ui = self.ui
        kind = ui.ImagingAnalysis_processing_baselineMethodCombo.currentIndex()
        ui.ImagingAnalysis_processing_percentileEdit.setEnabled(kind in (0,1))
        ui.ImagingAnalysis_processing_baselineWindowEdit.setEnabled(kind == 1)
        for label in ('baselineStartEdit','baselineEndEdit'):
            getattr(ui,'ImagingAnalysis_processing_' + label).setEnabled(kind == 2)
        ui.ImagingAnalysis_processing_backgroundValueEdit.setEnabled(
            ui.ImagingAnalysis_processing_backgroundMethodCombo.currentIndex() == 2)
        ui.ImagingAnalysis_processing_bleachWindowEdit.setEnabled(
            ui.ImagingAnalysis_processing_bleachCheck.isChecked())
        ui.ImagingAnalysis_processing_filterWindowEdit.setEnabled(
            ui.ImagingAnalysis_processing_filterMethodCombo.currentIndex() != 0)
        self.invalidate()

    def reset(self):
        self.result = None
        self.page.processed_recording = None
        loaded = self.page.recording is not None
        self.ui.ImagingAnalysis_processing_calculateButton.setEnabled(loaded)
        self.ui.ImagingAnalysis_processing_neuronCombo.setEnabled(loaded)
        self.ui.ImagingAnalysis_processing_exportButton.setEnabled(False)
        self.ui.ImagingAnalysis_processing_imageButton.setEnabled(False)
        self.ui.ImagingAnalysis_processing_statusLabel.setText(
            'Load an imaging recording, select processing settings, then click Apply processing.'
        )
        self.ui.ImagingAnalysis_processing_qualityLabel.setText(
            'Quality metrics will appear after processing. Original camera frames remain unchanged.'
        )
        for plot in self.plots:
            plot.clear()
        transients = getattr(self.page, "transients_view", None)
        if transients is not None:
            transients.reset()
        inference = getattr(self.page, "inference_view", None)
        if inference is not None:
            inference.reset()
        compare = getattr(self.page, "compare_view", None)
        if compare is not None:
            compare.invalidate(force=True)

    def invalidate(self, *_):
        if self.result is not None:
            self.reset()
            self.ui.ImagingAnalysis_processing_statusLabel.setText(
                'Parameters changed. Click Apply processing to recalculate before exporting or aligning.'
            )
            align = getattr(self.page, 'align_view', None)
            if align is not None:
                align.reset()

    def _settings(self) -> ProcessingSettings:
        ui=self.ui
        def number(name):
            return float(getattr(ui,'ImagingAnalysis_processing_'+name).text().strip())
        return ProcessingSettings(
            baseline_method=('percentile','rolling','fixed')[ui.ImagingAnalysis_processing_baselineMethodCombo.currentIndex()],
            baseline_percentile=number('percentileEdit'),
            baseline_start_ms=number('baselineStartEdit'),
            baseline_end_ms=number('baselineEndEdit'),
            baseline_window_ms=number('baselineWindowEdit'),
            background_method=('none','metadata','manual')[ui.ImagingAnalysis_processing_backgroundMethodCombo.currentIndex()],
            background_au=number('backgroundValueEdit'),
            bleach_correct=ui.ImagingAnalysis_processing_bleachCheck.isChecked(),
            bleach_window_ms=number('bleachWindowEdit'),
            filter_method=('none','mean','savgol')[ui.ImagingAnalysis_processing_filterMethodCombo.currentIndex()],
            filter_window_ms=number('filterWindowEdit'),
        )

    def calculate(self, *_):
        rec=self.page.recording
        if rec is None:
            return
        try:
            processed=process_imaging_recording(rec,self._settings())
        except (ValueError, TypeError, KeyError, OverflowError) as exc:
            self.reset()
            self.ui.ImagingAnalysis_processing_statusLabel.setText('Processing unavailable: '+str(exc))
            align = getattr(self.page,'align_view',None)
            if align is not None:
                align.reset()
            return
        self.result=processed
        self.page.processed_recording=processed
        self.ui.ImagingAnalysis_processing_statusLabel.setText(
            f'Processed all 3 one-pixel channels · {rec.n_frames:,} recorded camera frames · '
            'model reference channels excluded from processing.'
            + (f' {len(processed.warnings)} processing notice(s).' if processed.warnings else '')
        )
        self.ui.ImagingAnalysis_processing_exportButton.setEnabled(True)
        self.ui.ImagingAnalysis_processing_imageButton.setEnabled(True)
        self.draw()
        align=getattr(self.page,'align_view',None)
        if align is not None:
            align.reset()
        transients = getattr(self.page, "transients_view", None)
        if transients is not None:
            transients.reset()
        inference = getattr(self.page, "inference_view", None)
        if inference is not None:
            inference.reset()
        compare = getattr(self.page, "compare_view", None)
        if compare is not None:
            compare.invalidate(force=True)

    def draw(self, *_):
        for plot in self.plots:
            plot.clear()
        data=self.result
        if data is None:
            return
        neuron=self.ui.ImagingAnalysis_processing_neuronCombo.currentIndex()
        rec=self.page.recording
        t=data.time_ms
        gaps=data.gaps_before
        def trace(plot,values,role,label):
            cuts=np.flatnonzero(gaps)
            x=np.insert(t,cuts,np.nan)
            y=np.insert(np.asarray(values,dtype=float),cuts,np.nan)
            theme_manager.themed_plot(plot,x,y,role,connect='finite')
        role=f'imaging_fluo{neuron+1}'
        fplot,dplot=self.plots
        fplot.setTitle('Fluorescence — raw, processed, empirical F₀',
                       color=theme_manager.active_colour('text_primary'),size='9pt')
        dplot.setTitle('ΔF/F₀ — empirical processing and simulator normalisation',
                       color=theme_manager.active_colour('text_primary'),size='9pt')
        if self.ui.ImagingAnalysis_processing_rawCheck.isChecked():
            trace(fplot,rec.frame_fluorescence_au[:,neuron],'analysis_loop','Raw fluorescence')
        trace(fplot,data.fluorescence_au[:,neuron],role,'Processed fluorescence')
        if self.ui.ImagingAnalysis_processing_baselineCheck.isChecked():
            trace(fplot,data.baseline_au[:,neuron],'imaging_stimulus','Empirical F0')
        if self.ui.ImagingAnalysis_processing_storedCheck.isChecked():
            trace(dplot,rec.recorded_dff_percent[:,neuron],'analysis_loop','Recorded ΔF/F0')
        trace(dplot,data.dff_percent[:,neuron],role,'Processed ΔF/F0')
        for plot in self.plots:
            plot.setLabel('bottom','Frame time (ms)' if plot is dplot else '')
            plot.enableAutoRange(axis='y')
        m=data.metrics[neuron]
        def fmt(v,unit='',digits=3):
            return ('not estimable' if v is None or not np.isfinite(v)
                    else f'{v:.{digits}g}{unit}')
        self.ui.ImagingAnalysis_processing_qualityLabel.setText(
            f'Neuron {neuron+1} · valid frames {m["valid_frames"]:,} · '
            f'camera gap boundaries {m["frame_gap_boundaries"]} · '
            f'estimated missing frames {m["missing_frames_estimated"]} · '
            f'effective frame rate {fmt(m["effective_rate_hz"]," Hz")} · '
            f'empirical F₀ {fmt(m.get("median_f0_au")," a.u.")} · '
            f'noise proxy {fmt(m["noise_sd_au"]," a.u.")} · '
            f'SNR proxy {fmt(m["snr_proxy"])}'
        )
        self.ui.ImagingAnalysis_processing_qualityLabel.setToolTip(
            'Noise and SNR are approximate robust first-difference measures, not calibrated '
            'signal-detection metrics. Missing-frame count is an estimate from timestamps.'
        )
        theme_manager.style_traces()

    def refresh_theme(self, *_):
        if self.result is not None:
            self.draw()

    def _stem(self):
        return f'{self.page.recording.source.stem}_imaging_processed'

    def export_csv(self):
        if self.result is None:
            return
        path,_=QFileDialog.getSaveFileName(
            self.window,'Export processed imaging signals',
            str(recordings_directory()/(self._stem()+'.csv')),
            'CSV files (*.csv)',
        )
        if not path:
            return
        destination=Path(path)
        if destination.suffix.lower()!='.csv':
            destination=destination.with_suffix('.csv')
        source_paths=(self.page.recording.source,self.page.recording.frames_source,
                      self.page.recording.metadata_source)
        meta_dest=destination.with_name(destination.stem+'_processing.json')
        if destination.resolve() in {p.resolve() for p in source_paths} or meta_dest.resolve() in {p.resolve() for p in source_paths}:
            themed_message_box(self.window,'Cannot overwrite source recording',
                               'Choose a new export name. Original imaging recording files must remain unchanged.').exec()
            return
        data=self.result
        rec=self.page.recording
        cols={'FrameTime (ms)':data.time_ms,'Frame gap before':data.gaps_before.astype(int)}
        for i in range(3):
            ch=i+1
            cols[f'Neuron {ch} raw fluorescence (a.u.)']=rec.frame_fluorescence_au[:,i]
            cols[f'Neuron {ch} background corrected and bleach adjusted (a.u.)']=data.corrected_f_au[:,i]
            cols[f'Neuron {ch} processed fluorescence (a.u.)']=data.fluorescence_au[:,i]
            cols[f'Neuron {ch} empirical F0 (a.u.)']=data.baseline_au[:,i]
            cols[f'Neuron {ch} processed DF/F0 (%)']=data.dff_percent[:,i]
            cols[f'Neuron {ch} recorded model DF/F0 (%)']=rec.recorded_dff_percent[:,i]
            cols[f'Neuron {ch} bleaching envelope (a.u.)']=data.bleach_envelope_au[:,i]
            cols[f'Neuron {ch} bleaching correction factor']=data.bleach_factor[:,i]
        try:
            details={
                'schema':'Spikeling imaging processing v1',
                'processed_at_iso':datetime.now().astimezone().isoformat(timespec='seconds'),
                'input_files':{p.name:sha256(p.read_bytes()).hexdigest() for p in source_paths},
                'indicator':rec.metadata.get('indicator_name'),
                'acquisition_source':rec.metadata.get('source'),
                'camera_frame_times_used':True,
                'original_recording_unchanged':True,
                **data.parameters(),
                'metrics':list(data.metrics),
            }
            destination.parent.mkdir(parents=True,exist_ok=True)
            with TemporaryDirectory(dir=destination.parent) as temp:
                tmp=Path(temp)
                data_file=tmp/destination.name
                meta_file=tmp/meta_dest.name
                pd.DataFrame(cols).to_csv(data_file,index=False)
                meta_file.write_text(json.dumps(details,indent=2,allow_nan=False),encoding='utf-8')
                data_file.replace(destination)
                meta_file.replace(meta_dest)
        except (OSError,ValueError,TypeError) as exc:
            themed_message_box(self.window,'Cannot export processing results',str(exc)).exec()

    def export_images(self):
        if self.result is None:
            return
        folder=QFileDialog.getExistingDirectory(self.window,'Export imaging processing plots',
                                                 save_dialog_directory(recordings_directory()))
        if not folder:
            return
        try:
            for suffix,plot in zip(('fluorescence','dff'),self.plots):
                ImageExporter(plot.getPlotItem()).export(str(Path(folder)/f'{self._stem()}_{suffix}.png'))
        except (OSError,RuntimeError,ValueError) as exc:
            themed_message_box(self.window,'Cannot export processing graphs',str(exc)).exec()
