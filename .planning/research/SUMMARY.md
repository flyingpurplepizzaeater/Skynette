# Research Summary - Skynette Milestone 2

**Project:** Skynette AI Workspace - Code Editor and Provider Expansion
**Synthesized:** 2026-01-18
**Overall Confidence:** HIGH

---

## Executive Summary

Skynette Milestone 2 adds a code editor with AI assistance and expands the provider ecosystem to include Gemini and Grok. Research confirms this is achievable with moderate complexity. The existing architecture (layered design, provider abstraction via `BaseProvider`, AI Gateway with fallback) provides a solid foundation. New providers follow the established pattern with minimal friction.

The code editor should be built as a custom Flet control using Pygments for syntax highlighting - this avoids the complexity of wrapping Flutter packages while providing sufficient capability for AI-assisted editing. The Gemini provider requires the new `google-genai` SDK (the old `google-generativeai` is deprecated as of November 2025), while Grok uses the official `xai-sdk`. Both SDKs are production-ready and well-documented.

Key risks center on streaming error handling (mid-stream failures corrupt state), embedding dimension mismatches (breaks RAG if providers switch), and Flet state management at scale (already showing strain in AIHubView at 1669 lines). The code editor must build in resource disposal from day one to prevent memory leaks from editor instances.

---

## Key Findings

### From STACK.md

| Technology | Version | Purpose | Confidence |
|------------|---------|---------|------------|
| **Pygments** | >=2.19.2 | Syntax highlighting (598 languages) | HIGH |
| **google-genai** | >=1.59.0 | Gemini API - replaces deprecated google-generativeai | HIGH |
| **xai-sdk** | >=1.5.0 | Grok API - official xAI SDK | HIGH |
| **httpx** | >=0.27.0 | Keep for Ollama (already working) | HIGH |

**Critical:** The `google-generativeai` package is deprecated (EOL November 2025). Must use `google-genai` instead.

**Dependencies to add:**
```txt
Pygments>=2.19.2
google-genai>=1.59.0
xai-sdk>=1.5.0
```

### From FEATURES.md

**Table Stakes (must have for MVP):**
1. Syntax highlighting with multi-language support
2. AI inline suggestions (ghost text, Tab to accept)
3. AI chat panel with code context
4. Model selection dropdown
5. Diff preview for AI changes
6. Accept/Reject controls
7. File tree navigation

**Differentiators (Skynette advantages):**
1. **Workflow-integrated editing** - No competitor combines workflow automation with code editing
2. **Multi-provider auto-fallback** - Already exists in AI Gateway, extend to editor
3. **Codebase RAG** - Leverage existing ChromaDB for project-wide context
4. **Local-first AI** - Ollama for offline/privacy (differentiates from Cursor/Copilot)

**Defer to v2+:**
- Agent mode (requires extensive safety testing)
- Next edit prediction (requires fine-tuned models)
- MCP tool integration (emerging standard, wait for stability)

### From ARCHITECTURE.md

**Pattern:** Code editor as new top-level view following existing patterns:

```
CodeEditorView
  |-- EditorPane (text editing, syntax display)
  |-- AIAssistPanel (chat interface for code help)
  |-- FileExplorer (file system navigation)
  |-- CodeSessionManager (open files, undo history)
```

**Provider addition pattern:**
```python
class GeminiProvider(BaseProvider):
    name = "gemini"
    capabilities = {AICapability.CHAT, AICapability.CODE_GENERATION}
    # Uses google-genai SDK
```

**Build order from architecture analysis:**
1. Provider Foundation (Gemini, Grok following existing pattern)
2. Code Editor Core (syntax highlighting, file operations)
3. AI-Assisted Features (connect to gateway, completions)
4. Advanced Integration (workflow scripts, RAG)

### From PITFALLS.md

**Critical Pitfalls (cause rewrites/data corruption):**

| Pitfall | Phase | Prevention |
|---------|-------|------------|
| **Embedding dimension mismatch** | RAG | Validate dimensions before writes, store model metadata |
| **Streaming mid-stream failures** | Providers | Buffer responses, track partial state, user feedback |
| **API key memory exposure** | Security | Store to keyring immediately, clear variables |

