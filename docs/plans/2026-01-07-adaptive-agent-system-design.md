# Adaptive Agent/Skill Creation System Design

**Date:** 2026-01-07
**Status:** Approved
**Scope:** Full adaptive system (reactive, proactive, learning-based)

---

## Overview

Enable Skynette to dynamically create new agents and skills when existing options don't adequately cover a task. The system combines three approaches:

1. **Reactive Creation** - Detect when agents fail or produce poor results
2. **Proactive Gap Analysis** - Analyze before execution if agents truly cover the task
3. **Learning-Based Evolution** - Track patterns across sessions and suggest new agents

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ADAPTIVE AGENT SYSTEM                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐    │
│  │   REACTIVE   │   │  PROACTIVE   │   │   LEARNING   │    │
│  │   DETECTOR   │   │   ANALYZER   │   │   TRACKER    │    │
│  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘    │
│         │                  │                  │             │
│         └──────────────────┼──────────────────┘             │
│                            ▼                                │
│                   ┌────────────────┐                        │
│                   │ AGENT/SKILL    │                        │
│                   │ GENERATOR      │                        │
│                   └────────────────┘                        │
│                            │                                │
│                            ▼                                │
│                   ┌────────────────┐                        │
│                   │ REGISTRY       │                        │
│                   │ UPDATER        │                        │
│                   └────────────────┘                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## File Locations & Scope

```
~/.claude/                              # USER-LEVEL (personal)
├── agents/
│   ├── adaptive-creator.md             # Creates new agents/skills
│   ├── gap-analyzer.md                 # Detects capability gaps
│   └── [dynamically-created-agents]/   # New agents created here
├── skills/
│   └── [dynamically-created-skills]/   # New skills created here
└── settings/
    └── adaptive-learning.json          # Cross-session learning log

.claude/                                # PROJECT-LEVEL (Skynette)
├── agents/
│   └── skynette-orchestrator.md        # Updated to use adaptive system
└── settings.json                       # Add adaptive config
```

### Scope Rules

| What | Where | Why |
|------|-------|-----|
| Adaptive Creator Agent | `~/.claude/agents/` | Works everywhere |
| Gap Analyzer Agent | `~/.claude/agents/` | Works everywhere |
| New domain agents | `~/.claude/agents/` | Available to all projects |
| Learning log | `~/.claude/settings/` | Accumulates across sessions |
| Skynette integration | `.claude/` (project) | Project-specific orchestration |

---

## Gap Detection Logic

### Proactive Gap Detection (Before Execution)

```
User Request Received
        │
        ▼
┌─────────────────────────┐
│ Score each agent 0-100  │
│ against task requirements│
└───────────┬─────────────┘
            │
            ▼
    Best score < 60?  ───No──→ Use existing agent
            │
           Yes
            ▼
┌─────────────────────────┐
│ Can combine agents to   │
│ cover the gap?          │
└───────────┬─────────────┘
            │
           No
            ▼
    CREATE NEW AGENT
```

### Reactive Detection (During/After Execution)

Triggers when:
- Agent produces error or gives up
- Agent explicitly says "I don't have expertise in X"
- Output quality is poor (user rejects, asks to redo)
- Task requires >3 workarounds to complete

### Learning-Based Detection (Cross-Session)

Tracked in `adaptive-learning.json`:
```json
{
  "patterns": [
    {
      "domain": "kubernetes",
      "occurrences": 5,
      "workarounds_used": 3,
      "avg_satisfaction": 0.6,
      "suggested_agent": "kubernetes-expert",
      "status": "pending_creation"
    }
  ]
}
```

When `occurrences >= 3` AND `avg_satisfaction < 0.7` → Suggest/create specialized agent.

---

## Agent/Skill Generation

### Agent Template

```markdown
---
description: |
  [Auto-generated description based on detected gap]
  Specialist in [DOMAIN]. Created by adaptive-creator on [DATE].
  Trigger: [what triggers this agent]
tools: [relevant tools for this domain]
model: [sonnet/opus/haiku based on complexity]
---

# [DOMAIN] Expert Agent

## Expertise
[Generated based on the task that triggered creation]

## When to Use
[Specific scenarios this agent handles]

## Approach
[Domain-specific methodology]

## Integration
Created by Skynette adaptive system.
Source gap: [original task that revealed the gap]
```

### Skill Template

```markdown
---
name: [skill-name]
description: |
  [What this skill does]
  Auto-generated for [DOMAIN] tasks.
---

# [Skill Name]

## Purpose
[Why this skill exists]

## Process
[Step-by-step workflow]

## When to Use
[Trigger conditions]
```

### Generation Process

1. **Analyze the gap** - What's missing? What domain knowledge is needed?
2. **Research the domain** - Use `multi-source-researcher` to gather best practices
3. **Generate content** - Create agent/skill with proper frontmatter
4. **Write to user scope** - Save to `~/.claude/agents/` or `~/.claude/skills/`
5. **Update registry** - Add to Skynette's awareness
6. **Log creation** - Record in `adaptive-learning.json`

---

## Skynette Integration

### Updated Orchestration Flow

```
User Request
     │
     ▼
┌────────────────────┐
│ Skill Check        │ (existing)
└─────────┬──────────┘
          ▼
┌────────────────────┐
│ GAP ANALYZER       │ ◄── NEW
│ - Score all agents │
│ - Check learning   │
│   log for patterns │
└─────────┬──────────┘
          │
    Gap detected?
      │       │
     Yes      No
      │       │
      ▼       ▼
┌──────────┐  │
│ ADAPTIVE │  │
│ CREATOR  │  │
│ - Create │  │
│   agent  │  │
│ - Update │  │
│   registry│ │
└────┬─────┘  │
     │        │
     └────┬───┘
          ▼
┌────────────────────┐
│ Agent Selection    │ (existing, now includes new agents)
└─────────┬──────────┘
          ▼
┌────────────────────┐
│ Execute            │
└─────────┬──────────┘
          ▼
┌────────────────────┐
│ LEARNING TRACKER   │ ◄── NEW
│ - Log success/fail │
│ - Update patterns  │
└────────────────────┘
```

### Configuration

```json
{
  "adaptive": {
    "enabled": true,
    "autoCreate": true,
    "creationThreshold": 60,
    "learningEnabled": true,
    "minOccurrencesForSuggestion": 3,
    "defaultScope": "user",
    "requireApproval": false
  }
}
```

### Approval Modes

| Mode | Behavior |
|------|----------|
| `requireApproval: false` | Creates agents automatically, notifies user |
| `requireApproval: true` | Asks user before creating new agent |
| `requireApproval: "skills-only"` | Auto-create agents, ask for skills |

---

## Implementation Files

1. `~/.claude/agents/adaptive-creator.md` - Agent that generates new agents/skills
2. `~/.claude/agents/gap-analyzer.md` - Detects capability gaps
3. `~/.claude/settings/adaptive-learning.json` - Learning log structure
4. Update `.claude/agents/skynette-orchestrator.md` - Integrate adaptive flow
5. Update `.claude/settings.json` - Add adaptive config
