# Phase 16: MCP Tool Registration - Context

**Gathered:** 2026-01-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Wire MCP server tools into ToolRegistry when servers connect/disconnect so the agent can invoke them. This closes the gap where MCP tools are discovered but not registered — the agent currently can't use them.

</domain>

<decisions>
## Implementation Decisions

### Registration timing
- Auto re-register tools when server reconnects (seamless restoration)
- Graceful unregister with timeout on disconnect (keep tools briefly for transient disconnects)

### Claude's Discretion (Timing)
- When exactly tools get registered (on connect vs lazy)
- Specific timeout duration for graceful unregister

### Naming conflicts
- Tool metadata always includes source server (agent sees which server provides tool)
- Per-tool toggle: users can disable specific tools from a server (not just all-or-nothing)

### Claude's Discretion (Naming)
- Prefix strategy for tool names (always prefix vs only on conflict)
- How to handle duplicate tool names from different servers

### Error handling
- Auto-retry tool calls after server reconnects (don't fail immediately on disconnect)
- Retry timeout matches graceful unregister window (consistent timeouts)
- Use existing exponential backoff retry logic for failed tool executions
- Show tool connection status in UI (connected/disconnected visible)

### Tool metadata
- Use MCP-provided categories/tags if server provides them

### Claude's Discretion (Metadata)
- Which metadata fields to preserve (full schema vs essentials)
- Visual indicator for MCP tools vs built-in (distinct badge or not)
- Content sanitization approach for descriptions

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches that fit existing patterns.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 16-mcp-tool-registration*
*Context gathered: 2026-01-26*
