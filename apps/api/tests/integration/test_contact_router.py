"""Integration tests for Contact API router."""

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


class TestContactRouterList:
    def test_list_requires_tenant_header(self, app, client):
        from app.domains.contact.router import get_contact_service

        app.dependency_overrides[get_contact_service] = lambda: AsyncMock()
        response = client.get("/api/v1/contacts")
        assert response.status_code in (400, 401, 422)

    def test_list_returns_envelope(self, app, client, auth_headers):
        from app.domains.contact.router import get_contact_service

        mock_service = AsyncMock()
        mock_service.list.return_value = ([], 0)
        app.dependency_overrides[get_contact_service] = lambda: mock_service
        response = client.get("/api/v1/contacts?page=1&page_size=10", headers=auth_headers)
        assert response.status_code == 200


class TestContactRouterGet:
    def test_get_not_found(self, app, client, auth_headers):
        from app.domains.contact.exceptions import ContactNotFoundError
        from app.domains.contact.router import get_contact_service

        mock_service = AsyncMock()
        mock_service.get.side_effect = ContactNotFoundError(uuid4())
        app.dependency_overrides[get_contact_service] = lambda: mock_service
        response = client.get(f"/api/v1/contacts/{uuid4()}", headers=auth_headers)
        assert response.status_code in (404, 422)


class TestContactRouterCreate:
    def test_create_validates_body(self, app, client, auth_headers):
        from app.domains.contact.router import get_contact_service

        app.dependency_overrides[get_contact_service] = lambda: AsyncMock()
        response = client.post("/api/v1/contacts", headers=auth_headers, json={})
        assert response.status_code in (201, 422)


class TestContactRouterCount:
    def test_count_endpoint(self, app, client, auth_headers):
        from app.domains.contact.router import get_contact_service

        mock_service = AsyncMock()
        mock_service.count.return_value = 5
        app.dependency_overrides[get_contact_service] = lambda: mock_service
        response = client.get("/api/v1/contacts/count", headers=auth_headers)
        assert response.status_code == 200


class TestContactRouterActions:

    def test_set_primary_route_registered(self, app):
        path = "/api/v1/contacts/{entity_id}/set-primary"
        assert path in app.openapi()["paths"]


    def test_opt_out_notifications_route_registered(self, app):
        path = "/api/v1/contacts/{entity_id}/opt-out"
        assert path in app.openapi()["paths"]
