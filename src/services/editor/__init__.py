# src/services/editor/__init__.py
"""Code editor services: highlighting, file operations, icons."""

from src.services.editor.highlighter import PygmentsHighlighter
from src.services.editor.file_service import FileService, FileInfo
from src.services.editor.file_icons import (
    get_file_icon,
    LANGUAGE_ICONS,
    FOLDER_ICON,
    FOLDER_OPEN_ICON,
)

__all__ = [
    "PygmentsHighlighter",
    "FileService",
    "FileInfo",
    "get_file_icon",
    "LANGUAGE_ICONS",
    "FOLDER_ICON",
    "FOLDER_OPEN_ICON",
]
