"""
Usage Dashboard View - AI Cost Analytics & Budget Management.
Visualizes AI usage metrics, costs, and budget tracking.
"""

import flet as ft
from datetime import date, datetime, timedelta
from typing import Optional, Dict, Any
from src.ui.theme import Theme
from src.ai.storage import get_ai_storage


class UsageDashboardView(ft.Column):
    """Usage Dashboard for monitoring API usage and costs."""

    def __init__(self, page: ft.Page = None):
        super().__init__()
        self._page = page
        self.expand = True
        self.spacing = Theme.SPACING_MD
        self.ai_storage = get_ai_storage()

        # State
        self.current_time_range = "this_month"
        self.start_date: Optional[date] = None
        self.end_date: Optional[date] = None

    def build(self):
        """Build the usage dashboard layout."""
        return ft.Column(
            controls=[
                self._build_header(),
                ft.Container(
                    content=ft.Text(
                        "Usage Dashboard - Coming Soon",
                        size=16,
                        color=Theme.TEXT_SECONDARY,
                    ),
                    expand=True,
                    alignment=ft.alignment.Alignment(0, 0),
                ),
            ],
            expand=True,
            spacing=Theme.SPACING_MD,
        )

    def _build_header(self):
        """Build dashboard header."""
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.ANALYTICS, size=32, color=Theme.PRIMARY),
                    ft.Column(
                        controls=[
                            ft.Text(
                                "Usage Dashboard",
                                size=24,
                                weight=ft.FontWeight.BOLD,
                                color=Theme.TEXT_PRIMARY,
                            ),
                            ft.Text(
                                "Track AI costs and manage budgets",
                                size=12,
                                color=Theme.TEXT_SECONDARY,
                            ),
                        ],
                        spacing=2,
                    ),
                ],
            ),
            padding=Theme.SPACING_MD,
            border=ft.border.only(bottom=ft.BorderSide(1, Theme.BORDER)),
        )
