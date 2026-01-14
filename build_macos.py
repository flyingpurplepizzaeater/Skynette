"""
macOS Build Script for Skynette.

Creates a standalone macOS application bundle (.app) and disk image (.dmg).
Supports both Intel (x86_64) and Apple Silicon (arm64) architectures.

Usage:
    python build_macos.py [--notarize] [--arch arm64|x86_64|universal]

Requirements:
    - macOS 11.0+ (Big Sur or later)
    - Python 3.11+
    - PyInstaller
    - create-dmg (brew install create-dmg) for DMG creation
    - Apple Developer ID for notarization (optional)
"""

import argparse
import os
import plistlib
import shutil
import subprocess
import sys
from pathlib import Path


# Build configuration
APP_NAME = "Skynette"
APP_VERSION = "0.6.0"
BUNDLE_ID = "io.skynette.app"
ICON_NAME = "skynette.icns"


def check_platform():
    """Ensure we're running on macOS."""
    if sys.platform != "darwin":
        print("Error: This script must be run on macOS")
        sys.exit(1)


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

    # Check for create-dmg
    result = subprocess.run(["which", "create-dmg"], capture_output=True)
    if result.returncode != 0:
        print("  Warning: create-dmg not found. Install with: brew install create-dmg")
        print("           DMG creation will be skipped.")

    print("  Prerequisites check complete!")


def get_architecture():
    """Detect current architecture."""
    import platform
    machine = platform.machine()
    if machine == "arm64":
        return "arm64"
    return "x86_64"


def create_spec_file(arch: str):
    """Create PyInstaller spec file for macOS build."""
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
"""
Skynette macOS PyInstaller Spec File.
Architecture: {arch}
"""

import os
import sys
from pathlib import Path

block_cipher = None
project_root = os.path.dirname(os.path.abspath(SPEC))
src_path = os.path.join(project_root, 'src')

datas = [
    (src_path, 'src'),
]

assets_path = os.path.join(project_root, 'assets')
if os.path.exists(assets_path):
    datas.append((assets_path, 'assets'))

hiddenimports = [
    'flet', 'flet_core', 'flet_runtime',
    'pydantic', 'pydantic_core',
    'httpx', 'httpcore', 'anyio', 'sniffio', 'certifi',
    'yaml', 'dotenv',
    'sqlalchemy', 'aiosqlite',
    'cryptography', 'keyring',
    'apscheduler', 'watchdog',
    'pandas', 'openpyxl',
    'jinja2', 'jsonschema',
]

a = Analysis(
    ['src/main.py'],
    pathex=[project_root],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'scipy', 'numpy.testing'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='{APP_NAME}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    target_arch='{arch}',
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='{APP_NAME}',
)

app = BUNDLE(
    coll,
    name='{APP_NAME}.app',
    icon='assets/{ICON_NAME}' if os.path.exists('assets/{ICON_NAME}') else None,
    bundle_identifier='{BUNDLE_ID}',
    info_plist={{
        'CFBundleName': '{APP_NAME}',
        'CFBundleDisplayName': '{APP_NAME}',
        'CFBundleVersion': '{APP_VERSION}',
        'CFBundleShortVersionString': '{APP_VERSION}',
        'CFBundleIdentifier': '{BUNDLE_ID}',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '11.0',
        'NSRequiresAquaSystemAppearance': False,
    }},
)
'''

    spec_path = Path("skynette_macos.spec")
    spec_path.write_text(spec_content)
    print(f"Created spec file: {spec_path}")
    return spec_path


def build_app(spec_path: Path):
    """Build the macOS application bundle."""
    print("\nBuilding macOS application...")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        str(spec_path),
    ]

    result = subprocess.run(cmd)
    if result.returncode != 0:
        print("Error: Build failed!")
        sys.exit(1)

    print("Build complete!")


def create_dmg():
    """Create a DMG disk image for distribution."""
    print("\nCreating DMG disk image...")

    app_path = Path(f"dist/{APP_NAME}.app")
    dmg_path = Path(f"dist/{APP_NAME}-{APP_VERSION}.dmg")

    if not app_path.exists():
        print(f"Error: {app_path} not found")
        return False

    # Remove existing DMG
    if dmg_path.exists():
        dmg_path.unlink()

    # Check if create-dmg is available
    result = subprocess.run(["which", "create-dmg"], capture_output=True)
    if result.returncode != 0:
        print("Warning: create-dmg not found, skipping DMG creation")
        return False

    cmd = [
        "create-dmg",
        "--volname", APP_NAME,
        "--volicon", f"assets/{ICON_NAME}" if Path(f"assets/{ICON_NAME}").exists() else "",
        "--window-pos", "200", "120",
        "--window-size", "600", "400",
        "--icon-size", "100",
        "--icon", f"{APP_NAME}.app", "150", "190",
        "--hide-extension", f"{APP_NAME}.app",
        "--app-drop-link", "450", "190",
        str(dmg_path),
        str(app_path),
    ]

    # Remove empty icon argument if no icon
    cmd = [c for c in cmd if c]

    result = subprocess.run(cmd)
    if result.returncode == 0:
        print(f"DMG created: {dmg_path}")
        return True
    else:
        print("Warning: DMG creation failed")
        return False


def notarize_app(developer_id: str = None):
    """Notarize the app for Gatekeeper (requires Apple Developer account)."""
    print("\nNotarization requires:")
    print("  1. Apple Developer ID")
    print("  2. App-specific password")
    print("  3. Team ID")
    print("\nRun manually:")
    print(f"  xcrun notarytool submit dist/{APP_NAME}-{APP_VERSION}.dmg \\")
    print("    --apple-id YOUR_APPLE_ID \\")
    print("    --password YOUR_APP_PASSWORD \\")
    print("    --team-id YOUR_TEAM_ID \\")
    print("    --wait")


def main():
    parser = argparse.ArgumentParser(description="Build Skynette for macOS")
    parser.add_argument("--notarize", action="store_true", help="Show notarization instructions")
    parser.add_argument("--arch", choices=["arm64", "x86_64", "universal"],
                        default=None, help="Target architecture")
    parser.add_argument("--no-dmg", action="store_true", help="Skip DMG creation")
    args = parser.parse_args()

    check_platform()
    check_prerequisites()

    arch = args.arch or get_architecture()
    print(f"\nBuilding for architecture: {arch}")

    if arch == "universal":
        print("Note: Universal builds require building twice and using lipo")
        print("      Building for current architecture instead")
        arch = get_architecture()

    spec_path = create_spec_file(arch)
    build_app(spec_path)

    if not args.no_dmg:
        create_dmg()

    if args.notarize:
        notarize_app()

    print(f"\n{'='*50}")
    print(f"Build complete!")
    print(f"  App: dist/{APP_NAME}.app")
    if Path(f"dist/{APP_NAME}-{APP_VERSION}.dmg").exists():
        print(f"  DMG: dist/{APP_NAME}-{APP_VERSION}.dmg")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
