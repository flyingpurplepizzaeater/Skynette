# Research Summary - Skynette v3.0 Agent

**Project:** Skynette v3.0 Agent Mode
**Synthesized:** 2026-01-20
**Overall Confidence:** HIGH

---

## Executive Summary

Skynette v3.0 adds autonomous agent capabilities to an existing AI workspace. Research across stack, features, architecture, and pitfalls reveals a clear path: **build a custom Plan-and-Execute agent loop leveraging Skynette's existing multi-provider AI gateway, integrate with the MCP protocol for extensible tool use, and prioritize safety infrastructure from day one.**

The technology landscape strongly favors a minimal-framework approach. Skynette already has the hard parts (multi-provider routing, async architecture, workflow engine). Adding LangChain or similar frameworks would duplicate this work while adding abstraction layers. The recommended stack uses the official MCP SDK v1.25.0, Playwright/browser-use for web automation, and DuckDuckGo for free web search with optional premium APIs (Tavily, Exa).

The most critical insight from research: **safety is the differentiator**. With 57% of companies deploying agents in production, the gap between "demo" and "trusted tool" is human-in-the-loop approval flows, audit logging, and configurable autonomy levels. Seven critical pitfalls (command injection, tool poisoning, infinite loops, etc.) can cause security breaches or architectural rewrites if not addressed during initial design. The recommended build order addresses safety infrastructure in parallel with features, not as an afterthought.

---

## Key Findings

### From STACK.md

| Technology | Version | Purpose | Confidence |
|------------|---------|---------|------------|
| **mcp** | 1.25.0 | MCP client SDK (tool integration) | HIGH |
| **playwright** | 1.57.0 | Browser automation | HIGH |
| **browser-use** | 0.11.3 | AI-friendly browser control | HIGH |
| **duckduckgo-search** | 8.1.0 | Free web search | HIGH |
| **tavily-python** | latest | AI-optimized search (optional) | MEDIUM |
| **exa-py** | 2.0.2 | Semantic search (optional) | MEDIUM |
| **Custom agent loop** | N/A | Planning/execution | HIGH |

**Dependencies to Add:**
```toml
agent = [
    "mcp[cli]>=1.25.0",
    "playwright>=1.57.0",
    "browser-use>=0.11.3",
    "duckduckgo-search>=8.1.0",
]
```

**Key Decision: Build Custom, Not Framework**

Skynette's existing AI gateway eliminates the need for LangChain/LangGraph/CrewAI. These frameworks would:
- Duplicate provider abstraction already in place
- Add 5+ layers for simple customizations
- Increase latency (LangChain has highest latency in benchmarks)
- Create framework lock-in

### From FEATURES.md

**Table Stakes (Ship Blockers):**
| Feature | Complexity |
|---------|------------|
| MCP tool integration | Medium |
| Basic agent loop (plan-execute-observe) | Medium |
| Observability/tracing | Medium |
| HITL approval flows | Medium |
| Kill switch | Low |
| Audit logging | Medium |
| Risk classification | Medium |

**Differentiators (v3.0 Quality Bar):**
| Feature | Value |
|---------|-------|
| Autonomy levels (L1-L4) | User control over oversight |
| Graduated trust | Permissions expand as trust builds |
| Transparent safety controls | Users see and understand guardrails |
| Cost transparency | Real-time tracking per task |

**Defer to v3.1+:**
- YOLO Mode (L5) - only after safety proven
- Multi-agent coordination - complex, needs design
- Custom tool creation - power user feature
- Cross-session memory - privacy implications

**Anti-Features to Avoid:**
- "Uber agent" design (single agent for everything)
- Auto-execute without preview
- Prompt-based security ("please don't delete files")
- Uncapped autonomy
- Hidden guardrails

### From ARCHITECTURE.md

**Recommended Pattern: Hybrid Plan-and-Execute**

