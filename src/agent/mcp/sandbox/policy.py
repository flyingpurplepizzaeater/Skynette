"""Security policies and resource limits for MCP sandboxing."""

from dataclasses import dataclass, field


@dataclass
class SandboxPolicy:
    """Configuration for sandbox security and resource limits."""

    # Resource limits
    memory_limit: str = "512m"  # Docker memory limit format
    cpu_quota: int = 50000  # 50% of one CPU (100000 = 100%)
    cpu_period: int = 100000  # microseconds

    # Network settings
    network_enabled: bool = False  # Default to no network for untrusted
    allowed_hosts: list[str] = field(default_factory=list)  # Whitelist for network

    # Filesystem settings
    read_only_root: bool = True  # Read-only container filesystem
    temp_dir_size: str = "100m"  # Size of /tmp

    # Process limits
    pids_limit: int = 50  # Max processes in container

    # Timeout
    startup_timeout_seconds: int = 30
    execution_timeout_seconds: int = 300  # 5 min max per tool call

    # Container settings
    auto_remove: bool = True  # Remove container after stop
    privileged: bool = False  # Never run privileged


# Default policy for USER_ADDED servers
DEFAULT_POLICY = SandboxPolicy(
    memory_limit="512m",
    cpu_quota=50000,
    network_enabled=False,
    read_only_root=True,
)

# Relaxed policy for VERIFIED servers that need network (optional)
VERIFIED_POLICY = SandboxPolicy(
    memory_limit="1g",
    cpu_quota=100000,
    network_enabled=True,
    read_only_root=True,
)


def get_policy_for_trust_level(trust_level: str) -> SandboxPolicy:
    """Get appropriate policy based on trust level."""
    if trust_level == "builtin":
        # Built-in servers don't use sandbox
        return SandboxPolicy(network_enabled=True, read_only_root=False)
    elif trust_level == "verified":
        return VERIFIED_POLICY
    else:  # user_added
        return DEFAULT_POLICY
