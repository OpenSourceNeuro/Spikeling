# -*- mode: python ; coding: utf-8 -*-
import os, sys
from PySide6 import QtCore
from PyInstaller.building.datastruct import Tree

block_cipher = None

try:
    spec_dir = SPECPATH
except NameError:
    spec_dir = os.path.abspath(SPECPATH)

# Qt resolves HTTPS through a TLS backend plugin loaded at runtime. Omitting
# the 'tls' directory produces a binary where every network request fails
# with UnknownNetworkError and no further diagnostic, which is precisely the
# failure mode the update checker would hit. 'networkinformation' lets Qt
# detect offline state instead of hanging until timeout.
plugin_path = QtCore.QLibraryInfo.location(QtCore.QLibraryInfo.PluginsPath)
qt_plugins = []
for plugin_type in ['platforms', 'imageformats', 'tls', 'networkinformation']:
    src = os.path.join(plugin_path, plugin_type)
    if os.path.exists(src):
        qt_plugins.append((src, os.path.join('PySide6/Qt/plugins', plugin_type)))


app_datas = []
icon_file = os.path.join(spec_dir, 'Spikeling.ico')
if os.path.exists(icon_file):
    app_datas.append((icon_file, '.'))

hidden_imports = [
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'PySide6.QtNetwork',
    'theme_manager',
    'Page_Settings',
    'Page_GitHub',
    'update_service',
    'update_installer',
    'version',
]

a = Analysis(
    [os.path.join(spec_dir, 'Main.py')],
    pathex=[spec_dir],
    binaries=[],
    datas=qt_plugins + app_datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        'geometry_view',
        'PySide6.QtQml',
        'PySide6.QtQuick',
        'PySide6.QtQuickControls2',
        'PySide6.QtQmlModels',
        'PySide6.QtWebEngine',
        'PySide6.QtWebEngineCore',
        'PySide6.QtWebEngineWidgets',
        'PySide6.QtBluetooth',
        'PySide6.QtLocation',
        'PySide6.QtPositioning',
        'PySide6.QtMultimedia',
        'PySide6.QtMultimediaWidgets',
        'PySide6.QtSensors',
        'PySide6.QtSql',
        'PySide6.QtSvg',
        'PySide6.QtUiTools',
        'PySide6.QtWebSockets',
        'PySide6.QtXml',
        'PySide6.QtXmlPatterns',
        'PySide6.QtTest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# --- Bundle sanity check --------------------------------------------------
# A missing module here produces an application that launches normally and
# then does nothing on the Settings page, which is far more expensive to
# diagnose than a red CI job.
_required_modules = {'theme_manager', 'Page_Settings', 'Page_Spikeling_DataAnalysis',
                     'Page_GitHub', 'update_service', 'update_installer', 'version'}

_bundled_modules = {entry[0] for entry in a.pure}
_missing_modules = _required_modules - _bundled_modules
if _missing_modules:
    raise SystemExit(
        f"[spec] These modules were not collected into the bundle: "
        f"{sorted(_missing_modules)}. Check that they live next to Main.py "
        f"and are imported at module level."
    )

# Linux runners are case-sensitive: "Resources/" or "Spiky1.PNG" will build
# clean on Windows/macOS and silently ship nothing here.
a.datas += Tree(
    os.path.join(spec_dir, 'resources'),
    prefix='resources',
    excludes=['*.psd', '*.blend', '*.xcf', '*.ai', '.DS_Store', 'Thumbs.db'],
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Spikeling',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    noupx=True,
    console=False,
)
