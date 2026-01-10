# Phase 4: AI Integration - Design Document

**Date**: 2026-01-10
**Status**: Design Complete, Ready for Implementation
**Target Release**: v0.4.0

---

## Executive Summary

Phase 4 makes AI a production-ready, first-class feature in Skynette by building comprehensive UI, testing, and cost management around the existing AI infrastructure. This transforms AI from optional experimental code into a polished, user-friendly system with full observability.

**Design Philosophy**: Accessible for beginners (guided wizard), powerful for experts (advanced settings), transparent about costs (full analytics).

**Current State**:
- ✅ AI Gateway with auto-fallback exists
- ✅ 5 AI providers implemented (OpenAI, Anthropic, Local, LM Studio, Demo)
- ✅ 5 AI nodes created (Text Generation, Chat, Summarize, Extract, Classify)
- ❌ No AI tests (0 coverage)
- ❌ No UI for AI management
- ❌ AI dependencies are optional, not core
- ❌ No cost tracking or usage analytics

**Phase 4 Goal**: Production-ready AI with 110+ tests, full UI, cost transparency, and seamless user experience.

---

## Architecture Overview

### Three-Layer Architecture

#### 1. AI Core Layer (Exists, needs testing)

**AIGateway** - Unified interface for all AI operations
- Provider registration and priority management
- Auto-fallback when providers fail
- Response caching for duplicate requests
- Usage logging for analytics

**5 Providers** (all implemented):
- **OpenAI**: GPT-3.5, GPT-4 series
- **Anthropic**: Claude 3 series (Opus, Sonnet, Haiku)
- **Local**: llama.cpp integration for GGUF models
- **LM Studio**: Local API server integration
- **Demo**: Mock provider for testing/offline use

**Provider Abstraction**:
- `BaseProvider` abstract class
- Capability detection (`AICapability` enum)
- Standardized response format (`AIResponse`)
- Streaming support (`AIStreamChunk`)

#### 2. AI Services Layer (New - Sprint 1)

**ModelHub** - Local model management
- Download GGUF models from Hugging Face
- Curated recommendations (10 popular models)
- Full catalog browsing with search
- System requirements checking (RAM/GPU detection)
- Auto-update detection

**UsageTracker** - Analytics and logging
- Per-request logging (tokens, cost, latency)
- Aggregation by provider, workflow, time period
- Real-time cost calculation
- Export to CSV for expense tracking

**ProviderHealth** - Monitoring and diagnostics
- Availability checking
- Latency tracking
- Error rate monitoring
- Auto-disable on repeated failures

**CostCalculator** - Pricing engine
- Provider-specific pricing tables
- Model-specific token costs
- Real-time cost estimation
- Historical cost analysis

#### 3. AI UI Layer (New - Sprint 2 & 3)

**AIHubView** - Main AI management interface
- Setup Wizard (first-time onboarding)
- My Providers (management and configuration)
- Model Library (download and browse)

**UsageDashboard** - Cost analytics and budgets
- Time-series cost charts
- Provider breakdown tables
- Workflow cost analysis
- Budget alerts and limits

**Node Palette Updates** - Expose AI nodes
- New "AI" category in palette
- 5 AI nodes visible and draggable
- Node icons and descriptions

**ProviderStatusBar** - Live status indicator
- Shows active providers
- Quick access to AI Hub
- Alert badges for issues

---

## AI Hub UI - Detailed Design

### Tab 1: Setup Wizard (First-Time Experience)

**Step 1: Choose Providers**

```
┌─────────────────────────────────────────────────────┐
│  Welcome to Skynette AI Setup                       │
│                                                      │
│  Select which AI providers you want to use:         │
│                                                      │
│  ☐ OpenAI (GPT-4, GPT-3.5)                         │
│     Cloud • Requires API key • $$$                  │
│                                                      │
│  ☐ Anthropic (Claude 3 Opus, Sonnet, Haiku)       │
│     Cloud • Requires API key • $$                   │
│                                                      │
│  ☐ Local Models (llama.cpp)                        │
│     Free • Private • Runs on your computer          │
│                                                      │
│  ☐ LM Studio                                        │
│     Free • Requires LM Studio running locally       │
│                                                      │
│  [ Skip Setup ]              [ Next: Configure → ]  │
└─────────────────────────────────────────────────────┘
```

**Step 2: Configure Selected Providers**

For each selected provider, show configuration:

**OpenAI Configuration**:
```
┌─────────────────────────────────────────────────────┐
│  Configure OpenAI                                    │
│                                                      │
│  API Key: [sk-proj-.....................] 🔒        │
│                                                      │
│  [ Test Connection ]                                 │
│                                                      │
│  Status: ✓ Connected successfully!                  │
│  Available models: GPT-4, GPT-4 Turbo, GPT-3.5      │
│                                                      │
│  [ ← Back ]                    [ Next: Local → ]    │
└─────────────────────────────────────────────────────┘
```

**Local Models Configuration**:
```
┌─────────────────────────────────────────────────────┐
│  Configure Local Models                              │
│                                                      │
│  System Check:                                       │
│  ✓ RAM: 16GB detected (8GB minimum required)        │
│  ✓ llama.cpp: Ready to use                         │
│  ⚠️ GPU: No CUDA detected (CPU mode, slower)        │
│                                                      │
│  Your system can run models up to 7B parameters.    │
│                                                      │
│  [ ← Back ]                [ Next: Download → ]     │
└─────────────────────────────────────────────────────┘
```

**Step 3: Download Starter Model** (if Local selected)

```
┌─────────────────────────────────────────────────────┐
│  Download Your First Model                           │
│                                                      │
│  Recommended for you:                                │
│                                                      │
│  ┌───────────────────────────────────────────────┐ │
│  │ Mistral 7B Instruct v0.2                      │ │
│  │ ⭐⭐⭐⭐⭐ 4.8/5 • 4.1GB • General Purpose      │ │
│  │                                                │ │
│  │ Fast and capable model for chat, instructions │ │
│  │ and general text tasks. Great starting point! │ │
│  │                                                │ │
│  │ Requirements: ✓ 8GB RAM                       │ │
│  │                                                │ │
│  │              [ Download Now ]                  │ │
│  └───────────────────────────────────────────────┘ │
│                                                      │
│  You can download more models later from the         │
│  Model Library.                                      │
│                                                      │
│  [ Skip Download ]                  [ Download → ]   │
└─────────────────────────────────────────────────────┘
```

**Step 4: Summary & Completion**

```
┌─────────────────────────────────────────────────────┐
│  Setup Complete! 🎉                                 │
│                                                      │
│  Configured Providers:                               │
│  ✓ OpenAI (GPT-4) - Active                         │
│  ✓ Local Models (Mistral 7B) - Active              │
│                                                      │
│  You can now use AI nodes in your workflows!         │
│                                                      │
│  Next Steps:                                         │
│  • Add AI nodes from the node palette               │
│  • Check out example workflows                      │
│  • Monitor usage in the AI Dashboard                │
│                                                      │
│                          [ Start Using AI ]          │
└─────────────────────────────────────────────────────┘
```

### Tab 2: My Providers (Management View)

Provider card grid layout:

