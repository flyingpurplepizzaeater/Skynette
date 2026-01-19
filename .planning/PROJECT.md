# Skynette

## What This Is

An all-in-one, open-source AI workspace that combines chat, model management, workflow automation, and code editing in a single unified interface. Users can run it as a desktop app or self-host it as a web application. It supports both local AI models (via Ollama, llama.cpp) and cloud providers (OpenAI, Anthropic, Gemini, Grok) seamlessly. The integrated code editor provides AI-assisted development with syntax highlighting, inline suggestions, and RAG-powered codebase awareness.

## Core Value

One app to replace the need for separate AI chat clients, local model managers, workflow automation tools, and code editors - accessible to everyone, not just developers.

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

(None - define with `/gsd:new-milestone`)

### Out of Scope

- Mobile native apps - web/desktop first, mobile can access via web
- Real-time collaboration - single-user focus, complexity too high
- Plugin marketplace - SDK exists but marketplace deferred
- Custom model training - use pre-trained models only
- Agent mode - requires extensive safety testing
- MCP integration - emerging standard, wait for stability

## Context

**Current state:** Shipped v2.0 with 144,774 LOC Python across 143 files.

**Tech stack:** Python/Flet for GUI, FastAPI for webhooks, ChromaDB for RAG, Pygments for syntax highlighting, tiktoken for token counting.

**Provider support:** OpenAI, Anthropic, Gemini, Grok, Ollama, local llama.cpp

**Test coverage:** 477+ tests covering all major subsystems

**Known issues:**
- Manual CodeEditorView verification pending
- mypy not installed in dev environment

## Constraints

- **Tech stack**: Python/Flet - validated through v2.0 development
- **Deployment**: Must work as both desktop app (PyInstaller) and web app (self-hosted)
- **AI providers**: Must support OpenAI, Anthropic, Ollama, Gemini, Grok
- **Local-first**: Core features must work offline with local models
- **Open source**: All code public, self-hostable, privacy-respecting

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

---
*Last updated: 2026-01-20 after v2.0 milestone*
