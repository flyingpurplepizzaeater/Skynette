# Domain Pitfalls: AI Workspace with Code Editor and Multi-Provider Integration

**Project:** Skynette
**Domain:** All-in-one AI workspace with code editor, multi-provider AI gateway, Flet GUI
**Researched:** 2026-01-18
**Overall Confidence:** MEDIUM (verified against multiple sources, project codebase, and industry patterns)

---

## Critical Pitfalls

Mistakes that cause rewrites, data corruption, or major architectural issues.

---

### Pitfall 1: Embedding Dimension Mismatch Across Providers

**What goes wrong:** When switching embedding models or providers (e.g., OpenAI text-embedding-3-small at 1536 dimensions vs. local sentence-transformers at 384 dimensions), existing vector databases become incompatible. ChromaDB enforces consistent dimensions, causing cryptic errors or silent failures.

**Why it happens:**
- Different providers use different embedding dimensions by default
- Model updates change dimensions (OpenAI's text-embedding-3 supports custom dimensions but defaults changed)
- Documentation doesn't clearly warn about this
- Local models (nomic-embed-text at 768, all-MiniLM-L6-v2 at 384) differ from cloud defaults

**Consequences:**
- Complete RAG system failure
- Requirement to re-index all documents
- Data loss if old embeddings not recoverable
- Silent retrieval failures returning wrong results

**Warning signs:**
- "Dimension mismatch" errors from ChromaDB
- RAG queries returning empty or irrelevant results after provider changes
- New documents not being found despite successful indexing

**Prevention:**
1. Store embedding model info alongside vector collections
2. Validate dimension compatibility before any write operation
3. Version your vector database schema with model metadata
4. Use migration scripts when changing embedding models
5. Default to a single embedding provider (Skynette uses sentence-transformers locally - keep this consistent)

**Detection (code review checklist):**
```python
# BAD: No dimension validation
await chroma_collection.add(documents=docs, embeddings=embeddings)

# GOOD: Validate before write
expected_dim = collection.metadata.get("embedding_dimension")
if embeddings[0] and len(embeddings[0]) != expected_dim:
    raise DimensionMismatchError(f"Expected {expected_dim}, got {len(embeddings[0])}")
```

**Phase to address:** Foundation/Infrastructure phase - before any multi-provider embedding work

**Confidence:** HIGH - Verified in [CrewAI Issue #2464](https://github.com/crewAIInc/crewAI/issues/2464), [Open WebUI Discussion #9609](https://github.com/open-webui/open-webui/discussions/9609), and multiple Medium articles documenting this exact issue.

---

### Pitfall 2: Streaming Response Mid-Stream Failures

**What goes wrong:** When AI providers fail mid-stream (network timeout, token limit, provider error), partial responses are delivered without proper error handling. Users see incomplete AI responses, and the application state becomes inconsistent.

**Why it happens:**
- HTTP status code already sent (200 OK) before failure occurs
- Different providers have different mid-stream error semantics
- Fallback mechanisms don't work during streaming (can't switch providers mid-response)
- No checkpointing for resumable streams

**Consequences:**
- Incomplete responses shown to users
- Conversation history corrupted with partial messages
- Token counting becomes inaccurate
- Cost tracking is wrong

**Warning signs:**
- Messages ending abruptly without finish_reason
- "stream interrupted" errors in logs
- Inconsistent token counts vs. actual content length
- Users reporting "AI stopped responding mid-sentence"

**Prevention:**
1. Buffer streaming responses before displaying (show after sentence boundaries)
2. Track expected vs. actual token counts
3. Implement retry at conversation level, not stream level
4. Store partial responses with "incomplete" flag
5. Give users clear "response interrupted" UI feedback

**Skynette-specific fix in `src/ai/gateway.py`:**
```python
# Current code (line 234-237) has no fallback during streaming:
# Try first available provider (no fallback during streaming)
p = providers[0]
async for chunk in p.chat_stream(messages, config):
    yield chunk

# Should add: error detection, partial response tracking, user notification
```

**Phase to address:** Provider Integration phase - when implementing new providers

**Confidence:** HIGH - Verified in [OpenRouter docs](https://openrouter.ai/docs/api/reference/streaming), [Vercel AI SDK docs](https://ai-sdk.dev/docs/reference/ai-sdk-core/stream-text), and analysis at [michaellivs.com](https://michaellivs.com/blog/open-responses-missing-spec).

---

### Pitfall 3: Provider API Key Storage in Memory During Setup

**What goes wrong:** API keys entered during setup wizard remain in plain memory until wizard completion. If the app crashes, keys may be logged, dumped to crash reports, or exposed through memory inspection.

**Why it happens:**
- Wizard needs to validate keys before saving
- Multi-step wizards accumulate state
- Convenience of testing keys before committing

**Consequences:**
- API key exposure in crash dumps
- Keys in memory longer than necessary
- Security audit failures

**Warning signs:**
- API keys appearing in logs
- Keys visible in debugger memory inspection
- Keys persisting after wizard cancelled

**Prevention:**
1. Store keys to keyring immediately upon entry (not on wizard completion)
2. Clear key variables after storage
3. Use secure string types where available
4. Never log key values, only key presence

**Skynette already flagged this in CONCERNS.md:**
> "API Key Storage in Memory During Wizard: Provider configs are stored in plain memory (`self.provider_configs`) before completion"

**Phase to address:** Stability/Security phase

**Confidence:** HIGH - Already identified in codebase audit.

---

### Pitfall 4: Flet State Management at Scale

**What goes wrong:** Flet's imperative UI model becomes unmanageable as the application grows. State scattered across class variables, inconsistent update patterns, and no clear state ownership leads to UI bugs.

**Why it happens:**
- Flet requires explicit `page.update()` calls
- No built-in reactive state management
- Complex wizard flows (like AI Hub setup) accumulate state
- Multiple views share state without coordination

**Consequences:**
- UI not reflecting actual state
- Race conditions during async operations
- Difficult debugging of "why isn't it updating?"
- Maintenance burden increases exponentially with features

**Warning signs:**
- Need to call `page.update()` in many places
- UI shows stale data after operations
- State accessed from multiple places inconsistently
- Large class files (AI Hub is 1669 lines)

**Prevention:**
1. Centralize state in dedicated state classes
2. Use Flet's upcoming declarative mode (v1.0+)
3. Create update helper that consolidates state sync
4. Extract complex views into smaller components
5. Use Pydantic models for state validation

**Example pattern:**
```python
# BAD: Scattered state
class AIHubView:
    def __init__(self):
        self.wizard_step = 0
        self.selected_providers = []
        self.provider_configs = {}  # Multiple state variables

# BETTER: Centralized state
@dataclass
class WizardState:
    step: int = 0
    selected_providers: list[str] = field(default_factory=list)
    provider_configs: dict = field(default_factory=dict)

class AIHubView:
    def __init__(self):
        self.state = WizardState()
```

**Phase to address:** Code Editor Integration phase (prevent new code from inheriting bad patterns)

**Confidence:** MEDIUM - Based on [Flet discussions](https://github.com/flet-dev/flet/discussions/1020) and [Flet 1.0 beta announcement](https://flet.dev/blog/) acknowledging imperative approach limitations.

---

### Pitfall 5: Code Editor Resource Management

**What goes wrong:** Code editors (Monaco, Ace, CodeMirror) have significant memory footprints and don't clean up properly when components unmount. Multiple editor instances accumulate, leading to memory leaks and performance degradation.

**Why it happens:**
- Editors create DOM elements, event listeners, language workers
- Python-to-JavaScript bridge (in Flet) makes cleanup coordination difficult
- Tab-based interfaces may instantiate editors that aren't visible
- Custom completions, syntax handlers create additional references

**Consequences:**
- Memory grows unbounded over session
- Performance degrades as more files opened
- Browser/app becomes unresponsive
- Eventual crash

**Warning signs:**
- Memory usage climbing in Task Manager
- Slow response when switching tabs
- JavaScript errors about "disposed" objects
- Input lag in editor

**Prevention:**
1. Implement explicit dispose() on all editor instances
2. Lazy-load editors (only when tab actually visible)
3. Limit concurrent editor instances (close old tabs)
4. Monitor memory and warn users
5. Use worker pools instead of per-editor workers

**Monaco-specific from official GitHub:**
> "One important thing to be aware of is not forgetting to free all the custom handlers registered via Monaco languages API. Methods like addAction or registerCompletionItemProvider return an object implementing disposable interface."

**Phase to address:** Code Editor Integration phase - build disposal into architecture from start

**Confidence:** HIGH - Verified in [Monaco GitHub issues](https://github.com/microsoft/monaco-editor/issues/619), [Spectral blog](https://blog.spectralcore.com/integrating-monaco-editor/), and [Replit comparison](https://blog.replit.com/code-editors).

---

## Moderate Pitfalls

Mistakes that cause delays, technical debt, or degraded user experience.

---

### Pitfall 6: Provider-Specific Rate Limit Handling

**What goes wrong:** Each AI provider (OpenAI, Anthropic, Gemini, Grok, Ollama) has different rate limiting semantics. Generic retry logic fails or wastes credits.

**Why it happens:**
- OpenAI: per-minute and per-day limits, different by model tier
- Anthropic: token-based throttling
- Gemini: request-based with free tier limits
- Grok: newer API, limits less documented
- Ollama: local, but context-window limits

**Consequences:**
- Wasted API credits on retries that won't succeed
- User sees confusing error messages
- Fallback triggers unnecessarily
- Cost tracking inaccurate

**Warning signs:**
- 429 errors with varying retry-after headers
- Successful requests followed immediately by failures
- Inconsistent behavior across providers

**Prevention:**
1. Implement per-provider rate limit tracking
2. Parse provider-specific rate limit headers
3. Queue requests based on known limits
4. Show user-friendly "rate limited" status per provider
5. Pre-emptively pause before hitting limits

**Skynette gateway currently lacks this:**
```python
# src/ai/gateway.py lines 151-163 - generic fallback, no rate limit awareness
for p in providers:
    try:
        response = await p.generate(prompt, config)
        # ... success handling
    except Exception as e:
        last_error = e
        if not self.auto_fallback:
            raise
        continue  # No distinction between rate limit vs other errors
```

**Phase to address:** Provider Integration phase

**Confidence:** HIGH - Well-documented across [Portkey blog](https://portkey.ai/blog/tackling-rate-limiting-for-llm-apps/), [orq.ai](https://orq.ai/blog/api-rate-limit), and [TrueFoundry](https://www.truefoundry.com/blog/rate-limiting-in-llm-gateway).

---

### Pitfall 7: Ollama Service Discovery Failures

**What goes wrong:** Ollama runs as a separate service. App assumes it's available at localhost:11434 but fails silently or confusingly when Ollama isn't running, is on a different port, or hasn't pulled any models.

**Why it happens:**
- Ollama is a separate install
- Users might start Skynette before Ollama
- Docker deployments may use different URLs
- No models pulled = available but useless

**Consequences:**
- "Local AI" appears broken
- Users think the app is at fault
- Silent fallback to cloud (unexpected costs)
- No clear error guidance

**Warning signs:**
- Connection timeouts to localhost:11434
- "No model available" errors
- Model list returns empty

**Prevention:**
1. Health check Ollama on app start
2. Clear UI indicator for Ollama status (already partially implemented in `AIHubView`)
3. Guide users to install/start Ollama if missing
4. Allow custom Ollama URL configuration
5. Distinguish "Ollama not running" from "no models pulled"

**Skynette already has status tracking but needs improvement:**
```python
# src/ui/views/ai_hub.py lines 28-29
self.ollama_status_icon = None
self.ollama_status_text = None
# These exist but connection testing is stub
```

**Phase to address:** Provider Integration phase (Ollama provider)

**Confidence:** HIGH - Verified in [Ollama troubleshooting docs](https://docs.ollama.com/api/errors) and [Open-WebUI setup guide](https://medium.com/@Tan1pawat/setting-up-open-webui-with-ollama-gemini-api-and-groq-on-fedora-27285471c70d).

---

### Pitfall 8: Flet Build and Packaging Failures

**What goes wrong:** `flet build` gets stuck at "Packaging Python app" or produces non-functional executables. Platform-specific issues derail releases.

**Why it happens:**
- Flet packaging depends on Flutter, Dart, and serious_python
- Version mismatches between components
- Windows-specific subprocess issues
- Large dependency trees exceed limits

**Consequences:**
- Unable to ship desktop versions
- Inconsistent behavior between dev and production
- Slow startup times after packaging

**Warning signs:**
- Build hangs indefinitely
- "Packaging Python app..." with no progress
- Built app starts slowly (5-6 seconds)
- Missing dependencies at runtime

**Prevention:**
1. Pin Flet version and test builds after every upgrade
2. Use `flet pack` for simpler builds when possible
3. Keep dependency tree minimal
4. Test builds on clean VMs
5. Use CI for automated build testing

**Already documented in CONCERNS.md:**
> "Build Script Platform TODOs: NSIS/Inno Setup for Windows and AppImage for Linux not yet implemented"

**Phase to address:** Release/Polish phase

**Confidence:** HIGH - Verified in [Flet GitHub issues #5507](https://github.com/flet-dev/flet/issues/5507), [#4687](https://github.com/flet-dev/flet/issues/4687).

---

### Pitfall 9: Thread Safety in Async/GUI Hybrid

**What goes wrong:** Flet uses a main thread for UI while async operations run in event loops. Crossing these boundaries incorrectly causes crashes, UI freezes, or subtle data corruption.

**Why it happens:**
- AI provider calls are async
- File operations may block
- Flet controls must be updated from correct thread
- Python threading + asyncio + GUI = complex

**Consequences:**
- Random crashes
- UI freezes during AI calls
- Race conditions in state updates
- Memory leaks from orphaned threads

**Warning signs:**
- "RuntimeError: Event loop is running" errors
- UI not updating until operation completes
- Inconsistent behavior between runs

**Prevention:**
1. Use `asyncio.run_coroutine_threadsafe()` for cross-thread async calls
2. Always update Flet controls via `page.update()` on main thread
3. Use thread-safe queues for producer-consumer patterns
4. Avoid mixing threading and asyncio unless necessary
5. Profile for memory growth during long sessions

**Phase to address:** Stability phase - audit all async/threading patterns

**Confidence:** MEDIUM - Based on [Python bug tracker issues](https://bugs.python.org/issue43375), [discuss.python.org threading discussions](https://discuss.python.org/t/threading-memory-bug-in-windows-not-macos-or-linux/24605), and Qt/Tkinter threading documentation.

---

### Pitfall 10: Code Editor Mobile Incompatibility

**What goes wrong:** Monaco Editor explicitly doesn't support mobile browsers. Users accessing Skynette web version from tablets/phones get broken code editor or complete failure.

**Why it happens:**
- Monaco was designed for desktop browsers
- Touch interactions differ from mouse
- Mobile viewports too small for IDE-style UI
- Virtual keyboards conflict with editor shortcuts

**Consequences:**
- Unusable code editor on mobile
- Crashes or blank screens
- User perception of "broken app"

**Warning signs:**
- Touch events not registering
- Viewport scaling issues
- Keyboard not appearing or conflicting

**Prevention:**
1. Detect mobile and show warning/alternative UI
2. Consider CodeMirror 6 (better mobile support) for mobile
3. Provide read-only code view on mobile
4. Disable editor features that don't work on touch
5. Document mobile limitations clearly

**From Monaco official docs:**
> "The Monaco editor is not supported in mobile browsers or mobile devices."

**Phase to address:** Code Editor Integration phase - design decision upfront

**Confidence:** HIGH - [Official Monaco documentation](https://microsoft.github.io/monaco-editor/) and [Replit blog comparison](https://blog.replit.com/code-editors).

---

## Minor Pitfalls

Mistakes that cause annoyance or minor technical debt.

---

### Pitfall 11: Provider Model List Staleness

**What goes wrong:** Cached model lists become stale as providers add/remove models. Users select deprecated models or miss new capabilities.

**Why it happens:**
- Model lists hardcoded or cached too long
- OpenAI/Anthropic regularly add models
- No notification when models deprecated

**Consequences:**
- API errors from removed models
- Missing access to better/cheaper models
- Confusion about which models are current

**Prevention:**
1. Refresh model lists on app start
2. Cache with TTL (1 day maximum)
3. Handle "model not found" gracefully with suggestions
4. Display model release dates where available

**Phase to address:** Provider Integration phase

**Confidence:** MEDIUM - Common maintenance issue.

---

### Pitfall 12: Large Workflow Canvas Performance

**What goes wrong:** Flet canvas with 100+ nodes becomes sluggish. Every state change triggers expensive redraws.

**Why it happens:**
- Full re-render on updates
- No virtualization of off-screen nodes
- Connection lines calculated on every frame
- Complex node UI compounds overhead

**Consequences:**
- Laggy workflow editing
- Slow zoom/pan
- Unusable for large automations

**Warning signs:**
- FPS drops during canvas interaction
- Delay between click and response
- Memory growth with workflow size

**Prevention:**
1. Implement viewport culling (only render visible nodes)
2. Batch updates to reduce render cycles
3. Use simpler node representations when zoomed out
4. Limit max nodes with pagination
5. Profile and optimize hot paths

**Already documented in known-issues.md:**
> "Canvas tested with up to 50 nodes. Larger workflows (100+ nodes) may require optimization."

**Phase to address:** Stability phase (performance optimization)

**Confidence:** MEDIUM - Known issue in codebase.

---

### Pitfall 13: Content Security Policy with Monaco

**What goes wrong:** Monaco uses inline styles which violate strict Content Security Policy (CSP). Enterprise deployments requiring CSP will block Monaco.

**Why it happens:**
- Monaco generates inline styles dynamically
- CSP headers block inline scripts/styles
- EU-CRA compliance requires strict CSP

**Consequences:**
- Code editor broken in CSP-enabled environments
- Enterprise customers cannot deploy
- Security audit failures

**Prevention:**
1. Configure CSP nonces for Monaco
2. Use Monaco's webpack plugin for style extraction
3. Document CSP requirements for self-hosting
4. Consider alternative editors for strict environments

**Phase to address:** Code Editor Integration phase - if targeting enterprise

**Confidence:** MEDIUM - Verified in [Monaco GitHub issue #4927](https://github.com/microsoft/monaco-editor/issues/4927).

---

## Phase-Specific Warnings Summary

| Phase | Likely Pitfalls | Priority |
|-------|-----------------|----------|
| **Provider Integration** | Rate limits (#6), Ollama discovery (#7), Model staleness (#11), Streaming failures (#2) | HIGH |
| **Code Editor Integration** | Resource management (#5), Mobile incompatibility (#10), CSP issues (#13), State management (#4) | HIGH |
| **Stability/Security** | API key storage (#3), Thread safety (#9) | HIGH |
| **RAG/Embeddings** | Dimension mismatch (#1) | CRITICAL |
| **Release/Polish** | Build failures (#8), Canvas performance (#12) | MEDIUM |

---

## Detection Checklist for Code Reviews

Before merging code that touches these areas:

**Provider Integration:**
- [ ] Rate limit headers parsed and respected?
- [ ] Fallback distinguishes rate limits from other errors?
- [ ] Streaming errors handled with user feedback?
- [ ] Provider health checks implemented?

**Code Editor:**
- [ ] Dispose methods called on all editor resources?
- [ ] Editor instances limited or pooled?
- [ ] Mobile detection with graceful degradation?
- [ ] Memory profiled during extended use?

**State Management:**
- [ ] State centralized, not scattered?
- [ ] Page updates consolidated?
- [ ] Async operations don't block UI?

**Embeddings/RAG:**
- [ ] Dimension validation before storage?
- [ ] Model metadata tracked with vectors?
- [ ] Migration path for model changes?

---

## Sources

**High Confidence (Official Documentation, GitHub Issues):**
- [Monaco Editor GitHub](https://github.com/microsoft/monaco-editor)
- [Flet GitHub Issues](https://github.com/flet-dev/flet/issues)
- [Ollama Error Documentation](https://docs.ollama.com/api/errors)
- [Vercel AI SDK Streaming Docs](https://ai-sdk.dev/docs/reference/ai-sdk-core/stream-text)
- [OpenRouter Streaming Docs](https://openrouter.ai/docs/api/reference/streaming)

**Medium Confidence (Technical Blogs, Tutorials):**
- [Portkey Rate Limiting Guide](https://portkey.ai/blog/tackling-rate-limiting-for-llm-apps/)
- [Replit Code Editor Comparison](https://blog.replit.com/code-editors)
- [Spectral Monaco Integration Blog](https://blog.spectralcore.com/integrating-monaco-editor/)
- [TrueFoundry LLM Gateway Guide](https://www.truefoundry.com/blog/rate-limiting-in-llm-gateway)

**Low Confidence (Community Discussions, Unverified):**
- Stack Overflow discussions on memory leaks
- Python discuss.python.org threading topics

---

*Pitfalls research completed: 2026-01-18*
