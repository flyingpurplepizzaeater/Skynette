# Phase 16: MCP Tool Registration - Research

**Researched:** 2026-01-26
**Domain:** MCP tool lifecycle management, ToolRegistry integration, connection event handling
**Confidence:** HIGH

## Summary

This phase wires MCP server tools into the existing ToolRegistry when servers connect and removes them when servers disconnect. The key gap being closed: MCP tools are currently discovered via `MCPConnection.list_tools()` but never registered with `ToolRegistry`, so the agent cannot invoke them.

The existing codebase provides all necessary building blocks from Phase 9:
- `MCPClientManager` (Phase 09-02) manages connections with auto-reconnect
- `MCPToolAdapter` (Phase 09-03) wraps MCP tools as `BaseTool` instances
- `ToolRegistry` already has `register_mcp_tools_from_server()` and `unregister_mcp_tools_from_server()` methods

What's missing: **The wiring**. No code currently calls these registration methods when servers connect/disconnect. Phase 16 creates an `MCPToolBridge` that orchestrates tool registration lifecycle.

**Primary recommendation:** Create an `MCPToolBridge` class that coordinates between `MCPClientManager` and `ToolRegistry`. This bridge provides `connect_and_register()` and `disconnect_and_unregister()` methods that handle the full lifecycle. The bridge also implements graceful disconnect with a timeout window for transient disconnects, per 16-CONTEXT.md.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| mcp | >=1.25.0 | MCP SDK (already installed) | Official SDK, handles protocol |
| asyncio | stdlib | Async coordination, timers | Standard for async patterns |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| logging | stdlib | Debug/info logging | All connection events |
| typing | stdlib | Type hints | API clarity |

### Existing Codebase Components (Use These)
| Component | Location | Purpose |
|-----------|----------|---------|
| MCPClientManager | src/agent/mcp/client/manager.py | Connection management (Phase 09-02) |
| MCPConnection | src/agent/mcp/client/connection.py | Connection wrapper with tool caching |
| MCPToolAdapter | src/agent/mcp/adapter/tool_adapter.py | Wraps MCP tools as BaseTool (Phase 09-03) |
| ToolRegistry | src/agent/registry/tool_registry.py | Singleton tool registry |
| AgentEventEmitter | src/agent/events/emitter.py | Event broadcast pattern |
| MCPServerStorage | src/agent/mcp/storage/server_storage.py | Server config persistence |

## Architecture Patterns

### Recommended Project Structure
```
src/
  agent/
    mcp/
      bridge/                  # NEW: Phase 16 addition
        __init__.py
        tool_bridge.py         # MCPToolBridge coordinator
      client/
        manager.py             # Existing - add callback hooks
```

### Pattern 1: Tool Bridge Coordinator
**What:** Central coordinator between MCPClientManager and ToolRegistry
**When to use:** All MCP tool registration operations
**Why:** Separates concerns - manager handles connections, bridge handles tool registration

```python
# Source: Follows existing singleton patterns in codebase
class MCPToolBridge:
    """Coordinates MCP tool registration lifecycle."""

    _instance: Optional["MCPToolBridge"] = None

    def __new__(cls) -> "MCPToolBridge":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._manager = get_mcp_client_manager()
        self._registry = get_tool_registry()
        self._pending_unregister: dict[str, asyncio.Task] = {}

        # Graceful disconnect window
        self.GRACEFUL_UNREGISTER_TIMEOUT = 5.0  # seconds

    async def connect_and_register(self, config: MCPServerConfig) -> int:
        """
        Connect to server and register its tools.

        Returns number of tools registered.
        """
        # Cancel any pending unregister for this server
        if config.id in self._pending_unregister:
            self._pending_unregister[config.id].cancel()
            del self._pending_unregister[config.id]

        # Connect
        connection = await self._manager.connect(config)

        # List and register tools
        tools = await connection.list_tools()
        count = self._registry.register_mcp_tools_from_server(
            server_id=config.id,
            server_name=config.name,
            trust_level=config.trust_level,
            tools=tools,
        )

        logger.info(f"Registered {count} tools from {config.name}")
        return count

    async def disconnect_and_unregister(
        self,
        server_id: str,
        graceful: bool = True,
    ) -> None:
        """
        Disconnect from server and unregister its tools.

        If graceful=True, delays unregistration to allow for reconnection
        during transient disconnects.
        """
        if graceful:
            # Schedule delayed unregistration
            async def delayed_unregister():
                await asyncio.sleep(self.GRACEFUL_UNREGISTER_TIMEOUT)
                count = self._registry.unregister_mcp_tools_from_server(server_id)
                logger.info(f"Unregistered {count} tools after timeout")
                self._pending_unregister.pop(server_id, None)

            task = asyncio.create_task(delayed_unregister())
            self._pending_unregister[server_id] = task
        else:
            # Immediate unregistration
            count = self._registry.unregister_mcp_tools_from_server(server_id)
            logger.info(f"Unregistered {count} tools immediately")

        await self._manager.disconnect(server_id)
```

