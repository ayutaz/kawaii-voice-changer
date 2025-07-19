"""Recording control widgets."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from ...core import AudioRecorder, RecorderState
from ...utils import setup_logger

if TYPE_CHECKING:
    pass

logger = setup_logger(__name__)


class RecordingControls(QWidget):
    """Recording control widget."""

    # Signals
    recording_started = Signal(Path)  # Emits output file path
    recording_stopped = Signal(Path)  # Emits saved file path
    recording_state_changed = Signal(RecorderState)

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize recording controls.

        Args:
            parent: Parent widget.
        """
        super().__init__(parent)

        # Audio recorder
        self.recorder = AudioRecorder()
        self.recorder.set_level_callback(self._update_level)

        # Current output file
        self.current_output_file: Path | None = None

        # Timer for duration update
        self.duration_timer = QTimer()
        self.duration_timer.timeout.connect(self._update_duration)
        self.duration_timer.setInterval(100)  # Update every 100ms

        # Setup UI
        self._setup_ui()
        self._update_button_states()

    def _setup_ui(self) -> None:
        """Set up user interface."""
        layout = QVBoxLayout(self)

        # Device selection
        device_group = QGroupBox("Input Device")
        device_layout = QVBoxLayout(device_group)

        self.device_combo = QComboBox()
        self._refresh_devices()
        device_layout.addWidget(self.device_combo)

        refresh_btn = QPushButton("Refresh Devices")
        refresh_btn.clicked.connect(self._refresh_devices)
        device_layout.addWidget(refresh_btn)

        layout.addWidget(device_group)

        # Recording settings
        settings_group = QGroupBox("Recording Settings")
        settings_layout = QVBoxLayout(settings_group)

        # Sample rate
        rate_layout = QHBoxLayout()
        rate_layout.addWidget(QLabel("Sample Rate:"))
        self.sample_rate_combo = QComboBox()
        self.sample_rate_combo.addItems(["44100", "48000", "96000", "192000"])
        self.sample_rate_combo.setCurrentText("44100")
        rate_layout.addWidget(self.sample_rate_combo)
        rate_layout.addWidget(QLabel("Hz"))
        rate_layout.addStretch()
        settings_layout.addLayout(rate_layout)

        # Channels
        channel_layout = QHBoxLayout()
        channel_layout.addWidget(QLabel("Channels:"))
        self.channel_combo = QComboBox()
        self.channel_combo.addItems(["Mono", "Stereo"])
        channel_layout.addWidget(self.channel_combo)
        channel_layout.addStretch()
        settings_layout.addLayout(channel_layout)

        # Input gain
        gain_layout = QHBoxLayout()
        gain_layout.addWidget(QLabel("Input Gain:"))
        self.gain_slider = QSlider()
        self.gain_slider.setOrientation(Qt.Orientation.Horizontal)
        self.gain_slider.setRange(0, 200)  # 0-200%
        self.gain_slider.setValue(100)
        self.gain_slider.valueChanged.connect(self._update_gain)
        gain_layout.addWidget(self.gain_slider)
        self.gain_label = QLabel("100%")
        gain_layout.addWidget(self.gain_label)
        settings_layout.addLayout(gain_layout)

        layout.addWidget(settings_group)

        # Recording controls
        control_group = QGroupBox("Recording")
        control_layout = QVBoxLayout(control_group)

        # Buttons
        button_layout = QHBoxLayout()
        self.record_button = QPushButton("Record")
        self.record_button.clicked.connect(self._toggle_recording)
        button_layout.addWidget(self.record_button)

        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self._toggle_pause)
        self.pause_button.setEnabled(False)
        button_layout.addWidget(self.pause_button)

        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self._stop_recording)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)

        control_layout.addLayout(button_layout)

        # Duration display
        duration_layout = QHBoxLayout()
        duration_layout.addWidget(QLabel("Duration:"))
        self.duration_label = QLabel("00:00:00")
        self.duration_label.setStyleSheet("font-family: monospace; font-size: 14px;")
        duration_layout.addWidget(self.duration_label)
        duration_layout.addStretch()
        control_layout.addLayout(duration_layout)

        # Level meter
        level_layout = QVBoxLayout()
        level_layout.addWidget(QLabel("Input Level:"))
        self.level_bar = QProgressBar()
        self.level_bar.setRange(0, 100)
        self.level_bar.setValue(0)
        level_layout.addWidget(self.level_bar)
        control_layout.addLayout(level_layout)

        layout.addWidget(control_group)

        # Output directory
        output_group = QGroupBox("Output")
        output_layout = QVBoxLayout(output_group)

        dir_layout = QHBoxLayout()
        self.output_dir_label = QLabel(str(Path.cwd()))
        dir_layout.addWidget(self.output_dir_label)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_output_dir)
        dir_layout.addWidget(browse_btn)

        output_layout.addLayout(dir_layout)
        layout.addWidget(output_group)

        layout.addStretch()

    def _refresh_devices(self) -> None:
        """Refresh input device list."""
        self.device_combo.clear()

        devices = AudioRecorder.get_input_devices()
        for device in devices:
            text = device["name"]
            if device["is_default"]:
                text += " (Default)"
            self.device_combo.addItem(text, device["index"])

        # Select default device
        for i, device in enumerate(devices):
            if device["is_default"]:
                self.device_combo.setCurrentIndex(i)
                break

    def _update_gain(self, value: int) -> None:
        """Update input gain.

        Args:
            value: Slider value (0-200).
        """
        gain = value / 100.0
        self.recorder.settings.gain = gain
        self.gain_label.setText(f"{value}%")

    def _update_level(self, level: float) -> None:
        """Update level meter.

        Args:
            level: RMS level (0.0-1.0).
        """
        # Convert to percentage
        percent = int(level * 100)
        self.level_bar.setValue(percent)

    def _update_duration(self) -> None:
        """Update duration display."""
        duration = self.recorder.get_recording_duration()
        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        seconds = int(duration % 60)
        self.duration_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")

    def _update_button_states(self) -> None:
        """Update button states based on recorder state."""
        state = self.recorder.state

        if state == RecorderState.IDLE:
            self.record_button.setText("Record")
            self.record_button.setEnabled(True)
            self.pause_button.setEnabled(False)
            self.stop_button.setEnabled(False)
            self.device_combo.setEnabled(True)
            self.sample_rate_combo.setEnabled(True)
            self.channel_combo.setEnabled(True)

        elif state == RecorderState.RECORDING:
            self.record_button.setText("Recording...")
            self.record_button.setEnabled(False)
            self.pause_button.setText("Pause")
            self.pause_button.setEnabled(True)
            self.stop_button.setEnabled(True)
            self.device_combo.setEnabled(False)
            self.sample_rate_combo.setEnabled(False)
            self.channel_combo.setEnabled(False)

        elif state == RecorderState.PAUSED:
            self.record_button.setText("Resume")
            self.record_button.setEnabled(True)
            self.pause_button.setText("Paused")
            self.pause_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.device_combo.setEnabled(False)
            self.sample_rate_combo.setEnabled(False)
            self.channel_combo.setEnabled(False)

    def _toggle_recording(self) -> None:
        """Toggle recording start/resume."""
        if self.recorder.state == RecorderState.IDLE:
            # Apply settings
            device_index = self.device_combo.currentData()
            self.recorder.settings.device = device_index
            self.recorder.settings.sample_rate = int(self.sample_rate_combo.currentText())
            self.recorder.settings.channels = 1 if self.channel_combo.currentIndex() == 0 else 2

            # Start recording
            output_dir = Path(self.output_dir_label.text())
            self.current_output_file = self.recorder.start_recording(output_dir)

            if self.current_output_file:
                self.duration_timer.start()
                self.recording_started.emit(self.current_output_file)
                self.recording_state_changed.emit(RecorderState.RECORDING)
                logger.info(f"Started recording to {self.current_output_file}")
            else:
                QMessageBox.warning(self, "Recording Error", "Failed to start recording")

        elif self.recorder.state == RecorderState.PAUSED:
            # Resume recording
            self.recorder.start_recording()
            self.duration_timer.start()
            self.recording_state_changed.emit(RecorderState.RECORDING)

        self._update_button_states()

    def _toggle_pause(self) -> None:
        """Toggle recording pause."""
        if self.recorder.pause_recording():
            self.duration_timer.stop()
            self.recording_state_changed.emit(RecorderState.PAUSED)
            self._update_button_states()

    def _stop_recording(self) -> None:
        """Stop recording."""
        saved_file = self.recorder.stop_recording(self.current_output_file)
        self.duration_timer.stop()

        if saved_file:
            self.recording_stopped.emit(saved_file)
            self.recording_state_changed.emit(RecorderState.IDLE)
            QMessageBox.information(
                self,
                "Recording Saved",
                f"Recording saved to:\n{saved_file}"
            )
            logger.info(f"Stopped recording, saved to {saved_file}")

        # Reset duration
        self.duration_label.setText("00:00:00")
        self.current_output_file = None
        self._update_button_states()

    def _browse_output_dir(self) -> None:
        """Browse for output directory."""
        current_dir = Path(self.output_dir_label.text())
        new_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            str(current_dir),
            QFileDialog.Option.ShowDirsOnly
        )

        if new_dir:
            self.output_dir_label.setText(new_dir)
