# Codebase Structure

**Analysis Date:** 2026-01-17

## Directory Layout

```
skynette-repo/
├── src/                    # Main source code
│   ├── ai/                 # AI providers and gateway
│   ├── core/               # Workflow engine and nodes
│   ├── data/               # Storage layer
│   ├── plugins/            # Plugin SDK (placeholder)
│   ├── rag/                # RAG/knowledge base system
│   ├── ui/                 # Flet UI components
│   ├── utils/              # Shared utilities
│   ├── cli.py              # CLI entry (planned)
│   ├── main.py             # Module entry point
│   └── updater.py          # Auto-update system
├── tests/                  # Test suite
│   ├── e2e/                # End-to-end Playwright tests
│   ├── integration/        # Integration tests
│   ├── unit/               # Unit tests
│   ├── fixtures/           # Test fixtures
│   └── mocks/              # Mock implementations
├── assets/                 # Static assets
│   ├── fonts/              # Custom fonts
│   ├── icons/              # Application icons
│   └── images/             # UI images
├── docs/                   # Documentation
│   ├── development/        # Dev guides
│   ├── plans/              # Feature plans
│   ├── proposals/          # Design proposals
│   └── user-guide/         # User documentation
├── scripts/                # Build and utility scripts
├── workflows/              # Sample workflow files
├── logs/                   # Runtime logs (gitignored)
├── build/                  # PyInstaller build output
├── dist/                   # Distribution packages
├── .planning/              # GSD planning documents
│   └── codebase/           # Codebase analysis docs
├── skynette.py             # Root entry point
├── pyproject.toml          # Project configuration
├── requirements.txt        # Dependencies
└── *.py (root)             # Build scripts, tests
```

## Directory Purposes

**`src/ai/`:**
- Purpose: AI provider abstraction layer
- Contains: Gateway, providers, assistant, cost tracking, security
- Key files:
  - `gateway.py`: AIGateway class, provider management
  - `providers/base.py`: BaseProvider abstract class
  - `providers/openai.py`, `anthropic.py`, `local.py`: Provider implementations
  - `assistant/skynet.py`: SkynetAssistant chat interface
  - `cost.py`: Cost calculator for API usage
  - `storage.py`: AI-specific storage (usage logs)

**`src/core/`:**
- Purpose: Workflow engine and execution
- Contains: Workflow models, executor, node system, expressions
- Key files:
  - `workflow/models.py`: Workflow, WorkflowNode, WorkflowConnection
  - `workflow/executor.py`: WorkflowExecutor, DebugExecutor
  - `nodes/base.py`: BaseNode, NodeField, NodeDefinition
  - `nodes/registry.py`: NodeRegistry singleton
  - `expressions/parser.py`: Expression parser for `{{...}}`

**`src/core/nodes/`:**
- Purpose: All workflow node implementations
- Contains: Node types organized by category
- Subdirectories:
  - `ai/`: AI nodes (chat, summarize, extract, classify)
  - `apps/`: App integrations (100+ nodes for Slack, GitHub, etc.)
  - `coding/`: Dev tools (git, docker, CI/CD)
  - `data/`: File operations (read, write)
  - `flow/`: Control flow (if_else, set_variable, log_debug)
  - `http/`: HTTP request node
  - `rag/`: RAG nodes (ingest, query)
  - `triggers/`: Trigger nodes (manual, schedule)
  - `utility/`: Transform node

**`src/data/`:**
- Purpose: Persistence layer
- Contains: Storage classes
- Key files:
  - `storage.py`: WorkflowStorage (YAML + SQLite)

**`src/rag/`:**
- Purpose: RAG subsystem for knowledge bases
- Contains: Document processing, embeddings, vector store
- Key files:
  - `processor.py`: DocumentProcessor (chunking)
  - `embeddings.py`: Embedding generation
  - `chromadb_client.py`: ChromaDB vector store client
  - `models.py`: Collection, Document, Chunk models
  - `storage.py`: RAG-specific storage

**`src/ui/`:**
- Purpose: Flet-based user interface
- Contains: App shell, views, components, theme
- Key files:
  - `app.py`: SkynetteApp main class (~2500 lines)
  - `theme.py`: SkynetteTheme and Theme classes
  - `views/`: View classes for each screen
  - `components/`: Reusable UI components
  - `dialogs/`: Modal dialogs
  - `models/`: UI-specific data models

