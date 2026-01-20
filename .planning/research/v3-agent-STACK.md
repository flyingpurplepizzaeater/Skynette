# Stack Research: v3.0 Agent Capabilities

**Project:** Skynette v3.0 - Agent Mode
**Researched:** 2026-01-20
**Confidence:** HIGH (verified via official documentation and PyPI)

## Executive Summary

This research covers the technology stack needed to add agent capabilities to Skynette: MCP integration for tool use, browser automation for web tasks, an agent execution loop, and web search APIs. The recommendations prioritize libraries that:

1. Have official/stable releases (not pre-alpha)
2. Are async-native (matching Skynette's existing architecture)
3. Minimize new abstractions (build custom where frameworks add complexity)
4. Integrate well with existing multi-provider AI gateway

---

## Recommended Stack

### MCP Integration

| Technology | Version | Purpose | Rationale |
|------------|---------|---------|-----------|
| **mcp** | 1.25.0 | MCP client SDK | Official Anthropic SDK. Stable v1.x recommended for production (v2 is pre-alpha). Provides `ClientSession`, `StdioServerParameters`, and transport handling. |

**Installation:**
```bash
pip install "mcp[cli]>=1.25.0"
```

**Key Classes:**
- `ClientSession` - Manages connection to MCP servers
- `StdioServerParameters` - Configuration for stdio transport
- `stdio_client` - Factory for stdio connections
- `list_tools()` - Discover available tools
- `call_tool()` - Execute tool calls

**Transport Support:**
- **Stdio** - Local process communication (most common)
- **Streamable HTTP** - Remote server connections
- **SSE** - Server-sent events for web clients

**Why NOT FastMCP or mcp-use:**
- FastMCP is primarily for *building* MCP servers, not hosting/connecting to them
- mcp-use adds unnecessary abstraction over the official SDK
- The official SDK is well-documented and production-ready

---

### Browser Automation

| Technology | Version | Purpose | Rationale |
|------------|---------|---------|-----------|
| **playwright** | 1.57.0 | Browser control | Industry standard. 35-45% faster than Selenium. Native async support. Built-in headless mode. Already in Skynette's dev dependencies. |
| **browser-use** | 0.11.3 | AI-friendly browser automation | Wraps Playwright with vision-based element detection. Handles dynamic pages without brittle selectors. AI agent-optimized. |

**Installation:**
```bash
pip install playwright>=1.57.0
pip install browser-use>=0.11.3

# Post-install: download browser binaries
playwright install chromium
```

**When to Use Each:**

| Use Case | Library |
|----------|---------|
| Precise automation (known pages) | Playwright directly |
| AI agent browsing (unknown pages) | browser-use |
| Screenshot capture | Playwright |
| Form filling on dynamic sites | browser-use |
| Testing | Playwright |

**browser-use Integration:**
```python
from browser_use import Agent
from langchain_openai import ChatOpenAI

agent = Agent(
    task="Find the latest Python release",
    llm=ChatOpenAI(model="gpt-4"),
)
result = await agent.run()
```

**Playwright Direct (for precision):**
```python
from playwright.async_api import async_playwright

async with async_playwright() as p:
    browser = await p.chromium.launch(headless=True)
    page = await browser.new_page()
    await page.goto("https://example.com")
    content = await page.content()
    await browser.close()
```

**Why NOT Selenium:**
- Selenium uses WebDriver over HTTP (slower, more overhead)
- Playwright's CDP connection is 35-45% faster
- Selenium requires separate driver management
- Playwright has better async support

---

### Agent Framework

| Technology | Version | Purpose | Rationale |
|------------|---------|---------|-----------|
| **Custom implementation** | N/A | Agent execution loop | Skynette already has multi-provider gateway. Adding a framework would duplicate this and add abstraction layers. |
| **pydantic-ai** (optional) | 1.44.0 | Structured outputs, tool validation | Only if structured output validation becomes complex. Has MCP client support built-in. |

**Recommendation: Build Custom Agent Loop**

Skynette already has:
- Multi-provider AI gateway (OpenAI, Anthropic, Gemini, Grok, Ollama)
- Async architecture
- Workflow engine

Adding LangChain/LangGraph/CrewAI would:
- Duplicate the AI provider abstraction
- Add 5+ layers of abstraction for simple customizations
- Increase dependency surface area significantly
- Make debugging harder

**Minimal Agent Loop Pattern:**
```python
class AgentLoop:
    """Simple agent loop - observe, decide, execute, repeat."""

    async def run(self, task: str, tools: list[Tool]) -> str:
        messages = [{"role": "user", "content": task}]

        while True:
            # Call LLM with tool definitions
            response = await self.ai_gateway.chat(
                messages=messages,
                tools=[t.schema for t in tools],
            )

            # Check for completion
            if response.finish_reason == "stop":
                return response.content

            # Execute tool calls
            if response.tool_calls:
                for call in response.tool_calls:
                    result = await self.execute_tool(call, tools)
                    messages.append({"role": "tool", "content": result})

                messages.append(response.to_message())
```

**When to Consider pydantic-ai:**
- Complex structured output requirements
- Need built-in retry logic for tool validation
- Want MCP integration without custom code
- Multi-agent coordination needed

**Why NOT LangChain/LangGraph:**
- Skynette already has provider abstraction
- LangChain has highest latency in benchmarks
- Framework lock-in for minimal benefit
- "5 layers of abstraction just to change a minute detail"

**Why NOT CrewAI/AutoGen:**
- Designed for multi-agent coordination (not needed for v3.0 MVP)
- Heavy dependencies
- Overkill for single-agent tool use

---

### Web Search

| Technology | Version | Purpose | Rationale |
|------------|---------|---------|-----------|
| **duckduckgo-search** | 8.1.1 | Free web search | No API key required. MIT license. Production stable. Good for development and basic search. |
| **tavily-python** | N/A | AI-optimized search | 1,000 free searches/month. Returns LLM-ready summaries. Best for production RAG. |
| **exa-py** | 2.0.2 | Semantic search | Best accuracy for AI agents. Understands meaning, not just keywords. Sub-500ms response. |

**Tiered Approach:**

| Tier | Library | Use Case | Cost |
|------|---------|----------|------|
| **Free/Dev** | duckduckgo-search | Development, testing, basic search | Free |
| **Production** | tavily-python | RAG workflows, summarized results | $0.008/search after 1K free |
| **Premium** | exa-py | Semantic search, research tasks | $0.001-0.01/search |

**Installation:**
```bash
# Free tier (always include)
pip install duckduckgo-search>=8.1.0

# Production tier (optional)
pip install tavily-python

# Premium tier (optional)
pip install exa-py>=2.0.0
```

**Usage Examples:**

```python
# DuckDuckGo (free, no API key)
from duckduckgo_search import DDGS

results = DDGS().text("Python 3.12 features", max_results=10)

# Tavily (AI-optimized)
from tavily import TavilyClient

client = TavilyClient(api_key="...")
response = client.search("Python 3.12 features")

# Exa (semantic search)
from exa_py import Exa

exa = Exa(api_key="...")
results = exa.search_and_contents("Papers about transformer architectures")
```

**Why NOT SerpAPI:**
- $0.015/search (3-15x more expensive)
- Returns raw SERP data (needs post-processing)
- Only 250 free searches/month

---

## Complete Dependencies to Add

### Core (Required for Agent Mode)

```toml
# Add to pyproject.toml [project.optional-dependencies]
agent = [
    # MCP Integration
    "mcp[cli]>=1.25.0",

    # Browser Automation
    "playwright>=1.57.0",
    "browser-use>=0.11.3",

    # Web Search (free tier)
    "duckduckgo-search>=8.1.0",
]
```

### Production (Optional Enhancements)

```toml
agent-pro = [
    "skynette[agent]",

    # Premium search APIs
    "tavily-python",
    "exa-py>=2.0.0",

    # Structured agent framework (if needed)
    "pydantic-ai>=1.44.0",
]
```

### pip install commands

```bash
# Minimal agent setup
pip install "mcp[cli]>=1.25.0" "playwright>=1.57.0" "browser-use>=0.11.3" "duckduckgo-search>=8.1.0"

# Post-install browser setup
playwright install chromium
```

---

## Not Recommended

| Technology | Why Avoid |
|------------|-----------|
| **LangChain** | Duplicates Skynette's AI gateway. Highest latency in benchmarks. Heavy abstraction. |
| **LangGraph** | Overkill for single-agent use. Graph-based orchestration not needed for v3.0. |
| **CrewAI** | Multi-agent focused. Enterprise pricing. Not needed for single-agent MVP. |
| **AutoGen** | Multi-agent focused. Microsoft ecosystem lock-in risk. |
| **Selenium** | 35-45% slower than Playwright. Separate driver management. WebDriver overhead. |
| **mcp v2.x** | Pre-alpha. v1.x recommended for production until Q1 2026. |
| **SerpAPI** | 3-15x more expensive than alternatives. Raw data requires processing. |
| **FastMCP** | For building MCP servers, not connecting to them as a host. |

---

## Architecture Integration

### How Components Connect

```
+------------------+     +------------------+     +------------------+
|   Agent Loop     |---->|   AI Gateway     |---->|   LLM Provider   |
|   (Custom)       |     |   (Existing)     |     |   (Existing)     |
+------------------+     +------------------+     +------------------+
        |
        v
+------------------+     +------------------+
|   Tool Router    |---->|   MCP Client     |---> MCP Servers (external)
|                  |     |   (mcp SDK)      |
+------------------+     +------------------+
        |
        +--------------->|   Browser Tool   |---> Playwright / browser-use
        |                +------------------+
        |
        +--------------->|   Search Tool    |---> DuckDuckGo / Tavily / Exa
                         +------------------+
```

### Existing Skynette Components to Leverage

- **AI Gateway** - Already handles multi-provider routing
- **Workflow Engine** - Can orchestrate agent tasks
- **RAG System (ChromaDB)** - Agent memory/context storage
- **Async Architecture** - All new components are async-native

---

## Version Compatibility Matrix

| Component | Min Version | Tested Version | Python Req |
|-----------|-------------|----------------|------------|
| mcp | 1.25.0 | 1.25.0 | >=3.10 |
| playwright | 1.57.0 | 1.57.0 | >=3.9 |
| browser-use | 0.11.3 | 0.11.3 | >=3.11 |
| duckduckgo-search | 8.1.0 | 8.1.1 | >=3.9 |
| pydantic-ai | 1.44.0 | 1.44.0 | >=3.10 |
| exa-py | 2.0.0 | 2.0.2 | >=3.8 |

**Skynette Python requirement:** >=3.11 (all dependencies compatible)

---

## Sources

### MCP Integration
- [Official MCP Python SDK (GitHub)](https://github.com/modelcontextprotocol/python-sdk)
- [MCP Python SDK (PyPI)](https://pypi.org/project/mcp/) - v1.25.0
- [Build an MCP Client (Official Docs)](https://modelcontextprotocol.io/docs/develop/build-client)
- [OpenAI Agents SDK MCP Integration](https://openai.github.io/openai-agents-python/mcp/)

### Browser Automation
- [Playwright (PyPI)](https://pypi.org/project/playwright/) - v1.57.0
- [browser-use (GitHub)](https://github.com/browser-use/browser-use)
- [browser-use (PyPI)](https://pypi.org/project/browser-use/) - v0.11.3
- [Playwright vs Selenium 2025 (BrowserStack)](https://www.browserstack.com/guide/playwright-vs-selenium)

### Agent Framework
- [Pydantic AI](https://ai.pydantic.dev/) - v1.44.0
- [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/)
- [A Loop Is All You Need (DEV.to)](https://dev.to/adgapar/a-loop-is-all-you-need-building-conversation-ai-agents-1039)
- [Top AI Agent Frameworks 2025 (Langfuse)](https://langfuse.com/blog/2025-03-19-ai-agent-comparison)

### Web Search
- [duckduckgo-search (PyPI)](https://pypi.org/project/duckduckgo-search/) - v8.1.1
- [Tavily Docs](https://docs.tavily.com/welcome)
- [Exa AI](https://exa.ai/) - v2.0.2
- [Best SERP API Comparison 2025 (DEV.to)](https://dev.to/ritza/best-serp-api-comparison-2025-serpapi-vs-exa-vs-tavily-vs-scrapingdog-vs-scrapingbee-2jci)
