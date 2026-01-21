# Phase 9: MCP Integration - Research

**Researched:** 2026-01-21
**Domain:** MCP Protocol, Python SDK, Transport mechanisms, Tool discovery, Security sandboxing
**Confidence:** HIGH

## Summary

This research covers implementing Skynette as an MCP Host that connects to external MCP servers, discovers tools, and integrates them into the existing ToolRegistry. The Model Context Protocol (MCP) is an open standard introduced by Anthropic (November 2024) that standardizes how AI systems connect to external tools, systems, and data sources.

The MCP ecosystem is mature with 97+ million monthly SDK downloads, 10,000+ active servers, and first-class support in Claude, ChatGPT, Cursor, and VS Code. The official Python SDK (`mcp` package) provides a complete client implementation with support for stdio (local) and Streamable HTTP (remote) transports. The SDK handles JSON-RPC 2.0 messaging, session management, and tool discovery.

Key implementation decisions align with the 09-CONTEXT.md constraints: support both manual form and mcp.json import for server configuration, ship with curated vetted servers (filesystem, browser), validate connections on add, organize by category, use allowlist approach for tools, and implement three-tier trust system with sandboxing.

**Primary recommendation:** Use the official `mcp` Python SDK with `ClientSession` for connecting to MCP servers. Extend the existing `ToolRegistry` singleton with an `MCPToolAdapter` that wraps MCP tools as `BaseTool` instances. Implement sandboxing via Docker containers with seccomp profiles for untrusted servers.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| mcp | >=1.25.0 | Official Python MCP SDK | Anthropic's official SDK, handles protocol details, 8M+ weekly downloads |
| httpx | >=0.27.0 | HTTP client for Streamable HTTP transport | Already in stack, async support, required by mcp SDK |
| docker | >=7.0.0 | Container management for sandboxing | Industry standard for process isolation, Python API available |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| asyncio | stdlib | Subprocess management for stdio transport | Already used, MCP SDK builds on asyncio |
| pydantic | >=2.0.0 | Server configuration models | Already in stack, type-safe config storage |
| jsonschema | >=4.21.0 | Tool parameter validation | Already in stack, validate MCP tool schemas |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Official mcp SDK | fastmcp | FastMCP is great for servers but official SDK better for clients |
| Docker sandboxing | gVisor/Firecracker | Higher security but much more complex setup |
| Manual JSON-RPC | mcp SDK ClientSession | SDK handles protocol details, session lifecycle |

**Installation:**
```bash
pip install "mcp>=1.25.0" "docker>=7.0.0"
# httpx, pydantic, asyncio already in stack
```

## Architecture Patterns

### Recommended Project Structure
```
src/
  agent/
    mcp/                      # NEW: MCP integration
      __init__.py
      models/                 # MCP-specific models
        __init__.py
        server.py             # MCPServerConfig, MCPServerStatus
        trust.py              # TrustLevel, ToolApproval
      client/                 # MCP client implementation
        __init__.py
        manager.py            # MCPClientManager (manages all connections)
        connection.py         # MCPConnection (single server connection)
        transport.py          # Transport factory (stdio vs HTTP)
      adapter/                # Tool registry integration
        __init__.py
        tool_adapter.py       # MCPToolAdapter (wraps MCP tools as BaseTool)
      sandbox/                # Security sandboxing
        __init__.py
        docker_sandbox.py     # Docker container sandbox
        policy.py             # Seccomp/network policies
      storage/                # Server config persistence
        __init__.py
        server_storage.py     # SQLite storage for server configs
  ui/
    views/
      settings/
        mcp_servers.py        # MCP server management UI
    dialogs/
      mcp_add_server.py       # Add server dialog
      mcp_import_config.py    # Import from mcp.json dialog
      tool_approval.py        # Tool approval dialog
```

### Pattern 1: MCP Client Manager (Singleton)
**What:** Central manager for all MCP server connections
**When to use:** All MCP operations go through this manager
**Why:** Consistent with existing registry patterns, centralized connection lifecycle

