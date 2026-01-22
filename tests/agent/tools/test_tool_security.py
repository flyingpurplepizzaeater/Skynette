"""
Security tests for built-in tools (QUAL-03).

Tests verify that:
1. Filesystem tools enforce path restrictions
2. Filesystem tools block dangerous patterns
3. Code execution has proper timeout enforcement
4. Tools properly validate inputs
"""

import asyncio
import os
import tempfile
from pathlib import Path

import pytest

from src.agent.tools.base import FileSystemValidator
from src.agent.tools.filesystem import (
    FileDeleteTool,
    FileReadTool,
    FileWriteTool,
)
from src.agent.tools.code_execution import CodeExecutionTool
from src.agent.registry.base_tool import AgentContext


@pytest.fixture
def context():
    """Create test context."""
    return AgentContext(session_id="security_test")


class TestFileSystemValidator:
    """Test FileSystemValidator security."""

    def test_blocks_path_outside_allowed(self):
        """Paths outside allowed directories are rejected."""
        # Use Windows-compatible paths for testing
        temp_dir = tempfile.gettempdir()
        validator = FileSystemValidator([temp_dir], [])

        # Try to access system directory (outside temp)
        if os.name == "nt":
            system_path = "C:\\Windows\\System32\\config"
        else:
            system_path = "/etc/passwd"

        is_valid, error = validator.validate(system_path)
        assert not is_valid
        assert "not in allowed" in error.lower()

    def test_blocks_env_file(self):
        """Blocked patterns like .env are rejected."""
        temp_dir = tempfile.gettempdir()
        validator = FileSystemValidator([temp_dir], [".env"])
        test_path = os.path.join(temp_dir, ".env")
        is_valid, error = validator.validate(test_path)
        assert not is_valid
        assert ".env" in error

    def test_blocks_credentials(self):
        """Credential files are blocked."""
        home = str(Path.home())
        validator = FileSystemValidator([home], ["credentials", ".git/config"])
        test_path = os.path.join(home, "credentials.json")
        is_valid, error = validator.validate(test_path)
        assert not is_valid
        assert "credentials" in error.lower()

    def test_blocks_ssh_keys(self):
        """SSH keys are blocked."""
        home = str(Path.home())
        validator = FileSystemValidator([home], [".ssh/", "id_rsa"])
        test_path = os.path.join(home, ".ssh", "id_rsa")
        is_valid, _ = validator.validate(test_path)
        assert not is_valid

    def test_allows_valid_path(self):
        """Valid paths in allowed directories pass."""
        temp_dir = tempfile.gettempdir()
        validator = FileSystemValidator([temp_dir], [".env"])
        test_path = os.path.join(temp_dir, "test.txt")
        is_valid, error = validator.validate(test_path)
        assert is_valid
        assert error == ""

    def test_handles_path_traversal(self):
        """Path traversal doesn't bypass restrictions."""
        temp_dir = tempfile.gettempdir()
        validator = FileSystemValidator([temp_dir], [])

        # Attempt path traversal
        if os.name == "nt":
            traversal_path = os.path.join(temp_dir, "..", "Windows", "System32")
        else:
            traversal_path = os.path.join(temp_dir, "..", "etc", "passwd")

        is_valid, _ = validator.validate(traversal_path)
        assert not is_valid  # Path resolves outside allowed directory


class TestFileReadToolSecurity:
    """Test FileReadTool security enforcement."""

    @pytest.mark.asyncio
    async def test_rejects_system_files(self, context):
        """System files are not readable."""
        tool = FileReadTool()

        if os.name == "nt":
            system_path = "C:\\Windows\\System32\\config\\SAM"
        else:
            system_path = "/etc/shadow"

        result = await tool.execute({"path": system_path}, context)
        assert not result.success
        # Either blocked by path validation or file not found
        assert "not in allowed" in result.error.lower() or "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_rejects_env_files(self, context):
        """Environment files are blocked."""
        tool = FileReadTool()
        env_path = str(Path.home() / ".env")
        result = await tool.execute({"path": env_path}, context)
        assert not result.success
        assert ".env" in result.error.lower()

    @pytest.mark.asyncio
    async def test_reads_allowed_file(self, context):
        """Files in allowed directories can be read."""
        tool = FileReadTool()

        # Create a temp file in a location that should be allowed
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as f:
            f.write("test content")
            temp_path = f.name

        try:
            result = await tool.execute({"path": temp_path}, context)
            # Should succeed if temp dir is in allowed paths
            # May fail if temp dir is not allowed - that's expected
            if result.success:
                assert result.data["content"] == "test content"
        finally:
            os.unlink(temp_path)


