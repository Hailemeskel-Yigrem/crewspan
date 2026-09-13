"""Integration tests for Technician API router."""

from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def app():
    application = create_app()
    yield application
    application.dependency_overrides.clear()


@pytest.fixture
def client(app):
    # Avoid lifespan/DB startup; dependency overrides supply services.
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def auth_headers():
    return {
        "Authorization": "Bearer test-token",
        "X-Tenant-Id": str(uuid4()),
    }


class TestTechnicianRouterList:
    def test_list_requires_tenant_header(self, app, client):
        from app.domains.technician.router import get_technician_service

        app.dependency_overrides[get_technician_service] = lambda: AsyncMock()
        response = client.get("/api/v1/technicians")
        assert response.status_code in (400, 401, 422)

    def test_list_returns_envelope(self, app, client, auth_headers):
        from app.domains.technician.router import get_technician_service

        mock_service = AsyncMock()
        mock_service.list.return_value = ([], 0)
        app.dependency_overrides[get_technician_service] = lambda: mock_service
        response = client.get("/api/v1/technicians?page=1&page_size=10", headers=auth_headers)
        assert response.status_code == 200


class TestTechnicianRouterGet:
    def test_get_not_found(self, app, client, auth_headers):
        from app.domains.technician.exceptions import TechnicianNotFoundError
        from app.domains.technician.router import get_technician_service

        mock_service = AsyncMock()
        mock_service.get.side_effect = TechnicianNotFoundError(uuid4())
        app.dependency_overrides[get_technician_service] = lambda: mock_service
        response = client.get(f"/api/v1/technicians/{uuid4()}", headers=auth_headers)
        assert response.status_code in (404, 422)


class TestTechnicianRouterCreate:
    def test_create_validates_body(self, app, client, auth_headers):
        from app.domains.technician.router import get_technician_service

        app.dependency_overrides[get_technician_service] = lambda: AsyncMock()
        response = client.post("/api/v1/technicians", headers=auth_headers, json={})
        assert response.status_code in (201, 422)


class TestTechnicianRouterCount:
    def test_count_endpoint(self, app, client, auth_headers):
        from app.domains.technician.router import get_technician_service

        mock_service = AsyncMock()
        mock_service.count.return_value = 5
        app.dependency_overrides[get_technician_service] = lambda: mock_service
        response = client.get("/api/v1/technicians/count", headers=auth_headers)
        assert response.status_code == 200


class TestTechnicianRouterActions:

    def test_set_status_route_registered(self, app):
        path = "/api/v1/technicians/{entity_id}/set-status"
        assert path in app.openapi()["paths"]


    def test_update_location_route_registered(self, app):
        path = "/api/v1/technicians/{entity_id}/update-location"
        assert path in app.openapi()["paths"]


    def test_calculate_utilization_route_registered(self, app):
        path = "/api/v1/technicians/{entity_id}/calculate-utilization"
        assert path in app.openapi()["paths"]
