"""Settings view - Application configuration."""

import flet as ft
from src.ui.theme import Theme
from src.ui.views.settings_mcp import build_mcp_settings_content


class SettingsView(ft.Column):
    """Application settings and configuration."""

    def __init__(self):
        super().__init__()
        self.expand = True
        self._mcp_container: ft.Container | None = None

    def did_mount(self):
        """Called when view is mounted to page."""
        # Build MCP content now that page is available
        if self._mcp_container and self.page:
            self._mcp_container.content = build_mcp_settings_content(self.page)
            self.page.update()

    def build(self):
        # MCP container - content populated in did_mount when page available
        self._mcp_container = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "MCP Servers",
                        size=16,
                        weight=ft.FontWeight.W_600,
                        color=Theme.TEXT_PRIMARY,
                    ),
                    ft.Text(
                        "Loading...",
                        size=12,
                        color=Theme.TEXT_SECONDARY,
                    ),
                ],
                spacing=Theme.SPACING_SM,
            ),
            bgcolor=Theme.SURFACE,
            padding=Theme.SPACING_MD,
            border_radius=Theme.RADIUS_MD,
            border=ft.Border.all(1, Theme.BORDER),
        )

        return ft.Column(
            controls=[
                self._build_header(),
                ft.Container(
                    content=ft.Column(
                        controls=[
                            self._build_section("Appearance", self._build_appearance_settings()),
                            self._build_section("AI Settings", self._build_ai_settings()),
                            self._build_section("Storage", self._build_storage_settings()),
                            # MCP Servers section (has its own internal header)
                            self._mcp_container,
                            self._build_section("Advanced", self._build_advanced_settings()),
                        ],
                        scroll=ft.ScrollMode.AUTO,
                        spacing=Theme.SPACING_LG,
                    ),
                    expand=True,
                ),
            ],
            expand=True,
            spacing=Theme.SPACING_MD,
        )

    def _build_header(self):
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(
                        "Settings",
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        color=Theme.TEXT_PRIMARY,
                    ),
                ],
            ),
        )

    def _build_section(self, title, content):
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        title,
                        size=16,
                        weight=ft.FontWeight.W_600,
                        color=Theme.TEXT_PRIMARY,
                    ),
                    ft.Container(
                        content=content,
                        bgcolor=Theme.SURFACE,
                        padding=Theme.SPACING_MD,
                        border_radius=Theme.RADIUS_MD,
                        border=ft.Border.all(1, Theme.BORDER),
                    ),
                ],
                spacing=Theme.SPACING_SM,
            ),
        )

    def _build_appearance_settings(self):
        return ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Column(
                            controls=[
                                ft.Text("Theme", size=14, weight=ft.FontWeight.W_500),
                                ft.Text(
                                    "Choose light or dark mode",
                                    size=12,
                                    color=Theme.TEXT_SECONDARY,
                                ),
                            ],
                            expand=True,
                            spacing=2,
                        ),
                        ft.Dropdown(
                            value="dark",
                            width=150,
                            height=40,
                            options=[
                                ft.dropdown.Option("dark", "Dark"),
                                ft.dropdown.Option("light", "Light"),
                                ft.dropdown.Option("system", "System"),
                            ],
                            border_color=Theme.BORDER,
                        ),
                    ],
                ),
                ft.Divider(height=1, color=Theme.BORDER),
                ft.Row(
                    controls=[
                        ft.Column(
                            controls=[
                                ft.Text("Accent Color", size=14, weight=ft.FontWeight.W_500),
                                ft.Text(
                                    "Primary accent color",
                                    size=12,
                                    color=Theme.TEXT_SECONDARY,
                                ),
                            ],
                            expand=True,
                            spacing=2,
                        ),
                        ft.Row(
                            controls=[
                                ft.Container(
                                    width=28,
                                    height=28,
                                    bgcolor=Theme.PRIMARY,
                                    border_radius=14,
                                    border=ft.Border.all(2, Theme.TEXT_PRIMARY),
                                ),
                                ft.Container(width=24, height=24, bgcolor="#10B981", border_radius=12),
                                ft.Container(width=24, height=24, bgcolor="#F59E0B", border_radius=12),
                                ft.Container(width=24, height=24, bgcolor="#EF4444", border_radius=12),
                                ft.Container(width=24, height=24, bgcolor="#8B5CF6", border_radius=12),
                            ],
                            spacing=8,
                        ),
                    ],
                ),
                ft.Divider(height=1, color=Theme.BORDER),
                ft.Row(
                    controls=[
                        ft.Column(
                            controls=[
                                ft.Text("Editor Grid", size=14, weight=ft.FontWeight.W_500),
                                ft.Text(
                                    "Show grid in workflow editor",
                                    size=12,
                                    color=Theme.TEXT_SECONDARY,
                                ),
                            ],
                            expand=True,
                            spacing=2,
                        ),
                        ft.Switch(value=True, active_color=Theme.PRIMARY),
                    ],
                ),
            ],
            spacing=Theme.SPACING_MD,
        )

    def _build_ai_settings(self):
        return ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Column(
                            controls=[
                                ft.Text("Default AI Provider", size=14, weight=ft.FontWeight.W_500),
                                ft.Text(
                                    "Used when no specific provider is selected",
                                    size=12,
                                    color=Theme.TEXT_SECONDARY,
                                ),
                            ],
                            expand=True,
                            spacing=2,
                        ),
                        ft.Dropdown(
                            value="local",
                            width=150,
                            height=40,
                            options=[
                                ft.dropdown.Option("local", "Local (Free)"),
                                ft.dropdown.Option("openai", "OpenAI"),
                                ft.dropdown.Option("anthropic", "Anthropic"),
                                ft.dropdown.Option("auto", "Auto-select"),
                            ],
                            border_color=Theme.BORDER,
                        ),
                    ],
                ),
                ft.Divider(height=1, color=Theme.BORDER),
                ft.Row(
                    controls=[
                        ft.Column(
                            controls=[
                                ft.Text("Auto-fallback", size=14, weight=ft.FontWeight.W_500),
                                ft.Text(
                                    "Automatically try next provider on failure",
                                    size=12,
                                    color=Theme.TEXT_SECONDARY,
                                ),
                            ],
                            expand=True,
                            spacing=2,
                        ),
                        ft.Switch(value=True, active_color=Theme.PRIMARY),
                    ],
                ),
                ft.Divider(height=1, color=Theme.BORDER),
                ft.Row(
                    controls=[
                        ft.Column(
                            controls=[
                                ft.Text("GPU Acceleration", size=14, weight=ft.FontWeight.W_500),
                                ft.Text(
                                    "Use GPU for local model inference",
                                    size=12,
                                    color=Theme.TEXT_SECONDARY,
                                ),
                            ],
                            expand=True,
                            spacing=2,
                        ),
                        ft.Switch(value=True, active_color=Theme.PRIMARY),
                    ],
                ),
            ],
            spacing=Theme.SPACING_MD,
        )

    def _build_storage_settings(self):
        return ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Column(
                            controls=[
                                ft.Text("Workflows Location", size=14, weight=ft.FontWeight.W_500),
                                ft.Text(
                                    "~/skynette/workflows",
                                    size=12,
                                    color=Theme.TEXT_SECONDARY,
                                ),
                            ],
                            expand=True,
                            spacing=2,
                        ),
                        ft.Button("Change", bgcolor=Theme.SURFACE),
                    ],
                ),
                ft.Divider(height=1, color=Theme.BORDER),
                ft.Row(
                    controls=[
                        ft.Column(
                            controls=[
                                ft.Text("Models Location", size=14, weight=ft.FontWeight.W_500),
                                ft.Text(
                                    "~/skynette/models",
                                    size=12,
                                    color=Theme.TEXT_SECONDARY,
                                ),
                            ],
                            expand=True,
                            spacing=2,
                        ),
                        ft.Button("Change", bgcolor=Theme.SURFACE),
                    ],
                ),
                ft.Divider(height=1, color=Theme.BORDER),
                ft.Row(
                    controls=[
                        ft.Column(
                            controls=[
                                ft.Text("Auto-save", size=14, weight=ft.FontWeight.W_500),
                                ft.Text(
                                    "Automatically save workflow changes",
                                    size=12,
                                    color=Theme.TEXT_SECONDARY,
                                ),
                            ],
                            expand=True,
                            spacing=2,
                        ),
                        ft.Switch(value=True, active_color=Theme.PRIMARY),
                    ],
                ),
            ],
            spacing=Theme.SPACING_MD,
        )

    def _build_advanced_settings(self):
        return ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Column(
                            controls=[
                                ft.Text("Debug Mode", size=14, weight=ft.FontWeight.W_500),
                                ft.Text(
                                    "Enable verbose logging",
                                    size=12,
                                    color=Theme.TEXT_SECONDARY,
                                ),
                            ],
                            expand=True,
                            spacing=2,
                        ),
                        ft.Switch(value=False, active_color=Theme.PRIMARY),
                    ],
                ),
                ft.Divider(height=1, color=Theme.BORDER),
                ft.Row(
                    controls=[
                        ft.Column(
                            controls=[
                                ft.Text("Execution Timeout", size=14, weight=ft.FontWeight.W_500),
                                ft.Text(
                                    "Maximum time for node execution (seconds)",
                                    size=12,
                                    color=Theme.TEXT_SECONDARY,
                                ),
                            ],
                            expand=True,
                            spacing=2,
                        ),
                        ft.TextField(
                            value="300",
                            width=80,
                            height=40,
                            text_align=ft.TextAlign.CENTER,
                            border_color=Theme.BORDER,
                        ),
                    ],
                ),
                ft.Divider(height=1, color=Theme.BORDER),
                ft.Row(
                    controls=[
                        ft.Column(
                            controls=[
                                ft.Text("Reset Settings", size=14, weight=ft.FontWeight.W_500),
                                ft.Text(
                                    "Restore all settings to defaults",
                                    size=12,
                                    color=Theme.TEXT_SECONDARY,
                                ),
                            ],
                            expand=True,
                            spacing=2,
                        ),
                        ft.Button(
                            "Reset",
                            bgcolor=Theme.ERROR,
                            color=Theme.TEXT_PRIMARY,
                        ),
                    ],
                ),
            ],
            spacing=Theme.SPACING_MD,
        )
