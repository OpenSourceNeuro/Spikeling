"""Shared embedded spike timing view for Sweeps and Compare."""

import csv

import numpy as np
from PySide6.QtCore import QObject

from spikeling_gui.appearance.theme_manager import theme_manager

from . import page
from .spike_timing import isi_edges, psth, timing_edges
from .sweep_view import number


class SpikeTimingView(QObject):
    def __init__(self, window):
        super().__init__(window.ui.DataAnalysis_timingPage)
        self.window = window
        self.groups = []
        self.tables = {}
        self.form = ui = page.bind_controls(window.ui, "Timing", (
            "contextLabel", "rasterPlot", "psthPlot", "histogramPlot", "sequencePlot",
            "binEdit", "isiBinEdit", "rateCombo", "exportButton", "summaryLabel",
        ))
        for plot, left, bottom in (
            (ui.rasterPlot, "Sweep", "Time from onset (ms)"),
            (ui.psthPlot, "Rate (Hz)", "Time from onset (ms)"),
            (ui.histogramPlot, "Intervals", "ISI (ms)"),
            (ui.sequencePlot, "ISI (ms)", "Interval number"),
        ):
            theme_manager.set_plot_background_role(plot, "panel_background")
            plot.setLabel("left", left)
            plot.setLabel("bottom", bottom)
            plot.showGrid(x=True, y=True, alpha=.25)
        ui.psthPlot.addLegend(offset=(6, 5))
        ui.rasterPlot.setXLink(ui.psthPlot)
        ui.binEdit.editingFinished.connect(self.draw)
        ui.isiBinEdit.editingFinished.connect(self.draw)
        ui.rateCombo.currentIndexChanged.connect(self.draw)
        ui.exportButton.clicked.connect(self.export)

    def load(self, groups, neuron, threshold, context):
        self.groups = groups
        self.neuron = neuron
        self.threshold = threshold
        self.form.contextLabel.setText(context)
        self.draw()

    def draw(self):
        ui = self.form
        self.tables.clear()
        ui.exportButton.setEnabled(False)
        for plot in (ui.rasterPlot, ui.psthPlot, ui.histogramPlot, ui.sequencePlot):
            plot.clear()
        try:
            edges = timing_edges(self.groups, number(ui.binEdit, "PSTH bin width", .001))
            intervals = isi_edges(self.groups, number(ui.isiBinEdit, "ISI bin width", .001))
        except ValueError as error:
            ui.summaryLabel.setText(str(error))
            return
        use_count = ui.rateCombo.currentIndex() == 1
        ui.psthPlot.setLabel("left", "Spike count" if use_count else "Rate (Hz)")
        raster, histogram, sequence = [], [], []
        status, ticks, total = [], [], 0
        roles = ("neuron_vm", "neuron_current")
        for (condition, rows), role in zip(self.groups, roles):
            count, exposure, contributors, rate = psth(rows, edges)
            ui.psthPlot.plotItem.legend.removeItem(condition)
            self.plot_steps(ui.psthPlot, edges, count if use_count else rate, role, condition)
            x = np.concatenate([row.events for row in rows])
            y = np.repeat(np.arange(total + 1, total + len(rows) + 1), [len(r.events) for r in rows])
            ticks.extend(
                (total + i, f"{condition} {i}" if i == 1 else str(i))
                for i in range(1, len(rows) + 1) if len(rows) <= 20 or i in (1, len(rows))
            )
            total += len(rows)
            theme_manager.themed_plot(ui.rasterPlot, x, y, role, symbol="t", symbol_size=6)
            active_isi = np.concatenate([row.intervals for row in rows])
            isi_count, _ = np.histogram(active_isi[:, 1], bins=intervals)
            self.plot_steps(ui.histogramPlot, intervals, isi_count, role)
            theme_manager.themed_plot(
                ui.sequencePlot, active_isi[:, 0], active_isi[:, 1], role, symbol="o", symbol_size=5,
            )
            support = contributors[contributors > 0]
            coverage = f"{min(support)}–{max(support)}" if len(support) else "0"
            status.append(f"{condition}: {len(rows)} sweeps, {count.sum()} spikes, {len(active_isi)} ISIs"
                          f" ({coverage} sweeps per observed bin)")
            for i in range(len(count)):
                histogram.append((condition, edges[i], edges[i+1], count[i], exposure[i],
                                  contributors[i], rate[i] if np.isfinite(rate[i]) else ""))
            for row in rows:
                prefix = (condition, row.label, row.recording_id, row.onset_ms, self.neuron, self.threshold)
                for event in row.events if len(row.events) else ("",):
                    raster.append((*prefix, event))
                sequence.extend((*prefix, int(n), duration) for n, duration in row.intervals)
        ui.rasterPlot.getAxis("left").setTicks([ticks])
        ui.rasterPlot.setYRange(.5, total + .5, padding=0)
        ui.psthPlot.setXRange(edges[0], edges[-1], padding=0)
        ui.summaryLabel.setText(" · ".join(status) + " · ISIs measured within the active step")
        prefix = ("Condition", "Sweep", "Recording ID", "Onset (ms)", "Neuron", "Threshold (mV)")
        self.tables = {
            "psth": (("Condition", "Bin start (ms)", "Bin end (ms)", "Spikes", "Observed sweep-time (ms)",
                      "Contributing sweeps", "Rate (Hz)"), histogram),
            "spikes": ((*prefix, "Spike time from onset (ms)"), raster),
            "isi": ((*prefix, "Interval number within observed segment", "ISI (ms)"), sequence),
        }
        ui.exportButton.setEnabled(True)
        theme_manager.style_traces()

    def plot_steps(self, plot, edges, values, role, name=None):
        x = np.repeat(edges, 2)[1:-1]
        y = np.repeat(values, 2)
        theme_manager.themed_plot(plot, x, y, role, connect="finite", name=name)

    def export(self):
        folder = page.choose_export_folder("Data", "Export spike timing")
        if folder is None:
            return
        try:
            for suffix, (header, rows) in self.tables.items():
                with (folder / f"Spikeling_timing_{suffix}.csv").open("w", newline="", encoding="utf-8") as file:
                    writer = csv.writer(file)
                    writer.writerow(header)
                    writer.writerows(rows)
        except OSError as error:
            page.show_error(self.window.ui, "Cannot export spike timing", error)
