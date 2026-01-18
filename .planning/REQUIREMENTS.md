# Requirements: Skynette v2

**Defined:** 2026-01-18
**Core Value:** One app to replace separate AI chat clients, model managers, and workflow tools — accessible to everyone

## v2 Requirements

### Stability & Audit

- [x] **STAB-01**: Audit AI Chat functionality — identify and fix all bugs
- [x] **STAB-02**: Audit Model Management (local + cloud) — identify and fix all bugs
- [x] **STAB-03**: Audit Workflow Builder — identify and fix all bugs
- [x] **STAB-04**: Refactor state management to handle scale (address AIHubView complexity)
- [x] **STAB-05**: Achieve comprehensive test coverage for all existing features

### AI Providers

- [x] **PROV-01**: Add Gemini provider using `google-genai>=1.59.0` SDK
- [x] **PROV-02**: Add Grok provider using `xai-sdk>=1.5.0` SDK
- [x] **PROV-03**: Enhance Ollama with better service discovery and status UI
- [x] **PROV-04**: Implement provider-specific rate limit handling with pre-emptive throttling
- [x] **PROV-05**: Handle streaming mid-stream failures gracefully (buffer, track state, notify user)

### Code Editor — Core

- [x] **EDIT-01**: Create CodeEditor component with Pygments syntax highlighting (598 languages)
- [x] **EDIT-02**: Build CodeEditorView with toolbar and navigation
- [x] **EDIT-03**: Implement file open/save/create/delete operations
- [x] **EDIT-04**: Add file tree navigation for browsing project directories
- [x] **EDIT-05**: Support multiple open files with tabbed interface
- [x] **EDIT-06**: Implement proper resource disposal to prevent memory leaks

### Code Editor — AI Assistance

- [x] **AIED-01**: Add AI chat panel with code context awareness
- [x] **AIED-02**: Implement inline suggestions (ghost text with Tab to accept)
- [x] **AIED-03**: Add diff preview showing changes before applying
- [x] **AIED-04**: Implement accept/reject controls for AI changes
- [x] **AIED-05**: Connect editor to existing AI Gateway for completions

### Integration

- [x] **INTG-01**: Enable workflow script editing in code editor
- [x] **INTG-02**: Implement project-level RAG for codebase context (leverage ChromaDB)
- [x] **INTG-03**: Add code execution node for running snippets in workflows
- [x] **INTG-04**: Validate embedding dimensions before writes (prevent RAG corruption)

### Quality

- [x] **QUAL-01**: Unit tests for all new provider integrations
- [x] **QUAL-02**: Unit tests for code editor components
- [x] **QUAL-03**: Integration tests for AI-assisted editing flow
- [x] **QUAL-04**: E2E tests for critical user journeys
- [x] **QUAL-05**: Security audit — ensure API keys not exposed in memory

## v2+ Requirements (Deferred)

### Advanced AI Features

- **ADVN-01**: Agent mode for autonomous coding tasks (requires safety testing)
- **ADVN-02**: Next edit prediction with fine-tuned models
- **ADVN-03**: MCP tool integration (wait for standard stability)

### Platform Expansion

- **PLAT-01**: Mobile-optimized code editor (Monaco doesn't support mobile)
- **PLAT-02**: Plugin marketplace launch
- **PLAT-03**: Collaborative editing (multi-user)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Mobile native apps | Web/desktop first; mobile can access via web |
| Real-time collaboration | Single-user focus for v2; complexity too high |
| Plugin marketplace | SDK exists but marketplace deferred to v2+ |
| Custom model training | Use pre-trained models only |
| Agent mode | Requires extensive safety testing; defer to v2+ |
| MCP integration | Emerging standard; wait for stability |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| STAB-01 | Phase 1 | Complete |
| STAB-02 | Phase 1 | Complete |
| STAB-03 | Phase 1 | Complete |
| STAB-04 | Phase 1 | Complete |
| STAB-05 | Phase 5 | Complete |
| PROV-01 | Phase 2 | Complete |
| PROV-02 | Phase 2 | Complete |
| PROV-03 | Phase 2 | Complete |
| PROV-04 | Phase 2 | Complete |
| PROV-05 | Phase 2 | Complete |
| QUAL-01 | Phase 2 | Complete |
| EDIT-01 | Phase 3 | Complete |
| EDIT-02 | Phase 3 | Complete |
| EDIT-03 | Phase 3 | Complete |
| EDIT-04 | Phase 3 | Complete |
| EDIT-05 | Phase 3 | Complete |
| EDIT-06 | Phase 3 | Complete |
| QUAL-02 | Phase 3 | Complete |
| AIED-01 | Phase 4 | Complete |
| AIED-02 | Phase 4 | Complete |
| AIED-03 | Phase 4 | Complete |
| AIED-04 | Phase 4 | Complete |
| AIED-05 | Phase 4 | Complete |
| QUAL-03 | Phase 4 | Complete |
| INTG-01 | Phase 5 | Complete |
| INTG-02 | Phase 5 | Complete |
| INTG-03 | Phase 5 | Complete |
| INTG-04 | Phase 5 | Complete |
| QUAL-04 | Phase 5 | Complete |
| QUAL-05 | Phase 5 | Complete |

**Coverage:**
- v2 requirements: 30 total
- Mapped to phases: 30
- Unmapped: 0

---
*Requirements defined: 2026-01-18*
*Last updated: 2026-01-19 — v2 complete*
