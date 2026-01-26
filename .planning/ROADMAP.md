# Roadmap: Skynette v3.0 Agent

## Milestones

- v2.0 Code Editor - Phases 1-6 (shipped 2026-01-19)
- **v3.0 Agent** - Phases 7-14 (in progress)

## Overview

Skynette v3.0 transforms the AI workspace into a general-purpose autonomous assistant. The roadmap progresses from foundational agent infrastructure through MCP-based tool extensibility, safety systems, and configurable autonomy levels. Each phase delivers a coherent, verifiable capability that builds toward the goal: an agent that can build apps, browse the web, interact with external services, and execute multi-step tasks with appropriate human oversight.

## Phases

**Phase Numbering:**
- Phases 1-6: v2.0 (shipped)
- Phases 7-14: v3.0 Agent (current milestone)
- Decimal phases (e.g., 7.1): Urgent insertions (marked with INSERTED)

- [x] **Phase 7: Agent Core Infrastructure** - Data models, event system, state management, tool registry
- [x] **Phase 8: Planning and Execution** - Planner, executor, orchestrator, model routing
- [x] **Phase 9: MCP Integration** - MCP host, transports, tool discovery, server management
- [x] **Phase 10: Built-in Tools** - Web search, browser, filesystem, GitHub, code execution
- [x] **Phase 11: Safety and Approval Systems** - Classification, HITL approval, audit, kill switch
- [x] **Phase 12: UI Integration** - Agent panel, progress display, approvals, plan visualization
- [x] **Phase 13: Autonomy Levels** - L1-L4 implementation with graduated trust
- [x] **Phase 14: YOLO Mode** - L5 full autonomy with enhanced monitoring

## Phase Details

### Phase 7: Agent Core Infrastructure
**Goal**: Establish the foundational data structures and systems that all agent capabilities build upon
**Depends on**: v2.0 (existing multi-provider gateway, workflow engine)
**Requirements**: AGNT-01, AGNT-02, AGNT-04, AGNT-05, AI-03
**Success Criteria** (what must be TRUE):
  1. Agent can decompose a simple task into a visible step-by-step plan
  2. Agent can invoke a mock tool and receive its result
  3. Agent maintains conversation context within a task session
  4. Agent retries a failed tool call with exponential backoff
  5. Agent respects configured token budget limits
**Plans**: 3 plans in 2 waves

Plans:
- [x] 07-01-PLAN.md — Agent data models (state, plan, events)
- [x] 07-02-PLAN.md — Tool infrastructure (registry, base class, mock tool)
- [x] 07-03-PLAN.md — Agent runtime (budget, events, planner, executor)

### Phase 8: Planning and Execution
**Goal**: Agent can plan, execute, and report on multi-step tasks with model flexibility
**Depends on**: Phase 7
**Requirements**: AGNT-03, AGNT-06, AGNT-07, AI-01, AI-02, QUAL-01
**Success Criteria** (what must be TRUE):
  1. User sees real-time status updates as agent executes (thinking, step N of M)
  2. User can cancel running agent task and execution stops cleanly
  3. Agent traces are viewable for debugging (what happened, in what order)
  4. Agent suggests appropriate model for different task types
  5. Unit tests pass for all agent core components
**Plans**: 3 plans in 2 waves

Plans:
- [x] 08-01-PLAN.md — Trace storage and enhanced events (observability foundation)
- [x] 08-02-PLAN.md — Cancellation controls and status display (user visibility)
- [x] 08-03-PLAN.md — Model routing and unit tests (intelligence and quality)

### Phase 9: MCP Integration
**Goal**: Agent can discover and use tools from external MCP servers
**Depends on**: Phase 7
**Requirements**: MCP-01, MCP-02, MCP-03, MCP-04, MCP-05, MCP-06, MCP-07, QUAL-02
**Success Criteria** (what must be TRUE):
  1. Skynette connects to a local MCP server via stdio transport
  2. Skynette connects to a remote MCP server via HTTP/SSE transport
  3. Tools from connected MCP servers appear in agent tool registry
  4. User can add/remove MCP servers through settings UI
  5. Untrusted MCP servers run in sandboxed environment
