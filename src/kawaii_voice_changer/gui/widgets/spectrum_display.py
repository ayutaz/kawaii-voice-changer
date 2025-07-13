"""Spectrum display widget for real-time frequency visualization."""

from __future__ import annotations

import numpy as np
import numpy.typing as npt
import pyqtgraph as pg
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QVBoxLayout, QWidget


class SpectrumDisplay(QWidget):
    """Widget for displaying real-time spectrum and spectrogram."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize spectrum display.

        Args:
            parent: Parent widget.
        """
        super().__init__(parent)

        self.sample_rate = 44100
        self.fft_size = 2048
        self.hop_size = 512
        self.window = np.hanning(self.fft_size)

        # Data buffers
        self.audio_buffer: npt.NDArray[np.float32] | None = None
        self.spectrogram_data: npt.NDArray[np.float32] | None = None
        self.current_position = 0

        # Display settings
        self.freq_max = 5000  # Max frequency to display (Hz)
        self.db_range = 80  # Dynamic range in dB

        # Formant markers
        self.formant_lines: list[pg.InfiniteLine] = []
        self.formant_freqs = [700, 1200, 2500]  # Default F1, F2, F3

        self._setup_ui()

        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_spectrum)
        self.update_timer.setInterval(50)  # 20 FPS

    def _setup_ui(self) -> None:
        """Set up user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create plot widget with two plots
        self.graphics_layout = pg.GraphicsLayoutWidget()
        self.graphics_layout.setBackground("w")

        # Spectrum plot (top)
        self.spectrum_plot = self.graphics_layout.addPlot(
            row=0, col=0, title="スペクトラム"
        )
        self.spectrum_plot.setLabel("left", "振幅", units="dB")
        self.spectrum_plot.setLabel("bottom", "周波数", units="Hz")
        self.spectrum_plot.showGrid(x=True, y=True, alpha=0.3)
        self.spectrum_plot.setYRange(-self.db_range, 0)
        self.spectrum_plot.setXRange(0, self.freq_max)

        # Spectrum curve
        self.spectrum_curve = self.spectrum_plot.plot(
            pen=pg.mkPen(color=(50, 50, 200), width=2)
        )

        # Add formant markers
        for i, freq in enumerate(self.formant_freqs):
            line = pg.InfiniteLine(
                pos=freq,
                angle=90,
                pen=pg.mkPen(
                    color=(200, 50, 50),
                    width=2,
                    style=pg.QtCore.Qt.PenStyle.DashLine
                ),
                label=f"F{i+1}",
                labelOpts={"position": 0.95, "color": (200, 50, 50)}
            )
            self.spectrum_plot.addItem(line)
            self.formant_lines.append(line)

        # Spectrogram plot (bottom)
        self.spectrogram_plot = self.graphics_layout.addPlot(
            row=1, col=0, title="スペクトログラム"
        )
        self.spectrogram_plot.setLabel("left", "周波数", units="Hz")
        self.spectrogram_plot.setLabel("bottom", "時間", units="s")
        self.spectrogram_plot.setYRange(0, self.freq_max)

        # Spectrogram image
        self.spectrogram_img = pg.ImageItem()
        self.spectrogram_plot.addItem(self.spectrogram_img)

        # Color map
        self.colormap = pg.colormap.get("viridis")
        self.spectrogram_img.setColorMap(self.colormap)

        # Link x-axis of spectrum to y-axis of spectrogram
        self.spectrum_plot.setXLink(self.spectrogram_plot.getViewBox())

        layout.addWidget(self.graphics_layout)

    def set_audio_data(
        self,
        audio_data: npt.NDArray[np.float32] | None,
        sample_rate: int,
    ) -> None:
        """Set audio data for analysis.

        Args:
            audio_data: Audio samples.
            sample_rate: Sample rate in Hz.
        """
        self.audio_buffer = audio_data
        self.sample_rate = sample_rate
        self.current_position = 0

        if audio_data is None:
            self.clear()
            return

        # Initialize spectrogram buffer
        num_frames = (len(audio_data) - self.fft_size) // self.hop_size + 1
        freq_bins = self.fft_size // 2 + 1
        self.spectrogram_data = np.zeros((freq_bins, num_frames), dtype=np.float32)

        # Pre-compute spectrogram
        self._compute_spectrogram()

        # Start updates
        self.update_timer.start()

    def _compute_spectrogram(self) -> None:
        """Compute full spectrogram from audio data."""
        if self.audio_buffer is None or self.spectrogram_data is None:
            return

        for i in range(self.spectrogram_data.shape[1]):
            start = i * self.hop_size
            end = start + self.fft_size

            if end > len(self.audio_buffer):
                break

            # Window and FFT
            windowed = self.audio_buffer[start:end] * self.window
            spectrum = np.fft.rfft(windowed)
            magnitude = np.abs(spectrum)

            # Convert to dB
            db = 20 * np.log10(magnitude + 1e-10)
            self.spectrogram_data[:, i] = db

        # Update spectrogram display
        self._update_spectrogram_display()

    def _update_spectrogram_display(self) -> None:
        """Update spectrogram image display."""
        if self.spectrogram_data is None:
            return

        # Get frequency range
        freqs = np.fft.rfftfreq(self.fft_size, 1/self.sample_rate)
        freq_mask = freqs <= self.freq_max

        # Display only up to freq_max
        display_data = self.spectrogram_data[freq_mask, :]

        # Normalize for display
        vmin = -self.db_range
        vmax = 0
        normalized = (display_data - vmin) / (vmax - vmin)
        normalized = np.clip(normalized, 0, 1)

        # Set image
        self.spectrogram_img.setImage(
            normalized.T,
            autoLevels=False,
            levels=[0, 1]
        )

        # Set transform to match axes
        time_scale = self.hop_size / self.sample_rate
        freq_scale = self.freq_max / np.sum(freq_mask)
        self.spectrogram_img.setTransform(
            pg.QtGui.QTransform.fromScale(time_scale, freq_scale)
        )

    def set_playback_position(self, position: float) -> None:
        """Update playback position for spectrum display.

        Args:
            position: Position in seconds.
        """
        if self.audio_buffer is None:
            return

        # Convert to sample position
        self.current_position = int(position * self.sample_rate)

    def _update_spectrum(self) -> None:
        """Update spectrum display with current audio frame."""
        if self.audio_buffer is None or self.current_position >= len(self.audio_buffer):
            return

        # Get current frame
        start = self.current_position
        end = min(start + self.fft_size, len(self.audio_buffer))

        if end - start < self.fft_size:
            # Pad with zeros if needed
            frame = np.zeros(self.fft_size)
            frame[:end-start] = self.audio_buffer[start:end]
        else:
            frame = self.audio_buffer[start:end]

        # Apply window and compute FFT
        windowed = frame * self.window
        spectrum = np.fft.rfft(windowed)
        magnitude = np.abs(spectrum)

        # Convert to dB
        db = 20 * np.log10(magnitude + 1e-10)

        # Get frequencies
        freqs = np.fft.rfftfreq(self.fft_size, 1/self.sample_rate)

        # Update plot (only up to freq_max)
        freq_mask = freqs <= self.freq_max
        self.spectrum_curve.setData(freqs[freq_mask], db[freq_mask])

    def update_formant_markers(self, f1: float, f2: float, f3: float) -> None:
        """Update formant frequency markers.

        Args:
            f1: F1 frequency in Hz.
            f2: F2 frequency in Hz.
            f3: F3 frequency in Hz.
        """
        formants = [f1, f2, f3]
        for i, (line, freq) in enumerate(zip(self.formant_lines, formants, strict=False)):
            line.setPos(freq)
            line.label.setText(f"F{i+1}: {freq:.0f}Hz")

    def clear(self) -> None:
        """Clear all displays."""
        self.update_timer.stop()
        self.spectrum_curve.setData([], [])
        self.spectrogram_img.clear()
        self.audio_buffer = None
        self.spectrogram_data = None
        self.current_position = 0

    def start_updates(self) -> None:
        """Start real-time updates."""
        if self.audio_buffer is not None:
            self.update_timer.start()

    def stop_updates(self) -> None:
        """Stop real-time updates."""
        self.update_timer.stop()