```python
# Source: Official MCP Python SDK + existing ToolRegistry pattern
from typing import Optional
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.streamable_http import streamablehttp_client
from contextlib import AsyncExitStack

class MCPClientManager:
    """Singleton manager for all MCP server connections."""

    _instance: Optional["MCPClientManager"] = None
    _connections: dict[str, "MCPConnection"]  # server_id -> connection
    _exit_stack: AsyncExitStack

    def __new__(cls) -> "MCPClientManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    async def connect(self, config: MCPServerConfig) -> MCPConnection:
        """Connect to an MCP server based on config."""
        if config.id in self._connections:
            return self._connections[config.id]

        if config.transport == "stdio":
            connection = await self._connect_stdio(config)
        else:  # "http" or "sse"
            connection = await self._connect_http(config)

        self._connections[config.id] = connection
        return connection

    async def _connect_stdio(self, config: MCPServerConfig) -> MCPConnection:
        """Connect via stdio transport."""
        server_params = StdioServerParameters(
            command=config.command,
            args=config.args,
            env=config.env,
        )

        transport = await self._exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        read_stream, write_stream = transport

        session = await self._exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )
        await session.initialize()

        return MCPConnection(
            server_id=config.id,
            session=session,
            config=config,
        )

    async def _connect_http(self, config: MCPServerConfig) -> MCPConnection:
        """Connect via Streamable HTTP transport."""
        headers = config.headers or {}

        transport = await self._exit_stack.enter_async_context(
            streamablehttp_client(config.url, headers=headers)
        )
        read_stream, write_stream, _ = transport

        session = await self._exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )
        await session.initialize()

        return MCPConnection(
            server_id=config.id,
            session=session,
            config=config,
        )

    async def list_tools(self, server_id: str) -> list[ToolDefinition]:
        """List tools from a specific server."""
        connection = self._connections.get(server_id)
        if not connection:
            raise ValueError(f"Server {server_id} not connected")

        response = await connection.session.list_tools()
        return [
            self._convert_mcp_tool(tool, server_id)
            for tool in response.tools
        ]

    async def call_tool(
        self,
        server_id: str,
        tool_name: str,
        arguments: dict
    ) -> ToolResult:
        """Call a tool on a specific server."""
        connection = self._connections.get(server_id)
        if not connection:
            raise ValueError(f"Server {server_id} not connected")

        result = await connection.session.call_tool(tool_name, arguments)
        return ToolResult(
            tool_call_id=str(uuid4()),
            success=not result.isError if hasattr(result, 'isError') else True,
            data=result.content,
        )
```

### Pattern 2: MCP Tool Adapter
**What:** Wraps MCP tools as BaseTool instances for ToolRegistry integration
**When to use:** Making MCP tools available to the agent

```python
# Source: Existing BaseTool pattern + MCP SDK tool format
from src.agent.registry.base_tool import BaseTool, AgentContext
from src.agent.models.tool import ToolDefinition, ToolResult

class MCPToolAdapter(BaseTool):
    """Adapter that wraps an MCP tool as a BaseTool."""

    def __init__(
        self,
        mcp_tool: dict,  # From MCP list_tools response
        server_id: str,
        manager: MCPClientManager,
    ):
        self._mcp_tool = mcp_tool
        self._server_id = server_id
        self._manager = manager

        # Set BaseTool attributes
        self.name = f"mcp_{server_id}_{mcp_tool['name']}"  # Namespaced
        self.description = mcp_tool.get('description', '')
        self.parameters_schema = mcp_tool.get('inputSchema', {
            "type": "object",
            "properties": {}
        })

        # Metadata for UI
        self.source_server = server_id
        self.original_name = mcp_tool['name']

    async def execute(self, params: dict, context: AgentContext) -> ToolResult:
        """Execute the MCP tool."""
        result = await self._manager.call_tool(
            self._server_id,
            self.original_name,  # Use original name for MCP call
            params,
        )
        return result

    def get_definition(self) -> ToolDefinition:
        """Get tool definition with MCP metadata."""
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=self.parameters_schema,
            category=f"mcp:{self._server_id}",  # Category = source server
            is_destructive=False,  # Will be set based on trust level
            requires_approval=True,  # Default for MCP tools
        )
```

