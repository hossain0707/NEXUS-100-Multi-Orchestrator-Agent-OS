# Google AI Builder Cup 2026 — NEXUS-100 Submission

**Team:** NEXUS-100 AI Innovators  
**Challenge:** Future of Work  
**Team lead:** Md Najmul Hossain  
**Source:** https://github.com/hossain0707/NEXUS-100-Multi-Orchestrator-Agent-OS  
**Public console:** https://hossain0707.github.io/NEXUS-100-Multi-Orchestrator-Agent-OS/  
**Cloud Run:** https://nexus-100-multi-orchestrator-agent-os-393741258321.asia-northeast3.run.app

## Problem and value proposition

Organizations want AI agents across engineering, research, analytics, security, infrastructure, and business functions, but opaque prompting leaves weak auditability and governance. NEXUS-100 exposes an explicit planning pipeline: meta-orchestrator → capability router → model/effort policy → specialist assignment → governance. This makes orchestration inspectable and avoids unauthorized side effects.

## Implemented, verified in source

- 10 domain orchestrators and exactly 100 specialist capabilities in the registry.
- Deterministic mission planning, model/effort recommendations, bounded escalation.
- Five public read-only MCP tools, with protected internal REST APIs.
- FastAPI + Docker backend documented as deployed on Google Cloud Run.
- Public GitHub Pages architecture console and deterministic fixed-corpus benchmarks.
- Explicit non-claims: no public autonomous email, repository, payment, deployment, or data writes.

## Google AI integration: optional, safety-first

**Current runtime is NOT automatically Gemini-powered.** The existing backend speaks OpenAI-compatible Chat Completions; Google's Gemini API supports an OpenAI-compatible endpoint. The model catalog recognizes `gemini-2.5-flash-lite` and `gemini-2.5-flash` after the competition preparation update. Actual generation requires a private free-tier API key, configuration, enabling the backend and a redeploy. The public console's `/demo/strategy` is still read-only and does not invoke Gemini.

1. Create a **free-tier** Gemini API key at https://aistudio.google.com/apikey (check your project's pricing mode and quotas).
2. Copy settings from [`.env.gemini.free.example`](../.env.gemini.free.example) to **private** deployment secrets. Never commit real keys.
3. Keep `NEXUS_BACKEND_MODEL_EXECUTION_ENABLED=false` while developing and testing.
4. Review quota, API model eligibility and the private REST authorization gate. Only then consider setting `NEXUS_BACKEND_MODEL_EXECUTION_ENABLED=true` on a **protected** deployment with `NEXUS_API_TOKEN`.
5. Perform an authorized live API call and record the real model, status, and output for the judges. If an account lacks free quota, keep inference disabled instead of enabling billing.

**No automatic spend:** This change makes Google model IDs routable; it does not provision billing, invoke a paid endpoint, or expose an unauthenticated inference endpoint. Cloud Run may require a billing account even for requests within free usage allowance.

**Firestore/Firebase:** Neither is currently required for the implemented mission-planning path. No Firebase/Firestore integration is claimed. Firestore could later store mission and approval history, but doing so requires a deployment and tests; it must not be represented as built.

## Public demo flow (truthful)

1. Open the public console.
2. Inspect 10 domains / 100 specialist roles.
3. Verify Cloud Run `GET /health`, `GET /ready`, `GET /status`.
4. Send an objective to `POST /demo/strategy` via the existing console (sample: `Research an enterprise RAG deployment and review security`).
5. Inspect returned `route` and `model_strategy`; no generative response is created at this endpoint.
6. Explain protected execution, explicit approvals and bounded model escalation.

## Benchmark transparency

Repository's **small deterministic fixed-corpus** results: macro F1=0.916, exact match=70.0%, governance approval accuracy=100.0%. The ChatGPT-only routing baseline on this corpus had macro F1=0.983 and exact match=95.0%. These are *not* general intelligence or third-party benchmark claims. The system differentiates on governance, control, reproducibility and agent-routing architecture, not on better baseline routing accuracy.

## Submission constraints

Competition form requests: valid GCP / Cloud Run prototype link, public GitHub repository, prescribed-template PDF pitch deck (<=5MB), 3–4 minute public demo video, team/solution summary and details of Google technologies used. Provide only implementations actually tested and demonstrable. **Do not claim Gemini, Firebase or Firestore are live until demonstrated.** The organizers decide eligibility, deadline and acceptance.

## Security, licensing and ownership

Owner: Md Najmul Hossain. Deployment keys remain in secret infrastructure; public MCP remains read-only. Repository license is proprietary as stated in the main README. Respect the published competition eligibility policy, including team member requirements and student-status restrictions, before submission.
