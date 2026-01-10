"""
Skynette Main Application

The main Flet application shell with navigation and layout.
"""

import flet as ft
import asyncio
from src.ui.theme import SkynetteTheme
from src.updater import Updater, UpdateInfo
from src.data.storage import WorkflowStorage
from src.core.workflow.models import Workflow, WorkflowNode
from src.core.workflow.executor import WorkflowExecutor
from src.core.nodes.registry import NodeRegistry
from src.ai.assistant import get_assistant, ChatMessage
from src.ai.providers import initialize_default_providers
from src.ui.views.simple_mode import SimpleModeView
from src.ui.views.agents import AgentsView
from src.ui.views.devtools import DevToolsView


class WorkflowExecutionError(Exception):
    """Exception raised when workflow execution fails."""
    pass


class SkynetteApp:
    """Main application class for Skynette."""

    def __init__(self, page: ft.Page):
        self.page = page
        self.current_view = "workflows"
        self.sidebar_expanded = False

        # View containers
        self.content_area = ft.Container(expand=True)
        self.assistant_panel = None
        self.assistant_visible = True
        self.view_title_text = None  # Reference to title text for updates

        # Core services
        self.storage = WorkflowStorage()

        # Load theme preference
        theme_pref = self.storage.get_setting("theme_mode", "dark")
        SkynetteTheme.set_theme_mode(theme_pref)

        self.node_registry = NodeRegistry()
        self.executor = WorkflowExecutor()

        # Current workflow being edited
        self.current_workflow: Workflow = None
        self.workflows_list = []
        self.selected_node_id: str = None
        self.last_execution_result = None
        self.simple_mode = True  # Start in Simple mode by default

        # Updater state
        self.updater = Updater(on_progress=self._on_update_progress)
        self.update_info: UpdateInfo = None
        self.update_status_text = ft.Text("", size=12, color=SkynetteTheme.TEXT_SECONDARY)
        self.update_progress_bar = ft.ProgressBar(width=300, value=0, visible=False)
        self.check_update_btn = None
        self.download_update_btn = None

        # Skynet Assistant state
        self.assistant = get_assistant()
        self.chat_messages_column = None
        self.chat_input_field = None
        self.chat_is_loading = False

        # Loading state
        self.loading_overlay = ft.Container(
            content=ft.Column(
                controls=[
                    ft.ProgressRing(color=SkynetteTheme.PRIMARY),
                    ft.Container(height=16),
                    ft.Text(
                        "Loading...",
                        size=14,
                        color=SkynetteTheme.TEXT_SECONDARY,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.center,
            bgcolor=SkynetteTheme.BG_PRIMARY + "E6",  # Semi-transparent
            visible=False,
            expand=True,
        )

    def initialize(self):
        """Initialize the application."""
        # Initialize AI providers
        initialize_default_providers()

        # Configure page
        self.page.title = "Skynette"
        self.page.theme = SkynetteTheme.get_flet_theme()
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.bgcolor = SkynetteTheme.BG_PRIMARY
        self.page.padding = 0
        self.page.spacing = 0

        # Handle window resize
        self.page.on_resize = self._on_resize

        # Build UI
        self.page.add(self._build_layout())

        # Show workflows view by default
        self._navigate_to("workflows")

    def _build_layout(self) -> ft.Control:
        """Build the main application layout."""
        return ft.Stack(
            controls=[
                ft.Row(
                    controls=[
                        # Sidebar Navigation
                        self._build_sidebar(),
                        # Main Content Area
                        ft.VerticalDivider(width=1, color=SkynetteTheme.BORDER),
                        ft.Column(
                            controls=[
                                # Top Bar
                                self._build_top_bar(),
                                ft.Divider(height=1, color=SkynetteTheme.BORDER),
                                # Content + Assistant
                                ft.Row(
                                    controls=[
                                        # Main content
                                        self.content_area,
                                        # Assistant Panel
                                        self._build_assistant_panel(),
                                    ],
                                    expand=True,
                                    spacing=0,
                                ),
                            ],
                            expand=True,
                            spacing=0,
                        ),
                    ],
                    expand=True,
                    spacing=0,
                ),
                # Loading overlay
                self.loading_overlay,
            ],
            expand=True,
        )

    def _build_sidebar(self) -> ft.Container:
        """Build the sidebar navigation."""
        nav_items = [
            {"icon": ft.Icons.ACCOUNT_TREE_ROUNDED, "label": "Workflows", "view": "workflows"},
            {"icon": ft.Icons.SMART_TOY_ROUNDED, "label": "AI Hub", "view": "ai_hub"},
            {"icon": ft.Icons.AUTO_AWESOME, "label": "Agents", "view": "agents"},
            {"icon": ft.Icons.DEVELOPER_MODE, "label": "DevTools", "view": "devtools"},
            {"icon": ft.Icons.EXTENSION_ROUNDED, "label": "Plugins", "view": "plugins"},
            {"icon": ft.Icons.HISTORY_ROUNDED, "label": "Runs", "view": "runs"},
        ]

        nav_buttons = []
        for item in nav_items:
            nav_buttons.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(
                                item["icon"],
                                size=24,
                                color=(
                                    SkynetteTheme.PRIMARY
                                    if self.current_view == item["view"]
                                    else SkynetteTheme.TEXT_SECONDARY
                                ),
                            ),
                            ft.Text(
                                item["label"],
                                size=10,
                                color=(
                                    SkynetteTheme.PRIMARY
                                    if self.current_view == item["view"]
                                    else SkynetteTheme.TEXT_SECONDARY
                                ),
                                text_align=ft.TextAlign.CENTER,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=4,
                    ),
                    padding=ft.padding.symmetric(vertical=12, horizontal=8),
                    border_radius=SkynetteTheme.RADIUS_MD,
                    bgcolor=(
                        SkynetteTheme.BG_TERTIARY
                        if self.current_view == item["view"]
                        else "transparent"
                    ),
                    on_click=lambda e, v=item["view"]: self._navigate_to(v),
                    on_hover=lambda e: self._on_nav_hover(e),
                )
            )

        return ft.Container(
            content=ft.Column(
                controls=[
                    # Logo
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(
                                    ft.Icons.AUTO_AWESOME,
                                    size=28,
                                    color=SkynetteTheme.PRIMARY,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                        padding=ft.padding.symmetric(vertical=16),
                    ),
                    ft.Divider(height=1, color=SkynetteTheme.BORDER),
                    # Navigation Items
                    ft.Column(
                        controls=nav_buttons,
                        spacing=4,
                        scroll=ft.ScrollMode.AUTO,
                        expand=True,
                    ),
                    ft.Divider(height=1, color=SkynetteTheme.BORDER),
                    # Settings at bottom
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Icon(
                                    ft.Icons.SETTINGS_ROUNDED,
                                    size=24,
                                    color=SkynetteTheme.TEXT_SECONDARY,
                                ),
                                ft.Text(
                                    "Settings",
                                    size=10,
                                    color=SkynetteTheme.TEXT_SECONDARY,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=4,
                        ),
                        padding=ft.padding.symmetric(vertical=12, horizontal=8),
                        border_radius=SkynetteTheme.RADIUS_MD,
                        on_click=lambda e: self._navigate_to("settings"),
                        on_hover=lambda e: self._on_nav_hover(e),
                    ),
                ],
                spacing=0,
            ),
            width=SkynetteTheme.SIDEBAR_WIDTH,
            bgcolor=SkynetteTheme.BG_SECONDARY,
            padding=ft.padding.symmetric(horizontal=4, vertical=8),
        )

    def _build_top_bar(self) -> ft.Container:
        """Build the top bar with title and actions."""
        # Create title text with reference for dynamic updates
        self.view_title_text = ft.Text(
            self._get_view_title(),
            size=SkynetteTheme.FONT_XL,
            weight=ft.FontWeight.W_600,
            color=SkynetteTheme.TEXT_PRIMARY,
        )
        return ft.Container(
            content=ft.Row(
                controls=[
                    # View Title
                    self.view_title_text,
                    ft.Container(expand=True),
                    # Action Buttons
                    ft.IconButton(
                        icon=ft.Icons.CHAT_ROUNDED,
                        icon_color=(
                            SkynetteTheme.PRIMARY
                            if self.assistant_visible
                            else SkynetteTheme.TEXT_SECONDARY
                        ),
                        tooltip="Toggle Assistant",
                        on_click=self._toggle_assistant,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.NOTIFICATIONS_ROUNDED,
                        icon_color=SkynetteTheme.TEXT_SECONDARY,
                        tooltip="Notifications",
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.padding.symmetric(horizontal=24, vertical=12),
            bgcolor=SkynetteTheme.BG_PRIMARY,
        )

    def _build_assistant_panel(self) -> ft.Container:
        """Build the Skynet Assistant chat panel."""
        # Chat messages column
        self.chat_messages_column = ft.Column(
            controls=[self._build_welcome_message()],
            scroll=ft.ScrollMode.AUTO,
            auto_scroll=True,
            expand=True,
            spacing=12,
        )

        # Chat input field
        self.chat_input_field = ft.TextField(
            hint_text="Ask Skynet anything...",
            border_radius=SkynetteTheme.RADIUS_LG,
            bgcolor=SkynetteTheme.BG_TERTIARY,
            border_color="transparent",
            focused_border_color=SkynetteTheme.PRIMARY,
            text_size=SkynetteTheme.FONT_SM,
            expand=True,
            min_lines=1,
            max_lines=4,
            on_submit=self._on_chat_submit,
        )

        self.assistant_panel = ft.Container(
            content=ft.Column(
                controls=[
                    # Header
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(
                                    ft.Icons.SMART_TOY_ROUNDED,
                                    size=20,
                                    color=SkynetteTheme.PRIMARY,
                                ),
                                ft.Text(
                                    "Skynet Assistant",
                                    size=SkynetteTheme.FONT_MD,
                                    weight=ft.FontWeight.W_600,
                                    color=SkynetteTheme.TEXT_PRIMARY,
                                ),
                                ft.Container(expand=True),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE_OUTLINE,
                                    icon_size=18,
                                    icon_color=SkynetteTheme.TEXT_SECONDARY,
                                    tooltip="Clear chat",
                                    on_click=self._clear_chat,
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.CLOSE_ROUNDED,
                                    icon_size=18,
                                    icon_color=SkynetteTheme.TEXT_SECONDARY,
                                    on_click=self._toggle_assistant,
                                ),
                            ],
                        ),
                        padding=ft.padding.all(12),
                        border=ft.border.only(
                            bottom=ft.BorderSide(1, SkynetteTheme.BORDER)
                        ),
                    ),
                    # Chat Messages Area
                    ft.Container(
                        content=self.chat_messages_column,
                        expand=True,
                        padding=ft.padding.all(12),
                    ),
                    # Input Area
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                self.chat_input_field,
                                ft.IconButton(
                                    icon=ft.Icons.SEND_ROUNDED,
                                    icon_color=SkynetteTheme.PRIMARY,
                                    tooltip="Send",
                                    on_click=self._on_chat_submit,
                                ),
                            ],
                            spacing=8,
                        ),
                        padding=ft.padding.all(12),
                        border=ft.border.only(
                            top=ft.BorderSide(1, SkynetteTheme.BORDER)
                        ),
                    ),
                ],
                spacing=0,
            ),
            width=320,
            bgcolor=SkynetteTheme.BG_SECONDARY,
            border=ft.border.only(left=ft.BorderSide(1, SkynetteTheme.BORDER)),
            visible=self.assistant_visible,
        )
        return self.assistant_panel

    def _build_welcome_message(self) -> ft.Container:
        """Build the welcome message for the chat."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(
                        ft.Icons.AUTO_AWESOME,
                        size=40,
                        color=SkynetteTheme.PRIMARY,
                    ),
                    ft.Text(
                        "Hi! I'm Skynet",
                        size=SkynetteTheme.FONT_LG,
                        weight=ft.FontWeight.W_600,
                        color=SkynetteTheme.TEXT_PRIMARY,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        "I can help you build workflows using natural language. "
                        "Just describe what you want to automate!",
                        size=SkynetteTheme.FONT_SM,
                        color=SkynetteTheme.TEXT_SECONDARY,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=16),
                    ft.Text(
                        "Try asking:",
                        size=SkynetteTheme.FONT_SM,
                        color=SkynetteTheme.TEXT_MUTED,
                    ),
                    self._build_example_prompt(
                        "Create a workflow that monitors a folder"
                    ),
                    self._build_example_prompt(
                        "Build an email summarizer"
                    ),
                    self._build_example_prompt(
                        "How do I call an API?"
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            padding=ft.padding.all(16),
        )

    def _build_chat_message(self, message: ChatMessage) -> ft.Container:
        """Build a chat message bubble."""
        is_user = message.role == "user"

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(
                                ft.Icons.PERSON if is_user else ft.Icons.SMART_TOY_ROUNDED,
                                size=16,
                                color=SkynetteTheme.TEXT_SECONDARY if is_user else SkynetteTheme.PRIMARY,
                            ),
                            ft.Text(
                                "You" if is_user else "Skynet",
                                size=11,
                                weight=ft.FontWeight.W_600,
                                color=SkynetteTheme.TEXT_SECONDARY,
                            ),
                        ],
                        spacing=4,
                    ),
                    ft.Container(
                        content=ft.Markdown(
                            message.content,
                            selectable=True,
                            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                            code_theme=ft.MarkdownCodeTheme.MONOKAI,
                            code_style_sheet=ft.MarkdownStyleSheet(
                                code_text_style=ft.TextStyle(size=12),
                            ),
                        ) if not is_user else ft.Text(
                            message.content,
                            size=SkynetteTheme.FONT_SM,
                            color=SkynetteTheme.TEXT_PRIMARY,
                        ),
                        padding=ft.padding.all(10),
                        bgcolor=SkynetteTheme.BG_TERTIARY if is_user else SkynetteTheme.BG_PRIMARY,
                        border_radius=SkynetteTheme.RADIUS_MD,
                    ),
                ],
                spacing=4,
            ),
            padding=ft.padding.only(
                left=24 if is_user else 0,
                right=0 if is_user else 24,
            ),
        )

    def _build_loading_indicator(self) -> ft.Container:
        """Build a loading indicator for chat responses."""
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.ProgressRing(width=16, height=16, stroke_width=2),
                    ft.Text(
                        "Skynet is thinking...",
                        size=SkynetteTheme.FONT_SM,
                        color=SkynetteTheme.TEXT_SECONDARY,
                        italic=True,
                    ),
                ],
                spacing=8,
            ),
            padding=ft.padding.all(12),
        )

    def _on_chat_submit(self, e):
        """Handle chat message submission."""
        if self.chat_is_loading:
            return

        message = self.chat_input_field.value.strip()
        if not message:
            return

        # Clear input
        self.chat_input_field.value = ""
        self.page.update()

        # Add user message to UI
        user_msg = ChatMessage(
            id="temp",
            role="user",
            content=message,
        )
        self.chat_messages_column.controls.append(self._build_chat_message(user_msg))

        # Add loading indicator
        loading = self._build_loading_indicator()
        self.chat_messages_column.controls.append(loading)
        self.chat_is_loading = True
        self.page.update()

        # Scroll to bottom
        self.chat_messages_column.scroll_to(offset=-1, duration=200)

        # Set workflow context
        if self.current_workflow:
            self.assistant.set_context(self.current_workflow)

        # Send to assistant (async)
        async def get_response():
            try:
                response = await self.assistant.chat(message)

                # Remove loading indicator
                if loading in self.chat_messages_column.controls:
                    self.chat_messages_column.controls.remove(loading)

                # Remove the temp user message (assistant already added it)
                if self.chat_messages_column.controls:
                    # Find and remove our temp user message
                    for ctrl in self.chat_messages_column.controls[:]:
                        if hasattr(ctrl, '_temp_user'):
                            self.chat_messages_column.controls.remove(ctrl)

                # Add messages from assistant's conversation
                # The assistant already has the user message, just add the response
                self.chat_messages_column.controls.append(
                    self._build_chat_message(response)
                )

                self.chat_is_loading = False
                self.page.update()

                # Scroll to bottom to show response
                self.chat_messages_column.scroll_to(offset=-1, duration=200)

            except Exception as ex:
                if loading in self.chat_messages_column.controls:
                    self.chat_messages_column.controls.remove(loading)

                error_msg = ChatMessage(
                    id="error",
                    role="assistant",
                    content=f"Sorry, I encountered an error: {str(ex)}\n\n"
                            "Make sure you have an AI provider configured in Settings.",
                )
                self.chat_messages_column.controls.append(
                    self._build_chat_message(error_msg)
                )
                self.chat_is_loading = False
                self.page.update()

                # Scroll to bottom to show error
                self.chat_messages_column.scroll_to(offset=-1, duration=200)

        asyncio.create_task(get_response())

    def _clear_chat(self, e):
        """Clear the chat history."""
        self.assistant.clear_conversation()
        self.chat_messages_column.controls = [self._build_welcome_message()]
        self.page.update()

    def _build_example_prompt(self, text: str) -> ft.Container:
        """Build an example prompt chip."""
        return ft.Container(
            content=ft.Text(
                text,
                size=SkynetteTheme.FONT_SM,
                color=SkynetteTheme.TEXT_SECONDARY,
            ),
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            border_radius=SkynetteTheme.RADIUS_MD,
            bgcolor=SkynetteTheme.BG_TERTIARY,
            on_click=lambda e: self._use_example_prompt(text),
            on_hover=lambda e: self._on_example_hover(e),
        )

    def _get_view_title(self) -> str:
        """Get the title for the current view."""
        titles = {
            "workflows": "Workflows",
            "ai_hub": "AI Model Hub",
            "agents": "Agent Orchestrator",
            "devtools": "Developer Tools",
            "plugins": "Plugins & Marketplace",
            "runs": "Execution History",
            "settings": "Settings",
            "editor": f"Edit: {self.current_workflow.name if self.current_workflow else 'Workflow'}",
        }
        return titles.get(self.current_view, "Skynette")

    def _navigate_to(self, view: str):
        """Navigate to a different view."""
        self.current_view = view
        # Update the title text
        if self.view_title_text:
            self.view_title_text.value = self._get_view_title()
        self._update_content()
        self.page.update()

    def _build_workflows_view(self) -> ft.Control:
        """Build the workflows list view."""
        # Load workflows from storage
        self.workflows_list = self.storage.list_workflows()

        # Build workflow cards
        workflow_cards = []
        for wf in self.workflows_list:
            workflow_cards.append(self._build_workflow_card(wf))

        # Show empty state or workflow grid
        if workflow_cards:
            content = ft.Column(
                controls=[
                    # Header with actions
                    ft.Row(
                        controls=[
                            ft.Text(
                                "My Workflows",
                                size=SkynetteTheme.FONT_LG,
                                weight=ft.FontWeight.W_500,
                                color=SkynetteTheme.TEXT_PRIMARY,
                            ),
                            ft.Container(expand=True),
                            ft.ElevatedButton(
                                "New Workflow",
                                icon=ft.Icons.ADD_ROUNDED,
                                bgcolor=SkynetteTheme.PRIMARY,
                                color=SkynetteTheme.TEXT_PRIMARY,
                                on_click=self._create_new_workflow,
                            ),
                        ],
                    ),
                    ft.Container(height=16),
                    # Workflow grid
                    ft.Row(
                        controls=workflow_cards,
                        wrap=True,
                        spacing=16,
                        run_spacing=16,
                    ),
                ],
                scroll=ft.ScrollMode.AUTO,
            )
        else:
            content = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(
                            ft.Icons.FOLDER_OPEN_OUTLINED,
                            size=64,
                            color=SkynetteTheme.TEXT_MUTED,
                        ),
                        ft.Container(height=16),
                        ft.Text(
                            "No Workflows Yet",
                            size=20,
                            weight=ft.FontWeight.W_600,
                            color=SkynetteTheme.TEXT_PRIMARY,
                        ),
                        ft.Container(height=8),
                        ft.Text(
                            "Create your first workflow to get started",
                            size=14,
                            color=SkynetteTheme.TEXT_SECONDARY,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Container(height=24),
                        ft.ElevatedButton(
                            "Create Workflow",
                            icon=ft.Icons.ADD,
                            bgcolor=SkynetteTheme.PRIMARY,
                            color=SkynetteTheme.TEXT_PRIMARY,
                            on_click=lambda e: self._create_new_workflow(e),
                        ),
                        ft.Container(height=16),
                        ft.Container(
                            content=ft.Column([
                                ft.Text("💡 Quick Tips:", size=12, weight=ft.FontWeight.W_600),
                                ft.Text("• Use Simple Mode for step-by-step creation", size=11),
                                ft.Text("• Use Advanced Mode for visual editing", size=11),
                                ft.Text("• All workflows are saved automatically", size=11),
                            ], spacing=4),
                            padding=12,
                            bgcolor=SkynetteTheme.BG_SECONDARY,
                            border_radius=SkynetteTheme.RADIUS_MD,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                expand=True,
                alignment=ft.alignment.center,
            )

        return ft.Container(
            content=content,
            padding=ft.padding.all(24),
            expand=True,
        )

    def _build_workflow_card(self, wf: dict) -> ft.Container:
        """Build a workflow card for the grid."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(
                                ft.Icons.ACCOUNT_TREE_ROUNDED,
                                size=24,
                                color=SkynetteTheme.PRIMARY,
                            ),
                            ft.Container(expand=True),
                            ft.PopupMenuButton(
                                icon=ft.Icons.MORE_VERT,
                                icon_color=SkynetteTheme.TEXT_SECONDARY,
                                items=[
                                    ft.PopupMenuItem(
                                        content=ft.Text("Edit"),
                                        icon=ft.Icons.EDIT,
                                        on_click=lambda e, w=wf: self._open_workflow(w["id"]),
                                    ),
                                    ft.PopupMenuItem(
                                        content=ft.Text("Run"),
                                        icon=ft.Icons.PLAY_ARROW,
                                        on_click=lambda e, w=wf: self._run_workflow(w["id"]),
                                    ),
                                    ft.PopupMenuItem(
                                        content=ft.Text("Duplicate"),
                                        icon=ft.Icons.COPY,
                                        on_click=lambda e, w=wf: self._duplicate_workflow(w["id"]),
                                    ),
                                    ft.PopupMenuItem(),  # Divider
                                    ft.PopupMenuItem(
                                        content=ft.Text("Delete"),
                                        icon=ft.Icons.DELETE,
                                        on_click=lambda e, w=wf: self._delete_workflow(w["id"]),
                                    ),
                                ],
                            ),
                        ],
                    ),
                    ft.Text(
                        wf["name"],
                        size=SkynetteTheme.FONT_MD,
                        weight=ft.FontWeight.W_600,
                        color=SkynetteTheme.TEXT_PRIMARY,
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    ft.Text(
                        wf.get("description", "No description") or "No description",
                        size=SkynetteTheme.FONT_SM,
                        color=SkynetteTheme.TEXT_SECONDARY,
                        max_lines=2,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    ft.Container(expand=True),
                    ft.Text(
                        f"Updated: {wf.get('updated_at', '')[:10]}",
                        size=10,
                        color=SkynetteTheme.TEXT_MUTED,
                    ),
                ],
                spacing=8,
            ),
            width=220,
            height=160,
            padding=ft.padding.all(16),
            border_radius=SkynetteTheme.RADIUS_LG,
            bgcolor=SkynetteTheme.BG_SECONDARY,
            border=ft.border.all(1, SkynetteTheme.BORDER),
            on_click=lambda e, w=wf: self._open_workflow(w["id"]),
            on_hover=lambda e: self._on_card_hover(e),
        )

    def _on_card_hover(self, e):
        """Handle workflow card hover."""
        e.control.border = ft.border.all(
            1, SkynetteTheme.PRIMARY if e.data == "true" else SkynetteTheme.BORDER
        )
        e.control.update()

    def _build_ai_hub_view(self) -> ft.Control:
        """Build the AI Model Hub view."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "AI Model Hub",
                        size=SkynetteTheme.FONT_LG,
                        weight=ft.FontWeight.W_500,
                        color=SkynetteTheme.TEXT_PRIMARY,
                    ),
                    ft.Container(height=16),
                    ft.Text(
                        "Browse, download, and manage AI models",
                        size=SkynetteTheme.FONT_SM,
                        color=SkynetteTheme.TEXT_SECONDARY,
                    ),
                    ft.Container(height=24),
                    # Placeholder for model categories
                    ft.Row(
                        controls=[
                            self._build_model_category_card(
                                "Recommended", ft.Icons.STAR_ROUNDED, "5 models"
                            ),
                            self._build_model_category_card(
                                "Trending", ft.Icons.TRENDING_UP_ROUNDED, "12 models"
                            ),
                            self._build_model_category_card(
                                "My Models", ft.Icons.FOLDER_ROUNDED, "0 installed"
                            ),
                        ],
                        wrap=True,
                        spacing=16,
                    ),
                ],
            ),
            padding=ft.padding.all(24),
            expand=True,
        )

    def _build_model_category_card(
        self, title: str, icon: str, subtitle: str
    ) -> ft.Container:
        """Build a model category card."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(icon, size=32, color=SkynetteTheme.PRIMARY),
                    ft.Text(
                        title,
                        size=SkynetteTheme.FONT_MD,
                        weight=ft.FontWeight.W_500,
                        color=SkynetteTheme.TEXT_PRIMARY,
                    ),
                    ft.Text(
                        subtitle,
                        size=SkynetteTheme.FONT_SM,
                        color=SkynetteTheme.TEXT_SECONDARY,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            width=150,
            padding=ft.padding.all(20),
            border_radius=SkynetteTheme.RADIUS_LG,
            bgcolor=SkynetteTheme.BG_SECONDARY,
            border=ft.border.all(1, SkynetteTheme.BORDER),
        )

    def _build_plugins_view(self) -> ft.Control:
        """Build the plugins view."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Plugins & Marketplace",
                        size=SkynetteTheme.FONT_LG,
                        weight=ft.FontWeight.W_500,
                        color=SkynetteTheme.TEXT_PRIMARY,
                    ),
                    ft.Container(height=16),
                    ft.Text(
                        "Extend Skynette with community plugins",
                        size=SkynetteTheme.FONT_SM,
                        color=SkynetteTheme.TEXT_SECONDARY,
                    ),
                ],
            ),
            padding=ft.padding.all(24),
            expand=True,
        )

    def _build_runs_view(self) -> ft.Control:
        """Build the execution history view."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Execution History",
                        size=SkynetteTheme.FONT_LG,
                        weight=ft.FontWeight.W_500,
                        color=SkynetteTheme.TEXT_PRIMARY,
                    ),
                    ft.Container(height=16),
                    ft.Text(
                        "View past workflow executions and logs",
                        size=SkynetteTheme.FONT_SM,
                        color=SkynetteTheme.TEXT_SECONDARY,
                    ),
                ],
            ),
            padding=ft.padding.all(24),
            expand=True,
        )

    def _build_agents_view(self) -> ft.Control:
        """Build the Agent Orchestrator view."""
        agents_view = AgentsView(page=self.page)
        return ft.Container(
            content=agents_view,
            expand=True,
        )

    def _build_devtools_view(self) -> ft.Control:
        """Build the Developer Tools view."""
        devtools_view = DevToolsView(page=self.page)
        return ft.Container(
            content=devtools_view,
            expand=True,
        )

    def _build_settings_view(self) -> ft.Control:
        """Build the settings view."""
        # Initialize update buttons
        self.check_update_btn = ft.ElevatedButton(
            "Check for Updates",
            icon=ft.Icons.REFRESH_ROUNDED,
            bgcolor=SkynetteTheme.BG_TERTIARY,
            color=SkynetteTheme.TEXT_PRIMARY,
            on_click=self._check_for_updates,
        )
        self.download_update_btn = ft.ElevatedButton(
            "Download & Install",
            icon=ft.Icons.DOWNLOAD_ROUNDED,
            bgcolor=SkynetteTheme.PRIMARY,
            color=SkynetteTheme.TEXT_PRIMARY,
            on_click=self._download_and_install_update,
            visible=False,
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Settings",
                        size=SkynetteTheme.FONT_LG,
                        weight=ft.FontWeight.W_500,
                        color=SkynetteTheme.TEXT_PRIMARY,
                    ),
                    ft.Container(height=16),
                    ft.Text(
                        "Configure Skynette preferences",
                        size=SkynetteTheme.FONT_SM,
                        color=SkynetteTheme.TEXT_SECONDARY,
                    ),
                    ft.Container(height=24),
                    # Theme Section
                    self._build_settings_section(
                        "Appearance",
                        ft.Column(
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Icon(
                                            ft.Icons.PALETTE_OUTLINED,
                                            size=20,
                                            color=SkynetteTheme.PRIMARY,
                                        ),
                                        ft.Column(
                                            controls=[
                                                ft.Text(
                                                    "Theme",
                                                    size=14,
                                                    weight=ft.FontWeight.W_500,
                                                    color=SkynetteTheme.TEXT_PRIMARY,
                                                ),
                                                ft.Text(
                                                    "Choose light or dark theme",
                                                    size=12,
                                                    color=SkynetteTheme.TEXT_SECONDARY,
                                                ),
                                            ],
                                            spacing=2,
                                            expand=True,
                                        ),
                                    ],
                                    spacing=12,
                                ),
                                ft.Container(height=12),
                                ft.Row(
                                    controls=[
                                        ft.Switch(
                                            label="Dark Mode",
                                            value=SkynetteTheme.get_theme_mode() == "dark",
                                            on_change=self._toggle_theme,
                                        ),
                                    ],
                                ),
                            ],
                            spacing=8,
                        ),
                    ),
                    ft.Container(height=16),
                    # Updates Section
                    self._build_settings_section(
                        "Software Updates",
                        ft.Column(
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Icon(
                                            ft.Icons.INFO_OUTLINE_ROUNDED,
                                            size=20,
                                            color=SkynetteTheme.PRIMARY,
                                        ),
                                        ft.Column(
                                            controls=[
                                                ft.Text(
                                                    f"Current Version: v{Updater.CURRENT_VERSION}",
                                                    size=14,
                                                    weight=ft.FontWeight.W_500,
                                                    color=SkynetteTheme.TEXT_PRIMARY,
                                                ),
                                                ft.Text(
                                                    "Check for the latest version of Skynette",
                                                    size=12,
                                                    color=SkynetteTheme.TEXT_SECONDARY,
                                                ),
                                            ],
                                            spacing=2,
                                            expand=True,
                                        ),
                                    ],
                                    spacing=12,
                                ),
                                ft.Container(height=12),
                                ft.Row(
                                    controls=[
                                        self.check_update_btn,
                                        self.download_update_btn,
                                    ],
                                    spacing=12,
                                ),
                                self.update_progress_bar,
                                self.update_status_text,
                            ],
                            spacing=8,
                        ),
                    ),
                    ft.Container(height=16),
                    # About Section
                    self._build_settings_section(
                        "About",
                        ft.Column(
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Icon(
                                            ft.Icons.AUTO_AWESOME,
                                            size=32,
                                            color=SkynetteTheme.PRIMARY,
                                        ),
                                        ft.Column(
                                            controls=[
                                                ft.Text(
                                                    "Skynette",
                                                    size=18,
                                                    weight=ft.FontWeight.BOLD,
                                                    color=SkynetteTheme.TEXT_PRIMARY,
                                                ),
                                                ft.Text(
                                                    "AI-Native Workflow Automation Platform",
                                                    size=12,
                                                    color=SkynetteTheme.TEXT_SECONDARY,
                                                ),
                                            ],
                                            spacing=2,
                                        ),
                                    ],
                                    spacing=12,
                                ),
                                ft.Container(height=8),
                                ft.Text(
                                    "An open-source alternative to n8n with multi-AI model support.",
                                    size=12,
                                    color=SkynetteTheme.TEXT_MUTED,
                                ),
                            ],
                            spacing=8,
                        ),
                    ),
                ],
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=ft.padding.all(24),
            expand=True,
        )

    def _build_settings_section(self, title: str, content: ft.Control) -> ft.Container:
        """Build a settings section card."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        title,
                        size=14,
                        weight=ft.FontWeight.W_600,
                        color=SkynetteTheme.TEXT_PRIMARY,
                    ),
                    ft.Container(height=8),
                    content,
                ],
                spacing=0,
            ),
            bgcolor=SkynetteTheme.BG_SECONDARY,
            padding=ft.padding.all(16),
            border_radius=SkynetteTheme.RADIUS_LG,
            border=ft.border.all(1, SkynetteTheme.BORDER),
        )

    def _on_update_progress(self, message: str, percent: float):
        """Handle update progress callback."""
        self.update_status_text.value = message
        self.update_progress_bar.value = percent / 100
        self.update_progress_bar.visible = percent < 100
        self.page.update()

    async def _check_for_updates(self, e=None):
        """Check for available updates."""
        self.check_update_btn.disabled = True
        self.update_status_text.value = "Checking for updates..."
        self.update_progress_bar.visible = True
        self.update_progress_bar.value = None  # Indeterminate
        self.page.update()

        try:
            self.update_info = await self.updater.check_for_updates()

            if self.update_info and self.update_info.is_newer:
                self.update_status_text.value = (
                    f"Update available: v{self.update_info.version} "
                    f"(current: v{self.update_info.current_version})"
                )
                self.update_status_text.color = SkynetteTheme.SUCCESS
                self.download_update_btn.visible = True
            else:
                self.update_status_text.value = "You're running the latest version!"
                self.update_status_text.color = SkynetteTheme.TEXT_SECONDARY
                self.download_update_btn.visible = False
        except Exception as ex:
            self.update_status_text.value = f"Check failed: {str(ex)}"
            self.update_status_text.color = SkynetteTheme.ERROR

        self.check_update_btn.disabled = False
        self.update_progress_bar.visible = False
        self.page.update()

    async def _download_and_install_update(self, e=None):
        """Download and install the available update."""
        self.check_update_btn.disabled = True
        self.download_update_btn.disabled = True
        self.update_progress_bar.visible = True
        self.page.update()

        try:
            success = await self.updater.update()

            if success:
                # Show restart dialog
                self._show_restart_dialog()
            else:
                self.update_status_text.value = "Update failed. Please try again."
                self.update_status_text.color = SkynetteTheme.ERROR
        except Exception as ex:
            self.update_status_text.value = f"Update failed: {str(ex)}"
            self.update_status_text.color = SkynetteTheme.ERROR

        self.check_update_btn.disabled = False
        self.download_update_btn.disabled = False
        self.update_progress_bar.visible = False
        self.page.update()

    def _show_restart_dialog(self):
        """Show dialog prompting user to restart after update."""
        import subprocess
        import sys

        def restart_app(e):
            subprocess.Popen([sys.executable] + sys.argv)
            self.page.window.close()

        def close_dialog(e):
            dialog.open = False
            self.page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Update Complete"),
            content=ft.Text(
                "Skynette has been updated successfully. "
                "Please restart the application to apply changes."
            ),
            actions=[
                ft.TextButton("Later", on_click=close_dialog),
                ft.ElevatedButton(
                    "Restart Now",
                    icon=ft.Icons.RESTART_ALT_ROUNDED,
                    bgcolor=SkynetteTheme.PRIMARY,
                    color=SkynetteTheme.TEXT_PRIMARY,
                    on_click=restart_app,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _toggle_assistant(self, e=None):
        """Toggle the assistant panel visibility."""
        self.assistant_visible = not self.assistant_visible
        if self.assistant_panel:
            self.assistant_panel.visible = self.assistant_visible
        self.page.update()

    def _toggle_theme(self, e):
        """Toggle between light and dark theme."""
        new_mode = "dark" if e.control.value else "light"
        SkynetteTheme.set_theme_mode(new_mode)

        # Save preference
        self.storage.set_setting("theme_mode", new_mode)

        # Update Flet page theme
        self.page.theme_mode = ft.ThemeMode.DARK if new_mode == "dark" else ft.ThemeMode.LIGHT

        # Force full UI rebuild
        self._update_content()
        self.page.update()

    def _show_loading(self, message: str = "Loading..."):
        """Show loading overlay."""
        self.loading_overlay.content.controls[2].value = message
        self.loading_overlay.visible = True
        self.page.update()

    def _hide_loading(self):
        """Hide loading overlay."""
        self.loading_overlay.visible = False
        self.page.update()

    def _show_error_dialog(self, title: str, message: str, details: str = None):
        """Show a detailed error dialog with actionable guidance."""
        controls = [
            ft.Text(message, size=14, color=SkynetteTheme.TEXT_PRIMARY),
        ]

        if details:
            controls.extend([
                ft.Container(height=12),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Details:", size=12, weight=ft.FontWeight.W_600),
                        ft.Text(details, size=11, color=SkynetteTheme.TEXT_SECONDARY),
                    ]),
                    padding=12,
                    bgcolor=SkynetteTheme.BG_TERTIARY,
                    border_radius=SkynetteTheme.RADIUS_MD,
                ),
            ])

        dialog = ft.AlertDialog(
            title=ft.Text(title, color=SkynetteTheme.ERROR),
            content=ft.Column(controls, tight=True, spacing=8),
            actions=[
                ft.TextButton("Close", on_click=lambda e: self.page.close(dialog)),
            ],
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _create_new_workflow(self, e=None):
        """Create a new workflow."""
        # Create dialog for workflow name
        name_field = ft.TextField(
            value="New Workflow",
            label="Workflow Name",
            autofocus=True,
        )
        desc_field = ft.TextField(
            label="Description (optional)",
            multiline=True,
            min_lines=2,
            max_lines=4,
        )

        def create_workflow(e):
            # Create new workflow
            workflow = Workflow(
                name=name_field.value or "Untitled Workflow",
                description=desc_field.value or "",
            )
            # Add default manual trigger
            trigger = WorkflowNode(
                type="manual_trigger",
                name="Manual Trigger",
                position={"x": 100, "y": 100},
            )
            workflow.nodes.append(trigger)

            # Save to storage
            self.storage.save_workflow(workflow)
            self.current_workflow = workflow

            # Close dialog
            dialog.open = False
            self.page.update()

            # Refresh workflows list
            self._navigate_to("workflows")

        def cancel(e):
            dialog.open = False
            self.page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Create New Workflow"),
            content=ft.Column(
                controls=[name_field, desc_field],
                tight=True,
                spacing=16,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=cancel),
                ft.ElevatedButton(
                    "Create",
                    bgcolor=SkynetteTheme.PRIMARY,
                    color=SkynetteTheme.TEXT_PRIMARY,
                    on_click=create_workflow,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _open_workflow(self, workflow_id: str):
        """Open a workflow for editing."""
        try:
            workflow = self.storage.load_workflow(workflow_id)
            if workflow:
                self.current_workflow = workflow
                self.current_view = "editor"
                # Update the title text
                if self.view_title_text:
                    self.view_title_text.value = self._get_view_title()
                self._update_content()
                self.page.update()
            else:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Workflow not found"),
                    bgcolor=SkynetteTheme.ERROR,
                )
                self.page.snack_bar.open = True
                self.page.update()
        except Exception as ex:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error loading workflow: {str(ex)}"),
                bgcolor=SkynetteTheme.ERROR,
            )
            self.page.snack_bar.open = True
            self.page.update()

    def _update_content(self):
        """Update the main content area based on current view."""
        if self.current_view == "workflows":
            self._show_loading("Loading workflows...")
            try:
                workflows = self.storage.list_workflows()
                self.workflows_list = workflows
                self.content_area.content = self._build_workflows_view()
            finally:
                self._hide_loading()
        elif self.current_view == "ai_hub":
            self.content_area.content = self._build_ai_hub_view()
        elif self.current_view == "agents":
            self.content_area.content = self._build_agents_view()
        elif self.current_view == "devtools":
            self.content_area.content = self._build_devtools_view()
        elif self.current_view == "plugins":
            self.content_area.content = self._build_plugins_view()
        elif self.current_view == "runs":
            self.content_area.content = self._build_runs_view()
        elif self.current_view == "settings":
            self.content_area.content = self._build_settings_view()
        elif self.current_view == "editor":
            self.content_area.content = self._build_editor_view()

    def _build_editor_view(self) -> ft.Control:
        """Build the workflow editor view."""
        if not self.current_workflow:
            return self._build_workflows_view()

        return ft.Column(
            controls=[
                # Toolbar
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.IconButton(
                                icon=ft.Icons.ARROW_BACK,
                                tooltip="Back to workflows",
                                icon_color=SkynetteTheme.TEXT_SECONDARY,
                                on_click=lambda e: self._navigate_to("workflows"),
                            ),
                            ft.Text(
                                self.current_workflow.name,
                                size=18,
                                weight=ft.FontWeight.W_600,
                                color=SkynetteTheme.TEXT_PRIMARY,
                            ),
                            ft.Container(width=24),
                            # Simple/Advanced Mode Toggle
                            ft.Container(
                                content=ft.Row(
                                    controls=[
                                        ft.Container(
                                            content=ft.Text("Simple", size=12, color=SkynetteTheme.TEXT_PRIMARY if self.simple_mode else SkynetteTheme.TEXT_MUTED),
                                            padding=ft.padding.symmetric(horizontal=12, vertical=6),
                                            bgcolor=SkynetteTheme.PRIMARY if self.simple_mode else "transparent",
                                            border_radius=4,
                                            on_click=lambda e: self._set_editor_mode(simple=True),
                                        ),
                                        ft.Container(
                                            content=ft.Text("Advanced", size=12, color=SkynetteTheme.TEXT_PRIMARY if not self.simple_mode else SkynetteTheme.TEXT_MUTED),
                                            padding=ft.padding.symmetric(horizontal=12, vertical=6),
                                            bgcolor=SkynetteTheme.PRIMARY if not self.simple_mode else "transparent",
                                            border_radius=4,
                                            on_click=lambda e: self._set_editor_mode(simple=False),
                                        ),
                                    ],
                                    spacing=2,
                                ),
                                bgcolor=SkynetteTheme.BG_TERTIARY,
                                border_radius=6,
                                padding=2,
                            ),
                            ft.Container(expand=True),
                            # Execution status indicator
                            self._build_execution_indicator(),
                            ft.IconButton(
                                icon=ft.Icons.PLAY_ARROW,
                                tooltip="Run workflow",
                                icon_color=SkynetteTheme.SUCCESS,
                                on_click=lambda e: self._run_current_workflow(),
                            ),
                            ft.ElevatedButton(
                                "Save",
                                icon=ft.Icons.SAVE,
                                bgcolor=SkynetteTheme.PRIMARY,
                                color=SkynetteTheme.TEXT_PRIMARY,
                                on_click=lambda e: self._save_current_workflow(),
                            ),
                        ],
                    ),
                    bgcolor=SkynetteTheme.BG_SECONDARY,
                    padding=ft.padding.symmetric(horizontal=16, vertical=8),
                    border=ft.border.only(bottom=ft.BorderSide(1, SkynetteTheme.BORDER)),
                ),
                # Editor area - Simple or Advanced based on mode
                self._build_simple_editor_content() if self.simple_mode else self._build_advanced_editor_content(),
            ],
            expand=True,
            spacing=0,
        )

    def _build_simple_editor_content(self) -> ft.Control:
        """Build simple step-by-step editor content."""
        simple_view = SimpleModeView(
            workflow=self.current_workflow,
            on_save=lambda w: self._save_current_workflow(),
            on_change=lambda w=None: self._update_content(),
        )
        return ft.Container(
            content=simple_view,
            expand=True,
            padding=20,
        )

    def _build_advanced_editor_content(self) -> ft.Control:
        """Build advanced visual canvas editor content."""
        # Build node palette
        categories = {}
        for node_def in self.node_registry.get_all_definitions():
            cat = node_def.category or "other"
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(node_def)

        palette_items = []
        for cat_name, nodes in sorted(categories.items()):
            node_buttons = []
            for node_def in sorted(nodes, key=lambda n: n.name):
                node_buttons.append(
                    ft.ListTile(
                        title=ft.Text(node_def.name, size=12),
                        leading=ft.Icon(ft.Icons.CIRCLE, size=8, color=SkynetteTheme.PRIMARY),
                        dense=True,
                        on_click=lambda e, nd=node_def: self._add_node_to_workflow(nd),
                    )
                )

            palette_items.append(
                ft.ExpansionTile(
                    title=ft.Text(cat_name.title(), size=13, weight=ft.FontWeight.W_500),
                    expanded=cat_name.lower() in ["triggers", "trigger"],
                    controls=node_buttons,
                    tile_padding=ft.padding.symmetric(horizontal=8),
                )
            )

        return ft.Row(
            controls=[
                # Node Palette
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Container(
                                content=ft.TextField(
                                    hint_text="Search nodes...",
                                    prefix_icon=ft.Icons.SEARCH,
                                    height=36,
                                    text_size=12,
                                    border_color=SkynetteTheme.BORDER,
                                ),
                                padding=8,
                            ),
                            ft.Column(
                                controls=palette_items,
                                scroll=ft.ScrollMode.AUTO,
                                expand=True,
                            ),
                        ],
                        expand=True,
                    ),
                    width=220,
                    bgcolor=SkynetteTheme.BG_SECONDARY,
                    border=ft.border.only(right=ft.BorderSide(1, SkynetteTheme.BORDER)),
                ),
                # Canvas
                self._build_canvas(),
                # Properties Panel
                self._build_properties_panel(),
            ],
            expand=True,
            spacing=0,
        )

    def _set_editor_mode(self, simple: bool):
        """Switch between Simple and Advanced editor modes."""
        if self.simple_mode != simple:
            self.simple_mode = simple
            self._update_content()
            self.page.update()

    def _build_execution_indicator(self) -> ft.Container:
        """Build execution status indicator."""
        if not self.last_execution_result:
            return ft.Container()

        result = self.last_execution_result
        if result.status == "completed":
            return ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.CHECK_CIRCLE, size=16, color=SkynetteTheme.SUCCESS),
                        ft.Text(
                            f"Last run: {result.duration_ms:.0f}ms",
                            size=12,
                            color=SkynetteTheme.SUCCESS,
                        ),
                    ],
                    spacing=4,
                ),
                padding=ft.padding.symmetric(horizontal=8),
                on_click=lambda e: self._show_execution_details(),
            )
        elif result.status == "failed":
            return ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.ERROR, size=16, color=SkynetteTheme.ERROR),
                        ft.Text("Failed", size=12, color=SkynetteTheme.ERROR),
                    ],
                    spacing=4,
                ),
                padding=ft.padding.symmetric(horizontal=8),
                on_click=lambda e: self._show_execution_details(),
            )
        return ft.Container()

    def _build_connection_lines(self):
        """Build visual lines showing connections between nodes."""
        if not self.current_workflow or not self.current_workflow.connections:
            return []

        from src.ui.theme import Theme

        positions = self._calculate_node_positions()
        lines = []

        for conn in self.current_workflow.connections:
            source_pos = positions.get(conn.source_node_id)
            target_pos = positions.get(conn.target_node_id)

            if not source_pos or not target_pos:
                continue

            # Calculate line endpoints (center of nodes)
            x1 = source_pos["x"] + 60  # Half of node width (120/2)
            y1 = source_pos["y"] + 40  # Half of node height (80/2)
            x2 = target_pos["x"] + 60
            y2 = target_pos["y"] + 40

            # Simple line representation (Flet doesn't have native SVG lines)
            # Use a rotated container as a visual line
            import math

            dx = x2 - x1
            dy = y2 - y1
            length = math.sqrt(dx*dx + dy*dy)
            angle = math.atan2(dy, dx)

            line = ft.Container(
                width=length,
                height=2,
                bgcolor=Theme.PRIMARY + "80",  # Semi-transparent
                rotate=ft.transform.Rotate(angle),
                left=x1,
                top=y1,
            )
            lines.append(line)

        return lines

    def _build_properties_panel(self):
        """Build the properties panel for selected node."""
        from src.ui.theme import Theme

        if not self.selected_node_id:
            return ft.Container(
                content=ft.Text(
                    "Select a node to configure",
                    size=12,
                    color=Theme.TEXT_SECONDARY,
                ),
                padding=20,
            )

        node = next((n for n in self.current_workflow.nodes if n.id == self.selected_node_id), None)
        if not node:
            return ft.Container(content=ft.Text("Node not found"))

        node_def = self.node_registry.get_definition(node.type)

        return ft.Container(
            content=ft.Column(
                controls=[
                    # Header
                    ft.Container(
                        content=ft.Column([
                            ft.Text(
                                node_def.name if node_def else node.type,
                                size=14,
                                weight=ft.FontWeight.W_600,
                            ),
                            ft.Text(
                                node_def.description if node_def else "",
                                size=11,
                                color=Theme.TEXT_SECONDARY,
                            ) if node_def and node_def.description else ft.Container(),
                        ]),
                        padding=16,
                        bgcolor=Theme.BG_SECONDARY,
                    ),

                    # Configuration fields
                    ft.Container(
                        content=ft.Column(
                            controls=self._build_node_config_fields(node),
                            scroll=ft.ScrollMode.AUTO,
                            spacing=12,
                        ),
                        padding=16,
                        expand=True,
                    ),

                    # Connection selector
                    ft.Container(
                        content=self._build_connection_selector(node),
                        padding=16,
                        border=ft.border.only(top=ft.BorderSide(1, Theme.BORDER)),
                    ),
                ],
                spacing=0,
                expand=True,
            ),
            width=320,
            bgcolor=Theme.BG_PRIMARY,
            border=ft.border.only(left=ft.BorderSide(1, Theme.BORDER)),
        )

    def _select_node(self, node_id: str):
        """Select a node for editing."""
        self.selected_node_id = node_id
        self._update_content()
        self.page.update()

    def _deselect_node(self):
        """Deselect the current node."""
        self.selected_node_id = None
        self._update_content()
        self.page.update()

    def _update_node_name(self, node_id: str, new_name: str):
        """Update a node's name."""
        if self.current_workflow:
            node = self.current_workflow.get_node(node_id)
            if node:
                node.name = new_name

    def _build_node_config_fields(self, node):
        """Build configuration fields for a node based on its definition."""
        from src.ui.theme import Theme

        node_def = self.node_registry.get_definition(node.type)
        if not node_def or not node_def.inputs:
            return [ft.Text("No configuration needed", size=12, color=Theme.TEXT_SECONDARY)]

        fields = []

        for field in node_def.inputs:
            # Get current value from node config
            current_value = node.config.get(field.name, field.default)

            # Create appropriate input widget based on field type
            field_type = field.type.value if hasattr(field.type, 'value') else str(field.type)

            if field_type in ["string", "text"]:
                widget = ft.TextField(
                    label=field.label or field.name,
                    value=str(current_value) if current_value is not None else "",
                    hint_text=field.description or field.placeholder,
                    multiline=field_type == "text",
                    min_lines=3 if field_type == "text" else 1,
                    on_change=lambda e, f=field: self._update_node_config(node.id, f.name, e.control.value),
                )
            elif field_type == "number":
                widget = ft.TextField(
                    label=field.label or field.name,
                    value=str(current_value) if current_value is not None else "",
                    hint_text=field.description,
                    keyboard_type=ft.KeyboardType.NUMBER,
                    on_change=lambda e, f=field: self._update_node_config(node.id, f.name, float(e.control.value) if e.control.value and '.' in e.control.value else int(e.control.value) if e.control.value else 0),
                )
            elif field_type == "boolean":
                widget = ft.Checkbox(
                    label=field.label or field.name,
                    value=bool(current_value) if current_value is not None else False,
                    on_change=lambda e, f=field: self._update_node_config(node.id, f.name, e.control.value),
                )
            elif field_type == "select":
                widget = ft.Dropdown(
                    label=field.label or field.name,
                    value=current_value,
                    options=[ft.dropdown.Option(key=opt.get("value", opt), text=opt.get("label", opt)) for opt in (field.options or [])],
                    on_change=lambda e, f=field: self._update_node_config(node.id, f.name, e.control.value),
                )
            else:
                # Default to text field, handle code/expression/json types
                is_code = field_type in ["expression", "json"]
                widget = ft.TextField(
                    label=field.label or field.name,
                    value=str(current_value) if current_value is not None else "",
                    multiline=is_code,
                    min_lines=3 if is_code else 1,
                    hint_text=field.description or field.placeholder,
                    on_change=lambda e, f=field: self._update_node_config(node.id, f.name, e.control.value),
                )

            fields.append(widget)

        return fields

    def _update_node_config(self, node_id: str, field_name: str, value):
        """Update a node's configuration."""
        node = next((n for n in self.current_workflow.nodes if n.id == node_id), None)
        if node:
            node.config[field_name] = value

    def _add_connection(self, source_id: str, target_id: str):
        """Add a connection between two nodes."""
        if not target_id or not self.current_workflow:
            return

        from src.core.workflow.models import WorkflowConnection

        # Check if connection already exists
        for conn in self.current_workflow.connections:
            if conn.source_node_id == source_id and conn.target_node_id == target_id:
                return

        # Add new connection
        self.current_workflow.connections.append(
            WorkflowConnection(source_node_id=source_id, target_node_id=target_id)
        )
        self._update_content()
        self.page.update()

    def _delete_node(self, node_id: str):
        """Delete a node from the workflow."""
        if not self.current_workflow:
            return

        # Remove the node
        self.current_workflow.nodes = [n for n in self.current_workflow.nodes if n.id != node_id]

        # Remove any connections involving this node
        self.current_workflow.connections = [
            c for c in self.current_workflow.connections
            if c.source_node_id != node_id and c.target_node_id != node_id
        ]

        # Deselect if this was the selected node
        if self.selected_node_id == node_id:
            self.selected_node_id = None

        self._update_content()
        self.page.update()

    def _build_connection_selector(self, node):
        """Build UI for selecting node connections."""
        from src.ui.theme import Theme

        # Get available target nodes (all except current and already connected)
        available_targets = [
            n for n in self.current_workflow.nodes
            if n.id != node.id
        ]

        # Find current connections from this node
        current_targets = [
            conn.target_node_id
            for conn in self.current_workflow.connections
            if conn.source_node_id == node.id
        ]

        def add_connection_to(target_id):
            from src.core.workflow.models import WorkflowConnection

            # Check if connection already exists
            exists = any(
                conn.source_node_id == node.id and conn.target_node_id == target_id
                for conn in self.current_workflow.connections
            )

            if not exists:
                conn = WorkflowConnection(
                    source_node_id=node.id,
                    target_node_id=target_id,
                )
                self.current_workflow.connections.append(conn)
                self._update_content()
                self.page.update()

        return ft.Column(
            controls=[
                ft.Text("Connections", size=12, weight=ft.FontWeight.W_600),
                ft.Dropdown(
                    label="Connect to",
                    options=[
                        ft.dropdown.Option(key=n.id, text=n.name or n.type)
                        for n in available_targets
                    ],
                    on_change=lambda e: add_connection_to(e.control.value) if e.control.value else None,
                ),
                # Show current connections
                *[
                    ft.Text(
                        f"→ {self._get_node_name(target_id)}",
                        size=11,
                        color=Theme.TEXT_SECONDARY,
                    )
                    for target_id in current_targets
                ]
            ],
            spacing=8,
        )

    def _get_node_name(self, node_id):
        """Get display name for a node."""
        node = next((n for n in self.current_workflow.nodes if n.id == node_id), None)
        if node:
            return node.name or node.type
        return "Unknown"

    def _show_execution_details(self):
        """Show detailed execution results."""
        if not self.last_execution_result:
            return

        result = self.last_execution_result
        node_results = []

        for nr in result.node_results:
            # Find node name
            node_name = nr.node_id
            if self.current_workflow:
                node = self.current_workflow.get_node(nr.node_id)
                if node:
                    node_name = node.name

            status_icon = ft.Icons.CHECK_CIRCLE if nr.success else ft.Icons.ERROR
            status_color = SkynetteTheme.SUCCESS if nr.success else SkynetteTheme.ERROR

            node_results.append(
                ft.ListTile(
                    leading=ft.Icon(status_icon, color=status_color, size=20),
                    title=ft.Text(node_name, size=13),
                    subtitle=ft.Text(
                        f"{nr.duration_ms:.1f}ms" if nr.success else nr.error or "Error",
                        size=11,
                        color=SkynetteTheme.TEXT_SECONDARY,
                    ),
                )
            )

        def close_dialog(e):
            dialog.open = False
            self.page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Execution Results - {result.status.title()}"),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(
                            f"Total Duration: {result.duration_ms:.0f}ms",
                            size=14,
                            weight=ft.FontWeight.W_500,
                        ),
                        ft.Divider(),
                        ft.Text("Node Results:", size=12, color=SkynetteTheme.TEXT_SECONDARY),
                        ft.Column(controls=node_results, scroll=ft.ScrollMode.AUTO),
                    ],
                    spacing=8,
                ),
                width=400,
                height=300,
            ),
            actions=[ft.TextButton("Close", on_click=close_dialog)],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _build_canvas(self):
        """Build the visual workflow canvas."""
        if not self.current_workflow:
            return ft.Container(content=ft.Text("No workflow loaded"), expand=True)

        positions = self._calculate_node_positions()

        # Build connection lines first (render behind nodes)
        connection_lines = self._build_connection_lines()

        # Build node widgets
        node_widgets = []
        for node in self.current_workflow.nodes:
            pos = positions.get(node.id, {"x": 0, "y": 0})
            node_widgets.append(
                ft.Container(
                    content=self._build_canvas_node(node),
                    left=pos["x"],
                    top=pos["y"],
                )
            )

        # Combine connections and nodes
        all_elements = connection_lines + node_widgets

        from src.ui.theme import Theme

        # Add empty state if no nodes
        if len(self.current_workflow.nodes) == 0:
            empty_state = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(
                            ft.Icons.TOUCH_APP_OUTLINED,
                            size=48,
                            color=SkynetteTheme.TEXT_MUTED,
                        ),
                        ft.Container(height=12),
                        ft.Text(
                            "Add Nodes to Your Workflow",
                            size=16,
                            weight=ft.FontWeight.W_600,
                            color=SkynetteTheme.TEXT_PRIMARY,
                        ),
                        ft.Container(height=8),
                        ft.Text(
                            "Click nodes in the palette to add them to the canvas",
                            size=12,
                            color=SkynetteTheme.TEXT_SECONDARY,
                        ),
                        ft.Text(
                            "Then click a node to configure its properties",
                            size=12,
                            color=SkynetteTheme.TEXT_SECONDARY,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=4,
                ),
                alignment=ft.alignment.center,
                expand=True,
            )
            all_elements.append(empty_state)

        return ft.Container(
            content=ft.Stack(controls=all_elements if all_elements else []),
            expand=True,
            bgcolor=Theme.BG_PRIMARY,
        )

    def _calculate_node_positions(self):
        """Calculate positions for nodes in a grid layout."""
        if not self.current_workflow or not self.current_workflow.nodes:
            return {}

        positions = {}
        nodes_per_row = 4
        x_spacing = 150
        y_spacing = 120
        x_offset = 50
        y_offset = 50

        for i, node in enumerate(self.current_workflow.nodes):
            row = i // nodes_per_row
            col = i % nodes_per_row
            positions[node.id] = {
                "x": x_offset + (col * x_spacing),
                "y": y_offset + (row * y_spacing),
            }

        return positions

    def _select_canvas_node(self, node_id):
        """Select a node on the canvas."""
        self.selected_node_id = node_id
        self._update_content()  # Refresh to show properties panel
        self.page.update()

    def _build_canvas_node(self, node: WorkflowNode) -> ft.Container:
        """Render a single node on the canvas."""
        from src.ui.theme import Theme

        # Get node definition for styling
        node_def = self.node_registry.get_definition(node.type)

        # Determine color by category
        color_map = {
            "trigger": Theme.WARNING,
            "action": Theme.PRIMARY,
            "flow": Theme.INFO,
            "http": Theme.SUCCESS,
        }
        color = color_map.get(node_def.category if node_def else "action", Theme.PRIMARY)

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(
                        ft.Icons.CIRCLE,
                        size=16,
                        color=color,
                    ),
                    ft.Text(
                        node.name or node_def.name if node_def else node.type,
                        size=12,
                        weight=ft.FontWeight.W_600,
                        color=Theme.TEXT_PRIMARY,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        node_def.name if node_def else node.type,
                        size=10,
                        color=Theme.TEXT_SECONDARY,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4,
            ),
            width=120,
            height=80,
            bgcolor=Theme.BG_SECONDARY,
            border=ft.border.all(2, color),
            border_radius=Theme.RADIUS_MD,
            padding=12,
            data=node.id,  # Store node ID for click handling
            on_click=lambda e: self._select_canvas_node(node.id),
        )

    def _add_node_to_workflow(self, node_def):
        """Add a new node to the current workflow."""
        if not self.current_workflow:
            return

        # Calculate position based on existing nodes
        max_x = 100
        for node in self.current_workflow.nodes:
            if node.position.get("x", 0) > max_x:
                max_x = node.position.get("x", 0)

        new_node = WorkflowNode(
            type=node_def.type,
            name=node_def.name,
            position={"x": max_x + 220, "y": 100},
            config={field.name: field.default for field in node_def.inputs if field.default is not None},
        )
        self.current_workflow.nodes.append(new_node)

        # Refresh editor
        self._update_content()
        self.page.update()

    def _save_current_workflow(self):
        """Save the current workflow."""
        if self.current_workflow:
            try:
                self.storage.save_workflow(self.current_workflow)
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Workflow '{self.current_workflow.name}' saved"),
                    bgcolor=SkynetteTheme.SUCCESS,
                )
                self.page.snack_bar.open = True
                self.page.update()
            except Exception as e:
                self._show_error_dialog(
                    "Save Failed",
                    f"Could not save workflow '{self.current_workflow.name}'.",
                    f"Error: {str(e)}\n\nCheck file permissions and disk space."
                )

    def _run_current_workflow(self):
        """Run the current workflow."""
        if not self.current_workflow:
            return

        # Show loading
        self._show_loading("Executing workflow...")

        # Run async execution in the event loop
        async def run_async():
            try:
                execution = await self.executor.execute(self.current_workflow)
                self.storage.save_execution(execution)

                # Store result for UI display
                self.last_execution_result = execution

                # Show result
                if execution.status == "completed":
                    self.page.snack_bar = ft.SnackBar(
                        content=ft.Text(f"Workflow '{self.current_workflow.name}' completed successfully"),
                        bgcolor=SkynetteTheme.SUCCESS,
                    )
                else:
                    self.page.snack_bar = ft.SnackBar(
                        content=ft.Text(f"Workflow execution {execution.status}"),
                        bgcolor=SkynetteTheme.WARNING,
                    )

                self.page.snack_bar.open = True
                self.page.update()
            except WorkflowExecutionError as e:
                self._show_error_dialog(
                    "Workflow Execution Failed",
                    f"The workflow '{self.current_workflow.name}' failed during execution.",
                    f"Error: {str(e)}\n\nCheck node configurations and connections."
                )
            except Exception as e:
                self._show_error_dialog(
                    "Unexpected Error",
                    "An unexpected error occurred during workflow execution.",
                    f"Error: {str(e)}\n\nPlease check logs for more details."
                )
            finally:
                self._hide_loading()

                # Refresh UI to show execution indicator
                self._update_content()
                self.page.update()

        # Use page.run_task for async operations in Flet
        self.page.run_task(run_async)

    def _run_workflow(self, workflow_id: str):
        """Run a workflow by ID."""
        workflow = self.storage.load_workflow(workflow_id)
        if workflow:
            self.current_workflow = workflow
            self._run_current_workflow()

    def _duplicate_workflow(self, workflow_id: str):
        """Duplicate a workflow."""
        workflow = self.storage.load_workflow(workflow_id)
        if workflow:
            # Create copy with new ID and name
            new_workflow = Workflow(
                name=f"{workflow.name} (Copy)",
                description=workflow.description,
                nodes=workflow.nodes,
                connections=workflow.connections,
                variables=workflow.variables,
                settings=workflow.settings,
            )
            self.storage.save_workflow(new_workflow)
            self._navigate_to("workflows")

    def _delete_workflow(self, workflow_id: str, workflow_name: str = None):
        """Delete a workflow with confirmation."""
        # Get workflow name if not provided
        if not workflow_name:
            workflow = self.storage.load_workflow(workflow_id)
            workflow_name = workflow.name if workflow else "Unknown"

        def confirm_delete(e):
            try:
                self.storage.delete_workflow(workflow_id)
                dialog.open = False
                self.page.update()
                self._navigate_to("workflows")
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Workflow '{workflow_name}' deleted"),
                    bgcolor=SkynetteTheme.SUCCESS,
                )
                self.page.snack_bar.open = True
                self.page.update()
            except Exception as ex:
                dialog.open = False
                self.page.update()
                self._show_error_dialog(
                    "Delete Failed",
                    f"Could not delete workflow '{workflow_name}'.",
                    f"Error: {str(ex)}\n\nWorkflow may be in use or database may be locked."
                )

        def cancel(e):
            dialog.open = False
            self.page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Delete Workflow?"),
            content=ft.Text("This action cannot be undone."),
            actions=[
                ft.TextButton("Cancel", on_click=cancel),
                ft.ElevatedButton(
                    "Delete",
                    bgcolor=SkynetteTheme.ERROR,
                    color=SkynetteTheme.TEXT_PRIMARY,
                    on_click=confirm_delete,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.End,
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _use_example_prompt(self, text: str):
        """Use an example prompt in the assistant."""
        # Set the text in the input field and submit
        if self.chat_input_field:
            self.chat_input_field.value = text
            self.page.update()
            self._on_chat_submit(None)

    def _on_nav_hover(self, e):
        """Handle navigation item hover."""
        e.control.bgcolor = (
            SkynetteTheme.BG_TERTIARY if e.data == "true" else "transparent"
        )
        e.control.update()

    def _on_example_hover(self, e):
        """Handle example prompt hover."""
        e.control.bgcolor = (
            SkynetteTheme.BORDER if e.data == "true" else SkynetteTheme.BG_TERTIARY
        )
        e.control.update()

    def _on_resize(self, e):
        """Handle window resize."""
        # Hide assistant on small screens
        if self.page.width and self.page.width < 800:
            if self.assistant_visible:
                self._toggle_assistant()
