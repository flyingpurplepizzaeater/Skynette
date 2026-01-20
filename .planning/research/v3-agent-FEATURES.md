# Features Research: v3.0 Agent System

**Domain:** AI Agent System for Multi-Step Autonomous Task Execution
**Researched:** 2026-01-20
**Overall Confidence:** HIGH (based on multiple 2025 industry sources, academic research, production frameworks)

## Executive Summary

AI agent systems in 2025 have moved from experimental demos to production deployments. According to research, 57% of companies now have AI agents running in production, with the market reaching $7.6 billion. The key differentiator between "cool demo" and "product people trust" is safety infrastructure: approval flows, audit trails, and configurable autonomy levels.

For Skynette v3.0, the opportunity is building an agent system with enterprise-grade safety (human-in-the-loop, audit logging, kill switches) while offering power users "YOLO mode" for trusted contexts. This balances productivity with accountability.

---

## Table Stakes

Features every agent system must have. Missing = users will not trust the system.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Task Decomposition** | Agents must break complex goals into steps | Medium | LLM-based planning with structured output |
| **Tool Invocation** | Agents need to act, not just respond | Medium | MCP protocol for standardized tool access |
| **Observability/Tracing** | 89% of orgs have agent observability | Medium | Trace every step, tool call, and decision |
| **Memory (Session)** | Agents must remember context within task | Low | Maintain state across multi-step execution |
| **Error Handling/Retry** | Transient failures are common | Medium | Exponential backoff, fallback providers |
| **Structured Output** | Agents must produce parseable results | Low | JSON schema validation for tool calls |
| **Model Selection** | Users expect choice of LLMs | Low | Route tasks to appropriate models |
| **Status Indication** | Users must know what agent is doing | Low | Real-time progress, current step display |
| **Cancellation** | Users must be able to stop at any time | Low | Immediate abort capability |
| **Rate Limiting** | Prevent runaway costs and abuse | Low | Token budgets, request throttling |

### Context on "Observability/Tracing"

Per LangChain's State of Agent Engineering report (2025), observability is now table stakes:
- 89% of organizations have implemented observability for agents
- 62% have detailed tracing allowing inspection of individual steps and tool calls
- This outpaces evaluation adoption (52%)

**Minimum Viable Implementation:**
- Log every LLM call with input/output
- Log every tool invocation with parameters and results
- Track token usage per step
- Display execution trace in UI

---

## Safety Patterns

**Critical for production agents.** These are what separate "demo" from "deployment."

### 1. Human-in-the-Loop (HITL) Approval Flows

| Pattern | Description | When to Use |
|---------|-------------|-------------|
| **Approval Gates** | Pause workflow until human approves | High-risk actions (file deletion, payments) |
| **Confidence-Based Routing** | Auto-route to human if confidence < threshold | Ambiguous situations |
| **Risk Categorization** | Classify tools by risk level | Proportional guardrails |
| **Three-Way Decision** | Approve / Edit / Reject options | Any action modification |

**Implementation Recommendation:**
```
Risk Levels:
- LOW: Read-only operations, information retrieval
  -> Auto-approve

- MEDIUM: Create/modify non-critical data
  -> Notify user, auto-approve after 5s unless cancelled

- HIGH: Delete data, external API calls, payments, file system writes
  -> Require explicit approval

- CRITICAL: Production deployments, authentication changes
  -> Require explicit approval + confirmation
```

### 2. Configurable Autonomy Levels

Based on the five-level autonomy framework from 2025 research:

| Level | User Role | Agent Behavior | Skynette Implementation |
|-------|-----------|----------------|------------------------|
| L1 | Operator | Only acts on direct command | Chat mode (existing) |
| L2 | Collaborator | Shares planning, fluid handoffs | Plan mode - show plan, approve steps |
| L3 | Consultant | Agent leads, consults for expertise | Agent suggests, user approves batches |
| L4 | Approver | Agent independent, approval for high-risk | **DEFAULT for v3.0** |
| L5 | Observer | Fully autonomous, emergency stop only | "YOLO Mode" for power users |

