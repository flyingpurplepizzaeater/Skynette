"""Workflow editor view - Visual node canvas editor."""

import flet as ft

from src.core.workflow.models import Workflow
from src.ui.theme import Theme
from src.ui.views.simple_mode import SimpleModeView


class WorkflowEditorView(ft.Column):
    """Visual workflow editor with node canvas."""

    def __init__(self, workflow: Workflow = None, on_save=None, on_back=None, page=None):
        super().__init__()
        self.workflow = workflow or Workflow(name="Untitled Workflow")
        self.on_save = on_save
        self.on_back = on_back
        self.page = page
        self.expand = True
        self.simple_mode = True  # Start in simple mode by default
        self._content_area = None
        self._simple_view = None

    def build(self):
        # Content area switches between simple and advanced
        self._content_area = ft.Container(
            content=self._build_simple_content()
            if self.simple_mode
            else self._build_advanced_content(),
            expand=True,
        )

        return ft.Column(
            controls=[
                self._build_toolbar(),
                self._content_area,
            ],
            expand=True,
            spacing=0,
        )

    def _build_simple_content(self):
        """Build the simple mode step builder."""
        self._simple_view = SimpleModeView(
            workflow=self.workflow,
            on_save=self.on_save,
            on_change=self._on_workflow_change,
        )
        if self.page:
            self._simple_view.page = self.page
        return self._simple_view

    def _on_workflow_change(self, workflow):
        """Handle workflow changes from simple mode."""
        self.workflow = workflow

    def _build_advanced_content(self):
        """Build the advanced visual canvas editor."""
        return ft.Row(
            controls=[
                self._build_node_palette(),
                self._build_canvas(),
                self._build_properties_panel(),
            ],
            expand=True,
            spacing=0,
        )

    def _build_toolbar(self):
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        tooltip="Back to workflows",
                        icon_color=Theme.TEXT_SECONDARY,
                        on_click=lambda e: self.on_back() if self.on_back else None,
                    ),
                    ft.TextField(
                        value=self.workflow.name if self.workflow else "Untitled Workflow",
                        border=ft.InputBorder.NONE,
                        text_size=18,
                        weight=ft.FontWeight.W_600,
                        width=300,
                    ),
                    ft.Container(expand=True),
                    # Mode toggle
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.TextButton(
                                    "Simple",
                                    style=ft.ButtonStyle(
                                        color=Theme.PRIMARY
                                        if self.simple_mode
                                        else Theme.TEXT_SECONDARY,
                                    ),
                                    on_click=lambda e: self._toggle_mode(True),
                                ),
                                ft.TextButton(
                                    "Advanced",
                                    style=ft.ButtonStyle(
                                        color=Theme.PRIMARY
                                        if not self.simple_mode
                                        else Theme.TEXT_SECONDARY,
                                    ),
                                    on_click=lambda e: self._toggle_mode(False),
                                ),
                            ],
                            spacing=0,
                        ),
                        bgcolor=Theme.SURFACE,
                        border_radius=Theme.RADIUS_SM,
                        padding=ft.Padding.symmetric(horizontal=4, vertical=2),
                    ),
                    ft.Container(width=Theme.SPACING_MD),
                    ft.IconButton(
                        icon=ft.Icons.BUG_REPORT,
                        tooltip="Debug mode",
                        icon_color=Theme.TEXT_SECONDARY,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.PLAY_ARROW,
                        tooltip="Execute workflow",
                        icon_color=Theme.SUCCESS,
                    ),
                    ft.Button(
                        "Save",
                        icon=ft.Icons.SAVE,
                        bgcolor=Theme.PRIMARY,
                        color=Theme.TEXT_PRIMARY,
                        on_click=lambda e: self.on_save(self.workflow) if self.on_save else None,
                    ),
                ],
            ),
            bgcolor=Theme.SURFACE,
            padding=ft.Padding.symmetric(horizontal=Theme.SPACING_MD, vertical=Theme.SPACING_SM),
            border=ft.Border.only(bottom=ft.BorderSide(1, Theme.BORDER)),
        )

    def _build_node_palette(self):
        categories = [
            {
                "name": "Triggers",
                "icon": ft.Icons.BOLT,
                "nodes": ["Manual Trigger", "Schedule", "Webhook", "File Watch"],
            },
            {
                "name": "AI",
                "icon": ft.Icons.AUTO_AWESOME,
                "nodes": ["Text Generation", "Image Generation", "Embeddings", "RAG Query"],
            },
            {
                "name": "Data",
                "icon": ft.Icons.STORAGE,
                "nodes": ["Read File", "Write File", "JSON Transform", "Database"],
            },
            {
                "name": "HTTP",
                "icon": ft.Icons.HTTP,
                "nodes": ["HTTP Request", "GraphQL", "WebSocket"],
            },
            {
                "name": "Flow",
                "icon": ft.Icons.CALL_SPLIT,
                "nodes": ["If/Else", "Switch", "Loop", "Merge"],
            },
        ]

        category_items = []
        for cat in categories:
            category_items.append(
                ft.ExpansionTile(
                    title=ft.Text(cat["name"], size=13, weight=ft.FontWeight.W_500),
                    leading=ft.Icon(cat["icon"], size=18, color=Theme.PRIMARY),
                    expanded=cat["name"] == "Triggers",
                    controls=[
                        ft.ListTile(
                            title=ft.Text(node, size=12),
                            dense=True,
                            on_click=lambda e, n=node: self._add_node(n),
                        )
                        for node in cat["nodes"]
                    ],
                    tile_padding=ft.Padding.symmetric(horizontal=8),
                )
            )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=ft.TextField(
                            hint_text="Search nodes...",
                            prefix_icon=ft.Icons.SEARCH,
                            height=36,
                            text_size=12,
                            border_color=Theme.BORDER,
                        ),
                        padding=Theme.SPACING_SM,
                    ),
                    ft.Column(
                        controls=category_items,
                        scroll=ft.ScrollMode.AUTO,
                        expand=True,
                    ),
                ],
                expand=True,
            ),
            width=220,
            bgcolor=Theme.SURFACE,
            border=ft.Border.only(right=ft.BorderSide(1, Theme.BORDER)),
        )

    def _build_canvas(self):
        # Placeholder canvas - will be replaced with actual node canvas
        return ft.Container(
            content=ft.Stack(
                controls=[
                    # Grid background
                    ft.Container(
                        bgcolor=Theme.BACKGROUND,
                        expand=True,
                    ),
                    # Center instruction
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Icon(
                                    ft.Icons.ADD_CIRCLE_OUTLINE,
                                    size=64,
                                    color=Theme.TEXT_SECONDARY,
                                ),
                                ft.Text(
                                    "Drag nodes here or click to add",
                                    size=14,
                                    color=Theme.TEXT_SECONDARY,
                                ),
                                ft.Text(
                                    "Start with a trigger node",
                                    size=12,
                                    color=Theme.TEXT_SECONDARY,
                                    italic=True,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=Theme.SPACING_SM,
                        ),
                        alignment=ft.Alignment.CENTER,
                        expand=True,
                    ),
                    # Sample node for demonstration
                    ft.Container(
                        content=self._build_sample_node(),
                        left=100,
                        top=100,
                    ),
                ],
                expand=True,
            ),
            expand=True,
        )

    def _build_sample_node(self):
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.BOLT, size=16, color=Theme.WARNING),
                            ft.Text("Manual Trigger", size=12, weight=ft.FontWeight.W_500),
                        ],
                        spacing=8,
                    ),
                    ft.Container(
                        content=ft.Text("Click to run", size=10, color=Theme.TEXT_SECONDARY),
                        padding=ft.Padding.only(left=24),
                    ),
                ],
                spacing=4,
            ),
            bgcolor=Theme.SURFACE,
            border_radius=Theme.RADIUS_SM,
            border=ft.Border.all(2, Theme.WARNING),
            padding=Theme.SPACING_SM,
            width=180,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=8,
                color="#00000040",
                offset=ft.Offset(0, 2),
            ),
        )

    def _build_properties_panel(self):
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Text(
                            "Properties",
                            size=14,
                            weight=ft.FontWeight.W_600,
                            color=Theme.TEXT_PRIMARY,
                        ),
                        padding=Theme.SPACING_MD,
                        border=ft.Border.only(bottom=ft.BorderSide(1, Theme.BORDER)),
                    ),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text(
                                    "Select a node to edit its properties",
                                    size=12,
                                    color=Theme.TEXT_SECONDARY,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            expand=True,
                        ),
                        expand=True,
                        padding=Theme.SPACING_MD,
                    ),
                ],
                expand=True,
            ),
            width=280,
            bgcolor=Theme.SURFACE,
            border=ft.Border.only(left=ft.BorderSide(1, Theme.BORDER)),
        )

    def _toggle_mode(self, simple):
        self.simple_mode = simple
        # Switch content
        if self._content_area:
            if simple:
                self._content_area.content = self._build_simple_content()
            else:
                self._content_area.content = self._build_advanced_content()

            if self.page:
                self.page.update()

    def _add_node(self, node_type):
        # Add node to canvas
        print(f"Adding node: {node_type}")
