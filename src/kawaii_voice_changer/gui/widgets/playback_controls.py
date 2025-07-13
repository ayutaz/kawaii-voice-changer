"""Playback control widget."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QWidget,
)


class PlaybackControls(QWidget):
    """Widget for audio playback controls."""

    # Signals
    play_clicked = Signal()
    stop_clicked = Signal()
    volume_changed = Signal(float)
    loop_changed = Signal(bool)

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize playback controls.

        Args:
            parent: Parent widget.
        """
        super().__init__(parent)
        self.is_playing = False
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up user interface."""
        layout = QHBoxLayout(self)

        # Play/Pause button
        self.play_button = QPushButton("▶ 再生")
        self.play_button.clicked.connect(self._on_play_clicked)
        layout.addWidget(self.play_button)

        # Stop button
        self.stop_button = QPushButton("■ 停止")
        self.stop_button.clicked.connect(self._on_stop_clicked)
        layout.addWidget(self.stop_button)

        # Position label
        self.position_label = QLabel("0:00 / 0:00")
        layout.addWidget(self.position_label)

        layout.addStretch()

        # Loop checkbox
        self.loop_checkbox = QCheckBox("ループ")
        self.loop_checkbox.setChecked(True)
        self.loop_checkbox.toggled.connect(self.loop_changed.emit)
        layout.addWidget(self.loop_checkbox)

        # Volume controls
        layout.addWidget(QLabel("音量:"))

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(100)
        self.volume_slider.setFixedWidth(100)
        self.volume_slider.valueChanged.connect(self._on_volume_changed)
        layout.addWidget(self.volume_slider)

        self.volume_label = QLabel("100%")
        self.volume_label.setMinimumWidth(40)
        layout.addWidget(self.volume_label)

    def _on_play_clicked(self) -> None:
        """Handle play button click."""
        if self.is_playing:
            # Currently playing, so pause
            self.play_clicked.emit()  # Will be handled as pause
            self.set_playing(False)
        else:
            # Currently paused/stopped, so play
            self.play_clicked.emit()
            self.set_playing(True)

    def _on_stop_clicked(self) -> None:
        """Handle stop button click."""
        self.stop_clicked.emit()
        self.set_playing(False)

    def _on_volume_changed(self, value: int) -> None:
        """Handle volume slider change.

        Args:
            value: Slider value (0-100).
        """
        volume = value / 100.0
        self.volume_label.setText(f"{value}%")
        self.volume_changed.emit(volume)

    def set_playing(self, playing: bool) -> None:
        """Set playing state.

        Args:
            playing: True if playing, False if stopped/paused.
        """
        self.is_playing = playing
        if playing:
            self.play_button.setText("⏸ 一時停止")
        else:
            self.play_button.setText("▶ 再生")

    def set_position(self, position: float, duration: float) -> None:
        """Update position display.

        Args:
            position: Current position in seconds.
            duration: Total duration in seconds.
        """
        pos_min, pos_sec = divmod(int(position), 60)
        dur_min, dur_sec = divmod(int(duration), 60)
        self.position_label.setText(
            f"{pos_min}:{pos_sec:02d} / {dur_min}:{dur_sec:02d}"
        )

    def set_volume(self, volume: float) -> None:
        """Set volume slider value.

        Args:
            volume: Volume (0.0 to 1.0).
        """
        self.volume_slider.setValue(int(volume * 100))

    def set_loop(self, enabled: bool) -> None:
        """Set loop checkbox state.

        Args:
            enabled: Loop enabled state.
        """
        self.loop_checkbox.setChecked(enabled)
