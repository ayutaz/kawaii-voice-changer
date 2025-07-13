.PHONY: help install install-dev test lint format type-check clean build run generate-audio

# Default target
help:
	@echo "Available commands:"
	@echo "  make install       - Install project dependencies"
	@echo "  make install-dev   - Install with development dependencies"
	@echo "  make test         - Run tests"
	@echo "  make lint         - Run linting"
	@echo "  make format       - Format code"
	@echo "  make type-check   - Run type checking"
	@echo "  make clean        - Clean build artifacts"
	@echo "  make build        - Build executable"
	@echo "  make run          - Run the application"
	@echo "  make generate-audio - Generate test audio files"

# Install dependencies
install:
	uv sync

# Install with dev dependencies
install-dev:
	uv sync --all-extras

# Run tests
test:
	uv run pytest tests/ -v

# Run tests with coverage
test-cov:
	uv run pytest tests/ -v --cov=src --cov-report=html --cov-report=term

# Run linting
lint:
	uv run ruff check .

# Format code
format:
	uv run ruff format .
	uv run ruff check --fix .

# Type checking
type-check:
	uv run mypy src

# Clean build artifacts
clean:
	rm -rf build/ dist/ *.egg-info
	rm -rf .coverage htmlcov/ .pytest_cache/
	rm -rf .mypy_cache/ .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Build executable
build:
	uv run pyinstaller kawaii_voice_changer.spec --clean

# Run application
run:
	uv run python -m kawaii_voice_changer

# Generate test audio files
generate-audio:
	uv run python scripts/generate_test_audio.py

# Run pre-commit hooks
pre-commit:
	uv run pre-commit run --all-files

# Install pre-commit hooks
pre-commit-install:
	uv run pre-commit install