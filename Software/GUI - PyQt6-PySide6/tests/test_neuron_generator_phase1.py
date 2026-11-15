"""Run with: QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import csv
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch, Mock

import numpy as np
from PySide6.QtWidgets import QApplication, QWidget, QCheckBox, QLabel, QLineEdit, QComboBox, QStackedWidget, QVBoxLayout, QMainWindow
import pyqtgraph as pg
from spikeling_gui.features.neuron_generator import page as generator
from spikeling_gui.features.neuron_interface import page as interface
from spikeling_gui.features.emulator import controls as emulator
from spikeling_gui.neuron_csv import NEURON_COLUMNS, read_neuron_csv
from spikeling_gui.neuron_presets import IzhikevichNeurons

APP = QApplication.instance() or QApplication([])


class Phase1Tests(unittest.TestCase):
    def setUp(self):
        self.host = QWidget()
        ui = self.host.ui = SimpleNamespace()
        ui.mainbody_stackedWidget = QStackedWidget(self.host)
        ui.page_NeuronGenerator = QWidget()
        ui.mainbody_stackedWidget.addWidget(ui.page_NeuronGenerator)
        layout = QVBoxLayout(ui.page_NeuronGenerator)
        ui.NeuronGenerator_Oscilloscope_widget = pg.PlotWidget()
        layout.addWidget(ui.NeuronGenerator_Oscilloscope_widget)
        for trace in ("Vm", "stimulus"):
            checkbox = QCheckBox(self.host)
            checkbox.setChecked(True)
            setattr(ui, f"NeuronGenerator_subframe1_Oscilloscope_widget_{trace}_checkbox", checkbox)
        for name, value in zip(("a_value", "b_value", "c_value", "d_value", "StimInt_value"), (.02, .2, -65, 2, 15)):
            setattr(ui, name, QLineEdit(str(value), self.host))
        ui.NeuronGenerator_protocol_combo = QComboBox(self.host)
        ui.NeuronGenerator_protocol_combo.addItems(("Step", "Ramp", "Paired", "Rebound"))
        ui.NeuronGenerator_reference_check = QCheckBox(self.host)
        ui.NeuronGenerator_metrics_label = QLabel(self.host)
        ui.LoadNeuron_comboBox = QComboBox(self.host)
        ui.LoadNeuron_comboBox.addItems(("Select a preset", "Tonic Spiking"))
        ui.ImportNeuron = []
        ui.Spikeling_NeuronModeComboBox = QComboBox(self.host)
        self.temp = TemporaryDirectory()
        self.path = Path(self.temp.name) / "neuron.csv"

    def tearDown(self):
        self.host.close()
        self.host.deleteLater()
        APP.processEvents()
        self.temp.cleanup()

    def save(self):
        with patch.object(generator.QFileDialog, "getSaveFileName", return_value=(str(self.path), "")):
            generator.NeuronGenerator.SaveNeuron(self.host)

    def test_round_trip_both_importers_and_legacy_headers(self):
        self.host.neuron_generator_advanced_parameters = (25, .001, .025, -30, .985, 40, .995)
        self.save()
        expected = (.02, .2, -65, 2, 25, .001, .025, -30, .985, 40, .995)
        self.assertEqual(read_neuron_csv(self.path), expected)
        with self.path.open(newline="") as f:
            self.assertEqual(next(csv.reader(f)), list(NEURON_COLUMNS))
        for legacy in (False, True):
            if legacy:
                text = self.path.read_text()
                for canonical, old in zip(NEURON_COLUMNS[4:], ("PhotoGain( %)", "PhotoDecay(1 / ms)", "PhotoRecovery(1 / ms)", "Syn1 Gain( %)", "Syn1 Decay(1 / ms)", "Syn2 Gain( %)", "Syn2 Decay(1 / ms)")):
                    text = text.replace(canonical, old)
                self.path.write_text(text)
            with patch.object(interface.QFileDialog, "getOpenFileName", return_value=(str(self.path), "")):
                interface.Spikeling.BrowseNeuron(self.host)
            self.assertEqual(tuple(self.host.ui.ImportNeuron[-1]), expected)
            for channel in (0, 1, 2):
                selector = QComboBox(self.host)
                controller = SimpleNamespace(host=self.host, neuron_selector=lambda c: selector)
                with patch.object(emulator.QFileDialog, "getOpenFileName", return_value=(str(self.path), "")):
                    emulator.EmulatorControls.browse_neuron(controller, channel)
                self.assertEqual(selector.currentData(), expected)

    def test_presets_and_stimulus_boundaries(self):
        for preset in IzhikevichNeurons:
            for current in (-1000, -15.5, 0, 15, 1000):
                t, v, stim, spikes = generator._simulate(tuple(preset[:4]) + (current,), preset[4])
                self.assertEqual(len(t), 2501)
                self.assertTrue(np.isfinite(v).all())
                self.assertEqual(stim[499], 0)
                self.assertEqual(stim[500], current)
                self.assertEqual(stim[1999], current)
                self.assertEqual(stim[2000], 0)

    def test_plot_lifecycle_resize_and_current_range(self):
        self.host.ui.mainbody_stackedWidget.resize(700, 500)
        self.host.ui.mainbody_stackedWidget.show()
        generator.ShowPage(self.host)
        APP.processEvents()
        graph = self.host.ui.NeuronGenerator_Oscilloscope_widget
        initial_items = len(graph.scene().items())
        objects = (self.host.StimPlot, self.host.StimCurve, self.host.NeuronCurve)
        for value in (-1000, 0, 1000, 15.5):
            generator.ShowPage(self.host)
            self.host.ui.StimInt_value.setText(str(value))
            generator.NeuronGenerator.DrawNeuron(self.host)
            APP.processEvents()
            self.assertEqual(objects, (self.host.StimPlot, self.host.StimCurve, self.host.NeuronCurve))
            low, high = self.host.StimPlot.viewRange()[1]
            self.assertLess(low, min(0, value))
            self.assertGreater(high, max(0, value))
            self.assertEqual(len(graph.listDataItems()), 2)
            self.assertEqual(len(self.host.StimPlot.addedItems), 1)
            self.assertEqual(len(graph.scene().items()), initial_items)
        self.host.ui.mainbody_stackedWidget.resize(900, 600)
        APP.processEvents()
        self.assertEqual(self.host.StimPlot.geometry(), graph.getViewBox().sceneBoundingRect())
        self.assertTrue(graph.getAxis("right").isVisible())
        self.assertEqual(len(self.host.NeuronCurve.getData()[0]), 2501)

    def test_invalid_inputs_leave_trace_and_file_unchanged(self):
        generator.NeuronGenerator.DrawNeuron(self.host)
        old = self.host.NeuronCurve.getData()[1].copy()
        self.path.write_text("existing file")
        for field in ("a_value", "b_value", "c_value", "d_value", "StimInt_value"):
            widget = getattr(self.host.ui, field)
            previous = widget.text()
            for value in ("", "abc", "nan", "inf", "1e999", "1000000"):
                widget.setText(value)
                with patch.object(generator, "show_popup") as popup, patch.object(generator.QFileDialog, "getSaveFileName") as dialog:
                    generator.NeuronGenerator.DrawNeuron(self.host)
                    generator.NeuronGenerator.SaveNeuron(self.host)
                    self.assertEqual(popup.call_count, 2)
                    dialog.assert_not_called()
                np.testing.assert_array_equal(self.host.NeuronCurve.getData()[1], old)
            widget.setText(previous)
        for advanced in ((0, float("nan"), .025, 0, .995, 0, .995), (101, .001, .025, 0, .995, 0, .995), (0, -.1, .025, 0, .995, 0, .995), (0,)):
            self.host.neuron_generator_advanced_parameters = advanced
            with patch.object(generator, "show_popup") as popup:
                generator.NeuronGenerator.DrawNeuron(self.host)
                generator.NeuronGenerator.SaveNeuron(self.host)
                self.assertEqual(popup.call_count, 2)
        self.assertEqual(self.path.read_text(), "existing file")

    def test_cancel_and_file_failures(self):
        with patch.object(generator.QFileDialog, "getSaveFileName", return_value=("", "")):
            generator.NeuronGenerator.SaveNeuron(self.host)
        self.assertFalse(self.path.exists())
        self.path = Path(self.temp.name) / "missing" / "neuron.csv"
        with patch.object(generator, "show_popup") as popup:
            self.save()
            popup.assert_called_once()
        for path in ("", str(self.path)):
            with patch.object(interface.QFileDialog, "getOpenFileName", return_value=(path, "")), patch.object(interface, "show_popup") as popup:
                interface.Spikeling.BrowseNeuron(self.host)
                self.assertEqual(popup.call_count, bool(path))
        self.assertEqual(self.host.ui.ImportNeuron, [])

    def test_malformed_csv(self):
        cases = ["", ",".join(NEURON_COLUMNS), ",".join(NEURON_COLUMNS) + "\n1,2", ",".join(NEURON_COLUMNS) + "\n" + ",".join(["nan"] * 11)]
        for text in cases:
            self.path.write_text(text)
            with self.assertRaises(ValueError):
                read_neuron_csv(self.path)

    def test_apply_imported_parameters(self):
        expected = (.02, .2, -65, 2, 25, .001, .025, -30, .985, 40, .995)
        self.host.ui.ImportNeuron = [list(expected)]
        selector = self.host.ui.Spikeling_NeuronModeComboBox
        selector.addItems([str(i) for i in range(22)])
        selector.setCurrentIndex(21)
        with patch.object(interface, "serial_port") as port:
            port.is_open = True
            interface.Spikeling.SelectNeuronMode(self.host)
            commands = [call.args[0] for call in port.write.call_args_list]
            self.assertIn("SD11 985.0\n", commands)
            self.assertIn("SD21 995.0\n", commands)
            self.assertIn("PD1 0.001\n", commands)
        limits = ((-100, 100), (10, 125), (1, 100), (-100, 100), (975, 1000), (-100, 100), (975, 1000))
        bindings = {}
        for key, (low, high) in zip(emulator.PRESET_SLIDERS, limits):
            bindings[key] = Mock(slider=Mock(minimum=Mock(return_value=low), maximum=Mock(return_value=high)))
        controller = SimpleNamespace(ui=self.host.ui, neuron_selector=lambda c: Mock(currentData=Mock(return_value=expected)), bindings=bindings, neuron_revision=0)
        emulator.EmulatorControls.select_neuron(controller, 0)
        for key, position in zip(emulator.PRESET_SLIDERS, (25, 100, 25, -30, 985, 40, 995)):
            self.assertEqual(bindings[key].reconfigure.call_args.kwargs["default_position"], position)
        self.assertEqual(self.host.ui.Emulator_a, expected[0])

    def test_full_designer_ui_smoke(self):
        from spikeling_gui.ui.generated.UI_Spikeling import Ui_Spikeling
        window = QMainWindow()
        window.ui = Ui_Spikeling()
        window.ui.setupUi(window)
        try:
            window.show()
            generator.ShowPage(window)
            APP.processEvents()
            generator.NeuronGenerator.DrawNeuron(window)
            APP.processEvents()
            graph = window.ui.NeuronGenerator_Oscilloscope_widget
            self.assertTrue(graph.isVisible())
            vm = window.ui.NeuronGenerator_subframe1_Oscilloscope_widget_Vm_checkbox
            stim = window.ui.NeuronGenerator_subframe1_Oscilloscope_widget_stimulus_checkbox
            self.assertTrue(vm.isEnabled() and stim.isEnabled())
            vm.click()
            self.assertFalse(window.NeuronCurve.isVisible())
            self.assertTrue(window.StimCurve.isVisible())
            stim.click()
            generator.NeuronGenerator.DrawNeuron(window)
            self.assertFalse(window.StimCurve.isVisible())
            vm.click()
            self.assertTrue(window.NeuronCurve.isVisible())
            self.assertEqual(window.StimPlot.geometry(), graph.getViewBox().sceneBoundingRect())
            self.assertEqual(len(window.NeuronCurve.getData()[0]), 2501)
        finally:
            window.close()
            window.deleteLater()
            APP.processEvents()

    def test_protocols_and_spike_measurements(self):
        parameters = (.02, .2, -65, 6, 15)
        ramp = generator._simulate(parameters, -70, generator._RAMP)
        paired = generator._simulate(parameters, -70, generator._PAIRED)
        rebound = generator._simulate(parameters, -70, generator._REBOUND)
        self.assertEqual(ramp.voltage[0], -70)
        self.assertEqual((ramp.current[500], ramp.current[1999], ramp.current[2000]), (0, 15, 0))
        self.assertEqual(np.count_nonzero(paired.current), 200)
        self.assertEqual((rebound.current[499], rebound.current[500], rebound.current[1500]), (0, -15, 0))
        step = generator._simulate(parameters, -70)
        np.testing.assert_array_equal(step.time[step.voltage == 30], step.spikes)
        count, rate, latency, _ = generator._measure(step, generator._STEP)
        self.assertGreater(count, 0)
        self.assertEqual(rate, 4 * count)
        self.assertGreater(latency, 0)

    def test_open_round_trip_and_compare_on_the_same_protocol(self):
        self.save()
        self.host.ui.a_value.setText("0.9")
        with patch.object(generator.QFileDialog, "getOpenFileName", return_value=(str(self.path), "")):
            generator.NeuronGenerator.OpenNeuron(self.host)
        self.assertEqual(float(self.host.ui.a_value.text()), .02)
        self.host.ui.NeuronGenerator_protocol_combo.setCurrentIndex(generator._PAIRED)
        generator.NeuronGenerator.DrawNeuron(self.host)
        checkbox = self.host.ui.NeuronGenerator_reference_check
        checkbox.click()
        self.assertTrue(self.host.NeuronReferenceCurve.isVisible())
        old = self.host.NeuronReferenceCurve.getData()[1].copy()
        self.host.ui.d_value.setText("8")
        generator.NeuronGenerator.DrawNeuron(self.host)
        np.testing.assert_array_equal(old, self.host.NeuronReferenceCurve.getData()[1])
        self.assertFalse(np.array_equal(old, self.host.NeuronCurve.getData()[1]))

    def test_only_one_navigation_connection(self):
        text = Path("spikeling_gui/navigation.py").read_text(encoding="utf-8")
        self.assertEqual(text.count("NeuronGeneratorMenu_pushButton.clicked.connect(lambda: Page_NeuronGenerator.ShowPage(self))"), 1)


if __name__ == "__main__":
    unittest.main()
