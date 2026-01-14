#!/usr/bin/env python3
"""
Skynette Cross-Platform Build Script

Builds Skynette for Windows, macOS, and Linux with installers.

Usage:
    python build_all.py              # Build for current platform
    python build_all.py --windows    # Build Windows installer (requires NSIS)
    python build_all.py --macos      # Build macOS DMG
    python build_all.py --linux      # Build Linux AppImage and .deb
    python build_all.py --all        # Build all (on current platform)

Requirements:
    - Python 3.10+
    - PyInstaller
    - Platform-specific tools:
        Windows: NSIS (Nullsoft Scriptable Install System)
        macOS: create-dmg (brew install create-dmg)
        Linux: appimagetool, dpkg-deb
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

VERSION = "1.0.0"
APP_NAME = "Skynette"


class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'=' * 60}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{text}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'=' * 60}{Colors.END}\n")


def print_success(text):
    print(f"{Colors.GREEN}[SUCCESS]{Colors.END} {text}")


def print_error(text):
    print(f"{Colors.RED}[ERROR]{Colors.END} {text}")


def print_warning(text):
    print(f"{Colors.YELLOW}[WARNING]{Colors.END} {text}")


def print_info(text):
    print(f"{Colors.BLUE}[INFO]{Colors.END} {text}")


def run_command(cmd, cwd=None, check=True):
    """Run a command and return the result."""
    print_info(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=False)
    if check and result.returncode != 0:
        raise RuntimeError(f"Command failed with return code {result.returncode}")
    return result


def check_pyinstaller():
    """Ensure PyInstaller is installed."""
    try:
        import PyInstaller
        print_info(f"PyInstaller {PyInstaller.__version__} found")
        return True
    except ImportError:
        print_warning("PyInstaller not found, installing...")
        run_command([sys.executable, "-m", "pip", "install", "pyinstaller"])
        return True


def build_executable(project_root):
    """Build the application executable using PyInstaller."""
    print_header("Building Application Executable")

    spec_file = project_root / "skynette.spec"
    if not spec_file.exists():
        print_error(f"Spec file not found: {spec_file}")
        return False

    # Clean previous build
    for folder in ["build", "dist"]:
        folder_path = project_root / folder
        if folder_path.exists():
            print_info(f"Cleaning {folder}/")
            shutil.rmtree(folder_path)

    # Run PyInstaller
    try:
        run_command([
            sys.executable, "-m", "PyInstaller",
            str(spec_file),
            "--clean",
            "--noconfirm",
        ], cwd=project_root)

        # Check for output
        if platform.system() == "Windows":
            exe_path = project_root / "dist" / "Skynette" / "Skynette.exe"
        elif platform.system() == "Darwin":
            exe_path = project_root / "dist" / "Skynette.app"
        else:
            exe_path = project_root / "dist" / "Skynette" / "Skynette"

        if exe_path.exists():
            print_success(f"Executable built: {exe_path}")
            return True
        else:
            print_error("Executable not found after build")
            return False

    except Exception as e:
        print_error(f"Build failed: {e}")
        return False


def build_windows_installer(project_root):
    """Build Windows NSIS installer."""
    print_header("Building Windows Installer")

    # Check for NSIS
    nsis_path = shutil.which("makensis")
    if not nsis_path:
        # Try common installation paths
        common_paths = [
            r"C:\Program Files\NSIS\makensis.exe",
            r"C:\Program Files (x86)\NSIS\makensis.exe",
        ]
        for path in common_paths:
            if os.path.exists(path):
                nsis_path = path
                break

    if not nsis_path:
        print_error("NSIS not found. Please install from: https://nsis.sourceforge.io/")
        return False

    print_info(f"Using NSIS: {nsis_path}")

    nsi_file = project_root / "installer" / "windows" / "skynette.nsi"
    if not nsi_file.exists():
        print_error(f"NSIS script not found: {nsi_file}")
        return False

    try:
        run_command([nsis_path, str(nsi_file)], cwd=project_root)
        installer_path = project_root / "dist" / f"Skynette-{VERSION}-Setup.exe"

        if installer_path.exists():
            size_mb = installer_path.stat().st_size / (1024 * 1024)
            print_success(f"Windows installer created: {installer_path}")
            print_info(f"Size: {size_mb:.1f} MB")
            return True
        else:
            print_error("Installer not found after build")
            return False

    except Exception as e:
        print_error(f"Windows installer build failed: {e}")
        return False


def build_macos_dmg(project_root):
    """Build macOS DMG installer."""
    print_header("Building macOS DMG")

    script_path = project_root / "installer" / "macos" / "create_dmg.sh"
    if not script_path.exists():
        print_error(f"DMG script not found: {script_path}")
        return False

    try:
        run_command(["bash", str(script_path)], cwd=project_root)
        dmg_path = project_root / "dist" / f"Skynette-{VERSION}.dmg"

        if dmg_path.exists():
            size_mb = dmg_path.stat().st_size / (1024 * 1024)
            print_success(f"macOS DMG created: {dmg_path}")
            print_info(f"Size: {size_mb:.1f} MB")
            return True
        else:
            print_error("DMG not found after build")
            return False

    except Exception as e:
        print_error(f"macOS DMG build failed: {e}")
        return False


def build_linux_appimage(project_root):
    """Build Linux AppImage."""
    print_header("Building Linux AppImage")

    script_path = project_root / "installer" / "linux" / "create_appimage.sh"
    if not script_path.exists():
        print_error(f"AppImage script not found: {script_path}")
        return False

    try:
        run_command(["bash", str(script_path)], cwd=project_root)
        appimage_path = project_root / "dist" / f"Skynette-{VERSION}-x86_64.AppImage"

        if appimage_path.exists():
            size_mb = appimage_path.stat().st_size / (1024 * 1024)
            print_success(f"Linux AppImage created: {appimage_path}")
            print_info(f"Size: {size_mb:.1f} MB")
            return True
        else:
            print_error("AppImage not found after build")
            return False

    except Exception as e:
        print_error(f"Linux AppImage build failed: {e}")
        return False


def build_linux_deb(project_root):
    """Build Linux .deb package."""
    print_header("Building Linux .deb Package")

    script_path = project_root / "installer" / "linux" / "create_deb.sh"
    if not script_path.exists():
        print_error(f"DEB script not found: {script_path}")
        return False

    try:
        run_command(["bash", str(script_path)], cwd=project_root)
        deb_path = project_root / "dist" / f"skynette_{VERSION}_amd64.deb"

        if deb_path.exists():
            size_mb = deb_path.stat().st_size / (1024 * 1024)
            print_success(f"Linux .deb created: {deb_path}")
            print_info(f"Size: {size_mb:.1f} MB")
            return True
        else:
            print_error(".deb not found after build")
            return False

    except Exception as e:
        print_error(f"Linux .deb build failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Build Skynette for multiple platforms")
    parser.add_argument("--windows", action="store_true", help="Build Windows installer")
    parser.add_argument("--macos", action="store_true", help="Build macOS DMG")
    parser.add_argument("--linux", action="store_true", help="Build Linux packages")
    parser.add_argument("--all", action="store_true", help="Build for all platforms")
    parser.add_argument("--skip-exe", action="store_true", help="Skip executable build (use existing)")
    args = parser.parse_args()

    project_root = Path(__file__).parent

    print_header(f"Skynette Build System v{VERSION}")
    print_info(f"Platform: {platform.system()} {platform.machine()}")
    print_info(f"Python: {sys.version}")
    print_info(f"Project root: {project_root}")

    # Determine what to build
    build_windows = args.windows or args.all
    build_macos = args.macos or args.all
    build_linux = args.linux or args.all

    # If no platform specified, build for current platform
    if not (build_windows or build_macos or build_linux):
        current_os = platform.system()
        if current_os == "Windows":
            build_windows = True
        elif current_os == "Darwin":
            build_macos = True
        else:
            build_linux = True

    results = {}

    # Check PyInstaller
    if not check_pyinstaller():
        print_error("Failed to install PyInstaller")
        return 1

    # Build executable (unless skipped)
    if not args.skip_exe:
        results["executable"] = build_executable(project_root)
        if not results["executable"]:
            print_error("Executable build failed. Cannot continue with installers.")
            return 1

    # Build platform-specific installers
    if build_windows:
        results["windows"] = build_windows_installer(project_root)

    if build_macos:
        results["macos"] = build_macos_dmg(project_root)

    if build_linux:
        results["appimage"] = build_linux_appimage(project_root)
        results["deb"] = build_linux_deb(project_root)

    # Summary
    print_header("Build Summary")

    all_success = True
    for name, success in results.items():
        if success:
            print_success(f"{name}: OK")
        else:
            print_error(f"{name}: FAILED")
            all_success = False

    if all_success:
        print(f"\n{Colors.GREEN}{Colors.BOLD}All builds completed successfully!{Colors.END}")
        return 0
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}Some builds failed.{Colors.END}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
