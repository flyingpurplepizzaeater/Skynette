# Skynette - Open Source Workflow Automation Platform

[![CI](https://github.com/flyingpurplepizzaeater/Skynette/actions/workflows/ci.yml/badge.svg)](https://github.com/flyingpurplepizzaeater/Skynette/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/flyingpurplepizzaeater/Skynette/branch/main/graph/badge.svg)](https://codecov.io/gh/flyingpurplepizzaeater/Skynette)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Release](https://img.shields.io/github/v/release/flyingpurplepizzaeater/Skynette)](https://github.com/flyingpurplepizzaeater/Skynette/releases)

An intelligent, AI-powered workflow automation platform that combines visual workflow building with multi-model AI capabilities. Built with Python and Flet for cross-platform desktop and mobile deployment.

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

> **📚 For detailed installation instructions, troubleshooting, and platform-specific guides, see [INSTALLATION.md](INSTALLATION.md)**

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

# Install the package with dependencies (includes AI and dev tools)
pip install -e ".[ai,dev]"

# Run the application
python src/main.py
# or
flet run src/main.py
```

### Method 2: Install from PyPI

```bash
# Install the base package
pip install skynette

# Or install with all AI features
pip install skynette[ai]

# Or install with all optional features
pip install skynette[all]

# Run the application
skynette
# or
python -m src.main
```

> **Note**: After installing from PyPI, you can run Skynette with the `skynette` command or `python -m src.main`.

### Method 3: Pre-built Executables

Download pre-built executables from [GitHub Releases](https://github.com/flyingpurplepizzaeater/Skynette/releases):

| Platform | Download | Notes |
|----------|----------|-------|
| **Windows** | `Skynette-Windows.zip` | Extract and run `Skynette.exe` |
| **macOS** | `Skynette-macOS.zip` or `Skynette.dmg` | Drag to Applications folder |
| **Linux** | `Skynette.AppImage` or `Skynette-Linux.tar.gz` | Make executable with `chmod +x` |
| **Linux (Debian/Ubuntu)** | `skynette_*.deb` | Install with `sudo dpkg -i` |

**Installation instructions:**
- **Windows**: Download the ZIP, extract, and run `Skynette.exe`
- **macOS**: Download the DMG or ZIP, open, and drag to Applications folder
- **Linux (AppImage)**: Download, make executable (`chmod +x Skynette-*.AppImage`), and run
- **Linux (.deb)**: Download and install (`sudo dpkg -i skynette_*.deb`)

All release artifacts include SHA256 checksums for verification.

## Documentation

**📚 Complete guides to get you started:**

- 🚀 **[QUICKSTART.md](QUICKSTART.md)** - Get up and running in 5 minutes
- 📖 **[USER_GUIDE.md](docs/USER_GUIDE.md)** - Complete step-by-step usage guide
- 💻 **[INSTALLATION.md](INSTALLATION.md)** - Detailed installation instructions
- 📝 **[EXAMPLES.md](docs/EXAMPLES.md)** - 10 practical workflow examples
- ❓ **[FAQ.md](docs/FAQ.md)** - Frequently asked questions
- 🤝 **[CONTRIBUTING.md](CONTRIBUTING.md)** - How to contribute
- 🗺️ **[ROADMAP.md](ROADMAP.md)** - Planned features

## Quick Start

**New to Skynette? Follow these steps:**

### 1. Install & Launch

```bash
# Clone and navigate to directory
git clone https://github.com/flyingpurplepizzaeater/Skynette.git
cd Skynette

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install with AI features
pip install -e ".[ai,dev]"

# Launch application
python src/main.py
```

💡 **See [QUICKSTART.md](QUICKSTART.md) for faster methods and [INSTALLATION.md](INSTALLATION.md) for troubleshooting.**

### 2. Configure AI Providers (Optional)

On first launch, the **AI Hub Setup Wizard** helps you configure AI providers:
- ✅ Select providers (OpenAI, Anthropic, Google AI, etc.)
- ✅ Enter API keys (stored securely in system keyring)
- ✅ Or skip and configure later

**Don't have API keys?** Use **local models** (free, private, no keys needed)!

### 3. Create Your First Workflow

**Option A: Simple Mode (Recommended for beginners)**
1. Click **+ New Workflow** → **Simple Mode**
2. Follow the step-by-step wizard
3. Add trigger (when to run)
4. Add actions (what to do)
5. Test and save!

**Option B: Advanced Mode (For power users)**
1. Click **+ New Workflow** → **Advanced Mode**
2. Drag nodes from palette to canvas
3. Connect nodes to build workflow logic
4. Configure each node
5. Run and debug visually

💡 **See [USER_GUIDE.md](docs/USER_GUIDE.md) for detailed walkthrough with screenshots.**

### 4. Explore Examples

Check out [EXAMPLES.md](docs/EXAMPLES.md) for 10 ready-to-use workflows:
- 📧 Daily weather email reports
- 🤖 AI-powered email responder
- 📄 Document summarizer
- 📱 Social media content generator
- 💾 Automated backups
- 📚 Knowledge base Q&A bot
- And more!

## Key Features Explained

### 🤖 AI Hub
Centralized management for all AI providers and models:
- Configure multiple providers (OpenAI, Anthropic, Google, local models)
- Download and manage local AI models
- Track usage, costs, and token consumption
- Secure API key storage

**Learn more:** [USER_GUIDE.md - Working with AI](docs/USER_GUIDE.md#working-with-ai)

### 📚 Knowledge Bases (RAG)
Build AI assistants that answer questions from your documents:
- Upload markdown, text, and PDF files
- Semantic search powered by embeddings
- Query with natural language
- 100% local and private by default

**Learn more:** [USER_GUIDE.md - Knowledge Bases](docs/USER_GUIDE.md#knowledge-bases-rag)

### 🎨 Dual-Mode Editor
Choose the workflow builder that fits your style:
- **Simple Mode**: Wizard for beginners
- **Advanced Mode**: Visual canvas for power users
- Switch between modes anytime

**Learn more:** [USER_GUIDE.md - Creating Workflows](docs/USER_GUIDE.md#creating-your-first-workflow)

### 🔧 50+ Built-in Nodes
Pre-built integrations for common tasks:
- **AI**: Text generation, classification, embeddings
- **Data**: File operations, databases, transformations
- **HTTP**: REST APIs, webhooks, GraphQL
- **Apps**: Slack, GitHub, Google Drive, and more

**Browse all:** [USER_GUIDE.md - Workflow Nodes](docs/USER_GUIDE.md#workflow-nodes)

## Use Cases

**What can you build with Skynette?**

- 📧 **Email Automation**: Auto-respond to customers using AI
- 📊 **Report Generation**: Create automated business reports
- 📝 **Content Creation**: Generate social media posts from blogs
- 🔍 **Data Analysis**: Analyze sentiment in customer feedback
- 💾 **Backup Automation**: Auto-backup files to cloud storage
- 🤖 **Custom AI Assistants**: Build Q&A bots from your docs
- 🔄 **Data Pipelines**: Transform and move data between systems
- ⚡ **API Integrations**: Connect and automate your tools

**See real examples:** [EXAMPLES.md](docs/EXAMPLES.md)

## Community & Support

- 💬 **[GitHub Discussions](https://github.com/flyingpurplepizzaeater/Skynette/discussions)** - Ask questions, share workflows
- 🐛 **[Issue Tracker](https://github.com/flyingpurplepizzaeater/Skynette/issues)** - Report bugs, request features
- 📖 **[Documentation](docs/)** - Comprehensive guides and API docs
- 🤝 **[Contributing](CONTRIBUTING.md)** - Help improve Skynette

## Troubleshooting

**Having issues? Check these resources:**

1. **[FAQ.md](docs/FAQ.md)** - Common problems and solutions
2. **[INSTALLATION.md](INSTALLATION.md)** - Detailed setup troubleshooting
3. **[GitHub Issues](https://github.com/flyingpurplepizzaeater/Skynette/issues)** - Search existing issues
4. **[Discussions](https://github.com/flyingpurplepizzaeater/Skynette/discussions)** - Ask the community

**Quick fixes:**
```bash
# Reinstall dependencies
pip install -e ".[ai,dev]" --force-reinstall

# Clear cache
rm -rf ~/.skynette/cache

# Run with debug logging
python src/main.py --debug
```

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Code of Conduct
- Development setup
- Pull request process
- Coding standards

**Quick contribution:**
```bash
# Fork and clone
git clone https://github.com/YOUR_USERNAME/Skynette.git

# Create branch
git checkout -b feature/awesome-feature

# Make changes and test
pytest

# Submit PR
```
## License

MIT License - See [LICENSE](LICENSE) for details.

## Acknowledgments

- Inspired by [n8n](https://n8n.io), [Activepieces](https://activepieces.com), [Langflow](https://langflow.org)
- Built with [Flet](https://flet.dev) for cross-platform UI
- AI powered by [llama.cpp](https://github.com/ggerganov/llama.cpp), [ChromaDB](https://www.trychroma.com/), and [sentence-transformers](https://www.sbert.net/)

---

**Built with ❤️ by the Skynette community**

[⭐ Star on GitHub](https://github.com/flyingpurplepizzaeater/Skynette) | [🐛 Report Issue](https://github.com/flyingpurplepizzaeater/Skynette/issues) | [💬 Discussions](https://github.com/flyingpurplepizzaeater/Skynette/discussions)