```
┌─────────────────────┐  ┌─────────────────────┐
│ OpenAI              │  │ Anthropic           │
│ ● Active            │  │ ○ Configured        │
│                     │  │                     │
│ Last used: 2h ago   │  │ Last used: Never    │
│ Uptime: 98.5%       │  │ Uptime: N/A         │
│ Avg latency: 1.2s   │  │                     │
│                     │  │                     │
│ [ Configure ]       │  │ [ Configure ]       │
└─────────────────────┘  └─────────────────────┘

┌─────────────────────┐  ┌─────────────────────┐
│ Local Models        │  │ LM Studio           │
│ ● Active            │  │ ✗ Not Running       │
│                     │  │                     │
│ Model: Mistral 7B   │  │ Start LM Studio to  │
│ Last used: 5m ago   │  │ enable this provider│
│ Avg latency: 3.5s   │  │                     │
│                     │  │                     │
│ [ Configure ]       │  │ [ Configure ]       │
└─────────────────────┘  └─────────────────────┘
```

**Advanced Settings Modal** (opened from Configure button):

```
┌──────────────────────────────────────────────────────┐
│  OpenAI Configuration                          [ × ] │
├──────────────────────────────────────────────────────┤
│                                                       │
│  Basic Settings                                       │
│  ─────────────                                        │
│  API Key: ●●●●●●●●●●●●●●●●●●●●  [ Change ]          │
│  Default Model: [ GPT-4 Turbo ▼ ]                    │
│  Enabled: [✓]                                        │
│                                                       │
│  Advanced Settings  [ Show ▼ ]                       │
│  ─────────────────                                    │
│  Endpoint URL: [ https://api.openai.com/v1 ]         │
│  Timeout: [ 30 ] seconds                             │
│  Max Retries: [ 3 ]                                  │
│  Priority: [ 1 ] (Lower = higher priority)           │
│                                                       │
│  Usage Limits                                         │
│  ─────────────                                        │
│  Max tokens per request: [ 4096 ]                    │
│  Daily request limit: [ 1000 ] (0 = unlimited)       │
│                                                       │
│                      [ Cancel ]  [ Save Changes ]     │
└──────────────────────────────────────────────────────┘
```

### Tab 3: Model Library

**Tab 3a: Recommended Models** (Curated list)

```
┌─────────────────────────────────────────────────────┐
│  [ Recommended ]  [ Browse Hugging Face ]           │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Popular models curated by the Skynette team:       │
│                                                      │
│  ┌──────────┬──────────┬──────────┐               │
│  │ Mistral  │ Llama 2  │ Phi-2    │               │
│  │ 7B       │ 7B Chat  │          │               │
│  │          │          │          │               │
│  │ 4.1GB    │ 3.8GB    │ 2.7GB    │               │
│  │ General  │ Chat     │ Small    │               │
│  │ ⭐ 4.8   │ ⭐ 4.6   │ ⭐ 4.5   │               │
│  │          │          │          │               │
│  │ ✓ Inst.  │ Download │ Download │               │
│  └──────────┴──────────┴──────────┘               │
│                                                      │
│  ┌──────────┬──────────┬──────────┐               │
│  │ CodeLlama│ Mistral  │ TinyLlama│               │
│  │ 7B       │ OpenOrca │ 1.1B     │               │
│  │          │          │          │               │
│  │ 3.5GB    │ 4.1GB    │ 637MB    │               │
│  │ Code     │ Instruct │ Lite     │               │
│  │ ⭐ 4.7   │ ⭐ 4.9   │ ⭐ 4.3   │               │
│  │          │          │          │               │
│  │ Download │ Download │ Download │               │
│  └──────────┴──────────┴──────────┘               │
│                                                      │
└─────────────────────────────────────────────────────┘
```

**Model Card Detail**:
```
┌─────────────────────────────────────────────┐
│  Mistral 7B Instruct v0.2                   │
│  ⭐⭐⭐⭐⭐ 4.8/5 (12.4K downloads)          │
├─────────────────────────────────────────────┤
│  Size: 4.1GB (Q4_K_M quantization)          │
│  Purpose: General Purpose                   │
│                                              │
│  Fast and capable model for chat,           │
│  instructions and general text tasks.       │
│  Great starting point!                      │
│                                              │
│  Requirements:                               │
│  ✓ 8GB RAM (You have 16GB)                 │
│  ✓ 4.5GB free space                        │
│  ⚠️ GPU optional (faster with CUDA)         │
│                                              │
│  From: TheBloke/Mistral-7B-Instruct-v0.2   │
│                                              │
│              [ Download Now ]                │
└─────────────────────────────────────────────┘
```

**Tab 3b: Browse Hugging Face** (Power users)

```
┌─────────────────────────────────────────────────────┐
│  [ Recommended ]  [ Browse Hugging Face ]           │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Search: [mistral code         ] [ 🔍 Search ]     │
│                                                      │
│  Filters:                                            │
│  Size: [━━━━●────] 1GB - 10GB                       │
│  Quantization: [ Q4_K_M (Recommended) ▼ ]           │
│  Sort by: [ Downloads ▼ ]                           │
│                                                      │
│  Results (142 models found):                         │
│                                                      │
│  ┌────────────────────────────────────────────┐   │
│  │ CodeLlama-7B-Instruct-GGUF                 │   │
│  │ 3.5GB • Code Generation • ⭐ 4.7           │   │
│  │ Downloads: 45.2K                            │   │
│  │                              [ Download ]   │   │
│  └────────────────────────────────────────────┘   │
│                                                      │
│  ┌────────────────────────────────────────────┐   │
│  │ Mistral-7B-Code-v0.1-GGUF                  │   │
│  │ 4.0GB • Code & Chat • ⭐ 4.6               │   │
│  │ ⚠️ This model hasn't been verified         │   │
│  │                              [ Download ]   │   │
│  └────────────────────────────────────────────┘   │
│                                                      │
└─────────────────────────────────────────────────────┘
```

**Download Progress Overlay**:
```
┌─────────────────────────────────────────────────────┐
│  Downloading Mistral 7B Instruct                     │
├─────────────────────────────────────────────────────┤
│                                                      │
│  [████████████████░░░░░░░░░] 67% (2.7GB / 4.1GB)   │
│                                                      │
│  Speed: 8.5 MB/s                                     │
│  Time remaining: 2 minutes                           │
│                                                      │
│  You can continue using Skynette while downloading.  │
│                                                      │
│              [ Pause ]  [ Cancel ]                   │
└─────────────────────────────────────────────────────┘
```

---

## Usage Dashboard - Cost Analytics Design

### Dashboard Layout

**Top Row: Key Metrics** (4 cards)

```
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ This Month   │ │ Total Calls  │ │ Tokens Used  │ │ Budget       │
│              │ │              │ │              │ │              │
│   $2.47      │ │    1,247     │ │   234.5K     │ │ 25% used     │
│   ↑ 12%     │ │   ↓ 5%      │ │   ↑ 18%     │ │ [████░░░░]   │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
```

**Time-Series Chart** (Stacked area chart)

