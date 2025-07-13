"""Tests for GUI widgets."""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QApplication

from kawaii_voice_changer.gui.widgets import (
    ParameterSlider,
    PlaybackControls,
    WaveformDisplay,
)


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    # Don't quit the app, it might be reused


class TestParameterSlider:
    """Test ParameterSlider widget."""

    def test_initialization(self, qapp, qtbot):
        """Test slider initialization."""
        slider = ParameterSlider("Test Slider", 0.5, 2.0, 1.0, 0.1)
        qtbot.addWidget(slider)
        
        assert slider.value() == 1.0
        assert slider.min_value == 0.5
        assert slider.max_value == 2.0
        assert slider.step == 0.1

    def test_value_change(self, qapp, qtbot):
        """Test value change signal."""
        slider = ParameterSlider("Test", 0.0, 2.0, 1.0, 0.1)
        qtbot.addWidget(slider)
        
        # Create signal spy
        spy = QSignalSpy(slider.value_changed)
        
        # Change value
        slider.set_value(1.5)
        
        # Check signal was emitted
        assert len(spy) == 1
        assert spy[0][0] == pytest.approx(1.5, 0.01)

    def test_value_clamping(self, qapp, qtbot):
        """Test value clamping to range."""
        slider = ParameterSlider("Test", 0.5, 2.0, 1.0, 0.1)
        qtbot.addWidget(slider)
        
        # Test upper bound
        slider.set_value(3.0)
        assert slider.value() == 2.0
        
        # Test lower bound
        slider.set_value(0.1)
        assert slider.value() == 0.5


class TestPlaybackControls:
    """Test PlaybackControls widget."""

    def test_initialization(self, qapp, qtbot):
        """Test playback controls initialization."""
        controls = PlaybackControls()
        qtbot.addWidget(controls)
        
        assert not controls.is_playing
        assert controls.loop_checkbox.isChecked()
        assert controls.volume_slider.value() == 100

    def test_play_button_toggle(self, qapp, qtbot):
        """Test play button state toggle."""
        controls = PlaybackControls()
        qtbot.addWidget(controls)
        
        # Initially not playing
        assert "再生" in controls.play_button.text()
        
        # Set to playing
        controls.set_playing(True)
        assert "一時停止" in controls.play_button.text()
        
        # Set to stopped
        controls.set_playing(False)
        assert "再生" in controls.play_button.text()

    def test_volume_signal(self, qapp, qtbot):
        """Test volume change signal."""
        controls = PlaybackControls()
        qtbot.addWidget(controls)
        
        spy = QSignalSpy(controls.volume_changed)
        
        # Change volume to 50%
        controls.volume_slider.setValue(50)
        
        assert len(spy) == 1
        assert spy[0][0] == pytest.approx(0.5)
        assert controls.volume_label.text() == "50%"

    def test_position_display(self, qapp, qtbot):
        """Test position display update."""
        controls = PlaybackControls()
        qtbot.addWidget(controls)
        
        # Set position
        controls.set_position(65.5, 120.0)
        assert controls.position_label.text() == "1:05 / 2:00"


class TestWaveformDisplay:
    """Test WaveformDisplay widget."""

    def test_initialization(self, qapp, qtbot):
        """Test waveform display initialization."""
        display = WaveformDisplay()
        qtbot.addWidget(display)
        
        assert display.audio_data is None
        assert display.sample_rate == 44100
        assert display.playback_position == 0.0

    def test_set_audio_data(self, qapp, qtbot, test_audio, sample_rate):
        """Test setting audio data."""
        display = WaveformDisplay()
        qtbot.addWidget(display)
        
        display.set_audio_data(test_audio, sample_rate)
        
        assert display.audio_data is not None
        assert len(display.audio_data) == len(test_audio)
        assert display.sample_rate == sample_rate

    def test_playback_position(self, qapp, qtbot):
        """Test playback position update."""
        display = WaveformDisplay()
        qtbot.addWidget(display)
        
        display.set_playback_position(1.5)
        assert display.playback_position == 1.5
        assert display.position_line.pos().x() == 1.5

    def test_clear(self, qapp, qtbot, test_audio, sample_rate):
        """Test clearing display."""
        display = WaveformDisplay()
        qtbot.addWidget(display)
        
        # Set data first
        display.set_audio_data(test_audio, sample_rate)
        display.set_playback_position(1.0)
        
        # Clear
        display.clear()
        assert display.position_line.pos().x() == 0