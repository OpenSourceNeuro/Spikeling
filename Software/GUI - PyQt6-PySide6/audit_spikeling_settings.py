#!/usr/bin/env python3
"""Read-only audit of the locally generated Spikeling Settings page.

Run next to UI_Spikeling.py, UI_Spikeling.ui, resources.qrc, and Main.py:
    python audit_spikeling_settings.py

This does not launch Main.py, connect a board, or modify any files.
It instantiates only the generated Designer interface in offscreen Qt.
"""

from __future__ import annotations

import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(Path.cwd()))


def check_sources(base: Path) -> None:
    print("=== SOURCE FILES ===")
    for name in ("UI_Spikeling.py", "UI_Spikeling.ui", "Page_Settings.py", "Main.py",
                 "resources.qrc", "resources_rc.py"):
        path = base / name
        print(f"{'FOUND  ' if path.is_file() else 'MISSING'}  {name}")

    ui_xml = base / "UI_Spikeling.ui"
    ui_py = base / "UI_Spikeling.py"
    if ui_xml.exists() and ui_py.exists() and ui_xml.stat().st_mtime > ui_py.stat().st_mtime:
        print("WARNING: UI_Spikeling.ui is newer than UI_Spikeling.py. Regenerate the Python UI.")

    qrc = base / "resources.qrc"
    compiled = base / "resources_rc.py"
    if qrc.exists() and compiled.exists() and qrc.stat().st_mtime > compiled.stat().st_mtime:
        print("WARNING: resources.qrc is newer than resources_rc.py. Run pyside6-rcc.")

    main = base / "Main.py"
    if main.exists():
        data = main.read_text(encoding="utf-8", errors="replace")
        count = len(re.findall(r"self\.settings_page\s*=\s*SettingsPage\s*\(", data))
        print(f"Main.py SettingsPage instantiations: {count}")
        if count > 1:
            print("ERROR: SettingsPage created more than once; remove duplicate constructor.")

    controller = base / "Page_Settings.py"
    if controller.exists():
        data = controller.read_text(encoding="utf-8", errors="replace")
        if "page_601" in data:
            print("WARNING: Settings controller still refers to obsolete page_601.")
        if "_build_controls(" in data:
            print("WARNING: Settings controller still builds widgets programmatically;"
                  " check for duplication with your Designer page.")


def check_resources(base: Path) -> None:
    print("\n=== Qt RESOURCE FILE ===")
    qrc = base / "resources.qrc"
    ui_py = base / "UI_Spikeling.py"
    if not qrc.exists():
        print("Cannot check resources.qrc (not found).")
        return
    try:
        root = ET.parse(qrc).getroot()
    except ET.ParseError as exc:
        print(f"ERROR: Invalid resources.qrc XML: {exc}")
        return
    resource_names = set()
    missing_files = []
    for collection in root.findall("qresource"):
        prefix = collection.get("prefix", "").strip("/")
        for item in collection.findall("file"):
            rel = (item.text or "").strip()
            alias = item.get("alias", "") or rel
            resource_names.add(":/" + "/".join(filter(None, (prefix, alias))))
            if not (base / rel).is_file():
                missing_files.append(rel)
    print(f"Declared resource files: {len(resource_names)}")
    for name in missing_files[:30]:
        print(f"ERROR: Missing file referenced by qrc: {name}")
    if not missing_files:
        print("All resource source files declared in qrc exist on disk.")
    if ui_py.exists():
        contents = ui_py.read_text(encoding="utf-8", errors="replace")
        referenced = set(re.findall(r":/resources/[A-Za-z0-9_./-]+", contents))
        missing_refs = sorted(referenced - resource_names)
        if missing_refs:
            print(f"WARNING: {len(missing_refs)} UI resource paths absent from resources.qrc:")
            for ref in missing_refs[:25]:
                print("  ", ref)
        else:
            print("Every :/resources/... UI reference is declared in resources.qrc.")


def audit_live_ui(base: Path) -> None:
    print("\n=== OFFSCREEN DESIGNER PAGE ===")
    try:
        from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QGroupBox,
                                       QComboBox, QLineEdit, QPushButton, QLabel)
        from UI_Spikeling import Ui_Spikeling
    except Exception as exc:
        print(f"ERROR: Could not import UI / PySide6: {exc}")
        return

    app = QApplication.instance() or QApplication([])
    win = QMainWindow()
    ui = Ui_Spikeling()
    try:
        ui.setupUi(win)
    except Exception as exc:
        print(f"ERROR: setupUi failed: {type(exc).__name__}: {exc}")
        return

    page = getattr(ui, "page_Settings", None)
    if page is None:
        print("ERROR: generated UI has no page_Settings attribute.")
        return
    print("page_Settings exists:", isinstance(page, QWidget))
    print("Root layout:", type(page.layout()).__name__ if page.layout() else "MISSING")

    names = {}
    for widget in [page] + page.findChildren(QWidget):
        name = widget.objectName()
        if name:
            names.setdefault(name, []).append(type(widget).__name__)
    repeated = {name: classes for name, classes in names.items() if len(classes) > 1}
    print("Widgets in Settings page:", len(page.findChildren(QWidget)))
    if repeated:
        print("ERROR: Duplicate object names inside Settings:", repeated)

    for group in page.findChildren(QGroupBox):
        print(f"GROUP: objectName={group.objectName()!r} title={group.title()!r} "
              f"layout={type(group.layout()).__name__ if group.layout() else 'MISSING'}")

    for combo in page.findChildren(QComboBox):
        items = []
        for i in range(combo.count()):
            items.append({"label": combo.itemText(i), "data": combo.itemData(i),
                          "has_icon": not combo.itemIcon(i).isNull()})
        print(f"COMBO: {combo.objectName()} size={combo.iconSize().width()}x"
              f"{combo.iconSize().height()} items={items}")
        if "language" in combo.objectName().lower():
            if any(not entry["has_icon"] for entry in items):
                print("WARNING: one or more language items have no flag icon.")
            if any(not entry["data"] for entry in items):
                print("INFO: set stable item userData (en/fr/es/it/el) in Python controller.")

    for edit in page.findChildren(QLineEdit):
        print(f"LINE EDIT: {edit.objectName()} readOnly={edit.isReadOnly()} "
              f"placeholder={edit.placeholderText()!r}")

    for button in page.findChildren(QPushButton):
        print(f"BUTTON: {button.objectName()} text={button.text()!r}")

    print("\nAUDIT COMPLETE. Review any ERROR/WARNING messages and the widget names above.")


if __name__ == "__main__":
    base = Path.cwd()
    print("Spikeling Settings audit —", base)
    check_sources(base)
    check_resources(base)
    audit_live_ui(base)
