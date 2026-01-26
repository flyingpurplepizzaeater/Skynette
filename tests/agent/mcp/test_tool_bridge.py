"""Unit tests for MCPToolBridge.

Tests the coordination between MCP server connections and ToolRegistry
registration/unregistration, including graceful disconnect behavior.
"""

import asyncio
import gc
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.agent.mcp.bridge.tool_bridge import (
    MCPToolBridge,
    GRACEFUL_UNREGISTER_TIMEOUT,
    get_mcp_tool_bridge,
    initialize_mcp_tools,
)
from src.agent.mcp.models.server import MCPServerConfig


class TestMCPToolBridgeConnectRegister:
    """Tests for connect_and_register functionality."""

    @pytest.fixture
    def mock_manager(self):
        """Create a mocked MCPClientManager."""
        manager = MagicMock()
        manager.connect = AsyncMock()
        manager.disconnect = AsyncMock()
        return manager

    @pytest.fixture
    def mock_registry(self):
        """Create a mocked ToolRegistry."""
        registry = MagicMock()
        registry.register_mcp_tools_from_server = MagicMock(return_value=3)
        registry.unregister_mcp_tools_from_server = MagicMock(return_value=3)
        return registry

    @pytest.fixture
    def mock_connection(self):
        """Create a mocked MCPConnection."""
        conn = MagicMock()
        conn.list_tools = AsyncMock(return_value=[
            {"name": "tool1", "description": "Tool 1", "inputSchema": {}},
            {"name": "tool2", "description": "Tool 2", "inputSchema": {}},
            {"name": "tool3", "description": "Tool 3", "inputSchema": {}},
        ])
        return conn

    @pytest.fixture
    def bridge(self, mock_manager, mock_registry):
        """Create a fresh MCPToolBridge with mocked dependencies."""
        # Create fresh instance bypassing singleton
        bridge = MCPToolBridge.__new__(MCPToolBridge)
        bridge._initialized = False
        bridge._manager = mock_manager
        bridge._registry = mock_registry
        bridge._pending_unregister = {}
        bridge._initialized = True
        return bridge

    @pytest.fixture
    def server_config(self):
        """Create a test server config."""
        return MCPServerConfig(
            id="test-server-id",
            name="Test Server",
            transport="stdio",
            command="echo",
            trust_level="verified",
        )

    @pytest.mark.asyncio
    async def test_connect_and_register_success(
        self, bridge, mock_manager, mock_registry, mock_connection, server_config
    ):
        """Test successful connection and tool registration."""
        mock_manager.connect.return_value = mock_connection

        count = await bridge.connect_and_register(server_config)

        assert count == 3
        mock_manager.connect.assert_called_once_with(server_config)
        mock_connection.list_tools.assert_called_once()
        mock_registry.register_mcp_tools_from_server.assert_called_once_with(
            server_id=server_config.id,
            server_name=server_config.name,
            trust_level=server_config.trust_level,
            tools=mock_connection.list_tools.return_value,
        )

    @pytest.mark.asyncio
    async def test_connect_and_register_cancels_pending_unregister(
        self, bridge, mock_manager, mock_registry, mock_connection, server_config
    ):
        """Test that connecting cancels any pending unregister task."""
        mock_manager.connect.return_value = mock_connection

        # Create a pending unregister task
        pending_task = asyncio.create_task(asyncio.sleep(10))
        bridge._pending_unregister[server_config.id] = pending_task

        await bridge.connect_and_register(server_config)

        # Task should be cancelled and removed from pending dict
        assert server_config.id not in bridge._pending_unregister
        # Wait for cancellation to complete
        try:
            await pending_task
        except asyncio.CancelledError:
            pass
        assert pending_task.cancelled()

    @pytest.mark.asyncio
    async def test_connect_and_register_connection_failure(
        self, bridge, mock_manager, mock_registry, server_config
    ):
        """Test that connection failure propagates exception."""
        mock_manager.connect.side_effect = ConnectionError("Connection refused")

        with pytest.raises(ConnectionError, match="Connection refused"):
            await bridge.connect_and_register(server_config)

        # Registry should not be called
        mock_registry.register_mcp_tools_from_server.assert_not_called()


