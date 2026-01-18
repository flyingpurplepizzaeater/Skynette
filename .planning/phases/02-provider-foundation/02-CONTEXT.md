# Phase 2: Provider Foundation - Context

**Gathered:** 2026-01-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Users can access Gemini, Grok, and improved Ollama alongside existing providers. This phase implements the provider integrations (google-genai SDK, xai-sdk), connection status for Ollama, rate limit handling, and streaming failure recovery. Adding new AI features (completions, code assistance) belongs in later phases.

</domain>

<decisions>
## Implementation Decisions

### Provider UX
- Show all providers in model picker, grayed if unconfigured — users see what's possible
- All models in one flat list (local and cloud mixed), badge indicates local/cloud
- Claude's Discretion: API key configuration flow (inline vs settings page)
- Claude's Discretion: What happens when user selects unconfigured model

### Error Experience
- Keep partial content when streaming fails + show "[Response interrupted]" marker
- No auto-retry — show error immediately with manual Retry button
- Error messages are user-friendly with "Show details" expandable section (HTTP code, error body)
- Claude's Discretion: Rate limit notification style (toast vs inline)

### Status & Feedback
- Show usage meter when approaching rate limits (e.g., "80% of quota used")
- Ollama model discovery: auto-refresh on connect AND manual refresh button available
- Claude's Discretion: Ollama connection status placement (header vs model picker)
- Claude's Discretion: Rate limit usage info location

### Provider Consistency
- Badge capabilities per model (streaming ✓, vision ✓, function calling ✗)
- Provider logos and colors for visual identity (Gemini, Grok, Ollama each distinct)
- When switching providers mid-conversation, ask user: "Continue conversation or start fresh?"
- Claude's Discretion: Response format normalization

### Claude's Discretion
- API key configuration flow
- Unconfigured model selection behavior
- Rate limit notification style
- Ollama status indicator placement
- Rate limit usage info location
- Response format normalization across providers

</decisions>

<specifics>
## Specific Ideas

- Partial responses should be preserved even on failure — user typed for context, don't lose what came back
- Usage meter gives users control over their API costs — no surprise limits
- Provider branding helps users know what they're using at a glance

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 02-provider-foundation*
*Context gathered: 2026-01-18*
