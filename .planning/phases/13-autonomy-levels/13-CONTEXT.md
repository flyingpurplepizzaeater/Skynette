# Phase 13: Autonomy Levels - Context

**Gathered:** 2026-01-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Configure how much oversight agent requires (L1-L4). Users can set autonomy levels per-project, switch levels inline during sessions, and customize thresholds with allow/block rules. L5 (YOLO Mode) is a separate phase.

</domain>

<decisions>
## Implementation Decisions

### Level Transitions
- Switch via settings OR inline quick toggle in agent panel header
- No friction when escalating to higher autonomy — instant switch
- Can switch mid-task — new level applies immediately to remaining steps
- When downgrading mid-task, re-evaluate any pending queued actions under new level

### Per-Project Settings
- Default level for new projects: user's global default (set in app settings)
- New users: prompt during onboarding to choose their preferred default level
- Storage: Skynette's SQLite DB, keyed by project path (not project files)
- Show autonomy level badge/icon in project list/switcher

### Threshold Customization
- Levels are fixed presets, but users can add allowlist exceptions
- Allowlist rules: both tool-based ("always allow web_search") and pattern-based ("always allow file writes to /src/*")
- Scope: global rules apply everywhere, project rules add on top
- Also support blocklist rules ("always block" overrides level auto-approve)

### UI Indicators
- Color-coded indicator for current level in agent panel
- Subtle "auto" badge on steps that auto-executed (would have needed approval at lower level)
- Quick toggle: clickable level indicator in panel header opens dropdown selector

### Claude's Discretion
- Exact color scheme for levels (should harmonize with existing risk badge colors)
- Onboarding flow UX details
- Allowlist/blocklist UI in settings
- How pattern-based rules are expressed (glob, regex, etc.)

</decisions>

<specifics>
## Specific Ideas

- "I want switching to be instant — I know what I'm doing when I escalate"
- Re-evaluate pending actions on downgrade (safer approach when user increases oversight)
- Badge in project list so you know at a glance which projects have high autonomy

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 13-autonomy-levels*
*Context gathered: 2026-01-23*
