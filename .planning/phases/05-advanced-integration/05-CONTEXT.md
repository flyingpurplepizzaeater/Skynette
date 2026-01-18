# Phase 5: Advanced Integration - Context

**Gathered:** 2026-01-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Code editor integrates with workflow automation and codebase knowledge. Users can edit workflow scripts in the editor, ask AI questions informed by their codebase context (RAG), and run code snippets within workflows. Includes comprehensive E2E testing and security audit.

</domain>

<decisions>
## Implementation Decisions

### Workflow-Editor Bridge
- Support all three formats: JSON (current), YAML, and Python DSL
- User can choose format when creating/editing workflows
- Split view: code on left, visual node graph on right (synced)
- Live sync between code and visual — changes in either immediately update the other

### RAG Scope & Queries
- Index all code files with recognized extensions (.py, .js, .ts, .md, etc.)
- On-demand source visibility — collapsed "Sources" section user can expand
- AI retrieval is automatic when codebase context is relevant (smart activation)

### Code Execution Node
- Support any language with an interpreter installed on the system
- User-configurable timeout per node (with sensible default)
- Full access to workflow variables — code can read and write them

### Testing Strategy
- E2E tests cover all major features from all phases, plus error paths
- Security audit covers: API key exposure, code execution sandbox, input validation
- 90%+ test coverage target
- Full CI gate — all tests must pass before code is considered complete

### Claude's Discretion
- Workflow file location in editor tree (dedicated folder vs virtual node)
- RAG re-indexing strategy (incremental on save, background periodic, or hybrid)
- Output capture approach for code execution (stdout + return value recommended)
- Specific E2E test framework choice

</decisions>

<specifics>
## Specific Ideas

- Live sync between code and visual workflow should feel instant — no perceptible lag
- Sources section in RAG responses should show file names and relevant snippets
- Code execution should feel like running a script locally — familiar to developers

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 05-advanced-integration*
*Context gathered: 2026-01-18*
