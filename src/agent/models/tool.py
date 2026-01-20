"""
Tool Data Models

Pydantic models for tool definitions, calls, and results.
"""

from datetime import datetime, UTC
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class ToolDefinition(BaseModel):
    """Definition of an agent tool for LLM context."""

    name: str
    description: str
    parameters: dict
    category: str = "general"
    is_destructive: bool = False
    requires_approval: bool = False

    def to_openai_format(self) -> dict:
        """Convert to OpenAI function calling format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            }
        }

    def to_anthropic_format(self) -> dict:
        """Convert to Anthropic tool format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters,
        }


class ToolCall(BaseModel):
    """A request to execute a tool."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    tool_name: str
    parameters: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ToolResult(BaseModel):
    """Result of a tool execution."""

    tool_call_id: str
    success: bool
    data: Any = None
    error: Optional[str] = None
    duration_ms: float = 0

    @classmethod
    def success_result(
        cls,
        tool_call_id: str,
        data: Any,
        duration_ms: float = 0
    ) -> "ToolResult":
        """Create a successful result."""
        return cls(
            tool_call_id=tool_call_id,
            success=True,
            data=data,
            duration_ms=duration_ms
        )

    @classmethod
    def failure_result(
        cls,
        tool_call_id: str,
        error: str,
        duration_ms: float = 0
    ) -> "ToolResult":
        """Create a failure result."""
        return cls(
            tool_call_id=tool_call_id,
            success=False,
            error=error,
            duration_ms=duration_ms
        )
