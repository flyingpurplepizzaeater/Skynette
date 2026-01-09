"""
Write File Node

Writes content to local files.
"""

from pathlib import Path
from typing import Any
import json

from src.core.nodes.base import DataNode, NodeField, NodeOutput, FieldType


class WriteFileNode(DataNode):
    """Write File node - writes to local files."""

    type = "write_file"
    name = "Write File"
    description = "Write content to a local file"
    icon = "save"

    @classmethod
    def get_inputs(cls) -> list[NodeField]:
        return [
            NodeField(
                name="file_path",
                label="File Path",
                type=FieldType.EXPRESSION,
                description="Path to the file to write",
                required=True,
                placeholder="/path/to/file.txt",
            ),
            NodeField(
                name="content",
                label="Content",
                type=FieldType.EXPRESSION,
                description="Content to write to the file",
                required=True,
            ),
            NodeField(
                name="write_mode",
                label="Write Mode",
                type=FieldType.SELECT,
                description="How to write the file",
                required=False,
                default="overwrite",
                options=[
                    {"label": "Overwrite", "value": "overwrite"},
                    {"label": "Append", "value": "append"},
                    {"label": "Create Only (fail if exists)", "value": "create"},
                ],
            ),
            NodeField(
                name="content_type",
                label="Content Type",
                type=FieldType.SELECT,
                description="How to format the content",
                required=False,
                default="auto",
                options=[
                    {"label": "Auto Detect", "value": "auto"},
                    {"label": "Plain Text", "value": "text"},
                    {"label": "JSON (Pretty)", "value": "json"},
                    {"label": "JSON (Compact)", "value": "json_compact"},
                    {"label": "Binary (from Base64)", "value": "binary"},
                ],
            ),
            NodeField(
                name="encoding",
                label="Encoding",
                type=FieldType.STRING,
                description="Text encoding (default: utf-8)",
                required=False,
                default="utf-8",
            ),
            NodeField(
                name="create_directories",
                label="Create Directories",
                type=FieldType.BOOLEAN,
                description="Create parent directories if they don't exist",
                required=False,
                default=True,
            ),
        ]

    @classmethod
    def get_outputs(cls) -> list[NodeOutput]:
        return [
            NodeOutput(
                name="path",
                type="string",
                description="The file path that was written",
            ),
            NodeOutput(
                name="size",
                type="number",
                description="File size in bytes after writing",
            ),
            NodeOutput(
                name="success",
                type="boolean",
                description="Whether the write was successful",
            ),
        ]

    async def execute(self, config: dict, context: dict) -> Any:
        """Write the file."""
        file_path = config.get("file_path")
        content = config.get("content", "")
        write_mode = config.get("write_mode", "overwrite")
        content_type = config.get("content_type", "auto")
        encoding = config.get("encoding", "utf-8")
        create_directories = config.get("create_directories", True)

        if not file_path:
            raise ValueError("File path is required")

        path = Path(file_path).expanduser()

        # Check for create-only mode
        if write_mode == "create" and path.exists():
            raise FileExistsError(f"File already exists: {path}")

        # Create parent directories if needed
        if create_directories:
            path.parent.mkdir(parents=True, exist_ok=True)

        # Determine content type
        if content_type == "auto":
            if isinstance(content, (dict, list)):
                content_type = "json"
            else:
                content_type = "text"

        # Format content
        if content_type == "json":
            write_content = json.dumps(content, indent=2, default=str)
        elif content_type == "json_compact":
            write_content = json.dumps(content, default=str)
        elif content_type == "binary":
            import base64

            write_content = base64.b64decode(content)
        else:
            write_content = str(content)

        # Determine file mode
        if content_type == "binary":
            mode = "ab" if write_mode == "append" else "wb"
        else:
            mode = "a" if write_mode == "append" else "w"

        # Write the file
        if content_type == "binary":
            with open(path, mode) as f:
                f.write(write_content)
        else:
            with open(path, mode, encoding=encoding) as f:
                f.write(write_content)

        file_size = path.stat().st_size

        return {
            "path": str(path),
            "size": file_size,
            "success": True,
        }
