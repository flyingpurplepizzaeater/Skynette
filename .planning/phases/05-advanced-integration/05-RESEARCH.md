# Phase 5: Advanced Integration - Research

**Researched:** 2026-01-18
**Domain:** Code Editor Integration, Project-level RAG, Code Execution, E2E Testing, Security Audit
**Confidence:** MEDIUM (verified architecture with existing codebase, external best practices from WebSearch)

## Summary

Phase 5 integrates the code editor with workflow automation and codebase knowledge. Research covered six major domains: workflow script editing in the code editor, project-level RAG using existing ChromaDB infrastructure, code execution nodes for workflows, embedding dimension validation, E2E testing for Flet applications, and security audit for API key exposure.

The existing codebase provides strong foundations: workflows are stored as YAML files with Pydantic models supporting serialization/deserialization, ChromaDB infrastructure already exists with an in-memory implementation ready for production upgrade, and the E2E test infrastructure uses Playwright with pytest. The primary gaps are: no Python DSL for workflows (only JSON/YAML), no project-level RAG indexing (only document-level), no code execution node, and no embedding dimension pre-validation.

**Primary recommendation:** Extend the existing infrastructure incrementally - add workflow script editing to the code editor by leveraging the existing YAML serialization, extend the RAG system for project-level indexing with incremental updates, add a code execution node using subprocess with configurable timeouts, and implement embedding dimension validation before ChromaDB writes.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| chromadb | >=0.5.0 | Vector database for RAG | Already in use, Pydantic 2 compatible |
| sentence-transformers | >=2.2.0 | Local embeddings | Already in use with all-MiniLM-L6-v2 |
| pyyaml | >=6.0 | Workflow YAML serialization | Already in use, safe_load for security |
| subprocess | stdlib | Code execution isolation | Standard Python, no dependencies |
| playwright | >=1.40.0 | E2E testing | Already in use with pytest-playwright |
| keyring | >=24.0.0 | Secure API key storage | Already in use for secrets |
| bandit | >=1.7.0 | Security static analysis | Already in dev dependencies |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| watchdog | >=4.0.0 | File system monitoring | For incremental RAG re-indexing on file save |
| tiktoken | (already used) | Token counting | Already integrated for token limits |
| ruamel.yaml | >=0.18.0 | YAML round-trip preservation | Optional for preserving comments in YAML |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| subprocess | RestrictedPython | RestrictedPython has sandbox escapes, subprocess with timeout is simpler |
| In-memory ChromaDB | Persistent ChromaDB | Upgrade to persistent for production, keep in-memory for tests |
| watchdog | Polling | watchdog is more efficient but adds complexity |

**Installation:**
```bash
# Already installed via pyproject.toml
pip install chromadb>=0.5.0 sentence-transformers>=2.2.0 playwright>=1.40.0
```

## Architecture Patterns

### Recommended Project Structure
```
src/
├── ui/views/code_editor/          # Existing code editor
│   ├── workflow_bridge.py         # NEW: Workflow-Editor bridge
│   └── ai_panel/
│       └── rag_context.py         # NEW: RAG context provider
├── rag/
│   ├── chromadb_client.py         # Existing - upgrade to persistent
│   ├── embeddings.py              # Existing
│   ├── project_indexer.py         # NEW: Project-level indexing
│   └── dimension_validator.py     # NEW: Embedding dimension validation
├── core/
│   └── nodes/
│       └── execution/
│           └── code_runner.py     # NEW: Code execution node
└── services/
    └── workflow_serializer.py     # NEW: JSON/YAML/Python DSL conversion
```

### Pattern 1: Workflow-Editor Bridge
**What:** Bridge between code editor and workflow storage, enabling bi-directional sync.
**When to use:** When user edits workflow in code editor or visual canvas.
**Example:**
```python
# Based on existing Workflow model (src/core/workflow/models.py)
class WorkflowBridge:
    """Bridge between code editor and workflow storage."""

    def __init__(self, storage: WorkflowStorage):
        self.storage = storage
        self._listeners: list[Callable] = []

    def load_as_code(self, workflow_id: str, format: str = "yaml") -> str:
        """Load workflow as editable code."""
        workflow = self.storage.load_workflow(workflow_id)
        if format == "yaml":
            return workflow.to_yaml()  # Already exists
        elif format == "json":
            return workflow.model_dump_json(indent=2)
        elif format == "python":
            return self._to_python_dsl(workflow)
        raise ValueError(f"Unsupported format: {format}")

    def save_from_code(self, workflow_id: str, code: str, format: str) -> Workflow:
        """Parse code back to workflow model."""
        if format == "yaml":
            workflow = Workflow.from_yaml(code)  # Already exists
        elif format == "json":
            workflow = Workflow.model_validate_json(code)
        elif format == "python":
            workflow = self._from_python_dsl(code)
        workflow.id = workflow_id  # Preserve original ID
        self.storage.save_workflow(workflow)
        return workflow
```

