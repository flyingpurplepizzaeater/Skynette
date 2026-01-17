# Coding Conventions

**Analysis Date:** 2025-01-17

## Naming Patterns

**Files:**
- Python modules: `snake_case.py` (e.g., `workflow_models.py`, `knowledge_bases.py`)
- Test files: `test_<module_name>.py` (e.g., `test_rag_service.py`, `test_storage.py`)
- Init files: `__init__.py` in every package directory

**Functions:**
- Use `snake_case` for all functions and methods
- Prefix private methods with underscore: `_build_header()`, `_load_collections()`
- Async functions use same naming but often prefixed with action verb: `async def initialize()`, `async def ingest_document()`

**Variables:**
- Local variables: `snake_case` (e.g., `file_path`, `chunk_count`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `APP_PORT`, `STARTUP_TIMEOUT`, `PROJECT_ROOT`)
- Class attributes: `snake_case` (e.g., `self.collections_cache`, `self._is_initialized`)

**Types:**
- Classes: `PascalCase` (e.g., `WorkflowNode`, `RAGService`, `BaseProvider`)
- Pydantic models: `PascalCase` (e.g., `Collection`, `Document`, `Chunk`)
- Exceptions: `PascalCase` ending in `Error` (e.g., `AIProviderError`, `WorkflowValidationError`)

## Code Style

**Formatting:**
- Tool: Ruff (configured in `pyproject.toml`)
- Line length: 100 characters
- Target Python version: 3.11+
- Config location: `pyproject.toml` under `[tool.ruff]`

**Linting:**
- Tool: Ruff with select rules: E, F, I, N, W, UP
- E501 (line too long) is ignored
- Pre-commit hooks enforce linting via `.pre-commit-config.yaml`

**Security:**
- Bandit runs on pre-commit for security analysis
- Scans `src/` directory only
- B101 (assert statements) skipped in production code

## Import Organization

**Order:**
1. Standard library imports
2. Third-party imports
3. Local application imports (from `src.`)

**Example from `src/rag/service.py`:**
```python
import hashlib
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime, timezone

from src.rag.storage import RAGStorage
from src.rag.processor import DocumentProcessor
from src.rag.embeddings import EmbeddingManager
from src.rag.chromadb_client import ChromaDBClient
from src.rag.models import Collection, Document
```

**Path Aliases:**
- No path aliases used; use relative imports within `src/`
- All imports use `from src.<module>` pattern

## Error Handling

**Pattern - Custom Exception Hierarchy:**
- Base exception: `SkynetteError` in `src/core/errors/exceptions.py`
- All custom exceptions inherit from `SkynetteError`
- Exceptions include technical message, details dict, and user-friendly message

**Exception Creation Pattern:**
```python
class AIProviderError(SkynetteError):
    """Base class for AI provider errors."""

    def _default_user_message(self) -> str:
        return "AI service is currently unavailable. Please try again later."
```

**Try/Except Pattern:**
```python
try:
    # Operation
    result = await self.rag_service.ingest_document(file_path, coll_id)
except Exception as ex:
    # Log and show user-friendly error
    if self._page:
        self._page.show_snack_bar(
            ft.SnackBar(
                content=ft.Text(f"Failed to load collections: {str(ex)}"),
                bgcolor=ft.colors.ERROR,
            )
        )
```

**Async Error Handling:**
- Wrap async operations in try/except
- Update UI with SnackBar for user feedback
- Maintain cached data on failure when available

## Logging

**Framework:** Standard Python logging (configured in `src/core/errors/logging_config.py`)

**Patterns:**
- Use `print()` for debug output during development
- Structured logging for production error tracking
- Log files stored in `~/.skynette/logs/`

## Comments

**When to Comment:**
- Module-level docstrings for every Python file
- Class-level docstrings describing purpose
- Method docstrings for public methods with Args/Returns
- Inline comments for complex logic only

**Docstring Pattern (Google style):**
```python
def ingest_document(
    self,
    file_path: str,
    collection_id: str
) -> Dict[str, Any]:
    """
    Ingest document into collection.

    Args:
        file_path: Path to document
        collection_id: Target collection ID

    Returns:
        Dict with status, document_id, chunks_created
    """
```

**Module Docstring Pattern:**
```python
"""
RAG Service

Main service orchestrating RAG operations:
- Document ingestion with chunking and embedding
- Semantic search
- Collection management
"""
```

## Function Design

**Size:**
- Keep functions focused on single responsibility
- Extract helper methods for complex operations (e.g., `_build_header()`, `_build_empty_state()`)

**Parameters:**
- Use type hints for all parameters
- Use Optional[] for nullable parameters
- Use Pydantic models for complex configs
- Provide sensible defaults where appropriate

**Return Values:**
- Use type hints for all return values
- Return `Optional[T]` when value may be None
- Use Dict for complex return structures with status/data pattern
- Async functions use same patterns with `async def`

## Module Design

**Exports:**
- Use `__init__.py` for package-level exports
- Keep `__init__.py` minimal, usually just docstrings

**Organization Pattern:**
- Services: Business logic classes (e.g., `RAGService`, `WorkflowStorage`)
- Models: Pydantic data models (e.g., `Collection`, `Workflow`)
- Providers: Abstract base + concrete implementations (e.g., `BaseProvider`, `OpenAIProvider`)
- Views: Flet UI components (e.g., `KnowledgeBasesView`, `WorkflowsView`)
- Dialogs: Modal UI components (e.g., `QueryDialog`, `CollectionDialog`)

**Barrel Files:**
- Not heavily used; prefer explicit imports from specific modules

## Pydantic Model Conventions

**Pattern for Data Models:**
```python
from pydantic import BaseModel, Field, field_validator, model_validator
from uuid import uuid4

class Collection(BaseModel):
    id: str = Field(default_factory=lambda: f"coll-{uuid4().hex[:12]}")
    name: str = Field(..., min_length=1, max_length=100)
    description: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

**Validation:**
- Use `@field_validator` for single-field validation
- Use `@model_validator(mode='after')` for cross-field validation
- Raise `ValueError` with descriptive messages

## UI Component Conventions (Flet)

**View Class Pattern:**
```python
class KnowledgeBasesView(ft.Column):
    def __init__(self, page: ft.Page = None, rag_service: Optional[RAGService] = None):
        super().__init__()
        self._page = page
        self.expand = True
        self.spacing = Theme.SPACING_MD
        # State initialization

    def build(self):
        """Build the view."""
        return ft.Column(controls=[...])

    def did_mount(self):
        """Called when view is mounted."""
        # Load data asynchronously
```

**Event Handler Naming:**
- Prefix with `_on_`: `_on_new_collection()`, `_on_query_collection()`
- Accept event parameter: `def _on_new_collection(self, e):`

---

*Convention analysis: 2025-01-17*