**Plans**: 6 plans in 5 waves

Plans:
- [x] 09-01-PLAN.md — MCP models, storage, and curated server definitions
- [x] 09-02-PLAN.md — MCP client manager with stdio and HTTP transports
- [x] 09-03-PLAN.md — Tool adapter and registry integration
- [x] 09-04-PLAN.md — Docker sandbox for untrusted servers
- [x] 09-05-PLAN.md — Server management UI (settings view and dialogs)
- [x] 09-06-PLAN.md — Unit and integration tests

### Phase 10: Built-in Tools
**Goal**: Agent has concrete capabilities for web search, browsing, code, and GitHub
**Depends on**: Phase 7, Phase 9 (tool registry)
**Requirements**: TOOL-01, TOOL-02, TOOL-03, TOOL-04, TOOL-05, TOOL-06, QUAL-03
**Success Criteria** (what must be TRUE):
  1. Agent can search the web and return relevant results
  2. Agent can navigate a website, fill forms, and extract data
  3. Agent can read, write, create, and delete files in allowed directories
  4. Agent can execute code snippets and return output
  5. Agent can create GitHub repository and push code
**Plans**: 6 plans in 4 waves

Plans:
- [x] 10-01-PLAN.md — Foundation utilities (path validation, backup) and dependencies
- [x] 10-02-PLAN.md — Web search tool with DuckDuckGo and scraper fallback
- [x] 10-03-PLAN.md — Filesystem tools (read, write, delete, list) with security
- [x] 10-04-PLAN.md — Code execution tool with multi-language support
- [x] 10-05-PLAN.md — Browser automation (Playwright) and GitHub integration
- [x] 10-06-PLAN.md — Skynette system tools (RAG) and security tests (QUAL-03)

### Phase 11: Safety and Approval Systems
**Goal**: User has control over what agent can do with appropriate oversight
**Depends on**: Phase 8, Phase 10 (actions to approve)
**Requirements**: SAFE-01, SAFE-02, SAFE-03, SAFE-04, SAFE-05, SAFE-06, QUAL-04
**Success Criteria** (what must be TRUE):
  1. Actions are classified as safe/moderate/destructive/critical with visible indicator
  2. Flagged actions prompt user approval before execution
  3. All agent actions are logged in queryable audit trail
  4. Kill switch stops agent immediately from outside agent process
  5. Similar low-risk actions can be batched for single approval
**Plans**: 7 plans in 5 waves

Plans:
- [x] 11-01-PLAN.md — Classification models and ActionClassifier (risk levels, rules)
- [x] 11-02-PLAN.md — Kill switch with multiprocessing.Event (emergency stop)
- [x] 11-03-PLAN.md — Approval models and ApprovalManager (HITL flow)
- [x] 11-04-PLAN.md — Audit store with SQLite persistence (logging, query, export)
- [x] 11-05-PLAN.md — Approval UI components (RiskBadge, ApprovalSheet)
- [x] 11-06-PLAN.md — Executor integration (wire safety into execution loop)
- [x] 11-07-PLAN.md — E2E tests for safety systems (QUAL-04)

### Phase 12: UI Integration
**Goal**: Agent capabilities are accessible through intuitive UI with full visibility
**Depends on**: Phase 8, Phase 11 (events and approvals)
**Requirements**: UI-01, UI-02, UI-03, UI-04, UI-05, UI-06, QUAL-05
**Success Criteria** (what must be TRUE):
  1. User can start agent task and view status in dedicated panel
  2. Progress display shows thinking indicator and step completion
  3. Approval dialogs allow accept, reject, or modify actions
  4. User sees visual plan before execution begins
  5. Step-by-step audit trail is visible and scrollable in UI
**Plans**: 7 plans in 4 waves

