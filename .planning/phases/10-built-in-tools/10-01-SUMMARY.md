---
phase: 10-built-in-tools
plan: 01
subsystem: agent-tools
tags: [utilities, filesystem, validation, backup, dependencies]
dependency-graph:
  requires: [07-agent-core-infrastructure]
  provides: [FileSystemValidator, backup_before_modify, cleanup_old_backups, tool-dependencies]
  affects: [10-02, 10-03, 10-04, 10-05, 10-06]
tech-stack:
  added: [duckduckgo-search, playwright, playwright-stealth, PyGithub, psutil, beautifulsoup4]
  patterns: [path-validation-with-allowlist, timestamped-backup]
key-files:
  created:
    - src/agent/tools/__init__.py
    - src/agent/tools/base.py
  modified:
    - src/agent/registry/tool_registry.py
    - requirements.txt
decisions:
  - id: path-validation-approach
    choice: "Allowlist + blocked patterns with is_relative_to()"
    reason: "Security-first: explicitly permit directories, block dangerous patterns"
  - id: backup-timestamp-format
    choice: "YYYYMMDD_HHMMSS suffix before .bak extension"
    reason: "Sortable by name, human-readable, unique per second"
metrics:
  duration: ~4min
  completed: 2026-01-22
---

# Phase 10 Plan 01: Foundation Utilities Summary

**One-liner:** Path validation (allowlist + blocked patterns) and timestamped backup utilities for safe filesystem tools.

## What Was Built

### FileSystemValidator Class
Security utility that validates paths against:
1. **Allowlist**: Paths must be within specified allowed directories (uses `is_relative_to()`)
2. **Blocked patterns**: Rejects paths containing dangerous patterns (`.env`, `credentials`, `.git`)

```python
validator = FileSystemValidator(["/tmp", "/home/user/project"], [".env", ".git"])
validator.validate("/tmp/test.txt")  # (True, "")
validator.validate("/etc/passwd")     # (False, "Path not in allowed directories")
validator.validate("/tmp/.env")       # (False, "Path contains blocked pattern: .env")
```

### Backup Utilities
- **backup_before_modify(path)**: Creates timestamped backup like `file.20260122_143052.bak`
- **cleanup_old_backups(path, keep=5)**: Removes old backups, keeps N most recent

### ToolRegistry Update
Added placeholder comments for built-in tool registration. Tools from Plans 02-05 will be registered in `_load_builtin_tools()`.

### Dependencies Added
All Phase 10 dependencies declared in requirements.txt:
- `duckduckgo-search>=8.0.0` - Web search
- `playwright>=1.49.0` - Browser automation
- `playwright-stealth>=1.0.0` - Bot detection evasion
- `PyGithub>=2.8.0` - GitHub API
- `psutil>=7.0.0` - Process monitoring
- `beautifulsoup4>=4.12.0` - HTML parsing
- `tenacity>=8.0.0` - Retry logic (was implicit, now explicit)

## Decisions Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Path validation | Allowlist + blocked patterns | Security-first: default deny, explicit allow |
| Path resolution | `Path.resolve()` | Handles symlinks, prevents traversal attacks |
| Backup naming | `{stem}.{timestamp}.bak` | Sortable, unique, preserves original extension info |
| Backup preservation | `shutil.copy2()` | Preserves metadata (timestamps, permissions) |

## Deviations from Plan

None - plan executed exactly as written.

## Verification Results

All success criteria met:
- [x] FileSystemValidator validates paths correctly (allows valid, blocks dangerous)
- [x] backup_before_modify creates timestamped .bak files
- [x] cleanup_old_backups removes old backups, keeps N most recent
- [x] ToolRegistry loads without errors
- [x] requirements.txt includes all Phase 10 dependencies

## Artifacts

| File | Purpose | Lines |
|------|---------|-------|
| `src/agent/tools/__init__.py` | Package exports | 15 |
| `src/agent/tools/base.py` | FileSystemValidator, backup utilities | 137 |
| `src/agent/registry/tool_registry.py` | Updated _load_builtin_tools | +6 lines |
| `requirements.txt` | Phase 10 dependencies | +10 lines |

## Next Phase Readiness

**Ready for Plans 02-05:** All filesystem-touching tools can now use:
- `FileSystemValidator` for security
- `backup_before_modify` / `cleanup_old_backups` for safety

**Note:** After `pip install -r requirements.txt`, run `playwright install chromium` for browser binaries.
