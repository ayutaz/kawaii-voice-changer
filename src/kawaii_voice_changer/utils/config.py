"""Configuration management."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Config:
    """Application configuration."""

    # Audio settings
    sample_rate: int = 44100
    buffer_size: int = 512

    # UI settings
    window_width: int = 900
    window_height: int = 700
    theme: str = "fusion"
    language: str = "ja"

    # File settings
    last_directory: str = ""
    recent_files: list[str] = field(default_factory=list)
    max_recent_files: int = 10

    # Playback settings
    default_volume: float = 1.0
    loop_by_default: bool = True
    auto_play_on_load: bool = True

    # Advanced settings
    cache_processed_audio: bool = True
    show_advanced_controls: bool = False

    # Parameter settings
    last_f0_ratio: float = 1.0
    last_formant_ratios: dict[str, float] = field(default_factory=lambda: {"f1": 1.0, "f2": 1.0, "f3": 1.0})
    last_formant_link: bool = True
    last_loop_crossfade_ms: int = 50

    def save(self, path: Path) -> None:
        """Save configuration to JSON file.

        Args:
            path: Path to save configuration.
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, path: Path) -> Config:
        """Load configuration from JSON file.

        Args:
            path: Path to load configuration from.

        Returns:
            Config instance.
        """
        if not path.exists():
            return cls()

        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            return cls.from_dict(data)
        except Exception:
            # Return default config on error
            return cls()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "sample_rate": self.sample_rate,
            "buffer_size": self.buffer_size,
            "window_width": self.window_width,
            "window_height": self.window_height,
            "theme": self.theme,
            "language": self.language,
            "last_directory": self.last_directory,
            "recent_files": self.recent_files,
            "max_recent_files": self.max_recent_files,
            "default_volume": self.default_volume,
            "loop_by_default": self.loop_by_default,
            "auto_play_on_load": self.auto_play_on_load,
            "cache_processed_audio": self.cache_processed_audio,
            "show_advanced_controls": self.show_advanced_controls,
            "last_f0_ratio": self.last_f0_ratio,
            "last_formant_ratios": self.last_formant_ratios,
            "last_formant_link": self.last_formant_link,
            "last_loop_crossfade_ms": self.last_loop_crossfade_ms,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Config:
        """Create from dictionary.

        Args:
            data: Dictionary data.

        Returns:
            Config instance.
        """
        return cls(
            sample_rate=data.get("sample_rate", 44100),
            buffer_size=data.get("buffer_size", 512),
            window_width=data.get("window_width", 900),
            window_height=data.get("window_height", 700),
            theme=data.get("theme", "fusion"),
            language=data.get("language", "ja"),
            last_directory=data.get("last_directory", ""),
            recent_files=data.get("recent_files", []),
            max_recent_files=data.get("max_recent_files", 10),
            default_volume=data.get("default_volume", 1.0),
            loop_by_default=data.get("loop_by_default", True),
            auto_play_on_load=data.get("auto_play_on_load", True),
            cache_processed_audio=data.get("cache_processed_audio", True),
            show_advanced_controls=data.get("show_advanced_controls", False),
            last_f0_ratio=data.get("last_f0_ratio", 1.0),
            last_formant_ratios=data.get("last_formant_ratios", {"f1": 1.0, "f2": 1.0, "f3": 1.0}),
            last_formant_link=data.get("last_formant_link", True),
            last_loop_crossfade_ms=data.get("last_loop_crossfade_ms", 50),
        )

    def add_recent_file(self, file_path: str) -> None:
        """Add file to recent files list.

        Args:
            file_path: File path to add.
        """
        # Remove if already exists
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)

        # Add to beginning
        self.recent_files.insert(0, file_path)

        # Limit size
        if len(self.recent_files) > self.max_recent_files:
            self.recent_files = self.recent_files[: self.max_recent_files]
