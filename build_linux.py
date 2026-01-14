"""
Linux Build Script for Skynette.

Creates distributable packages for Linux:
- AppImage (universal Linux package)
- .deb package (Debian/Ubuntu)
- .rpm package (Fedora/RHEL) - optional

Usage:
    python build_linux.py [--appimage] [--deb] [--all]

Requirements:
    - Linux (Ubuntu 20.04+ recommended)
    - Python 3.11+
    - PyInstaller
    - appimagetool (for AppImage)
    - dpkg-deb (for .deb, usually pre-installed)
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


# Build configuration
APP_NAME = "skynette"
APP_DISPLAY_NAME = "Skynette"
APP_VERSION = "0.6.0"
APP_DESCRIPTION = "AI-Native Workflow Automation Platform"
APP_MAINTAINER = "Skynette Team <team@skynette.io>"
APP_HOMEPAGE = "https://skynette.io"
APP_CATEGORY = "Development;Utility;"


def check_platform():
    """Ensure we're running on Linux."""
    if sys.platform != "linux":
        print("Error: This script must be run on Linux")
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

    # Check for appimagetool
    result = subprocess.run(["which", "appimagetool"], capture_output=True)
    if result.returncode != 0:
        print("  Warning: appimagetool not found")
        print("           Install from: https://github.com/AppImage/AppImageKit/releases")
        print("           AppImage creation will be skipped.")

    # Check for dpkg-deb
    result = subprocess.run(["which", "dpkg-deb"], capture_output=True)
    if result.returncode != 0:
        print("  Warning: dpkg-deb not found")
        print("           .deb creation will be skipped.")

    print("  Prerequisites check complete!")


def create_spec_file():
    """Create PyInstaller spec file for Linux build."""
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
"""
Skynette Linux PyInstaller Spec File.
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
    # Linux-specific
    'gi', 'gi.repository',
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
    strip=True,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=True,
    upx=True,
    upx_exclude=[],
    name='{APP_NAME}',
)
'''

    spec_path = Path("skynette_linux.spec")
    spec_path.write_text(spec_content)
    print(f"Created spec file: {spec_path}")
    return spec_path


def build_binary(spec_path: Path):
    """Build the Linux binary using PyInstaller."""
    print("\nBuilding Linux binary...")

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

    print("Binary build complete!")


def create_desktop_file():
    """Create .desktop file for Linux desktop integration."""
    desktop_content = f"""[Desktop Entry]
Name={APP_DISPLAY_NAME}
Comment={APP_DESCRIPTION}
Exec={APP_NAME}
Icon={APP_NAME}
Terminal=false
Type=Application
Categories={APP_CATEGORY}
StartupWMClass={APP_DISPLAY_NAME}
Keywords=workflow;automation;ai;
"""
    return desktop_content


def create_appimage():
    """Create AppImage package."""
    print("\nCreating AppImage...")

    # Check for appimagetool
    result = subprocess.run(["which", "appimagetool"], capture_output=True)
    if result.returncode != 0:
        print("Warning: appimagetool not found, skipping AppImage creation")
        return False

    appdir = Path(f"dist/{APP_DISPLAY_NAME}.AppDir")

    # Clean and create AppDir structure
    if appdir.exists():
        shutil.rmtree(appdir)

    appdir.mkdir(parents=True)
    (appdir / "usr" / "bin").mkdir(parents=True)
    (appdir / "usr" / "share" / "applications").mkdir(parents=True)
    (appdir / "usr" / "share" / "icons" / "hicolor" / "256x256" / "apps").mkdir(parents=True)

    # Copy binary
    src_binary = Path(f"dist/{APP_NAME}")
    if src_binary.is_dir():
        shutil.copytree(src_binary, appdir / "usr" / "bin" / APP_NAME)
    else:
        print(f"Error: Binary not found at {src_binary}")
        return False

    # Create desktop file
    desktop_path = appdir / "usr" / "share" / "applications" / f"{APP_NAME}.desktop"
    desktop_path.write_text(create_desktop_file())

    # Copy to AppDir root (required by AppImage)
    shutil.copy(desktop_path, appdir / f"{APP_NAME}.desktop")

    # Create AppRun script
    apprun_content = f"""#!/bin/bash
