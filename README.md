# Skynette - Open Source Workflow Automation Platform

[![CI](https://github.com/flyingpurplepizzaeater/Skynette/actions/workflows/ci.yml/badge.svg)](https://github.com/flyingpurplepizzaeater/Skynette/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/flyingpurplepizzaeater/Skynette/branch/master/graph/badge.svg)](https://codecov.io/gh/flyingpurplepizzaeater/Skynette)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An intelligent, AI-powered workflow automation platform that rivals n8n, combining visual workflow building with multi-model AI capabilities. Built with Python and Flet for cross-platform desktop and mobile deployment.

## Features

### Dual-Mode Workflow Editor
- **Simple Mode**: Step-by-step wizard for beginners
- **Advanced Mode**: Full node canvas with drag-and-drop for power users
- One-click toggle between modes

### Multi-AI Model Support
- **Local Models**: Run LLaMA, Mistral, Phi via llama.cpp (free, private)
- **Cloud Providers**: OpenAI, Anthropic, Google AI, Mistral API
- **AI Gateway**: Unified interface with auto-fallback across providers
- **Model Hub**: Download models from Hugging Face, Ollama, GitHub, or URLs

### Skynet Assistant
- AI chat agent for natural language workflow building
- "Create a workflow that checks my email and sends Slack notifications"
- Context-aware suggestions and debugging help

### Comprehensive Node Library
- **Triggers**: Manual, Schedule (cron), Webhook, File Watch
- **AI Nodes**: Text Generation, Image Generation, Embeddings, RAG
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

## Installation

### From Source
```bash
# Clone repository
git clone https://github.com/yourusername/skynette.git
cd skynette

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run application
flet run src/main.py
```

### Pre-built Executables
Download from [Releases](https://github.com/yourusername/skynette/releases):
- Windows: `skynette-windows.exe`
- macOS: `skynette-macos.app`
- Linux: `skynette-linux.AppImage`

## Quick Start

1. **Launch Skynette** - Opens to the workflow dashboard
2. **Create New Workflow** - Click "+" or use Skynet Assistant
3. **Add Nodes** - Drag from node palette or describe in chat
4. **Connect Nodes** - Draw connections between outputs and inputs
5. **Configure** - Click nodes to set parameters
6. **Execute** - Click Run or set up a trigger

### Example: Email Notification Workflow
```
Manual Trigger → HTTP Request (fetch data) → If/Else (check condition) → Send Email
```

## Architecture

```
src/
├── main.py              # Application entry point
├── ui/
│   ├── app.py           # Main Flet application
│   ├── theme.py         # UI theme and styling
│   └── views/           # View components
├── core/
│   ├── workflow/        # Workflow models and executor
│   ├── nodes/           # Node implementations
│   ├── expressions/     # Expression parser ({{$prev.data}})
│   └── errors/          # Error handling
├── ai/
│   ├── gateway.py       # Unified AI interface
│   ├── providers/       # Provider adapters
│   └── models/          # Local model management
├── plugins/             # Plugin system
├── data/                # Database and storage
└── cloud/               # Cloud sync services
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
theme: dark
ai:
  default_provider: local
  openai_key: sk-...
  anthropic_key: sk-ant-...
storage:
  workflows_dir: ~/skynette/workflows
  models_dir: ~/skynette/models
cloud:
  enabled: false
  sync_interval: 300
```

## Roadmap

- [x] Phase 1: Core foundation (workflow engine, basic nodes)
- [ ] Phase 2: AI integration (local models, cloud providers)
- [ ] Phase 3: App integrations (30+ connectors)
- [ ] Phase 4: Cloud features (sync, sharing, marketplace)
- [ ] Phase 5: Mobile apps (iOS, Android via Flet)

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup
```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check src/
```

## License

MIT License - See [LICENSE](LICENSE) for details.

## Acknowledgments

- Inspired by [n8n](https://n8n.io), [Activepieces](https://activepieces.com), [Langflow](https://langflow.org)
- Built with [Flet](https://flet.dev) for cross-platform UI
- AI powered by [llama.cpp](https://github.com/ggerganov/llama.cpp)
