# src/ui/views/code_editor/ai_panel/__init__.py
"""AI Panel components for code editor.

Provides ChatState for managing chat panel state and ChatMessage
for representing individual messages in the conversation.
Also provides ChatPanel for the main chat interface,
GhostTextOverlay for inline code suggestions,
DiffPreview for reviewing AI-suggested code changes,
and RAGContextProvider for codebase context retrieval.
"""

from .chat_panel import ChatPanel
from .chat_state import ChatMessage, ChatState
from .diff_preview import DiffPreview
from .ghost_text import GhostTextOverlay, Suggestion
from .rag_context import RAGContextProvider

__all__ = [
    "ChatMessage",
    "ChatPanel",
    "ChatState",
    "DiffPreview",
    "GhostTextOverlay",
    "RAGContextProvider",
    "Suggestion",
]
