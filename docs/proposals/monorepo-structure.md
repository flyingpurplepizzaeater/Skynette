# Skynette Monorepo Structure Proposal

## Overview

This document proposes restructuring Skynette into a monorepo architecture, inspired by n8n's proven package-based approach. This would improve modularity, enable independent versioning, and facilitate community contributions.

## Current Structure

```
skynette-repo/
├── src/
│   ├── core/          # Workflow engine, nodes, execution
│   ├── ui/            # Flet-based GUI
│   ├── data/          # Storage, credentials
│   ├── plugins/       # Plugin system
│   └── ai/            # AI chat assistant
├── main.py            # Entry point
└── requirements.txt
```

## Proposed Monorepo Structure

```
skynette/
├── packages/
│   ├── @skynette/core/           # Workflow engine
│   │   ├── src/
│   │   │   ├── workflow/         # Workflow models, execution
│   │   │   ├── expressions/      # Expression parser
│   │   │   └── events/           # Event system
│   │   ├── pyproject.toml
│   │   └── README.md
│   │
│   ├── @skynette/nodes-base/     # Built-in nodes
│   │   ├── src/
│   │   │   ├── triggers/
│   │   │   ├── http/
│   │   │   ├── flow/
│   │   │   ├── data/
│   │   │   └── utility/
│   │   ├── pyproject.toml
│   │   └── README.md
│   │
│   ├── @skynette/nodes-ai/       # AI/LLM nodes
│   │   ├── src/
│   │   │   ├── chat/
│   │   │   ├── summarize/
│   │   │   ├── extract/
│   │   │   └── classify/
│   │   ├── pyproject.toml
│   │   └── README.md
│   │
│   ├── @skynette/nodes-apps/     # App integration nodes
│   │   ├── src/
│   │   │   ├── slack/
│   │   │   ├── discord/
│   │   │   ├── github/
│   │   │   └── ...
│   │   ├── pyproject.toml
│   │   └── README.md
│   │
│   ├── @skynette/gui/            # Desktop GUI (Flet)
│   │   ├── src/
│   │   │   ├── components/
│   │   │   ├── views/
│   │   │   └── app.py
│   │   ├── pyproject.toml
│   │   └── README.md
│   │
│   ├── @skynette/cli/            # Command-line interface
│   │   ├── src/
│   │   │   ├── commands/
│   │   │   └── cli.py
│   │   ├── pyproject.toml
│   │   └── README.md
│   │
│   ├── @skynette/api/            # REST API server
│   │   ├── src/
│   │   │   ├── routes/
│   │   │   └── server.py
│   │   ├── pyproject.toml
│   │   └── README.md
│   │
│   ├── @skynette/webhooks/       # Webhook server
│   │   ├── src/
│   │   │   └── manager.py
│   │   ├── pyproject.toml
│   │   └── README.md
│   │
│   ├── @skynette/credentials/    # Credential vault
│   │   ├── src/
│   │   │   └── vault.py
│   │   ├── pyproject.toml
│   │   └── README.md
│   │
│   ├── @skynette/storage/        # Workflow storage backend
│   │   ├── src/
│   │   │   ├── sqlite/
│   │   │   ├── postgres/
│   │   │   └── base.py
│   │   ├── pyproject.toml
│   │   └── README.md
│   │
│   ├── @skynette/plugin-sdk/     # Plugin development SDK
│   │   ├── src/
│   │   │   ├── decorators.py
│   │   │   └── base.py
│   │   ├── pyproject.toml
│   │   └── README.md
│   │
│   └── @skynette/skynet/         # AI assistant
│       ├── src/
│       │   ├── chat.py
│       │   └── agent.py
│       ├── pyproject.toml
│       └── README.md
│
├── apps/
│   ├── desktop/                   # Desktop app entry point
│   │   ├── main.py
│   │   └── pyproject.toml
│   │
│   └── server/                    # Headless server mode
│       ├── main.py
│       └── pyproject.toml
│
├── tools/
│   ├── build/                     # Build scripts
│   ├── release/                   # Release automation
│   └── dev/                       # Development utilities
│
├── docs/
│   ├── getting-started/
│   ├── api/
│   ├── plugins/
│   └── contributing/
│
├── examples/
│   ├── workflows/
│   └── plugins/
│
├── pyproject.toml                 # Root project config
├── pnpm-workspace.yaml            # Workspace definition
└── README.md
```

## Package Dependencies

