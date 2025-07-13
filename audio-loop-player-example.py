#!/usr/bin/env python3
"""
Audio Loop Player with Real-time Formant/Pitch Processing
Demonstrates how to play audio loops while applying kawaii voice effects
"""

import numpy as np
import sounddevice as sd
import soundfile as sf
import pyworld as pw
import threading
import queue
import time
from pathlib import Path

class AudioLoopProcessor:
    def __init__(self, 
                 loop_file=None,
                 pitch_shift_ratio=1.0,
                 formant_shift_ratio=1.0,
                 sample_rate=44100,
                 block_size=512):
        """
        Initialize audio loop player with real-time processing.
        
        Args:
            loop_file: Path to audio file to loop (WAV format recommended)
            pitch_shift_ratio: Pitch modification ratio
            formant_shift_ratio: Formant modification ratio
            sample_rate: Sample rate for playback
            block_size: Audio block size for processing
        """
        self.pitch_shift_ratio = pitch_shift_ratio
        self.formant_shift_ratio = formant_shift_ratio
        self.sample_rate = sample_rate
        self.block_size = block_size
        
        # Load audio loop if provided
        self.loop_audio = None
        self.loop_position = 0
        if loop_file:
            self.load_loop(loop_file)
        
        # Processing queues
        self.input_queue = queue.Queue()
        self.output_queue = queue.Queue()
        
        # Control flags
        self.is_running = False
        self.loop_enabled = True
        self.process_enabled = True
        
        # Mix controls
        self.dry_wet_mix = 1.0  # 0 = dry, 1 = wet
        self.loop_volume = 0.5
        self.mic_volume = 0.5
        
    def load_loop(self, file_path):
        """Load an audio file for looping."""
        try:
            self.loop_audio, file_sr = sf.read(file_path)
            
            # Convert to mono if stereo
            if len(self.loop_audio.shape) > 1:
                self.loop_audio = np.mean(self.loop_audio, axis=1)
            
            # Resample if necessary
            if file_sr != self.sample_rate:
                # Simple resampling (in production, use scipy.signal.resample)
                ratio = self.sample_rate / file_sr
                new_length = int(len(self.loop_audio) * ratio)
                x_old = np.linspace(0, len(self.loop_audio), len(self.loop_audio))
                x_new = np.linspace(0, len(self.loop_audio), new_length)
                self.loop_audio = np.interp(x_new, x_old, self.loop_audio)
            
            print(f"Loaded loop: {file_path}")
            print(f"Duration: {len(self.loop_audio) / self.sample_rate:.2f} seconds")
            
        except Exception as e:
            print(f"Error loading loop: {e}")
            self.loop_audio = None
    
    def get_loop_chunk(self, chunk_size):
        """Get the next chunk of audio from the loop."""
        if self.loop_audio is None or not self.loop_enabled:
            return np.zeros(chunk_size)
        
        chunk = np.zeros(chunk_size)
        remaining = chunk_size
        pos = 0
        
        while remaining > 0:
            # Calculate how much we can copy from current position
            available = len(self.loop_audio) - self.loop_position
            to_copy = min(remaining, available)
            
            # Copy audio
            chunk[pos:pos + to_copy] = self.loop_audio[
                self.loop_position:self.loop_position + to_copy
            ]
            
            # Update positions
            self.loop_position += to_copy
            pos += to_copy
            remaining -= to_copy
            
            # Wrap around if we hit the end
            if self.loop_position >= len(self.loop_audio):
                self.loop_position = 0
        
        return chunk * self.loop_volume
    
    def process_audio_pyworld(self, audio_chunk):
        """Process audio using PyWorld vocoder."""
        if not self.process_enabled or len(audio_chunk) < 512:
            return audio_chunk
        
        try:
            # PyWorld processing
            _f0, t = pw.dio(audio_chunk, self.sample_rate, frame_period=5.0)
            f0 = pw.stonemask(audio_chunk, _f0, t, self.sample_rate)
            sp = pw.cheaptrick(audio_chunk, f0, t, self.sample_rate)
            ap = pw.d4c(audio_chunk, f0, t, self.sample_rate)
            
            # Apply modifications
            f0_shifted = f0 * self.pitch_shift_ratio
            sp_shifted = self.shift_formants(sp, self.formant_shift_ratio)
            
            # Synthesize
            processed = pw.synthesize(f0_shifted, sp_shifted, ap, self.sample_rate)
            
            # Apply dry/wet mix
            mixed = (audio_chunk * (1 - self.dry_wet_mix) + 
                    processed * self.dry_wet_mix)
            
            return mixed
            
        except Exception as e:
            print(f"Processing error: {e}")
            return audio_chunk
    
    def shift_formants(self, sp, ratio):
        """Shift formants in spectral envelope."""
        sp_shifted = np.zeros_like(sp)
        
        for i in range(sp.shape[0]):
            spectrum = sp[i]
            shifted = np.zeros_like(spectrum)
            
            for j in range(len(spectrum)):
                src_bin = int(j / ratio)
                if 0 <= src_bin < len(spectrum):
                    shifted[j] = spectrum[src_bin]
            
            sp_shifted[i] = shifted
        
        return sp_shifted
    
    def audio_callback(self, indata, outdata, frames, time_info, status):
        """Real-time audio callback."""
        if status:
            print(f"Audio status: {status}")
        
        # Get microphone input
        mic_input = indata[:, 0] * self.mic_volume
        
        # Get loop chunk
        loop_chunk = self.get_loop_chunk(frames)
        
        # Mix microphone and loop
        mixed_input = mic_input + loop_chunk
        
        # Process the mixed audio
        if self.process_enabled:
            # Add to processing queue
            self.input_queue.put(mixed_input)
            
            # Try to get processed output
            try:
                processed = self.output_queue.get_nowait()
                outdata[:, 0] = processed
            except queue.Empty:
                # If no processed audio ready, output the mixed input
                outdata[:, 0] = mixed_input
        else:
            # Pass through without processing
            outdata[:, 0] = mixed_input
    
    def processing_worker(self):
        """Background processing thread."""
        buffer_size = self.block_size * 4
        buffer = np.zeros(buffer_size)
        
        while self.is_running:
            try:
                # Get input chunk
                chunk = self.input_queue.get(timeout=0.1)
                
                # Update buffer
                buffer = np.roll(buffer, -len(chunk))
                buffer[-len(chunk):] = chunk
                
                # Process buffer
                processed = self.process_audio_pyworld(buffer)
                
                # Extract output chunk
                output_chunk = processed[-len(chunk):]
                
                # Send to output queue
                self.output_queue.put(output_chunk)
                
            except queue.Empty:
                continue
    
    def start(self):
        """Start the audio loop player."""
        print("Starting Audio Loop Processor...")
        print(f"Loop enabled: {self.loop_enabled}")
        print(f"Processing enabled: {self.process_enabled}")
        print(f"Pitch ratio: {self.pitch_shift_ratio}")
        print(f"Formant ratio: {self.formant_shift_ratio}")
        print("\nControls during playback:")
        print("  'l' - Toggle loop on/off")
        print("  'p' - Toggle processing on/off")
        print("  'q' - Quit")
        print("-" * 40)
        
        # Start processing thread
        self.is_running = True
        processing_thread = threading.Thread(target=self.processing_worker)
        processing_thread.start()
        
        # Start audio stream
        with sd.Stream(
            samplerate=self.sample_rate,
            blocksize=self.block_size,
            channels=1,
            callback=self.audio_callback,
            dtype='float32'
        ):
            # Simple command loop
            while self.is_running:
                try:
                    import sys, select
                    # Check for keyboard input (Unix/Linux/Mac only)
                    if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                        cmd = sys.stdin.readline().strip().lower()
                        
                        if cmd == 'q':
                            break
                        elif cmd == 'l':
                            self.loop_enabled = not self.loop_enabled
                            print(f"Loop: {'ON' if self.loop_enabled else 'OFF'}")
                        elif cmd == 'p':
                            self.process_enabled = not self.process_enabled
                            print(f"Processing: {'ON' if self.process_enabled else 'OFF'}")
                    
                    time.sleep(0.1)
                    
                except KeyboardInterrupt:
                    break
                except:
                    # For Windows compatibility, just sleep
                    time.sleep(0.1)
        
        # Clean up
        self.is_running = False
        processing_thread.join()
        print("\nStopped.")

