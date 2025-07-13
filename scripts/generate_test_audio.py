"""Generate test audio file for development."""

import numpy as np
import soundfile as sf
from pathlib import Path


def generate_sine_sweep(duration: float = 3.0, sample_rate: int = 44100) -> np.ndarray:
    """Generate a sine wave sweep from 100Hz to 1000Hz.
    
    Args:
        duration: Duration in seconds.
        sample_rate: Sample rate in Hz.
        
    Returns:
        Audio data array.
    """
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Frequency sweep
    f_start = 100
    f_end = 1000
    frequency = np.linspace(f_start, f_end, len(t))
    
    # Generate sweep
    phase = 2 * np.pi * np.cumsum(frequency) / sample_rate
    audio = np.sin(phase) * 0.3
    
    # Add envelope
    envelope = np.ones_like(t)
    fade_samples = int(0.1 * sample_rate)  # 100ms fade
    envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
    envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
    
    return audio * envelope


def generate_voice_like_sound(duration: float = 3.0, sample_rate: int = 44100) -> np.ndarray:
    """Generate a simple voice-like sound using formant synthesis.
    
    Args:
        duration: Duration in seconds.
        sample_rate: Sample rate in Hz.
        
    Returns:
        Audio data array.
    """
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Fundamental frequency (varies slightly)
    f0_base = 200  # Female voice range
    f0_variation = 10 * np.sin(2 * np.pi * 3 * t)  # 3Hz vibrato
    f0 = f0_base + f0_variation
    
    # Generate harmonics
    signal = np.zeros_like(t)
    for harmonic in range(1, 10):
        amplitude = 1.0 / harmonic
        phase = 2 * np.pi * np.cumsum(f0 * harmonic) / sample_rate
        signal += amplitude * np.sin(phase)
    
    # Normalize
    signal = signal / np.max(np.abs(signal)) * 0.3
    
    # Simple formant filter simulation (using resonances)
    # This is a very simplified version
    from scipy import signal as scipy_signal
    
    # Formant frequencies for /a/ vowel
    formants = [700, 1200, 2500]  # F1, F2, F3
    filtered = signal.copy()
    
    for formant_freq in formants:
        # Create resonant filter
        Q = 10
        w0 = 2 * np.pi * formant_freq / sample_rate
        b, a = scipy_signal.iirpeak(w0, Q)
        filtered = scipy_signal.filtfilt(b, a, filtered)
    
    # Normalize again
    filtered = filtered / np.max(np.abs(filtered)) * 0.3
    
    return filtered


def main():
    """Generate test audio files."""
    # Create output directory
    output_dir = Path("test_audio")
    output_dir.mkdir(exist_ok=True)
    
    # Generate sine sweep
    print("Generating sine sweep...")
    sweep = generate_sine_sweep()
    sf.write(output_dir / "sine_sweep.wav", sweep, 44100)
    
    # Generate voice-like sound
    print("Generating voice-like sound...")
    voice = generate_voice_like_sound()
    sf.write(output_dir / "voice_test.wav", voice, 44100)
    
    print(f"Test audio files generated in {output_dir}/")


if __name__ == "__main__":
    main()