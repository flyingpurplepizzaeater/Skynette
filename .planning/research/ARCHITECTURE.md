# Architecture Patterns

**Domain:** AI Workspace with Code Editor Integration
**Researched:** 2026-01-18
**Confidence:** HIGH (based on existing codebase analysis)

## Executive Summary

Skynette has a well-structured layered architecture that can cleanly accommodate a code editor and new AI providers. The existing patterns (provider abstraction, gateway with fallback, Flet component composition) provide solid foundations. The code editor should integrate as a new UI view that leverages the existing AI gateway for assistance features.

## Existing Architecture Overview

```
+------------------------------------------+
|              UI Layer (Flet)             |
|  Views: Chat, Workflows, Agents, AIHub   |
|  Components: Dialogs, Cards, Panels      |
+------------------------------------------+
           |              |
           v              v
+------------------+  +--------------------+
|   Core Layer     |  |   AI Gateway       |
|  - Workflows     |  |  - Provider Mgmt   |
|  - Nodes         |  |  - Fallback Logic  |
|  - Agents        |  |  - Usage Tracking  |
|  - Coding Utils  |  +--------------------+
+------------------+           |
           |                   v
           |          +--------------------+
           |          |   AI Providers     |
           |          |  - OpenAI          |
           |          |  - Anthropic       |
           |          |  - Ollama          |
           |          |  - Local (llama)   |
           |          +--------------------+
           v
+------------------------------------------+
|            Data Layer                    |
|  - SQLite (executions, settings, usage)  |
|  - YAML files (workflow definitions)     |
|  - Keyring (API key storage)             |
+------------------------------------------+
           |
           v
+------------------------------------------+
|            RAG Subsystem                 |
|  - ChromaDB (vector store)               |
|  - Document processors                   |
|  - Embedding generation                  |
+------------------------------------------+
```

## Code Editor Integration Architecture

### Recommended Approach: Editor as New View

The code editor should be implemented as a new top-level view (`CodeEditorView`) that follows the existing view patterns.

```
src/ui/views/code_editor.py
    |
    +-- EditorPane (main editing area)
    |   +-- Syntax highlighting via Flet Markdown or custom Code control
    |   +-- Line numbers
    |   +-- File tabs
    |
    +-- AIAssistPanel (AI assistance sidebar)
    |   +-- Chat interface for code questions
    |   +-- Code completion requests
    |   +-- Code explanation
    |
    +-- FileExplorer (project navigation)
        +-- Directory tree
        +-- File operations
```

### Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| `CodeEditorView` | Top-level orchestration, toolbar, layout | `SkynetteApp`, `AIGateway` |
| `EditorPane` | Text editing, syntax display, cursor management | `CodeEditorView` |
| `AIAssistPanel` | AI chat interface for code help | `AIGateway`, `EditorPane` |
| `FileExplorer` | File system navigation, open/save | `CodeEditorView`, local filesystem |
| `CodeSessionManager` | Track open files, modifications, undo history | `EditorPane`, `FileExplorer` |

### Data Flow for AI-Assisted Coding

```
User types code or requests assistance
            |
            v
    +---------------+
    | EditorPane    |  (captures context: current file, selection, cursor)
    +---------------+
            |
            v
    +------------------+
    | AIAssistPanel    |  (formats prompt with code context)
    +------------------+
            |
            v
    +---------------+
    | AIGateway     |  (routes to best available provider)
    +---------------+
            |
            +-- Try primary provider (user preference)
            |
            +-- Fallback to secondary if fails
            |
            v
    +---------------+
    | Provider      |  (OpenAI/Anthropic/Ollama/etc)
    +---------------+
            |
            v
    Response flows back through AIAssistPanel to EditorPane
```

## AI Provider Architecture

### Existing Pattern (Maintain)

The existing `BaseProvider` abstraction is well-designed:

```python
class BaseProvider(ABC):
    name: str
    display_name: str
    capabilities: set[AICapability]

    async def initialize(self) -> bool
    def is_available(self) -> bool
    async def generate(prompt, config) -> AIResponse
    async def chat(messages, config) -> AIResponse
    async def chat_stream(messages, config) -> AsyncIterator[AIStreamChunk]
    async def embed(texts) -> list[list[float]]
```

### Adding New Providers

New providers (Gemini, Grok) should follow the exact same pattern:

**Gemini Provider:**
```
src/ai/providers/gemini.py
    - Uses google-genai SDK (GA as of 2025)
    - Install: pip install google-genai
    - Capabilities: TEXT_GENERATION, CHAT, EMBEDDINGS, CODE_GENERATION
    - Context: Up to 2M tokens with Gemini 1.5
```

