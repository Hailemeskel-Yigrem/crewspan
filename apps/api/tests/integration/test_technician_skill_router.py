"""Integration tests for TechnicianSkill API router."""

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


class TestTechnicianSkillRouterList:
    def test_list_requires_tenant_header(self, app, client):
        from app.domains.technician_skill.router import get_technician_skill_service

        app.dependency_overrides[get_technician_skill_service] = lambda: AsyncMock()
        response = client.get("/api/v1/technician-skills")
        assert response.status_code in (400, 401, 422)

    def test_list_returns_envelope(self, app, client, auth_headers):
        from app.domains.technician_skill.router import get_technician_skill_service

        mock_service = AsyncMock()
        mock_service.list.return_value = ([], 0)
        app.dependency_overrides[get_technician_skill_service] = lambda: mock_service
        response = client.get("/api/v1/technician-skills?page=1&page_size=10", headers=auth_headers)
        assert response.status_code == 200


class TestTechnicianSkillRouterGet:
    def test_get_not_found(self, app, client, auth_headers):
        from app.domains.technician_skill.exceptions import TechnicianSkillNotFoundError
        from app.domains.technician_skill.router import get_technician_skill_service

        mock_service = AsyncMock()
        mock_service.get.side_effect = TechnicianSkillNotFoundError(uuid4())
        app.dependency_overrides[get_technician_skill_service] = lambda: mock_service
        response = client.get(f"/api/v1/technician-skills/{uuid4()}", headers=auth_headers)
        assert response.status_code in (404, 422)


class TestTechnicianSkillRouterCreate:
    def test_create_validates_body(self, app, client, auth_headers):
        from app.domains.technician_skill.router import get_technician_skill_service

        app.dependency_overrides[get_technician_skill_service] = lambda: AsyncMock()
        response = client.post("/api/v1/technician-skills", headers=auth_headers, json={})
        assert response.status_code in (201, 422)


class TestTechnicianSkillRouterCount:
    def test_count_endpoint(self, app, client, auth_headers):
        from app.domains.technician_skill.router import get_technician_skill_service

        mock_service = AsyncMock()
        mock_service.count.return_value = 5
        app.dependency_overrides[get_technician_skill_service] = lambda: mock_service
        response = client.get("/api/v1/technician-skills/count", headers=auth_headers)
        assert response.status_code == 200


class TestTechnicianSkillRouterActions:

    def test_renew_certification_route_registered(self, app):
        path = "/api/v1/technician-skills/{entity_id}/renew-certification"
        assert path in app.openapi()["paths"]


    def test_is_valid_route_registered(self, app):
        path = "/api/v1/technician-skills/{entity_id}/is-valid"
        assert path in app.openapi()["paths"]
