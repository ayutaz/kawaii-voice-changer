"""Tests for audio export functionality."""

import numpy as np
import pytest
import soundfile as sf
from pathlib import Path

from kawaii_voice_changer.core import AudioProcessor


class TestAudioExport:
    """Test audio export functionality."""

    def test_export_processed_audio(
        self, audio_processor: AudioProcessor, test_audio: np.ndarray, tmp_path: Path
    ) -> None:
        """Test exporting processed audio."""
        # Setup
        audio_processor.audio_data = test_audio.astype(np.float64)
        audio_processor.sample_rate = 44100
        audio_processor.original_f0 = np.ones(100) * 440.0
        audio_processor.original_sp = np.ones((100, 513))
        audio_processor.original_ap = np.ones((100, 513))
        
        # Set parameters
        audio_processor.set_f0_ratio(1.5)
        
        # Export
        output_path = tmp_path / "processed.wav"
        result = audio_processor.export_audio(output_path, processed=True)
        
        assert result is True
        assert output_path.exists()
        
        # Verify exported file
        data, sr = sf.read(str(output_path))
        assert sr == audio_processor.sample_rate
        assert len(data) > 0

    def test_export_original_audio(
        self, audio_processor: AudioProcessor, test_audio: np.ndarray, tmp_path: Path
    ) -> None:
        """Test exporting original audio."""
        # Setup
        audio_processor.audio_data = test_audio.astype(np.float64)
        audio_processor.sample_rate = 44100
        
        # Export original
        output_path = tmp_path / "original.wav"
        result = audio_processor.export_audio(output_path, processed=False)
        
        assert result is True
        assert output_path.exists()
        
        # Verify exported file matches original
        data, sr = sf.read(str(output_path))
        assert sr == audio_processor.sample_rate
        np.testing.assert_allclose(data, test_audio.astype(np.float32), rtol=1e-4, atol=1e-4)

    def test_export_with_no_audio(
        self, audio_processor: AudioProcessor, tmp_path: Path
    ) -> None:
        """Test export with no audio loaded."""
        output_path = tmp_path / "empty.wav"
        result = audio_processor.export_audio(output_path)
        
        assert result is False
        assert not output_path.exists()

    def test_export_with_bypass_mode(
        self, audio_processor: AudioProcessor, test_audio: np.ndarray, tmp_path: Path
    ) -> None:
        """Test export respects bypass mode."""
        # Setup
        audio_processor.audio_data = test_audio.astype(np.float64)
        audio_processor.sample_rate = 44100
        audio_processor.original_f0 = np.ones(100) * 440.0
        audio_processor.original_sp = np.ones((100, 513))
        audio_processor.original_ap = np.ones((100, 513))
        
        # Enable bypass mode
        audio_processor.set_bypass_mode(True)
        
        # Export "processed" audio (should be original due to bypass)
        output_path = tmp_path / "bypass.wav"
        result = audio_processor.export_audio(output_path, processed=True)
        
        assert result is True
        
        # Should match original audio
        data, _ = sf.read(str(output_path))
        np.testing.assert_allclose(data, test_audio.astype(np.float32), rtol=1e-4, atol=1e-4)

    def test_export_invalid_path(
        self, audio_processor: AudioProcessor, test_audio: np.ndarray
    ) -> None:
        """Test export with invalid path."""
        # Setup
        audio_processor.audio_data = test_audio.astype(np.float64)
        
        # Try to export to invalid path
        result = audio_processor.export_audio("/invalid/path/that/does/not/exist.wav")
        
        assert result is False