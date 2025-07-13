"""Tests for AudioProcessor module."""

from pathlib import Path

import numpy as np
import pytest

from kawaii_voice_changer.core import AudioProcessor


class TestAudioProcessor:
    """Test AudioProcessor class."""

    def test_initialization(self, audio_processor: AudioProcessor) -> None:
        """Test processor initialization."""
        assert audio_processor.sample_rate == 44100
        assert audio_processor.f0_ratio == 1.0
        assert audio_processor.formant_ratios == {"f1": 1.0, "f2": 1.0, "f3": 1.0}
        assert audio_processor.formant_link is True

    def test_load_audio(
        self, audio_processor: AudioProcessor, temp_audio_file: Path
    ) -> None:
        """Test audio file loading."""
        success = audio_processor.load_audio(temp_audio_file)
        assert success is True
        assert audio_processor.audio_data is not None
        assert len(audio_processor.audio_data) > 0

    def test_set_f0_ratio(self, audio_processor: AudioProcessor) -> None:
        """Test F0 ratio setting."""
        audio_processor.set_f0_ratio(1.5)
        assert audio_processor.f0_ratio == 1.5

        # Test clipping
        audio_processor.set_f0_ratio(3.0)
        assert audio_processor.f0_ratio == 2.0

        audio_processor.set_f0_ratio(0.1)
        assert audio_processor.f0_ratio == 0.5

    def test_set_formant_ratio(self, audio_processor: AudioProcessor) -> None:
        """Test formant ratio setting."""
        audio_processor.set_formant_ratio("f1", 1.3)
        assert audio_processor.formant_ratios["f1"] == 1.3

        # Test link mode
        audio_processor.set_formant_link(True)
        audio_processor.set_formant_ratio("f2", 1.5)
        assert all(r == 1.5 for r in audio_processor.formant_ratios.values())

    def test_get_set_parameters(self, audio_processor: AudioProcessor) -> None:
        """Test parameter getting and setting."""
        params = {
            "f0_ratio": 1.2,
            "formant_ratios": {"f1": 1.3, "f2": 1.4, "f3": 1.5},
            "formant_link": False,
        }
        audio_processor.set_parameters(params)

        retrieved = audio_processor.get_parameters()
        assert retrieved["f0_ratio"] == 1.2
        assert retrieved["formant_ratios"]["f1"] == 1.3
        assert retrieved["formant_link"] is False

    def test_process_audio(
        self,
        audio_processor: AudioProcessor,
        temp_audio_file: Path,
    ) -> None:
        """Test audio processing."""
        audio_processor.load_audio(temp_audio_file)
        audio_processor.set_f0_ratio(1.5)

        processed = audio_processor.get_processed_audio()
        assert len(processed) > 0
        assert isinstance(processed, np.ndarray)
        assert processed.dtype == np.float32

    def test_duration_property(
        self,
        audio_processor: AudioProcessor,
        temp_audio_file: Path,
    ) -> None:
        """Test duration property."""
        assert audio_processor.duration == 0.0

        audio_processor.load_audio(temp_audio_file)
        assert audio_processor.duration > 0.0
        assert abs(audio_processor.duration - 1.0) < 0.1  # ~1 second