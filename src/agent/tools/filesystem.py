"""
Filesystem Tools

Tools for reading, writing, deleting, and listing files with security validation.
"""

import asyncio
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.agent.models.tool import ToolResult
from src.agent.registry.base_tool import AgentContext, BaseTool
from src.agent.tools.base import (
    FileSystemValidator,
    backup_before_modify,
    cleanup_old_backups,
)

logger = logging.getLogger(__name__)

# Configuration - can be overridden via user settings in future
DEFAULT_BLOCKED_PATTERNS = [
    ".env",
    "credentials",
    ".git/config",
    "id_rsa",
    ".ssh/",
    ".aws/",
]

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

# Binary file extensions (read as bytes, not text)
BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".webp",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".zip", ".tar", ".gz", ".7z", ".rar",
    ".exe", ".dll", ".so", ".dylib",
    ".mp3", ".mp4", ".wav", ".avi", ".mov", ".mkv",
    ".pyc", ".class", ".o", ".obj",
}


def _get_validator() -> FileSystemValidator:
    """Get validator with default paths. Can be overridden via config."""
    # TODO: Load from user settings in future
    return FileSystemValidator(
        allowed_paths=[str(Path.home()), str(Path.cwd())],
        blocked_patterns=DEFAULT_BLOCKED_PATTERNS,
    )


class FileReadTool(BaseTool):
    """Tool for reading file contents."""

    name = "file_read"
    description = "Read contents of a file. Respects allowed directories and blocked patterns."
    parameters_schema = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Absolute path to file",
            },
            "encoding": {
                "type": "string",
                "description": "Text encoding (default: utf-8)",
                "default": "utf-8",
            },
        },
        "required": ["path"],
    }

    async def execute(self, params: dict, context: AgentContext) -> ToolResult:
        """Read a file's contents."""
        start_time = time.time()
        path_str = params.get("path", "")
        encoding = params.get("encoding", "utf-8")

        # Validate path
        validator = _get_validator()
        is_valid, error = validator.validate(path_str)
        if not is_valid:
            duration_ms = (time.time() - start_time) * 1000
            return ToolResult.failure_result(
                tool_call_id="",
                error=f"Path validation failed: {error}",
                duration_ms=duration_ms,
            )

        path = Path(path_str).resolve()

        # Check file exists
        if not path.exists():
            duration_ms = (time.time() - start_time) * 1000
            return ToolResult.failure_result(
                tool_call_id="",
                error=f"File not found: {path}",
                duration_ms=duration_ms,
            )

        if not path.is_file():
            duration_ms = (time.time() - start_time) * 1000
            return ToolResult.failure_result(
                tool_call_id="",
                error=f"Path is not a file: {path}",
                duration_ms=duration_ms,
            )

        # Check file size
        file_size = path.stat().st_size
        if file_size > MAX_FILE_SIZE:
            duration_ms = (time.time() - start_time) * 1000
            return ToolResult.failure_result(
                tool_call_id="",
                error=f"File too large: {file_size} bytes (max: {MAX_FILE_SIZE})",
                duration_ms=duration_ms,
            )

        # Check if binary
        is_binary = path.suffix.lower() in BINARY_EXTENSIONS

        try:
            if is_binary:
                # Read binary file
                def _read_binary() -> bytes:
                    return path.read_bytes()

                content = await asyncio.to_thread(_read_binary)
                # Return base64 encoded for binary files
                import base64

                content_b64 = base64.b64encode(content).decode("ascii")
                duration_ms = (time.time() - start_time) * 1000
                return ToolResult.success_result(
                    tool_call_id="",
                    data={
                        "content": content_b64,
                        "path": str(path),
                        "size": file_size,
                        "encoding": "base64",
                        "is_binary": True,
                    },
                    duration_ms=duration_ms,
                )
            else:
                # Read text file
                try:
                    # Try aiofiles first
                    import aiofiles

                    async with aiofiles.open(path, "r", encoding=encoding) as f:
                        content = await f.read()
                except ImportError:
                    # Fallback to thread pool
                    def _read_text() -> str:
                        return path.read_text(encoding=encoding)

                    content = await asyncio.to_thread(_read_text)

                duration_ms = (time.time() - start_time) * 1000
                return ToolResult.success_result(
                    tool_call_id="",
                    data={
                        "content": content,
                        "path": str(path),
                        "size": file_size,
                        "encoding": encoding,
                        "is_binary": False,
                    },
                    duration_ms=duration_ms,
                )

        except UnicodeDecodeError as e:
            duration_ms = (time.time() - start_time) * 1000
            return ToolResult.failure_result(
                tool_call_id="",
                error=f"Encoding error reading file: {e}",
                duration_ms=duration_ms,
            )
        except Exception as e:
            logger.error(f"Error reading file {path}: {e}")
            duration_ms = (time.time() - start_time) * 1000
            return ToolResult.failure_result(
                tool_call_id="",
                error=f"Error reading file: {e}",
                duration_ms=duration_ms,
            )


