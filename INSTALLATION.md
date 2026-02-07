# Skynette Installation Guide

Complete guide for installing, building, and running Skynette on your local machine.

## Table of Contents

- [Installation Methods](#installation-methods)
  - [Method 1: Install from PyPI (Recommended)](#method-1-install-from-pypi-recommended)
  - [Method 2: Pre-built Executables](#method-2-pre-built-executables)
  - [Method 3: Install from Source](#method-3-install-from-source)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Detailed Installation](#detailed-installation)
  - [Step 1: Install Prerequisites](#step-1-install-prerequisites)
  - [Step 2: Clone Repository](#step-2-clone-repository)
  - [Step 3: Set Up Virtual Environment](#step-3-set-up-virtual-environment)
  - [Step 4: Install Dependencies](#step-4-install-dependencies)
  - [Step 5: Run the Application](#step-5-run-the-application)
- [Building from Source](#building-from-source)
- [Platform-Specific Instructions](#platform-specific-instructions)
  - [Windows](#windows)
  - [macOS](#macos)
  - [Linux](#linux)
- [Optional Features](#optional-features)
- [Troubleshooting](#troubleshooting)
- [Verifying Installation](#verifying-installation)

---

## Installation Methods

### Method 1: Install from PyPI (Recommended)

The easiest way to install Skynette is via pip from the Python Package Index (PyPI).

**Prerequisites:**
- Python 3.11 or 3.12
- pip (usually comes with Python)

**Installation:**

```bash
# Basic installation
pip install skynette

# Install with AI features (recommended)
pip install skynette[ai]

# Install with database integrations
pip install skynette[databases]

# Install with cloud service integrations
pip install skynette[cloud]

# Install with all optional features
pip install skynette[all]
```

**Running Skynette:**

```bash
# Run with the command-line tool
skynette

# Or run as a Python module
python -m src.main
```

**Upgrade to the latest version:**

```bash
pip install --upgrade skynette
```

---

### Method 2: Pre-built Executables

Download ready-to-run executables from the [GitHub Releases](https://github.com/flyingpurplepizzaeater/Skynette/releases) page.

#### Windows

1. Download `Skynette-Windows.zip` from the latest release
2. Extract the ZIP file to a folder (e.g., `C:\Program Files\Skynette`)
3. Run `Skynette.exe`
4. (Optional) Create a desktop shortcut for easy access

#### macOS

**Option A: DMG Installer**
1. Download `Skynette.dmg` from the latest release
2. Open the DMG file
3. Drag `Skynette.app` to your Applications folder
4. Launch from Applications or Spotlight

**Option B: ZIP Archive**
1. Download `Skynette-macOS.zip` from the latest release
2. Extract the ZIP file
3. Move `Skynette.app` to your Applications folder
4. Right-click and select "Open" the first time (to bypass Gatekeeper)

#### Linux

**Option A: AppImage (Universal)**
1. Download `Skynette-*.AppImage` from the latest release
2. Make it executable: `chmod +x Skynette-*.AppImage`
3. Run: `./Skynette-*.AppImage`
4. (Optional) Use AppImageLauncher for desktop integration

**Option B: Debian/Ubuntu Package**
1. Download `skynette_*.deb` from the latest release
2. Install: `sudo dpkg -i skynette_*.deb`
3. Run: `skynette` or find it in your application menu

**Option C: Tarball**
1. Download `Skynette-Linux.tar.gz` from the latest release
2. Extract: `tar -xzvf Skynette-Linux.tar.gz`
3. Run: `cd Skynette && ./Skynette`

**Verifying Downloads:**

All releases include a `SHA256SUMS.txt` file for integrity verification:

```bash
# Download the release and checksums file
# Then verify:
sha256sum -c SHA256SUMS.txt
```

---

### Method 3: Install from Source

For developers or users who want the latest features.

See the [Quick Start](#quick-start) and [Detailed Installation](#detailed-installation) sections below.

---

## Prerequisites

### System Requirements

- **Operating System**: 
  - Windows 10 or later
  - macOS 11 (Big Sur) or later
  - Linux (Ubuntu 20.04+, Debian, Fedora, or similar)

- **Python**: Version 3.11 or 3.12 (required)
  - Python 3.11 is recommended for maximum compatibility
  - Python 3.12 is also supported

- **RAM**: 
  - Minimum: 4GB
  - Recommended: 8GB
  - For local AI models: 16GB+

- **Storage**:
  - Application: ~2GB
  - Per local AI model: 4-8GB each
  - Workspace data: Variable

- **GPU** (Optional):
  - NVIDIA GPU with CUDA support for faster local AI model inference
  - Not required for basic functionality or cloud AI providers

### Software Dependencies

- **Git**: For cloning the repository
- **Python 3.11+**: With pip and venv support
- **Internet Connection**: For downloading dependencies and AI models

---

## Quick Start

**For users who want to run the application immediately:**

```bash
# 1. Clone the repository
git clone https://github.com/flyingpurplepizzaeater/Skynette.git
cd Skynette

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Linux/macOS
# OR
venv\Scripts\activate     # On Windows

# 3. Install with AI features
pip install -e ".[ai,dev]"

# 4. Run the application
python src/main.py
```

That's it! Skynette should launch with its graphical interface.

---

## Detailed Installation

### Step 1: Install Prerequisites

#### Install Python 3.11 or 3.12

**Windows:**
1. Download Python from [python.org](https://www.python.org/downloads/)
2. Run the installer
3. ✅ **Important**: Check "Add Python to PATH" during installation
4. Verify installation:
   ```cmd
   python --version
   ```
   Should show `Python 3.11.x` or `Python 3.12.x`

**macOS:**
```bash
# Using Homebrew (recommended)
brew install python@3.11

# Or download from python.org
# Verify installation
python3 --version
```

**Linux (Ubuntu/Debian):**
```bash
# Update package list
sudo apt update

# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3.11-dev

# Or Python 3.12
sudo apt install python3.12 python3.12-venv python3.12-dev

# Verify installation
python3.11 --version
```

**Linux (Fedora):**
```bash
sudo dnf install python3.11 python3.11-devel
```

#### Install Git

**Windows:**
- Download from [git-scm.com](https://git-scm.com/download/win)
- Run the installer with default settings

**macOS:**
```bash
# Using Homebrew
brew install git

# Or install Xcode Command Line Tools
xcode-select --install
```

**Linux:**
```bash
# Ubuntu/Debian
sudo apt install git

# Fedora
sudo dnf install git
```

Verify Git installation:
```bash
git --version
```

### Step 2: Clone Repository

```bash
# Clone the repository
git clone https://github.com/flyingpurplepizzaeater/Skynette.git

# Navigate to the project directory
cd Skynette

# Verify you're in the right directory
ls
# You should see: README.md, src/, pyproject.toml, requirements.txt, etc.
```

### Step 3: Set Up Virtual Environment

A virtual environment isolates Skynette's dependencies from your system Python.

**Create virtual environment:**

```bash
# On all platforms
python -m venv venv

# On Linux/macOS, if python points to Python 2.x, use:
python3.11 -m venv venv
# or
python3.12 -m venv venv
```

**Activate virtual environment:**

**Windows (Command Prompt):**
```cmd
venv\Scripts\activate
```

**Windows (PowerShell):**
```powershell
venv\Scripts\Activate.ps1
```

**Linux/macOS:**
```bash
source venv/bin/activate
```

**Verify activation:**
After activation, your command prompt should show `(venv)` at the beginning.

```bash
# Verify Python is from the virtual environment
which python   # Linux/macOS
where python   # Windows

# Should point to venv/bin/python or venv\Scripts\python.exe
```

### Step 4: Install Dependencies

**Skynette offers different installation options:**

#### Option A: Full Installation (Recommended)

Includes all features: AI, RAG, development tools
```bash
pip install -e ".[ai,dev]"
```

#### Option B: AI Features Only

Includes AI providers and RAG, without dev tools
```bash
pip install -e ".[ai]"
```

#### Option C: Basic Installation

Core features only (no AI)
```bash
pip install -e .
```

#### Option D: Everything

All optional dependencies
```bash
pip install -e ".[all,dev]"
```

**Installation may take 5-10 minutes depending on your internet speed and system.**

**Troubleshooting Installation:**

If you encounter errors during installation:

1. **Upgrade pip:**
   ```bash
   pip install --upgrade pip setuptools wheel
   ```

2. **Install build tools (if needed):**
   - **Windows**: Install [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
   - **macOS**: Install Xcode Command Line Tools: `xcode-select --install`
   - **Linux**: Install build essentials: `sudo apt install build-essential python3-dev`

3. **For llama-cpp-python issues:**
   ```bash
   # Use prebuilt wheels (no compilation needed)
   pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
   ```

### Step 5: Run the Application

**Run Skynette:**

```bash
# Method 1: Using Python directly
python src/main.py

# Method 2: Using Flet (if flet is installed)
flet run src/main.py

# Method 3: Using the skynette command (after installation)
skynette
```

**Alternative entry points:**

```bash
# Using the root script (works from project root)
python skynette.py

# With web interface (for testing)
python skynette.py --web
```

**First Launch:**

On first launch, Skynette will:
1. Create configuration directory at `~/.skynette/`
2. Show the AI Hub Setup Wizard
3. Prompt you to configure AI providers (optional)

You can skip the wizard and configure providers later.

---

## Building from Source

Build standalone executables for distribution.

### Prerequisites for Building

```bash
# Install PyInstaller (included in dev dependencies)
pip install pyinstaller

# For Windows builds
pip install pywin32

# For macOS builds
# No additional requirements

# For Linux builds
# No additional requirements
```

### Build Executables

**Build for your current platform:**

```bash
# Using build script
python scripts/build.py

# Output will be in dist/ directory
```

**Platform-specific build scripts:**

```bash
# Windows
python build_windows.py

# macOS
python build_macos.py

# Linux
python build_linux.py

# All platforms
python build_all.py
```

**Build artifacts:**
- **Windows**: `dist/Skynette.exe` or `Skynette-Setup.exe` (installer)
- **macOS**: `dist/Skynette.app` or `Skynette.dmg`
- **Linux**: `dist/Skynette` or `Skynette.AppImage`

---

## Platform-Specific Instructions

### Windows

**Complete Windows Installation:**

```cmd
REM 1. Open Command Prompt or PowerShell as Administrator
REM 2. Verify Python installation
python --version

REM 3. Clone repository
cd %USERPROFILE%\Documents
git clone https://github.com/flyingpurplepizzaeater/Skynette.git
cd Skynette

REM 4. Create virtual environment
python -m venv venv

REM 5. Activate virtual environment
venv\Scripts\activate

REM 6. Upgrade pip
python -m pip install --upgrade pip

REM 7. Install Skynette with AI features
pip install -e ".[ai,dev]"

REM 8. Run the application
python src\main.py
```

**Windows-Specific Notes:**

- If you encounter "python not recognized", ensure Python is in your PATH
- For PowerShell execution policy errors:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```
- Windows Defender may scan files during installation (this is normal)
- Use `python` instead of `python3` on Windows

**Building Windows Installer:**

```cmd
REM Create MSI installer
python setup_msi.py
```

### macOS

**Complete macOS Installation:**

```bash
# 1. Open Terminal
# 2. Verify Python installation
python3 --version

# 3. Clone repository
cd ~/Documents
git clone https://github.com/flyingpurplepizzaeater/Skynette.git
cd Skynette

# 4. Create virtual environment
python3.11 -m venv venv

# 5. Activate virtual environment
source venv/bin/activate

# 6. Upgrade pip
pip install --upgrade pip

# 7. Install Skynette with AI features
pip install -e ".[ai,dev]"

# 8. Run the application
python src/main.py
```

**macOS-Specific Notes:**

- Use `python3` instead of `python` (may point to Python 2.7)
- You may need to install Xcode Command Line Tools:
  ```bash
  xcode-select --install
  ```
- For M1/M2 Macs (Apple Silicon):
  - All dependencies should work natively
  - For llama-cpp-python with Metal (GPU acceleration):
    ```bash
    CMAKE_ARGS="-DLLAMA_METAL=on" pip install llama-cpp-python --force-reinstall --no-cache-dir
    ```

**Building macOS App:**

```bash
# Create .app bundle
python build_macos.py

# Create DMG installer
# (Requires create-dmg: brew install create-dmg)
```

### Linux

**Complete Linux Installation (Ubuntu/Debian):**

```bash
# 1. Open Terminal
# 2. Update package list
sudo apt update

# 3. Install Python 3.11 and dependencies
sudo apt install python3.11 python3.11-venv python3.11-dev git build-essential

# 4. Clone repository
cd ~/Documents
git clone https://github.com/flyingpurplepizzaeater/Skynette.git
cd Skynette

# 5. Create virtual environment
python3.11 -m venv venv

# 6. Activate virtual environment
source venv/bin/activate

# 7. Upgrade pip
pip install --upgrade pip

# 8. Install Skynette with AI features
pip install -e ".[ai,dev]"

# 9. Run the application
python src/main.py
```

**Linux-Specific Notes:**

- Use `python3.11` or `python3.12` explicitly
- You may need additional libraries for Flet GUI:
  ```bash
  # Ubuntu/Debian
  sudo apt install libgtk-3-0 libglib2.0-0 libgdk-pixbuf2.0-0 libcairo2 libpango-1.0-0

  # Fedora
  sudo dnf install gtk3 glib2 gdk-pixbuf2 cairo pango
  ```

- For CUDA support (NVIDIA GPU):
  ```bash
  # Install CUDA toolkit from NVIDIA
  # Then install llama-cpp-python with CUDA:
  CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python --force-reinstall --no-cache-dir
  ```

**Building Linux AppImage:**

```bash
# Create AppImage
python build_linux.py

# Make it executable
chmod +x dist/Skynette.AppImage

# Run AppImage
./dist/Skynette.AppImage
```

---

## Optional Features

### Installing Additional Dependencies

**Database Support:**
```bash
pip install -e ".[databases]"
```
Adds: PostgreSQL, MySQL, MongoDB drivers

**Cloud Services:**
```bash
pip install -e ".[cloud]"
```
Adds: Google Drive, AWS S3, Dropbox integrations

**Everything:**
```bash
pip install -e ".[all,dev]"
```

### Setting Up E2E Tests

For contributors who want to run end-to-end tests:

```bash
# Install Playwright
pip install playwright pytest-playwright

# Install browser drivers
playwright install chromium

# Run E2E tests
pytest tests/e2e/
```

### Configuring AI Providers

See [docs/AI_PROVIDERS.md](docs/AI_PROVIDERS.md) for detailed setup of:
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- Google AI (Gemini)
- Groq (Fast inference)
- Local models (LLaMA, Mistral, Phi)

**Quick Configuration:**

1. Launch Skynette
2. Complete the AI Hub Setup Wizard
3. Enter API keys (stored securely in system keyring)
4. Or configure manually in `~/.skynette/config.yaml`

---

## Troubleshooting

### Common Issues and Solutions

#### 1. "python: command not found"

**Solution:**
- **Windows**: Add Python to PATH during installation
- **macOS/Linux**: Use `python3`, `python3.11`, or `python3.12`

#### 2. "pip: command not found"

**Solution:**
```bash
# Use Python module directly
python -m pip install --upgrade pip

# Or reinstall pip
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python get-pip.py
```

#### 3. "Permission denied" errors

**Solution:**
```bash
# Don't use sudo with pip (it breaks virtual environments)
# Instead, ensure virtual environment is activated

# If you must install globally (not recommended):
pip install --user <package>
```

#### 4. Virtual environment activation not working

**Windows PowerShell:**
```powershell
# Set execution policy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then activate
venv\Scripts\Activate.ps1
```

**Linux/macOS:**
```bash
# Ensure script is executable
chmod +x venv/bin/activate

# Source the script
source venv/bin/activate
```

#### 5. "ImportError: No module named 'flet'"

**Solution:**
```bash
# Ensure virtual environment is activated
# Reinstall dependencies
pip install -e ".[ai,dev]"
```

#### 6. llama-cpp-python installation fails

**Solution:**
```bash
# Use prebuilt wheels (faster, no compilation)
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu

# For GPU support (CUDA)
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121

# For macOS Metal (Apple Silicon)
CMAKE_ARGS="-DLLAMA_METAL=on" pip install llama-cpp-python --force-reinstall --no-cache-dir
```

#### 7. Application crashes on startup

**Solution:**
```bash
# Check logs
# Windows: logs/ directory in Skynette folder
# Linux/macOS: ~/.skynette/logs/

# Run with verbose output
python src/main.py --debug

# Verify dependencies
pip list | grep flet
pip list | grep llama
```

#### 8. "Address already in use" (web mode)

**Solution:**
```bash
# Kill process using port 8550
# Linux/macOS:
lsof -ti:8550 | xargs kill -9

# Windows:
netstat -ano | findstr :8550
taskkill /PID <PID> /F
```

#### 9. Tests failing

**Solution:**
```bash
# Clear pytest cache
pytest --cache-clear

# Reinstall in editable mode
pip install -e ".[ai,dev]"

# Run tests with verbose output
pytest -vv
```

#### 10. Build failures

**Solution:**
```bash
# Clean build artifacts
rm -rf build/ dist/ *.spec

# On Windows:
rmdir /s /q build dist

# Ensure PyInstaller is installed
pip install pyinstaller

# Rebuild
python scripts/build.py
```

### Getting More Help

If you're still experiencing issues:

1. **Check existing issues**: [GitHub Issues](https://github.com/flyingpurplepizzaeater/Skynette/issues)
2. **Search discussions**: [GitHub Discussions](https://github.com/flyingpurplepizzaeater/Skynette/discussions)
3. **Create a new issue**: Provide:
   - Operating system and version
   - Python version (`python --version`)
   - Full error message and traceback
   - Steps to reproduce
4. **Check documentation**: [docs/](docs/) directory

---

## Verifying Installation

After installation, verify everything is working:

### 1. Check Python and Pip

```bash
# Should show 3.11.x or 3.12.x
python --version

# Should show pip from your venv
pip --version
```

### 2. Verify Dependencies

```bash
# List installed packages
pip list

# Check key packages
pip show flet
pip show llama-cpp-python  # if AI features installed
pip show chromadb          # if AI features installed
```

### 3. Run Quick Test

```bash
# Run application
python src/main.py

# Application should launch with GUI
# You should see the Skynette dashboard
```

### 4. Run Test Suite

```bash
# Run unit tests (should take ~30 seconds)
pytest tests/unit/ -v

# All tests should pass
# Expected: 279 passed
```

### 5. Check Installation Type

```bash
# Verify editable installation
pip show -f skynette

# Should show: Location: /path/to/Skynette
# Should show: Editable project location: /path/to/Skynette
```

---

## Next Steps

After successful installation:

1. **Read the Quick Start**: [QUICKSTART.md](QUICKSTART.md)
2. **Configure AI Providers**: [docs/AI_PROVIDERS.md](docs/AI_PROVIDERS.md)
3. **Create Your First Workflow**: Follow examples in [README.md](README.md)
4. **Explore Documentation**: Browse [docs/](docs/) directory
5. **Join the Community**: 
   - [GitHub Discussions](https://github.com/flyingpurplepizzaeater/Skynette/discussions)
   - [Report Issues](https://github.com/flyingpurplepizzaeater/Skynette/issues)

---

## Summary of Commands

**Quick Reference:**

```bash
# Clone
git clone https://github.com/flyingpurplepizzaeater/Skynette.git
cd Skynette

# Setup
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Install
pip install -e ".[ai,dev]"

# Run
python src/main.py

# Test
pytest tests/unit/

# Build
python scripts/build.py
```

---

**Welcome to Skynette! Happy automating! 🚀**

For questions or issues, please visit our [GitHub repository](https://github.com/flyingpurplepizzaeater/Skynette).