```
┌─────────────────────────────────────────────────────┐
│  Cost Over Time                                      │
│  [ Last 7 Days ]  [ Last 30 Days ]  [ 3 Months ]   │
├─────────────────────────────────────────────────────┤
│                                                      │
│  $0.50 │                          ╱╲               │
│        │                    ╱╲   ╱  ╲              │
│  $0.40 │              ╱╲   ╱  ╲ ╱    ╲             │
│        │        ╱╲   ╱  ╲ ╱    ╲      ╲            │
│  $0.30 │  ╱╲  ╱  ╲ ╱    ╲                           │
│        │ ╱  ╲╱    ╲                                 │
│  $0.20 │╱                                            │
│        │                                             │
│  $0.10 │                                             │
│        │                                             │
│  $0.00 └─────────────────────────────────────────   │
│         Jun 1    Jun 4    Jun 7    Jun 10          │
│                                                      │
│  Legend: ■ OpenAI  ■ Anthropic  ■ Local (Free)     │
└─────────────────────────────────────────────────────┘
```

Hover tooltip:
```
┌────────────────────┐
│ June 8, 2026       │
├────────────────────┤
│ OpenAI: $0.23      │
│ (145 calls)        │
│                    │
│ Anthropic: $0.15   │
│ (8 calls)          │
│                    │
│ Total: $0.38       │
└────────────────────┘
```

**Provider Breakdown Table**

```
┌─────────────────────────────────────────────────────────────────┐
│  Provider Breakdown (This Month)                                │
├──────────┬───────┬─────────┬─────────┬──────────────────────────┤
│ Provider │ Calls │ Tokens  │ Cost    │ Avg Cost/Call            │
├──────────┼───────┼─────────┼─────────┼──────────────────────────┤
│ OpenAI   │   89  │  45.2K  │ $1.81   │ $0.020                   │
│ (GPT-4)  │       │         │         │ ████████████░░░░░░       │
├──────────┼───────┼─────────┼─────────┼──────────────────────────┤
│ Anthropic│   24  │  18.1K  │ $0.54   │ $0.023                   │
│ (Claude) │       │         │         │ █████░░░░░░░░░░░         │
├──────────┼───────┼─────────┼─────────┼──────────────────────────┤
│ Local    │ 1,134 │ 171.2K  │ $0.00   │ FREE                     │
│ (Mistral)│       │         │         │ ████████████████████     │
└──────────┴───────┴─────────┴─────────┴──────────────────────────┘
```

**Workflow Breakdown** (Expandable section)

```
┌─────────────────────────────────────────────────────┐
│  Top Workflows by Cost                [ ▼ Expand ]  │
├─────────────────────────────────────────────────────┤
│                                                      │
│  1. Daily Report Generator                           │
│     $0.85 (34% of total) • 234 runs                 │
│     [████████░░░░░░░░░░░░░░░░░░]                    │
│                                                      │
│  2. Customer Support Classifier                      │
│     $0.62 (25% of total) • 89 runs                  │
│     [██████░░░░░░░░░░░░░░░░░░░]                     │
│                                                      │
│  3. Code Documentation Generator                     │
│     $0.45 (18% of total) • 12 runs                  │
│     [████░░░░░░░░░░░░░░░░░░░░]                      │
│                                                      │
│  [ View All Workflows ]                              │
└─────────────────────────────────────────────────────┘
```

Click workflow for detail view:
```
┌─────────────────────────────────────────────────────┐
│  Daily Report Generator - Cost Breakdown             │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Total Cost (June): $0.85                           │
│  Total Runs: 234                                     │
│  Avg Cost per Run: $0.0036                          │
│                                                      │
│  AI Nodes Used:                                      │
│  • Summarize Node: $0.52 (61%)                      │
│  • Extract Node: $0.28 (33%)                        │
│  • Text Generation: $0.05 (6%)                      │
│                                                      │
│  Most Expensive Run:                                 │
│  June 7, 10:23 AM - $0.12                           │
│  (Input: 3,245 tokens, Output: 1,892 tokens)        │
│                                                      │
│  [ View Execution History ]                          │
└─────────────────────────────────────────────────────┘
```

**Budget Management Panel**

```
┌─────────────────────────────────────────────────────┐
│  Budget Settings                                     │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Monthly Budget: $ [ 10.00 ]                        │
│                                                      │
│  Current Usage: $2.47 / $10.00 (25%)                │
│  [██████░░░░░░░░░░░░░░░░]                           │
│                                                      │
│  Alert Threshold: [━━━━━━━━●─] 80%                  │
│  Send alert when reaching $8.00                      │
│                                                      │
│  Notifications:                                      │
│  [✓] Show in-app alerts                             │
│  [ ] Send email notifications                        │
│      Email: [user@example.com      ]                │
│                                                      │
│  Budget resets on: 1st of each month                │
│                                                      │
│               [ Save Budget Settings ]               │
└─────────────────────────────────────────────────────┘
```

**Export Panel**

```
┌─────────────────────────────────────────────────────┐
│  Export Usage Data                                   │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Date Range:                                         │
│  From: [ June 1, 2026 ▼ ]                          │
│  To:   [ June 10, 2026 ▼ ]                         │
│                                                      │
│  Include:                                            │
│  [✓] Workflow names                                 │
│  [✓] Provider and model details                     │
│  [✓] Token counts                                   │
│  [✓] Cost breakdown                                 │
│  [ ] Raw request/response data                      │
│                                                      │
│  Format: [ CSV ▼ ]                                  │
│                                                      │
│              [ Download Export ]                     │
└─────────────────────────────────────────────────────┘
```

CSV Export Format:
```csv
timestamp,workflow_id,workflow_name,node_id,provider,model,prompt_tokens,completion_tokens,cost_usd
2026-06-08T10:23:15Z,wf_123,Daily Report,node_456,openai,gpt-4,1245,892,0.0234
2026-06-08T14:15:32Z,wf_789,Support Classifier,node_012,anthropic,claude-3-sonnet,567,123,0.0156
```

---

## Data Models & Storage

### Database Schema

**Table: `ai_providers`**
```sql
CREATE TABLE ai_providers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,              -- 'openai', 'anthropic', 'local', etc.
    enabled BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 0,       -- Lower = higher priority
    config JSON NOT NULL,             -- Provider-specific settings
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

Example `config` JSON:
```json
{
    "api_key_stored": true,
    "model": "gpt-4-turbo",
    "endpoint": "https://api.openai.com/v1",
    "timeout": 30,
    "max_retries": 3,
    "daily_limit": 1000,
    "custom_settings": {}
}
```

**Table: `ai_usage`**
```sql
CREATE TABLE ai_usage (
    id TEXT PRIMARY KEY,
    workflow_id TEXT,                 -- NULL for manual AI Hub tests
    node_id TEXT,                     -- Which AI node was used
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    cost_usd REAL,                   -- Calculated cost in USD
    latency_ms INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE
);

