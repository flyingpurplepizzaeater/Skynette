# Phase 10: Built-in Tools - Research

**Researched:** 2026-01-21
**Domain:** Agent tool infrastructure (web search, browser automation, filesystem, code execution, GitHub)
**Confidence:** HIGH

## Summary

This phase implements concrete agent capabilities as BaseTool subclasses that register with the existing ToolRegistry. The codebase already has a mature tool infrastructure from Phase 9 (MCP Integration) - `BaseTool`, `ToolRegistry`, `ToolResult`, and `AgentContext` are well-defined patterns to follow.

Key insight: Built-in tools should be native `BaseTool` subclasses (not MCP tools) since they run locally without external server processes. This provides better performance, simpler error handling, and consistent integration with the existing codebase patterns.

The standard stack is clear: `duckduckgo-search` (renamed to `ddgs`) for web search with fallback scraping, `playwright` with `playwright-stealth` for browser automation, `PyGithub` for GitHub API, existing `pathlib` + `aiofiles` for filesystem, and `subprocess`/`asyncio.create_subprocess_exec` for code execution building on existing sandbox infrastructure.

**Primary recommendation:** Implement tools as BaseTool subclasses following the MockTool pattern, registering them in `_load_builtin_tools()` of ToolRegistry.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| duckduckgo-search | >=8.0.0 | Web search API | No API key required, comprehensive features, actively maintained |
| playwright | >=1.49.0 | Browser automation | Cross-browser support, async API, Microsoft-backed |
| playwright-stealth | >=1.0.0 | Bot detection evasion | Port of puppeteer-stealth, patches automation signals |
| PyGithub | >=2.8.0 | GitHub API client | Official-style library, typed, comprehensive API coverage |
| aiofiles | >=25.1.0 | Async file I/O | Already in requirements.txt (>=23.0.0), delegates to thread pool |
| psutil | >=7.0.0 | Process/resource monitoring | Cross-platform, provides resource usage stats |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| httpx | >=0.27.0 | HTTP client | Already in requirements.txt - for SerpAPI/Bing fallback |
| GitPython | >=3.1.43 | Local git operations | When local repo manipulation needed (push requires auth) |
| beautifulsoup4 | >=4.12.0 | HTML parsing | For search result scraping fallback |
| tenacity | >=8.0.0 | Retry logic | Exponential backoff for API rate limits (already in codebase) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| duckduckgo-search | SerpAPI/Serper | API key required, cost, but higher reliability |
| playwright | selenium | Playwright has better async support, auto-wait, cross-browser |
| PyGithub | gh CLI subprocess | CLI requires separate installation, but simpler auth flow |

**Installation:**
```bash
pip install duckduckgo-search playwright playwright-stealth PyGithub psutil beautifulsoup4
playwright install chromium  # Install browser binary
```

## Architecture Patterns

### Recommended Project Structure
```
src/agent/tools/
    __init__.py             # Exports all built-in tools
    base.py                 # Shared utilities (path validation, etc.)
    web_search.py           # WebSearchTool
    browser.py              # BrowserTool (Playwright wrapper)
    filesystem.py           # FileReadTool, FileWriteTool, FileDeleteTool
    code_execution.py       # CodeExecutionTool
    github.py               # GitHubTool (create repo, push, etc.)
```

### Pattern 1: BaseTool Subclass Pattern
**What:** Each tool is a BaseTool subclass with name, description, parameters_schema, and async execute()
**When to use:** All built-in tools
**Example:**
```python
# Source: Existing codebase pattern from src/agent/registry/mock_tool.py
from src.agent.models.tool import ToolResult
from src.agent.registry.base_tool import AgentContext, BaseTool


class WebSearchTool(BaseTool):
    """Search the web via DuckDuckGo."""

    name = "web_search"
    description = "Search the web and return relevant results with titles, URLs, and snippets."
    parameters_schema = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query"
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum results to return (default: 10)",
                "default": 10
            },
            "time_filter": {
                "type": "string",
                "enum": ["day", "week", "month", "year", None],
                "description": "Filter by time period"
            }
        },
        "required": ["query"]
    }

    async def execute(self, params: dict, context: AgentContext) -> ToolResult:
        """Execute web search."""
        import time
        start = time.perf_counter()

        query = params.get("query", "")
        max_results = params.get("max_results", 10)
        time_filter = params.get("time_filter")

        try:
            results = await self._search(query, max_results, time_filter)
            duration_ms = (time.perf_counter() - start) * 1000
            return ToolResult.success_result(
                tool_call_id=context.session_id,
                data=results,
                duration_ms=duration_ms
            )
        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000
            return ToolResult.failure_result(
                tool_call_id=context.session_id,
                error=str(e),
                duration_ms=duration_ms
            )
```

