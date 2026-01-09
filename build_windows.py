"""
Windows Installer Build Script for Skynette.

This script creates a standalone Windows executable with all dependencies bundled.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def check_prerequisites():
    """Check and install required build tools."""
    print("Checking prerequisites...")

    # Check for PyInstaller
    try:
        import PyInstaller
        print(f"  PyInstaller {PyInstaller.__version__} found")
    except ImportError:
        print("  Installing PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)

    # Ensure all runtime dependencies are installed
    deps = [
        "flet>=0.21.0",
        "pydantic>=2.0.0",
        "httpx>=0.25.0",
        "aiofiles>=23.0.0",
        "pyyaml>=6.0",
        "python-dotenv>=1.0.0",
        "openai>=1.0.0",
        "anthropic>=0.18.0",
        "boto3>=1.28.0",
        "google-auth>=2.0.0",
        "google-auth-oauthlib>=1.0.0",
        "google-api-python-client>=2.0.0",
    ]

    print("  Checking runtime dependencies...")
    for dep in deps:
        pkg_name = dep.split(">=")[0].split("[")[0]
        try:
            __import__(pkg_name.replace("-", "_"))
        except ImportError:
            print(f"    Installing {dep}...")
            subprocess.run([sys.executable, "-m", "pip", "install", dep], check=True)

    print("  All prerequisites satisfied!")


def create_spec_file():
    """Create PyInstaller spec file for the build."""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-
"""
Skynette PyInstaller Spec File.

Bundles the application with all dependencies for Windows distribution.
"""

import os
import sys
from pathlib import Path

block_cipher = None

# Get the project root
project_root = os.path.dirname(os.path.abspath(SPEC))

# Collect all source files
src_path = os.path.join(project_root, 'src')

# Data files to include
datas = [
    # Include entire src directory as data
    (src_path, 'src'),
]

# Check for assets/icons if they exist
assets_path = os.path.join(project_root, 'assets')
if os.path.exists(assets_path):
    datas.append((assets_path, 'assets'))

# Hidden imports that PyInstaller might miss
hiddenimports = [
    # Flet and Flutter
    'flet',
    'flet_core',
    'flet_runtime',

    # Core dependencies
    'pydantic',
    'pydantic_core',
    'httpx',
    'httpcore',
    'anyio',
    'sniffio',
    'certifi',
    'h11',
    'h2',
    'hpack',
    'hyperframe',

    # Async
    'asyncio',
    'aiofiles',

    # Data handling
    'json',
    'yaml',
    'pyyaml',

    # AI providers
    'openai',
    'anthropic',

    # Cloud services
    'boto3',
    'botocore',
    's3transfer',

    # Google APIs
    'google.auth',
    'google.oauth2',
    'google_auth_oauthlib',
    'googleapiclient',

    # Email
    'email',
    'smtplib',
    'imaplib',

    # Standard library modules
    'sqlite3',
    'datetime',
    'uuid',
    're',
    'pathlib',
    'logging',
    'typing',
    'dataclasses',
    'enum',

    # All src modules
    'src',
    'src.core',
    'src.core.engine',
    'src.core.workflow',
    'src.core.nodes',
    'src.core.nodes.base',
    'src.core.nodes.core',
    'src.core.nodes.ai',
    'src.core.nodes.apps',
    'src.core.nodes.utility',
    'src.ai',
    'src.ai.gateway',
    'src.ai.models',
    'src.ai.providers',
    'src.ui',
    'src.ui.app',
    'src.ui.components',
    'src.storage',
]

a = Analysis(
    ['main.py'],
    pathex=[project_root],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'cv2',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Skynette',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(project_root, 'assets', 'icon.ico') if os.path.exists(os.path.join(project_root, 'assets', 'icon.ico')) else None,
)
'''

    spec_path = Path("skynette.spec")
    spec_path.write_text(spec_content)
    print(f"Created {spec_path}")
    return spec_path


def create_icon():
    """Create a simple icon file if it doesn't exist."""
    assets_dir = Path("assets")
    assets_dir.mkdir(exist_ok=True)

    icon_path = assets_dir / "icon.ico"
    if not icon_path.exists():
        # Create a simple placeholder - in production you'd want a real icon
        print("  Note: No icon.ico found. The exe will use the default Python icon.")
        print("  To add a custom icon, place 'icon.ico' in the assets/ folder.")


