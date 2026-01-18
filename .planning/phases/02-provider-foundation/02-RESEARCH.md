# Phase 2: Provider Foundation - Research

**Researched:** 2026-01-18
**Domain:** AI Provider Integration (Gemini, Grok, Ollama enhancements)
**Confidence:** HIGH

## Summary

This phase adds Gemini and Grok providers alongside enhancing the existing Ollama integration. The google-genai SDK (v1.59.0) is the official, actively maintained SDK for Gemini API access - the legacy google-generativeai package is deprecated. The xai-sdk (v1.5.0) is the official gRPC-based Python SDK for Grok, supporting both sync and async patterns. Both SDKs have mature streaming APIs that fit the existing BaseProvider pattern.

The codebase already has a well-structured provider architecture with `BaseProvider`, `AIGateway`, and typed dataclasses for messages, responses, and stream chunks. The existing `OllamaProvider` uses httpx for HTTP/streaming and the `AIHubState` already tracks Ollama connection status. Rate limit handling requires tracking response headers and implementing pre-emptive throttling. Streaming failure recovery requires buffering partial responses and maintaining clean state.

**Primary recommendation:** Implement Gemini and Grok providers following the existing Anthropic/OpenAI patterns, with enhanced error handling for streaming failures and rate limits. Extend AIHubState for Ollama status with auto-refresh on connect.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| google-genai | >=1.59.0 | Gemini API client | Official Google SDK, replaces deprecated google-generativeai |
| xai-sdk | >=1.5.0 | Grok API client | Official xAI SDK, gRPC-based with streaming support |
| httpx | >=0.27.0 | HTTP client for Ollama | Already in codebase, async-native with streaming |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| google-genai[aiohttp] | >=1.59.0 | Faster async transport | Optional for production async performance |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| google-genai | OpenAI SDK with base_url | Would miss Gemini-specific features (Live API) |
| xai-sdk | OpenAI SDK with base_url | Works for basic chat, but misses agent tools API |

**Installation:**
```bash
pip install "google-genai>=1.59.0" "xai-sdk>=1.5.0"
```

**pyproject.toml addition:**
```toml
[project.optional-dependencies]
ai = [
    # ... existing entries ...
    "google-genai>=1.59.0",  # Gemini (NOT google-generativeai)
    "xai-sdk>=1.5.0",        # Grok
]
```

## Architecture Patterns

### Recommended Project Structure
```
src/ai/providers/
    base.py          # BaseProvider ABC (exists)
    gemini.py        # NEW: Gemini provider
    grok.py          # NEW: Grok provider
    ollama.py        # ENHANCE: better status/discovery
    __init__.py      # Register new providers

src/ai/
    gateway.py       # ENHANCE: rate limit tracking
    exceptions.py    # NEW: streaming failure exceptions
```

### Pattern 1: Provider Implementation (follow existing pattern)
**What:** Each provider extends BaseProvider with SDK-specific logic
**When to use:** Adding any new AI provider
**Example:**
```python
# Source: Existing src/ai/providers/anthropic.py pattern
class GeminiProvider(BaseProvider):
    name = "gemini"
    display_name = "Google Gemini"
    capabilities = {
        AICapability.TEXT_GENERATION,
        AICapability.CHAT,
        AICapability.IMAGE_ANALYSIS,
        AICapability.CODE_GENERATION,
    }

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.5-flash"):
        super().__init__()
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        self.model = model
        self._client = None

    async def initialize(self) -> bool:
        if not self.api_key:
            self._is_available = False
            return False
        try:
            from google import genai
            self._client = genai.Client(api_key=self.api_key).aio
            self._is_initialized = True
            self._is_available = True
            return True
        except ImportError:
            self._is_available = False
            return False
```

### Pattern 2: Async Streaming with google-genai
**What:** Stream chat responses using the new SDK pattern
**When to use:** Gemini streaming responses
**Example:**
```python
# Source: https://googleapis.github.io/python-genai/
async def chat_stream(self, messages: list[AIMessage], config: GenerationConfig) -> AsyncIterator[AIStreamChunk]:
    chat = self._client.chats.create(model=self.model)
    # Add previous messages to chat
    for msg in messages[:-1]:
        if msg.role == "user":
            await chat.send_message(msg.content)

    # Stream the last message
    last_msg = messages[-1].content
    async for chunk in await chat.send_message_stream(last_msg):
        yield AIStreamChunk(
            content=chunk.text,
            is_final=False,
        )
    yield AIStreamChunk(content="", is_final=True)
```

