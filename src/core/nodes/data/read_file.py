"""
Read File Node

Reads content from local files.
"""

import json
from pathlib import Path
from typing import Any

from src.core.nodes.base import DataNode, FieldType, NodeField, NodeOutput


class ReadFileNode(DataNode):
    """Read File node - reads local files."""

    type = "read_file"
    name = "Read File"
    description = "Read content from a local file"
    icon = "file_open"

    @classmethod
    def get_inputs(cls) -> list[NodeField]:
        return [
            NodeField(
                name="file_path",
                label="File Path",
                type=FieldType.EXPRESSION,
                description="Path to the file to read",
                required=True,
                placeholder="/path/to/file.txt",
            ),
            NodeField(
                name="read_as",
                label="Read As",
                type=FieldType.SELECT,
                description="How to read the file content",
                required=False,
                default="auto",
                options=[
                    {"label": "Auto Detect", "value": "auto"},
                    {"label": "Plain Text", "value": "text"},
                    {"label": "JSON", "value": "json"},
                    {"label": "Binary (Base64)", "value": "binary"},
                    {"label": "Lines (Array)", "value": "lines"},
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
        ]

    @classmethod
    def get_outputs(cls) -> list[NodeOutput]:
        return [
            NodeOutput(
                name="content",
                type="object",
                description="File content (type depends on read_as setting)",
            ),
            NodeOutput(
                name="path",
                type="string",
                description="The file path that was read",
            ),
            NodeOutput(
                name="size",
                type="number",
                description="File size in bytes",
            ),
            NodeOutput(
                name="exists",
                type="boolean",
                description="Whether the file exists",
            ),
        ]

    async def execute(self, config: dict, context: dict) -> Any:
        """Read the file."""
        file_path = config.get("file_path")
        read_as = config.get("read_as", "auto")
        encoding = config.get("encoding", "utf-8")

        if not file_path:
            raise ValueError("File path is required")

        path = Path(file_path).expanduser()

        if not path.exists():
            return {
                "content": None,
                "path": str(path),
                "size": 0,
                "exists": False,
            }

        file_size = path.stat().st_size

        # Auto-detect based on extension
        if read_as == "auto":
            suffix = path.suffix.lower()
            if suffix == ".json":
                read_as = "json"
            elif suffix in [".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip"]:
                read_as = "binary"
            else:
                read_as = "text"

        # Read content
        if read_as == "json":
            with open(path, encoding=encoding) as f:
                content = json.load(f)
        elif read_as == "binary":
            import base64

            with open(path, "rb") as f:
                content = base64.b64encode(f.read()).decode("ascii")
        elif read_as == "lines":
            with open(path, encoding=encoding) as f:
                content = f.read().splitlines()
        else:  # text
            with open(path, encoding=encoding) as f:
                content = f.read()

        return {
            "content": content,
            "path": str(path),
            "size": file_size,
            "exists": True,
        }
