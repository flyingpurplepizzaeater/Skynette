# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-01-20)

**Core value:** One app to replace separate AI chat clients, model managers, workflow tools, code editors, and AI assistants - accessible to everyone
**Current focus:** v3.0 Gap closure (Phases 15-16)

## Current Position

Phase: 15 of 16 (Approval Flow Wiring)
Plan: 1 of 1 in current phase - PHASE COMPLETE
Status: Gap closure in progress
Last activity: 2026-01-26 - Completed 15-01-PLAN.md (Approval Flow Wiring)

Progress: [###################-] 90% (9/10 phases for v3.0)

## Milestone History

| Milestone | Shipped | Phases | Plans | Summary |
|-----------|---------|--------|-------|---------|
| v2.0 | 2026-01-19 | 6 | 25 | Code editor, multi-provider, RAG |

## Performance Metrics

**Velocity:**
- Total plans completed: 35 (v3.0)
- Average duration: ~5 minutes
- Total execution time: ~3.5 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 7 | 3 | ~37min | ~12min |
| 8 | 3 | ~29min | ~10min |
| 9 | 6 | ~34min | ~6min |
| 10 | 6 | ~30min | ~5min |
| 11 | 7 | ~32min | ~5min |
| 12 | 7 | ~24min | ~3min |
| 13 | 7 | ~28min | ~4min |
| 14 | 6 | ~18min | ~3min |
| 15 | 1 | ~3min | ~3min |

**Recent Trend:**
- Last 5 plans: 14-04, 14-05, 14-06, 15-01
- Trend: Stable velocity (~3min)

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
- 11-03: asyncio.Event for blocking approval requests
- 11-03: Parent directory for file operation similarity matching
- 11-03: 60s default timeout for approval requests
- 11-04: SQLite with WAL mode for audit storage (consistent with TraceStore)
- 11-04: 4KB max for parameter/result truncation in audit entries
- 11-04: 30-day default retention for audit trail
- 11-05: Container with colored dot + label for risk badge (simple, clear visualization)
- 11-05: Non-dismissible BottomSheet for approval (requires explicit decision)
- 11-06: Kill switch checked at start of loop and after each step (step boundaries)
- 11-06: Approval timeout results in skipped action, not auto-reject
- 11-06: Run method wrapped with try/finally for safety cleanup
- 11-07: Structure E2E tests into 4 test classes by component (Classification, Approval, KillSwitch, Audit)
- 11-07: Use asyncio.create_task for approval blocking tests
- 11-07: Windows-compatible cleanup with gc.collect() and PermissionError handling (per 09-06)
- 12-01: Panel width bounds MIN=280, MAX=600, DEFAULT=350
- 12-01: Invert delta_x for right sidebar resize (moving left = wider)
- 12-01: Badge count capped at 99 for pending event indicator
- 12-02: STATUS_ICONS and STATUS_COLORS maps for consistent step styling
- 12-02: AnimatedSwitcher with FADE transition for smooth view mode changes
- 12-02: Expandable detail sections in checklist and cards views
- 12-04: Three detail levels (minimal, detailed, progressive) for approval content
- 12-04: Parameter editing with JSON validation before approval
- 12-04: Remember choice with session/type scope options
- 12-03: _safe_update helper with try/except for RuntimeError (Flet page attachment)
- 12-03: ft.Alignment(0, 0) instead of deprecated ft.alignment.center
- 12-05: on_select instead of on_change for Dropdown in Flet 0.80
- 12-05: Fixed 300px height for audit trail in ExpansionPanel
- 12-06: 50 character truncation for task descriptions in history view
- 12-06: PAGE_SIZE of 20 sessions per load for pagination
- 12-06: Expandable rows for session details (tokens, cost, duration)
- 12-07: Lazy panel initialization (created on first toggle, not app start)
- 12-07: E2E tests use mock executor with real AgentEventEmitter
- 12-07: Performance benchmarks: <100ms panel, <200ms 100-steps, <500ms 50-events
- 13-01: L2 (Collaborator) as default autonomy level
- 13-01: Autonomy colors harmonize with existing RISK_COLORS (blue/emerald/amber/red)
- 13-01: _is_downgrade() helper for detecting restrictive level changes
- 13-02: L2 (Collaborator) as default autonomy level for new projects
- 13-02: Path normalization via Path.resolve() for consistent DB keys
- 13-02: Nullable allowlist/blocklist columns (rules added in Plan 04)
- 13-03: Lazy import of get_autonomy_service in classify() to avoid circular import
- 13-03: Remove static APPROVAL_REQUIRED dict - approval is entirely level-based
- 13-03: Callbacks notified only on downgrade (more restrictive level change)
- 13-04: Blocklist rules always take priority over allowlist (security-first)
- 13-04: fnmatch for glob patterns (stdlib, familiar syntax)
- 13-04: Path rules can optionally restrict to specific tools
- 13-04: Dict input supported for JSON serialization compatibility
- 13-05: PopupMenuButton for autonomy level dropdown selection
- 13-05: Badge placement before view mode dropdown in panel header
- 13-05: Immediate callback (no confirmation) per "no friction on escalation"
- 13-06: auto_executed = non-safe risk that doesn't require approval at current level
- 13-06: Downgrade callback sets flag; classify() called fresh each step for re-evaluation
- 13-06: Fixed callback type annotation to include downgrade boolean parameter
- 13-07: Test structure mirrors source structure (tests/agent/safety/ for src/agent/safety/)
- 13-07: Fresh service instances per test to avoid global state pollution
- 14-01: Purple (#8B5CF6) for L5 color - power mode aesthetic, not warning
- 14-01: Session-only YOLO via _session_yolo_projects set in AutonomyLevelService
- 14-01: Sandbox detection errs toward 'sandboxed' (false positives better than false negatives)
- 14-02: Follow CancelDialog pattern for YoloConfirmationDialog consistency
- 14-02: Warning container only shows when not sandboxed
- 14-02: Don't warn again button requires callback to appear
- 14-03: L5 bypass happens BEFORE rule checks - L5 means no restrictions
- 14-03: L5 stored only in _session_yolo_projects set, never persisted to SQLite
- 14-03: Downgrade from L5 persists new level to storage
- 14-04: YOLO_RETENTION_DAYS = 90 (3x standard retention for post-incident analysis)
- 14-04: full_parameters stored only for YOLO entries (non-YOLO still truncate at 4KB)
- 14-04: _safe_json_loads returns {'_truncated': value} for broken JSON from truncation
- 14-05: Skip dialog if sandboxed or user opted out (instant L5 activation)
- 14-05: yolo_dont_warn_sandbox setting for "don't warn again" preference
- 14-05: YOLO_COLOR constant defined in agent_panel.py for purple border styling
- 14-06: Mock service class pattern for ActionClassifier testing
- 14-06: Temp file cleanup with gc.collect() for Windows
- 15-01: Timeout decision treated as rejection (user didn't approve)
- 15-01: Warning log for unknown decisions (fail gracefully with visibility)

### Pending Todos

- Manual verification of CodeEditorView (deferred from v2.0 03-04)

### Blockers/Concerns

- mypy not installed in dev environment

## Session Continuity

Last session: 2026-01-26
Stopped at: Completed 15-01-PLAN.md (Approval Flow Wiring) - Phase 15 COMPLETE
Resume file: None

## Next Steps

Gap Closure Phases (from audit):
- Phase 15: Approval Flow Wiring - COMPLETE (closes SAFE-02)
- Phase 16: MCP Tool Registration - PENDING (closes MCP-04)

Next: /gsd:plan-phase 16 (plan MCP tool registration fix)
