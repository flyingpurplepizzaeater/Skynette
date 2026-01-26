"""
MCP Tool Bridge

Coordinates MCP server connections with ToolRegistry registration/unregistration.
Implements graceful disconnect with delayed unregistration to handle transient issues.
"""

import asyncio
import logging
from typing import Optional

from src.agent.mcp.client.manager import get_mcp_client_manager, MCPClientManager
from src.agent.mcp.models.server import MCPServerConfig
from src.agent.mcp.storage.server_storage import get_mcp_storage, MCPServerStorage
from src.agent.registry.tool_registry import get_tool_registry, ToolRegistry

logger = logging.getLogger(__name__)


# Per 16-CONTEXT.md: 5 second graceful timeout for transient disconnects
GRACEFUL_UNREGISTER_TIMEOUT = 5.0


class MCPToolBridge:
    """Singleton coordinator for MCP tool registration lifecycle.

    Bridges MCPClientManager connections to ToolRegistry registration,
    handling graceful disconnect with delayed unregistration.
    """

    _instance: Optional["MCPToolBridge"] = None
    _manager: MCPClientManager
    _registry: ToolRegistry
    _pending_unregister: dict[str, asyncio.Task]
    _initialized: bool

    def __new__(cls) -> "MCPToolBridge":
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._manager = get_mcp_client_manager()
        self._registry = get_tool_registry()
        self._pending_unregister = {}
        logger.debug("MCPToolBridge initialized")

    async def connect_and_register(self, config: MCPServerConfig) -> int:
        """Connect to an MCP server and register its tools.

        Cancels any pending unregister task for this server before connecting.

        Args:
            config: Server configuration

        Returns:
            Number of tools registered

        Raises:
            ConnectionError: If connection fails
        """
        # Cancel any pending unregister for this server (reconnect scenario)
        if self.cancel_pending_unregister(config.id):
            logger.info(f"Cancelled pending unregister for {config.name} on reconnect")

        # Connect to server
        connection = await self._manager.connect(config)

        # Get tools from connection
        tools = await connection.list_tools()

        # Register with ToolRegistry
        count = self._registry.register_mcp_tools_from_server(
            server_id=config.id,
            server_name=config.name,
            trust_level=config.trust_level,
            tools=tools,
        )

        logger.info(f"Connected and registered {count} tools from {config.name}")
        return count

    async def disconnect_and_unregister(
        self,
        server_id: str,
        graceful: bool = True,
    ) -> None:
        """Disconnect from an MCP server and unregister its tools.

        With graceful=True, schedules delayed unregistration to handle
        transient disconnects. If server reconnects within the timeout,
        unregistration is cancelled.

        Args:
            server_id: Server to disconnect
            graceful: If True, delay unregistration by GRACEFUL_UNREGISTER_TIMEOUT
        """
        if graceful:
            # Schedule delayed unregister
            async def _delayed_unregister():
                try:
                    await asyncio.sleep(GRACEFUL_UNREGISTER_TIMEOUT)
                    count = self._registry.unregister_mcp_tools_from_server(server_id)
                    logger.info(f"Graceful timeout elapsed, unregistered {count} tools from {server_id}")
                except asyncio.CancelledError:
                    logger.debug(f"Graceful unregister cancelled for {server_id}")
                    raise
                finally:
                    self._pending_unregister.pop(server_id, None)

            # Cancel any existing pending task for this server
            self.cancel_pending_unregister(server_id)

            # Create new pending task
            task = asyncio.create_task(_delayed_unregister())
            self._pending_unregister[server_id] = task
            logger.info(f"Scheduled graceful unregister for {server_id} in {GRACEFUL_UNREGISTER_TIMEOUT}s")
        else:
            # Immediate unregister
            count = self._registry.unregister_mcp_tools_from_server(server_id)
            logger.info(f"Immediately unregistered {count} tools from {server_id}")

        # Disconnect from manager
        await self._manager.disconnect(server_id)

    def cancel_pending_unregister(self, server_id: str) -> bool:
        """Cancel a pending graceful unregister task.

        Args:
            server_id: Server ID to cancel unregister for

        Returns:
            True if a task was cancelled, False if no pending task
        """
        task = self._pending_unregister.pop(server_id, None)
        if task and not task.done():
            task.cancel()
            return True
        return False


# Module-level singleton accessor
_bridge: Optional[MCPToolBridge] = None


def get_mcp_tool_bridge() -> MCPToolBridge:
    """Get the global MCP tool bridge instance.

    Returns:
        The singleton MCPToolBridge instance
    """
    global _bridge
    if _bridge is None:
        _bridge = MCPToolBridge()
    return _bridge


async def initialize_mcp_tools() -> dict[str, int]:
    """Initialize MCP tools by connecting to all enabled servers.

    Connects to all enabled MCP servers in parallel and registers
    their tools with the ToolRegistry.

    Returns:
        Dictionary mapping server_id to tool count (or -1 for errors)
    """
    bridge = get_mcp_tool_bridge()
    storage = get_mcp_storage()

    # Get enabled servers
    servers = storage.list_servers(enabled_only=True)

    if not servers:
        logger.info("No enabled MCP servers to initialize")
        return {}

    logger.info(f"Initializing {len(servers)} enabled MCP servers")

    # Connect to all servers in parallel
    async def _connect_server(config: MCPServerConfig) -> tuple[str, int]:
        try:
            count = await bridge.connect_and_register(config)
            return (config.id, count)
        except Exception as e:
            logger.error(f"Failed to connect to {config.name}: {e}")
            return (config.id, -1)

    tasks = [_connect_server(config) for config in servers]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Build results dict
    result_dict: dict[str, int] = {}
    success_count = 0
    error_count = 0

    for result in results:
        if isinstance(result, Exception):
            error_count += 1
            logger.error(f"Unexpected error during MCP init: {result}")
        else:
            server_id, count = result
            result_dict[server_id] = count
            if count >= 0:
                success_count += 1
            else:
                error_count += 1

    logger.info(
        f"MCP initialization complete: {success_count} servers connected, "
        f"{error_count} errors"
    )

    return result_dict
