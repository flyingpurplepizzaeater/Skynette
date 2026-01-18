# Phase 4: AI-Assisted Editing - Research

**Researched:** 2026-01-18
**Domain:** AI-assisted code editing, chat panels, inline suggestions, diff preview
**Confidence:** MEDIUM (Flet lacks native ghost text; requires custom implementation)

## Summary

Phase 4 integrates AI assistance into the code editor through three main features: a chat panel for code questions, inline suggestions (ghost text), and diff-based change preview with accept/reject controls. The existing codebase provides a solid foundation with AIGateway for provider abstraction, EditorState with listener/notify pattern, and ResizableSplitPanel for layout.

The primary technical challenge is implementing ghost text in Flet, which lacks native support for inline suggestions. This requires a custom Stack-based overlay approach. The chat panel follows established Flet patterns (ListView + TextField), while diff preview can leverage Python's built-in difflib for generation and rendering with custom Flet components.

**Primary recommendation:** Use Stack overlays for ghost text, leverage existing AIGateway.chat_stream for streaming responses, and implement a DiffService with difflib.unified_diff for change management.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| flet | >=0.25.0 | UI framework | Already in project; provides Stack, ListView, TextField |
| difflib | stdlib | Diff generation | Python standard library; generates unified diffs |
| tiktoken | >=0.5.0 | Token counting | OpenAI's fast BPE tokenizer; 3-6x faster than alternatives |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| unidiff | >=0.7.0 | Diff parsing | If need to parse/apply external patches (optional) |
| patch-ng | >=1.17.0 | Patch application | If need to apply diffs programmatically (optional) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| tiktoken | Anthropic API count_tokens | Requires API call; tiktoken works offline but less accurate for Claude |
| difflib | whatthepatch | More features but external dependency; difflib sufficient |
| Custom ghost text | Monaco/CodeMirror | Would require web view; Flet TextField approach simpler |

**Installation:**
```bash
pip install tiktoken
# Optional: pip install unidiff patch-ng
```

## Architecture Patterns

### Recommended Project Structure
```
src/
├── ai/
│   └── completions/           # New: AI completion service
│       ├── __init__.py
│       ├── completion_service.py  # Manages completion requests
│       └── token_counter.py       # Token estimation
├── services/
│   └── diff/                  # New: Diff service
│       ├── __init__.py
│       ├── diff_service.py    # Diff generation and application
│       └── models.py          # DiffHunk, DiffLine data classes
└── ui/
    ├── views/
    │   └── code_editor/
    │       └── ai_panel/      # New: AI assistance components
    │           ├── __init__.py
    │           ├── chat_panel.py
    │           ├── chat_state.py
    │           ├── ghost_text.py
    │           └── diff_preview.py
    └── components/
        └── code_editor/
            └── diff_view.py   # Reusable diff visualization
```

### Pattern 1: Chat Panel State with Listener/Notify
**What:** Follows established EditorState pattern for chat panel state
**When to use:** Always for chat panel, matches existing codebase patterns
**Example:**
```python
# Source: Existing pattern from src/ui/views/code_editor/state.py
@dataclass
class ChatState:
    """Centralized state for chat panel."""
    messages: list[ChatMessage] = field(default_factory=list)
    is_streaming: bool = False
    selected_provider: str | None = None
    context_mode: str = "current_file"  # current_file, imports, project

    _listeners: list[Callable[[], None]] = field(default_factory=list, repr=False)

    def add_listener(self, callback: Callable[[], None]) -> None:
        self._listeners.append(callback)

    def notify(self) -> None:
        for listener in self._listeners:
            listener()

    def add_message(self, role: str, content: str) -> None:
        self.messages.append(ChatMessage(role=role, content=content))
        self.notify()
```

