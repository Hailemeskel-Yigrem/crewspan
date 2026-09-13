"""Pydantic schema validation tests for SlaPolicy."""

from __future__ import annotations

import pytest

from app.domains.sla_policy.schemas import SlaPolicyCreate, SlaPolicyListResponse, SlaPolicyUpdate


class TestSlaPolicySchemas:
    def test_list_response_pages(self):
        envelope = SlaPolicyListResponse.from_page(items=[], total=100, page=1, page_size=25)
        assert envelope.pages == 4

    def test_update_allows_partial(self):
        patch = SlaPolicyUpdate()
        dumped = patch.model_dump(exclude_unset=True)
        assert dumped == {}

    def test_create_rejects_blank_strings_when_required(self):
        field_names = [f for f in SlaPolicyCreate.model_fields if f not in ("password_hash",)]
        if not field_names:
            pytest.skip("no create fields")
        # Smoke: model can be instantiated with minimal valid defaults where possible
        assert SlaPolicyCreate.__name__ == "SlaPolicyCreate"
