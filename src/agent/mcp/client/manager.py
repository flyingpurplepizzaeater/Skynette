"""
MCP Client Manager

Singleton manager for all MCP server connections with auto-reconnect support.
Per 09-CONTEXT.md: Background lazy connection, auto-reconnect with exponential backoff.
"""

import asyncio
import logging
from contextlib import AsyncExitStack
from typing import Optional

from typing import TYPE_CHECKING

from src.agent.mcp.client.connection import MCPConnection
from src.agent.mcp.models.server import MCPServerConfig, MCPServerStatus

if TYPE_CHECKING:
    from src.agent.mcp.sandbox.docker_sandbox import DockerSandbox

logger = logging.getLogger(__name__)


class MCPClientManager:
    """Singleton manager for all MCP server connections.

    Provides:
    - Connection management for stdio and HTTP transports
    - Automatic reconnection with exponential backoff
    - Connection lifecycle through AsyncExitStack
    - Tool listing and invocation across servers
    """

    _instance: Optional["MCPClientManager"] = None
    _connections: dict[str, MCPConnection]
    _exit_stack: AsyncExitStack
    _initialized: bool
    _reconnect_tasks: dict[str, asyncio.Task]
    _server_configs: dict[str, MCPServerConfig]
    _sandboxes: dict[str, "DockerSandbox"]  # Server ID -> sandbox instance

    # Reconnect settings (per 09-CONTEXT.md: exponential backoff)
    RECONNECT_BASE_DELAY = 1.0  # Initial delay in seconds
    RECONNECT_MAX_DELAY = 60.0  # Maximum delay
    RECONNECT_MAX_ATTEMPTS = 5  # Max attempts before giving up

    def __new__(cls) -> "MCPClientManager":
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    async def initialize(self) -> None:
        """Initialize the manager (call once at startup)."""
        if self._initialized:
            return
        self._connections = {}
        self._exit_stack = AsyncExitStack()
        self._reconnect_tasks = {}
        self._server_configs = {}
        self._sandboxes = {}
        self._initialized = True
        logger.info("MCPClientManager initialized")

    async def connect(self, config: MCPServerConfig) -> MCPConnection:
        """Connect to an MCP server based on config.

        Args:
            config: Server configuration with transport details

        Returns:
            MCPConnection wrapper for the active session

        Raises:
            ConnectionError: If connection fails
        """
        if not self._initialized:
            await self.initialize()

        if config.id in self._connections:
            return self._connections[config.id]

        # Store config for potential reconnection
        self._server_configs[config.id] = config

        try:
            if config.transport == "stdio":
                connection = await self._connect_stdio(config)
            else:  # HTTP
                connection = await self._connect_http(config)

            self._connections[config.id] = connection
            logger.info(f"Connected to MCP server: {config.name}")
            return connection

        except Exception as e:
            logger.error(f"Failed to connect to {config.name}: {e}")
            raise ConnectionError(f"Failed to connect to {config.name}: {e}") from e

    async def _connect_stdio(self, config: MCPServerConfig) -> MCPConnection:
        """Connect via stdio transport, using sandbox for untrusted servers.

        Spawns a subprocess running the MCP server and communicates
        via stdin/stdout. For USER_ADDED servers with sandbox_enabled=True,
        runs the server in a Docker container for isolation.
        """
        from mcp import ClientSession
        from mcp.client.stdio import stdio_client, StdioServerParameters
        from src.agent.mcp.sandbox.docker_sandbox import DockerSandbox, is_docker_available
        from src.agent.mcp.sandbox.policy import get_policy_for_trust_level

        if not config.command:
            raise ValueError(f"stdio transport requires 'command' for server {config.name}")

        # Check if sandbox is needed
        use_sandbox = (
            config.sandbox_enabled
            and config.trust_level == "user_added"
        )

        if use_sandbox:
            if not is_docker_available():
                logger.warning(
                    f"Docker not available for sandboxing {config.name}. "
                    "Running without sandbox (less secure)."
                )
                use_sandbox = False

        if use_sandbox:
            # Start sandboxed server
            policy = get_policy_for_trust_level(config.trust_level)
            sandbox = DockerSandbox(config, policy)
            read_stream, write_stream = await sandbox.start()
            self._sandboxes[config.id] = sandbox

            session = await self._exit_stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )
        else:
            # Direct stdio connection
            server_params = StdioServerParameters(
                command=config.command,
                args=config.args,
                env=config.env or None,
            )

            transport = await self._exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            read_stream, write_stream = transport

            session = await self._exit_stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )

        await session.initialize()

        return MCPConnection(
            server_id=config.id,
            session=session,
            config=config,
        )

    async def _connect_http(self, config: MCPServerConfig) -> MCPConnection:
        """Connect via Streamable HTTP transport.

        Connects to a remote MCP server over HTTP/SSE.
        """
        from mcp import ClientSession
        from mcp.client.streamable_http import streamablehttp_client

        if not config.url:
            raise ValueError(f"HTTP transport requires 'url' for server {config.name}")

        headers = config.headers or {}

        transport = await self._exit_stack.enter_async_context(
            streamablehttp_client(config.url, headers=headers)
        )
        read_stream, write_stream, _ = transport

        session = await self._exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )
        await session.initialize()

        return MCPConnection(
            server_id=config.id,
            session=session,
            config=config,
        )

    def _schedule_reconnect(self, server_id: str, attempt: int = 1) -> None:
        """Schedule a reconnection attempt with exponential backoff.

        Per 09-CONTEXT.md: Auto-reconnect with exponential backoff if server
        disconnects mid-session.

        Args:
            server_id: ID of the server to reconnect
            attempt: Current attempt number (1-based)
        """
        if server_id not in self._server_configs:
            logger.warning(f"No config stored for server {server_id}, cannot reconnect")
            return

        if attempt > self.RECONNECT_MAX_ATTEMPTS:
            logger.error(
                f"Max reconnect attempts ({self.RECONNECT_MAX_ATTEMPTS}) reached for {server_id}"
            )
            return

        # Cancel any existing reconnect task for this server
        if server_id in self._reconnect_tasks:
            self._reconnect_tasks[server_id].cancel()

        # Calculate delay with exponential backoff
        delay = min(
            self.RECONNECT_BASE_DELAY * (2 ** (attempt - 1)),
            self.RECONNECT_MAX_DELAY,
        )

        async def _do_reconnect():
            await asyncio.sleep(delay)
            config = self._server_configs.get(server_id)
            if not config:
                return

            logger.info(f"Attempting reconnect to {config.name} (attempt {attempt})")
            try:
                await self.connect(config)
                logger.info(f"Reconnected to {config.name}")
                # Clear reconnect task on success
                self._reconnect_tasks.pop(server_id, None)
            except Exception as e:
                logger.warning(f"Reconnect attempt {attempt} failed for {config.name}: {e}")
                # Schedule next attempt
                self._schedule_reconnect(server_id, attempt + 1)

        task = asyncio.create_task(_do_reconnect())
        self._reconnect_tasks[server_id] = task
        logger.info(f"Scheduled reconnect for {server_id} in {delay:.1f}s (attempt {attempt})")

    async def handle_connection_lost(self, server_id: str) -> None:
        """Handle unexpected connection loss - trigger reconnect.

        Call this when a connection error is detected during operation.

        Args:
            server_id: ID of the disconnected server
        """
        if server_id in self._connections:
            del self._connections[server_id]

        config = self._server_configs.get(server_id)
        if config and config.enabled:
            logger.info(f"Connection lost to {config.name}, scheduling reconnect")
            self._schedule_reconnect(server_id)

    async def disconnect(self, server_id: str) -> None:
        """Disconnect from a specific server.

        Args:
            server_id: ID of the server to disconnect
        """
        # Cancel any pending reconnect
        if server_id in self._reconnect_tasks:
            self._reconnect_tasks[server_id].cancel()
            del self._reconnect_tasks[server_id]

        # Cleanup sandbox if exists
        if server_id in self._sandboxes:
            await self._sandboxes[server_id].stop()
            del self._sandboxes[server_id]

        if server_id in self._connections:
            # Note: AsyncExitStack handles cleanup
            del self._connections[server_id]
            logger.info(f"Disconnected from server: {server_id}")

        # Remove stored config to prevent auto-reconnect
        self._server_configs.pop(server_id, None)

    async def disconnect_all(self) -> None:
        """Disconnect from all servers and cleanup.

        Ensures no orphaned processes or containers remain.
        """
        # Cancel all reconnect tasks
        for task in self._reconnect_tasks.values():
            task.cancel()
        self._reconnect_tasks.clear()

        # Stop all sandboxes
        for sandbox in self._sandboxes.values():
            await sandbox.stop()
        self._sandboxes.clear()

        self._connections.clear()
        self._server_configs.clear()
        await self._exit_stack.aclose()
        self._exit_stack = AsyncExitStack()
        logger.info("Disconnected from all MCP servers")

    def get_connection(self, server_id: str) -> Optional[MCPConnection]:
        """Get an existing connection by server ID.

        Args:
            server_id: ID of the server

        Returns:
            MCPConnection if connected, None otherwise
        """
        return self._connections.get(server_id)

    def list_connections(self) -> list[MCPConnection]:
        """List all active connections.

        Returns:
            List of active MCPConnection instances
        """
        return list(self._connections.values())

    def get_all_status(self) -> dict[str, MCPServerStatus]:
        """Get status for all connections.

        Returns:
            Dictionary mapping server_id to MCPServerStatus
        """
        return {
            server_id: conn.get_status()
            for server_id, conn in self._connections.items()
        }

    def is_reconnecting(self, server_id: str) -> bool:
        """Check if a server is currently attempting to reconnect.

        Args:
            server_id: ID of the server

        Returns:
            True if reconnection is in progress
        """
        return server_id in self._reconnect_tasks

    def is_sandboxed(self, server_id: str) -> bool:
        """Check if a server is running in a sandbox.

        Args:
            server_id: ID of the server

        Returns:
            True if running in a Docker container sandbox
        """
        return server_id in self._sandboxes

    async def list_tools(self, server_id: str) -> list[dict]:
        """List tools from a specific server.

        Args:
            server_id: ID of the server

        Returns:
            List of tool definitions

        Raises:
            ValueError: If server is not connected
        """
        conn = self._connections.get(server_id)
        if not conn:
            raise ValueError(f"Server {server_id} not connected")
        return await conn.list_tools()

    async def call_tool(
        self, server_id: str, tool_name: str, arguments: dict
    ) -> dict:
        """Call a tool on a specific server.

        Args:
            server_id: ID of the server
            tool_name: Name of the tool to invoke
            arguments: Tool arguments

        Returns:
            Tool result dictionary

        Raises:
            ValueError: If server is not connected
            Exception: If tool call fails (triggers reconnect)
        """
        conn = self._connections.get(server_id)
        if not conn:
            raise ValueError(f"Server {server_id} not connected")
        try:
            return await conn.call_tool(tool_name, arguments)
        except Exception as e:
            # Connection might be broken - trigger reconnect
            logger.error(f"Tool call failed, connection may be lost: {e}")
            await self.handle_connection_lost(server_id)
            raise


# Module-level singleton accessor
_manager: Optional[MCPClientManager] = None


def get_mcp_client_manager() -> MCPClientManager:
    """Get the global MCP client manager instance.

    Returns:
        The singleton MCPClientManager instance
    """
    global _manager
    if _manager is None:
        _manager = MCPClientManager()
    return _manager