### Pattern 2: Ghost Text with Stack Overlay
**What:** Overlay transparent/dimmed text on TextField using Stack
**When to use:** For inline suggestions display
**Example:**
```python
# Source: Flet Stack documentation + existing CodeEditor pattern
class GhostTextEditor(ft.Container):
    """TextField with ghost text overlay for suggestions."""

    def __init__(self):
        super().__init__()
        self._suggestion: str = ""
        self._text_field = ft.TextField(
            value="",
            multiline=True,
            expand=True,
            border=ft.InputBorder.NONE,
            on_change=self._on_change,
        )
        self._ghost_text = ft.Text(
            value="",
            color=ft.colors.with_opacity(0.4, ft.colors.WHITE),
            font_family="monospace",
            size=13,
            visible=False,
        )

    def build(self):
        return ft.Stack(
            controls=[
                ft.Container(content=self._text_field, expand=True),
                ft.Container(
                    content=self._ghost_text,
                    left=8,  # Match TextField padding
                    top=8,
                    visible=self._ghost_text.visible,
                ),
            ],
            expand=True,
        )

    def set_suggestion(self, suggestion: str, position: int) -> None:
        """Show suggestion at cursor position."""
        current = self._text_field.value or ""
        # Calculate where to show ghost text
        self._ghost_text.value = current[:position] + suggestion
        self._ghost_text.visible = bool(suggestion)
        self._ghost_text.update()
```

### Pattern 3: Streaming Response Handling
**What:** Use AIGateway.chat_stream with async iteration
**When to use:** For chat responses and completion streaming
**Example:**
```python
# Source: Existing src/ai/gateway.py pattern
async def stream_response(
    self,
    messages: list[AIMessage],
    on_chunk: Callable[[str], None],
) -> None:
    """Stream AI response, calling on_chunk for each piece."""
    config = GenerationConfig(max_tokens=2048, stream=True)

    async for chunk in self.gateway.chat_stream(messages, config):
        if chunk.content:
            on_chunk(chunk.content)
        if chunk.is_final:
            break
        if chunk.error:
            # Handle interruption gracefully
            on_chunk("\n\n[Response interrupted]")
            break
```

### Pattern 4: Diff Generation and Rendering
**What:** Use difflib for diff generation, custom components for rendering
**When to use:** For diff preview before applying AI changes
**Example:**
```python
# Source: Python difflib documentation
import difflib

class DiffService:
    """Generate and apply diffs between code versions."""

    def generate_diff(
        self,
        original: str,
        modified: str,
        filename: str = "file",
    ) -> list[DiffHunk]:
        """Generate diff hunks between original and modified."""
        original_lines = original.splitlines(keepends=True)
        modified_lines = modified.splitlines(keepends=True)

        diff = difflib.unified_diff(
            original_lines,
            modified_lines,
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
            lineterm="",
        )

        return self._parse_unified_diff(list(diff))

    def apply_hunk(self, original: str, hunk: DiffHunk) -> str:
        """Apply a single hunk to original content."""
        # Implementation applies additions, removes deletions
        pass
```

### Anti-Patterns to Avoid
- **Blocking UI with sync API calls:** Always use async/await with AIGateway
- **Direct TextField manipulation for ghost text:** Use Stack overlay instead
- **Storing large chat histories in memory:** Implement persistence with configurable limits
- **Re-rendering entire chat on each message:** Use ListView with efficient updates

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Diff generation | Custom line-by-line comparison | `difflib.unified_diff` | Handles edge cases, standard format |
| Token counting | Character/word estimation | `tiktoken` | Accurate BPE encoding, fast |
| Stream recovery | Manual try/catch per stream | `BaseProvider._stream_with_recovery` | Already implemented in codebase |
| Message history | Custom list management | `ChatState` dataclass | Matches existing pattern |
| Keyboard shortcuts | Custom keypress tracking | `page.on_keyboard_event` | Flet's built-in handler |

**Key insight:** The codebase already has patterns for state management (listener/notify), streaming (AIGateway), and resizable panels (ResizableSplitPanel). Extend these rather than creating new patterns.

## Common Pitfalls

### Pitfall 1: Tab Key Capture for Accept
**What goes wrong:** Tab key moves focus instead of accepting suggestion
**Why it happens:** Flet's default Tab behavior is focus navigation
**How to avoid:** Use `page.on_keyboard_event` to intercept Tab when ghost text is visible; programmatically manage focus
**Warning signs:** Tab keypress has no effect or jumps to different control

### Pitfall 2: Ghost Text Position Sync
**What goes wrong:** Ghost text appears at wrong position relative to cursor
**Why it happens:** TextField and overlay Text have different padding/positioning
**How to avoid:** Match exact padding values; use monospace font for predictable character widths; account for scroll position
**Warning signs:** Ghost text offset from cursor, misaligned with typed text