**Moderate Pitfalls (cause delays/debt):**

| Pitfall | Phase | Prevention |
|---------|-------|------------|
| **Provider-specific rate limits** | Providers | Parse provider headers, pre-emptive throttling |
| **Ollama service discovery** | Providers | Health check on start, clear status UI |
| **Code editor resource leaks** | Editor | Explicit dispose(), limit instances, lazy load |
| **Flet state management** | Editor | Centralize state, smaller components |

---

## Implications for Roadmap

### Suggested Phase Structure

**Phase 1: Provider Foundation**
- Add Gemini provider using `google-genai` SDK
- Add Grok provider using `xai-sdk`
- Implement provider-specific rate limit handling
- Enhance Ollama service discovery with clear status UI

*Rationale:* Providers are independent of code editor and unblock AI features. Low risk, follows established patterns exactly.

*Pitfalls to avoid:* Rate limit handling (#6), Ollama discovery (#7), streaming failures (#2)

*Research needed:* LOW - SDKs are well-documented, patterns exist

---

**Phase 2: Code Editor Core**
- Create `CodeEditor` component with Pygments highlighting
- Build `CodeEditorView` with toolbar, file tabs
- Implement file open/save/navigation
- Add to main app navigation

*Rationale:* Foundation for all AI-assisted editing. Must be solid before adding AI features.

*Pitfalls to avoid:* Resource management (#5), mobile incompatibility (#10), state management (#4)

*Research needed:* MEDIUM - Custom Flet control patterns need validation

---

**Phase 3: AI-Assisted Editing**
- Add `AIAssistPanel` component
- Connect editor to AI Gateway for completions
- Implement inline suggestions (ghost text)
- Add diff preview with accept/reject

*Rationale:* Core value proposition. Requires Phase 1 (providers) and Phase 2 (editor).

*Pitfalls to avoid:* Streaming failures (#2), thread safety (#9)

*Research needed:* LOW - Follows chat panel patterns already in Skynette

---

**Phase 4: Advanced Integration**
- Workflow script editing in code editor
- Project-level RAG for code context
- Code execution node for workflows

*Rationale:* Differentiators that leverage existing Skynette infrastructure.

*Pitfalls to avoid:* Embedding dimension mismatch (#1)

*Research needed:* HIGH - RAG for code has different chunking needs

---

### Research Flags

| Phase | Needs `/gsd:research-phase`? | Rationale |
|-------|------------------------------|-----------|
| Phase 1 | NO | SDKs documented, patterns exist |
| Phase 2 | YES | Custom Flet code editor is novel |
| Phase 3 | NO | Extends existing chat patterns |
| Phase 4 | YES | Code RAG chunking strategies |

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All packages verified on PyPI, official SDKs |
| Features | HIGH | Based on competitor analysis, Context7 verification |
| Architecture | HIGH | Based on existing codebase analysis |
| Pitfalls | MEDIUM | Mix of verified issues and extrapolated patterns |

### Gaps to Address During Planning

1. **Flet code editor performance** - No benchmarks for Pygments+Flet with large files (1000+ lines)
2. **Grok rate limits** - Newer API, limits less documented than OpenAI/Anthropic
3. **Mobile code editor strategy** - Monaco doesn't support mobile; need alternative approach
4. **State management refactor** - Current patterns won't scale; need to decide on approach before editor adds more complexity

---

## Sources (Aggregated)

### Official Documentation (HIGH confidence)
- [Google GenAI SDK](https://googleapis.github.io/python-genai/)
- [xAI Grok API](https://docs.x.ai/docs/overview)
- [Pygments](https://pygments.org/)
- [Flet Documentation](https://flet.dev/docs/)
- [Ollama API](https://github.com/ollama/ollama)

### PyPI Packages (HIGH confidence)
- google-genai v1.59.0
- xai-sdk v1.5.0
- Pygments v2.19.2

### Industry Analysis (MEDIUM confidence)
- Cursor, Continue.dev, Copilot feature comparisons
- Monaco Editor GitHub issues
- Flet community discussions

### Deprecation Notices (HIGH confidence)
- google-generativeai deprecated November 2025
- vertexai.generative_models removal June 2026

---

*Research synthesis completed: 2026-01-18*