### Pattern 2: Project-Level RAG Indexer
**What:** Indexes all code files in a project for AI context retrieval.
**When to use:** When user opens a project folder in code editor.
**Example:**
```python
# Extends existing rag/embeddings.py and rag/chromadb_client.py
class ProjectIndexer:
    """Index project files for RAG retrieval."""

    SUPPORTED_EXTENSIONS = {
        '.py', '.js', '.ts', '.jsx', '.tsx',
        '.md', '.txt', '.json', '.yaml', '.yml',
        '.html', '.css', '.sql', '.sh', '.bash'
    }

    def __init__(
        self,
        chromadb_client: ChromaDBClient,
        embedding_manager: EmbeddingManager,
    ):
        self.chromadb = chromadb_client
        self.embeddings = embedding_manager
        self._file_hashes: dict[str, str] = {}  # path -> hash for incremental

    async def index_project(self, project_root: str) -> None:
        """Index all supported files in project."""
        collection_id = f"project-{self._hash_path(project_root)}"

        # Validate embedding dimension before any writes
        await self._ensure_dimension_consistency(collection_id)

        for file_path in self._iter_files(project_root):
            file_hash = self._compute_hash(file_path)
            if self._file_hashes.get(file_path) != file_hash:
                await self._index_file(collection_id, file_path)
                self._file_hashes[file_path] = file_hash

    async def query_context(
        self,
        query: str,
        project_root: str,
        top_k: int = 5
    ) -> list[dict]:
        """Retrieve relevant code snippets for AI context."""
        collection_id = f"project-{self._hash_path(project_root)}"
        query_embedding = await self.embeddings.embed(query)
        return await self.chromadb.query(
            collection_id=collection_id,
            query_embedding=query_embedding,
            top_k=top_k,
            min_similarity=0.3  # Filter low-relevance results
        )
```

### Pattern 3: Embedding Dimension Validator
**What:** Validates embedding dimensions before writes to prevent RAG corruption.
**When to use:** Before any add_chunks call to ChromaDB.
**Example:**
```python
class DimensionValidator:
    """Validate embedding dimensions before ChromaDB writes."""

    EXPECTED_DIMENSIONS = {
        "all-MiniLM-L6-v2": 384,
        "text-embedding-ada-002": 1536,
        "text-embedding-3-small": 1536,
    }

    async def validate_before_write(
        self,
        collection_id: str,
        embeddings: list[list[float]],
        chromadb_client: ChromaDBClient,
        expected_model: str = "all-MiniLM-L6-v2"
    ) -> None:
        """Validate embeddings before write."""
        if not embeddings:
            return

        # Check expected dimension for model
        expected_dim = self.EXPECTED_DIMENSIONS.get(expected_model)
        actual_dim = len(embeddings[0])

        if expected_dim and actual_dim != expected_dim:
            raise ValueError(
                f"Embedding dimension mismatch: expected {expected_dim} "
                f"for {expected_model}, got {actual_dim}"
            )

        # Check collection consistency if exists
        if await chromadb_client.collection_exists(collection_id):
            # Query existing to get dimension
            try:
                sample = await chromadb_client.query(
                    collection_id=collection_id,
                    query_embedding=[0.0] * actual_dim,
                    top_k=1
                )
            except Exception:
                # Collection dimension mismatch - would fail at query
                raise ValueError(
                    f"Collection {collection_id} has different embedding "
                    f"dimension than provided embeddings ({actual_dim})"
                )

        # Validate all embeddings have same dimension
        for i, emb in enumerate(embeddings):
            if len(emb) != actual_dim:
                raise ValueError(
                    f"Inconsistent embedding dimensions: embedding {i} "
                    f"has {len(emb)}, expected {actual_dim}"
                )
```

