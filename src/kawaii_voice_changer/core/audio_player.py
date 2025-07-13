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
            # Calculate needed samples
            samples_needed = frames
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
                    # Loop playback
                    remaining = samples_needed - samples_available
                    self.play_position = remaining
                    outdata[samples_available:, 0] = audio[:remaining] * self.volume
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
