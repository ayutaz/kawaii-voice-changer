"""Main entry point for Kawaii Voice Changer application."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from .gui import MainWindow
from .utils import Config, setup_logger

logger = setup_logger("kawaii_voice_changer")


def main() -> int:
    """Main application entry point.

    Returns:
        Exit code.
    """
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Kawaii Voice Changer")
    app.setOrganizationName("ayutaz")
    
    # Set application style
    app.setStyle("Fusion")
    
    # Load configuration
    config_path = Path.home() / ".kawaii_voice_changer" / "config.json"
    config = Config.load(config_path)
    
    # Create and show main window
    window = MainWindow(config)
    window.show()
    
    logger.info("Application started")
    
    # Run application
    result = app.exec()
    
    # Save configuration
    config.save(config_path)
    
    return result


if __name__ == "__main__":
    sys.exit(main())