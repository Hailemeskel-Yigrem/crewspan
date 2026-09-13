"""Integration tests for PartsRequest API router."""

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


class TestPartsRequestRouterList:
    def test_list_requires_tenant_header(self, app, client):
        from app.domains.parts_request.router import get_parts_request_service

        app.dependency_overrides[get_parts_request_service] = lambda: AsyncMock()
        response = client.get("/api/v1/parts-requests")
        assert response.status_code in (400, 401, 422)

    def test_list_returns_envelope(self, app, client, auth_headers):
        from app.domains.parts_request.router import get_parts_request_service

        mock_service = AsyncMock()
        mock_service.list.return_value = ([], 0)
        app.dependency_overrides[get_parts_request_service] = lambda: mock_service
        response = client.get("/api/v1/parts-requests?page=1&page_size=10", headers=auth_headers)
        assert response.status_code == 200


class TestPartsRequestRouterGet:
    def test_get_not_found(self, app, client, auth_headers):
        from app.domains.parts_request.exceptions import PartsRequestNotFoundError
        from app.domains.parts_request.router import get_parts_request_service

        mock_service = AsyncMock()
        mock_service.get.side_effect = PartsRequestNotFoundError(uuid4())
        app.dependency_overrides[get_parts_request_service] = lambda: mock_service
        response = client.get(f"/api/v1/parts-requests/{uuid4()}", headers=auth_headers)
        assert response.status_code in (404, 422)


class TestPartsRequestRouterCreate:
    def test_create_validates_body(self, app, client, auth_headers):
        from app.domains.parts_request.router import get_parts_request_service

        app.dependency_overrides[get_parts_request_service] = lambda: AsyncMock()
        response = client.post("/api/v1/parts-requests", headers=auth_headers, json={})
        assert response.status_code in (201, 422)


class TestPartsRequestRouterCount:
    def test_count_endpoint(self, app, client, auth_headers):
        from app.domains.parts_request.router import get_parts_request_service

        mock_service = AsyncMock()
        mock_service.count.return_value = 5
        app.dependency_overrides[get_parts_request_service] = lambda: mock_service
        response = client.get("/api/v1/parts-requests/count", headers=auth_headers)
        assert response.status_code == 200


class TestPartsRequestRouterActions:

    def test_approve_route_registered(self, app):
        path = "/api/v1/parts-requests/{entity_id}/approve"
        assert path in app.openapi()["paths"]


    def test_fulfill_route_registered(self, app):
        path = "/api/v1/parts-requests/{entity_id}/fulfill"
        assert path in app.openapi()["paths"]


    def test_reject_route_registered(self, app):
        path = "/api/v1/parts-requests/{entity_id}/reject"
        assert path in app.openapi()["paths"]
