---
phase: 09-mcp-integration
plan: 05
subsystem: mcp-ui
tags: [flet, settings, dialogs, server-management]

dependency-graph:
  requires: ["09-03", "09-04"]
  provides: ["MCP settings UI", "Add server dialog", "Import config dialog"]
  affects: []

tech-stack:
  added: []
  patterns: ["controller pattern", "content builder functions", "modal dialogs"]

key-files:
  created:
    - src/ui/dialogs/mcp_add_server.py
    - src/ui/dialogs/mcp_import_config.py
    - src/ui/views/settings_mcp.py
  modified:
    - src/ui/dialogs/__init__.py
    - src/ui/views/settings.py

decisions:
  - key: "content-builder-pattern"
    value: "function-returns-column"
    rationale: "build_mcp_settings_content() returns Flet Column compatible with existing settings patterns"
  - key: "controller-not-view"
    value: "MCPSettingsController"
    rationale: "Controller manages state/actions without Flet lifecycle - cleaner separation"
  - key: "import-defaults"
    value: "untrusted-sandboxed"
    rationale: "Imported servers marked USER_ADDED with sandbox enabled by default for security"

metrics:
  duration: "5min"
  completed: "2026-01-21"
---

# Phase 9 Plan 5: UI Components Summary

MCP server management UI with dialogs for adding, importing, and managing servers in settings.

## What Was Built

### MCPAddServerDialog
- Modal dialog for manually adding MCP servers
- Transport toggle (stdio/HTTP) with dynamic field visibility
- Category dropdown (Browser Tools, File Tools, Dev Tools, etc.)
- Sandbox checkbox (enabled by default for security)
- Form validation for required fields
- Creates `MCPServerConfig` on save with `USER_ADDED` trust level

### MCPImportConfigDialog
- Modal dialog for importing from mcp.json file
- File picker for browsing to config file
- Parses both Claude Desktop and Claude Code mcp.json formats
- Preview shows servers found with transport type
- Warning about imported servers being untrusted/sandboxed
- Validates JSON and shows error states

### MCPSettingsController
- Controller class for MCP settings state management
- Loads servers from `MCPServerStorage`
- Provides dialog show methods (add, import, curated)
- Handles save, import, toggle, and delete actions
- Maintains status cache for connection indicators
- Refreshes UI after state changes

### build_mcp_settings_content()
- Function that returns Flet Column for settings integration
- Header with title and popup menu (Add, Import, Curated)
- Server list grouped by category
- Empty state with helpful message
- Each server shows: trust icon, name, status, transport, toggle, delete

## Key Files

| File | Purpose |
|------|---------|
| `src/ui/dialogs/mcp_add_server.py` | MCPAddServerDialog class |
| `src/ui/dialogs/mcp_import_config.py` | MCPImportConfigDialog and parse_mcp_config() |
| `src/ui/views/settings_mcp.py` | MCPSettingsController and build_mcp_settings_content() |
| `src/ui/dialogs/__init__.py` | Updated exports |
| `src/ui/views/settings.py` | Integration with MCP section |

## UI Components

```
Settings View
  |
  +-- MCP Servers Section
        |
        +-- Header
        |     +-- Title: "MCP Servers"
        |     +-- Subtitle: "Connect to external tool servers"
        |     +-- Menu: Add Server | Import | Curated
        |
        +-- Server List (grouped by category)
              +-- [Category Name]
              |     +-- [Server Row]
              |           +-- Trust Icon
              |           +-- Name + Status
              |           +-- Enable Toggle
              |           +-- Delete Button
              |
              +-- Empty State (when no servers)
```

## Trust Level Icons

| Trust Level | Icon | Color | Meaning |
|-------------|------|-------|---------|
| BUILTIN | Verified | Primary | Built-in server |
| VERIFIED | Verified User | Success | Third-party verified |
| USER_ADDED | Shield Outlined | Warning | User added (sandboxed) |

## Decisions Made

1. **Content Builder Pattern** - `build_mcp_settings_content()` returns Column compatible with existing `_build_section()` pattern
2. **Controller Not View** - MCPSettingsController manages state without Flet lifecycle methods (cleaner separation)
3. **Import Defaults** - Imported servers marked `USER_ADDED` with sandbox enabled (security first)
4. **Popup Menu** - Single menu button with Add/Import/Curated options (cleaner than multiple buttons)

## Commits

| Hash | Type | Description |
|------|------|-------------|
| 3a102f0 | feat | Add MCP server dialog for manual configuration |
| 4904854 | feat | Add MCP import config dialog for mcp.json |
| 9555b75 | feat | Add MCP settings content with server management |

## Deviations from Plan

None - plan executed exactly as written.

## Checkpoint Resolution

Task 4 (human verification) was approved. User chose to skip manual testing until v3 release - UI components verified through code review and automated import tests.

## Next Phase Readiness

Plan 09-05 complete. Phase 9 (MCP Integration) is now complete.

All MCP Integration components are ready:
- Server models and storage (09-01)
- MCP client connection (09-02)
- Tool registry integration (09-03)
- Sandbox security (09-04)
- UI components (09-05)

Ready to proceed to Phase 10.

## Notes

- Visual testing deferred to v3 release milestone
- UI follows existing Flet patterns from settings.py
- Server list refreshes automatically after add/import/delete operations
