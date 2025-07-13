"""Tests for settings manager functionality."""

import pytest

from kawaii_voice_changer.core.settings_manager import SettingsManager, SettingsSlot


class TestSettingsSlot:
    """Test SettingsSlot class."""

    def test_initialization(self) -> None:
        """Test slot initialization."""
        slot = SettingsSlot(name="Test Slot")
        assert slot.name == "Test Slot"
        assert slot.f0_ratio == 1.0
        assert slot.formant_ratios == {"f1": 1.0, "f2": 1.0, "f3": 1.0}
        assert slot.formant_link is True
        assert slot.is_empty is True

    def test_to_dict(self) -> None:
        """Test conversion to dictionary."""
        slot = SettingsSlot(
            name="Test",
            f0_ratio=1.5,
            formant_ratios={"f1": 0.9, "f2": 1.1, "f3": 1.2},
            formant_link=False,
            is_empty=False,
        )

        data = slot.to_dict()
        assert data["name"] == "Test"
        assert data["f0_ratio"] == 1.5
        assert data["formant_ratios"] == {"f1": 0.9, "f2": 1.1, "f3": 1.2}
        assert data["formant_link"] is False
        assert data["is_empty"] is False

    def test_from_dict(self) -> None:
        """Test creation from dictionary."""
        data = {
            "name": "Loaded",
            "f0_ratio": 2.0,
            "formant_ratios": {"f1": 0.8, "f2": 1.0, "f3": 1.3},
            "formant_link": True,
            "is_empty": False,
        }

        slot = SettingsSlot.from_dict(data)
        assert slot.name == "Loaded"
        assert slot.f0_ratio == 2.0
        assert slot.formant_ratios == {"f1": 0.8, "f2": 1.0, "f3": 1.3}
        assert slot.formant_link is True
        assert slot.is_empty is False


class TestSettingsManager:
    """Test SettingsManager class."""

    @pytest.fixture
    def manager(self) -> SettingsManager:
        """Create settings manager."""
        return SettingsManager()

    def test_initialization(self, manager: SettingsManager) -> None:
        """Test manager initialization."""
        assert len(manager.slots) == SettingsManager.MAX_SLOTS
        assert manager.current_slot_index == 0

        # All slots should be empty initially
        for i in range(SettingsManager.MAX_SLOTS):
            assert manager.slots[i].is_empty is True
            assert manager.slots[i].name == f"スロット {i + 1}"

    def test_save_to_slot(self, manager: SettingsManager) -> None:
        """Test saving to a slot."""
        result = manager.save_to_slot(
            0,
            f0_ratio=1.5,
            formant_ratios={"f1": 0.9, "f2": 1.1, "f3": 1.2},
            formant_link=False,
            name="Custom Slot",
        )

        assert result is True
        assert manager.slots[0].is_empty is False
        assert manager.slots[0].f0_ratio == 1.5
        assert manager.slots[0].formant_ratios == {"f1": 0.9, "f2": 1.1, "f3": 1.2}
        assert manager.slots[0].formant_link is False
        assert manager.slots[0].name == "Custom Slot"

    def test_load_from_slot(self, manager: SettingsManager) -> None:
        """Test loading from a slot."""
        # Empty slot should return None
        assert manager.load_from_slot(0) is None

        # Save settings
        manager.save_to_slot(
            0,
            f0_ratio=1.5,
            formant_ratios={"f1": 0.9, "f2": 1.1, "f3": 1.2},
            formant_link=False,
        )

        # Load settings
        settings = manager.load_from_slot(0)
        assert settings is not None
        assert settings["f0_ratio"] == 1.5
        assert settings["formant_ratios"] == {"f1": 0.9, "f2": 1.1, "f3": 1.2}
        assert settings["formant_link"] is False

    def test_clear_slot(self, manager: SettingsManager) -> None:
        """Test clearing a slot."""
        # Save settings
        manager.save_to_slot(
            1,
            f0_ratio=1.5,
            formant_ratios={"f1": 0.9, "f2": 1.1, "f3": 1.2},
            formant_link=False,
        )

        # Clear slot
        result = manager.clear_slot(1)
        assert result is True
        assert manager.slots[1].is_empty is True
        assert manager.slots[1].name == "スロット 2"

    def test_get_slot_info(self, manager: SettingsManager) -> None:
        """Test getting slot information."""
        # Empty slot
        info = manager.get_slot_info(0)
        assert info is not None
        assert info["is_empty"] is True
        assert info["f0_ratio"] is None

        # Filled slot
        manager.save_to_slot(
            0,
            f0_ratio=1.5,
            formant_ratios={"f1": 0.9, "f2": 1.1, "f3": 1.2},
            formant_link=False,
        )

        info = manager.get_slot_info(0)
        assert info is not None
        assert info["is_empty"] is False
        assert info["f0_ratio"] == 1.5

    def test_current_slot_management(self, manager: SettingsManager) -> None:
        """Test current slot management."""
        assert manager.get_current_slot() == 0

        # Set current slot
        assert manager.set_current_slot(2) is True
        assert manager.get_current_slot() == 2

        # Invalid index
        assert manager.set_current_slot(10) is False
        assert manager.get_current_slot() == 2  # Should remain unchanged

    def test_rename_slot(self, manager: SettingsManager) -> None:
        """Test renaming a slot."""
        assert manager.rename_slot(0, "My Custom Slot") is True
        assert manager.slots[0].name == "My Custom Slot"

        # Invalid index
        assert manager.rename_slot(10, "Invalid") is False

    def test_serialization(self, manager: SettingsManager) -> None:
        """Test to_dict and from_dict."""
        # Save some settings
        manager.save_to_slot(
            0,
            f0_ratio=1.5,
            formant_ratios={"f1": 0.9, "f2": 1.1, "f3": 1.2},
            formant_link=False,
        )
        manager.save_to_slot(
            2,
            f0_ratio=2.0,
            formant_ratios={"f1": 0.8, "f2": 1.0, "f3": 1.3},
            formant_link=True,
        )
        manager.set_current_slot(2)

        # Serialize
        data = manager.to_dict()

        # Create new manager and load
        new_manager = SettingsManager()
        new_manager.from_dict(data)

        # Verify
        assert new_manager.current_slot_index == 2
        assert new_manager.slots[0].is_empty is False
        assert new_manager.slots[0].f0_ratio == 1.5
        assert new_manager.slots[2].is_empty is False
        assert new_manager.slots[2].f0_ratio == 2.0

    def test_boundary_conditions(self, manager: SettingsManager) -> None:
        """Test boundary conditions."""
        # Invalid slot indices
        assert manager.save_to_slot(-1, 1.0, {}, True) is False
        assert manager.save_to_slot(4, 1.0, {}, True) is False
        assert manager.load_from_slot(-1) is None
        assert manager.load_from_slot(4) is None
        assert manager.clear_slot(-1) is False
        assert manager.clear_slot(4) is False
        assert manager.get_slot_info(-1) is None
        assert manager.get_slot_info(4) is None
