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
        assert strategy_body["model_strategy"]["policy"] == "adaptive-model-v1"
        assert strategy_body["model_strategy"]["decisions"]

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
