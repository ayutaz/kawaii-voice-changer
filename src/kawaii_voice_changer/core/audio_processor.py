"""Audio processing module using PyWorld for voice analysis and synthesis."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

import numpy as np
import numpy.typing as npt
import pyworld as pw
import soundfile as sf


class AudioProcessor:
    """Core audio processing class using PyWorld vocoder."""

    def __init__(self, sample_rate: int = 44100) -> None:
        """Initialize audio processor.

        Args:
            sample_rate: Audio sample rate in Hz. Defaults to 44100.
        """
        self.sample_rate = sample_rate
        self.audio_data: npt.NDArray[np.float64] | None = None
        self.original_f0: npt.NDArray[np.float64] | None = None
        self.original_sp: npt.NDArray[np.float64] | None = None
        self.original_ap: npt.NDArray[np.float64] | None = None
        self.time_axis: npt.NDArray[np.float64] | None = None

        # Parameters
        self.f0_ratio = 1.0
        self.formant_ratios = {"f1": 1.0, "f2": 1.0, "f3": 1.0}
        self.formant_link = True  # Formant link mode
        self.bypass_mode = False  # A/B comparison mode

        # Processed audio cache
        self._processed_audio: npt.NDArray[np.float32] | None = None
        self._cache_valid = False

        # Thread safety locks
        self._param_lock = threading.Lock()
        self._cache_lock = threading.Lock()

    def load_audio(self, file_path: str | Path) -> bool:
        """Load and analyze audio file.

        Args:
            file_path: Path to audio file.

        Returns:
            True if successful, False otherwise.
        """
        try:
            file_path = Path(file_path)

            # Load audio file
            self.audio_data, file_sr = sf.read(str(file_path), always_2d=False)

            # Convert stereo to mono if needed
            if len(self.audio_data.shape) > 1:
                self.audio_data = np.mean(self.audio_data, axis=1)

            # Resample if needed
            if file_sr != self.sample_rate:
                ratio = self.sample_rate / file_sr
                new_length = int(len(self.audio_data) * ratio)
                x = np.linspace(0, len(self.audio_data) - 1, new_length)
                self.audio_data = np.interp(
                    x, np.arange(len(self.audio_data)), self.audio_data
                )

            # Analyze with PyWorld
            self._analyze_audio()

            # Invalidate cache
            self._invalidate_cache()

            return True

        except Exception as e:
            print(f"Error loading audio file: {e}")
            return False

    def _analyze_audio(self) -> None:
        """Analyze audio using PyWorld."""
        if self.audio_data is None:
            return

        # Extract F0 (fundamental frequency)
        _f0, t = pw.dio(self.audio_data, self.sample_rate)
        self.original_f0 = pw.stonemask(self.audio_data, _f0, t, self.sample_rate)
        self.time_axis = t

        # Extract spectral envelope
        self.original_sp = pw.cheaptrick(
            self.audio_data, self.original_f0, t, self.sample_rate
        )

        # Extract aperiodicity
        self.original_ap = pw.d4c(
            self.audio_data, self.original_f0, t, self.sample_rate
        )

    def set_f0_ratio(self, ratio: float) -> None:
        """Set fundamental frequency ratio.

        Args:
            ratio: F0 modification ratio (0.5 to 2.0).
        """
        with self._param_lock:
            if self.f0_ratio != ratio:
                self.f0_ratio = np.clip(ratio, 0.5, 2.0)
                self._invalidate_cache()

    def set_formant_ratio(self, formant: str, ratio: float) -> None:
        """Set formant modification ratio.

        Args:
            formant: Formant name ('f1', 'f2', or 'f3').
            ratio: Modification ratio (0.5 to 2.0).
        """
        with self._param_lock:
            if formant in self.formant_ratios:
                old_ratio = self.formant_ratios[formant]
                new_ratio = np.clip(ratio, 0.5, 2.0)

                if old_ratio != new_ratio:
                    self.formant_ratios[formant] = new_ratio

                    # Link mode: apply same ratio to all formants
                    if self.formant_link:
                        for f in self.formant_ratios:
                            self.formant_ratios[f] = new_ratio

                    self._invalidate_cache()

    def set_formant_link(self, linked: bool) -> None:
        """Set formant link mode.

        Args:
            linked: True to link all formants together.
        """
        with self._param_lock:
            self.formant_link = linked
            if linked:
                # Unify all formants to F1 value
                base_ratio = self.formant_ratios["f1"]
                for f in self.formant_ratios:
                    self.formant_ratios[f] = base_ratio
                self._invalidate_cache()

    def set_bypass_mode(self, enabled: bool) -> None:
        """Set bypass mode for A/B comparison.

        Args:
            enabled: True to bypass processing (return original).
        """
        with self._param_lock:
            self.bypass_mode = enabled
            self._invalidate_cache()

    def _shift_formants(
        self, sp: npt.NDArray[np.float64], ratio: float
    ) -> npt.NDArray[np.float64]:
        """Shift formants by scaling spectral envelope in frequency domain.

        Args:
            sp: Spectral envelope.
            ratio: Formant shift ratio.

        Returns:
            Shifted spectral envelope.
        """
        if ratio == 1.0:
            return sp

        shifted_sp = np.zeros_like(sp)
        freq_bins = sp.shape[1]

        for i in range(sp.shape[0]):
            # Frequency axis remapping
            original_freqs = np.arange(freq_bins)
            shifted_freqs = original_freqs / ratio

            # Linear interpolation for new spectral envelope
            shifted_sp[i] = np.interp(
                original_freqs,
                shifted_freqs,
                sp[i],
                left=sp[i, 0],
                right=sp[i, -1],
            )

        return shifted_sp

    def _shift_formants_independent(
        self, sp: npt.NDArray[np.float64]
    ) -> npt.NDArray[np.float64]:
        """Shift formants independently based on frequency bands.

        This method applies different shift ratios to different frequency bands
        corresponding to F1, F2, and F3 formants.

        Args:
            sp: Original spectral envelope.

        Returns:
            Spectral envelope with independent formant shifts.
        """
        # Define formant frequency bands (in Hz)
        # These are approximate ranges for adult speech
        f1_range = (200, 1000)   # F1 typically 200-1000 Hz
        f2_range = (800, 2500)   # F2 typically 800-2500 Hz
        f3_range = (2000, 4000)  # F3 typically 2000-4000 Hz

        # Get frequency axis
        freq_bins = sp.shape[1]
        nyquist = self.sample_rate / 2
        freqs = np.linspace(0, nyquist, freq_bins)

        # Create masks for each formant band
        f1_mask = (freqs >= f1_range[0]) & (freqs <= f1_range[1])
        f2_mask = (freqs >= f2_range[0]) & (freqs <= f2_range[1])
        f3_mask = (freqs >= f3_range[0]) & (freqs <= f3_range[1])

        shifted_sp = np.zeros_like(sp)

        for i in range(sp.shape[0]):
            # Start with original spectrum
            frame_sp = sp[i].copy()

            # Apply shifts to each formant band
            # F1 shift
            if np.any(f1_mask):
                f1_indices = np.where(f1_mask)[0]
                shifted_f1 = self._apply_local_shift(
                    frame_sp, f1_indices, self.formant_ratios["f1"]
                )
                frame_sp[f1_mask] = shifted_f1[f1_mask]

            # F2 shift
            if np.any(f2_mask):
                f2_indices = np.where(f2_mask)[0]
                shifted_f2 = self._apply_local_shift(
                    frame_sp, f2_indices, self.formant_ratios["f2"]
                )
                # Blend with F1 in overlap region
                overlap_mask = f1_mask & f2_mask
                if np.any(overlap_mask):
                    frame_sp[overlap_mask] = (
                        frame_sp[overlap_mask] + shifted_f2[overlap_mask]
                    ) / 2
                else:
                    frame_sp[f2_mask] = shifted_f2[f2_mask]

            # F3 shift
            if np.any(f3_mask):
                f3_indices = np.where(f3_mask)[0]
                shifted_f3 = self._apply_local_shift(
                    frame_sp, f3_indices, self.formant_ratios["f3"]
                )
                # Blend with F2 in overlap region
                overlap_mask = f2_mask & f3_mask
                if np.any(overlap_mask):
                    frame_sp[overlap_mask] = (
                        frame_sp[overlap_mask] + shifted_f3[overlap_mask]
                    ) / 2
                else:
                    frame_sp[f3_mask] = shifted_f3[f3_mask]

            shifted_sp[i] = frame_sp

        return shifted_sp

    def _apply_local_shift(
        self,
        spectrum: npt.NDArray[np.float64],
        indices: npt.NDArray[np.intp],
        ratio: float
    ) -> npt.NDArray[np.float64]:
        """Apply frequency shift to a local region of the spectrum.

        Args:
            spectrum: Full spectrum array.
            indices: Indices of the region to shift.
            ratio: Shift ratio.

        Returns:
            Spectrum with local shift applied.
        """
        if ratio == 1.0:
            return spectrum

        shifted = spectrum.copy()

        # Extract the local region
        local_spectrum = spectrum[indices]

        # Create local frequency mapping
        local_freqs = np.arange(len(local_spectrum))
        shifted_freqs = local_freqs / ratio

        # Interpolate
        shifted_local = np.interp(
            local_freqs,
            shifted_freqs,
            local_spectrum,
            left=local_spectrum[0],
            right=local_spectrum[-1]
        )

        # Apply smoothing at boundaries to avoid discontinuities
        if len(indices) > 10:
            # Create smooth transition at boundaries
            fade_length = min(5, len(indices) // 4)
            fade_in = np.linspace(0, 1, fade_length)
            fade_out = np.linspace(1, 0, fade_length)

            shifted_local[:fade_length] = (
                spectrum[indices[:fade_length]] * (1 - fade_in) +
                shifted_local[:fade_length] * fade_in
            )
            shifted_local[-fade_length:] = (
                spectrum[indices[-fade_length:]] * (1 - fade_out) +
                shifted_local[-fade_length:] * fade_out
            )

        shifted[indices] = shifted_local
        return shifted

    def _process_audio(self) -> npt.NDArray[np.float32]:
        """Process audio with current parameters.

        Returns:
            Processed audio data.
        """
        if self.original_f0 is None or self.audio_data is None:
            return np.array([], dtype=np.float32)

        with self._param_lock:
            # Bypass mode: return original audio
            if self.bypass_mode:
                return self.audio_data.astype(np.float32)
            # Modify F0
            modified_f0 = self.original_f0 * self.f0_ratio

            # Modify spectral envelope (formant shift)
            if self.original_sp is None:
                return np.array([], dtype=np.float32)
            modified_sp = self.original_sp.copy()

            # Apply formant shifts
            if self.formant_link:
                # Linked mode: shift all together
                modified_sp = self._shift_formants(
                    modified_sp, self.formant_ratios["f1"]
                )
            else:
                # Independent mode: shift each formant separately
                modified_sp = self._shift_formants_independent(modified_sp)

            # Synthesize
            synthesized = pw.synthesize(
                modified_f0, modified_sp, self.original_ap, self.sample_rate
            )

            return synthesized.astype(np.float32)  # type: ignore[no-any-return]

    def get_processed_audio(self) -> npt.NDArray[np.float32]:
        """Get processed audio (using cache).

        Returns:
            Processed audio data.
        """
        with self._cache_lock:
            if not self._cache_valid:
                self._processed_audio = self._process_audio()
                self._cache_valid = True

            return (
                self._processed_audio
                if self._processed_audio is not None
                else np.array([], dtype=np.float32)
            )

    def _invalidate_cache(self) -> None:
        """Invalidate processed audio cache."""
        with self._cache_lock:
            self._cache_valid = False

    def get_parameters(self) -> dict[str, Any]:
        """Get current parameters.

        Returns:
            Dictionary of current parameters.
        """
        with self._param_lock:
            return {
                "f0_ratio": self.f0_ratio,
                "formant_ratios": self.formant_ratios.copy(),
                "formant_link": self.formant_link,
            }

    def set_parameters(self, params: dict[str, Any]) -> None:
        """Set parameters from dictionary.

        Args:
            params: Parameter dictionary.
        """
        with self._param_lock:
            if "f0_ratio" in params:
                self.f0_ratio = np.clip(params["f0_ratio"], 0.5, 2.0)

            if "formant_ratios" in params:
                for f, ratio in params["formant_ratios"].items():
                    if f in self.formant_ratios:
                        self.formant_ratios[f] = np.clip(ratio, 0.5, 2.0)

            if "formant_link" in params:
                self.formant_link = params["formant_link"]

            self._invalidate_cache()

    @property
    def duration(self) -> float:
        """Get audio duration in seconds.

        Returns:
            Duration in seconds, or 0 if no audio loaded.
        """
        if self.audio_data is None:
            return 0.0
        return len(self.audio_data) / self.sample_rate

    def export_audio(self, file_path: str | Path, processed: bool = True) -> bool:
        """Export audio to file.

        Args:
            file_path: Output file path.
            processed: Export processed audio if True, original if False.

        Returns:
            True if successful, False otherwise.
        """
        try:
            file_path = Path(file_path)

            if processed:
                audio_data = self.get_processed_audio()
            else:
                if self.audio_data is None:
                    return False
                audio_data = self.audio_data.astype(np.float32)

            if len(audio_data) == 0:
                return False

            # Write audio file
            sf.write(str(file_path), audio_data, self.sample_rate)

            return True

        except Exception as e:
            print(f"Error exporting audio: {e}")
            return False