CREATE INDEX idx_ai_usage_workflow ON ai_usage(workflow_id);
CREATE INDEX idx_ai_usage_timestamp ON ai_usage(timestamp);
CREATE INDEX idx_ai_usage_provider ON ai_usage(provider);
```

**Table: `local_models`**
```sql
CREATE TABLE local_models (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    file_path TEXT NOT NULL UNIQUE,
    size_bytes INTEGER,
    quantization TEXT,               -- 'Q4_K_M', 'Q8_0', etc.
    source TEXT,                     -- 'recommended' or 'huggingface'
    huggingface_repo TEXT,
    downloaded_at TIMESTAMP,
    last_used TIMESTAMP,
    usage_count INTEGER DEFAULT 0
);
```

**Table: `ai_budgets`**
```sql
CREATE TABLE ai_budgets (
    id TEXT PRIMARY KEY DEFAULT 'default',
    monthly_limit_usd REAL,
    alert_threshold REAL DEFAULT 0.8,
    email_notifications BOOLEAN DEFAULT FALSE,
    notification_email TEXT,
    reset_day INTEGER DEFAULT 1,     -- Day of month to reset (1-31)
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Pydantic Models

**ProviderConfig**
```python
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import uuid4

class ProviderConfig(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str                        # 'openai', 'anthropic', etc.
    enabled: bool = True
    priority: int = 0
    config: dict
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

**UsageRecord**
```python
class UsageRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    workflow_id: Optional[str] = None
    node_id: Optional[str] = None
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    latency_ms: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    success: bool = True
    error_message: Optional[str] = None
```

**LocalModel**
```python
from pathlib import Path

class LocalModel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    file_path: Path
    size_bytes: int
    quantization: str
    source: str                      # 'recommended' | 'huggingface'
    huggingface_repo: Optional[str] = None
    downloaded_at: datetime
    last_used: Optional[datetime] = None
    usage_count: int = 0
```

**BudgetSettings**
```python
class BudgetSettings(BaseModel):
    id: str = 'default'
    monthly_limit_usd: Optional[float] = None
    alert_threshold: float = 0.8
    email_notifications: bool = False
    notification_email: Optional[str] = None
    reset_day: int = 1
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

### Storage Service

**AIStorage** (`src/ai/storage.py`)
```python
class AIStorage:
    """Handles all AI-related database operations."""

    def __init__(self, db_path: str = "~/.skynette/skynette.db"):
        self.db_path = Path(db_path).expanduser()

    # Provider Configuration
    async def save_provider_config(self, config: ProviderConfig) -> None
    async def get_provider_configs(self) -> list[ProviderConfig]
    async def get_provider_config(self, provider_id: str) -> Optional[ProviderConfig]
    async def update_provider_priority(self, provider_id: str, priority: int) -> None
    async def delete_provider_config(self, provider_id: str) -> None

    # Usage Tracking
    async def log_usage(self, record: UsageRecord) -> None
    async def get_usage_stats(
        self,
        start_date: date,
        end_date: date
    ) -> dict[str, Any]
    async def get_cost_by_provider(self, month: int, year: int) -> dict[str, float]
    async def get_cost_by_workflow(self, month: int, year: int) -> dict[str, float]
    async def get_total_cost(self, month: int, year: int) -> float

    # Model Management
    async def save_model(self, model: LocalModel) -> None
    async def get_downloaded_models(self) -> list[LocalModel]
    async def get_model(self, model_id: str) -> Optional[LocalModel]
    async def update_model_usage(self, model_id: str) -> None
    async def delete_model(self, model_id: str) -> None

    # Budget Management
    async def get_budget_settings(self) -> Optional[BudgetSettings]
    async def update_budget_settings(self, settings: BudgetSettings) -> None
```

### API Key Security

**Security Requirements**:
- ❌ Never store API keys in database
- ✅ Use system keyring for secure storage
- ✅ Keys encrypted at OS level
- ✅ Keys never logged or displayed

**Implementation** (using `keyring` package):
```python
import keyring

# Store API key
def store_api_key(provider: str, api_key: str) -> None:
    keyring.set_password('skynette-ai', provider, api_key)

# Retrieve API key
def get_api_key(provider: str) -> Optional[str]:
    return keyring.get_password('skynette-ai', provider)

# Delete API key
def delete_api_key(provider: str) -> None:
    keyring.delete_password('skynette-ai', provider)
```

**Platform Support**:
- **Windows**: Windows Credential Manager
- **macOS**: Keychain
- **Linux**: Secret Service API (GNOME Keyring, KWallet)

**Database Storage**:
```json
{
    "api_key_stored": true,  // Boolean flag only
    "model": "gpt-4"
}
```

The actual API key is retrieved via:
```python
api_key = keyring.get_password('skynette-ai', 'openai')
```

---

## Testing Strategy

### Test Coverage Goals

**Current State**: 0 AI tests
**Phase 4 Target**: 110+ tests, 90%+ coverage

### Test Suite Structure

#### 1. Unit Tests - AI Core (`tests/unit/test_ai_core.py`)

**AIGateway Tests** (20 tests):
```python
class TestAIGateway:
    async def test_register_provider(self)
    async def test_provider_priority_ordering(self)
    async def test_auto_fallback_on_failure(self)
    async def test_response_caching(self)
    async def test_usage_logging(self)
    async def test_capability_detection(self)
    async def test_provider_selection_by_capability(self)
    async def test_get_available_providers(self)
    async def test_concurrent_requests(self)
    async def test_streaming_support(self)
    # ... 10 more tests
```

**Cost Calculator Tests** (10 tests):
```python
class TestCostCalculator:
    def test_openai_gpt4_cost(self)
    def test_openai_gpt35_cost(self)
    def test_anthropic_opus_cost(self)
    def test_anthropic_sonnet_cost(self)
    def test_anthropic_haiku_cost(self)
    def test_local_model_cost_is_zero(self)
    def test_unknown_model_fallback(self)
    def test_cost_rounding(self)
    def test_bulk_cost_calculation(self)
    def test_pricing_updates(self)
```

#### 2. Unit Tests - AI Providers (`tests/unit/test_ai_providers.py`)

**Per-Provider Tests** (5 providers × 8 tests = 40 tests):
```python
class TestOpenAIProvider:
    async def test_initialization_with_api_key(self)
    async def test_initialization_without_api_key(self)
    async def test_availability_check(self)
    async def test_text_generation(self)
    async def test_chat_completion(self)
    async def test_streaming_response(self)
    async def test_api_error_handling(self)
    async def test_timeout_handling(self)
    async def test_rate_limit_handling(self)
    async def test_token_counting(self)

class TestAnthropicProvider:
    # Same 10 tests as OpenAI

class TestLocalProvider:
    # Same tests adapted for local models

class TestLMStudioProvider:
    # Same tests adapted for LM Studio

class TestDemoProvider:
    # Same tests for demo provider
```

**Mocking Strategy**:
```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.fixture
def mock_openai_response():
    return {
        "id": "chatcmpl-123",
        "choices": [{
            "message": {
                "role": "assistant",
                "content": "This is a test response."
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15
        }
    }

@pytest.mark.asyncio
async def test_openai_chat(mock_openai_response):
    with patch('openai.AsyncOpenAI') as mock_client:
        mock_client.return_value.chat.completions.create = AsyncMock(
            return_value=mock_openai_response
        )

        provider = OpenAIProvider()
        await provider.initialize()

        response = await provider.chat(
            messages=[{"role": "user", "content": "Hello"}],
            config=GenerationConfig()
        )

        assert response.content == "This is a test response."
        assert response.usage["total_tokens"] == 15
```

#### 3. Integration Tests - AI Nodes (`tests/integration/test_ai_nodes.py`)

**Node Execution Tests** (5 nodes × 6 tests = 30 tests):
```python
class TestTextGenerationNode:
    async def test_basic_generation(self)
    async def test_variable_substitution(self)
    async def test_system_prompt(self)
    async def test_provider_selection(self)
    async def test_temperature_control(self)
    async def test_error_propagation(self)

class TestChatNode:
    async def test_single_message(self)
    async def test_conversation_context(self)
    async def test_context_from_previous_nodes(self)
    async def test_max_tokens_limit(self)
    async def test_streaming_disabled_in_workflow(self)
    async def test_provider_fallback(self)

class TestSummarizeNode:
    async def test_short_text_summarization(self)
    async def test_long_text_summarization(self)
    async def test_custom_length(self)
    async def test_bullet_points_format(self)
    async def test_paragraph_format(self)
    async def test_invalid_input(self)

# Similar for ExtractNode and ClassifyNode
```

**End-to-End Workflow Test**:
```python
@pytest.mark.asyncio
async def test_complete_ai_workflow():
    """Test: Manual Trigger → Text Generation → Log"""
    storage = WorkflowStorage()
    executor = WorkflowExecutor()

    # Create workflow
    workflow = Workflow(name="AI Test Workflow")

    trigger = WorkflowNode(
        type="manual_trigger",
        name="Start"
    )

    ai_node = WorkflowNode(
        type="ai-text-generation",
        name="Generate",
        config={
            "prompt": "Write a haiku about {{topic}}",
            "provider": "demo",  # Use demo provider for tests
            "max_tokens": 100
        }
    )

    log = WorkflowNode(
        type="log_debug",
        name="Log Result"
    )

    workflow.nodes.extend([trigger, ai_node, log])
    workflow.connections.extend([
        WorkflowConnection(source_node_id=trigger.id, target_node_id=ai_node.id),
        WorkflowConnection(source_node_id=ai_node.id, target_node_id=log.id),
    ])

    # Execute
    execution = await executor.execute(
        workflow,
        trigger_data={"topic": "testing"}
    )

    # Verify
    assert execution.status == "completed"
    assert len(execution.node_results) == 3

    ai_result = execution.node_results[1]
    assert ai_result.success
    assert "text" in ai_result.outputs
    assert len(ai_result.outputs["text"]) > 0

    # Verify usage was logged
    ai_storage = AIStorage()
    usage_records = await ai_storage.get_usage_stats(
        start_date=date.today(),
        end_date=date.today()
    )
    assert usage_records["total_calls"] >= 1
```

#### 4. UI Tests - AI Hub (`tests/e2e/test_ai_hub.py`)

**Setup Wizard Tests** (10 tests):
```python
class TestSetupWizard:
    def test_wizard_appears_on_first_launch(self, page)
    def test_select_providers_step(self, page)
    def test_configure_openai_step(self, page)
    def test_api_key_validation_success(self, page)
    def test_api_key_validation_failure(self, page)
    def test_local_model_system_check(self, page)
    def test_model_download_step(self, page)
    def test_skip_download_option(self, page)
    def test_wizard_summary_screen(self, page)
    def test_wizard_completion(self, page)
```

**Provider Management Tests** (8 tests):
```python
class TestProviderManagement:
    def test_provider_cards_display(self, page)
    def test_enable_disable_provider(self, page)
    def test_configure_provider_modal(self, page)
    def test_change_api_key(self, page)
    def test_update_provider_priority(self, page)
    def test_provider_status_indicators(self, page)
    def test_provider_advanced_settings(self, page)
    def test_delete_provider_config(self, page)
```

**Model Library Tests** (6 tests):
```python
class TestModelLibrary:
    def test_recommended_models_display(self, page)
    def test_model_card_details(self, page)
    def test_download_model_button(self, page)
    def test_search_huggingface(self, page)
    def test_filter_by_size(self, page)
    def test_cancel_download(self, page)
```

**Usage Dashboard Tests** (8 tests):
```python
class TestUsageDashboard:
    def test_metrics_cards_display(self, page)
    def test_cost_chart_renders(self, page)
    def test_provider_breakdown_table(self, page)
    def test_workflow_breakdown(self, page)
    def test_budget_settings_update(self, page)
    def test_budget_alert_triggers(self, page)
    def test_export_csv(self, page)
    def test_date_range_filter(self, page)
```

### Test Fixtures

**Mock Data** (`tests/fixtures/ai_responses.py`):
```python
# OpenAI mock response
MOCK_OPENAI_RESPONSE = {
    "id": "chatcmpl-123",
    "object": "chat.completion",
    "created": 1677652288,
    "model": "gpt-4",
    "choices": [{
        "index": 0,
        "message": {
            "role": "assistant",
            "content": "This is a mocked response from GPT-4."
        },
        "finish_reason": "stop"
    }],
    "usage": {
        "prompt_tokens": 10,
        "completion_tokens": 8,
        "total_tokens": 18
    }
}

# Anthropic mock response
MOCK_ANTHROPIC_RESPONSE = {
    "id": "msg_123",
    "type": "message",
    "role": "assistant",
    "content": [{
        "type": "text",
        "text": "This is a mocked response from Claude."
    }],
    "model": "claude-3-opus-20240229",
    "stop_reason": "end_turn",
    "usage": {
        "input_tokens": 10,
        "output_tokens": 7
    }
}

# Local model mock response
MOCK_LOCAL_RESPONSE = {
    "choices": [{
        "text": "This is a mocked response from local model.",
        "finish_reason": "stop"
    }],
    "usage": {
        "prompt_tokens": 10,
        "completion_tokens": 7,
        "total_tokens": 17
    }
}
```

### CI/CD Integration

**GitHub Actions Workflow**:
```yaml
name: AI Tests

on: [push, pull_request]

jobs:
  test-ai:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -e ".[dev,ai]"

      - name: Run AI unit tests
        run: |
          pytest tests/unit/test_ai_core.py -v
          pytest tests/unit/test_ai_providers.py -v

      - name: Run AI integration tests
        run: |
          pytest tests/integration/test_ai_nodes.py -v

      - name: Run E2E tests
        run: |
          pytest tests/e2e/test_ai_hub.py -v

      - name: Generate coverage report
        run: |
          pytest --cov=src/ai --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

**Test Isolation**:
- All tests use mocked API responses
- No actual API calls to OpenAI/Anthropic
- No API keys required in CI
- Local provider tests skip if llama.cpp unavailable
- Fast execution (< 2 minutes for full suite)

---

## Implementation Plan

### Sprint Structure

**Total Estimated Tasks**: 25-30 tasks across 3 sprints
**Development Approach**: Subagent-Driven Development (same as Phase 3)

### Sprint 1: AI Core Testing & Foundation (8-10 tasks)

**Goal**: Make existing AI infrastructure production-ready through comprehensive testing and data persistence.

**Task 1: Database Migrations**
- Create 4 new tables: `ai_providers`, `ai_usage`, `local_models`, `ai_budgets`
- Write migration script with rollback support
- Test migration on fresh and existing databases
- Commit: `feat(ai): add database schema for AI persistence`

**Task 2: AIStorage Service**
- Implement `AIStorage` class with all CRUD methods
- Provider config management (save/load/update/delete)
- Usage logging and aggregation
- Model management operations
- Budget settings persistence
- Unit tests for all methods
- Commit: `feat(ai): implement AIStorage service`

**Task 3: API Key Security**
- Integrate `keyring` library
- Implement secure key storage/retrieval
- Migration from any existing plaintext keys
- Test on Windows/Mac/Linux
- Commit: `feat(ai): secure API key storage with keyring`

**Task 4: AIGateway Unit Tests**
- 20 tests covering gateway functionality
- Provider registration, priority, fallback
- Response caching tests
- Usage logging verification
- Commit: `test(ai): add comprehensive AIGateway tests`

**Task 5: Provider Unit Tests**
- 40 tests (8 per provider × 5 providers)
- Mock all external API calls
- Test error handling, timeouts, retries
- Streaming support tests
- Commit: `test(ai): add provider unit tests with mocking`

**Task 6: AI Node Integration Tests**
- 30 tests (6 per node × 5 nodes)
- End-to-end workflow execution
- Variable substitution tests
- Provider fallback tests
- Commit: `test(ai): add AI node integration tests`

**Task 7: Update Dependencies**
- Move AI dependencies from `[project.optional-dependencies].ai` to core `dependencies`
- Update installation docs
- Test fresh install
- Commit: `build: move AI dependencies to core`

**Task 8: Cost Calculator Service**
- Implement cost calculation per provider
- Pricing tables for OpenAI models
- Pricing tables for Anthropic models
- Local models = $0.00
- Unit tests for accuracy
- Commit: `feat(ai): implement cost calculation service`

**Task 9: Provider Health Monitoring**
- Implement `ProviderHealth` service
- Availability checking
- Latency tracking
- Error rate monitoring
- Auto-disable on failures
- Commit: `feat(ai): add provider health monitoring`

**Task 10: Usage Logging Integration**
- Update existing AI nodes to log usage
- Automatic cost calculation on each call
- Test usage appears in database
- Commit: `feat(ai): integrate usage logging in AI nodes`

**Sprint 1 Success Criteria**:
- ✅ 90+ tests passing
- ✅ All AI code has 90%+ coverage
- ✅ Database migrations work
- ✅ API keys stored securely
- ✅ Usage logged correctly

### Sprint 2: AI Hub UI & Model Management (10-12 tasks)

**Goal**: Build complete AI Hub interface for provider and model management.

**Task 1: AIHubView Structure**
- Create `AIHubView` with 3-tab layout
- Setup Wizard tab skeleton
- My Providers tab skeleton
- Model Library tab skeleton
- Navigation between tabs
- Commit: `feat(ai-ui): create AI Hub view structure`

**Task 2: Setup Wizard - Step 1 & 2**
- Provider selection checkboxes
- Provider configuration forms
- API key input with show/hide
- Test Connection button
- Success/error feedback
- Commit: `feat(ai-ui): implement wizard steps 1-2`

**Task 3: Setup Wizard - Step 3 & 4**
- Recommended model card
- Download button with mock download
- Summary screen
- Completion and activation
- Commit: `feat(ai-ui): implement wizard steps 3-4`

**Task 4: My Providers Management**
- Provider card grid layout
- Status indicators (Active/Configured/Not Set Up)
- Quick stats display
- Enable/disable toggle
- Commit: `feat(ai-ui): build My Providers view`

**Task 5: Provider Configuration Modal**
- Modal dialog for each provider
- Basic settings (API key, model)
- Advanced settings (expandable)
- Priority ordering
- Save/cancel buttons
- Commit: `feat(ai-ui): add provider configuration modals`

**Task 6: Model Library - Recommended Tab**
- Grid of 10 curated model cards
- Model details (size, purpose, rating)
- System requirements checking
- Download button
- Installed badge
- Commit: `feat(ai-ui): build recommended models tab`

**Task 7: Model Library - Browse Tab**
- Hugging Face API integration
- Search input and filters
- Size slider
- Quantization dropdown
- Results display
- Commit: `feat(ai-ui): add Hugging Face browse tab`

**Task 8: Model Download Manager**
- Download progress overlay
- Speed and ETA display
- Pause/cancel buttons
- Background download support
- Completion notification
- Commit: `feat(ai-ui): implement model download manager`

**Task 9: System Requirements Detection**
- Detect available RAM
- Check for CUDA/GPU
- Warn on insufficient resources
- Model recommendations based on system
- Commit: `feat(ai): add system requirements detection`

**Task 10: ModelHub Service**
- `ModelHub` class implementation
- Download GGUF from Hugging Face
- Verify file integrity
- Track downloads in database
- Delete model files
- Commit: `feat(ai): implement ModelHub service`

**Task 11: AI Nodes in Palette**
- Add "AI" category to node palette
- Register 5 AI nodes
- Custom icons for AI nodes
- Violet color theme (#8B5CF6)
- Drag-and-drop to canvas
- Commit: `feat(ai-ui): add AI nodes to palette`

**Task 12: Provider Status Bar**
- Status bar component showing active providers
- Click to open AI Hub
- Alert badges for errors
- Quick toggle providers
- Commit: `feat(ai-ui): add provider status bar`

**Task 13: E2E Tests for AI Hub**
- 32 tests covering all UI interactions
- Wizard flow tests
- Provider management tests
- Model library tests
- Mock all downloads
- Commit: `test(ai-ui): add E2E tests for AI Hub`

**Sprint 2 Success Criteria**:
- ✅ Setup wizard completable end-to-end
- ✅ All providers configurable via UI
- ✅ Model download UI functional (mocked)
- ✅ AI nodes visible in palette
- ✅ 32 E2E tests passing

### Sprint 3: Usage Dashboard & Polish (7-8 tasks)

**Goal**: Complete cost tracking, analytics, and final polish.

**Task 1: Usage Dashboard View**
- Create `UsageDashboardView`
- 4 metrics cards (cost, calls, tokens, budget)
- Layout and styling
- Commit: `feat(ai-ui): create usage dashboard view`

**Task 2: Time-Series Cost Chart**
- Integrate charting library (Chart.js)
- Stacked area chart implementation
- Time range selectors (7d, 30d, 3m)
- Interactive tooltips
- Provider color coding
- Commit: `feat(ai-ui): add cost over time chart`

**Task 3: Provider Breakdown Table**
- Table with provider stats
- Sorting by columns
- Visual cost bars
- Click for detailed view
- Commit: `feat(ai-ui): add provider breakdown table`

**Task 4: Workflow Cost Breakdown**
- Top workflows by cost
- Expandable detail views
- Per-workflow AI node costs
- Most expensive run stats
- Commit: `feat(ai-ui): add workflow cost breakdown`

**Task 5: Budget Management**
- Budget settings panel
- Monthly limit input
- Alert threshold slider
- Email notification toggle
- Save settings
- Commit: `feat(ai-ui): implement budget management`

**Task 6: CSV Export**
- Export usage data to CSV
- Date range selector
- Configurable columns
- Download trigger
- Commit: `feat(ai): add CSV export functionality`

**Task 7: Budget Alert System**
- Monitor budget usage
- Trigger alerts at threshold
- In-app notifications
- Email notifications (optional)
- Commit: `feat(ai): implement budget alerts`

**Task 8: End-to-End Integration Test**
- Complete workflow: Setup → Use AI → Track Cost
- Verify all components work together
- Multi-provider fallback test
- Cost accuracy validation
- Commit: `test(ai): add full integration test`

**Task 9: Performance Testing**
- Test with 1000+ usage records
- Chart rendering performance
- Database query optimization
- Pagination if needed
- Commit: `perf(ai): optimize for large usage datasets`

**Task 10: Documentation Updates**
- Update `AI_PROVIDERS.md`
- Add Phase 4 to `CHANGELOG.md`
- User guide for AI Hub
- Cost management guide
- Commit: `docs: update for Phase 4 AI integration`

**Sprint 3 Success Criteria**:
- ✅ Dashboard displays accurate costs
- ✅ Charts render correctly
- ✅ Budget alerts trigger at threshold
- ✅ CSV export works
- ✅ Performance acceptable with 1000+ records
- ✅ All 110+ tests passing
- ✅ Documentation complete

---

## Success Criteria (Phase 4 Complete)

### Functional Requirements

- ✅ **Provider Management**: All 5 providers configurable via Setup Wizard
- ✅ **Model Management**: Can download and manage local models
- ✅ **AI Nodes**: All 5 AI nodes visible in palette and usable
- ✅ **Cost Tracking**: Every AI call logged with accurate cost
- ✅ **Budget Alerts**: Alerts trigger at configured threshold
- ✅ **Security**: API keys stored in system keyring, never in database
- ✅ **Export**: Can export usage data to CSV

### Testing Requirements

- ✅ **Test Coverage**: 90%+ coverage for all AI code
- ✅ **Test Count**: 110+ tests passing
- ✅ **CI/CD**: All tests run on every PR
- ✅ **No External Calls**: All API calls mocked in tests

### Performance Requirements

- ✅ **Dashboard Load**: < 1s with 1000 usage records
- ✅ **Chart Render**: < 500ms
- ✅ **Model Download**: Progress updates every second
- ✅ **Cost Calculation**: Real-time (< 10ms per calculation)

### User Experience Requirements

- ✅ **Setup Time**: Complete wizard in < 5 minutes
- ✅ **Error Messages**: Clear, actionable error messages
- ✅ **Help Text**: Tooltips and descriptions throughout
- ✅ **Responsive**: UI works on different screen sizes

---

## Technical Decisions

### AI Dependencies

**Decision**: Move AI libraries from optional to core dependencies.

**Rationale**:
- AI is now a first-class feature, not experimental
- Simplifies installation (one command: `pip install skynette`)
- All users get AI capabilities out of the box
- Optional was causing confusion ("Why can't I use AI nodes?")

**Impact**:
- Larger package size (~500MB with llama-cpp-python)
- Longer installation time
- But: Better user experience, fewer support issues

**Alternatives Considered**:
- Keep optional: Too confusing, fragmented experience
- Separate package: Too complex for users to manage

### Cost Calculation Approach

**Decision**: Calculate and store cost in USD at time of API call.

**Rationale**:
- Historical costs remain accurate even if pricing changes
- No need to recalculate when viewing old data
- Simpler queries (cost already in database)

**Implementation**:
```python
# At time of AI call:
cost_usd = calculate_cost(
    provider="openai",
    model="gpt-4",
    prompt_tokens=100,
    completion_tokens=50
)

await storage.log_usage(UsageRecord(
    provider="openai",
    model="gpt-4",
    prompt_tokens=100,
    completion_tokens=50,
    cost_usd=cost_usd,  # Stored immediately
    timestamp=datetime.utcnow()
))
```

**Pricing Table** (hardcoded, can be updated):
```python
PRICING = {
    "openai": {
        "gpt-4": {
            "prompt": 0.03 / 1000,      # $0.03 per 1K tokens
            "completion": 0.06 / 1000    # $0.06 per 1K tokens
        },
        "gpt-4-turbo": {
            "prompt": 0.01 / 1000,
            "completion": 0.03 / 1000
        },
        "gpt-3.5-turbo": {
            "prompt": 0.0015 / 1000,
            "completion": 0.002 / 1000
        }
    },
    "anthropic": {
        "claude-3-opus": {
            "input": 0.015 / 1000,
            "output": 0.075 / 1000
        },
        "claude-3-sonnet": {
            "input": 0.003 / 1000,
            "output": 0.015 / 1000
        },
        "claude-3-haiku": {
            "input": 0.00025 / 1000,
            "output": 0.00125 / 1000
        }
    },
    "local": {
        "*": {
            "input": 0.0,
            "output": 0.0
        }
    }
}
```

### Model Storage Location

**Decision**: Store downloaded models in `~/.skynette/models/`

**Rationale**:
- User directory, not system directory (no admin required)
- Separate from Skynette database
- Easy to back up or delete
- Cross-platform (`Path.home()` works everywhere)

**Structure**:
```
~/.skynette/
├── skynette.db          # Main database
├── models/              # Downloaded models
│   ├── mistral-7b-instruct-v0.2.Q4_K_M.gguf
│   ├── llama-2-7b-chat.Q4_K_M.gguf
│   └── codellama-7b.Q8_0.gguf
└── logs/
```

**Database tracks models**:
```python
LocalModel(
    id="model_123",
    name="Mistral 7B Instruct",
    file_path=Path("~/.skynette/models/mistral-7b-instruct-v0.2.Q4_K_M.gguf"),
    size_bytes=4100000000,
    quantization="Q4_K_M",
    source="recommended"
)
```

### Hugging Face Integration

**Decision**: Use Hugging Face Hub API for model browsing and downloading.

**Library**: `huggingface-hub>=0.20.0` (already in dependencies)

**Implementation**:
```python
from huggingface_hub import hf_hub_download, list_models

# Search models
def search_models(query: str, filters: dict) -> list[dict]:
    models = list_models(
        filter="gguf",
        search=query,
        limit=50
    )
    return [
        {
            "id": model.id,
            "name": model.id.split("/")[1],
            "downloads": model.downloads,
            "likes": model.likes,
            "tags": model.tags
        }
        for model in models
    ]

# Download model
def download_model(repo_id: str, filename: str) -> Path:
    return hf_hub_download(
        repo_id=repo_id,
        filename=filename,
        cache_dir="~/.skynette/models",
        resume_download=True  # Support pause/resume
    )
```

**Progress Tracking**:
```python
from huggingface_hub import hf_hub_download
from tqdm import tqdm

def download_with_progress(repo_id: str, filename: str, callback):
    with tqdm.wrapattr(
        open(os.devnull, "wb"),
        "write",
        miniters=1,
        desc=filename,
        total=get_file_size(repo_id, filename)
    ) as f:
        hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            cache_dir="~/.skynette/models",
            resume_download=True,
            local_dir_use_symlinks=False
        )
        callback(progress)  # Update UI
