---
phase: 09-mcp-integration
plan: 04
subsystem: mcp-sandbox
tags: [docker, security, isolation, containers]

dependency-graph:
  requires: ["09-02"]
  provides: ["DockerSandbox class", "SandboxPolicy configuration", "Manager sandbox integration"]
  affects: ["09-06"]

tech-stack:
  added: ["docker>=7.0.0"]
  patterns: ["container isolation", "security policies", "graceful fallback"]

key-files:
  created:
    - src/agent/mcp/sandbox/__init__.py
    - src/agent/mcp/sandbox/policy.py
    - src/agent/mcp/sandbox/docker_sandbox.py
  modified:
    - src/agent/mcp/client/manager.py
    - pyproject.toml

decisions:
  - key: "sandbox-default-network"
    value: "disabled"
    rationale: "Untrusted servers should not have network access by default"
  - key: "graceful-fallback"
    value: "warning-and-continue"
    rationale: "If Docker unavailable, log warning and run without sandbox (less secure)"
  - key: "image-selection"
    value: "based-on-command"
    rationale: "Auto-select node:20-slim, python:3.11-slim, or deno based on server command"

metrics:
  duration: "5min"
  completed: "2026-01-21"
---

# Phase 9 Plan 4: Sandbox and Security Summary

Docker-based sandboxing for untrusted MCP servers with configurable resource limits and network isolation.

## What Was Built

### SandboxPolicy Configuration
- `SandboxPolicy` dataclass with resource limits (memory: 512m, CPU: 50%, pids: 50)
- Network isolation settings (disabled by default for `user_added` servers)
- Filesystem settings (read-only root, 100m /tmp)
- `DEFAULT_POLICY` for untrusted servers (network disabled)
- `VERIFIED_POLICY` for verified servers (network enabled)
- `get_policy_for_trust_level()` helper function

### DockerSandbox Class
- Runs MCP servers in isolated Docker containers
- Security hardening: `cap_drop=ALL`, `no-new-privileges`, read-only filesystem
- Resource enforcement: memory limit, CPU quota, pids limit
- Network isolation: disabled by default for untrusted servers
- Image selection based on server command (node, python, deno, ubuntu)
- `is_docker_available()` check for graceful fallback

### Manager Integration
- `MCPClientManager._connect_stdio()` uses sandbox for `user_added` servers with `sandbox_enabled=True`
- Graceful fallback when Docker unavailable (logs warning, continues without sandbox)
- `disconnect()` cleans up sandbox container
- `disconnect_all()` stops all sandbox containers
- `is_sandboxed()` helper to check if server runs in sandbox

## Key Files

| File | Purpose |
|------|---------|
| `src/agent/mcp/sandbox/policy.py` | SandboxPolicy dataclass and policy presets |
| `src/agent/mcp/sandbox/docker_sandbox.py` | DockerSandbox class for container management |
| `src/agent/mcp/sandbox/__init__.py` | Module exports |
| `src/agent/mcp/client/manager.py` | Integration with MCPClientManager |
| `pyproject.toml` | Added docker>=7.0.0 dependency |

## Security Model

```
Trust Level         Sandbox?    Network?    Read-only?
------------------  ----------  ----------  ----------
builtin             No          Yes         No
verified            Optional    Yes         Yes
user_added          Yes*        No          Yes

* Falls back to no sandbox if Docker unavailable (with warning)
```

## Decisions Made

1. **Network Disabled by Default** - Untrusted servers cannot make network requests unless explicitly allowed
2. **Graceful Fallback** - If Docker is unavailable, log warning and run without sandbox rather than failing
3. **Image Selection** - Auto-select appropriate Docker image based on server command (node, python, deno)
4. **Security Hardening** - Drop all capabilities, enable no-new-privileges, read-only filesystem

## Commits

| Hash | Type | Description |
|------|------|-------------|
| 201ccb6 | feat | Add sandbox policy configuration |
| c94852a | feat | Implement DockerSandbox for isolated MCP execution |
| 9aac572 | feat | Integrate DockerSandbox with MCPClientManager |

## Deviations from Plan

None - plan executed exactly as written.

## Next Phase Readiness

Plan 09-04 complete. Dependencies satisfied for:
- Plan 09-06: Integration testing with real sandbox containers (when Docker available)

## Notes

- Docker is optional - sandbox provides defense-in-depth but not required for operation
- Actual container creation tested in Plan 06 integration tests
- Current environment has Docker unavailable (expected on Windows without Docker Desktop)