**Grok Provider:**
```
src/ai/providers/grok.py
    - Uses OpenAI-compatible API (xAI supports OpenAI SDK)
    - Install: pip install openai (already present)
    - Capabilities: TEXT_GENERATION, CHAT, CODE_GENERATION, FUNCTION_CALLING
    - Notable: Built-in RAG, web search tools
```

### Provider Registration

Update `src/ai/providers/__init__.py`:

```python
def initialize_default_providers():
    gateway = get_gateway()

    # Priority order: Local first (free), then cloud
    providers = [
        (LocalProvider(), 1),
        (OllamaProvider(), 2),
        (OpenAIProvider(), 3),
        (AnthropicProvider(), 4),
        (GeminiProvider(), 5),    # NEW
        (GrokProvider(), 6),      # NEW
        (DemoProvider(), 99),     # Fallback
    ]

    for provider, priority in providers:
        try:
            gateway.register_provider(provider, priority)
        except Exception:
            pass  # Provider optional
```

### Fallback Strategy Enhancement

The existing fallback is sequential. Consider enhancing for code tasks:

```python
# In AIGateway
def get_providers_for_capability(
    self,
    capability: AICapability,
    prefer_local: bool = False  # For privacy-sensitive code
) -> list[BaseProvider]:
    providers = [
        p for name in self.provider_priority
        for p in [self.providers.get(name)]
        if p and capability in p.capabilities and p.is_available()
    ]

    if prefer_local:
        # Reorder to prefer local providers for code
        local = [p for p in providers if p.name in ('local', 'ollama')]
        cloud = [p for p in providers if p.name not in ('local', 'ollama')]
        return local + cloud

    return providers
```

## Code Editor Data Model

### New Model: CodeSession

```python
# src/core/coding/models.py

class CodeFile(BaseModel):
    """Represents an open file in the editor."""
    path: str
    content: str
    language: str
    modified: bool = False
    cursor_position: tuple[int, int] = (0, 0)

class CodeSession(BaseModel):
    """Represents the editor session state."""
    id: str
    open_files: list[CodeFile]
    active_file_index: int = 0
    project_root: Optional[str] = None
    ai_context: dict = {}  # Stores relevant context for AI assistance
```

### Storage Extension

Add to `src/data/storage.py`:

```python
# New table for code sessions
cursor.execute("""
    CREATE TABLE IF NOT EXISTS code_sessions (
        id TEXT PRIMARY KEY,
        project_root TEXT,
        open_files TEXT,  -- JSON
        active_file TEXT,
        created_at TEXT,
        updated_at TEXT
    )
""")
```

## Flet Code Editor Implementation

### Syntax Highlighting Approach

Based on research, Flet code editors typically use one of:

1. **Custom `Code` UserControl** - Build syntax highlighting using regex patterns and Flet `Text` spans with colors
2. **Markdown code blocks** - Use `ft.Markdown` with `MarkdownCodeTheme.GITHUB`
3. **WebView with Monaco/CodeMirror** - Embed a web-based editor (desktop/web only)

**Recommendation:** Start with approach 1 (custom control) for consistency across all platforms:

```python
# src/ui/components/code_editor.py

class CodeEditor(ft.UserControl):
    """Syntax-highlighted code editor component."""

    def __init__(
        self,
        value: str = "",
        language: str = "python",
        on_change: callable = None,
        theme: str = "github_dark",
    ):
        super().__init__()
        self.value = value
        self.language = language
        self.on_change = on_change
        self.theme = theme

        # Syntax rules per language
        self.syntax_rules = self._get_syntax_rules(language)

    def _get_syntax_rules(self, language: str) -> dict:
        """Return regex patterns for syntax highlighting."""
        if language == "python":
            return {
                "keyword": r"\b(def|class|if|else|elif|for|while|return|import|from|as|with|try|except|finally|raise|yield|async|await)\b",
                "builtin": r"\b(print|len|range|str|int|float|list|dict|set|tuple|bool|None|True|False)\b",
                "string": r'("""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'|"[^"]*"|\'[^\']*\')',
                "comment": r"#.*$",
                "function": r"\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\(",
                "number": r"\b\d+\.?\d*\b",
            }
        # Add more languages...
        return {}

    def build(self):
        # Build editor UI with highlighted text
        ...
```

## Integration Points

### 1. Navigation Integration

Add to `SkynetteApp._build_nav_items()`:

```python
{"icon": ft.Icons.CODE, "label": "Code", "view": "code_editor"},
```

### 2. AI Hub Integration

The code editor should appear in AI Hub's capabilities:
- Model selection for code assistance
- Code-specific model recommendations (CodeLlama, DeepSeek Coder)

