# Phase 1: Stability & Audit - Context

**Gathered:** 2026-01-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Fix existing features — AI Chat, Model Management, Workflow Builder — before building new capabilities. Ensure reliable operation of current functionality and refactor state management to handle future complexity. This is an audit-and-fix phase, not a feature-building phase.

</domain>

<decisions>
## Implementation Decisions

### Audit approach
- Conduct audits using both manual walkthrough AND automated tests, in sequence
- Manual discovery first to find issues, then write tests to capture findings
- "Working" means full coverage: all documented features work as intended, including edge cases
- Claude's discretion on documentation format (inline TODOs, issue tracker, or audit report)
- Claude's discretion on performance profiling (note obvious issues vs active measurement)

### Fix strategy
- Claude's discretion on fix timing (fix-as-found vs batch vs hybrid)
- Claude's discretion on breaking changes (pre-release, so clean design preferred when justified)
- Claude's discretion on cleanup scope (local cleanup allowed when clearly problematic)
- Claude's discretion on dead code handling (removal preferred to reduce maintenance burden)

### State management refactor
- Refactor aggressiveness left to Claude's judgment based on what's found during audit
- All four priorities matter equally: testability, readability, performance, extensibility
- No specific pain points identified yet — this is a preemptive refactor based on AIHubView size (1669 lines)
- UI behavior preservation left to Claude's judgment (minor improvements acceptable)

### Success threshold
- **Zero known bugs** before proceeding to Phase 2
- Every fix MUST have a regression test that would catch the bug if reintroduced
- Truly unfixable issues: document clearly and defer (with justification)
- Full manual QA walkthrough required before phase completion

### Claude's Discretion
- Audit documentation format
- Performance profiling depth
- Fix timing and batching strategy
- Breaking changes when design benefits outweigh compatibility
- Cleanup scope during fixes
- Dead code handling
- Refactor architecture approach
- Minor UI improvements during refactor

</decisions>

<specifics>
## Specific Ideas

- User hasn't tested the current state management, so the refactor is preemptive based on code size metrics
- Research already identified AIHubView at 1669 lines as a concern

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-stability-audit*
*Context gathered: 2026-01-18*
