# src/ui/views/code_editor/ai_panel/chat_panel.py
"""AI chat panel for code assistance in the code editor.

Provides a chat interface for users to interact with AI about their code.
Features message history with streaming support, provider selection,
code context attachment, and RAG-based codebase context.
"""

import asyncio
from collections.abc import Callable
from typing import TYPE_CHECKING

import flet as ft

from src.ai.gateway import AIGateway, AIMessage
from src.ui.theme import SkynetteTheme
from src.ui.views.code_editor.ai_panel.chat_state import ChatMessage, ChatState

if TYPE_CHECKING:
    from src.ui.views.code_editor.ai_panel.rag_context import RAGContextProvider


class ChatPanel(ft.Column):
    """AI chat panel for code assistance.

    Displays message history with streaming support, input field
    with send button, and provider selection dropdown.

    Layout:
    - Header with title and provider dropdown
    - Scrollable message list (auto-scroll to bottom)
    - Input row with TextField and send button

    Example:
        panel = ChatPanel(page=page, state=chat_state, gateway=gateway)
    """

    def __init__(
        self,
        page: ft.Page,
        state: ChatState,
        gateway: AIGateway,
        on_include_code: Callable[[], str] | None = None,
        on_code_suggestion: Callable[[str], None] | None = None,
        rag_provider: "RAGContextProvider | None" = None,
        get_project_root: Callable[[], str | None] | None = None,
    ):
        """Initialize the chat panel.

        Args:
            page: Flet page reference.
            state: ChatState instance for managing conversation state.
            gateway: AIGateway instance for AI communication.
            on_include_code: Optional callback to get selected code from editor.
            on_code_suggestion: Optional callback when AI suggests code changes.
            rag_provider: Optional RAGContextProvider for codebase context.
            get_project_root: Optional callback to get current project root path.
        """
        super().__init__()
        self._page_ref = page
        self.state = state
        self.gateway = gateway
        self._on_include_code_callback = on_include_code
        self._on_code_suggestion = on_code_suggestion
        self._rag_provider = rag_provider
        self._get_project_root = get_project_root

        self.expand = True
        self.spacing = 0

        # Pending code context for next message
        self._pending_code_context: str | None = None

        # Last retrieved RAG sources for display
        self._last_sources: list[dict] = []

        # UI components (initialized in build)
        self._message_list: ft.ListView | None = None
        self._input_field: ft.TextField | None = None
        self._provider_dropdown: ft.Dropdown | None = None
        self._send_button: ft.IconButton | None = None
        self._include_code_btn: ft.IconButton | None = None

        # Register state listener
        self.state.add_listener(self._on_state_change)

        # Build UI
        self.build()

    def build(self) -> None:
        """Build the chat panel UI components."""
        # Provider dropdown
        provider_options = [
            ft.dropdown.Option(key=name, text=name.capitalize())
            for name in self.gateway.providers.keys()
        ]
        if not provider_options:
            provider_options = [ft.dropdown.Option(key="none", text="No providers")]

        self._provider_dropdown = ft.Dropdown(
            options=provider_options,
            value=self.state.selected_provider or self.gateway.default_provider,
            width=140,
            height=36,
            text_size=SkynetteTheme.FONT_SM,
            bgcolor=SkynetteTheme.BG_TERTIARY,
            border_color=SkynetteTheme.BORDER,
            color=SkynetteTheme.TEXT_PRIMARY,
            on_change=self._on_provider_change,
        )

        # Header row
        header = ft.Container(
            content=ft.Row(
                [
                    ft.Text(
                        "AI Assistant",
                        size=SkynetteTheme.FONT_MD,
                        weight=ft.FontWeight.W_600,
                        color=SkynetteTheme.TEXT_PRIMARY,
                    ),
                    ft.Container(expand=True),
                    self._provider_dropdown,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.padding.only(
                left=SkynetteTheme.SPACING_MD,
                right=SkynetteTheme.SPACING_MD,
                top=SkynetteTheme.SPACING_SM,
                bottom=SkynetteTheme.SPACING_SM,
            ),
            bgcolor=SkynetteTheme.BG_SECONDARY,
            border=ft.border.only(bottom=ft.BorderSide(1, SkynetteTheme.BORDER)),
        )

        # Message list
        self._message_list = ft.ListView(
            expand=True,
            auto_scroll=True,
            spacing=0,
            padding=ft.padding.all(SkynetteTheme.SPACING_SM),
        )
        self._rebuild_message_list()

        # Include code button
        self._include_code_btn = ft.IconButton(
            icon=ft.icons.CODE,
            icon_size=20,
            icon_color=SkynetteTheme.TEXT_SECONDARY,
            tooltip="Include selected code",
            on_click=self._on_include_code,
        )

        # Send button
        self._send_button = ft.IconButton(
            icon=ft.icons.SEND,
            icon_size=20,
            icon_color=SkynetteTheme.PRIMARY,
            tooltip="Send message",
            on_click=self._on_send,
        )

        # Input field
        self._input_field = ft.TextField(
            hint_text="Ask about your code...",
            hint_style=ft.TextStyle(
                color=SkynetteTheme.TEXT_MUTED,
                size=SkynetteTheme.FONT_SM,
            ),
            text_style=ft.TextStyle(
                color=SkynetteTheme.TEXT_PRIMARY,
                size=SkynetteTheme.FONT_SM,
            ),
            bgcolor=SkynetteTheme.BG_TERTIARY,
            border_color=SkynetteTheme.BORDER,
            focused_border_color=SkynetteTheme.PRIMARY,
            cursor_color=SkynetteTheme.PRIMARY,
            min_lines=1,
            max_lines=5,
            multiline=True,
            shift_enter=True,
            expand=True,
            on_submit=self._on_send,
        )

        # Input row
        input_row = ft.Container(
            content=ft.Row(
                [
                    self._include_code_btn,
                    self._input_field,
                    self._send_button,
                ],
                spacing=SkynetteTheme.SPACING_XS,
                vertical_alignment=ft.CrossAxisAlignment.END,
            ),
            padding=ft.padding.all(SkynetteTheme.SPACING_SM),
            bgcolor=SkynetteTheme.BG_SECONDARY,
            border=ft.border.only(top=ft.BorderSide(1, SkynetteTheme.BORDER)),
        )

        # Assemble layout
        self.controls = [
            header,
            ft.Container(
                content=self._message_list,
                expand=True,
                bgcolor=SkynetteTheme.BG_PRIMARY,
            ),
            input_row,
        ]

    def _build_message_bubble(
        self, msg: ChatMessage, sources: list[dict] | None = None
    ) -> ft.Control:
        """Build a message bubble for display.

        Args:
            msg: ChatMessage to render.
            sources: Optional list of RAG sources to display for assistant messages.

        Returns:
            Container with styled message bubble.
        """
        is_user = msg.role == "user"

        # Build content column
        content_controls: list[ft.Control] = []

        # Code context display (if present)
        if msg.code_context:
            code_display = ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Icon(
                                    ft.icons.CODE,
                                    size=14,
                                    color=SkynetteTheme.TEXT_MUTED,
                                ),
                                ft.Text(
                                    "Code context",
                                    size=SkynetteTheme.FONT_XS,
                                    color=SkynetteTheme.TEXT_MUTED,
                                ),
                            ],
                            spacing=4,
                        ),
                        ft.Container(
                            content=ft.Text(
                                msg.code_context[:500]
                                + ("..." if len(msg.code_context) > 500 else ""),
                                size=SkynetteTheme.FONT_XS,
                                font_family="monospace",
                                color=SkynetteTheme.TEXT_SECONDARY,
                                selectable=True,
                            ),
                            bgcolor=SkynetteTheme.BG_PRIMARY,
                            border_radius=4,
                            padding=SkynetteTheme.SPACING_XS,
                        ),
                    ],
                    spacing=4,
                ),
                padding=ft.padding.only(bottom=SkynetteTheme.SPACING_XS),
            )
            content_controls.append(code_display)

        # Message text
        content_controls.append(
            ft.Text(
                msg.content if msg.content else "...",
                size=SkynetteTheme.FONT_SM,
                color=SkynetteTheme.TEXT_PRIMARY,
                selectable=True,
            )
        )

        # Sources display for assistant messages (collapsible)
        if not is_user and sources:
            sources_panel = self._build_sources_panel(sources)
            content_controls.append(sources_panel)

        # Role indicator
        role_text = "You" if is_user else "AI"
        role_color = SkynetteTheme.PRIMARY if is_user else SkynetteTheme.SECONDARY

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        role_text,
                        size=SkynetteTheme.FONT_XS,
                        color=role_color,
                        weight=ft.FontWeight.W_600,
                    ),
                    *content_controls,
                ],
                spacing=4,
            ),
            bgcolor=SkynetteTheme.BG_SECONDARY if is_user else SkynetteTheme.BG_TERTIARY,
            border_radius=SkynetteTheme.RADIUS_MD,
            padding=SkynetteTheme.SPACING_SM,
            margin=ft.margin.only(
                left=50 if is_user else 0,
                right=0 if is_user else 50,
                top=SkynetteTheme.SPACING_XS,
                bottom=SkynetteTheme.SPACING_XS,
            ),
        )

    def _build_sources_panel(self, sources: list[dict]) -> ft.Control:
        """Build a collapsible sources panel.

        Args:
            sources: List of source dicts with path, snippet, language, similarity.

        Returns:
            ExpansionTile control for sources display.
        """
        source_items = []
        for source in sources:
            path = source.get("path", "unknown")
            snippet = source.get("snippet", "")
            similarity = source.get("similarity", 0)

            # Extract filename from path
            import os

            filename = os.path.basename(path)

            source_item = ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Icon(
                                    ft.icons.INSERT_DRIVE_FILE,
                                    size=14,
                                    color=SkynetteTheme.TEXT_MUTED,
                                ),
                                ft.Text(
                                    filename,
                                    size=SkynetteTheme.FONT_XS,
                                    color=SkynetteTheme.TEXT_SECONDARY,
                                    weight=ft.FontWeight.W_500,
                                ),
                                ft.Container(expand=True),
                                ft.Text(
                                    f"{similarity:.0%}",
                                    size=SkynetteTheme.FONT_XS,
                                    color=SkynetteTheme.TEXT_MUTED,
                                ),
                            ],
                            spacing=4,
                        ),
                        ft.Text(
                            path,
                            size=SkynetteTheme.FONT_XS - 1,
                            color=SkynetteTheme.TEXT_MUTED,
                        ),
                        ft.Container(
                            content=ft.Text(
                                snippet,
                                size=SkynetteTheme.FONT_XS,
                                font_family="monospace",
                                color=SkynetteTheme.TEXT_SECONDARY,
                            ),
                            bgcolor=SkynetteTheme.BG_PRIMARY,
                            border_radius=4,
                            padding=SkynetteTheme.SPACING_XS,
                        ),
                    ],
                    spacing=2,
                ),
                padding=ft.padding.only(bottom=SkynetteTheme.SPACING_XS),
            )
            source_items.append(source_item)

        return ft.ExpansionTile(
            title=ft.Text(
                f"Sources ({len(sources)} files)",
                size=SkynetteTheme.FONT_XS,
                color=SkynetteTheme.TEXT_MUTED,
            ),
            initially_expanded=False,
            controls=source_items,
            bgcolor=SkynetteTheme.BG_PRIMARY,
            collapsed_bgcolor=SkynetteTheme.BG_PRIMARY,
            tile_padding=ft.padding.symmetric(
                horizontal=SkynetteTheme.SPACING_XS,
                vertical=0,
            ),
        )

    def _rebuild_message_list(self) -> None:
        """Rebuild the message list from current state."""
        if self._message_list is None:
            return

        controls = []
        for i, msg in enumerate(self.state.messages):
            # Pass sources to the last assistant message
            sources = None
            if msg.role == "assistant" and i == len(self.state.messages) - 1 and self._last_sources:
                sources = self._last_sources
            controls.append(self._build_message_bubble(msg, sources))

        self._message_list.controls = controls

    def _on_state_change(self) -> None:
        """Handle state changes - rebuild message list and update UI."""
        self._rebuild_message_list()

        # Update send button state during streaming
        if self._send_button:
            self._send_button.disabled = self.state.is_streaming
            self._send_button.icon_color = (
                SkynetteTheme.TEXT_MUTED if self.state.is_streaming else SkynetteTheme.PRIMARY
            )

        # Try to update UI
        try:
            if self._message_list:
                self._message_list.update()
            if self._send_button:
                self._send_button.update()
        except Exception:
            # UI may not be mounted yet
            pass

    def _on_provider_change(self, e: ft.ControlEvent) -> None:
        """Handle provider dropdown change.

        Args:
            e: Control event from dropdown.
        """
        if e.control.value:
            self.state.set_provider(e.control.value)

    def _on_include_code(self, e: ft.ControlEvent) -> None:
        """Get code from editor and store for next message.

        Args:
            e: Control event from button click.
        """
        if self._on_include_code_callback:
            code = self._on_include_code_callback()
            if code:
                self._pending_code_context = code
                # Visual feedback
                if self._include_code_btn:
                    self._include_code_btn.icon_color = SkynetteTheme.SUCCESS
                    self._include_code_btn.update()

    def _on_send(self, e: ft.ControlEvent | None = None) -> None:
        """Handle send button click or Enter key.

        Args:
            e: Optional control event.
        """
        if self._input_field is None:
            return

        message = self._input_field.value
        if not message:
            return
        message = message.strip()
        if not message or self.state.is_streaming:
            return

        # Get code context if Include Code was clicked
        code_context = self._pending_code_context
        self._pending_code_context = None

        # Reset include code button color
        if self._include_code_btn:
            self._include_code_btn.icon_color = SkynetteTheme.TEXT_SECONDARY
            self._include_code_btn.update()

        # Add user message
        self.state.add_message("user", message, code_context)

        # Clear input
        self._input_field.value = ""
        self._input_field.update()

        # Start streaming response
        asyncio.create_task(self._stream_response())

    async def _stream_response(self) -> None:
        """Stream AI response and update state.

        Uses gateway.chat_stream() for streaming chat responses.
        Updates the last message incrementally as chunks arrive.
        Handles errors gracefully by appending error text to message.
        Retrieves RAG context if rag_provider is configured.
        """
        self.state.set_streaming(True)

        # Clear previous sources
        self._last_sources = []

        # Get RAG context if available
        rag_context = ""
        if self._rag_provider and self._get_project_root:
            project_root = self._get_project_root()
            if project_root:
                # Get the user's last message for context query
                last_user_msg = ""
                for msg in reversed(self.state.messages):
                    if msg.role == "user":
                        last_user_msg = msg.content
                        break

                if last_user_msg:
                    try:
                        rag_context, sources = await self._rag_provider.get_context(
                            last_user_msg, project_root
                        )
                        self._last_sources = sources
                    except Exception as e:
                        # Log but don't fail if RAG fails
                        import logging

                        logging.warning(f"RAG context retrieval failed: {e}")

        # Build messages for API (with RAG context)
        messages = self._build_api_messages(rag_context)

        # Add empty assistant message for streaming
        self.state.add_message("assistant", "")

        try:
            provider = self.state.selected_provider
            # Use chat_stream for streaming chat responses
            async for chunk in self.gateway.chat_stream(messages, provider=provider):
                if chunk.content:
                    # Append to last message
                    current = self.state.messages[-1].content
                    self.state.update_last_message(current + chunk.content)

                if chunk.error:
                    self.state.update_last_message(
                        self.state.messages[-1].content + "\n\n[Response interrupted]"
                    )
                    break

        except Exception as e:
            error_msg = str(e)
            # Make error messages more user-friendly
            if "No providers available" in error_msg:
                error_msg = "No AI provider configured. Please set up a provider in Settings."
            self.state.update_last_message(f"Error: {error_msg}")

        finally:
            self.state.set_streaming(False)
            # Rebuild to show sources
            self._rebuild_message_list()
            try:
                if self._message_list:
                    self._message_list.update()
            except Exception:
                pass
            # Check if response contains code suggestion
            if self.state.messages:
                final_content = self.state.messages[-1].content
                self._check_for_code_suggestion(final_content)

    def _build_api_messages(self, rag_context: str = "") -> list[AIMessage]:
        """Convert ChatMessages to AIMessages for API.

        Builds the message list for the API call, including:
        - System message with coding assistant context and RAG context
        - All chat history messages
        - Code context prepended to user messages that have it

        Args:
            rag_context: Optional RAG context string to include in system prompt.

        Returns:
            List of AIMessage objects ready for gateway.chat_stream().
        """
        api_messages: list[AIMessage] = []

        # System message with context mode
        system_prompt = (
            "You are a helpful coding assistant. "
            "Help the user understand, write, and improve their code. "
            "Be concise but thorough. Use code blocks with language tags when showing code."
        )

        # Add RAG context if available
        if rag_context:
            system_prompt = (
                f"{system_prompt}\n\n"
                f"Use this codebase context to inform your responses:\n\n"
                f"{rag_context}"
            )

        api_messages.append(AIMessage(role="system", content=system_prompt))

        # Convert chat history
        for msg in self.state.messages:
            content = msg.content
            if msg.code_context:
                content = f"Code context:\n```\n{msg.code_context}\n```\n\n{content}"
            api_messages.append(AIMessage(role=msg.role, content=content))

        return api_messages

    def _detect_code_in_response(self, content: str) -> str | None:
        """Extract code from AI response if present.

        Args:
            content: Full AI response content.

        Returns:
            Extracted code string, or None if no code block found.
        """
        import re

        # Match ```language\ncode\n```
        match = re.search(r"```\w*\n(.*?)```", content, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None

    def _check_for_code_suggestion(self, content: str) -> None:
        """Check if response contains code and trigger diff preview.

        Args:
            content: Full AI response content.
        """
        if self._on_code_suggestion:
            code = self._detect_code_in_response(content)
            if code:
                self._on_code_suggestion(code)

    def dispose(self) -> None:
        """Clean up resources and listeners."""
        self.state.remove_listener(self._on_state_change)
