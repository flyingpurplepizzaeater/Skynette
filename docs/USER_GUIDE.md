# Skynette User Guide

**Complete guide to using Skynette for workflow automation**

Welcome to Skynette! This guide will walk you through everything you need to know to start automating your workflows with AI-powered intelligence.

## Table of Contents

- [Getting Started](#getting-started)
- [First Launch](#first-launch)
- [Interface Overview](#interface-overview)
- [Creating Your First Workflow](#creating-your-first-workflow)
- [Working with AI](#working-with-ai)
- [Knowledge Bases (RAG)](#knowledge-bases-rag)
- [Workflow Nodes](#workflow-nodes)
- [Tips & Best Practices](#tips--best-practices)

---

## Getting Started

### Prerequisites

Before you begin, make sure you have:
- ✅ Installed Skynette (see [INSTALLATION.md](../INSTALLATION.md))
- ✅ Python 3.11+ with virtual environment activated
- 💡 Optional: API keys for AI providers (OpenAI, Anthropic, etc.)

### Launching Skynette

**From source:**
```bash
cd Skynette
source venv/bin/activate  # or venv\Scripts\activate on Windows
python src/main.py
```

**From executable:**
- Double-click `Skynette.exe` (Windows)
- Open `Skynette.app` (macOS)
- Run `./Skynette` (Linux)

---

## First Launch

When you first launch Skynette, you'll see the **AI Hub Setup Wizard**. This helps you configure your AI providers.

### Setup Wizard Steps

**Step 1: Welcome Screen**
- Choose which AI providers you want to use
- You can select multiple or skip and configure later

**Step 2: Provider Configuration**
- Enter API keys for selected cloud providers
- API keys are stored securely in your system keyring
- Local providers (llama.cpp, Ollama) don't require keys

**Step 3: Complete**
- Your setup is saved
- You're ready to start building workflows!

### Skipping Setup

You can skip the wizard and configure providers later:
1. Navigate to **AI Hub** → **My Providers**
2. Click **Configure** next to any provider
3. Enter your API key
4. Click **Save**

---

## Interface Overview

Skynette has a clean, intuitive interface with several main sections:

### Navigation Bar (Left Side)

- **🏠 Dashboard**: Overview of your workflows and recent activity
- **📋 Workflows**: List of all your workflows with search and filters
- **🎨 Workflow Editor**: Visual workflow builder
- **🤖 AI Hub**: Manage AI providers, models, and usage
- **⚙️ Settings**: Application preferences and configuration

### Dashboard

Your home screen showing:
- **Quick Actions**: Create new workflow, open recent workflows
- **Recent Workflows**: Last 5 workflows you worked on
- **Statistics**: Total workflows, executions, success rate
- **Tips**: Helpful hints for using Skynette

### Workflows List

View and manage all your workflows:
- **Search**: Find workflows by name or description
- **Filter**: By status (active/inactive), tags, or creation date
- **Sort**: By name, date modified, or execution count
- **Actions**: Run, edit, duplicate, or delete workflows

---

## Creating Your First Workflow

Let's build a simple workflow that sends you a daily weather report!

### Step 1: Choose Your Mode

Skynette offers two workflow creation modes:

**🎯 Simple Mode** (Recommended for beginners)
- Step-by-step wizard
- Guided configuration
- Perfect for common use cases

**🎨 Advanced Mode** (For power users)
- Visual node canvas
- Drag-and-drop interface
- Full control over workflow logic

Let's use **Simple Mode** for this example.

### Step 2: Create New Workflow

1. Click **+ New Workflow** on the dashboard
2. Select **Simple Mode**
3. Enter workflow details:
   - **Name**: "Daily Weather Report"
   - **Description**: "Get weather forecast every morning"
4. Click **Next**

### Step 3: Add Trigger

Choose when your workflow runs:

1. Select **Schedule Trigger**
2. Set schedule: `0 8 * * *` (Every day at 8 AM)
3. Or use the visual cron editor
4. Click **Next**

### Step 4: Add Actions

Add steps to your workflow:

**Action 1: Fetch Weather**
1. Search for "HTTP Request" node
2. Configure:
   - **Method**: GET
   - **URL**: `https://api.open-meteo.com/v1/forecast?latitude=40.7128&longitude=-74.0060&daily=temperature_2m_max,temperature_2m_min&timezone=America/New_York&forecast_days=1`
3. Click **Add**

**Action 2: Format Message**
1. Search for "AI Text Generation" node
2. Configure:
   - **Prompt**: "Create a friendly weather report from this data: {{$prev.data}}"
   - **Provider**: Choose your configured AI provider
3. Click **Add**

**Action 3: Send Notification**
1. Search for "Send Email" or "Slack" node
2. Configure with your email/Slack webhook
3. Click **Add**

### Step 5: Test & Save

1. Click **Test Workflow** to run immediately
2. Check the execution log for results
3. If successful, click **Save & Activate**
4. Your workflow will now run automatically!

---

## Working with AI

Skynette supports multiple AI providers with a unified interface.

### Configuring AI Providers

**Cloud Providers** (Require API keys):
- **OpenAI**: GPT-3.5, GPT-4, GPT-4 Turbo
- **Anthropic**: Claude, Claude-2, Claude Instant
- **Google AI**: Gemini Pro, Gemini Pro Vision
- **Groq**: LLaMA 2, Mistral (Fast inference)

**Local Providers** (No API keys needed):
- **llama.cpp**: Run GGUF models locally
- **Ollama**: Easy local model management

### Using AI Nodes

#### AI Chat Node

Perfect for conversational AI:

```yaml
Node: AI Chat
Inputs:
  - messages: Array of {role, content}
  - provider: openai
  - model: gpt-4
  - temperature: 0.7
Output:
  - response: AI's reply
  - tokens_used: Token count
```

**Example use cases:**
- Customer support automation
- Content generation
- Data analysis
- Code generation

#### AI Text Generation Node

For single-shot text generation:

```yaml
Node: AI Text Generation
Inputs:
  - prompt: "Summarize this article: {{$prev.content}}"
  - max_tokens: 500
  - temperature: 0.5
Output:
  - text: Generated text
  - model: Model used
  - cost: Estimated cost
```

#### AI Classification Node

Categorize text automatically:

```yaml
Node: AI Classify
Inputs:
  - text: Content to classify
  - categories: ["positive", "negative", "neutral"]
Output:
  - category: Selected category
  - confidence: 0.0 - 1.0
```

### AI Usage Dashboard

Track your AI usage and costs:

1. Go to **AI Hub** → **Usage**
2. View:
   - **Total calls**: Number of API requests
   - **Total tokens**: Input + output tokens
   - **Estimated cost**: Based on provider pricing
   - **Cost by provider**: Breakdown per provider
   - **Cost by workflow**: Breakdown per workflow

### Download Local Models

For private, offline AI:

1. Go to **AI Hub** → **Model Library**
2. Click **Download** tab
3. Choose a model:
   - **LLaMA 2 7B (Q4)**: Good balance, 4GB
   - **Mistral 7B (Q5)**: Better quality, 5GB
   - **Phi-2 (Q4)**: Smaller, faster, 2GB
4. Click **Download**
5. Track progress in the download manager
6. Once downloaded, select in AI nodes

---

## Knowledge Bases (RAG)

Retrieval Augmented Generation (RAG) lets you query your documents with AI.

### Creating a Knowledge Base

**Step 1: Create Collection**

1. Go to **AI Hub** → **Knowledge Bases**
2. Click **Create Collection**
3. Enter:
   - **Name**: "Company Docs"
   - **Description**: "Internal documentation"
   - **Embedding Model**: all-MiniLM-L6-v2 (default)
4. Click **Create**

**Step 2: Upload Documents**

1. Click on your collection
2. Click **Upload Documents**
3. Choose upload method:
   - **File Picker**: Select individual files
   - **Folder**: Upload entire folder
4. Supported formats:
   - Markdown (.md)
   - Text (.txt)
   - More formats coming soon!
5. Click **Start Upload**
6. Monitor progress (parallel processing of 5 files)

**Step 3: Wait for Processing**

Documents are:
1. ✂️ Chunked into smaller pieces
2. 🧮 Converted to embeddings (vectors)
3. 💾 Stored in ChromaDB for fast search

Processing time depends on:
- Number of documents
- Document size
- Your computer speed

### Querying Knowledge Bases

**Using the UI:**

1. Click on your collection
2. Click **Query**
3. Enter your question: "What is our refund policy?"
4. View results with:
   - Relevant text chunks
   - Source files
   - Similarity scores
5. Click **Copy** to use in workflows

**Using Workflow Nodes:**

**Query Node:**
```yaml
Node: Query Knowledge Base
Inputs:
  - query: "What is our refund policy?"
  - collection_id: "company-docs"
  - top_k: 3
  - min_similarity: 0.7
Output:
  - results: Array of chunks
  - sources: Source files
```

**Combined with AI:**
```yaml
Workflow:
1. Query Knowledge Base
   - query: {{$trigger.question}}
   
2. AI Text Generation
   - prompt: "Answer this question using only this context: {{$prev.results}}\n\nQuestion: {{$trigger.question}}"
```

This creates an AI that only answers from your documents!

### Managing Collections

**View Statistics:**
- Document count
- Total chunks
- Storage size
- Last updated

**Delete Documents:**
1. Open collection
2. Click **Manage Documents**
3. Select documents to delete
4. Click **Delete**

**Delete Collection:**
1. Click ⚙️ on collection card
2. Click **Delete Collection**
3. Confirm (this cannot be undone!)

---

## Workflow Nodes

Skynette includes 50+ built-in nodes organized by category.

### Trigger Nodes

Start your workflows automatically:

- **Manual Trigger**: Run on demand
- **Schedule**: Cron-based scheduling
- **Webhook**: HTTP endpoint
- **File Watch**: Monitor file changes
- **Email**: Trigger on new emails (coming soon)

### AI Nodes

Leverage artificial intelligence:

- **AI Chat**: Conversational AI
- **AI Text Generation**: Text completion
- **AI Classify**: Categorize text
- **AI Extract**: Extract structured data
- **AI Summarize**: Summarize content
- **Embeddings**: Generate vector embeddings

### RAG Nodes

Work with knowledge bases:

- **Ingest Document**: Add files to collection
- **Query Knowledge**: Search collections
- **Update Document**: Modify existing docs
- **Delete Document**: Remove from collection

### Data Nodes

Handle data transformation:

- **Read File**: Load file content
- **Write File**: Save to disk
- **JSON Transform**: Modify JSON data
- **CSV Parse**: Parse CSV files
- **Database Query**: SQL queries

### HTTP Nodes

Make web requests:

- **HTTP Request**: REST API calls
- **Webhook Response**: Reply to webhooks
- **GraphQL**: GraphQL queries
- **WebSocket**: Real-time connections

### Flow Control

Control workflow logic:

- **If/Else**: Conditional branching
- **Switch**: Multiple conditions
- **Loop**: Iterate over items
- **Merge**: Combine multiple paths
- **Delay**: Wait for duration
- **Error Handler**: Handle failures

### App Integrations

Connect to popular services:

- **Slack**: Send messages, files
- **GitHub**: Create issues, PRs
- **Google Drive**: Upload, download
- **Notion**: Create pages
- **Stripe**: Process payments
- And 25+ more!

### Using Expressions

Nodes support expressions to access data from previous nodes:

**Syntax:**
- `{{$trigger.data}}` - Data from trigger
- `{{$prev.result}}` - Result from previous node
- `{{$node.id.output}}` - Output from specific node
- `{{$env.API_KEY}}` - Environment variables

**Examples:**
```javascript
// Access previous node's output
{{$prev.temperature}}

// Conditional expression
{{$prev.age > 18 ? "adult" : "minor"}}

// String template
"Hello {{$prev.name}}, you are {{$prev.age}} years old"

// JSON path
{{$prev.user.address.city}}

// Array access
{{$prev.items[0].price}}
```

---

## Tips & Best Practices

### Workflow Design

**✅ Do:**
- Give workflows descriptive names
- Add descriptions explaining what they do
- Use comments on complex nodes
- Test workflows before activating
- Handle errors with error handlers
- Use variables for repeated values

**❌ Don't:**
- Create overly complex workflows (break them up!)
- Hardcode sensitive data (use environment variables)
- Skip error handling
- Forget to test edge cases

### Performance

**Optimize workflows:**
- Use local AI for repetitive tasks
- Cache results when possible
- Batch operations instead of loops
- Set appropriate timeouts
- Limit concurrent executions

**Monitor resource usage:**
- Check AI Hub → Usage dashboard
- Review execution logs regularly
- Set budget alerts for AI costs
- Clean up old execution history

### Security

**Protect sensitive data:**
- Never commit API keys to workflows
- Use environment variables or keyring
- Review data flow in workflows
- Limit webhook access
- Enable authentication for webhooks

**Best practices:**
- Keep Skynette updated
- Review plugin permissions
- Use HTTPS for webhooks
- Backup workflows regularly
- Test in development first

### Debugging

**When workflows fail:**

1. **Check Execution Log**
   - View in Workflows → [Your Workflow] → Executions
   - Look for error messages
   - Check input/output of each node

2. **Test Individual Nodes**
   - Right-click node → Test
   - Verify inputs are correct
   - Check output format

3. **Enable Debug Mode**
   - Add Log/Debug nodes
   - Print intermediate values
   - Check console output

4. **Common Issues**
   - API rate limits exceeded
   - Invalid JSON format
   - Missing required fields
   - Timeout errors
   - Authentication failures

### Backups

**Export workflows:**
1. Go to Workflows
2. Select workflow
3. Click ⚙️ → Export
4. Save JSON file

**Import workflows:**
1. Go to Workflows
2. Click **Import**
3. Select JSON file
4. Review and save

**Backup schedule:**
- Export important workflows weekly
- Store backups securely
- Test imports occasionally
- Keep old versions

---

## Getting Help

### Documentation

- 📖 [README](../README.md) - Overview and features
- 🚀 [QUICKSTART](../QUICKSTART.md) - Fast setup
- 💻 [INSTALLATION](../INSTALLATION.md) - Detailed install guide
- 📚 [EXAMPLES](./EXAMPLES.md) - Workflow examples
- ❓ [FAQ](./FAQ.md) - Common questions
- 🗺️ [ROADMAP](../ROADMAP.md) - Future plans

### Community

- 🐛 [Report Issues](https://github.com/flyingpurplepizzaeater/Skynette/issues)
- 💬 [Discussions](https://github.com/flyingpurplepizzaeater/Skynette/discussions)
- 🤝 [Contributing](../CONTRIBUTING.md)

### Support

- Check the FAQ first
- Search existing issues
- Provide details when reporting bugs
- Include logs and screenshots

---

## Next Steps

Now that you know the basics, try:

1. **Build more workflows**
   - Start with simple automation
   - Gradually add complexity
   - Share with the community!

2. **Explore AI features**
   - Try different providers
   - Experiment with prompts
   - Build knowledge bases

3. **Join the community**
   - Share your workflows
   - Help others
   - Request features

4. **Contribute**
   - Report bugs
   - Suggest improvements
   - Submit pull requests

---

**Happy automating! 🚀**

For more examples and tutorials, see [EXAMPLES.md](./EXAMPLES.md)