### 3. Workflow Integration

Allow workflows to trigger code operations:
- `CodeGenerateNode` - Generate code from prompt
- `CodeReviewNode` - Review code with AI
- `CodeExecuteNode` - Run Python code (sandboxed)

## Patterns to Follow

### Pattern 1: View Lifecycle

All views follow this pattern:

```python
class MyView(ft.Column):
    def __init__(self, page: ft.Page = None):
        super().__init__()
        self._page = page
        self.expand = True
        # Initialize state

    def build(self):
        # Return the view's control tree
        return ft.Column(controls=[...])

    def did_mount(self):
        # Called when view is mounted (optional)
        pass
```

### Pattern 2: Async Operations

Use `asyncio.create_task()` for async operations triggered by UI:

```python
def _on_button_click(self, e):
    asyncio.create_task(self._do_async_work())

async def _do_async_work(self):
    result = await self.ai_gateway.generate(...)
    # Update UI
    if self._page:
        self._page.update()
```

### Pattern 3: Provider Implementation

```python
class NewProvider(BaseProvider):
    name = "provider_name"
    display_name = "Provider Display Name"
    capabilities = {AICapability.CHAT, AICapability.CODE_GENERATION}

    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.api_key = api_key or os.environ.get("PROVIDER_API_KEY")
        self._client = None

    async def initialize(self) -> bool:
        if not self.api_key:
            self._is_available = False
            return False
        # Initialize SDK client
        self._is_available = True
        return True

    def is_available(self) -> bool:
        return self._is_available and self.api_key is not None
```

## Anti-Patterns to Avoid

### Anti-Pattern 1: Direct Provider Access

**Bad:** Views calling providers directly
```python
# DON'T DO THIS
response = await OpenAIProvider().chat(messages)
```

**Good:** Always go through gateway
```python
# DO THIS
response = await get_gateway().chat(messages)
```

### Anti-Pattern 2: Blocking UI Thread

**Bad:** Synchronous API calls
```python
# DON'T DO THIS
response = requests.post(api_url, ...)  # Blocks UI
```

**Good:** Async with proper task management
```python
# DO THIS
async with httpx.AsyncClient() as client:
    response = await client.post(api_url, ...)
```

### Anti-Pattern 3: Tight Coupling

**Bad:** Editor directly manipulating workflow models
```python
# DON'T DO THIS
class CodeEditor:
    def save(self):
        workflow = Workflow(...)  # Creating workflow models in editor
```

**Good:** Use defined interfaces
```python
# DO THIS
class CodeEditor:
    def __init__(self, on_save: callable):
        self.on_save = on_save

    def save(self):
        self.on_save(self.content)  # Let parent handle persistence
```

## Build Order Implications

Based on architectural dependencies, the recommended build order is:

### Phase 1: Provider Foundation
1. Add Gemini provider (follows existing pattern exactly)
2. Add Grok provider (uses OpenAI SDK, minimal new code)
3. Update provider initialization
4. Test fallback across all providers

### Phase 2: Code Editor Core
1. Create `CodeEditor` component (syntax highlighting)
2. Create `CodeEditorView` (view shell with toolbar)
3. Add file open/save functionality
4. Integrate into main app navigation

### Phase 3: AI-Assisted Features
1. Add `AIAssistPanel` component
2. Connect to AI gateway for code operations
3. Implement code completion/explanation
4. Add context-aware suggestions

### Phase 4: Advanced Integration
1. Workflow script editing in code editor
2. Code execution node for workflows
3. Project-level RAG for code assistance
4. Git integration for version control

## Scalability Considerations

| Concern | Current | At Scale |
|---------|---------|----------|
| Provider Selection | Sequential fallback | Health-aware routing with circuit breakers |
| Code Context | Single file | Project-wide RAG with file indexing |
| Syntax Highlighting | Client-side regex | Consider server-side for large files |
| File Operations | Synchronous | Async with progress indication |

## Sources

- Existing codebase analysis (HIGH confidence)
- [Flet code editor patterns](https://medium.com/@edoardobalducci/creating-a-real-time-code-editor-with-syntax-highlighting-with-flet-ac62834da2cf)
- [Google GenAI SDK](https://github.com/googleapis/python-genai)
- [xAI Grok API](https://docs.x.ai/docs/overview)
- [Multi-Provider AI Gateway patterns](https://portkey.ai/blog/how-to-design-a-reliable-fallback-system-for-llm-apps-using-an-ai-gateway/)
- [AWS AI Gateway architecture](https://aws.amazon.com/blogs/machine-learning/streamline-ai-operations-with-the-multi-provider-generative-ai-gateway-reference-architecture/)
