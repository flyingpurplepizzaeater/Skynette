# Release Preparation Design

**Date:** 2026-01-16
**Status:** Approved
**Scope:** Cloud removal, marketplace repository, AI model source expansion

---

## Overview

Three changes for release preparation:
1. Remove cloud features placeholder
2. Create official marketplace repository
3. Expand AI model sources for maximum flexibility

---

## 1. Cloud Feature Removal

### Scope
- Delete `src/cloud/` directory entirely
- Remove any imports/references to `src.cloud` throughout codebase
- Remove cloud-related UI elements (if any exist in settings)
- Update documentation that mentions cloud features

### What Stays
- SaaS integration nodes (Google Drive, Dropbox, S3, etc.) - workflow building blocks
- App remains "local-first" as designed

### Files Affected
- `src/cloud/__init__.py` - DELETE
- Any files importing from `src.cloud` - remove imports
- `src/ui/views/settings.py` - check for cloud settings UI

### Risk
Low - cloud features were never implemented, just a placeholder.

---

## 2. Marketplace Repository

### Repository: `skynette-marketplace`

```
skynette-marketplace/
├── README.md                 # Overview, how to submit plugins
├── CONTRIBUTING.md           # Submission guidelines, review criteria
├── registry.json             # Machine-readable plugin index
├── plugins/
│   ├── featured/            # Curated, verified plugins
│   │   └── plugin-name.md   # Details, screenshots, changelog
│   └── community/           # Community-submitted plugins
└── templates/
    └── plugin-submission.md  # Template for PRs
```

### registry.json Schema

```json
{
  "version": "1.0.0",
  "updated": "2026-01-16",
  "featured": [
    {
      "id": "example-plugin",
      "name": "Example Plugin",
      "author": "author-name",
      "description": "What it does",
      "repo": "github.com/author/skynette-plugin-example",
      "version": "1.0.0",
      "tags": ["utility", "integration"],
      "verified": true
    }
  ],
  "community": []
}
```

### App Integration Changes
- Update `src/plugins/manager.py` to fetch `registry.json` from raw GitHub URL
- Featured plugins shown first in marketplace UI
- Add "verified" badge for featured plugins
- Keep existing GitHub/npm search for broader discovery

---

## 3. AI Model Sources

### Architecture

```
src/ai/models/
├── hub.py                    # Refactor to use sources
├── sources/
│   ├── __init__.py          # ModelSource base class
│   ├── huggingface.py       # HF recommended + custom URL + browse
│   ├── ollama.py            # Ollama library integration
│   └── local.py             # Local file import
└── data.py                  # Existing data models
```

### ModelSource Interface

```python
class ModelSource(ABC):
    @abstractmethod
    async def search(self, query: str) -> list[ModelInfo]:
        """Search for models matching query."""
        pass

    @abstractmethod
    async def download(self, model_id: str, progress_callback) -> Path:
        """Download model, return local path."""
        pass

    @abstractmethod
    async def list_available(self) -> list[ModelInfo]:
        """List available/recommended models."""
        pass
```

### ModelInfo Dataclass

```python
@dataclass
class ModelInfo:
    id: str
    name: str
    source: str  # "huggingface" | "ollama" | "local"
    size_bytes: int
    quantization: str | None
    description: str
    download_url: str | None
    local_path: Path | None
    capabilities: list[str]  # ["chat", "code", "embeddings"]
```

### 3.1 Hugging Face Source

**Capabilities:**
1. Recommended models (existing curated list)
2. Custom URL paste (any HF model URL)
3. Browse/search (query HF API)

**API Endpoints:**
```python
# Search
GET https://huggingface.co/api/models?filter=gguf&search={query}

# Model files
GET https://huggingface.co/api/models/{repo_id}/tree/main
```

**UI Flow - Custom URL:**
1. User clicks "Add from URL"
2. Pastes URL like `https://huggingface.co/TheBloke/Llama-2-7B-GGUF`
3. App fetches available GGUF files
4. User selects quantization
5. Download with progress tracking

