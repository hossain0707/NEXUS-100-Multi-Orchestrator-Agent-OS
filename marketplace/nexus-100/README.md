# NEXUS-100 OpenAI public plugin submission checklist

This package is intentionally small, read-only, and auditable. It contains one remote Streamable HTTP MCP server, no bundled skills, no custom MCP UI, no app references, no hooks, and no commerce.

## Package contents

The upload ZIP is built from only:

- `plugin.json`
- `mcp.json`
- `assets/icon.svg`
- `assets/logo.svg`

Build and inspect it with:

```bash
python marketplace/build_release.py
```

Expected artifact:

```text
marketplace/dist/nexus-100-plugin-1.0.1.zip
```

## Public MCP contract

Production MCP URL:

```text
https://nexus-100-multi-orchestrator-agent-os-393741258321.asia-northeast3.run.app/mcp/
```

Expected public tools:

1. `get_system_status`
2. `list_domains`
3. `plan_mission`
4. `list_model_catalog`
5. `recommend_model_strategy`

All five are read-only/non-consequential. The public MCP server does not expose tracked mission creation, mission execution, approval creation, external provider writes, deployment, messaging, purchasing, or paid backend inference.

## Already prepared in the repository

- Portable Agent Plugins `plugin.json`
- Portable `mcp.json` with exactly one production Streamable HTTP server
- Professional listing metadata and starter prompts
- Square SVG listing logo and composer icon
- Public website, support page, privacy policy, and terms page
- Exactly 5 positive MCP review cases
- Exactly 3 negative review cases
- Release notes
- No commerce declaration
- Explicit MCP annotations on every public tool
- Typed MCP input and output contracts
- Domain challenge route at `/.well-known/openai-apps-challenge`
- Automated package validation
- Automated ZIP build and ZIP-content inspection in GitHub Actions

## Domain verification

OpenAI currently requires a domain-verification challenge for remote MCP submissions.

Do **not** invent a token. After the submission portal generates the real token, set:

```text
NEXUS_OPENAI_APPS_CHALLENGE=<exact portal token>
```

on the Cloud Run service and redeploy. The portal should then read the exact plain-text token at:

```text
https://nexus-100-multi-orchestrator-agent-os-393741258321.asia-northeast3.run.app/.well-known/openai-apps-challenge
```

When the environment variable is unset, that route intentionally returns 404.

## Manual requirements that cannot be completed in source code

1. Complete individual or business publisher verification in the OpenAI Platform organization that will own the plugin.
2. Ensure the selected project is eligible for MCP submission. OpenAI currently excludes projects with EU data residency from MCP public review.
3. Ensure the account has the required Apps Management permissions.
4. Create a draft using the **With MCP** flow and upload the release ZIP.
5. Complete the real domain-verification challenge.
6. Connect the production MCP endpoint and run **Scan Tools**.
7. Confirm the current scan discovers exactly the five public tools and the expected schemas/annotations.
8. Run all five positive and three negative cases against the deployed plugin.
9. Record a real reviewer-accessible walkthrough using `DEMO_RECORDING_SCRIPT.md`.
10. Put the real HTTPS demo-recording URL into the submission portal. The manifest intentionally omits `review.demo_recording_url` until such a URL actually exists.
11. Complete policy attestations and any annotation explanation/justification fields shown by the portal.
12. Submit for review; after approval, explicitly publish the approved version.

## Annotation rationale for the portal

Every public tool is `readOnlyHint=true` because it retrieves or computes a preview/recommendation without creating, updating, deleting, queuing, or sending anything outside the conversation.

Every public tool is `destructiveHint=false` because none can delete, overwrite, revoke, transmit, purchase, deploy, or perform another irreversible operation.

Every public tool is `openWorldHint=false` because it does not search arbitrary public internet destinations or operate on open-ended external entities. `recommend_model_strategy` may refresh a bounded server-owned model catalog from the configured model provider, but it does not send the user's objective to that provider and does not perform model inference.

If the OpenAI tool scan reports different behavior, fix the server and rescan rather than overriding the finding in prose.

## Publisher-name check

The current manifest uses:

```text
Md Najmul Hossain
```

The OpenAI directory ultimately uses the verified developer/business identity selected in the portal. If that verified identity uses a different exact public name, update the manifest before final upload.

## No screenshots

The current MCP server does not return a custom MCP UI output template. Do not add screenshots to the manifest unless a real custom UI is added later and the OpenAI tool scan recognizes it.

## Honest product boundary

NEXUS-100 currently provides orchestration previews, capability routing, adaptive backend-model strategy recommendations, policy primitives, and a protected internal control plane. It does **not** claim public GitHub/Gmail/cloud/provider execution, OAuth/RBAC-backed user integrations, durable public multi-user state, or the ability to change the model selected in the ChatGPT UI.

See `docs/MCP_DEPLOYMENT.md` for deployment environment variables and the full reproducible submission flow.
