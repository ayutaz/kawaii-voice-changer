"""Settings slot management for storing multiple parameter sets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class SettingsSlot:
    """A single settings slot containing parameter values."""

    name: str
    f0_ratio: float = 1.0
    formant_ratios: dict[str, float] | None = None
    formant_link: bool = True
    is_empty: bool = True

    def __post_init__(self) -> None:
        """Initialize formant ratios if not provided."""
        if self.formant_ratios is None:
            self.formant_ratios = {"f1": 1.0, "f2": 1.0, "f3": 1.0}

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "name": self.name,
            "f0_ratio": self.f0_ratio,
            "formant_ratios": self.formant_ratios.copy() if self.formant_ratios else {},
            "formant_link": self.formant_link,
            "is_empty": self.is_empty,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SettingsSlot:
        """Create from dictionary."""
        return cls(
            name=data.get("name", ""),
            f0_ratio=data.get("f0_ratio", 1.0),
            formant_ratios=data.get("formant_ratios"),
            formant_link=data.get("formant_link", True),
            is_empty=data.get("is_empty", True),
        )


class SettingsManager:
    """Manages multiple settings slots."""

    MAX_SLOTS = 4

    def __init__(self) -> None:
        """Initialize settings manager."""
        self.slots: list[SettingsSlot] = []
        self.current_slot_index = 0

        # Initialize empty slots
        for i in range(self.MAX_SLOTS):
            self.slots.append(SettingsSlot(name=f"スロット {i + 1}"))

    def save_to_slot(
        self,
        index: int,
        f0_ratio: float,
        formant_ratios: dict[str, float],
        formant_link: bool,
        name: str | None = None,
    ) -> bool:
        """Save settings to a specific slot.

        Args:
            index: Slot index (0-3).
            f0_ratio: F0 ratio value.
            formant_ratios: Formant ratios dictionary.
            formant_link: Formant link state.
            name: Optional custom name for the slot.

        Returns:
            True if successful.
        """
        if not 0 <= index < self.MAX_SLOTS:
            return False

        slot = self.slots[index]
        slot.f0_ratio = f0_ratio
        slot.formant_ratios = formant_ratios.copy()
        slot.formant_link = formant_link
        slot.is_empty = False

        if name:
            slot.name = name

        return True

    def load_from_slot(self, index: int) -> dict[str, Any] | None:
        """Load settings from a specific slot.

        Args:
            index: Slot index (0-3).

        Returns:
            Settings dictionary if successful, None otherwise.
        """
        if not 0 <= index < self.MAX_SLOTS:
            return None

        slot = self.slots[index]
        if slot.is_empty:
            return None

        return {
            "f0_ratio": slot.f0_ratio,
            "formant_ratios": slot.formant_ratios.copy() if slot.formant_ratios else {},
            "formant_link": slot.formant_link,
        }

    def clear_slot(self, index: int) -> bool:
        """Clear a specific slot.

        Args:
            index: Slot index (0-3).

        Returns:
            True if successful.
        """
        if not 0 <= index < self.MAX_SLOTS:
            return False

        self.slots[index] = SettingsSlot(name=f"スロット {index + 1}")
        return True

    def get_slot_info(self, index: int) -> dict[str, Any] | None:
        """Get information about a slot.

        Args:
            index: Slot index (0-3).

        Returns:
            Slot information dictionary.
        """
        if not 0 <= index < self.MAX_SLOTS:
            return None

        slot = self.slots[index]
        return {
            "name": slot.name,
            "is_empty": slot.is_empty,
            "f0_ratio": slot.f0_ratio if not slot.is_empty else None,
            "formant_ratios": slot.formant_ratios.copy() if not slot.is_empty and slot.formant_ratios else None,
            "formant_link": slot.formant_link if not slot.is_empty else None,
        }

    def get_all_slots_info(self) -> list[dict[str, Any]]:
        """Get information about all slots.

        Returns:
            List of slot information dictionaries.
        """
        return [self.get_slot_info(i) for i in range(self.MAX_SLOTS) if self.get_slot_info(i) is not None]

    def set_current_slot(self, index: int) -> bool:
        """Set the current active slot.

        Args:
            index: Slot index (0-3).

        Returns:
            True if successful.
        """
        if not 0 <= index < self.MAX_SLOTS:
            return False

        self.current_slot_index = index
        return True

    def get_current_slot(self) -> int:
        """Get the current active slot index.

        Returns:
            Current slot index.
        """
        return self.current_slot_index

    def rename_slot(self, index: int, name: str) -> bool:
        """Rename a slot.

        Args:
            index: Slot index (0-3).
            name: New name for the slot.

        Returns:
            True if successful.
        """
        if not 0 <= index < self.MAX_SLOTS:
            return False

        self.slots[index].name = name
        return True

    def to_dict(self) -> dict[str, Any]:
        """Convert all slots to dictionary format.

        Returns:
            Dictionary containing all slots data.
        """
        return {
            "slots": [slot.to_dict() for slot in self.slots],
            "current_slot_index": self.current_slot_index,
        }

    def from_dict(self, data: dict[str, Any]) -> None:
        """Load slots from dictionary format.

        Args:
            data: Dictionary containing slots data.
        """
        slots_data = data.get("slots", [])
        for i, slot_data in enumerate(slots_data[:self.MAX_SLOTS]):
            self.slots[i] = SettingsSlot.from_dict(slot_data)

        self.current_slot_index = data.get("current_slot_index", 0)
