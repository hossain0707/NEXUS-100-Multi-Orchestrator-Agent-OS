# NEXUS-100 Demo Recording Script

Target length: about 3-5 minutes. Record the actual production plugin in ChatGPT or Codex after the latest MCP scan.

1. Show the NEXUS-100 listing and confirm the production MCP endpoint is connected.
2. Ask: "Show me the NEXUS-100 domains and the capabilities under each domain." Confirm `list_domains` is selected.
3. Ask: "Plan an 8B LLM deployment that needs engineering, GPU infrastructure, cost analysis, and a security review." Confirm `plan_mission` returns a stateless multi-domain route.
4. Ask: "Recommend the NEXUS model strategy for debugging a complex production API security issue." Confirm `recommend_model_strategy` returns model, reasoning effort, token budget, and fallback information.
5. Ask: "List the models NEXUS can currently consider for adaptive routing." Confirm `list_model_catalog` returns sanitized catalog metadata.
6. Ask: "Check whether NEXUS-100 is healthy and tell me how many domains and agents are registered." Confirm `get_system_status` returns the expected counts.
7. Show one unsupported write request such as "Deploy this application now." Demonstrate that the public NEXUS plugin has no deployment/write tool and does not claim the action was executed.
8. End on the public privacy, terms, and support pages.

Do not include API keys, access tokens, private account data, hidden prompts, or developer-mode secrets in the recording.