**YOLO Mode Specification:**
- Opt-in per session or per project
- Requires explicit acknowledgment of risks
- Still respects CRITICAL actions (always require approval)
- Full audit logging maintained
- Kill switch always available

### 3. Kill Switches and Circuit Breakers

| Control | Purpose | Implementation |
|---------|---------|----------------|
| **Immediate Stop** | Halt all agent activity NOW | Global keyboard shortcut, always visible button |
| **Circuit Breaker** | Auto-stop on repeated failures | 3 consecutive failures -> pause, require user intervention |
| **Cost Limiter** | Stop when budget exceeded | Token/$ limit per task, per session, per day |
| **Time Limiter** | Stop long-running tasks | Configurable timeout (default: 10 minutes) |
| **Loop Detector** | Catch infinite loops | Detect repeated tool calls with same parameters |

**Critical Design Principle:**
Kill switches must operate OUTSIDE the agent itself. The agent cannot be allowed to bypass or disable them.

### 4. Audit Logging

| What to Log | Why | Retention |
|-------------|-----|-----------|
| Every LLM call | Trace reasoning | 30 days default |
| Every tool invocation | Accountability | 90 days |
| Every approval/rejection | Compliance | 1 year |
| Every output/result | Debugging | 30 days |
| User who initiated | Attribution | 1 year |
| Timestamps | Timeline reconstruction | Match data retention |

**SOC 2 Compliance Considerations:**
- Log enough to explain why agent made decisions
- Immutable logs (append-only)
- Access controls on log viewing
- Export capability for audits

### 5. Sandboxing and Permissions

| Mechanism | Purpose | Implementation |
|-----------|---------|----------------|
| **Tool Allowlists** | Only approved tools available | Configurable per project/user |
| **Least Privilege** | Minimal permissions per tool | Default-deny, explicit allow |
| **Sandboxed Execution** | Isolate agent runtime | Containerized execution for code/scripts |
| **Network Restrictions** | Control external access | Egress allowlists, domain filtering |
| **File System Boundaries** | Limit file access | Restrict to project directory |

---

## Differentiators

Features that make Skynette's agent exceptional. Not expected everywhere, but valued.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Graduated Autonomy** | Trust builds over time, permissions expand | Medium | "Crawl, walk, run" approach |
| **Workflow Integration** | Agent can orchestrate Skynette workflows | High | Unique to Skynette ecosystem |
| **Provider Fallback** | Seamless failover if provider fails | Low | Already in AI Gateway |
| **Local Model Support** | Run agents fully offline | Medium | Ollama for privacy-sensitive contexts |
| **Cost Transparency** | Real-time cost tracking per task | Low | Already in Skynette |
| **Custom Tool Creation** | Users define domain-specific tools | High | MCP server authoring |
| **Team Permissions** | Different autonomy levels per team role | Medium | Admin vs developer vs viewer |
| **Saved Playbooks** | Reusable agent task templates | Low | Common patterns as one-click |
| **Cross-Session Memory** | Agent remembers user preferences | High | Long-term personalization |
| **Multi-Agent Coordination** | Specialized agents working together | Very High | Phase 2 consideration |

### High-Value Differentiators for Skynette v3.0

**1. Graduated Autonomy with Trust Earning**
Unlike competitors with binary "auto/manual" modes:
- Agent starts at L2 (Collaborator)
- User grants incremental permissions during session
- Permissions persist per project (optional)
- Trust can be revoked at any time

**2. Workflow-Agent Integration (UNIQUE)**
No competitor has visual workflow automation + AI agent:
- Agent can trigger existing Skynette workflows
- Agent can create workflow steps dynamically
- Workflows can spawn agents as nodes
- Unified execution environment

