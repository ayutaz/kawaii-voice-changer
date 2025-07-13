"""Tests for audio player functionality."""

import numpy as np
import pytest

from kawaii_voice_changer.core import AudioPlayer, AudioProcessor


class TestAudioPlayer:
    """Test AudioPlayer class."""

    @pytest.fixture
    def processor(self) -> AudioProcessor:
        """Create test processor."""
        proc = AudioProcessor(sample_rate=44100)
        # Create test audio
        duration = 3.0
        t = np.linspace(0, duration, int(44100 * duration))
        audio = np.sin(2 * np.pi * 440 * t) * 0.5
        proc.audio_data = audio
        proc._process_audio()
        return proc

    @pytest.fixture
    def player(self, processor: AudioProcessor) -> AudioPlayer:
        """Create test player."""
        return AudioPlayer(processor, buffer_size=512)

    def test_initialization(
        self, player: AudioPlayer, processor: AudioProcessor
    ) -> None:
        """Test player initialization."""
        assert player.processor is processor
        assert player.buffer_size == 512
        assert not player.is_playing
        assert player.loop_enabled
        assert player.loop_start == 0
        assert player.loop_end == 0
        assert player.loop_crossfade_ms == 50
        assert player.volume == 1.0
        assert player.play_position == 0

    def test_set_volume(self, player: AudioPlayer) -> None:
        """Test volume control."""
        player.set_volume(0.5)
        assert player.volume == 0.5

        # Test clipping
        player.set_volume(1.5)
        assert player.volume == 1.0

        player.set_volume(-0.5)
        assert player.volume == 0.0

    def test_set_loop(self, player: AudioPlayer) -> None:
        """Test loop control."""
        player.set_loop(False)
        assert not player.loop_enabled

        player.set_loop(True)
        assert player.loop_enabled

    def test_set_loop_crossfade(self, player: AudioPlayer) -> None:
        """Test loop crossfade control."""
        player.set_loop_crossfade(100)
        assert player.get_loop_crossfade() == 100

        # Test clipping
        player.set_loop_crossfade(600)
        assert player.get_loop_crossfade() == 500

        player.set_loop_crossfade(-50)
        assert player.get_loop_crossfade() == 0

    def test_set_loop_region(
        self, player: AudioPlayer, processor: AudioProcessor
    ) -> None:
        """Test loop region setting."""
        # Set loop region
        player.set_loop_region(1.0, 2.0)

        # Get effective sample rate
        processed_audio = processor.get_processed_audio()
        if len(processed_audio) > 0:
            audio_length = len(processed_audio)
            effective_sample_rate = audio_length / processor.duration

            # Check loop boundaries
            expected_start = int(1.0 * effective_sample_rate)
            expected_end = int(2.0 * effective_sample_rate)

            assert player.loop_start == expected_start
            assert player.loop_end == expected_end

            # Test invalid region (end < start)
            player.set_loop_region(2.0, 1.0)
            assert player.loop_start < player.loop_end
        else:
            # No processed audio
            assert player.loop_start == 0
            assert player.loop_end == 0

    def test_get_loop_region(
        self, player: AudioPlayer, processor: AudioProcessor
    ) -> None:
        """Test getting loop region."""
        # Get processed audio to check if available
        processed_audio = processor.get_processed_audio()
        if len(processed_audio) > 0:
            # Set loop region
            player.set_loop_region(1.0, 2.0)

            # Get loop region
            start, end = player.get_loop_region()

            # Should be close to original values (may differ slightly due to sample rate conversion)
            assert abs(start - 1.0) < 0.01
            assert abs(end - 2.0) < 0.01
        else:
            # No processed audio, loop region should be 0
            start, end = player.get_loop_region()
            assert start == 0.0
            assert end == 0.0

    def test_clear_loop_region(self, player: AudioPlayer) -> None:
        """Test clearing loop region."""
        # Set loop region
        player.set_loop_region(1.0, 2.0)

        # Clear
        player.clear_loop_region()
        assert player.loop_start == 0
        assert player.loop_end == 0

    def test_seek(self, player: AudioPlayer, processor: AudioProcessor) -> None:
        """Test seek functionality."""
        # Get processed audio length
        processed_audio = processor.get_processed_audio()

        if len(processed_audio) > 0:
            # Seek to middle
            player.seek(1.5)

            # Position should be updated (with some tolerance for rounding)
            position = player.get_position()
            assert abs(position - 1.5) < 0.1

            # Test bounds
            player.seek(-1.0)
            assert player.play_position == 0

            player.seek(10.0)
            assert player.play_position < len(processed_audio)

    def test_playback_control(self, player: AudioPlayer) -> None:
        """Test playback control methods."""
        try:
            # Start should set is_playing
            player.start()
            assert player.is_playing

            # Stop should clear is_playing and reset position
            player.play_position = 1000
            player.stop()
            assert not player.is_playing
            assert player.play_position == 0

            # Cleanup
            if player.stream:
                player.stream.close()
        except Exception as e:
            # Skip test if no audio device available (common in CI)
            if "Error querying device" in str(e):
                pytest.skip("No audio device available in test environment")
            else:
                raise
