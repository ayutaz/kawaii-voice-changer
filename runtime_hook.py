"""Runtime hook for PyInstaller to set Qt platform plugin path."""

import os
import sys

# Set Qt platform plugin path for PyInstaller
if hasattr(sys, "_MEIPASS"):
    plugin_path = os.path.join(sys._MEIPASS, "PySide6", "Qt", "plugins")
    if os.path.exists(plugin_path):
        os.environ["QT_PLUGIN_PATH"] = plugin_path

    # Also set QT_QPA_PLATFORM_PLUGIN_PATH
    platforms_path = os.path.join(plugin_path, "platforms")
    if os.path.exists(platforms_path):
        os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = platforms_path

    # Platform-specific configurations
    if sys.platform == "win32":
        # Windows-specific Qt environment
        if "QT_QPA_PLATFORM" not in os.environ:
            os.environ["QT_QPA_PLATFORM"] = "windows"

        # Ensure Qt can find its binaries
        qt_bin_path = os.path.join(sys._MEIPASS, "PySide6", "Qt", "bin")
        if os.path.exists(qt_bin_path):
            os.environ["PATH"] = qt_bin_path + os.pathsep + os.environ.get("PATH", "")

        # Set additional Windows-specific paths
        styles_path = os.path.join(plugin_path, "styles")
        if os.path.exists(styles_path):
            os.environ["QT_STYLE_OVERRIDE"] = "windows"

    elif sys.platform == "linux":
        # Linux-specific Qt environment
        if "QT_QPA_PLATFORM" not in os.environ:
            os.environ["QT_QPA_PLATFORM"] = "xcb"

        # Set library path for bundled libraries
        lib_path = os.path.join(sys._MEIPASS, "PySide6", "Qt", "lib")
        if os.path.exists(lib_path):
            ld_library_path = os.environ.get("LD_LIBRARY_PATH", "")
            if ld_library_path:
                os.environ["LD_LIBRARY_PATH"] = lib_path + os.pathsep + ld_library_path
            else:
                os.environ["LD_LIBRARY_PATH"] = lib_path

        # Enable OpenGL integration
        os.environ["QT_XCB_GL_INTEGRATION"] = "xcb_glx"

        # Set audio backend preference (ALSA > PulseAudio > JACK)
        if "SDL_AUDIODRIVER" not in os.environ:
            os.environ["SDL_AUDIODRIVER"] = "alsa,pulse,jack"

        # Disable Wayland decorations if running under Wayland
        if os.environ.get("XDG_SESSION_TYPE") == "wayland":
            os.environ["QT_WAYLAND_DISABLE_WINDOWDECORATION"] = "1"

    elif sys.platform == "darwin":
        # macOS-specific Qt environment
        if "QT_QPA_PLATFORM" not in os.environ:
            os.environ["QT_QPA_PLATFORM"] = "cocoa"
