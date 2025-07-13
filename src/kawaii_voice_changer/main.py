"""Main entry point for Kawaii Voice Changer application."""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

from PySide6.QtCore import QtMsgType, qInstallMessageHandler
from PySide6.QtWidgets import QApplication, QMessageBox

from .gui import MainWindow
from .utils import Config, setup_logger

logger = setup_logger("kawaii_voice_changer")


def qt_message_handler(msg_type: QtMsgType, context, msg: str) -> None:  # noqa: ARG001
    """Handle Qt messages.

    Args:
        msg_type: Message type.
        context: Message context.
        msg: Message text.
    """
    if msg_type == QtMsgType.QtDebugMsg:
        logger.debug(f"Qt: {msg}")
    elif msg_type == QtMsgType.QtInfoMsg:
        logger.info(f"Qt: {msg}")
    elif msg_type == QtMsgType.QtWarningMsg:
        logger.warning(f"Qt: {msg}")
    elif msg_type == QtMsgType.QtCriticalMsg:
        logger.error(f"Qt: {msg}")
    elif msg_type == QtMsgType.QtFatalMsg:
        logger.critical(f"Qt: {msg}")


def main() -> int:
    """Main application entry point.

    Returns:
        Exit code.
    """
    try:
        # Install Qt message handler
        qInstallMessageHandler(qt_message_handler)

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

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        logger.error(traceback.format_exc())

        # Show error dialog if possible
        try:
            app = QApplication.instance()
            if app:
                QMessageBox.critical(
                    None,
                    "Fatal Error",
                    f"An unexpected error occurred:\n\n{str(e)}\n\n"
                    "Please check the log file for details.",
                )
        except Exception:  # noqa: S110
            pass

        return 1


if __name__ == "__main__":
    sys.exit(main())