### Pattern 2: Connection Lifecycle Callbacks
**What:** Hook pattern to trigger registration on connect/disconnect
**When to use:** Wiring MCPClientManager events to MCPToolBridge

The MCP SDK doesn't provide explicit on_connect/on_disconnect callbacks. Instead, wrap the connect/disconnect calls at the bridge level. The bridge becomes the single entry point for connection operations.

```python
# Pattern: Bridge wraps all connection operations
# UI/app code calls bridge, not manager directly

# GOOD: Use bridge
await tool_bridge.connect_and_register(config)

# AVOID: Direct manager calls (tools won't register)
await manager.connect(config)  # Missing registration!
```

### Pattern 3: Graceful Disconnect with Timeout
**What:** Keep tools registered briefly after disconnect for transient failures
**When to use:** Unexpected disconnects, network hiccups
**Per 16-CONTEXT.md:** "Graceful unregister with timeout on disconnect"

```python
# Source: 16-CONTEXT.md decisions
# Timeout matches reconnect window for consistency

GRACEFUL_UNREGISTER_TIMEOUT = 5.0  # seconds

# On connection lost:
# 1. Don't unregister tools immediately
# 2. Start timeout timer
# 3. If reconnect succeeds before timeout, cancel unregister
# 4. If timeout expires, unregister tools

# This prevents tool flapping during transient disconnects
```

### Pattern 4: Startup Initialization
**What:** Connect to all enabled servers and register tools on app startup
**When to use:** Application initialization

```python
async def initialize_mcp_tools() -> None:
    """Initialize MCP connections and register tools on startup."""
    bridge = get_mcp_tool_bridge()
    storage = get_mcp_storage()

    # Get all enabled servers
    enabled_servers = storage.list_servers(enabled_only=True)

    # Connect and register in parallel
    tasks = [
        bridge.connect_and_register(config)
        for config in enabled_servers
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    for config, result in zip(enabled_servers, results):
        if isinstance(result, Exception):
            logger.error(f"Failed to initialize {config.name}: {result}")
        else:
            logger.info(f"Initialized {config.name} with {result} tools")
```

### Anti-Patterns to Avoid
- **Calling manager.connect() directly:** Tools won't be registered; always use bridge
- **Immediate unregistration on any disconnect:** Causes tool flapping; use graceful timeout
- **Registering tools without checking enabled status:** Respect user's per-server enable toggle
- **Blocking UI on connection:** Use async patterns, show connection status
- **Forgetting to cancel pending unregister on reconnect:** Tools would be lost after reconnect

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Tool wrapping | Manual dict conversion | MCPToolAdapter | Already handles namespacing, metadata |
| Tool registration | Manual dict management | ToolRegistry.register_mcp_tools_from_server() | Already implemented in Phase 09-03 |
| Connection management | New connection code | MCPClientManager | Already has reconnect, cleanup |
| Tool caching | Repeated list_tools calls | MCPConnection._tools_cache | Already caches per connection |

**Key insight:** Phase 9 built all the pieces. Phase 16 just wires them together.

## Common Pitfalls

### Pitfall 1: Direct Manager Access Bypasses Registration
**What goes wrong:** Code calls `manager.connect()` directly, tools discovered but never registered
**Why it happens:** Manager exists, easy to call directly
**How to avoid:**
- Make MCPToolBridge the sole entry point for connection operations
- Document that UI/app code should call bridge, not manager
- Consider making manager internal to bridge
**Warning signs:** Tools show as available in MCP status but agent can't call them

### Pitfall 2: Tool Flapping on Transient Disconnects
**What goes wrong:** Brief network hiccup causes tools to unregister then re-register
**Why it happens:** Immediate unregistration on any disconnect
**How to avoid:**
- Implement graceful unregister with timeout (5 seconds recommended)
- Cancel pending unregister if reconnect succeeds
- Match timeout to reconnect window
**Warning signs:** Agent errors "tool not found" during brief network issues

### Pitfall 3: Duplicate Tool Registration on Reconnect
**What goes wrong:** Tools registered twice after reconnect
**Why it happens:** Forgot to check if already registered, or pending unregister wasn't cancelled
**How to avoid:**
- ToolRegistry.register_mcp_tool() already checks for duplicates
- Cancel pending unregister task before re-registering
- Clear tool cache on reconnect (connection.invalidate_cache())
**Warning signs:** Logger shows "Tool already registered, skipping" warnings

### Pitfall 4: Missing Server Configuration on Reconnect
**What goes wrong:** Auto-reconnect succeeds but registration fails
**Why it happens:** Config not stored in manager._server_configs
**How to avoid:**
- Manager already stores configs in _server_configs for reconnect
- Always use bridge.connect_and_register() which passes full config
**Warning signs:** Reconnect logs success but tools not available

