# Requirements: Skynette v3.0

**Defined:** 2026-01-20
**Core Value:** One app to replace separate AI chat clients, model managers, workflow tools, code editors, and AI assistants - accessible to everyone

## v3 Requirements

### Agent Core

- [ ] **AGNT-01**: Agent can decompose complex tasks into executable steps (planning phase)
- [ ] **AGNT-02**: Agent can invoke tools through unified interface (tool calling)
- [ ] **AGNT-03**: Agent provides observability/tracing of execution (what's happening)
- [ ] **AGNT-04**: Agent maintains session memory within task context
- [ ] **AGNT-05**: Agent handles errors gracefully with retry logic
- [ ] **AGNT-06**: Agent shows status indication (thinking spinner, step progress)
- [ ] **AGNT-07**: User can cancel agent execution at any point

### MCP Integration

- [ ] **MCP-01**: Skynette acts as MCP host (connects to MCP servers)
- [ ] **MCP-02**: Support stdio transport for local MCP servers
- [ ] **MCP-03**: Support HTTP/SSE transport for remote MCP servers
- [ ] **MCP-04**: Automatic tool discovery from connected MCP servers
- [ ] **MCP-05**: Server configuration UI for adding/removing MCP servers
- [ ] **MCP-06**: Pre-bundled vetted MCP servers (filesystem, search)
- [ ] **MCP-07**: Security sandboxing for untrusted MCP servers

### Built-in Tools

- [ ] **TOOL-01**: Web search via DuckDuckGo API (no key required)
- [ ] **TOOL-02**: Headless browser for complex web interactions (Playwright + stealth)
- [ ] **TOOL-03**: Filesystem operations (read, write, create, delete)
- [ ] **TOOL-04**: Code execution (extend existing workflow node)
- [ ] **TOOL-05**: GitHub integration (create repos, commit, push)
- [ ] **TOOL-06**: Existing Skynette systems exposed as tools (RAG, workflows, code editor)

### Safety & Control

- [ ] **SAFE-01**: Action classification system (safe, moderate, destructive, critical)
- [ ] **SAFE-02**: Human-in-the-loop approval for flagged actions
- [ ] **SAFE-03**: Comprehensive audit log of all agent actions
- [ ] **SAFE-04**: Kill switch that operates outside agent process
- [ ] **SAFE-05**: Risk-tiered approval batching (reduce approval fatigue)
- [ ] **SAFE-06**: Configurable approval levels per tool type
- [ ] **SAFE-07**: YOLO bypass mode for power users (skip approvals)

### Autonomy Levels

- [ ] **AUTO-01**: L1 Assistant mode (agent suggests, user executes)
- [ ] **AUTO-02**: L2 Collaborator mode (auto-execute safe, ask for risky)
- [ ] **AUTO-03**: L3 Trusted mode (auto-execute moderate, ask for destructive)
- [ ] **AUTO-04**: L4 Expert mode (auto-execute most, ask for critical only)
- [ ] **AUTO-05**: L5 Observer/YOLO mode (fully autonomous with monitoring)

### UI Integration

- [ ] **UI-01**: Agent panel for starting tasks and viewing status
- [ ] **UI-02**: Progress display with thinking indicator and step completion
- [ ] **UI-03**: Approval dialogs with accept/reject/modify options
- [ ] **UI-04**: Plan visualization before execution begins
- [ ] **UI-05**: Step-by-step audit trail visible in UI
- [ ] **UI-06**: Task history with replay capability

### AI Backend

- [ ] **AI-01**: Smart model routing (agent suggests best model per task)
- [ ] **AI-02**: User-configurable model defaults per task type
- [ ] **AI-03**: Agent leverages existing multi-provider gateway

### Quality

- [ ] **QUAL-01**: Unit tests for agent core components
- [ ] **QUAL-02**: Integration tests for MCP server connections
- [ ] **QUAL-03**: Security tests for tool sandboxing
- [ ] **QUAL-04**: E2E tests for critical agent workflows
- [ ] **QUAL-05**: Performance benchmarks for agent execution

## v3+ Requirements (Deferred)

### Advanced Agent

- **ADVN-01**: Multi-agent coordination (agent spawns sub-agents)
- **ADVN-02**: Cross-session memory (remember context between sessions)
- **ADVN-03**: Learning from feedback (improve based on user corrections)

### Platform

- **PLAT-01**: Mobile-optimized agent interface
- **PLAT-02**: Team permission model for shared agents
- **PLAT-03**: Agent marketplace (share/discover agent configurations)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Mobile native apps | Web/desktop first; mobile can access via web |
| Real-time collaboration | Single-user focus for v3; complexity too high |
| Plugin marketplace | SDK exists but marketplace deferred |
| Custom model training | Use pre-trained models only |
| Email integration | Users add via MCP servers |
| Stock market integration | Users add via MCP servers |
| Multi-agent coordination | Complexity, defer to v3.1+ |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| AGNT-01 | Phase 7 | Pending |
| AGNT-02 | Phase 7 | Pending |
| AGNT-03 | Phase 8 | Pending |
| AGNT-04 | Phase 7 | Pending |
| AGNT-05 | Phase 7 | Pending |
| AGNT-06 | Phase 8 | Pending |
| AGNT-07 | Phase 8 | Pending |
| MCP-01 | Phase 9 | Pending |
| MCP-02 | Phase 9 | Pending |
| MCP-03 | Phase 9 | Pending |
| MCP-04 | Phase 9 | Pending |
| MCP-05 | Phase 9 | Pending |
| MCP-06 | Phase 9 | Pending |
| MCP-07 | Phase 9 | Pending |
| TOOL-01 | Phase 10 | Pending |
| TOOL-02 | Phase 10 | Pending |
| TOOL-03 | Phase 10 | Pending |
| TOOL-04 | Phase 10 | Pending |
| TOOL-05 | Phase 10 | Pending |
| TOOL-06 | Phase 10 | Pending |
| SAFE-01 | Phase 11 | Pending |
| SAFE-02 | Phase 11 | Pending |
| SAFE-03 | Phase 11 | Pending |
| SAFE-04 | Phase 11 | Pending |
| SAFE-05 | Phase 11 | Pending |
| SAFE-06 | Phase 11 | Pending |
| SAFE-07 | Phase 14 | Pending |
| AUTO-01 | Phase 13 | Pending |
| AUTO-02 | Phase 13 | Pending |
| AUTO-03 | Phase 13 | Pending |
| AUTO-04 | Phase 13 | Pending |
| AUTO-05 | Phase 14 | Pending |
| UI-01 | Phase 12 | Pending |
| UI-02 | Phase 12 | Pending |
| UI-03 | Phase 12 | Pending |
| UI-04 | Phase 12 | Pending |
| UI-05 | Phase 12 | Pending |
| UI-06 | Phase 12 | Pending |
| AI-01 | Phase 8 | Pending |
| AI-02 | Phase 8 | Pending |
| AI-03 | Phase 7 | Pending |
| QUAL-01 | Phase 8 | Pending |
| QUAL-02 | Phase 9 | Pending |
| QUAL-03 | Phase 10 | Pending |
| QUAL-04 | Phase 11 | Pending |
| QUAL-05 | Phase 12 | Pending |

**Coverage:**
- v3 requirements: 46 total
- Mapped to phases: 46
- Unmapped: 0

**By Phase:**
| Phase | Count | Requirements |
|-------|-------|--------------|
| Phase 7 | 5 | AGNT-01, AGNT-02, AGNT-04, AGNT-05, AI-03 |
| Phase 8 | 6 | AGNT-03, AGNT-06, AGNT-07, AI-01, AI-02, QUAL-01 |
| Phase 9 | 8 | MCP-01 through MCP-07, QUAL-02 |
| Phase 10 | 7 | TOOL-01 through TOOL-06, QUAL-03 |
| Phase 11 | 7 | SAFE-01 through SAFE-06, QUAL-04 |
| Phase 12 | 7 | UI-01 through UI-06, QUAL-05 |
| Phase 13 | 4 | AUTO-01 through AUTO-04 |
| Phase 14 | 2 | AUTO-05, SAFE-07 |

---
*Requirements defined: 2026-01-20*
*Last updated: 2026-01-20 after roadmap creation*
