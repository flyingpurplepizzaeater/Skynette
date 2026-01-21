"""Unit tests for MCP server storage."""

import pytest
import tempfile
import os
import gc
from pathlib import Path

from src.agent.mcp.storage.server_storage import MCPServerStorage
from src.agent.mcp.models.server import MCPServerConfig
from src.agent.mcp.models.trust import ToolApproval


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    # Force garbage collection to close any lingering connections on Windows
    gc.collect()
    try:
        os.unlink(path)
    except PermissionError:
        # On Windows, SQLite files may still be locked briefly
        pass


@pytest.fixture
def storage(temp_db):
    """Create storage instance with temp database."""
    return MCPServerStorage(temp_db)


class TestMCPServerStorage:
    """Tests for MCPServerStorage."""

    def test_save_and_load_server(self, storage):
        """Test saving and loading a server config."""
        config = MCPServerConfig(
            name="Test Server",
            transport="stdio",
            command="npx",
            args=["-y", "@mcp/test"],
            category="dev_tools",
        )

        storage.save_server(config)
        loaded = storage.get_server(config.id)

        assert loaded is not None
        assert loaded.name == "Test Server"
        assert loaded.transport == "stdio"
        assert loaded.command == "npx"
        assert loaded.args == ["-y", "@mcp/test"]
        assert loaded.category == "dev_tools"

    def test_list_servers(self, storage):
        """Test listing all servers."""
        config1 = MCPServerConfig(
            name="Server 1",
            transport="stdio",
            command="echo",
        )
        config2 = MCPServerConfig(
            name="Server 2",
            transport="http",
            url="https://example.com",
            enabled=False,
        )

        storage.save_server(config1)
        storage.save_server(config2)

        all_servers = storage.list_servers()
        assert len(all_servers) == 2

        enabled_only = storage.list_servers(enabled_only=True)
        assert len(enabled_only) == 1
        assert enabled_only[0].name == "Server 1"

    def test_delete_server(self, storage):
        """Test deleting a server."""
        config = MCPServerConfig(
            name="To Delete",
            transport="stdio",
            command="echo",
        )

        storage.save_server(config)
        assert storage.get_server(config.id) is not None

        result = storage.delete_server(config.id)
        assert result is True
        assert storage.get_server(config.id) is None

    def test_delete_nonexistent_server(self, storage):
        """Test deleting a server that doesn't exist."""
        result = storage.delete_server("nonexistent-id")
        assert result is False

    def test_get_servers_by_category(self, storage):
        """Test filtering servers by category."""
        config1 = MCPServerConfig(
            name="Dev Tool",
            transport="stdio",
            command="echo",
            category="dev_tools",
        )
        config2 = MCPServerConfig(
            name="Browser Tool",
            transport="stdio",
            command="echo",
            category="browser_tools",
        )

        storage.save_server(config1)
        storage.save_server(config2)

        dev_tools = storage.get_servers_by_category("dev_tools")
        assert len(dev_tools) == 1
        assert dev_tools[0].name == "Dev Tool"

    def test_tool_approval_operations(self, storage):
        """Test tool approval save and load."""
        config = MCPServerConfig(
            name="Server",
            transport="stdio",
            command="echo",
        )
        storage.save_server(config)

        approval = ToolApproval(
            id="approval-1",
            server_id=config.id,
            tool_name="dangerous_tool",
            approved=True,
        )
        storage.save_tool_approval(approval)

        assert storage.is_tool_approved(config.id, "dangerous_tool") is True
        assert storage.is_tool_approved(config.id, "other_tool") is False

    def test_get_tool_approval(self, storage):
        """Test retrieving tool approval record."""
        config = MCPServerConfig(
            name="Server",
            transport="stdio",
            command="echo",
        )
        storage.save_server(config)

        approval = ToolApproval(
            id="approval-1",
            server_id=config.id,
            tool_name="my_tool",
            approved=True,
        )
        storage.save_tool_approval(approval)

        retrieved = storage.get_tool_approval(config.id, "my_tool")
        assert retrieved is not None
        assert retrieved.tool_name == "my_tool"
        assert retrieved.approved is True

    def test_get_nonexistent_approval(self, storage):
        """Test getting approval that doesn't exist."""
        result = storage.get_tool_approval("server-1", "nonexistent_tool")
        assert result is None


class TestServerConfigPersistence:
    """Test complex config persistence."""

    def test_env_and_headers_persist(self, storage):
        """Test that env vars and headers persist correctly."""
        config = MCPServerConfig(
            name="Complex Config",
            transport="http",
            url="https://api.example.com",
            env={"API_KEY": "secret", "DEBUG": "true"},
            headers={"Authorization": "Bearer token"},
        )

        storage.save_server(config)
        loaded = storage.get_server(config.id)

        assert loaded.env == {"API_KEY": "secret", "DEBUG": "true"}
        assert loaded.headers == {"Authorization": "Bearer token"}

    def test_update_existing_server(self, storage):
        """Test updating an existing server config."""
        config = MCPServerConfig(
            name="Original Name",
            transport="stdio",
            command="echo",
        )
        storage.save_server(config)

        # Update the config
        config_updated = MCPServerConfig(
            id=config.id,  # Same ID
            name="Updated Name",
            transport="stdio",
            command="npx",
        )
        storage.save_server(config_updated)

        loaded = storage.get_server(config.id)
        assert loaded.name == "Updated Name"
        assert loaded.command == "npx"

        # Should still be just one server
        all_servers = storage.list_servers()
        assert len(all_servers) == 1

    def test_server_deletion_removes_approvals(self, storage):
        """Test that deleting a server also removes its tool approvals."""
        config = MCPServerConfig(
            name="Server",
            transport="stdio",
            command="echo",
        )
        storage.save_server(config)

        approval = ToolApproval(
            id="approval-1",
            server_id=config.id,
            tool_name="tool1",
            approved=True,
        )
        storage.save_tool_approval(approval)

        # Verify approval exists
        assert storage.is_tool_approved(config.id, "tool1") is True

        # Delete server
        storage.delete_server(config.id)

        # Approval should be gone
        assert storage.is_tool_approved(config.id, "tool1") is False
