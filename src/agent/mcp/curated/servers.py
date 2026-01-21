"""
Curated MCP Server Definitions

Pre-defined configurations for vetted MCP servers.
Per 09-CONTEXT.md: Ship with curated list that user can enable (allowlist approach).
"""

from copy import deepcopy
from typing import Optional

from src.agent.mcp.models.server import MCPServerConfig


# Fixed IDs for curated servers (enables lookup by key)
_CURATED_IDS = {
    "filesystem": "curated-filesystem-001",
    "browser": "curated-browser-001",
    "git": "curated-git-001",
    "fetch": "curated-fetch-001",
    "memory": "curated-memory-001",
}


# Pre-defined configurations for vetted MCP servers
# Per 09-RESEARCH.md: These are VERIFIED trust level, maintained by Anthropic/MCP team
CURATED_SERVERS: dict[str, MCPServerConfig] = {
    "filesystem": MCPServerConfig(
        id=_CURATED_IDS["filesystem"],
        name="Filesystem",
        description="Secure file operations (read, write, create, delete) with explicit path restrictions",
        transport="stdio",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed"],
        trust_level="verified",
        sandbox_enabled=False,  # Built-in has explicit path restrictions
        category="file_tools",
        enabled=False,  # User must explicitly enable (allowlist approach)
    ),
    "browser": MCPServerConfig(
        id=_CURATED_IDS["browser"],
        name="Browser",
        description="Playwright-based browser automation for web interactions",
        transport="stdio",
        command="npx",
        args=["-y", "@anthropic/browser-mcp"],
        trust_level="verified",
        sandbox_enabled=False,
        category="browser_tools",
        enabled=False,
    ),
    "git": MCPServerConfig(
        id=_CURATED_IDS["git"],
        name="Git",
        description="Git repository operations (status, log, diff, commit, etc.)",
        transport="stdio",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-git"],
        trust_level="verified",
        sandbox_enabled=False,
        category="dev_tools",
        enabled=False,
    ),
    "fetch": MCPServerConfig(
        id=_CURATED_IDS["fetch"],
        name="Fetch",
        description="Web content fetching and retrieval",
        transport="stdio",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-fetch"],
        trust_level="verified",
        sandbox_enabled=False,
        category="data_tools",
        enabled=False,
    ),
    "memory": MCPServerConfig(
        id=_CURATED_IDS["memory"],
        name="Memory",
        description="Knowledge graph memory for persistent context across sessions",
        transport="stdio",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-memory"],
        trust_level="verified",
        sandbox_enabled=False,
        category="productivity",
        enabled=False,
    ),
}


def get_curated_server(server_key: str) -> Optional[MCPServerConfig]:
    """Get a copy of a curated server configuration.

    Returns a deep copy to prevent mutation of the curated definitions.

    Args:
        server_key: Key of the curated server (e.g., 'filesystem', 'browser')

    Returns:
        Copy of the server configuration, or None if not found
    """
    if server_key not in CURATED_SERVERS:
        return None
    return deepcopy(CURATED_SERVERS[server_key])


def list_curated_servers() -> list[MCPServerConfig]:
    """Get copies of all curated server configurations.

    Returns:
        List of server configurations (deep copies)
    """
    return [deepcopy(config) for config in CURATED_SERVERS.values()]


def is_curated_server(server_id: str) -> bool:
    """Check if a server ID belongs to a curated server.

    Args:
        server_id: Server ID to check

    Returns:
        True if this is a curated server ID
    """
    return server_id in _CURATED_IDS.values()


def get_curated_server_key(server_id: str) -> Optional[str]:
    """Get the key for a curated server by its ID.

    Args:
        server_id: Server ID

    Returns:
        Server key (e.g., 'filesystem') or None if not curated
    """
    for key, id_ in _CURATED_IDS.items():
        if id_ == server_id:
            return key
    return None
