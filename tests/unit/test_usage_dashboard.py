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