### Pattern 3: Server Configuration Model
**What:** Pydantic models for MCP server configuration
**When to use:** Storing and validating server configs

```python
# Source: MCP JSON configuration format + 09-CONTEXT.md decisions
from pydantic import BaseModel, Field
from typing import Optional, Literal
from enum import Enum
from datetime import datetime, UTC

class TrustLevel(str, Enum):
    BUILTIN = "builtin"           # Built into Skynette
    VERIFIED = "verified"         # Third-party, verified
    USER_ADDED = "user_added"     # User-added, untrusted

class TransportType(str, Enum):
    STDIO = "stdio"
    HTTP = "http"
    SSE = "sse"  # Legacy, maps to HTTP

class ServerCategory(str, Enum):
    BROWSER_TOOLS = "browser_tools"
    FILE_TOOLS = "file_tools"
    DEV_TOOLS = "dev_tools"
    DATA_TOOLS = "data_tools"
    PRODUCTIVITY = "productivity"
    OTHER = "other"

class MCPServerConfig(BaseModel):
    """Configuration for an MCP server."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: Optional[str] = None

    # Transport configuration
    transport: TransportType

    # For stdio transport
    command: Optional[str] = None
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)

    # For HTTP transport
    url: Optional[str] = None
    headers: dict[str, str] = Field(default_factory=dict)

    # Trust and security
    trust_level: TrustLevel = TrustLevel.USER_ADDED
    sandbox_enabled: bool = True  # Default to sandboxed for user-added

    # Organization
    category: ServerCategory = ServerCategory.OTHER
    enabled: bool = True

    # Status tracking
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_connected: Optional[datetime] = None
    last_error: Optional[str] = None

class MCPServerStatus(BaseModel):
    """Runtime status of an MCP server connection."""

    server_id: str
    connected: bool = False
    connecting: bool = False
    latency_ms: Optional[float] = None
    tools_count: int = 0
    last_active: Optional[datetime] = None
    error: Optional[str] = None
```

### Pattern 4: Import from mcp.json
**What:** Parse Claude Desktop/Claude Code mcp.json format
**When to use:** Bulk import of server configurations

```python
# Source: MCP JSON configuration standard
import json
from pathlib import Path

def import_mcp_config(config_path: Path) -> list[MCPServerConfig]:
    """Import server configs from mcp.json format."""
    with open(config_path) as f:
        data = json.load(f)

    configs = []
    mcp_servers = data.get("mcpServers", {})

    for name, server_data in mcp_servers.items():
        # Determine transport type
        if "url" in server_data:
            transport = TransportType.HTTP
        else:
            transport = TransportType.STDIO

        config = MCPServerConfig(
            name=name,
            transport=transport,
            command=server_data.get("command"),
            args=server_data.get("args", []),
            env=server_data.get("env", {}),
            url=server_data.get("url"),
            headers=server_data.get("headers", {}),
            trust_level=TrustLevel.USER_ADDED,  # Imported = untrusted
        )
        configs.append(config)

    return configs
```

### Pattern 5: Docker Sandbox for Untrusted Servers
**What:** Run untrusted MCP servers in isolated Docker containers
**When to use:** User-added servers with `sandbox_enabled=True`

