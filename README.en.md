# Kawaii Voice Changer 🎤

English | [日本語](README.md)

[![CI](https://github.com/ayutaz/kawaii-voice-changer/actions/workflows/ci.yml/badge.svg)](https://github.com/ayutaz/kawaii-voice-changer/actions/workflows/ci.yml)
[![Release](https://github.com/ayutaz/kawaii-voice-changer/actions/workflows/release.yml/badge.svg)](https://github.com/ayutaz/kawaii-voice-changer/actions/workflows/release.yml)
[![Nightly Build](https://github.com/ayutaz/kawaii-voice-changer/actions/workflows/nightly.yml/badge.svg)](https://github.com/ayutaz/kawaii-voice-changer/actions/workflows/nightly.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)

![](docs/kawaii-voice-changer.png)

A desktop application to find the "cute voice" sweet spot by adjusting fundamental frequency (F0) and formant frequencies (F1-F3). Based on the research paper "[Super Kawaii Vocalics:
Amplifying the "Cute" Factor in Computer Voice](https://arxiv.org/pdf/2507.06235)" (arXiv:2507.06235).

## 📥 Download

### Stable Release
Download the latest stable release from the [Releases page](https://github.com/ayutaz/kawaii-voice-changer/releases/latest).

### Development Build (Nightly)
Try the latest features with [Nightly Build](https://github.com/ayutaz/kawaii-voice-changer/releases/tag/nightly).
※ Development builds may be unstable.

## 🌟 Features

- **Real-time Audio Processing**: Instant feedback as you adjust parameters
- **Independent Control**: Separate control over pitch (F0) and formants (F1-F3)
- **Loop Playback**: Continuous playback for easy comparison
- **Built-in Presets**: Pre-configured kawaii voice settings
- **Cross-platform**: Works on Windows, macOS, and Linux

## 📋 Requirements

- Python 3.12+
- uv (dependency management)
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

# Install uv if not already installed
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

# Linting
uv run ruff check .
uv run ruff format .

# Type checking
uv run mypy src
```

## 🎮 Usage

1. **Load Audio File**: Drag & drop or use file dialog to select audio
2. **Adjust Parameters**:
   - **F0 (Pitch)**: Change voice pitch (0.5x to 2.0x)
   - **F1-F3 (Formants)**: Modify voice characteristics
   - **Link Mode**: Adjust all formants together
3. **Apply Presets**: Choose from built-in kawaii voice presets
4. **Playback Control**: Auto-loop for easy comparison

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

## 🔧 Building Executables

```bash
# Build standalone executable
uv run pyinstaller kawaii_voice_changer.spec --clean

# Or use Makefile
make build
```

## 🧪 Testing

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test
uv run pytest tests/test_audio_processor.py
```

## 📚 Documentation

- [Kawaii Voice Research Report](docs/technical-decisions/kawaii-voice-research-report.md) - About acoustic characteristics of "kawaii voice"

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Pre-commit Hooks

```bash
# Install pre-commit hooks
make pre-commit-install

# Run manually
make pre-commit
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Based on the paper [Super Kawaii Vocalics:
Amplifying the "Cute" Factor in Computer Voice](https://arxiv.org/pdf/2507.06235)
- Uses [WORLD Vocoder](https://github.com/mmorise/World) for high-quality voice analysis and synthesis
- Uses [PySide6](https://www.qt.io/qt-for-python) for cross-platform GUI

## 📮 Contact

- GitHub Issues: [Bug reports and feature requests](https://github.com/ayutaz/kawaii-voice-changer/issues)

## 🛠️ Development Commands

```bash
# Common commands
make help          # Show available commands
make install       # Install dependencies
make run           # Run the application
make test          # Run tests
make lint          # Run linting
make format        # Format code
make clean         # Clean build artifacts
```