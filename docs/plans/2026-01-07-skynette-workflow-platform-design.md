# Skynette - AI-Native Workflow Automation Platform

**Design Document**
**Date:** 2026-01-07
**Status:** Approved
**Version:** 1.0

---

## Executive Summary

Skynette is an open-source, AI-native workflow automation platform that runs locally on desktop and mobile devices. It combines the visual workflow building of n8n/Zapier with the AI capabilities of Langflow/Dify, creating a unique hybrid that serves users from absolute beginners to coding professionals.

### Key Differentiators

- **Local-first**: All processing on-device, complete privacy, works offline
- **AI-native**: AI woven throughout, not bolted on - Smart AI node, Model Hub, Skynet Assistant
- **Progressive complexity**: Simple step builder for beginners, node canvas for pros
- **Model freedom**: Download and run any AI model from Hugging Face, GitHub, or direct URL
- **Truly open**: MIT license, no restrictions

---

## Design Decisions Summary

| Aspect | Decision |
|--------|----------|
| **Focus** | Hybrid AI-first + general automation |
| **Platform** | Local desktop/mobile app (.exe, iOS, Android) |
| **Tech Stack** | Flet (Python + Flutter) |
| **Editor** | Dual-mode: Simple step builder + Advanced node canvas |
| **AI Integration** | Unified Smart AI node + provider-specific nodes + auto-fallback |
| **Storage** | SQLite (data) + YAML (workflows) + folders (assets) |
| **Integrations** | ~35-40 core nodes + plugin SDK + marketplace |
| **Name** | Skynette |
| **License** | MIT open-source + marketplace revenue + optional cloud |

---

## 1. Product Vision & Architecture

### Core Principles

1. **Local-first**: All processing happens on your device. Your workflows, credentials, and data never leave your machine unless you choose cloud sync.

2. **AI-native**: AI isn't an afterthought—it's woven throughout. The Smart AI node makes any AI model accessible in one click, while advanced nodes unlock provider-specific power.

3. **AI-assisted building**: A built-in AI chat assistant (Skynet) helps you create workflows using natural language. Describe what you want, and Skynette builds it.

4. **Model freedom**: Download and run any AI model - from Hugging Face, GitHub, or direct URL.

5. **Progressive complexity**: Beginners start with a simple step-by-step builder. As skills grow, switch to the full node canvas. Same workflow, two views.

6. **Truly open**: MIT license means no gotchas. Build commercial products, modify the code, contribute back—your choice.

### Unique Features

| Feature | Description |
|---------|-------------|
| **Skynet Assistant** | AI chat agent that builds workflows from natural language |
| **AI Model Hub** | Browse, download, manage AI models from multiple sources |
| **AI Auto-Debug** | Plain-English error explanations with fix suggestions |
| **Smart Suggestions** | Context-aware next-node recommendations |
| **Expression Copilot** | AI-assisted data transformations and code |
| **Workflow Templates** | Ready-to-use workflow library |
| **Community Marketplace** | Share workflows and plugins |
| **Version History** | Git-like workflow versioning with diff view |
| **Execution Dashboard** | Real-time monitoring and AI cost tracking |

### AI Model Hub Features

```
+-------------------------------------------------------------+
|                      AI MODEL HUB                           |
+-------------------------------------------------------------+
|  Download Sources                                           |
|  - Hugging Face (browse/search models)                      |
|  - GitHub Releases (paste repo URL)                         |
|  - Direct URL (any GGUF, ONNX, SafeTensors link)            |
|  - Ollama Library (pull from ollama.com)                    |
+-------------------------------------------------------------+
|  Model Discovery                                            |
|  - Recommended Models (curated by Skynette team)            |
|  - Trending (most downloaded this week)                     |
|  - Recently Updated (new releases)                          |
|  - By Category (chat, code, vision, embedding, etc.)        |
|  - Search (by name, size, quantization, capability)         |
+-------------------------------------------------------------+
|  My Models (Local Library)                                  |
|  - Downloaded models with metadata                          |
|  - Storage usage per model                                  |
|  - One-click delete / update                                |
|  - Compatibility checker (RAM/VRAM requirements)            |
|  - Quick-launch to test in chat                             |
+-------------------------------------------------------------+
|  Model Settings                                             |
|  - Default model for Skynet Assistant                       |
|  - Default model for workflow AI nodes                      |
|  - GPU/CPU allocation preferences                           |
|  - Context length & generation settings                     |
+-------------------------------------------------------------+
```

### High-Level Architecture