```
User Request
    |
[Planner Agent] -- Large model (Claude/GPT-4)
    |
Execution Plan (visible to user, approval point)
    |
[Executor Loop] -- Can use smaller/cheaper models
    |
    +---> [Tool Call] --> Result --> Update Plan
    +---> [Sub-Agent] --> ReAct for complex sub-tasks
    |
Progress Events --> UI
```

**Why Plan-and-Execute:**
1. Visual progress feedback - users see plan before execution
2. Cost efficiency - plan with large model, execute with smaller
3. Approval workflow - plans can be reviewed/modified
4. Debuggability - matches existing workflow model

**Build Order:**
1. **Phase 1: Core Infrastructure** (2-3 weeks) - Models, events, state, tool registry
2. **Phase 2: Planning/Execution** (2-3 weeks) - Planner, executor, orchestrator
3. **Phase 3: MCP Integration** (2 weeks) - Transport, client, config
4. **Phase 4: UI Integration** (2-3 weeks) - Progress display, approvals, agent panel
5. **Phase 5: Safety/Control** (1-2 weeks) - Classification, audit, kill switch, YOLO

**New Module Structure:**
```
src/agents/
    models.py, events.py, state.py
    planner.py, executor.py, orchestrator.py
    tools/
        registry.py, builtin.py
    mcp/
        transport.py, client.py, config.py
    safety/
        classifier.py, audit.py, controls.py
```

### From PITFALLS.md

**Critical Pitfalls (Cause Security Issues/Rewrites):**

| # | Pitfall | Phase | Prevention |
|---|---------|-------|------------|
| 1 | MCP Command Injection | MCP Integration | Parameterized commands, never shell=True |
| 2 | Tool Poisoning Attacks | MCP Integration | Display/hash tool definitions, alert on changes |
| 3 | OAuth Token Theft via MCP | MCP Integration | Store tokens in keyring, not MCP server |
| 4 | Agent Infinite Loop Drift | Agent Framework | Hard iteration limit (20), timeout (5 min), repetition detection |
| 5 | YOLO Mode Supply Chain Risk | Safety Systems | Isolated environments only, never git push in YOLO |
| 6 | Runaway Token Consumption | Agent Framework | Per-task budgets, circuit breakers |
| 7 | Prompt Injection via Tools | Tool Use | Sanitize results, context boundaries |

**Moderate Pitfalls (Cause Delays/Debt):**

| # | Pitfall | Prevention |
|---|---------|------------|
| 8 | Approval Fatigue | Risk-tier actions, batch similar, remember preferences |
| 9 | Tool Schema Hallucination | Validate all calls against schema, limit tools per context |
| 10 | Browser Detection/Blocking | Stealth plugins, human-like timing |
| 11 | MCP Server Silent Updates | Hash definitions, alert on changes |
| 12 | Browser Session State Loss | Persistent contexts, session serialization |

---

## Implications for Roadmap

### Suggested Phase Structure

Based on dependency analysis and pitfall mapping, here is the recommended phase structure:

#### Phase 1: Agent Core Infrastructure
**Duration:** 2-3 weeks
**Rationale:** Everything else depends on data models, event system, and tool registry

**Delivers:**
- AgentMessage, AgentEvent, AgentPlan data models
- AgentSession state management
- ToolDefinition and ToolRegistry
- Built-in tool wrappers (AI, RAG, code execution, file ops)

**Pitfalls to Address:**
- #6 Token budgets designed into AgentSession from start
- #4 Iteration/timeout limits in model design

**Features from FEATURES.md:**
- Session memory
- Status indication groundwork
- Cancellation support

---

#### Phase 2: Planning and Execution
**Duration:** 2-3 weeks
**Rationale:** Core agent loop before external integrations

**Delivers:**
- AgentPlanner (creates user-visible plans)
- AgentExecutor (runs plans step by step)
- AgentOrchestrator (coordinates planner + executor)
- Async event streaming for progress

**Pitfalls to Address:**
- #4 Infinite loop prevention enforced here
- #6 Token tracking per execution

