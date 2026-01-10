"""Workflows list view - Dashboard showing all workflows."""

import flet as ft
from src.ui.theme import Theme


class WorkflowsView(ft.Column):
    """Main workflows dashboard showing all workflows."""

    def __init__(self, on_workflow_select=None, on_create_new=None):
        super().__init__()
        self.on_workflow_select = on_workflow_select
        self.on_create_new = on_create_new
        self.workflows = []  # Will be loaded from storage
        self.expand = True

    def build(self):
        return ft.Column(
            controls=[
                self._build_header(),
                self._build_toolbar(),
                self._build_workflow_grid(),
            ],
            expand=True,
            spacing=Theme.SPACING_MD,
        )

    def _build_header(self):
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(
                        "Workflows",
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        color=Theme.TEXT_PRIMARY,
                    ),
                    ft.Container(expand=True),
                    ft.Button(
                        "New Workflow",
                        icon=ft.Icons.ADD,
                        bgcolor=Theme.PRIMARY,
                        color=Theme.TEXT_PRIMARY,
                        on_click=self._on_create_click,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.Padding.only(bottom=Theme.SPACING_SM),
        )

    def _build_toolbar(self):
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.TextField(
                        hint_text="Search workflows...",
                        prefix_icon=ft.Icons.SEARCH,
                        width=300,
                        height=40,
                        border_color=Theme.BORDER,
                        focused_border_color=Theme.PRIMARY,
                        text_size=14,
                        on_change=self._on_search,
                    ),
                    ft.Container(width=Theme.SPACING_MD),
                    ft.Dropdown(
                        hint_text="Filter by status",
                        width=150,
                        height=40,
                        options=[
                            ft.dropdown.Option("all", "All"),
                            ft.dropdown.Option("active", "Active"),
                            ft.dropdown.Option("inactive", "Inactive"),
                            ft.dropdown.Option("error", "Has Errors"),
                        ],
                        border_color=Theme.BORDER,
                    ),
                    ft.Container(expand=True),
                    ft.IconButton(
                        icon=ft.Icons.GRID_VIEW,
                        tooltip="Grid view",
                        icon_color=Theme.PRIMARY,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.LIST,
                        tooltip="List view",
                        icon_color=Theme.TEXT_SECONDARY,
                    ),
                ],
            ),
            padding=ft.Padding.only(bottom=Theme.SPACING_MD),
        )

    def _build_workflow_grid(self):
        # Sample workflows for UI demonstration
        sample_workflows = [
            {
                "id": "1",
                "name": "Email Notification",
                "description": "Send email when new order arrives",
                "status": "active",
                "last_run": "2 hours ago",
                "runs": 156,
            },
            {
                "id": "2",
                "name": "Data Sync",
                "description": "Sync data between CRM and database",
                "status": "active",
                "last_run": "5 mins ago",
                "runs": 1024,
            },
            {
                "id": "3",
                "name": "AI Content Generator",
                "description": "Generate blog posts using AI",
                "status": "inactive",
                "last_run": "3 days ago",
                "runs": 42,
            },
        ]

        cards = [self._build_workflow_card(w) for w in sample_workflows]
        cards.append(self._build_new_workflow_card())

        return ft.Container(
            content=ft.GridView(
                controls=cards,
                runs_count=3,
                max_extent=350,
                spacing=Theme.SPACING_MD,
                run_spacing=Theme.SPACING_MD,
                expand=True,
            ),
            expand=True,
        )

    def _build_workflow_card(self, workflow):
        status_color = Theme.SUCCESS if workflow["status"] == "active" else Theme.TEXT_SECONDARY

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(
                                ft.Icons.ACCOUNT_TREE,
                                color=Theme.PRIMARY,
                                size=24,
                            ),
                            ft.Container(expand=True),
                            ft.Container(
                                content=ft.Text(
                                    workflow["status"].upper(),
                                    size=10,
                                    weight=ft.FontWeight.BOLD,
                                    color=status_color,
                                ),
                                padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                                border_radius=4,
                                bgcolor=f"{status_color}20",
                            ),
                        ],
                    ),
                    ft.Text(
                        workflow["name"],
                        size=16,
                        weight=ft.FontWeight.W_600,
                        color=Theme.TEXT_PRIMARY,
                    ),
                    ft.Text(
                        workflow["description"],
                        size=12,
                        color=Theme.TEXT_SECONDARY,
                        max_lines=2,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    ft.Container(expand=True),
                    ft.Divider(height=1, color=Theme.BORDER),
                    ft.Row(
                        controls=[
                            ft.Text(
                                f"Last run: {workflow['last_run']}",
                                size=11,
                                color=Theme.TEXT_SECONDARY,
                            ),
                            ft.Container(expand=True),
                            ft.Text(
                                f"{workflow['runs']} runs",
                                size=11,
                                color=Theme.TEXT_SECONDARY,
                            ),
                        ],
                    ),
                ],
                spacing=Theme.SPACING_SM,
            ),
            padding=Theme.SPACING_MD,
            bgcolor=Theme.SURFACE,
            border_radius=Theme.RADIUS_MD,
            border=ft.Border.all(1, Theme.BORDER),
            on_click=lambda e, w=workflow: self._on_workflow_click(w),
            on_hover=self._on_card_hover,
            ink=True,
        )

    def _build_new_workflow_card(self):
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(
                        ft.Icons.ADD_CIRCLE_OUTLINE,
                        color=Theme.TEXT_SECONDARY,
                        size=48,
                    ),
                    ft.Text(
                        "Create New Workflow",
                        size=14,
                        color=Theme.TEXT_SECONDARY,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=Theme.SPACING_SM,
            ),
            padding=Theme.SPACING_MD,
            bgcolor=Theme.SURFACE,
            border_radius=Theme.RADIUS_MD,
            border=ft.Border.all(2, Theme.BORDER),
            on_click=self._on_create_click,
            on_hover=self._on_card_hover,
            ink=True,
        )

    def _on_search(self, e):
        # Filter workflows based on search text
        pass

    def _on_workflow_click(self, workflow):
        if self.on_workflow_select:
            self.on_workflow_select(workflow)

    def _on_create_click(self, e):
        if self.on_create_new:
            self.on_create_new()

    def _on_card_hover(self, e):
        if e.data == "true":
            e.control.border = ft.Border.all(1, Theme.PRIMARY)
        else:
            e.control.border = ft.Border.all(1, Theme.BORDER)
        e.control.update()
