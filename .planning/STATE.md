# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-01-20)

**Core value:** One app to replace separate AI chat clients, model managers, workflow tools, code editors, and AI assistants - accessible to everyone
**Current focus:** Phase 11 - Approval System (Phase 10 complete)

## Current Position

Phase: 11 of 14 (Safety and Approval Systems)
Plan: 2 of 6 in current phase
Status: In progress
Last activity: 2026-01-22 - Completed 11-02-PLAN.md (Kill Switch Mechanism)

Progress: [##################..] 90% (16/18 v3.0 plans)

## Milestone History

| Milestone | Shipped | Phases | Plans | Summary |
|-----------|---------|--------|-------|---------|
| v2.0 | 2026-01-19 | 6 | 25 | Code editor, multi-provider, RAG |

## Performance Metrics

**Velocity:**
- Total plans completed: 15 (v3.0)
- Average duration: ~7 minutes
- Total execution time: ~1.8 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 7 | 3 | ~37min | ~12min |
| 8 | 3 | ~29min | ~10min |
| 9 | 6 | ~34min | ~6min |
| 10 | 6 | ~30min | ~5min |

**Recent Trend:**
- Last 5 plans: 10-02, 10-04, 10-05, 10-06
- Trend: Consistent fast velocity (~5min)

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- v3.0: Build custom agent loop (not LangChain/LangGraph)
- v3.0: MCP for tool extensibility
- v3.0: Plan-and-Execute pattern for agent architecture
- 07-01: Use Literal type for AgentEventType instead of Enum (better JSON serialization)
- 07-02: Follow NodeRegistry pattern for ToolRegistry (consistency with codebase)
- 07-02: Separate AgentContext from AgentSession (lightweight tool-facing vs full session state)
- 07-03: Use tenacity for retry with exponential jitter backoff
- 07-03: Bounded event queues (100) to prevent slow subscribers blocking
- 07-03: Fallback single-step plan when AI planning fails
- 08-01: SQLite with WAL mode for trace storage (consistent with existing patterns)
- 08-01: 4KB max for raw I/O truncation (prevents bloat, preserves debug value)
- 08-01: 30 days default trace retention (balance utility vs storage)
- 08-02: AFTER_CURRENT as default cancel mode (safer - allows step to complete)
- 08-02: KEEP as default result mode (safer - preserves completed work)
- 08-03: Keyword-based task classification for MVP (ML-based is future enhancement)
- 08-03: Default to sonnet for most tasks (balance capability and cost)
- 09-01: Use Literal types for MCP enums (TrustLevel, TransportType, ServerCategory)
- 09-01: Fixed IDs for curated servers to enable key-based lookup
- 09-01: Default enabled=False for curated servers (allowlist approach)
- 09-02: Use official MCP SDK (mcp>=1.25.0) for client implementation
- 09-02: Exponential backoff reconnect: 1s base, 60s max, 5 attempts max
- 09-02: Tool caching in MCPConnection to avoid repeated list_tools calls
- 09-03: Namespaced tool names with 8-char server ID prefix
- 09-04: Network disabled by default for untrusted sandbox (security-first)
- 09-04: Graceful fallback when Docker unavailable (warning, continue without sandbox)
- 09-04: Image auto-selection based on server command (node, python, deno)
- 09-05: Content builder pattern (function returns Flet Column for settings integration)
- 09-05: Imported servers marked USER_ADDED with sandbox enabled by default
- 09-06: Mock MCP sessions for integration tests (external packages may be unavailable)
- 09-06: Graceful Windows SQLite cleanup with gc.collect() and PermissionError handling
- 10-01: Path validation with allowlist + blocked patterns using is_relative_to()
- 10-01: Timestamped backup format: {stem}.YYYYMMDD_HHMMSS.bak
- 10-02: Use ddgs package (renamed from duckduckgo-search) for DuckDuckGo API
- 10-02: Provider abstraction allows swapping search backends
- 10-02: 5-minute TTL cache for search results
- 10-03: Binary file detection via extension, base64 encoding for binary content
- 10-03: Best-effort backup on write (continue on failure), required backup on delete
- 10-04: Inline execution for short code (<1000 chars), temp file for longer
- 10-04: Use sys.executable for Python to ensure same interpreter as app
- 10-05: BrowserManager singleton for shared browser lifecycle
- 10-05: Session-based page tracking via module-level dict for multi-step operations
- 10-05: asyncio.to_thread for PyGithub async compatibility
- 10-06: RAGQueryTool returns graceful empty result when ChromaDB not initialized
- 10-06: Security tests use Windows-compatible paths (tempfile.gettempdir())
- 11-02: Ctrl+Shift+K for kill switch shortcut (Cmd+Shift+K on macOS)

### Pending Todos

- Manual verification of CodeEditorView (deferred from v2.0 03-04)

### Blockers/Concerns

- mypy not installed in dev environment

## Session Continuity

Last session: 2026-01-22
Stopped at: Completed 11-02-PLAN.md (Kill Switch Mechanism)
Resume file: None

## Next Steps

Phase 11 (Safety and Approval Systems) in progress:
- 11-01: Action Classification (RiskLevel, ActionClassification, ActionClassifier) - COMPLETE
- 11-02: Kill Switch Mechanism (KillSwitch with multiprocessing.Event) - COMPLETE
- 11-03: HITL Approval Flow
- 11-04: Audit Trail
- 11-05: UI Components
- 11-06: Integration Tests

Next: Run `/gsd:execute-plan 11-03` for HITL Approval Flow.
