# Technology Stack - Skynette Milestone 2

**Project:** Skynette AI Workspace - Code Editor and Provider Expansion
**Researched:** 2026-01-18

## Executive Summary

This research covers the technology stack for adding a code editor with AI assistance and new AI providers (Gemini, Grok) to Skynette. The existing Ollama provider already exists and requires refinement rather than replacement.

**Key Recommendations:**
- **Code Editor:** Custom Flet control using Pygments for syntax highlighting (practical approach)
- **Gemini Provider:** `google-genai` SDK v1.59.0 (NEW SDK - the old `google-generativeai` is deprecated)
- **Grok Provider:** `xai-sdk` v1.5.0 (official gRPC-based SDK)
- **Ollama:** Use existing httpx implementation OR migrate to `ollama` v0.6.1 SDK

---

## Recommended Stack

### Code Editor Component

| Technology | Version | Purpose | Confidence |
|------------|---------|---------|------------|
| Pygments | >=2.19.2 | Syntax highlighting lexer (598 languages) | HIGH |
| Flet Custom Control | - | Code editor UI using TextField + styled text | HIGH |

**Why Pygments:**
- Industry standard for Python syntax highlighting
- 598+ language support built-in
- BSD-2-Clause license
- Works purely in Python (no Flutter wrapper needed)
- Already used by Spyder, Jupyter, and most Python documentation tools

**Why NOT wrap a Flutter code editor package:**
- `flutter_code_editor` and `re_editor` would require creating a Flet extension (Dart wrapper code)
- Flet 0.26+ supports wrapping Flutter packages, but adds complexity
- For code viewing/editing with AI assistance, Pygments + Flet TextField is sufficient
- Saves significant development time vs. Flutter package integration

**Architecture for Code Editor:**
```python
# Pattern: Pygments for tokenization, Flet for display
from pygments.lexers import get_lexer_by_name
from pygments.token import Token
import flet as ft

class CodeEditor(ft.UserControl):
    """
    Code editor using:
    - ft.TextField for input (multiline=True)
    - Pygments for tokenization
    - ft.Column of styled ft.Text for display
    """
```

**Alternative Considered - Flutter Package Wrapping:**
If rich IDE-like features are needed later (code folding, bracket matching, minimap), consider:
- `flutter_code_editor` (212 likes, 44K downloads) - supports 100+ languages, code folding
- `re_editor` (123 likes) - lightweight, performant
- Requires creating Flet extension per https://flet.dev/blog/flet-v-0-26-release-announcement/

### AI Provider: Gemini (Google)

| Technology | Version | Purpose | Confidence |
|------------|---------|---------|------------|
| google-genai | >=1.59.0 | Gemini API client (NEW unified SDK) | HIGH |

**CRITICAL:** The `google-generativeai` package is DEPRECATED. End-of-life was November 30, 2025. Use `google-genai` instead.

**Installation:**
```bash
pip install google-genai
# For async support:
pip install google-genai[aiohttp]
```

**Why `google-genai`:**
- Official unified SDK for Gemini (GA as of May 2025)
- Supports both Gemini Developer API and Vertex AI
- Modern async support via `client.aio`
- Streaming via `generate_content_stream()`
- Active maintenance, regular releases

**Provider Implementation Pattern:**
```python
from google import genai
from src.ai.providers.base import BaseProvider

class GeminiProvider(BaseProvider):
    name = "gemini"
    display_name = "Google Gemini"

    async def initialize(self) -> bool:
        self._client = genai.Client(api_key=self.api_key)
        # Async client via: self._client.aio
        return True

    async def chat(self, messages, config) -> AIResponse:
        response = await self._client.aio.models.generate_content(
            model=config.model or 'gemini-2.5-flash',
            contents=[...],
        )
        return AIResponse(content=response.text, ...)

    async def chat_stream(self, messages, config):
        async for chunk in await self._client.aio.models.generate_content_stream(
            model=config.model or 'gemini-2.5-flash',
            contents=[...],
        ):
            yield AIStreamChunk(content=chunk.text, ...)
```

