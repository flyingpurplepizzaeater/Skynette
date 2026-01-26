"""
Tests for sandbox detection.
"""

import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.agent.safety.sandbox import SandboxDetector, SandboxInfo


class TestSandboxDetector:
    """Tests for SandboxDetector.detect()."""

    def test_detect_returns_sandbox_info(self):
        """detect() returns SandboxInfo dataclass."""
        result = SandboxDetector.detect()
        assert isinstance(result, SandboxInfo)
        assert isinstance(result.is_sandboxed, bool)
        assert result.confidence in ("high", "medium", "low")

    def test_detect_docker_via_dockerenv(self):
        """Detects Docker when /.dockerenv exists."""
        with patch("src.agent.safety.sandbox.Path") as mock_path:
            mock_dockerenv = MagicMock()
            mock_dockerenv.exists.return_value = True
            mock_path.return_value = mock_dockerenv

            result = SandboxDetector.detect()
            assert result.is_sandboxed is True
            assert result.environment == "docker"
            assert result.confidence == "high"

    def test_detect_codespaces_env_var(self):
        """Detects GitHub Codespaces via environment variable."""
        with patch.dict(os.environ, {"CODESPACES": "true"}, clear=False):
            # Mock file checks to return False first
            with patch("src.agent.safety.sandbox.Path") as mock_path:
                mock_instance = MagicMock()
                mock_instance.exists.return_value = False
                mock_path.return_value = mock_instance

                result = SandboxDetector.detect()
                assert result.is_sandboxed is True
                assert result.environment == "codespaces"

    def test_detect_gitpod_env_var(self):
        """Detects Gitpod via GITPOD_WORKSPACE_ID."""
        with patch.dict(os.environ, {"GITPOD_WORKSPACE_ID": "workspace-123"}, clear=False):
            with patch("src.agent.safety.sandbox.Path") as mock_path:
                mock_instance = MagicMock()
                mock_instance.exists.return_value = False
                mock_path.return_value = mock_instance

                result = SandboxDetector.detect()
                assert result.is_sandboxed is True
                assert result.environment == "gitpod"

    def test_detect_devcontainer_env_var(self):
        """Detects VS Code devcontainer via REMOTE_CONTAINERS."""
        with patch.dict(os.environ, {"REMOTE_CONTAINERS": "true"}, clear=False):
            with patch("src.agent.safety.sandbox.Path") as mock_path:
                mock_instance = MagicMock()
                mock_instance.exists.return_value = False
                mock_path.return_value = mock_instance

                result = SandboxDetector.detect()
                assert result.is_sandboxed is True
                assert result.environment == "devcontainer"

    def test_detect_not_sandboxed(self):
        """Returns not sandboxed when no indicators found."""
        # Clear all sandbox env vars
        clean_env = {k: v for k, v in os.environ.items()
                    if k not in ("CODESPACES", "GITPOD_WORKSPACE_ID", "REMOTE_CONTAINERS")}

        with patch.dict(os.environ, clean_env, clear=True):
            with patch("src.agent.safety.sandbox.Path") as mock_path:
                mock_instance = MagicMock()
                mock_instance.exists.return_value = False
                mock_path.return_value = mock_instance

                with patch("platform.machine", return_value="x86_64"):
                    result = SandboxDetector.detect()
                    assert result.is_sandboxed is False
                    assert result.environment is None
                    assert result.confidence == "high"

    def test_detect_handles_permission_error(self):
        """Gracefully handles PermissionError when reading /proc files."""
        with patch("src.agent.safety.sandbox.Path") as mock_path:
            mock_instance = MagicMock()
            mock_instance.exists.return_value = True
            mock_instance.read_text.side_effect = PermissionError("Access denied")
            mock_path.return_value = mock_instance

            # Should not raise, should continue checking
            result = SandboxDetector.detect()
            assert isinstance(result, SandboxInfo)

    def test_detect_docker_via_cgroup(self):
        """Detects Docker via /proc/1/cgroup content."""
        with patch("src.agent.safety.sandbox.Path") as mock_path:
            # Mock different paths with different behaviors
            def path_factory(path_str):
                mock = MagicMock()
                if path_str == "/.dockerenv":
                    mock.exists.return_value = False
                elif path_str == "/proc/1/cgroup":
                    mock.exists.return_value = True
                    mock.read_text.return_value = "0::/docker/abc123"
                else:
                    mock.exists.return_value = False
                return mock

            mock_path.side_effect = path_factory

            result = SandboxDetector.detect()
            assert result.is_sandboxed is True
            assert result.environment == "docker"

    def test_detect_lxc_via_cgroup(self):
        """Detects LXC via /proc/1/cgroup content."""
        with patch("src.agent.safety.sandbox.Path") as mock_path:
            def path_factory(path_str):
                mock = MagicMock()
                if path_str == "/.dockerenv":
                    mock.exists.return_value = False
                elif path_str == "/proc/1/cgroup":
                    mock.exists.return_value = True
                    mock.read_text.return_value = "0::/lxc/container1"
                else:
                    mock.exists.return_value = False
                return mock

            mock_path.side_effect = path_factory

            result = SandboxDetector.detect()
            assert result.is_sandboxed is True
            assert result.environment == "lxc"

    def test_detect_wsl_via_proc_version(self):
        """Detects WSL via /proc/version content."""
        with patch("src.agent.safety.sandbox.Path") as mock_path:
            def path_factory(path_str):
                mock = MagicMock()
                if path_str == "/.dockerenv":
                    mock.exists.return_value = False
                elif path_str == "/proc/1/cgroup":
                    mock.exists.return_value = False
                elif path_str == "/proc/version":
                    mock.exists.return_value = True
                    mock.read_text.return_value = "Linux version 5.10.0-microsoft-standard-WSL2"
                else:
                    mock.exists.return_value = False
                return mock

            mock_path.side_effect = path_factory

            result = SandboxDetector.detect()
            assert result.is_sandboxed is True
            assert result.environment == "wsl"

    def test_detect_vm_via_platform_machine(self):
        """Detects VM via platform.machine() heuristic."""
        # Clear sandbox env vars
        clean_env = {k: v for k, v in os.environ.items()
                    if k not in ("CODESPACES", "GITPOD_WORKSPACE_ID", "REMOTE_CONTAINERS")}

        with patch.dict(os.environ, clean_env, clear=True):
            with patch("src.agent.safety.sandbox.Path") as mock_path:
                mock_instance = MagicMock()
                mock_instance.exists.return_value = False
                mock_path.return_value = mock_instance

                with patch("platform.machine", return_value="Virtual_Machine"):
                    result = SandboxDetector.detect()
                    assert result.is_sandboxed is True
                    assert result.environment == "vm"
                    assert result.confidence == "medium"