### Pattern 2: Filesystem Path Validation
**What:** Validate all file paths against allowlist using pathlib.resolve()
**When to use:** Any filesystem operation
**Example:**
```python
# Source: OpenStack security guidelines + Python pathlib docs
from pathlib import Path


class FileSystemValidator:
    """Validates file paths against security constraints."""

    def __init__(self, allowed_paths: list[str], blocked_patterns: list[str]):
        self.allowed_paths = [Path(p).resolve() for p in allowed_paths]
        self.blocked_patterns = blocked_patterns  # e.g., [".env", "credentials", ".git"]

    def validate(self, path_str: str) -> tuple[bool, str]:
        """Validate path is allowed. Returns (is_valid, error_message)."""
        try:
            path = Path(path_str).resolve()
        except Exception as e:
            return False, f"Invalid path: {e}"

        # Check blocked patterns
        for pattern in self.blocked_patterns:
            if pattern in str(path):
                return False, f"Path contains blocked pattern: {pattern}"

        # Check allowlist using is_relative_to (Python 3.9+)
        for allowed in self.allowed_paths:
            if path.is_relative_to(allowed):
                return True, ""

        return False, f"Path not in allowed directories"
```

### Pattern 3: Provider Abstraction for Web Search
**What:** Abstract interface with multiple backend implementations
**When to use:** Web search to allow fallback/switching providers
**Example:**
```python
# Source: CONTEXT.md requirement for abstracted provider interface
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str


class SearchProvider(ABC):
    """Abstract search provider interface."""

    @abstractmethod
    async def search(
        self,
        query: str,
        max_results: int = 10,
        time_filter: str | None = None,
        domain_filter: str | None = None,
    ) -> list[SearchResult]:
        pass


class DuckDuckGoProvider(SearchProvider):
    """DuckDuckGo search via duckduckgo-search library."""

    async def search(self, query: str, **kwargs) -> list[SearchResult]:
        from duckduckgo_search import DDGS
        import asyncio

        def _search():
            with DDGS() as ddgs:
                timelimit = kwargs.get("time_filter")  # d, w, m, y
                results = ddgs.text(
                    query,
                    max_results=kwargs.get("max_results", 10),
                    timelimit=timelimit
                )
                return [
                    SearchResult(
                        title=r.get("title", ""),
                        url=r.get("href", ""),
                        snippet=r.get("body", "")
                    )
                    for r in results
                ]

        # Run sync library in thread pool
        return await asyncio.to_thread(_search)
```

### Pattern 4: Browser Context Management
**What:** Reusable browser instance with per-operation pages
**When to use:** Browser automation tool
**Example:**
```python
# Source: Playwright docs + playwright-stealth usage
from contextlib import asynccontextmanager


class BrowserManager:
    """Manages browser lifecycle for automation tool."""

    def __init__(self):
        self._playwright = None
        self._browser = None

    async def ensure_browser(self, headless: bool = True):
        """Ensure browser is running, start if needed."""
        if self._browser is None:
            from playwright.async_api import async_playwright
            from playwright_stealth import Stealth

            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=headless,
                args=["--disable-blink-features=AutomationControlled"]
            )
        return self._browser

    @asynccontextmanager
    async def new_page(self, headless: bool = True):
        """Create a new page with stealth applied."""
        from playwright_stealth import Stealth

        browser = await self.ensure_browser(headless)
        context = await browser.new_context()

        # Apply stealth
        stealth = Stealth()
        await stealth.apply_stealth_async(context)

        page = await context.new_page()
        try:
            yield page
        finally:
            await page.close()
            await context.close()
```

### Anti-Patterns to Avoid
- **Creating new browser instances per operation:** Kill performance. Reuse browser, create pages.
- **String concatenation for file paths:** Use pathlib for cross-platform safety.
- **Blocking subprocess calls:** Use asyncio.create_subprocess_exec for async execution.
- **Hardcoded allowed paths:** Use configuration - user sets allowed directories.
- **Ignoring timeouts:** All external operations (web, subprocess) need timeouts.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Web search scraping | Custom DuckDuckGo scraper | duckduckgo-search library | Handles rate limits, parsing changes, proxies |
| Browser fingerprint evasion | Manual navigator patches | playwright-stealth | Maintained set of evasion techniques |
| GitHub API auth | Custom OAuth flow | PyGithub with PAT | Handles token refresh, rate limits, pagination |
| Path traversal prevention | Regex-based filtering | pathlib.resolve() + is_relative_to() | Handles symlinks, edge cases |
| Process resource limits | Manual cgroup setup | Existing DockerSandbox from Phase 9 | Already implemented for MCP |
| Async file I/O | Custom thread pool | aiofiles library | Well-tested, proper async interface |

