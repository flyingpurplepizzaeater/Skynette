# Testing Patterns

**Analysis Date:** 2025-01-17

## Test Framework

**Runner:**
- pytest >= 8.0.0
- Config: `pyproject.toml` under `[tool.pytest.ini_options]`

**Async Support:**
- pytest-asyncio >= 0.23.0
- Mode: `asyncio_mode = "auto"` (auto-detects async tests)

**Additional Plugins:**
- pytest-cov >= 4.1.0 (coverage)
- pytest-playwright >= 0.5.0 (E2E browser tests)
- pytest-xdist >= 3.5.0 (parallel execution)

**Run Commands:**
```bash
pytest                          # Run all tests
pytest tests/unit               # Run unit tests only
pytest tests/e2e                # Run E2E tests only
pytest --cov=src                # Run with coverage
pytest -x                       # Stop on first failure
pytest -n auto                  # Parallel execution (xdist)
```

## Test File Organization

**Location:**
- Tests are in separate `tests/` directory (not co-located)
- Mirrors `src/` structure loosely

**Directory Structure:**
```
tests/
├── conftest.py              # Shared fixtures
├── helpers.py               # Test utility functions
├── fixtures/                # Test data files
├── mocks/                   # Mock implementations
│   ├── __init__.py
│   ├── ai_providers.py      # Mock AI providers
│   └── storage.py           # Mock storage
├── unit/                    # Unit tests
│   ├── test_workflow_models.py
│   ├── test_storage.py
│   ├── test_rag_service.py
│   └── ...
├── integration/             # Integration tests
│   ├── test_ui_workflows.py
│   ├── test_ui_execution.py
│   └── ...
└── e2e/                     # End-to-end browser tests
    ├── conftest.py          # E2E-specific fixtures
    ├── test_navigation.py
    ├── test_workflows.py
    └── ...
```

**Naming:**
- Test files: `test_<feature>.py`
- Test classes: `Test<Feature>` (e.g., `TestWorkflowStorage`, `TestRAGService`)
- Test methods: `test_<action>_<expected>` (e.g., `test_create_collection`, `test_load_nonexistent_workflow`)

## Test Structure

**Unit Test Pattern:**
```python
class TestWorkflowNode:
    """Tests for WorkflowNode model."""

    def test_create_node(self):
        """Test creating a workflow node."""
        node = WorkflowNode(
            type="manual_trigger",
            name="Start",
            position={"x": 100, "y": 200},
            config={"test_data": {"foo": "bar"}},
        )

        assert node.type == "manual_trigger"
        assert node.name == "Start"
        assert node.position["x"] == 100
        assert node.enabled is True
        assert node.id is not None

    def test_node_defaults(self):
        """Test node default values."""
        node = WorkflowNode(type="http_request", name="API Call")

        assert node.position == {"x": 0, "y": 0}
        assert node.config == {}
        assert node.enabled is True
```

**Async Test Pattern:**
```python
class TestRAGService:
    """Test RAG service integration."""

    @pytest.fixture
    async def service(self, tmp_path):
        """Create temp RAG service."""
        service = RAGService(storage_path=str(tmp_path))
        await service.initialize()
        return service

    @pytest.mark.asyncio
    async def test_create_collection(self, service):
        """Should create collection."""
        coll_id = await service.create_collection(
            name="test_collection",
            description="Test"
        )

        assert coll_id is not None
        coll = service.storage.get_collection(coll_id)
        assert coll.name == "test_collection"
```

**Setup/Teardown:**
- Use pytest fixtures for setup
- Use `yield` in fixtures for teardown
- `scope="session"` for expensive setup (e.g., app process)
- Default scope for test isolation

## Mocking

**Framework:** Custom mocks + pytest fixtures (no unittest.mock heavily used)

**Mock Provider Pattern (from `tests/mocks/ai_providers.py`):**
```python
class MockAIProvider(BaseProvider):
    """Mock AI provider for testing."""

    name = "mock"
    display_name = "Mock Provider"
    capabilities = {AICapability.TEXT_GENERATION, AICapability.CHAT}

    def __init__(self, response_text: str = "Mock response"):
        super().__init__()
        self.response_text = response_text
        self._is_initialized = True
        self._is_available = True
        self.generate_calls: list[dict] = []  # Track calls for assertions

    async def generate(self, prompt: str, config: GenerationConfig) -> AIResponse:
        self.generate_calls.append({"prompt": prompt, "config": config})
        return AIResponse(content=self.response_text, ...)

    def reset(self):
        """Reset call tracking for test isolation."""
        self.generate_calls.clear()
```

**Mock Storage Pattern (from `tests/mocks/storage.py`):**
```python
class MockWorkflowStorage:
    """In-memory mock storage for testing."""

    def __init__(self):
        self.workflows: dict[str, Workflow] = {}
        self.executions: list[WorkflowExecution] = []
        self.settings: dict[str, str] = {}

    def reset(self):
        """Reset storage for test isolation."""
        self.workflows.clear()
        self.executions.clear()
        self.settings.clear()
```

**What to Mock:**
- External AI providers (use `MockAIProvider`)
- File system operations (use `tmp_path` fixture)
- Database operations (use `MockWorkflowStorage` or temp directories)
- Network requests (mock httpx responses)

**What NOT to Mock:**
- Pydantic model validation
- In-memory data transformations
- The actual code under test

## Fixtures and Factories

