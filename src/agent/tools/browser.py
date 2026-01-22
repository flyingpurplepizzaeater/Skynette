"""
Browser Automation Tool

Navigate websites, fill forms, click elements, and extract data using Playwright with stealth.
"""

import base64
import logging
import time
from typing import Any, Optional

from src.agent.models.tool import ToolResult
from src.agent.registry.base_tool import AgentContext, BaseTool

logger = logging.getLogger(__name__)

# Active pages tracked by session_id for multi-step operations
_active_pages: dict[str, Any] = {}


class BrowserManager:
    """Manages shared browser instance for efficiency."""

    _instance: Optional["BrowserManager"] = None
    _browser: Any = None
    _playwright: Any = None

    def __new__(cls) -> "BrowserManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def get_browser(self, headless: bool = True) -> Any:
        """Get or create browser instance."""
        if self._browser is None or not self._browser.is_connected():
            from playwright.async_api import async_playwright

            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=headless,
                args=["--disable-blink-features=AutomationControlled"],
            )
        return self._browser

    async def close(self) -> None:
        """Close browser and playwright."""
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None


# Module-level singleton
_browser_manager: Optional[BrowserManager] = None


def get_browser_manager() -> BrowserManager:
    """Get the browser manager singleton."""
    global _browser_manager
    if _browser_manager is None:
        _browser_manager = BrowserManager()
    return _browser_manager