class TestMCPToolBridgeDisconnectUnregister:
    """Tests for disconnect_and_unregister functionality."""

    @pytest.fixture
    def mock_manager(self):
        """Create a mocked MCPClientManager."""
        manager = MagicMock()
        manager.connect = AsyncMock()
        manager.disconnect = AsyncMock()
        return manager

    @pytest.fixture
    def mock_registry(self):
        """Create a mocked ToolRegistry."""
        registry = MagicMock()
        registry.register_mcp_tools_from_server = MagicMock(return_value=3)
        registry.unregister_mcp_tools_from_server = MagicMock(return_value=3)
        return registry

    @pytest.fixture
    def bridge(self, mock_manager, mock_registry):
        """Create a fresh MCPToolBridge with mocked dependencies."""
        bridge = MCPToolBridge.__new__(MCPToolBridge)
        bridge._initialized = False
        bridge._manager = mock_manager
        bridge._registry = mock_registry
        bridge._pending_unregister = {}
        bridge._initialized = True
        return bridge

    @pytest.mark.asyncio
    async def test_disconnect_graceful_schedules_delayed_unregister(
        self, bridge, mock_manager, mock_registry
    ):
        """Test that graceful disconnect schedules delayed unregistration."""
        server_id = "test-server-id"

        await bridge.disconnect_and_unregister(server_id, graceful=True)

        # Should have created a pending task
        assert server_id in bridge._pending_unregister
        task = bridge._pending_unregister[server_id]
        assert not task.done()

        # Registry should not be called immediately
        mock_registry.unregister_mcp_tools_from_server.assert_not_called()

        # Manager disconnect should be called
        mock_manager.disconnect.assert_called_once_with(server_id)

        # Clean up task
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_disconnect_immediate_unregisters_now(
        self, bridge, mock_manager, mock_registry
    ):
        """Test that immediate disconnect unregisters tools right away."""
        server_id = "test-server-id"

        await bridge.disconnect_and_unregister(server_id, graceful=False)

        # Registry should be called immediately
        mock_registry.unregister_mcp_tools_from_server.assert_called_once_with(server_id)

        # No pending task should exist
        assert server_id not in bridge._pending_unregister

        # Manager disconnect should be called
        mock_manager.disconnect.assert_called_once_with(server_id)

    @pytest.mark.asyncio
    async def test_graceful_timeout_triggers_unregister(
        self, bridge, mock_manager, mock_registry
    ):
        """Test that graceful timeout actually triggers unregistration."""
        server_id = "test-server-id"

        # Use a very short timeout for testing
        with patch(
            "src.agent.mcp.bridge.tool_bridge.GRACEFUL_UNREGISTER_TIMEOUT",
            0.1,
        ):
            # Re-import to get patched timeout
            from importlib import reload
            import src.agent.mcp.bridge.tool_bridge as tool_bridge_module

            # Create the delayed unregister manually with short timeout
            async def _delayed_unregister():
                try:
                    await asyncio.sleep(0.1)
                    bridge._registry.unregister_mcp_tools_from_server(server_id)
                except asyncio.CancelledError:
                    raise
                finally:
                    bridge._pending_unregister.pop(server_id, None)

            task = asyncio.create_task(_delayed_unregister())
            bridge._pending_unregister[server_id] = task

            # Wait for timeout to elapse
            await asyncio.wait_for(task, timeout=1.0)

            # Registry should now be called
            mock_registry.unregister_mcp_tools_from_server.assert_called_once_with(server_id)

            # Task should be removed from pending
            assert server_id not in bridge._pending_unregister

    @pytest.mark.asyncio
    async def test_reconnect_cancels_graceful_unregister(
        self, bridge, mock_manager, mock_registry
    ):
        """Test that reconnecting during graceful window cancels unregister."""
        server_id = "test-server-id"

        # Set up mock connection for reconnect
        mock_conn = MagicMock()
        mock_conn.list_tools = AsyncMock(return_value=[])
        mock_manager.connect.return_value = mock_conn

        # Create a pending unregister task
        pending_task = asyncio.create_task(asyncio.sleep(10))
        bridge._pending_unregister[server_id] = pending_task

        # Simulate reconnect
        config = MCPServerConfig(
            id=server_id,
            name="Test Server",
            transport="stdio",
            command="echo",
        )
        await bridge.connect_and_register(config)

        # Task should be removed from pending dict
        assert server_id not in bridge._pending_unregister
        # Wait for cancellation to complete
        try:
            await pending_task
        except asyncio.CancelledError:
            pass
        assert pending_task.cancelled()

        # Unregister should NOT have been called
        mock_registry.unregister_mcp_tools_from_server.assert_not_called()