```
+-------------------------------------------------------------+
|                     Skynette App (Flet)                     |
+-------------------------------------------------------------+
|  UI Layer (Flutter)                                         |
|  - Skynet Assistant (AI Chat Panel)                         |
|  - AI Model Hub (Browse, Download, Manage)                  |
|  - Simple Mode (Step Builder)                               |
|  - Advanced Mode (Node Canvas)                              |
|  - Execution Dashboard                                      |
|  - Settings / Plugin Manager / Marketplace                  |
+-------------------------------------------------------------+
|  Core Engine (Python)                                       |
|  - Workflow Executor                                        |
|  - AI Gateway (cloud providers + local inference)           |
|  - Model Manager (download, load, run local models)         |
|  - Skynet Brain (assistant logic, NL->workflow)             |
|  - Plugin Runtime                                           |
|  - Trigger System (cron, webhook, file, app events)         |
+-------------------------------------------------------------+
|  Data Layer                                                 |
|  - SQLite (settings, credentials, history, metrics)         |
|  - YAML Files (workflow definitions, version history)       |
|  - Asset Folder (uploads, cache, AI models)                 |
+-------------------------------------------------------------+
```

---

## 2. Node Types & AI Integration

### Core Node Categories (~35-40 nodes)

#### AI & Intelligence (8 nodes)
- Smart AI (unified interface)
- AI Chat (conversation with memory)
- AI Vision (image analysis)
- AI Embedding (vector generation)
- AI Speech-to-Text
- AI Text-to-Speech
- AI Agent (autonomous multi-step)
- AI Classifier (categorize inputs)

#### Triggers (7 nodes)
- Manual Trigger (button click)
- Schedule (cron expressions)
- Webhook (receive HTTP calls)
- File Watcher (folder changes)
- Email Trigger (IMAP polling)
- App Event (OS-level events)
- Workflow Trigger (called by other workflows)

#### HTTP & APIs (4 nodes)
- HTTP Request (any REST API)
- GraphQL
- WebSocket (real-time connections)
- API Response (for webhook responses)

#### Files & Data (5 nodes)
- Read File (local filesystem)
- Write File
- CSV/Excel (parse and generate)
- JSON/XML (parse and transform)
- PDF (extract text, generate)

#### Databases (5 nodes)
- SQLite (local database)
- PostgreSQL
- MySQL
- MongoDB
- Vector DB (ChromaDB, built-in for RAG)

#### Flow Control (6 nodes)
- If/Else (conditional branching)
- Switch (multiple conditions)
- Loop (iterate over items)
- Wait (delay execution)
- Parallel (split into concurrent branches)
- Merge (combine parallel results)

#### Utilities (5 nodes)
- Code Block (Python or JavaScript)
- Transform (data mapping/expressions)
- Set Variable (workflow state)
- Error Handler (try/catch)
- Log/Debug (output inspection)

#### Popular Apps (6 nodes)
- Google (Sheets, Drive, Gmail, Calendar)
- Slack
- Discord
- Notion
- Telegram
- SMTP Email (send emails)

### Smart AI Node (Unified Interface)

```
+-------------------------------------------------------------+
|                     SMART AI NODE                           |
+-------------------------------------------------------------+
|  Task Type: [Dropdown]                                      |
|  - Chat/Complete (text generation)                          |
|  - Analyze (extract structured data)                        |
|  - Rewrite (transform text style/format)                    |
|  - Translate (language conversion)                          |
|  - Summarize (condense content)                             |
|  - Q&A (answer based on context)                            |
|  - Classify (categorize input)                              |
+-------------------------------------------------------------+
|  Model: [Dropdown with smart defaults]                      |
|  - Auto (best available based on task)                      |
|  - Local: Llama 3.2, Mistral, Qwen... (from Hub)            |
|  - Cloud: GPT-4o, Claude, Gemini, Groq...                   |
|  - Fallback chain: [Model 1] -> [Model 2] -> [Model 3]      |
+-------------------------------------------------------------+
|  Input:                                                     |
|  - Prompt template (with {{variable}} support)              |
|  - System message (optional)                                |
|  - Attachments: images, files (for vision/analysis)         |
+-------------------------------------------------------------+
|  Output Options:                                            |
|  - Plain text                                               |
|  - JSON (structured, with schema)                           |
|  - Streaming (real-time output)                             |
+-------------------------------------------------------------+
|  Advanced:                                                  |
|  - Temperature, Max tokens                                  |
|  - Cost limit per execution                                 |
|  - Timeout settings                                         |
+-------------------------------------------------------------+
```

### AI Gateway Architecture (Auto-Fallback)

The AI Gateway handles routing requests to the right provider with automatic fallback:

