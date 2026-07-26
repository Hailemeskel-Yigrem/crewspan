"""Unit tests for TechnicianSkill service layer."""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.domains.technician_skill.exceptions import TechnicianSkillNotFoundError, TechnicianSkillValidationError
from app.domains.technician_skill.service import TechnicianSkillService


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    entity = MagicMock()
    entity.id = uuid4()
    entity.tenant_id = uuid4()
    entity.technician_id = uuid4()
    entity.skill_code = "sample-skill_code"
    entity.skill_name = "sample-skill_name"
    entity.proficiency_level = 1
    entity.certified_at = date.today()
    entity.expires_at = date.today()
    entity.created_at = datetime.now(timezone.utc)
    entity.updated_at = datetime.now(timezone.utc)
    entity.deleted_at = None
    repo.get_by_id.return_value = entity
    repo.list.return_value = ([entity], 1)
    repo.count.return_value = 1
    repo.exists.return_value = True
    repo.create.return_value = entity
    repo.update.return_value = entity
    return repo


@pytest.fixture
def service(mock_repo):
    return TechnicianSkillService(repository=mock_repo)


class TestTechnicianSkillServiceList:
    @pytest.mark.asyncio
    async def test_list_returns_paginated(self, service, mock_repo):
        items, total = await service.list(tenant_id=uuid4(), page=1, page_size=10)
        assert total == 1
        assert len(items) == 1
        mock_repo.list.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_rejects_invalid_page(self, service):
        with pytest.raises(TechnicianSkillValidationError):
            await service.list(tenant_id=uuid4(), page=0, page_size=10)



class TestTechnicianSkillServiceGet:
    @pytest.mark.asyncio
    async def test_get_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(TechnicianSkillNotFoundError):
            await service.get(uuid4(), tenant_id=uuid4())

    @pytest.mark.asyncio
    async def test_get_returns_read_model(self, service):
        result = await service.get(uuid4(), tenant_id=uuid4())
        assert result is not None


class TestTechnicianSkillServiceCount:
    @pytest.mark.asyncio
    async def test_count_delegates(self, service, mock_repo):
        total = await service.count(tenant_id=uuid4())
        assert total == 1
        mock_repo.count.assert_awaited_once()


class TestTechnicianSkillServiceExists:
    @pytest.mark.asyncio
    async def test_exists_true(self, service):
        assert await service.exists(uuid4(), tenant_id=uuid4()) is True


class TestTechnicianSkillServiceDelete:
    @pytest.mark.asyncio
    async def test_delete_soft_deletes(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        await service.delete(entity.id, tenant_id=uuid4())
        mock_repo.soft_delete.assert_awaited_once()


class TestTechnicianSkillDomainMethods:
    @pytest.mark.asyncio
    async def test_renew_certification_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(TechnicianSkillNotFoundError):
            await service.renew_certification(entity_id=uuid4(), tenant_id=uuid4(), expires_at=None)

    @pytest.mark.asyncio
    async def test_renew_certification_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.renew_certification(entity_id=entity.id, tenant_id=uuid4(), expires_at=None)
        assert result is not None

    @pytest.mark.asyncio
    async def test_is_valid_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(TechnicianSkillNotFoundError):
            await service.is_valid(entity_id=uuid4(), tenant_id=uuid4())

    @pytest.mark.asyncio
    async def test_is_valid_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.is_valid(entity_id=entity.id, tenant_id=uuid4())
        assert result is not None
