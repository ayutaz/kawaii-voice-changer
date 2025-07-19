"""Audio recording module using sounddevice."""

from __future__ import annotations

import queue
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np
import numpy.typing as npt
import sounddevice as sd
import soundfile as sf

from ..utils import setup_logger

logger = setup_logger(__name__)


class RecorderState(Enum):
    """Recording state enum."""

    IDLE = "idle"
    RECORDING = "recording"
    PAUSED = "paused"


@dataclass
class RecordingSettings:
    """Recording settings dataclass."""

    sample_rate: int = 44100
    channels: int = 1  # 1: mono, 2: stereo
    dtype: str = "float32"
    device: int | None = None  # None uses default device
    block_duration: float = 0.05  # 50ms blocks
    gain: float = 1.0  # Input gain


class AudioRecorder:
    """Audio recorder using sounddevice."""

    def __init__(self, settings: RecordingSettings | None = None) -> None:
        """Initialize audio recorder.

        Args:
            settings: Recording settings. If None, uses default settings.
        """
        self.settings = settings or RecordingSettings()
        self.state = RecorderState.IDLE

        # Recording data
        self._recording_queue: queue.Queue[npt.NDArray[np.float32]] = queue.Queue()
        self._recording_data: list[npt.NDArray[np.float32]] = []
        self._start_time: float | None = None
        self._pause_time: float | None = None
        self._total_pause_duration: float = 0.0

        # Stream
        self._stream: sd.InputStream | None = None

        # Callbacks
        self._level_callback: Callable[[float], None] | None = None

        # Thread safety
        self._state_lock = threading.Lock()
        self._data_lock = threading.Lock()

        logger.info("Audio recorder initialized")

    @staticmethod
    def get_input_devices() -> list[dict[str, Any]]:
        """Get list of available input devices.

        Returns:
            List of input device info dictionaries.
        """
        devices = []
        for i, device in enumerate(sd.query_devices()):
            if device["max_input_channels"] > 0:
                devices.append({
                    "index": i,
                    "name": device["name"],
                    "channels": device["max_input_channels"],
                    "sample_rate": device["default_samplerate"],
                    "is_default": i == sd.default.device[0],
                })
        return devices

    def set_level_callback(self, callback: Callable[[float], None] | None) -> None:
        """Set callback for input level updates.

        Args:
            callback: Function that receives RMS level (0.0-1.0).
        """
        self._level_callback = callback

    def start_recording(self, output_dir: Path | None = None) -> Path | None:
        """Start recording.

        Args:
            output_dir: Directory to save recording. If None, uses current directory.

        Returns:
            Path to the output file that will be created.
        """
        with self._state_lock:
            if self.state == RecorderState.RECORDING:
                logger.warning("Already recording")
                return None

            if self.state == RecorderState.PAUSED:
                # Resume from pause
                self._total_pause_duration += time.time() - (self._pause_time or 0)
                self.state = RecorderState.RECORDING
                logger.info("Resumed recording")
                return None

            # Start new recording
            self._recording_data.clear()
            self._recording_queue = queue.Queue()
            self._start_time = time.time()
            self._total_pause_duration = 0.0

            # Generate output filename
            if output_dir is None:
                output_dir = Path.cwd()
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = output_dir / f"recording_{timestamp}.wav"

            # Start stream
            try:
                self._stream = sd.InputStream(
                    samplerate=self.settings.sample_rate,
                    channels=self.settings.channels,
                    dtype=self.settings.dtype,
                    device=self.settings.device,
                    callback=self._audio_callback,
                    blocksize=int(self.settings.sample_rate * self.settings.block_duration),
                )
                self._stream.start()
                self.state = RecorderState.RECORDING
                logger.info(f"Started recording to {output_file}")
                return output_file

            except Exception as e:
                logger.error(f"Failed to start recording: {e}")
                self.state = RecorderState.IDLE
                return None

    def pause_recording(self) -> bool:
        """Pause recording.

        Returns:
            True if successfully paused.
        """
        with self._state_lock:
            if self.state != RecorderState.RECORDING:
                logger.warning("Not recording")
                return False

            self._pause_time = time.time()
            self.state = RecorderState.PAUSED
            logger.info("Paused recording")
            return True

    def stop_recording(self, output_file: Path | None = None) -> Path | None:
        """Stop recording and save to file.

        Args:
            output_file: Path to save recording. If None, generates timestamped filename.

        Returns:
            Path to saved file, or None if failed.
        """
        with self._state_lock:
            if self.state == RecorderState.IDLE:
                logger.warning("Not recording")
                return None

            # Stop stream
            if self._stream:
                self._stream.stop()
                self._stream.close()
                self._stream = None

            # Process remaining queue data
            while not self._recording_queue.empty():
                try:
                    data = self._recording_queue.get_nowait()
                    self._recording_data.append(data)
                except queue.Empty:
                    break

            self.state = RecorderState.IDLE

        # Save recording
        if not self._recording_data:
            logger.warning("No data recorded")
            return None

        with self._data_lock:
            # Concatenate all data
            audio_data = np.concatenate(self._recording_data)

            # Generate output filename if not provided
            if output_file is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = Path.cwd() / f"recording_{timestamp}.wav"

            # Save to file
            try:
                sf.write(output_file, audio_data, self.settings.sample_rate)
                logger.info(f"Saved recording to {output_file}")
                return output_file
            except Exception as e:
                logger.error(f"Failed to save recording: {e}")
                return None

    def get_recording_duration(self) -> float:
        """Get current recording duration in seconds.

        Returns:
            Duration in seconds.
        """
        if self._start_time is None:
            return 0.0

        if self.state == RecorderState.IDLE:
            return 0.0

        current_time = time.time()
        if self.state == RecorderState.PAUSED:
            current_time = self._pause_time or current_time

        return current_time - self._start_time - self._total_pause_duration

    def get_recording_level(self) -> float:
        """Get current input level.

        Returns:
            RMS level (0.0-1.0).
        """
        # This is updated via callback
        return 0.0

    def _audio_callback(
        self,
        indata: npt.NDArray[np.float32],
        _frames: int,
        _time_info: Any,
        status: sd.CallbackFlags,
    ) -> None:
        """Audio stream callback.

        Args:
            indata: Input audio data.
            frames: Number of frames.
            time_info: Timing information.
            status: Stream status flags.
        """
        if status:
            logger.warning(f"Stream status: {status}")

        if self.state != RecorderState.RECORDING:
            return

        # Apply gain
        data = indata.copy() * self.settings.gain

        # Add to recording queue
        self._recording_queue.put(data)
        with self._data_lock:
            self._recording_data.append(data)

        # Calculate and report level
        if self._level_callback:
            rms = float(np.sqrt(np.mean(data**2)))
            # Clamp to 0.0-1.0
            level = min(1.0, rms)
            self._level_callback(level)

    def __del__(self) -> None:
        """Cleanup on deletion."""
        if self._stream:
            self._stream.stop()
            self._stream.close()
