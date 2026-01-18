# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-01-17)

**Core value:** One app to replace separate AI chat clients, model managers, and workflow tools -- accessible to everyone
**Current focus:** Phase 5 - Advanced Integration

## Current Position

Phase: 5 of 5 (Advanced Integration)
Plan: 3 of 4 in current phase
Status: In progress
Last activity: 2026-01-18 -- Completed 05-03-PLAN.md (Code Execution Node)

Progress: [######################] 96%

## Performance Metrics

**Velocity:**
- Total plans completed: 23
- Average duration: 8.0 min
- Total execution time: 3.05 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1. Stability & Audit | 4/4 | 80 min | 20 min |
| 2. Provider Foundation | 5/5 | 34 min | 7 min |
| 3. Code Editor Core | 5/5 | 31 min | 6 min |
| 4. AI-Assisted Editing | 6/6 | 21 min | 3.5 min |
| 5. Advanced Integration | 3/4 | 15 min | 5 min |

**Recent Trend:**
- Last 5 plans: 05-03 (5 min), 05-02 (5 min), 05-01 (5 min), 04-06 (3 min), 04-05 (5 min)
- Trend: Fast

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Roadmap]: Five phases derived from requirement categories (STAB, PROV, EDIT, AIED, INTG, QUAL)
- [Research]: Use google-genai SDK (not deprecated google-generativeai) for Gemini
- [Research]: Use xai-sdk for Grok provider
- [Research]: Use Pygments for syntax highlighting (598 languages, no Flutter wrapper complexity)
- [01-02]: Import sorting issues in ai_hub.py deferred to Plan 04 (refactor)
- [01-02]: Wizard multi-provider config is UX limitation, not blocking bug
- [01-03]: BUG-01 fixed: _add_step connection logic now captures steps before adding new node
- [01-01]: simple_mode.py is workflow builder, not AI Chat (plan naming discrepancy documented)
- [01-01]: AIGateway regression tests added (17 tests)
- [01-04]: State container pattern with listener/notify for reactive updates
- [01-04]: TabBar + TabBarView pattern for Flet 0.80 compatibility (Tab.content deprecated)
- [01-04]: Feature-based decomposition for large Flet views
- [02-01]: GeminiProvider uses google-genai SDK with client.aio for async
- [02-02]: GrokProvider uses xai-sdk with 3600s timeout for reasoning models
- [02-03]: User-friendly Ollama error messages over technical errors
- [02-03]: did_mount lifecycle hook for auto-refresh on tab load
- [02-04]: Streaming recovery wrapper catches all exceptions, yields interrupt marker, re-raises wrapped
- [02-04]: Rate limit threshold at 80% for is_approaching_limit flag
- [02-04]: _raw_chat_stream pattern separates internal implementation from public chat_stream
- [02-05]: Provider tests verify behavior without requiring actual SDK packages
- [03-01]: GitHub Dark theme colors for Pygments syntax highlighting
- [03-01]: File size limits: 50KB warn, 500KB refuse for editor performance
- [03-01]: Hierarchical token lookup in Pygments for reasonable color defaults
- [03-03]: ft.Column base class for custom controls (Flet 0.80 removed UserControl)
- [03-03]: ListView item_extent=28 enables virtualization for large file trees
- [03-03]: GestureDetector for drag-based resize interactions
- [03-04]: Use _page_ref instead of page to avoid Flet read-only property conflict
- [03-04]: ft.alignment.Alignment(0, 0) instead of ft.alignment.center
- [03-04]: FilePicker.on_result assigned as property, not constructor kwarg
- [03-04]: FilePicker must be initialized in __init__ and added to page.overlay before use
- [03-05]: Dispose chains from view to children to state for complete cleanup
- [03-05]: App navigation calls dispose in _update_content() before switching views
- [04-01]: tiktoken cl100k_base for OpenAI, p50k_base fallback for other providers
- [04-01]: ChatState follows EditorState listener/notify pattern
- [04-01]: DiffService uses difflib.unified_diff for cross-platform diff generation
- [04-02]: Use gateway.chat_stream() for streaming responses (not generate())
- [04-02]: Coding assistant system prompt for API messages
- [04-02]: User-friendly error messages for missing AI providers
- [04-03]: 500ms debounce delay for completion requests
- [04-03]: Temperature 0.2 for deterministic inline completions
- [04-03]: Stop sequences for natural completion boundaries
- [04-04]: GitHub-style diff colors for familiarity (green add, red remove)
- [04-04]: Per-hunk acceptance tracked in _accepted_hunks set for O(1) lookup
- [04-04]: Visual feedback via border color/width and check icon for accepted state
- [04-05]: Keyboard shortcuts: Ctrl+Shift+A (AI panel), Tab (accept), Escape (dismiss), Ctrl+Shift+D (diff)
- [04-05]: Provider selection persists in ChatState across chat sessions
- [04-05]: Ghost text hidden on typing, re-triggered after 500ms pause
- [04-06]: Mock Flet update() method for component tests without running app
- [04-06]: Test state management directly rather than full UI rendering
- [05-01]: WorkflowBridge with YAML, JSON, Python DSL format support
- [05-01]: yaml.safe_load for security, restricted exec for Python DSL
- [05-02]: DimensionValidator for embedding consistency across providers
- [05-03]: 300 second max timeout cap for code execution safety
- [05-03]: PowerShell uses -ExecutionPolicy Bypass for script execution
- [05-03]: Variable injection uses repr/JSON for safe escaping

### Pending Todos

- [03-04]: Manual verification of CodeEditorView (open folder, file tree, tabs, save, dirty indicator, sidebar resize)

### Blockers/Concerns

- [Research]: Flet code editor performance with large files (1000+ lines) not benchmarked
- [Research]: Grok rate limits less documented than OpenAI/Anthropic
- [01-02]: mypy not installed in dev environment
- ~~[Research]: State management refactor needed before editor adds more complexity (AIHubView at 1669 lines)~~ RESOLVED in 01-04

## Session Continuity

Last session: 2026-01-18
Stopped at: Completed 05-03-PLAN.md (Code Execution Node)
Resume file: None
