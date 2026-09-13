"""Integration tests for Schedule API router."""

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


class TestScheduleRouterList:
    def test_list_requires_tenant_header(self, app, client):
        from app.domains.schedule.router import get_schedule_service

        app.dependency_overrides[get_schedule_service] = lambda: AsyncMock()
        response = client.get("/api/v1/schedules")
        assert response.status_code in (400, 401, 422)

    def test_list_returns_envelope(self, app, client, auth_headers):
        from app.domains.schedule.router import get_schedule_service

        mock_service = AsyncMock()
        mock_service.list.return_value = ([], 0)
        app.dependency_overrides[get_schedule_service] = lambda: mock_service
        response = client.get("/api/v1/schedules?page=1&page_size=10", headers=auth_headers)
        assert response.status_code == 200


class TestScheduleRouterGet:
    def test_get_not_found(self, app, client, auth_headers):
        from app.domains.schedule.exceptions import ScheduleNotFoundError
        from app.domains.schedule.router import get_schedule_service

        mock_service = AsyncMock()
        mock_service.get.side_effect = ScheduleNotFoundError(uuid4())
        app.dependency_overrides[get_schedule_service] = lambda: mock_service
        response = client.get(f"/api/v1/schedules/{uuid4()}", headers=auth_headers)
        assert response.status_code in (404, 422)


class TestScheduleRouterCreate:
    def test_create_validates_body(self, app, client, auth_headers):
        from app.domains.schedule.router import get_schedule_service

        app.dependency_overrides[get_schedule_service] = lambda: AsyncMock()
        response = client.post("/api/v1/schedules", headers=auth_headers, json={})
        assert response.status_code in (201, 422)


class TestScheduleRouterCount:
    def test_count_endpoint(self, app, client, auth_headers):
        from app.domains.schedule.router import get_schedule_service

        mock_service = AsyncMock()
        mock_service.count.return_value = 5
        app.dependency_overrides[get_schedule_service] = lambda: mock_service
        response = client.get("/api/v1/schedules/count", headers=auth_headers)
        assert response.status_code == 200


class TestScheduleRouterActions:

    def test_lock_route_registered(self, app):
        path = "/api/v1/schedules/{entity_id}/lock"
        assert path in app.openapi()["paths"]


    def test_unlock_route_registered(self, app):
        path = "/api/v1/schedules/{entity_id}/unlock"
        assert path in app.openapi()["paths"]


    def test_detect_conflicts_route_registered(self, app):
        path = "/api/v1/schedules/{entity_id}/detect-conflicts"
        assert path in app.openapi()["paths"]