class SimpleLooper:
    """Simple audio looper for testing without processing."""
    def __init__(self, loop_file, sample_rate=44100):
        self.sample_rate = sample_rate
        self.loop_audio, file_sr = sf.read(loop_file)
        
        if len(self.loop_audio.shape) > 1:
            self.loop_audio = np.mean(self.loop_audio, axis=1)
        
        self.position = 0
        
    def callback(self, indata, outdata, frames, time_info, status):
        # Mix input with loop
        loop_chunk = self.get_chunk(frames)
        outdata[:, 0] = indata[:, 0] * 0.5 + loop_chunk * 0.5
        
    def get_chunk(self, size):
        chunk = np.zeros(size)
        
        if self.position + size <= len(self.loop_audio):
            chunk = self.loop_audio[self.position:self.position + size]
            self.position += size
        else:
            # Handle wrap-around
            first_part = len(self.loop_audio) - self.position
            chunk[:first_part] = self.loop_audio[self.position:]
            chunk[first_part:] = self.loop_audio[:size - first_part]
            self.position = size - first_part
            
        return chunk
    
    def run(self):
        with sd.Stream(callback=self.callback, channels=1, 
                      samplerate=self.sample_rate):
            print("Simple looper running. Press Ctrl+C to stop.")
            try:
                while True:
                    time.sleep(0.1)
            except KeyboardInterrupt:
                print("\nStopped.")

