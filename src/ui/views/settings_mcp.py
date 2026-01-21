"""MCP Server settings content builder.

Provides build_mcp_settings_content() that returns Flet controls compatible
with the existing SettingsView._build_section() pattern.
"""

import flet as ft
from typing import Optional

from src.ui.theme import Theme
from src.agent.mcp.storage.server_storage import get_mcp_storage
from src.agent.mcp.models.server import MCPServerConfig, MCPServerStatus, ServerCategory
from src.agent.mcp.models.trust import TrustLevel
from src.agent.mcp.curated.servers import list_curated_servers


class MCPSettingsController:
    """Controller for MCP settings state and actions.

    Manages server list state and provides callbacks for UI actions.
    This is a controller, not a view - it doesn't have Flet lifecycle methods.
    """

    def __init__(self, page: ft.Page):
        self.page = page
        self.storage = get_mcp_storage()
        self.servers: list[MCPServerConfig] = []
        self._status_cache: dict[str, MCPServerStatus] = {}
        self._content_column: Optional[ft.Column] = None

    def load_servers(self) -> None:
        """Load server configs from storage."""
        self.servers = self.storage.list_servers()

    def refresh_ui(self) -> None:
        """Refresh the UI after state changes."""
        if self._content_column:
            self._content_column.controls = [self._build_server_list()]
            self.page.update()

    def _build_server_list(self) -> ft.Control:
        """Build the list of configured servers."""
        if not self.servers:
            return ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.EXTENSION_OFF, size=48, color=Theme.TEXT_MUTED),
                        ft.Text(
                            "No MCP servers configured",
                            size=14,
                            color=Theme.TEXT_SECONDARY,
                        ),
                        ft.Text(
                            "Add servers to extend agent capabilities",
                            size=12,
                            color=Theme.TEXT_MUTED,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                ),
                padding=Theme.SPACING_LG,
                alignment=ft.alignment.center,
            )

        # Group by category
        by_category: dict[ServerCategory, list[MCPServerConfig]] = {}
        for server in self.servers:
            cat = server.category
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(server)

        controls = []
        for category, servers in sorted(by_category.items(), key=lambda x: x[0]):
            controls.append(
                ft.Text(
                    category.replace("_", " ").title(),
                    size=12,
                    color=Theme.TEXT_SECONDARY,
                    weight=ft.FontWeight.W_500,
                )
            )
            for server in servers:
                controls.append(self._build_server_row(server))
            controls.append(ft.Container(height=8))  # Spacing

        return ft.Container(
            content=ft.Column(controls=controls, spacing=4),
            bgcolor=Theme.SURFACE,
            padding=Theme.SPACING_MD,
            border_radius=Theme.RADIUS_MD,
            border=ft.Border.all(1, Theme.BORDER),
        )

    def _build_server_row(self, server: MCPServerConfig) -> ft.Control:
        """Build a single server row."""
        # Trust level icon
        trust_level: TrustLevel = server.trust_level
        if trust_level == "builtin":
            trust_icon = ft.Icon(ft.Icons.VERIFIED, color=Theme.PRIMARY, size=16)
            trust_tooltip = "Built-in"
        elif trust_level == "verified":
            trust_icon = ft.Icon(ft.Icons.VERIFIED_USER, color=Theme.SUCCESS, size=16)
            trust_tooltip = "Verified"
        else:
            trust_icon = ft.Icon(ft.Icons.SHIELD_OUTLINED, color=Theme.WARNING, size=16)
            trust_tooltip = "User-added (sandboxed)" if server.sandbox_enabled else "User-added"

        # Connection status
        status = self._status_cache.get(server.id)
        if status and status.connected:
            status_icon = ft.Icon(ft.Icons.CIRCLE, color=Theme.SUCCESS, size=8)
            status_text = f"{status.tools_count} tools"
        elif status and status.error:
            status_icon = ft.Icon(ft.Icons.CIRCLE, color=Theme.ERROR, size=8)
            status_text = "Error"
        else:
            status_icon = ft.Icon(ft.Icons.CIRCLE_OUTLINED, color=Theme.TEXT_MUTED, size=8)
            status_text = "Not connected"

        def on_row_hover(e):
            e.control.bgcolor = Theme.BG_TERTIARY if e.data == "true" else None
            e.control.update()

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Tooltip(message=trust_tooltip, content=trust_icon),
                    ft.Column(
                        controls=[
                            ft.Text(server.name, size=14, weight=ft.FontWeight.W_500),
                            ft.Row(
                                controls=[
                                    status_icon,
                                    ft.Text(status_text, size=11, color=Theme.TEXT_SECONDARY),
                                    ft.Text(
                                        f" | {server.transport}",
                                        size=11,
                                        color=Theme.TEXT_MUTED,
                                    ),
                                ],
                                spacing=4,
                            ),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    ft.Switch(
                        value=server.enabled,
                        active_color=Theme.PRIMARY,
                        on_change=lambda e, s=server: self._toggle_server(s, e.control.value),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE,
                        icon_color=Theme.TEXT_SECONDARY,
                        tooltip="Remove",
                        on_click=lambda _, s=server: self._delete_server(s),
                    ),
                ],
                spacing=Theme.SPACING_SM,
            ),
            padding=ft.padding.symmetric(vertical=4, horizontal=8),
            border_radius=Theme.RADIUS_SM,
            on_hover=on_row_hover,
        )

    def show_add_dialog(self, e=None) -> None:
        """Show add server dialog."""
        from src.ui.dialogs.mcp_add_server import MCPAddServerDialog

        dialog = MCPAddServerDialog(on_save=self._save_server)
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def show_import_dialog(self, e=None) -> None:
        """Show import dialog."""
        from src.ui.dialogs.mcp_import_config import MCPImportConfigDialog

        dialog = MCPImportConfigDialog(on_import=self._import_servers)
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def show_curated_dialog(self, e=None) -> None:
        """Show curated servers selection."""
        # Get curated servers not already added
        curated = list_curated_servers()
        existing_names = {s.name for s in self.servers}
        available = [c for c in curated if c.name not in existing_names]

        if not available:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("All curated servers already added"),
            )
            self.page.snack_bar.open = True
            self.page.update()
            return

        # Simple selection dialog
        selected: list[MCPServerConfig] = []

        def toggle_select(e, config: MCPServerConfig):
            if e.control.value:
                selected.append(config)
            else:
                if config in selected:
                    selected.remove(config)

        items = []
        for config in available:
            items.append(
                ft.ListTile(
                    leading=ft.Checkbox(
                        value=False,
                        on_change=lambda e, c=config: toggle_select(e, c),
                    ),
                    title=ft.Text(config.name),
                    subtitle=ft.Text(config.description or "", size=11),
                )
            )

        def close_dialog(dlg):
            dlg.open = False
            self.page.update()

        def add_curated(dlg):
            dlg.open = False
            for config in selected:
                self.storage.save_server(config)
            self.load_servers()
            self.refresh_ui()

        dialog = ft.AlertDialog(
            title=ft.Text("Add Curated Servers"),
            content=ft.Container(
                content=ft.Column(controls=items, scroll=ft.ScrollMode.AUTO),
                width=400,
                height=300,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: close_dialog(dialog)),
                ft.ElevatedButton(
                    "Add Selected",
                    bgcolor=Theme.PRIMARY,
                    on_click=lambda _: add_curated(dialog),
                ),
            ],
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _save_server(self, config: MCPServerConfig) -> None:
        """Save a new server config."""
        self.storage.save_server(config)
        self.load_servers()
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(f"Added server: {config.name}"),
        )
        self.page.snack_bar.open = True
        self.refresh_ui()

    def _import_servers(self, configs: list[MCPServerConfig]) -> None:
        """Import multiple server configs."""
        for config in configs:
            self.storage.save_server(config)
        self.load_servers()
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(f"Imported {len(configs)} server(s)"),
        )
        self.page.snack_bar.open = True
        self.refresh_ui()

    def _toggle_server(self, server: MCPServerConfig, enabled: bool) -> None:
        """Toggle server enabled state."""
        server.enabled = enabled
        self.storage.save_server(server)

    def _delete_server(self, server: MCPServerConfig) -> None:
        """Delete a server config."""
        self.storage.delete_server(server.id)
        self.load_servers()
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(f"Removed server: {server.name}"),
        )
        self.page.snack_bar.open = True
        self.refresh_ui()


