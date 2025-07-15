"""Runtime hook for PyInstaller to set Qt platform plugin path."""

import os
import sys

# Set Qt platform plugin path for PyInstaller
if hasattr(sys, '_MEIPASS'):
    plugin_path = os.path.join(sys._MEIPASS, 'PySide6', 'Qt', 'plugins')
    if os.path.exists(plugin_path):
        os.environ['QT_PLUGIN_PATH'] = plugin_path
    
    # Also set QT_QPA_PLATFORM_PLUGIN_PATH for xcb plugin
    platforms_path = os.path.join(plugin_path, 'platforms')
    if os.path.exists(platforms_path):
        os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = platforms_path
    
    # Set default platform to xcb on Linux
    if sys.platform == 'linux' and 'QT_QPA_PLATFORM' not in os.environ:
        os.environ['QT_QPA_PLATFORM'] = 'xcb'