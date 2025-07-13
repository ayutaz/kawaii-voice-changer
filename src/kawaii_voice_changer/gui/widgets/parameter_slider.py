"""Parameter slider widget with label and value display."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QSlider, QVBoxLayout, QWidget


class ParameterSlider(QWidget):
    """Slider widget for parameter adjustment."""

    # Signal emitted when value changes
    value_changed = Signal(float)

    def __init__(
        self,
        label: str,
        min_value: float = 0.0,
        max_value: float = 1.0,
        default_value: float = 0.5,
        step: float = 0.01,
        parent: QWidget | None = None,
    ) -> None:
        """Initialize parameter slider.

        Args:
            label: Slider label text.
            min_value: Minimum value.
            max_value: Maximum value.
            default_value: Default value.
            step: Value step size.
            parent: Parent widget.
        """
        super().__init__(parent)
        
        self.min_value = min_value
        self.max_value = max_value
        self.step = step
        
        # Calculate slider range based on step
        self.slider_max = int((max_value - min_value) / step)
        
        self._setup_ui(label, default_value)

    def _setup_ui(self, label: str, default_value: float) -> None:
        """Set up user interface.

        Args:
            label: Label text.
            default_value: Default slider value.
        """
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Label and value display
        label_layout = QHBoxLayout()
        self.label = QLabel(label)
        label_layout.addWidget(self.label)
        
        label_layout.addStretch()
        
        self.value_label = QLabel()
        label_layout.addWidget(self.value_label)
        
        layout.addLayout(label_layout)
        
        # Slider
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(self.slider_max)
        self.slider.valueChanged.connect(self._on_slider_changed)
        layout.addWidget(self.slider)
        
        # Set default value
        self.set_value(default_value)

    def _on_slider_changed(self, slider_value: int) -> None:
        """Handle slider value change.

        Args:
            slider_value: Slider position value.
        """
        # Convert slider position to actual value
        actual_value = self.min_value + (slider_value * self.step)
        self.value_label.setText(f"{actual_value:.2f}x")
        self.value_changed.emit(actual_value)

    def value(self) -> float:
        """Get current value.

        Returns:
            Current slider value.
        """
        slider_value = self.slider.value()
        return self.min_value + (slider_value * self.step)

    def set_value(self, value: float) -> None:
        """Set slider value.

        Args:
            value: Value to set.
        """
        # Clamp value to range
        value = max(self.min_value, min(self.max_value, value))
        
        # Convert to slider position
        slider_value = int((value - self.min_value) / self.step)
        self.slider.setValue(slider_value)

    def set_enabled(self, enabled: bool) -> None:
        """Set widget enabled state.

        Args:
            enabled: True to enable, False to disable.
        """
        self.slider.setEnabled(enabled)
        self.label.setEnabled(enabled)
        self.value_label.setEnabled(enabled)