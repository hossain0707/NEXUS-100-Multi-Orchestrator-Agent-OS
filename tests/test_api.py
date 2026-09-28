from fastapi.testclient import TestClient

from nexus.main import app


def test_api_end_to_end():
    # The MCP Streamable HTTP session manager is intentionally single-lifecycle.
    # Keep one application lifespan for the complete API integration scenario.
    with TestClient(app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"

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