```

---

## Migration Strategy

### From v0.3.0 to v0.4.0

**Database Migration**:
```python
# Migration: 0003_add_ai_tables.py
async def upgrade():
    """Add AI tables to existing database."""
    async with aiosqlite.connect(db_path) as db:
        # Create 4 new tables
        await db.execute(CREATE_AI_PROVIDERS_TABLE)
        await db.execute(CREATE_AI_USAGE_TABLE)
        await db.execute(CREATE_LOCAL_MODELS_TABLE)
        await db.execute(CREATE_AI_BUDGETS_TABLE)

        # Create indices
        await db.execute(CREATE_AI_USAGE_INDICES)

        await db.commit()

async def downgrade():
    """Remove AI tables (rollback)."""
    async with aiosqlite.connect(db_path) as db:
        await db.execute("DROP TABLE IF EXISTS ai_providers")
        await db.execute("DROP TABLE IF EXISTS ai_usage")
        await db.execute("DROP TABLE IF EXISTS local_models")
        await db.execute("DROP TABLE IF EXISTS ai_budgets")
        await db.commit()
```

**Existing Workflows**:
- Continue working unchanged
- AI nodes already exist, just not discoverable
- If workflow uses AI node, it will work
- Usage logging starts automatically on v0.4.0

**API Key Migration**:
- Check for any API keys in old config files
- Migrate to system keyring
- Delete from plaintext storage
- Log migration success

```python
async def migrate_api_keys():
    """Migrate API keys from config to keyring."""
    config = load_config("~/.skynette/config.yaml")

    for provider in ["openai", "anthropic"]:
        if provider in config and "api_key" in config[provider]:
            api_key = config[provider]["api_key"]

            # Store in keyring
            keyring.set_password('skynette-ai', provider, api_key)

            # Remove from config
            del config[provider]["api_key"]
            config[provider]["api_key_stored"] = True

    save_config(config, "~/.skynette/config.yaml")
    logger.info("API keys migrated to secure storage")
