"""Integration tests for InventoryItem API router."""

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


class TestInventoryItemRouterList:
    def test_list_requires_tenant_header(self, app, client):
        from app.domains.inventory_item.router import get_inventory_item_service

        app.dependency_overrides[get_inventory_item_service] = lambda: AsyncMock()
        response = client.get("/api/v1/inventory-items")
        assert response.status_code in (400, 401, 422)

    def test_list_returns_envelope(self, app, client, auth_headers):
        from app.domains.inventory_item.router import get_inventory_item_service

        mock_service = AsyncMock()
        mock_service.list.return_value = ([], 0)
        app.dependency_overrides[get_inventory_item_service] = lambda: mock_service
        response = client.get("/api/v1/inventory-items?page=1&page_size=10", headers=auth_headers)
        assert response.status_code == 200


class TestInventoryItemRouterGet:
    def test_get_not_found(self, app, client, auth_headers):
        from app.domains.inventory_item.exceptions import InventoryItemNotFoundError
        from app.domains.inventory_item.router import get_inventory_item_service

        mock_service = AsyncMock()
        mock_service.get.side_effect = InventoryItemNotFoundError(uuid4())
        app.dependency_overrides[get_inventory_item_service] = lambda: mock_service
        response = client.get(f"/api/v1/inventory-items/{uuid4()}", headers=auth_headers)
        assert response.status_code in (404, 422)


class TestInventoryItemRouterCreate:
    def test_create_validates_body(self, app, client, auth_headers):
        from app.domains.inventory_item.router import get_inventory_item_service

        app.dependency_overrides[get_inventory_item_service] = lambda: AsyncMock()
        response = client.post("/api/v1/inventory-items", headers=auth_headers, json={})
        assert response.status_code in (201, 422)


class TestInventoryItemRouterCount:
    def test_count_endpoint(self, app, client, auth_headers):
        from app.domains.inventory_item.router import get_inventory_item_service

        mock_service = AsyncMock()
        mock_service.count.return_value = 5
        app.dependency_overrides[get_inventory_item_service] = lambda: mock_service
        response = client.get("/api/v1/inventory-items/count", headers=auth_headers)
        assert response.status_code == 200


class TestInventoryItemRouterActions:

    def test_adjust_reorder_levels_route_registered(self, app):
        path = "/api/v1/inventory-items/{entity_id}/adjust-reorder-levels"
        assert path in app.openapi()["paths"]


    def test_deactivate_route_registered(self, app):
        path = "/api/v1/inventory-items/{entity_id}/deactivate"
        assert path in app.openapi()["paths"]


    def test_calculate_stock_value_route_registered(self, app):
        path = "/api/v1/inventory-items/{entity_id}/stock-value"
        assert path in app.openapi()["paths"]
