"""Geometry and Scope regressions for the extracellular teaching module."""
from copy import deepcopy
import os
from unittest import TestCase
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QApplication

from spikeling_gui.appearance.theme_manager import EXTRACELLULAR_CHANNEL_KEYS, theme_manager
from spikeling_gui.features.extracellular.scope import (
    ExtraCellularGraph,
    TETRODE_CONTACT_KEYS,
    TETRODE_NEURON_KEYS,
    Y_MAX_UV,
    Y_MIN_UV,
)
from spikeling_gui.features.extracellular.tetrode_window import SCENE_UNITS_PER_UM
from spikeling_gui.main_window import MainWindow


APP = QApplication.instance() or QApplication([])
POSITION_TOLERANCE_UM = 1e-6


class ExtracellularGeometryTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.window = MainWindow()
        cls.graph = cls.window.extracellular_graph
        cls.tetrode = cls.window.tetrode_window

    @classmethod
    def tearDownClass(cls):
        cls.tetrode.close()
        cls.window.close()

    def setUp(self):
        self.tetrode.reset_geometry()
        self.tetrode.ui.Tetrode_Parameters_View_GridSize_doubleSpinBox.setValue(1)

    def assert_scene_agrees(self):
        payload = self.tetrode.get_geometry_payload()
        objects = [*payload["neurons"].values(), payload["tetrode"]["center_um"]]
        for (item, x, y), coordinates in zip(self.tetrode._position_controls, objects):
            self.assertAlmostEqual(item.x() / SCENE_UNITS_PER_UM, x.value())
            self.assertAlmostEqual(item.y() / SCENE_UNITS_PER_UM, y.value())
            self.assertAlmostEqual(item.depth_z / SCENE_UNITS_PER_UM, coordinates["z_um"])
            self.assertEqual(x.value(), coordinates["x_um"])
            self.assertEqual(y.value(), coordinates["y_um"])
        expected = [[payload["distance_matrix_um"][key][contact] for contact in TETRODE_CONTACT_KEYS]
                    for key in TETRODE_NEURON_KEYS]
        np.testing.assert_allclose(self.graph.distance_matrix_um, expected, rtol=0, atol=POSITION_TOLERANCE_UM)

    def test_snap_updates_scene_controls_and_payload_once(self):
        self.tetrode.ui.Tetrode_Parameters_View_GridSize_doubleSpinBox.setValue(2.5)
        for (_, x, y), (a, b) in zip(self.tetrode._position_controls, [(39, -10.9), (-6.9, 0.4), (0, -0.1), (-31, 18.2)]):
            x.setValue(a)
            y.setValue(b)
        emissions = []
        self.tetrode.geometryChanged.connect(emissions.append)
        try:
            self.tetrode.ui.Tetrode_Parameters_View_SnaToGrid_pushButton.click()
        finally:
            self.tetrode.geometryChanged.disconnect(emissions.append)
        self.assertEqual(len(emissions), 1)
        self.assertEqual([(x.value(), y.value()) for _, x, y in self.tetrode._position_controls],
                         [(40, -10), (-7.5, 0), (0, 0), (-30, 17.5)])
        self.assert_scene_agrees()

    def test_drag_path_quantises_to_control_resolution_and_stops_at_limits(self):
        for item, x, y in self.tetrode._position_controls:
            item.setPos(401.7, -258.2)
            self.assertEqual((x.value(), y.value()), (40.2, -25.8))
            self.assertIn("X=40.2 µm", item.toolTip())
            item.setPos(1e5, -1e5)
            self.assertEqual((x.value(), y.value()), (x.maximum(), y.minimum()))
        self.assert_scene_agrees()
        self.tetrode.reset_geometry()
        self.assert_scene_agrees()

    def test_rotated_contacts_agree_with_scene_and_coordinate_only_payload(self):
        initial = self.graph.distance_matrix_um.copy()
        ui = self.tetrode.ui
        ui.Tetrode_Parameters_Electrode_x_doubleSpinBox.setValue(13.2)
        ui.Tetrode_Parameters_Electrode_y_doubleSpinBox.setValue(-7.4)
        ui.Tetrode_Parameters_Electrode_Rotx_spinBox.setValue(25)
        ui.Tetrode_Parameters_Electrode_Roty_spinBox.setValue(-40)
        ui.Tetrode_Parameters_Electrode_Rotz_spinBox.setValue(70)
        self.assertFalse(np.array_equal(initial, self.graph.distance_matrix_um))
        self.assert_scene_agrees()
        payload = self.tetrode.get_geometry_payload()
        contacts = payload["tetrode"]["contacts_um"]
        for point, contact in zip(self.tetrode.tetrode_item.site_positions_scene(), contacts):
            self.assertAlmostEqual(point.x() / SCENE_UNITS_PER_UM, contact["x_um"])
            self.assertAlmostEqual(point.y() / SCENE_UNITS_PER_UM, contact["y_um"])
        self.assertEqual([contact["name"] for contact in contacts], list(TETRODE_CONTACT_KEYS))
        expected = self.graph.distance_matrix_um.copy()
        del payload["distance_matrix_um"]
        contacts.reverse()
        self.assertTrue(self.graph.apply_tetrode_geometry(payload))
        np.testing.assert_allclose(self.graph.distance_matrix_um, expected, rtol=0, atol=POSITION_TOLERANCE_UM)

    def test_bad_geometry_does_not_replace_valid_values(self):
        valid = self.tetrode.get_geometry_payload()
        before = self.graph.distance_matrix_um.copy()
        accepted_payload = self.graph.tetrode_geometry
        for value in (None, float("nan"), float("inf"), -1, 12):
            invalid = deepcopy(valid)
            invalid["distance_matrix_um"]["main"]["E4"] = value
            self.assertFalse(self.graph.apply_tetrode_geometry(invalid))
        invalid = deepcopy(valid)
        del invalid["distance_matrix_um"]["main"]["E4"]
        self.assertFalse(self.graph.apply_tetrode_geometry(invalid))
        invalid = deepcopy(valid)
        invalid["tetrode"]["contacts_um"][3]["name"] = "E3"
        self.assertFalse(self.graph.apply_tetrode_geometry(invalid))
        invalid = deepcopy(valid)
        del invalid["neurons"]["aux1"]["z_um"]
        self.assertFalse(self.graph.apply_tetrode_geometry(invalid))
        self.assertFalse(self.graph.apply_tetrode_geometry({"tetrode": []}))
        np.testing.assert_array_equal(self.graph.distance_matrix_um, before)
        self.assertIs(self.graph.tetrode_geometry, accepted_payload)

    def test_zero_distance_is_reported_and_projection_retains_safety_floor(self):
        graph = self.graph
        graph.set_geometry_from_positions(np.zeros((4, 3)), np.zeros((3, 3)))
        self.assertTrue((graph.distance_matrix_um == 0).all())
        gains = graph._compute_projection_matrix({"spatial_falloff": 1.0})
        self.assertTrue(np.isfinite(gains).all())
        np.testing.assert_array_equal(gains, np.repeat(gains[:, :1], 4, axis=1))

    def test_scope_reconnect_and_shared_axes(self):
        self.window.extracellular_page.ShowPage()
        self.window.show()
        ui = self.window.ui
        graph = self.graph
        button = ui.ExtraCellular_AutoRange_pushButton
        self.assertFalse(button.isEnabled())
        try:
            for _ in range(2):
                graph.connect()
                graph._rx_timer.stop()
                APP.processEvents()
                self.assertTrue(button.isVisible() and button.isEnabled())
                self.assertFalse(ui.ExtraCellular_Oscilloscope_widget.isAncestorOf(button))
                views = [plot.getViewBox() for plot in graph.channel_plot_widgets]
                time_view = graph.time_axis_widget.getViewBox()
                self.assertLessEqual(max(v.height() for v in views) - min(v.height() for v in views), 1)
                self.assertTrue(all(v.sceneBoundingRect().left() == time_view.sceneBoundingRect().left() for v in views))

                checks = graph._channel_checkboxes()
                checks[-1].setChecked(False)
                self.assertTrue(graph.time_axis_widget.isVisible())
                graph.Time_buffer.append(1)
                graph.Extra_buffers[-1].append(250)
                button.click()
                ranges = [tuple(view.viewRange()[1]) for view in views]
                self.assertEqual(len(set(ranges)), 1)
                self.assertGreater(ranges[0][1], 250)
                button.click()
                self.assertTrue(all(v.viewRange()[1] == [Y_MIN_UV, Y_MAX_UV] for v in views))
                for box in checks:
                    box.setChecked(False)
                self.assertTrue(graph.time_axis_widget.isHidden())
                ui.Extracellular_Tetrode_Vm_checkBox.setChecked(True)
                ui.Extracellular_Tetrode_Stimulus_checkBox.setChecked(True)
                self.assertTrue(graph.time_axis_widget.isVisible())
                self.assertEqual([p.getAxis("left").labelUnits for p, *_ in graph.source_plots], ["mV", "%"])
                graph.source_plots[0][0].setXRange(-300, -10, padding=0)
                self.assertTrue(all(v.viewRange()[0] == [-300, -10] for v in (*views, time_view)))

                for box in (*checks, ui.Extracellular_Tetrode_Vm_checkBox, ui.Extracellular_Tetrode_Stimulus_checkBox):
                    box.setChecked(box in checks)
                graph.disconnect()
                APP.processEvents()
                self.assertFalse(button.isEnabled())
        finally:
            graph.disconnect()

    def test_theme_refresh_updates_live_scope_and_geometry(self):
        graph = self.graph
        graph.connect()
        graph._rx_timer.stop()
        try:
            with patch.object(theme_manager, "_active", theme_manager._active.copy()), patch.object(
                theme_manager, "_pending", theme_manager._pending.copy()
            ), patch.object(theme_manager._settings, "setValue"):
                for mode in ("dark", "light"):
                    theme_manager.set_mode(mode)
                    theme_manager.apply_and_save()
                    self.tetrode.show()
                    APP.processEvents()
                    self.tetrode.close()
                    colors = [color.name() for color in self.tetrode.tetrode_item.contact_colors]
                    self.assertEqual(colors, [theme_manager.active_colour(key).lower() for key in EXTRACELLULAR_CHANNEL_KEYS])
                    threshold_ink = graph.channel_threshold_lines[0].pen.color().name()
                    self.assertEqual(threshold_ink, theme_manager.active_colour("text_muted").lower())
        finally:
            graph.disconnect()
            theme_manager.repaint()

    def test_scale_bar_tracks_zoom_and_grid_label_keeps_fractional_resolution(self):
        view = self.tetrode.ui.Tetrode_graphicsView
        control = self.tetrode.ui.Tetrode_Parameters_View_GridSize_doubleSpinBox
        control.setValue(2.5)
        self.assertIn("2.5 µm", self.tetrode.grid_scale_label.text())
        try:
            for zoom_factor in (1.0, 0.35, 22.0):
                view.scale(zoom_factor, zoom_factor)
                self.tetrode._update_scale_bar_overlay()
                bar = self.tetrode.scale_bar_overlay
                length_um = float(bar.label_text.removesuffix(" µm"))
                length_px = length_um * SCENE_UNITS_PER_UM * view.transform().m11()
                self.assertAlmostEqual(bar.bar_length_px, length_px, delta=0.5)
        finally:
            view.reset_zoom()
