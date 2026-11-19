"""No-Qt regression checks for the Spikeling Phase 2A tutorial overlay.

Run from the GUI root:
    python -m pytest -q tests/test_tutorials_phase2a.py

Installer tests require the distributed installer; set the environment variable
SPIKELING_TUTORIAL_PHASE2A_INSTALLER to its full path on Windows.
"""
from __future__ import annotations

import ast
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import types
import xml.etree.ElementTree as ET

import pytest

ROOT = Path(__file__).resolve().parents[1]
TUTORIALS = ROOT / "spikeling_gui/features/tutorials"
FORMS = ROOT / "spikeling_gui/ui/forms"
GENERATED = ROOT / "spikeling_gui/ui/generated"


def load_module(name: str):
    file = TUTORIALS / f"{name}.py"
    unique = f"phase2a_test_{name}"
    spec = importlib.util.spec_from_file_location(unique, file)
    module = importlib.util.module_from_spec(spec)
    sys.modules[unique] = module
    spec.loader.exec_module(module)
    return module


def installer():
    configured = os.environ.get("SPIKELING_TUTORIAL_PHASE2A_INSTALLER")
    path = Path(configured) if configured else ROOT / "apply_spikeling_tutorials_phase2a.py"
    if not path.is_file():
        pytest.skip("The standalone Phase 2A installer is external. Set SPIKELING_TUTORIAL_PHASE2A_INSTALLER.")
    return path


def test_catalogue_has_complete_current_injection_learning_sequence():
    module = load_module("catalogue")
    module.validate_catalogue()
    assert {x.id for x in module.TUTORIALS} == {"NI-04", "EM-01", "DA-01"}
    tutorial = module.get_tutorial("NI-04")
    assert len(tutorial.steps) >= 10
    assert {s.response_kind for s in tutorial.steps} >= {"predict", "observe", "explain"}
    assert {s.completion for s in tutorial.steps} >= {
        "board_connected", "cc_ready", "spike_seen", "recording_saved"
    }
    assert any(s.confirmation and "physical" in s.instruction.lower() for s in tutorial.steps)
    assert all(s.id.startswith("NI-04-") for s in tutorial.steps)
    assert len({s.id for s in tutorial.steps}) == len(tutorial.steps)


def test_ui_designer_form_agrees_with_generated_class():
    required = {"phaseLabel", "progressBar", "reflectionPrompt", "reflectionEdit",
                "attestationCheck", "showControlButton", "manualObservationButton"}
    xml = ET.parse(FORMS / "UI_TutorialPanel.ui").getroot()
    xml_names = {w.get("name") for w in xml.iter("widget")}
    assert required <= xml_names
    tree = ast.parse((GENERATED / "UI_TutorialPanel.py").read_text(encoding="utf-8"))
    names = {call.args[0].value for call in ast.walk(tree)
             if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
             and call.func.attr == "setObjectName" and call.args
             and isinstance(call.args[0], ast.Constant)}
    assert xml_names <= names, xml_names - names


def test_spike_detector_counts_new_crossings_without_claiming_causality():
    module = load_module("observations")
    detector = module.SpikeEvidence()
    assert not detector.observe([-65])
    assert not detector.observe([-40])
    assert detector.observe([30])
    assert detector.count == 1
    assert not detector.observe([29])
    assert not detector.observe([-60])
    assert detector.observe([30])
    assert detector.count == 2
    assert not detector.observe([float("nan")])
    assert not detector.observe([])
    assert module.response_is_substantive("Vm increased")
    assert not module.response_is_substantive(" ")


def test_recording_evidence_requires_new_cycle_successful_save(tmp_path):
    module = load_module("observations")
    sample = tmp_path / "trial.csv"
    sample.write_text("t,vm\n0,0\n", encoding="utf-8")
    evidence = module.RecordingEvidence()
    assert not evidence.observe(active=False, pending=False, path=sample, label="Saved 12 samples")
    evidence.observe(active=True, pending=False, path=sample, label="Recording")
    assert not evidence.observe(active=False, pending=True, path=sample, label="Retry save")
    assert not evidence.observe(active=False, pending=False, path=sample, label="No samples received")
    assert evidence.observe(active=False, pending=False, path=sample, label="Stopped • Saved 12 samples")