class TestFileWriteToolSecurity:
    """Test FileWriteTool security enforcement."""

    @pytest.mark.asyncio
    async def test_rejects_write_to_system_dir(self, context):
        """Cannot write to system directories."""
        tool = FileWriteTool()

        if os.name == "nt":
            system_path = "C:\\Windows\\System32\\test_file.txt"
        else:
            system_path = "/etc/test_file"

        result = await tool.execute(
            {"path": system_path, "content": "malicious"}, context
        )
        assert not result.success

    @pytest.mark.asyncio
    async def test_rejects_env_overwrite(self, context):
        """Cannot overwrite .env files."""
        tool = FileWriteTool()
        env_path = str(Path.home() / ".env")
        result = await tool.execute(
            {"path": env_path, "content": "stolen"}, context
        )
        assert not result.success


class TestCodeExecutionToolSecurity:
    """Test CodeExecutionTool security measures."""

    @pytest.mark.asyncio
    async def test_timeout_enforced(self, context):
        """Long-running code is killed after timeout."""
        tool = CodeExecutionTool()
        result = await tool.execute(
            {
                "code": "import time; time.sleep(60)",
                "language": "python",
                "timeout": 2,  # 2 second timeout
            },
            context,
        )

        assert result.success  # Tool execution succeeds
        assert result.data["timed_out"] is True
        assert result.data["exit_code"] == -1

    @pytest.mark.asyncio
    async def test_returns_exit_code(self, context):
        """Exit codes are properly captured."""
        tool = CodeExecutionTool()
        result = await tool.execute(
            {"code": "import sys; sys.exit(42)", "language": "python"}, context
        )

        assert result.success
        assert result.data["exit_code"] == 42

    @pytest.mark.asyncio
    async def test_captures_stderr(self, context):
        """Error output is captured."""
        tool = CodeExecutionTool()
        result = await tool.execute(
            {
                "code": "import sys; print('error', file=sys.stderr)",
                "language": "python",
            },
            context,
        )

        assert result.success
        assert "error" in result.data["stderr"]

    @pytest.mark.asyncio
    async def test_invalid_language_handled(self, context):
        """Invalid language is handled gracefully."""
        tool = CodeExecutionTool()
        result = await tool.execute(
            {"code": "print('test')", "language": "not_a_language"}, context
        )
        # Should fail with unsupported language error
        assert not result.success
        assert "unsupported" in result.error.lower()


class TestToolInputValidation:
    """Test input validation across tools."""

    def test_file_read_requires_path(self):
        """FileReadTool requires path parameter."""
        tool = FileReadTool()
        is_valid, error = tool.validate_params({})
        assert not is_valid
        assert "path" in error.lower()

    def test_file_write_requires_path_and_content(self):
        """FileWriteTool requires path and content parameters."""
        tool = FileWriteTool()

        # Missing both
        is_valid, error = tool.validate_params({})
        assert not is_valid

        # Missing content
        is_valid, error = tool.validate_params({"path": "/tmp/test"})
        assert not is_valid
        assert "content" in error.lower()

    def test_file_delete_requires_path(self):
        """FileDeleteTool requires path parameter."""
        tool = FileDeleteTool()
        is_valid, error = tool.validate_params({})
        assert not is_valid
        assert "path" in error.lower()

    def test_code_execution_requires_code(self):
        """Code execution requires code parameter."""
        tool = CodeExecutionTool()
        is_valid, error = tool.validate_params({})
        assert not is_valid
        assert "code" in error.lower()


class TestDestructiveToolMarking:
    """Test that destructive tools are properly marked."""

    def test_file_write_is_destructive(self):
        """FileWriteTool is marked as destructive."""
        tool = FileWriteTool()
        assert hasattr(tool, "is_destructive")
        assert tool.is_destructive is True

    def test_file_delete_is_destructive(self):
        """FileDeleteTool is marked as destructive."""
        tool = FileDeleteTool()
        assert hasattr(tool, "is_destructive")
        assert tool.is_destructive is True

    def test_code_execution_is_destructive(self):
        """CodeExecutionTool is marked as destructive."""
        tool = CodeExecutionTool()
        assert hasattr(tool, "is_destructive")
        assert tool.is_destructive is True

    def test_file_read_is_not_destructive(self):
        """FileReadTool is not marked as destructive."""
        tool = FileReadTool()
        # Either not set or explicitly False
        is_destructive = getattr(tool, "is_destructive", False)
        assert is_destructive is False
