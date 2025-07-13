"""Waveform display widget using pyqtgraph."""

from __future__ import annotations

import numpy as np
import numpy.typing as npt
import pyqtgraph as pg
from PySide6.QtWidgets import QVBoxLayout, QWidget


class WaveformDisplay(QWidget):
    """Widget for displaying audio waveform."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize waveform display.

        Args:
            parent: Parent widget.
        """
        super().__init__(parent)

        self.audio_data: npt.NDArray[np.float32] | None = None
        self.sample_rate = 44100
        self.playback_position = 0.0

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create plot widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setLabel("left", "振幅")
        self.plot_widget.setLabel("bottom", "時間", units="s")
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setYRange(-1, 1)

        # Set background color
        self.plot_widget.setBackground("w")

        # Create plot items
        self.waveform_plot = self.plot_widget.plot(
            pen=pg.mkPen(color=(50, 50, 200), width=1)
        )

        # Playback position line
        self.position_line = pg.InfiniteLine(
            pos=0,
            angle=90,
            pen=pg.mkPen(color=(200, 50, 50), width=2),
        )
        self.plot_widget.addItem(self.position_line)

        layout.addWidget(self.plot_widget)

    def set_audio_data(
        self,
        audio_data: npt.NDArray[np.float32] | None,
        sample_rate: int,
    ) -> None:
        """Set audio data to display.

        Args:
            audio_data: Audio samples.
            sample_rate: Sample rate in Hz.
        """
        self.audio_data = audio_data
        self.sample_rate = sample_rate

        if audio_data is None or len(audio_data) == 0:
            self.waveform_plot.setData([], [])
            return

        # Downsample for display if necessary
        max_points = 10000
        if len(audio_data) > max_points:
            # Simple downsampling
            factor = len(audio_data) // max_points
            display_data = audio_data[::factor]
            time_axis = np.arange(len(display_data)) * factor / sample_rate
        else:
            display_data = audio_data
            time_axis = np.arange(len(audio_data)) / sample_rate

        # Update plot
        self.waveform_plot.setData(time_axis, display_data)

        # Update x-axis range
        duration = len(audio_data) / sample_rate
        self.plot_widget.setXRange(0, duration)

    def set_playback_position(self, position: float) -> None:
        """Update playback position indicator.

        Args:
            position: Position in seconds.
        """
        self.playback_position = position
        self.position_line.setPos(position)

    def clear(self) -> None:
        """Clear the waveform display."""
        self.waveform_plot.setData([], [])
        self.position_line.setPos(0)
