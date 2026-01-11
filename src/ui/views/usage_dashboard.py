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

        # Budget dialog state
        self.budget_dialog = None
        self.budget_limit_field = None
        self.budget_threshold_slider = None
        self.budget_reset_day_dropdown = None

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
                # For other ranges, return empty dict
                return {}
        except Exception as e:
            print(f"Error fetching workflow breakdown: {e}")
            return {}

    async def _load_dashboard_data(self):
        """Load all dashboard data asynchronously."""
        # Fetch data in parallel using asyncio.gather
        usage_stats, budget_settings, provider_breakdown, workflow_costs = await asyncio.gather(
            self._fetch_usage_data(),
            self._fetch_budget_data(),
            self._fetch_provider_breakdown(),
            self._fetch_workflow_breakdown()
        )

        # Update UI with fetched data
        self._update_metrics_with_data(usage_stats, budget_settings, provider_breakdown, workflow_costs)

        # Check for budget alerts
        self.budget_alert = await self._check_budget_alert()

        if self._page:
            self._page.update()

    def _update_metrics_with_data(self, usage_stats: Dict[str, Any], budget_settings, provider_breakdown: Dict[str, float] = None, workflow_costs: Dict[str, float] = None):
        """Update metrics cards with fetched data."""
        # Store data for rendering
        self.usage_stats = usage_stats
        self.budget_settings = budget_settings
        self.provider_breakdown = provider_breakdown if provider_breakdown else {}
        self.workflow_costs = workflow_costs if workflow_costs else {}

        # Trigger UI update
        if self._page:
            self._page.update()

    async def _check_budget_alert(self):
        """Check if budget alert should be shown."""
        if not self.usage_stats or not self.budget_settings:
            return None

        current_cost = self.usage_stats.get("total_cost", 0.0)
        alert = await self.ai_storage.check_budget_alert(current_cost)
        return alert

    def build(self):
        """Build the usage dashboard layout."""
        # Set default time range
        self.start_date, self.end_date = self._calculate_time_range(self.current_time_range)

        # Initialize data
        self.usage_stats = None
        self.budget_settings = None
        self.provider_breakdown = {}
        self.workflow_costs = {}

        # Trigger async data loading
        if self._page:
            asyncio.create_task(self._load_dashboard_data())

        # Build controls list with optional alert banner
        controls = [
            self._build_time_range_selector(),
        ]

        # Add alert banner if present
        alert_banner = self._build_alert_banner()
        if alert_banner:
            controls.insert(0, alert_banner)

        # Add remaining dashboard components
        controls.extend([
            self._build_metrics_cards(),
            self._build_provider_breakdown(),
            self._build_workflow_breakdown(),
        ])

        return ft.Column(
            controls=[
                self._build_header(),
                ft.Container(
                    content=ft.Column(
                        controls=controls,
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
                    ft.Container(expand=True),  # Spacer
                    ft.IconButton(
                        icon=ft.Icons.SETTINGS,
                        tooltip="Budget Settings",
                        on_click=lambda e: self._open_budget_dialog(),
                        icon_color=Theme.TEXT_SECONDARY,
                    ),
                ],
            ),
            padding=Theme.SPACING_MD,
            border=ft.Border.only(bottom=ft.BorderSide(1, Theme.BORDER)),
        )

    def _build_alert_banner(self) -> Optional[ft.Container]:
        """Build budget alert banner if alert is active."""
        alert = getattr(self, 'budget_alert', None)
        if not alert:
            return None

        # Determine color and message
        if alert["type"] == "exceeded":
            bgcolor = Theme.ERROR
            icon = ft.Icons.ERROR
            message = f"🚨 Monthly budget exceeded! ${alert['current']:.2f} spent of ${alert['limit']:.2f} limit"
        else:  # threshold
            bgcolor = Theme.WARNING
            icon = ft.Icons.WARNING
            percentage = int(alert['percentage'] * 100)
            message = f"⚠️ You've used {percentage}% of your monthly AI budget (${alert['current']:.2f} of ${alert['limit']:.2f})"

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(icon, color=ft.Colors.WHITE, size=20),
                    ft.Text(message, color=ft.Colors.WHITE, weight=ft.FontWeight.W_500, size=13),
                ],
                spacing=12,
            ),
            padding=12,
            bgcolor=bgcolor,
            border_radius=Theme.RADIUS_SM,
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

    def _build_workflow_breakdown(self) -> ft.Container:
        """Build workflow cost breakdown table."""
        # Get workflow data
        workflow_data = self.workflow_costs if hasattr(self, 'workflow_costs') else {}

        # Build table or empty state
        if workflow_data:
            # Sort workflows by cost (descending) and take top 10
            sorted_workflows = sorted(workflow_data.items(), key=lambda x: x[1], reverse=True)[:10]

            # Build table rows
            table_rows = []

            # Header row
            table_rows.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Text("Workflow", width=200, size=12, weight=ft.FontWeight.BOLD, color=Theme.TEXT_SECONDARY),
                            ft.Text("Cost", width=100, size=12, weight=ft.FontWeight.BOLD, color=Theme.TEXT_SECONDARY),
                            ft.Text("Calls", width=100, size=12, weight=ft.FontWeight.BOLD, color=Theme.TEXT_SECONDARY),
                            ft.Text("Tokens", width=100, size=12, weight=ft.FontWeight.BOLD, color=Theme.TEXT_SECONDARY),
                        ],
                        spacing=16,
                    ),
                    padding=ft.Padding.symmetric(vertical=8, horizontal=16),
                    border=ft.Border.only(bottom=ft.BorderSide(1, Theme.BORDER)),
                )
            )

            # Data rows
            for workflow_name, cost in sorted_workflows:
                table_rows.append(
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Text(workflow_name, width=200, size=12, color=Theme.TEXT_PRIMARY),
                                ft.Text(f"${cost:.2f}", width=100, size=12, color=Theme.TEXT_PRIMARY),
                                ft.Text("—", width=100, size=12, color=Theme.TEXT_MUTED),  # Placeholder
                                ft.Text("—", width=100, size=12, color=Theme.TEXT_MUTED),  # Placeholder
                            ],
                            spacing=16,
                        ),
                        padding=ft.Padding.symmetric(vertical=8, horizontal=16),
                        border=ft.Border.only(bottom=ft.BorderSide(1, Theme.BORDER)),
                    )
                )

            # Scrollable container for table
            table_content = ft.Container(
                content=ft.Column(
                    controls=table_rows,
                    spacing=0,
                    scroll=ft.ScrollMode.AUTO,
                ),
                height=300,
                padding=0,
                bgcolor=Theme.SURFACE,
                border_radius=Theme.RADIUS_MD,
                border=ft.Border.all(1, Theme.BORDER),
            )
        else:
            # Empty state
            table_content = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.TABLE_CHART, size=48, color=Theme.TEXT_MUTED),
                        ft.Text(
                            "No workflow usage data for this time range",
                            size=14,
                            color=Theme.TEXT_SECONDARY,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                ),
                padding=32,
                bgcolor=Theme.SURFACE,
                border_radius=Theme.RADIUS_MD,
                border=ft.Border.all(1, Theme.BORDER),
            )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.TABLE_CHART, size=20, color=Theme.PRIMARY),
                            ft.Text(
                                "Top Workflows by Cost",
                                size=16,
                                weight=ft.FontWeight.BOLD,
                                color=Theme.TEXT_PRIMARY,
                            ),
                            ft.Container(expand=True),  # Spacer
                            ft.IconButton(
                                icon=ft.Icons.DOWNLOAD,
                                tooltip="Export CSV",
                                on_click=lambda e: asyncio.create_task(self._export_csv()),
                                icon_size=20,
                            ),
                        ],
                        spacing=8,
                    ),
                    table_content,
                ],
                spacing=Theme.SPACING_SM,
            ),
            padding=ft.Padding.only(bottom=Theme.SPACING_MD),
        )

    def _open_budget_dialog(self):
        """Open budget settings dialog."""
        # Load current budget settings
        budget = self.budget_settings if hasattr(self, 'budget_settings') else None
        if budget:
            initial_limit = str(budget.monthly_limit_usd)
            initial_threshold = budget.alert_threshold
            initial_reset_day = budget.reset_day
        else:
            initial_limit = "50.00"
            initial_threshold = 0.8
            initial_reset_day = 1

        # Create form fields
        self.budget_limit_field = ft.TextField(
            label="Monthly Limit (USD)",
            value=initial_limit,
            keyboard_type=ft.KeyboardType.NUMBER,
            width=300,
        )

        self.budget_threshold_slider = ft.Slider(
            min=0.5,
            max=1.0,
            value=initial_threshold,
            divisions=10,
            label="{value}%",
            width=300,
        )

        self.budget_reset_day_dropdown = ft.Dropdown(
            label="Reset Day (of month)",
            value=str(initial_reset_day),
            options=[ft.dropdown.Option(str(i)) for i in range(1, 32)],
            width=300,
        )

        # Create dialog
        self.budget_dialog = ft.AlertDialog(
            title=ft.Text("Budget Settings"),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        self.budget_limit_field,
                        ft.Text("Alert Threshold:", size=12, color=Theme.TEXT_SECONDARY),
                        self.budget_threshold_slider,
                        ft.Text(
                            f"{int(self.budget_threshold_slider.value * 100)}% of monthly limit",
                            size=11,
                            color=Theme.TEXT_SECONDARY,
                        ),
                        self.budget_reset_day_dropdown,
                    ],
                    spacing=16,
                    tight=True,
                ),
                width=400,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self._close_budget_dialog()),
                ft.ElevatedButton(
                    "Save",
                    on_click=lambda e: asyncio.create_task(self._save_budget_settings())
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        if self._page:
            self._page.overlay.append(self.budget_dialog)
            self.budget_dialog.open = True
            self._page.update()

    def _close_budget_dialog(self):
        """Close budget settings dialog."""
        if self.budget_dialog and self._page:
            self.budget_dialog.open = False
            self._page.update()

    async def _save_budget_settings(self):
        """Save budget settings to database."""
        try:
            # Parse form values
            limit_str = self.budget_limit_field.value
            monthly_limit = float(limit_str) if limit_str else 50.0

            if monthly_limit <= 0:
                # Show error
                print("Monthly limit must be greater than 0")
                return

            threshold = self.budget_threshold_slider.value
            reset_day = int(self.budget_reset_day_dropdown.value)

            # Create budget settings object
            from src.ai.models import BudgetSettings
            budget = BudgetSettings(
                monthly_limit_usd=monthly_limit,
                alert_threshold=threshold,
                reset_day=reset_day,
            )

            # Save to database
            await self.ai_storage.update_budget_settings(budget)

            # Reload dashboard data
            await self._load_dashboard_data()

            # Close dialog
            self._close_budget_dialog()

        except ValueError as e:
            print(f"Invalid budget settings: {e}")
        except Exception as e:
            print(f"Error saving budget settings: {e}")

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

        # Add provider costs
        provider_costs = getattr(self, 'provider_costs', {})
        for provider, cost in provider_costs.items():
            rows.append([
                f"{self.start_date} to {self.end_date}",
                provider,
                "All Workflows",
                f"{cost:.2f}",
                "-",
                "-",
            ])

        # Add workflow costs
        workflow_costs = getattr(self, 'workflow_costs', {})
        for workflow, cost in workflow_costs.items():
            rows.append([
                f"{self.start_date} to {self.end_date}",
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
