# External Integrations

**Analysis Date:** 2025-01-17

## AI Providers

**OpenAI:**
- Purpose: Chat completion, embeddings, image generation (DALL-E 3)
- SDK: `openai>=1.0.0` (AsyncOpenAI client)
- Auth: `OPENAI_API_KEY` environment variable
- Implementation: `src/ai/providers/openai.py`
- Models: GPT-4o, GPT-4o Mini, GPT-4 Turbo, GPT-3.5 Turbo
- Capabilities: TEXT_GENERATION, CHAT, EMBEDDINGS, IMAGE_GENERATION, IMAGE_ANALYSIS, CODE_GENERATION, FUNCTION_CALLING

**Anthropic:**
- Purpose: Chat completion with Claude models
- SDK: `anthropic>=0.25.0` (AsyncAnthropic client)
- Auth: `ANTHROPIC_API_KEY` environment variable
- Implementation: `src/ai/providers/anthropic.py`
- Models: Claude Sonnet 4, Claude 3.5 Sonnet, Claude 3.5 Haiku, Claude 3 Opus
- Capabilities: TEXT_GENERATION, CHAT, IMAGE_ANALYSIS, CODE_GENERATION

**Ollama (Local):**
- Purpose: Local model inference via Ollama API
- SDK: Native HTTP via `httpx` (no SDK)
- Auth: None (local service)
- Implementation: `src/ai/providers/ollama.py`
- Endpoint: `http://localhost:11434`
- Capabilities: TEXT_GENERATION, CHAT, EMBEDDINGS, CODE_GENERATION

**LM Studio (Local):**
- Purpose: Local model inference via OpenAI-compatible API
- SDK: `openai>=1.0.0` (same as OpenAI, different base_url)
- Auth: `api_key="lm-studio"` (placeholder)
- Implementation: `src/ai/providers/lm_studio.py`
- Endpoint: `http://localhost:1234/v1`
- Capabilities: TEXT_GENERATION, CHAT, EMBEDDINGS, CODE_GENERATION

**Local llama.cpp:**
- Purpose: Direct GGUF model inference
- SDK: `llama-cpp-python>=0.2.0`
- Auth: None (local files)
- Implementation: `src/ai/providers/local.py`
- Model location: `~/skynette/models/*.gguf`
- Capabilities: TEXT_GENERATION, CHAT, EMBEDDINGS, CODE_GENERATION

## Data Storage

**SQLite:**
- Purpose: Workflow metadata, execution history, settings, credentials, AI usage tracking
- Driver: `aiosqlite>=0.19.0` (async)
- ORM: `sqlalchemy>=2.0.0`
- Location: `~/.skynette/skynette.db`
- Implementation: `src/data/storage.py`

**ChromaDB (Vector Store):**
- Purpose: RAG document embeddings
- SDK: In-memory implementation in MVP, full ChromaDB in production
- Implementation: `src/rag/chromadb_client.py`
- Storage: Configurable path

**File Storage:**
- Purpose: Workflow YAML files, local AI models
- Location: `~/.skynette/workflows/` (workflows), `~/skynette/models/` (GGUF models)

## Cloud Services

**AWS S3:**
- Purpose: File upload/download, object listing
- SDK: `boto3>=1.28.0`
- Auth: `access_key` + `secret_key` per node configuration
- Implementation: `src/core/nodes/apps/aws_s3.py`
- Nodes: S3UploadNode, S3DownloadNode, S3ListObjectsNode

**Google Sheets:**
- Purpose: Read/write spreadsheet data
- SDK: `google-api-python-client>=2.0.0`
- Auth: Service Account JSON credential
- Implementation: `src/core/nodes/apps/google_sheets.py`
- Nodes: GoogleSheetsReadNode, GoogleSheetsWriteNode

**Google Drive:**
- Purpose: File management (planned)
- SDK: `google-api-python-client>=2.0.0`
- Implementation: `src/core/nodes/apps/google_drive.py`

## Communication Platforms

**Discord:**
- Purpose: Send messages via webhook or bot API
- SDK: Native HTTP via `httpx`
- Auth: Webhook URL or Bot Token
- Implementation: `src/core/nodes/apps/discord.py`
- Nodes: DiscordWebhookNode, DiscordBotMessageNode

**Slack:**
- Purpose: Send messages
- SDK: Native HTTP via `httpx`
- Implementation: `src/core/nodes/apps/slack.py`

**Microsoft Teams:**
- Purpose: Send messages
- SDK: Native HTTP via `httpx`
- Implementation: `src/core/nodes/apps/teams.py`

