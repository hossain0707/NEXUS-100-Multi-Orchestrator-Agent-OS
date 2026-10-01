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

## Benchmarking

NEXUS-100 includes a reproducible benchmark suite for the capabilities the current system can genuinely measure: **domain-routing quality, routing latency, and governance/approval correctness**.

```bash
python benchmarks/run.py
```

The current corpus contains **20 routing cases + 8 governance cases** spanning all 10 domains. Reported routing metrics include macro precision, macro recall, macro F1, exact-match rate, and deterministic router latency. Governance tests verify that sensitive or high-risk actions are sent to human approval.

For a fair **ChatGPT-only vs ChatGPT + NEXUS-100** comparison, use the same task, same model, same available information, and blind-score the outputs on correctness, completeness, decomposition, routing, tool use, cross-domain coordination, safety/governance, and reproducibility.

See [`benchmarks/README.md`](benchmarks/README.md) for the full A/B protocol and reproducible commands.

> The benchmark does **not** claim that NEXUS-100 is more intelligent than ChatGPT. NEXUS-100 is currently an orchestration/control layer; answer-quality claims should only be published after controlled A/B runs.

## Live architecture UI

https://hossain0707.github.io/NEXUS-100-Multi-Orchestrator-Agent-OS/