### Pitfall 5: Race Condition Between Register and Unregister
**What goes wrong:** Disconnect happens during registration, both tasks running
**Why it happens:** Async operations can interleave
**How to avoid:**
- Track pending operations per server
- Cancel conflicting operations before starting new one
- Use server_id as key for pending operation tracking
**Warning signs:** Inconsistent tool counts, tools appear then disappear

## Code Examples

Verified patterns from existing codebase:

### Existing Tool Registration (ToolRegistry)
```python
# Source: src/agent/registry/tool_registry.py lines 128-154
def register_mcp_tools_from_server(
    self,
    server_id: str,
    server_name: str,
    trust_level: "TrustLevel",
    tools: list[dict],
) -> int:
    """Register all tools from an MCP server."""
    from src.agent.mcp.adapter.tool_adapter import MCPToolAdapter

    count = 0
    for mcp_tool in tools:
        adapter = MCPToolAdapter(
            mcp_tool=mcp_tool,
            server_id=server_id,
            server_name=server_name,
            trust_level=trust_level,
        )
        self.register_mcp_tool(adapter)
        count += 1

    logger.info(f"Registered {count} MCP tools from {server_name}")
    return count
```

### Existing Tool Unregistration (ToolRegistry)
```python
# Source: src/agent/registry/tool_registry.py lines 156-170
def unregister_mcp_tools_from_server(self, server_id: str) -> int:
    """Unregister all tools from a specific MCP server."""
    prefix = f"mcp_{server_id[:8]}_"
    to_remove = [name for name in self._mcp_tools.keys() if name.startswith(prefix)]

    for name in to_remove:
        del self._mcp_tools[name]

    logger.info(f"Unregistered {len(to_remove)} MCP tools from server {server_id}")
    return len(to_remove)
```

### Existing Connection Management (MCPClientManager)
```python
# Source: src/agent/mcp/client/manager.py lines 66-99
async def connect(self, config: MCPServerConfig) -> MCPConnection:
    """Connect to an MCP server based on config."""
    if not self._initialized:
        await self.initialize()

    if config.id in self._connections:
        return self._connections[config.id]

    # Store config for potential reconnection
    self._server_configs[config.id] = config

    # ... transport-specific connection logic ...

    self._connections[config.id] = connection
    logger.info(f"Connected to MCP server: {config.name}")
    return connection
```

### Tool Listing from Connection
```python
# Source: src/agent/mcp/client/connection.py lines 45-65
async def list_tools(self) -> list[dict]:
    """List available tools from this server."""
    if self._tools_cache is None:
        response = await self.session.list_tools()
        self._tools_cache = [
            {
                "name": tool.name,
                "description": tool.description or "",
                "inputSchema": tool.inputSchema,
            }
            for tool in response.tools
        ]
    self.last_activity = datetime.now(UTC)
    return self._tools_cache
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual tool definition | MCP tool discovery | MCP spec (2024-11) | Auto-discovery from servers |
| Singleton tools | Dynamic registration | This phase | Tools appear/disappear with servers |
| Fail on disconnect | Graceful unregister | This phase | Resilient to transient failures |

**Current codebase state:**
- MCPClientManager: Full implementation with reconnect (Phase 09-02)
- MCPToolAdapter: Full implementation (Phase 09-03)
- ToolRegistry: MCP methods exist but never called

## Open Questions

Things that couldn't be fully resolved:

1. **Startup ordering with app initialization**
   - What we know: App.initialize() must call MCP initialization
   - What's unclear: Exact timing relative to other initialization
   - Recommendation: Add to app.py after initialize_default_providers()

2. **Per-tool disable toggle persistence**
   - What we know: 16-CONTEXT.md mentions per-tool toggle
   - What's unclear: Where to store disabled tools (server_storage or new table?)
   - Recommendation: Defer to separate task, focus on server-level for now

3. **Tool refresh when server updates**
   - What we know: Tools can change when server restarts
   - What's unclear: When to invalidate cache and re-register
   - Recommendation: Invalidate on reconnect, add manual refresh button later

## Sources

### Primary (HIGH confidence)
- Existing codebase: `src/agent/registry/tool_registry.py` (Phase 09-03 implementation)
- Existing codebase: `src/agent/mcp/client/manager.py` (Phase 09-02 implementation)
- Existing codebase: `src/agent/mcp/adapter/tool_adapter.py` (Phase 09-03 implementation)
- 16-CONTEXT.md decisions on timing, naming, error handling

### Secondary (MEDIUM confidence)
- [MCP Build Client Guide](https://modelcontextprotocol.io/docs/develop/build-client) - Client lifecycle patterns
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) - SDK capabilities

### Tertiary (LOW confidence)
- Web search: MCP SDK doesn't provide explicit on_connect/on_disconnect callbacks; lifecycle managed via context managers

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Uses existing codebase components, no new dependencies
- Architecture: HIGH - Bridge pattern follows existing singleton patterns
- Pitfalls: HIGH - Based on understanding existing code flow

**Research date:** 2026-01-26
**Valid until:** 30 days (stable domain, mostly internal wiring)
