"""Static and optional Qt checks for the Spikeling tutorial panel appearance patch."""
from __future__ import annotations

import ast
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

import pytest

ROOT = Path(__file__).resolve().parents[1]
FORMS = ROOT / 'spikeling_gui/ui/forms/UI_TutorialPanel.ui'
GENERATED = ROOT / 'spikeling_gui/ui/generated/UI_TutorialPanel.py'
CONTROLLER = ROOT / 'spikeling_gui/features/tutorials/controller.py'


def test_designer_form_has_compact_responsive_structure():
    form = ET.parse(FORMS).getroot()
    nodes = {w.get('name'): w for w in form.iter('widget')}
    parent = {child: ancestor for ancestor in form.iter() for child in ancestor}
    assert nodes['instructionText'].get('class') == 'QLabel'
    assert nodes['reflectionEdit'].get('class') == 'QPlainTextEdit'
    assert nodes['stepScrollArea'].get('class') == 'QScrollArea'
    assert nodes['titleCloseButton'].get('class') == 'QPushButton'
    assert nodes['resizeGripHost'].get('class') == 'QWidget'
    assert nodes['confirmationDetails'].find("property[@name='wordWrap']/bool").text == 'true'
    assert nodes['progressBar'].find("property[@name='textVisible']/bool").text == 'false'
    assert nodes['stepScrollArea'].find("property[@name='widgetResizable']/bool").text == 'true'
    assert parent[parent[nodes['reflectionCard']]].get('name') == 'contentLayout'
    assert parent[parent[nodes['statusCard']]].get('name') == 'footerLayout'
    assert parent[parent[nodes['nextButton']]].get('name') == 'bottomLayout'
    assert parent[parent[nodes['footerCard']]].get('name') == 'rootLayout'


def test_form_and_generated_qt_class_have_same_widget_names():
    widgets = {w.get('name') for w in ET.parse(FORMS).iter('widget')}
    module = ast.parse(GENERATED.read_text(encoding='utf-8'))
    strings = {node.args[0].value for node in ast.walk(module)
               if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
               and node.func.attr == 'setObjectName' and node.args
               and isinstance(node.args[0], ast.Constant)
               and isinstance(node.args[0].value, str)}
    assert widgets <= strings, widgets - strings
    assert len(widgets) == len(set(widgets))


def test_style_is_qt_designer_owned_and_uses_spikeling_palette():
    form = ET.parse(FORMS).getroot()
    qss = form.find("./widget/property[@name='styleSheet']/string").text
    module = ast.parse(GENERATED.read_text(encoding='utf-8'))
    defined_styles = [n.value for n in module.body if isinstance(n, ast.Assign)
                      and any(isinstance(t, ast.Name) and t.id == 'STYLE_SHEET' for t in n.targets)]
    # Support both the supplied companion and future pyside6-uic regeneration.
    if defined_styles:
        assert isinstance(defined_styles[0], ast.Constant)
        assert defined_styles[0].value == qss
    else:
        assert 'QDialog#TutorialPanel' in GENERATED.read_text(encoding='utf-8')
    # Literal factory palette RGB strings are required by WidgetRetheme.
    assert 'rgb(0, 43, 54)' in qss
    assert 'rgb(7, 54, 66)' in qss
    assert 'rgb(190, 205, 205)' in qss
    assert 'rgb(38, 139, 210)' in qss
    assert 'QDialog#TutorialPanel QPushButton' in qss
    assert 'QDialog#TutorialPanel QPlainTextEdit#reflectionEdit' in qss
    assert 'QDialog#TutorialPanel QPushButton#nextButton' in qss
    assert 'QDialog#TutorialPanel QProgressBar#progressBar' in qss
    # Python controls behaviour, not ad hoc appearance overrides.
    assert 'self.panel.setStyleSheet' not in CONTROLLER.read_text(encoding='utf-8')


