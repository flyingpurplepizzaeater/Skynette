# src/services/editor/__init__.py
"""Code editor services: highlighting, file operations, icons."""

from src.services.editor.file_icons import (
    FOLDER_ICON,
    FOLDER_OPEN_ICON,
    LANGUAGE_ICONS,
    get_file_icon,
)
from src.services.editor.file_service import FileInfo, FileService
from src.services.editor.highlighter import PygmentsHighlighter

__all__ = [
    "PygmentsHighlighter",
    "FileService",
    "FileInfo",
    "get_file_icon",
    "LANGUAGE_ICONS",
    "FOLDER_ICON",
    "FOLDER_OPEN_ICON",
]