**Recommended Models (per SDK codegen instructions):**
- `gemini-3-flash-preview` - General tasks
- `gemini-3-pro-preview` - Complex reasoning
- `gemini-2.5-flash-lite` - High-volume, low-latency
- `gemini-2.5-flash` - Balanced (current default)

### AI Provider: Grok (xAI)

| Technology | Version | Purpose | Confidence |
|------------|---------|---------|------------|
| xai-sdk | >=1.5.0 | Official xAI Grok API client | HIGH |

**Installation:**
```bash
pip install xai-sdk
# For telemetry (optional):
pip install xai-sdk[telemetry-http]
```

**Why `xai-sdk`:**
- Official Python SDK from xAI
- gRPC-based with both sync and async clients
- Supports streaming, function calling, vision
- Agentic tool calling (web search, X search, code execution)
- Production-stable (Apache 2.0 license)

**Provider Implementation Pattern:**
```python
from xai_sdk import AsyncClient
from src.ai.providers.base import BaseProvider

class GrokProvider(BaseProvider):
    name = "grok"
    display_name = "xAI Grok"

    async def initialize(self) -> bool:
        self._client = AsyncClient(api_key=self.api_key)
        return True

    async def chat(self, messages, config) -> AIResponse:
        chat = self._client.chat.create(
            model=config.model or "grok-4-1-fast",
            messages=[...],
        )
        response = await chat.sample()
        return AIResponse(content=response.content, ...)

    async def chat_stream(self, messages, config):
        # xai-sdk streaming pattern
        chat = self._client.chat.create(model="grok-4-1-fast", messages=[...])
        async for response, chunk in chat.stream():
            yield AIStreamChunk(content=chunk.text, ...)
```

**Recommended Models:**
- `grok-4-1-fast` - Recommended for agentic tool calling
- `grok-4-1-fast-reasoning` - Frontier model with reasoning (2M context)
- `grok-code-fast-1` - Optimized for coding (256K context)

### AI Provider: Ollama (Refinement)

| Technology | Version | Purpose | Confidence |
|------------|---------|---------|------------|
| ollama | >=0.6.1 | Official Ollama Python client (OPTIONAL) | MEDIUM |
| httpx | >=0.27.0 | HTTP client (CURRENT approach) | HIGH |

**Current State:**
Skynette already has an Ollama provider using httpx directly. Two options:

**Option A: Keep httpx (Recommended)**
- Already implemented and working
- Zero new dependencies
- Full control over HTTP behavior
- The official `ollama` SDK is also built on httpx

**Option B: Migrate to official `ollama` SDK**
- Cleaner API (Pythonic interface)
- Maintained by Ollama team
- Same underlying httpx transport
- Example: `ollama.chat()`, `ollama.AsyncClient()`

**Recommendation:** Keep existing httpx implementation unless refactoring for consistency. The official SDK adds no new capabilities.

---

## Framework Versions

### Core Framework

| Technology | Current | Target | Notes |
|------------|---------|--------|-------|
| Flet | 0.25.0+ | >=0.80.2 | Major version jump available; evaluate breaking changes |
| Python | 3.11+ | 3.11+ | All dependencies support 3.11-3.13 |

**Flet Upgrade Considerations:**
- Current: `flet>=0.25.0`
- Latest: `0.80.2` (January 2026)
- Flet 0.26+ adds improved extension support for Flutter packages
- Flet 0.80+ includes Shimmer control, improved error handling
- **Recommendation:** Test upgrade to 0.80.x in separate branch before committing

### Supporting Libraries

| Library | Purpose | Version | Notes |
|---------|---------|---------|-------|
| httpx | HTTP client (existing) | >=0.27.0 | Already in use |
| Pygments | Syntax highlighting | >=2.19.2 | New addition |
| google-genai | Gemini API | >=1.59.0 | Replaces google-generativeai |
| xai-sdk | Grok API | >=1.5.0 | New addition |

---

## Dependencies Update

### requirements.txt additions

```txt
# Code Editor
Pygments>=2.19.2

# AI Providers (update AI section)
google-genai>=1.59.0      # Replaces google-generativeai
xai-sdk>=1.5.0            # New - Grok provider
```

### pyproject.toml [project.optional-dependencies] updates