**Key insight:** The codebase already has subprocess execution patterns in `src/core/nodes/coding/execution.py` and sandbox infrastructure in `src/agent/mcp/sandbox/`. Extend these rather than rebuilding.

## Common Pitfalls

### Pitfall 1: Sync Library in Async Context
**What goes wrong:** Blocking the event loop with synchronous library calls
**Why it happens:** duckduckgo-search and some GitPython operations are synchronous
**How to avoid:** Use `asyncio.to_thread()` to run sync code in thread pool
**Warning signs:** Agent becomes unresponsive during tool execution

### Pitfall 2: Unrestricted File Access
**What goes wrong:** Tool can read/write arbitrary system files
**Why it happens:** Missing or incomplete path validation
**How to avoid:** Always validate against resolved allowlist, check every operation
**Warning signs:** Tool can access files outside configured directories

### Pitfall 3: Browser Resource Leaks
**What goes wrong:** Memory grows unbounded, zombie browser processes
**Why it happens:** Pages/contexts not closed properly, especially on errors
**How to avoid:** Use context managers, ensure cleanup in finally blocks
**Warning signs:** System memory usage grows over time, orphan chrome processes

### Pitfall 4: Missing Timeouts
**What goes wrong:** Operations hang indefinitely, agent stuck
**Why it happens:** External services (web, GitHub) can be slow/unresponsive
**How to avoid:** Set explicit timeouts on all external operations (web: 30s, browser: 30s per navigation, subprocess: per CONTEXT.md 5 min default)
**Warning signs:** Agent unresponsive, no error returned

### Pitfall 5: Rate Limit Exhaustion
**What goes wrong:** APIs block requests, searches fail
**Why it happens:** Too many rapid requests to DuckDuckGo or GitHub
**How to avoid:** Implement request caching, respect rate limits, use tenacity for backoff
**Warning signs:** HTTP 429 responses, "rate limited" errors

### Pitfall 6: Insecure Code Execution
**What goes wrong:** Arbitrary code runs with full system access
**Why it happens:** No sandboxing for code execution
**How to avoid:** Use existing DockerSandbox from Phase 9, network disabled by default (per CONTEXT.md)
**Warning signs:** Code can access network, read arbitrary files

## Code Examples

Verified patterns from official sources:

### DuckDuckGo Search
```python
# Source: https://pypi.org/project/duckduckgo-search/
from duckduckgo_search import DDGS

# Basic text search
results = DDGS().text("python programming", max_results=5)
# Returns list of dicts with: title, href, body

# With filters
results = DDGS().text(
    keywords="AI news",
    region="us-en",           # Regional results
    safesearch="moderate",    # on, moderate, off
    timelimit="w",           # d=day, w=week, m=month, y=year
    max_results=10
)

# Site-restricted search (handled in query)
results = DDGS().text("site:github.com playwright python", max_results=5)
```

### Playwright with Stealth
```python
# Source: https://pypi.org/project/playwright-stealth/
import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def scrape_page(url: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()

        # Apply stealth to all pages in context
        stealth = Stealth()
        await stealth.apply_stealth_async(context)

        page = await context.new_page()
        await page.goto(url, timeout=30000)  # 30s timeout

        # Screenshot on navigation
        await page.screenshot(path="page.png")

        # Extract data
        title = await page.title()
        content = await page.content()

        await browser.close()
        return {"title": title, "html": content}
```

### PyGithub Repository Creation
```python
# Source: https://pypi.org/project/PyGithub/
from github import Github, Auth

# Authenticate with PAT
auth = Auth.Token("ghp_xxxxxxxxxxxx")
g = Github(auth=auth)

# Create repository
user = g.get_user()
repo = user.create_repo(
    name="new-repo",
    description="Created via PyGithub",
    private=False,
    auto_init=True  # Creates with README
)

# Create/update file
repo.create_file(
    path="hello.py",
    message="Add hello.py",
    content="print('Hello, World!')"
)

# Push requires local git operations - use subprocess or GitPython
g.close()
```

### Filesystem with Backup
```python
# Source: CONTEXT.md requirement + Python pathlib docs
import shutil
from datetime import datetime
from pathlib import Path

def backup_before_modify(path: Path) -> Path | None:
    """Create timestamped backup before modification."""
    if not path.exists():
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = path.with_suffix(f".{timestamp}.bak")
    shutil.copy2(path, backup_path)
    return backup_path

def cleanup_old_backups(original_path: Path, keep: int = 5):
    """Remove old backups, keeping most recent N."""
    pattern = f"{original_path.stem}.*.bak"
    backups = sorted(original_path.parent.glob(pattern), reverse=True)
    for old_backup in backups[keep:]:
        old_backup.unlink()
```

