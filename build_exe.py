"""
Simple build script for Skynette executable.

Usage:
    python build_exe.py

This will create a standalone executable in the dist/ folder.
Note: Renamed from build.py to avoid shadowing Python's 'build' package.
"""

import subprocess
import sys
import os
from pathlib import Path


def main():
    project_root = Path(__file__).parent

    print("=" * 60)
    print("Building Skynette Windows Executable")
    print("=" * 60)

    # Check for PyInstaller
    print("\n[1/4] Checking PyInstaller...")
    try:
        import PyInstaller
        print(f"  PyInstaller {PyInstaller.__version__} found")
    except ImportError:
        print("  Installing PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)

    # Verify src/main.py exists
    print("\n[2/4] Verifying project structure...")
    main_py = project_root / "src" / "main.py"
    if not main_py.exists():
        print(f"  ERROR: main.py not found at {main_py}")
        sys.exit(1)
    print(f"  src/main.py found")

    spec_file = project_root / "skynette.spec"
    if not spec_file.exists():
        print(f"  ERROR: skynette.spec not found at {spec_file}")
        sys.exit(1)
    print(f"  skynette.spec found")

    # Clean old build
    print("\n[3/4] Cleaning previous build...")
    for folder in ["build", "dist"]:
        folder_path = project_root / folder
        if folder_path.exists():
            import shutil
            shutil.rmtree(folder_path)
            print(f"  Removed {folder}/")

    # Run PyInstaller
    print("\n[4/4] Building executable with PyInstaller...")
    print("  This may take several minutes...")

    result = subprocess.run(
        [
            sys.executable, "-m", "PyInstaller",
            str(spec_file),
            "--clean",
            "--noconfirm",
        ],
        cwd=project_root,
    )

    if result.returncode == 0:
        exe_path = project_root / "dist" / "Skynette.exe"
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print("\n" + "=" * 60)
            print("BUILD SUCCESSFUL!")
            print("=" * 60)
            print(f"\nExecutable: {exe_path}")
            print(f"Size: {size_mb:.1f} MB")
            print("\nYou can now run Skynette.exe from the dist/ folder.")
        else:
            print("\nBuild completed but executable not found.")
    else:
        print("\n" + "=" * 60)
        print("BUILD FAILED!")
        print("=" * 60)
        print("\nCheck the output above for errors.")
        sys.exit(1)


if __name__ == "__main__":
    main()