1. Request comes in from Smart AI Node
2. Provider Router checks user's priority list and model availability
3. Try Primary Model (e.g., Local Llama)
4. On failure: Try Fallback #1 (e.g., Groq free tier)
5. On failure: Try Fallback #2 (e.g., OpenAI)
6. All failed: Return error with diagnostic info

**Supported Providers:**

Local (via Model Hub):
- Ollama
- llama.cpp
- LM Studio (API)
- Custom GGUF models

Cloud APIs:
- OpenAI (GPT-4o, etc.)
- Anthropic (Claude)
- Google (Gemini)
- Groq (fast, free tier)
- Together AI
- Hugging Face Inference
- Mistral AI
- Cohere
- Azure OpenAI
- OpenRouter (multi)

**Format Support:**
- GGUF (llama.cpp)
- ONNX
- SafeTensors
- PyTorch (.bin)

---

## 3. User Interface & Editor

### Overall App Layout

```
+-------------------------------------------------------------------------+
|  Skynette                                                    - [] X     |
+-------------------------------------------------------------------------+
| +---------+  +-----------------------------------------------------------+
| | Workflows|  |                                                          |
| |         |  |                    EDITOR AREA                            |
| +---------+  |                                                           |
| | AI Hub  |  |         (Simple Mode or Advanced Mode)                    |
| |         |  |                                                           |
| +---------+  |                                                           |
| | Plugins |  |                                                           |
| |         |  +-----------------------------------------------------------+
| +---------+  |  > Run  | Debug | Save |  Simple <=> Advanced             |
| | Runs    |  +-----------------------------------------------------------+
| |         |  +-----------------------------------------------------------+
| +---------+  | Skynet Assistant                                    - X   |
| | Settings|  | How can I help you build today?                           |
| |         |  | [Type a message or describe a workflow...]                |
| +---------+  +-----------------------------------------------------------+
+-------------------------------------------------------------------------+
```

### Navigation Sidebar

| Section | Description |
|---------|-------------|
| **Workflows** | All your workflows, organized in folders |
| **AI Hub** | Model browser, downloads, local model management |
| **Plugins** | Installed plugins, marketplace browser |
| **Runs** | Execution history, logs, performance metrics |
| **Settings** | App preferences, credentials vault, backup/sync |

### Simple Mode (Step Builder)

For beginners - a clean, linear view:
- Linear step-by-step flow (easy to follow)
- Branches shown as nested/indented steps
- Click any step to configure in a side panel
- Drag to reorder steps
- "Add condition" button for If/Else
- Clear visual flow with arrows

### Advanced Mode (Node Canvas)

For power users - full visual programming:
- Infinite canvas with pan/zoom
- Drag nodes from palette or right-click menu
- Connect nodes by dragging wires between ports
- Multi-select, copy/paste, group nodes
- Minimap for navigation
- Snap-to-grid option
- Node search (Ctrl+K)
- Keyboard shortcuts

### Skynet Assistant Capabilities

- Natural language -> workflow generation
- "Why did this fail?" debugging
- "How do I..." explanations
- "Improve this workflow" suggestions
- Voice input support
- Attach screenshots for visual debugging
- Context-aware (knows your current workflow)

### Mobile Layout

On tablets/phones, the UI adapts:
- Bottom navigation bar
- Simplified workflow editor (Simple Mode preferred)
- Focus on monitoring and quick edits
- Full Skynet chat for building on-the-go
- Push notifications for workflow status

---

## 4. Plugin System & Marketplace

### Plugin Types

| Type | Description | Example |
|------|-------------|---------|
| **Node Pack** | Adds new nodes | Shopify nodes |
| **Trigger Pack** | Adds new triggers | Stripe webhooks |
| **AI Provider** | Adds AI model providers | Custom API |
| **Theme** | UI customization | Dark mode variants |
| **Template Pack** | Pre-built workflows | Marketing templates |
| **Integration Suite** | Complete app integration | Full HubSpot suite |

### Plugin Structure

```
my-plugin/
├── plugin.yaml              # Plugin manifest
├── icon.png                 # Plugin icon (256x256)
├── README.md                # Documentation
├── requirements.txt         # Python dependencies
├── src/
│   ├── __init__.py
│   ├── nodes/
│   ├── triggers/
│   └── auth/
└── tests/
```

### Plugin Security Model

**Submission Flow:**
1. Developer Submits
2. Automated Review (malware scan, CVE check, API compliance)
3. Manual Review (premium only)
4. Published to Marketplace

**Runtime Sandboxing:**
- Isolated Python environment
- No filesystem access (except temp folder)
- Network: only declared domains
- Memory limit: 256MB per execution
- Timeout: 60 seconds (configurable)
- No system calls, subprocess, or shell

