"""Static and content tests; no Qt runtime or physical board needed."""
from __future__ import annotations

import ast
import importlib.util
import os
import pathlib
import subprocess
import sys
import types
import xml.etree.ElementTree as ET

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
TUTORIALS = ROOT / "spikeling_gui/features/tutorials"
FORMS = ROOT / "spikeling_gui/ui/forms"
GENERATED = ROOT / "spikeling_gui/ui/generated"


def standalone_installer():
    """Locate the standalone distribution installer if available.

    The installer is not part of an installed GUI checkout. Developers can
    supply its location explicitly with SPIKELING_TUTORIAL_INSTALLER.
    """
    configured = os.environ.get("SPIKELING_TUTORIAL_INSTALLER")
    path = pathlib.Path(configured).expanduser() if configured else ROOT / "apply_spikeling_tutorials_phase1.py"
    if not path.is_file():
        pytest.skip(
            "Standalone installer is not in this checkout; "
            "set SPIKELING_TUTORIAL_INSTALLER to run its integration tests"
        )
    return path


def load_catalogue():
    name = "spikeling_tutorial_catalogue_static_test"
    spec = importlib.util.spec_from_file_location(name, TUTORIALS / "catalogue.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_catalogue_is_unique_and_has_three_pilots():
    catalogue = load_catalogue()
    catalogue.validate_catalogue()
    assert {t.id for t in catalogue.TUTORIALS} == {"NI-04", "EM-01", "DA-01"}
    assert all(t.steps for t in catalogue.TUTORIALS)
    assert any(s.completion == "board_connected" for t in catalogue.TUTORIALS for s in t.steps)
    assert any(s.completion == "emulator_running" for t in catalogue.TUTORIALS for s in t.steps)
    assert any(s.completion == "recording_loaded" for t in catalogue.TUTORIALS for s in t.steps)
    assert catalogue.get_tutorial("invalid") is None


def test_qt_forms_and_companion_widgets_have_matching_names():
    for name in ("TutorialCatalogue", "TutorialPanel"):
        form = FORMS / f"UI_{name}.ui"
        generated = GENERATED / f"UI_{name}.py"
        xml = ET.parse(form).getroot()
        widgets = {element.attrib["name"] for element in xml.findall(".//widget")}
        text = generated.read_text(encoding="utf-8")
        tree = ast.parse(text)
        declared_names = {
            node.args[0].value for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "setObjectName"
            and node.args and isinstance(node.args[0], ast.Constant)
        }
        assert widgets <= declared_names, f"Generated class is missing widgets in {name}: {widgets - declared_names}"


def test_progress_resume_and_completion(monkeypatch):
    class FakeSettings:
        def __init__(self): self.data = {}
        def value(self, key, default=""): return self.data.get(key, default)
        def setValue(self, key, value): self.data[key] = value
        def remove(self, key): self.data.pop(key, None)
        def sync(self): pass

    fake_preferences = types.ModuleType("spikeling_gui.preferences")
    fake_preferences.preference_store = FakeSettings
    monkeypatch.setitem(sys.modules, "spikeling_gui", types.ModuleType("spikeling_gui"))
    monkeypatch.setitem(sys.modules, "spikeling_gui.preferences", fake_preferences)
    name = "spikeling_tutorial_progress_test"
    spec = importlib.util.spec_from_file_location(name, TUTORIALS / "progress.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    store = FakeSettings()
    progress = module.TutorialProgress(store)
    assert progress.get_resume() is None
    progress.save_resume("NI-04", "NI-04-02")
    assert progress.get_resume() == ("NI-04", "NI-04-02")
    assert not progress.is_complete("NI-04")
    progress.mark_complete("NI-04")
    assert progress.is_complete("NI-04")
    assert progress.get_resume() is None


def test_installer_dryrun_and_idempotence(tmp_path):
    gui = tmp_path / "GUI - PyQt6-PySide6"
    base = gui / "spikeling_gui"
    (base / "ui/forms").mkdir(parents=True)
    (base / "ui/forms/UI_Spikeling.ui").write_text(
        '<ui><widget name="NeuronTutorial_pushButton"/><widget name="mainbody_stackedWidget"/>'
        '<widget name="page_Spikeling_NeuronInterface"/><widget name="page_Spikeling_NeuronEmulator"/>'
        '<widget name="page_Spikeling_DataAnalysis"/></ui>', encoding="utf-8")
    (gui / "Data").mkdir()
    (gui / "Data/.gitignore").write_text("*/*\n", encoding="utf-8")
    (base / "main_window.py").write_text(
        "from spikeling_gui.features.settings.page import SettingsPage\n"
        "class MainWindow:\n"
        "    def __init__(self):\n"
        "        self.ui = Ui_Spikeling()\n"
        "        self.ui.setupUi(self)\n"
        "        NavigationButtons.Buttons(self)\n"
        "        print('ready')\n", encoding="utf-8")
    installer = standalone_installer()
    prefix = [sys.executable, str(installer), "--root", str(gui), "--allow-updated-main-window"]
    dry = subprocess.run([*prefix, "--check"], capture_output=True, text=True)
    assert dry.returncode == 0, dry.stderr
    assert not (base / "features/tutorials/controller.py").exists()
    apply = subprocess.run([*prefix, "--apply"], capture_output=True, text=True)
    assert apply.returncode == 0, apply.stderr
    assert (base / "features/tutorials/controller.py").is_file()
    assert "!/Tutorials/tutorial_CC_spikes.csv" in (gui / "Data/.gitignore").read_text()
    source = (base / "main_window.py").read_text()
    assert source.count("self.tutorials = TutorialController(self)") == 1
    assert source.count("from spikeling_gui.features.tutorials.controller import TutorialController") == 1
    again = subprocess.run([*prefix, "--apply"], capture_output=True, text=True)
    assert again.returncode == 0, again.stderr
    assert (base / "main_window.py").read_text() == source



def test_installer_works_with_committed_main_window_reorganisation(tmp_path):
    # Simulate a clean but structurally different branch: no textual anchors,
    # altered imports and renamed navigation initialisation.
    gui = tmp_path / "GUI - PyQt6-PySide6"
    base = gui / "spikeling_gui"
    (base / "ui/forms").mkdir(parents=True)
    (base / "ui/forms/UI_Spikeling.ui").write_text(
        '<ui><widget name="NeuronTutorial_pushButton"/><widget name="mainbody_stackedWidget"/>'
        '<widget name="page_Spikeling_NeuronInterface"/><widget name="page_Spikeling_NeuronEmulator"/>'
        '<widget name="page_Spikeling_DataAnalysis"/></ui>', encoding="utf-8")
    (gui / "Data").mkdir()
    (gui / "Data/.gitignore").write_text("*/*\n", encoding="utf-8")
    (base / "main_window.py").write_text(
        "from PySide6.QtWidgets import QMainWindow\n"
        "from spikeling_gui.foo import NewNavigation\n"
        "class MainWindow(QMainWindow):\n"
        "    def __init__(self):\n"
        "        super().__init__()\n"
        "        self.ui = MyUI()\n"
        "        self.ui.setupUi(self)\n"
        "        NewNavigation.start(self)\n"
        "        self.settings = object()\n", encoding="utf-8")
    installer = standalone_installer()
    result = subprocess.run(
        [sys.executable, str(installer), "--root", str(gui),
         "--allow-updated-main-window", "--check"], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "at the end of MainWindow.__init__" in result.stdout
    result = subprocess.run(
        [sys.executable, str(installer), "--root", str(gui),
         "--allow-updated-main-window", "--apply"], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    source = (base / "main_window.py").read_text()
    tree = ast.parse(source)
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "MainWindow")
    init = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "__init__")
    assert isinstance(init.body[-1], ast.Assign)
    assert source.count("self.tutorials = TutorialController(self)") == 1
    assert source.count("NewNavigation.start(self)") == 1

def test_bundled_csv_matches_spikeling_cc_import_schema():
    import csv
    sample = ROOT / "Data/Tutorials/tutorial_CC_spikes.csv"
    expected = (
        "Time (ms)", "Stimulus (%)", "Trigger", "Spikeling Vm (mV)",
        "Synapse 1 Vm (mV)", "Synapse 2 Vm (mV)",
        "Total Current Input (a.u.)", "Synapse 1 Input (a.u.)",
        "Synapse 2 Input (a.u.)",
    )
    with sample.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        assert tuple(reader.fieldnames) == expected
        rows = list(reader)
    assert len(rows) >= 10000
    time = [float(x["Time (ms)"]) for x in rows]
    assert all(a < b for a, b in zip(time, time[1:]))
    spikes = sum(float(x["Spikeling Vm (mV)"]) >= 30 for x in rows)
    assert spikes >= 5
    assert any(int(x["Trigger"]) for x in rows)
