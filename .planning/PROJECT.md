# Skynette

## What This Is

An all-in-one, open-source AI workspace that combines chat, model management, workflow automation, code editing, and autonomous agent capabilities in a single unified interface. Users can run it as a desktop app or self-host it as a web application. It supports both local AI models (via Ollama, llama.cpp) and cloud providers (OpenAI, Anthropic, Gemini, Grok) seamlessly. The integrated agent can build apps, browse the web, interact with external services, and execute multi-step tasks autonomously or with human oversight.

## Core Value

One app to replace the need for separate AI chat clients, local model managers, workflow automation tools, code editors, and AI assistants - accessible to everyone, not just developers.

## Current State

**Shipped Version:** v3.0 Agent (2026-01-27)

Skynette is now a general-purpose AI assistant capable of autonomous task execution with configurable human oversight. The agent can decompose complex tasks into steps, execute tools (web search, browser, filesystem, code, GitHub), and respects user-defined autonomy levels from L1 (suggestion only) to L5 (full YOLO mode).

**Next Milestone Goals:**
- v3.1: Multi-agent coordination, cross-session memory
- v4.0: Mobile optimization, team features

## Requirements

### Validated

- ✓ Flet-based cross-platform GUI (desktop + web) - existing
- ✓ Node-based workflow automation engine with visual editor - existing
- ✓ Multi-provider AI gateway with auto-fallback - existing
- ✓ OpenAI provider integration (GPT-4, embeddings) - existing
- ✓ Anthropic provider integration (Claude) - existing
- ✓ Local model support via llama.cpp (GGUF models) - existing
- ✓ RAG subsystem with ChromaDB for knowledge bases - existing
- ✓ Scheduled and trigger-based workflow execution - existing
- ✓ Expression system for dynamic workflow values - existing
- ✓ Credential encryption and secure storage - existing
- ✓ SQLite + YAML hybrid storage - existing
- ✓ AI Chat functionality audited and stabilized - v2.0
- ✓ Model Management (local + cloud) audited and stabilized - v2.0
- ✓ Workflow Builder audited and stabilized - v2.0
- ✓ Gemini provider integration (google-genai SDK) - v2.0
- ✓ Grok provider integration (xai-sdk) - v2.0
- ✓ Ollama provider with status UI and service discovery - v2.0
- ✓ Code editor with Pygments syntax highlighting (598 languages) - v2.0
- ✓ File tree navigation with tabbed multi-file interface - v2.0
- ✓ AI chat panel integrated with code context awareness - v2.0
- ✓ Inline ghost text suggestions with Tab to accept - v2.0
- ✓ Diff preview with accept/reject controls for AI changes - v2.0
- ✓ Workflow script editing in code editor (YAML/JSON/Python DSL) - v2.0
- ✓ Project-level RAG with semantic code search - v2.0
- ✓ Code execution node for workflows (Python/JS/Bash/PowerShell) - v2.0
- ✓ Comprehensive test coverage (477+ tests) - v2.0
- ✓ Security audit confirming API key protection - v2.0
- ✓ Agent planning phase (decompose tasks into executable steps) - v3.0
- ✓ Agent execution loop with tool use and retry logic - v3.0
- ✓ Visual progress feedback (thinking indicator, status updates) - v3.0
- ✓ Both autonomous (background) and interactive modes - v3.0
- ✓ Configurable per-action approval levels (L1-L4) - v3.0
- ✓ YOLO bypass mode (L5) for power users - v3.0
- ✓ MCP host implementation (connect to MCP servers) - v3.0
- ✓ Support for stdio, SSE, and HTTP transports - v3.0
- ✓ Tool discovery and registration from MCP servers - v3.0
- ✓ Built-in MCP server management UI - v3.0
- ✓ Web search via DuckDuckGo API (no key required) - v3.0
- ✓ Headless browser for complex web interactions (Playwright) - v3.0
- ✓ Filesystem operations (read, write, create, delete) - v3.0
- ✓ Code execution tool (Python/JS/Bash/PowerShell) - v3.0
- ✓ GitHub integration (create repos, commit, push) - v3.0
- ✓ Smart model routing (suggest best model per task) - v3.0
- ✓ User-configurable model defaults per task type - v3.0
- ✓ Action classification (safe, moderate, destructive, critical) - v3.0
- ✓ Human-in-the-loop approval workflow with batch support - v3.0
- ✓ Comprehensive audit log with JSON/CSV export - v3.0
- ✓ Kill switch (Ctrl+Shift+K) to stop running agent tasks - v3.0
- ✓ 370+ tests covering all agent subsystems - v3.0

