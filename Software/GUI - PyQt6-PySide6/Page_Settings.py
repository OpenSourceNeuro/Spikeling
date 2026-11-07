"""Controller for the Settings page saved in UI_Spikeling.ui.

Designer owns the controls and layouts; only the preview graph is inserted
here. Edits affect local previews until Apply. Revert and Restore defaults
never silently commit settings. Language changes take effect on restart.
"""
from functools import partial
import math
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QSignalBlocker, QTimer, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QApplication, QColorDialog, QDialog, QFileDialog, QLabel, QMessageBox,
    QPushButton, QVBoxLayout,
)
import pyqtgraph as pg

from app_preferences import (
    LANGUAGES, LANGUAGE_KEY, RECORDING_DIRECTORY_KEY,
    default_recording_directory, language_available, preference_store,
)
from theme_manager import (
    ROLES_BY_KEY, TRACE_WIDTH_MAX, TRACE_WIDTH_MIN, TRACE_WIDTH_STEP,
    mix, theme_manager,
)


class TracePreview:
    """Illustrative Vm/current examples, independent of board or simulation."""

    def __init__(self, host, manager):
        self.manager = manager
        self.widget = pg.GraphicsLayoutWidget(host)
        self.widget.setObjectName("Settings_TracePreview_graph")
        self.widget.setToolTip(QCoreApplication.translate("SettingsPage", "Illustrative appearance preview; not a live recording or model simulation."))
        layout = host.layout()
        if layout is None:
            layout = QVBoxLayout(host)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.widget)
        self.vm_plot = self.widget.addPlot(row=0, col=0)
        self.current_plot = self.widget.addPlot(row=1, col=0)
        self.current_plot.setXLink(self.vm_plot)
        self.vm_plot.hideAxis("bottom")
        self.vm_plot.setLabel("left", "Vm", units="mV")
        self.current_plot.setLabel("left", QCoreApplication.translate("SettingsPage", "Input current (a.u.)"))
        self.current_plot.setLabel("bottom", QCoreApplication.translate("SettingsPage", "Time"), units="ms")
        self.widget.ci.layout.setRowStretchFactor(0, 3)
        self.widget.ci.layout.setRowStretchFactor(1, 1)
        for plot in (self.vm_plot, self.current_plot):
            plot.setMenuEnabled(False)
            plot.setMouseEnabled(x=False, y=False)
            plot.hideButtons()
            plot.setXRange(0, 100, padding=0)
            plot.getAxis("left").setWidth(72)
        self.vm_plot.setYRange(-90, 40, padding=0)
        self.current_plot.setYRange(-0.15, 1.2, padding=0)
        times = [i / 10 for i in range(1001)]
        vm = [-70 + 105 * math.exp(-((t - 36) / 1.5) ** 2)
              - 10 * math.exp(-((t - 41) / 3.5) ** 2) for t in times]
        current = [1.0 if 20 <= t < 80 else 0.0 for t in times]
        self._sample_data = times, vm, current
        self.vm_curve = self.vm_plot.plot(times, vm, antialias=True)
        self.current_curve = self.current_plot.plot(times, current, antialias=True)
        self.refresh()

    def refresh(self):
        """Use pending colours, width and grid without a global repaint."""
        colour = self.manager.colour
        self.widget.setBackground(colour("window_background"))
        foreground = colour("text_primary")
        for plot in (self.vm_plot, self.current_plot):
            plot.showGrid(x=self.manager.show_grid, y=self.manager.show_grid, alpha=0.2)
            for side in ("left", "bottom"):
                axis = plot.getAxis(side)
                axis.setPen(pg.mkPen(foreground))
                axis.setTextPen(pg.mkPen(foreground))
                axis.setLabel(axis.labelText, units=axis.labelUnits, color=foreground)
        self.vm_curve.setPen(pg.mkPen(colour("neuron_vm"), width=self.manager.trace_width))
        self.current_curve.setPen(pg.mkPen(colour("neuron_current"), width=self.manager.trace_width))
        self.widget.viewport().update()

    def redraw_after_show(self):
        """Refresh curve geometry once the previously hidden page is laid out."""
        times, vm, current = self._sample_data
        self.vm_curve.setData(times, vm)
        self.current_curve.setData(times, current)
        self.refresh()


