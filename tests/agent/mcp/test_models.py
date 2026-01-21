"""Unit tests for MCP models."""

import pytest
from datetime import datetime, UTC

from src.agent.mcp.models.server import (
    MCPServerConfig,
    MCPServerStatus,
)
from src.agent.mcp.models.trust import ToolApproval


class TestMCPServerConfig:
    """Tests for MCPServerConfig model."""

    def test_create_stdio_config(self):
        """Test creating a stdio transport config."""
        config = MCPServerConfig(
            name="Test Server",
            transport="stdio",
            command="npx",
            args=["-y", "@mcp/server-test"],
        )

        assert config.name == "Test Server"
        assert config.transport == "stdio"
        assert config.command == "npx"
        assert config.args == ["-y", "@mcp/server-test"]
        assert config.url is None
        assert config.id  # Should have auto-generated ID

    def test_create_http_config(self):
        """Test creating an HTTP transport config."""
        config = MCPServerConfig(
            name="Remote Server",
            transport="http",
            url="https://mcp.example.com/api",
            headers={"Authorization": "Bearer token"},
        )

        assert config.transport == "http"
        assert config.url == "https://mcp.example.com/api"
        assert config.headers == {"Authorization": "Bearer token"}
        assert config.command is None

    def test_default_trust_level(self):
        """Test default trust level is user_added."""
        config = MCPServerConfig(
            name="Test",
            transport="stdio",
            command="echo",
        )
        assert config.trust_level == "user_added"

    def test_default_sandbox_enabled(self):
        """Test sandbox is enabled by default."""
        config = MCPServerConfig(
            name="Test",
            transport="stdio",
            command="echo",
        )
        assert config.sandbox_enabled is True

    def test_json_serialization(self):
        """Test config serializes to JSON correctly."""
        config = MCPServerConfig(
            name="Test",
            transport="stdio",
            command="npx",
            args=["test"],
            trust_level="verified",
            category="dev_tools",
        )

        json_data = config.model_dump_json()
        # Check transport and trust_level are in the JSON (case-insensitive check)
        json_lower = json_data.lower()
        assert '"transport":"stdio"' in json_lower or '"transport": "stdio"' in json_lower
        assert '"trust_level":"verified"' in json_lower or '"trust_level": "verified"' in json_lower

    def test_from_json(self):
        """Test config can be loaded from JSON."""
        config = MCPServerConfig(
            name="Test",
            transport="stdio",
            command="npx",
        )
        json_data = config.model_dump_json()

        loaded = MCPServerConfig.model_validate_json(json_data)
        assert loaded.name == config.name
        assert loaded.transport == config.transport
        assert loaded.id == config.id

    def test_category_default(self):
        """Test default category is 'other'."""
        config = MCPServerConfig(
            name="Test",
            transport="stdio",
            command="echo",
        )
        assert config.category == "other"

    def test_enabled_default(self):
        """Test enabled defaults to True."""
        config = MCPServerConfig(
            name="Test",
            transport="stdio",
            command="echo",
        )
        assert config.enabled is True


class TestMCPServerStatus:
    """Tests for MCPServerStatus model."""

    def test_create_connected_status(self):
        """Test creating connected status."""
        status = MCPServerStatus(
            server_id="test-123",
            connected=True,
            tools_count=5,
            latency_ms=15.5,
        )

        assert status.connected is True
        assert status.tools_count == 5
        assert status.latency_ms == 15.5

    def test_create_error_status(self):
        """Test creating error status."""
        status = MCPServerStatus(
            server_id="test-123",
            connected=False,
            error="Connection refused",
        )

        assert status.connected is False
        assert status.error == "Connection refused"

    def test_default_values(self):
        """Test status default values."""
        status = MCPServerStatus(server_id="test-123")
        assert status.connected is False
        assert status.connecting is False
        assert status.tools_count == 0
        assert status.latency_ms is None


class TestTrustLevel:
    """Tests for TrustLevel literal type."""

    def test_trust_level_values(self):
        """Test trust level literal values work in config."""
        # Test each valid trust level
        for level in ["builtin", "verified", "user_added"]:
            config = MCPServerConfig(
                name="Test",
                transport="stdio",
                command="echo",
                trust_level=level,
            )
            assert config.trust_level == level

    def test_invalid_trust_level_rejected(self):
        """Test that invalid trust levels are rejected."""
        with pytest.raises(Exception):  # Pydantic validation error
            MCPServerConfig(
                name="Test",
                transport="stdio",
                command="echo",
                trust_level="invalid_level",
            )


class TestToolApproval:
    """Tests for ToolApproval model."""

    def test_create_approval(self):
        """Test creating tool approval."""
        approval = ToolApproval(
            id="approval-1",
            server_id="server-1",
            tool_name="read_file",
            approved=True,
            approved_at=datetime.now(UTC),
        )

        assert approval.approved is True
        assert approval.tool_name == "read_file"
        assert approval.server_id == "server-1"

    def test_default_not_approved(self):
        """Test default approval is False."""
        approval = ToolApproval(
            id="approval-1",
            server_id="server-1",
            tool_name="dangerous_tool",
        )
        assert approval.approved is False
        assert approval.approved_at is None

    def test_approve_method(self):
        """Test the approve() method creates a new approved instance."""
        original = ToolApproval(
            id="approval-1",
            server_id="server-1",
            tool_name="read_file",
        )
        assert original.approved is False

        approved = original.approve()
        assert approved.approved is True
        assert approved.approved_at is not None
        assert approved.id == original.id
        assert approved.tool_name == original.tool_name