**`src/ui/views/`:**
- Purpose: Main screen views
- Contains: Page-level components
- Files:
  - `workflows.py`: Workflow list/dashboard
  - `workflow_editor.py`: Canvas-based editor
  - `ai_hub.py`: AI Hub (models, providers)
  - `knowledge_bases.py`: RAG collection management
  - `settings.py`: App settings
  - `runs.py`: Execution history
  - `agents.py`: Agent management
  - `devtools.py`: Developer tools
  - `plugins.py`: Plugin marketplace
  - `credentials.py`: Credential management
  - `simple_mode.py`: Simplified UI mode
  - `usage_dashboard.py`: AI usage stats

**`tests/`:**
- Purpose: Test suite
- Contains: Unit, integration, E2E tests
- Key patterns:
  - `unit/test_*.py`: Unit tests for specific modules
  - `integration/test_*.py`: Cross-module integration tests
  - `e2e/test_*.py`: Playwright browser tests
  - `fixtures/`: Test data factories
  - `mocks/`: Mock implementations for testing

## Key File Locations

**Entry Points:**
- `skynette.py`: Root entry (frozen app support, logging)
- `src/main.py`: Module entry (test mode support)

**Configuration:**
- `pyproject.toml`: Project metadata, dependencies, tool config
- `requirements.txt`: Pip requirements
- `.pre-commit-config.yaml`: Pre-commit hooks

**Core Logic:**
- `src/core/workflow/executor.py`: Workflow execution engine
- `src/core/nodes/registry.py`: Node type registry
- `src/ai/gateway.py`: AI provider gateway
- `src/data/storage.py`: Data persistence

**Testing:**
- `tests/conftest.py`: Shared pytest fixtures
- `tests/e2e/conftest.py`: Playwright fixtures

## Naming Conventions

**Files:**
- snake_case.py for all Python files
- Module files match class names (e.g., `storage.py` contains `WorkflowStorage`)
- Node files named after service (e.g., `slack.py`, `github.py`)

**Directories:**
- lowercase with underscores where needed
- Category-based grouping (e.g., `nodes/apps/`, `nodes/ai/`)

**Classes:**
- PascalCase (e.g., `WorkflowExecutor`, `BaseNode`)
- Node classes: `{Service}{Action}Node` (e.g., `SlackSendMessageNode`)
- Views: `{Name}View` (e.g., `WorkflowsView`)

**Functions/Methods:**
- snake_case (e.g., `execute_workflow`, `get_handler`)
- Private methods: `_method_name`

**Variables:**
- snake_case for locals and module-level
- SCREAMING_SNAKE_CASE for constants

## Where to Add New Code

**New Workflow Node:**
1. Create file in appropriate `src/core/nodes/{category}/` directory
2. Extend `BaseNode` (or category base like `AINode`, `DataNode`)
3. Define `type`, `name`, `category`, `description`, `icon`, `color`
4. Implement `get_inputs()`, `get_outputs()`, `execute()`
5. Add to category's `__init__.py` exports and `*_NODES` list
6. Node auto-registers via `NodeRegistry._load_builtin_nodes()`

**New AI Provider:**
1. Create `src/ai/providers/{provider_name}.py`
2. Extend `BaseProvider`
3. Implement `initialize()`, `is_available()`, `generate()`, `chat()`
4. Add capabilities to `capabilities` set
5. Register in `src/ai/__init__.py` and `setup_default_providers()`

**New UI View:**
1. Create `src/ui/views/{view_name}.py`
2. Extend `ft.Column` or `ft.Container`
3. Implement `build()` method returning Flet controls
4. Add to `src/ui/views/__init__.py`
5. Add navigation entry in `src/ui/app.py`

**New Test:**
- Unit: `tests/unit/test_{module}.py`
- Integration: `tests/integration/test_{feature}.py`
- E2E: `tests/e2e/test_{screen}.py`

**Utilities:**
- Shared helpers: `src/utils/`

## Special Directories

**`logs/`:**
- Purpose: Runtime log files
- Generated: Yes, at runtime
- Committed: No (gitignored)

**`build/` and `dist/`:**
- Purpose: PyInstaller output
- Generated: Yes, by build scripts
- Committed: No (gitignored)

**`.planning/`:**
- Purpose: GSD planning documents
- Generated: By GSD commands
- Committed: Yes

**`workflows/`:**
- Purpose: Sample workflow YAML files
- Generated: No, hand-crafted
- Committed: Yes

**`venv/`:**
- Purpose: Virtual environment
- Generated: Yes
- Committed: No (gitignored)

---

*Structure analysis: 2026-01-17*
