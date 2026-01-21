"""
MCP Integration Package

Model Context Protocol (MCP) integration for Skynette.
Enables connecting to external MCP servers for tool extensibility.
"""

from src.agent.mcp.models import (
    MCPServerConfig,
    MCPServerStatus,
    TransportType,
    ServerCategory,
    TrustLevel,
    ToolApproval,
)

__all__ = [
    # Models
    "MCPServerConfig",
    "MCPServerStatus",
    "TransportType",
    "ServerCategory",
    "TrustLevel",
    "ToolApproval",
]
