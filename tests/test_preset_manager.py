"""Tests for preset manager functionality."""

import json
from pathlib import Path

import pytest

from kawaii_voice_changer.core import Preset, PresetManager


class TestPresetManager:
    """Test preset manager functionality."""

    @pytest.fixture
    def preset_manager(self, tmp_path: Path) -> PresetManager:
        """Create preset manager with temporary directory."""
        return PresetManager(preset_dir=tmp_path / "presets")

    @pytest.fixture
    def test_preset(self) -> Preset:
        """Create test preset."""
        return Preset(
            name="Test Preset",
            description="A test preset",
            f0_ratio=1.2,
            formant_ratios={"f1": 0.9, "f2": 1.1, "f3": 1.3},
            formant_link=False,
        )

    def test_initialization(self, preset_manager: PresetManager) -> None:
        """Test preset manager initialization."""
        assert preset_manager.preset_dir.exists()
        assert preset_manager.list_presets() == []

    def test_save_preset(
        self, preset_manager: PresetManager, test_preset: Preset
    ) -> None:
        """Test saving a preset."""
        # Save preset
        result = preset_manager.save_preset(test_preset)
        assert result is True

        # Check that file was created
        preset_file = preset_manager.preset_dir / "test_preset.json"
        assert preset_file.exists()

        # Check file contents
        with preset_file.open("r") as f:
            data = json.load(f)
        assert data["name"] == "Test Preset"
        assert data["description"] == "A test preset"
        assert data["f0_ratio"] == 1.2
        assert data["formant_ratios"] == {"f1": 0.9, "f2": 1.1, "f3": 1.3}
        assert data["formant_link"] is False

        # Check that preset is in cache
        assert preset_manager.preset_exists("Test Preset")

    def test_load_presets(self, tmp_path: Path) -> None:
        """Test loading presets from disk."""
        preset_dir = tmp_path / "presets"
        preset_dir.mkdir()

        # Create preset file manually
        preset_data = {
            "name": "Loaded Preset",
            "description": "A loaded preset",
            "f0_ratio": 1.5,
            "formant_ratios": {"f1": 1.0, "f2": 1.2, "f3": 1.4},
            "formant_link": True,
        }
        preset_file = preset_dir / "loaded_preset.json"
        with preset_file.open("w") as f:
            json.dump(preset_data, f)

        # Create manager and check it loaded the preset
        manager = PresetManager(preset_dir=preset_dir)
        assert "Loaded Preset" in manager.list_presets()

        preset = manager.get_preset("Loaded Preset")
        assert preset is not None
        assert preset.name == "Loaded Preset"
        assert preset.f0_ratio == 1.5

    def test_delete_preset(
        self, preset_manager: PresetManager, test_preset: Preset
    ) -> None:
        """Test deleting a preset."""
        # Save preset first
        preset_manager.save_preset(test_preset)
        assert preset_manager.preset_exists("Test Preset")

        # Delete preset
        result = preset_manager.delete_preset("Test Preset")
        assert result is True

        # Check that preset is gone
        assert not preset_manager.preset_exists("Test Preset")
        assert "Test Preset" not in preset_manager.list_presets()

        # Check that file is gone
        preset_file = preset_manager.preset_dir / "test_preset.json"
        assert not preset_file.exists()

    def test_get_preset(
        self, preset_manager: PresetManager, test_preset: Preset
    ) -> None:
        """Test getting a preset."""
        # Should return None for non-existent preset
        assert preset_manager.get_preset("Non-existent") is None

        # Save and get preset
        preset_manager.save_preset(test_preset)
        retrieved = preset_manager.get_preset("Test Preset")

        assert retrieved is not None
        assert retrieved.name == test_preset.name
        assert retrieved.f0_ratio == test_preset.f0_ratio
        assert retrieved.formant_ratios == test_preset.formant_ratios

    def test_list_presets(self, preset_manager: PresetManager) -> None:
        """Test listing presets."""
        # Empty initially
        assert preset_manager.list_presets() == []

        # Add multiple presets
        for i in range(3):
            preset = Preset(
                name=f"Preset {i}",
                description="",
                f0_ratio=1.0 + i * 0.1,
                formant_ratios={"f1": 1.0, "f2": 1.0, "f3": 1.0},
                formant_link=True,
            )
            preset_manager.save_preset(preset)

        # Should be sorted
        presets = preset_manager.list_presets()
        assert presets == ["Preset 0", "Preset 1", "Preset 2"]

    def test_export_import_preset(
        self, preset_manager: PresetManager, test_preset: Preset, tmp_path: Path
    ) -> None:
        """Test exporting and importing presets."""
        # Save preset
        preset_manager.save_preset(test_preset)

        # Export to file
        export_path = tmp_path / "exported.json"
        result = preset_manager.export_preset("Test Preset", export_path)
        assert result is True
        assert export_path.exists()

        # Create new manager and import
        new_manager = PresetManager(preset_dir=tmp_path / "new_presets")
        imported = new_manager.import_preset(export_path)

        assert imported is not None
        assert imported.name == test_preset.name
        assert new_manager.preset_exists("Test Preset")

    def test_overwrite_preset(
        self, preset_manager: PresetManager, test_preset: Preset
    ) -> None:
        """Test overwriting an existing preset."""
        # Save original
        preset_manager.save_preset(test_preset)

        # Create modified version
        modified = Preset(
            name="Test Preset",  # Same name
            description="Modified description",
            f0_ratio=2.0,  # Different value
            formant_ratios={"f1": 0.5, "f2": 0.5, "f3": 0.5},
            formant_link=True,
        )

        # Save should overwrite
        result = preset_manager.save_preset(modified)
        assert result is True

        # Check that it was overwritten
        retrieved = preset_manager.get_preset("Test Preset")
        assert retrieved is not None
        assert retrieved.description == "Modified description"
        assert retrieved.f0_ratio == 2.0
        assert retrieved.formant_link is True
