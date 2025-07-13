"""Preset management functionality."""

from __future__ import annotations

import json
from pathlib import Path

from .presets import Preset


class PresetManager:
    """Manages user-defined presets."""

    def __init__(self, preset_dir: Path | None = None) -> None:
        """Initialize preset manager.

        Args:
            preset_dir: Directory to store presets. Defaults to user config directory.
        """
        if preset_dir is None:
            preset_dir = Path.home() / ".kawaii_voice_changer" / "presets"
        self.preset_dir = preset_dir
        self.preset_dir.mkdir(parents=True, exist_ok=True)

        # Cache of loaded presets
        self._user_presets: dict[str, Preset] = {}
        self._load_presets()

    def _load_presets(self) -> None:
        """Load all user presets from disk."""
        self._user_presets.clear()

        for preset_file in self.preset_dir.glob("*.json"):
            try:
                with preset_file.open("r", encoding="utf-8") as f:
                    data = json.load(f)

                preset = Preset(
                    name=data["name"],
                    description=data.get("description", ""),
                    f0_ratio=data["f0_ratio"],
                    formant_ratios=data["formant_ratios"],
                    formant_link=data.get("formant_link", True),
                )
                self._user_presets[preset.name] = preset

            except Exception as e:
                print(f"Error loading preset {preset_file}: {e}")

    def save_preset(self, preset: Preset) -> bool:
        """Save a preset to disk.

        Args:
            preset: Preset to save.

        Returns:
            True if successful, False otherwise.
        """
        try:
            # Create filename from preset name
            filename = f"{preset.name.replace(' ', '_').lower()}.json"
            preset_path = self.preset_dir / filename

            # Prepare data
            data = {
                "name": preset.name,
                "description": preset.description,
                "f0_ratio": preset.f0_ratio,
                "formant_ratios": preset.formant_ratios,
                "formant_link": preset.formant_link,
            }

            # Write to file
            with preset_path.open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            # Update cache
            self._user_presets[preset.name] = preset

            return True

        except Exception as e:
            print(f"Error saving preset: {e}")
            return False

    def delete_preset(self, name: str) -> bool:
        """Delete a user preset.

        Args:
            name: Name of preset to delete.

        Returns:
            True if successful, False otherwise.
        """
        if name not in self._user_presets:
            return False

        try:
            # Find and delete file
            filename = f"{name.replace(' ', '_').lower()}.json"
            preset_path = self.preset_dir / filename

            if preset_path.exists():
                preset_path.unlink()

            # Remove from cache
            del self._user_presets[name]

            return True

        except Exception as e:
            print(f"Error deleting preset: {e}")
            return False

    def get_preset(self, name: str) -> Preset | None:
        """Get a user preset by name.

        Args:
            name: Preset name.

        Returns:
            Preset if found, None otherwise.
        """
        return self._user_presets.get(name)

    def list_presets(self) -> list[str]:
        """List all user preset names.

        Returns:
            List of preset names.
        """
        return sorted(self._user_presets.keys())

    def get_all_presets(self) -> dict[str, Preset]:
        """Get all user presets.

        Returns:
            Dictionary of preset name to Preset.
        """
        return self._user_presets.copy()

    def preset_exists(self, name: str) -> bool:
        """Check if a preset exists.

        Args:
            name: Preset name.

        Returns:
            True if preset exists.
        """
        return name in self._user_presets

    def export_preset(self, name: str, export_path: Path) -> bool:
        """Export a preset to a file.

        Args:
            name: Preset name.
            export_path: Path to export to.

        Returns:
            True if successful.
        """
        preset = self.get_preset(name)
        if not preset:
            return False

        try:
            data = {
                "name": preset.name,
                "description": preset.description,
                "f0_ratio": preset.f0_ratio,
                "formant_ratios": preset.formant_ratios,
                "formant_link": preset.formant_link,
            }

            with export_path.open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return True

        except Exception as e:
            print(f"Error exporting preset: {e}")
            return False

    def import_preset(self, import_path: Path) -> Preset | None:
        """Import a preset from a file.

        Args:
            import_path: Path to import from.

        Returns:
            Imported preset if successful, None otherwise.
        """
        try:
            with import_path.open("r", encoding="utf-8") as f:
                data = json.load(f)

            preset = Preset(
                name=data["name"],
                description=data.get("description", ""),
                f0_ratio=data["f0_ratio"],
                formant_ratios=data["formant_ratios"],
                formant_link=data.get("formant_link", True),
            )

            # Save to presets directory
            if self.save_preset(preset):
                return preset

            return None

        except Exception as e:
            print(f"Error importing preset: {e}")
            return None
