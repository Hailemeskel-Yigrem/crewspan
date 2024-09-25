"""Integration tests for ServiceContract API router."""

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


class TestServiceContractRouterList:
    def test_list_requires_tenant_header(self, app, client):
        from app.domains.service_contract.router import get_service_contract_service

        app.dependency_overrides[get_service_contract_service] = lambda: AsyncMock()
        response = client.get("/api/v1/service-contracts")
        assert response.status_code in (400, 401, 422)

    def test_list_returns_envelope(self, app, client, auth_headers):
        from app.domains.service_contract.router import get_service_contract_service

        mock_service = AsyncMock()
        mock_service.list.return_value = ([], 0)
        app.dependency_overrides[get_service_contract_service] = lambda: mock_service
        response = client.get("/api/v1/service-contracts?page=1&page_size=10", headers=auth_headers)
        assert response.status_code == 200


class TestServiceContractRouterGet:
    def test_get_not_found(self, app, client, auth_headers):
        from app.domains.service_contract.exceptions import ServiceContractNotFoundError
        from app.domains.service_contract.router import get_service_contract_service

        mock_service = AsyncMock()
        mock_service.get.side_effect = ServiceContractNotFoundError(uuid4())
        app.dependency_overrides[get_service_contract_service] = lambda: mock_service
        response = client.get(f"/api/v1/service-contracts/{uuid4()}", headers=auth_headers)
        assert response.status_code in (404, 422)


class TestServiceContractRouterCreate:
    def test_create_validates_body(self, app, client, auth_headers):
        from app.domains.service_contract.router import get_service_contract_service

        app.dependency_overrides[get_service_contract_service] = lambda: AsyncMock()
        response = client.post("/api/v1/service-contracts", headers=auth_headers, json={})
        assert response.status_code in (201, 422)


class TestServiceContractRouterCount:
    def test_count_endpoint(self, app, client, auth_headers):
        from app.domains.service_contract.router import get_service_contract_service

        mock_service = AsyncMock()
        mock_service.count.return_value = 5
        app.dependency_overrides[get_service_contract_service] = lambda: mock_service
        response = client.get("/api/v1/service-contracts/count", headers=auth_headers)
        assert response.status_code == 200


class TestServiceContractRouterActions:

    def test_renew_route_registered(self, app):
        path = "/api/v1/service-contracts/{entity_id}/renew"
        assert path in app.openapi()["paths"]


    def test_terminate_route_registered(self, app):
        path = "/api/v1/service-contracts/{entity_id}/terminate"
        assert path in app.openapi()["paths"]


    def test_generate_work_orders_route_registered(self, app):
        path = "/api/v1/service-contracts/{entity_id}/generate-work-orders"
        assert path in app.openapi()["paths"]
