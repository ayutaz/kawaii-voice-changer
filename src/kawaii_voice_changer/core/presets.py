"""Preset definitions for voice effects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Preset:
    """Voice effect preset."""

    name: str
    f0_ratio: float
    formant_ratios: dict[str, float]
    formant_link: bool
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert preset to dictionary.

        Returns:
            Dictionary representation of preset.
        """
        return {
            "name": self.name,
            "f0_ratio": self.f0_ratio,
            "formant_ratios": self.formant_ratios.copy(),
            "formant_link": self.formant_link,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Preset:
        """Create preset from dictionary.

        Args:
            data: Dictionary containing preset data.

        Returns:
            Preset instance.
        """
        return cls(
            name=data["name"],
            f0_ratio=data["f0_ratio"],
            formant_ratios=data["formant_ratios"].copy(),
            formant_link=data.get("formant_link", True),
            description=data.get("description", ""),
        )


# Built-in presets
PRESETS = {
    "オリジナル": Preset(
        name="オリジナル",
        f0_ratio=1.0,
        formant_ratios={"f1": 1.0, "f2": 1.0, "f3": 1.0},
        formant_link=True,
        description="元の音声そのまま",
    ),
    "可愛い声1": Preset(
        name="可愛い声1",
        f0_ratio=1.2,
        formant_ratios={"f1": 1.3, "f2": 1.3, "f3": 1.3},
        formant_link=True,
        description="やや高めの可愛い声",
    ),
    "可愛い声2": Preset(
        name="可愛い声2",
        f0_ratio=1.15,
        formant_ratios={"f1": 1.4, "f2": 1.4, "f3": 1.4},
        formant_link=True,
        description="フォルマント強調の可愛い声",
    ),
    "アニメ声": Preset(
        name="アニメ声",
        f0_ratio=1.3,
        formant_ratios={"f1": 1.5, "f2": 1.5, "f3": 1.5},
        formant_link=True,
        description="アニメキャラクター風の声",
    ),
    "ロボット声": Preset(
        name="ロボット声",
        f0_ratio=1.0,
        formant_ratios={"f1": 0.8, "f2": 0.8, "f3": 0.8},
        formant_link=True,
        description="機械的な声",
    ),
}