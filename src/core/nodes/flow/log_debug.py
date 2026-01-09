"""
Log/Debug Node

Logs data for debugging purposes.
"""

from datetime import datetime
from typing import Any
import logging
import json

from src.core.nodes.base import UtilityNode, NodeField, NodeOutput, FieldType

logger = logging.getLogger(__name__)


class LogDebugNode(UtilityNode):
    """Log/Debug node - outputs data for debugging."""

    type = "log_debug"
    name = "Log / Debug"
    description = "Log data for debugging and inspection"
    icon = "bug_report"

    @classmethod
    def get_inputs(cls) -> list[NodeField]:
        return [
            NodeField(
                name="message",
                label="Message",
                type=FieldType.EXPRESSION,
                description="Message to log (can include expressions)",
                required=False,
                placeholder="Processing item: {{$prev.id}}",
            ),
            NodeField(
                name="data",
                label="Data to Log",
                type=FieldType.EXPRESSION,
                description="Data to include in the log (default: previous node output)",
                required=False,
                default="{{$prev}}",
            ),
            NodeField(
                name="log_level",
                label="Log Level",
                type=FieldType.SELECT,
                description="Logging level",
                required=False,
                default="info",
                options=[
                    {"label": "Debug", "value": "debug"},
                    {"label": "Info", "value": "info"},
                    {"label": "Warning", "value": "warning"},
                    {"label": "Error", "value": "error"},
                ],
            ),
            NodeField(
                name="include_timestamp",
                label="Include Timestamp",
                type=FieldType.BOOLEAN,
                description="Add timestamp to the log",
                required=False,
                default=True,
            ),
            NodeField(
                name="pretty_print",
                label="Pretty Print JSON",
                type=FieldType.BOOLEAN,
                description="Format JSON data for readability",
                required=False,
                default=True,
            ),
        ]

    @classmethod
    def get_outputs(cls) -> list[NodeOutput]:
        return [
            NodeOutput(
                name="logged",
                type="boolean",
                description="Whether the log was successful",
            ),
            NodeOutput(
                name="message",
                type="string",
                description="The logged message",
            ),
            NodeOutput(
                name="data",
                type="object",
                description="Pass-through of the logged data",
            ),
        ]

    async def execute(self, config: dict, context: dict) -> Any:
        """Log the data."""
        message = config.get("message", "")
        data = config.get("data", context.get("$prev", {}))
        log_level = config.get("log_level", "info")
        include_timestamp = config.get("include_timestamp", True)
        pretty_print = config.get("pretty_print", True)

        # Build log entry
        log_parts = []

        if include_timestamp:
            log_parts.append(f"[{datetime.utcnow().isoformat()}]")

        if message:
            log_parts.append(message)

        log_message = " ".join(log_parts)

        # Format data
        if data:
            if pretty_print:
                try:
                    data_str = json.dumps(data, indent=2, default=str)
                except Exception:
                    data_str = str(data)
            else:
                data_str = str(data)

            if log_message:
                log_message = f"{log_message}\n{data_str}"
            else:
                log_message = data_str

        # Log at appropriate level
        log_func = getattr(logger, log_level, logger.info)
        log_func(log_message)

        return {
            "logged": True,
            "message": message or "Debug output",
            "data": data,
        }
