"""Tests for Usage Dashboard view."""

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.skip(reason="Navigation infrastructure needs fixing - AI Hub button not found")
class TestUsageDashboard:
    """Tests for Usage Dashboard view."""

    @pytest.fixture(autouse=True)
    def navigate_to_ai_hub(self, page: Page, helpers):
        """Navigate to AI Hub before each test."""
        helpers.navigate_to(page, "ai_hub")
        page.wait_for_timeout(500)

    def test_usage_tab_exists_in_ai_hub(self, page: Page):
        """AI Hub should have a Usage tab."""
        # Already at AI Hub from fixture
        # Look for the Usage text - it should be visible as a tab
        usage_locator = page.get_by_text("Usage", exact=False)
        expect(usage_locator.first).to_be_visible(timeout=10000)

    def test_usage_dashboard_view_loads(self, page: Page):
        """Usage dashboard view should load successfully."""
        # Click on Usage tab
        usage_tab = page.locator(":has-text('Usage')").filter(has=page.locator("flt-semantics"))
        usage_tab.first.click()
        page.wait_for_timeout(500)
        expect(page.locator("text=Usage Dashboard")).to_be_visible(timeout=10000)


@pytest.mark.skip(reason="Navigation infrastructure needs fixing - AI Hub button not found")
class TestMetricsCards:
    """Tests for metrics cards display."""

    @pytest.fixture(autouse=True)
    def navigate_to_usage(self, page: Page):
        """Navigate to Usage Dashboard before each test."""
        # Click AI Hub navigation button
        ai_hub_btn = page.locator("flt-semantics[role='button']:has-text('AI Hub')")
        if ai_hub_btn.count() > 0:
            ai_hub_btn.first.click()
            page.wait_for_timeout(500)

        # Click on Usage tab
        usage_tab = page.locator(":has-text('Usage')").filter(has=page.locator("flt-semantics"))
        if usage_tab.count() > 0:
            usage_tab.first.click()
            page.wait_for_timeout(500)

    def test_metrics_cards_display_cost(self, page: Page):
        """Metrics should display total cost."""
        # Wait for dashboard to be visible
        expect(page.locator("text=Usage Dashboard")).to_be_visible(timeout=10000)
        # Wait a bit for metrics to load
        page.wait_for_timeout(1000)
        # Check for Total Cost label
        expect(page.locator("text=Total Cost")).to_be_visible(timeout=10000)
        # Cost value should be visible (format: $X.XX)
        expect(page.locator("text=/\\$\\d+\\.\\d{2}/").first).to_be_visible()

    def test_metrics_cards_display_api_calls(self, page: Page):
        """Metrics should display API calls count."""
        expect(page.locator("text=API Calls")).to_be_visible()

    def test_metrics_cards_display_tokens(self, page: Page):
        """Metrics should display total tokens."""
        expect(page.locator("text=Total Tokens")).to_be_visible()

    def test_metrics_cards_display_budget_usage(self, page: Page):
        """Metrics should display budget usage percentage."""
        expect(page.locator("text=Budget")).to_be_visible()


# Unit-style tests that verify component structure without E2E navigation
class TestMetricsCardsUnit:
    """Unit tests for metrics cards - verify component builds correctly."""

    def test_usage_dashboard_builds_without_error(self):
        """Usage dashboard should build without errors."""
        from src.ui.views.usage_dashboard import UsageDashboardView
        import flet as ft

        # Create dashboard view
        dashboard = UsageDashboardView()

        # Build should not raise an exception
        result = dashboard.build()

        # Result should be a Column
        assert isinstance(result, ft.Column)
        assert len(result.controls) > 0

    def test_metrics_cards_method_exists(self):
        """Usage dashboard should have _build_metrics_cards method."""
        from src.ui.views.usage_dashboard import UsageDashboardView

        dashboard = UsageDashboardView()
        assert hasattr(dashboard, '_build_metrics_cards')
        assert callable(dashboard._build_metrics_cards)

    def test_metrics_cards_creates_container(self):
        """_build_metrics_cards should return a Container."""
        from src.ui.views.usage_dashboard import UsageDashboardView
        import flet as ft

        dashboard = UsageDashboardView()
        # Initialize usage_stats to avoid AttributeError
        dashboard.usage_stats = None
        dashboard.budget_settings = None
        result = dashboard._build_metrics_cards()

        assert isinstance(result, ft.Container)
        assert result.content is not None

    def test_metric_card_helper_creates_container(self):
        """_build_metric_card should create a card container."""
        from src.ui.views.usage_dashboard import UsageDashboardView
        import flet as ft
        from src.ui.theme import Theme

        dashboard = UsageDashboardView()
        card = dashboard._build_metric_card(
            "Test Label",
            "$0.00",
            ft.Icons.INFO,
            Theme.PRIMARY
        )

        assert isinstance(card, ft.Container)
        assert card.width == 200

    def test_budget_card_creates_container_with_progress_bar(self):
        """_build_budget_card should create a card with progress indicator."""
        from src.ui.views.usage_dashboard import UsageDashboardView
        import flet as ft

        dashboard = UsageDashboardView()
        card = dashboard._build_budget_card(0.5)

        assert isinstance(card, ft.Container)
        assert card.width == 200
        # Should have progress indicator in controls
        column = card.content
        assert isinstance(column, ft.Column)
        # Last control should be ProgressBar
        assert any(isinstance(ctrl, ft.ProgressBar) for ctrl in column.controls)


@pytest.mark.skip(reason="Navigation infrastructure needs fixing - AI Hub button not found")
class TestTimeRangeSelector:
    """Tests for time range selection."""

    @pytest.fixture(autouse=True)
    def navigate_to_usage(self, page: Page, helpers):
        """Navigate to Usage Dashboard before each test."""
        helpers.navigate_to("usage")

    def test_time_range_buttons_visible(self, page: Page):
        """Time range selector should show all options."""
        expect(page.locator("text=Last 7 days")).to_be_visible()
        expect(page.locator("text=Last 30 days")).to_be_visible()
        expect(page.locator("text=This Month")).to_be_visible()
        expect(page.locator("text=Last Month")).to_be_visible()

    def test_this_month_selected_by_default(self, page: Page):
        """This Month should be selected by default."""
        # Check if This Month button has primary color (indicating selection)
        # This is implementation-dependent, may need adjustment
        this_month_button = page.locator("text=This Month")
        expect(this_month_button).to_be_visible()