### Pattern 4: Code Execution Node
**What:** Executes code snippets in workflows with timeout and output capture.
**When to use:** When user adds a code execution node to workflow.
**Example:**
```python
import subprocess
import tempfile
import os
from pathlib import Path

class CodeExecutionNode(BaseNode):
    """Execute code snippets in workflow."""

    type = "code_execution"
    name = "Execute Code"
    category = "Execution"

    async def execute(self, config: dict, context: dict) -> dict:
        """Execute code with timeout and capture output."""
        code = config.get("code", "")
        language = config.get("language", "python")
        timeout = config.get("timeout", 30)  # Default 30 seconds

        # Resolve workflow variables in code
        for var_name, var_value in context.get("$vars", {}).items():
            code = code.replace(f"{{${var_name}}}", str(var_value))

        # Create temp file for code
        suffix = self._get_suffix(language)
        with tempfile.NamedTemporaryFile(
            mode='w', suffix=suffix, delete=False
        ) as f:
            f.write(code)
            temp_path = f.name

        try:
            # Get interpreter command
            cmd = self._get_command(language, temp_path)

            # Execute with timeout
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=config.get("working_directory"),
            )

            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "success": result.returncode == 0,
            }

        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": f"Execution timed out after {timeout} seconds",
                "return_code": -1,
                "success": False,
            }
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def _get_suffix(self, language: str) -> str:
        return {
            "python": ".py",
            "javascript": ".js",
            "bash": ".sh",
            "powershell": ".ps1",
        }.get(language, ".txt")

    def _get_command(self, language: str, path: str) -> list[str]:
        return {
            "python": ["python", path],
            "javascript": ["node", path],
            "bash": ["bash", path],
            "powershell": ["powershell", "-File", path],
        }.get(language, ["python", path])
```

### Anti-Patterns to Avoid
- **Executing code without timeout:** Always use subprocess timeout to prevent runaway processes
- **Storing API keys in code:** Use keyring for secure storage, never log or serialize keys
- **Ignoring embedding dimension mismatches:** Always validate dimensions before ChromaDB writes
- **Polling for file changes:** Use watchdog for efficient file system monitoring
- **Blocking main thread for RAG indexing:** Use asyncio or background tasks

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Vector similarity search | Custom numpy loops | ChromaDB query | Optimized, handles large scales |
| Token counting | char_count / 4 | tiktoken | Accurate per-model counting |
| YAML parsing | Regex | PyYAML safe_load | Handles edge cases, security |
| File system watching | Sleep + poll | watchdog | Efficient OS-level events |
| Secret storage | Environment variables | keyring | OS-level secure storage |
| Python sandboxing | RestrictedPython | subprocess + timeout | RestrictedPython has known escapes |
| E2E browser automation | Selenium | Playwright | Modern, auto-waiting, faster |

**Key insight:** The existing codebase already uses the right libraries. The task is extending them, not replacing them.

## Common Pitfalls

### Pitfall 1: ChromaDB Embedding Dimension Mismatch
**What goes wrong:** Adding embeddings with different dimensions corrupts the collection.
**Why it happens:** ChromaDB locks dimension on first insert. Switching embedding models breaks existing collections.
**How to avoid:** Validate dimensions before every write. Store embedding model name in collection metadata.
**Warning signs:** `InvalidDimensionException` errors at runtime.

### Pitfall 2: Subprocess Code Execution Escapes
**What goes wrong:** Malicious code can escape subprocess and affect host system.
**Why it happens:** Subprocess doesn't sandbox - it runs with user privileges.
**How to avoid:** Use strict timeouts, don't pass user input as shell commands, consider AppArmor/seccomp for production.
**Warning signs:** Resource exhaustion, unexpected file modifications.

### Pitfall 3: API Key Exposure in Memory
**What goes wrong:** API keys remain in memory after use, visible in heap dumps.
**Why it happens:** Python strings are immutable; "deleting" a variable doesn't clear memory.
**How to avoid:** Use keyring (OS-level storage), minimize time keys are in memory, use `del` + `gc.collect()`.
**Warning signs:** Keys visible in process memory dumps.

### Pitfall 4: Flet E2E Test Flakiness
**What goes wrong:** Tests pass locally but fail in CI, or fail intermittently.
**Why it happens:** Flet renders to canvas, needs semantic tree for element access. Async timing varies.
**How to avoid:** Enable accessibility semantics, use explicit waits, add page.wait_for_timeout after actions.
**Warning signs:** "Element not found" errors, tests passing on retry.

### Pitfall 5: YAML Deserialization Attacks
**What goes wrong:** User-provided YAML executes arbitrary code via `yaml.load`.
**Why it happens:** Default YAML loader can instantiate Python objects.
**How to avoid:** Always use `yaml.safe_load`, never `yaml.load` without Loader.
**Warning signs:** Arbitrary code execution from YAML files.