### Pattern 3: Async Streaming with xai-sdk
**What:** Stream chat responses using the xAI SDK
**When to use:** Grok streaming responses
**Example:**
```python
# Source: https://github.com/xai-org/xai-sdk-python
async def chat_stream(self, messages: list[AIMessage], config: GenerationConfig) -> AsyncIterator[AIStreamChunk]:
    from xai_sdk.chat import user, assistant, system

    chat = self._client.chat.create(model=self.model)
    for msg in messages:
        if msg.role == "system":
            chat.append(system(msg.content))
        elif msg.role == "user":
            chat.append(user(msg.content))
        elif msg.role == "assistant":
            chat.append(assistant(msg.content))

    for response, chunk in chat.stream():
        yield AIStreamChunk(
            content=chunk.content,
            is_final=False,
        )
    yield AIStreamChunk(content="", is_final=True)
```

### Pattern 4: Streaming Failure Recovery
**What:** Buffer partial content, track state, provide clean error with partial response
**When to use:** Any streaming operation that can fail mid-response
**Example:**
```python
# Source: Best practice pattern from OpenAI community
async def chat_stream_with_recovery(self, messages, config) -> AsyncIterator[AIStreamChunk]:
    buffer = []
    try:
        async for chunk in self._raw_stream(messages, config):
            buffer.append(chunk.content)
            yield chunk
    except Exception as e:
        # Preserve partial content
        partial_content = "".join(buffer)
        yield AIStreamChunk(
            content="\n\n[Response interrupted]",
            is_final=True,
            error={
                "type": "stream_interrupted",
                "partial_content": partial_content,
                "error_message": str(e),
            }
        )
```

### Pattern 5: Rate Limit Header Tracking
**What:** Extract rate limit info from response headers for pre-emptive throttling
**When to use:** Cloud providers with rate limits (Gemini, Grok)
**Example:**
```python
# Source: https://ai.google.dev/gemini-api/docs/rate-limits
@dataclass
class RateLimitInfo:
    limit_requests: int = 0
    remaining_requests: int = 0
    reset_time: Optional[datetime] = None
    limit_tokens: int = 0
    remaining_tokens: int = 0

def extract_rate_limits(headers: dict) -> RateLimitInfo:
    """Extract rate limit info from response headers."""
    return RateLimitInfo(
        limit_requests=int(headers.get("x-ratelimit-limit-requests", 0)),
        remaining_requests=int(headers.get("x-ratelimit-remaining-requests", 0)),
        # Parse reset time from header
    )

def get_usage_percentage(info: RateLimitInfo) -> float:
    """Calculate usage percentage for UI meter."""
    if info.limit_requests == 0:
        return 0.0
    return 1.0 - (info.remaining_requests / info.limit_requests)
```

### Anti-Patterns to Avoid
- **Using deprecated google-generativeai:** The legacy package is deprecated as of Nov 30, 2025. Use google-genai.
- **Blocking async with sync iteration:** Use `async for` not `for` when iterating streams. Sync iteration blocks the event loop.
- **Ignoring partial responses on failure:** Always buffer and preserve partial content when streaming fails mid-response.
- **Silent rate limit failures:** Track rate limit headers and notify users before hitting limits, not after.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Gemini API client | Custom HTTP requests | google-genai SDK | Handles auth, retries, model endpoints |
| Grok API client | OpenAI SDK hack | xai-sdk | Native gRPC, agent tools API access |
| Ollama connection check | Custom ping logic | httpx GET /api/tags | Already returns status + model list |
| Exponential backoff | Custom sleep loops | Use SDK built-in retries | SDKs handle this, or use tenacity |
| Rate limit parsing | Regex on headers | Standard header extraction | Headers follow standard naming |

