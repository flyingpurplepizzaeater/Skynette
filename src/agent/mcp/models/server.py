"""
MCP Server Configuration Models

Pydantic models for MCP server configuration and status.
"""

from datetime import datetime, UTC
from typing import Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from src.agent.mcp.models.trust import TrustLevel


# Use Literal types for JSON serialization (per 07-01 decision)
TransportType = Literal["stdio", "http"]
ServerCategory = Literal[
    "browser_tools",
    "file_tools",
    "dev_tools",
    "data_tools",
    "productivity",
    "other",
]


class MCPServerConfig(BaseModel):
    """Configuration for an MCP server.

    Supports both stdio (local) and HTTP (remote) transports.
    Per 09-CONTEXT.md: Three trust tiers, category-based organization.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: Optional[str] = None

    # Transport configuration
    transport: TransportType

    # For stdio transport
    command: Optional[str] = None
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)

    # For HTTP transport
    url: Optional[str] = None
    headers: dict[str, str] = Field(default_factory=dict)

    # Trust and security
    trust_level: TrustLevel = "user_added"
    sandbox_enabled: bool = True  # Default to sandboxed for user-added

    # Organization (per 09-CONTEXT.md: organize by category, not transport)
    category: ServerCategory = "other"
    enabled: bool = True

    # Status tracking
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_connected: Optional[datetime] = None
    last_error: Optional[str] = None


class MCPServerStatus(BaseModel):
    """Runtime status of an MCP server connection.

    Per 09-CONTEXT.md: Detailed health info for expandable view.
    """

    server_id: str
    connected: bool = False
    connecting: bool = False
    latency_ms: Optional[float] = None
    tools_count: int = 0
    last_active: Optional[datetime] = None
    error: Optional[str] = None
