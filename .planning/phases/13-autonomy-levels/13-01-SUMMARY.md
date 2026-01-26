---
phase: 13-autonomy-levels
plan: 01
subsystem: safety
tags: [autonomy, risk-classification, agent-safety, literals]

# Dependency graph
requires:
  - phase: 11-safety-controls
    provides: RiskLevel type and classification system
provides:
  - AutonomyLevel type (L1-L4)
  - AUTONOMY_THRESHOLDS mapping levels to auto-execute risk sets
  - AUTONOMY_LABELS and AUTONOMY_COLORS for UI
  - AutonomySettings dataclass with auto_executes() method
  - AutonomyLevelService singleton for per-project level management
affects: [13-02 persistence, 13-03 approval integration, 13-04 custom rules, 13-05 ui, 14-yolo]

# Tech tracking
tech-stack:
  added: []
  patterns: [singleton service pattern, Literal types for levels]

key-files:
  created: [src/agent/safety/autonomy.py]
  modified: [src/agent/safety/__init__.py]

key-decisions:
  - "L2 (Collaborator) as default autonomy level"
  - "Colors that harmonize with existing RISK_COLORS"
  - "_is_downgrade() for detecting restrictive level changes"

patterns-established:
  - "AutonomyLevel uses Literal type (consistent with RiskLevel pattern)"
  - "Service callback pattern for level change notifications"

# Metrics
duration: 3min
completed: 2026-01-26
---

# Phase 13 Plan 01: Core Models Summary

**AutonomyLevel type (L1-L4) with threshold mappings and AutonomyLevelService for per-project level management**

## Performance

- **Duration:** 3 min
- **Started:** 2026-01-26T04:04:31Z
- **Completed:** 2026-01-26T04:07:39Z
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments
- Created AutonomyLevel Literal type with L1, L2, L3, L4 levels
- Defined AUTONOMY_THRESHOLDS mapping each level to auto-execute risk sets
- Implemented AutonomySettings with auto_executes() method
- Created AutonomyLevelService with per-project level caching and change callbacks
- Exported all types from safety module

## Task Commits

Each task was committed atomically:

1. **Task 1: Create autonomy level types and constants** - `4630452` (feat)
2. **Task 2: Create AutonomySettings and AutonomyLevelService** - `bf16580` (feat)
3. **Task 3: Export from safety module** - `b9858ef` (feat)

## Files Created/Modified
- `src/agent/safety/autonomy.py` - Autonomy level types, constants, settings dataclass, and service
- `src/agent/safety/__init__.py` - Added exports for autonomy types

## Decisions Made
- L2 (Collaborator) chosen as default level - balances safety with usability
- Autonomy colors chosen to harmonize with existing RISK_COLORS (blue/emerald/amber/red gradient)
- Added _is_downgrade() helper for future re-evaluation of pending actions on restrictive changes
- check_rules() returns None placeholder - implementation deferred to Plan 04

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Core models ready for persistence layer (13-02)
- AutonomySettings.auto_executes() ready for approval integration (13-03)
- check_rules() placeholder ready for custom rules implementation (13-04)
- AUTONOMY_COLORS and AUTONOMY_LABELS ready for UI components (13-05)

---
*Phase: 13-autonomy-levels*
*Completed: 2026-01-26*
