"""
Usage Dashboard View - AI Cost Analytics & Budget Management.
Visualizes AI usage metrics, costs, and budget tracking.
"""

import asyncio
import flet as ft
from datetime import date, datetime, timedelta
from typing import Optional, Dict, Any, Tuple
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

    def _calculate_time_range(self, range_type: str) -> Tuple[date, date]:
        """Calculate start and end dates for time range."""
        today = date.today()

        if range_type == "last_7d":
            return today - timedelta(days=7), today
        elif range_type == "last_30d":
            return today - timedelta(days=30), today
        elif range_type == "this_month":
            return date(today.year, today.month, 1), today
        elif range_type == "last_month":
            # First day of last month
            first_this_month = date(today.year, today.month, 1)
            last_month_end = first_this_month - timedelta(days=1)
            last_month_start = date(last_month_end.year, last_month_end.month, 1)
            return last_month_start, last_month_end
        else:
            # Default to this month
            return date(today.year, today.month, 1), today

    async def _fetch_usage_data(self) -> Dict[str, Any]:
        """Fetch usage statistics for current time range."""
        try:
            stats = await self.ai_storage.get_usage_stats(self.start_date, self.end_date)
            return stats
        except Exception as e:
            print(f"Error fetching usage data: {e}")
            return {
                "total_calls": 0,
                "total_tokens": 0,
                "total_cost": 0.0,
                "avg_latency": 0.0,
            }

    async def _fetch_budget_data(self):
        """Fetch budget settings."""
        try:
            budget = await self.ai_storage.get_budget_settings()
            return budget
        except Exception as e:
            print(f"Error fetching budget data: {e}")
            return None

    async def _fetch_provider_breakdown(self) -> Dict[str, float]:
        """Fetch provider cost breakdown for current time range."""
        try:
            # Get month and year from end_date (current period)
            month = self.end_date.month
            year = self.end_date.year
            provider_costs = await self.ai_storage.get_cost_by_provider(month, year)
            return provider_costs
        except Exception as e:
            print(f"Error fetching provider breakdown: {e}")
            return {}

    async def _load_dashboard_data(self):
        """Load all dashboard data asynchronously."""
        # Fetch data in parallel using asyncio.gather
        usage_stats, budget_settings, provider_breakdown = await asyncio.gather(
            self._fetch_usage_data(),
            self._fetch_budget_data(),
            self._fetch_provider_breakdown()
        )

        # Update UI with fetched data
        self._update_metrics_with_data(usage_stats, budget_settings, provider_breakdown)

    def _update_metrics_with_data(self, usage_stats: Dict[str, Any], budget_settings, provider_breakdown: Dict[str, float] = None):
        """Update metrics cards with fetched data."""
        # Store data for rendering
        self.usage_stats = usage_stats
        self.budget_settings = budget_settings
        self.provider_breakdown = provider_breakdown if provider_breakdown else {}

        # Trigger UI update
        if self._page:
            self._page.update()

    def build(self):
        """Build the usage dashboard layout."""
        # Set default time range
        self.start_date, self.end_date = self._calculate_time_range(self.current_time_range)

        # Initialize data
        self.usage_stats = None
        self.budget_settings = None
        self.provider_breakdown = {}

        # Trigger async data loading
        if self._page:
            asyncio.create_task(self._load_dashboard_data())

        return ft.Column(
            controls=[
                self._build_header(),
                ft.Container(
                    content=ft.Column(
                        controls=[
                            self._build_time_range_selector(),
                            self._build_metrics_cards(),
                            self._build_provider_breakdown(),
                        ],
                        scroll=ft.ScrollMode.AUTO,
                    ),
                    expand=True,
                    padding=Theme.SPACING_MD,
                ),
            ],
            expand=True,
            spacing=0,
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
            border=ft.Border.only(bottom=ft.BorderSide(1, Theme.BORDER)),
        )

    def _build_time_range_selector(self) -> ft.Container:
        """Build time range selector buttons."""
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text("Time Range:", size=14, color=Theme.TEXT_SECONDARY, weight=ft.FontWeight.W_500),
                    self._build_time_range_button("Last 7 days", "last_7d"),
                    self._build_time_range_button("Last 30 days", "last_30d"),
                    self._build_time_range_button("This Month", "this_month"),
                    self._build_time_range_button("Last Month", "last_month"),
                ],
                spacing=8,
            ),
            padding=ft.Padding.only(bottom=Theme.SPACING_MD, left=0, right=0, top=0),
        )

    def _build_time_range_button(self, label: str, range_type: str) -> ft.TextButton:
        """Build a time range selection button."""
        is_selected = self.current_time_range == range_type

        return ft.TextButton(
            label,
            on_click=lambda e: self._on_time_range_change(range_type),
            style=ft.ButtonStyle(
                bgcolor=Theme.PRIMARY if is_selected else Theme.SURFACE,
                color=ft.Colors.WHITE if is_selected else Theme.TEXT_PRIMARY,
            ),
        )

    def _on_time_range_change(self, range_type: str):
        """Handle time range selection change."""
        self.current_time_range = range_type
        self.start_date, self.end_date = self._calculate_time_range(range_type)

        # Reload data with new time range
        if self._page:
            asyncio.create_task(self._load_dashboard_data())
            self._page.update()

    def _build_metrics_cards(self) -> ft.Container:
        """Build metrics cards displaying key statistics."""
        # Use real data if available, otherwise show zeros
        if self.usage_stats:
            total_cost = self.usage_stats.get("total_cost", 0.0)
            total_calls = self.usage_stats.get("total_calls", 0)
            total_tokens = self.usage_stats.get("total_tokens", 0)
        else:
            total_cost = 0.0
            total_calls = 0
            total_tokens = 0

        # Calculate budget percentage
        budget_percentage = 0.0
        if self.budget_settings and self.budget_settings.monthly_limit_usd > 0:
            budget_percentage = total_cost / self.budget_settings.monthly_limit_usd

        return ft.Container(
            content=ft.Row(
                controls=[
                    self._build_metric_card(
                        "Total Cost",
                        f"${total_cost:.2f}",
                        ft.Icons.ATTACH_MONEY,
                        Theme.PRIMARY,
                    ),
                    self._build_metric_card(
                        "API Calls",
                        f"{total_calls:,}",
                        ft.Icons.API,
                        Theme.INFO,
                    ),
                    self._build_metric_card(
                        "Total Tokens",
                        f"{total_tokens:,}",
                        ft.Icons.TOKEN,
                        Theme.SUCCESS,
                    ),
                    self._build_budget_card(budget_percentage),
                ],
                spacing=Theme.SPACING_MD,
                wrap=True,
            ),
            padding=ft.Padding.only(bottom=Theme.SPACING_MD),
        )

    def _build_metric_card(
        self, label: str, value: str, icon: str, color: str
    ) -> ft.Container:
        """Build a single metric card."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(icon, size=20, color=color),
                            ft.Text(label, size=12, color=Theme.TEXT_SECONDARY),
                        ],
                        spacing=8,
                    ),
                    ft.Text(
                        value,
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        color=Theme.TEXT_PRIMARY,
                    ),
                ],
                spacing=8,
            ),
            padding=16,
            bgcolor=Theme.SURFACE,
            border_radius=Theme.RADIUS_MD,
            border=ft.Border.all(1, Theme.BORDER),
            width=200,
        )

    def _build_budget_card(self, percentage: float) -> ft.Container:
        """Build budget usage card with progress bar."""
        # Determine color based on percentage
        if percentage >= 1.0:
            color = Theme.ERROR
        elif percentage >= 0.8:
            color = Theme.WARNING
        else:
            color = Theme.SUCCESS

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.ACCOUNT_BALANCE_WALLET, size=20, color=color),
                            ft.Text("Budget", size=12, color=Theme.TEXT_SECONDARY),
                        ],
                        spacing=8,
                    ),
                    ft.Text(
                        f"{percentage * 100:.0f}%",
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        color=Theme.TEXT_PRIMARY,
                    ),
                    ft.ProgressBar(
                        value=min(percentage, 1.0),
                        color=color,
                        bgcolor=Theme.BG_TERTIARY,
                        height=8,
                    ),
                ],
                spacing=8,
            ),
            padding=16,
            bgcolor=Theme.SURFACE,
            border_radius=Theme.RADIUS_MD,
            border=ft.Border.all(1, Theme.BORDER),
            width=200,
        )

    def _build_provider_breakdown(self) -> ft.Container:
        """Build provider cost breakdown chart."""
        # Provider color scheme
        provider_colors = {
            "openai": "#10a37f",
            "anthropic": "#d4a574",
            "local": "#6b7280",
            "groq": "#f55036",
            "google": "#4285f4",
        }

        # Get provider data
        provider_data = self.provider_breakdown if hasattr(self, 'provider_breakdown') else {}

        # Calculate total cost
        total_cost = sum(provider_data.values()) if provider_data else 0.0

        # Build provider bars or empty state
        if total_cost > 0:
            # Sort providers by cost (descending)
            sorted_providers = sorted(provider_data.items(), key=lambda x: x[1], reverse=True)

            provider_bars = [
                self._build_provider_bar(
                    provider_name=provider_name,
                    cost=cost,
                    total=total_cost,
                    color=provider_colors.get(provider_name.lower(), "#6b7280")
                )
                for provider_name, cost in sorted_providers
            ]
        else:
            # Empty state
            provider_bars = [
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.PIE_CHART_OUTLINE, size=48, color=Theme.TEXT_MUTED),
                            ft.Text(
                                "No provider usage data",
                                size=14,
                                color=Theme.TEXT_SECONDARY,
                            ),
                            ft.Text(
                                "Start using AI nodes to see provider breakdown",
                                size=12,
                                color=Theme.TEXT_MUTED,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    padding=32,
                )
            ]

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Cost by Provider",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=Theme.TEXT_PRIMARY,
                    ),
                    ft.Container(
                        content=ft.Column(
                            controls=provider_bars,
                            spacing=8,
                        ),
                        padding=Theme.SPACING_MD,
                        bgcolor=Theme.SURFACE,
                        border_radius=Theme.RADIUS_MD,
                        border=ft.Border.all(1, Theme.BORDER),
                    ),
                ],
                spacing=Theme.SPACING_SM,
            ),
            padding=ft.Padding.only(bottom=Theme.SPACING_MD),
        )

    def _build_provider_bar(self, provider_name: str, cost: float, total: float, color: str) -> ft.Container:
        """Build a single provider bar chart element."""
        percentage = (cost / total) * 100 if total > 0 else 0
        bar_width = (cost / total) * 400 if total > 0 else 0  # Max width 400px

        # Provider icon mapping
        provider_icons = {
            "openai": ft.Icons.SMART_TOY,
            "anthropic": ft.Icons.PSYCHOLOGY,
            "local": ft.Icons.COMPUTER,
            "groq": ft.Icons.FLASH_ON,
            "google": ft.Icons.CLOUD,
        }

        icon = provider_icons.get(provider_name.lower(), ft.Icons.HELP_OUTLINE)

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(icon, size=16, color=color),
                    ft.Text(
                        provider_name.capitalize(),
                        width=100,
                        size=12,
                        color=Theme.TEXT_PRIMARY,
                    ),
                    ft.Container(
                        width=bar_width,
                        height=24,
                        bgcolor=color,
                        border_radius=4,
                    ),
                    ft.Text(
                        f"${cost:.2f} ({percentage:.0f}%)",
                        size=12,
                        color=Theme.TEXT_SECONDARY,
                    ),
                ],
                spacing=8,
            ),
            padding=ft.Padding.symmetric(vertical=4),
        )