### Active

(No active requirements - new milestone not yet defined)

### Out of Scope

- Mobile native apps - web/desktop first, mobile can access via web
- Real-time collaboration - single-user focus, complexity too high
- Plugin marketplace - SDK exists but marketplace deferred
- Custom model training - use pre-trained models only
- Email integration - defer to MCP servers (users can add their own)
- Stock market integration - defer to MCP servers
- Multi-agent coordination - complexity, defer to v3.1+

## Context

**Current state:** Shipped v3.0 with ~195,000 LOC Python across 250+ files.

**Tech stack:** Python/Flet for GUI, FastAPI for webhooks, ChromaDB for RAG, Pygments for syntax highlighting, tiktoken for token counting, MCP SDK for tool extensibility, Playwright for browser automation.

**Provider support:** OpenAI, Anthropic, Gemini, Grok, Ollama, local llama.cpp

**Test coverage:** 847+ tests covering all major subsystems (477 v2.0 + 370 v3.0)

**Known issues:**
- Manual CodeEditorView verification pending (deferred from v2.0)
- mypy not installed in dev environment
- Flet deprecation warnings (symmetric(), ElevatedButton) for 0.73/1.0

## Constraints

- **Tech stack**: Python/Flet - validated through v3.0 development
- **Deployment**: Must work as both desktop app (PyInstaller) and web app (self-hosted)
- **AI providers**: Must support OpenAI, Anthropic, Ollama, Gemini, Grok
- **Local-first**: Core features must work offline with local models
- **Open source**: All code public, self-hostable, privacy-respecting
- **Safety**: Agent actions must be auditable and controllable

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Python/Flet for GUI | Cross-platform from single codebase | ✓ Good (shipped v3.0) |
| SQLite for storage | No external database dependency | ✓ Good |
| Multi-provider gateway pattern | Easy to add new AI providers | ✓ Good (5 providers) |
| Node-based workflows | Visual, accessible to non-developers | ✓ Good |
| State container pattern | Reactive updates without external library | ✓ Good (used in AIHub, Editor, Agent) |
| Pygments for syntax highlighting | 598 languages, no Flutter wrapper complexity | ✓ Good |
| google-genai SDK for Gemini | Official SDK, async support, actively maintained | ✓ Good |
| DimensionValidator for embeddings | Prevents ChromaDB corruption from model changes | ✓ Good |
| RAG context in system prompt | Maintains conversation history integrity | ✓ Good |
| Lazy project indexing | Avoid slow startup, index on first query | ✓ Good |
| MCP for extensibility | Standard protocol, community ecosystem, future-proof | ✓ Good (shipped v3.0) |
| Configurable approval levels | Balance autonomy with safety | ✓ Good (L1-L5 shipped) |
| Custom agent loop (not LangChain) | Simplicity, control, no heavy dependencies | ✓ Good |
| Plan-and-execute pattern | Proven architecture for agent systems | ✓ Good |
| Session-only YOLO mode | Safety - L5 never persists to storage | ✓ Good |
| SQLite WAL for all storage | Consistent pattern across traces, audit, autonomy | ✓ Good |

---
*Last updated: 2026-01-27 after v3.0 milestone shipped*
