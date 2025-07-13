"""Waveform display widget using pyqtgraph."""

from __future__ import annotations

from typing import Any

import numpy as np
import numpy.typing as npt
import pyqtgraph as pg
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QVBoxLayout, QWidget


class WaveformDisplay(QWidget):
    """Widget for displaying audio waveform."""

    # Signals
    loop_region_changed = Signal(float, float)  # start, end in seconds

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize waveform display.

        Args:
            parent: Parent widget.
        """
        super().__init__(parent)

        self.audio_data: npt.NDArray[np.float32] | None = None
        self.sample_rate = 44100
        self.playback_position = 0.0

        # Loop region selection
        self.loop_start = 0.0
        self.loop_end = 0.0
        self.is_selecting = False
        self.selection_start_x = 0.0

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

        # Loop region
        self.loop_region = pg.LinearRegionItem(
            values=[0, 0],
            brush=pg.mkBrush(100, 100, 255, 50),
            pen=pg.mkPen(color=(100, 100, 255), width=2),
            movable=True,
        )
        self.loop_region.setVisible(False)
        self.plot_widget.addItem(self.loop_region)

        # Connect loop region signals
        self.loop_region.sigRegionChanged.connect(self._on_loop_region_changed)

        # Enable mouse interaction
        self.plot_widget.scene().sigMouseClicked.connect(self._on_mouse_clicked)

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

    def set_loop_region(self, start: float, end: float) -> None:
        """Set loop region.

        Args:
            start: Start time in seconds.
            end: End time in seconds (0 = end of file).
        """
        if self.audio_data is None:
            return

        duration = len(self.audio_data) / self.sample_rate
        if end <= 0:
            end = duration

        self.loop_start = max(0, min(start, duration))
        self.loop_end = max(self.loop_start, min(end, duration))

        self.loop_region.setRegion([self.loop_start, self.loop_end])
        self.loop_region.setVisible(self.loop_end > self.loop_start)

    def get_loop_region(self) -> tuple[float, float]:
        """Get current loop region.

        Returns:
            Tuple of (start, end) in seconds.
        """
        return self.loop_start, self.loop_end

    def clear_loop_region(self) -> None:
        """Clear loop region."""
        self.loop_start = 0.0
        self.loop_end = 0.0
        self.loop_region.setRegion([0, 0])
        self.loop_region.setVisible(False)
        self.loop_region_changed.emit(0.0, 0.0)

    def _on_loop_region_changed(self) -> None:
        """Handle loop region change."""
        start, end = self.loop_region.getRegion()
        self.loop_start = start
        self.loop_end = end
        self.loop_region_changed.emit(start, end)

    def _on_mouse_clicked(self, event: Any) -> None:
        """Handle mouse click for loop region selection.

        Args:
            event: Mouse event.
        """
        if event.button() == Qt.MouseButton.RightButton:
            # Right click to clear loop region
            self.clear_loop_region()
        elif event.button() == Qt.MouseButton.LeftButton and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # Ctrl+click to start loop region selection
            pos = self.plot_widget.plotItem.vb.mapSceneToView(event.scenePos())
            x = pos.x()

            if self.audio_data is not None:
                duration = len(self.audio_data) / self.sample_rate
                x = max(0, min(x, duration))

                if not self.is_selecting:
                    # Start selection
                    self.is_selecting = True
                    self.selection_start_x = x
                    self.set_loop_region(x, x)
                else:
                    # End selection
                    self.is_selecting = False
                    start = min(self.selection_start_x, x)
                    end = max(self.selection_start_x, x)
                    self.set_loop_region(start, end)

    def clear(self) -> None:
        """Clear the waveform display."""
        self.waveform_plot.setData([], [])
        self.position_line.setPos(0)
        self.clear_loop_region()
