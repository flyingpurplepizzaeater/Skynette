# Phase 4: AI-Assisted Editing - Context

**Gathered:** 2026-01-18
**Status:** Ready for planning

<domain>
## Phase Boundary

AI assistance integrated into the code editor — chat panel for code questions, inline suggestions (ghost text), and diff-based change management with accept/reject controls. Users can select any configured AI provider for completions.

</domain>

<decisions>
## Implementation Decisions

### Chat Panel Placement & Behavior
- Panel position: User choice of right, left, or bottom placement
- Toggle: Both toolbar button AND keyboard shortcut to show/hide
- Code context: Auto-attach selected text + manual "Include code" button for additional context
- Chat history: User configurable — session-only, per-file, or global conversation modes

### Inline Suggestions (Ghost Text)
- Trigger: Auto after typing pause by default, plus manual shortcut trigger
- Visual style: User configurable (dimmed gray, distinct color, or italic + dimmed)
- Accept/dismiss: Tab accepts, Arrow keys cycle through alternatives
- Suggestion length: Smart adaptive — single line for completions, multi-line for new code blocks

### Diff Preview & Accept/Reject
- Diff location: Inline in editor by default, option to expand to side-by-side panel
- Accept/reject modes: Whole change, line-by-line, or hunk-based — all available
- Yolo mode: Option to auto-apply changes without confirmation
- Diff styling: User configurable (GitHub style, subtle indicators, or theme-matched)
- After accept: Apply + auto-save option (user configures whether accepting auto-saves)

### Provider Selection & Context
- Provider picker: Dropdown in chat panel + ability to set different providers per task type (chat vs inline vs diff)
- Context scope: User configurable — current file only, current + imports, or project-aware smart selection
- Token visibility: User configurable — hidden, on-demand, or always visible counter
- Limit handling: Ask user before truncating context when limits approached

### Claude's Discretion
- Exact keyboard shortcuts (must not conflict with existing editor shortcuts)
- Animation timing for ghost text appearance/dismissal
- Debounce timing for auto-trigger suggestions
- Diff algorithm implementation details
- Default provider if none configured

</decisions>

<specifics>
## Specific Ideas

- Heavy emphasis on user configurability — almost every behavior has user preference options
- "Yolo mode" for experienced users who want AI changes applied without friction
- Per-task provider selection for power users who want different models for different purposes (e.g., fast model for completions, powerful model for complex refactors)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 04-ai-assisted-editing*
*Context gathered: 2026-01-18*
