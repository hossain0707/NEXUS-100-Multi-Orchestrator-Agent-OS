# NEXUS-100 MCP deployment and OpenAI plugin submission

This document describes the **Python FastAPI/FastMCP service in `nexus/`**, which is the production implementation used by the public plugin package. The root `server.js` is retained as a legacy standalone development harness and is **not** the server referenced by `marketplace/nexus-100/mcp.json` or the Python Dockerfile.

## Implemented public MCP surface

The production service exposes Streamable HTTP MCP at `/mcp/`. The public directory surface is deliberately read-only and contains exactly five tools:

- `get_system_status` — public health/capability counts
- `list_domains` — the fixed 10-domain capability map
- `plan_mission` — stateless routing preview; no mission is created
- `list_model_catalog` — sanitized cached model-routing metadata
- `recommend_model_strategy` — stateless model/effort/token-budget recommendation

Every public tool advertises explicit `readOnlyHint=true`, `destructiveHint=false`, `openWorldHint=false`, a constrained input schema, and a structured output schema.

The public MCP server does **not** expose `run_mission`, mission persistence, approval creation, adaptive backend execution, GitHub writes, Gmail, cloud deployment, database administration, or any other consequential operation.

## Architecture boundary

```text
ChatGPT / Codex
      |
Streamable HTTP MCP
      |
NEXUS Meta Orchestrator
      |
Capability Router
      |
Adaptive Model / Effort Router
      |
10 Domain Orchestrators
      |
100 Specialist Agent Definitions
      |
Governance / Policy Boundary
```

The public MCP tools stop at planning/recommendation. They do not execute the routed work.

NEXUS can optionally run its own backend-model calls through the protected REST control plane, but that feature is disabled by default. A NEXUS backend model decision is separate from the model selected by a user in the ChatGPT interface. MCP cannot silently change the ChatGPT host model.

## Production URLs

Public MCP endpoint:

```text
https://nexus-100-multi-orchestrator-agent-os-393741258321.asia-northeast3.run.app/mcp/
```

Health endpoint:

```text
https://nexus-100-multi-orchestrator-agent-os-393741258321.asia-northeast3.run.app/health
```

Domain-verification endpoint, when a real portal token is configured:

```text
https://nexus-100-multi-orchestrator-agent-os-393741258321.asia-northeast3.run.app/.well-known/openai-apps-challenge
```

The challenge route returns HTTP 404 while `NEXUS_OPENAI_APPS_CHALLENGE` is unset. When the OpenAI submission portal generates a token, set that environment variable to the **exact** token and redeploy. The route returns that token as plain text and nothing else.

## Authentication boundary

The public directory MCP is intentionally read-only and does not require a user account. Leave `NEXUS_MCP_API_TOKEN` unset for the public submission.

The internal REST control plane is a separate boundary. Production startup requires `NEXUS_API_TOKEN`, and callers of `/api/*` must present that bearer token when it is configured. Do not reuse a public MCP credential as a control-plane credential.

For any future MCP capability that reads private user data or writes to an external system, add proper user authentication/authorization (for example OAuth 2.1 where appropriate) before exposing that capability publicly.

## Required production environment

At minimum for the public deployment:

```text
NEXUS_ENVIRONMENT=production
NEXUS_API_TOKEN=<secret stored in Secret Manager>
NEXUS_MCP_API_TOKEN=
NEXUS_BACKEND_MODEL_EXECUTION_ENABLED=false
NEXUS_OPENAI_APPS_CHALLENGE=
```

Recommended durable control-plane deployment:

```text
NEXUS_DATABASE_URL=postgresql+asyncpg://...
```

The default SQLite database under `/tmp` is ephemeral on Cloud Run and is not suitable for durable multi-instance mission state.

Optional backend-model execution requires all of the following:

```text
NEXUS_BACKEND_MODEL_EXECUTION_ENABLED=true
NEXUS_API_TOKEN=<secret>
NEXUS_LLM_API_KEY=<secret>
NEXUS_LLM_BASE_URL=https://api.openai.com/v1
```

Keep provider keys in a deployment secret manager. Never commit them.

## Local validation

Python service:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
ruff check nexus tests marketplace/build_release.py
pytest -q
python benchmarks/run.py
python marketplace/build_release.py
uvicorn nexus.main:app --reload --port 8080
```

Health:

```bash
curl http://localhost:8080/health
```

MCP Inspector:

```bash
npx @modelcontextprotocol/inspector@latest
```

Connect using Streamable HTTP:

```text
http://localhost:8080/mcp/
```

Verify initialization, `tools/list`, all five positive tool flows, invalid arguments, and requests that should not select a NEXUS tool.

## Public package

Build:

```bash
python marketplace/build_release.py
```

The build script validates the manifest/MCP configuration, checks the whitelisted files for obvious credential patterns, builds a clean ZIP, reopens it, validates its CRC, and rejects unexpected or unsafe members.

Expected output:

```text
marketplace/dist/nexus-100-plugin-1.0.1.zip
```

Expected ZIP members:

```text
plugin.json
mcp.json
assets/icon.svg
assets/logo.svg
```

The ZIP intentionally contains no `.env`, credentials, caches, repository source, tests, or development-only files.

## Current OpenAI directory requirements

OpenAI's current plugin submission documentation requires a remote MCP submission to use a production HTTPS server, complete domain verification, complete a current tool scan, provide the required listing URLs, provide exactly five positive and three negative review cases, provide release notes, and provide a reviewer-accessible demo recording before final submission. The organization/project also needs the applicable Apps Management permissions and a verified individual or business publishing identity.

Projects with EU data residency currently cannot submit MCP plugins for public review; use an eligible project with global data residency.

The package contains the five positive and three negative cases, release notes, listing metadata, icons, and public URLs. It deliberately does **not** contain a fake demo URL, fake domain token, test credentials, or reviewer credentials.

## Manual submission steps

1. In the OpenAI Platform organization/project that will own the plugin, complete individual or business identity verification and confirm the required Apps Management permissions.
2. Create a plugin draft using the **With MCP** submission path.
3. Upload the ZIP from `marketplace/dist/`.
4. Connect the production MCP URL shown above.
5. Complete the portal-generated domain challenge by setting `NEXUS_OPENAI_APPS_CHALLENGE` to the exact token, redeploying, and choosing Verify Domain.
6. Select **Scan Tools** and confirm exactly the five public tools above. Confirm input/output schemas and all three required annotations are present and accurate.
7. Run every positive and negative review case on the deployed plugin.
8. Record a real reviewer-accessible demo using `marketplace/nexus-100/DEMO_RECORDING_SCRIPT.md` and enter the resulting HTTPS video URL in the portal.
9. Complete the portal policy attestations and any annotation-justification fields it presents.
10. Submit for review. After approval, explicitly publish the approved version.

Do not add screenshots unless the MCP server later provides an actual custom UI output template; the current plugin has no embedded MCP UI.

## Future integrations

The following are **not** implemented as public plugin capabilities today:

- user-authenticated GitHub actions or repository writes
- Gmail, Calendar, Drive, Slack, or other account integrations
- cloud/Kubernetes deployment actions
- payment or commerce operations
- public multi-user mission persistence
- OAuth/RBAC-backed user accounts
- model-backed semantic task routing
- verifier-driven quality escalation and final multi-agent synthesis

If any of these are added later, treat them as a new security/review surface and update the MCP contract, privacy policy, test cases, and OpenAI submission metadata accordingly.
