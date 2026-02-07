"""
Unit tests for CSV export functionality in Usage Dashboard.
"""

import pytest
from datetime import date
from src.ui.views.usage_dashboard import UsageDashboardView


class TestCSVExport:
    """Tests for CSV export methods."""

    def test_export_csv_method_exists(self):
        """_export_csv method should exist and be async."""
        import inspect

        dashboard = UsageDashboardView()
        assert hasattr(dashboard, '_export_csv')
        assert callable(dashboard._export_csv)
        # Should be async
        assert inspect.iscoroutinefunction(dashboard._export_csv)

    def test_build_csv_content_method_exists(self):
        """_build_csv_content method should exist and be async."""
        import inspect

        dashboard = UsageDashboardView()
        assert hasattr(dashboard, '_build_csv_content')
        assert callable(dashboard._build_csv_content)
        # Should be async
        assert inspect.iscoroutinefunction(dashboard._build_csv_content)

    def test_save_csv_file_method_exists(self):
        """_save_csv_file method should exist."""
        dashboard = UsageDashboardView()
        assert hasattr(dashboard, '_save_csv_file')
        assert callable(dashboard._on_csv_save_result)

    @pytest.mark.asyncio
    async def test_build_csv_content_structure(self):
        """CSV content should have correct header and structure."""
        dashboard = UsageDashboardView()
        dashboard.start_date = date(2024, 1, 1)
        dashboard.end_date = date(2024, 1, 31)
        dashboard.provider_costs = {"openai": 0.05, "anthropic": 0.04}
        dashboard.workflow_costs = {"data_processing": 0.03, "content_generation": 0.02}

        csv_content = await dashboard._build_csv_content()

        # Check header
        assert "Date Range,Provider,Workflow,Cost (USD),Calls,Tokens" in csv_content

        # Check provider rows
        assert "2024-01-01 to 2024-01-31,openai,All Workflows,0.05,-,-" in csv_content
        assert "2024-01-01 to 2024-01-31,anthropic,All Workflows,0.04,-,-" in csv_content

        # Check workflow rows
        assert "2024-01-01 to 2024-01-31,All Providers,data_processing,0.03,-,-" in csv_content
        assert "2024-01-01 to 2024-01-31,All Providers,content_generation,0.02,-,-" in csv_content

    @pytest.mark.asyncio
    async def test_build_csv_content_empty_data(self):
        """CSV content should handle empty data gracefully."""
        dashboard = UsageDashboardView()
        dashboard.start_date = date(2024, 1, 1)
        dashboard.end_date = date(2024, 1, 31)
        # No provider_costs or workflow_costs set

        csv_content = await dashboard._build_csv_content()

        # Should have header only
        lines = csv_content.strip().split('\n')
        assert len(lines) == 1
        assert lines[0] == "Date Range,Provider,Workflow,Cost (USD),Calls,Tokens"

    @pytest.mark.asyncio
    async def test_build_csv_content_cost_formatting(self):
        """CSV content should format costs to 2 decimal places."""
        dashboard = UsageDashboardView()
        dashboard.start_date = date(2024, 1, 1)
        dashboard.end_date = date(2024, 1, 31)
        dashboard.provider_costs = {"openai": 0.123456}
        dashboard.workflow_costs = {}

        csv_content = await dashboard._build_csv_content()

        # Cost should be formatted to 2 decimal places
        assert "0.12" in csv_content
        assert "0.123" not in csv_content
