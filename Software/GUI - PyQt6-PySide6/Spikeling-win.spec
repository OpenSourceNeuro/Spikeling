# -*- mode: python ; coding: utf-8 -*-
import os, sys
from PySide6 import QtCore
from PyInstaller.building.datastruct import Tree

block_cipher = None

# PyInstaller injects SPECPATH (directory holding this spec). sys.argv[0] points
# at the pyinstaller launcher, not at the spec, so it cannot anchor data paths.
try:
    spec_dir = SPECPATH
except NameError:
    spec_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

# Qt plugins
plugin_path = QtCore.QLibraryInfo.location(QtCore.QLibraryInfo.PluginsPath)
qt_plugins = []
for plugin_type in ['platforms', 'imageformats', 'styles']:
    src = os.path.join(plugin_path, plugin_type)
    if os.path.exists(src):
        qt_plugins.append((src, os.path.join('PySide6/Qt/plugins', plugin_type)))

# Loose files addressed through resource_path() at runtime.
app_datas = []
icon_file = os.path.join(spec_dir, 'Spikeling.ico')
if os.path.exists(icon_file):
    app_datas.append((icon_file, '.'))

hidden_imports = [
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'PySide6.QtSerialPort',   # used by serial_manager
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
        'geometry_view',          # injected into sys.modules by Tetrode.py
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

# Asset tree: resources/Spiky*.png (tetrode scene) and
# resources/geci/<indicator>/frame_*.png (rotating protein previews).
# Mirrored verbatim under the bundle root, which is what resource_path() reads.
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
    upx=False,              # UPX mangles Qt plugin payloads on some runners
    console=False,
    icon=icon_file if os.path.exists(icon_file) else None,
)
