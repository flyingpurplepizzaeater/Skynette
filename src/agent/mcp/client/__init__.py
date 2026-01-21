"""
MCP Client Package

Client-side MCP implementation for connecting to MCP servers.
"""

from src.agent.mcp.client.connection import MCPConnection
from src.agent.mcp.client.manager import MCPClientManager, get_mcp_client_manager

__all__ = [
    "MCPConnection",
    "MCPClientManager",
    "get_mcp_client_manager",
]
