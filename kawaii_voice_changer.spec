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

# Platform-specific binaries and data files
binaries = []
datas = []

if sys.platform == 'win32':
    # Windows-specific configurations
    import PySide6
    import sounddevice
    import soundfile
    
    pyside_path = Path(PySide6.__file__).parent
    
    # Include Qt platform plugins for Windows
    qt_plugins_path = pyside_path / 'Qt' / 'plugins'
    if qt_plugins_path.exists():
        binaries.append((str(qt_plugins_path / 'platforms'), 'PySide6/Qt/plugins/platforms'))
        binaries.append((str(qt_plugins_path / 'styles'), 'PySide6/Qt/plugins/styles'))
        binaries.append((str(qt_plugins_path / 'imageformats'), 'PySide6/Qt/plugins/imageformats'))
    
    # Include Qt6 DLLs
    qt_bin_path = pyside_path / 'Qt' / 'bin'
    if qt_bin_path.exists():
        for dll in qt_bin_path.glob('*.dll'):
            binaries.append((str(dll), 'PySide6/Qt/bin'))
    
    # Handle sounddevice PortAudio dependency
    sounddevice_path = Path(sounddevice.__file__).parent
    portaudio_path = sounddevice_path / '_sounddevice_data' / 'portaudio-binaries'
    if portaudio_path.exists():
        datas.append((str(portaudio_path), '_sounddevice_data/portaudio-binaries'))
    
    # Handle soundfile dependencies
    soundfile_path = Path(soundfile.__file__).parent
    soundfile_bins = soundfile_path / '_soundfile_data'
    if soundfile_bins.exists():
        datas.append((str(soundfile_bins), '_soundfile_data'))
    
    # Include Visual C++ runtime if needed
    import sysconfig
    python_dll_path = Path(sysconfig.get_paths()['data']) / 'DLLs'
    for vcruntime in python_dll_path.glob('vcruntime*.dll'):
        binaries.append((str(vcruntime), '.'))
    for msvcp in python_dll_path.glob('msvcp*.dll'):
        binaries.append((str(msvcp), '.'))

elif sys.platform == 'linux':
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

elif sys.platform == 'darwin':
    # macOS-specific configurations can be added here if needed
    pass

a = Analysis(
    ['src/kawaii_voice_changer/__main__.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=[
        'pyworld',
        'scipy.signal',
        'scipy.fft',
        'scipy.optimize',
        'scipy.interpolate',
        'scipy.linalg',
        'scipy.sparse',
        'scipy.special',
        'scipy.special._cdflib',  # Fix for SciPy 1.13.0+ compatibility
        'scipy._lib',
        'scipy._lib.messagestream',
        'numpy',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtMultimedia',
        'PySide6.QtOpenGL',
        'PySide6.QtOpenGLWidgets',
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
    [],
    exclude_binaries=True,  # Changed for onedir mode
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

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='KawaiiVoiceChanger',
)

# For macOS, create an app bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='KawaiiVoiceChanger.app',
        icon=None,  # Add icon path here if available
        bundle_identifier='com.ayutaz.kawaiivoicechanger',
        info_plist={
            'NSHighResolutionCapable': 'True',
            'LSBackgroundOnly': 'False',
            'NSMicrophoneUsageDescription': 'This app requires microphone access for voice processing.',
        },
    )