class FileWriteTool(BaseTool):
    """Tool for writing content to files."""

    name = "file_write"
    description = "Write content to a file. Creates backup before overwriting. Creates directories as needed."
    parameters_schema = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Absolute path to file",
            },
            "content": {
                "type": "string",
                "description": "Content to write",
            },
            "encoding": {
                "type": "string",
                "description": "Text encoding (default: utf-8)",
                "default": "utf-8",
            },
            "append": {
                "type": "boolean",
                "description": "Append instead of overwrite",
                "default": False,
            },
        },
        "required": ["path", "content"],
    }
    is_destructive = True  # Mark as destructive for Phase 11 classification

    async def execute(self, params: dict, context: AgentContext) -> ToolResult:
        """Write content to a file."""
        start_time = time.time()
        path_str = params.get("path", "")
        content = params.get("content", "")
        encoding = params.get("encoding", "utf-8")
        append = params.get("append", False)

        # Validate path
        validator = _get_validator()
        is_valid, error = validator.validate(path_str)
        if not is_valid:
            duration_ms = (time.time() - start_time) * 1000
            return ToolResult.failure_result(
                tool_call_id="",
                error=f"Path validation failed: {error}",
                duration_ms=duration_ms,
            )

        path = Path(path_str).resolve()

        # Create parent directories if needed
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return ToolResult.failure_result(
                tool_call_id="",
                error=f"Failed to create directories: {e}",
                duration_ms=duration_ms,
            )

        # Create backup if file exists
        backup_path: Optional[Path] = None
        if path.exists():
            try:
                backup_path = await asyncio.to_thread(backup_before_modify, path)
                logger.debug(f"Created backup: {backup_path}")
            except Exception as e:
                logger.warning(f"Failed to create backup: {e}")
                # Continue anyway - backup is best-effort

        # Write content
        try:
            mode = "a" if append else "w"
            try:
                # Try aiofiles first
                import aiofiles

                async with aiofiles.open(path, mode, encoding=encoding) as f:
                    await f.write(content)
            except ImportError:
                # Fallback to thread pool
                def _write_text() -> None:
                    if append:
                        with open(path, "a", encoding=encoding) as f:
                            f.write(content)
                    else:
                        path.write_text(content, encoding=encoding)

                await asyncio.to_thread(_write_text)

            # Cleanup old backups
            if backup_path:
                await asyncio.to_thread(cleanup_old_backups, path)

            file_size = path.stat().st_size
            duration_ms = (time.time() - start_time) * 1000

            return ToolResult.success_result(
                tool_call_id="",
                data={
                    "path": str(path),
                    "size": file_size,
                    "backup_path": str(backup_path) if backup_path else None,
                    "appended": append,
                },
                duration_ms=duration_ms,
            )

        except Exception as e:
            logger.error(f"Error writing file {path}: {e}")
            duration_ms = (time.time() - start_time) * 1000
            return ToolResult.failure_result(
                tool_call_id="",
                error=f"Error writing file: {e}",
                duration_ms=duration_ms,
            )


