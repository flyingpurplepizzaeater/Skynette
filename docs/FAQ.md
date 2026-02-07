# Frequently Asked Questions (FAQ)

Quick answers to common questions about Skynette.

## Table of Contents

- [Installation & Setup](#installation--setup)
- [Using Skynette](#using-skynette)
- [AI & Models](#ai--models)
- [Knowledge Bases](#knowledge-bases)
- [Troubleshooting](#troubleshooting)
- [Performance](#performance)
- [Security & Privacy](#security--privacy)
- [Contributing](#contributing)

---

## Installation & Setup

### What are the system requirements?

**Minimum:**
- OS: Windows 10+, macOS 11+, or Ubuntu 20.04+
- Python: 3.11 or 3.12
- RAM: 4GB
- Storage: 2GB

**Recommended:**
- RAM: 8GB (16GB for local AI models)
- Storage: 10GB+ (for models and workspace data)
- GPU: NVIDIA with CUDA (optional, for faster AI)

### Which Python version should I use?

Python **3.11** is recommended for maximum compatibility. Python 3.12 is also supported.

```bash
python --version
# Should show: Python 3.11.x or 3.12.x
```

### How do I install Python?

**Windows:**
1. Download from [python.org](https://www.python.org/downloads/)
2. Run installer
3. ✅ Check "Add Python to PATH"
4. Restart terminal

**macOS:**
```bash
brew install python@3.11
```

**Linux:**
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv
```

### Installation fails with "No module named 'flet'"

This means dependencies aren't installed. Make sure you:

1. Activated the virtual environment
2. Installed with the correct command

```bash
# Activate venv first!
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Then install
pip install -e ".[ai,dev]"
```

### Do I need a virtual environment?

**Strongly recommended!** Virtual environments:
- ✅ Isolate dependencies
- ✅ Prevent conflicts
- ✅ Make it easy to clean up
- ✅ Allow multiple Python projects

Without a venv, you might pollute your system Python.

### Can I use Anaconda/Conda?

Yes, but not recommended. We've tested with standard Python venv. If using Conda:

```bash
conda create -n skynette python=3.11
conda activate skynette
pip install -e ".[ai,dev]"
```

### Application won't start - what should I check?

**Checklist:**
1. ✅ Python 3.11+ installed: `python --version`
2. ✅ Virtual environment activated: `which python` (should show venv path)
3. ✅ Dependencies installed: `pip list | grep flet`
4. ✅ No conflicting processes: Close other instances
5. ✅ Permissions: Check write access to data directory

**Get logs:**
```bash
python src/main.py --debug 2>&1 | tee debug.log
```

---

## Using Skynette

### How do I create my first workflow?

See the [Creating Your First Workflow](USER_GUIDE.md#creating-your-first-workflow) section in the User Guide.

Quick version:
1. Click **+ New Workflow**
2. Choose **Simple Mode** (easier) or **Advanced Mode**
3. Add a trigger (when to run)
4. Add actions (what to do)
5. Test and save!

### What's the difference between Simple and Advanced Mode?

**Simple Mode:**
- ✅ Step-by-step wizard
- ✅ Guided configuration
- ✅ Perfect for beginners
- ❌ Limited to linear workflows

**Advanced Mode:**
- ✅ Visual canvas
- ✅ Drag-and-drop nodes
- ✅ Complex branching and loops
- ✅ Full control
- ❌ Steeper learning curve

You can switch between modes anytime!

### Can I schedule workflows to run automatically?

Yes! Use the **Schedule Trigger** node:

1. Add Schedule Trigger to workflow
2. Set cron expression: `0 9 * * *` (daily at 9 AM)
3. Or use the visual cron builder
4. Activate workflow
5. It will run automatically on schedule

### How do I access data from previous nodes?

Use expressions with double curly braces:

```javascript
{{$prev.result}}        // Previous node's output
{{$trigger.data}}       // Trigger data
{{$node.abc123.value}}  // Specific node by ID
```

Example:
```
Node 1 outputs: {name: "John", age: 30}
Node 2 can access: {{$prev.name}} → "John"
```

### Can workflows call other workflows?

Not directly yet, but you can:
- Export/import workflow fragments
- Use the same nodes in multiple workflows
- Call external APIs (including your own Skynette webhooks)

Workflow-to-workflow calls are on the roadmap!

### How do I share workflows with others?

**Export:**
1. Go to Workflows
2. Select your workflow
3. Click ⚙️ → Export
4. Save JSON file

**Import:**
1. Send JSON file to colleague
2. They click **Import** in Workflows
3. Select your JSON file
4. Workflow is added to their workspace

---

## AI & Models

### Do I need API keys?

**It depends:**
- **Cloud AI** (OpenAI, Anthropic, etc.): Yes, you need API keys
- **Local AI** (llama.cpp, Ollama): No keys needed!

You can mix and match. Start with local models (free!) and add cloud providers later.

### Where do I get API keys?

**OpenAI:**
- Visit [platform.openai.com](https://platform.openai.com/)
- Create account → API Keys → Create new key
- Copy and paste into Skynette

**Anthropic:**
- Visit [console.anthropic.com](https://console.anthropic.com/)
- Create account → API Keys → Create key

**Google AI:**
- Visit [makersuite.google.com](https://makersuite.google.com/)
- Get API key

### Are API keys stored securely?

Yes! Skynette uses your system's **keyring** (Keychain on Mac, Credential Manager on Windows, Secret Service on Linux).

API keys are:
- ✅ Encrypted at rest
- ✅ Not stored in plain text
- ✅ Not visible in workflow exports
- ✅ Protected by OS security

### How much do AI providers cost?

Varies by provider (February 2024 pricing):

**OpenAI:**
- GPT-3.5 Turbo: ~$0.001/1K tokens
- GPT-4: ~$0.03/1K tokens
- GPT-4 Turbo: ~$0.01/1K tokens

**Anthropic:**
- Claude Instant: ~$0.0016/1K tokens
- Claude 2: ~$0.024/1K tokens

**Local models:**
- Free! Just costs compute time

Check the AI Hub → Usage dashboard to track your spending.

### Can I use AI without internet?

Yes! Use **local models**:

1. Go to AI Hub → Model Library
2. Download a model (e.g., Mistral 7B)
3. Select it in AI nodes
4. Runs 100% locally, no internet needed

Local models are:
- ✅ Free
- ✅ Private
- ✅ Work offline
- ❌ Slower than cloud (without GPU)
- ❌ Require disk space (4-8GB per model)

### Which AI model should I use?

**For general use:**
- GPT-4 Turbo: Best quality, moderate cost
- Claude 2: Great for long documents
- GPT-3.5 Turbo: Fast and cheap

**For local/private:**
- Mistral 7B: Best quality
- LLaMA 2 7B: Good balance
- Phi-2: Fastest, smallest

**For coding:**
- GPT-4
- Claude 2

**For cost-sensitive:**
- GPT-3.5 Turbo
- Groq (fast and cheap)
- Local models (free!)

### How do I download local models?

1. Go to **AI Hub** → **Model Library**
2. Click **Download** tab
3. Browse available models
4. Click **Download** on your choice
5. Wait for download (shows progress)
6. Model appears in **My Models**
7. Use in AI nodes!

### Can I use my own models?

Yes! For GGUF models:

1. Download .gguf file
2. Go to AI Hub → Model Library
3. Click **Import Local File**
4. Select your .gguf file
5. Model is added and ready to use

---

## Knowledge Bases

### What are Knowledge Bases?

Knowledge Bases (also called RAG - Retrieval Augmented Generation) let you:
- Upload your documents
- Search them semantically (by meaning, not just keywords)
- Let AI answer questions using your documents
- Create custom AI assistants with domain knowledge

### What file types are supported?

Currently:
- ✅ Markdown (.md)
- ✅ Plain text (.txt)
- 🔄 Coming soon: PDF, DOCX, HTML

### How many documents can I upload?

No hard limit! But consider:
- **Storage**: Each document takes disk space
- **Processing time**: Large collections take longer to search
- **RAM usage**: Very large collections may need more memory

Tested with:
- ✅ 1,000 documents: Works great
- ✅ 10,000 documents: Works, may be slower
- ⚠️ 100,000+ documents: Not tested yet

### How does document search work?

**Behind the scenes:**
1. Documents are chunked (500-1000 characters)
2. Each chunk converted to embedding (384-dimensional vector)
3. Stored in ChromaDB (fast vector database)
4. Your query is also converted to embedding
5. ChromaDB finds most similar chunks (cosine similarity)
6. Results ranked by relevance

**No machine learning required** - it's all automatic!

### Are embeddings generated locally?

Yes! Skynette uses `all-MiniLM-L6-v2`:
- ✅ Runs 100% locally
- ✅ Free
- ✅ No API needed
- ✅ Private (your documents never leave your computer)
- ✅ Fast (processes hundreds of documents/minute)

### Can I use different embedding models?

Not yet in the UI, but it's technically possible. Coming in a future update!

### How do I delete a knowledge base?

**Warning: This cannot be undone!**

1. Go to AI Hub → Knowledge Bases
2. Find your collection
3. Click ⚙️ (settings icon)
4. Click **Delete Collection**
5. Confirm deletion

All documents and embeddings are permanently deleted.

---

## Troubleshooting

### Application crashes on startup

**Try these steps:**

1. **Check Python version:**
   ```bash
   python --version
   # Must be 3.11 or 3.12
   ```

2. **Reinstall dependencies:**
   ```bash
   pip uninstall skynette
   pip install -e ".[ai,dev]"
   ```

3. **Clear cache:**
   ```bash
   rm -rf ~/.skynette/cache
   rm -rf ~/.cache/skynette
   ```

4. **Check logs:**
   ```bash
   python src/main.py --debug
   ```

5. **Start fresh:**
   ```bash
   deactivate
   rm -rf venv
   python -m venv venv
   source venv/bin/activate
   pip install -e ".[ai,dev]"
   ```

### Import errors like "No module named 'sentence_transformers'"

AI features not installed. Install with:

```bash
pip install -e ".[ai]"
```

Or for full dev setup:
```bash
pip install -e ".[ai,dev]"
```

### ChromaDB errors or SQLite issues

**On macOS:**
```bash
brew install sqlite3
```

**On Linux:**
```bash
sudo apt install libsqlite3-dev
```

Then reinstall ChromaDB:
```bash
pip uninstall chromadb
pip install chromadb
```

### Flet errors or UI doesn't load

1. **Update Flet:**
   ```bash
   pip install --upgrade flet
   ```

2. **Clear Flet cache:**
   ```bash
   rm -rf ~/.flet
   ```

3. **Check for conflicting processes:**
   ```bash
   # Kill any existing Flet processes
   pkill -f flet
   ```

### AI provider returns errors

**Check these:**
- ✅ API key is valid
- ✅ API key has credits/not expired
- ✅ Rate limits not exceeded
- ✅ Internet connection working
- ✅ Provider's API is up (check status pages)

**Test with:**
```bash
curl -H "Authorization: Bearer YOUR_KEY" https://api.openai.com/v1/models
```

### Workflow execution fails

**Debug steps:**
1. Check execution log for error message
2. Test each node individually
3. Verify inputs are correct format
4. Check for missing required fields
5. Add Log nodes to see intermediate values
6. Review workflow with fresh eyes tomorrow!

---

## Performance

### Application feels slow

**Quick fixes:**
1. **Close unused workflows** in editor
2. **Limit concurrent workflow runs** (Settings)
3. **Clear old execution logs** (Settings → Data)
4. **Use local AI** for repetitive tasks (faster with GPU)
5. **Reduce model size** (Q4 instead of Q8 quantization)

### Knowledge Base search is slow

**Optimize:**
- Use smaller documents (split large files)
- Reduce `top_k` parameter (return fewer results)
- Increase `min_similarity` threshold
- Use SSD instead of HDD
- Close other applications

### Local AI models are slow

**Speed up inference:**
- Use GPU instead of CPU (much faster!)
- Use smaller models (Phi-2 vs LLaMA 2)
- Use quantized models (Q4 vs F16)
- Reduce `max_tokens` parameter
- Use `temperature=0` for faster generation

**GPU setup:**
1. Install CUDA toolkit
2. Install llama-cpp-python with GPU support:
   ```bash
   pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121
   ```

### How many workflows can run concurrently?

Default: 5 concurrent workflow executions

Change in Settings → Workflow → Max Concurrent Executions

More concurrent = more RAM usage, but faster if you have resources.

---

## Security & Privacy

### Is my data private?

**Yes!** Skynette runs locally on your computer:
- Workflows stored locally
- No telemetry or tracking
- You control what data leaves your machine

**When using cloud AI:**
- Your prompts are sent to the provider
- Subject to their privacy policy
- Consider using local models for sensitive data

### Where is data stored?

**Default locations:**
- **Linux**: `~/.skynette/`
- **macOS**: `~/Library/Application Support/Skynette/`
- **Windows**: `%APPDATA%\Skynette\`

Contains:
- Workflows (JSON)
- Execution logs (SQLite)
- Knowledge bases (ChromaDB)
- Configuration (YAML)
- API keys (system keyring, not in folder!)

### Can I use Skynette for sensitive data?

**Yes, with precautions:**
- ✅ Use **local AI models** (no data leaves your computer)
- ✅ Use **local embeddings** for knowledge bases
- ✅ Avoid cloud providers for sensitive prompts
- ✅ Review workflow data flow carefully
- ✅ Encrypt your disk/folder
- ❌ Don't commit API keys to workflows
- ❌ Don't share workflows with sensitive data

### How are API keys protected?

API keys stored in system keyring:
- **macOS**: Keychain (same as passwords)
- **Windows**: Credential Manager
- **Linux**: Secret Service (GNOME Keyring, KWallet)

Keys are:
- Encrypted by OS
- Not in plain text files
- Not in workflow exports
- Not in git repositories

### Can I run Skynette behind a firewall?

**Yes!** Local features work offline:
- Workflow editor
- Local AI models
- Local embeddings
- File operations

**Requires internet:**
- Cloud AI providers
- Downloading models
- Plugin marketplace (coming soon)
- Cloud sync (coming soon)

---

## Contributing

### How can I contribute?

Many ways!
- 🐛 Report bugs
- 💡 Suggest features
- 📝 Improve documentation
- 🧪 Write tests
- 🔧 Fix bugs
- ✨ Add features
- 🎨 Design UI improvements
- 🔌 Create plugins

See [CONTRIBUTING.md](../CONTRIBUTING.md) for details.

### I found a bug - what should I include in my report?

**Great bug reports include:**
1. Clear title: "Workflow fails when using AI Chat node with empty prompt"
2. Steps to reproduce
3. Expected behavior
4. Actual behavior
5. Screenshots/videos
6. System info (OS, Python version)
7. Logs (use `--debug` flag)
8. Minimal example workflow (if applicable)

See [issue template](.github/ISSUE_TEMPLATE/bug_report.md).

### Can I create custom nodes?

**Coming soon!** Plugin system is in development:
- Custom nodes in Python
- Sandboxed execution
- Publish to marketplace
- Revenue sharing for premium plugins

For now, you can:
- Use Code Execution node (runs Python)
- Request features for built-in nodes
- Contribute to core (add nodes directly)

### How do I run tests?

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/

# Integration tests
pytest tests/integration/

# E2E tests (requires Playwright)
playwright install chromium
pytest tests/e2e/

# With coverage
pytest --cov=src --cov-report=html
```

### Coding standards?

We use:
- **Ruff** for linting and formatting
- **Type hints** where practical
- **Docstrings** for public APIs
- **Tests** for new features

Before submitting PR:
```bash
# Format code
ruff format src/

# Check for issues
ruff check src/

# Run tests
pytest
```

---

## Still Have Questions?

- 📖 Check [USER_GUIDE.md](USER_GUIDE.md) for detailed usage
- 🚀 See [QUICKSTART.md](../QUICKSTART.md) for fast setup
- 💬 Ask in [Discussions](https://github.com/flyingpurplepizzaeater/Skynette/discussions)
- 🐛 [Report issues](https://github.com/flyingpurplepizzaeater/Skynette/issues)

---

**Last Updated**: February 2026
