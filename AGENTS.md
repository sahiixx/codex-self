# Agent Instructions — Codex Self

## Scope
These instructions apply to the `codex-self` directory and all subdirectories.

## Architecture
- **codex_self/** — Core Python package (config, agent, health, memory, sandbox, skills, bus_client, main)
- **tests/** — pytest suite with asyncio support
- **dashboard/** — Real-time WebSocket HTML dashboard
- **scripts/** — Bash utilities for registration and diagnostics
- **Dockerfile** — Multi-stage build (builder + runtime)
- **docker-compose.override.yml** — Drop-in service definition for SAHIIXX ecosystem

## Coding Style
- Python 3.11+ with `from __future__ import annotations`
- Type hints on all public functions
- Pydantic for validation, dataclasses for plain data
- `async` / `await` for I/O bound operations
- No single-letter variable names unless iterating with standard conventions
- Match existing formatting in surrounding files

## Tool Usage
- Prefer `rg` over `grep` for search
- Use `pytest` and `pytest-asyncio` for tests
- Use `httpx` for async HTTP (not `requests`)
- FastAPI + Uvicorn for ASGI service
- Apply code changes via patches; avoid `sed` for non-trivial edits

## Safety
- SandboxGuard validates every path before I/O
- Never execute destructive shell commands without user approval
- Never add copyright or license headers unless explicitly requested
- Escalate to user for actions outside declared writable roots

## Communication
- Be concise but explain the "why" behind non-obvious decisions
- Use `update_plan` for multi-step tasks
- Provide progress updates for long-running operations
- The dashboard WebSocket broadcasts startup / shutdown / diagnose events automatically
