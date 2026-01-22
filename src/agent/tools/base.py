"""
Base Tool Utilities

Shared utilities for filesystem-touching tools: path validation and backup.
"""

import logging
import shutil
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class FileSystemValidator:
    """
    Validates file paths against allowlist and blocked patterns.

    Security utility to ensure tools only access permitted paths.
    """

    def __init__(
        self,
        allowed_paths: list[str],
        blocked_patterns: list[str] | None = None,
    ) -> None:
        """
        Initialize validator with allowed paths and blocked patterns.

        Args:
            allowed_paths: List of directory paths that are allowed for access.
            blocked_patterns: List of patterns to block (e.g., [".env", ".git"]).
        """
        # Resolve all allowed paths to handle symlinks
        self._allowed_paths = [Path(p).resolve() for p in allowed_paths]
        self._blocked_patterns = blocked_patterns or [".env", "credentials", ".git"]

    def validate(self, path_str: str) -> tuple[bool, str]:
        """
        Validate a path against allowlist and blocked patterns.

        Args:
            path_str: The path to validate.

        Returns:
            Tuple of (is_valid, error_message).
            If valid, error_message is empty string.
        """
        try:
            # Resolve to handle symlinks and relative paths
            resolved = Path(path_str).resolve()
            path_string = str(resolved)

            # Check blocked patterns against full path
            for pattern in self._blocked_patterns:
                if pattern in path_string:
                    return (False, f"Path contains blocked pattern: {pattern}")

            # Check if path is within any allowed directory
            for allowed in self._allowed_paths:
                try:
                    if resolved.is_relative_to(allowed):
                        return (True, "")
                except ValueError:
                    # is_relative_to raises ValueError on Windows for different drives
                    continue

            return (False, "Path not in allowed directories")

        except Exception as e:
            return (False, f"Path validation error: {e}")


def backup_before_modify(path: Path) -> Path | None:
    """
    Create a timestamped backup of a file before modifying it.

    Args:
        path: The file path to backup.

    Returns:
        The backup path if created, None if original doesn't exist.
    """
    if not path.exists():
        return None

    # Create timestamped backup: original.20260121_143052.bak
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = path.with_suffix(f".{timestamp}.bak")

    # Use copy2 to preserve metadata
    shutil.copy2(path, backup_path)
    logger.debug(f"Created backup: {backup_path}")

    return backup_path


def cleanup_old_backups(original_path: Path, keep: int = 5) -> int:
    """
    Remove old backup files, keeping only the most recent ones.

    Args:
        original_path: The original file path (backups are in same directory).
        keep: Number of most recent backups to keep.

    Returns:
        Number of backups removed.
    """
    # Find all backups matching {stem}.*.bak pattern
    parent = original_path.parent
    stem = original_path.stem

    # Match files like: filename.20260121_143052.bak
    backup_pattern = f"{stem}.*.bak"
    backups = list(parent.glob(backup_pattern))

    if len(backups) <= keep:
        return 0

    # Sort by modification time descending (newest first)
    backups.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    # Remove all but the most recent `keep` backups
    removed = 0
    for backup in backups[keep:]:
        try:
            backup.unlink()
            logger.debug(f"Removed old backup: {backup}")
            removed += 1
        except PermissionError:
            logger.warning(f"Permission denied removing backup: {backup}")
        except Exception as e:
            logger.warning(f"Failed to remove backup {backup}: {e}")

    return removed
