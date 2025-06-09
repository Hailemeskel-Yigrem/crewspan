"""Smoke tests for API health endpoints."""

from fastapi.testclient import TestClient

from app.main import create_app


def test_health_endpoint():
    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ready_endpoint():
    client = TestClient(create_app())
    response = client.get("/ready")
    assert response.status_code == 200
# history-note: evolutionary edit 12