class FileDeleteTool(BaseTool):
    """Tool for deleting files."""

    name = "file_delete"
    description = "Delete a file. Creates backup before deletion."
    parameters_schema = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Absolute path to file",
            },
        },
        "required": ["path"],
    }
    is_destructive = True  # Mark as destructive

    async def execute(self, params: dict, context: AgentContext) -> ToolResult:
        """Delete a file after creating backup."""
        start_time = time.time()
        path_str = params.get("path", "")

        # Validate path
        validator = _get_validator()
        is_valid, error = validator.validate(path_str)
        if not is_valid:
            duration_ms = (time.time() - start_time) * 1000
            return ToolResult.failure_result(
                tool_call_id="",
                error=f"Path validation failed: {error}",
                duration_ms=duration_ms,
            )

        path = Path(path_str).resolve()

        # Check file exists
        if not path.exists():
            duration_ms = (time.time() - start_time) * 1000
            return ToolResult.failure_result(
                tool_call_id="",
                error=f"File not found: {path}",
                duration_ms=duration_ms,
            )

        if not path.is_file():
            duration_ms = (time.time() - start_time) * 1000
            return ToolResult.failure_result(
                tool_call_id="",
                error=f"Path is not a file: {path}",
                duration_ms=duration_ms,
            )

        # Create backup before deletion
        backup_path: Optional[Path] = None
        try:
            backup_path = await asyncio.to_thread(backup_before_modify, path)
            logger.debug(f"Created backup before delete: {backup_path}")
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return ToolResult.failure_result(
                tool_call_id="",
                error=f"Failed to create backup: {e}",
                duration_ms=duration_ms,
            )

        # Delete the file
        try:
            await asyncio.to_thread(path.unlink)

            duration_ms = (time.time() - start_time) * 1000
            return ToolResult.success_result(
                tool_call_id="",
                data={
                    "deleted_path": str(path),
                    "backup_path": str(backup_path) if backup_path else None,
                },
                duration_ms=duration_ms,
            )

        except Exception as e:
            logger.error(f"Error deleting file {path}: {e}")
            duration_ms = (time.time() - start_time) * 1000
            return ToolResult.failure_result(
                tool_call_id="",
                error=f"Error deleting file: {e}",
                duration_ms=duration_ms,
            )


class FileListTool(BaseTool):
    """Tool for listing directory contents."""

    name = "file_list"
    description = "List files in a directory. Respects allowed directories."
    parameters_schema = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Absolute path to directory",
            },
            "pattern": {
                "type": "string",
                "description": "Glob pattern (default: *)",
                "default": "*",
            },
            "recursive": {
                "type": "boolean",
                "description": "Search recursively",
                "default": False,
            },
        },
        "required": ["path"],
    }

    async def execute(self, params: dict, context: AgentContext) -> ToolResult:
        """List directory contents."""
        start_time = time.time()
        path_str = params.get("path", "")
        pattern = params.get("pattern", "*")
        recursive = params.get("recursive", False)

        # Validate path
        validator = _get_validator()
        is_valid, error = validator.validate(path_str)
        if not is_valid:
            duration_ms = (time.time() - start_time) * 1000
            return ToolResult.failure_result(
                tool_call_id="",
                error=f"Path validation failed: {error}",
                duration_ms=duration_ms,
            )

        path = Path(path_str).resolve()

        # Check directory exists
        if not path.exists():
            duration_ms = (time.time() - start_time) * 1000
            return ToolResult.failure_result(
                tool_call_id="",
                error=f"Directory not found: {path}",
                duration_ms=duration_ms,
            )

        if not path.is_dir():
            duration_ms = (time.time() - start_time) * 1000
            return ToolResult.failure_result(
                tool_call_id="",
                error=f"Path is not a directory: {path}",
                duration_ms=duration_ms,
            )

        try:
            def _list_files() -> list[dict]:
                if recursive:
                    # Use rglob for recursive search
                    glob_pattern = f"**/{pattern}" if not pattern.startswith("**") else pattern
                    matches = list(path.glob(glob_pattern))
                else:
                    matches = list(path.glob(pattern))

                results = []
                for p in matches:
                    try:
                        stat = p.stat()
                        modified = datetime.fromtimestamp(stat.st_mtime).isoformat()
                        results.append({
                            "name": p.name,
                            "path": str(p),
                            "size": stat.st_size,
                            "is_dir": p.is_dir(),
                            "modified": modified,
                        })
                    except (OSError, PermissionError) as e:
                        # Skip files we can't access
                        logger.debug(f"Cannot stat {p}: {e}")
                        continue

                # Sort by name
                results.sort(key=lambda x: x["name"].lower())
                return results

            files = await asyncio.to_thread(_list_files)

            duration_ms = (time.time() - start_time) * 1000
            return ToolResult.success_result(
                tool_call_id="",
                data=files,
                duration_ms=duration_ms,
            )

        except Exception as e:
            logger.error(f"Error listing directory {path}: {e}")
            duration_ms = (time.time() - start_time) * 1000
            return ToolResult.failure_result(
                tool_call_id="",
                error=f"Error listing directory: {e}",
                duration_ms=duration_ms,
            )
