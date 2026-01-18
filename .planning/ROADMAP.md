# Roadmap: Skynette v2

## Overview

Skynette v2 transforms the AI workspace from a chat-and-workflow tool into a complete development environment with an AI-assisted code editor and expanded provider support. The journey begins with stabilizing what exists (audit and fix), then expands the provider ecosystem (Gemini, Grok, Ollama improvements), builds a code editor foundation (syntax, files, navigation), adds AI assistance to the editor (completions, diff preview), and culminates in advanced integrations (workflow scripts in editor, codebase RAG, comprehensive testing).

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3, 4, 5): Planned milestone work
- Decimal phases (e.g., 2.1): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Stability & Audit** - Fix what is broken before building new
- [x] **Phase 2: Provider Foundation** - Gemini, Grok, and Ollama improvements
- [x] **Phase 3: Code Editor Core** - Syntax highlighting, file operations, navigation
- [x] **Phase 4: AI-Assisted Editing** - Completions, diff preview, accept/reject
- [ ] **Phase 5: Advanced Integration** - Workflow scripts, RAG, execution node, final tests

## Phase Details

### Phase 1: Stability & Audit
**Goal**: Existing features work reliably before adding new capabilities
**Depends on**: Nothing (first phase)
**Requirements**: STAB-01, STAB-02, STAB-03, STAB-04
**Success Criteria** (what must be TRUE):
  1. User can send messages in AI Chat and receive responses without errors
  2. User can list, add, and switch between local and cloud AI models
  3. User can create, save, and execute workflows without crashes
  4. AIHubView state management handles large conversation histories without degradation
**Plans**: 4 plans in 2 waves

Plans:
- [x] 01-01-PLAN.md - Audit AI Chat functionality (STAB-01)
- [x] 01-02-PLAN.md - Audit Model Management (STAB-02)
- [x] 01-03-PLAN.md - Audit Workflow Builder (STAB-03)
- [x] 01-04-PLAN.md - Refactor AIHubView state management (STAB-04)

### Phase 2: Provider Foundation
**Goal**: Users can access Gemini, Grok, and improved Ollama alongside existing providers
**Depends on**: Phase 1 (stable foundation required)
**Requirements**: PROV-01, PROV-02, PROV-03, PROV-04, PROV-05, QUAL-01
**Success Criteria** (what must be TRUE):
  1. User can select and chat with Gemini models via google-genai SDK
  2. User can select and chat with Grok models via xai-sdk
  3. User can see Ollama connection status and available models in UI
  4. User receives clear feedback when rate limits are approached (pre-emptive throttling)
  5. User sees graceful error messages when streaming fails mid-response (no corrupt state)
**Plans**: 5 plans in 4 waves

Plans:
- [x] 02-01-PLAN.md - Implement Gemini provider (PROV-01)
- [x] 02-02-PLAN.md - Implement Grok provider (PROV-02)
- [x] 02-03-PLAN.md - Enhance Ollama service discovery and status UI (PROV-03)
- [x] 02-04-PLAN.md - Implement rate limit handling and streaming failure recovery (PROV-04, PROV-05)
- [x] 02-05-PLAN.md - Unit tests for provider integrations (QUAL-01)

### Phase 3: Code Editor Core
**Goal**: Users can open, edit, and save code files with syntax highlighting
**Depends on**: Phase 1 (stable app shell required)
**Requirements**: EDIT-01, EDIT-02, EDIT-03, EDIT-04, EDIT-05, EDIT-06, QUAL-02
**Success Criteria** (what must be TRUE):
  1. User can open a file and see syntax-highlighted code (Python, JavaScript, etc.)
  2. User can edit text, save changes, and confirm file is updated on disk
  3. User can browse project directories via file tree and open files by clicking
  4. User can open multiple files in tabs and switch between them
  5. User can close files/tabs without memory leaks (proper resource disposal)
**Plans**: 5 plans in 4 waves

Plans:
- [x] 03-01-PLAN.md - Core editor services (Pygments highlighter, file I/O, icons)
- [x] 03-02-PLAN.md - EditorState and CodeEditor component with line numbers
- [x] 03-03-PLAN.md - FileTree and ResizableSplitPanel components
- [x] 03-04-PLAN.md - TabBar, Toolbar, CodeEditorView assembly, app navigation
- [x] 03-05-PLAN.md - Resource disposal and unit tests (QUAL-02)

### Phase 4: AI-Assisted Editing
**Goal**: Users can get AI help while coding, with suggestions they can accept or reject
**Depends on**: Phase 2 (providers), Phase 3 (editor)
**Requirements**: AIED-01, AIED-02, AIED-03, AIED-04, AIED-05, QUAL-03
**Success Criteria** (what must be TRUE):
  1. User can open AI chat panel in editor and ask questions about their code
  2. User sees inline suggestions (ghost text) and can press Tab to accept
  3. User can preview AI-suggested changes as a diff before applying
  4. User can accept or reject AI changes with clear controls
  5. User can select any configured AI provider for completions
**Plans**: 6 plans in 4 waves

Plans:
- [x] 04-01-PLAN.md - Foundation services (ChatState, TokenCounter, DiffService)
- [x] 04-02-PLAN.md - Chat panel component with streaming responses
- [x] 04-03-PLAN.md - Ghost text suggestions with completion service
- [x] 04-04-PLAN.md - Diff preview with accept/reject controls
- [x] 04-05-PLAN.md - CodeEditorView integration and keyboard shortcuts

### Phase 5: Advanced Integration
**Goal**: Code editor integrates with workflow automation and codebase knowledge
**Depends on**: Phase 4 (complete editor with AI)
**Requirements**: INTG-01, INTG-02, INTG-03, INTG-04, STAB-05, QUAL-04, QUAL-05
**Success Criteria** (what must be TRUE):
  1. User can edit workflow scripts directly in the code editor
  2. User can ask AI questions that are informed by their codebase context (RAG)
  3. User can add a code execution node to workflows that runs snippets
  4. RAG writes are validated for embedding dimension consistency (no corruption)
  5. Critical user journeys pass E2E tests, security audit confirms no API key exposure
**Plans**: TBD

Plans:
- [ ] 05-01: Enable workflow script editing in code editor
- [ ] 05-02: Implement project-level RAG for codebase context
- [ ] 05-03: Add code execution node for workflows
- [ ] 05-04: Comprehensive test coverage (E2E, security audit)

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Stability & Audit | 4/4 | Complete | 2026-01-18 |
| 2. Provider Foundation | 5/5 | Complete | 2026-01-18 |
| 3. Code Editor Core | 5/5 | Complete | 2026-01-18 |
| 4. AI-Assisted Editing | 5/5 | Complete | 2026-01-18 |
| 5. Advanced Integration | 0/4 | Not started | - |

---
*Roadmap created: 2026-01-18*
*Last updated: 2026-01-18*
