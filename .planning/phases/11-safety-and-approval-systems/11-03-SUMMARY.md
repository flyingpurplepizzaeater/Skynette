---
phase: 11-safety-and-approval-systems
plan: 03
subsystem: agent-safety
tags: [approval-flow, hitl, async, similarity-matching]
dependency-graph:
  requires: [11-01]
  provides: [approval-flow, approval-manager, similarity-cache]
  affects: [11-05, 11-06]
tech-stack:
  added: []
  patterns: [asyncio-event, singleton-factory, session-scoped-cache]
key-files:
  created:
    - src/agent/safety/approval.py
  modified:
    - src/agent/safety/__init__.py
    - src/agent/__init__.py
decisions:
  - id: 11-03-01
    choice: "asyncio.Event for blocking approval requests"
    rationale: "Standard async pattern for waiting on external input"
  - id: 11-03-02
    choice: "Parent directory for file operation similarity"
    rationale: "Matches context requirement - /src writes also cover /src/components"
  - id: 11-03-03
    choice: "60s default timeout per CONTEXT.md"
    rationale: "Balances responsiveness with user think time"
metrics:
  duration: ~4min
  completed: 2026-01-22
---

# Phase 11 Plan 03: HITL Approval Flow Summary

**One-liner:** Async approval flow with similarity caching for "Approve All Similar" feature

## What Was Built

### ApprovalRequest and ApprovalResult (Task 1)

Created dataclass models for approval flow:

```python
@dataclass
class ApprovalRequest:
    id: str
    classification: ActionClassification
    step_id: str
    session_id: str
    _approved: asyncio.Event  # Internal blocking mechanism
    result: Optional[ApprovalResult]

    async def wait_for_decision(self, timeout: Optional[float]) -> ApprovalResult
    def set_result(self, result: ApprovalResult)
```

- `wait_for_decision()` blocks until user approves/rejects or timeout
- `set_result()` unblocks waiters via asyncio.Event
- Timeout returns `ApprovalResult(decision="timeout")`

### ApprovalManager with Similarity Matching (Task 2)

Manager handles pending requests and similarity cache:

```python
class ApprovalManager:
    def start_session(session_id: str)  # Clear caches, start fresh
    def end_session()                   # Clear all state
    async def request_approval(classification, step_id, timeout) -> ApprovalResult
    def approve(request_id, approve_similar=False)
    def reject(request_id)
    def get_pending() -> list[ApprovalRequest]
    @staticmethod
    def are_similar(a1, a2) -> bool
```

Similarity matching logic:
- File operations: Same parent directory = similar
- Subdirectories included: `/src` approval covers `/src/components`
- Other tools: Same tool name = similar

### Exports and Singleton (Task 3)

- `get_approval_manager()` returns global singleton
- All types exported from `src.agent` package
- Full integration with existing safety module

## Key Implementation Details

### Similarity Cache

When user clicks "Approve All Similar":
1. Cache key = (tool_name, parent_directory)
2. Future requests with same cache key auto-approve
3. Cache scoped to session (clears on end_session)

### Async Flow

```
Agent requests approval
    -> Check similarity cache
        -> Hit: Return auto-approved result
        -> Miss: Create ApprovalRequest, add to pending
            -> Wait on asyncio.Event
                -> UI calls approve()/reject()
                    -> set_result() triggers Event
                    -> wait_for_decision() returns
```

## Decisions Made

| ID | Decision | Rationale |
|----|----------|-----------|
| 11-03-01 | asyncio.Event for blocking | Standard async pattern, integrates with event loop |
| 11-03-02 | Parent directory for file similarity | Per CONTEXT.md - /src covers /src/components |
| 11-03-03 | 60s default timeout | Per CONTEXT.md - balance responsiveness/think time |

## Deviations from Plan

None - plan executed exactly as written.

## Verification Results

Full async test passed:
- ApprovalRequest blocks until approved
- Similarity cache auto-approves same directory
- decided_by="similar_match" for cached approvals
- Singleton returns same instance

## Commits

| Hash | Type | Description |
|------|------|-------------|
| a06d203 | feat | Create approval data models |
| 36e0dca | feat | Add ApprovalManager with similarity matching |
| da0774e | feat | Export approval types with global manager factory |

## Next Phase Readiness

Ready for:
- 11-04: Audit Trail (will record approval decisions)
- 11-05: UI Components (ApprovalBottomSheet)
- 11-06: Integration Tests (approval flow tests)

No blockers identified.

---

*Plan: 11-03 | Duration: ~4min | Completed: 2026-01-22*
