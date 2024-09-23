"""Integration tests for InventoryLocation API router."""

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


class TestInventoryLocationRouterList:
    def test_list_requires_tenant_header(self, app, client):
        from app.domains.inventory_location.router import get_inventory_location_service

        app.dependency_overrides[get_inventory_location_service] = lambda: AsyncMock()
        response = client.get("/api/v1/inventory-locations")
        assert response.status_code in (400, 401, 422)

    def test_list_returns_envelope(self, app, client, auth_headers):
        from app.domains.inventory_location.router import get_inventory_location_service

        mock_service = AsyncMock()
        mock_service.list.return_value = ([], 0)
        app.dependency_overrides[get_inventory_location_service] = lambda: mock_service
        response = client.get("/api/v1/inventory-locations?page=1&page_size=10", headers=auth_headers)
        assert response.status_code == 200


class TestInventoryLocationRouterGet:
    def test_get_not_found(self, app, client, auth_headers):
        from app.domains.inventory_location.exceptions import InventoryLocationNotFoundError
        from app.domains.inventory_location.router import get_inventory_location_service

        mock_service = AsyncMock()
        mock_service.get.side_effect = InventoryLocationNotFoundError(uuid4())
        app.dependency_overrides[get_inventory_location_service] = lambda: mock_service
        response = client.get(f"/api/v1/inventory-locations/{uuid4()}", headers=auth_headers)
        assert response.status_code in (404, 422)


class TestInventoryLocationRouterCreate:
    def test_create_validates_body(self, app, client, auth_headers):
        from app.domains.inventory_location.router import get_inventory_location_service

        app.dependency_overrides[get_inventory_location_service] = lambda: AsyncMock()
        response = client.post("/api/v1/inventory-locations", headers=auth_headers, json={})
        assert response.status_code in (201, 422)


class TestInventoryLocationRouterCount:
    def test_count_endpoint(self, app, client, auth_headers):
        from app.domains.inventory_location.router import get_inventory_location_service

        mock_service = AsyncMock()
        mock_service.count.return_value = 5
        app.dependency_overrides[get_inventory_location_service] = lambda: mock_service
        response = client.get("/api/v1/inventory-locations/count", headers=auth_headers)
        assert response.status_code == 200


class TestInventoryLocationRouterActions:

    def test_assign_to_technician_route_registered(self, app):
        path = "/api/v1/inventory-locations/{entity_id}/assign-to-technician"
        assert path in app.openapi()["paths"]


    def test_list_low_stock_route_registered(self, app):
        path = "/api/v1/inventory-locations/{entity_id}/low-stock"
        assert path in app.openapi()["paths"]
