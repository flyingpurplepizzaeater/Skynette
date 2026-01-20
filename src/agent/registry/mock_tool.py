"""
Mock Tool

A mock tool for testing the registry and agent loop.
"""

from src.agent.models.tool import ToolResult
from src.agent.registry.base_tool import AgentContext, BaseTool


class MockTool(BaseTool):
    """Mock tool for testing the registry and agent loop."""

    name = "mock_echo"
    description = "A mock tool that echoes back the input. For testing only."
    parameters_schema = {
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "Message to echo back"
            }
        },
        "required": ["message"]
    }

    async def execute(self, params: dict, context: AgentContext) -> ToolResult:
        """Echo the message back."""
        message = params.get("message", "")
        return ToolResult.success_result(
            tool_call_id="mock",
            data={"echo": message, "session_id": context.session_id},
            duration_ms=1.0
        )
