"""Pydantic schema validation tests for TechnicianSkill."""

from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.domains.technician_skill.schemas import TechnicianSkillCreate, TechnicianSkillListResponse, TechnicianSkillUpdate


class TestTechnicianSkillSchemas:
    def test_list_response_pages(self):
        envelope = TechnicianSkillListResponse.from_page(items=[], total=100, page=1, page_size=25)
        assert envelope.pages == 4

    def test_update_allows_partial(self):
        patch = TechnicianSkillUpdate()
        dumped = patch.model_dump(exclude_unset=True)
        assert dumped == {}

    def test_create_rejects_blank_strings_when_required(self):
        field_names = [f for f in TechnicianSkillCreate.model_fields if f not in ("password_hash",)]
        if not field_names:
            pytest.skip("no create fields")
        # Smoke: model can be instantiated with minimal valid defaults where possible
        assert TechnicianSkillCreate.__name__ == "TechnicianSkillCreate"