### Pitfall 3: Streaming Response Memory Leaks
**What goes wrong:** Memory grows unbounded during long streaming sessions
**Why it happens:** Appending to strings/lists without cleanup
**How to avoid:** Use generators for streaming; clear intermediate buffers; implement message limits
**Warning signs:** App slowdown during extended AI conversations

### Pitfall 4: Token Count Inaccuracy
**What goes wrong:** Displayed token count differs significantly from API usage
**Why it happens:** Different providers use different tokenizers
**How to avoid:** Use tiktoken for OpenAI/GPT models; use heuristics or API for Anthropic; display as estimate
**Warning signs:** User complaints about unexpected costs, context truncation

### Pitfall 5: Diff Application Race Conditions
**What goes wrong:** Applying diff to outdated content corrupts file
**Why it happens:** User edits file while viewing diff preview
**How to avoid:** Lock editing during diff preview; re-validate diff applicability before apply; show warning if content changed
**Warning signs:** Applied diff produces garbage output, lost user changes

### Pitfall 6: Large Context Token Overflow
**What goes wrong:** Request fails due to exceeding model context limit
**Why it happens:** Including too much code context in chat
**How to avoid:** Implement pre-flight token counting; warn user before truncation; offer manual context selection
**Warning signs:** API errors about context length, silent truncation

## Code Examples

Verified patterns from official sources:

### Flet Chat Panel Layout
```python
# Source: https://flet.dev/docs/tutorials/python-chat/
class ChatPanel(ft.Column):
    """Chat panel for AI code assistance."""

    def __init__(self, page: ft.Page, state: ChatState):
        super().__init__()
        self._page = page
        self.state = state
        self.expand = True

    def build(self):
        # Message list with auto-scroll
        self.message_list = ft.ListView(
            auto_scroll=True,
            expand=True,
            spacing=10,
        )

        # Input field
        self.input_field = ft.TextField(
            hint_text="Ask about your code...",
            autofocus=True,
            shift_enter=True,  # Shift+Enter for newline
            min_lines=1,
            max_lines=5,
            filled=True,
            expand=True,
            on_submit=self._on_submit,
        )

        # Send button
        send_btn = ft.IconButton(
            icon=ft.Icons.SEND,
            on_click=self._on_submit,
        )

        return ft.Column(
            controls=[
                self.message_list,
                ft.Row([self.input_field, send_btn]),
            ],
            expand=True,
        )
```

### Keyboard Shortcut Registration
```python
# Source: https://flet.dev/docs/cookbook/keyboard-shortcuts/
def setup_keyboard_shortcuts(page: ft.Page, editor_view):
    """Register keyboard shortcuts for AI features."""

    def on_keyboard(e: ft.KeyboardEvent):
        # Ctrl+Shift+A: Toggle AI panel
        if e.ctrl and e.shift and e.key == "A":
            editor_view.toggle_ai_panel()
            return

        # Tab: Accept suggestion (when visible)
        if e.key == "Tab" and editor_view.has_suggestion():
            editor_view.accept_suggestion()
            # Note: Cannot truly prevent default in Flet
            return

        # Escape: Dismiss suggestion
        if e.key == "Escape" and editor_view.has_suggestion():
            editor_view.dismiss_suggestion()
            return

    page.on_keyboard_event = on_keyboard
```

### Token Counting with tiktoken
```python
# Source: https://github.com/openai/tiktoken
import tiktoken

class TokenCounter:
    """Estimate token counts for different providers."""

    def __init__(self):
        # cl100k_base for GPT-4/3.5, text-embedding models
        self._openai_enc = tiktoken.get_encoding("cl100k_base")
        # p50k_base as approximation for other providers
        self._fallback_enc = tiktoken.get_encoding("p50k_base")

    def count_tokens(self, text: str, provider: str = "openai") -> int:
        """Count tokens for the given text and provider."""
        if provider in ("openai", "gpt-4", "gpt-3.5"):
            return len(self._openai_enc.encode(text))
        else:
            # Approximation for Anthropic, Gemini, etc.
            # Use p50k as rough estimate
            return len(self._fallback_enc.encode(text))

    def estimate_heuristic(self, text: str) -> int:
        """Quick heuristic: ~4 chars per token average."""
        return len(text) // 4
```