```

---

## Future Enhancements (Post-Phase 4)

### Phase 5 Candidates

**RAG (Retrieval Augmented Generation)**:
- ChromaDB integration (already in optional deps)
- Document ingestion pipeline
- Semantic search nodes
- Context injection in prompts

**Multi-Agent Workflows**:
- Agent orchestration
- Inter-agent communication
- Shared memory/state
- Parallel agent execution

**Custom Model Fine-Tuning**:
- Fine-tuning interface
- Dataset preparation
- Training job management
- Model versioning

**Advanced AI Nodes**:
- Image generation (DALL-E, Stable Diffusion)
- Image analysis (GPT-4 Vision)
- Audio transcription (Whisper)
- Speech synthesis (TTS)

**Enterprise Features**:
- Team workspaces with separate budgets
- User-level API key management
- Audit logging
- RBAC for AI provider access

---

## Appendices

### A. Curated Model List (10 Models)

1. **Mistral 7B Instruct v0.2**
   - Size: 4.1GB (Q4_K_M)
   - Purpose: General purpose
   - Repo: TheBloke/Mistral-7B-Instruct-v0.2-GGUF
   - Why: Best all-around model, fast, capable

2. **Llama 2 7B Chat**
   - Size: 3.8GB (Q4_K_M)
   - Purpose: Conversational AI
   - Repo: TheBloke/Llama-2-7B-Chat-GGUF
   - Why: Meta's stable chat model, well-tested

3. **Phi-2**
   - Size: 2.7GB (Q4_K_M)
   - Purpose: Small but capable
   - Repo: TheBloke/phi-2-GGUF
   - Why: Runs on low-end hardware, good quality

4. **CodeLlama 7B**
   - Size: 3.5GB (Q4_K_M)
   - Purpose: Code generation
   - Repo: TheBloke/CodeLlama-7B-Instruct-GGUF
   - Why: Best for coding tasks

5. **Mistral 7B OpenOrca**
   - Size: 4.1GB (Q4_K_M)
   - Purpose: Instruction following
   - Repo: TheBloke/Mistral-7B-OpenOrca-GGUF
   - Why: Excellent instruction following

6. **TinyLlama 1.1B**
   - Size: 637MB (Q4_K_M)
   - Purpose: Ultra-light
   - Repo: TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF
   - Why: Runs on 4GB RAM, very fast

7. **Neural Chat 7B v3.3**
   - Size: 4.1GB (Q4_K_M)
   - Purpose: Conversational
   - Repo: TheBloke/neural-chat-7B-v3-3-GGUF
   - Why: Optimized for dialogue

8. **Zephyr 7B Beta**
   - Size: 4.1GB (Q4_K_M)
   - Purpose: High-quality responses
   - Repo: TheBloke/zephyr-7B-beta-GGUF
   - Why: Strong performance, good reasoning

9. **OpenHermes 2.5 Mistral 7B**
   - Size: 4.1GB (Q4_K_M)
   - Purpose: Instruction following
   - Repo: TheBloke/OpenHermes-2.5-Mistral-7B-GGUF
   - Why: Excellent at following complex instructions

10. **Starling 7B Alpha**
    - Size: 4.1GB (Q4_K_M)
    - Purpose: Strong reasoning
    - Repo: TheBloke/Starling-LM-7B-alpha-GGUF
    - Why: Good at complex reasoning tasks

### B. Provider Pricing (January 2026)

**OpenAI**:
| Model | Input (per 1M tokens) | Output (per 1M tokens) |
|-------|----------------------|------------------------|
| GPT-4 | $30 | $60 |
| GPT-4 Turbo | $10 | $30 |
| GPT-3.5 Turbo | $1.50 | $2.00 |

**Anthropic**:
| Model | Input (per 1M tokens) | Output (per 1M tokens) |
|-------|----------------------|------------------------|
| Claude 3 Opus | $15 | $75 |
| Claude 3 Sonnet | $3 | $15 |
| Claude 3 Haiku | $0.25 | $1.25 |

**Local Models**: FREE (electricity costs only)

### C. System Requirements

**Minimum** (for UI only, no local models):
- RAM: 4GB
- Storage: 2GB
- OS: Windows 10+, macOS 10.15+, Ubuntu 20.04+

**Recommended** (for local 7B models):
- RAM: 16GB
- Storage: 50GB (for multiple models)
- CPU: Modern multi-core (Intel i5/AMD Ryzen 5+)
- GPU: Optional (NVIDIA with CUDA for 3x speed)

**Model Size Guide**:
- 1B models: 4GB RAM minimum
- 7B models (Q4): 8GB RAM minimum
- 7B models (Q8): 12GB RAM minimum
- 13B models: 16GB RAM minimum

---

## Conclusion

Phase 4 transforms Skynette's AI capabilities from experimental code into a production-ready, user-friendly system. By focusing on testing, UI polish, and cost transparency, we create a trustworthy AI integration that users can rely on.

**Key Achievements**:
- 110+ tests ensure reliability
- Guided wizard makes setup painless
- Cost tracking prevents bill shock
- Secure key storage protects credentials
- Local models offer free alternative

**Next Steps**:
1. Review and approve this design
2. Create git worktree for Phase 4
3. Write detailed implementation plan
4. Execute via Subagent-Driven Development

---

**Design Status**: ✅ Complete
**Ready for Implementation**: Yes
**Estimated Completion**: 3 sprints (similar timeline to Phase 3)