def test_controller_uses_wrapping_text_and_visible_status():
    source = CONTROLLER.read_text(encoding='utf-8')
    ast.parse(source)
    assert 'ui.instructionText.setText(step.instruction)' in source
    assert 'ui.reflectionCard.setVisible(bool(step.prompt))' in source
    assert 'ui.confirmationCard.setVisible(bool(step.confirmation))' in source
    assert 'ui.confirmationDetails.setText(step.confirmation)' in source
    assert 'ui.stepScrollArea.verticalScrollBar().setValue(0)' in source
    assert 'Qt.WindowType.FramelessWindowHint' in source
    assert 'self.panel_ui.titleCloseButton.clicked.connect(self.panel.reject)' in source
    assert 'QSizeGrip(self.panel_ui.resizeGripHost)' in source
    assert 'serial_port.write' not in source


def test_qt_widget_smoke_if_pyside6_is_installed(monkeypatch):
    pytest.importorskip('PySide6')
    # Use Qt's offscreen platform only for this isolated test; don't affect the real GUI.
    monkeypatch.setenv('QT_QPA_PLATFORM', 'offscreen')
    from PySide6.QtWidgets import QApplication, QDialog, QScrollArea, QLabel
    # The test suite operates from GUI root, so the module can be imported directly.
    from spikeling_gui.ui.generated.UI_TutorialPanel import Ui_TutorialPanel
    app = QApplication.instance() or QApplication([])
    dialog = QDialog()
    ui = Ui_TutorialPanel()
    ui.setupUi(dialog)
    assert isinstance(ui.instructionText, QLabel)
    assert isinstance(ui.stepScrollArea, QScrollArea)
    assert ui.stepScrollArea.widgetResizable()
    assert not ui.progressBar.isTextVisible()
    assert ui.reflectionEdit.minimumHeight() >= 80
    assert ui.nextButton.styleSheet() == ''  # Scoped designer QSS remains on root.
    assert dialog.styleSheet()
    dialog.close()


def test_safe_check_apply_idempotence_rollback(tmp_path):
    patch = os.environ.get('SPIKELING_TUTORIAL_APPEARANCE_PATCH')
    installer = Path(patch) if patch else ROOT / 'apply_tutorial_appearance.py'
    if not installer.is_file():
        pytest.skip('External installer not found; set SPIKELING_TUTORIAL_APPEARANCE_PATCH.')
    distribution = installer.resolve().parent
    gui = tmp_path / 'GUI - PyQt6-PySide6'
    (gui / 'spikeling_gui/ui/forms').mkdir(parents=True)
    (gui / 'spikeling_gui/main_window.py').write_text('class MainWindow:\n    pass\n', encoding='utf-8')
    (gui / 'spikeling_gui/ui/forms/UI_Spikeling.ui').write_text('<ui/>', encoding='utf-8')
    replace = ('spikeling_gui/ui/forms/UI_TutorialPanel.ui',
               'spikeling_gui/ui/generated/UI_TutorialPanel.py',
               'spikeling_gui/features/tutorials/controller.py')
    for rel in replace:
        dest = gui / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes((distribution / 'compat/phase2a' / rel).read_bytes())
    run = lambda action: subprocess.run([sys.executable, str(installer), '--root', str(gui), action],
                                         capture_output=True, text=True)
    check = run('--check')
    assert check.returncode == 0, check.stderr
    assert 'Files to replace: 3; add: 2' in check.stdout
    assert (gui / replace[0]).read_bytes() == (distribution / 'compat/phase2a' / replace[0]).read_bytes()
    changed = run('--apply')
    assert changed.returncode == 0, changed.stderr
    assert (gui / replace[0]).read_bytes() == (distribution / replace[0]).read_bytes()
    repeated = run('--apply')
    assert repeated.returncode == 0, repeated.stderr
    assert 'Files to replace: 0; add: 0' in repeated.stdout
    # Changes to the installed UI must be preserved, not clobbered by rollback.
    (gui / replace[0]).write_text('custom UI', encoding='utf-8')
    refused = run('--rollback')
    assert refused.returncode != 0
    (gui / replace[0]).write_bytes((distribution / replace[0]).read_bytes())
    rolled = run('--rollback')
    assert rolled.returncode == 0, rolled.stderr
    for rel in replace:
        assert (gui / rel).read_bytes() == (distribution / 'compat/phase2a' / rel).read_bytes()
    assert not (gui / 'tests/test_tutorials_phase2a_appearance.py').exists()
