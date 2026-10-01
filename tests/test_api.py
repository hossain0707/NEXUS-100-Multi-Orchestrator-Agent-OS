from fastapi.testclient import TestClient

from nexus.config import settings
from nexus.main import app
from nexus.memory import memory


def _mcp_headers():
    return {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
        "Host": "localhost",
    }


def _initialize(client, request_id=1):
    return client.post(
        "/mcp/",
        headers=_mcp_headers(),
        json={
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {
                    "name": "nexus-ci",
                    "version": "1.0",
                },
            },
        },
    )


def test_api_end_to_end():
    # The MCP session manager is intentionally single-lifecycle. Keep one
    # application lifespan for the complete REST + MCP integration scenario.
    with TestClient(app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"

        ready = client.get("/ready")
        assert ready.status_code == 200
        assert ready.json()["status"] == "ready"

        # Domain verification must be disabled until the real portal token exists.
        settings.openai_apps_challenge = None
        challenge = client.get("/.well-known/openai-apps-challenge")
        assert challenge.status_code == 404
        settings.openai_apps_challenge = "openai-real-token-would-go-here"
        challenge = client.get("/.well-known/openai-apps-challenge")
        assert challenge.status_code == 200
        assert challenge.text == "openai-real-token-would-go-here"
        assert challenge.headers["content-type"].startswith("text/plain")
        settings.openai_apps_challenge = None

        public_status = client.get("/status")
        assert public_status.status_code == 200
        assert public_status.json()["agents"] == 100
        assert public_status.json()["adaptive_model_routing"] is True

        preview = client.post(
            "/demo/strategy",
            json={
                "objective": (
                    "Research an LLM deployment, estimate GPU cost, and review security"
                )
            },
        )
        assert preview.status_code == 200
        preview_body = preview.json()
        assert preview_body["route"]
        assert preview_body["model_strategy"]["policy"] == "adaptive-model-v2-catalog"

        initialized = _initialize(client)
        assert initialized.status_code == 200
        assert initialized.json()["result"]["serverInfo"]["name"] == "NEXUS-100"

        tool_list = client.post(
            "/mcp/",
            headers=_mcp_headers(),
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {},
            },
        )
        assert tool_list.status_code == 200
        tools = tool_list.json()["result"]["tools"]
        names = {tool["name"] for tool in tools}
        assert names == {
            "get_system_status",
            "list_domains",
            "plan_mission",
            "list_model_catalog",
            "recommend_model_strategy",
        }
        assert {
            "run_mission",
            "get_mission",
            "request_sensitive_action",
        }.isdisjoint(names)

        for tool in tools:
            annotations = tool["annotations"]
            assert annotations["readOnlyHint"] is True
            assert annotations["destructiveHint"] is False
            assert annotations["openWorldHint"] is False
            assert tool["description"]
            assert tool["inputSchema"]["type"] == "object"
            assert tool.get("outputSchema", {}).get("type") == "object"

        by_name = {tool["name"]: tool for tool in tools}
        plan_schema = by_name["plan_mission"]["inputSchema"]
        assert plan_schema["properties"]["objective"]["minLength"] == 3
        assert plan_schema["properties"]["objective"]["maxLength"] == 4000
        assert set(plan_schema["properties"]["priority"]["enum"]) == {
            "low",
            "normal",
            "high",
            "critical",
        }

        missions_before = len(memory.missions)
        events_before = len(memory.events)
        called = client.post(
            "/mcp/",
            headers=_mcp_headers(),
            json={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "plan_mission",
                    "arguments": {
                        "objective": (
                            "Research an LLM, estimate GPU cost, and review security"
                        ),
                        "priority": "high",
                    },
                },
            },
        )
        assert called.status_code == 200
        result = called.json()["result"]
        assert result["isError"] is False
        assert result["structuredContent"]["priority"] == "high"
        assert result["structuredContent"]["route"]
        assert len(memory.missions) == missions_before
        assert len(memory.events) == events_before

        agents = client.get("/api/v1/agents")
        assert agents.status_code == 200
        assert agents.json()["count"] == 100

        strategy = client.post(
            "/api/v1/model-routing/recommend",
            json={
                "objective": (
                    "Deploy an LLM API on GPU infrastructure with a security review"
                )
            },
        )
        assert strategy.status_code == 200
        strategy_body = strategy.json()
        assert strategy_body["model_strategy"]["policy"] == "adaptive-model-v2-catalog"
        assert strategy_body["model_strategy"]["decisions"]

        models = client.get("/api/v1/models")
        assert models.status_code == 200
        assert "models" in models.json()

        created = client.post(
            "/api/v1/missions",
            json={
                "objective": (
                    "Research an LLM and estimate GPU deployment security risk"
                )
            },
        )
        assert created.status_code == 200
        mission = created.json()

        fetched = client.get(f"/api/v1/missions/{mission['id']}")
        assert fetched.status_code == 200
        assert fetched.json()["id"] == mission["id"]

        events = client.get("/api/v1/events")
        assert events.status_code == 200
        assert any(
            event["kind"] == "mission_planned"
            for event in events.json()["events"]
        )

        # Production can protect the internal REST API without accidentally
        # protecting the public read-only MCP endpoint.
        settings.api_token = "rest-control-plane-secret"
        try:
            assert client.get("/api/v1/agents").status_code == 401
            authorized = client.get(
                "/api/v1/agents",
                headers={"Authorization": "Bearer rest-control-plane-secret"},
            )
            assert authorized.status_code == 200

            still_public = _initialize(client, request_id=10)
            assert still_public.status_code == 200
        finally:
            settings.api_token = None
