# src/ui/views/code_editor/ai_panel/chat_state.py
"""Centralized state for AI chat panel in the code editor.

Follows the listener/notify pattern from EditorState for reactive updates.
"""

import time
from collections.abc import Callable
from dataclasses import dataclass, field


@dataclass
class ChatMessage:
    """A message in the AI chat conversation.

    Attributes:
        role: Message role - "user", "assistant", or "system".
        content: The message text content.
        timestamp: Unix timestamp when message was created.
        code_context: Optional attached code snippet for context.
    """

    role: str  # "user", "assistant", "system"
    content: str
    timestamp: float = field(default_factory=time.time)
    code_context: str | None = None


@dataclass
class ChatState:
    """Centralized state for AI chat panel in code editor.

    Follows the listener/notify pattern from EditorState for reactive
    updates across chat panel components (message list, input, controls).

    Example:
        state = ChatState()
        state.add_listener(lambda: page.update())
        state.add_message("user", "Explain this code")
        # Listener called, UI updates
    """

    messages: list[ChatMessage] = field(default_factory=list)
    is_streaming: bool = False
    selected_provider: str | None = None
    context_mode: str = "current_file"  # current_file, imports, project

    _listeners: list[Callable[[], None]] = field(default_factory=list, repr=False)

    def add_listener(self, callback: Callable[[], None]) -> None:
        """Register a callback to be notified of state changes.

        Args:
            callback: Function to call when state changes.
        """
        self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[], None]) -> None:
        """Unregister a callback.

        Args:
            callback: Function to remove from listeners.
        """
        if callback in self._listeners:
            self._listeners.remove(callback)

    def notify(self) -> None:
        """Notify all listeners of state change."""
        for listener in self._listeners:
            listener()

    def add_message(
        self, role: str, content: str, code_context: str | None = None
    ) -> None:
        """Add a new message to the conversation.

        Args:
            role: Message role - "user", "assistant", or "system".
            content: The message text content.
            code_context: Optional attached code snippet.
        """
        message = ChatMessage(role=role, content=content, code_context=code_context)
        self.messages.append(message)
        self.notify()

    def update_last_message(self, content: str) -> None:
        """Update the content of the last message.

        Useful for streaming responses where content is built incrementally.

        Args:
            content: New content to set on last message.
        """
        if self.messages:
            self.messages[-1].content = content
            self.notify()

    def clear_messages(self) -> None:
        """Clear all messages from the conversation."""
        self.messages.clear()
        self.notify()

    def set_streaming(self, is_streaming: bool) -> None:
        """Set streaming state.

        Args:
            is_streaming: True if currently streaming a response.
        """
        self.is_streaming = is_streaming
        self.notify()

    def set_provider(self, provider: str) -> None:
        """Set the selected AI provider.

        Args:
            provider: Provider name (e.g., "openai", "anthropic").
        """
        self.selected_provider = provider
        self.notify()

    def set_context_mode(self, mode: str) -> None:
        """Set the context mode for code context.

        Args:
            mode: Context mode - "current_file", "imports", or "project".
        """
        self.context_mode = mode
        self.notify()

    def dispose(self) -> None:
        """Clear all state and listeners."""
        self._listeners.clear()
        self.messages.clear()
        self.is_streaming = False
        self.selected_provider = None
        self.context_mode = "current_file"
