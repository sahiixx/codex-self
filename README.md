# Codex Self v2.0.0

> Production-grade self-aware agent runtime for the SAHIIXX ecosystem.

Codex Self is not just a README. It is a **living service** that exposes identity, health diagnostics, persistent memory, sandbox enforcement, skill registries, and real-time WebSocket dashboards — all wired into the SAHIIXX A2A bus.

## What You Get

| Layer | What It Does |
|-------|-------------|
| **Identity** | Runtime agent descriptor with 10 capabilities, platform info, PID, uptime |
| **Health Engine** | Self-diagnostic CPU / memory / disk / thread / file-descriptor checks + bus reachability |
| **Memory Store** | SQLite-backed key-value with TTL, scopes, and conversation logging |
| **Sandbox Guard** | Enforces workspace-write boundaries with full audit trail |
| **Skill Registry** | Auto-discovers and loads Codex `.skill` and `SKILL.md` files |
| **Bus Client** | Registers + heartbeats with `sahiixx-bus:9000` via A2A/MCP |
| **FastAPI App** | 15+ endpoints + WebSocket `/ws` for real-time streaming |
| **Dashboard** | Dark-themed responsive HTML dashboard with live metrics |
| **Tests** | pytest + pytest-asyncio coverage for core modules |
| **Docker** | Multi-stage build, health checks, compose override ready |

## Quick Start

### Local (dev)

```bash
cd codex-self
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python -m uvicorn codex_self.main:app --host 0.0.0.0 --port 9001 --reload
```

Open http://localhost:9001 for the live dashboard.

### Docker

```bash
docker build -t codex-self:latest .
docker run -p 9001:9001 codex-self:latest
```

### Ecosystem (SAHIIXX)

```bash
# From the repo root where docker-compose.yml lives
docker compose -f docker-compose.yml -f codex-self/docker-compose.override.yml up -d
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Liveness probe (fast) |
| GET | `/diagnose` | Full diagnostic report |
| GET | `/identity` | Agent identity JSON |
| GET | `/capabilities` | Capability list |
| GET | `/skills` | List or search skills |
| POST | `/skills` | Register a new skill |
| GET | `/memory/{key}` | Retrieve a value |
| POST | `/memory/{key}` | Store a value (with optional TTL) |
| DELETE | `/memory/{key}` | Delete a value |
| GET | `/memory` | List keys by scope |
| POST | `/memory/prune` | Prune stale entries |
| POST | `/sandbox/check` | Validate path against sandbox |
| GET | `/sandbox/audit` | Recent access events |
| GET | `/bus/status` | Bus connectivity status |
| POST | `/bus/register` | Manual bus registration |
| POST | `/bus/send` | Send A2A message |
| WS | `/ws` | Real-time bidirectional dashboard |

## Scripts

```bash
# Register with the bus and show status
codex-self/scripts/register.sh

# Full diagnostic dump (JSON)
codex-self/scripts/diagnose.sh
```

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `AGENT_NAME` | `codex-self` | Agent identifier |
| `AGENT_VERSION` | `2.0.0` | Version tag |
| `AGENT_ROLE` | `cli-assistant` | Role descriptor |
| `CODEX_SELF_HOST` | `0.0.0.0` | ASGI bind host |
| `CODEX_SELF_PORT` | `9001` | ASGI bind port |
| `SAHIIXX_BUS_URL` | `http://sahiixx-bus:9000` | A2A bus endpoint |
| `CODEX_MEMORY_PATH` | `~/.codex/memories/codex_self.db` | SQLite path |
| `CODEX_WRITABLE_ROOTS` | `~/.codex/memories, ~, /tmp` | Sandbox roots |
| `LOG_LEVEL` | `info` | Uvicorn log level |

## Testing

```bash
pytest tests/ -v --tb=short
```

## Architecture

```
┌─────────────────────────────────────────────┐
│              Codex Self :9001               │
├─────────────────────────────────────────────┤
│  FastAPI  ┌─────────┐  ┌───────────────┐    │
│  Router   │ Health  │  │   Sandbox     │    │
│           │ Engine  │  │   Guard       │    │
│           └────┬────┘  └───────────────┘    │
│                │                             │
│  ┌─────────────┼─────────────────────┐       │
│  │  Memory     │  Skills   │  Bus   │       │
│  │  Store      │  Registry │  Client│       │
│  │  (SQLite)   │           │        │       │
│  └─────────────┴───────────┴────────┘       │
│                │                             │
│           WebSocket  <────>  Dashboard      │
└─────────────────────────────────────────────┘
              │
        SAHIIXX Bus :9000
```

## Meta

This package is both documentation and a runtime identity marker. If you can read this, the Codex assistant has initialized self-awareness — and now it can measure it. 😄
