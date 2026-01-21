"""Docker container sandbox for untrusted MCP servers."""

import asyncio
import logging
from typing import Optional, Tuple, TYPE_CHECKING

from src.agent.mcp.models.server import MCPServerConfig
from src.agent.mcp.sandbox.policy import SandboxPolicy, DEFAULT_POLICY

logger = logging.getLogger(__name__)

# Check if Docker is available
DOCKER_AVAILABLE = False
try:
    import docker
    from docker.models.containers import Container
    DOCKER_AVAILABLE = True
except ImportError:
    logger.warning("docker package not installed, sandboxing unavailable")
    docker = None  # type: ignore
    Container = None  # type: ignore

if TYPE_CHECKING:
    from docker.models.containers import Container


class DockerSandbox:
    """
    Docker container sandbox for running untrusted MCP servers.

    Provides process isolation and network restrictions for USER_ADDED servers.
    """

    def __init__(
        self,
        config: MCPServerConfig,
        policy: Optional[SandboxPolicy] = None,
    ):
        """
        Initialize sandbox for an MCP server.

        Args:
            config: Server configuration
            policy: Security policy (defaults to DEFAULT_POLICY)
        """
        self.config = config
        self.policy = policy or DEFAULT_POLICY
        self.container: Optional["Container"] = None
        self._client = None

    @property
    def is_available(self) -> bool:
        """Check if Docker sandboxing is available."""
        if not DOCKER_AVAILABLE:
            return False

        # Check if Docker daemon is running
        try:
            client = docker.from_env()
            client.ping()
            return True
        except Exception:
            return False

    async def start(self) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        """
        Start the sandboxed server and return stdio streams.

        Returns:
            Tuple of (reader, writer) for communicating with the server.

        Raises:
            RuntimeError: If Docker is unavailable or container fails to start.
        """
        if not self.is_available:
            raise RuntimeError(
                "Docker is not available. Install Docker Desktop or disable sandboxing."
            )

        self._client = docker.from_env()

        # Determine the base image based on server command
        image = self._select_image()

        # Build the command
        cmd = self._build_command()

        logger.info(f"Starting sandboxed container for {self.config.name}")
        logger.debug(f"Image: {image}, Command: {cmd}")

        try:
            # Create container with security restrictions
            self.container = self._client.containers.create(
                image=image,
                command=cmd,
                stdin_open=True,
                tty=False,
                detach=True,
                # Resource limits
                mem_limit=self.policy.memory_limit,
                cpu_quota=self.policy.cpu_quota,
                cpu_period=self.policy.cpu_period,
                pids_limit=self.policy.pids_limit,
                # Network isolation
                network_disabled=not self.policy.network_enabled,
                # Filesystem isolation
                read_only=self.policy.read_only_root,
                # Temp directory
                tmpfs={"/tmp": f"size={self.policy.temp_dir_size}"},
                # Security
                privileged=False,
                cap_drop=["ALL"],  # Drop all capabilities
                security_opt=["no-new-privileges:true"],
                # Environment
                environment=self.config.env,
                # Cleanup
                auto_remove=self.policy.auto_remove,
            )

            # Start the container
            self.container.start()

            # Attach to container stdio
            socket = self.container.attach_socket(
                params={
                    "stdin": True,
                    "stdout": True,
                    "stderr": True,
                    "stream": True,
                }
            )

            # Wrap socket as asyncio streams
            reader, writer = await self._wrap_socket_as_streams(socket)
            return reader, writer

        except Exception as e:
            logger.error(f"Failed to start sandboxed container: {e}")
            await self.stop()
            raise RuntimeError(f"Container startup failed: {e}")

    async def stop(self) -> None:
        """Stop and remove the container."""
        if self.container:
            try:
                self.container.stop(timeout=5)
            except Exception as e:
                logger.warning(f"Error stopping container: {e}")
            try:
                if not self.policy.auto_remove:
                    self.container.remove(force=True)
            except Exception:
                pass  # May already be removed
            self.container = None

    def _select_image(self) -> str:
        """Select Docker image based on server command."""
        cmd = self.config.command or ""

        if cmd in ("node", "npx"):
            return "node:20-slim"
        elif cmd in ("python", "python3", "uvx"):
            return "python:3.11-slim"
        elif cmd in ("deno",):
            return "denoland/deno:latest"
        else:
            # Generic image with common tools
            return "ubuntu:22.04"

    def _build_command(self) -> list[str]:
        """Build the container command."""
        cmd = [self.config.command] if self.config.command else []
        cmd.extend(self.config.args)
        return cmd

    async def _wrap_socket_as_streams(
        self,
        socket,
    ) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        """Wrap Docker socket as asyncio streams."""
        # Get the raw socket file descriptor
        raw_socket = socket._sock

        loop = asyncio.get_event_loop()

        # Create reader
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)

        # Create transport and protocol
        transport, _ = await loop.create_connection(
            lambda: protocol,
            sock=raw_socket,
        )

        # Create writer
        writer = asyncio.StreamWriter(transport, protocol, reader, loop)

        return reader, writer


def is_docker_available() -> bool:
    """Check if Docker is available for sandboxing."""
    if not DOCKER_AVAILABLE:
        return False
    try:
        client = docker.from_env()
        client.ping()
        return True
    except Exception:
        return False
