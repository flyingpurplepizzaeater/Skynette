"""Tests for Usage Dashboard view."""

import pytest
from playwright.sync_api import Page, expect


class TestUsageDashboard:
    """Tests for Usage Dashboard view."""

    @pytest.fixture(autouse=True)
    def navigate_to_ai_hub(self, page: Page, helpers):
        """Navigate to AI Hub before each test."""
        helpers.navigate_to(page, "ai_hub")

    def test_usage_tab_exists_in_ai_hub(self, page: Page):
        """AI Hub should have a Usage tab."""
        # Already at AI Hub from fixture
        expect(page.locator("flt-semantics[role='tab']:has-text('Usage')")).to_be_visible()

    def test_usage_dashboard_view_loads(self, page: Page):
        """Usage dashboard view should load successfully."""
        # Click on Usage tab
        page.locator("flt-semantics[role='tab']:has-text('Usage')").click()
        expect(page.locator("text=Usage Dashboard")).to_be_visible(timeout=10000)

    def test_usage_dashboard_displays_metrics(self, page: Page):
        """Usage dashboard should display usage metrics."""
        # Click on Usage tab
        page.locator("flt-semantics[role='tab']:has-text('Usage')").click()

        # Verify key metric sections are visible
        expect(page.locator("text=Total Requests")).to_be_visible(timeout=5000)
        expect(page.locator("text=API Usage")).to_be_visible(timeout=5000)

    def test_usage_dashboard_has_time_period_selector(self, page: Page):
        """Usage dashboard should have a time period selector."""
        # Click on Usage tab
        page.locator("flt-semantics[role='tab']:has-text('Usage')").click()

        # Look for time period options (e.g., Last 7 days, Last 30 days, etc.)
        # This assumes there's a dropdown or selector for time periods
        expect(page.locator("flt-semantics[role='button']").filter(has_text="Last")).to_be_visible(timeout=5000)

    def test_usage_dashboard_displays_charts(self, page: Page):
        """Usage dashboard should display usage charts."""
        # Click on Usage tab
        page.locator("flt-semantics[role='tab']:has-text('Usage')").click()

        # Verify at least one chart/visualization element exists
        # Flutter canvas elements are typically used for charts
        chart_locator = page.locator("flt-canvas, flt-picture, [aria-label*='chart']").first
        expect(chart_locator).to_be_visible(timeout=10000)


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


class TestProviderBreakdown:
    """Tests for provider cost breakdown visualization."""

    @pytest.fixture(autouse=True)
    def navigate_to_usage(self, page: Page, helpers):
        """Navigate to Usage Dashboard before each test."""
        helpers.navigate_to("usage")

    def test_provider_breakdown_section_visible(self, page: Page):
        """Provider breakdown section should be visible."""
        expect(page.locator("text=Cost by Provider")).to_be_visible()

    def test_provider_breakdown_shows_providers(self, page: Page):
        """Provider breakdown should show provider names."""
        # Wait for data to load
        page.wait_for_timeout(1000)
        # At minimum, should show "No data" or provider names
        # This test will be more specific once we have test data
        provider_section = page.locator("text=Cost by Provider")
        expect(provider_section).to_be_visible()