Plans:
- [x] 12-01-PLAN.md — AgentPanel core (resizable sidebar, event subscription, preferences)
- [x] 12-02-PLAN.md — Step views (checklist, timeline, cards with animated switching)
- [x] 12-03-PLAN.md — Plan views (list, tree with dependency visualization)
- [x] 12-04-PLAN.md — Enhanced ApprovalSheet (editing, detail levels, batch approval)
- [x] 12-05-PLAN.md — Audit trail view (scrollable, filterable, real-time updates)
- [x] 12-06-PLAN.md — Task history with replay capability
- [x] 12-07-PLAN.md — Main app integration and E2E tests (QUAL-05)

### Phase 13: Autonomy Levels
**Goal**: Users can configure how much oversight agent requires (L1-L4)
**Depends on**: Phase 11 (approval system)
**Requirements**: AUTO-01, AUTO-02, AUTO-03, AUTO-04
**Success Criteria** (what must be TRUE):
  1. L1 (Assistant): Agent suggests actions, user must execute each one
  2. L2 (Collaborator): Safe actions auto-execute, risky actions require approval
  3. L3 (Trusted): Moderate actions auto-execute, destructive require approval
  4. L4 (Expert): Most actions auto-execute, only critical require approval
  5. User can switch autonomy level per-project in settings
**Plans**: 7 plans in 4 waves

Plans:
- [x] 13-01-PLAN.md — Autonomy models and service (AutonomyLevel, thresholds, service)
- [x] 13-02-PLAN.md — Storage schema (project_autonomy table, persistence)
- [x] 13-03-PLAN.md — Autonomy-aware classification (dynamic approval based on level)
- [x] 13-04-PLAN.md — Allowlist/blocklist rules (pattern-based overrides)
- [x] 13-05-PLAN.md — UI components (AutonomyBadge, quick toggle in panel)
- [x] 13-06-PLAN.md — Executor integration (project_path, mid-task changes)
- [x] 13-07-PLAN.md — Unit tests (comprehensive coverage)

### Phase 14: YOLO Mode
**Goal**: Power users can run agent fully autonomously with monitoring
**Depends on**: Phase 11, Phase 13 (safety infrastructure proven)
**Requirements**: AUTO-05, SAFE-07
**Success Criteria** (what must be TRUE):
  1. L5 (Observer/YOLO) mode allows fully autonomous execution
  2. YOLO mode skips approval prompts but maintains full audit logging
  3. Clear UI indicator shows when YOLO mode is active
  4. YOLO mode only available in isolated/sandboxed environments
**Plans**: 6 plans in 4 waves

Plans:
- [x] 14-01-PLAN.md — L5 types, constants, and SandboxDetector utility
- [x] 14-02-PLAN.md — YoloConfirmationDialog component
- [x] 14-03-PLAN.md — Classification L5 bypass and session-only behavior
- [x] 14-04-PLAN.md — Enhanced audit logging for YOLO mode
- [x] 14-05-PLAN.md — UI components (badge, toggle, panel) L5 styling
- [x] 14-06-PLAN.md — E2E integration tests

## Progress

**Execution Order:**
Phases execute in numeric order: 7 -> 8 -> 9 -> 10 -> 11 -> 12 -> 13 -> 14
(Note: Phases 8 and 9 can potentially run in parallel as they share Phase 7 dependency)

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 7. Agent Core Infrastructure | v3.0 | 3/3 | Complete | 2026-01-20 |
| 8. Planning and Execution | v3.0 | 3/3 | Complete | 2026-01-21 |
| 9. MCP Integration | v3.0 | 6/6 | Complete | 2026-01-21 |
| 10. Built-in Tools | v3.0 | 6/6 | Complete | 2026-01-22 |
| 11. Safety and Approval | v3.0 | 7/7 | Complete | 2026-01-22 |
| 12. UI Integration | v3.0 | 7/7 | Complete | 2026-01-23 |
| 13. Autonomy Levels | v3.0 | 7/7 | Complete | 2026-01-26 |
| 14. YOLO Mode | v3.0 | 6/6 | Complete | 2026-01-26 |

---
*Roadmap created: 2026-01-20*
*Last updated: 2026-01-26 (Phase 14 complete - v3.0 milestone complete)*
