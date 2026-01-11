"""Unit tests for Usage Dashboard view."""

import pytest
import flet as ft
from src.ui.views.usage_dashboard import UsageDashboardView
from src.ui.theme import Theme


class TestTimeRangeSelectorUnit:
    """Unit tests for time range selector component."""

    def test_time_range_selector_method_exists(self):
        """Usage dashboard should have _build_time_range_selector method."""
        dashboard = UsageDashboardView()
        assert hasattr(dashboard, '_build_time_range_selector')
        assert callable(dashboard._build_time_range_selector)

    def test_time_range_selector_creates_container(self):
        """_build_time_range_selector should return a Container with buttons."""
        dashboard = UsageDashboardView()
        result = dashboard._build_time_range_selector()

        assert isinstance(result, ft.Container)
        assert isinstance(result.content, ft.Row)
        # Should have 5 controls: label + 4 buttons
        assert len(result.content.controls) == 5

    def test_time_range_button_selected_state(self):
        """Time range button should reflect selected state."""
        dashboard = UsageDashboardView()
        dashboard.current_time_range = "last_7d"

        # Build selected button
        selected_button = dashboard._build_time_range_button("Last 7 days", "last_7d")
        assert selected_button.style.bgcolor == Theme.PRIMARY
        assert selected_button.style.color == ft.Colors.WHITE

        # Build non-selected button
        other_button = dashboard._build_time_range_button("Last 30 days", "last_30d")
        assert other_button.style.bgcolor == Theme.SURFACE
        assert other_button.style.color == Theme.TEXT_PRIMARY
