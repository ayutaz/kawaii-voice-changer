"""Tests for spectrum display widget."""

import numpy as np
import pytest
from PySide6.QtWidgets import QApplication

from kawaii_voice_changer.gui.widgets.spectrum_display import SpectrumDisplay


class TestSpectrumDisplay:
    """Test spectrum display widget."""

    def test_initialization(self, qtbot) -> None:
        """Test spectrum display initialization."""
        widget = SpectrumDisplay()
        qtbot.addWidget(widget)
        
        assert widget.sample_rate == 44100
        assert widget.fft_size == 2048
        assert widget.hop_size == 512
        assert widget.freq_max == 5000
        assert widget.db_range == 80
        assert len(widget.formant_lines) == 3
        assert widget.formant_freqs == [700, 1200, 2500]

    def test_set_audio_data(self, qtbot) -> None:
        """Test setting audio data."""
        widget = SpectrumDisplay()
        qtbot.addWidget(widget)
        
        # Create test audio data
        sample_rate = 44100
        duration = 1.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = np.sin(2 * np.pi * 440 * t).astype(np.float32)
        
        # Set audio data
        widget.set_audio_data(audio_data, sample_rate)
        
        assert widget.audio_buffer is not None
        assert widget.sample_rate == sample_rate
        assert widget.spectrogram_data is not None
        assert widget.update_timer.isActive()

    def test_set_audio_data_none(self, qtbot) -> None:
        """Test clearing audio data."""
        widget = SpectrumDisplay()
        qtbot.addWidget(widget)
        
        # Set to None
        widget.set_audio_data(None, 44100)
        
        assert widget.audio_buffer is None
        assert widget.spectrogram_data is None
        assert not widget.update_timer.isActive()

    def test_set_playback_position(self, qtbot) -> None:
        """Test setting playback position."""
        widget = SpectrumDisplay()
        qtbot.addWidget(widget)
        
        # Create test audio
        sample_rate = 44100
        duration = 1.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = np.sin(2 * np.pi * 440 * t).astype(np.float32)
        
        widget.set_audio_data(audio_data, sample_rate)
        
        # Set position
        widget.set_playback_position(0.5)
        assert widget.current_position == int(0.5 * sample_rate)

    def test_update_formant_markers(self, qtbot) -> None:
        """Test updating formant markers."""
        widget = SpectrumDisplay()
        qtbot.addWidget(widget)
        
        # Update formant frequencies
        widget.update_formant_markers(800.0, 1500.0, 3000.0)
        
        # Check that markers were updated
        assert widget.formant_lines[0].value() == 800.0
        assert widget.formant_lines[1].value() == 1500.0
        assert widget.formant_lines[2].value() == 3000.0

    def test_clear(self, qtbot) -> None:
        """Test clearing display."""
        widget = SpectrumDisplay()
        qtbot.addWidget(widget)
        
        # Set some data first
        sample_rate = 44100
        duration = 0.1
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = np.sin(2 * np.pi * 440 * t).astype(np.float32)
        widget.set_audio_data(audio_data, sample_rate)
        
        # Clear
        widget.clear()
        
        assert widget.audio_buffer is None
        assert widget.spectrogram_data is None
        assert widget.current_position == 0
        assert not widget.update_timer.isActive()

    def test_start_stop_updates(self, qtbot) -> None:
        """Test starting and stopping updates."""
        widget = SpectrumDisplay()
        qtbot.addWidget(widget)
        
        # Set audio data
        sample_rate = 44100
        duration = 0.1
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = np.sin(2 * np.pi * 440 * t).astype(np.float32)
        widget.set_audio_data(audio_data, sample_rate)
        
        # Stop updates
        widget.stop_updates()
        assert not widget.update_timer.isActive()
        
        # Start updates
        widget.start_updates()
        assert widget.update_timer.isActive()