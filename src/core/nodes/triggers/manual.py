"""
Manual Trigger Node

Triggers a workflow when manually clicked.
"""

from datetime import UTC, datetime
from typing import Any

from src.core.nodes.base import FieldType, NodeField, NodeOutput, TriggerNode


class ManualTriggerNode(TriggerNode):
    """Manual trigger - starts workflow on button click."""

    type = "manual_trigger"
    name = "Manual Trigger"
    description = "Start the workflow manually with a button click"
    icon = "play_circle"

    @classmethod
    def get_inputs(cls) -> list[NodeField]:
        return [
            NodeField(
                name="test_data",
                label="Test Data",
                type=FieldType.JSON,
                description="Optional JSON data to pass when triggered",
                required=False,
                default={},
            ),
        ]

    @classmethod
    def get_outputs(cls) -> list[NodeOutput]:
        return [
            NodeOutput(
                name="triggered_at",
                type="string",
                description="ISO timestamp when triggered",
            ),
            NodeOutput(
                name="data",
                type="object",
                description="Test data passed to the trigger",
            ),
        ]

    async def execute(self, config: dict, context: dict) -> Any:
        """Execute the manual trigger."""
        return {
            "triggered_at": datetime.now(UTC).isoformat(),
            "data": config.get("test_data", {}),
            "trigger_type": "manual",
        }
