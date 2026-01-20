---
phase: 08-planning-and-execution
plan: 01
subsystem: agent-observability
tags: [tracing, sqlite, pydantic, debugging]
depends_on:
  requires: [07-01, 07-02, 07-03]
  provides: [trace-models, trace-store, trace-viewer, enhanced-events]
  affects: [08-02, 08-03, 08-04]
tech_stack:
  added: []
  patterns: [sqlite-storage, trace-persistence, event-conversion]
key_files:
  created:
    - src/agent/observability/__init__.py
    - src/agent/observability/trace_models.py
    - src/agent/observability/trace_store.py
    - src/agent/observability/trace_viewer.py
  modified:
    - src/agent/models/event.py
    - src/agent/__init__.py
decisions:
  - key: trace-storage
    choice: SQLite with WAL mode
    reason: Consistent with existing storage patterns, no external dependencies
  - key: raw-io-truncation
    choice: 4KB max for raw_input/raw_output
    reason: Prevents database bloat while preserving debug value
  - key: retention-default
    choice: 30 days default retention
    reason: Balance between debug utility and storage management
metrics:
  duration: ~12 minutes
  completed: 2026-01-20
---

# Phase 08 Plan 01: Agent Execution Tracing Summary

SQLite-persisted trace infrastructure enabling debugging and audit of agent execution with configurable retention

## What Was Built

### 1. Trace Models (TraceEntry, TraceSession)
- **TraceEntry**: Captures individual events with trace_id, parent_trace_id, duration_ms, token counts, costs, and raw I/O
- **TraceSession**: Groups related events with aggregate metrics (total_events, total_tokens, total_cost_usd)
- **from_agent_event()**: Factory method for converting AgentEvent to TraceEntry

### 2. TraceStore (SQLite Persistence)
- SQLite database at ~/.skynette/agent_traces.db with WAL mode
- Tables: agent_trace_sessions, agent_traces, trace_settings
- Indexes on session_id, timestamp, type for efficient queries
- Session management: start_session(), end_session(), get_session(), get_sessions()
- Trace persistence: save_trace() with automatic raw I/O truncation
- Query: get_traces() with filters (session, type, time range, text search)
- Cleanup: cleanup_old_traces() with configurable retention

### 3. TraceViewer (Debug Interface)
- list_sessions(): Recent sessions with summary stats
- get_session_timeline(): Chronological event list
- get_session_summary(): Aggregate metrics (duration, tokens, cost, errors)
- search_traces(): Full-text search across trace data
- get_trace_detail(): Full trace with raw I/O
- format_timeline(): Human-readable timeline string
- format_tree(): Indented parent-child hierarchy
- Filtering: filter_by_type(), filter_errors(), filter_by_duration()

### 4. Enhanced AgentEvent
- New trace fields: trace_id, parent_trace_id, duration_ms
- Token tracking: input_tokens, output_tokens, model_used, provider_used
- Cost tracking: estimated_cost_usd
- Debug fields: raw_input, raw_output
- New event types: model_selected, model_switched, trace_started, trace_ended
- Factory methods: model_selected(), model_switched()

## Commits

| Commit | Type | Description |
|--------|------|-------------|
| 6a5455c | feat | Create trace models for agent observability |
| a19bf78 | feat | Add TraceStore with SQLite persistence |
| f1cd327 | feat | Add TraceViewer for debugging traces |
| f91cfda | feat | Enhance AgentEvent with trace context fields |

## Decisions Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Storage backend | SQLite with WAL | Consistent with src/data/storage.py patterns, no external deps |
| Raw I/O handling | Truncate to 4KB | Prevents storage bloat while preserving debug value |
| Default retention | 30 days | Balance between utility and storage management |
| Session aggregates | Calculated on query | Avoids sync issues vs. stored values |

## Deviations from Plan

None - plan executed exactly as written.

## Key Patterns

### Event-to-Trace Conversion
```python
from src.agent.models.event import AgentEvent
from src.agent.observability import TraceEntry

event = AgentEvent(type='tool_called', data={'tool': 'search'}, session_id='sess-1')
trace = TraceEntry.from_agent_event(event)
```

### Trace Querying
```python
from src.agent.observability import TraceStore, TraceViewer

store = TraceStore()
viewer = TraceViewer(store)

# List recent sessions
sessions = viewer.list_sessions(limit=20)

# Get timeline for specific session
timeline = viewer.get_session_timeline(session_id='abc-123')

# Search across traces
results = viewer.search_traces('error', session_id='abc-123')
```

## Success Criteria Met

- [x] TraceEntry and TraceSession models defined with all required fields
- [x] TraceStore creates SQLite database with proper schema and indexes
- [x] Sessions can be started, ended, and queried
- [x] Trace entries can be saved and queried with filters
- [x] Retention cleanup deletes traces older than configured days
- [x] TraceViewer can list sessions, show timelines, and format output
- [x] TraceViewer supports search and filtering for debugging
- [x] AgentEvent has trace_id, duration_ms, token counts, and cost fields
- [x] New event types (model_selected, model_switched) are available
- [x] All components exportable from src.agent package

## Next Phase Readiness

**Ready for:**
- 08-02 (Status Display): Can emit events with full trace context
- 08-03 (Cancellation Control): Trace events capture cancellation flow
- 08-04 (Model Routing): model_selected/model_switched events ready

**Dependencies satisfied:**
- AGNT-03 (observability/tracing): Trace storage and query complete
- Success Criteria #3: Traces are viewable via TraceViewer
