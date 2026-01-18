# Phase 3: Code Editor Core - Context

**Gathered:** 2026-01-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Users can open, edit, and save code files with syntax highlighting and file navigation. This phase delivers the core editor component with Pygments-based syntax highlighting, file tree navigation, and tabbed interface. AI assistance, completions, and diff preview are Phase 4.

</domain>

<decisions>
## Implementation Decisions

### Editor Layout
- File tree on left sidebar, editor takes remaining space (VS Code style)
- Sidebar is resizable with drag handle, remembers user preference
- Toolbar above tabs for global actions (save all, settings)
- Toggle button to collapse/show file tree (maximizes editor space)

### File Tree Behavior
- Hidden files (dotfiles) always visible — show everything
- Language-specific file icons (.py gets Python icon, .js gets JS icon, folders get folder icons)
- Single-click toggles folder expand/collapse
- Filter/search box at top of tree for quick file finding

### Tab Behavior
- Horizontal scroll when many tabs open (all accessible)
- Close button (X) visible on each tab
- Dot or asterisk next to filename indicates unsaved changes
- Prompt dialog on close with unsaved changes: Save / Don't Save / Cancel
- Tabs reorderable via drag-and-drop
- Opening same file focuses existing tab (no duplicates)
- Middle-click closes tab
- Right-click context menu: Close All, Close Others, Close to Right

### Editing Experience
- Line numbers always visible in gutter
- Subtle highlight on current line (line with cursor)
- Minimap on right edge (VS Code-style code overview)

### Claude's Discretion
- Word wrap handling (no wrap vs soft wrap vs user toggle)
- Exact spacing, typography, and color choices
- Error state handling
- Loading states

</decisions>

<specifics>
## Specific Ideas

- VS Code is the reference for general layout and feel
- File tree should be functional but not cluttered
- Tabs should behave like browser tabs (familiar patterns)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 03-code-editor-core*
*Context gathered: 2026-01-18*
