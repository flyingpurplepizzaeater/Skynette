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
from src.agent.mcp.storage import MCPServerStorage, get_mcp_storage
from src.agent.mcp.curated import (
    CURATED_SERVERS,
    get_curated_server,
    list_curated_servers,
    is_curated_server,
)
from src.agent.mcp.client import (
    MCPConnection,
    MCPClientManager,
    get_mcp_client_manager,
)
from src.agent.mcp.bridge import (
    MCPToolBridge,
    get_mcp_tool_bridge,
    initialize_mcp_tools,
)

__all__ = [
    # Models
    "MCPServerConfig",
    "MCPServerStatus",
    "TransportType",
    "ServerCategory",
    "TrustLevel",
    "ToolApproval",
    # Storage
    "MCPServerStorage",
    "get_mcp_storage",
    # Curated servers
    "CURATED_SERVERS",
    "get_curated_server",
    "list_curated_servers",
    "is_curated_server",
    # Client
    "MCPConnection",
    "MCPClientManager",
    "get_mcp_client_manager",
    # Bridge
    "MCPToolBridge",
    "get_mcp_tool_bridge",
    "initialize_mcp_tools",
]
