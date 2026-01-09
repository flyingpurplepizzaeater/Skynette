"""
MSI Installer Builder for Skynette using cx_Freeze.
"""

import sys
import os
from cx_Freeze import setup, Executable

# Dependencies - only include what's truly needed
build_exe_options = {
    "packages": [
        "flet",
        "pydantic",
        "httpx",
        "aiofiles",
        "yaml",
        "asyncio",
        "json",
        "sqlite3",
        "logging",
    ],
    "excludes": [
        "tkinter",
        "matplotlib",
        "numpy",
        "pandas",
        "scipy",
        "PIL",
        "cv2",
        "test",
        "unittest",
    ],
    "include_files": [
        ("src", "src"),
    ],
    "optimize": 2,
    "include_msvcr": True,
}

# MSI options with shortcuts
bdist_msi_options = {
    "upgrade_code": "{E8F5D3A2-1B4C-4E6F-9A8D-7C2B1E3F4A5D}",
    "add_to_path": False,
    "initial_target_dir": r"[ProgramFiles64Folder]\Skynette",
    "all_users": True,
    "summary_data": {
        "author": "Skynette",
        "comments": "AI-Native Workflow Automation Platform",
    },
}

# Base for Windows GUI app (no console)
base = None
if sys.platform == "win32":
    base = "gui"  # cx_Freeze 7.x uses "gui" instead of "Win32GUI"

# Check for icon
icon_path = None
if os.path.exists("assets/icon.ico"):
    icon_path = "assets/icon.ico"

# Define shortcuts for Start Menu and Desktop
shortcut_table = [
    (
        "DesktopShortcut",        # Shortcut
        "DesktopFolder",          # Directory_
        "Skynette",               # Name
        "TARGETDIR",              # Component_
        "[TARGETDIR]Skynette.exe",# Target
        None,                     # Arguments
        None,                     # Description
        None,                     # Hotkey
        None,                     # Icon
        None,                     # IconIndex
        None,                     # ShowCmd
        "TARGETDIR",              # WkDir
    ),
    (
        "StartMenuShortcut",      # Shortcut
        "StartMenuFolder",        # Directory_
        "Skynette",               # Name
        "TARGETDIR",              # Component_
        "[TARGETDIR]Skynette.exe",# Target
        None,                     # Arguments
        "AI-Native Workflow Automation",  # Description
        None,                     # Hotkey
        None,                     # Icon
        None,                     # IconIndex
        None,                     # ShowCmd
        "TARGETDIR",              # WkDir
    ),
]

# Add shortcut data to MSI options
bdist_msi_options["data"] = {"Shortcut": shortcut_table}

executables = [
    Executable(
        "main.py",
        base=base,
        target_name="Skynette.exe",
        icon=icon_path,
        copyright="Copyright 2024 Skynette",
        shortcut_name="Skynette",
        shortcut_dir="DesktopFolder",
    )
]

setup(
    name="Skynette",
    version="1.0.0",
    description="AI-Native Workflow Automation Platform",
    author="Skynette",
    options={
        "build_exe": build_exe_options,
        "bdist_msi": bdist_msi_options,
    },
    executables=executables,
)
