# src/ui/views/code_editor/ai_panel/__init__.py
"""AI Panel components for code editor.

Provides ChatState for managing chat panel state and ChatMessage
for representing individual messages in the conversation.
Also provides ChatPanel for the main chat interface,
GhostTextOverlay for inline code suggestions,
and DiffPreview for reviewing AI-suggested code changes.
"""

from .chat_panel import ChatPanel
from .chat_state import ChatMessage, ChatState
from .diff_preview import DiffPreview
from .ghost_text import GhostTextOverlay, Suggestion

__all__ = [
    "ChatMessage",
    "ChatPanel",
    "ChatState",
    "DiffPreview",
    "GhostTextOverlay",
    "Suggestion",
]
