"""Unit tests for MCP tool adapter."""

import pytest
from unittest.mock import AsyncMock, patch

from src.agent.mcp.adapter.tool_adapter import MCPToolAdapter
from src.agent.registry.base_tool import AgentContext


class TestMCPToolAdapter:
    """Tests for MCPToolAdapter."""

    @pytest.fixture
    def mock_mcp_tool(self):
        """Create a mock MCP tool definition."""
        return {
            "name": "read_file",
            "description": "Read contents of a file",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path"},
                },
                "required": ["path"],
            },
        }

    @pytest.fixture
    def adapter(self, mock_mcp_tool):
        """Create an adapter instance."""
        return MCPToolAdapter(
            mcp_tool=mock_mcp_tool,
            server_id="test-server-12345678",
            server_name="Filesystem",
            trust_level="verified",
        )

    def test_namespaced_tool_name(self, adapter):
        """Test tool name is properly namespaced."""
        assert adapter.name == "mcp_test-ser_read_file"
        assert adapter.original_name == "read_file"

    def test_description_includes_source(self, adapter):
        """Test description includes server name."""
        assert "[Filesystem]" in adapter.description
        assert "Read contents" in adapter.description

    def test_parameters_schema_preserved(self, adapter, mock_mcp_tool):
        """Test parameters schema is preserved."""
        assert adapter.parameters_schema == mock_mcp_tool["inputSchema"]

    def test_get_definition(self, adapter):
        """Test get_definition returns proper ToolDefinition."""
        defn = adapter.get_definition()

        assert defn.name == adapter.name
        assert "Filesystem" in defn.description
        assert defn.category == "mcp:filesystem"
        assert defn.requires_approval is False  # VERIFIED doesn't require approval

    def test_user_added_requires_approval(self, mock_mcp_tool):
        """Test USER_ADDED tools require approval."""
        adapter = MCPToolAdapter(
            mcp_tool=mock_mcp_tool,
            server_id="untrusted-123",
            server_name="Unknown Server",
            trust_level="user_added",
        )

        defn = adapter.get_definition()
        assert defn.requires_approval is True

    def test_builtin_no_approval(self, mock_mcp_tool):
        """Test BUILTIN tools don't require approval."""
        adapter = MCPToolAdapter(
            mcp_tool=mock_mcp_tool,
            server_id="builtin-123",
            server_name="Builtin Server",
            trust_level="builtin",
        )

        defn = adapter.get_definition()
        assert defn.requires_approval is False

    def test_get_mcp_metadata(self, adapter):
        """Test metadata extraction."""
        meta = adapter.get_mcp_metadata()

        assert meta["server_id"] == "test-server-12345678"
        assert meta["server_name"] == "Filesystem"
        assert meta["original_name"] == "read_file"
        assert meta["trust_level"] == "verified"

    def test_openai_format(self, adapter):
        """Test OpenAI format conversion."""
        defn = adapter.get_definition()
        openai_format = defn.to_openai_format()

        assert openai_format["type"] == "function"
        assert openai_format["function"]["name"] == adapter.name
        assert "properties" in openai_format["function"]["parameters"]

    def test_anthropic_format(self, adapter):
        """Test Anthropic format conversion."""
        defn = adapter.get_definition()
        anthropic_format = defn.to_anthropic_format()

        assert anthropic_format["name"] == adapter.name
        assert "input_schema" in anthropic_format

    def test_tool_with_no_description(self):
        """Test adapter handles tool with no description."""
        mcp_tool = {
            "name": "silent_tool",
            "inputSchema": {"type": "object", "properties": {}},
        }
        adapter = MCPToolAdapter(
            mcp_tool=mcp_tool,
            server_id="server-123",
            server_name="Test Server",
            trust_level="verified",
        )
        assert "[Test Server]" in adapter.description
        assert "No description provided" in adapter.description

    def test_tool_with_no_schema(self):
        """Test adapter handles tool with no input schema."""
        mcp_tool = {
            "name": "schemaless_tool",
            "description": "A tool without input schema",
        }
        adapter = MCPToolAdapter(
            mcp_tool=mcp_tool,
            server_id="server-123",
            server_name="Test Server",
            trust_level="verified",
        )
        # Should provide default empty schema
        assert adapter.parameters_schema == {"type": "object", "properties": {}}

    @pytest.mark.asyncio
    async def test_execute_success(self, adapter):
        """Test successful tool execution."""
        context = AgentContext(session_id="test-session")

        # Mock the manager - patch where it's defined
        mock_result = {
            "success": True,
            "content": [{"type": "text", "text": "file contents here"}],
        }

        with patch("src.agent.mcp.client.manager.get_mcp_client_manager") as mock_get_manager:
            mock_manager = AsyncMock()
            mock_manager.call_tool.return_value = mock_result
            mock_get_manager.return_value = mock_manager

            result = await adapter.execute({"path": "/test/file.txt"}, context)

            assert result.success is True
            assert result.data == "file contents here"
            mock_manager.call_tool.assert_called_once_with(
                "test-server-12345678",
                "read_file",
                {"path": "/test/file.txt"},
            )

    @pytest.mark.asyncio
    async def test_execute_error(self, adapter):
        """Test tool execution with error."""
        context = AgentContext(session_id="test-session")

        mock_result = {
            "success": False,
            "content": [{"type": "text", "text": "File not found"}],
        }

        with patch("src.agent.mcp.client.manager.get_mcp_client_manager") as mock_get_manager:
            mock_manager = AsyncMock()
            mock_manager.call_tool.return_value = mock_result
            mock_get_manager.return_value = mock_manager

            result = await adapter.execute({"path": "/nonexistent"}, context)

            assert result.success is False
            assert "File not found" in result.error

    @pytest.mark.asyncio
    async def test_execute_exception(self, adapter):
        """Test tool execution handles exceptions."""
        context = AgentContext(session_id="test-session")

        with patch("src.agent.mcp.client.manager.get_mcp_client_manager") as mock_get_manager:
            mock_manager = AsyncMock()
            mock_manager.call_tool.side_effect = Exception("Connection lost")
            mock_get_manager.return_value = mock_manager

            result = await adapter.execute({"path": "/test"}, context)

            assert result.success is False
            assert "Connection lost" in result.error

    @pytest.mark.asyncio
    async def test_execute_empty_content(self, adapter):
        """Test tool execution with empty content."""
        context = AgentContext(session_id="test-session")

        mock_result = {
            "success": True,
            "content": [],
            "structured": {"key": "value"},
        }

        with patch("src.agent.mcp.client.manager.get_mcp_client_manager") as mock_get_manager:
            mock_manager = AsyncMock()
            mock_manager.call_tool.return_value = mock_result
            mock_get_manager.return_value = mock_manager

            result = await adapter.execute({"path": "/test"}, context)

            assert result.success is True
            # With empty content, falls back to structured
            assert result.data == {"key": "value"}