**Key insight:** Both google-genai and xai-sdk handle authentication, retries, and connection management. Don't wrap raw HTTP around them.

## Common Pitfalls

### Pitfall 1: Using Deprecated Gemini SDK
**What goes wrong:** Import errors, missing features, no Live API access
**Why it happens:** Old tutorials reference google-generativeai
**How to avoid:** Always use `from google import genai`, never `import google.generativeai`
**Warning signs:** Package name has "generativeai", streaming uses `stream=True` parameter instead of `*_stream()` method

### Pitfall 2: Sync vs Async Client Confusion (google-genai)
**What goes wrong:** Blocking main thread, unresponsive UI
**Why it happens:** SDK has both sync and async APIs with similar names
**How to avoid:** Always use `client.aio.*` for async operations, call `await aclient.aclose()` on cleanup
**Warning signs:** Using `client.models.*` directly instead of `client.aio.models.*`

### Pitfall 3: xai-sdk Timeout on Reasoning Models
**What goes wrong:** Requests fail with DEADLINE_EXCEEDED
**Why it happens:** Grok reasoning models take longer, default timeout is 900s but may not be enough
**How to avoid:** Set explicit timeout `Client(timeout=3600)` for reasoning-heavy requests
**Warning signs:** Intermittent failures only on complex prompts

### Pitfall 4: Ollama Model Not Loaded
**What goes wrong:** First request takes 30+ seconds or fails
**Why it happens:** Ollama lazy-loads models on first request
**How to avoid:** Call `/api/generate` with empty prompt on connect to warm up model
**Warning signs:** Inconsistent response times, first request always slow

### Pitfall 5: Losing Partial Responses on Stream Error
**What goes wrong:** User loses all content when stream fails at 90%
**Why it happens:** Exceptions thrown without preserving buffer
**How to avoid:** Wrap streaming in try/except, yield error chunk with partial content
**Warning signs:** Empty chat messages after network blips

### Pitfall 6: Rate Limit 429 Without User Feedback
**What goes wrong:** User thinks app is broken, retries make it worse
**Why it happens:** Error not surfaced to UI, no pre-emptive warning
**How to avoid:** Track rate limit headers, show usage meter when > 80%, clear error with retry timing
**Warning signs:** Users reporting "random failures"

## Code Examples

Verified patterns from official sources:

### Gemini Client Setup (Async)
```python
# Source: https://googleapis.github.io/python-genai/
from google import genai
from google.genai import errors

# Create async client
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
aclient = client.aio

# Generate content
response = await aclient.models.generate_content(
    model="gemini-2.5-flash",
    contents="Hello, world!"
)
print(response.text)

# Error handling
try:
    await aclient.models.generate_content(model="invalid", contents="text")
except errors.APIError as e:
    print(f"Error {e.code}: {e.message}")

# Cleanup
await aclient.aclose()
```

### Gemini Streaming Chat
```python
# Source: https://googleapis.github.io/python-genai/
chat = client.aio.chats.create(model="gemini-2.5-flash")
async for chunk in await chat.send_message_stream("tell me a story"):
    print(chunk.text, end="", flush=True)
```

### Gemini Model Listing
```python
# Source: https://googleapis.github.io/python-genai/
pager = client.models.list(config={"page_size": 10})
for model in pager:
    print(model.name)
```

### Grok Client Setup
```python
# Source: https://github.com/xai-org/xai-sdk-python
from xai_sdk import Client, AsyncClient

# Sync client (uses XAI_API_KEY env var by default)
client = Client()

# Or explicit API key with timeout
client = Client(
    api_key=os.getenv("XAI_API_KEY"),
    timeout=3600,  # For reasoning models
)

# Async client
async_client = AsyncClient()
```

### Grok Streaming Chat
```python
# Source: https://github.com/xai-org/xai-sdk-python
from xai_sdk import Client
from xai_sdk.chat import user, system

client = Client()
chat = client.chat.create(model="grok-3")
chat.append(system("You are a helpful assistant."))
chat.append(user("What is the meaning of life?"))

for response, chunk in chat.stream():
    print(chunk.content, end="", flush=True)
chat.append(response)  # Add response to history
```

