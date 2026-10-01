# NEXUS-100 — Python AI Agent OS

NEXUS-100 is evolving from an architecture preview into a **Python multi-orchestrator AI Agent OS**: 10 domain orchestrators, exactly 100 capability-scoped specialist agents, a Meta Orchestrator, governance/approval boundaries, REST control-plane APIs, and a Streamable HTTP MCP interface for ChatGPT.

> **Current implementation boundary:** the control plane, 100-agent registry, mission routing, adaptive model/effort planning, bounded backend-model execution, policy primitives, REST API and MCP surface are implemented in Python. External application providers (GitHub/Gmail/cloud), durable PostgreSQL/Redis infrastructure, OAuth/RBAC, and full model-backed semantic task routing remain future production layers; the project does not pretend those side effects already exist.

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
   Adaptive Model + Effort Router
   fast / balanced / strong / premium
   low / medium / high / extra-high
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
- `nexus/model_catalog.py` — dynamic provider model discovery, capability/cost/speed profiles, specialization-aware selection
- `nexus/model_router.py` — per-agent model tier, concrete model, reasoning effort, token budget and escalation policy
- `nexus/llm.py` — optional OpenAI-compatible backend model adapter with usage telemetry
- `nexus/executor.py` — bounded adaptive execution with model escalation on provider failures
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

## Adaptive model and reasoning routing

NEXUS-100 keeps the existing **10 domain orchestrators and all 100 specialist agents**. Model choice is an execution policy above the agents, so an agent's identity/capability is not tied to one expensive model.

For each selected specialist, `adaptive-model-v2-catalog` assigns:

- a model tier: **fast → balanced → strong → premium**
- reasoning effort: **low → medium → high → extra-high**
- a bounded output-token budget
- a confidence score and routing rationale
- up to `NEXUS_MAX_MODEL_ESCALATIONS` stronger fallback models

Simple productivity/personal tasks can stay on the fast tier, while complex cross-domain, production, or security work is promoted to stronger compute. Security has a stronger minimum tier. Backend execution records provider-reported input/output token usage and only escalates to a stronger configured model when an execution attempt fails.

NEXUS no longer depends on only four hard-coded model names. When a provider key is configured it calls the provider's standard `/models` endpoint, builds a cached catalog of the exact model IDs available to that account, classifies recognized general/specialist families, and selects the least-cost qualified model for each agent. Domain specialists are preferred when available. The four tier settings remain only as safe fallbacks when provider discovery is unavailable.

The catalog is refreshed at startup and lazily after its TTL expires. `GET /api/v1/models` and the MCP tool `list_model_catalog` expose the cached catalog without triggering paid inference.

Backend model execution is disabled by default to prevent accidental API spend. Enabling it requires both `NEXUS_API_TOKEN` and `NEXUS_LLM_API_KEY`. This keeps paid execution behind the existing authenticated API boundary.

Read-only recommendation endpoint:

```text
POST /api/v1/model-routing/recommend
```

The MCP server exposes `recommend_model_strategy`, so ChatGPT can inspect NEXUS's selected agents, exact selected model IDs, model tiers, effort levels, token budgets, fallback models, and selection source without triggering paid backend inference.

> **ChatGPT host-model boundary:** an MCP server cannot silently change the model selected by the user in the ChatGPT interface. Automatic model switching applies to NEXUS-managed backend model calls. When NEXUS is used only as a ChatGPT MCP tool, ChatGPT remains the host reasoning model while NEXUS supplies orchestration/model recommendations.

## Benchmarking

NEXUS-100 includes a reproducible benchmark suite for the capabilities the current system can genuinely measure: **domain-routing quality, routing latency, and governance/approval correctness**.

```bash
python benchmarks/run.py
```

The current corpus contains **20 routing cases + 8 governance cases** spanning all 10 domains.

| Current deterministic benchmark | Result |
|---|---:|
| Routing macro precision | **0.926** |
| Routing macro recall | **0.938** |
| Routing macro F1 | **0.916** |
| Routing exact-match rate | **70.0%** |
| Governance approval accuracy | **100.0%** |

Reported routing metrics measure domain-selection behavior. Router latency is generated at runtime because it depends on the execution environment. Governance tests verify that sensitive or high-risk actions are sent to human approval. Machine-readable and Markdown results are stored under [`benchmarks/results/`](benchmarks/results/).

For a fair **ChatGPT-only vs ChatGPT + NEXUS-100** comparison, use the same task, same model, same available information, and blind-score the outputs on correctness, completeness, decomposition, routing, tool use, cross-domain coordination, safety/governance, and reproducibility.

See [`benchmarks/README.md`](benchmarks/README.md) for the full A/B protocol and reproducible commands.

> The benchmark does **not** claim that NEXUS-100 is more intelligent than ChatGPT. NEXUS-100 is currently an orchestration/control layer; answer-quality claims should only be published after controlled A/B runs.

## ChatGPT vs NEXUS-100 comparison

A controlled **routing-only** comparison is now included using the same 20 benchmark prompts and gold domain labels.

| System | Macro precision | Macro recall | Macro F1 | Exact-match rate |
|---|---:|---:|---:|---:|
| ChatGPT-only baseline | **1.000** | **0.975** | **0.983** | **95.0%** |
| NEXUS-100 router | 0.926 | 0.938 | 0.916 | 70.0% |

This result shows that the current deterministic NEXUS keyword router is not yet more accurate than ChatGPT on this routing corpus. NEXUS-100's current advantage is structured orchestration, explicit agent/domain control, governance, mission tracking, and MCP integration—not superior raw routing intelligence.

See [`benchmarks/results/chatgpt_vs_nexus.md`](benchmarks/results/chatgpt_vs_nexus.md) for methodology, predictions, limitations, and interpretation.

## Live architecture UI

https://hossain0707.github.io/NEXUS-100-Multi-Orchestrator-Agent-OS/

