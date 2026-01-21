"""Integration tests for MCP integration infrastructure.

These tests verify the MCP client infrastructure works correctly by testing:
1. Client manager initialization and state management
2. Connection lifecycle methods
3. Tool registry integration with MCP adapters

Real server connection tests are marked as `external` and can be run with:
    pytest -m "external" tests/agent/mcp/test_integration.py

These tests require npx and network access and may fail if external servers
are unavailable.
"""

import pytest
import asyncio
import shutil
from contextlib import AsyncExitStack
from unittest.mock import AsyncMock, MagicMock, patch

from src.agent.mcp.client.manager import MCPClientManager
from src.agent.mcp.models.server import MCPServerConfig, MCPServerStatus
from src.agent.mcp.client.connection import MCPConnection
from src.agent.registry.tool_registry import ToolRegistry


# Check if npx is available for external tests
NPX_AVAILABLE = shutil.which("npx") is not None


class TestMCPClientManagerIntegration:
    """Integration tests for MCPClientManager without external servers."""

    @pytest.fixture
    async def manager(self):
        """Create and initialize a fresh manager for each test."""
        mgr = MCPClientManager.__new__(MCPClientManager)
        mgr._initialized = False
        await mgr.initialize()
        yield mgr
        # Clean up without relying on exit stack
        mgr._connections.clear()
        mgr._server_configs.clear()
        for task in mgr._reconnect_tasks.values():
            task.cancel()
        mgr._reconnect_tasks.clear()

    @pytest.mark.asyncio
    async def test_manager_initialization(self, manager):
        """Test manager initializes correctly."""
        assert manager._initialized is True
        assert manager._connections == {}
        assert manager._server_configs == {}
        assert manager._reconnect_tasks == {}

    @pytest.mark.asyncio
    async def test_list_connections_empty(self, manager):
        """Test listing connections when none exist."""
        connections = manager.list_connections()
        assert connections == []

    @pytest.mark.asyncio
    async def test_get_connection_nonexistent(self, manager):
        """Test getting a connection that doesn't exist."""
        conn = manager.get_connection("nonexistent-server-id")
        assert conn is None

    @pytest.mark.asyncio
    async def test_get_all_status_empty(self, manager):
        """Test getting status when no connections exist."""
        status = manager.get_all_status()
        assert status == {}

    @pytest.mark.asyncio
    async def test_is_reconnecting_false(self, manager):
        """Test is_reconnecting returns False when not reconnecting."""
        assert manager.is_reconnecting("some-server-id") is False

    @pytest.mark.asyncio
    async def test_is_sandboxed_false(self, manager):
        """Test is_sandboxed returns False when not sandboxed."""
        assert manager.is_sandboxed("some-server-id") is False

    @pytest.mark.asyncio
    async def test_list_tools_nonexistent_raises(self, manager):
        """Test listing tools for nonexistent server raises ValueError."""
        with pytest.raises(ValueError, match="not connected"):
            await manager.list_tools("nonexistent-server")

    @pytest.mark.asyncio
    async def test_call_tool_nonexistent_raises(self, manager):
        """Test calling tool for nonexistent server raises ValueError."""
        with pytest.raises(ValueError, match="not connected"):
            await manager.call_tool("nonexistent-server", "tool", {})


class TestMCPConnectionIntegration:
    """Integration tests for MCPConnection."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock MCP session."""
        session = MagicMock()
        # Mock list_tools response
        mock_tool = MagicMock()
        mock_tool.name = "test_tool"
        mock_tool.description = "A test tool"
        mock_tool.inputSchema = {"type": "object", "properties": {}}

        tools_response = MagicMock()
        tools_response.tools = [mock_tool]
        session.list_tools = AsyncMock(return_value=tools_response)

        # Mock call_tool response
        mock_content = MagicMock()
        mock_content.type = "text"
        mock_content.text = "Tool result"

        call_response = MagicMock()
        call_response.content = [mock_content]
        call_response.isError = False
        session.call_tool = AsyncMock(return_value=call_response)

        return session

    @pytest.fixture
    def connection(self, mock_session):
        """Create a connection with mock session."""
        config = MCPServerConfig(
            name="Test Server",
            transport="stdio",
            command="echo",
        )
        return MCPConnection(
            server_id=config.id,
            session=mock_session,
            config=config,
        )

    @pytest.mark.asyncio
    async def test_list_tools_returns_tools(self, connection):
        """Test list_tools returns parsed tool definitions."""
        tools = await connection.list_tools()

        assert len(tools) == 1
        assert tools[0]["name"] == "test_tool"
        assert tools[0]["description"] == "A test tool"
        assert "inputSchema" in tools[0]

    @pytest.mark.asyncio
    async def test_list_tools_caches_result(self, connection, mock_session):
        """Test list_tools caches the result."""
        await connection.list_tools()
        await connection.list_tools()

        # Should only call the session once
        assert mock_session.list_tools.call_count == 1

    @pytest.mark.asyncio
    async def test_invalidate_cache_clears_tools(self, connection, mock_session):
        """Test invalidate_cache clears the tools cache."""
        await connection.list_tools()
        connection.invalidate_cache()
        await connection.list_tools()

        # Should call twice now
        assert mock_session.list_tools.call_count == 2

    @pytest.mark.asyncio
    async def test_call_tool_success(self, connection):
        """Test calling a tool returns parsed result."""
        result = await connection.call_tool("test_tool", {"param": "value"})

        assert result["success"] is True
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "text"
        assert result["content"][0]["text"] == "Tool result"

    @pytest.mark.asyncio
    async def test_call_tool_error(self, connection, mock_session):
        """Test calling a tool with error response."""
        mock_content = MagicMock()
        mock_content.type = "text"
        mock_content.text = "Error message"

        call_response = MagicMock()
        call_response.content = [mock_content]
        call_response.isError = True
        mock_session.call_tool = AsyncMock(return_value=call_response)

        result = await connection.call_tool("test_tool", {})

        assert result["success"] is False

    def test_get_status(self, connection):
        """Test get_status returns correct status."""
        status = connection.get_status()

        assert isinstance(status, MCPServerStatus)
        assert status.server_id == connection.server_id
        assert status.connected is True
        assert status.tools_count == 0  # Before list_tools call

    @pytest.mark.asyncio
    async def test_get_status_after_list_tools(self, connection):
        """Test get_status reflects tools count after listing."""
        await connection.list_tools()
        status = connection.get_status()

        assert status.tools_count == 1