### Code Execution with Resource Tracking
```python
# Source: Python subprocess docs + psutil
import asyncio
import time
from dataclasses import dataclass


@dataclass
class ExecutionResult:
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool


async def execute_code(
    command: list[str],
    timeout: int = 300,  # 5 min default per CONTEXT.md
    cwd: str | None = None,
    env: dict | None = None,
) -> ExecutionResult:
    """Execute code with timeout and capture output."""
    start = time.perf_counter()

    proc = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd,
        env=env,
    )

    try:
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(),
            timeout=timeout
        )
        duration = time.perf_counter() - start
        return ExecutionResult(
            exit_code=proc.returncode or 0,
            stdout=stdout.decode("utf-8", errors="replace"),
            stderr=stderr.decode("utf-8", errors="replace"),
            duration_seconds=duration,
            timed_out=False
        )
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        duration = time.perf_counter() - start
        return ExecutionResult(
            exit_code=-1,
            stdout="",
            stderr=f"Execution timed out after {timeout} seconds",
            duration_seconds=duration,
            timed_out=True
        )
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| puppeteer-extra-plugin-stealth | playwright-stealth | 2023 | Python-native, maintained |
| duckduckgo-search | ddgs (package rename) | 2024 | Same library, new package name |
| requests for HTTP | httpx (async) | 2022 | Better async support, HTTP/2 |
| os.path.join | pathlib | Python 3.4+ | Object-oriented, safer |

**Deprecated/outdated:**
- **selenium standalone:** Playwright preferred for new projects (better async, auto-wait)
- **requests library for async:** Use httpx - already in project dependencies
- **PyGithub without Auth class:** Old direct token passing deprecated

## Open Questions

Things that couldn't be fully resolved:

1. **GitHub Authentication Flow**
   - What we know: PyGithub supports PAT authentication, gh CLI uses GITHUB_TOKEN env var
   - What's unclear: Should we support OAuth device flow for better UX? How to handle token storage securely?
   - Recommendation: Start with PAT via keyring (existing pattern), defer OAuth to later enhancement

2. **Search Result Caching Strategy**
   - What we know: DuckDuckGo has rate limits, caching helps
   - What's unclear: Cache duration? Per-query vs semantic similarity? Storage location?
   - Recommendation: Simple TTL cache (5 min) in memory initially, expand later if needed

3. **Browser Session Persistence**
   - What we know: Can save/restore browser context storage
   - What's unclear: How to handle cookies/auth across sessions? Security implications?
   - Recommendation: Ephemeral contexts by default, optional persistence as parameter

4. **Sandbox Technology for Code Execution**
   - What we know: DockerSandbox exists from Phase 9, subprocess with timeout is simpler
   - What's unclear: Should built-in code execution use Docker? Performance impact?
   - Recommendation: Use subprocess with timeout for trusted/simple cases, Docker option for untrusted (per CONTEXT.md: network disabled by default)

## Sources

### Primary (HIGH confidence)
- Existing codebase patterns: `src/agent/registry/base_tool.py`, `tool_registry.py`, `mock_tool.py`
- Existing codebase: `src/agent/mcp/sandbox/docker_sandbox.py` (code execution sandboxing)
- Existing codebase: `src/core/nodes/coding/execution.py` (subprocess patterns)
- Existing codebase: `src/core/nodes/data/read_file.py`, `write_file.py` (file patterns)
- [duckduckgo-search PyPI](https://pypi.org/project/duckduckgo-search/) - API documentation
- [Playwright Python docs](https://playwright.dev/python/docs/intro) - Official documentation
- [PyGithub docs](https://pygithub.readthedocs.io/en/stable/) - Official documentation
- [playwright-stealth PyPI](https://pypi.org/project/playwright-stealth/) - Usage documentation

### Secondary (MEDIUM confidence)
- [ZenRows Playwright Stealth Guide](https://www.zenrows.com/blog/playwright-stealth) - Stealth patterns
- [OpenStack Path Traversal Prevention](https://security.openstack.org/guidelines/dg_using-file-paths.html) - Security patterns
- [Python httpx Async docs](https://www.python-httpx.org/async/) - HTTP client patterns

### Tertiary (LOW confidence)
- Web search results for current library versions and best practices
- Medium articles on patterns (verified against official docs)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries are well-documented, active, and verified against official sources
- Architecture: HIGH - Based on existing codebase patterns (BaseTool, ToolRegistry)
- Pitfalls: MEDIUM - Based on general async/web automation experience, needs validation in practice

**Research date:** 2026-01-21
**Valid until:** 2026-02-21 (30 days - stable domain, libraries are mature)