class SettingsPage:
    """Connect Designer controls to staged preferences exactly once."""

    def __init__(self, parent, manager=theme_manager, preferences=None):
        if getattr(parent, "_settings_controller", None) is not None:
            raise RuntimeError("SettingsPage must be constructed only once per window")
        self.parent, self.ui, self.manager = parent, parent.ui, manager
        self.page = self.ui.page_Settings
        self.preferences = preferences if preferences is not None else preference_store()
        self._folder_dialog = self._colour_dialog = self._message = None
        self._swatches = {}
        self._saved_language = str(self.preferences.value(LANGUAGE_KEY, "en"))
        self._pending_language = self._saved_language
        self._saved_folder = str(default_recording_directory(self.preferences))
        self._pending_folder = self._saved_folder
        self._launch_language = getattr(QApplication.instance(), "_spikeling_language", "en")
        for button in self.page.findChildren(QPushButton):
            key = button.property("themeRole")
            if not key:
                continue
            if key not in ROLES_BY_KEY or key in self._swatches:
                raise ValueError(f"Invalid or duplicate Settings themeRole: {key}")
            stem = button.objectName().removesuffix("_pushButton")
            label = self.page.findChild(QLabel, stem + "_Value_label")
            if label is None:
                raise ValueError(f"Missing colour value label for {button.objectName()}")
            self._swatches[key] = (button, label)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(partial(self._pick_colour, key))
        self.ui.Settings_Trace_lineEdit.setReadOnly(True)
        self.ui.Settings_Trace_lineEdit.setMaximumWidth(80)
        self.ui.Settings_RecordingFolder_lineEdit.setReadOnly(True)
        slider = self.ui.Settings_Trace_slider
        slider.setRange(round(TRACE_WIDTH_MIN / TRACE_WIDTH_STEP),
                        round(TRACE_WIDTH_MAX / TRACE_WIDTH_STEP))
        slider.setSingleStep(1)
        slider.setPageStep(1)
        slider.valueChanged.connect(lambda value: self.manager.set_trace_width(value * TRACE_WIDTH_STEP))
        self.ui.Settings_ShowGrid_checkBox.toggled.connect(self.manager.set_show_grid)
        self.ui.Settings_Dark_pushButton.clicked.connect(lambda: self.manager.set_mode("dark"))
        self.ui.Settings_Light_pushButton.clicked.connect(lambda: self.manager.set_mode("light"))
        self.ui.Settings_Apply_pushButton.clicked.connect(self.ApplyTheme)
        self.ui.Settings_Revert_pushButton.clicked.connect(self.RevertTheme)
        self.ui.Settings_Defaults_pushButton.clicked.connect(self.ResetTheme)
        self.ui.Settings_Defaults_pushButton.setToolTip(QCoreApplication.translate(
            "SettingsPage", "Restore default appearance and English. The recording folder is retained. Changes wait for Apply."))
        self.ui.Settings_RecordingFolderBrowse_pushButton.clicked.connect(self._browse_folder)
        self._configure_languages()
        self.ui.Settings_Language_comboBox.currentIndexChanged.connect(self._language_changed)
        self._preview = TracePreview(self.ui.Settings_TracePreview_widget, manager)
        self.manager.pendingChanged.connect(self._on_pending_changed)
        self.manager.themeChanged.connect(self._on_theme_applied)
        parent._settings_controller = self
        self._sync_controls()

    def ShowPage(self):
        self.ui.mainbody_stackedWidget.setCurrentWidget(self.page)
        self._sync_controls()
        QTimer.singleShot(0, self._preview.redraw_after_show)

    def _configure_languages(self):
        """Preserve flag icons and disable languages without installed catalogues."""
        combo = self.ui.Settings_Language_comboBox
        for index, (code, name) in enumerate(LANGUAGES):
            if index >= combo.count():
                combo.addItem(name)
            combo.setItemData(index, code)
            available = language_available(code)
            combo.model().item(index).setEnabled(available)
            combo.setItemData(index, QCoreApplication.translate("SettingsPage", "Translation catalogue not installed.") if not available else "",
                              Qt.ItemDataRole.ToolTipRole)
        combo.setToolTip(QCoreApplication.translate("SettingsPage", "Language changes take effect after restarting. Languages without an installed translation are unavailable."))

    def _language_changed(self, index):
        code = self.ui.Settings_Language_comboBox.itemData(index)
        if code and language_available(code):
            self._pending_language = code
        self._sync_status()

    def _on_pending_changed(self, *_):
        self._sync_controls()

    def _on_theme_applied(self, *_):
        self._sync_controls()
        for dialog in (self._folder_dialog, self._colour_dialog, self._message):
            if dialog is not None:
                dialog.setStyleSheet(self.manager.stylesheet())

    def _sync_controls(self):
        """Refresh the existing controls under signal blockers."""
        for key, (button, label) in self._swatches.items():
            colour = self.manager.colour(key)
            border = mix(self.manager.active_colour("panel_background"),
                         self.manager.active_colour("text_primary"), 0.55)
            button.setStyleSheet(
                f"QPushButton {{background-color: {colour}; border: 1px solid {border}; border-radius: 0px;}}"
                f"QPushButton:hover {{border: 2px solid {self.manager.active_colour('text_primary')};}}"
                f"QPushButton:pressed {{border: 2px solid {self.manager.active_colour('neuron_stimulus')};}}")
            label.setText(colour.upper())
            label.setToolTip(QCoreApplication.translate("SettingsPage", "Hexadecimal colour: {colour}").format(colour=colour.upper()))
        buttons = self.ui.Settings_Theme_buttonGroup
        # A custom palette must not falsely advertise either built-in preset.
        buttons.setExclusive(False)
        for mode, button in (("dark", self.ui.Settings_Dark_pushButton),
                             ("light", self.ui.Settings_Light_pushButton)):
            with QSignalBlocker(button):
                button.setChecked(self.manager.mode == mode)
        buttons.setExclusive(True)
        with QSignalBlocker(self.ui.Settings_Trace_slider):
            self.ui.Settings_Trace_slider.setValue(round(self.manager.trace_width / TRACE_WIDTH_STEP))
        self.ui.Settings_Trace_lineEdit.setText(f"{self.manager.trace_width:g} px")
        with QSignalBlocker(self.ui.Settings_ShowGrid_checkBox):
            self.ui.Settings_ShowGrid_checkBox.setChecked(self.manager.show_grid)
        combo = self.ui.Settings_Language_comboBox
        with QSignalBlocker(combo):
            index = combo.findData(self._pending_language)
            combo.setCurrentIndex(index if index >= 0 else 0)
        self.ui.Settings_RecordingFolder_lineEdit.setText(self._pending_folder)
        self._style_width_slider()
        self._preview.refresh()
        self._sync_status()

    def _style_width_slider(self):
        colour = self.manager.active_colour
        border = mix(colour('panel_background'), colour('text_primary'), 0.4)
        for editor in (self.ui.Settings_RecordingFolder_lineEdit,
                       self.ui.Settings_Trace_lineEdit, self.ui.Settings_Language_comboBox):
            editor.setStyleSheet(f"""
                QLineEdit, QComboBox {{background: {colour('panel_background')}; color: {colour('text_primary')};
                    border: 1px solid {border}; border-radius: 5px; padding: 4px 8px;}}
                QComboBox QAbstractItemView {{background: {colour('panel_background')}; color: {colour('text_primary')};
                    selection-background-color: {colour('neuron_stimulus')};}}
            """)
        self.ui.Settings_RecordingFolderBrowse_pushButton.setStyleSheet(f"""
            QPushButton {{background: {colour('surface')}; color: {colour('text_primary')};
                border: 1px solid {border}; border-radius: 5px; padding: 5px 12px;}}
            QPushButton:hover {{border-color: {colour('neuron_stimulus')};}}
            QPushButton:pressed {{background: {colour('window_background')};}}
        """)
        self.ui.Settings_Trace_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{height: 6px; background: {colour('text_muted')}; border-radius: 3px;}}
            QSlider::sub-page:horizontal {{background: {colour('neuron_stimulus')}; border-radius: 3px;}}
            QSlider::handle:horizontal {{width: 16px; margin: -5px 0; background: {colour('text_primary')};
                border: 1px solid {colour('neuron_stimulus')}; border-radius: 8px;}}
        """)

    @property
    def is_dirty(self):
        return (self.manager.is_dirty or self._pending_language != self._saved_language
                or self._pending_folder != self._saved_folder)

    def _sync_status(self):
        self.ui.Settings_Apply_pushButton.setEnabled(self.is_dirty)
        self.ui.Settings_Revert_pushButton.setEnabled(self.is_dirty)
        if self.is_dirty:
            text = QCoreApplication.translate("SettingsPage", "Unapplied changes")
        elif self._saved_language != self._launch_language:
            text = QCoreApplication.translate("SettingsPage", "Settings saved. Restart to change language.")
        else:
            text = QCoreApplication.translate("SettingsPage", "Settings applied and saved")
        self.ui.Settings_Status_label.setText(text)

    def _pick_colour(self, key, checked=False):
        """A themed asynchronous picker leaves acquisition event processing alive."""
        if self._colour_dialog is not None:
            self._colour_dialog.raise_()
            return
        button = self._swatches[key][0]
        label = button.parentWidget().findChild(QLabel, button.objectName().replace("_pushButton", "_label"))
        title = label.text() if label is not None else key
        dialog = QColorDialog(QColor(self.manager.colour(key)), self.parent)
        dialog.setOption(QColorDialog.ColorDialogOption.DontUseNativeDialog, True)
        dialog.setWindowTitle(QCoreApplication.translate("SettingsPage", "Select colour: {signal}").format(signal=title))
        dialog.setStyleSheet(self.manager.stylesheet())
        dialog.colorSelected.connect(lambda colour: self.manager.set_colour(key, colour.name()))
        dialog.finished.connect(self._colour_dialog_finished)
        self._colour_dialog = dialog
        dialog.open()

    def _colour_dialog_finished(self, *_):
        dialog, self._colour_dialog = self._colour_dialog, None
        if dialog is not None:
            dialog.deleteLater()

    def _browse_folder(self, checked=False):
        if self._folder_dialog is None:
            dialog = QFileDialog(self.parent)
            dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
            dialog.setOption(QFileDialog.Option.DontUseCustomDirectoryIcons, True)
            dialog.setFileMode(QFileDialog.FileMode.Directory)
            dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
            dialog.setWindowTitle(QCoreApplication.translate("SettingsPage", "Select default recording folder"))
            dialog.finished.connect(self._folder_selected)
            self._folder_dialog = dialog
        self._folder_dialog.setStyleSheet(self.manager.stylesheet())
        self._folder_dialog.setDirectory(self._pending_folder)
        self._folder_dialog.open()

    def _folder_selected(self, result):
        if result == QDialog.DialogCode.Accepted:
            paths = self._folder_dialog.selectedFiles()
            if paths:
                self._pending_folder = str(Path(paths[0]).resolve())
                self._sync_controls()

    def _show_error(self, text):
        self._message = QMessageBox(self.parent)
        self._message.setWindowTitle(QCoreApplication.translate("SettingsPage", "Settings could not be saved"))
        self._message.setText(text)
        self._message.setIcon(QMessageBox.Icon.Warning)
        self._message.setStyleSheet(self.manager.stylesheet())
        self._message.open()

    def ApplyTheme(self, checked=False):
        """Save preferences without redirecting any active recording."""
        if self._pending_folder != self._saved_folder and not Path(self._pending_folder).is_dir():
            self._show_error(QCoreApplication.translate("SettingsPage", "The selected recording folder does not exist."))
            return
        if not language_available(self._pending_language):
            self._show_error(QCoreApplication.translate("SettingsPage", "The selected language translation is not installed."))
            return
        self.preferences.setValue(LANGUAGE_KEY, self._pending_language)
        self.preferences.setValue(RECORDING_DIRECTORY_KEY, self._pending_folder)
        self.preferences.sync()
        if self.preferences.status() != self.preferences.Status.NoError:
            self._show_error(QCoreApplication.translate("SettingsPage", "Your preferences could not be written to disk."))
            return
        try:
            self.manager.apply_and_save()
        except OSError:
            # Keep the general preferences in step with the unsaved theme.
            self.preferences.setValue(LANGUAGE_KEY, self._saved_language)
            self.preferences.setValue(RECORDING_DIRECTORY_KEY, self._saved_folder)
            self.preferences.sync()
            self._show_error(QCoreApplication.translate("SettingsPage", "Your appearance settings could not be written to disk."))
            return
        self._saved_language = self._pending_language
        self._saved_folder = self._pending_folder
        self._sync_controls()

    def RevertTheme(self, checked=False):
        self._pending_language = self._saved_language
        self._pending_folder = self._saved_folder
        self.manager.discard_changes()

    def ResetTheme(self, checked=False):
        """Stage factory appearance and English, keeping the data destination."""
        self._pending_language = "en"
        self.manager.stage_defaults()


def ShowPage(self):
    """Navigation entry point retained for Parameters_NavigationButtons."""
    self.settings_page.ShowPage()
