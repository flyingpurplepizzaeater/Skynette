# Architecture

**Analysis Date:** 2026-01-17

## Pattern Overview

**Overall:** Layered Monolith with Plugin-Ready Architecture

**Key Characteristics:**
- Flet-based desktop GUI with clear separation between UI, Core, and Data layers
- Node-based workflow automation engine with pluggable node types
- Multi-provider AI gateway with auto-fallback and priority management
- RAG (Retrieval Augmented Generation) subsystem for knowledge bases
- Singleton pattern for global services (Gateway, Storage, Registry, Assistant)

## Layers

**UI Layer:**
- Purpose: User interface built with Flet framework
- Location: `src/ui/`
- Contains: App shell, views, components, dialogs, theme
- Depends on: Core layer (workflow models, executor), Data layer (storage)
- Used by: Entry points (`skynette.py`, `src/main.py`)

**Core Layer:**
- Purpose: Workflow engine, nodes, execution logic, expressions
- Location: `src/core/`
- Contains: Workflow models, executor, node registry, node implementations, expression parser
- Depends on: AI layer (for AI nodes), Data layer (for storage)
- Used by: UI layer, CLI

**AI Layer:**
- Purpose: Multi-provider AI abstraction with gateway pattern
- Location: `src/ai/`
- Contains: Gateway, providers (OpenAI, Anthropic, Local, LM Studio), assistant, cost tracking
- Depends on: External APIs, local model runtime
- Used by: Core layer (AI nodes), UI layer (assistant panel)

**RAG Layer:**
- Purpose: Document processing, vector storage, semantic search
- Location: `src/rag/`
- Contains: Document processor, embeddings, ChromaDB client, storage models
- Depends on: AI layer (for embeddings), ChromaDB
- Used by: Core layer (RAG nodes), UI layer (knowledge bases view)

**Data Layer:**
- Purpose: Persistence of workflows, settings, credentials, usage logs
- Location: `src/data/`
- Contains: WorkflowStorage class with SQLite + YAML hybrid storage
- Depends on: SQLite, filesystem
- Used by: All layers

**Plugins Layer (Planned):**
- Purpose: Third-party extensibility
- Location: `src/plugins/`
- Contains: SDK placeholder, future marketplace integration
- Depends on: Core layer (node system)
- Used by: Future plugin ecosystem

## Data Flow

**Workflow Execution Flow:**

1. User triggers workflow (manual, schedule, webhook) via UI or trigger
2. `WorkflowExecutor.execute()` receives workflow and trigger data
3. Executor gets execution order via topological sort (`workflow.get_execution_order()`)
4. For each node: resolve expressions, get handler from registry, execute
5. Node results stored in context (`$nodes`, `$prev`, `$vars`)
6. Execution record saved to SQLite via `WorkflowStorage`

**AI Request Flow:**

1. Node or assistant calls `AIGateway.chat()` or `AIGateway.generate()`
2. Gateway selects provider by priority and capability
3. Provider makes API call (OpenAI, Anthropic, local model)
4. Response returned; usage logged for cost tracking
5. Auto-fallback to next provider on failure if enabled

**State Management:**
- Workflow state: YAML files + SQLite metadata
- Runtime state: In-memory context dict during execution
- Conversation state: `ChatNode._conversations` class variable
- Settings: SQLite settings table via `WorkflowStorage`
- AI provider state: `AIGateway.providers` dict with priority ordering

## Key Abstractions

**Workflow:**
- Purpose: Complete workflow definition with nodes, connections, variables
- Examples: `src/core/workflow/models.py`
- Pattern: Pydantic model with YAML serialization, topological sort for execution order

**Node System:**
- Purpose: Pluggable workflow actions with config and execution
- Examples: `src/core/nodes/base.py`, `src/core/nodes/ai/chat.py`
- Pattern: Abstract `BaseNode` class with `execute()` method, NodeField for config schema

**Provider:**
- Purpose: AI service abstraction for multiple backends
- Examples: `src/ai/providers/base.py`, `src/ai/providers/openai.py`
- Pattern: Abstract `BaseProvider` with capabilities enum, registered in `AIGateway`

**Storage:**
- Purpose: Unified persistence layer
- Examples: `src/data/storage.py`
- Pattern: Singleton `WorkflowStorage` with YAML files for workflows, SQLite for metadata

## Entry Points

**Desktop Application:**
- Location: `skynette.py` (root)
- Triggers: Double-click, command line
- Responsibilities: Logging setup, import SkynetteApp, run Flet

**Module Entry:**
- Location: `src/main.py`
- Triggers: `python -m src.main`, `flet run src/main.py`
- Responsibilities: Test mode configuration, create SkynetteApp, run Flet

**CLI (Planned):**
- Location: `src/cli.py`
- Triggers: Command line
- Responsibilities: Headless workflow execution, management commands

## Error Handling

**Strategy:** Node-level error handling with configurable strategies

**Patterns:**
- Per-node `on_error` config: `stop`, `continue`, `retry`
- Failed nodes return `ExecutionResult` with `success=False` and error message
- Workflow execution status: `pending`, `running`, `completed`, `failed`, `cancelled`
- AI provider errors trigger auto-fallback to next available provider
- UI displays friendly error messages via `SkynetAssistant.explain_error()`

## Cross-Cutting Concerns

**Logging:**
- Python logging module configured in `skynette.py`
- Log files in `logs/` directory with timestamps
- Per-module loggers (e.g., `logging.getLogger(__name__)`)

**Validation:**
- Pydantic models for workflow structures (`Workflow`, `WorkflowNode`, `WorkflowConnection`)
- Node input validation via `NodeField` definitions
- Expression validation via `ExpressionParser`

**Authentication:**
- Credentials stored encrypted in SQLite `credentials` table
- Per-service credential types (API keys, OAuth tokens)
- `requires_credentials` field on node definitions

**Expression Resolution:**
- `{{expression}}` syntax in node configs
- `resolve_expressions()` called before node execution
- Context: `$trigger`, `$vars`, `$nodes`, `$prev`

---

*Architecture analysis: 2026-01-17*
