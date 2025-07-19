"""Tests for audio recorder functionality."""

from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
import sounddevice as sd

from kawaii_voice_changer.core import AudioRecorder, RecorderState, RecordingSettings


class TestAudioRecorder:
    """Test audio recorder class."""

    @pytest.fixture
    def recorder(self) -> AudioRecorder:
        """Create audio recorder instance."""
        return AudioRecorder()

    @pytest.fixture
    def temp_dir(self, tmp_path: Path) -> Path:
        """Create temporary directory for recordings."""
        return tmp_path

    def test_initial_state(self, recorder: AudioRecorder) -> None:
        """Test initial recorder state."""
        assert recorder.state == RecorderState.IDLE
        assert recorder.get_recording_duration() == 0.0

    @patch("sounddevice.query_devices")
    def test_get_input_devices(self, mock_query_devices: MagicMock) -> None:
        """Test getting input devices."""
        # Mock device list
        mock_query_devices.return_value = [
            {
                "name": "Built-in Microphone",
                "max_input_channels": 2,
                "max_output_channels": 0,
                "default_samplerate": 44100.0,
            },
            {
                "name": "USB Audio Device",
                "max_input_channels": 1,
                "max_output_channels": 2,
                "default_samplerate": 48000.0,
            },
            {
                "name": "Output Only Device",
                "max_input_channels": 0,
                "max_output_channels": 2,
                "default_samplerate": 44100.0,
            },
        ]

        devices = AudioRecorder.get_input_devices()

        # Should only return input-capable devices
        assert len(devices) == 2
        assert devices[0]["name"] == "Built-in Microphone"
        assert devices[0]["channels"] == 2
        assert devices[1]["name"] == "USB Audio Device"
        assert devices[1]["channels"] == 1

    def test_recording_settings(self) -> None:
        """Test recording settings."""
        settings = RecordingSettings(
            sample_rate=48000,
            channels=2,
            dtype="float32",
            device=1,
            gain=1.5,
        )

        recorder = AudioRecorder(settings)
        assert recorder.settings.sample_rate == 48000
        assert recorder.settings.channels == 2
        assert recorder.settings.gain == 1.5

    @patch("sounddevice.InputStream")
    def test_start_recording(
        self,
        mock_stream_class: MagicMock,
        recorder: AudioRecorder,
        temp_dir: Path,
    ) -> None:
        """Test starting recording."""
        # Mock stream
        mock_stream = MagicMock()
        mock_stream_class.return_value = mock_stream

        # Start recording
        output_file = recorder.start_recording(temp_dir)

        assert output_file is not None
        assert output_file.parent == temp_dir
        assert output_file.suffix == ".wav"
        assert recorder.state == RecorderState.RECORDING

        # Verify stream was started
        mock_stream.start.assert_called_once()

    @patch("sounddevice.InputStream")
    def test_pause_resume_recording(
        self,
        mock_stream_class: MagicMock,
        recorder: AudioRecorder,
        temp_dir: Path,
    ) -> None:
        """Test pause and resume recording."""
        # Mock stream
        mock_stream = MagicMock()
        mock_stream_class.return_value = mock_stream

        # Start recording
        recorder.start_recording(temp_dir)
        assert recorder.state == RecorderState.RECORDING

        # Pause
        assert recorder.pause_recording() is True
        assert recorder.state == RecorderState.PAUSED

        # Resume
        recorder.start_recording()  # Resume doesn't need output_dir
        assert recorder.state == RecorderState.RECORDING

    @patch("sounddevice.InputStream")
    @patch("soundfile.write")
    def test_stop_recording(
        self,
        mock_sf_write: MagicMock,
        mock_stream_class: MagicMock,
        recorder: AudioRecorder,
        temp_dir: Path,
    ) -> None:
        """Test stopping recording."""
        # Mock stream
        mock_stream = MagicMock()
        mock_stream_class.return_value = mock_stream

        # Start recording
        output_file = recorder.start_recording(temp_dir)

        # Add some fake recording data after starting
        recorder._recording_data = [
            np.random.rand(1024).astype(np.float32),
            np.random.rand(1024).astype(np.float32),
        ]

        # Stop recording
        saved_file = recorder.stop_recording(output_file)

        assert saved_file == output_file
        assert recorder.state == RecorderState.IDLE

        # Verify stream was stopped
        mock_stream.stop.assert_called_once()
        mock_stream.close.assert_called_once()

        # Verify file was saved
        mock_sf_write.assert_called_once()

    def test_level_callback(self, recorder: AudioRecorder) -> None:
        """Test level callback functionality."""
        level_values = []

        def callback(level: float) -> None:
            level_values.append(level)

        recorder.set_level_callback(callback)

        # Simulate audio callback
        test_data = np.array([0.5, -0.5, 0.3, -0.3], dtype=np.float32)
        recorder.state = RecorderState.RECORDING
        recorder._audio_callback(test_data, len(test_data), None, sd.CallbackFlags())

        # Check callback was called
        assert len(level_values) == 1
        assert 0.0 <= level_values[0] <= 1.0

    def test_recording_duration(self, recorder: AudioRecorder) -> None:
        """Test recording duration calculation."""
        # Not recording
        assert recorder.get_recording_duration() == 0.0

        # Mock recording start time
        recorder._start_time = time.time() - 5.0  # Started 5 seconds ago
        recorder.state = RecorderState.RECORDING

        duration = recorder.get_recording_duration()
        assert 4.9 <= duration <= 5.1  # Allow small timing variance

        # Test with pause
        recorder._pause_time = time.time() - 2.0  # Paused 2 seconds ago
        recorder._total_pause_duration = 1.0  # Was paused for 1 second before
        recorder.state = RecorderState.PAUSED

        duration = recorder.get_recording_duration()
        assert 1.9 <= duration <= 2.1  # 3 seconds recording - 1 second pause
