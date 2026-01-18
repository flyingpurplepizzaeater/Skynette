# src/services/editor/file_icons.py
"""File extension to icon mapping for the file tree."""

import flet as ft
from pathlib import Path

# Map file extensions to Flet icons
# Organized by category for maintainability
LANGUAGE_ICONS: dict[str, str] = {
    # Python
    ".py": ft.Icons.CODE,
    ".pyw": ft.Icons.CODE,
    ".pyi": ft.Icons.CODE,
    ".pyx": ft.Icons.CODE,
    ".pxd": ft.Icons.CODE,
    ".ipynb": ft.Icons.CODE,
    # JavaScript/TypeScript
    ".js": ft.Icons.JAVASCRIPT,
    ".jsx": ft.Icons.JAVASCRIPT,
    ".ts": ft.Icons.JAVASCRIPT,
    ".tsx": ft.Icons.JAVASCRIPT,
    ".mjs": ft.Icons.JAVASCRIPT,
    ".cjs": ft.Icons.JAVASCRIPT,
    # Web markup
    ".html": ft.Icons.HTML,
    ".htm": ft.Icons.HTML,
    ".xhtml": ft.Icons.HTML,
    ".vue": ft.Icons.HTML,
    ".svelte": ft.Icons.HTML,
    # Stylesheets
    ".css": ft.Icons.CSS,
    ".scss": ft.Icons.CSS,
    ".sass": ft.Icons.CSS,
    ".less": ft.Icons.CSS,
    # Data formats
    ".json": ft.Icons.DATA_OBJECT,
    ".yaml": ft.Icons.DATA_OBJECT,
    ".yml": ft.Icons.DATA_OBJECT,
    ".xml": ft.Icons.DATA_OBJECT,
    ".toml": ft.Icons.DATA_OBJECT,
    ".csv": ft.Icons.DATA_OBJECT,
    ".tsv": ft.Icons.DATA_OBJECT,
    # Markdown/Documentation
    ".md": ft.Icons.DESCRIPTION,
    ".markdown": ft.Icons.DESCRIPTION,
    ".txt": ft.Icons.DESCRIPTION,
    ".rst": ft.Icons.DESCRIPTION,
    ".adoc": ft.Icons.DESCRIPTION,
    ".tex": ft.Icons.DESCRIPTION,
    # Configuration
    ".ini": ft.Icons.SETTINGS,
    ".cfg": ft.Icons.SETTINGS,
    ".conf": ft.Icons.SETTINGS,
    ".config": ft.Icons.SETTINGS,
    ".env": ft.Icons.SETTINGS,
    ".properties": ft.Icons.SETTINGS,
    ".editorconfig": ft.Icons.SETTINGS,
    # Shell/Terminal
    ".sh": ft.Icons.TERMINAL,
    ".bash": ft.Icons.TERMINAL,
    ".zsh": ft.Icons.TERMINAL,
    ".fish": ft.Icons.TERMINAL,
    ".ps1": ft.Icons.TERMINAL,
    ".psm1": ft.Icons.TERMINAL,
    ".bat": ft.Icons.TERMINAL,
    ".cmd": ft.Icons.TERMINAL,
    # Images
    ".png": ft.Icons.IMAGE,
    ".jpg": ft.Icons.IMAGE,
    ".jpeg": ft.Icons.IMAGE,
    ".gif": ft.Icons.IMAGE,
    ".svg": ft.Icons.IMAGE,
    ".ico": ft.Icons.IMAGE,
    ".webp": ft.Icons.IMAGE,
    ".bmp": ft.Icons.IMAGE,
    ".tiff": ft.Icons.IMAGE,
    # C/C++
    ".c": ft.Icons.CODE,
    ".h": ft.Icons.CODE,
    ".cpp": ft.Icons.CODE,
    ".hpp": ft.Icons.CODE,
    ".cc": ft.Icons.CODE,
    ".cxx": ft.Icons.CODE,
    # Java/Kotlin
    ".java": ft.Icons.CODE,
    ".kt": ft.Icons.CODE,
    ".kts": ft.Icons.CODE,
    ".gradle": ft.Icons.CODE,
    # Go
    ".go": ft.Icons.CODE,
    ".mod": ft.Icons.DATA_OBJECT,
    # Rust
    ".rs": ft.Icons.CODE,
    # Ruby
    ".rb": ft.Icons.CODE,
    ".erb": ft.Icons.CODE,
    ".rake": ft.Icons.CODE,
    # PHP
    ".php": ft.Icons.CODE,
    # SQL
    ".sql": ft.Icons.STORAGE,
    ".sqlite": ft.Icons.STORAGE,
    ".db": ft.Icons.STORAGE,
    # Lock/Dependency files
    ".lock": ft.Icons.LOCK,
    # Git
    ".gitignore": ft.Icons.SOURCE,
    ".gitattributes": ft.Icons.SOURCE,
    ".gitmodules": ft.Icons.SOURCE,
    # Docker
    ".dockerfile": ft.Icons.CLOUD,
    # Archives
    ".zip": ft.Icons.FOLDER_ZIP,
    ".tar": ft.Icons.FOLDER_ZIP,
    ".gz": ft.Icons.FOLDER_ZIP,
    ".7z": ft.Icons.FOLDER_ZIP,
    ".rar": ft.Icons.FOLDER_ZIP,
    # PDF/Documents
    ".pdf": ft.Icons.PICTURE_AS_PDF,
    ".doc": ft.Icons.ARTICLE,
    ".docx": ft.Icons.ARTICLE,
    # Fonts
    ".ttf": ft.Icons.FONT_DOWNLOAD,
    ".otf": ft.Icons.FONT_DOWNLOAD,
    ".woff": ft.Icons.FONT_DOWNLOAD,
    ".woff2": ft.Icons.FONT_DOWNLOAD,
}

