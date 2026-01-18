# src/ui/views/code_editor/ai_panel/chat_panel.py
"""AI chat panel for code assistance in the code editor.

Provides a chat interface for users to interact with AI about their code.
Features message history with streaming support, provider selection,
and code context attachment.
"""

import asyncio
from collections.abc import Callable

import flet as ft

from src.ai.gateway import AIGateway, AIMessage, AIStreamChunk
from src.ui.theme import SkynetteTheme
from src.ui.views.code_editor.ai_panel.chat_state import ChatMessage, ChatState


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
    ):
        """Initialize the chat panel.

        Args:
            page: Flet page reference.
            state: ChatState instance for managing conversation state.
            gateway: AIGateway instance for AI communication.
            on_include_code: Optional callback to get selected code from editor.
        """
        super().__init__()
        self._page_ref = page
        self.state = state
        self.gateway = gateway
        self._on_include_code_callback = on_include_code

        self.expand = True
        self.spacing = 0

        # Pending code context for next message
        self._pending_code_context: str | None = None

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
            border=ft.border.only(
                bottom=ft.BorderSide(1, SkynetteTheme.BORDER)
            ),
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
            border=ft.border.only(
                top=ft.BorderSide(1, SkynetteTheme.BORDER)
            ),
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

    def _build_message_bubble(self, msg: ChatMessage) -> ft.Control:
        """Build a message bubble for display.

        Args:
            msg: ChatMessage to render.

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
                                msg.code_context[:500] + ("..." if len(msg.code_context) > 500 else ""),
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

    def _rebuild_message_list(self) -> None:
        """Rebuild the message list from current state."""
        if self._message_list is None:
            return

        self._message_list.controls = [
            self._build_message_bubble(msg) for msg in self.state.messages
        ]

    def _on_state_change(self) -> None:
        """Handle state changes - rebuild message list and update UI."""
        self._rebuild_message_list()

        # Update send button state during streaming
        if self._send_button:
            self._send_button.disabled = self.state.is_streaming
            self._send_button.icon_color = (
                SkynetteTheme.TEXT_MUTED if self.state.is_streaming
                else SkynetteTheme.PRIMARY
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

    def dispose(self) -> None:
        """Clean up resources and listeners."""
        self.state.remove_listener(self._on_state_change)