**Trust Levels:**
- Verified: Reviewed by Skynette team
- Community: Passed automated checks
- Unverified: User-installed from file

### Developer Revenue Model

**Pricing Options:**
- Free (open source, donations)
- One-time purchase ($1.99 - $99.99)
- Subscription ($0.99 - $29.99/month)
- Freemium (free tier + premium features)

**Revenue Split:**
- Developer: 80%
- Skynette: 20%
- First year: 90% / 10% for early developers

---

## 5. Data Flow, Execution & Error Handling

### Data Flow Model

Every node receives input, processes it, and produces output:

```json
{
  "node": "http_request_1",
  "execution_id": "exec_abc123",
  "timestamp": "2026-01-07T10:30:00Z",
  "data": {
    "status": 200,
    "body": { "users": [...] }
  },
  "meta": {
    "duration_ms": 234,
    "retries": 0
  }
}
```

### Expression System

**Basic References:**
- `{{$trigger.data}}` - Data from trigger
- `{{$node.HTTP_Request.body}}` - Output from specific node
- `{{$prev.items}}` - Output from previous node
- `{{$vars.api_key}}` - Workflow variable
- `{{$env.DATABASE_URL}}` - Environment variable

**Transformations:**
- `{{$prev.items.length}}` - Array length
- `{{$prev.items.filter(i => i.active)}}` - Filter array
- `{{$prev.items.map(i => i.email)}}` - Map to emails
- `{{$prev.date | format('YYYY-MM-DD')}}` - Pipe filters

**Built-in Functions:**
- `{{$now()}}` - Current timestamp
- `{{$uuid()}}` - Generate UUID
- `{{$hash($prev.password)}}` - SHA-256 hash
- `{{$ai.summarize($prev.text)}}` - AI-powered transforms

### Execution Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| **Immediate** | Execute right now | Manual trigger |
| **Scheduled** | Execute at specific time | Cron jobs |
| **Queued** | Execute when resources available | Batch processing |
| **Parallel** | Multiple instances simultaneously | High-volume |
| **Debug** | Step-by-step with inspection | Development |

### Error Handling

**Error Types:**
- Connection Error
- Authentication
- Rate Limited
- Validation
- Server Error
- Execution Error
- Resource Error

**Error Strategies (per node):**
1. Retry (with exponential backoff)
2. Use fallback value
3. Skip and continue
4. Branch to error handler
5. Stop workflow

**Retry Configuration:**
- Max retries: configurable
- Backoff: Fixed, Exponential, or Linear
- Retry conditions: selectable error types
- On final failure: configurable action

### AI Auto-Debug

When a workflow fails, Skynet analyzes and explains:
- Root cause identification
- Plain-English explanation
- Suggested fixes with one-click apply
- Alternative approaches

---

## 6. Cloud Features (Optional)

### Cloud Tiers

| Tier | Price | Features |
|------|-------|----------|
| **Free** | $0 | Local only, unlimited workflows, all core features |
| **Pro** | $9/mo | Cloud sync, cross-device, backups, remote webhooks |
| **Team** | $29/user/mo | Team workspace, shared credentials, RBAC, SSO |
| **Cloud Runners** | +$19/mo | Run workflows in cloud when device is off |

### Sync Model

**What Syncs:**
- Workflow definitions (YAML)
- App settings
- Plugin list
- Workflow templates
- Version history

**What Stays Local:**
- Credentials (never sent to cloud)
- Execution logs (unless shared)
- Downloaded AI models
- Temp files and cache

**Sync Behavior:**
- Real-time sync when online
- Offline changes queued
- End-to-end encryption (E2EE)
- Zero-knowledge: servers cannot read your data

### Privacy & Security

**Credentials:**
- Stored locally in encrypted SQLite
- NEVER sent to cloud
- Device-specific key + user password

**Cloud Data:**
- End-to-end encrypted
- Zero-knowledge architecture
- GDPR compliant

**AI Usage:**
- Local models: 100% on-device
- Cloud AI: data sent to provider per their ToS
- Cost tracking stored locally

---

## 7. Technical Implementation

### Project Structure

