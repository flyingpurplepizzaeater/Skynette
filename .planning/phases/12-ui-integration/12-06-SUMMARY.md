---
phase: 12
plan: 06
subsystem: ui
tags: [ui, flet, task-history, replay, trace-store]

depends:
  requires: ["12-01", "08-01"]
  provides: ["task-history-view", "replay-capability"]
  affects: ["12-07"]

tech-stack:
  added: []
  patterns:
    - Session row with expandable details
    - Pagination with load more button
    - Relative time formatting for timestamps
    - Replay callback architecture

key-files:
  created:
    - src/agent/ui/task_history.py
    - tests/agent/ui/test_task_history.py
  modified:
    - src/agent/ui/__init__.py

decisions:
  - id: "12-06-01"
    decision: "50 character truncation for task descriptions"
    rationale: "Balances readability with space efficiency in list view"
  - id: "12-06-02"
    decision: "PAGE_SIZE of 20 sessions per load"
    rationale: "Reasonable batch size for performance and usability"
  - id: "12-06-03"
    decision: "Expandable rows for session details"
    rationale: "Keep list compact while allowing access to tokens, cost, duration"

metrics:
  duration: "4 minutes"
  completed: "2026-01-23"
---

# Phase 12 Plan 06: Task History View Summary

**One-liner:** TaskHistoryView component showing past agent executions with session details, replay buttons, and pagination from TraceStore.

## Completed Tasks

| # | Task | Commit | Key Files |
|---|------|--------|-----------|
| 1 | Create TaskHistoryView component | 10dcbd4 | `task_history.py` |
| 2 | Update exports and add tests | 412541a | `__init__.py`, `test_task_history.py` |

## Implementation Details

### TaskSessionRow Component

Row component for displaying individual TraceSession with:

**Visual Elements:**
- Status icon (play/check/error/cancel) with semantic colors
- Truncated task description (50 chars max)
- Relative timestamp ("Just now", "5m ago", "2d ago", etc.)
- Replay IconButton with PRIMARY color
- Expand/collapse chevron icon

**Status Mappings:**
```python
SESSION_STATUS_ICONS = {
    "running": ft.Icons.PLAY_CIRCLE,
    "completed": ft.Icons.CHECK_CIRCLE,
    "failed": ft.Icons.ERROR,
    "cancelled": ft.Icons.CANCEL,
}
SESSION_STATUS_COLORS = {
    "running": Theme.PRIMARY,
    "completed": Theme.SUCCESS,
    "failed": Theme.ERROR,
    "cancelled": Theme.WARNING,
}
```

**Expanded Details:**
- Duration (calculated from started_at/completed_at)
- Token count with comma formatting
- Cost in USD format
- Status badge with colored background

### TaskHistoryView Component

Column-based view extending ft.Column with:

**Layout:**
- Header with "Recent Tasks" title and refresh button
- ListView of TaskSessionRow items
- "Load more" TextButton for pagination
- Empty state with history icon and message

**Constructor Parameters:**
- `on_replay: Optional[Callable[[str], None]]` - Callback receiving task description
- `trace_store: Optional[TraceStore]` - Injected store (creates new if None)

**Methods:**
- `refresh()` - Reload sessions from offset 0
- `load_more()` - Append next page of sessions
- `sessions` property - Current sessions list

**Pagination:**
- PAGE_SIZE = 20 sessions per request
- Tracks `_has_more` based on returned count
- Increments `_offset` on load_more

### Helper Functions

**_format_relative_time(dt):**
- "Just now" for < 1 minute
- "Xm ago" for < 1 hour
- "Xh ago" for < 1 day
- "Xd ago" for < 1 week
- "Mon DD, YYYY" for older

**_format_duration(started_at, completed_at):**
- "Running..." if no end time
- "Xs" for < 1 minute
- "Xm Ys" for < 1 hour
- "Xh Ym" for longer

**_format_cost(cost):**
- "$0.00" for None/0
- "$X.XXXX" for < $0.01 (4 decimal places)
- "$X.XX" otherwise (2 decimal places)

### Package Exports

Added to `src/agent/ui/__init__.py`:
- TaskHistoryView
- TaskSessionRow

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed Flet TextButton API**
- **Found during:** Task 2 test execution
- **Issue:** `ft.TextButton(text="...")` is invalid; first positional arg is the text
- **Fix:** Changed `text="Load more"` to positional `"Load more"`
- **Files modified:** `task_history.py`
- **Commit:** 412541a

## Verification Results

All verification criteria passed:
- [x] TaskHistoryView shows list of past sessions
- [x] Status icon matches session status
- [x] Task description truncated appropriately (47 chars + "...")
- [x] Replay button visible and clickable
- [x] on_replay callback receives task description
- [x] Empty state handled gracefully
- [x] Pagination works for long history (tested with PAGE_SIZE items)

Test results:
- 17 tests pass in `test_task_history.py`
- TaskSessionRow renders all status types
- TaskHistoryView loads and paginates correctly
- Helper functions format time/duration/cost properly

## What's Next

**Next plan:** 12-07 (E2E Tests)
- Integration tests for full agent UI flow
- Test agent panel with real event streams

**Integration ready:**
- TaskHistoryView can be embedded in AgentPanel
- Replay callback enables re-running past tasks
- TraceStore integration provides persistent history