**Telegram:**
- Purpose: Send messages
- SDK: Native HTTP via `httpx`
- Implementation: `src/core/nodes/apps/telegram.py`

**Email (SMTP/IMAP):**
- Purpose: Send and read emails
- SDK: Python stdlib `smtplib`, `imaplib`
- Auth: SMTP/IMAP credentials per node
- Implementation: `src/core/nodes/apps/email.py`
- Nodes: EmailSendNode, EmailReadNode

## Developer Tools

**GitHub:**
- Purpose: Create issues, PRs, list repositories
- SDK: Native HTTP via `httpx`
- Auth: Personal Access Token
- Implementation: `src/core/nodes/apps/github.py`
- Nodes: GitHubCreateIssueNode, GitHubCreatePRNode, GitHubListReposNode

**Jira:**
- Purpose: Issue management
- SDK: Native HTTP via `httpx`
- Implementation: `src/core/nodes/apps/jira.py`

**Trello:**
- Purpose: Card/board management
- SDK: Native HTTP via `httpx`
- Implementation: `src/core/nodes/apps/trello.py`

## Business Tools

**Notion:**
- Purpose: Page/database management
- SDK: Native HTTP via `httpx`
- Implementation: `src/core/nodes/apps/notion.py`

**Airtable:**
- Purpose: Database operations
- SDK: Native HTTP via `httpx`
- Implementation: `src/core/nodes/apps/airtable.py`

**HubSpot:**
- Purpose: CRM operations
- SDK: Native HTTP via `httpx`
- Implementation: `src/core/nodes/apps/hubspot.py`

**Zendesk:**
- Purpose: Support ticket management
- SDK: Native HTTP via `httpx`
- Implementation: `src/core/nodes/apps/zendesk.py`

## Payment/E-commerce

**Stripe:**
- Purpose: Payment processing
- SDK: Native HTTP via `httpx`
- Implementation: `src/core/nodes/apps/stripe.py`

**Shopify:**
- Purpose: E-commerce operations
- SDK: Native HTTP via `httpx`
- Implementation: `src/core/nodes/apps/shopify.py`

## Messaging Services

**Twilio:**
- Purpose: SMS/voice
- SDK: Native HTTP via `httpx`
- Implementation: `src/core/nodes/apps/twilio.py`

**SendGrid:**
- Purpose: Email delivery
- SDK: Native HTTP via `httpx`
- Implementation: `src/core/nodes/apps/sendgrid.py`

**Mailchimp:**
- Purpose: Email marketing
- SDK: Native HTTP via `httpx`
- Implementation: `src/core/nodes/apps/mailchimp.py`

## Auto-Update System

**GitHub Releases:**
- Purpose: Check for and download application updates
- SDK: Native HTTP via `httpx`
- Auth: None (public API)
- Implementation: `src/updater.py`
- Endpoint: `https://api.github.com/repos/skynette/skynette/releases/latest`

## Webhooks

**Incoming Webhooks:**
- Purpose: Trigger workflows via HTTP
- Implementation: `src/core/nodes/apps/webhook.py` (WebhookTriggerNode)
- Server: FastAPI + Uvicorn
- Methods: GET, POST, PUT, DELETE, ANY
- Auth options: None, Header Token, Query Parameter, Basic Auth

**Outgoing Webhooks:**
- Purpose: Call external HTTP endpoints
- Implementation: `src/core/nodes/apps/webhook.py` (WebhookCallNode)
- Methods: GET, POST, PUT, PATCH, DELETE
- Features: Custom headers, auth, timeout configuration

## Environment Configuration

**Required for Core Features:**
- None (works offline with local models)

**Required for Cloud AI:**
- `OPENAI_API_KEY` - OpenAI features
- `ANTHROPIC_API_KEY` - Anthropic features

**Required for Integrations:**
- API keys/tokens configured per-node in workflow editor
- Service account JSON for Google APIs
- AWS credentials for S3

**Secrets Storage:**
- OS keyring via `keyring>=24.0.0`
- Encrypted credentials table in SQLite
- Implementation: `src/data/storage.py` (credentials table)

## RAG System

**Document Processing:**
- Implementation: `src/rag/processor.py`
- Supported: Text chunking with configurable size/overlap

**Embeddings:**
- Implementation: `src/rag/embeddings.py`
- Model: `all-MiniLM-L6-v2` (384 dimensions)
- SDK: `sentence-transformers>=2.2.0`

**Vector Storage:**
- Implementation: `src/rag/chromadb_client.py`
- Current: In-memory vector store for MVP
- Production: ChromaDB persistent storage

---

*Integration audit: 2025-01-17*