```python
# Source: Security research + Docker best practices
import docker
from docker.models.containers import Container

class DockerSandbox:
    """Docker container sandbox for untrusted MCP servers."""

    DEFAULT_SECCOMP_PROFILE = {
        "defaultAction": "SCMP_ACT_ERRNO",
        "architectures": ["SCMP_ARCH_X86_64"],
        "syscalls": [
            # Minimal syscalls for stdio communication
            {"name": "read", "action": "SCMP_ACT_ALLOW"},
            {"name": "write", "action": "SCMP_ACT_ALLOW"},
            {"name": "close", "action": "SCMP_ACT_ALLOW"},
            {"name": "fstat", "action": "SCMP_ACT_ALLOW"},
            {"name": "mmap", "action": "SCMP_ACT_ALLOW"},
            {"name": "mprotect", "action": "SCMP_ACT_ALLOW"},
            {"name": "munmap", "action": "SCMP_ACT_ALLOW"},
            {"name": "brk", "action": "SCMP_ACT_ALLOW"},
            {"name": "exit_group", "action": "SCMP_ACT_ALLOW"},
            # Add more as needed for specific servers
        ]
    }

    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.client = docker.from_env()
        self.container: Optional[Container] = None

    async def start(self) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        """Start sandboxed server and return stdio streams."""
        # Create container with restrictions
        self.container = self.client.containers.create(
            image=self._get_base_image(),
            command=self._build_command(),
            stdin_open=True,
            tty=False,
            network_disabled=not self.config.network_allowed,
            mem_limit="512m",
            cpu_quota=50000,  # 50% of one CPU
            read_only=True,
            security_opt=[f"seccomp={json.dumps(self.DEFAULT_SECCOMP_PROFILE)}"],
            environment=self.config.env,
        )

        self.container.start()

        # Attach to container stdio
        socket = self.container.attach_socket(
            params={"stdin": True, "stdout": True, "stderr": True, "stream": True}
        )

        # Wrap socket as asyncio streams
        return await self._wrap_socket_as_streams(socket)

    async def stop(self):
        """Stop and remove the container."""
        if self.container:
            self.container.stop(timeout=5)
            self.container.remove()
```

### Anti-Patterns to Avoid
- **Running untrusted servers without sandboxing:** User-added servers MUST run in Docker containers
- **Storing API keys in server config env:** Use Skynette's credential manager instead
- **Blocking on connection in UI thread:** Use background lazy connection
- **Auto-enabling all discovered tools:** Use allowlist approach, disabled by default
- **Ignoring tool name conflicts:** Prompt user to choose or rename on conflict

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JSON-RPC messaging | Manual JSON encoding | mcp SDK ClientSession | Protocol version, session lifecycle, error handling |
| stdio subprocess | subprocess.Popen | mcp SDK stdio_client | AsyncExitStack, stream management, cleanup |
| HTTP/SSE streaming | httpx + manual SSE parsing | mcp SDK streamablehttp_client | Protocol negotiation, reconnection, session IDs |
| Tool schema conversion | Manual dict mapping | mcp SDK response objects | Already typed, handles version differences |
| Container isolation | subprocess + chroot | Docker + seccomp | Battle-tested, cross-platform, resource limits |

**Key insight:** The MCP SDK handles all protocol details. Focus on integration with ToolRegistry and UI, not protocol implementation.

## Common Pitfalls

### Pitfall 1: Connection Lifecycle Mismanagement
**What goes wrong:** Connections leak, sessions not properly closed, zombie processes
**Why it happens:** AsyncExitStack not properly used, missing cleanup on errors
**How to avoid:**
- Use `AsyncExitStack.enter_async_context()` for all connections
- Implement proper `async with` context managers
- Handle disconnection events and cleanup
- Use background reconnection with exponential backoff (per 09-CONTEXT.md)
**Warning signs:** Growing process count, connection refused after restart

### Pitfall 2: Tool Name Conflicts
**What goes wrong:** Two servers expose `read_file` tool, one overwrites the other
**Why it happens:** No namespace prefixing, no conflict detection
**How to avoid:**
- Prefix tool names with server ID: `mcp_filesystem_read_file`
- Detect conflicts during discovery
- Per 09-CONTEXT.md: prompt user to pick primary or rename
- Store original name for MCP call, display name for UI
**Warning signs:** Tool behavior changes after adding new server

### Pitfall 3: Unbounded Trust
**What goes wrong:** User adds malicious MCP server, gains system access
**Why it happens:** All servers treated equally, no sandboxing
**How to avoid:**
- Per 09-CONTEXT.md: three trust tiers (builtin, verified, user-added)
- Sandbox user-added servers in Docker containers
- First-use approval for untrusted server tools
- Network restrictions for untrusted servers
**Warning signs:** Unauthorized file access, network connections to unknown hosts

### Pitfall 4: Blocking UI on Connection
**What goes wrong:** App freezes while connecting to slow/unreachable server
**Why it happens:** Connection happens synchronously on add
**How to avoid:**
- Per 09-CONTEXT.md: background lazy connection
- Show connecting indicator, don't block
- Validate connection on add (async), reject if fails
- Auto-reconnect with exponential backoff
**Warning signs:** UI unresponsive when adding servers

