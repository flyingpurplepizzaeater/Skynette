"""
MCP Trust Models

Trust levels and tool approval tracking for MCP servers.
"""

from datetime import datetime, UTC
from typing import Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


# Use Literal type for JSON serialization (per 07-01 decision)
TrustLevel = Literal["builtin", "verified", "user_added"]


class ToolApproval(BaseModel):
    """Records user approval for an MCP tool.

    Per 09-CONTEXT.md: First-use approval for untrusted server tools,
    then remember the approval.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    server_id: str
    tool_name: str
    approved: bool = False
    approved_at: Optional[datetime] = None

    def approve(self) -> "ToolApproval":
        """Mark this tool as approved."""
        return ToolApproval(
            id=self.id,
            server_id=self.server_id,
            tool_name=self.tool_name,
            approved=True,
            approved_at=datetime.now(UTC),
        )
