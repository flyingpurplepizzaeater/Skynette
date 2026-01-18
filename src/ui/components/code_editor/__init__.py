# src/ui/components/code_editor/__init__.py
"""Code editor UI components.

Reusable components for the code editor view:
- LineNumbers: Line number gutter
"""

from src.ui.components.code_editor.line_numbers import LineNumbers

__all__ = [
    "LineNumbers",
]
