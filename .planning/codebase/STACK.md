# Technology Stack

**Analysis Date:** 2025-01-17

## Languages

**Primary:**
- Python 3.11+ - Core application logic, UI, AI integrations, workflow engine

**Secondary:**
- YAML - Workflow definitions stored in `~/.skynette/workflows/`
- SQL - SQLite database queries in `src/data/storage.py`

## Runtime

**Environment:**
- Python 3.11 minimum, 3.12 supported
- CPython interpreter

**Package Manager:**
- pip with pyproject.toml (PEP 517/518 compliant)
- hatchling build backend
- Lockfile: Not present (uses version ranges in pyproject.toml)

## Frameworks

**Core:**
- Flet 0.25.0+ - Cross-platform UI framework (Flutter-based)
- FastAPI 0.110.0+ - Webhook server and REST API
- Uvicorn 0.27.0+ - ASGI server for FastAPI

**Testing:**
- pytest 8.0.0+ - Test runner
- pytest-asyncio 0.23.0+ - Async test support
- pytest-playwright 0.5.0+ - E2E browser testing
- pytest-cov 4.1.0+ - Coverage reporting
- pytest-xdist 3.5.0+ - Parallel test execution

**Build/Dev:**
- Ruff 0.3.0+ - Linting and formatting (replaces black, isort, flake8)
- mypy 1.8.0+ - Static type checking
- bandit 1.7.0+ - Security scanning
- PyInstaller 6.0.0+ - Executable bundling
- pre-commit - Git hooks for code quality

## Key Dependencies

**Critical:**
- `flet>=0.25.0` - UI framework, entire GUI depends on it
- `pydantic>=2.0.0` - Data validation and settings management
- `sqlalchemy>=2.0.0` - Database ORM (async mode with aiosqlite)
- `httpx>=0.27.0` - Async HTTP client for all external API calls

**AI/ML:**
- `openai>=1.0.0` - OpenAI API client (GPT-4, embeddings, DALL-E)
- `anthropic>=0.25.0` - Anthropic Claude API client
- `llama-cpp-python>=0.2.0` - Local GGUF model inference
- `sentence-transformers>=2.2.0` - Local embeddings (all-MiniLM-L6-v2)
- `chromadb>=0.5.0` - Vector database for RAG
- `google-generativeai>=0.5.0` - Google Gemini API
- `groq>=0.5.0` - Groq API for fast inference

**Cloud/Infrastructure:**
- `boto3>=1.28.0` - AWS SDK (S3 integration)
- `google-api-python-client>=2.0.0` - Google Sheets/Drive integration
- `google-auth>=2.0.0` - Google authentication

**Workflow Engine:**
- `apscheduler>=3.10.0` - Scheduled workflow triggers
- `watchdog>=4.0.0` - File system monitoring
- `jinja2>=3.1.0` - Template expressions in workflows
- `jsonschema>=4.21.0` - JSON schema validation

**File Processing:**
- `pandas>=2.0.0` - Data manipulation
- `openpyxl>=3.1.0` - Excel file handling
- `pypdf>=4.0.0` - PDF processing

**Security:**
- `cryptography>=41.0.0` - Credential encryption
- `keyring>=24.0.0` - OS-level secret storage

## Configuration

**Environment:**
- `python-dotenv>=1.0.0` - Loads `.env` files
- Environment variables for API keys:
  - `OPENAI_API_KEY` - OpenAI provider
  - `ANTHROPIC_API_KEY` - Anthropic provider
  - `SKYNETTE_TEST_MODE` - Test mode flag
  - `SKYNETTE_MOCK_AI` - Mock AI providers
  - `SKYNETTE_DATA_DIR` - Override data directory

**Build:**
- `pyproject.toml` - Project configuration, dependencies, tool settings
- `skynette.spec` - PyInstaller specification for Windows builds
- `build_windows.py`, `build_macos.py`, `build_linux.py` - Platform-specific build scripts

## Data Storage

**Local Database:**
- SQLite via `aiosqlite>=0.19.0`
- Location: `~/.skynette/skynette.db`
- Tables: workflows, executions, settings, credentials, ai_providers, ai_usage, local_models, ai_budgets

**Workflow Files:**
- YAML format in `~/.skynette/workflows/`
- Format defined in `src/core/workflow/models.py`

**AI Models:**
- Local GGUF models: `~/skynette/models/`
- ChromaDB vectors: Path configurable in RAG service

## Platform Requirements

**Development:**
- Python 3.11+
- pip for dependency management
- Git for version control
- Optional: CUDA for GPU-accelerated local models

**Production:**
- Windows: Bundled as .exe via PyInstaller
- macOS: Bundled as .app
- Linux: AppImage or direct Python execution
- No external database required (SQLite embedded)

## Optional Dependency Groups

Install with `pip install skynette[group]`:

| Group | Purpose | Key Packages |
|-------|---------|--------------|
| `ai` | AI/ML features | openai, anthropic, chromadb, sentence-transformers |
| `databases` | External DB connections | asyncpg, aiomysql, motor |
| `cloud` | Cloud integrations | boto3, google-api-python-client |
| `dev` | Development tools | pytest, ruff, mypy, playwright |
| `all` | Everything | All optional dependencies |

---

*Stack analysis: 2025-01-17*
