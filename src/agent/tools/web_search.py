"""
Web Search Tool

Provides web search capability using DuckDuckGo with scraper fallback.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from src.agent.models.tool import ToolResult
from src.agent.registry.base_tool import AgentContext, BaseTool

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """A single web search result."""

    title: str
    url: str
    snippet: str


class SearchProvider(ABC):
    """Abstract base class for search providers."""

    @abstractmethod
    async def search(
        self,
        query: str,
        max_results: int = 10,
        time_filter: Optional[str] = None,  # d, w, m, y
        domain_filter: Optional[str] = None,  # site:example.com
    ) -> list[SearchResult]:
        """
        Execute a web search.

        Args:
            query: Search query string
            max_results: Maximum number of results to return
            time_filter: Time filter (d=day, w=week, m=month, y=year)
            domain_filter: Restrict results to domain (e.g., github.com)

        Returns:
            List of SearchResult objects
        """
        pass


class DuckDuckGoProvider(SearchProvider):
    """Search provider using DuckDuckGo API via ddgs library."""

    async def search(
        self,
        query: str,
        max_results: int = 10,
        time_filter: Optional[str] = None,
        domain_filter: Optional[str] = None,
    ) -> list[SearchResult]:
        """Execute search using DuckDuckGo."""
        # Try newer ddgs package first, fall back to older duckduckgo_search
        DDGS = None
        try:
            from ddgs import DDGS
        except ImportError:
            try:
                from duckduckgo_search import DDGS
            except ImportError:
                raise ImportError(
                    "ddgs package required. Install with: pip install ddgs"
                )

        # Apply domain filter to query
        search_query = query
        if domain_filter:
            search_query = f"site:{domain_filter} {query}"

        # Run sync library in thread pool
        def _search() -> list[dict]:
            with DDGS() as ddgs:
                return list(
                    ddgs.text(
                        search_query,
                        max_results=max_results,
                        timelimit=time_filter,
                    )
                )

        raw_results = await asyncio.to_thread(_search)

        # Map to SearchResult objects
        results = []
        for r in raw_results:
            results.append(
                SearchResult(
                    title=r.get("title", ""),
                    url=r.get("href", ""),
                    snippet=r.get("body", ""),
                )
            )

        return results


class ScraperFallbackProvider(SearchProvider):
    """Fallback provider that scrapes DuckDuckGo HTML directly."""

    async def search(
        self,
        query: str,
        max_results: int = 10,
        time_filter: Optional[str] = None,
        domain_filter: Optional[str] = None,
    ) -> list[SearchResult]:
        """Execute search by scraping DuckDuckGo HTML."""
        try:
            import httpx
            from bs4 import BeautifulSoup
        except ImportError:
            logger.warning("httpx and beautifulsoup4 required for scraper fallback")
            return []

        # Build search URL
        search_query = query
        if domain_filter:
            search_query = f"site:{domain_filter} {query}"

        # DuckDuckGo HTML search URL
        url = "https://html.duckduckgo.com/html/"
        params = {"q": search_query}

        # Add time filter if specified
        if time_filter:
            # DuckDuckGo uses df parameter for time
            time_map = {"d": "d", "w": "w", "m": "m", "y": "y"}
            if time_filter in time_map:
                params["df"] = time_map[time_filter]

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    data=params,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    },
                    timeout=30.0,
                )
                response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            results = []
            # Find result divs
            for result_div in soup.select(".result"):
                if len(results) >= max_results:
                    break

                # Extract title and URL
                title_elem = result_div.select_one(".result__a")
                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)
                url_href = title_elem.get("href", "")

                # Extract snippet
                snippet_elem = result_div.select_one(".result__snippet")
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

                if title and url_href:
                    results.append(
                        SearchResult(title=title, url=url_href, snippet=snippet)
                    )

            return results

        except Exception as e:
            logger.warning(f"Scraper fallback failed: {e}")
            return []


# TTL cache for search results
_search_cache: dict[tuple, tuple[list[SearchResult], float]] = {}
_CACHE_TTL_SECONDS = 300  # 5 minutes


def _clean_expired_cache() -> None:
    """Remove expired entries from cache."""
    now = time.time()
    expired = [k for k, (_, ts) in _search_cache.items() if now - ts > _CACHE_TTL_SECONDS]
    for k in expired:
        del _search_cache[k]


class WebSearchTool(BaseTool):
    """Tool for searching the web."""

    name = "web_search"
    description = "Search the web and return relevant results with titles, URLs, and snippets."
    parameters_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
            "max_results": {
                "type": "integer",
                "description": "Maximum results (default: 10)",
                "default": 10,
            },
            "time_filter": {
                "type": "string",
                "enum": ["day", "week", "month", "year"],
                "description": "Filter by time period",
            },
            "domain_filter": {
                "type": "string",
                "description": "Restrict to domain (e.g., github.com)",
            },
        },
        "required": ["query"],
    }

    def __init__(self) -> None:
        """Initialize with default providers."""
        self._primary_provider = DuckDuckGoProvider()
        self._fallback_provider = ScraperFallbackProvider()

    async def execute(self, params: dict, context: AgentContext) -> ToolResult:
        """Execute web search."""
        start_time = time.time()

        query = params.get("query", "")
        max_results = params.get("max_results", 10)
        time_filter_input = params.get("time_filter")
        domain_filter = params.get("domain_filter")

        # Map time_filter values: day->d, week->w, month->m, year->y
        time_filter_map = {"day": "d", "week": "w", "month": "m", "year": "y"}
        time_filter = time_filter_map.get(time_filter_input) if time_filter_input else None

        # Check cache
        cache_key = (query, max_results, time_filter, domain_filter)
        _clean_expired_cache()

        if cache_key in _search_cache:
            cached_results, _ = _search_cache[cache_key]
            logger.debug(f"Cache hit for query: {query}")
            duration_ms = (time.time() - start_time) * 1000
            return ToolResult.success_result(
                tool_call_id="",
                data=[
                    {"title": r.title, "url": r.url, "snippet": r.snippet}
                    for r in cached_results
                ],
                duration_ms=duration_ms,
            )

        # Try primary provider
        results: list[SearchResult] = []
        try:
            results = await self._primary_provider.search(
                query=query,
                max_results=max_results,
                time_filter=time_filter,
                domain_filter=domain_filter,
            )
            logger.debug(f"DuckDuckGo returned {len(results)} results")
        except Exception as e:
            logger.warning(f"DuckDuckGo provider failed: {e}, trying fallback")
            try:
                results = await self._fallback_provider.search(
                    query=query,
                    max_results=max_results,
                    time_filter=time_filter,
                    domain_filter=domain_filter,
                )
                logger.debug(f"Scraper fallback returned {len(results)} results")
            except Exception as fallback_error:
                logger.error(f"Both providers failed: {fallback_error}")
                duration_ms = (time.time() - start_time) * 1000
                return ToolResult.failure_result(
                    tool_call_id="",
                    error=f"Search failed: {str(e)}",
                    duration_ms=duration_ms,
                )

        # Cache results
        _search_cache[cache_key] = (results, time.time())

        duration_ms = (time.time() - start_time) * 1000
        return ToolResult.success_result(
            tool_call_id="",
            data=[
                {"title": r.title, "url": r.url, "snippet": r.snippet}
                for r in results
            ],
            duration_ms=duration_ms,
        )
