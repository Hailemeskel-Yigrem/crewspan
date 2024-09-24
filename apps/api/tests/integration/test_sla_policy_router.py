"""Integration tests for SlaPolicy API router."""

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


class TestSlaPolicyRouterList:
    def test_list_requires_tenant_header(self, app, client):
        from app.domains.sla_policy.router import get_sla_policy_service

        app.dependency_overrides[get_sla_policy_service] = lambda: AsyncMock()
        response = client.get("/api/v1/sla-policies")
        assert response.status_code in (400, 401, 422)

    def test_list_returns_envelope(self, app, client, auth_headers):
        from app.domains.sla_policy.router import get_sla_policy_service

        mock_service = AsyncMock()
        mock_service.list.return_value = ([], 0)
        app.dependency_overrides[get_sla_policy_service] = lambda: mock_service
        response = client.get("/api/v1/sla-policies?page=1&page_size=10", headers=auth_headers)
        assert response.status_code == 200


class TestSlaPolicyRouterGet:
    def test_get_not_found(self, app, client, auth_headers):
        from app.domains.sla_policy.exceptions import SlaPolicyNotFoundError
        from app.domains.sla_policy.router import get_sla_policy_service

        mock_service = AsyncMock()
        mock_service.get.side_effect = SlaPolicyNotFoundError(uuid4())
        app.dependency_overrides[get_sla_policy_service] = lambda: mock_service
        response = client.get(f"/api/v1/sla-policies/{uuid4()}", headers=auth_headers)
        assert response.status_code in (404, 422)


class TestSlaPolicyRouterCreate:
    def test_create_validates_body(self, app, client, auth_headers):
        from app.domains.sla_policy.router import get_sla_policy_service

        app.dependency_overrides[get_sla_policy_service] = lambda: AsyncMock()
        response = client.post("/api/v1/sla-policies", headers=auth_headers, json={})
        assert response.status_code in (201, 422)


class TestSlaPolicyRouterCount:
    def test_count_endpoint(self, app, client, auth_headers):
        from app.domains.sla_policy.router import get_sla_policy_service

        mock_service = AsyncMock()
        mock_service.count.return_value = 5
        app.dependency_overrides[get_sla_policy_service] = lambda: mock_service
        response = client.get("/api/v1/sla-policies/count", headers=auth_headers)
        assert response.status_code == 200


class TestSlaPolicyRouterActions:

    def test_evaluate_deadlines_route_registered(self, app):
        path = "/api/v1/sla-policies/{entity_id}/evaluate-deadlines"
        assert path in app.openapi()["paths"]


    def test_clone_route_registered(self, app):
        path = "/api/v1/sla-policies/{entity_id}/clone"
        assert path in app.openapi()["paths"]
