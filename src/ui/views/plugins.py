"""Plugins view - Plugin marketplace and management."""

import flet as ft
from src.ui.theme import Theme


class PluginsView(ft.Column):
    """Plugin marketplace and management interface."""

    def __init__(self):
        super().__init__()
        self.expand = True

    def build(self):
        return ft.Column(
            controls=[
                self._build_header(),
                ft.Tabs(
                    tabs=[
                        ft.Tab(
                            text="Installed",
                            content=self._build_installed_tab(),
                        ),
                        ft.Tab(
                            text="Marketplace",
                            content=self._build_marketplace_tab(),
                        ),
                        ft.Tab(
                            text="Develop",
                            content=self._build_develop_tab(),
                        ),
                    ],
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
                        "Plugins",
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        color=Theme.TEXT_PRIMARY,
                    ),
                    ft.Container(expand=True),
                    ft.TextField(
                        hint_text="Search plugins...",
                        prefix_icon=ft.Icons.SEARCH,
                        width=250,
                        height=40,
                        border_color=Theme.BORDER,
                    ),
                ],
            ),
        )

    def _build_installed_tab(self):
        plugins = [
            {
                "name": "Slack Integration",
                "author": "Skynette Team",
                "version": "1.2.0",
                "enabled": True,
                "description": "Send messages and receive webhooks from Slack",
            },
            {
                "name": "Google Sheets",
                "author": "Community",
                "version": "0.9.1",
                "enabled": True,
                "description": "Read and write Google Sheets data",
            },
            {
                "name": "PDF Generator",
                "author": "Skynette Team",
                "version": "1.0.0",
                "enabled": False,
                "description": "Generate PDF documents from templates",
            },
        ]

        return ft.Container(
            content=ft.Column(
                controls=[
                    self._build_plugin_card(p, installed=True) for p in plugins
                ],
                scroll=ft.ScrollMode.AUTO,
                spacing=Theme.SPACING_SM,
            ),
            padding=Theme.SPACING_MD,
            expand=True,
        )

    def _build_marketplace_tab(self):
        categories = ["All", "Communication", "Data", "AI", "Productivity", "Developer"]

        featured = [
            {
                "name": "Discord Bot",
                "author": "Community",
                "downloads": "12.5k",
                "rating": 4.8,
                "description": "Full Discord bot integration with slash commands",
            },
            {
                "name": "Notion Sync",
                "author": "Skynette Team",
                "downloads": "8.2k",
                "rating": 4.9,
                "description": "Two-way sync with Notion databases",
            },
            {
                "name": "AWS S3 Storage",
                "author": "Community",
                "downloads": "6.7k",
                "rating": 4.7,
                "description": "Upload and manage files in S3 buckets",
            },
            {
                "name": "Stripe Payments",
                "author": "Skynette Team",
                "downloads": "5.3k",
                "rating": 4.6,
                "description": "Process payments and manage subscriptions",
            },
        ]

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Text(cat, size=12),
                                bgcolor=Theme.SURFACE if i > 0 else Theme.PRIMARY,
                                padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                                border_radius=16,
                                on_click=lambda e, c=cat: self._filter_category(c),
                            )
                            for i, cat in enumerate(categories)
                        ],
                        spacing=8,
                    ),
                    ft.Container(height=Theme.SPACING_MD),
                    ft.Text("Featured Plugins", size=16, weight=ft.FontWeight.W_600),
                    ft.GridView(
                        controls=[
                            self._build_plugin_card(p, installed=False) for p in featured
                        ],
                        runs_count=2,
                        max_extent=400,
                        spacing=Theme.SPACING_MD,
                        run_spacing=Theme.SPACING_MD,
                        expand=True,
                    ),
                ],
                scroll=ft.ScrollMode.AUTO,
                spacing=Theme.SPACING_SM,
            ),
            padding=Theme.SPACING_MD,
            expand=True,
        )

    def _build_develop_tab(self):
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Icon(ft.Icons.CODE, size=48, color=Theme.PRIMARY),
                                ft.Text(
                                    "Create Your Own Plugin",
                                    size=18,
                                    weight=ft.FontWeight.W_600,
                                ),
                                ft.Text(
                                    "Build custom nodes and integrations using Python",
                                    size=14,
                                    color=Theme.TEXT_SECONDARY,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                                ft.Container(height=Theme.SPACING_MD),
                                ft.Button(
                                    "Create New Plugin",
                                    icon=ft.Icons.ADD,
                                    bgcolor=Theme.PRIMARY,
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=Theme.SPACING_SM,
                        ),
                        bgcolor=Theme.SURFACE,
                        padding=Theme.SPACING_XL,
                        border_radius=Theme.RADIUS_MD,
                        border=ft.Border.all(2, Theme.BORDER),
                        alignment=ft.alignment.Alignment(0, 0),
                    ),
                    ft.Container(height=Theme.SPACING_LG),
                    ft.Text("Documentation", size=16, weight=ft.FontWeight.W_600),
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.BOOK, color=Theme.PRIMARY),
                        title=ft.Text("Plugin SDK Guide"),
                        subtitle=ft.Text("Learn how to create plugins"),
                        trailing=ft.Icon(ft.Icons.CHEVRON_RIGHT),
                    ),
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.CODE, color=Theme.PRIMARY),
                        title=ft.Text("API Reference"),
                        subtitle=ft.Text("Complete API documentation"),
                        trailing=ft.Icon(ft.Icons.CHEVRON_RIGHT),
                    ),
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.LIGHTBULB, color=Theme.PRIMARY),
                        title=ft.Text("Example Plugins"),
                        subtitle=ft.Text("Sample code and templates"),
                        trailing=ft.Icon(ft.Icons.CHEVRON_RIGHT),
                    ),
                ],
                scroll=ft.ScrollMode.AUTO,
                spacing=Theme.SPACING_SM,
            ),
            padding=Theme.SPACING_MD,
            expand=True,
        )

    def _build_plugin_card(self, plugin, installed=False):
        if installed:
            return ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.EXTENSION, color=Theme.PRIMARY, size=32),
                        ft.Column(
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Text(
                                            plugin["name"],
                                            size=14,
                                            weight=ft.FontWeight.W_600,
                                        ),
                                        ft.Text(
                                            f"v{plugin['version']}",
                                            size=11,
                                            color=Theme.TEXT_SECONDARY,
                                        ),
                                    ],
                                    spacing=8,
                                ),
                                ft.Text(
                                    plugin["description"],
                                    size=12,
                                    color=Theme.TEXT_SECONDARY,
                                ),
                            ],
                            spacing=4,
                            expand=True,
                        ),
                        ft.Switch(
                            value=plugin["enabled"],
                            active_color=Theme.PRIMARY,
                        ),
                    ],
                    spacing=Theme.SPACING_MD,
                ),
                bgcolor=Theme.SURFACE,
                padding=Theme.SPACING_MD,
                border_radius=Theme.RADIUS_MD,
                border=ft.Border.all(1, Theme.BORDER),
            )
        else:
            return ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.EXTENSION, color=Theme.PRIMARY),
                                ft.Text(
                                    plugin["name"],
                                    size=14,
                                    weight=ft.FontWeight.W_600,
                                    expand=True,
                                ),
                                ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.STAR, size=14, color=Theme.WARNING),
                                        ft.Text(str(plugin["rating"]), size=12),
                                    ],
                                    spacing=4,
                                ),
                            ],
                        ),
                        ft.Text(
                            plugin["description"],
                            size=12,
                            color=Theme.TEXT_SECONDARY,
                            max_lines=2,
                        ),
                        ft.Row(
                            controls=[
                                ft.Text(
                                    f"by {plugin['author']}",
                                    size=11,
                                    color=Theme.TEXT_SECONDARY,
                                ),
                                ft.Container(expand=True),
                                ft.Text(
                                    f"{plugin['downloads']} downloads",
                                    size=11,
                                    color=Theme.TEXT_SECONDARY,
                                ),
                            ],
                        ),
                        ft.Button(
                            "Install",
                            bgcolor=Theme.PRIMARY,
                            expand=True,
                        ),
                    ],
                    spacing=Theme.SPACING_SM,
                ),
                bgcolor=Theme.SURFACE,
                padding=Theme.SPACING_MD,
                border_radius=Theme.RADIUS_MD,
                border=ft.Border.all(1, Theme.BORDER),
            )

    def _filter_category(self, category):
        print(f"Filtering by: {category}")
