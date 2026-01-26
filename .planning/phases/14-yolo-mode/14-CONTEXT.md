# Phase 14: YOLO Mode - Context

**Gathered:** 2026-01-26
**Status:** Ready for planning

<domain>
## Phase Boundary

L5 (Observer/YOLO) mode for power users who want fully autonomous agent execution. All approval prompts are skipped, but full audit logging and kill switch remain active. This phase adds L5 to the existing L1-L4 autonomy system from Phase 13.

</domain>

<decisions>
## Implementation Decisions

### Activation safeguards
- Confirmation dialog when selecting L5 (not just a quick toggle like L1-L4)
- Brief one-liner warning in dialog: "Actions will execute without approval prompts"
- Auto-deactivation is user-configurable in settings
- Default behavior: session only (YOLO resets when Skynette closes)

### Environment restrictions
- Soft requirement: warn if not in sandboxed environment, but allow user to proceed
- Warning dialog includes two options: "Proceed anyway" and "Don't warn again"
- "Don't warn again" preference is global (applies to all projects once acknowledged)

### Visual indicators
- Distinctive styling: badge + panel border color change when YOLO active
- Purple color for YOLO mode (power mode aesthetic, not danger/warning)
- Startup reminder when opening a project that has YOLO active
- Consistent badge placement with L1-L4 (in panel header)

### Absolute limits
- True YOLO: no actions require approval, regardless of risk classification
- Kill switch always remains active (emergency stop independent of autonomy level)
- Enhanced audit logging: extra verbosity, full parameters captured, longer retention

### Claude's Discretion
- Sandbox detection heuristics (Docker, WSL, VM, cloud dev environments)
- Whether/how to display execution stats on YOLO badge
- Whether allowlist/blocklist rules apply in YOLO mode

</decisions>

<specifics>
## Specific Ideas

- "Power users" is the target - people who understand the risks and want speed
- Purple differentiates from risk colors (red/amber) - it's a mode, not a warning
- Session-only default adds a safety reset point (reboot = exit YOLO)

</specifics>

<deferred>
## Deferred Ideas

None - discussion stayed within phase scope

</deferred>

---

*Phase: 14-yolo-mode*
*Context gathered: 2026-01-26*