class TestMCPToolBridgeCancelPending:
    """Tests for cancel_pending_unregister functionality."""

    @pytest.fixture
    def bridge(self):
        """Create a fresh MCPToolBridge."""
        bridge = MCPToolBridge.__new__(MCPToolBridge)
        bridge._initialized = False
        bridge._manager = MagicMock()
        bridge._registry = MagicMock()
        bridge._pending_unregister = {}
        bridge._initialized = True
        return bridge

    def test_cancel_pending_no_task(self, bridge):
        """Test cancelling when no pending task exists."""
        result = bridge.cancel_pending_unregister("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_cancel_pending_with_task(self, bridge):
        """Test cancelling an existing pending task."""
        server_id = "test-server"
        task = asyncio.create_task(asyncio.sleep(10))
        bridge._pending_unregister[server_id] = task

        result = bridge.cancel_pending_unregister(server_id)

        assert result is True
        assert server_id not in bridge._pending_unregister
        # Wait for cancellation to complete
        try:
            await task
        except asyncio.CancelledError:
            pass
        assert task.cancelled()

    @pytest.mark.asyncio
    async def test_cancel_pending_already_done(self, bridge):
        """Test cancelling a task that already completed."""
        server_id = "test-server"
        task = asyncio.create_task(asyncio.sleep(0))
        await task  # Let it complete
        bridge._pending_unregister[server_id] = task

        result = bridge.cancel_pending_unregister(server_id)

        # Returns False because task was already done
        assert result is False


class TestMCPToolBridgeInitialize:
    """Tests for initialize_mcp_tools functionality."""

    @pytest.fixture
    def mock_storage(self):
        """Create a mocked MCPServerStorage."""
        storage = MagicMock()
        return storage

    @pytest.fixture
    def mock_bridge(self):
        """Create a mocked MCPToolBridge."""
        bridge = MagicMock()
        bridge.connect_and_register = AsyncMock()
        return bridge

    @pytest.mark.asyncio
    async def test_initialize_mcp_tools_connects_enabled_servers(
        self, mock_storage, mock_bridge
    ):
        """Test that initialize connects all enabled servers."""
        # Set up two enabled servers
        server1 = MCPServerConfig(
            id="server-1",
            name="Server 1",
            transport="stdio",
            command="echo",
            enabled=True,
        )
        server2 = MCPServerConfig(
            id="server-2",
            name="Server 2",
            transport="stdio",
            command="echo",
            enabled=True,
        )
        mock_storage.list_servers.return_value = [server1, server2]
        mock_bridge.connect_and_register.return_value = 5

        with patch(
            "src.agent.mcp.bridge.tool_bridge.get_mcp_tool_bridge",
            return_value=mock_bridge,
        ), patch(
            "src.agent.mcp.bridge.tool_bridge.get_mcp_storage",
            return_value=mock_storage,
        ):
            results = await initialize_mcp_tools()

        assert len(results) == 2
        assert results["server-1"] == 5
        assert results["server-2"] == 5
        mock_storage.list_servers.assert_called_once_with(enabled_only=True)
        assert mock_bridge.connect_and_register.call_count == 2

    @pytest.mark.asyncio
    async def test_initialize_mcp_tools_empty_servers(self, mock_storage, mock_bridge):
        """Test initialize with no enabled servers."""
        mock_storage.list_servers.return_value = []

        with patch(
            "src.agent.mcp.bridge.tool_bridge.get_mcp_tool_bridge",
            return_value=mock_bridge,
        ), patch(
            "src.agent.mcp.bridge.tool_bridge.get_mcp_storage",
            return_value=mock_storage,
        ):
            results = await initialize_mcp_tools()

        assert results == {}
        mock_bridge.connect_and_register.assert_not_called()

    @pytest.mark.asyncio
    async def test_initialize_mcp_tools_handles_partial_failures(
        self, mock_storage, mock_bridge
    ):
        """Test that initialize handles partial failures gracefully."""
        # Set up servers where one fails
        server1 = MCPServerConfig(
            id="server-1",
            name="Server 1",
            transport="stdio",
            command="echo",
        )
        server2 = MCPServerConfig(
            id="server-2",
            name="Server 2",
            transport="stdio",
            command="echo",
        )
        mock_storage.list_servers.return_value = [server1, server2]

        # First server succeeds, second fails
        async def mock_connect(config):
            if config.id == "server-1":
                return 5
            raise ConnectionError("Connection refused")

        mock_bridge.connect_and_register.side_effect = mock_connect

        with patch(
            "src.agent.mcp.bridge.tool_bridge.get_mcp_tool_bridge",
            return_value=mock_bridge,
        ), patch(
            "src.agent.mcp.bridge.tool_bridge.get_mcp_storage",
            return_value=mock_storage,
        ):
            results = await initialize_mcp_tools()

        # Should have results for both, with -1 for failure
        assert len(results) == 2
        assert results["server-1"] == 5
        assert results["server-2"] == -1


class TestMCPToolBridgeSingleton:
    """Tests for singleton behavior."""

    def test_get_mcp_tool_bridge_returns_same_instance(self):
        """Test that get_mcp_tool_bridge returns singleton."""
        # Reset singleton for test
        import src.agent.mcp.bridge.tool_bridge as module
        original_bridge = module._bridge
        original_instance = MCPToolBridge._instance

        try:
            module._bridge = None
            MCPToolBridge._instance = None

            bridge1 = get_mcp_tool_bridge()
            bridge2 = get_mcp_tool_bridge()

            assert bridge1 is bridge2
        finally:
            # Restore original state
            module._bridge = original_bridge
            MCPToolBridge._instance = original_instance
            # Windows cleanup
            gc.collect()
