# src/services/editor/file_service.py
"""Async file operations service for the code editor."""

import aiofiles
from dataclasses import dataclass
from pathlib import Path


@dataclass
class FileInfo:
    """Information about a file or directory.

    Attributes:
        path: Absolute path to the file.
        name: The file or directory name.
        is_dir: True if this is a directory.
        size: File size in bytes (0 for directories).
        extension: File extension including dot (e.g., ".py"), empty for directories.
    """

    path: str
    name: str
    is_dir: bool
    size: int
    extension: str


class FileService:
    """Async file operations for the code editor.

    Provides async read/write operations with size limits to prevent
    UI freezing on large files. Directory operations are synchronous
    since they're typically fast.

    File Size Limits:
        - WARN_FILE_SIZE (50KB): Files above this show a warning
        - MAX_FILE_SIZE (500KB): Files above this are refused

    Example:
        service = FileService()
        content = await service.read_file("path/to/file.py")
        await service.write_file("path/to/file.py", modified_content)
    """

    MAX_FILE_SIZE = 500_000  # 500KB limit - refuse to open larger files
    WARN_FILE_SIZE = 50_000  # 50KB warning threshold

    async def read_file(self, path: str) -> str:
        """Read file content asynchronously.

        Args:
            path: Path to the file to read.

        Returns:
            The file content as a string.

        Raises:
            ValueError: If the file exceeds MAX_FILE_SIZE.
            FileNotFoundError: If the file doesn't exist.
            PermissionError: If the file can't be read.
        """
        file_path = Path(path)
        size = file_path.stat().st_size

        if size > self.MAX_FILE_SIZE:
            raise ValueError(
                f"File too large ({size:,} bytes). "
                f"Maximum supported size is {self.MAX_FILE_SIZE:,} bytes."
            )

        async with aiofiles.open(path, mode="r", encoding="utf-8") as f:
            return await f.read()

    async def write_file(self, path: str, content: str) -> None:
        """Write content to file asynchronously.

        Args:
            path: Path to the file to write.
            content: The content to write.

        Raises:
            PermissionError: If the file can't be written.
        """
        async with aiofiles.open(path, mode="w", encoding="utf-8") as f:
            await f.write(content)

    async def create_file(self, path: str, content: str = "") -> None:
        """Create a new file with optional content.

        Args:
            path: Path for the new file.
            content: Initial content (defaults to empty).

        Raises:
            FileExistsError: If a file already exists at the path.
            PermissionError: If the file can't be created.
        """
        file_path = Path(path)
        if file_path.exists():
            raise FileExistsError(f"File already exists: {path}")

        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(path, mode="w", encoding="utf-8") as f:
            await f.write(content)

    async def delete_file(self, path: str) -> None:
        """Delete a file.

        Args:
            path: Path to the file to delete.

        Raises:
            FileNotFoundError: If the file doesn't exist.
            PermissionError: If the file can't be deleted.
            IsADirectoryError: If the path is a directory.
        """
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        if file_path.is_dir():
            raise IsADirectoryError(f"Cannot delete directory: {path}")
        file_path.unlink()

    def list_directory(self, path: str) -> list[FileInfo]:
        """List directory contents sorted (folders first, then by name).

        Args:
            path: Path to the directory to list.

        Returns:
            List of FileInfo objects for each item in the directory.
            Sorted with directories first, then files, both alphabetically.

        Raises:
            NotADirectoryError: If the path is not a directory.
            FileNotFoundError: If the directory doesn't exist.
        """
        dir_path = Path(path)
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {path}")
        if not dir_path.is_dir():
            raise NotADirectoryError(f"Not a directory: {path}")

        items = list(dir_path.iterdir())

        # Sort: directories first, then by name (case-insensitive)
        items = sorted(items, key=lambda x: (not x.is_dir(), x.name.lower()))

        return [
            FileInfo(
                path=str(item.resolve()),
                name=item.name,
                is_dir=item.is_dir(),
                size=item.stat().st_size if not item.is_dir() else 0,
                extension=item.suffix if not item.is_dir() else "",
            )
            for item in items
        ]

    def get_file_size(self, path: str) -> int:
        """Get file size in bytes.

        Args:
            path: Path to the file.

        Returns:
            The file size in bytes.

        Raises:
            FileNotFoundError: If the file doesn't exist.
        """
        return Path(path).stat().st_size

    def file_exists(self, path: str) -> bool:
        """Check if file exists.

        Args:
            path: Path to check.

        Returns:
            True if the file exists, False otherwise.
        """
        return Path(path).exists()

    def is_file_too_large(self, path: str) -> bool:
        """Check if file exceeds MAX_FILE_SIZE.

        Args:
            path: Path to the file.

        Returns:
            True if file exceeds the maximum size limit.
        """
        return self.get_file_size(path) > self.MAX_FILE_SIZE

    def should_warn_about_size(self, path: str) -> bool:
        """Check if file should show size warning.

        Args:
            path: Path to the file.

        Returns:
            True if file exceeds warning threshold but not max.
        """
        size = self.get_file_size(path)
        return self.WARN_FILE_SIZE < size <= self.MAX_FILE_SIZE
