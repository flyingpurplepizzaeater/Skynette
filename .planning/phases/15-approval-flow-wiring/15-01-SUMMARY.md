---
phase: 15-approval-flow-wiring
plan: 01
subsystem: agent-safety
tags: [approval-flow, human-in-the-loop, gap-closure]

dependency_graph:
  requires: [11-03]
  provides: [resolve-method, ui-approval-integration]
  affects: []

tech_stack:
  added: []
  patterns: [router-method, decision-dispatch]

file_tracking:
  created: []
  modified:
    - src/agent/safety/approval.py
    - tests/agent/test_safety_e2e.py

decisions:
  - id: "15-01-01"
    choice: "timeout treated as rejection"
    rationale: "User not responding means they didn't approve; safer default"
  - id: "15-01-02"
    choice: "Warning log for unknown decisions"
    rationale: "Fail gracefully with visibility rather than raising exception"

metrics:
  duration: ~3min
  completed: 2026-01-26
---

# Phase 15 Plan 01: Approval Flow Wiring Summary

**resolve() router method connects UI callbacks to ApprovalManager approve/reject**

## What Was Built

Added the missing `resolve()` method to `ApprovalManager` that bridges UI approval callbacks to the underlying `approve()` and `reject()` methods. This closes the SAFE-02 integration gap identified in the milestone audit.

### Key Implementation

```python
def resolve(self, request_id: str, decision: str, approve_similar: bool = False) -> None:
    if decision == "approved":
        self.approve(request_id, approve_similar)
    elif decision == "rejected":
        self.reject(request_id)
    elif decision == "timeout":
        self.reject(request_id)  # Timeout = user didn't approve
    else:
        logger.warning(f"Unknown approval decision '{decision}' for request {request_id}")
```

### Integration Points

The method signature matches exactly what `agents.py` expects:
- Line 387: `approval_manager.resolve(request.id, decision="approved", approve_similar=approve_similar)`
- Line 396: `approval_manager.resolve(request.id, decision="rejected")`
- Line 420: `approval_manager.resolve(request.id, decision="timeout")`

## Tasks Completed

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | Add resolve() method to ApprovalManager | 9e1f952 | src/agent/safety/approval.py |
| 2 | Add E2E tests for resolve() method | bd85cd1 | tests/agent/test_safety_e2e.py |
| 3 | Verify full approval flow works | - | (verification only) |

## Verification Results

All success criteria met:

- ApprovalManager.resolve() method exists: **PASS**
- resolve("approved") completes approval flow: **PASS**
- resolve("rejected") completes rejection flow: **PASS**
- resolve("timeout") routes to rejection: **PASS**
- E2E tests (7/7 approval tests): **PASS**
- AgentsView imports successfully: **PASS**
- Integration flow verification: **PASS**

## Deviations from Plan

None - plan executed exactly as written.

## Notes

Two pre-existing test failures in `TestClassificationE2E` were observed (unrelated to this plan):
- `test_unknown_tool_defaults_moderate` - assumes moderate risk doesn't require approval
- `test_approval_required_by_risk_level` - assumes browser tool doesn't require approval

These tests were written in Phase 11-07 with assumptions that were likely invalidated by Phase 13-03 (which modified classification behavior to be more strict). This is tracked but not addressed in this gap-closure plan.

## Gap Closure Status

**SAFE-02 (Human-in-the-loop approval):** CLOSED

The approval flow now works end-to-end:
1. Agent executor requests approval via `ApprovalManager.request_approval()`
2. UI displays approval sheet with approve/reject buttons
3. UI callbacks invoke `ApprovalManager.resolve()` with decision
4. `resolve()` routes to `approve()` or `reject()`
5. `ApprovalRequest.set_result()` unblocks the waiting executor
6. Executor continues or skips based on decision
