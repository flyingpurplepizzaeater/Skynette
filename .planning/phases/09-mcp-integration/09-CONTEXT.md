# Phase 9: MCP Integration - Context

**Gathered:** 2026-01-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Agent can discover and use tools from external MCP servers. This includes connecting via stdio and HTTP/SSE transports, discovering tools from connected servers, making those tools available in the agent tool registry, and providing user management through settings UI. Untrusted servers run in sandboxed environment.

</domain>

<decisions>
## Implementation Decisions

### Server Configuration
- Both manual form AND import from file (mcp.json) — form for quick add, import for bulk/sharing
- Ship with curated list of vetted MCP servers (filesystem, browser, etc.) that user can enable
- Validate connection on add — test when user adds server, reject if fails
- Organize servers by category (browser tools, dev tools, etc.) not by transport type

### Connection Behavior
- Background lazy connection — start connecting after UI loads, don't block startup
- Subtle indicator on failure — show status icon but don't interrupt user
- Auto-reconnect with exponential backoff if server disconnects mid-session
- Detailed panel for health status — connection status, latency, last active in expandable view

### Tool Presentation
- Group tools by function (browser tools, file tools, etc.) regardless of source server
- Allowlist approach — all tools disabled by default, user explicitly enables what they want
- User chooses on naming conflicts — prompt user to pick primary or rename when same tool name from multiple servers
- Detailed source on tool usage — badge showing which server provided the tool, plus expandable info (server, version, etc.)

### Security Boundaries
- Three trust tiers: Built-in, verified third-party, user-added
- Sandboxing means both process isolation AND network restrictions for untrusted servers
- Shield icons for trust indicators — verified shield, warning shield, no shield
- First-use approval for untrusted server tools — approve once per tool, then remember

### Claude's Discretion
- Specific curated server list (which servers to include)
- Exact UI layout for server management settings
- Retry backoff timing and limits
- Technical implementation of process isolation and network sandboxing

</decisions>

<specifics>
## Specific Ideas

- Users want to see detailed health info (latency, status) but don't want to be interrupted by failures
- Tool organization should feel function-based, not implementation-based — users think in terms of "what can I do" not "where did this come from"
- Security should be visible but not intrusive — shield icons give quick recognition without being alarming

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 09-mcp-integration*
*Context gathered: 2026-01-21*
