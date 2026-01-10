"""
E2E test fixtures for Flet app testing.

This module provides fixtures for launching the Skynette app
in web mode and automating it with Playwright.
"""

import os
import sys
import time
import subprocess
import asyncio
from pathlib import Path
from typing import Generator

import pytest
from playwright.sync_api import Page, Browser, Playwright, sync_playwright

# App configuration
APP_PORT = 8550
APP_URL = f"http://localhost:{APP_PORT}"
STARTUP_TIMEOUT = 30  # seconds
PROJECT_ROOT = Path(__file__).parent.parent.parent


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the project root directory."""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def app_env(tmp_path_factory) -> dict:
    """Environment variables for test mode."""
    temp_dir = tmp_path_factory.mktemp("skynette_test_data")
    return {
        **os.environ,
        "SKYNETTE_TEST_MODE": "true",
        "SKYNETTE_MOCK_AI": "true",
        "SKYNETTE_DATA_DIR": str(temp_dir),
        "PYTHONPATH": str(PROJECT_ROOT),
    }


@pytest.fixture(scope="session")
def app_process(project_root: Path, app_env: dict) -> Generator[subprocess.Popen, None, None]:
    """
    Start the Flet app in web mode for testing.

    This fixture starts the application once per test session
    and shuts it down when all tests are complete.
    """
    # Build the command to run the app in web mode
    # Note: Flet uses canvas rendering, but Flutter creates accessibility semantics
    # which we enable via JavaScript after page load

    cmd = [
        sys.executable,
        "-c",
        f"""
import sys
sys.path.insert(0, r'{project_root}')
import flet as ft
from src.main import main
ft.app(target=main, port={APP_PORT}, view=ft.AppView.WEB_BROWSER)
""",
    ]

    print(f"\nStarting Skynette app: {' '.join(cmd)}")

    # Start the process
    proc = subprocess.Popen(
        cmd,
        env=app_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(project_root),
    )

    # Wait for app to be ready
    start_time = time.time()
    app_ready = False

    while time.time() - start_time < STARTUP_TIMEOUT:
        try:
            import httpx
            response = httpx.get(APP_URL, timeout=2.0)
            if response.status_code == 200:
                app_ready = True
                print(f"App ready at {APP_URL}")
                break
        except Exception:
            pass

        # Check if process died
        if proc.poll() is not None:
            stdout, stderr = proc.communicate()
            raise RuntimeError(
                f"App process died during startup.\n"
                f"stdout: {stdout.decode()}\n"
                f"stderr: {stderr.decode()}"
            )

        time.sleep(0.5)

    if not app_ready:
        proc.terminate()
        proc.wait()
        raise RuntimeError(f"App failed to start within {STARTUP_TIMEOUT} seconds")

    yield proc

    # Cleanup
    print("\nShutting down Skynette app...")
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()


@pytest.fixture(scope="session")
def browser_instance(app_process) -> Generator[Browser, None, None]:
    """
    Launch a browser for the test session.

    Requires app_process to ensure the app is running.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,  # Set to False for debugging
            args=["--disable-gpu", "--no-sandbox"],
        )
        yield browser
        browser.close()


@pytest.fixture
def page(browser_instance: Browser) -> Generator[Page, None, None]:
    """
    Create a new page for each test.

    Each test gets a fresh browser context and page.
    """
    context = browser_instance.new_context(
        viewport={"width": 1280, "height": 720},
    )
    page = context.new_page()

    # Navigate to app with extended timeout for Flet initialization
    page.goto(APP_URL, timeout=60000)
    page.wait_for_load_state("networkidle", timeout=30000)

    # Wait for Flet to initialize (the app shell should be visible)
    # Flet apps need extra time to hydrate the Flutter web app
    page.wait_for_timeout(3000)  # Give Flet time to render

    # Enable accessibility mode to create DOM elements we can interact with
    # By default, Flutter renders to canvas with no DOM elements.
    # Clicking the accessibility placeholder enables the semantics tree.
    page.evaluate('''
        const placeholder = document.querySelector('flt-semantics-placeholder');
        if (placeholder) {
            placeholder.click();
        }
    ''')
    page.wait_for_timeout(2000)  # Wait for semantics tree to build

    yield page

    page.close()
    context.close()


@pytest.fixture
def page_with_screenshot_on_failure(page: Page, request) -> Generator[Page, None, None]:
    """
    Page fixture that captures screenshot on test failure.
    """
    yield page

    # Capture screenshot on failure
    if request.node.rep_call.failed if hasattr(request.node, 'rep_call') else False:
        screenshot_dir = PROJECT_ROOT / "test-results" / "screenshots"
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        screenshot_path = screenshot_dir / f"{request.node.name}.png"
        page.screenshot(path=str(screenshot_path))
        print(f"Screenshot saved to: {screenshot_path}")


