# Skynette

## What This Is

An all-in-one, open-source AI workspace that combines chat, model management, workflow automation, code editing, and autonomous agent capabilities in a single unified interface. Users can run it as a desktop app or self-host it as a web application. It supports both local AI models (via Ollama, llama.cpp) and cloud providers (OpenAI, Anthropic, Gemini, Grok) seamlessly. The integrated agent can build apps, browse the web, interact with external services, and execute multi-step tasks autonomously or with human oversight.

## Core Value

One app to replace the need for separate AI chat clients, local model managers, workflow automation tools, code editors, and AI assistants - accessible to everyone, not just developers.

## Current Milestone: v3.0 Agent

**Goal:** Transform Skynette from an AI workspace into a general-purpose AI assistant that can autonomously execute tasks, interact with external services, and build software.

**Target features:**
- Agent framework with planning, execution, and progress feedback
- MCP integration for extensible tool use
- Built-in tools: web search, browser automation, code execution
- Configurable approval levels with YOLO bypass mode
- Smart model routing (agent suggests best model per task)
- GitHub integration for project creation

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

### Active

**Agent Framework:**
- [ ] Agent planning phase (asks clarifying questions before execution)
- [ ] Agent execution loop with tool use
- [ ] Visual progress feedback (thinking indicator, status updates)
- [ ] Both autonomous (background) and interactive modes
- [ ] Configurable per-action approval levels
- [ ] YOLO bypass mode for power users

**MCP Integration:**
- [ ] MCP host implementation (connect to MCP servers)
- [ ] Support for stdio, SSE, and HTTP transports
- [ ] Tool discovery and registration from MCP servers
- [ ] Built-in MCP server management UI

**Built-in Tools:**
- [ ] Web search via search APIs (Google, Bing, etc.)
- [ ] Headless browser for complex web interactions
- [ ] Filesystem operations (read, write, create, delete)
- [ ] Code execution (extend existing node)
- [ ] GitHub integration (create repos, push code)

**AI Backend:**
- [ ] Smart model routing (suggest best model per task)
- [ ] User-configurable model defaults per task type
- [ ] Agent uses existing multi-provider gateway

**Safety & Control:**
- [ ] Action classification (safe, moderate, destructive)
- [ ] Approval workflow for flagged actions
- [ ] Audit log of agent actions
- [ ] Kill switch to stop running agent tasks

### Out of Scope

- Mobile native apps - web/desktop first, mobile can access via web
- Real-time collaboration - single-user focus, complexity too high
- Plugin marketplace - SDK exists but marketplace deferred
- Custom model training - use pre-trained models only
- Email integration - defer to MCP servers (users can add their own)
- Stock market integration - defer to MCP servers

## Context

**Current state:** Shipped v2.0 with 144,774 LOC Python across 143 files.

**Tech stack:** Python/Flet for GUI, FastAPI for webhooks, ChromaDB for RAG, Pygments for syntax highlighting, tiktoken for token counting.

**Provider support:** OpenAI, Anthropic, Gemini, Grok, Ollama, local llama.cpp

**Test coverage:** 477+ tests covering all major subsystems

**v3.0 direction:** Agent mode transforms Skynette from a tool into an assistant. Users can give it tasks ("build me an app", "research this topic", "check the news") and it executes autonomously with appropriate oversight.

**Known issues:**
- Manual CodeEditorView verification pending
- mypy not installed in dev environment

## Constraints

- **Tech stack**: Python/Flet - validated through v2.0 development
- **Deployment**: Must work as both desktop app (PyInstaller) and web app (self-hosted)
- **AI providers**: Must support OpenAI, Anthropic, Ollama, Gemini, Grok
- **Local-first**: Core features must work offline with local models
- **Open source**: All code public, self-hostable, privacy-respecting
- **Safety**: Agent actions must be auditable and controllable

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Python/Flet for GUI | Cross-platform from single codebase | ✓ Good (shipped v2.0) |
| SQLite for storage | No external database dependency | ✓ Good |
| Multi-provider gateway pattern | Easy to add new AI providers | ✓ Good (5 providers) |
| Node-based workflows | Visual, accessible to non-developers | ✓ Good |
| State container pattern | Reactive updates without external library | ✓ Good (used in AIHub, Editor) |
| Pygments for syntax highlighting | 598 languages, no Flutter wrapper complexity | ✓ Good |
| google-genai SDK for Gemini | Official SDK, async support, actively maintained | ✓ Good |
| DimensionValidator for embeddings | Prevents ChromaDB corruption from model changes | ✓ Good |
| RAG context in system prompt | Maintains conversation history integrity | ✓ Good |
| Lazy project indexing | Avoid slow startup, index on first query | ✓ Good |
| MCP for extensibility | Standard protocol, community ecosystem, future-proof | — Pending |
| Configurable approval levels | Balance autonomy with safety | — Pending |

---
*Last updated: 2026-01-20 after v3.0 milestone initialization*
