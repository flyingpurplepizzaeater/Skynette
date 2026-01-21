"""Dialog for adding a new MCP server."""

import flet as ft
from typing import Callable, Optional
from uuid import uuid4

from src.ui.theme import Theme
from src.agent.mcp.models.server import (
    MCPServerConfig,
    TransportType,
    ServerCategory,
)
from src.agent.mcp.models.trust import TrustLevel


class MCPAddServerDialog(ft.AlertDialog):
    """Dialog for configuring and adding a new MCP server."""

    def __init__(
        self,
        on_save: Callable[[MCPServerConfig], None],
        on_cancel: Optional[Callable[[], None]] = None,
    ):
        super().__init__()
        self.modal = True
        self.on_save = on_save
        self.on_cancel = on_cancel

        # Form fields
        self.name_field = ft.TextField(
            label="Server Name",
            hint_text="e.g., My Filesystem Server",
            border_color=Theme.BORDER,
            expand=True,
        )
        self.description_field = ft.TextField(
            label="Description (optional)",
            hint_text="What this server provides",
            border_color=Theme.BORDER,
            expand=True,
        )
        self.transport_dropdown = ft.Dropdown(
            label="Transport",
            value="stdio",
            options=[
                ft.dropdown.Option("stdio", "Local (stdio)"),
                ft.dropdown.Option("http", "Remote (HTTP)"),
            ],
            border_color=Theme.BORDER,
            width=200,
        )
        # Set on_change after construction
        self.transport_dropdown.on_change = self._on_transport_change
        self.category_dropdown = ft.Dropdown(
            label="Category",
            value="other",
            options=[
                ft.dropdown.Option("browser_tools", "Browser Tools"),
                ft.dropdown.Option("file_tools", "File Tools"),
                ft.dropdown.Option("dev_tools", "Development Tools"),
                ft.dropdown.Option("data_tools", "Data Tools"),
                ft.dropdown.Option("productivity", "Productivity"),
                ft.dropdown.Option("other", "Other"),
            ],
            border_color=Theme.BORDER,
            width=200,
        )

        # Stdio fields
        self.command_field = ft.TextField(
            label="Command",
            hint_text="e.g., npx, node, python",
            border_color=Theme.BORDER,
            expand=True,
        )
        self.args_field = ft.TextField(
            label="Arguments",
            hint_text="Space-separated: -y @package/name --flag",
            border_color=Theme.BORDER,
            expand=True,
        )

        # HTTP fields
        self.url_field = ft.TextField(
            label="URL",
            hint_text="https://mcp.example.com/api",
            border_color=Theme.BORDER,
            expand=True,
            visible=False,
        )

        # Security
        self.sandbox_checkbox = ft.Checkbox(
            label="Enable sandboxing (recommended for untrusted servers)",
            value=True,
        )

        self._build_dialog()

    def _build_dialog(self):
        """Build the dialog content."""
        self.title = ft.Text(
            "Add MCP Server",
            size=18,
            weight=ft.FontWeight.BOLD,
        )

        self.stdio_fields = ft.Column(
            controls=[
                self.command_field,
                self.args_field,
            ],
            spacing=Theme.SPACING_SM,
        )

        self.http_fields = ft.Column(
            controls=[self.url_field],
            spacing=Theme.SPACING_SM,
            visible=False,
        )

        self.content = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row([self.name_field], spacing=Theme.SPACING_SM),
                    ft.Row([self.description_field], spacing=Theme.SPACING_SM),
                    ft.Divider(height=1, color=Theme.BORDER),
                    ft.Row(
                        [self.transport_dropdown, self.category_dropdown],
                        spacing=Theme.SPACING_MD,
                    ),
                    self.stdio_fields,
                    self.http_fields,
                    ft.Divider(height=1, color=Theme.BORDER),
                    self.sandbox_checkbox,
                ],
                spacing=Theme.SPACING_MD,
                scroll=ft.ScrollMode.AUTO,
            ),
            width=500,
            height=400,
        )

        self.actions = [
            ft.TextButton("Cancel", on_click=self._handle_cancel),
            ft.ElevatedButton(
                "Add Server",
                bgcolor=Theme.PRIMARY,
                color=Theme.TEXT_PRIMARY,
                on_click=self._handle_save,
            ),
        ]

    def _on_transport_change(self, e):
        """Toggle fields based on transport type."""
        is_stdio = self.transport_dropdown.value == "stdio"
        self.stdio_fields.visible = is_stdio
        self.http_fields.visible = not is_stdio
        self.url_field.visible = not is_stdio
        self.update()

    def _handle_cancel(self, e):
        """Handle cancel button."""
        self.open = False
        self.update()
        if self.on_cancel:
            self.on_cancel()

    def _handle_save(self, e):
        """Handle save button - validate and create config."""
        # Validate required fields
        if not self.name_field.value:
            self.name_field.error_text = "Name is required"
            self.update()
            return

        is_stdio = self.transport_dropdown.value == "stdio"

        if is_stdio and not self.command_field.value:
            self.command_field.error_text = "Command is required"
            self.update()
            return

        if not is_stdio and not self.url_field.value:
            self.url_field.error_text = "URL is required"
            self.update()
            return

        # Parse args
        args = []
        if self.args_field.value:
            args = self.args_field.value.split()

        # Create config
        transport: TransportType = "stdio" if is_stdio else "http"
        category: ServerCategory = self.category_dropdown.value  # type: ignore
        trust: TrustLevel = "user_added"

        config = MCPServerConfig(
            id=str(uuid4()),
            name=self.name_field.value,
            description=self.description_field.value or None,
            transport=transport,
            command=self.command_field.value if is_stdio else None,
            args=args,
            url=self.url_field.value if not is_stdio else None,
            category=category,
            trust_level=trust,
            sandbox_enabled=self.sandbox_checkbox.value or True,
        )

        self.open = False
        self.update()
        self.on_save(config)
