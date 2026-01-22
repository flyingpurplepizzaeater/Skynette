# Phase 12: UI Integration - Context

**Gathered:** 2026-01-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Make agent capabilities visible and controllable through the UI. This includes:
- Agent panel for viewing status and interacting with agent
- Progress display showing thinking state and step completion
- Approval dialogs for HITL decisions
- Plan visualization before and during execution
- Audit trail visibility

This phase wires existing agent backend (Phase 8) and safety systems (Phase 11) into the Flet UI. New agent capabilities or safety features belong in other phases.

</domain>

<decisions>
## Implementation Decisions

### Agent Panel Layout
- Right sidebar docked to workspace edge
- Toggle button for visibility (user-controlled, persists between sessions)
- Resizable width — user can drag to resize, system remembers preference
- Attention handling: Badge on toggle button when collapsed AND auto-expand for critical moments (approvals needed)

### Progress Visualization
- Thinking state: Animated dots/spinner combined with progress bar showing phase (planning/executing)
- Step display: User-selectable view toggle between:
  - Checklist style (vertical list with checkmarks)
  - Timeline/stepper (horizontal or vertical step numbers)
  - Expandable cards (detail per step)
- Step results: Collapsed by default; click to expand and see full result

### Approval Experience
- Detail level: User-configurable global setting (minimal, detailed, or progressive)
- Modification: Users can edit action parameters before approving
- Remember choice: Checkbox with scope options — "Remember for this session" / "Remember for this type"
- Batch approvals: Grouped card showing count with expandable list ("Approve 5 similar file reads?")

### Plan Display
- View format: User-configurable between:
  - Step list (numbered, scannable)
  - Tree view (hierarchical with dependencies)
  - Flowchart/diagram (visual graph)
- Plan approval: Editable plan with full editing (reorder, remove, add steps, edit descriptions)
- Dynamic updates: Plan view updates in real-time if agent replans during execution

### Claude's Discretion
- Exact animation timings and easing
- Color scheme for risk levels (building on existing RiskBadge)
- Layout of settings page for UI preferences
- Default view selections for new users
- Accessibility considerations (screen reader support)

</decisions>

<specifics>
## Specific Ideas

- User wants flexibility and configuration throughout — "option for each, user configurable" was a consistent theme
- Views should be switchable, not locked to one approach
- Progressive disclosure pattern: start simple, expand for detail (especially approvals and step results)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 12-ui-integration*
*Context gathered: 2026-01-22*
