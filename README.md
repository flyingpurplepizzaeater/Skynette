# Skynette - Open Source Workflow Automation Platform

[![CI](https://github.com/flyingpurplepizzaeater/Skynette/actions/workflows/ci.yml/badge.svg)](https://github.com/flyingpurplepizzaeater/Skynette/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/flyingpurplepizzaeater/Skynette/branch/main/graph/badge.svg)](https://codecov.io/gh/flyingpurplepizzaeater/Skynette)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Release](https://img.shields.io/github/v/release/flyingpurplepizzaeater/Skynette)](https://github.com/flyingpurplepizzaeater/Skynette/releases)

An intelligent, AI-powered workflow automation platform that rivals n8n, combining visual workflow building with multi-model AI capabilities. Built with Python and Flet for cross-platform desktop and mobile deployment.

## Features

### AI Hub - Centralized AI Management
- **Setup Wizard**: First-time guided configuration for AI providers
- **Provider Management**: OpenAI, Anthropic, Google AI, Groq, and local models
- **Model Library**: Download and manage local AI models with progress tracking
- **Usage Dashboard**: Real-time analytics, token usage, and cost tracking across all providers
- **Secure Storage**: API keys stored in system keyring for security

### Knowledge Bases (RAG)
- **Create Collections**: Organize documents into searchable knowledge bases
- **Upload Documents**: Support for markdown and text files with batch processing
  - File picker, drag & drop, or folder upload
  - Parallel processing (5 concurrent files) with progress tracking
- **Semantic Search**: Query your documents using natural language
- **Local Embeddings**: Free, private embedding model (all-MiniLM-L6-v2, 384 dimensions)
- **ChromaDB Integration**: High-performance vector database for semantic search
- **Collection Management**: View statistics, document counts, and storage usage

See [User Guide](docs/user-guide/knowledge-bases.md) for details.

### Dual-Mode Workflow Editor
- **Simple Mode**: Step-by-step wizard for beginners
- **Advanced Mode**: Full node canvas with drag-and-drop for power users
- One-click toggle between modes

### Multi-AI Model Support
- **Local Models**: Run LLaMA, Mistral, Phi via llama.cpp (free, private)
- **Cloud Providers**: OpenAI, Anthropic, Google AI, Groq
- **AI Gateway**: Unified interface with auto-fallback across providers
- **Model Hub**: Download models with progress tracking and metadata

### Comprehensive Node Library
- **Triggers**: Manual, Schedule (cron), Webhook, File Watch
- **AI Nodes**: Text Generation, Image Generation, Embeddings
- **RAG Nodes**: Ingest Documents, Query Knowledge Bases
- **Data**: Read/Write Files, JSON Transform, CSV, Database
- **HTTP**: REST API calls, GraphQL, WebSockets
- **Flow Control**: If/Else, Switch, Loop, Merge, Error Handler
- **Integrations**: 30+ built-in apps, extensible via plugins

### Plugin Marketplace
- Community-contributed nodes and integrations
- Sandboxed Python plugin SDK
- Revenue sharing for premium plugins

### Cloud Sync (Optional)
- Sync workflows across devices
- Share workflows with team members
- Cloud execution for scheduled workflows

## Requirements

### System Requirements
- **Operating System**: Windows 10+, macOS 11+, or Linux (Ubuntu 20.04+)
- **Python**: 3.11 or higher
- **RAM**: 4GB minimum, 8GB recommended (16GB for local AI models)
- **Storage**: 2GB for application, 4-8GB per local AI model
- **GPU** (optional): NVIDIA GPU with CUDA for faster local model inference

### Python Dependencies
All dependencies are automatically installed via pip. Key packages include:
- **UI**: Flet 0.25+
- **AI**: llama-cpp-python, openai, anthropic, google-generativeai
- **RAG**: chromadb, sentence-transformers
- **Security**: keyring (for secure API key storage)
- **Data**: SQLAlchemy, pandas, pyyaml
- **Workflow**: apscheduler, watchdog, jinja2
- **Testing**: pytest, playwright (E2E tests)

See [pyproject.toml](pyproject.toml) for complete list.

## Installation

### Method 1: From Source (Recommended for Development)

```bash
# Clone the repository
git clone https://github.com/flyingpurplepizzaeater/Skynette.git
cd Skynette

# Create and activate virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install the package with dependencies
pip install -e ".[dev]"

# Run the application
python src/main.py
# or
flet run src/main.py
```

### Method 2: Install from PyPI (Coming Soon)

```bash
pip install skynette
skynette
```

### Method 3: Pre-built Executables (Coming Soon)

Download from [Releases](https://github.com/flyingpurplepizzaeater/Skynette/releases):
- **Windows**: `Skynette-Setup.exe`
- **macOS**: `Skynette.dmg`
- **Linux**: `Skynette.AppImage`

Double-click to install and launch.

## Quick Start

### First Time Setup

1. **Launch Skynette**:
   ```bash
   python src/main.py
   ```

2. **Complete AI Hub Setup Wizard** (First launch):
   - Select AI providers to configure (OpenAI, Anthropic, Google AI, Groq, Local Models)
   - Enter API keys (securely stored in system keyring)
   - Or skip to configure later in **AI Hub** → **My Providers**

3. **Download Models** (Optional - for local AI):
   - Navigate to **AI Hub** → **Model Library** → **Download**
   - Choose from recommended models or enter custom URL
   - Track download progress in real-time

4. **Create Your First Workflow**:
   - Click **New Workflow** button on the dashboard
   - Choose between Simple Mode (wizard) or Advanced Mode (canvas)

### Building a Workflow

#### Option 1: Using Skynet Assistant (Easiest)

1. Click the **Assistant** tab
2. Describe your workflow in natural language:
   ```
   "Create a workflow that fetches weather data from an API every morning at 8 AM
   and sends me a notification"
   ```
3. Review the generated workflow
4. Click **Create Workflow** to build it automatically

#### Option 2: Visual Editor

1. **Add Trigger Node**:
   - Drag **Schedule Trigger** from the node palette
   - Configure: `0 8 * * *` (8 AM daily)

2. **Add Action Nodes**:
   - Drag **HTTP Request** node
   - Set URL: `https://api.weather.com/...`
   - Connect from trigger to HTTP node

3. **Add Logic** (optional):
   - Drag **If/Else** node to add conditions
   - Example: If temperature < 10°C, add cold weather warning

4. **Add Output**:
   - Drag **Send Notification** node
   - Configure notification settings

5. **Execute**:
   - Click **Run** to test immediately
   - Or enable the trigger for automatic execution

### Example Workflows

#### 1. Email Notification Workflow
```
Manual Trigger → HTTP Request (fetch data) → If/Else (check condition) → Send Email
```

#### 2. Data Processing Pipeline
```
File Watch Trigger → Read CSV → Transform Data → AI Analysis → Write to Database → Send Slack Message
```

#### 3. Content Generation
```
Schedule Trigger → AI Text Generation → Format Output → Post to Blog → Tweet Summary
```

#### 4. Smart Home Automation
```
Webhook Trigger → Check Sensor Data → If/Else Logic → Control Smart Devices → Log Event
```

## Architecture

```
src/
├── main.py              # Application entry point
├── ui/
│   ├── app.py           # Main Flet application
│   ├── theme.py         # UI theme and styling (light/dark mode)
│   ├── views/           # View components
│   │   ├── ai_hub.py    # AI Hub (5 tabs: Setup, Providers, Library, Usage, Knowledge Bases)
│   │   ├── knowledge_bases.py  # RAG collection management
│   │   └── usage_dashboard.py  # Usage analytics and cost tracking
│   ├── components/      # Reusable UI components
│   ├── dialogs/         # Modal dialogs (upload, query, collection)
│   └── models/          # UI data models
├── core/
│   ├── workflow/        # Workflow models and executor
│   ├── nodes/           # Node implementations
│   │   └── rag/         # RAG workflow nodes (ingest, query)
│   ├── expressions/     # Expression parser ({{$prev.data}})
│   └── errors/          # Error handling
├── ai/
│   ├── gateway.py       # Unified AI interface
│   ├── providers/       # Provider adapters (OpenAI, Anthropic, etc.)
│   ├── models/          # Local model management
│   └── security.py      # Secure API key storage (keyring)
├── rag/                 # RAG (Retrieval Augmented Generation)
│   ├── service.py       # High-level RAG service
│   ├── chromadb_client.py  # Vector database client
│   ├── embeddings.py    # Local embedding model manager
│   ├── processor.py     # Document processing and chunking
│   ├── storage.py       # SQLite metadata storage
│   └── models.py        # RAG data models
├── plugins/             # Plugin system
├── data/                # Database and storage
└── tests/               # Comprehensive test suite (299 tests)
    ├── unit/            # Unit tests (279 tests)
    ├── integration/     # Integration tests (20 tests)
    └── e2e/             # Playwright E2E tests
```

## Node Development

Create custom nodes by extending `BaseNode`:

```python
from src.core.nodes.base import BaseNode, NodeField, FieldType

class MyCustomNode(BaseNode):
    type = "my-custom-node"
    name = "My Custom Node"
    category = "Custom"
    description = "Does something custom"

    inputs = [
        NodeField(name="input_data", label="Input", type=FieldType.STRING)
    ]
    outputs = [
        NodeField(name="result", label="Result", type=FieldType.JSON)
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        input_data = config.get("input_data", "")
        # Your logic here
        return {"result": {"processed": input_data}}
```

## Configuration

Settings stored in `~/.skynette/config.yaml`:

```yaml
theme: dark  # or light
ai:
  default_provider: local
  # API keys now stored securely in system keyring via AI Hub
storage:
  workflows_dir: ~/skynette/workflows
  models_dir: ~/skynette/models
  rag_storage: ~/.skynette/rag  # ChromaDB and embeddings
rag:
  embedding_model: all-MiniLM-L6-v2  # Local embedding model
  chunk_size: 1000  # Characters per chunk
  chunk_overlap: 200  # Overlap between chunks
  max_concurrent_uploads: 5  # Parallel processing limit
cloud:
  enabled: false
  sync_interval: 300
```

**Security Note**: API keys are stored in your system's secure keyring (Windows Credential Manager, macOS Keychain, Linux Secret Service), not in plain text config files.

## Roadmap

### Completed ✅
- [x] **Phase 1**: Core foundation (workflow engine, basic nodes)
- [x] **Phase 2**: Advanced workflow editor (simple/advanced modes)
- [x] **Phase 3**: UI polish and production readiness
- [x] **Phase 4**: AI Integration
  - [x] Sprint 1: AI core, providers, security
  - [x] Sprint 2: AI Hub UI, model management
  - [x] Sprint 3: Usage dashboard and cost analytics
- [x] **Phase 5**: RAG Integration
  - [x] Sprint 1: RAG core (ChromaDB, embeddings, document processing)
  - [x] Sprint 4: Knowledge Bases UI and polish

### In Progress 🚧
- [ ] **Phase 6**: App integrations and workflow nodes
  - [ ] Email (Gmail, Outlook)
  - [ ] Communication (Slack, Discord, Teams)
  - [ ] File storage (Google Drive, Dropbox, OneDrive)
  - [ ] Databases (PostgreSQL, MySQL, MongoDB)
  - [ ] And 20+ more integrations

### Planned 📋
- [ ] **Phase 7**: Cloud features (sync, sharing, marketplace)
- [ ] **Phase 8**: Mobile apps (iOS, Android via Flet)
- [ ] **Phase 9**: Enterprise features (SSO, audit logs, roles)

See [docs/plans/](docs/plans/) for detailed implementation plans.

## Documentation

### User Guides
- **[Knowledge Bases User Guide](docs/user-guide/knowledge-bases.md)**: Creating collections, uploading documents, semantic search
- **[AI Provider Setup](docs/AI_PROVIDERS.md)**: Configure OpenAI, Anthropic, Google AI, Groq, and local models

### Developer Documentation
- **[RAG UI Architecture](docs/development/rag-ui-architecture.md)**: Component hierarchy, data flows, and testing
- **[Contributing Guide](CONTRIBUTING.md)**: How to contribute to Skynette
- **[Implementation Plans](docs/plans/)**: Detailed sprint plans and designs

### Quick Links
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Example Workflows](#example-workflows)
- [Configuration](#configuration)
- [Roadmap](#roadmap)

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup
```bash
# Clone and install
git clone https://github.com/flyingpurplepizzaeater/Skynette.git
cd Skynette
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -e ".[dev]"

# Run tests (299 total: 279 unit + 20 integration)
pytest --cov=src --cov-report=term-missing

# Run only unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run E2E tests (requires Playwright)
playwright install --with-deps chromium
pytest tests/e2e/

# Run linting
ruff check src/
ruff format --check src/
```

### Test Coverage
- **Unit Tests**: 279 tests covering individual components
- **Integration Tests**: 20 tests for multi-component workflows
- **E2E Tests**: Playwright-based browser automation tests
- **Total**: 299 tests with comprehensive coverage

## License

MIT License - See [LICENSE](LICENSE) for details.

## Acknowledgments

- Inspired by [n8n](https://n8n.io), [Activepieces](https://activepieces.com), [Langflow](https://langflow.org)
- Built with [Flet](https://flet.dev) for cross-platform UI
- AI powered by [llama.cpp](https://github.com/ggerganov/llama.cpp)
