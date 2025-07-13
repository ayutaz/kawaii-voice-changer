"""Audio playback module using sounddevice for real-time output."""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any

import numpy as np
import numpy.typing as npt
import sounddevice as sd

if TYPE_CHECKING:
    from .audio_processor import AudioProcessor


class AudioPlayer:
    """Manages audio playback with loop support."""

    def __init__(self, processor: AudioProcessor, buffer_size: int = 512) -> None:
        """Initialize audio player.

        Args:
            processor: AudioProcessor instance.
            buffer_size: Audio buffer size in samples. Defaults to 512.
        """
        self.processor = processor
        self.buffer_size = buffer_size
        self.is_playing = False
        self.loop_enabled = True
        self.loop_start = 0  # Loop start position in samples
        self.loop_end = 0    # Loop end position in samples (0 = end of file)
        self.loop_crossfade_ms = 50  # Crossfade duration in milliseconds
        self.volume = 1.0

        # Playback position
        self.play_position = 0
        self._position_lock = threading.Lock()

        # Audio stream
        self.stream: sd.OutputStream | None = None

        # Playback control
        self._stop_event = threading.Event()

    def _audio_callback(
        self,
        outdata: npt.NDArray[np.float32],
        frames: int,
        time_info: Any,  # noqa: ARG002
        status: sd.CallbackFlags,
    ) -> None:
        """Sounddevice callback function.

        Args:
            outdata: Output buffer to fill.
            frames: Number of frames to generate.
            time_info: Time information.
            status: Callback status flags.
        """
        if status:
            print(f"Audio callback status: {status}")

        # Get processed audio
        audio = self.processor.get_processed_audio()

        if len(audio) == 0:
            outdata.fill(0)
            return

        with self._position_lock:
            # Get effective loop boundaries
            loop_end = self.loop_end if self.loop_end > 0 else len(audio)
            loop_start = min(self.loop_start, loop_end - 1)

            # Calculate needed samples
            samples_needed = frames

            # Handle loop region
            if self.loop_enabled and self.play_position >= loop_start:
                # We're in the loop region
                samples_available = loop_end - self.play_position

                if samples_available >= samples_needed:
                    # Enough samples in loop region
                    outdata[:, 0] = (
                        audio[self.play_position : self.play_position + samples_needed]
                        * self.volume
                    )
                    self.play_position += samples_needed
                else:
                    # Need to loop back
                    if samples_available > 0:
                        outdata[:samples_available, 0] = (
                            audio[self.play_position : loop_end] * self.volume
                        )

                    # Fill remaining from loop start with crossfade
                    remaining = samples_needed - samples_available
                    loop_length = loop_end - loop_start

                    if loop_length > 0:
                        # Calculate crossfade samples
                        crossfade_samples = int(self.loop_crossfade_ms * self.processor.sample_rate / 1000)
                        crossfade_samples = min(crossfade_samples, samples_available, loop_length // 4)

                        # Apply crossfade if we have samples at the end
                        if samples_available > 0 and crossfade_samples > 0:
                            # Fade out the end
                            fade_out = np.linspace(1.0, 0.0, crossfade_samples)
                            start_idx = samples_available - crossfade_samples
                            outdata[start_idx:samples_available, 0] *= fade_out

                            # Fade in from loop start and mix
                            fade_in = np.linspace(0.0, 1.0, crossfade_samples)
                            loop_audio = audio[loop_start : loop_start + crossfade_samples] * self.volume
                            outdata[start_idx:samples_available, 0] += loop_audio * fade_in

                        # Fill the rest normally
                        pos = samples_available
                        while remaining > 0:
                            chunk_size = min(remaining, loop_length)
                            outdata[pos : pos + chunk_size, 0] = (
                                audio[loop_start : loop_start + chunk_size] * self.volume
                            )
                            pos += chunk_size
                            remaining -= chunk_size

                        # Update position
                        self.play_position = loop_start + ((samples_needed - samples_available) % loop_length)
                    else:
                        # Invalid loop region
                        outdata[samples_available:, 0] = 0
                        self.play_position = loop_end
            else:
                # Normal playback (not in loop region yet)
                samples_available = len(audio) - self.play_position

                if samples_available >= samples_needed:
                    # Enough samples available
                    outdata[:, 0] = (
                        audio[self.play_position : self.play_position + samples_needed]
                        * self.volume
                    )
                    self.play_position += samples_needed
                else:
                    # Not enough samples
                    if samples_available > 0:
                        outdata[:samples_available, 0] = (
                            audio[self.play_position :] * self.volume
                        )

                    if self.loop_enabled:
                        # Loop from beginning or loop start
                        remaining = samples_needed - samples_available
                        self.play_position = loop_start + remaining
                        outdata[samples_available:, 0] = audio[loop_start : loop_start + remaining] * self.volume
                    else:
                        # No loop: fill with silence
                        outdata[samples_available:, 0] = 0
                        self.play_position = len(audio)
                        self.stop()

    def start(self) -> None:
        """Start playback."""
        if self.is_playing:
            return

        self.stream = sd.OutputStream(
            samplerate=self.processor.sample_rate,
            channels=1,
            callback=self._audio_callback,
            blocksize=self.buffer_size,
            dtype="float32",
        )

        self.stream.start()
        self.is_playing = True
        self._stop_event.clear()

    def stop(self) -> None:
        """Stop playback."""
        if not self.is_playing:
            return

        self.is_playing = False
        self._stop_event.set()

        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

        # Reset playback position
        with self._position_lock:
            self.play_position = 0

    def pause(self) -> None:
        """Pause playback."""
        if self.stream and self.is_playing:
            self.stream.stop()
            self.is_playing = False

    def resume(self) -> None:
        """Resume playback."""
        if self.stream and not self.is_playing:
            self.stream.start()
            self.is_playing = True

    def set_volume(self, volume: float) -> None:
        """Set playback volume.

        Args:
            volume: Volume level (0.0 to 1.0).
        """
        self.volume = np.clip(volume, 0.0, 1.0)

    def set_loop(self, enabled: bool) -> None:
        """Set loop playback mode.

        Args:
            enabled: True to enable loop playback.
        """
        self.loop_enabled = enabled

    def get_position(self) -> float:
        """Get current playback position in seconds.

        Returns:
            Position in seconds.
        """
        with self._position_lock:
            return self.play_position / self.processor.sample_rate

    def seek(self, position_sec: float) -> None:
        """Seek to specific position.

        Args:
            position_sec: Target position in seconds.
        """
        with self._position_lock:
            audio_length = len(self.processor.get_processed_audio())
            sample_position = int(position_sec * self.processor.sample_rate)
            self.play_position = np.clip(sample_position, 0, audio_length - 1)

    def set_loop_region(self, start_time: float, end_time: float) -> None:
        """Set loop region.

        Args:
            start_time: Loop start time in seconds.
            end_time: Loop end time in seconds (0 = end of file).
        """
        with self._position_lock:
            # Ensure start_time is not negative
            start_time = max(0, start_time)

            # Get the actual processed audio to determine the real sample rate
            processed_audio = self.processor.get_processed_audio()
            audio_length = len(processed_audio)

            if audio_length > 0:
                # Calculate effective sample rate from actual audio length
                # This handles cases where PyWorld might resample the audio
                effective_duration = self.processor.duration
                if effective_duration > 0:
                    effective_sample_rate = audio_length / effective_duration
                else:
                    effective_sample_rate = self.processor.sample_rate

                # Convert to samples using effective sample rate
                self.loop_start = int(start_time * effective_sample_rate)
                self.loop_end = int(end_time * effective_sample_rate) if end_time > 0 else 0

                # Ensure valid range
                self.loop_start = max(0, min(self.loop_start, audio_length - 1))
                if self.loop_end > 0:
                    self.loop_end = max(self.loop_start + 1, min(self.loop_end, audio_length))

                # If end < start, swap them
                if self.loop_end > 0 and self.loop_end < self.loop_start:
                    self.loop_start, self.loop_end = self.loop_end, self.loop_start
            else:
                # No audio loaded
                self.loop_start = 0
                self.loop_end = 0

    def set_loop_crossfade(self, crossfade_ms: float) -> None:
        """Set loop crossfade duration.

        Args:
            crossfade_ms: Crossfade duration in milliseconds (0-500ms).
        """
        with self._position_lock:
            self.loop_crossfade_ms = np.clip(crossfade_ms, 0, 500)

    def get_loop_crossfade(self) -> float:
        """Get current loop crossfade duration.

        Returns:
            Crossfade duration in milliseconds.
        """
        return self.loop_crossfade_ms

    def get_loop_region(self) -> tuple[float, float]:
        """Get current loop region.

        Returns:
            Tuple of (start_time, end_time) in seconds.
        """
        with self._position_lock:
            # Get the actual processed audio to determine the real sample rate
            processed_audio = self.processor.get_processed_audio()
            audio_length = len(processed_audio)

            if audio_length > 0:
                # Calculate effective sample rate
                effective_duration = self.processor.duration
                if effective_duration > 0:
                    effective_sample_rate = audio_length / effective_duration
                else:
                    effective_sample_rate = self.processor.sample_rate

                start_time = self.loop_start / effective_sample_rate
                end_time = self.loop_end / effective_sample_rate if self.loop_end > 0 else 0
            else:
                start_time = 0.0
                end_time = 0.0

            return start_time, end_time

    def clear_loop_region(self) -> None:
        """Clear loop region (loop entire file)."""
        with self._position_lock:
            self.loop_start = 0
            self.loop_end = 0
