"""Runs view - Workflow execution history."""

import flet as ft
from src.ui.theme import Theme


class RunsView(ft.Column):
    """Workflow execution history and logs."""

    def __init__(self):
        super().__init__()
        self.expand = True

    def build(self):
        return ft.Column(
            controls=[
                self._build_header(),
                self._build_filters(),
                self._build_runs_list(),
            ],
            expand=True,
            spacing=Theme.SPACING_MD,
        )

    def _build_header(self):
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(
                        "Execution History",
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        color=Theme.TEXT_PRIMARY,
                    ),
                    ft.Container(expand=True),
                    ft.Button(
                        "Clear History",
                        icon=ft.Icons.DELETE_OUTLINE,
                        bgcolor=Theme.SURFACE,
                        color=Theme.TEXT_PRIMARY,
                    ),
                ],
            ),
        )

    def _build_filters(self):
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Dropdown(
                        hint_text="All Workflows",
                        width=200,
                        height=40,
                        options=[
                            ft.dropdown.Option("all", "All Workflows"),
                            ft.dropdown.Option("1", "Email Notification"),
                            ft.dropdown.Option("2", "Data Sync"),
                            ft.dropdown.Option("3", "AI Content Generator"),
                        ],
                        border_color=Theme.BORDER,
                    ),
                    ft.Dropdown(
                        hint_text="All Statuses",
                        width=150,
                        height=40,
                        options=[
                            ft.dropdown.Option("all", "All Statuses"),
                            ft.dropdown.Option("success", "Success"),
                            ft.dropdown.Option("failed", "Failed"),
                            ft.dropdown.Option("running", "Running"),
                        ],
                        border_color=Theme.BORDER,
                    ),
                    ft.Container(expand=True),
                    ft.IconButton(
                        icon=ft.Icons.REFRESH,
                        tooltip="Refresh",
                        icon_color=Theme.TEXT_SECONDARY,
                    ),
                ],
                spacing=Theme.SPACING_SM,
            ),
        )

    def _build_runs_list(self):
        runs = [
            {
                "id": "run-001",
                "workflow": "Data Sync",
                "status": "success",
                "started": "2 mins ago",
                "duration": "1.2s",
                "nodes": 5,
            },
            {
                "id": "run-002",
                "workflow": "Email Notification",
                "status": "success",
                "started": "15 mins ago",
                "duration": "0.8s",
                "nodes": 3,
            },
            {
                "id": "run-003",
                "workflow": "AI Content Generator",
                "status": "failed",
                "started": "1 hour ago",
                "duration": "5.3s",
                "nodes": 7,
                "error": "API rate limit exceeded",
            },
            {
                "id": "run-004",
                "workflow": "Data Sync",
                "status": "running",
                "started": "Just now",
                "duration": "...",
                "nodes": 5,
            },
            {
                "id": "run-005",
                "workflow": "Email Notification",
                "status": "success",
                "started": "2 hours ago",
                "duration": "0.9s",
                "nodes": 3,
            },
        ]

        return ft.Container(
            content=ft.Column(
                controls=[self._build_run_item(r) for r in runs],
                scroll=ft.ScrollMode.AUTO,
                spacing=Theme.SPACING_SM,
            ),
            expand=True,
        )

    def _build_run_item(self, run):
        status_config = {
            "success": {"icon": ft.Icons.CHECK_CIRCLE, "color": Theme.SUCCESS},
            "failed": {"icon": ft.Icons.ERROR, "color": Theme.ERROR},
            "running": {"icon": ft.Icons.HOURGLASS_EMPTY, "color": Theme.WARNING},
        }
        config = status_config.get(run["status"], status_config["success"])

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(config["icon"], color=config["color"], size=20),
                            ft.Text(
                                run["workflow"],
                                size=14,
                                weight=ft.FontWeight.W_600,
                                color=Theme.TEXT_PRIMARY,
                            ),
                            ft.Container(
                                content=ft.Text(
                                    run["status"].upper(),
                                    size=10,
                                    weight=ft.FontWeight.BOLD,
                                    color=config["color"],
                                ),
                                padding=ft.Padding.symmetric(horizontal=8, vertical=2),
                                border_radius=4,
                                bgcolor=f"{config['color']}20",
                            ),
                            ft.Container(expand=True),
                            ft.Text(
                                run["started"],
                                size=12,
                                color=Theme.TEXT_SECONDARY,
                            ),
                        ],
                        spacing=Theme.SPACING_SM,
                    ),
                    ft.Row(
                        controls=[
                            ft.Text(
                                f"ID: {run['id']}",
                                size=11,
                                color=Theme.TEXT_SECONDARY,
                            ),
                            ft.Text("•", color=Theme.TEXT_SECONDARY, size=11),
                            ft.Text(
                                f"Duration: {run['duration']}",
                                size=11,
                                color=Theme.TEXT_SECONDARY,
                            ),
                            ft.Text("•", color=Theme.TEXT_SECONDARY, size=11),
                            ft.Text(
                                f"{run['nodes']} nodes",
                                size=11,
                                color=Theme.TEXT_SECONDARY,
                            ),
                            ft.Container(expand=True),
                            ft.TextButton(
                                "View Details",
                                style=ft.ButtonStyle(
                                    color=Theme.PRIMARY,
                                ),
                            ),
                        ],
                        spacing=4,
                    ),
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.WARNING, color=Theme.ERROR, size=14),
                                ft.Text(
                                    run.get("error", ""),
                                    size=12,
                                    color=Theme.ERROR,
                                ),
                            ],
                            spacing=8,
                        ),
                        visible=run["status"] == "failed",
                        padding=ft.Padding.only(top=8),
                    ),
                ],
                spacing=4,
            ),
            bgcolor=Theme.SURFACE,
            padding=Theme.SPACING_MD,
            border_radius=Theme.RADIUS_MD,
            border=ft.Border.all(1, Theme.BORDER),
            on_click=lambda e, r=run: self._view_run_details(r),
            ink=True,
        )

    def _view_run_details(self, run):
        print(f"Viewing run: {run['id']}")
