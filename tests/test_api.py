from fastapi.testclient import TestClient

from nexus.main import app


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

        # Exercise a real MCP Streamable HTTP initialize request instead of
        # treating the endpoint like a browser page.
        initialized = client.post(
            "/mcp/",
            headers={
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
                "Host": "localhost",
            },
            json={
                "jsonrpc": "2.0",
                "id": 1,
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
        assert initialized.status_code == 200
        assert initialized.json()["result"]["serverInfo"]["name"] == "NEXUS-100"

        tool_list = client.post(
            "/mcp/",
            headers={
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
                "Host": "localhost",
            },
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
        for tool in tools:
            annotations = tool["annotations"]
            assert annotations["readOnlyHint"] is True
            assert annotations["destructiveHint"] is False
            assert annotations["openWorldHint"] is False

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
