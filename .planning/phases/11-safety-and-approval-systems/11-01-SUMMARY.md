---
phase: 11-safety-and-approval-systems
plan: 01
subsystem: safety
tags: [classification, risk-levels, approval, pydantic, literal-types]

# Dependency graph
requires:
  - phase: 10-built-in-tools
    provides: Built-in tool implementations (file_*, code_execute, browser, github, etc.)
provides:
  - RiskLevel Literal type (safe/moderate/destructive/critical)
  - ActionClassification Pydantic model
  - ActionClassifier with tool-specific rules
  - RISK_COLORS and RISK_LABELS constants for UI
affects: [11-02, 11-03, 11-04, 11-05, 11-06, 11-07, phase-12, phase-13]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Literal type for risk levels (consistent with 07-01 decision)"
    - "Static dict-based classification for built-in tools"
    - "Default to moderate for unknown/MCP tools"

key-files:
  created:
    - src/agent/safety/__init__.py
    - src/agent/safety/classification.py
  modified:
    - src/agent/__init__.py

key-decisions:
  - "Four risk levels: safe, moderate, destructive, critical"
  - "Built-in tools have static classifications (10 tools mapped)"
  - "Unknown/MCP tools default to moderate until first approval"
  - "safe/moderate do not require approval by default"
  - "destructive/critical require approval"

patterns-established:
  - "Classification lookup via dict mapping tool_name to RiskLevel"
  - "Human-readable reasons with parameter context"
  - "Color theming for risk badges (green/amber/orange/red)"

# Metrics
duration: 5min
completed: 2026-01-22
---

# Phase 11 Plan 01: Action Classification System Summary

**RiskLevel Literal type with ActionClassifier providing tool-specific risk classification for 10 built-in tools, with RISK_COLORS/RISK_LABELS for UI theming**

## Performance

- **Duration:** 5 min
- **Started:** 2026-01-22T09:38:13Z
- **Completed:** 2026-01-22T09:43:42Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments
- Created RiskLevel Literal type with four risk levels (safe/moderate/destructive/critical)
- ActionClassification Pydantic model with risk_level, reason, requires_approval, tool_name, parameters, timestamp
- ActionClassifier with TOOL_CLASSIFICATIONS dict for 10 built-in tools
- RISK_COLORS and RISK_LABELS constants for UI badge theming
- All types exported from src.agent package

## Task Commits

Each task was committed atomically:

1. **Task 1: Create safety module with classification models** - `5e826cf` (feat)
2. **Task 2: Create ActionClassifier with tool-specific rules** - `8de7c48` (feat)
3. **Task 3: Export from agent package and add risk colors constant** - `f6b1bbe` (feat)

## Files Created/Modified
- `src/agent/safety/__init__.py` - Safety module package exports
- `src/agent/safety/classification.py` - RiskLevel, ActionClassification, ActionClassifier, RISK_COLORS, RISK_LABELS
- `src/agent/__init__.py` - Added safety module exports

## Decisions Made
- Four risk levels as specified: safe, moderate, destructive, critical
- Used Literal type per 07-01 decision (better JSON serialization than Enum)
- Static dict-based classification for built-in tools (simple, efficient lookup)
- Unknown/MCP tools default to moderate (safe default until first approval)
- Colors match Theme patterns: green (#22C55E), amber (#F59E0B), orange (#F97316), red (#EF4444)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

Parallel execution detected: While executing this plan, a parallel agent was executing plan 11-02 (KillSwitch). The agents coordinated commits appropriately - each plan committed its own changes without conflicts.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- ActionClassifier ready for use in approval flow (11-03, 11-04)
- Risk colors/labels ready for UI badges (11-05)
- Classification models ready for audit trail (11-06)
- Foundation complete for human-in-the-loop approval system

---
*Phase: 11-safety-and-approval-systems*
*Plan: 01*
*Completed: 2026-01-22*
