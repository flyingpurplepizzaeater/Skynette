"""
Sandbox Detection Utility

Detects if running in a sandboxed/isolated environment such as Docker,
WSL, cloud dev environments (Codespaces, Gitpod), or virtual machines.

Used by YOLO mode to determine if safety warnings should be shown.
"""

import os
import platform
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


@dataclass
class SandboxInfo:
    """Result of sandbox detection."""

    is_sandboxed: bool
    environment: str | None  # "docker", "wsl", "codespaces", "gitpod", "devcontainer", "lxc", "vm", None
    confidence: Literal["high", "medium", "low"]


class SandboxDetector:
    """
    Detects sandboxed/isolated execution environments.

    Checks for:
    - Docker containers (/.dockerenv, /proc/1/cgroup)
    - LXC containers (/proc/1/cgroup)
    - WSL (/proc/version containing "microsoft" or "wsl")
    - Cloud IDEs (CODESPACES, GITPOD, REMOTE_CONTAINERS environment variables)
    - VMs (heuristic based on platform.machine())

    Detection is designed to err toward "sandboxed" (false positives are
    better than false negatives for user experience).
    """

    @staticmethod
    def detect() -> SandboxInfo:
        """
        Detect if running in a sandboxed environment.

        Returns:
            SandboxInfo with detection result, environment type, and confidence level.
        """
        # Check Docker (highest priority - most common)
        if Path("/.dockerenv").exists():
            return SandboxInfo(True, "docker", "high")

        # Check cgroup for container indicators (Linux)
        cgroup_path = Path("/proc/1/cgroup")
        if cgroup_path.exists():
            try:
                content = cgroup_path.read_text()
                if "docker" in content or "containerd" in content:
                    return SandboxInfo(True, "docker", "high")
                if "lxc" in content:
                    return SandboxInfo(True, "lxc", "high")
            except PermissionError:
                pass
            except OSError:
                pass

        # Check WSL
        proc_version = Path("/proc/version")
        if proc_version.exists():
            try:
                content = proc_version.read_text().lower()
                if "microsoft" in content or "wsl" in content:
                    return SandboxInfo(True, "wsl", "high")
            except PermissionError:
                pass
            except OSError:
                pass

        # Check cloud dev environments (environment variables)
        if os.environ.get("CODESPACES") == "true":
            return SandboxInfo(True, "codespaces", "high")

        if os.environ.get("GITPOD_WORKSPACE_ID"):
            return SandboxInfo(True, "gitpod", "high")

        if os.environ.get("REMOTE_CONTAINERS") == "true":
            return SandboxInfo(True, "devcontainer", "high")

        # Check for VM indicators (lower confidence heuristic)
        try:
            machine = platform.machine().lower()
            if "virtual" in machine:
                return SandboxInfo(True, "vm", "medium")
        except Exception:
            pass

        # No sandbox detected
        return SandboxInfo(False, None, "high")