### Pitfall 5: Tool Discovery Spam
**What goes wrong:** Server with 100 tools floods the agent context
**Why it happens:** All tools auto-enabled, no filtering
**How to avoid:**
- Per 09-CONTEXT.md: allowlist approach, all disabled by default
- User explicitly enables tools they want
- Group by function for discoverability
- Limit tools per context (5-7 max per agent call)
**Warning signs:** Token budget exceeded, LLM confused by tool count

## Code Examples

Verified patterns from official sources:

### MCP Client Session Lifecycle
```python
# Source: Official MCP Python SDK documentation
import asyncio
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def connect_and_list_tools(command: str, args: list[str]) -> list[dict]:
    """Connect to MCP server and list available tools."""

    async with AsyncExitStack() as stack:
        # Create server parameters
        server_params = StdioServerParameters(
            command=command,
            args=args,
            env=None,
        )

        # Connect via stdio transport
        transport = await stack.enter_async_context(
            stdio_client(server_params)
        )
        read_stream, write_stream = transport

        # Create and initialize session
        session = await stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )
        await session.initialize()

        # List tools
        response = await session.list_tools()
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.inputSchema,
            }
            for tool in response.tools
        ]
```

### Streamable HTTP Client Connection
```python
# Source: Official MCP Python SDK + Cloudflare blog
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def connect_http_server(url: str, token: Optional[str] = None) -> ClientSession:
    """Connect to MCP server via Streamable HTTP."""

    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    async with AsyncExitStack() as stack:
        transport = await stack.enter_async_context(
            streamablehttp_client(url, headers=headers)
        )
        read_stream, write_stream, _ = transport

        session = await stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )
        await session.initialize()

        return session
```

### Tool Call with Result Handling
```python
# Source: Official MCP documentation + tools specification
async def call_mcp_tool(
    session: ClientSession,
    tool_name: str,
    arguments: dict,
) -> dict:
    """Call an MCP tool and handle the result."""

    result = await session.call_tool(tool_name, arguments)

    # Handle different result types
    if hasattr(result, 'isError') and result.isError:
        return {
            "success": False,
            "error": _extract_error_message(result.content),
        }

    # Extract content (can be text, structured, or mixed)
    content = []
    for item in result.content:
        if item.type == "text":
            content.append(item.text)
        elif item.type == "image":
            content.append({"image": item.data, "mimeType": item.mimeType})

    # Check for structured content (spec 2025-06-18+)
    structured = getattr(result, 'structuredContent', None)

    return {
        "success": True,
        "content": content,
        "structured": structured,
    }
```

