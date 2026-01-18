# src/ui/views/code_editor/__init__.py
"""Code editor view components.

This package contains the main code editor view and its components:
- EditorState: Centralized state management
- OpenFile: File data container
- CodeEditor: Main editing component with syntax highlighting
"""

from src.ui.views.code_editor.state import EditorState, OpenFile
from src.ui.views.code_editor.editor import CodeEditor

__all__ = [
    "EditorState",
    "OpenFile",
    "CodeEditor",
]