### Ollama Status Check
```python
# Source: Existing src/ai/models/sources/ollama.py pattern
async def check_ollama_status() -> tuple[bool, list[str]]:
    """Check if Ollama is running and get available models."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:11434/api/tags")
            if response.status_code == 200:
                data = response.json()
                models = [m["name"] for m in data.get("models", [])]
                return True, models
            return False, []
    except Exception:
        return False, []
```

### Streaming with Error Recovery
```python
# Source: Best practice pattern
async def stream_with_recovery(
    self,
    stream_fn: Callable[[], AsyncIterator[AIStreamChunk]],
) -> AsyncIterator[AIStreamChunk]:
    """Wrap streaming with partial response preservation."""
    buffer = []
    try:
        async for chunk in stream_fn():
            buffer.append(chunk.content)
            yield chunk
    except Exception as e:
        partial = "".join(buffer)
        # Yield final chunk with error info
        yield AIStreamChunk(
            content="\n\n[Response interrupted]",
            is_final=True,
            error={
                "type": type(e).__name__,
                "message": str(e),
                "partial_content_length": len(partial),
            }
        )
        # Let caller know about partial content
        raise StreamInterruptedError(partial_content=partial, cause=e)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| google-generativeai SDK | google-genai SDK | Nov 2025 deprecated | Must migrate, old SDK won't get features |
| model.generate_content(stream=True) | client.models.generate_content_stream() | google-genai 1.0 | Different streaming API pattern |
| OpenAI SDK for Grok | xai-sdk native | xai-sdk 1.0 (2024) | Better agent tools, native gRPC |
| Ollama library (ollama-python) | Direct HTTP (httpx) | Optional | Both work, httpx already in deps |

**Deprecated/outdated:**
- google-generativeai: Deprecated Nov 30, 2025. No new features, missing Live API.
- Using OpenAI SDK base_url for Grok: Works but misses agent tools API features in xai-sdk 1.3+

## Open Questions

Things that couldn't be fully resolved:

1. **Gemini rate limit header names**
   - What we know: Returns 429 with Retry-After header
   - What's unclear: Exact header names for remaining/limit counts (x-ratelimit-* vs custom)
   - Recommendation: Log headers in development, document what we find

2. **xai-sdk async client completeness**
   - What we know: AsyncClient exists, basic operations work
   - What's unclear: Whether streaming works identically in async mode
   - Recommendation: Test async streaming early, fall back to sync+executor if needed

3. **Ollama auto-refresh timing**
   - What we know: User wants auto-refresh on connect AND manual button
   - What's unclear: How often to auto-refresh (every connect? periodic?)
   - Recommendation: Refresh on initial connect, provide manual button, maybe 60s polling when tab is active

## Sources

### Primary (HIGH confidence)
- google-genai GitHub: https://github.com/googleapis/python-genai - Installation, client setup, streaming
- google-genai docs: https://googleapis.github.io/python-genai/ - Async client, error handling
- xai-sdk GitHub: https://github.com/xai-org/xai-sdk-python - Full SDK documentation
- xai docs streaming: https://docs.x.ai/docs/guides/streaming-response - Streaming patterns
- Ollama docs: https://docs.ollama.com/api/introduction - API endpoints
- Existing codebase: src/ai/providers/*.py - Established patterns

### Secondary (MEDIUM confidence)
- Gemini rate limits: https://ai.google.dev/gemini-api/docs/rate-limits - Rate limit concepts
- xAI rate limits: https://docs.x.ai/docs/key-information/consumption-and-rate-limits - Header names
- OpenAI community: https://community.openai.com/t/best-practices-for-handling-mid-stream-errors-responses-api/1370883 - Error recovery

### Tertiary (LOW confidence)
- Blog posts on rate limiting strategies - General patterns, need verification

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Official SDKs verified, versions confirmed via pip index
- Architecture: HIGH - Following existing codebase patterns
- Pitfalls: MEDIUM - Mix of official docs and community experience
- Rate limit headers: MEDIUM - Verified for xAI, less clear for Gemini specifics

**Research date:** 2026-01-18
**Valid until:** 2026-02-18 (30 days - SDKs are stable)
