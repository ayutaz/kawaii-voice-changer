# Contributing to Kawaii Voice Changer

Thank you for your interest in contributing to Kawaii Voice Changer! This document provides guidelines and instructions for contributing.

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- uv (for dependency management)
- Git

### Development Setup

1. Fork and clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/kawaii-voice-changer.git
cd kawaii-voice-changer
```

2. Install uv if you haven't already:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

3. Install development dependencies:
```bash
make install-dev
```

4. Install pre-commit hooks:
```bash
make pre-commit-install
```

5. Generate test audio files:
```bash
make generate-audio
```

## 🧪 Development Workflow

### Running the Application

```bash
make run
```

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-cov
```

### Code Quality

Before submitting a PR, ensure your code passes all checks:

```bash
# Format code
make format

# Run linting
make lint

# Type checking
make type-check

# Run all pre-commit hooks
make pre-commit
```

## 📝 Code Style

- We use `ruff` for linting and formatting
- Follow PEP 8 guidelines
- Use type hints for all function signatures
- Write docstrings for all public functions and classes

### Example Function

```python
def process_audio(
    audio_data: np.ndarray,
    sample_rate: int = 44100,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Process audio data with effects.
    
    Args:
        audio_data: Input audio samples.
        sample_rate: Sample rate in Hz.
        
    Returns:
        Tuple of (processed_audio, metadata).
        
    Raises:
        ValueError: If audio_data is empty.
    """
    if len(audio_data) == 0:
        raise ValueError("Audio data cannot be empty")
        
    # Processing logic here
    processed = audio_data * 0.5
    metadata = {"gain": -6.0}
    
    return processed, metadata
```

## 🏗️ Project Structure

```
kawaii-voice-changer/
├── src/kawaii_voice_changer/
│   ├── core/          # Audio processing core
│   ├── gui/           # GUI components
│   └── utils/         # Utilities
├── tests/             # Test files
├── docs/              # Documentation
├── scripts/           # Helper scripts
└── resources/         # Assets
```

## 🧩 Adding New Features

1. Create a new branch:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes following the code style

3. Add tests for new functionality

4. Update documentation if needed

5. Commit your changes:
```bash
git add .
git commit -m "feat: Add your feature description"
```

### Commit Message Convention

We follow conventional commits:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Test additions or modifications
- `chore:` Maintenance tasks

## 🐛 Reporting Issues

### Bug Reports

Please include:
- Python version
- Operating system
- Steps to reproduce
- Expected behavior
- Actual behavior
- Error messages/logs

### Feature Requests

Please describe:
- The problem you're trying to solve
- Your proposed solution
- Any alternatives considered

## 📚 Documentation

- Update docstrings for any API changes
- Update README.md for user-facing changes
- Add technical documentation in `docs/` for complex features

## ✅ Pull Request Process

1. Ensure all tests pass
2. Update documentation
3. Add an entry to CHANGELOG.md (if it exists)
4. Request review from maintainers
5. Address review feedback

### PR Checklist

- [ ] Tests pass (`make test`)
- [ ] Code is formatted (`make format`)
- [ ] Type hints added
- [ ] Documentation updated
- [ ] Commit messages follow convention

## 🤝 Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Provide constructive feedback
- Focus on what is best for the community

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 🙏 Thank You!

Your contributions make this project better for everyone. Thank you for taking the time to contribute!