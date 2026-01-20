"""
Base Tool Classes

Abstract base class for all agent tools.
"""

from abc import ABC, abstractmethod
from typing import Optional

from pydantic import BaseModel, Field

from src.agent.models.tool import ToolDefinition, ToolResult


class AgentContext(BaseModel):
    """Lightweight context passed to tools during execution."""

    session_id: str
    variables: dict = Field(default_factory=dict)
    working_directory: Optional[str] = None


class BaseTool(ABC):
    """Abstract base class for all agent tools."""

    # Class attributes - override in subclasses
    name: str = "base_tool"
    description: str = "Base tool description"
    parameters_schema: dict = {"type": "object", "properties": {}}

    @abstractmethod
    async def execute(self, params: dict, context: AgentContext) -> ToolResult:
        """
        Execute the tool with validated parameters.

        Args:
            params: Tool parameters (already validated against schema)
            context: Execution context

        Returns:
            ToolResult with success/failure and data/error
        """
        pass

    def get_definition(self) -> ToolDefinition:
        """Get tool definition for LLM context."""
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=self.parameters_schema,
        )

    def validate_params(self, params: dict) -> tuple[bool, Optional[str]]:
        """
        Validate parameters against schema.

        Returns (is_valid, error_message).
        Basic validation - can be enhanced with jsonschema later.
        """
        # For now, just check required fields from schema
        required = self.parameters_schema.get("required", [])
        for field in required:
            if field not in params:
                return False, f"Missing required parameter: {field}"
        return True, None
