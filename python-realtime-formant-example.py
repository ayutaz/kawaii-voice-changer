#!/usr/bin/env python3
"""
Real-time Formant and Pitch Shifting Example using PyWorld and Sounddevice
For kawaii voice experiments - allows independent control of pitch and formants
"""

import numpy as np
import sounddevice as sd
import pyworld as pw
from scipy import signal
import threading
import queue
import time

class KawaiiVoiceProcessor:
    def __init__(self, 
                 pitch_shift_ratio=1.2,      # 1.2 = up 20%
                 formant_shift_ratio=1.3,    # 1.3 = formants up 30%
                 sample_rate=16000,
                 block_size=512,
                 buffer_size=2048):
        """
        Initialize the kawaii voice processor.
        
        Args:
            pitch_shift_ratio: Ratio for pitch shifting (>1 for higher pitch)
            formant_shift_ratio: Ratio for formant shifting (>1 for higher/younger voice)
            sample_rate: Audio sample rate
            block_size: Processing block size
            buffer_size: Internal buffer size
        """
        self.pitch_shift_ratio = pitch_shift_ratio
        self.formant_shift_ratio = formant_shift_ratio
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.buffer_size = buffer_size
        
        # Processing buffer
        self.input_buffer = np.zeros(buffer_size, dtype=np.float64)
        self.output_buffer = np.zeros(buffer_size, dtype=np.float64)
        
        # Thread-safe queues
        self.input_queue = queue.Queue()
        self.output_queue = queue.Queue()
        
        # Processing thread
        self.processing_thread = None
        self.is_running = False
        
        # Crossfade for smooth transitions
        self.crossfade_samples = 64
        self.prev_output = np.zeros(self.crossfade_samples)
        
    def shift_formants(self, spectral_envelope, ratio):
        """
        Shift formants by manipulating the spectral envelope.
        This preserves the spectral shape while shifting formant frequencies.
        """
        shifted_envelope = np.zeros_like(spectral_envelope)
        
        for i in range(spectral_envelope.shape[0]):
            # Get the current frame's spectrum
            frame_spectrum = spectral_envelope[i]
            
            # Convert to log domain for better manipulation
            log_spectrum = np.log(frame_spectrum + 1e-7)
            
            # Create frequency axis
            freq_bins = len(frame_spectrum)
            original_freqs = np.linspace(0, self.sample_rate/2, freq_bins)
            
            # Shift frequencies
            shifted_freqs = original_freqs / ratio
            
            # Interpolate to get shifted spectrum
            # Only interpolate within valid frequency range
            valid_mask = shifted_freqs < (self.sample_rate/2)
            
            shifted_log_spectrum = np.zeros_like(log_spectrum)
            shifted_log_spectrum[valid_mask] = np.interp(
                shifted_freqs[valid_mask],
                original_freqs,
                log_spectrum
            )
            
            # Convert back from log domain
            shifted_envelope[i] = np.exp(shifted_log_spectrum)
            
        return shifted_envelope
    
    def process_frame(self, audio_frame):
        """
        Process a single audio frame with PyWorld vocoder.
        """
        try:
            # Ensure we have enough samples
            if len(audio_frame) < 512:
                return audio_frame
            
            # PyWorld analysis
            # Extract pitch (F0)
            _f0, t = pw.dio(audio_frame, self.sample_rate, frame_period=5.0)
            f0 = pw.stonemask(audio_frame, _f0, t, self.sample_rate)
            
            # Extract spectral envelope (contains formant information)
            sp = pw.cheaptrick(audio_frame, f0, t, self.sample_rate)
            
            # Extract aperiodic component
            ap = pw.d4c(audio_frame, f0, t, self.sample_rate)
            
            # Apply pitch shifting
            f0_shifted = f0 * self.pitch_shift_ratio
            
            # Apply formant shifting
            sp_shifted = self.shift_formants(sp, self.formant_shift_ratio)
            
            # Synthesize the modified audio
            y = pw.synthesize(f0_shifted, sp_shifted, ap, self.sample_rate)
            
            # Apply crossfade to reduce artifacts
            if len(y) >= self.crossfade_samples:
                fade_in = np.linspace(0, 1, self.crossfade_samples)
                fade_out = np.linspace(1, 0, self.crossfade_samples)
                
                y[:self.crossfade_samples] = (
                    y[:self.crossfade_samples] * fade_in + 
                    self.prev_output * fade_out
                )
                self.prev_output = y[-self.crossfade_samples:].copy()
            
            return y
            
        except Exception as e:
            print(f"Processing error: {e}")
            return audio_frame
    
    def processing_worker(self):
        """
        Background thread for audio processing.
        """
        while self.is_running:
            try:
                # Get input audio chunk with timeout
                audio_chunk = self.input_queue.get(timeout=0.1)
                
                # Update input buffer
                self.input_buffer = np.roll(self.input_buffer, -len(audio_chunk))
                self.input_buffer[-len(audio_chunk):] = audio_chunk
                
                # Process the buffer
                processed = self.process_frame(self.input_buffer)
                
                # Extract the output chunk
                output_chunk = processed[-len(audio_chunk):]
                
                # Put processed audio in output queue
                self.output_queue.put(output_chunk)
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Worker error: {e}")
    
    def audio_callback(self, indata, outdata, frames, time_info, status):
        """
        Sounddevice callback for real-time audio I/O.
        """
        if status:
            print(f"Audio callback status: {status}")
        
        # Convert input to float64 for processing
        audio_in = indata[:, 0].astype(np.float64)
        
        # Put input in processing queue
        self.input_queue.put(audio_in)
        
        # Try to get processed output
        try:
            processed = self.output_queue.get_nowait()
            outdata[:, 0] = processed.astype(np.float32)
        except queue.Empty:
            # If no processed audio available, output silence or pass-through
            outdata[:, 0] = audio_in.astype(np.float32) * 0.1  # Attenuated pass-through
    
    def start(self):
        """
        Start real-time processing.
        """
        print("Starting Kawaii Voice Processor...")
        print(f"Pitch shift ratio: {self.pitch_shift_ratio}")
        print(f"Formant shift ratio: {self.formant_shift_ratio}")
        print(f"Sample rate: {self.sample_rate} Hz")
        print("Press Ctrl+C to stop")
        
        # Start processing thread
        self.is_running = True
        self.processing_thread = threading.Thread(target=self.processing_worker)
        self.processing_thread.start()
        
        # Start audio stream
        with sd.Stream(
            samplerate=self.sample_rate,
            blocksize=self.block_size,
            channels=1,
            callback=self.audio_callback,
            dtype='float32'
        ):
            try:
                while True:
                    time.sleep(0.1)
            except KeyboardInterrupt:
                print("\nStopping...")
        
        # Clean up
        self.is_running = False
        self.processing_thread.join()
        print("Stopped.")

