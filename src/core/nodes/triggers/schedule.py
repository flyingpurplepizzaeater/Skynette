"""
Schedule Trigger Node

Triggers a workflow on a schedule (cron expression).
"""

from datetime import UTC, datetime
from typing import Any

from src.core.nodes.base import FieldType, NodeField, NodeOutput, TriggerNode


class ScheduleTriggerNode(TriggerNode):
    """Schedule trigger - starts workflow on a time schedule."""

    type = "schedule_trigger"
    name = "Schedule Trigger"
    description = "Start the workflow on a recurring schedule"
    icon = "schedule"

    @classmethod
    def get_inputs(cls) -> list[NodeField]:
        return [
            NodeField(
                name="schedule_type",
                label="Schedule Type",
                type=FieldType.SELECT,
                description="How to define the schedule",
                required=True,
                default="interval",
                options=[
                    {"label": "Interval", "value": "interval"},
                    {"label": "Daily", "value": "daily"},
                    {"label": "Weekly", "value": "weekly"},
                    {"label": "Cron Expression", "value": "cron"},
                ],
            ),
            NodeField(
                name="interval_minutes",
                label="Interval (minutes)",
                type=FieldType.NUMBER,
                description="Run every N minutes",
                required=False,
                default=60,
                min_value=1,
            ),
            NodeField(
                name="time",
                label="Time",
                type=FieldType.STRING,
                description="Time to run (HH:MM format)",
                required=False,
                default="09:00",
                placeholder="09:00",
            ),
            NodeField(
                name="day_of_week",
                label="Day of Week",
                type=FieldType.SELECT,
                description="Day to run (for weekly)",
                required=False,
                default="monday",
                options=[
                    {"label": "Monday", "value": "monday"},
                    {"label": "Tuesday", "value": "tuesday"},
                    {"label": "Wednesday", "value": "wednesday"},
                    {"label": "Thursday", "value": "thursday"},
                    {"label": "Friday", "value": "friday"},
                    {"label": "Saturday", "value": "saturday"},
                    {"label": "Sunday", "value": "sunday"},
                ],
            ),
            NodeField(
                name="cron",
                label="Cron Expression",
                type=FieldType.STRING,
                description="Cron expression (e.g., '0 9 * * *' for daily at 9am)",
                required=False,
                placeholder="0 9 * * *",
            ),
            NodeField(
                name="timezone",
                label="Timezone",
                type=FieldType.STRING,
                description="Timezone for the schedule",
                required=False,
                default="UTC",
                placeholder="UTC",
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
                name="scheduled_time",
                type="string",
                description="The scheduled time that triggered this run",
            ),
            NodeOutput(
                name="schedule",
                type="object",
                description="Schedule configuration",
            ),
        ]

    async def execute(self, config: dict, context: dict) -> Any:
        """Execute the schedule trigger."""
        return {
            "triggered_at": datetime.now(UTC).isoformat(),
            "scheduled_time": context.get("$trigger", {}).get(
                "scheduled_time", datetime.now(UTC).isoformat()
            ),
            "schedule": {
                "type": config.get("schedule_type", "interval"),
                "timezone": config.get("timezone", "UTC"),
            },
            "trigger_type": "schedule",
        }
