# src/ui/views/code_editor/ai_panel/__init__.py
"""AI Panel components for code editor.

Provides ChatState for managing chat panel state and ChatMessage
for representing individual messages in the conversation.
"""

from .chat_state import ChatMessage, ChatState

__all__ = ["ChatMessage", "ChatState"]
