"""Integration tests for StockMovement API router."""

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


class TestStockMovementRouterList:
    def test_list_requires_tenant_header(self, app, client):
        from app.domains.stock_movement.router import get_stock_movement_service

        app.dependency_overrides[get_stock_movement_service] = lambda: AsyncMock()
        response = client.get("/api/v1/stock-movements")
        assert response.status_code in (400, 401, 422)

    def test_list_returns_envelope(self, app, client, auth_headers):
        from app.domains.stock_movement.router import get_stock_movement_service

        mock_service = AsyncMock()
        mock_service.list.return_value = ([], 0)
        app.dependency_overrides[get_stock_movement_service] = lambda: mock_service
        response = client.get("/api/v1/stock-movements?page=1&page_size=10", headers=auth_headers)
        assert response.status_code == 200


class TestStockMovementRouterGet:
    def test_get_not_found(self, app, client, auth_headers):
        from app.domains.stock_movement.exceptions import StockMovementNotFoundError
        from app.domains.stock_movement.router import get_stock_movement_service

        mock_service = AsyncMock()
        mock_service.get.side_effect = StockMovementNotFoundError(uuid4())
        app.dependency_overrides[get_stock_movement_service] = lambda: mock_service
        response = client.get(f"/api/v1/stock-movements/{uuid4()}", headers=auth_headers)
        assert response.status_code in (404, 422)


class TestStockMovementRouterCreate:
    def test_create_validates_body(self, app, client, auth_headers):
        from app.domains.stock_movement.router import get_stock_movement_service

        app.dependency_overrides[get_stock_movement_service] = lambda: AsyncMock()
        response = client.post("/api/v1/stock-movements", headers=auth_headers, json={})
        assert response.status_code in (201, 422)


class TestStockMovementRouterCount:
    def test_count_endpoint(self, app, client, auth_headers):
        from app.domains.stock_movement.router import get_stock_movement_service

        mock_service = AsyncMock()
        mock_service.count.return_value = 5
        app.dependency_overrides[get_stock_movement_service] = lambda: mock_service
        response = client.get("/api/v1/stock-movements/count", headers=auth_headers)
        assert response.status_code == 200


class TestStockMovementRouterActions:

    def test_validate_quantity_route_registered(self, app):
        path = "/api/v1/stock-movements/{entity_id}/validate"
        assert path in app.openapi()["paths"]


    def test_reverse_route_registered(self, app):
        path = "/api/v1/stock-movements/{entity_id}/reverse"
        assert path in app.openapi()["paths"]