**UI Flow - Browse:**
1. User clicks "Browse Hugging Face"
2. Search bar + filters (size, quantization, task)
3. Results show model cards
4. Click → details → select file → download

**Validation:**
- Only allow `.gguf` files
- Warn if model >8GB
- Show estimated RAM requirements

### 3.2 Ollama Source

**Integration:** Connect to Ollama service (port 11434)

**API Endpoints:**
```python
# List local models
GET http://localhost:11434/api/tags

# Pull model
POST http://localhost:11434/api/pull {"name": "llama3.2"}

# Generate
POST http://localhost:11434/api/generate
```

**New OllamaProvider** (`src/ai/providers/ollama.py`):
- Extends base provider interface
- Detects if Ollama running
- Lists Ollama library models
- Handles streaming responses

**UI Flow:**
1. "Ollama" tab in Model Library
2. If not detected → show install guide
3. If running → show library (llama3.2, mistral, codellama...)
4. One-click pull
5. Pulled models appear in "My Models"

### 3.3 Local File Import

**Use Cases:**
- User has GGUF files already
- Models from LM Studio, GPT4All, etc.
- Air-gapped environments

**Import Flow:**
1. User clicks "Import Local Model"
2. File picker (filter: `*.gguf`)
3. Select file(s)
4. Copy/move to `~/.skynette/models/`
5. Auto-detect metadata from filename

**Metadata Detection:**
```python
# "llama-3.2-3b-instruct-q4_k_m.gguf"
# → model_name="llama-3.2-3b-instruct", quantization="Q4_K_M"
```

**File Handling Options:**
- Copy - Keep original, copy to models folder
- Move - Move to models folder (saves space)
- Link - Symlink to original (advanced)

**Validation:**
- Verify valid GGUF (check magic bytes)
- Warn if corrupted
- Show size and RAM requirements

---

## 4. UI Changes

### Model Library Tab Restructure

```
┌─────────────────────────────────────────────────┐
│  Model Library                                  │
├─────────────────────────────────────────────────┤
│  [My Models] [Hugging Face] [Ollama] [Import]   │
├─────────────────────────────────────────────────┤
│  My Models:                                     │
│  ├─ Llama 3.2 3B (Q4_K_M) - 2.1 GB    [Delete] │
│  └─ Mistral 7B (Q5_K_M) - 4.8 GB      [Delete] │
│                                                 │
│  Hugging Face tab:                              │
│  ├─ Recommended models (current behavior)       │
│  ├─ [Search Hugging Face] button                │
│  └─ [Add from URL] button                       │
│                                                 │
│  Ollama tab:                                    │
│  ├─ Status: Running / Not detected              │
│  ├─ Available: llama3.2, mistral, codellama...  │
│  └─ [Pull] buttons                              │
│                                                 │
│  Import tab:                                    │
│  └─ [Import Local GGUF File] button             │
└─────────────────────────────────────────────────┘
```

### Provider Priority
- Ollama models available → add OllamaProvider
- Local GGUF → LocalProvider (existing)
- Cloud providers unchanged

---

## Implementation Order

1. **Cloud removal** - Quick cleanup task
2. **Model source abstraction** - Refactor hub.py architecture
3. **Hugging Face enhancements** - URL paste, browse
4. **Ollama integration** - Provider + UI
5. **Local import** - File picker + validation
6. **Marketplace repo** - Create external repo, update app

---

## Files to Create/Modify

### New Files
- `src/ai/models/sources/__init__.py`
- `src/ai/models/sources/huggingface.py`
- `src/ai/models/sources/ollama.py`
- `src/ai/models/sources/local.py`
- `src/ai/providers/ollama.py`

### Modified Files
- `src/ai/models/hub.py` - Refactor to use sources
- `src/ai/models/data.py` - Add ModelInfo
- `src/plugins/manager.py` - Fetch registry.json
- `src/ui/views/ai_hub.py` - New tabs, UI flows
- `src/ui/views/plugins.py` - Verified badge

### Deleted Files
- `src/cloud/__init__.py` (entire directory)
