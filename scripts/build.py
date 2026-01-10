"""
Build script for creating Skynette distribution packages.

Usage:
    python scripts/build.py --platform windows
    python scripts/build.py --platform macos
    python scripts/build.py --platform linux
    python scripts/build.py --all
"""

import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


def run_command(cmd: list, cwd=None):
    """Run a shell command."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd or PROJECT_ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result.stdout


def build_executable():
    """Build executable using PyInstaller."""
    print("Building executable with PyInstaller...")
    run_command([sys.executable, "-m", "PyInstaller", "skynette.spec", "--clean"])
    print("✓ Executable built successfully")


def create_installer_windows():
    """Create Windows installer using NSIS or Inno Setup."""
    print("Creating Windows installer...")
    # TODO: Add NSIS or Inno Setup script
    print("Windows installer creation not yet implemented")


def create_app_bundle_macos():
    """Create macOS app bundle."""
    print("Creating macOS app bundle...")
    # PyInstaller already creates .app bundle
    print("✓ macOS app bundle created")


def create_appimage_linux():
    """Create Linux AppImage."""
    print("Creating Linux AppImage...")
    # TODO: Add AppImage creation
    print("Linux AppImage creation not yet implemented")


def main():
    parser = argparse.ArgumentParser(description="Build Skynette distribution packages")
    parser.add_argument(
        "--platform",
        choices=["windows", "macos", "linux", "all"],
        default=platform.system().lower(),
        help="Target platform"
    )
    parser.add_argument("--skip-tests", action="store_true", help="Skip running tests")

    args = parser.parse_args()

    # Run tests unless skipped
    if not args.skip_tests:
        print("Running tests...")
        run_command([sys.executable, "-m", "pytest", "tests/unit/", "-v"])

    # Build executable
    build_executable()

    # Platform-specific packaging
    current_platform = platform.system().lower()

    if args.platform == "all" or args.platform == "windows":
        if current_platform == "windows":
            create_installer_windows()
        else:
            print("Skipping Windows installer (not on Windows)")

    if args.platform == "all" or args.platform == "macos":
        if current_platform == "darwin":
            create_app_bundle_macos()
        else:
            print("Skipping macOS app bundle (not on macOS)")

    if args.platform == "all" or args.platform == "linux":
        if current_platform == "linux":
            create_appimage_linux()
        else:
            print("Skipping Linux AppImage (not on Linux)")

    print("\n✓ Build complete!")
    print(f"Output directory: {PROJECT_ROOT / 'dist'}")


if __name__ == "__main__":
    main()
