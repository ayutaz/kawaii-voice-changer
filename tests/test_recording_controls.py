"""Tests for recording controls widget."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton

from kawaii_voice_changer.core import RecorderState
from kawaii_voice_changer.gui.widgets import RecordingControls


@pytest.fixture
def recording_controls(qtbot) -> RecordingControls:
    """Create recording controls widget."""
    widget = RecordingControls()
    qtbot.addWidget(widget)
    return widget


class TestRecordingControls:
    """Test recording controls widget."""

    def test_initial_state(self, recording_controls: RecordingControls) -> None:
        """Test initial widget state."""
        # Check buttons
        assert recording_controls.record_button.isEnabled()
        assert not recording_controls.pause_button.isEnabled()
        assert not recording_controls.stop_button.isEnabled()

        # Check controls
        assert recording_controls.device_combo.isEnabled()
        assert recording_controls.sample_rate_combo.isEnabled()
        assert recording_controls.channel_combo.isEnabled()

        # Check defaults
        assert recording_controls.sample_rate_combo.currentText() == "44100"
        assert recording_controls.channel_combo.currentText() == "Mono"
        assert recording_controls.gain_slider.value() == 100

    @patch("kawaii_voice_changer.core.AudioRecorder.get_input_devices")
    def test_refresh_devices(
        self,
        mock_get_devices: MagicMock,
        recording_controls: RecordingControls,
        qtbot,
    ) -> None:
        """Test device refresh."""
        # Mock device list
        mock_get_devices.return_value = [
            {
                "index": 0,
                "name": "Device 1",
                "channels": 2,
                "sample_rate": 44100,
                "is_default": True,
            },
            {
                "index": 1,
                "name": "Device 2",
                "channels": 1,
                "sample_rate": 48000,
                "is_default": False,
            },
        ]

        # Refresh devices
        for button in recording_controls.findChildren(QPushButton):
            if button.text() == "Refresh Devices":
                qtbot.mouseClick(button, Qt.MouseButton.LeftButton)
                break

        # Check combo box
        assert recording_controls.device_combo.count() == 2
        assert "Device 1 (Default)" in recording_controls.device_combo.itemText(0)
        assert recording_controls.device_combo.itemText(1) == "Device 2"
        assert recording_controls.device_combo.currentIndex() == 0

    def test_gain_control(self, recording_controls: RecordingControls) -> None:
        """Test gain control."""
        # Change gain
        recording_controls.gain_slider.setValue(150)

        assert recording_controls.gain_label.text() == "150%"
        assert recording_controls.recorder.settings.gain == 1.5

    def test_level_meter_update(self, recording_controls: RecordingControls) -> None:
        """Test level meter update."""
        # Simulate level update
        recording_controls._update_level(0.75)

        assert recording_controls.level_bar.value() == 75

    def test_duration_display(self, recording_controls: RecordingControls) -> None:
        """Test duration display update."""
        # Mock recording duration
        recording_controls.recorder.get_recording_duration = MagicMock(
            return_value=3665.5
        )  # 1h 1m 5s

        recording_controls._update_duration()

        assert recording_controls.duration_label.text() == "01:01:05"

    @patch("kawaii_voice_changer.core.AudioRecorder.start_recording")
    def test_start_recording(
        self,
        mock_start_recording: MagicMock,
        recording_controls: RecordingControls,
        qtbot,
        tmp_path: Path,
    ) -> None:
        """Test starting recording."""
        # Mock successful recording start
        output_file = tmp_path / "test_recording.wav"
        mock_start_recording.return_value = output_file

        # Set recorder state manually (since we're mocking)
        recording_controls.recorder.state = RecorderState.IDLE

        # Click record button
        qtbot.mouseClick(recording_controls.record_button, Qt.MouseButton.LeftButton)

        # Update state manually
        recording_controls.recorder.state = RecorderState.RECORDING
        recording_controls._update_button_states()

        # Check button states
        assert not recording_controls.record_button.isEnabled()
        assert recording_controls.pause_button.isEnabled()
        assert recording_controls.stop_button.isEnabled()

        # Check settings are disabled
        assert not recording_controls.device_combo.isEnabled()
        assert not recording_controls.sample_rate_combo.isEnabled()
        assert not recording_controls.channel_combo.isEnabled()

    def test_button_state_transitions(
        self, recording_controls: RecordingControls
    ) -> None:
        """Test button state transitions."""
        # Idle state
        recording_controls.recorder.state = RecorderState.IDLE
        recording_controls._update_button_states()

        assert recording_controls.record_button.text() == "Record"
        assert recording_controls.record_button.isEnabled()

        # Recording state
        recording_controls.recorder.state = RecorderState.RECORDING
        recording_controls._update_button_states()

        assert recording_controls.record_button.text() == "Recording..."
        assert not recording_controls.record_button.isEnabled()
        assert recording_controls.pause_button.text() == "Pause"
        assert recording_controls.pause_button.isEnabled()

        # Paused state
        recording_controls.recorder.state = RecorderState.PAUSED
        recording_controls._update_button_states()

        assert recording_controls.record_button.text() == "Resume"
        assert recording_controls.record_button.isEnabled()
        assert recording_controls.pause_button.text() == "Paused"
        assert not recording_controls.pause_button.isEnabled()

    @patch("PySide6.QtWidgets.QFileDialog.getExistingDirectory")
    def test_browse_output_directory(
        self,
        mock_dialog: MagicMock,
        recording_controls: RecordingControls,
        qtbot,
        tmp_path: Path,
    ) -> None:
        """Test browsing for output directory."""
        # Mock dialog return
        new_dir = str(tmp_path / "recordings")
        mock_dialog.return_value = new_dir

        # Find and click browse button
        for button in recording_controls.findChildren(QPushButton):
            if button.text() == "Browse...":
                qtbot.mouseClick(button, Qt.MouseButton.LeftButton)
                break

        assert recording_controls.output_dir_label.text() == new_dir