**Features from FEATURES.md:**
- Task decomposition
- Structured output
- Model selection routing

---

#### Phase 3: MCP Integration
**Duration:** 2 weeks
**Rationale:** Can run in parallel with Phase 2; extends tool registry

**Delivers:**
- MCP transport layer (stdio, HTTP)
- MCPClient for server connections
- MCP server configuration management
- Tool discovery and registration

**Pitfalls to Address:**
- #1 Command injection prevention (parameterized commands)
- #2 Tool poisoning defense (hash definitions, alert on changes)
- #3 Token theft prevention (keyring storage, minimal scopes)
- #11 Silent update detection

**Features from FEATURES.md:**
- Tool invocation via MCP
- MCP server management

---

#### Phase 4: Built-in Tools
**Duration:** 2 weeks
**Rationale:** Depends on tool registry; provides agent capabilities

**Delivers:**
- Web search tool (DuckDuckGo, optional Tavily/Exa)
- Browser automation tool (Playwright, browser-use)
- GitHub operations tool
- Code execution tool (sandboxed)

**Pitfalls to Address:**
- #7 Prompt injection via tool results (sanitization)
- #9 Schema validation for all tools
- #10 Browser detection countermeasures
- #12 Browser session persistence

**Features from FEATURES.md:**
- Web search capability
- Browser automation
- Code execution
- Git operations

---

#### Phase 5: Safety and Approval Systems
**Duration:** 2-3 weeks
**Rationale:** Requires working execution to have actions to approve/audit

**Delivers:**
- Action risk classification (safe/moderate/destructive)
- HITL approval flows with batch support
- Audit logging (immutable, queryable)
- Kill switch implementation
- Cost limits and circuit breakers

**Pitfalls to Address:**
- #5 YOLO mode with proper isolation
- #8 Approval fatigue prevention

**Features from FEATURES.md:**
- HITL approval flows
- Risk classification
- Audit logging
- Kill switches
- Rate limiting

---

#### Phase 6: UI Integration
**Duration:** 2-3 weeks
**Rationale:** Depends on events and approvals existing

**Delivers:**
- AgentPanel view with plan visualization
- Progress display with step indicators
- Approval dialogs (approve/modify/skip/cancel)
- Settings for MCP server management
- Real-time cost tracking display

**Pitfalls to Address:**
- Flet state coordination (existing v2.0 pitfall)

**Features from FEATURES.md:**
- Status indication
- Transparent safety controls
- Cost transparency

---

#### Phase 7: Autonomy Levels
**Duration:** 1-2 weeks
**Rationale:** Refinement layer on top of working approval system

**Delivers:**
- L1-L4 autonomy implementation
- Per-project autonomy settings
- Graduated trust earning
- Trust persistence

**Features from FEATURES.md:**
- Configurable autonomy (L1-L4)
- Graduated permissions

---

#### Phase 8: YOLO Mode (v3.1)
**Duration:** 1 week
**Rationale:** Only after safety infrastructure proven in production

**Delivers:**
- L5 autonomy (observer mode)
- Isolated environment enforcement
- Enhanced audit logging for YOLO
- Clear UI indicators when active

**Pitfalls to Address:**
- #5 Supply chain risks in YOLO

**Features from FEATURES.md:**
- YOLO mode (deferred)

---

### Research Flags

**Phases Needing Deeper Research:**

| Phase | Research Needed | Reason |
|-------|-----------------|--------|
| Phase 3: MCP | `/gsd:research-phase` recommended | MCP security patterns are evolving rapidly; verify latest CVEs and mitigations before implementation |
| Phase 4: Built-in Tools | `/gsd:research-phase` for browser | Browser automation detection changes frequently; verify current stealth patterns |
| Phase 5: Safety | Review existing implementations | Look at Claude Code, Cursor Agent approval patterns for UX guidance |

**Phases with Standard Patterns (Skip Research):**

