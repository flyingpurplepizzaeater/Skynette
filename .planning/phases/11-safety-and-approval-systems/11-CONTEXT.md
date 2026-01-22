# Phase 11: Safety and Approval Systems - Context

**Gathered:** 2026-01-22
**Status:** Ready for planning

<domain>
## Phase Boundary

User has control over what agent can do with appropriate oversight. This phase delivers:
- Action classification with visible risk levels (safe/moderate/destructive/critical)
- HITL approval workflow for flagged actions
- Queryable audit trail for all agent actions
- Kill switch for emergency stops
- Batch approval for similar low-risk actions

Autonomy level configuration (L1-L4) is Phase 13. Full YOLO mode is Phase 14.

</domain>

<decisions>
## Implementation Decisions

### Classification Display
- Color-coded badges with text labels (Green/Safe, Yellow/Moderate, Orange/Destructive, Red/Critical)
- Badge appears in BOTH step header (visible in plan list) AND inline when action details expanded
- Always show classification reason alongside badge (e.g., "Destructive: deletes files")
- Unknown/custom MCP tools default to moderate risk until user approves once

### Approval Flow
- Bottom sheet slides up from bottom with action details and approval buttons
- Three options: Approve / Approve All Similar / Reject
- "Approve All Similar" matches same tool + similar parameter pattern (e.g., file writes to same directory)
- Approval scoped to current agent task session only
- Timeout behavior: skip to safer alternative if available, otherwise pause (not auto-reject)

### Audit Trail Design
- Comprehensive entries: timestamp, action name, result, risk level, parameters, approval decision, duration, full input/output, context, parent plan step
- Tree view navigation showing hierarchy: plan > step > actions
- Filters for risk level, tool type, date range, status
- Export in multiple formats: JSON, CSV, markdown report
- 30-day retention with auto-purge

### Kill Switch UX
- Multiple invocation methods: prominent red stop button, keyboard shortcut, system tray option
- Immediate halt behavior (current action may be left incomplete)
- Summary dialog after kill: shows what completed, what interrupted, any cleanup needed
- Offer both undo (rollback completed steps where possible) AND resume (continue from where stopped)

### Claude's Discretion
- Exact color hex values for risk badges
- Keyboard shortcut choice for kill switch
- Bottom sheet animation and layout details
- Tree view expand/collapse behavior
- Timeout duration before falling back to safe action

</decisions>

<specifics>
## Specific Ideas

- Classification reasoning should be concise but clear (e.g., "Destructive: modifies system files" not just "Destructive")
- "Approve All Similar" should feel smart — approving file writes to `/src` should also approve writes to `/src/components` but not to `/config`
- Kill switch must work even if UI is sluggish or agent is in a tight loop

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 11-safety-and-approval-systems*
*Context gathered: 2026-01-22*