```toml
ai = [
    # Existing (keep)
    "llama-cpp-python>=0.2.0",
    "openai>=1.0.0",
    "anthropic>=0.25.0",
    "huggingface-hub>=0.20.0",
    "chromadb>=0.5.0",
    "sentence-transformers>=2.2.0",

    # Updated (replace google-generativeai)
    "google-genai>=1.59.0",

    # Removed (deprecated)
    # "google-generativeai>=0.5.0",  # DEPRECATED - DO NOT USE
    # "groq>=0.5.0",  # Replace with xai-sdk

    # New
    "xai-sdk>=1.5.0",
]
```

**Note:** The `groq` package in current requirements.txt is for Groq Cloud (different from xAI Grok). Clarify whether both are needed.

---

## What NOT to Use

| Technology | Reason |
|------------|--------|
| `google-generativeai` | DEPRECATED - EOL November 30, 2025 |
| `vertexai.generative_models` | Deprecated June 24, 2025, removal June 24, 2026 |
| Monaco Editor (direct) | Cannot directly integrate with Flet without Flutter wrapper |
| CodeMirror (direct) | Web-only, no Python bindings |
| tree-sitter (Python) | Overkill for syntax highlighting; Pygments is simpler |
| `code_text_field` Flutter package | Poor maintenance status per Flutter Gems |
| `flutter_highlight` Flutter package | Poor maintenance status per Flutter Gems |

---

## Installation Commands

```bash
# Core additions
pip install Pygments>=2.19.2 google-genai>=1.59.0 xai-sdk>=1.5.0

# Optional: async support for google-genai
pip install google-genai[aiohttp]

# Development testing
pip install -e ".[ai,dev]"
```

---

## API Key Environment Variables

```bash
# Existing
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# New for Gemini
GEMINI_API_KEY=...
# OR (auto-detected by google-genai)
GOOGLE_API_KEY=...

# New for Grok
XAI_API_KEY=...
```

---

## Confidence Assessment

| Component | Confidence | Rationale |
|-----------|------------|-----------|
| Pygments | HIGH | Verified on PyPI, standard library, 2.19.2 released June 2025 |
| google-genai | HIGH | Verified on PyPI (1.59.0), official Google SDK, documented deprecation of old SDK |
| xai-sdk | HIGH | Verified on PyPI (1.5.0), official xAI SDK, production-stable |
| Flet code editor approach | MEDIUM | Community examples exist, but no official code editor control; requires custom implementation |
| ollama SDK migration | LOW | Optional change; existing httpx approach works fine |

---

## Sources

### Official Documentation
- [Google GenAI SDK Documentation](https://googleapis.github.io/python-genai/)
- [Google GenAI GitHub](https://github.com/googleapis/python-genai)
- [xAI SDK GitHub](https://github.com/xai-org/xai-sdk-python)
- [xAI Documentation](https://docs.x.ai/)
- [Pygments Official Site](https://pygments.org/)
- [Flet Documentation](https://flet.dev/docs/)
- [Flet v0.26 Release (Flutter package wrapping)](https://flet.dev/blog/flet-v-0-26-release-announcement/)

### PyPI Package Pages
- [google-genai on PyPI](https://pypi.org/project/google-genai/) - v1.59.0
- [xai-sdk on PyPI](https://pypi.org/project/xai-sdk/) - v1.5.0
- [Pygments on PyPI](https://pypi.org/project/Pygments/) - v2.19.2
- [ollama on PyPI](https://pypi.org/project/ollama/) - v0.6.1

### Deprecation Notices
- [google-generativeai deprecated](https://github.com/google-gemini/deprecated-generative-ai-python)
- [Migrate to Google GenAI SDK](https://ai.google.dev/gemini-api/docs/migrate)

### Code Editor References
- [Flutter Code Editor on pub.dev](https://pub.dev/packages/flutter_code_editor)
- [Top Flutter Code Editor Packages](https://fluttergems.dev/editor-syntax-highlighter/)
- [Flet Syntax Highlighting Gist](https://gist.github.com/Bbalduzz/dc6e5037ccc505b27adc1e5f6a34d687)