### Diff Rendering Component
```python
# Source: difflib documentation + Flet patterns
class DiffView(ft.Column):
    """Render diff with syntax-colored additions/deletions."""

    ADDED_COLOR = "#22863a"    # GitHub green
    REMOVED_COLOR = "#cb2431"  # GitHub red
    CONTEXT_COLOR = "#6a737d"  # GitHub gray

    def __init__(self, hunks: list[DiffHunk]):
        super().__init__()
        self.hunks = hunks
        self.spacing = 0

    def build(self):
        lines = []
        for hunk in self.hunks:
            # Hunk header
            lines.append(ft.Container(
                content=ft.Text(
                    f"@@ -{hunk.source_start},{hunk.source_length} "
                    f"+{hunk.target_start},{hunk.target_length} @@",
                    color=self.CONTEXT_COLOR,
                    font_family="monospace",
                    size=12,
                ),
                bgcolor="#f1f8ff",
            ))

            for line in hunk.lines:
                if line.startswith("+"):
                    color = self.ADDED_COLOR
                    bg = "#e6ffec"
                elif line.startswith("-"):
                    color = self.REMOVED_COLOR
                    bg = "#ffebe9"
                else:
                    color = self.CONTEXT_COLOR
                    bg = None

                lines.append(ft.Container(
                    content=ft.Text(
                        line,
                        color=color,
                        font_family="monospace",
                        size=12,
                    ),
                    bgcolor=bg,
                ))

        self.controls = lines
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Full-file context | Smart context selection | 2024+ | Reduces token usage, improves relevance |
| Popup autocomplete | Inline ghost text | 2023+ | Less intrusive UX (Copilot-style) |
| Blocking API calls | Streaming responses | 2023+ | Better perceived performance |
| Single model | Multi-provider routing | 2024+ | Cost optimization, capability matching |

**Deprecated/outdated:**
- google-generativeai: Replaced by google-genai SDK (already updated in codebase)
- Anthropic TypeScript tokenizer: Not accurate for Claude 3+ models

## Open Questions

Things that couldn't be fully resolved:

1. **Tab Key Prevention in Flet**
   - What we know: `page.on_keyboard_event` captures Tab but cannot prevent default focus behavior
   - What's unclear: Whether Flet has any mechanism to prevent default key actions
   - Recommendation: Use alternative shortcut (Enter when suggestion visible) or accept slight focus jump with immediate refocus

2. **Claude Token Counting Accuracy**
   - What we know: Anthropic doesn't publish their tokenizer; tiktoken p50k_base is rough estimate
   - What's unclear: How inaccurate the estimate is (could be 10-20% off)
   - Recommendation: Use tiktoken estimate with "~" prefix to indicate approximation; offer API count on demand

3. **Flet Text Cursor Position Access**
   - What we know: TextField has `value` but cursor position is not directly exposed
   - What's unclear: Whether there's an undocumented property or workaround
   - Recommendation: Track cursor position via on_change events and text length; may limit ghost text positioning precision

## Sources

### Primary (HIGH confidence)
- Flet documentation (keyboard shortcuts, Stack, TextField): https://flet.dev/docs/
- Python difflib documentation: https://docs.python.org/3/library/difflib.html
- tiktoken GitHub: https://github.com/openai/tiktoken
- Existing codebase patterns: src/ai/gateway.py, src/ui/views/code_editor/state.py

### Secondary (MEDIUM confidence)
- Flet chat tutorial: https://flet.dev/docs/tutorials/python-chat/
- Token counting guide: https://www.propelcode.ai/blog/token-counting-tiktoken-anthropic-gemini-guide-2025
- unidiff library: https://pypi.org/project/unidiff/

### Tertiary (LOW confidence)
- Flet GitHub discussions on Tab key handling
- Community patterns for ghost text implementation (no official Flet support)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Uses established libraries (difflib, tiktoken) and existing codebase patterns
- Architecture: MEDIUM - Ghost text pattern is custom; follows Flet Stack docs but untested
- Pitfalls: MEDIUM - Based on known Flet limitations and general streaming patterns
- Code examples: HIGH - From official documentation and existing codebase

**Research date:** 2026-01-18
**Valid until:** 2026-02-18 (30 days - Flet updates frequently)