class BrowserTool(BaseTool):
    """Navigate websites, fill forms, click elements, and extract data."""

    name = "browser"
    description = (
        "Navigate websites, fill forms, click elements, and extract data. "
        "Uses headless browser with stealth to avoid detection. "
        "Supports actions: navigate, click, fill, extract, screenshot, get_text, close."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["navigate", "click", "fill", "extract", "screenshot", "get_text", "close"],
                "description": "Browser action to perform",
            },
            "url": {
                "type": "string",
                "description": "URL to navigate to (for navigate action)",
            },
            "selector": {
                "type": "string",
                "description": "CSS selector for element (for click, fill, extract actions)",
            },
            "value": {
                "type": "string",
                "description": "Value for fill action",
            },
            "timeout": {
                "type": "integer",
                "description": "Timeout in milliseconds (default: 30000)",
                "default": 30000,
            },
            "headless": {
                "type": "boolean",
                "description": "Run headless (default: true)",
                "default": True,
            },
        },
        "required": ["action"],
    }
    is_destructive = True  # Can fill forms, click buttons

    async def execute(self, params: dict, context: AgentContext) -> ToolResult:
        """Execute browser action."""
        start = time.perf_counter()

        action = params.get("action")
        url = params.get("url", "")
        selector = params.get("selector", "")
        value = params.get("value", "")
        timeout = params.get("timeout", 30000)  # 30s default per CONTEXT.md
        headless = params.get("headless", True)

        session_id = context.session_id

        try:
            # Handle close action
            if action == "close":
                return await self._close_page(session_id, start)

            # Get or create page for this session
            page = await self._get_or_create_page(session_id, headless)

            if action == "navigate":
                return await self._navigate(page, url, timeout, session_id, start)
            elif action == "click":
                return await self._click(page, selector, timeout, session_id, start)
            elif action == "fill":
                return await self._fill(page, selector, value, timeout, session_id, start)
            elif action == "extract":
                return await self._extract(page, selector, timeout, session_id, start)
            elif action == "screenshot":
                return await self._screenshot(page, session_id, start)
            elif action == "get_text":
                return await self._get_text(page, session_id, start)
            else:
                return ToolResult.failure_result(
                    tool_call_id=session_id,
                    error=f"Unknown action: {action}",
                    duration_ms=(time.perf_counter() - start) * 1000,
                )

        except ImportError as e:
            return ToolResult.failure_result(
                tool_call_id=session_id,
                error=f"Playwright not installed. Run: pip install playwright && playwright install chromium. Error: {e}",
                duration_ms=(time.perf_counter() - start) * 1000,
            )
        except Exception as e:
            logger.error(f"Browser error: {e}", exc_info=True)
            return ToolResult.failure_result(
                tool_call_id=session_id,
                error=f"Browser error: {str(e)}",
                duration_ms=(time.perf_counter() - start) * 1000,
            )

    async def _get_or_create_page(self, session_id: str, headless: bool) -> Any:
        """Get existing page or create new one for session."""
        if session_id in _active_pages:
            page = _active_pages[session_id]
            # Check if page is still valid
            try:
                if not page.is_closed():
                    return page
            except Exception:
                pass
            # Page closed, remove from tracking
            del _active_pages[session_id]

        # Create new page with stealth
        manager = get_browser_manager()
        browser = await manager.get_browser(headless=headless)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )

        # Apply stealth if available
        try:
            from playwright_stealth import stealth_async

            await stealth_async(context)
            logger.debug("Applied playwright-stealth to browser context")
        except ImportError:
            logger.debug("playwright-stealth not installed, continuing without stealth")

        page = await context.new_page()
        _active_pages[session_id] = page
        logger.debug(f"Created new browser page for session {session_id}")
        return page

    async def _close_page(self, session_id: str, start: float) -> ToolResult:
        """Close page for session."""
        if session_id in _active_pages:
            page = _active_pages.pop(session_id)
            try:
                await page.context.close()
            except Exception:
                pass
            return ToolResult.success_result(
                tool_call_id=session_id,
                data={"closed": True, "session_id": session_id},
                duration_ms=(time.perf_counter() - start) * 1000,
            )
        return ToolResult.success_result(
            tool_call_id=session_id,
            data={"closed": False, "message": "No active page for session"},
            duration_ms=(time.perf_counter() - start) * 1000,
        )

    async def _navigate(
        self, page: Any, url: str, timeout: int, session_id: str, start: float
    ) -> ToolResult:
        """Navigate to URL."""
        if not url:
            return ToolResult.failure_result(
                tool_call_id=session_id,
                error="URL required for navigate action",
                duration_ms=(time.perf_counter() - start) * 1000,
            )

        await page.goto(url, timeout=timeout)

        # Auto screenshot on navigation per CONTEXT.md
        screenshot = await page.screenshot()
        title = await page.title()

        logger.info(f"Navigated to {url}: {title}")

        return ToolResult.success_result(
            tool_call_id=session_id,
            data={
                "title": title,
                "url": page.url,
                "screenshot_b64": base64.b64encode(screenshot).decode(),
            },
            duration_ms=(time.perf_counter() - start) * 1000,
        )

    async def _click(
        self, page: Any, selector: str, timeout: int, session_id: str, start: float
    ) -> ToolResult:
        """Click element."""
        if not selector:
            return ToolResult.failure_result(
                tool_call_id=session_id,
                error="Selector required for click action",
                duration_ms=(time.perf_counter() - start) * 1000,
            )

        await page.click(selector, timeout=timeout)
        logger.info(f"Clicked element: {selector}")

        return ToolResult.success_result(
            tool_call_id=session_id,
            data={"clicked": selector},
            duration_ms=(time.perf_counter() - start) * 1000,
        )

    async def _fill(
        self, page: Any, selector: str, value: str, timeout: int, session_id: str, start: float
    ) -> ToolResult:
        """Fill form field."""
        if not selector:
            return ToolResult.failure_result(
                tool_call_id=session_id,
                error="Selector required for fill action",
                duration_ms=(time.perf_counter() - start) * 1000,
            )

        await page.fill(selector, value, timeout=timeout)
        logger.info(f"Filled element: {selector}")

        return ToolResult.success_result(
            tool_call_id=session_id,
            data={"filled": selector, "value": value},
            duration_ms=(time.perf_counter() - start) * 1000,
        )

    async def _extract(
        self, page: Any, selector: str, timeout: int, session_id: str, start: float
    ) -> ToolResult:
        """Extract element content."""
        if not selector:
            return ToolResult.failure_result(
                tool_call_id=session_id,
                error="Selector required for extract action",
                duration_ms=(time.perf_counter() - start) * 1000,
            )

        element = await page.wait_for_selector(selector, timeout=timeout)
        if not element:
            return ToolResult.failure_result(
                tool_call_id=session_id,
                error=f"Element not found: {selector}",
                duration_ms=(time.perf_counter() - start) * 1000,
            )

        text = await element.text_content()
        html = await element.inner_html()

        return ToolResult.success_result(
            tool_call_id=session_id,
            data={"selector": selector, "text": text, "html": html},
            duration_ms=(time.perf_counter() - start) * 1000,
        )

    async def _screenshot(self, page: Any, session_id: str, start: float) -> ToolResult:
        """Take full page screenshot."""
        screenshot = await page.screenshot(full_page=True)

        return ToolResult.success_result(
            tool_call_id=session_id,
            data={"screenshot_b64": base64.b64encode(screenshot).decode()},
            duration_ms=(time.perf_counter() - start) * 1000,
        )

    async def _get_text(self, page: Any, session_id: str, start: float) -> ToolResult:
        """Get all visible text from page."""
        text = await page.text_content("body")

        return ToolResult.success_result(
            tool_call_id=session_id,
            data={"text": text},
            duration_ms=(time.perf_counter() - start) * 1000,
        )
