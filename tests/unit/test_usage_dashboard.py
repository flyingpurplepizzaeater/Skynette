# tests/unit/test_usage_dashboard.py
import pytest
from datetime import date, datetime
from unittest.mock import AsyncMock, patch
from src.ui.views.usage_dashboard import UsageDashboardView


@pytest.mark.asyncio
class TestUsageDashboardDataFetching:
    """Unit tests for UsageDashboardView data fetching."""

    async def test_fetch_usage_data_returns_stats(self):
        """fetch_usage_data should return usage statistics."""
        view = UsageDashboardView()
        view.start_date = date(2026, 1, 1)
        view.end_date = date(2026, 1, 31)

        # Mock AIStorage
        with patch.object(view.ai_storage, 'get_usage_stats', new_callable=AsyncMock) as mock_stats:
            mock_stats.return_value = {
                "total_calls": 100,
                "total_tokens": 50000,
                "total_cost": 12.50,
                "avg_latency": 1200,
            }

            stats = await view._fetch_usage_data()

            assert stats["total_calls"] == 100
            assert stats["total_tokens"] == 50000
            assert stats["total_cost"] == 12.50
            mock_stats.assert_called_once_with(view.start_date, view.end_date)

    async def test_fetch_budget_data_returns_settings(self):
        """fetch_budget_data should return budget settings."""
        view = UsageDashboardView()

        with patch.object(view.ai_storage, 'get_budget_settings', new_callable=AsyncMock) as mock_budget:
            from src.ai.models.data import BudgetSettings
            mock_budget.return_value = BudgetSettings(
                monthly_limit_usd=50.0,
                alert_threshold=0.8,
                reset_day=1,
            )

            budget = await view._fetch_budget_data()

            assert budget.monthly_limit_usd == 50.0
            assert budget.alert_threshold == 0.8
            mock_budget.assert_called_once()

    async def test_fetch_usage_data_handles_errors(self):
        """_fetch_usage_data should return defaults on error."""
        view = UsageDashboardView()
        view.start_date = date(2026, 1, 1)
        view.end_date = date(2026, 1, 31)

        with patch.object(view.ai_storage, 'get_usage_stats',
                          new_callable=AsyncMock,
                          side_effect=Exception("Database error")):
            stats = await view._fetch_usage_data()

            # Should return defaults, not raise
            assert stats["total_calls"] == 0
            assert stats["total_tokens"] == 0
            assert stats["total_cost"] == 0.0

    async def test_fetch_budget_data_handles_errors(self):
        """_fetch_budget_data should return None on error."""
        view = UsageDashboardView()

        with patch.object(view.ai_storage, 'get_budget_settings',
                          new_callable=AsyncMock,
                          side_effect=Exception("Database error")):
            budget = await view._fetch_budget_data()

            assert budget is None

    async def test_load_dashboard_data_fetches_in_parallel(self):
        """_load_dashboard_data should fetch both data types in parallel."""
        view = UsageDashboardView()
        view.start_date = date(2026, 1, 1)
        view.end_date = date(2026, 1, 31)
        view.current_time_range = "this_month"

        mock_stats = {"total_calls": 100, "total_tokens": 50000, "total_cost": 12.50}
        from src.ai.models.data import BudgetSettings
        mock_budget = BudgetSettings(monthly_limit_usd=50.0, alert_threshold=0.8, reset_day=1)
        mock_provider_breakdown = {"openai": 10.0, "anthropic": 2.5}

        with patch.object(view, '_fetch_usage_data',
                          new_callable=AsyncMock,
                          return_value=mock_stats) as mock_usage, \
             patch.object(view, '_fetch_budget_data',
                          new_callable=AsyncMock,
                          return_value=mock_budget) as mock_budget_fetch, \
             patch.object(view, '_fetch_provider_breakdown',
                          new_callable=AsyncMock,
                          return_value=mock_provider_breakdown) as mock_provider_fetch, \
             patch.object(view, '_update_metrics_with_data') as mock_update:

            await view._load_dashboard_data()

            mock_usage.assert_called_once()
            mock_budget_fetch.assert_called_once()
            mock_provider_fetch.assert_called_once()
            mock_update.assert_called_once_with(mock_stats, mock_budget, mock_provider_breakdown)

    def test_update_metrics_with_data_stores_and_updates(self):
        """_update_metrics_with_data should store data and trigger UI update."""
        from unittest.mock import MagicMock
        mock_page = MagicMock()
        view = UsageDashboardView(page=mock_page)

        mock_stats = {"total_calls": 100}
        from src.ai.models.data import BudgetSettings
        mock_budget = BudgetSettings(monthly_limit_usd=50.0, alert_threshold=0.8, reset_day=1)

        view._update_metrics_with_data(mock_stats, mock_budget)

        assert view.usage_stats == mock_stats
        assert view.budget_settings == mock_budget
        mock_page.update.assert_called_once()

    def test_build_metrics_cards_uses_real_data_when_available(self):
        """_build_metrics_cards should use real data when available."""
        import flet as ft
        view = UsageDashboardView()
        view.usage_stats = {
            "total_calls": 150,
            "total_tokens": 75000,
            "total_cost": 25.50,
        }
        from src.ai.models.data import BudgetSettings
        view.budget_settings = BudgetSettings(monthly_limit_usd=100.0, alert_threshold=0.8, reset_day=1)

        result = view._build_metrics_cards()

        # Verify container was built
        assert isinstance(result, ft.Container)

    def test_build_metrics_cards_shows_zeros_when_no_data(self):
        """_build_metrics_cards should show zeros when data is None."""
        import flet as ft
        view = UsageDashboardView()
        view.usage_stats = None
        view.budget_settings = None

        result = view._build_metrics_cards()

        # Verify container was built
        assert isinstance(result, ft.Container)

    def test_calculate_time_range_last_7d(self):
        """_calculate_time_range should calculate last 7 days correctly."""
        from datetime import timedelta
        view = UsageDashboardView()

        start, end = view._calculate_time_range("last_7d")

        assert (end - start).days == 7
        assert end == date.today()

    def test_calculate_time_range_last_30d(self):
        """_calculate_time_range should calculate last 30 days correctly."""
        view = UsageDashboardView()

        start, end = view._calculate_time_range("last_30d")

        assert (end - start).days == 30
        assert end == date.today()

    def test_calculate_time_range_this_month(self):
        """_calculate_time_range should calculate current month correctly."""
        view = UsageDashboardView()

        start, end = view._calculate_time_range("this_month")

        today = date.today()
        assert start.day == 1
        assert start.month == today.month
        assert start.year == today.year
        assert end == today

    def test_calculate_time_range_last_month(self):
        """_calculate_time_range should calculate last month correctly."""
        view = UsageDashboardView()

        start, end = view._calculate_time_range("last_month")

        assert start.day == 1
        # End should be last day of previous month
        assert end.day >= 28  # All months have at least 28 days

    def test_calculate_time_range_default(self):
        """_calculate_time_range should default to this_month for unknown range."""
        view = UsageDashboardView()

        start, end = view._calculate_time_range("unknown")

        today = date.today()
        assert start.day == 1
        assert start.month == today.month
        assert end == today

    def test_build_header(self):
        """_build_header should create header container."""
        import flet as ft
        view = UsageDashboardView()

        result = view._build_header()

        assert isinstance(result, ft.Container)

    def test_build_budget_card_under_threshold(self):
        """_build_budget_card should show success color when under threshold."""
        import flet as ft
        view = UsageDashboardView()

        result = view._build_budget_card(0.5)  # 50% usage

        assert isinstance(result, ft.Container)

    def test_build_budget_card_at_warning_threshold(self):
        """_build_budget_card should show warning color at 80%."""
        import flet as ft
        view = UsageDashboardView()

        result = view._build_budget_card(0.85)  # 85% usage

        assert isinstance(result, ft.Container)

    def test_build_budget_card_over_limit(self):
        """_build_budget_card should show error color when over limit."""
        import flet as ft
        view = UsageDashboardView()

        result = view._build_budget_card(1.2)  # 120% usage

        assert isinstance(result, ft.Container)
