# NEXUS-100 Public Directory Submission Checklist

The package in this directory is intentionally read-only and contains no skills or embedded UI. That keeps the first public review surface small and auditable.

## Already prepared

- Portable Agent Plugins `plugin.json`
- Remote Streamable HTTP `mcp.json`
- Square SVG listing logo and composer icon
- Public website
- Privacy policy
- Terms of service
- Support page
- Exactly 5 positive MCP review cases
- Exactly 3 negative MCP review cases
- Release notes
- No commerce
- Read-only MCP server with explicit `readOnlyHint`, `destructiveHint`, and `openWorldHint`
- Production domain challenge route at `/.well-known/openai-apps-challenge`

## Manual portal steps that cannot be pre-generated

1. Verify the individual or business publisher identity in the OpenAI Platform organization that will own the plugin.
2. Upload the release ZIP from this directory.
3. When the portal generates the domain challenge token, set Cloud Run environment variable `NEXUS_OPENAI_APPS_CHALLENGE` to that exact token and redeploy. Verify the portal can read:
   `https://nexus-100-multi-orchestrator-agent-os-393741258321.asia-northeast3.run.app/.well-known/openai-apps-challenge`
4. Run the production MCP tool scan and resolve any portal findings.
5. Record a short real walkthrough using the script in `DEMO_RECORDING_SCRIPT.md`, host it at a reviewer-accessible HTTPS URL, and paste that URL into Review information.
6. Complete the policy attestations and submit for review.
7. After approval, choose Publish plugin.

If the verified publisher identity uses a different exact spelling than `Hossain Md Najmul`, update `author.name` and `extensions.com.openai.interface.developerName` before upload.
