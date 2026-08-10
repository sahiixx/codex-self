# codex-self

![Python](https://img.shields.io/badge/python-3.11+-blue) ![Docker](https://img.shields.io/badge/docker-ready-blue)

Codex Self is not just a README. It is a **living service** that exposes identity, health diagnostics, persistent memory, sandbox enforcement, skill registries, and real-time WebSocket dashboards — all wired into the SAH

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Model Routing](#model-routing)
- [Project Layout](#project-layout)
- [Development](#development)
- [Related Repositories](#related-repositories)

## Overview

Codex Self is not just a README. It is a **living service** that exposes identity, health diagnostics, persistent memory, sandbox enforcement, skill registries, and real-time WebSocket dashboards — all wired into the SAH

| | |
|---|---|
| **Stack** | python |
| **Frameworks** | docker, fastapi, pydantic |
| **Tests** | yes |
| **Commits** | 2 |
| **Last activity** | 2026-08-10 |
| **Visibility** | public |

## Quick Start

### Install

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # or: pip install -e .
```

### Run

```bash
# Entry point not auto-detected; inspect the layout below.
```

## Model Routing

Agent work in this repo routes through Azure AI Foundry. See [`AGENTS.md`](./AGENTS.md)
for the full contract.

| Purpose | Deployment | Endpoint |
|---|---|---|
| Default / general | `gpt-5.6-sol` | `/openai/v1/chat/completions` |
| Deep reasoning | `claude-opus-5` | `/openai/v1/responses` **only** |
| Embeddings | `text-embedding-3-small` | `/openai/v1/embeddings` |

```bash
export AZURE_FOUNDRY_API_KEY=...        # never commit this
export AZURE_FOUNDRY_BASE_URL=https://<resource>.openai.azure.com/openai/v1
```

> **Gotcha:** Claude deployments on Azure return `404 api_not_supported` on
> `/chat/completions`. They answer **only** via the Responses API.

## Project Layout

```
AGENTS.md
Dockerfile
LICENSE
README.md
codex-self.skill
dashboard/
docker-compose.override.yml
pyproject.toml
scripts/
src/
tests/
```

## Development

```bash
# lint / format before committing
ruff check . && ruff format .

# run the CI check locally
gh workflow run hermes-azure-check.yml
```

Secrets live in environment variables and CI secrets — never in tracked files.

## Related Repositories

Part of a 84-repository workspace sharing one agentic contract:

- **[agentic-harness](https://github.com/sahiixx/agentic-harness)** — patterns, contracts, and reference implementations
- `AGENTS.md` in every repo pins identical model routing

---

<sub>README maintained by the agentic harness · last regenerated 2026-08-10</sub>
