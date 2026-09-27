# NEXUS-100 — Multi-Orchestrator Agent OS

A governed multi-orchestrator architecture for coordinating **100 specialist agents across 10 domains**, with an interactive control-plane preview and a real Model Context Protocol (MCP) gateway for ChatGPT integration.

## Live architecture preview

https://hossain0707.github.io/NEXUS-100-Multi-Orchestrator-Agent-OS/

The preview visualizes mission routing, cross-domain handoffs, specialist activation, event flow, memory, and approval gates.

## MCP gateway

The repository now includes a real Streamable HTTP MCP server built with the official Model Context Protocol TypeScript SDK.

### Exposed tools

| Tool | Purpose | Side effect |
|---|---|---|
| `get_system_status` | Inspect control-plane health | Read only |
| `list_domains` | Inspect orchestrators, capabilities and 100 agent slots | Read only |
| `plan_mission` | Route an objective to the smallest useful domain set | Read only |
| `run_mission` | Create a tracked mission/dry run | Control-plane state |
| `get_mission` | Inspect a mission | Read only |
| `request_sensitive_action` | Create a human-approval proposal | No external execution |

The MCP endpoint is `/mcp`. A health endpoint is available at `/health`.

## Architecture

```text
ChatGPT / API / User
        │
        ▼
   NEXUS MCP Gateway
        │
        ▼
   Meta Orchestrator
        │
   Mission Planner
        │
   Global Event Bus
        │
 ┌──────┼──────────────────────────────┐
 ▼      ▼                              ▼
Research Engineering ...       Personal
 Orch.     Orch.               Orch.
 │          │                    │
10 agents  10 agents    ...    10 agents
 └──────────┼────────────────────┘
            ▼
      Memory / Audit
            │
      Policy + Approval
            │
       Tool Adapters
```

## Run locally

```bash
npm install
npm run check
npm start
```

Then:

- MCP: `http://localhost:8787/mcp`
- Health: `http://localhost:8787/health`

Test with:

```bash
npx @modelcontextprotocol/inspector@latest
```

Select **Streamable HTTP** and enter `http://localhost:8787/mcp`.

## Docker

```bash
docker build -t nexus-100-mcp .
docker run --rm -p 8787:8787 --env-file .env nexus-100-mcp
```

## ChatGPT connection

GitHub Pages hosts only the visual frontend; ChatGPT needs the MCP server deployed separately at a stable HTTPS URL such as:

```text
https://your-nexus-api.example/mcp
```

After deployment, add that endpoint as a custom MCP app/plugin in ChatGPT developer mode and run **Scan Tools**.

Detailed deployment, security, authentication and ChatGPT setup instructions are in [docs/MCP_DEPLOYMENT.md](docs/MCP_DEPLOYMENT.md).

## Production boundaries

The MCP transport, tool schemas, safety annotations, Docker packaging, health endpoint, CI validation and approval-oriented tool surface are implemented. The current mission state is intentionally in-memory and is for contract/integration testing.

Before multi-user production deployment, add:

- OAuth 2.1 with server-side scope/audience enforcement
- PostgreSQL durable mission/audit state
- Redis or another durable worker/event queue
- RBAC and tenant isolation
- structured logs, OpenTelemetry traces and metrics
- rate limiting and idempotency
- provider-specific GitHub/Google/cloud adapters
- human approval before consequential external writes

NEXUS-100 deliberately does not claim an external action succeeded unless a configured executor actually confirms it.

## Security model

Agents should receive narrow capabilities rather than generic shell/network access. Read operations can be automated when authorized. Repository writes, deployments, deletion, spending and external communication should pass through explicit policy and approval gates.

Never commit secrets. Use the deployment platform's secret manager.

## Repository layout

```text
index.html                  Interactive architecture preview
server.js                   MCP Streamable HTTP gateway
package.json                MCP runtime dependencies
Dockerfile                  Container deployment
.env.example                Runtime configuration template
.github/workflows/mcp-ci.yml  MCP validation CI
docs/MCP_DEPLOYMENT.md      Deployment + ChatGPT guide
```

## License

Add a license before redistributing this project publicly if you want explicit reuse terms.

---

**MD NAJMUL HOSSAIN**  
AI Research Engineer · LLM Training · Multi-Agent Systems · AI Infrastructure
