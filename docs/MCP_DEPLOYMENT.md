# NEXUS-100 MCP deployment and ChatGPT connection

## What is implemented

The repository exposes a Streamable HTTP MCP endpoint at `/mcp` using the official Model Context Protocol TypeScript SDK. The initial tool surface is intentionally small and governed:

- `get_system_status`
- `list_domains`
- `plan_mission`
- `run_mission`
- `get_mission`
- `request_sensitive_action`

The MCP gateway represents the NEXUS-100 control plane. It does not falsely report external side effects. Real GitHub, Gmail, cloud, database, or deployment executors should be added as narrow provider adapters with authorization, audit logging, idempotency, timeouts, and approval gates.

## Local validation

```bash
npm install
npm run check
npm start
```

Health check:

```bash
curl http://localhost:8787/health
```

Run MCP Inspector:

```bash
npx @modelcontextprotocol/inspector@latest
```

Choose **Streamable HTTP** and connect to:

```text
http://localhost:8787/mcp
```

Test initialization, tool discovery, valid inputs, invalid inputs, and every tool result.

## Docker

```bash
docker build -t nexus-100-mcp .
docker run --rm -p 8787:8787 --env-file .env nexus-100-mcp
```

## Production deployment

GitHub Pages cannot host the MCP backend. Deploy the container to a platform that provides a stable HTTPS endpoint and supports streaming HTTP. The final URL should look like:

```text
https://YOUR-MCP-DOMAIN.example/mcp
```

Production requirements:

- TLS/HTTPS
- OAuth 2.1 for multi-user/private data
- server-side scope and audience validation on every request
- secrets in the deployment platform's secret manager
- rate limits and request/body limits
- structured logs, metrics, traces, alerts
- durable mission state in PostgreSQL rather than the in-memory development store
- Redis or a durable queue for distributed workers
- idempotency keys for write operations
- human approval for consequential writes
- backups and a rollback strategy
- outbound network allow-lists for high-risk connectors

The current in-memory mission map is suitable for MCP contract testing, not multi-instance production persistence.

## Connect to ChatGPT

After deploying the MCP server:

1. Verify `https://YOUR-DOMAIN/mcp` with MCP Inspector.
2. In ChatGPT on the web, enable **Developer mode** where your plan/workspace supports it.
3. Open **Plugins/Apps** and create a custom app/plugin.
4. Enter the HTTPS MCP URL including `/mcp`.
5. Configure the authentication mechanism used by your deployment.
6. Run **Scan Tools** and confirm the six NEXUS tools and their annotations.
7. Create the draft app.
8. Open a new chat, select/mention NEXUS-100, and test:
   - “Use NEXUS-100 to plan a mission to review my AI repository and estimate its GPU deployment needs.”
   - “Show the NEXUS-100 domains.”
   - “Start that mission in dry-run mode and show me the route.”
9. Verify that consequential actions stop at `request_sensitive_action` rather than being represented as executed.

## Production authentication

A shared `NEXUS_API_TOKEN` is provided only as a simple private-development boundary. For a real multi-user ChatGPT deployment, replace it with OAuth 2.1 authorization and validate token signature, issuer, audience, expiry, subject, and scopes on every tool invocation.

## Recommended next adapters

Implement provider adapters separately from the MCP contract:

- GitHub: repository/issue/PR/Actions read tools; approval-gated commit/PR tools
- Google: Gmail/Calendar/Drive with OAuth scopes
- Infrastructure: Kubernetes/cloud/GPU metrics read tools; approval-gated deployment changes
- Knowledge: web/search/document retrieval with provenance
- Notifications: Slack/email/mobile providers with explicit external-communication approval

Do not give a generic shell, unrestricted HTTP client, or broad cloud credentials directly to an LLM agent.
