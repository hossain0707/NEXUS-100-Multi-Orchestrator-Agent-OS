from fastapi.testclient import TestClient

from nexus.main import app


def test_health():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


def test_agents_registry_api():
    with TestClient(app) as client:
        response = client.get("/api/v1/agents")
        assert response.status_code == 200
        assert response.json()["count"] == 100


def test_create_and_read_mission():
    with TestClient(app) as client:
        created = client.post(
            "/api/v1/missions",
            json={"objective": "Research an LLM and estimate GPU deployment security risk"},
        )
        assert created.status_code == 200
        mission = created.json()
        fetched = client.get(f"/api/v1/missions/{mission['id']}")
        assert fetched.status_code == 200
        assert fetched.json()["id"] == mission["id"]