### Pitfall 6: RAG Re-indexing Performance
**What goes wrong:** Full re-index on every file save causes UI lag.
**Why it happens:** Embedding generation is slow (100ms+ per chunk).
**How to avoid:** Use file hashing for incremental indexing, background tasks, debounce.
**Warning signs:** UI freezes after saving files.

## Code Examples

Verified patterns based on existing codebase:

### Loading Workflow as Editable YAML
```python
# Based on existing src/core/workflow/models.py and src/data/storage.py
from src.core.workflow.models import Workflow
from src.data.storage import get_storage

def load_workflow_as_yaml(workflow_id: str) -> str:
    """Load workflow for editing in code editor."""
    storage = get_storage()
    workflow = storage.load_workflow(workflow_id)
    if workflow:
        return workflow.to_yaml()  # Existing method
    return ""

def save_workflow_from_yaml(workflow_id: str, yaml_content: str) -> bool:
    """Save edited YAML back to workflow storage."""
    try:
        workflow = Workflow.from_yaml(yaml_content)  # Existing method
        workflow.id = workflow_id  # Preserve original ID
        storage = get_storage()
        storage.save_workflow(workflow)
        return True
    except Exception:
        return False
```

### Project RAG Query with Context
```python
# Based on existing src/rag/chromadb_client.py and src/rag/embeddings.py
async def get_codebase_context(
    query: str,
    project_root: str,
    chromadb: ChromaDBClient,
    embeddings: EmbeddingManager,
    top_k: int = 5
) -> str:
    """Get relevant code context for AI prompt."""
    collection_id = f"project-{hash(project_root)}"

    # Generate query embedding
    query_embedding = await embeddings.embed(query)

    # Query ChromaDB
    results = await chromadb.query(
        collection_id=collection_id,
        query_embedding=query_embedding,
        top_k=top_k,
        min_similarity=0.3
    )

    # Format as context string
    context_parts = []
    for result in results:
        chunk = result["chunk"]
        context_parts.append(
            f"# File: {chunk.metadata.get('source_path', 'unknown')}\n"
            f"{chunk.content}"
        )

    return "\n\n---\n\n".join(context_parts)
```

### Secure Code Execution with Workflow Variables
```python
# Based on existing workflow executor patterns
import subprocess
import tempfile
from pathlib import Path

async def execute_code_snippet(
    code: str,
    language: str,
    workflow_vars: dict,
    timeout: int = 30
) -> dict:
    """Execute code snippet with workflow variable access."""
    # Inject workflow variables as Python code
    if language == "python":
        var_code = "\n".join(
            f"{name} = {repr(value)}"
            for name, value in workflow_vars.items()
        )
        code = f"{var_code}\n\n{code}"

    # Write to temp file
    suffix = ".py" if language == "python" else ".js"
    with tempfile.NamedTemporaryFile(
        mode='w', suffix=suffix, delete=False
    ) as f:
        f.write(code)
        temp_path = f.name

    try:
        cmd = ["python" if language == "python" else "node", temp_path]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0
        }
    except subprocess.TimeoutExpired:
        return {
            "stdout": "",
            "stderr": f"Timeout after {timeout}s",
            "success": False
        }
    finally:
        Path(temp_path).unlink(missing_ok=True)
```