class SimplePitchShifter:
    """
    Simpler alternative using phase vocoder for comparison.
    """
    def __init__(self, pitch_ratio=1.2, sample_rate=44100):
        self.pitch_ratio = pitch_ratio
        self.sample_rate = sample_rate
        self.hop_size = 256
        self.window_size = 2048
        self.window = np.hanning(self.window_size)
        
    def pitch_shift_stft(self, audio):
        """
        Simple pitch shifting using STFT phase vocoder.
        """
        # STFT
        f, t, Zxx = signal.stft(audio, fs=self.sample_rate, 
                                window='hann', nperseg=self.window_size)
        
        # Shift frequencies
        shifted_Zxx = np.zeros_like(Zxx)
        for i in range(Zxx.shape[1]):
            for j in range(Zxx.shape[0]):
                new_bin = int(j / self.pitch_ratio)
                if 0 <= new_bin < Zxx.shape[0]:
                    shifted_Zxx[new_bin, i] = Zxx[j, i]
        
        # ISTFT
        _, shifted_audio = signal.istft(shifted_Zxx, fs=self.sample_rate,
                                       window='hann', nperseg=self.window_size)
        
        return shifted_audio

def main():
    """
    Main function with example usage.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Kawaii Voice Processor')
    parser.add_argument('--pitch', type=float, default=1.2,
                       help='Pitch shift ratio (default: 1.2)')
    parser.add_argument('--formant', type=float, default=1.3,
                       help='Formant shift ratio (default: 1.3)')
    parser.add_argument('--rate', type=int, default=16000,
                       help='Sample rate (default: 16000)')
    parser.add_argument('--simple', action='store_true',
                       help='Use simple pitch shifter instead')
    
    args = parser.parse_args()
    
    if args.simple:
        print("Using simple pitch shifter (no formant control)")
        # Simple demo with just pitch shifting
        shifter = SimplePitchShifter(pitch_ratio=args.pitch)
        
        def simple_callback(indata, outdata, frames, time_info, status):
            outdata[:] = shifter.pitch_shift_stft(indata[:, 0])[:, np.newaxis]
        
        with sd.Stream(callback=simple_callback, channels=1, 
                      samplerate=args.rate, blocksize=2048):
            print("Simple pitch shifter running. Press Ctrl+C to stop.")
            try:
                while True:
                    time.sleep(0.1)
            except KeyboardInterrupt:
                print("\nStopped.")
    else:
        # Full kawaii voice processor
        processor = KawaiiVoiceProcessor(
            pitch_shift_ratio=args.pitch,
            formant_shift_ratio=args.formant,
            sample_rate=args.rate
        )
        processor.start()

if __name__ == "__main__":
    main()