SELF=$(readlink -f "$0")
HERE=${{SELF%/*}}
export PATH="${{HERE}}/usr/bin/{APP_NAME}:${{PATH}}"
exec "${{HERE}}/usr/bin/{APP_NAME}/{APP_NAME}" "$@"
"""
    apprun_path = appdir / "AppRun"
    apprun_path.write_text(apprun_content)
    apprun_path.chmod(0o755)

    # Create/copy icon
    icon_src = Path("assets/skynette.png")
    if icon_src.exists():
        icon_dest = appdir / "usr" / "share" / "icons" / "hicolor" / "256x256" / "apps" / f"{APP_NAME}.png"
        shutil.copy(icon_src, icon_dest)
        shutil.copy(icon_src, appdir / f"{APP_NAME}.png")
    else:
        # Create placeholder icon
        placeholder = appdir / f"{APP_NAME}.png"
        placeholder.touch()

    # Build AppImage
    output_path = Path(f"dist/{APP_DISPLAY_NAME}-{APP_VERSION}-x86_64.AppImage")
    if output_path.exists():
        output_path.unlink()

    cmd = ["appimagetool", str(appdir), str(output_path)]
    result = subprocess.run(cmd)

    if result.returncode == 0:
        print(f"AppImage created: {output_path}")
        # Make executable
        output_path.chmod(0o755)
        return True
    else:
        print("Warning: AppImage creation failed")
        return False


def create_deb_package():
    """Create .deb package for Debian/Ubuntu."""
    print("\nCreating .deb package...")

    # Check for dpkg-deb
    result = subprocess.run(["which", "dpkg-deb"], capture_output=True)
    if result.returncode != 0:
        print("Warning: dpkg-deb not found, skipping .deb creation")
        return False

    pkg_name = f"{APP_NAME}_{APP_VERSION}_amd64"
    pkg_dir = Path(f"dist/{pkg_name}")

    # Clean and create package structure
    if pkg_dir.exists():
        shutil.rmtree(pkg_dir)

    (pkg_dir / "DEBIAN").mkdir(parents=True)
    (pkg_dir / "usr" / "bin").mkdir(parents=True)
    (pkg_dir / "usr" / "share" / "applications").mkdir(parents=True)
    (pkg_dir / "usr" / "share" / "icons" / "hicolor" / "256x256" / "apps").mkdir(parents=True)
    (pkg_dir / "usr" / "share" / "doc" / APP_NAME).mkdir(parents=True)

    # Create control file
    control_content = f"""Package: {APP_NAME}
Version: {APP_VERSION}
Section: utils
Priority: optional
Architecture: amd64
Depends: libgtk-3-0, libwebkit2gtk-4.0-37
Maintainer: {APP_MAINTAINER}
Description: {APP_DESCRIPTION}
 Skynette is an AI-native workflow automation platform that lets you
 build powerful automations using visual workflows. It supports multiple
 AI providers, integrations, and local AI models.
Homepage: {APP_HOMEPAGE}
"""
    (pkg_dir / "DEBIAN" / "control").write_text(control_content)

    # Copy binary
    src_binary = Path(f"dist/{APP_NAME}")
    if src_binary.is_dir():
        shutil.copytree(src_binary, pkg_dir / "usr" / "share" / APP_NAME)
        # Create wrapper script
        wrapper = f"""#!/bin/bash
exec /usr/share/{APP_NAME}/{APP_NAME} "$@"
"""
        wrapper_path = pkg_dir / "usr" / "bin" / APP_NAME
        wrapper_path.write_text(wrapper)
        wrapper_path.chmod(0o755)
    else:
        print(f"Error: Binary not found at {src_binary}")
        return False

    # Create desktop file
    desktop_path = pkg_dir / "usr" / "share" / "applications" / f"{APP_NAME}.desktop"
    desktop_content = create_desktop_file().replace(f"Exec={APP_NAME}", f"Exec=/usr/bin/{APP_NAME}")
    desktop_path.write_text(desktop_content)

    # Copy icon
    icon_src = Path("assets/skynette.png")
    if icon_src.exists():
        icon_dest = pkg_dir / "usr" / "share" / "icons" / "hicolor" / "256x256" / "apps" / f"{APP_NAME}.png"
        shutil.copy(icon_src, icon_dest)

    # Create copyright file
    copyright_content = f"""Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: {APP_DISPLAY_NAME}
Upstream-Contact: {APP_MAINTAINER}
Source: {APP_HOMEPAGE}

Files: *
Copyright: 2024 Skynette Team
License: MIT
 Permission is hereby granted, free of charge, to any person obtaining a copy
 of this software and associated documentation files (the "Software"), to deal
 in the Software without restriction, including without limitation the rights
 to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 copies of the Software, and to permit persons to whom the Software is
 furnished to do so, subject to the following conditions:
 .
 The above copyright notice and this permission notice shall be included in all
 copies or substantial portions of the Software.
 .
 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
"""
    (pkg_dir / "usr" / "share" / "doc" / APP_NAME / "copyright").write_text(copyright_content)

    # Build .deb package
    output_path = Path(f"dist/{pkg_name}.deb")
    if output_path.exists():
        output_path.unlink()

    cmd = ["dpkg-deb", "--build", str(pkg_dir)]
    result = subprocess.run(cmd)

    if result.returncode == 0:
        print(f".deb package created: {output_path}")
        return True
    else:
        print("Warning: .deb package creation failed")
        return False


def main():
    parser = argparse.ArgumentParser(description="Build Skynette for Linux")
    parser.add_argument("--appimage", action="store_true", help="Create AppImage only")
    parser.add_argument("--deb", action="store_true", help="Create .deb package only")
    parser.add_argument("--all", action="store_true", help="Create all package formats")
    args = parser.parse_args()

    check_platform()
    check_prerequisites()

    # Default to --all if no format specified
    if not args.appimage and not args.deb:
        args.all = True

    spec_path = create_spec_file()
    build_binary(spec_path)

    results = []

    if args.all or args.appimage:
        if create_appimage():
            results.append(f"AppImage: dist/{APP_DISPLAY_NAME}-{APP_VERSION}-x86_64.AppImage")

    if args.all or args.deb:
        if create_deb_package():
            results.append(f".deb: dist/{APP_NAME}_{APP_VERSION}_amd64.deb")

    print(f"\n{'='*50}")
    print("Build complete!")
    if results:
        print("Created packages:")
        for r in results:
            print(f"  {r}")
    else:
        print(f"Binary: dist/{APP_NAME}/")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