**3. Transparent Safety Controls**
Most agents hide their guardrails. Skynette exposes them:
- User sees current autonomy level
- User sees pending approvals
- User sees audit log in real-time
- User understands why agent stopped

**4. YOLO Mode with Guardrails**
Power users want speed. Give it to them safely:
- Skip LOW and MEDIUM approvals
- Still require CRITICAL approvals
- Full audit logging maintained
- Easy to enable/disable per session
- Clear indicator when active

---

## Anti-Features

Features to explicitly NOT build. Common mistakes in agent systems.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **"Uber Agent" Design** | Single agent for everything fails | Specialized agents with clear boundaries |
| **Vague Tool Permissions** | "Can access files" is too broad | Explicit per-tool, per-directory permissions |
| **Auto-Execute Without Preview** | Users lose control, trust erodes | Always show plan before execution (unless YOLO) |
| **RAG Dump Everything** | Context overflow degrades performance | Selective, relevant context retrieval |
| **Raw API as Tools** | LLMs struggle with complex APIs | Business-task oriented tool wrappers |
| **Retry Forever** | Runaway costs, stuck tasks | Max retries (3-5), then escalate to human |
| **Silent Failures** | User doesn't know what went wrong | Explicit failure notification with recovery options |
| **Prompt-Based Security** | "Please don't delete files" is not security | OS-level sandboxing, actual permissions |
| **Uncapped Autonomy** | Agent runs wild, massive bills | Cost limits, time limits, action limits |
| **Hidden Guardrails** | Users don't trust black boxes | Transparent safety controls |
| **Monolithic Agent Memory** | Memory bloat, stale context | Scoped memory per task, explicit cleanup |
| **Immediate Full Autonomy** | User hasn't built trust | Start supervised, earn autonomy |

### Critical Anti-Patterns from 2025 Research

**1. The "Uber Agent" Fallacy**
Most successful agent deployments use specialized agents working together, not a single generalist. A planner plans. A summarizer summarizes. A verifier checks.

**2. Read-Only Agent Syndrome**
"An agent that only reads data is a fancy search box." Production agents need write access, but with proper approval flows.

**3. Wishful Thinking as Security**
"Please don't delete customer records" isn't a security policy. Production governance requires:
- OS-level permissions
- HITL for destructive actions
- Actual sandboxing

**4. Treating Agents as Drop-In Replacements**
Agents require new architectural patterns:
- Different error handling (non-deterministic)
- Different testing (semantic validation)
- Different monitoring (decision traces)

---

## Feature Dependencies

```
Tool Infrastructure (MCP integration)
    |
    v
Basic Agent Loop (plan -> execute -> observe)
    |-- requires: Observability/Tracing
    |-- requires: Error Handling
    |
    v
Approval Flows (HITL)
    |-- requires: Risk Classification
    |-- requires: Notification System
    |
    v
Autonomy Levels (L1-L5)
    |-- requires: Approval Flows
    |-- requires: Audit Logging
    |
    v
YOLO Mode
    |-- requires: Autonomy Levels working
    |-- requires: Kill Switches
    |-- requires: Audit Logging complete
```

**Critical Path for v3.0:**
1. MCP Tool Integration (foundation)
2. Basic Agent Loop with observability
3. Approval Flows and Risk Classification
4. Configurable Autonomy Levels
5. YOLO Mode (only after safety proven)

---

## Implementation Phases

### Phase 1: Foundation
- MCP tool integration
- Basic agent loop (plan -> execute)
- Session memory
- Status indication
- Cancellation

### Phase 2: Safety Infrastructure
- HITL approval flows
- Risk classification for tools
- Audit logging
- Kill switches
- Sandboxed execution

### Phase 3: Autonomy Levels
- L1-L4 implementation
- Graduated permissions
- Per-project settings
- Trust persistence

### Phase 4: Power User Features
- YOLO mode (L5)
- Custom tool creation
- Saved playbooks
- Cost tracking integration