def build_mcp_settings_content(page: ft.Page) -> ft.Column:
    """
    Build MCP settings content compatible with SettingsView._build_section().

    This function returns a Flet Column containing the MCP settings UI.
    It creates a controller instance and wires up the UI.

    Args:
        page: The Flet page (needed for dialogs and snackbars)

    Returns:
        A Column containing the MCP settings controls
    """
    controller = MCPSettingsController(page)
    controller.load_servers()

    # Header with action buttons
    header = ft.Row(
        controls=[
            ft.Column(
                controls=[
                    ft.Text(
                        "MCP Servers",
                        size=16,
                        weight=ft.FontWeight.W_600,
                        color=Theme.TEXT_PRIMARY,
                    ),
                    ft.Text(
                        "Connect to external tool servers",
                        size=12,
                        color=Theme.TEXT_SECONDARY,
                    ),
                ],
                spacing=2,
                expand=True,
            ),
            ft.PopupMenuButton(
                items=[
                    ft.PopupMenuItem(
                        text="Add Server",
                        icon=ft.Icons.ADD,
                        on_click=controller.show_add_dialog,
                    ),
                    ft.PopupMenuItem(
                        text="Import from mcp.json",
                        icon=ft.Icons.FILE_UPLOAD,
                        on_click=controller.show_import_dialog,
                    ),
                    ft.PopupMenuItem(),  # Divider
                    ft.PopupMenuItem(
                        text="Add Curated Servers",
                        icon=ft.Icons.STAR,
                        on_click=controller.show_curated_dialog,
                    ),
                ],
                icon=ft.Icons.MORE_VERT,
            ),
        ],
    )

    # Server list (will be refreshed by controller)
    server_list_container = ft.Column(
        controls=[controller._build_server_list()],
        spacing=Theme.SPACING_MD,
    )
    controller._content_column = server_list_container

    return ft.Column(
        controls=[header, server_list_container],
        spacing=Theme.SPACING_MD,
    )
