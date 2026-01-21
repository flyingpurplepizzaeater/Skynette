---
phase: 09-mcp-integration
plan: 03
subsystem: agent-mcp
tags: [mcp, tools, adapter, registry]

dependency-graph:
  requires: ["09-01", "09-02"]
  provides: ["MCPToolAdapter", "ToolRegistry MCP integration"]
  affects: ["09-04", "09-05"]

tech-stack:
  added: []
  patterns: ["Adapter pattern for MCP-to-BaseTool bridging"]

key-files:
  created:
    - src/agent/mcp/adapter/__init__.py
    - src/agent/mcp/adapter/tool_adapter.py
  modified:
    - src/agent/registry/tool_registry.py

decisions:
  - id: "09-03-01"
    summary: "Namespaced tool names with 8-char server ID prefix"
    reason: "Prevent conflicts while keeping names reasonably short"

metrics:
  duration: "~2min"
  completed: "2026-01-21"
---

# Phase 09 Plan 03: Tool Discovery and Registry Integration Summary

**One-liner:** MCPToolAdapter bridges MCP tools to BaseTool API with namespaced names, source attribution, and trust-based approval requirements.

## What Was Built

### MCPToolAdapter (src/agent/mcp/adapter/tool_adapter.py)
Adapter class that wraps MCP tools as BaseTool instances:

```python
class MCPToolAdapter(BaseTool):
    def __init__(
        self,
        mcp_tool: dict,  # From MCP list_tools
        server_id: str,
        server_name: str,
        trust_level: TrustLevel,
    ):
        # Namespaced name: mcp_{server_id[:8]}_{original_name}
        self.name = f"mcp_{server_id[:8]}_{mcp_tool['name']}"
        # Source attribution in description
        self.description = f"[{server_name}] {mcp_tool.get('description')}"
```

Key features:
- **Namespacing:** `mcp_abc12345_read_file` prevents conflicts between servers
- **Source attribution:** `[Filesystem] Read contents of a file` for UI clarity
- **Trust-based approval:** `user_added` trust level triggers `requires_approval=True`
- **MCP metadata accessor:** `get_mcp_metadata()` returns server info for UI display
- **Async execution:** Routes through `MCPClientManager.call_tool()`

### ToolRegistry MCP Integration (src/agent/registry/tool_registry.py)
Extended the existing ToolRegistry with MCP support:

```python
# New instance variable
self._mcp_tools: dict[str, BaseTool] = {}

# New methods
register_mcp_tool(tool: MCPToolAdapter) -> None
unregister_mcp_tool(tool_name: str) -> None
register_mcp_tools_from_server(server_id, server_name, trust_level, tools) -> int
unregister_mcp_tools_from_server(server_id: str) -> int
get_mcp_tools() -> list[MCPToolAdapter]

# Updated methods
get_tool(name)      # Now checks _mcp_tools first
get_all_definitions()  # Includes MCP tools
tool_names          # Includes MCP tool names
```

## Verification Results

All success criteria verified:

| Criterion | Status | Evidence |
|-----------|--------|----------|
| MCPToolAdapter inherits BaseTool | PASS | Verified via import and instantiation |
| Namespaced names | PASS | `mcp_abc12345_read_file` format confirmed |
| Source attribution | PASS | `[ServerName] description` format confirmed |
| get_tool() returns MCP tools | PASS | Retrieved tool by namespaced name |
| get_all_definitions() includes MCP | PASS | MCP tools appear in definitions list |
| Per-server register/unregister | PASS | Bulk operations work correctly |
| USER_ADDED requires approval | PASS | `requires_approval=True` confirmed |

## Commits

| Hash | Type | Description |
|------|------|-------------|
| fb1dc07 | feat | add MCPToolAdapter to wrap MCP tools as BaseTool |
| 43e3ecd | feat | extend ToolRegistry for MCP tool integration |

## Deviations from Plan

None - plan executed exactly as written.

## Key Links Established

- `MCPToolAdapter` -> `BaseTool`: Inheritance for tool abstraction
- `MCPToolAdapter` -> `MCPClientManager`: Execution routing via `call_tool()`
- `ToolRegistry` -> `MCPToolAdapter`: Creates instances via `register_mcp_tools_from_server()`

## Next Phase Readiness

Ready for 09-04 (Server Lifecycle Management):
- MCPToolAdapter provides the adapter for wrapping discovered tools
- ToolRegistry provides registration/unregistration APIs
- Server lifecycle can now register tools on connect, unregister on disconnect

No blockers identified.