def build_executable():
    """Run Flet pack to create the executable."""
    print("\nBuilding Windows executable with Flet pack...")

    # Clean previous builds
    for folder in ["build", "dist"]:
        if Path(folder).exists():
            print(f"  Cleaning {folder}/...")
            shutil.rmtree(folder)

    # Try flet pack first (recommended for Flet apps)
    print("  Using 'flet pack' for Flet application...")

    # Build command
    cmd = [
        sys.executable, "-m", "flet", "pack",
        "main.py",
        "--name", "Skynette",
        "--add-data", "src;src",
    ]

    # Add icon if exists
    icon_path = Path("assets/icon.ico")
    if icon_path.exists():
        cmd.extend(["--icon", str(icon_path)])

    result = subprocess.run(cmd, capture_output=False)

    if result.returncode != 0:
        print("\n  Flet pack failed, trying direct PyInstaller...")
        # Fallback to direct PyInstaller
        result = subprocess.run(
            [sys.executable, "-m", "PyInstaller", "skynette.spec", "--clean"],
            capture_output=False
        )

        if result.returncode != 0:
            print("\nBuild failed! Check the output above for errors.")
            return False

    print("\nBuild successful!")
    return True


def create_installer_readme():
    """Create a README for the installer package."""
    readme_content = """# Skynette - Windows Installation

## Quick Start

1. Run `Skynette.exe` to launch the application
2. No installation required - it's a portable executable

## System Requirements

- Windows 10 or later (64-bit)
- 4GB RAM minimum (8GB recommended for local AI models)
- 500MB disk space (more for local AI models)

## Features

- Visual workflow automation builder
- Multi-AI model support (OpenAI, Anthropic, Local models)
- 40+ pre-built integration nodes
- Real-time workflow execution
- Cross-platform workflow exports

## First Run

On first launch, Skynette will:
1. Create a configuration directory in your user folder
2. Initialize the workflow database
3. Open the main workflow editor

## AI Model Setup

### Cloud AI (OpenAI/Anthropic)
- Add your API keys in Settings > AI Providers

### Local AI (llama.cpp)
- Click "Model Hub" to download models
- Recommended: Phi-3-mini or Mistral-7B for starters
- Models are stored in `~/.skynette/models/`

## Integrations

Configure API keys for integrations in Settings:
- Slack, Discord, Telegram
- GitHub, Notion
- Google Sheets
- AWS S3
- Twitter/X
- Email (SMTP/IMAP)

## Troubleshooting

### App won't start
- Ensure Windows Defender isn't blocking the executable
- Try running as Administrator

### AI models slow
- Local models require CPU/GPU resources
- Use smaller quantized models (Q4_K_M)
- Or switch to cloud providers

### Missing integrations
- Check API keys in Settings
- Verify network connectivity

## Support

- GitHub: https://github.com/skynette/skynette
- Documentation: https://docs.skynette.io

## License

MIT License - Free for personal and commercial use
"""

    dist_dir = Path("dist")
    dist_dir.mkdir(exist_ok=True)

    readme_path = dist_dir / "README.txt"
    readme_path.write_text(readme_content)
    print(f"Created {readme_path}")


def package_distribution():
    """Package the final distribution."""
    print("\nPackaging distribution...")

    dist_dir = Path("dist")

    if not (dist_dir / "Skynette.exe").exists():
        print("  Error: Skynette.exe not found in dist/")
        return False

    # Create the README
    create_installer_readme()

    # Get file size
    exe_size = (dist_dir / "Skynette.exe").stat().st_size / (1024 * 1024)

    print(f"\n{'='*50}")
    print("BUILD COMPLETE!")
    print(f"{'='*50}")
    print(f"\nOutput: dist/Skynette.exe")
    print(f"Size: {exe_size:.1f} MB")
    print(f"\nThe executable is portable - no installation needed!")
    print("Simply copy Skynette.exe to any location and run it.")

    return True


def main():
    """Main build process."""
    print("="*50)
    print("Skynette Windows Build Script")
    print("="*50)

    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    print(f"\nProject directory: {project_dir}")

    # Step 1: Check prerequisites
    check_prerequisites()

    # Step 2: Create assets folder and check for icon
    create_icon()

    # Step 3: Create spec file
    create_spec_file()

    # Step 4: Build executable
    if not build_executable():
        sys.exit(1)

    # Step 5: Package distribution
    if not package_distribution():
        sys.exit(1)

    print("\nDone!")


if __name__ == "__main__":
    main()