class TestToolRegistryMCPIntegration:
    """Integration tests for ToolRegistry with MCP tools."""

    @pytest.fixture
    def registry(self):
        """Create a fresh registry for testing."""
        reg = ToolRegistry.__new__(ToolRegistry)
        reg._initialized = False
        reg._tools = {}
        reg._mcp_tools = {}
        return reg

    def test_register_mcp_tools_from_server(self, registry):
        """Test registering MCP tools from server response."""
        mock_tools = [
            {
                "name": "tool_one",
                "description": "First tool",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "tool_two",
                "description": "Second tool",
                "inputSchema": {"type": "object", "properties": {}},
            },
        ]

        count = registry.register_mcp_tools_from_server(
            server_id="server-12345678",
            server_name="Test Server",
            trust_level="verified",
            tools=mock_tools,
        )

        assert count == 2
        assert len(registry.get_mcp_tools()) == 2

    def test_unregister_mcp_tools_from_server(self, registry):
        """Test unregistering all tools from a server."""
        mock_tools = [
            {
                "name": "tool_one",
                "description": "First tool",
                "inputSchema": {},
            },
        ]

        registry.register_mcp_tools_from_server(
            server_id="server-12345678",
            server_name="Test Server",
            trust_level="verified",
            tools=mock_tools,
        )

        assert len(registry.get_mcp_tools()) == 1

        count = registry.unregister_mcp_tools_from_server("server-12345678")
        assert count == 1
        assert len(registry.get_mcp_tools()) == 0

    def test_mcp_tools_appear_in_definitions(self, registry):
        """Test MCP tools appear in get_all_definitions."""
        mock_tools = [
            {
                "name": "mcp_tool",
                "description": "MCP tool",
                "inputSchema": {"type": "object", "properties": {}},
            },
        ]

        registry.register_mcp_tools_from_server(
            server_id="server-12345678",
            server_name="Test Server",
            trust_level="verified",
            tools=mock_tools,
        )

        defs = registry.get_all_definitions()
        mcp_defs = [d for d in defs if d.name.startswith("mcp_")]
        assert len(mcp_defs) == 1

    def test_mcp_tools_in_openai_format(self, registry):
        """Test MCP tools appear in OpenAI format."""
        mock_tools = [
            {
                "name": "openai_tool",
                "description": "Tool for OpenAI",
                "inputSchema": {"type": "object", "properties": {"arg": {"type": "string"}}},
            },
        ]

        registry.register_mcp_tools_from_server(
            server_id="server-12345678",
            server_name="Test Server",
            trust_level="verified",
            tools=mock_tools,
        )

        openai_tools = registry.get_openai_tools()
        mcp_tools = [t for t in openai_tools if t["function"]["name"].startswith("mcp_")]
        assert len(mcp_tools) == 1
        assert mcp_tools[0]["type"] == "function"

    def test_mcp_tools_in_anthropic_format(self, registry):
        """Test MCP tools appear in Anthropic format."""
        mock_tools = [
            {
                "name": "anthropic_tool",
                "description": "Tool for Anthropic",
                "inputSchema": {"type": "object", "properties": {}},
            },
        ]

        registry.register_mcp_tools_from_server(
            server_id="server-12345678",
            server_name="Test Server",
            trust_level="verified",
            tools=mock_tools,
        )

        anthropic_tools = registry.get_anthropic_tools()
        mcp_tools = [t for t in anthropic_tools if t["name"].startswith("mcp_")]
        assert len(mcp_tools) == 1
        assert "input_schema" in mcp_tools[0]


# External tests that require real MCP servers
@pytest.mark.external
@pytest.mark.skipif(not NPX_AVAILABLE, reason="npx not available")
class TestExternalMCPServers:
    """Tests that connect to real external MCP servers.

    These tests may fail due to network issues or package unavailability.
    Run with: pytest -m external
    """

    @pytest.fixture
    async def manager(self):
        """Create manager for external tests."""
        mgr = MCPClientManager.__new__(MCPClientManager)
        mgr._initialized = False
        await mgr.initialize()
        yield mgr
        try:
            await mgr.disconnect_all()
        except Exception:
            pass

    @pytest.mark.asyncio
    async def test_connect_to_real_server(self, manager):
        """Test connecting to a real MCP server (if available)."""
        pytest.skip("Skipping external server test - package may not be available")
