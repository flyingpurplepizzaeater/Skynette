"""
Usage Dashboard View - AI Cost Analytics & Budget Management.
Visualizes AI usage metrics, costs, and budget tracking.
"""

import asyncio
import csv
import flet as ft
from datetime import date, datetime, timedelta
from io import StringIO
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
        """Fetch cost breakdown by provider for current time range."""
        try:
            # For monthly ranges, use get_cost_by_provider
            if self.current_time_range in ["this_month", "last_month"]:
                month = self.start_date.month
                year = self.start_date.year
                return await self.ai_storage.get_cost_by_provider(month, year)
            else:
                # For custom ranges, aggregate from usage stats
                # For now, return empty dict (will enhance later if needed)
                return {}
        except Exception as e:
            print(f"Error fetching provider breakdown: {e}")
            return {}

    async def _fetch_workflow_breakdown(self) -> Dict[str, float]:
        """Fetch cost breakdown by workflow for current time range."""
        try:
            # For monthly ranges, use get_cost_by_workflow
            if self.current_time_range in ["this_month", "last_month"]:
                month = self.start_date.month
                year = self.start_date.year
                return await self.ai_storage.get_cost_by_workflow(month, year)
            else:
                # For custom ranges, aggregate from usage stats
                # For now, return empty dict (will enhance later if needed)
                return {}
        except Exception as e:
            print(f"Error fetching workflow breakdown: {e}")
            return {}

    async def _load_dashboard_data(self):
        """Load all dashboard data asynchronously."""
        # Fetch data in parallel
        usage_task = self._fetch_usage_data()
        budget_task = self._fetch_budget_data()
        provider_task = self._fetch_provider_breakdown()
        workflow_task = self._fetch_workflow_breakdown()

        usage_stats = await usage_task
        budget_settings = await budget_task
        provider_costs = await provider_task
        workflow_costs = await workflow_task

        # Update UI with fetched data
        self._update_metrics_with_data(usage_stats, budget_settings)
        self.provider_costs = provider_costs
        self.workflow_costs = workflow_costs

        if self._page:
            self._page.update()

    def _update_metrics_with_data(self, usage_stats: Dict[str, Any], budget_settings):
        """Update metrics cards with fetched data."""
        # Store data for rendering
        self.usage_stats = usage_stats
        self.budget_settings = budget_settings

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
                            self._build_workflow_breakdown(),
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
        """Build provider cost breakdown visualization."""
        provider_costs = getattr(self, 'provider_costs', {})

        if not provider_costs or sum(provider_costs.values()) == 0:
            # Empty state
            return ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.PIE_CHART, size=16, color=Theme.TEXT_SECONDARY),
                                ft.Text("Cost by Provider", weight=ft.FontWeight.BOLD, size=16),
                            ],
                            spacing=8,
                        ),
                        ft.Container(
                            content=ft.Text(
                                "No provider usage data for this time range",
                                size=14,
                                color=Theme.TEXT_SECONDARY,
                                italic=True,
                            ),
                            alignment=ft.alignment.center,
                            padding=40,
                        ),
                    ],
                    spacing=Theme.SPACING_SM,
                ),
                padding=16,
                bgcolor=Theme.SURFACE,
                border_radius=Theme.RADIUS_MD,
                border=ft.Border.all(1, Theme.BORDER),
            )

        # Calculate total for percentages
        total_cost = sum(provider_costs.values())

        # Provider colors mapping
        provider_colors = {
            "openai": "#10a37f",
            "anthropic": "#d4a574",
            "local": "#6b7280",
            "groq": "#f55036",
            "google": "#4285f4",
        }

        # Build bars for each provider
        provider_bars = []
        for provider_id, cost in sorted(provider_costs.items(), key=lambda x: x[1], reverse=True):
            percentage = (cost / total_cost) * 100
            color = provider_colors.get(provider_id.lower(), Theme.INFO)

            provider_bars.append(
                self._build_provider_bar(provider_id, cost, total_cost, color)
            )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.PIE_CHART, size=16, color=Theme.PRIMARY),
                            ft.Text("Cost by Provider", weight=ft.FontWeight.BOLD, size=16),
                        ],
                        spacing=8,
                    ),
                    ft.Column(
                        controls=provider_bars,
                        spacing=8,
                    ),
                ],
                spacing=Theme.SPACING_SM,
            ),
            padding=16,
            bgcolor=Theme.SURFACE,
            border_radius=Theme.RADIUS_MD,
            border=ft.Border.all(1, Theme.BORDER),
        )

    def _build_provider_bar(
        self, provider_name: str, cost: float, total_cost: float, color: str
    ) -> ft.Container:
        """Build a single provider bar in the breakdown."""
        percentage = (cost / total_cost) * 100
        bar_width = (cost / total_cost) * 400  # Max width 400px

        # Capitalize provider name
        display_name = provider_name.capitalize()

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Text(display_name, size=13, weight=ft.FontWeight.W_500),
                        width=100,
                    ),
                    ft.Container(
                        width=max(bar_width, 20),  # Minimum 20px even for tiny values
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
                spacing=12,
                alignment=ft.MainAxisAlignment.START,
            ),
            padding=ft.Padding.symmetric(vertical=4),
        )

    def _build_workflow_breakdown(self) -> ft.Container:
        """Build workflow cost breakdown visualization."""
        workflow_costs = getattr(self, 'workflow_costs', {})

        if not workflow_costs or sum(workflow_costs.values()) == 0:
            # Empty state
            return ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.TABLE_CHART, size=16, color=Theme.TEXT_SECONDARY),
                                ft.Text("Top Workflows by Cost", weight=ft.FontWeight.BOLD, size=16),
                            ],
                            spacing=8,
                        ),
                        ft.Container(
                            content=ft.Text(
                                "No workflow usage data for this time range",
                                size=14,
                                color=Theme.TEXT_SECONDARY,
                                italic=True,
                            ),
                            alignment=ft.alignment.center,
                            padding=40,
                        ),
                    ],
                    spacing=Theme.SPACING_SM,
                ),
                padding=16,
                bgcolor=Theme.SURFACE,
                border_radius=Theme.RADIUS_MD,
                border=ft.Border.all(1, Theme.BORDER),
            )

        # Calculate total for percentages
        total_cost = sum(workflow_costs.values())

        # Build bars for each workflow
        workflow_bars = []
        for workflow_id, cost in sorted(workflow_costs.items(), key=lambda x: x[1], reverse=True):
            percentage = (cost / total_cost) * 100

            workflow_bars.append(
                self._build_workflow_bar(workflow_id, cost, total_cost)
            )

        # Header row with export button
        header_row = ft.Row(
            controls=[
                ft.Icon(ft.Icons.TABLE_CHART, size=16, color=Theme.PRIMARY),
                ft.Text("Top Workflows by Cost", weight=ft.FontWeight.BOLD, size=16),
                ft.Container(expand=True),  # Spacer
                ft.IconButton(
                    icon=ft.Icons.DOWNLOAD,
                    tooltip="Export CSV",
                    on_click=lambda e: asyncio.create_task(self._export_csv()),
                    icon_size=20,
                ),
            ],
            spacing=8,
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    header_row,
                    ft.Column(
                        controls=workflow_bars,
                        spacing=8,
                    ),
                ],
                spacing=Theme.SPACING_SM,
            ),
            padding=16,
            bgcolor=Theme.SURFACE,
            border_radius=Theme.RADIUS_MD,
            border=ft.Border.all(1, Theme.BORDER),
        )

    def _build_workflow_bar(
        self, workflow_name: str, cost: float, total_cost: float
    ) -> ft.Container:
        """Build a single workflow bar in the breakdown."""
        percentage = (cost / total_cost) * 100
        bar_width = (cost / total_cost) * 400  # Max width 400px

        # Use workflow name as-is
        display_name = workflow_name

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Text(display_name, size=13, weight=ft.FontWeight.W_500),
                        width=150,
                    ),
                    ft.Container(
                        width=max(bar_width, 20),  # Minimum 20px even for tiny values
                        height=24,
                        bgcolor=Theme.INFO,
                        border_radius=4,
                    ),
                    ft.Text(
                        f"${cost:.2f} ({percentage:.0f}%)",
                        size=12,
                        color=Theme.TEXT_SECONDARY,
                    ),
                ],
                spacing=12,
                alignment=ft.MainAxisAlignment.START,
            ),
            padding=ft.Padding.symmetric(vertical=4),
        )

    async def _build_csv_content(self) -> str:
        """Build CSV content from usage data."""
        # CSV Header
        header = [
            "Date Range",
            "Provider",
            "Workflow",
            "Cost (USD)",
            "Calls",
            "Tokens",
        ]

        rows = []
        rows.append(header)

        # Date range string
        date_range = f"{self.start_date} to {self.end_date}"

        # Add provider costs (sorted by cost descending)
        provider_costs = getattr(self, 'provider_costs', {})
        for provider, cost in sorted(provider_costs.items(), key=lambda x: x[1], reverse=True):
            rows.append([
                date_range,
                provider,
                "All Workflows",
                f"{cost:.2f}",
                "-",
                "-",
            ])

        # Add workflow costs (sorted by cost descending)
        workflow_costs = getattr(self, 'workflow_costs', {})
        for workflow, cost in sorted(workflow_costs.items(), key=lambda x: x[1], reverse=True):
            rows.append([
                date_range,
                "All Providers",
                workflow,
                f"{cost:.2f}",
                "-",
                "-",
            ])

        # Convert to CSV string
        output = StringIO()
        writer = csv.writer(output)
        writer.writerows(rows)
        return output.getvalue()

    def _on_csv_save_result(self, e: ft.FilePickerResultEvent, csv_content: str):
        """Handle CSV file save result."""
        if e.path:
            try:
                # Write CSV to selected file
                with open(e.path, 'w', newline='', encoding='utf-8') as f:
                    f.write(csv_content)

                # Show success snackbar
                if self._page:
                    snackbar = ft.SnackBar(
                        ft.Text(f"Exported to {e.path}"),
                        bgcolor=Theme.SUCCESS,
                    )
                    self._page.overlay.append(snackbar)
                    snackbar.open = True
                    self._page.update()

            except Exception as ex:
                print(f"Error writing CSV file: {ex}")
                if self._page:
                    snackbar = ft.SnackBar(ft.Text(f"Save failed: {str(ex)}"), bgcolor=Theme.ERROR)
                    self._page.overlay.append(snackbar)
                    snackbar.open = True
                    self._page.update()

    async def _export_csv(self):
        """Export usage data to CSV file."""
        try:
            # For MVP, export current time range data
            # Future enhancement: Add dialog to select custom range

            # Build CSV content
            csv_content = await self._build_csv_content()

            # Generate filename
            filename = f"skynette-ai-usage-{self.start_date}-to-{self.end_date}.csv"

            # Use Flet's file picker to save
            if self._page:
                file_picker = ft.FilePicker(on_result=lambda e: self._on_csv_save_result(e, csv_content))
                self._page.overlay.append(file_picker)
                self._page.update()

                # Open save dialog
                file_picker.save_file(
                    dialog_title="Export Usage Data",
                    file_name=filename,
                    allowed_extensions=["csv"],
                )

        except Exception as e:
            print(f"Error exporting CSV: {e}")
            if self._page:
                # Show error snackbar
                snackbar = ft.SnackBar(ft.Text(f"Export failed: {str(e)}"), bgcolor=Theme.ERROR)
                self._page.overlay.append(snackbar)
                snackbar.open = True
                self._page.update()