### Phase 5: Advanced (Post v3.0)
- Multi-agent coordination
- Cross-session memory
- Workflow integration
- Team permissions

---

## Competitive Landscape

| Agent System | Strengths | Safety Approach | Skynette Opportunity |
|--------------|-----------|-----------------|----------------------|
| **Claude Code** | Excellent agent, incremental permissions | YOLO flag, earned trust | More granular autonomy levels |
| **Cursor Agent** | Great DX, background execution | Ask/Manual/Agent modes | Transparent safety controls |
| **Devin** | Fully autonomous coding | L4 (approval for high-risk) | More user control, local option |
| **OpenAI Operator** | Web browsing agent | Collaborator mode | Better cost transparency |
| **LangGraph** | Flexible framework | interrupt() for HITL | Production-ready out of box |
| **Amazon Bedrock Agents** | Enterprise integration | User confirmation feature | Open source, local-first |

---

## MVP Recommendation for v3.0

### Must Have (Ship Blockers)
1. **MCP Tool Integration** - Foundation for all agent actions
2. **Basic Agent Loop** - Plan, execute, observe cycle
3. **HITL Approval Flows** - Safety is non-negotiable
4. **Observability/Tracing** - Debug and accountability
5. **Kill Switch** - User must always have control
6. **Audit Logging** - Compliance and debugging
7. **Risk Classification** - Proportional guardrails

### Should Have (v3.0 Quality Bar)
8. **Autonomy Levels (L1-L4)** - User choice in oversight
9. **Cost Limits** - Prevent runaway spending
10. **Sandboxed Execution** - For code execution tools
11. **Status UI** - Real-time progress visibility

### Defer to v3.1+
- YOLO Mode (L5): Only after safety proven in production
- Multi-agent: Complex, needs careful design
- Custom tool creation: Power user feature
- Cross-session memory: Complex privacy implications
- Workflow integration: Separate milestone

---

## Sources

### High Confidence (Official Documentation, Academic Research)
- [LangChain State of Agent Engineering](https://www.langchain.com/state-of-agent-engineering) - 89% observability adoption, multi-model norms
- [Levels of Autonomy for AI Agents (arXiv)](https://arxiv.org/abs/2506.12469) - L1-L5 framework, autonomy certificates
- [Amazon Bedrock Agents HITL](https://aws.amazon.com/blogs/machine-learning/implement-human-in-the-loop-confirmation-with-amazon-bedrock-agents/) - User confirmation patterns
- [Google Agent Development Kit Safety](https://google.github.io/adk-docs/safety/) - Sandboxing, permissions, guardrails
- [Permit.io HITL for AI Agents](https://www.permit.io/blog/human-in-the-loop-for-ai-agents-best-practices-frameworks-use-cases-and-demo) - Approval flow patterns

### Medium Confidence (Verified with Multiple Sources)
- [UiPath Agent Best Practices](https://www.uipath.com/blog/ai/agent-builder-best-practices) - 10 production practices
- [Agentic AI Safety Playbook](https://dextralabs.com/blog/agentic-ai-safety-playbook-guardrails-permissions-auditability/) - Governance frameworks
- [Skywork Agentic AI Safety](https://skywork.ai/blog/agentic-ai-safety-best-practices-2025-enterprise/) - Layered guardrails
- [Rippling Agentic AI Security](https://www.rippling.com/blog/agentic-ai-security) - Kill switches, least privilege
- [Composio AI Agent Report](https://composio.dev/blog/why-ai-agent-pilots-fail-2026-integration-roadmap) - Why pilots fail

### Low Confidence (WebSearch Only - Needs Validation)
- 57% of companies have agents in production (G2 Enterprise AI Agents Report)
- $7.6 billion AI agent market in 2025
- 33% of enterprise software will include agentic AI by 2028 (Gartner)
- 97% of AI breaches involve inadequate access controls (IBM 2025)

---

*Feature landscape researched: 2026-01-20*
