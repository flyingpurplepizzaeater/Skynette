# Codebase Concerns

**Analysis Date:** 2026-01-17

## Tech Debt

**AI Hub Wizard Incomplete Tab Switching:**
- Issue: Multiple TODO comments indicate tab switching after wizard completion is not implemented
- Files: `src/ui/views/ai_hub.py` (lines 405, 442)
- Impact: Users complete wizard but don't automatically navigate to the providers tab
- Fix approach: Implement Flet Tabs navigation by setting the selected_index on the parent Tabs control

**API Key Storage in Memory During Wizard:**
- Issue: Provider configs are stored in plain memory (`self.provider_configs`) before completion
- Files: `src/ui/views/ai_hub.py` (line 390-394)
- Impact: API keys exist in memory temporarily; not using secure keyring until wizard completes
- Fix approach: Store keys to keyring immediately upon input, not just on wizard completion

**Provider Connection Testing Not Implemented:**
- Issue: `_test_provider_connection` method is a stub that only prints
- Files: `src/ui/views/ai_hub.py` (line 396-399)
- Impact: Users cannot verify API keys work before completing setup
- Fix approach: Implement actual API test calls for each provider type

**Build Script Platform TODOs:**
- Issue: NSIS/Inno Setup for Windows and AppImage for Linux not yet implemented
- Files: `scripts/build.py` (lines 41, 55)
- Impact: Distribution packaging incomplete for production releases
- Fix approach: Add Windows installer script (NSIS recommended) and Linux AppImage support

**Hardcoded Provider List in Security Module:**
- Issue: `list_stored_providers()` uses hardcoded list of known providers
- Files: `src/ai/security.py` (line 105)
- Impact: New providers added dynamically won't appear in listing
- Fix approach: Store provider names in a registry or scan keyring for SERVICE_NAME entries

## Known Bugs

**Bare Exception in Workflow Deletion:**
- Symptoms: Silent failure when loading workflow for deletion confirmation
- Files: `src/ui/app.py` (line 2338)
- Trigger: Delete workflow when workflow file is corrupted or inaccessible
- Workaround: Error is caught but workflow name shows "Unknown Workflow"

**E2E Tests Navigation Broken:**
- Symptoms: Multiple E2E tests skipped due to "Navigation infrastructure needs fixing"
- Files: `tests/e2e/test_usage_dashboard.py` (lines 7, 33, 151, 298)
- Trigger: Attempting to navigate to AI Hub in E2E tests
- Workaround: Tests are currently skipped with `@pytest.mark.skip`

## Security Considerations

**Shell Execution Node Allows Arbitrary Commands:**
- Risk: The RunShellCommandNode executes user-provided shell commands with `shell=True`
- Files: `src/core/nodes/coding/execution.py` (lines 291-311)
- Current mitigation: Timeout prevents runaway processes; documented as intentional (`nosec B602`)
- Recommendations:
  - Add command allowlist/blocklist option
  - Add sandboxing option (Docker container execution)
  - Add audit logging for executed commands

**Expression Parser Exposes Environment Variables:**
- Risk: `$env.VAR_NAME` syntax allows workflows to read any environment variable
- Files: `src/core/expressions/parser.py` (lines 220-224)
- Current mitigation: None - any env var can be read
- Recommendations:
  - Add allowlist for which env vars can be accessed
  - Log env var access for auditing
  - Consider requiring explicit opt-in for env access

**Credential Vault Uses Machine-Based Key Derivation:**
- Risk: Credentials tied to machine identity, not user-specific
- Files: `src/data/credentials.py` (lines 61-86)
- Current mitigation: PBKDF2 with 480000 iterations; comment acknowledges this is "NOT high security"
- Recommendations:
  - Consider hardware-backed key storage (TPM, Secure Enclave) for production
  - Add optional user passphrase for additional security
  - Document security model clearly for users

**Plugin System Executes Remote Code:**
- Risk: Plugins downloaded from GitHub/npm execute Python code in application context
- Files: `src/plugins/manager.py` (entire file)
- Current mitigation: None - plugins have full access
- Recommendations:
  - Add plugin signing/verification
  - Add permission system for plugins
  - Sandbox plugin execution
  - Add security warnings before plugin installation

**Webhook Authentication Values Stored in Database:**
- Risk: Webhook auth secrets (API keys, HMAC secrets) stored in SQLite
- Files: `src/core/webhooks/manager.py` (line 43 - `auth_value` field)
- Current mitigation: Stored encrypted via credential vault
- Recommendations: Ensure auth_value encryption at rest; add secret rotation support

## Performance Bottlenecks

**Main App File Size:**
- Problem: `src/ui/app.py` is 2393 lines - monolithic and hard to maintain
- Files: `src/ui/app.py`
- Cause: All app views, handlers, and state managed in single class
- Improvement path:
  - Extract views into separate view classes (already partially done for some views)
  - Create separate state management module
  - Move dialog builders to `src/ui/dialogs/`