def test_progress_uses_versioned_local_keys_and_stores_responses(monkeypatch):
    class Store:
        def __init__(self): self.values = {}
        def value(self, key, default=""): return self.values.get(key, default)
        def setValue(self, key, value): self.values[key] = value
        def remove(self, key): self.values.pop(key, None)
        def sync(self): pass

    stub = types.ModuleType("spikeling_gui.preferences")
    stub.preference_store = Store
    monkeypatch.setitem(sys.modules, "spikeling_gui", types.ModuleType("spikeling_gui"))
    monkeypatch.setitem(sys.modules, "spikeling_gui.preferences", stub)
    module = load_module("progress")
    assert module.PREFIX.endswith("/v2")
    saved = Store()
    p = module.TutorialProgress(saved)
    p.save_resume("NI-04", "NI-04-05")
    p.save_response("NI-04", "NI-04-05", "A negative current should lower Vm")
    assert p.get_resume() == ("NI-04", "NI-04-05")
    assert p.get_response("NI-04", "NI-04-05").startswith("A negative")
    p.mark_complete("NI-04")
    assert p.get_resume() is None and p.is_complete("NI-04")
    p.save_response("NI-04", "NI-04-05", "")
    assert p.get_response("NI-04", "NI-04-05") == ""


def test_controller_never_writes_serial_or_starts_recording():
    source = (TUTORIALS / "controller.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
    dangerous = {"write", "start_recording", "stop_recording", "setChecked", "setValue"}
    # Safe tutorial widgets use setChecked(False) for an attestation checkbox,
    # and setValue for the tutorial progress bar. Serial output is prohibited.
    assert "serial_port.write" not in source
    assert "serial_manager.write" not in source
    assert "graph.start_recording" not in source
    assert "graph.stop_recording" not in source
    assert 'self._active.id == "NI-04" and self._step_index >= 3' in source
    assert "recording_in_cc" in source
    assert all(not (isinstance(c.func, ast.Attribute) and c.func.attr == "write") for c in calls)


def test_installer_check_apply_repeat_rollback_and_collision(tmp_path):
    patch = installer()
    distribution = patch.parent
    gui = tmp_path / "GUI - PyQt6-PySide6"
    base = gui / "spikeling_gui"
    (base / "ui/forms").mkdir(parents=True)
    (base / "widgets").mkdir(parents=True)
    (gui / "Data/Tutorials").mkdir(parents=True)
    (base / "main_window.py").write_text(
        "from spikeling_gui.features.tutorials.controller import TutorialController\n"
        "class MainWindow:\n"
        "    def __init__(self):\n"
        "        self.ui.setupUi(self)\n"
        "        self.tutorials = TutorialController(self)\n", encoding="utf-8"
    )
    (base / "widgets/toggle_buttons.py").write_text(
        "# PatchClampMode_toggleButton PatchClamp_toggleButton\n", encoding="utf-8")
    widgetnames = ("NeuronTutorial_pushButton", "mainbody_stackedWidget",
                   "page_Spikeling_NeuronInterface", "page_Spikeling_NeuronEmulator",
                   "page_Spikeling_DataAnalysis", "Spikeling_ConnectButton", "Spikeling_VmCheckbox",
                   "Spikeling_DataRecording_Record_pushButton", "Spikeling_NeuronParameter_pushButton")
    ui_xml = "<ui>" + "".join(f'<widget name="{name}"/>' for name in widgetnames) + "</ui>"
    (base / "ui/forms/UI_Spikeling.ui").write_text(ui_xml, encoding="utf-8")

    replacement = ("spikeling_gui/features/tutorials/catalogue.py",
                   "spikeling_gui/features/tutorials/controller.py",
                   "spikeling_gui/features/tutorials/progress.py",
                   "spikeling_gui/ui/forms/UI_TutorialPanel.ui",
                   "spikeling_gui/ui/generated/UI_TutorialPanel.py")
    for relative in replacement:
        target = gui / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((distribution / "compat/phase1" / relative).read_bytes())
    args = [sys.executable, str(patch), "--root", str(gui)]
    check = subprocess.run([*args, "--check"], capture_output=True, text=True)
    assert check.returncode == 0, check.stderr
    assert "Updated files: 5 New files: 4" in check.stdout
    apply = subprocess.run([*args, "--apply"], capture_output=True, text=True)
    assert apply.returncode == 0, apply.stderr
    assert (gui / "spikeling_gui/features/tutorials/observations.py").is_file()
    repeated = subprocess.run([*args, "--apply"], capture_output=True, text=True)
    assert repeated.returncode == 0, repeated.stderr
    assert "Updated files: 0 New files: 0" in repeated.stdout
    # Refuse rollback if the user has edited installed tutorial files.
    edited = gui / replacement[0]
    edited.write_text("# User modification\n", encoding="utf-8")
    refused = subprocess.run([*args, "--rollback"], capture_output=True, text=True)
    assert refused.returncode != 0
    assert "refusing rollback" in refused.stderr
    edited.write_bytes((distribution / replacement[0]).read_bytes())
    rollback = subprocess.run([*args, "--rollback"], capture_output=True, text=True)
    assert rollback.returncode == 0, rollback.stderr
    assert not (gui / "spikeling_gui/features/tutorials/observations.py").exists()
    assert (gui / replacement[0]).read_bytes() == (distribution / "compat/phase1" / replacement[0]).read_bytes()
