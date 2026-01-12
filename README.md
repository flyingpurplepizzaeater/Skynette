# Skynette - Open Source Workflow Automation Platform

[![CI](https://github.com/flyingpurplepizzaeater/Skynette/actions/workflows/ci.yml/badge.svg)](https://github.com/flyingpurplepizzaeater/Skynette/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/flyingpurplepizzaeater/Skynette/branch/master/graph/badge.svg)](https://codecov.io/gh/flyingpurplepizzaeater/Skynette)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An intelligent, AI-powered workflow automation platform that rivals n8n, combining visual workflow building with multi-model AI capabilities. Built with Python and Flet for cross-platform desktop and mobile deployment.

## Features

### Knowledge Bases (RAG)
- **Create Collections**: Organize documents into searchable knowledge bases
- **Upload Documents**: Support for markdown and text files (more formats coming)
- **Semantic Search**: Query your documents using natural language
- **Local Embeddings**: Free, private embedding model (all-MiniLM-L6-v2)
- **Real-time Progress**: Track upload progress with detailed status

See [User Guide](docs/user-guide/knowledge-bases.md) for details.

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
- **Data**: SQLAlchemy, pandas, pyyaml
- **Workflow**: apscheduler, watchdog, jinja2

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

2. **Configure AI Provider** (Optional but recommended):
   - Navigate to **Settings** → **AI Providers**
   - Choose between:
     - **Local Models**: Free, private, but requires model download
     - **Cloud Providers**: Fast, powerful, but requires API key
   - See [AI Provider Setup Guide](docs/AI_PROVIDERS.md) for detailed instructions

3. **Create Your First Workflow**:
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

## Documentation

### Guides
- **[AI Provider Setup](docs/AI_PROVIDERS.md)**: Configure OpenAI, Anthropic, Google AI, local models, and more
- **[Contributing Guide](CONTRIBUTING.md)**: How to contribute to Skynette
- **[Architecture Overview](docs/ARCHITECTURE.md)**: System design and technical details (Coming Soon)
- **[Plugin Development](docs/PLUGIN_DEVELOPMENT.md)**: Create custom nodes and integrations (Coming Soon)

### Quick Links
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Example Workflows](#example-workflows)
- [Configuration](#configuration)
- [Troubleshooting](docs/AI_PROVIDERS.md#troubleshooting)

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
