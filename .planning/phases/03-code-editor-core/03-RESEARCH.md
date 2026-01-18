# Phase 3: Code Editor Core - Research

**Researched:** 2026-01-18
**Domain:** Code editing with syntax highlighting, file management, tabbed interface
**Confidence:** HIGH

## Summary

This phase implements a code editor within the existing Flet-based Skynette application. The core challenge is combining Pygments syntax highlighting (a Python library) with Flet's UI controls to create a VS Code-like experience. Since Flet lacks native code editor widgets, we must build a custom component using TextField for editing and Text/Container elements for rendering highlighted code.

The key architectural decision is using Pygments for tokenization and rendering the highlighted output through Flet controls rather than through HTML/CSS (Pygments' native output). This requires converting Pygments tokens to Flet TextSpan objects with appropriate styling. The file tree must be custom-built since Flet has no TreeView control (planned for Flet 1.0, 2025). Resizable panels require GestureDetector with horizontal drag events.

**Primary recommendation:** Build a layered architecture with: (1) PygmentsHighlighter service for tokenization, (2) CodeEditor component for rendering/editing, (3) FileTree component using ListView with indentation, (4) TabManager for multi-file handling, (5) FileService for disk operations.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Pygments | 2.17+ | Syntax highlighting (598 languages) | Industry standard, Python-native, lexer per language |
| pathlib | stdlib | File path operations | Modern, OOP-based, cross-platform |
| aiofiles | 24.1+ | Async file I/O | Non-blocking file operations for UI responsiveness |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| watchdog | 4.0+ | File system monitoring | Optional: auto-reload on external changes |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Pygments | Tree-sitter | Tree-sitter is faster but requires native bindings; Pygments is pure Python |
| aiofiles | sync I/O | Sync I/O blocks UI thread; small files may be acceptable |
| watchdog | polling | Polling is simpler but less efficient; defer to Phase 5 if needed |

**Installation:**
```bash
pip install pygments aiofiles
# Optional: pip install watchdog
```

## Architecture Patterns

### Recommended Project Structure
```
src/ui/
├── views/
│   └── code_editor/
│       ├── __init__.py          # CodeEditorView (main view)
│       ├── state.py             # EditorState dataclass with listener pattern
│       ├── editor.py            # CodeEditor component (text + highlighting)
│       ├── file_tree.py         # FileTree component (directory browser)
│       ├── tab_bar.py           # TabBar component (file tabs)
│       └── toolbar.py           # EditorToolbar component
├── components/
│   └── code_editor/
│       ├── line_numbers.py      # Line number gutter
│       ├── minimap.py           # Code minimap (scaled overview)
│       └── resizable_panel.py   # Resizable split container
└── services/
    └── editor/
        ├── highlighter.py       # PygmentsHighlighter service
        ├── file_service.py      # File I/O operations
        └── file_icons.py        # Extension-to-icon mapping
```

### Pattern 1: State Container with Listener/Notify
**What:** Centralized state management following Phase 1 patterns (see `src/ui/views/ai_hub/state.py`)
**When to use:** Always for editor state (open files, active tab, cursor position, dirty flags)
**Example:**
```python
# Source: Existing pattern from src/ui/views/ai_hub/state.py
from dataclasses import dataclass, field
from collections.abc import Callable
from typing import Any

@dataclass
class OpenFile:
    path: str
    content: str
    language: str
    is_dirty: bool = False
    scroll_position: int = 0
    cursor_position: int = 0

@dataclass
class EditorState:
    """Centralized state for code editor components."""

    open_files: list[OpenFile] = field(default_factory=list)
    active_file_index: int = -1
    file_tree_root: str | None = None
    sidebar_width: int = 250

    _listeners: list[Callable[[], None]] = field(default_factory=list, repr=False)

    def add_listener(self, callback: Callable[[], None]) -> None:
        self._listeners.append(callback)

    def notify(self) -> None:
        for listener in self._listeners:
            listener()

    def open_file(self, path: str, content: str, language: str) -> None:
        # Check if already open
        for i, f in enumerate(self.open_files):
            if f.path == path:
                self.active_file_index = i
                self.notify()
                return

        self.open_files.append(OpenFile(path=path, content=content, language=language))
        self.active_file_index = len(self.open_files) - 1
        self.notify()
```

### Pattern 2: Pygments Token-to-Flet Conversion
**What:** Convert Pygments tokens to Flet TextSpan objects for rich text rendering
**When to use:** For rendering syntax-highlighted code in the editor
**Example:**
```python
# Source: Pygments API docs + Flet Text/TextSpan docs
import flet as ft
from pygments import lex
from pygments.lexers import get_lexer_by_name, get_lexer_for_filename
from pygments.token import Token

class PygmentsHighlighter:
    """Convert code to Flet TextSpans with syntax highlighting."""

    # Token type to color mapping (GitHub Dark theme)
    TOKEN_COLORS = {
        Token.Keyword: "#ff7b72",
        Token.Keyword.Constant: "#79c0ff",
        Token.Name.Function: "#d2a8ff",
        Token.Name.Class: "#f0883e",
        Token.String: "#a5d6ff",
        Token.Comment: "#8b949e",
        Token.Number: "#79c0ff",
        Token.Operator: "#ff7b72",
        Token.Punctuation: "#c9d1d9",
        Token.Name.Builtin: "#ffa657",
    }
    DEFAULT_COLOR = "#c9d1d9"

    def highlight(self, code: str, language: str) -> list[ft.TextSpan]:
        """Convert code to list of styled TextSpans."""
        try:
            lexer = get_lexer_by_name(language)
        except Exception:
            # Fallback: return unstyled
            return [ft.TextSpan(code, style=ft.TextStyle(color=self.DEFAULT_COLOR))]

        spans = []
        for token_type, token_value in lex(code, lexer):
            color = self._get_color_for_token(token_type)
            spans.append(ft.TextSpan(
                token_value,
                style=ft.TextStyle(color=color, font_family="monospace")
            ))
        return spans

    def _get_color_for_token(self, token_type) -> str:
        """Get color for token type, checking parent types."""
        while token_type:
            if token_type in self.TOKEN_COLORS:
                return self.TOKEN_COLORS[token_type]
            token_type = token_type.parent
        return self.DEFAULT_COLOR
```

### Pattern 3: Custom File Tree with ListView
**What:** Build file tree using ListView with indentation levels
**When to use:** For directory browser (Flet has no native TreeView)
**Example:**
```python
# Source: Flet ListView docs + custom implementation
import flet as ft
from pathlib import Path

class FileTreeItem:
    def __init__(self, path: Path, level: int = 0):
        self.path = path
        self.level = level
        self.is_expanded = False
        self.is_dir = path.is_dir()

class FileTree(ft.Column):
    """File tree using ListView with manual expansion."""

    def __init__(self, root_path: str, on_file_select: Callable[[str], None]):
        super().__init__()
        self.root = Path(root_path)
        self.on_file_select = on_file_select
        self.items: list[FileTreeItem] = []
        self.expand = True

    def build(self):
        self._load_directory(self.root, level=0)
        return ft.ListView(
            controls=[self._build_item(item) for item in self.items],
            expand=True,
            spacing=2,
        )

    def _build_item(self, item: FileTreeItem) -> ft.Container:
        indent = item.level * 16
        icon = self._get_icon(item)

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(icon, size=16),
                    ft.Text(item.path.name, size=13),
                ],
                spacing=4,
            ),
            padding=ft.padding.only(left=indent, top=4, bottom=4, right=8),
            on_click=lambda e, i=item: self._handle_click(i),
        )

    def _get_icon(self, item: FileTreeItem) -> str:
        if item.is_dir:
            return ft.Icons.FOLDER if not item.is_expanded else ft.Icons.FOLDER_OPEN
        # File icon based on extension
        return self._get_file_icon(item.path.suffix)
```

### Pattern 4: Resizable Split Panel with GestureDetector
**What:** Horizontal drag to resize sidebar/editor split
**When to use:** For adjustable file tree width
**Example:**
```python
# Source: Flet GestureDetector docs
import flet as ft

class ResizableSplitPanel(ft.Row):
    """Two-panel layout with draggable divider."""

    def __init__(self, left: ft.Control, right: ft.Control, initial_width: int = 250):
        super().__init__()
        self.left_panel = left
        self.right_panel = right
        self.left_width = initial_width
        self.expand = True

    def build(self):
        divider = ft.GestureDetector(
            content=ft.Container(
                width=4,
                bgcolor=ft.Colors.with_opacity(0.3, ft.Colors.WHITE),
            ),
            on_horizontal_drag_update=self._on_drag,
            mouse_cursor=ft.MouseCursor.RESIZE_LEFT_RIGHT,
        )

        return ft.Row(
            controls=[
                ft.Container(content=self.left_panel, width=self.left_width),
                divider,
                ft.Container(content=self.right_panel, expand=True),
            ],
            expand=True,
        )

    def _on_drag(self, e: ft.DragUpdateEvent):
        self.left_width = max(150, min(500, self.left_width + e.delta_x))
        self.controls[0].width = self.left_width
        self.update()
```

### Pattern 5: Tab Reordering with Draggable/DragTarget
**What:** Drag tabs to reorder using Flet's drag-and-drop
**When to use:** For reorderable file tabs
**Example:**
```python
# Source: Flet Draggable docs + Trello tutorial pattern
import flet as ft

class DraggableTab(ft.Draggable):
    def __init__(self, file_path: str, label: str, on_reorder: Callable):
        super().__init__(
            group="tabs",
            content=self._build_tab(label),
            content_feedback=self._build_tab(label, dragging=True),
        )
        self.file_path = file_path
        self.on_reorder = on_reorder
```

### Anti-Patterns to Avoid
- **Rendering all lines at once:** For large files, only render visible lines. Use ListView with item_extent for virtualization.
- **Synchronous file I/O:** Always use async file operations to prevent UI freezing.
- **Storing highlighted spans in state:** Re-highlight on render, not on edit. Highlighting is fast.
- **Direct page.update() everywhere:** Use state container with notify() for coordinated updates.
- **Building full tree on load:** Lazy-load subdirectories on expand for large projects.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Syntax highlighting | Regex-based tokenizer | Pygments | 598 languages, edge cases handled, maintained |
| Language detection | Extension mapping | `pygments.lexers.get_lexer_for_filename()` | Handles ambiguous extensions, content guessing |
| File path handling | String manipulation | `pathlib.Path` | Cross-platform, OOP, handles edge cases |
| Async file I/O | Thread pools | `aiofiles` | Proper async/await, non-blocking |
| File watching | Polling loop | `watchdog` (optional) | Uses OS-native inotify/FSEvents |

**Key insight:** Pygments does the heavy lifting for syntax highlighting. The challenge is rendering its output in Flet, not parsing code.

## Common Pitfalls

### Pitfall 1: TextField Character Limit
**What goes wrong:** Flet TextField may have performance issues with very large content (10k+ lines)
**Why it happens:** Flutter's TextField isn't optimized for code editing
**How to avoid:**
- Set reasonable file size limit (warn at 50KB, refuse at 500KB)
- Consider read-only mode for very large files
- Use virtualized line rendering for display, TextField for input
**Warning signs:** UI lag when typing, slow scrolling

### Pitfall 2: Tab.content Deprecation in Flet 0.80+
**What goes wrong:** Using `Tab(content=...)` causes errors or warnings
**Why it happens:** Flet 0.80 deprecated Tab.content in favor of TabBar + TabBarView pattern
**How to avoid:** Use TabBar with TabBarView as separate controls (see ai_hub pattern)
**Warning signs:** Deprecation warnings, content not rendering

### Pitfall 3: Memory Leaks from Open Files
**What goes wrong:** Memory grows as user opens/closes files
**Why it happens:** Event listeners, file handles, or control references not cleaned up
**How to avoid:**
- Implement explicit `dispose()` methods on components
- Remove state listeners when tabs close
- Clear file content from state on close
- Use weak references where appropriate
**Warning signs:** Memory growth over time, slow performance after many file opens

### Pitfall 4: Cursor/Selection Sync Issues
**What goes wrong:** Cursor position doesn't match where user clicks in highlighted text
**Why it happens:** Mismatch between TextField content and rendered TextSpans
**How to avoid:**
- Keep single source of truth for content (TextField)
- Highlight in overlay or separate display control
- Sync scroll positions between display and edit areas
**Warning signs:** Clicking in wrong place, selection off by characters

### Pitfall 5: File Tree Performance with Large Projects
**What goes wrong:** UI freezes when opening directory with thousands of files
**Why it happens:** Loading all files upfront, not using virtualization
**How to avoid:**
- Lazy-load subdirectories on expand only
- Use ListView (virtualized) not Column
- Set `item_extent` for consistent performance
- Limit visible depth initially
**Warning signs:** Slow initial load, scroll lag in file tree

### Pitfall 6: Unsaved Changes Lost on Close
**What goes wrong:** User closes tab without saving, loses work
**Why it happens:** No dirty tracking or close confirmation
**How to avoid:**
- Track `is_dirty` flag in OpenFile state
- Show visual indicator (dot/asterisk) on dirty tabs
- Prompt on close: Save / Don't Save / Cancel
- Handle window close event for all dirty files
**Warning signs:** User complaints about lost work

## Code Examples

Verified patterns from official sources:

### Pygments Tokenization
```python
# Source: https://pygments.org/docs/quickstart/
from pygments import lex
from pygments.lexers import get_lexer_by_name, get_lexer_for_filename

# Get lexer by language name
lexer = get_lexer_by_name('python')

# Or by filename
lexer = get_lexer_for_filename('example.py')

# Tokenize code
code = 'def hello():\n    print("Hello")'
for token_type, token_value in lex(code, lexer):
    print(f"{token_type}: {repr(token_value)}")
```

### Async File Operations
```python
# Source: aiofiles PyPI + Python pathlib docs
import aiofiles
from pathlib import Path

async def read_file(path: str) -> str:
    async with aiofiles.open(path, mode='r', encoding='utf-8') as f:
        return await f.read()

async def write_file(path: str, content: str) -> None:
    async with aiofiles.open(path, mode='w', encoding='utf-8') as f:
        await f.write(content)

def list_directory(path: str, include_hidden: bool = True) -> list[Path]:
    """List directory contents sorted (folders first, then files)."""
    p = Path(path)
    items = list(p.iterdir())
    if not include_hidden:
        items = [i for i in items if not i.name.startswith('.')]
    # Sort: directories first, then by name
    return sorted(items, key=lambda x: (not x.is_dir(), x.name.lower()))
```

### Flet TabBar + TabBarView Pattern
```python
# Source: src/ui/views/ai_hub/__init__.py (existing project pattern)
import flet as ft

# Create tab headers
tab_bar = ft.TabBar(
    tabs=[
        ft.Tab(label="File 1"),
        ft.Tab(label="File 2"),
    ],
    on_change=lambda e: handle_tab_change(e.control.selected_index),
)

# Create tab content view
tab_view = ft.TabBarView(
    controls=[
        editor_for_file_1,
        editor_for_file_2,
    ],
    expand=True,
)

# Wrap in Tabs controller
tabs = ft.Tabs(
    content=ft.Column([tab_bar, tab_view], expand=True),
    length=2,
    expand=True,
)
```

### Flet Rich Text with TextSpan
```python
# Source: Flet Text docs
import flet as ft

highlighted_text = ft.Text(
    spans=[
        ft.TextSpan("def ", style=ft.TextStyle(color="#ff7b72")),
        ft.TextSpan("hello", style=ft.TextStyle(color="#d2a8ff")),
        ft.TextSpan("():", style=ft.TextStyle(color="#c9d1d9")),
    ],
    selectable=True,
    font_family="monospace",
)
```

### GestureDetector Drag Events
```python
# Source: https://flet.dev/docs/controls/gesturedetector/
import flet as ft

def handle_drag(e: ft.DragUpdateEvent):
    print(f"Delta X: {e.delta_x}, Delta Y: {e.delta_y}")
    # e.local_x, e.local_y - position relative to control
    # e.global_x, e.global_y - position relative to screen

detector = ft.GestureDetector(
    content=ft.Container(width=10, height=100, bgcolor=ft.Colors.GREY),
    on_horizontal_drag_start=lambda e: print("Drag started"),
    on_horizontal_drag_update=handle_drag,
    on_horizontal_drag_end=lambda e: print("Drag ended"),
    mouse_cursor=ft.MouseCursor.RESIZE_LEFT_RIGHT,
)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Tab.content | TabBar + TabBarView | Flet 0.80 | Must use new API for tabs |
| sync file I/O | aiofiles async | Python 3.5+ | Non-blocking UI |
| os.path | pathlib.Path | Python 3.4+ | Cleaner, cross-platform |
| Pygments HTML output | Token iteration + custom rendering | Always | For non-HTML targets (Flet) |

**Deprecated/outdated:**
- `Tab(content=...)`: Use TabBar + TabBarView pattern instead
- `os.walk()` for small trees: Use `pathlib.Path.iterdir()` or `Path.walk()` (Python 3.12+)
- Inline Pygments styles: Use token iteration for Flet TextSpan rendering

## Open Questions

Things that couldn't be fully resolved:

1. **Large File Performance**
   - What we know: ListView virtualization helps, TextField may lag at 10k+ lines
   - What's unclear: Exact performance ceiling for Flet TextField with large content
   - Recommendation: Implement with size warnings; test with 1k, 5k, 10k line files; add read-only mode fallback

2. **Minimap Implementation**
   - What we know: No built-in minimap in Flet; must be custom
   - What's unclear: Best approach for scaled code overview (Canvas? Scaled container?)
   - Recommendation: Start simple (scrollbar with position indicator), enhance to true minimap in Phase 4 if needed

3. **Undo/Redo**
   - What we know: Flet TextField inherits Flutter's basic undo, but no explicit API in Flet docs
   - What's unclear: How much undo history is maintained, how to programmatically undo
   - Recommendation: Rely on native TextField undo (Ctrl+Z), document limitation

4. **Middle-click Tab Close**
   - What we know: Flet supports on_click, but middle-click detection unclear
   - What's unclear: How to detect middle mouse button specifically
   - Recommendation: Implement X button close first; investigate GestureDetector for middle-click

## Sources

### Primary (HIGH confidence)
- Pygments API documentation: https://pygments.org/docs/api/
- Pygments Quickstart: https://pygments.org/docs/quickstart/
- Flet TextField docs: https://flet.dev/docs/controls/textfield/
- Flet GestureDetector docs: https://flet.dev/docs/controls/gesturedetector/
- Flet Draggable docs: https://flet.dev/docs/controls/draggable/
- Flet Large Lists cookbook: https://flet.dev/docs/cookbook/large-lists/
- Flet Tabs docs: https://flet.dev/docs/controls/tabs/
- Existing project patterns: `src/ui/views/ai_hub/state.py`, `src/ui/views/ai_hub/__init__.py`

### Secondary (MEDIUM confidence)
- aiofiles PyPI: https://pypi.org/project/aiofiles/
- watchdog PyPI: https://pypi.org/project/watchdog/
- Flet drag-and-drop cookbook: https://flet.dev/docs/cookbook/drag-and-drop/
- Flet Trello tutorial (reordering): https://flet.dev/docs/tutorials/trello-clone/

### Tertiary (LOW confidence)
- Flet code highlighting gist (community): https://gist.github.com/Bbalduzz/dc6e5037ccc505b27adc1e5f6a34d687
- TreeView feature request status (GitHub issues): https://github.com/flet-dev/flet/issues/961

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Pygments and pathlib are well-documented, aiofiles is standard
- Architecture: HIGH - Follows established project patterns from Phase 1
- Pitfalls: MEDIUM - Performance concerns based on search results, not benchmarked
- File Tree: MEDIUM - No native TreeView, custom implementation required
- Minimap: LOW - No direct guidance, requires experimentation

**Research date:** 2026-01-18
**Valid until:** 2026-02-18 (30 days - Flet and Pygments are stable)

---

*Phase: 03-code-editor-core*
*Research completed: 2026-01-18*
