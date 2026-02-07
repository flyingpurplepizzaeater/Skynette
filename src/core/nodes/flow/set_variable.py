"""
Set Variable Node

Sets workflow variables for use in downstream nodes.
"""

from typing import Any

from src.core.nodes.base import FieldType, FlowNode, NodeField, NodeOutput


class SetVariableNode(FlowNode):
    """Set Variable node - stores values for later use."""

    type = "set_variable"
    name = "Set Variable"
    description = "Set a variable value for use in downstream nodes"
    icon = "data_object"

    @classmethod
    def get_inputs(cls) -> list[NodeField]:
        return [
            NodeField(
                name="variable_name",
                label="Variable Name",
                type=FieldType.STRING,
                description="Name of the variable to set",
                required=True,
                placeholder="my_variable",
            ),
            NodeField(
                name="value",
                label="Value",
                type=FieldType.EXPRESSION,
                description="Value to assign (can use expressions)",
                required=True,
            ),
            NodeField(
                name="value_type",
                label="Value Type",
                type=FieldType.SELECT,
                description="Type of the value",
                required=False,
                default="auto",
                options=[
                    {"label": "Auto Detect", "value": "auto"},
                    {"label": "String", "value": "string"},
                    {"label": "Number", "value": "number"},
                    {"label": "Boolean", "value": "boolean"},
                    {"label": "JSON Object", "value": "json"},
                    {"label": "Array", "value": "array"},
                ],
            ),
        ]

    @classmethod
    def get_outputs(cls) -> list[NodeOutput]:
        return [
            NodeOutput(
                name="name",
                type="string",
                description="The variable name",
            ),
            NodeOutput(
                name="value",
                type="object",
                description="The variable value",
            ),
            NodeOutput(
                name="previous",
                type="object",
                description="Pass-through of input data",
            ),
        ]

    async def execute(self, config: dict, context: dict) -> Any:
        """Set the variable."""
        name = config.get("variable_name", "")
        value = config.get("value")
        value_type = config.get("value_type", "auto")

        if not name:
            raise ValueError("Variable name is required")

        # Convert value type if specified
        if value_type != "auto":
            value = self._convert_type(value, value_type)

        # Store in context (workflow executor will handle this)
        return {
            "name": name,
            "value": value,
            "previous": context.get("$prev", {}),
        }

    def _convert_type(self, value: Any, target_type: str) -> Any:
        """Convert value to the specified type."""
        if target_type == "string":
            return str(value) if value is not None else ""
        elif target_type == "number":
            try:
                if isinstance(value, str) and "." in value:
                    return float(value)
                return int(value)
            except (ValueError, TypeError):
                return 0
        elif target_type == "boolean":
            if isinstance(value, str):
                return value.lower() in ["true", "1", "yes"]
            return bool(value)
        elif target_type == "json":
            if isinstance(value, str):
                import json

                return json.loads(value)
            return value
        elif target_type == "array":
            if isinstance(value, list):
                return value
            if isinstance(value, str):
                import json

                try:
                    parsed = json.loads(value)
                    return parsed if isinstance(parsed, list) else [parsed]
                except Exception:
                    return [value]
            return [value]
        return value
