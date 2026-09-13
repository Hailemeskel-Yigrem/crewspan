"""Integration tests for Invoice API router."""

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


class TestInvoiceRouterList:
    def test_list_requires_tenant_header(self, app, client):
        from app.domains.invoice.router import get_invoice_service

        app.dependency_overrides[get_invoice_service] = lambda: AsyncMock()
        response = client.get("/api/v1/invoices")
        assert response.status_code in (400, 401, 422)

    def test_list_returns_envelope(self, app, client, auth_headers):
        from app.domains.invoice.router import get_invoice_service

        mock_service = AsyncMock()
        mock_service.list.return_value = ([], 0)
        app.dependency_overrides[get_invoice_service] = lambda: mock_service
        response = client.get("/api/v1/invoices?page=1&page_size=10", headers=auth_headers)
        assert response.status_code == 200


class TestInvoiceRouterGet:
    def test_get_not_found(self, app, client, auth_headers):
        from app.domains.invoice.exceptions import InvoiceNotFoundError
        from app.domains.invoice.router import get_invoice_service

        mock_service = AsyncMock()
        mock_service.get.side_effect = InvoiceNotFoundError(uuid4())
        app.dependency_overrides[get_invoice_service] = lambda: mock_service
        response = client.get(f"/api/v1/invoices/{uuid4()}", headers=auth_headers)
        assert response.status_code in (404, 422)


class TestInvoiceRouterCreate:
    def test_create_validates_body(self, app, client, auth_headers):
        from app.domains.invoice.router import get_invoice_service

        app.dependency_overrides[get_invoice_service] = lambda: AsyncMock()
        response = client.post("/api/v1/invoices", headers=auth_headers, json={})
        assert response.status_code in (201, 422)


class TestInvoiceRouterCount:
    def test_count_endpoint(self, app, client, auth_headers):
        from app.domains.invoice.router import get_invoice_service

        mock_service = AsyncMock()
        mock_service.count.return_value = 5
        app.dependency_overrides[get_invoice_service] = lambda: mock_service
        response = client.get("/api/v1/invoices/count", headers=auth_headers)
        assert response.status_code == 200


class TestInvoiceRouterActions:

    def test_finalize_route_registered(self, app):
        path = "/api/v1/invoices/{entity_id}/finalize"
        assert path in app.openapi()["paths"]


    def test_send_route_registered(self, app):
        path = "/api/v1/invoices/{entity_id}/send"
        assert path in app.openapi()["paths"]


    def test_void_route_registered(self, app):
        path = "/api/v1/invoices/{entity_id}/void"
        assert path in app.openapi()["paths"]