**Test File Size:**
- Problem: `tests/unit/test_app_nodes.py` is 6900 lines - slow to parse/run
- Files: `tests/unit/test_app_nodes.py`
- Cause: All app node tests in single file
- Improvement path: Split into per-integration test files (test_slack_nodes.py, test_github_nodes.py, etc.)

**Expression Parser Re-instantiation:**
- Problem: Although singleton pattern exists, individual evaluations create regex matches repeatedly
- Files: `src/core/expressions/parser.py`
- Cause: Regex pattern compiled at class level but used per-evaluation
- Improvement path: Consider caching parsed expression ASTs for repeated use

## Fragile Areas

**AI Hub View:**
- Files: `src/ui/views/ai_hub.py` (1669 lines)
- Why fragile: Complex wizard state management, multiple nested tabs, async model downloads
- Safe modification: Test wizard flow end-to-end; ensure tab state is preserved on updates
- Test coverage: E2E tests exist but some are skipped; unit test coverage limited

**Workflow Executor:**
- Files: `src/core/workflow/executor.py`
- Why fragile: Handles node execution, error recovery, resume points, variable passing
- Safe modification: Run full integration test suite; test resume functionality specifically
- Test coverage: `tests/unit/test_workflow_executor.py` exists with DebugExecutor tests

**Plugin Manager Dynamic Loading:**
- Files: `src/plugins/manager.py` (796 lines)
- Why fragile: Dynamic Python module loading, path manipulation, external downloads
- Safe modification: Test with both valid and malformed plugins; test uninstall/reinstall cycles
- Test coverage: `tests/unit/test_plugin_manager.py` exists

**Updater Self-Replacement Logic:**
- Files: `src/updater.py` (lines 236-255)
- Why fragile: Renames running executable, copies new version over - Windows-specific issues
- Safe modification: Test on all target platforms; ensure rollback on failure
- Test coverage: `tests/unit/test_updater.py` exists but may not test actual file operations

## Scaling Limits

**SQLite Single-File Storage:**
- Current capacity: All data (workflows, credentials, settings, executions) in one SQLite file
- Limit: SQLite concurrent write contention; single-user assumption
- Scaling path:
  - Already designed for single-user desktop use
  - For multi-user: migrate to PostgreSQL with connection pooling

**In-Memory Workflow Execution:**
- Current capacity: All node outputs held in memory during execution
- Limit: Large data processing (e.g., processing many files) can exhaust memory
- Scaling path: Add streaming/chunked processing option for data-heavy nodes

## Dependencies at Risk

**Flet UI Framework (v0.25.0+):**
- Risk: Flet is relatively young; API may change between versions
- Impact: UI code could break on major Flet updates
- Migration plan: Pin to specific version; test thoroughly before upgrading

**llama-cpp-python (optional):**
- Risk: Native compilation required; platform-specific issues common
- Impact: Local model execution may fail on some systems
- Migration plan: Make truly optional; graceful fallback to API-only mode

## Missing Critical Features

**Workflow Version History:**
- Problem: No version control for workflow changes
- Blocks: Users cannot rollback workflow edits; no audit trail

**Rate Limiting for Webhook Endpoints:**
- Problem: Webhook server has no rate limiting
- Blocks: Vulnerable to denial-of-service; could trigger excessive workflow executions

**Graceful Shutdown Handling:**
- Problem: Running workflows may not complete gracefully on app close
- Blocks: Could leave workflows in inconsistent state; data loss risk

## Test Coverage Gaps

**UI Component Unit Tests:**
- What's not tested: Most Flet UI components lack unit tests
- Files: `src/ui/views/*.py`, `src/ui/components/*.py`
- Risk: UI changes could introduce regressions undetected
- Priority: Medium - E2E tests provide some coverage

**Error Handler Decorators:**
- What's not tested: `@safe_async`, `@retry` decorators in `src/core/errors/handlers.py`
- Files: `src/core/errors/handlers.py`
- Risk: Error suppression could hide bugs
- Priority: High - core infrastructure

**RAG Service Integration:**
- What's not tested: Full RAG pipeline with real embeddings
- Files: `src/rag/service.py`
- Risk: Embedding/query mismatches in production
- Priority: High - core AI feature

**Webhook HMAC Validation:**
- What's not tested: HMAC signature validation edge cases
- Files: `src/core/webhooks/manager.py`
- Risk: Invalid signatures could be accepted
- Priority: High - security-critical

**Agent System:**
- What's not tested: Supervisor/agent coordination, tool execution
- Files: `src/core/agents/base.py`, `src/core/agents/supervisor.py`
- Risk: Agent loops, infinite recursion, LLM error handling
- Priority: Medium - newer feature

---

*Concerns audit: 2026-01-17*
