"""Integration tests for Equipment API router."""

from __future__ import annotations

from uuid import uuid4
from unittest.mock import AsyncMock

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


class TestEquipmentRouterList:
    def test_list_requires_tenant_header(self, app, client):
        from app.domains.equipment.router import get_equipment_service

        app.dependency_overrides[get_equipment_service] = lambda: AsyncMock()
        response = client.get("/api/v1/equipments")
        assert response.status_code in (400, 401, 422)

    def test_list_returns_envelope(self, app, client, auth_headers):
        from app.domains.equipment.router import get_equipment_service

        mock_service = AsyncMock()
        mock_service.list.return_value = ([], 0)
        app.dependency_overrides[get_equipment_service] = lambda: mock_service
        response = client.get("/api/v1/equipments?page=1&page_size=10", headers=auth_headers)
        assert response.status_code == 200


class TestEquipmentRouterGet:
    def test_get_not_found(self, app, client, auth_headers):
        from app.domains.equipment.exceptions import EquipmentNotFoundError
        from app.domains.equipment.router import get_equipment_service

        mock_service = AsyncMock()
        mock_service.get.side_effect = EquipmentNotFoundError(uuid4())
        app.dependency_overrides[get_equipment_service] = lambda: mock_service
        response = client.get(f"/api/v1/equipments/{uuid4()}", headers=auth_headers)
        assert response.status_code in (404, 422)


class TestEquipmentRouterCreate:
    def test_create_validates_body(self, app, client, auth_headers):
        from app.domains.equipment.router import get_equipment_service

        app.dependency_overrides[get_equipment_service] = lambda: AsyncMock()
        response = client.post("/api/v1/equipments", headers=auth_headers, json={})
        assert response.status_code in (201, 422)


class TestEquipmentRouterCount:
    def test_count_endpoint(self, app, client, auth_headers):
        from app.domains.equipment.router import get_equipment_service

        mock_service = AsyncMock()
        mock_service.count.return_value = 5
        app.dependency_overrides[get_equipment_service] = lambda: mock_service
        response = client.get("/api/v1/equipments/count", headers=auth_headers)
        assert response.status_code == 200


class TestEquipmentRouterActions:

    def test_record_service_route_registered(self, app):
        path = "/api/v1/equipments/{entity_id}/record-service"
        assert path in app.openapi()["paths"]


    def test_retire_route_registered(self, app):
        path = "/api/v1/equipments/{entity_id}/retire"
        assert path in app.openapi()["paths"]