### Server Configuration Storage (SQLite)
```python
# Source: Existing AIStorage pattern from src/ai/storage.py
import sqlite3
import json
from datetime import datetime, timezone

class MCPServerStorage:
    """Persist MCP server configurations."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_tables()

    def _init_tables(self):
        """Create MCP-related tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS mcp_servers (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    transport TEXT NOT NULL,
                    command TEXT,
                    args TEXT,
                    env TEXT,
                    url TEXT,
                    headers TEXT,
                    trust_level TEXT NOT NULL,
                    sandbox_enabled INTEGER DEFAULT 1,
                    category TEXT,
                    enabled INTEGER DEFAULT 1,
                    created_at TEXT,
                    last_connected TEXT,
                    last_error TEXT
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS mcp_tool_approvals (
                    id TEXT PRIMARY KEY,
                    server_id TEXT NOT NULL,
                    tool_name TEXT NOT NULL,
                    approved INTEGER DEFAULT 0,
                    approved_at TEXT,
                    FOREIGN KEY (server_id) REFERENCES mcp_servers(id)
                )
            """)

    async def save_server(self, config: MCPServerConfig) -> None:
        """Save server configuration."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO mcp_servers
                (id, name, description, transport, command, args, env, url, headers,
                 trust_level, sandbox_enabled, category, enabled, created_at,
                 last_connected, last_error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                config.id,
                config.name,
                config.description,
                config.transport.value,
                config.command,
                json.dumps(config.args),
                json.dumps(config.env),
                config.url,
                json.dumps(config.headers),
                config.trust_level.value,
                1 if config.sandbox_enabled else 0,
                config.category.value,
                1 if config.enabled else 0,
                config.created_at.isoformat(),
                config.last_connected.isoformat() if config.last_connected else None,
                config.last_error,
            ))
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| HTTP+SSE transport | Streamable HTTP | March 2025 (spec 2025-03-26) | Simpler, supports stateless |
| No authentication | OAuth Resource Server | June 2025 (spec 2025-06-18) | Secure remote servers |
| Unstructured output | Structured tool output | June 2025 (spec 2025-06-18) | Type-safe responses |
| No server registry | Community registries | Late 2025 | Easier discovery |

**Deprecated/outdated:**
- **SSE-only transport:** Replaced by Streamable HTTP as of spec 2025-03-26
- **JSON-RPC batching:** Removed in spec 2025-06-18
- **Unauthenticated remote servers:** OAuth now standard for production

## Curated MCP Servers (for MCP-06)

Recommended vetted servers to bundle/reference:

| Server | Category | Transport | Purpose | Trust Level |
|--------|----------|-----------|---------|-------------|
| @modelcontextprotocol/server-filesystem | File Tools | stdio | Secure file operations | VERIFIED |
| @anthropic/browser-mcp | Browser Tools | stdio | Playwright-based browser automation | VERIFIED |
| @modelcontextprotocol/server-git | Dev Tools | stdio | Git repository operations | VERIFIED |
| @modelcontextprotocol/server-memory | Productivity | stdio | Knowledge graph memory | VERIFIED |
| @modelcontextprotocol/server-fetch | Data Tools | stdio | Web content fetching | VERIFIED |

## Open Questions

Things that couldn't be fully resolved:

1. **Docker availability on all platforms**
   - What we know: Docker works on Windows/Mac/Linux but requires Docker Desktop
   - What's unclear: How to handle systems without Docker installed
   - Recommendation: Fallback to process-level isolation (less secure), warn user

2. **Seccomp profile completeness**
   - What we know: Default seccomp profile blocks dangerous syscalls
   - What's unclear: Which syscalls specific MCP servers need
   - Recommendation: Start restrictive, document how to expand for specific servers

3. **Tool approval persistence across sessions**
   - What we know: First-use approval per 09-CONTEXT.md
   - What's unclear: Scope of approval (per-server, per-tool, per-version?)
   - Recommendation: Approve per-tool, invalidate on server update

## Sources

### Primary (HIGH confidence)
- [MCP Specification 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25) - Protocol reference
- [MCP Python SDK GitHub](https://github.com/modelcontextprotocol/python-sdk) - Official implementation
- [MCP Build Client Guide](https://modelcontextprotocol.io/docs/develop/build-client) - Client patterns
- [MCP Tools Specification](https://modelcontextprotocol.io/specification/draft/server/tools) - Tool schema
- Existing codebase: `src/agent/registry/tool_registry.py`, `src/data/storage.py`, `src/ai/storage.py`

### Secondary (MEDIUM confidence)
- [Cloudflare: Streamable HTTP Transport](https://blog.cloudflare.com/streamable-http-mcp-servers-python/) - HTTP transport guide
- [Docker Seccomp Docs](https://docs.docker.com/engine/security/seccomp/) - Container security
- [Real Python: MCP Client](https://realpython.com/python-mcp-client/) - Tutorial
- [Awesome MCP Servers](https://github.com/wong2/awesome-mcp-servers) - Server catalog

### Tertiary (LOW confidence)
- [MCP Security Risks 2025](https://datasciencedojo.com/blog/mcp-security-risks-and-challenges/) - Security overview (for awareness)
- [OWASP MCP Guidelines](https://arxiv.org/html/2511.20920v1) - Security research paper

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Official SDK, well-documented, widely used
- Architecture: HIGH - Based on existing codebase patterns + official examples
- Pitfalls: HIGH - Documented in security research + industry reports
- Sandboxing: MEDIUM - Docker approach proven but seccomp profile needs tuning

**Research date:** 2026-01-21
**Valid until:** 30 days (MCP ecosystem evolving rapidly, SDK version may change)
