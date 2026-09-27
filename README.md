# NEXUS-100 — Python AI Agent OS

NEXUS-100 is evolving from an architecture preview into a **Python multi-orchestrator AI Agent OS**: 10 domain orchestrators, exactly 100 capability-scoped specialist agents, a Meta Orchestrator, governance/approval boundaries, REST control-plane APIs, and a Streamable HTTP MCP interface for ChatGPT.

> **Current implementation boundary:** the control plane, registry, routing, mission state, policy primitives, REST API and MCP surface are implemented in Python. External provider execution (GitHub/Gmail/cloud), durable PostgreSQL/Redis infrastructure, OAuth/RBAC, and model-backed reasoning are the next production layers; the project does not pretend those side effects already exist.

## Runtime architecture

```text
ChatGPT / MCP Clients / REST Clients
               │
        FastAPI + MCP Gateway
               │
         Meta Orchestrator
               │
       Capability Router
               │
 ┌─────────────┼────────────────────┐
 │ 10 domain orchestrators          │
 │ 100 capability-scoped agents     │
 └─────────────┼────────────────────┘
               │
       Policy / Approval
               │
       Memory / Event Store
               │
        Provider Adapters
```

## Python core

- `nexus/registry.py` — deterministic 100-agent capability registry
- `nexus/orchestrator.py` — objective routing and mission planning
- `nexus/policy.py` — governed autonomy boundary
- `nexus/memory.py` — storage interface/development event store
- `nexus/api.py` — REST control-plane API
- `nexus/mcp_server.py` — ChatGPT/MCP tools
- `nexus/main.py` — FastAPI application and MCP mount
- `tests/` — registry/routing invariants

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
uvicorn nexus.main:app --reload --port 8080
```

Endpoints: `/health`, `/api/v1/agents`, `/api/v1/missions`, `/api/v1/events`, and Streamable HTTP MCP at `/mcp`.

## Docker / Cloud Run

```bash
docker build -t nexus-100-agent-os .
docker run --rm -p 8080:8080 nexus-100-agent-os
```

The container is Cloud Run compatible and honors the platform-provided `PORT`.

## Live architecture UI

https://hossain0707.github.io/NEXUS-100-Multi-Orchestrator-Agent-OS/

