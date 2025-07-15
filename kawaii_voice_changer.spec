# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

# Spec file for Kawaii Voice Changer

block_cipher = None

# Determine the base path
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    base_path = sys._MEIPASS
else:
    base_path = os.path.abspath('.')

# Additional binaries for Linux Qt support
binaries = []
if sys.platform == 'linux':
    # Include Qt platform plugins for Linux
    import PySide6
    pyside_path = Path(PySide6.__file__).parent
    qt_plugins_path = pyside_path / 'Qt' / 'plugins'
    if qt_plugins_path.exists():
        binaries.append((str(qt_plugins_path / 'platforms'), 'PySide6/Qt/plugins/platforms'))
        binaries.append((str(qt_plugins_path / 'xcbglintegrations'), 'PySide6/Qt/plugins/xcbglintegrations'))
        binaries.append((str(qt_plugins_path / 'wayland-shell-integration'), 'PySide6/Qt/plugins/wayland-shell-integration'))
        binaries.append((str(qt_plugins_path / 'wayland-graphics-integration-client'), 'PySide6/Qt/plugins/wayland-graphics-integration-client'))
        binaries.append((str(qt_plugins_path / 'wayland-decoration-client'), 'PySide6/Qt/plugins/wayland-decoration-client'))

a = Analysis(
    ['src/kawaii_voice_changer/__main__.py'],
    pathex=[],
    binaries=binaries,
    datas=[
        # Add any data files here if needed
    ],
    hiddenimports=[
        'pyworld',
        'scipy.signal',
        'scipy.fft',
        'scipy.optimize',
        'scipy.interpolate',
        'scipy.linalg',
        'numpy',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'pyqtgraph',
        'sounddevice',
        'soundfile',
        # Add Qt platform plugin imports
        'PySide6.QtDBus',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['runtime_hook.py'],
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
    name='KawaiiVoiceChanger',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to False for GUI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if available
)

# For macOS, create an app bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='KawaiiVoiceChanger.app',
        icon=None,  # Add icon path here if available
        bundle_identifier='com.ayutaz.kawaiivoicechanger',
        info_plist={
            'NSHighResolutionCapable': 'True',
            'LSBackgroundOnly': 'False',
        },
    )