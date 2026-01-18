# src/services/diff/models.py
"""Data models for diff representation.

Provides structured types for representing unified diff output.
"""

from dataclasses import dataclass, field


@dataclass
class DiffLine:
    """A single line in a diff.

    Attributes:
        content: The line content (without diff prefix).
        line_type: Type of line - "add", "remove", or "context".
        old_line_no: Line number in original file (None for additions).
        new_line_no: Line number in modified file (None for removals).
    """

    content: str
    line_type: str  # "add", "remove", "context"
    old_line_no: int | None = None
    new_line_no: int | None = None


@dataclass
class DiffHunk:
    """A hunk (section) of changes in a diff.

    Represents a contiguous section of changes with context lines.

    Attributes:
        source_start: Starting line in original file.
        source_length: Number of lines from original file.
        target_start: Starting line in modified file.
        target_length: Number of lines in modified file.
        lines: List of DiffLine objects in this hunk.
        header: Optional @@ header with function/class context.
    """

    source_start: int
    source_length: int
    target_start: int
    target_length: int
    lines: list[DiffLine] = field(default_factory=list)
    header: str = ""  # @@ -X,Y +A,B @@ optional context
