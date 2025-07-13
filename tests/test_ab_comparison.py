"""Tests for A/B comparison functionality."""

import numpy as np
import pytest

from kawaii_voice_changer.core import AudioProcessor


class TestABComparison:
    """Test A/B comparison feature."""

    def test_bypass_mode_initialization(self, audio_processor: AudioProcessor) -> None:
        """Test bypass mode is initially disabled."""
        assert audio_processor.bypass_mode is False

    def test_set_bypass_mode(self, audio_processor: AudioProcessor) -> None:
        """Test setting bypass mode."""
        # Enable bypass
        audio_processor.set_bypass_mode(True)
        assert audio_processor.bypass_mode is True
        
        # Disable bypass
        audio_processor.set_bypass_mode(False)
        assert audio_processor.bypass_mode is False

    def test_bypass_returns_original(
        self, audio_processor: AudioProcessor, test_audio: np.ndarray, sample_rate: int
    ) -> None:
        """Test bypass mode returns original audio."""
        # Load test audio
        audio_processor.audio_data = test_audio
        audio_processor.sample_rate = sample_rate
        
        # Create dummy analysis data
        audio_processor.original_f0 = np.ones(100) * 440.0
        audio_processor.original_sp = np.ones((100, 513))
        audio_processor.original_ap = np.ones((100, 513))
        
        # Process without bypass
        audio_processor.set_bypass_mode(False)
        audio_processor.set_f0_ratio(2.0)  # Double pitch
        processed_normal = audio_processor.get_processed_audio()
        
        # Process with bypass
        audio_processor.set_bypass_mode(True)
        processed_bypass = audio_processor.get_processed_audio()
        
        # Bypass should return original audio
        np.testing.assert_array_almost_equal(
            processed_bypass, test_audio.astype(np.float32)
        )
        
        # Normal processing should be different
        with pytest.raises(AssertionError):
            np.testing.assert_array_almost_equal(processed_normal, test_audio)

    def test_bypass_cache_invalidation(
        self, audio_processor: AudioProcessor, test_audio: np.ndarray
    ) -> None:
        """Test cache is invalidated when bypass mode changes."""
        # Setup
        audio_processor.audio_data = test_audio
        audio_processor.original_f0 = np.ones(100) * 440.0
        audio_processor.original_sp = np.ones((100, 513))
        audio_processor.original_ap = np.ones((100, 513))
        
        # Get processed audio to populate cache
        _ = audio_processor.get_processed_audio()
        assert audio_processor._cache_valid is True
        
        # Change bypass mode should invalidate cache
        audio_processor.set_bypass_mode(True)
        assert audio_processor._cache_valid is False
        
        # Get processed audio again
        _ = audio_processor.get_processed_audio()
        assert audio_processor._cache_valid is True
        
        # Change back should invalidate again
        audio_processor.set_bypass_mode(False)
        assert audio_processor._cache_valid is False

    def test_bypass_with_no_audio(self, audio_processor: AudioProcessor) -> None:
        """Test bypass mode with no audio loaded."""
        audio_processor.set_bypass_mode(True)
        result = audio_processor.get_processed_audio()
        assert len(result) == 0
        assert result.dtype == np.float32