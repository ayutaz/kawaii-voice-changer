"""Pytest configuration and fixtures."""

import os
from pathlib import Path

import numpy as np
import pytest

# Set Qt to use offscreen platform for CI
if os.environ.get("CI"):
    os.environ["QT_QPA_PLATFORM"] = "offscreen"

from kawaii_voice_changer.core import AudioProcessor


@pytest.fixture
def sample_rate() -> int:
    """Sample rate for tests."""
    return 44100


@pytest.fixture
def test_audio(sample_rate: int) -> np.ndarray:
    """Generate test audio signal."""
    duration = 1.0  # 1 second
    t = np.linspace(0, duration, int(sample_rate * duration))
    # 440Hz sine wave
    return (np.sin(2 * np.pi * 440 * t) * 0.3).astype(np.float32)


@pytest.fixture
def audio_processor(sample_rate: int) -> AudioProcessor:
    """Create AudioProcessor instance."""
    return AudioProcessor(sample_rate=sample_rate)


@pytest.fixture
def temp_audio_file(tmp_path: Path, test_audio: np.ndarray, sample_rate: int) -> Path:
    """Create temporary audio file."""
    import soundfile as sf

    file_path = tmp_path / "test_audio.wav"
    sf.write(str(file_path), test_audio, sample_rate)
    return file_path