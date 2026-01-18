# src/services/diff/__init__.py
"""Diff service for code change preview and application.

Provides DiffService for generating and applying unified diffs,
along with DiffHunk and DiffLine models for structured diff data.
"""

from .diff_service import DiffService
from .models import DiffHunk, DiffLine

__all__ = ["DiffService", "DiffHunk", "DiffLine"]
