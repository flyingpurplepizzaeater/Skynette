# Contributing to Skynette

Thank you for your interest in contributing to Skynette! This document provides guidelines and instructions for contributing to the project.

## Table of Contents
- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)

## Code of Conduct

This project adheres to a Code of Conduct. By participating, you are expected to uphold this code. Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/Skynette.git
   cd Skynette
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/flyingpurplepizzaeater/Skynette.git
   ```

## Development Setup

### Prerequisites
- Python 3.11 or higher
- Git
- Virtual environment tool (venv, conda, etc.)

### Installation

1. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

2. **Install development dependencies**:
   ```bash
   pip install -e ".[ai,dev]"
   ```

3. **Install Playwright browsers** (for E2E tests):
   ```bash
   playwright install chromium
   ```

4. **Verify installation**:
   ```bash
   pytest tests/ -v
   ruff check src/
   ```

## How to Contribute

### Types of Contributions

We welcome various types of contributions:

- **Bug Fixes**: Fix identified bugs
- **New Features**: Implement new functionality
- **Documentation**: Improve or add documentation
- **Tests**: Add or improve test coverage
- **Performance**: Optimize existing code
- **UI/UX**: Enhance user interface and experience

### Finding Work

1. Check the [Issues](https://github.com/flyingpurplepizzaeater/Skynette/issues) page
2. Look for issues labeled `good first issue` or `help wanted`
3. Comment on an issue to express interest
4. Wait for maintainer approval before starting work

## Coding Standards

### Python Style Guide

We use [Ruff](https://github.com/astral-sh/ruff) for linting and formatting:

```bash
# Check code style
ruff check src/

# Auto-fix issues
ruff check --fix src/

# Format code
ruff format src/
```

### Code Style Rules

- **Line length**: Maximum 100 characters
- **Type hints**: Use type hints for function signatures
- **Docstrings**: Use Google-style docstrings for public APIs
- **Naming conventions**:
  - Classes: `PascalCase`
  - Functions/methods: `snake_case`
  - Constants: `UPPER_SNAKE_CASE`
  - Private attributes: `_leading_underscore`

### Example Code

```python
from typing import Optional

class WorkflowExecutor:
    """Executes workflow definitions.

    Args:
        config: Configuration dictionary for the executor

    Attributes:
        status: Current execution status
    """

    def __init__(self, config: dict) -> None:
        self._config = config
        self.status = "idle"

    async def execute(self, workflow_id: str) -> Optional[dict]:
        """Execute a workflow by ID.

        Args:
            workflow_id: Unique identifier for the workflow

        Returns:
            Execution result dictionary or None if failed

        Raises:
            WorkflowNotFoundError: If workflow doesn't exist
        """
        # Implementation here
        pass
```

## Testing Guidelines

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_workflow.py

# Run with coverage
pytest --cov=src --cov-report=html

# Run E2E tests only
pytest tests/e2e/

# Run in parallel
pytest -n auto
```

### Writing Tests

- Place unit tests in `tests/`
- Place E2E tests in `tests/e2e/`
- Use descriptive test names: `test_should_execute_workflow_successfully`
- Use fixtures for common setup
- Mock external dependencies
- Aim for >80% code coverage

### Test Example

```python
import pytest
from src.core.workflow.executor import WorkflowExecutor

@pytest.fixture
def executor():
    """Create a workflow executor for testing."""
    config = {"timeout": 30}
    return WorkflowExecutor(config)

def test_should_execute_simple_workflow(executor):
    """Test that executor can run a simple workflow."""
    workflow_id = "test-workflow-123"
    result = await executor.execute(workflow_id)

    assert result is not None
    assert result["status"] == "success"
```

## Pull Request Process

### Before Submitting

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/my-new-feature
   # or
   git checkout -b fix/bug-description
   ```

2. **Make your changes** following coding standards

3. **Write/update tests** for your changes

4. **Run the test suite**:
   ```bash
   pytest
   ruff check src/
   ```

5. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat: add new workflow node type"
   ```

   Follow [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` New feature
   - `fix:` Bug fix
   - `docs:` Documentation changes
   - `test:` Test additions/changes
   - `refactor:` Code refactoring
   - `perf:` Performance improvements
   - `chore:` Maintenance tasks

6. **Push to your fork**:
   ```bash
   git push origin feature/my-new-feature
   ```

### Submitting the PR

1. Go to the [Skynette repository](https://github.com/flyingpurplepizzaeater/Skynette)
2. Click "New Pull Request"
3. Select your branch
4. Fill out the PR template:
   - Clear description of changes
   - Reference related issues (e.g., "Fixes #123")
   - Screenshots (for UI changes)
   - Testing notes
5. Submit and wait for review

### PR Review Process

- A maintainer will review your PR
- Address any requested changes
- Once approved, a maintainer will merge your PR
- Your contribution will be credited in the release notes

### PR Checklist

- [ ] Code follows project style guidelines
- [ ] Tests added/updated and passing
- [ ] Documentation updated (if needed)
- [ ] Commit messages follow conventional commits
- [ ] No merge conflicts
- [ ] PR description is clear and complete

## Issue Reporting

### Before Creating an Issue

1. Search existing issues to avoid duplicates
2. Check if it's already fixed in the latest version
3. Gather relevant information

### Creating a Good Issue

Use the issue templates provided:

**For Bugs:**
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version)
- Error logs/screenshots

**For Features:**
- Problem statement
- Proposed solution
- Use cases and benefits
- Alternatives considered

## Development Workflow

### Branching Strategy

- `master`: Stable production code
- `develop`: Integration branch (if used)
- `feature/*`: New features
- `fix/*`: Bug fixes
- `docs/*`: Documentation updates
- `test/*`: Test improvements

### Keeping Your Fork Updated

```bash
# Fetch upstream changes
git fetch upstream

# Merge into your local master
git checkout master
git merge upstream/master

# Push to your fork
git push origin master
```

## Community

### Getting Help

- GitHub Issues for bugs and features
- GitHub Discussions for questions
- Check existing documentation

### Recognition

Contributors are recognized in:
- Release notes
- Contributors section of README
- GitHub contributors page

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Skynette! Your efforts help make workflow automation accessible to everyone.
