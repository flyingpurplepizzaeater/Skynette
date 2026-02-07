"""
Docker Integration Nodes - Container management for development workflows.
"""

import asyncio
import subprocess

from src.core.nodes.base import BaseNode, FieldType, NodeField


class DockerBuildNode(BaseNode):
    """Build a Docker image."""

    type = "docker-build"
    name = "Docker: Build"
    category = "Coding"
    description = "Build a Docker image from Dockerfile"
    icon = "build"
    color = "#2496ED"  # Docker blue

    inputs = [
        NodeField(
            name="context_path",
            label="Build Context",
            type=FieldType.STRING,
            required=True,
            description="Path to build context (usually project root).",
        ),
        NodeField(
            name="dockerfile",
            label="Dockerfile",
            type=FieldType.STRING,
            required=False,
            default="Dockerfile",
        ),
        NodeField(
            name="tag",
            label="Image Tag",
            type=FieldType.STRING,
            required=True,
            description="Tag for the built image (e.g., myapp:latest).",
        ),
        NodeField(
            name="build_args",
            label="Build Args",
            type=FieldType.JSON,
            required=False,
            description="Build arguments as JSON object.",
        ),
        NodeField(
            name="no_cache", label="No Cache", type=FieldType.BOOLEAN, required=False, default=False
        ),
        NodeField(
            name="platform",
            label="Platform",
            type=FieldType.STRING,
            required=False,
            description="Target platform (e.g., linux/amd64).",
        ),
    ]

    outputs = [
        NodeField(name="success", label="Success", type=FieldType.BOOLEAN),
        NodeField(name="image_id", label="Image ID", type=FieldType.STRING),
        NodeField(name="tag", label="Image Tag", type=FieldType.STRING),
        NodeField(name="output", label="Build Output", type=FieldType.TEXT),
        NodeField(name="error", label="Error", type=FieldType.STRING),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        context_path = config.get("context_path", ".")
        dockerfile = config.get("dockerfile", "Dockerfile")
        tag = config.get("tag", "")
        build_args = config.get("build_args", {})
        no_cache = config.get("no_cache", False)
        platform = config.get("platform")

        cmd = ["docker", "build", "-t", tag, "-f", dockerfile]

        if no_cache:
            cmd.append("--no-cache")
        if platform:
            cmd.extend(["--platform", platform])
        for key, value in (build_args or {}).items():
            cmd.extend(["--build-arg", f"{key}={value}"])

        cmd.append(context_path)

        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(
                None, lambda: subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            )

            if result.returncode == 0:
                # Get image ID
                inspect_result = await loop.run_in_executor(
                    None,
                    lambda: subprocess.run(
                        ["docker", "inspect", "--format={{.Id}}", tag],
                        capture_output=True,
                        text=True,
                    ),
                )
                image_id = inspect_result.stdout.strip()[:12]

                return {
                    "success": True,
                    "image_id": image_id,
                    "tag": tag,
                    "output": result.stdout,
                    "error": "",
                }

            return {
                "success": False,
                "image_id": "",
                "tag": tag,
                "output": result.stdout,
                "error": result.stderr,
            }
        except Exception as e:
            return {
                "success": False,
                "image_id": "",
                "tag": tag,
                "output": "",
                "error": str(e),
            }


class DockerRunNode(BaseNode):
    """Run a Docker container."""

    type = "docker-run"
    name = "Docker: Run"
    category = "Coding"
    description = "Run a Docker container"
    icon = "play_arrow"
    color = "#2496ED"

    inputs = [
        NodeField(name="image", label="Image", type=FieldType.STRING, required=True),
        NodeField(name="name", label="Container Name", type=FieldType.STRING, required=False),
        NodeField(name="command", label="Command", type=FieldType.STRING, required=False),
        NodeField(
            name="ports",
            label="Port Mappings",
            type=FieldType.STRING,
            required=False,
            description="Port mappings (e.g., 8080:80,3000:3000).",
        ),
        NodeField(
            name="volumes",
            label="Volume Mounts",
            type=FieldType.STRING,
            required=False,
            description="Volume mounts (e.g., ./data:/app/data).",
        ),
        NodeField(
            name="env_vars", label="Environment Variables", type=FieldType.JSON, required=False
        ),
        NodeField(
            name="detach",
            label="Run Detached",
            type=FieldType.BOOLEAN,
            required=False,
            default=True,
        ),
        NodeField(
            name="remove",
            label="Auto Remove",
            type=FieldType.BOOLEAN,
            required=False,
            default=False,
        ),
        NodeField(name="network", label="Network", type=FieldType.STRING, required=False),
    ]

    outputs = [
        NodeField(name="success", label="Success", type=FieldType.BOOLEAN),
        NodeField(name="container_id", label="Container ID", type=FieldType.STRING),
        NodeField(name="output", label="Output", type=FieldType.TEXT),
        NodeField(name="error", label="Error", type=FieldType.STRING),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        image = config.get("image", "")
        name = config.get("name")
        command = config.get("command")
        ports = config.get("ports", "")
        volumes = config.get("volumes", "")
        env_vars = config.get("env_vars", {})
        detach = config.get("detach", True)
        remove = config.get("remove", False)
        network = config.get("network")

        cmd = ["docker", "run"]

        if detach:
            cmd.append("-d")
        if remove:
            cmd.append("--rm")
        if name:
            cmd.extend(["--name", name])
        if network:
            cmd.extend(["--network", network])

        # Ports
        for port in ports.split(","):
            if port.strip():
                cmd.extend(["-p", port.strip()])

        # Volumes
        for vol in volumes.split(","):
            if vol.strip():
                cmd.extend(["-v", vol.strip()])

        # Environment variables
        for key, value in (env_vars or {}).items():
            cmd.extend(["-e", f"{key}={value}"])

        cmd.append(image)

        if command:
            cmd.extend(command.split())

        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(
                None, lambda: subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            )

            if result.returncode == 0:
                container_id = result.stdout.strip()[:12]
                return {
                    "success": True,
                    "container_id": container_id,
                    "output": result.stdout,
                    "error": "",
                }

            return {
                "success": False,
                "container_id": "",
                "output": result.stdout,
                "error": result.stderr,
            }
        except Exception as e:
            return {"success": False, "container_id": "", "output": "", "error": str(e)}


class DockerComposeNode(BaseNode):
    """Run Docker Compose commands."""

    type = "docker-compose"
    name = "Docker: Compose"
    category = "Coding"
    description = "Run Docker Compose commands"
    icon = "layers"
    color = "#2496ED"

    inputs = [
        NodeField(name="project_path", label="Project Path", type=FieldType.STRING, required=True),
        NodeField(
            name="compose_file",
            label="Compose File",
            type=FieldType.STRING,
            required=False,
            default="docker-compose.yml",
        ),
        NodeField(
            name="action",
            label="Action",
            type=FieldType.SELECT,
            required=True,
            default="up",
            options=[
                {"value": "up", "label": "Up (Start)"},
                {"value": "down", "label": "Down (Stop)"},
                {"value": "build", "label": "Build"},
                {"value": "restart", "label": "Restart"},
                {"value": "logs", "label": "View Logs"},
                {"value": "ps", "label": "List Containers"},
            ],
        ),
        NodeField(
            name="detach",
            label="Detached Mode",
            type=FieldType.BOOLEAN,
            required=False,
            default=True,
        ),
        NodeField(
            name="build_on_up",
            label="Build on Up",
            type=FieldType.BOOLEAN,
            required=False,
            default=False,
        ),
        NodeField(name="service", label="Specific Service", type=FieldType.STRING, required=False),
    ]

    outputs = [
        NodeField(name="success", label="Success", type=FieldType.BOOLEAN),
        NodeField(name="output", label="Output", type=FieldType.TEXT),
        NodeField(name="containers", label="Containers", type=FieldType.JSON),
        NodeField(name="error", label="Error", type=FieldType.STRING),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        project_path = config.get("project_path", ".")
        compose_file = config.get("compose_file", "docker-compose.yml")
        action = config.get("action", "up")
        detach = config.get("detach", True)
        build_on_up = config.get("build_on_up", False)
        service = config.get("service")

        cmd = ["docker", "compose", "-f", compose_file]

        if action == "up":
            cmd.append("up")
            if detach:
                cmd.append("-d")
            if build_on_up:
                cmd.append("--build")
        elif action == "down":
            cmd.extend(["down", "--remove-orphans"])
        elif action == "build":
            cmd.append("build")
        elif action == "restart":
            cmd.append("restart")
        elif action == "logs":
            cmd.extend(["logs", "--tail=100"])
        elif action == "ps":
            cmd.append("ps")

        if service:
            cmd.append(service)

        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    cmd, capture_output=True, text=True, cwd=project_path, timeout=300
                ),
            )

            containers = []
            if action == "ps":
                # Parse ps output
                lines = result.stdout.strip().split("\n")[1:]  # Skip header
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 4:
                        containers.append(
                            {
                                "name": parts[0],
                                "status": parts[3] if len(parts) > 3 else "unknown",
                            }
                        )

            return {
                "success": result.returncode == 0,
                "output": result.stdout + result.stderr,
                "containers": containers,
                "error": result.stderr if result.returncode != 0 else "",
            }
        except Exception as e:
            return {"success": False, "output": "", "containers": [], "error": str(e)}


class DockerExecNode(BaseNode):
    """Execute command in running container."""

    type = "docker-exec"
    name = "Docker: Exec"
    category = "Coding"
    description = "Execute command in a running container"
    icon = "terminal"
    color = "#2496ED"

    inputs = [
        NodeField(
            name="container", label="Container ID/Name", type=FieldType.STRING, required=True
        ),
        NodeField(name="command", label="Command", type=FieldType.STRING, required=True),
        NodeField(name="workdir", label="Working Directory", type=FieldType.STRING, required=False),
        NodeField(name="user", label="User", type=FieldType.STRING, required=False),
        NodeField(
            name="env_vars", label="Environment Variables", type=FieldType.JSON, required=False
        ),
    ]

    outputs = [
        NodeField(name="success", label="Success", type=FieldType.BOOLEAN),
        NodeField(name="stdout", label="Standard Output", type=FieldType.TEXT),
        NodeField(name="stderr", label="Standard Error", type=FieldType.TEXT),
        NodeField(name="return_code", label="Return Code", type=FieldType.NUMBER),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        container = config.get("container", "")
        command = config.get("command", "")
        workdir = config.get("workdir")
        user = config.get("user")
        env_vars = config.get("env_vars", {})

        cmd = ["docker", "exec"]

        if workdir:
            cmd.extend(["-w", workdir])
        if user:
            cmd.extend(["-u", user])
        for key, value in (env_vars or {}).items():
            cmd.extend(["-e", f"{key}={value}"])

        cmd.append(container)
        cmd.extend(["sh", "-c", command])

        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(
                None, lambda: subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            )

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
            }
        except Exception as e:
            return {"success": False, "stdout": "", "stderr": str(e), "return_code": -1}


class DockerLogsNode(BaseNode):
    """Get container logs."""

    type = "docker-logs"
    name = "Docker: Logs"
    category = "Coding"
    description = "Get logs from a Docker container"
    icon = "description"
    color = "#2496ED"

    inputs = [
        NodeField(
            name="container", label="Container ID/Name", type=FieldType.STRING, required=True
        ),
        NodeField(
            name="tail", label="Tail Lines", type=FieldType.NUMBER, required=False, default=100
        ),
        NodeField(
            name="since",
            label="Since",
            type=FieldType.STRING,
            required=False,
            description="Show logs since (e.g., 10m, 1h, 2023-01-01).",
        ),
        NodeField(
            name="timestamps",
            label="Show Timestamps",
            type=FieldType.BOOLEAN,
            required=False,
            default=False,
        ),
    ]

    outputs = [
        NodeField(name="logs", label="Logs", type=FieldType.TEXT),
        NodeField(name="line_count", label="Line Count", type=FieldType.NUMBER),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        container = config.get("container", "")
        tail = int(config.get("tail", 100))
        since = config.get("since")
        timestamps = config.get("timestamps", False)

        cmd = ["docker", "logs", "--tail", str(tail)]

        if since:
            cmd.extend(["--since", since])
        if timestamps:
            cmd.append("--timestamps")

        cmd.append(container)

        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(
                None, lambda: subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            )

            logs = result.stdout + result.stderr
            return {
                "logs": logs,
                "line_count": len(logs.split("\n")),
            }
        except Exception as e:
            return {"logs": str(e), "line_count": 0}


class DockerPushNode(BaseNode):
    """Push image to registry."""

    type = "docker-push"
    name = "Docker: Push"
    category = "Coding"
    description = "Push Docker image to registry"
    icon = "cloud_upload"
    color = "#2496ED"

    inputs = [
        NodeField(
            name="image",
            label="Image Tag",
            type=FieldType.STRING,
            required=True,
            description="Full image tag (e.g., registry.io/image:tag).",
        ),
        NodeField(name="registry", label="Registry URL", type=FieldType.STRING, required=False),
        NodeField(name="username", label="Username", type=FieldType.STRING, required=False),
        NodeField(name="password", label="Password", type=FieldType.SECRET, required=False),
    ]

    outputs = [
        NodeField(name="success", label="Success", type=FieldType.BOOLEAN),
        NodeField(name="digest", label="Image Digest", type=FieldType.STRING),
        NodeField(name="output", label="Output", type=FieldType.TEXT),
        NodeField(name="error", label="Error", type=FieldType.STRING),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        image = config.get("image", "")
        registry = config.get("registry")
        username = config.get("username")
        password = config.get("password")

        loop = asyncio.get_event_loop()

        try:
            # Login if credentials provided
            if username and password and registry:
                login_cmd = ["docker", "login", registry, "-u", username, "--password-stdin"]
                await loop.run_in_executor(
                    None,
                    lambda: subprocess.run(
                        login_cmd, input=password, capture_output=True, text=True
                    ),
                )

            # Push
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    ["docker", "push", image], capture_output=True, text=True, timeout=600
                ),
            )

            if result.returncode == 0:
                # Extract digest
                import re

                digest_match = re.search(r"digest: (sha256:\w+)", result.stdout)
                digest = digest_match.group(1) if digest_match else ""

                return {
                    "success": True,
                    "digest": digest,
                    "output": result.stdout,
                    "error": "",
                }

            return {
                "success": False,
                "digest": "",
                "output": result.stdout,
                "error": result.stderr,
            }
        except Exception as e:
            return {"success": False, "digest": "", "output": "", "error": str(e)}