**Shared Fixtures (from `tests/conftest.py`):**
```python
@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the project root directory."""
    return PROJECT_ROOT

@pytest.fixture
def temp_data_dir(tmp_path: Path) -> Path:
    """Create a temporary data directory for tests."""
    data_dir = tmp_path / "skynette_data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

@pytest.fixture
def test_env_vars(temp_data_dir: Path) -> dict:
    """Environment variables for test mode."""
    return {
        "SKYNETTE_TEST_MODE": "true",
        "SKYNETTE_MOCK_AI": "true",
        "SKYNETTE_DATA_DIR": str(temp_data_dir),
    }

@pytest.fixture
def sample_workflow_data() -> dict:
    """Sample workflow data for testing."""
    return {
        "id": "test-workflow-1",
        "name": "Test Workflow",
        "nodes": [...],
        "connections": [...],
    }

@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances between tests."""
    yield
    # Clean up after each test
```

**Test Data Location:**
- `tests/fixtures/` for static test data files
- Inline in test files for simple data
- Factory fixtures for complex objects

## Coverage

**Requirements:** No enforced minimum (not configured)

**View Coverage:**
```bash
pytest --cov=src --cov-report=html
# Opens htmlcov/index.html

pytest --cov=src --cov-report=term
# Terminal output
```

**Coverage Artifacts:**
- `.coverage` file in project root
- `htmlcov/` directory for HTML reports

## Test Types

**Unit Tests (`tests/unit/`):**
- Test individual functions/methods in isolation
- Fast execution (no I/O, no network)
- One assertion focus per test
- Examples: `test_workflow_models.py`, `test_rag_processor.py`

**Integration Tests (`tests/integration/`):**
- Test interaction between components
- May use temp files/databases
- Examples: `test_ui_workflows.py`, `test_rag_workflow.py`

**E2E Tests (`tests/e2e/`):**
- Test full application via Playwright browser automation
- Require app process running on port 8550
- Use Flet semantics tree for element selection
- Examples: `test_navigation.py`, `test_ai_hub.py`

## Common Patterns

**Async Testing:**
```python
@pytest.mark.asyncio
async def test_ingest_document(self, service, tmp_path):
    """Should ingest markdown document."""
    coll_id = await service.create_collection(name="test")

    md_file = tmp_path / "test.md"
    md_file.write_text("# Test\n\nContent")

    result = await service.ingest_document(str(md_file), coll_id)

    assert result["status"] == "success"
    assert result["chunks_created"] > 0
```

**Error Testing:**
```python
def test_unsupported_file_type(self, tmp_path):
    """Should raise error for unsupported file type."""
    processor = DocumentProcessor()

    file = tmp_path / "test.pdf"
    file.write_text("content")

    with pytest.raises(ValueError, match="Unsupported file type"):
        processor.process_file(str(file), "pdf")
```

**Fixture Chaining:**
```python
@pytest.fixture
def storage(temp_data_dir: Path) -> WorkflowStorage:
    """Create a WorkflowStorage instance with temp directory."""
    return WorkflowStorage(data_dir=str(temp_data_dir))

@pytest.fixture
def sample_workflow() -> Workflow:
    """Create a sample workflow for testing."""
    workflow = Workflow(name="Test Workflow")
    workflow.nodes = [WorkflowNode(type="manual_trigger", name="Start")]
    return workflow
```

**Temp File Testing:**
```python
def test_process_markdown_file(self, tmp_path):
    """Should parse markdown file."""
    processor = DocumentProcessor()

    md_file = tmp_path / "test.md"
    md_file.write_text("""# Title
Introduction.

## Section 1
Content.
""")

    chunks = processor.process_file(str(md_file), "markdown")
    assert len(chunks) > 0
```

## E2E Test Patterns

**App Process Fixture (from `tests/e2e/conftest.py`):**
```python
@pytest.fixture(scope="session")
def app_process(project_root: Path, app_env: dict):
    """Start the Flet app in web mode for testing."""
    proc = subprocess.Popen(cmd, env=app_env, ...)

    # Wait for app to be ready
    while time.time() - start_time < STARTUP_TIMEOUT:
        try:
            response = httpx.get(APP_URL, timeout=2.0)
            if response.status_code == 200:
                break
        except Exception:
            pass

    yield proc
    proc.terminate()
```

**Page Fixture:**
```python
@pytest.fixture
def page(browser_instance: Browser):
    """Create a new page for each test."""
    context = browser_instance.new_context(viewport={"width": 1280, "height": 720})
    page = context.new_page()
    page.goto(APP_URL, timeout=60000)
    page.wait_for_load_state("networkidle")

    # Enable Flet accessibility mode
    page.evaluate('''
        const placeholder = document.querySelector('flt-semantics-placeholder');
        if (placeholder) placeholder.click();
    ''')

    yield page
    page.close()
```

**Selector Constants:**
```python
class Selectors:
    """Common selectors for Skynette UI."""
    NAV_WORKFLOWS = "flt-semantics[role='button']:has-text('Workflows')"
    NAV_AI_HUB = "flt-semantics[role='button']:has-text('AI Hub')"
    NEW_WORKFLOW_BTN = "flt-semantics[role='button']:has-text('New Workflow')"
    DIALOG = "[role='dialog'], flt-semantics[role='dialog']"
```

**Navigation Helper:**
```python
class TestHelpers:
    @staticmethod
    def navigate_to(page: Page, view: str):
        """Navigate to a specific view."""
        view_map = {
            "workflows": Selectors.NAV_WORKFLOWS,
            "ai_hub": Selectors.NAV_AI_HUB,
        }
        page.locator(view_map[view]).first.click()
        page.wait_for_timeout(500)
```

## Pre-commit Testing

**Hooks (from `.pre-commit-config.yaml`):**
- Ruff linting and formatting
- Trailing whitespace removal
- YAML/JSON/TOML validation
- Large file check (max 1000KB)
- Private key detection
- Commit message format (commitizen)

---

*Testing analysis: 2025-01-17*
