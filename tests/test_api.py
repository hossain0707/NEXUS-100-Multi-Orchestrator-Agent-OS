from fastapi.testclient import TestClient

from nexus.main import app


def test_api_end_to_end():
    # The MCP Streamable HTTP session manager is intentionally single-lifecycle.
    # Keep one application lifespan for the complete integration scenario.
    with TestClient(app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"

        ready = client.get("/ready")
        assert ready.status_code == 200
        assert ready.json()["status"] == "ready"

        # /mcp must resolve to the MCP transport itself, not a Starlette 404.
        # A plain browser-style GET is not a valid MCP protocol request, so
        # any protocol-level response is acceptable here; routing 404 is not.
        mcp_response = client.get("/mcp")
        assert mcp_response.status_code != 404

        agents = client.get("/api/v1/agents")
        assert agents.status_code == 200
        assert agents.json()["count"] == 100

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