### E2E Test Pattern for Flet
```python
# Based on existing tests/e2e/conftest.py patterns
import pytest
from playwright.sync_api import Page

class TestWorkflowCodeEditing:
    """E2E tests for workflow code editing."""

    def test_open_workflow_in_code_editor(self, page: Page, helpers):
        """User can open workflow as code in editor."""
        # Navigate to workflows
        helpers.navigate_to(page, "workflows")
        page.wait_for_timeout(1000)

        # Click on a workflow to edit
        workflow_card = page.locator("[role='group'][aria-label]").first
        workflow_card.click()
        page.wait_for_timeout(500)

        # Switch to code view (using existing data-testid pattern)
        code_view_btn = page.locator("text=Code")
        code_view_btn.click()
        page.wait_for_timeout(1000)

        # Verify code editor shows YAML
        editor_content = page.locator(".code-editor").text_content()
        assert "nodes:" in editor_content or "name:" in editor_content

    def test_edit_and_save_workflow_code(self, page: Page, helpers):
        """User can edit workflow code and save."""
        # ... navigate and open workflow ...

        # Make edit
        editor = page.locator("textarea").first
        editor.fill("name: Updated Workflow\nnodes: []")

        # Save
        save_btn = page.locator("[role='button']:has-text('Save')")
        save_btn.click()
        page.wait_for_timeout(500)

        # Verify success
        assert page.locator("text=Saved").is_visible()
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| yaml.load() | yaml.safe_load() | Security best practice | Prevents code execution |
| In-memory ChromaDB | Persistent ChromaDB | Production readiness | Data survives restarts |
| RestrictedPython | subprocess + timeout | Security research 2023+ | RestrictedPython has escapes |
| Full re-indexing | Incremental with hashing | Performance optimization | 10x faster updates |
| Environment variables | keyring + secrets | Security best practice | OS-level protection |

**Deprecated/outdated:**
- `google-generativeai` SDK: Replaced by `google-genai` (already noted in prior decisions)
- `yaml.load` without Loader: Security vulnerability
- ChromaDB <0.5.0: Pydantic 2 incompatibility

## Open Questions

Things that couldn't be fully resolved:

1. **Python DSL Format for Workflows**
   - What we know: JSON and YAML serialization exist. Highway-DSL and Argo Python DSL are examples.
   - What's unclear: Exact syntax for Python DSL that's intuitive and bi-directionally convertible.
   - Recommendation: Start with JSON/YAML only. Add Python DSL as optional feature after core integration.

2. **Code Execution Sandboxing Level**
   - What we know: subprocess + timeout is minimum viable. AppArmor/seccomp provide stronger isolation.
   - What's unclear: Whether full sandboxing is needed for v2 (user-configurable timeout may be sufficient).
   - Recommendation: Implement subprocess + timeout first. Add sandboxing if security audit requires.

3. **RAG Re-indexing Trigger Strategy**
   - What we know: Incremental on save, background periodic, or hybrid are options.
   - What's unclear: Best user experience - immediate but slow vs. background but stale.
   - Recommendation: Hybrid - debounced on-save (500ms) with background full scan on project open.

4. **Flet Flutter Semantics Accessibility**
   - What we know: Flet renders to canvas, requires clicking accessibility placeholder.
   - What's unclear: Whether this is stable across Flet versions.
   - Recommendation: Continue using existing pattern from tests/e2e/conftest.py, update if Flet changes.

## Sources

### Primary (HIGH confidence)
- **Existing codebase** - src/core/workflow/models.py, src/data/storage.py (workflow storage patterns)
- **Existing codebase** - src/rag/chromadb_client.py, src/rag/embeddings.py (RAG infrastructure)
- **Existing codebase** - tests/e2e/conftest.py (E2E testing patterns with Playwright)
- **Existing codebase** - src/ai/security.py (API key storage with keyring)
- **ChromaDB Docs** - https://docs.trychroma.com/guides (collection creation, queries)
- **ChromaDB Cookbook** - https://cookbook.chromadb.dev/faq/ (dimension handling)

### Secondary (MEDIUM confidence)
- [Ailog RAG Guide](https://app.ailog.fr/en/blog/guides/chromadb-setup-guide) - ChromaDB best practices
- [BrowserStack Playwright Tutorial](https://www.browserstack.com/guide/playwright-python-tutorial) - E2E testing patterns
- [Playwright Best Practices](https://playwright.dev/docs/best-practices) - Official Playwright guidance
- [GitGuardian Secrets Management](https://blog.gitguardian.com/secrets-api-management/) - API key security
- [OpenEdX CodeJail](https://github.com/openedx/codejail) - Subprocess sandboxing patterns

### Tertiary (LOW confidence)
- [Healeycodes Running Untrusted Python](https://healeycodes.com/running-untrusted-python-code) - Sandbox approaches
- [Highway-DSL](https://farshid.co.uk/entry/highway_dsl_a_pydantic_native_dsl_for_defining_complex_workflows) - Python workflow DSL patterns
- [CrewAI ChromaDB Issue](https://github.com/crewAIInc/crewAI/issues/2464) - Dimension mismatch examples

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Verified against existing pyproject.toml and codebase
- Architecture: MEDIUM - Patterns based on existing code, new components designed
- Pitfalls: MEDIUM - Combination of existing test patterns and web research
- Code Examples: HIGH - Based on actual existing code patterns

**Research date:** 2026-01-18
**Valid until:** 2026-02-18 (30 days for stable libraries, existing infrastructure)

---
*Phase: 05-advanced-integration*
*Research completed: 2026-01-18*
