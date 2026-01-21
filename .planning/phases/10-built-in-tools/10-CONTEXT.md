# Phase 10: Built-in Tools - Context

**Gathered:** 2026-01-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Provide concrete agent capabilities for web search, browsing, filesystem operations, code execution, and GitHub integration. These are tools the agent uses to accomplish tasks — the foundational actions that make the agent useful.

</domain>

<decisions>
## Implementation Decisions

### Web Search Behavior
- Return structured snippets: title, URL, snippet text (agent parses what it needs)
- Default to 10 results per search
- Support domain filtering (site:) and time filtering (past day/week/month/year)
- Abstracted provider interface supporting multiple backends (SerpAPI, Bing, DuckDuckGo)
- Built-in scraper as fallback when API unavailable

### Browser Automation
- Headless by default, visible mode available for debugging
- 30 second default page navigation timeout
- Automatic screenshots on key actions (navigation, form submit, errors)
- Support both Playwright and Selenium as automation libraries

### Filesystem Boundaries
- User-configured allowlist for permitted directories (not hardcoded project-only)
- Automatic .bak backup before any modify or delete operation
- 50 MB maximum file size limit
- Configurable file protection levels per pattern:
  - Block: prevent modification entirely (.env, credentials, keys, system files)
  - Warn: allow but require confirmation
  - Allow: unrestricted in permitted paths

### Code Execution Sandbox
- Language-agnostic: run any language with appropriate interpreter
- 5 minute default execution timeout (configurable)
- Network disabled by default, explicit opt-in required
- Full process info output: exit code, timing, resource usage, stdout, stderr

### Claude's Discretion
- GitHub tool specifics (authentication flow, API vs CLI, operation scope)
- Search result caching strategy
- Browser session persistence approach
- Sandbox isolation technology (Docker, subprocess, etc.)

</decisions>

<specifics>
## Specific Ideas

- Search provider should degrade gracefully — if API fails, try scraper
- Browser screenshots are for debugging/audit, not primary output
- Filesystem backups should be timestamped and auto-cleaned after success
- Code execution should feel like running in a terminal — full visibility

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 10-built-in-tools*
*Context gathered: 2026-01-21*
