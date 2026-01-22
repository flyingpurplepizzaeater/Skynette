---
phase: 11
plan: 05
subsystem: safety
tags: [ui, flet, approval, risk-badge, bottom-sheet]

depends:
  requires: ["11-01", "11-03"]
  provides: ["approval-ui", "risk-badge"]
  affects: ["11-06", "13"]

tech-stack:
  added: []
  patterns:
    - Flet BottomSheet for modal approval
    - Color-coded risk visualization

key-files:
  created:
    - src/agent/ui/risk_badge.py
    - src/agent/ui/approval_sheet.py
  modified:
    - src/agent/ui/__init__.py
    - src/agent/__init__.py

decisions:
  - id: "11-05-01"
    decision: "Use Container with colored dot + label for risk badge"
    rationale: "Simple, clear visual indicator matching Theme patterns"
  - id: "11-05-02"
    decision: "Non-dismissible BottomSheet for approval"
    rationale: "Requires explicit user decision - no accidental dismissal"

metrics:
  duration: "4 minutes"
  completed: "2026-01-22"
---

# Phase 11 Plan 05: Approval UI Components Summary

**One-liner:** RiskBadge color-coded component and ApprovalSheet BottomSheet for human-in-the-loop approval workflow.

## Completed Tasks

| # | Task | Commit | Key Files |
|---|------|--------|-----------|
| 1 | Create RiskBadge component | 0fa199d | `risk_badge.py` |
| 2 | Create ApprovalSheet bottom sheet | d313831, 2d97620 | `approval_sheet.py` |
| 3 | Export UI components | d73b775 | `__init__.py` files |

## Implementation Details

### RiskBadge Component

Color-coded badge for risk level display:

- **Full mode:** Colored dot + label text (e.g., "[*] Destructive")
- **Compact mode:** Dot only with tooltip
- **Styling:** Uses RISK_COLORS from classification, 20% opacity background
- **Dynamic update:** `update_risk_level()` method for live updates

Risk level colors:
- `safe`: Green (#22C55E)
- `moderate`: Amber (#F59E0B)
- `destructive`: Orange (#F97316)
- `critical`: Red (#EF4444)

### ApprovalSheet Component

BottomSheet for action approval workflow:

- **Header:** RiskBadge + tool name
- **Body:** Reason text + parameter preview (monospace, truncated to 500 chars)
- **Actions:** Three buttons - Reject (outlined), Approve (filled), Approve All Similar (tonal)
- **Behavior:** `dismissible=False` - requires explicit user decision, no click-outside dismiss
- **Integration:** Uses ApprovalRequest and ActionClassification from safety module

### Package Exports

Both components exported from:
- `src.agent.ui` module
- `src.agent` package (top-level)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed unsupported Flet BottomSheet parameters**
- **Found during:** Task 2 verification
- **Issue:** `enable_drag` and `is_scroll_controlled` not valid in Flet 0.80.1
- **Fix:** Removed unsupported parameters, kept `show_drag_handle` and `dismissible`
- **Files modified:** `approval_sheet.py`
- **Commit:** 2d97620

## Verification Results

All success criteria verified:
- RiskBadge shows colored dot + label for all four risk levels
- RiskBadge compact mode with tooltip works correctly
- ApprovalSheet displays classification details
- ApprovalSheet has three buttons (Reject, Approve, Approve All Similar)
- ApprovalSheet is non-dismissible (dismissible=False)
- Parameters truncated to 500 chars for display
- All components use Theme for colors and spacing
- Components exported from both packages

## What's Next

**Next plan:** 11-06 (Integration Tests)
- Test safety system components together
- Test UI component integration with approval flow

**Integration ready:**
- RiskBadge can display any ActionClassification risk level
- ApprovalSheet can handle any ApprovalRequest
- Components ready for AgentView integration in Phase 13