```
skynette/
├── src/
│   ├── main.py                  # Entry point
│   ├── ui/                      # Flet UI Layer
│   │   ├── components/          # Reusable components
│   │   ├── views/               # Full-page views
│   │   └── dialogs/             # Modal dialogs
│   ├── core/                    # Core Engine
│   │   ├── workflow/            # Executor, parser, scheduler
│   │   ├── nodes/               # All node implementations
│   │   ├── expressions/         # Expression parser/evaluator
│   │   └── errors/              # Error handling
│   ├── ai/                      # AI Gateway
│   │   ├── gateway.py           # Unified interface
│   │   ├── providers/           # Provider implementations
│   │   ├── models/              # Model Hub logic
│   │   └── assistant/           # Skynet Assistant
│   ├── plugins/                 # Plugin System
│   ├── data/                    # Data Layer
│   └── cloud/                   # Cloud Features
├── assets/                      # Static assets
├── workflows/                   # Templates
├── tests/                       # Test suite
└── scripts/                     # Build scripts
```

### Key Dependencies

**UI:** flet >= 0.25.0

**AI & ML:**
- llama-cpp-python
- openai, anthropic, google-generativeai, groq
- huggingface-hub
- chromadb

**Data:**
- sqlalchemy, aiosqlite
- pyyaml
- cryptography, keyring

**HTTP:**
- httpx, websockets
- fastapi, uvicorn

**Workflow:**
- apscheduler
- watchdog
- jinja2

### Development Phases

**Phase 1: MVP Foundation**
- Basic UI shell, Simple Mode editor
- Core nodes (8): Manual, HTTP, Variable, If/Else, Transform, Log, Read/Write File
- Sequential executor, YAML storage, SQLite
- Windows .exe build

**Phase 2: AI Integration**
- AI Gateway, provider integrations
- Smart AI node, Model Hub UI
- Local inference (Ollama, llama.cpp)
- Provider fallback chain

**Phase 3: Full Node Set**
- All trigger types
- All flow control, data, database nodes
- App integrations (Slack, Discord, Google, etc.)
- Expression system with AI copilot

**Phase 4: Advanced Editor**
- Node canvas (Advanced Mode)
- Skynet Assistant
- NL -> workflow generation
- Debug mode, version history

**Phase 5: Plugin System**
- Plugin SDK, loader, sandbox
- Marketplace UI
- First-party plugins

**Phase 6: Cross-Platform**
- macOS, Linux builds
- iOS, Android apps
- Auto-update system

**Phase 7: Cloud Features**
- Cloud backend, auth
- E2E encrypted sync
- Team workspaces
- Payment integration

### MVP Scope (Phase 1)

**Included:**
- App shell with navigation
- Workflow list (create, rename, delete)
- Simple Mode editor only
- 8 essential nodes
- Sequential execution
- Basic expressions
- YAML workflow storage
- SQLite for settings
- Windows .exe

**Excluded (Later):**
- AI nodes
- Model Hub
- Skynet Assistant
- Advanced Mode canvas
- Plugins
- Mobile apps
- Cloud sync

### Build & Distribution

**Desktop:**
- Windows: .exe installer (~150MB)
- macOS: .dmg with notarization (~120MB)
- Linux: AppImage + .deb (~130MB)

**Mobile:**
- iOS: App Store
- Android: Play Store + direct APK

**Auto-Update:**
- Check on startup
- Background download
- User-prompted install
- Rollback on failure

---

## Appendix: Research Summary

### Competitive Landscape

**Traditional Workflow Tools:**
- n8n: Fair-code license, self-hosted, 400+ nodes
- Zapier: 8000+ integrations, expensive at scale
- Make: Better value than Zapier, complex workflows
- Activepieces: MIT license, unlimited tasks model

**AI Workflow Tools:**
- Langflow: MIT, maximum flexibility, Python components
- Flowise: Stable, enterprise-ready, basic debugging
- Dify: Best debugging, full lifecycle, restrictive license

### Key Insights

1. Open-source is closing the gap with commercial tools
2. AI-first is essential for 2026
3. Hybrid architecture (local + optional cloud) wins
4. Multi-provider AI support is critical
5. Plugin ecosystems drive growth

### Free AI Options

**Local:** Ollama, LM Studio, llama.cpp
**Cloud Free Tiers:** Groq (14,400 req/day), Together AI ($25 credits), Hugging Face

### Top Open-Source Models

- Llama 4 (Meta) - General purpose
- Qwen 3/3.5 (Alibaba) - Most downloaded, 100+ languages
- Mistral/Mixtral - Best cost-to-performance
- DeepSeek R1/V3 - Enterprise adoption
- Gemma 3 (Google) - Fine-tuning friendly

---

## Next Steps

1. **Save this document** - Done
2. **Create project structure** - Next
3. **Implement MVP Phase 1** - Begin development
4. **Test on Windows** - Validate .exe build
5. **Iterate based on usage** - Continuous improvement

---

*Document generated: 2026-01-07*
*Author: Skynette Design Team*