# Common selectors for Skynette UI elements
# Flutter creates flt-semantics elements with text content and some aria-labels
class Selectors:
    """Common CSS/text selectors for Skynette UI elements."""

    # Navigation - flt-semantics elements with role=button and text content
    SIDEBAR = "flt-semantics"
    NAV_WORKFLOWS = "flt-semantics[role='button']:has-text('Workflows')"
    NAV_AI_HUB = "flt-semantics[role='button']:has-text('AI Hub')"
    NAV_AGENTS = "flt-semantics[role='button']:has-text('Agents')"
    NAV_DEVTOOLS = "flt-semantics[role='button']:has-text('DevTools')"
    NAV_PLUGINS = "flt-semantics[role='button']:has-text('Plugins')"
    NAV_RUNS = "flt-semantics[role='button']:has-text('Runs')"
    NAV_SETTINGS = "flt-semantics[role='button']:has-text('Settings')"

    # Workflows view - text-based selectors for flt-semantics elements
    NEW_WORKFLOW_BTN = "flt-semantics[role='button']:has-text('New Workflow')"
    WORKFLOW_CARD = "flt-semantics[role='group'][aria-label]"

    # Editor
    SAVE_BTN = "flt-semantics[role='button']:has-text('Save')"
    RUN_BTN = "flt-semantics[role='button']:has-text('Run')"
    SIMPLE_MODE_BTN = "flt-semantics:has-text('Simple')"
    ADVANCED_MODE_BTN = "flt-semantics:has-text('Advanced')"

    # Assistant - aria-label selectors for items that have them
    ASSISTANT_HEADER = "flt-semantics span:has-text('Skynet Assistant')"
    ASSISTANT_INPUT = "textarea[aria-label*='Ask'], textarea, input"
    ASSISTANT_SEND = "flt-semantics[aria-label*='Send']"

    # Dialogs
    DIALOG = "[role='dialog'], flt-semantics[role='dialog']"
    CONFIRM_BTN = "flt-semantics[role='button']:has-text('Confirm')"
    CANCEL_BTN = "flt-semantics[role='button']:has-text('Cancel')"
    CREATE_BTN = "flt-semantics[role='button']:has-text('Create')"

    # Common
    LOADING = "flt-semantics:has-text('Loading')"
    ERROR = "flt-semantics:has-text('Error')"
    SUCCESS = "flt-semantics:has-text('Success')"


@pytest.fixture
def selectors() -> type[Selectors]:
    """Provide access to common selectors."""
    return Selectors


# Helpers for common test operations
class TestHelpers:
    """Helper methods for common test operations."""

    @staticmethod
    def navigate_to(page: Page, view: str):
        """Navigate to a specific view using aria-label selectors."""
        view_map = {
            "workflows": Selectors.NAV_WORKFLOWS,
            "ai_hub": Selectors.NAV_AI_HUB,
            "agents": Selectors.NAV_AGENTS,
            "devtools": Selectors.NAV_DEVTOOLS,
            "plugins": Selectors.NAV_PLUGINS,
            "runs": Selectors.NAV_RUNS,
            "settings": Selectors.NAV_SETTINGS,
        }
        if view in view_map:
            selector = view_map[view]
            page.locator(selector).first.click()
            page.wait_for_timeout(500)  # Wait for view transition

    @staticmethod
    def wait_for_app_ready(page: Page, timeout: int = 5000):
        """Wait for the app to be fully loaded."""
        # Wait for sidebar navigation to be visible
        page.wait_for_selector(Selectors.NAV_WORKFLOWS, timeout=timeout)

    @staticmethod
    def create_workflow(page: Page, name: str, description: str = ""):
        """Create a new workflow via UI."""
        page.locator(Selectors.NEW_WORKFLOW_BTN).first.click()
        page.wait_for_selector(Selectors.DIALOG, timeout=5000)
        # Fill the name input
        inputs = page.locator("input, [role='textbox']")
        if inputs.count() > 0:
            inputs.first.fill(name)
        page.locator(Selectors.CREATE_BTN).first.click()
        page.wait_for_timeout(500)


@pytest.fixture
def helpers() -> type[TestHelpers]:
    """Provide access to test helpers."""
    return TestHelpers


# Hook for capturing test results (for screenshot on failure)
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook to capture test results for screenshot fixture."""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)
