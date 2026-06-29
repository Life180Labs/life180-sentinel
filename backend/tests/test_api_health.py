"""Integration tests for the FastAPI health endpoint."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_200() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200


def test_health_response_structure() -> None:
    response = client.get("/api/v1/health")
    data = response.json()
    assert "status" in data
    assert data["status"] == "ok"
