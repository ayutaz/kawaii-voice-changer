"""Tests for formant processing functionality."""

import numpy as np
import pytest

from kawaii_voice_changer.core import AudioProcessor


class TestFormantProcessing:
    """Test formant processing features."""

    def test_independent_formant_mode(
        self, audio_processor: AudioProcessor, test_audio: np.ndarray
    ) -> None:
        """Test independent formant mode processing."""
        # Setup
        audio_processor.audio_data = test_audio.astype(np.float64)
        audio_processor.sample_rate = 44100
        
        # Create dummy analysis data
        frames = 100
        freq_bins = 513
        audio_processor.original_f0 = np.ones(frames) * 440.0
        audio_processor.original_sp = np.ones((frames, freq_bins))
        audio_processor.original_ap = np.ones((frames, freq_bins))
        
        # Set independent mode
        audio_processor.set_formant_link(False)
        
        # Set different ratios for each formant
        audio_processor.set_formant_ratio("f1", 0.8)
        audio_processor.set_formant_ratio("f2", 1.2)
        audio_processor.set_formant_ratio("f3", 1.5)
        
        # Process audio
        result = audio_processor.get_processed_audio()
        
        # Should return processed audio
        assert len(result) > 0
        assert result.dtype == np.float32

    def test_linked_formant_mode(
        self, audio_processor: AudioProcessor, test_audio: np.ndarray
    ) -> None:
        """Test linked formant mode processing."""
        # Setup
        audio_processor.audio_data = test_audio.astype(np.float64)
        audio_processor.sample_rate = 44100
        
        # Create dummy analysis data
        frames = 100
        freq_bins = 513
        audio_processor.original_f0 = np.ones(frames) * 440.0
        audio_processor.original_sp = np.ones((frames, freq_bins))
        audio_processor.original_ap = np.ones((frames, freq_bins))
        
        # Set linked mode
        audio_processor.set_formant_link(True)
        
        # Set different initial ratios
        audio_processor.set_formant_ratio("f1", 0.8)
        audio_processor.set_formant_ratio("f2", 1.2)
        audio_processor.set_formant_ratio("f3", 1.5)
        
        # In linked mode, all should be set to the same value
        assert audio_processor.formant_ratios["f1"] == 1.5
        assert audio_processor.formant_ratios["f2"] == 1.5
        assert audio_processor.formant_ratios["f3"] == 1.5
        
        # Process audio
        result = audio_processor.get_processed_audio()
        
        # Should return processed audio
        assert len(result) > 0
        assert result.dtype == np.float32

    def test_formant_shift_methods(self, audio_processor: AudioProcessor) -> None:
        """Test formant shift helper methods."""
        # Create test spectral envelope
        frames = 10
        freq_bins = 513
        test_sp = np.ones((frames, freq_bins))
        
        # Test basic shift
        shifted = audio_processor._shift_formants(test_sp, 1.5)
        assert shifted.shape == test_sp.shape
        
        # Test no shift (ratio = 1.0)
        no_shift = audio_processor._shift_formants(test_sp, 1.0)
        np.testing.assert_array_equal(no_shift, test_sp)
        
        # Test independent shift
        audio_processor.formant_ratios = {"f1": 0.8, "f2": 1.2, "f3": 1.5}
        independent_shifted = audio_processor._shift_formants_independent(test_sp)
        assert independent_shifted.shape == test_sp.shape

    def test_local_shift_method(self, audio_processor: AudioProcessor) -> None:
        """Test local shift application."""
        # Create test spectrum
        spectrum = np.ones(100)
        indices = np.arange(20, 40)
        
        # Apply shift
        shifted = audio_processor._apply_local_shift(spectrum, indices, 1.5)
        
        # Check that only the specified region was modified
        assert shifted.shape == spectrum.shape
        # Regions outside indices should remain unchanged
        np.testing.assert_array_equal(shifted[:20], spectrum[:20])
        np.testing.assert_array_equal(shifted[40:], spectrum[40:])
        
        # Test no shift
        no_shift = audio_processor._apply_local_shift(spectrum, indices, 1.0)
        np.testing.assert_array_equal(no_shift, spectrum)

    def test_formant_mode_switching(
        self, audio_processor: AudioProcessor, test_audio: np.ndarray
    ) -> None:
        """Test switching between linked and independent modes."""
        # Setup
        audio_processor.audio_data = test_audio.astype(np.float64)
        audio_processor.sample_rate = 44100
        
        # Create more realistic spectral envelope with formant peaks
        frames = 100
        freq_bins = 513
        freqs = np.linspace(0, audio_processor.sample_rate / 2, freq_bins)
        
        # Create spectral envelope with formant peaks
        sp = np.zeros((frames, freq_bins))
        for i in range(frames):
            # Add formant peaks at typical frequencies
            for f_center, bandwidth in [(700, 100), (1200, 150), (2500, 200)]:
                mask = np.exp(-((freqs - f_center) ** 2) / (2 * bandwidth ** 2))
                sp[i] += mask * 10
            sp[i] += 1  # Add baseline
        
        audio_processor.original_f0 = np.ones(frames) * 440.0
        audio_processor.original_sp = sp
        audio_processor.original_ap = np.ones((frames, freq_bins)) * 0.01
        
        # Start in independent mode
        audio_processor.set_formant_link(False)
        audio_processor.set_formant_ratio("f1", 0.7)
        audio_processor.set_formant_ratio("f2", 1.3)
        audio_processor.set_formant_ratio("f3", 1.6)
        
        # Get independent result
        independent_result = audio_processor.get_processed_audio()
        
        # Switch to linked mode
        audio_processor.set_formant_link(True)
        
        # All formants should now be equal to F1's value
        assert audio_processor.formant_ratios["f1"] == 0.7
        assert audio_processor.formant_ratios["f2"] == 0.7
        assert audio_processor.formant_ratios["f3"] == 0.7
        
        # Get linked result
        linked_result = audio_processor.get_processed_audio()
        
        # Results should be different (check RMS difference)
        rms_diff = np.sqrt(np.mean((independent_result - linked_result) ** 2))
        assert rms_diff > 0.001  # Should have noticeable difference