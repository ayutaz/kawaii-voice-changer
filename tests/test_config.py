"""Tests for configuration module."""

from pathlib import Path

from kawaii_voice_changer.utils import Config


class TestConfig:
    """Test Config class."""

    def test_default_values(self):
        """Test default configuration values."""
        config = Config()

        assert config.sample_rate == 44100
        assert config.buffer_size == 512
        assert config.window_width == 900
        assert config.window_height == 700
        assert config.theme == "fusion"
        assert config.language == "ja"
        assert config.loop_by_default is True
        assert config.auto_play_on_load is True

    def test_to_dict(self):
        """Test conversion to dictionary."""
        config = Config()
        config.last_directory = "/test/path"
        config.recent_files = ["/test/file1.wav", "/test/file2.wav"]

        data = config.to_dict()

        assert isinstance(data, dict)
        assert data["last_directory"] == "/test/path"
        assert data["recent_files"] == ["/test/file1.wav", "/test/file2.wav"]
        assert data["sample_rate"] == 44100

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "sample_rate": 48000,
            "buffer_size": 1024,
            "window_width": 1200,
            "window_height": 800,
            "last_directory": "/custom/path",
            "recent_files": ["/custom/file.wav"],
        }

        config = Config.from_dict(data)

        assert config.sample_rate == 48000
        assert config.buffer_size == 1024
        assert config.window_width == 1200
        assert config.window_height == 800
        assert config.last_directory == "/custom/path"
        assert config.recent_files == ["/custom/file.wav"]

    def test_save_load(self, tmp_path: Path):
        """Test saving and loading configuration."""
        config = Config()
        config.last_directory = "/test/save"
        config.recent_files = ["/test/save1.wav", "/test/save2.wav"]
        config.default_volume = 0.8

        # Save
        config_file = tmp_path / "test_config.json"
        config.save(config_file)

        assert config_file.exists()

        # Load
        loaded_config = Config.load(config_file)

        assert loaded_config.last_directory == "/test/save"
        assert loaded_config.recent_files == ["/test/save1.wav", "/test/save2.wav"]
        assert loaded_config.default_volume == 0.8

    def test_load_nonexistent(self, tmp_path: Path):
        """Test loading non-existent config file."""
        config_file = tmp_path / "nonexistent.json"
        config = Config.load(config_file)

        # Should return default config
        assert config.sample_rate == 44100
        assert config.recent_files == []

    def test_load_invalid_json(self, tmp_path: Path):
        """Test loading invalid JSON file."""
        config_file = tmp_path / "invalid.json"
        config_file.write_text("{ invalid json }")

        config = Config.load(config_file)

        # Should return default config on error
        assert config.sample_rate == 44100

    def test_add_recent_file(self):
        """Test adding recent files."""
        config = Config()
        config.max_recent_files = 3

        # Add files
        config.add_recent_file("/file1.wav")
        config.add_recent_file("/file2.wav")
        config.add_recent_file("/file3.wav")

        assert config.recent_files == ["/file3.wav", "/file2.wav", "/file1.wav"]

        # Add duplicate (should move to front)
        config.add_recent_file("/file1.wav")
        assert config.recent_files == ["/file1.wav", "/file3.wav", "/file2.wav"]

        # Add new file (should remove oldest)
        config.add_recent_file("/file4.wav")
        assert config.recent_files == ["/file4.wav", "/file1.wav", "/file3.wav"]
        assert len(config.recent_files) == 3
