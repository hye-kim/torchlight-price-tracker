# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Torchlight Infinite Price Tracker
"""

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all data files needed by the application
datas = [
    ('config.json', '.'),
    ('en_id_table.json', '.'),
    ('full_table.json', '.'),
    ('translation_mapping.json', '.'),
]

# Hidden imports that PyInstaller might miss
hiddenimports = [
    'PyQt5.QtCore',
    'PyQt5.QtGui',
    'PyQt5.QtWidgets',
    'PyQt5.sip',
    'win32api',
    'win32con',
    'win32process',
    'win32gui',
    'psutil',
    'requests',
    'openpyxl',
    'openpyxl.cell',
    'openpyxl.styles',
    'openpyxl.utils',
    'src.constants',
    'src.config_manager',
    'src.file_manager',
    'src.log_parser',
    'src.inventory_tracker',
    'src.statistics_tracker',
    'src.game_detector',
]

a = Analysis(
    ['index.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='TorchlightInfiniteTracker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to False for a GUI application (no console window)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add an icon file path here if you have one (e.g., 'icon.ico')
)
