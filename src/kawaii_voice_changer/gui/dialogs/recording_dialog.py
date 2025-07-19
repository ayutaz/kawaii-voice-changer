"""Recording dialog window."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QDialog, QVBoxLayout

from ...utils import setup_logger
from ..widgets import RecordingControls

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

logger = setup_logger(__name__)


class RecordingDialog(QDialog):
    """Recording dialog window."""

    # Signals
    recording_completed = Signal(Path)  # Emits saved file path

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize recording dialog.

        Args:
            parent: Parent widget.
        """
        super().__init__(parent)

        self.setWindowTitle("録音")
        self.setModal(False)  # Non-modal to allow using main window
        self.setMinimumSize(400, 600)

        # Setup UI
        self._setup_ui()

        # Connect signals
        self._setup_connections()

        logger.info("Recording dialog initialized")

    def _setup_ui(self) -> None:
        """Set up user interface."""
        layout = QVBoxLayout(self)

        # Add recording controls
        self.recording_controls = RecordingControls()
        layout.addWidget(self.recording_controls)

    def _setup_connections(self) -> None:
        """Set up signal connections."""
        # Forward recording stopped signal
        self.recording_controls.recording_stopped.connect(self._on_recording_stopped)

    def _on_recording_stopped(self, file_path: Path) -> None:
        """Handle recording stopped.

        Args:
            file_path: Path to saved recording.
        """
        self.recording_completed.emit(file_path)
        logger.info(f"Recording completed: {file_path}")
