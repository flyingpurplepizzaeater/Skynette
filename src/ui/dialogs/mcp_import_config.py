"""Dialog for importing MCP servers from mcp.json file."""

import json
import flet as ft
from pathlib import Path
from typing import Callable, Optional

from src.ui.theme import Theme
from src.agent.mcp.models.server import (
    MCPServerConfig,
    TransportType,
    ServerCategory,
)
from src.agent.mcp.models.trust import TrustLevel


def parse_mcp_config(config_path: Path) -> list[MCPServerConfig]:
    """
    Parse mcp.json file and return list of server configs.

    Supports both Claude Desktop and Claude Code mcp.json formats.
    """
    with open(config_path) as f:
        data = json.load(f)

    configs = []
    mcp_servers = data.get("mcpServers", {})

    for name, server_data in mcp_servers.items():
        # Determine transport type
        if "url" in server_data:
            transport: TransportType = "http"
        else:
            transport = "stdio"

        trust: TrustLevel = "user_added"
        category: ServerCategory = "other"

        config = MCPServerConfig(
            name=name,
            transport=transport,
            command=server_data.get("command"),
            args=server_data.get("args", []),
            env=server_data.get("env", {}),
            url=server_data.get("url"),
            headers=server_data.get("headers", {}),
            trust_level=trust,  # Imported = untrusted
            sandbox_enabled=True,  # Default to sandboxed
            category=category,  # User can recategorize
        )
        configs.append(config)

    return configs


class MCPImportConfigDialog(ft.AlertDialog):
    """Dialog for importing MCP servers from mcp.json file."""

    def __init__(
        self,
        on_import: Callable[[list[MCPServerConfig]], None],
        on_cancel: Optional[Callable[[], None]] = None,
    ):
        super().__init__()
        self.modal = True
        self.on_import = on_import
        self.on_cancel = on_cancel
        self.parsed_configs: list[MCPServerConfig] = []

        # File picker
        self.file_picker = ft.FilePicker(on_result=self._on_file_picked)

        # Path display
        self.path_field = ft.TextField(
            label="Config File Path",
            hint_text="Select mcp.json file or paste path",
            border_color=Theme.BORDER,
            expand=True,
        )
        self.path_field.on_change = self._on_path_change

        # Preview area
        self.preview_text = ft.Text(
            "Select a file to preview servers",
            size=12,
            color=Theme.TEXT_SECONDARY,
        )
        self.preview_list = ft.Column(
            controls=[],
            spacing=4,
            scroll=ft.ScrollMode.AUTO,
        )

        self._build_dialog()

    def _build_dialog(self):
        """Build the dialog content."""
        self.title = ft.Text(
            "Import MCP Servers",
            size=18,
            weight=ft.FontWeight.BOLD,
        )

        self.content = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Import server configurations from a Claude Desktop or Claude Code mcp.json file.",
                        size=12,
                        color=Theme.TEXT_SECONDARY,
                    ),
                    ft.Row(
                        controls=[
                            self.path_field,
                            ft.IconButton(
                                icon=ft.Icons.FOLDER_OPEN,
                                tooltip="Browse",
                                on_click=lambda _: self.file_picker.pick_files(
                                    allowed_extensions=["json"],
                                    dialog_title="Select mcp.json",
                                ),
                            ),
                        ],
                        spacing=Theme.SPACING_SM,
                    ),
                    ft.Divider(height=1, color=Theme.BORDER),
                    ft.Text("Preview:", size=14, weight=ft.FontWeight.W_500),
                    ft.Container(
                        content=ft.Column(
                            controls=[self.preview_text, self.preview_list],
                            spacing=8,
                        ),
                        bgcolor=Theme.SURFACE,
                        padding=Theme.SPACING_SM,
                        border_radius=Theme.RADIUS_SM,
                        height=200,
                    ),
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.WARNING, color=Theme.WARNING, size=16),
                                ft.Text(
                                    "Imported servers will be marked as untrusted and sandboxed by default.",
                                    size=11,
                                    color=Theme.TEXT_SECONDARY,
                                ),
                            ],
                            spacing=8,
                        ),
                    ),
                ],
                spacing=Theme.SPACING_MD,
            ),
            width=500,
            height=420,
        )

        self.import_button = ft.ElevatedButton(
            "Import",
            bgcolor=Theme.PRIMARY,
            color=Theme.TEXT_PRIMARY,
            on_click=self._handle_import,
            disabled=True,
        )

        self.actions = [
            self.file_picker,
            ft.TextButton("Cancel", on_click=self._handle_cancel),
            self.import_button,
        ]

    def _on_file_picked(self, e: ft.FilePickerResultEvent):
        """Handle file picker result."""
        if e.files and len(e.files) > 0:
            self.path_field.value = e.files[0].path
            self._parse_and_preview()
            self.update()

    def _on_path_change(self, e):
        """Handle manual path entry."""
        self._parse_and_preview()

    def _parse_and_preview(self):
        """Parse the config file and show preview."""
        path = self.path_field.value
        if not path:
            return

        try:
            config_path = Path(path)
            if not config_path.exists():
                self.preview_text.value = "File not found"
                self.preview_text.color = Theme.ERROR
                self.preview_list.controls = []
                self.parsed_configs = []
                self._update_import_button()
                self.update()
                return

            self.parsed_configs = parse_mcp_config(config_path)

            if not self.parsed_configs:
                self.preview_text.value = "No servers found in file"
                self.preview_text.color = Theme.WARNING
                self.preview_list.controls = []
            else:
                self.preview_text.value = f"Found {len(self.parsed_configs)} server(s):"
                self.preview_text.color = Theme.TEXT_SECONDARY
                self.preview_list.controls = [
                    ft.Row(
                        controls=[
                            ft.Icon(
                                ft.Icons.CHECK_CIRCLE_OUTLINE,
                                color=Theme.SUCCESS,
                                size=16,
                            ),
                            ft.Text(
                                f"{c.name} ({c.transport})",
                                size=12,
                            ),
                        ],
                        spacing=8,
                    )
                    for c in self.parsed_configs
                ]

        except json.JSONDecodeError:
            self.preview_text.value = "Invalid JSON file"
            self.preview_text.color = Theme.ERROR
            self.preview_list.controls = []
            self.parsed_configs = []
        except Exception as e:
            self.preview_text.value = f"Error: {str(e)}"
            self.preview_text.color = Theme.ERROR
            self.preview_list.controls = []
            self.parsed_configs = []

        self._update_import_button()
        self.update()

    def _update_import_button(self):
        """Enable/disable import button based on parsed configs."""
        self.import_button.disabled = len(self.parsed_configs) == 0

    def _handle_cancel(self, e):
        """Handle cancel button."""
        self.open = False
        self.update()
        if self.on_cancel:
            self.on_cancel()

    def _handle_import(self, e):
        """Handle import button."""
        if self.parsed_configs:
            self.open = False
            self.update()
            self.on_import(self.parsed_configs)