| Phase | Reason |
|-------|--------|
| Phase 1: Core Infrastructure | Standard data modeling, well-documented patterns |
| Phase 2: Planning/Execution | Plan-and-Execute pattern thoroughly documented |
| Phase 6: UI Integration | Extends existing Flet patterns in Skynette |
| Phase 7: Autonomy Levels | Design decisions documented in FEATURES.md |

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| **Stack** | HIGH | Official docs, PyPI versions verified, clear rationale for custom vs framework |
| **Features** | HIGH | Multiple 2025 industry sources, academic research (arXiv), production frameworks |
| **Architecture** | HIGH | Existing codebase well-documented, agent patterns (Plan-and-Execute) well-established |
| **Pitfalls** | MEDIUM-HIGH | CVEs verified, security research current, but MCP security landscape still evolving |

**Areas of Lower Confidence:**
- Browser detection countermeasures (cat-and-mouse game with anti-bot systems)
- Optimal approval UX (needs user testing)
- Multi-agent patterns (deferred to v3.1, less research conducted)

---

## Gaps to Address During Planning

| Gap | Impact | Resolution |
|-----|--------|------------|
| MCP server sandboxing approach | HIGH | Decide: Docker, VM, or restricted user? |
| Token budget defaults | MEDIUM | Need benchmarks for typical agent tasks |
| Approval UX specifics | MEDIUM | Wireframe approval dialogs before implementation |
| Browser stealth library choice | LOW | Test playwright-stealth vs custom solution |
| Audit log storage format | MEDIUM | SQLite? Separate file? Retention policy? |
| Cost tracking integration | LOW | How does agent cost tracking integrate with existing? |

---

## Sources (Aggregated)

### Official Documentation
- [MCP Python SDK (GitHub)](https://github.com/modelcontextprotocol/python-sdk) - v1.25.0
- [MCP Security Best Practices](https://modelcontextprotocol.io/specification/draft/basic/security_best_practices)
- [Playwright (PyPI)](https://pypi.org/project/playwright/) - v1.57.0
- [Flet Async Apps](https://flet.dev/docs/getting-started/async-apps/)
- [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/)

### Security Research
- [CVE-2025-6514 mcp-remote RCE](https://www.practical-devsecops.com/mcp-security-vulnerabilities/)
- [Red Hat MCP Security Analysis](https://www.redhat.com/en/blog/model-context-protocol-mcp-understanding-security-risks-and-controls)
- [UpGuard YOLO Mode Analysis](https://www.upguard.com/blog/yolo-mode-hidden-risks-in-claude-code-permissions)
- [Palo Alto Unit 42 MCP Vectors](https://unit42.paloaltonetworks.com/model-context-protocol-attack-vectors/)
- [Microsoft MCP Prompt Injection Defense](https://developer.microsoft.com/blog/protecting-against-indirect-injection-attacks-mcp)

### Architecture and Patterns
- [Plan-and-Execute Agents - LangChain Blog](https://www.blog.langchain.com/planning-agents/)
- [LangGraph Plan-and-Execute Tutorial](https://langchain-ai.github.io/langgraph/tutorials/plan-and-execute/plan-and-execute/)
- [Martin Fowler Function Calling](https://martinfowler.com/articles/function-call-LLM.html)
- [LangChain State of Agent Engineering](https://www.langchain.com/state-of-agent-engineering)

### Industry Research
- [Levels of Autonomy for AI Agents (arXiv)](https://arxiv.org/abs/2506.12469)
- [Google Agent Development Kit Safety](https://google.github.io/adk-docs/safety/)
- [Amazon Bedrock Agents HITL](https://aws.amazon.com/blogs/machine-learning/implement-human-in-the-loop-confirmation-with-amazon-bedrock-agents/)
- [Partnership on AI Agent Failure Detection](https://partnershiponai.org/wp-content/uploads/2025/09/agents-real-time-failure-detection.pdf)

---

*Synthesis completed: 2026-01-20*