def create_test_loop(filename="test_loop.wav", duration=2.0, sample_rate=44100):
    """Create a simple test loop file."""
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Create a simple melody
    frequencies = [440, 523, 587, 440]  # A4, C5, D5, A4
    samples_per_note = len(t) // len(frequencies)
    
    audio = np.zeros_like(t)
    
    for i, freq in enumerate(frequencies):
        start = i * samples_per_note
        end = (i + 1) * samples_per_note if i < len(frequencies) - 1 else len(t)
        
        # Add fundamental and harmonics
        audio[start:end] = (
            0.5 * np.sin(2 * np.pi * freq * t[start:end]) +
            0.3 * np.sin(2 * np.pi * freq * 2 * t[start:end]) +
            0.2 * np.sin(2 * np.pi * freq * 3 * t[start:end])
        )
        
        # Apply envelope
        envelope = np.ones(end - start)
        fade_samples = int(0.05 * sample_rate)  # 50ms fade
        envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
        envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
        audio[start:end] *= envelope
    
    # Normalize
    audio = audio / np.max(np.abs(audio)) * 0.8
    
    # Save
    sf.write(filename, audio, sample_rate)
    print(f"Created test loop: {filename}")
    
    return filename

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Audio Loop Player with Voice Processing')
    parser.add_argument('--loop', type=str, help='Path to audio loop file')
    parser.add_argument('--create-test', action='store_true', 
                       help='Create a test loop file')
    parser.add_argument('--pitch', type=float, default=1.2,
                       help='Pitch shift ratio (default: 1.2)')
    parser.add_argument('--formant', type=float, default=1.3,
                       help='Formant shift ratio (default: 1.3)')
    parser.add_argument('--simple', action='store_true',
                       help='Use simple looper without processing')
    
    args = parser.parse_args()
    
    # Create test loop if requested
    if args.create_test:
        loop_file = create_test_loop()
    else:
        loop_file = args.loop
    
    if args.simple and loop_file:
        # Simple looper
        looper = SimpleLooper(loop_file)
        looper.run()
    else:
        # Full processor
        processor = AudioLoopProcessor(
            loop_file=loop_file,
            pitch_shift_ratio=args.pitch,
            formant_shift_ratio=args.formant
        )
        processor.start()

if __name__ == "__main__":
    main()