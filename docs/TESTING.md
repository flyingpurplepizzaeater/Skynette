# Testing Guide for Skynette

This document provides comprehensive information about testing in the Skynette project.

## Table of Contents
- [Overview](#overview)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Writing Tests](#writing-tests)
- [Test Coverage](#test-coverage)
- [CI/CD Integration](#cicd-integration)
- [Troubleshooting](#troubleshooting)

## Overview

Skynette uses `pytest` as its testing framework with several plugins for enhanced functionality:
- **pytest-asyncio**: For testing async code
- **pytest-cov**: For code coverage reporting
- **pytest-playwright**: For E2E browser-based testing
- **pytest-xdist**: For parallel test execution

### Test Types

1. **Unit Tests** (`tests/unit/`): Fast, isolated tests for individual functions and classes
2. **Integration Tests** (`tests/integration/`): Tests for module interactions
3. **E2E Tests** (`tests/e2e/`): End-to-end tests using Playwright for UI testing

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── unit/                    # Unit tests
│   ├── __init__.py
│   └── test_*.py
├── integration/             # Integration tests
│   ├── __init__.py
│   └── test_*.py
├── e2e/                     # End-to-end tests
│   ├── __init__.py
│   ├── conftest.py         # E2E-specific fixtures
│   └── test_*.py
├── fixtures/                # Test data and fixtures
│   ├── __init__.py
│   └── workflows.py
└── mocks/                   # Mock objects
    ├── __init__.py
    ├── ai_providers.py
    └── storage.py
```

## Running Tests

### Prerequisites

Install test dependencies:
```bash
# Install all dev dependencies
pip install -e ".[dev]"

# Or install just test dependencies
pip install pytest pytest-asyncio pytest-cov pytest-xdist
```

For E2E tests, install Playwright browsers:
```bash
playwright install chromium
```

### Basic Test Commands

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/unit/test_imports.py

# Run specific test
pytest tests/unit/test_imports.py::test_main_module_imports

# Run tests by pattern
pytest -k "test_workflow"

# Run only unit tests
pytest tests/unit/

# Run only E2E tests
pytest tests/e2e/
```

### Advanced Test Commands

```bash
# Run tests in parallel (4 workers)
pytest -n 4

# Run with coverage
pytest --cov=src --cov-report=html

# Run with coverage and show missing lines
pytest --cov=src --cov-report=term-missing

# Stop on first failure
pytest -x

# Show print statements
pytest -s

# Run last failed tests
pytest --lf

# Run tests that failed last time, then all others
pytest --ff
```

### Test Selection

```bash
# Run tests with specific marker
pytest -m "unit"

# Exclude tests with marker
pytest -m "not slow"

# Run tests matching expression
pytest -k "workflow and not editor"
```

## Writing Tests

### Test File Naming

- Test files must start with `test_` or end with `_test.py`
- Test functions must start with `test_`
- Test classes must start with `Test`

### Basic Test Structure

```python
import pytest

def test_function_name():
    """Test description."""
    # Arrange
    expected = "hello"

    # Act
    result = some_function()

    # Assert
    assert result == expected
```

### Using Fixtures

```python
import pytest

@pytest.fixture
def sample_data():
    """Provide sample data for tests."""
    return {"id": 1, "name": "Test"}

def test_with_fixture(sample_data):
    """Test using a fixture."""
    assert sample_data["id"] == 1
    assert sample_data["name"] == "Test"
```

### Testing Async Code

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    """Test an async function."""
    result = await async_function()
    assert result is not None
```

### Parametrized Tests

```python
import pytest

@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
])
def test_multiply_by_two(input, expected):
    """Test multiplication with multiple inputs."""
    assert input * 2 == expected
```

### Testing Exceptions

```python
import pytest

def test_exception_raised():
    """Test that function raises expected exception."""
    with pytest.raises(ValueError, match="Invalid input"):
        function_that_raises()
```

### Mocking

```python
from unittest.mock import Mock, patch

def test_with_mock():
    """Test using a mock object."""
    mock_service = Mock()
    mock_service.get_data.return_value = {"test": "data"}

    result = use_service(mock_service)
    assert result["test"] == "data"
    mock_service.get_data.assert_called_once()

@patch('src.module.external_api')
def test_with_patch(mock_api):
    """Test using patch decorator."""
    mock_api.return_value = "mocked"
    result = function_using_api()
    assert result == "mocked"
```

## Test Coverage

### Generating Coverage Reports

```bash
# Generate HTML coverage report
pytest --cov=src --cov-report=html

# Open the report (opens in browser)
open htmlcov/index.html  # macOS
start htmlcov/index.html  # Windows
xdg-open htmlcov/index.html  # Linux
```

### Coverage Configuration

Coverage settings in `pyproject.toml`:

```toml
[tool.coverage.run]
source = ["src"]
omit = [
    "*/tests/*",
    "*/migrations/*",
    "*/__pycache__/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
]
```

### Coverage Goals

- **Minimum**: 70% coverage
- **Target**: 80% coverage
- **Ideal**: 90%+ coverage

Focus on:
- Core business logic
- Critical paths
- Error handling
- Edge cases

Lower priority for coverage:
- UI code (tested via E2E)
- Simple getters/setters
- Configuration code

## CI/CD Integration

### GitHub Actions

Tests run automatically on:
- Every push to main/develop
- Every pull request
- Scheduled runs (optional)

See `.github/workflows/ci.yml` for configuration.

### Pre-commit Hooks

Add tests to pre-commit hooks (optional):

```yaml
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: pytest
      name: pytest
      entry: pytest
      language: system
      pass_filenames: false
      always_run: true
```

## E2E Testing with Playwright

### Writing E2E Tests

```python
import pytest
from playwright.sync_api import Page, expect

def test_workflow_creation(page: Page):
    """Test creating a new workflow."""
    # Navigate to workflows page
    page.goto("http://localhost:8000/workflows")

    # Click new workflow button
    page.click("button[aria-label='New Workflow']")

    # Fill in workflow details
    page.fill("input[name='name']", "Test Workflow")
    page.fill("textarea[name='description']", "Test Description")

    # Submit form
    page.click("button[type='submit']")

    # Verify workflow was created
    expect(page.locator("text=Test Workflow")).to_be_visible()
```

### E2E Test Environment

E2E tests use environment variables:

```bash
SKYNETTE_TEST_MODE=true
SKYNETTE_MOCK_AI=true
SKYNETTE_DATA_DIR=/tmp/skynette_test
```

### Running E2E Tests

```bash
# Run E2E tests
pytest tests/e2e/

# Run E2E tests with browser visible (headed mode)
pytest tests/e2e/ --headed

# Run E2E tests with specific browser
pytest tests/e2e/ --browser chromium
pytest tests/e2e/ --browser firefox
pytest tests/e2e/ --browser webkit

# Generate trace for debugging
pytest tests/e2e/ --tracing on
```

## Test Markers

Use markers to categorize tests:

```python
import pytest

@pytest.mark.unit
def test_unit():
    pass

@pytest.mark.integration
def test_integration():
    pass

@pytest.mark.e2e
def test_e2e():
    pass

@pytest.mark.slow
def test_slow_operation():
    pass

@pytest.mark.skip(reason="Not implemented yet")
def test_future_feature():
    pass
```

Register markers in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "e2e: End-to-end tests",
    "slow: Slow running tests",
]
```

## Troubleshooting

### Common Issues

#### Import Errors

```bash
# Ensure src is in Python path
export PYTHONPATH="${PYTHONPATH}:${PWD}"

# Or install in editable mode
pip install -e .
```

#### Playwright Errors

```bash
# Install browsers
playwright install

# Install system dependencies
playwright install-deps
```

#### Async Test Warnings

Add `pytest-asyncio` mode to `pyproject.toml`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

#### Test Discovery Issues

Ensure:
- Test files start with `test_` or end with `_test.py`
- Test functions start with `test_`
- All directories have `__init__.py` files

### Debugging Tests

```bash
# Run with PDB on failure
pytest --pdb

# Run with PDB on first failure
pytest -x --pdb

# Increase verbosity
pytest -vv

# Show local variables on failure
pytest -l

# Show print output
pytest -s
```

### Cleaning Test Cache

```bash
# Clear pytest cache
pytest --cache-clear

# Remove __pycache__ directories
find . -type d -name __pycache__ -exec rm -rf {} +

# Remove .pyc files
find . -type f -name "*.pyc" -delete
```

## Best Practices

### Test Design

1. **Follow AAA Pattern**: Arrange, Act, Assert
2. **One Assertion Per Test**: Focused tests are easier to debug
3. **Use Descriptive Names**: `test_should_return_error_when_input_is_empty`
4. **Test Edge Cases**: Empty inputs, None values, boundary conditions
5. **Keep Tests Independent**: No shared state between tests
6. **Use Fixtures**: Reuse setup code with pytest fixtures
7. **Mock External Dependencies**: Don't test third-party code

### Performance

1. **Fast Tests**: Unit tests should run in milliseconds
2. **Parallel Execution**: Use `pytest-xdist` for parallel runs
3. **Mark Slow Tests**: Use `@pytest.mark.slow` for integration tests
4. **Optimize Fixtures**: Use appropriate fixture scopes

### Maintainability

1. **DRY Principle**: Extract common setup to fixtures
2. **Clear Test Names**: Self-documenting test functions
3. **Comprehensive Docstrings**: Explain what's being tested
4. **Keep Tests Simple**: Easy to understand and modify
5. **Regular Cleanup**: Remove obsolete tests

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Playwright Python Documentation](https://playwright.dev/python/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)

---

**Last Updated**: 2026-01-10
**Maintainer**: Skynette Team
