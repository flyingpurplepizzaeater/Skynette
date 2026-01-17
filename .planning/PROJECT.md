# Skynette

## What This Is

An all-in-one, open-source AI workspace that combines chat, model management, and workflow automation in a single unified interface. Users can run it as a desktop app or self-host it as a web application. It supports both local AI models (via Ollama, llama.cpp) and cloud providers (OpenAI, Anthropic, Gemini, Grok) seamlessly.

## Core Value

One app to replace the need for separate AI chat clients, local model managers, and workflow automation tools — accessible to everyone, not just developers.

## Requirements

### Validated

- ✓ Flet-based cross-platform GUI (desktop + web) — existing
- ✓ Node-based workflow automation engine with visual editor — existing
- ✓ Multi-provider AI gateway with auto-fallback — existing
- ✓ OpenAI provider integration (GPT-4, embeddings) — existing
- ✓ Anthropic provider integration (Claude) — existing
- ✓ Local model support via llama.cpp (GGUF models) — existing
- ✓ RAG subsystem with ChromaDB for knowledge bases — existing
- ✓ Scheduled and trigger-based workflow execution — existing
- ✓ Expression system for dynamic workflow values — existing
- ✓ Credential encryption and secure storage — existing
- ✓ SQLite + YAML hybrid storage — existing

### Active

- [ ] Audit and stabilize AI Chat functionality
- [ ] Audit and stabilize Model Management (local + cloud)
- [ ] Audit and stabilize Workflow Builder
- [ ] Add Gemini provider integration
- [ ] Add Grok provider integration
- [ ] Add Ollama provider integration (distinct from llama.cpp)
- [ ] Implement integrated code editor with AI assistance
- [ ] Implement workflow script editing in code editor
- [ ] General-purpose coding capabilities in editor
- [ ] Comprehensive test coverage for all features
- [ ] Fix all bugs discovered during audit

### Out of Scope

- Mobile native apps — web/desktop first, mobile can access via web
- Real-time collaboration — single-user focus for v2
- Plugin marketplace — SDK exists but marketplace deferred
- Custom model training — use pre-trained models only

## Context

**Existing codebase:** ~50+ Python files with layered architecture (UI, Core, AI, RAG, Data layers). Uses Flet for GUI, FastAPI for webhooks, Pydantic for validation.

**Inspirations:** Aims to combine the best of:
- Open WebUI (chat interface, model management)
- LM Studio (local model experience)
- n8n / Make (visual workflow automation)

**Current state:** Uncertain — comprehensive audit needed to understand what works, what's broken, and what's incomplete.

**Target users:** Everyone — from developers wanting AI-integrated workflows to non-technical users who want a simple AI chat.

## Constraints

- **Tech stack**: Python/Flet currently, open to changes if justified
- **Deployment**: Must work as both desktop app (PyInstaller) and web app (self-hosted)
- **AI providers**: Must support OpenAI, Anthropic, Ollama, Gemini, Grok
- **Local-first**: Core features must work offline with local models
- **Open source**: All code public, self-hostable, privacy-respecting

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Python/Flet for GUI | Cross-platform from single codebase | — Pending (open to revisit) |
| SQLite for storage | No external database dependency | ✓ Good |
| Multi-provider gateway pattern | Easy to add new AI providers | ✓ Good |
| Node-based workflows | Visual, accessible to non-developers | ✓ Good |

---
*Last updated: 2026-01-17 after initialization*
