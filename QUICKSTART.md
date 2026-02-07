# Quick Start Guide

Get Skynette running in 5 minutes!

> **📚 Need more help?** See [INSTALLATION.md](INSTALLATION.md) for detailed installation instructions, troubleshooting, and platform-specific guides.

## For Users

### Download Pre-built Executable (Easiest)

1. Go to [Releases](https://github.com/flyingpurplepizzaeater/Skynette/releases)
2. Download for your platform:
   - **Windows**: `Skynette.exe`
   - **macOS**: `Skynette.app`
   - **Linux**: `Skynette`
3. Run the executable
4. Done! 🎉

### From Source

```bash
# 1. Clone repository
git clone https://github.com/flyingpurplepizzaeater/Skynette.git
cd Skynette

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 4. Install dependencies (includes AI features)
pip install -e ".[ai,dev]"

# 5. Run application
python src/main.py
```

## For Contributors

### Setup Development Environment

```bash
# 1. Fork and clone your fork
git clone https://github.com/YOUR_USERNAME/Skynette.git
cd Skynette

# 2. Add upstream remote
git remote add upstream https://github.com/flyingpurplepizzaeater/Skynette.git

# 3. Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# 4. Install with dev and AI dependencies
pip install -e ".[ai,dev]"

# 5. Install Playwright browsers (for E2E tests)
playwright install chromium

# 6. Run tests to verify setup
pytest tests/unit/ -v
```

### Make Your First Contribution

```bash
# 1. Create a new branch
git checkout -b feature/my-awesome-feature

# 2. Make your changes
# ... edit code ...

# 3. Run tests
pytest

# 4. Run linter
ruff check src/

# 5. Commit changes
git add .
git commit -m "feat: add awesome feature"

# 6. Push to your fork
git push origin feature/my-awesome-feature

# 7. Open Pull Request on GitHub
```

### Run the Application

```bash
# Development mode
python src/main.py

# With debugging
python src/main.py --debug

# Run tests
pytest

# Run tests with coverage
pytest --cov=src --cov-report=html

# Run E2E tests
pytest tests/e2e/

# Run linter
ruff check src/

# Format code
ruff format src/
```

## Common Tasks

### Run Tests

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/

# E2E tests only
pytest tests/e2e/

# With coverage
pytest --cov=src --cov-report=html
```

### Build Executable

```bash
# For current platform
python scripts/build.py

# Skip tests
python scripts/build.py --skip-tests

# Output in dist/ directory
```

### Create a Release

```bash
# 1. Update version in pyproject.toml
# version = "0.2.0"

# 2. Update CHANGELOG.md

# 3. Commit changes
git add pyproject.toml CHANGELOG.md
git commit -m "Bump version to 0.2.0"

# 4. Create and push tag
git tag v0.2.0
git push origin v0.2.0

# GitHub Actions will automatically build and release
```

### Configure AI Providers

See [docs/AI_PROVIDERS.md](docs/AI_PROVIDERS.md) for detailed setup.

**Quick config** (`~/.skynette/config.yaml`):

```yaml
ai:
  default_provider: openai
  openai:
    api_key: sk-...
  anthropic:
    api_key: sk-ant-...
```

## Troubleshooting

### Import Errors

```bash
# Ensure you're in virtual environment
which python  # Should show venv path

# Reinstall in editable mode with AI features
pip install -e ".[ai,dev]"
```

### Test Failures

```bash
# Clear cache
pytest --cache-clear

# Run with verbose output
pytest -vv
```

### Build Issues

```bash
# Install PyInstaller
pip install pyinstaller

# Clean build
rm -rf build/ dist/
python scripts/build.py
```

## Next Steps

- 📖 Read [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines
- 🗺️ Check [ROADMAP.md](ROADMAP.md) for planned features
- 📚 Browse [docs/](docs/) for comprehensive guides
- 🐛 [Report issues](https://github.com/flyingpurplepizzaeater/Skynette/issues)
- 💬 [Join discussions](https://github.com/flyingpurplepizzaeater/Skynette/discussions)

## Getting Help

- **Documentation**: Check the [docs/](docs/) directory
- **Issues**: [GitHub Issues](https://github.com/flyingpurplepizzaeater/Skynette/issues)
- **Discussions**: [GitHub Discussions](https://github.com/flyingpurplepizzaeater/Skynette/discussions)

---

**Welcome to Skynette! Happy automating! 🚀**