# Special filenames (exact match, case-insensitive)
SPECIAL_FILE_ICONS: dict[str, str] = {
    "dockerfile": ft.Icons.CLOUD,
    "makefile": ft.Icons.BUILD,
    "cmakelists.txt": ft.Icons.BUILD,
    "requirements.txt": ft.Icons.LIST_ALT,
    "package.json": ft.Icons.JAVASCRIPT,
    "package-lock.json": ft.Icons.LOCK,
    "yarn.lock": ft.Icons.LOCK,
    "pipfile": ft.Icons.CODE,
    "pipfile.lock": ft.Icons.LOCK,
    "pyproject.toml": ft.Icons.CODE,
    "setup.py": ft.Icons.CODE,
    "setup.cfg": ft.Icons.SETTINGS,
    "license": ft.Icons.GAVEL,
    "license.txt": ft.Icons.GAVEL,
    "license.md": ft.Icons.GAVEL,
    "readme": ft.Icons.DESCRIPTION,
    "readme.md": ft.Icons.DESCRIPTION,
    "readme.txt": ft.Icons.DESCRIPTION,
    "changelog": ft.Icons.HISTORY,
    "changelog.md": ft.Icons.HISTORY,
    ".gitignore": ft.Icons.SOURCE,
    ".dockerignore": ft.Icons.CLOUD,
    ".env": ft.Icons.SETTINGS,
    ".env.local": ft.Icons.SETTINGS,
    ".env.example": ft.Icons.SETTINGS,
}

# Default icons
DEFAULT_FILE_ICON = ft.Icons.INSERT_DRIVE_FILE
FOLDER_ICON = ft.Icons.FOLDER
FOLDER_OPEN_ICON = ft.Icons.FOLDER_OPEN


def get_file_icon(
    filename: str, is_dir: bool = False, is_expanded: bool = False
) -> str:
    """Get appropriate icon for file or folder.

    Args:
        filename: The file or folder name (can be full path or just name).
        is_dir: True if this is a directory.
        is_expanded: True if directory is expanded (shows open folder icon).

    Returns:
        A Flet icon constant string (e.g., ft.Icons.FOLDER).

    Example:
        >>> get_file_icon("main.py")
        'code'
        >>> get_file_icon("src", is_dir=True)
        'folder'
        >>> get_file_icon("src", is_dir=True, is_expanded=True)
        'folder_open'
    """
    if is_dir:
        return FOLDER_OPEN_ICON if is_expanded else FOLDER_ICON

    # Extract just the filename if a full path was provided
    name = Path(filename).name.lower()

    # Check special filenames first (exact match)
    if name in SPECIAL_FILE_ICONS:
        return SPECIAL_FILE_ICONS[name]

    # Check by extension
    extension = Path(filename).suffix.lower()
    if extension in LANGUAGE_ICONS:
        return LANGUAGE_ICONS[extension]

    return DEFAULT_FILE_ICON
