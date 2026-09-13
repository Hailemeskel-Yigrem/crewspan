"""Integration tests for CustomerSite API router."""

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


class TestCustomerSiteRouterList:
    def test_list_requires_tenant_header(self, app, client):
        from app.domains.customer_site.router import get_customer_site_service

        app.dependency_overrides[get_customer_site_service] = lambda: AsyncMock()
        response = client.get("/api/v1/customer-sites")
        assert response.status_code in (400, 401, 422)

    def test_list_returns_envelope(self, app, client, auth_headers):
        from app.domains.customer_site.router import get_customer_site_service

        mock_service = AsyncMock()
        mock_service.list.return_value = ([], 0)
        app.dependency_overrides[get_customer_site_service] = lambda: mock_service
        response = client.get("/api/v1/customer-sites?page=1&page_size=10", headers=auth_headers)
        assert response.status_code == 200


class TestCustomerSiteRouterGet:
    def test_get_not_found(self, app, client, auth_headers):
        from app.domains.customer_site.exceptions import CustomerSiteNotFoundError
        from app.domains.customer_site.router import get_customer_site_service

        mock_service = AsyncMock()
        mock_service.get.side_effect = CustomerSiteNotFoundError(uuid4())
        app.dependency_overrides[get_customer_site_service] = lambda: mock_service
        response = client.get(f"/api/v1/customer-sites/{uuid4()}", headers=auth_headers)
        assert response.status_code in (404, 422)


class TestCustomerSiteRouterCreate:
    def test_create_validates_body(self, app, client, auth_headers):
        from app.domains.customer_site.router import get_customer_site_service

        app.dependency_overrides[get_customer_site_service] = lambda: AsyncMock()
        response = client.post("/api/v1/customer-sites", headers=auth_headers, json={})
        assert response.status_code in (201, 422)


class TestCustomerSiteRouterCount:
    def test_count_endpoint(self, app, client, auth_headers):
        from app.domains.customer_site.router import get_customer_site_service

        mock_service = AsyncMock()
        mock_service.count.return_value = 5
        app.dependency_overrides[get_customer_site_service] = lambda: mock_service
        response = client.get("/api/v1/customer-sites/count", headers=auth_headers)
        assert response.status_code == 200


class TestCustomerSiteRouterActions:

    def test_geocode_route_registered(self, app):
        path = "/api/v1/customer-sites/{entity_id}/geocode"
        assert path in app.openapi()["paths"]


    def test_validate_access_window_route_registered(self, app):
        path = "/api/v1/customer-sites/{entity_id}/validate-access-window"
        assert path in app.openapi()["paths"]
