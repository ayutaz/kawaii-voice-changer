# Kawaii Voice Changer 🎤

[![CI](https://github.com/ayutaz/kawaii-voice-changer/actions/workflows/ci.yml/badge.svg)](https://github.com/ayutaz/kawaii-voice-changer/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)

A desktop application to find the sweet spot of "kawaii" (cute) voice by adjusting fundamental frequency (F0) and formant frequencies (F1-F3). Based on the research paper "Finding Kawaii" (arXiv:2507.06235).

## 🌟 Features

- **Real-time Voice Processing**: Adjust voice parameters and hear changes instantly
- **Independent Control**: Separate control of pitch (F0) and formants (F1-F3)
- **Loop Playback**: Continuous playback for easy comparison
- **Presets**: Built-in kawaii voice presets
- **Cross-platform**: Works on Windows, macOS, and Linux

## 📋 Requirements

- Python 3.12+
- uv (for dependency management)
- System dependencies:
  - **Windows**: No additional requirements
  - **macOS**: `brew install portaudio libsndfile`
  - **Linux**: `sudo apt-get install libportaudio2 libsndfile1`

## 🚀 Quick Start

### Installation with uv

```bash
# Clone the repository
git clone https://github.com/ayutaz/kawaii-voice-changer.git
cd kawaii-voice-changer

# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Run the application
uv run kawaii-voice-changer
```

### Development Setup

```bash
# Install with development dependencies
uv sync --all-extras

# Run tests
uv run pytest

# Run linting
uv run ruff check .
uv run ruff format .

# Type checking
uv run mypy src
```

## 🎮 Usage

1. **Load Audio File**: Drag and drop an audio file or use the file dialog
2. **Adjust Parameters**:
   - **F0 (Pitch)**: Changes voice pitch (0.5x - 2.0x)
   - **F1-F3 (Formants)**: Changes voice characteristics
   - **Link Mode**: Adjust all formants together
3. **Apply Presets**: Choose from built-in kawaii voice presets
4. **Playback Control**: Auto-loops for easy comparison

## 🏗️ Project Structure

```
kawaii-voice-changer/
├── src/
│   └── kawaii_voice_changer/
│       ├── core/          # Audio processing modules
│       ├── gui/           # GUI components
│       └── utils/         # Utilities
├── tests/                 # Test files
├── docs/                  # Documentation
└── resources/            # Icons, assets
```

## 🔧 Building Executable

```bash
# Build standalone executable
uv run pyinstaller --name=KawaiiVoiceChanger \
                   --onefile \
                   --windowed \
                   --add-data "resources:resources" \
                   src/kawaii_voice_changer/main.py
```

## 🧪 Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test
uv run pytest tests/test_audio_processor.py
```

## 📚 Documentation

- [Requirements Specification](docs/requirements-specification.md)
- [Technical Selection](docs/technical-selection.md)
- [Development Plan](docs/development-plan.md)

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Pre-commit Hooks

```bash
# Install pre-commit hooks
uv run pre-commit install

# Run manually
uv run pre-commit run --all-files
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Based on the research paper "Finding Kawaii: A Study of Kawaii Vocal Aesthetics in Modern Japanese Popular Music" (arXiv:2507.06235)
- Uses [WORLD Vocoder](https://github.com/mmorise/World) for high-quality voice analysis and synthesis
- Built with [PySide6](https://www.qt.io/qt-for-python) for cross-platform GUI

## 📮 Contact

- GitHub Issues: [Report bugs or request features](https://github.com/ayutaz/kawaii-voice-changer/issues)