```
                    ┌─────────────────┐
                    │  @skynette/core │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ @skynette/      │ │ @skynette/      │ │ @skynette/      │
│ nodes-base      │ │ nodes-ai        │ │ nodes-apps      │
└─────────────────┘ └─────────────────┘ └─────────────────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ @skynette/      │
                    │ plugin-sdk      │
                    └─────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ @skynette/gui   │ │ @skynette/cli   │ │ @skynette/api   │
└─────────────────┘ └─────────────────┘ └─────────────────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ @skynette/      │ │ @skynette/      │ │ @skynette/      │
│ credentials     │ │ storage         │ │ webhooks        │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

## Benefits

### 1. Independent Versioning
Each package can be versioned independently, enabling:
- Faster iteration on individual components
- Easier rollbacks for specific features
- Clearer changelog per component

### 2. Selective Installation
Users can install only what they need:
```bash
# Full desktop experience
pip install skynette[desktop]

# Headless server only
pip install skynette[server]

# CLI only for automation
pip install skynette-cli

# Just the core engine for embedding
pip install skynette-core
```

### 3. Community Contributions
- Clear separation makes it easier to contribute
- Node packages can be maintained by different teams
- Third-party packages can follow the same structure

### 4. Testing Isolation
- Each package has its own test suite
- CI can test packages in parallel
- Easier to maintain high test coverage

### 5. Build Optimization
- Only rebuild changed packages
- Smaller deployment artifacts
- Faster development cycles

## Implementation Phases

### Phase 1: Extract Core (Week 1-2)
1. Create packages/core with workflow engine
2. Extract expression parser
3. Establish package interfaces
4. Set up workspace tooling

### Phase 2: Split Nodes (Week 2-3)
1. Create nodes-base package
2. Create nodes-ai package
3. Create nodes-apps package
4. Update node registry for package discovery

### Phase 3: Frontend Packages (Week 3-4)
1. Extract GUI to standalone package
2. Extract CLI to standalone package
3. Create API server package

### Phase 4: Infrastructure (Week 4-5)
1. Create webhooks package
2. Create credentials package
3. Create storage abstraction package

### Phase 5: SDK & Documentation (Week 5-6)
1. Finalize plugin-sdk package
2. Create comprehensive documentation
3. Add example plugins and workflows

## Workspace Configuration

### pyproject.toml (root)
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "skynette"
version = "2.0.0"
description = "AI-powered workflow automation platform"
dependencies = [
    "skynette-core",
    "skynette-nodes-base",
    "skynette-nodes-ai",
    "skynette-gui",
    "skynette-cli",
]

[project.optional-dependencies]
desktop = ["skynette-gui"]
server = ["skynette-api", "skynette-webhooks"]
all = ["skynette[desktop]", "skynette[server]"]

[tool.hatch.envs.default]
dependencies = [
    "pytest",
    "pytest-asyncio",
    "pytest-cov",
]
```

### Package pyproject.toml Example
```toml
# packages/@skynette/core/pyproject.toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "skynette-core"
version = "2.0.0"
description = "Skynette workflow execution engine"
dependencies = [
    "pydantic>=2.0",
]

[project.entry-points."skynette.packages"]
core = "skynette.core"
```

## Migration Strategy

### Step 1: Create Package Structure
```bash
mkdir -p packages/@skynette/{core,nodes-base,gui,cli}
```

### Step 2: Move Code with Git History
```bash
# Use git filter-branch or git subtree to preserve history
git subtree split -P src/core -b core-package
```

### Step 3: Update Imports
```python
# Before
from src.core.workflow import Workflow

# After
from skynette.core.workflow import Workflow
```

### Step 4: Establish Package Boundaries
- Define clear interfaces between packages
- Document public APIs
- Mark internal APIs as private

## Node Package Structure

Each node should follow this structure:
```
nodes-apps/src/slack/
├── __init__.py          # Exports
├── slack.py             # Main node class
├── auth.py              # OAuth handling
├── actions/             # Sub-actions
│   ├── send_message.py
│   ├── list_channels.py
│   └── upload_file.py
└── tests/
    ├── test_slack.py
    └── fixtures/
```

## Versioning Strategy

Use semantic versioning with coordinated releases:
- **Major**: Breaking changes to core APIs
- **Minor**: New features, new nodes
- **Patch**: Bug fixes

Node packages can have independent minor/patch versions but major versions should align with core.

## Conclusion

This monorepo structure will enable Skynette to scale as a platform while maintaining code quality and enabling community contributions. The phased approach minimizes disruption while delivering incremental value.

### Next Steps

1. [ ] Review and approve this proposal
2. [ ] Set up monorepo tooling (hatch workspaces or similar)
3. [ ] Begin Phase 1: Extract Core
4. [ ] Create migration scripts for existing installations
5. [ ] Update documentation and contributing guides
