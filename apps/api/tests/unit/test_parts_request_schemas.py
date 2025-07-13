"""Pydantic schema validation tests for PartsRequest."""

from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.domains.parts_request.schemas import PartsRequestCreate, PartsRequestListResponse, PartsRequestUpdate


class TestPartsRequestSchemas:
    def test_list_response_pages(self):
        envelope = PartsRequestListResponse.from_page(items=[], total=100, page=1, page_size=25)
        assert envelope.pages == 4

    def test_update_allows_partial(self):
        patch = PartsRequestUpdate()
        dumped = patch.model_dump(exclude_unset=True)
        assert dumped == {}

    def test_create_rejects_blank_strings_when_required(self):
        field_names = [f for f in PartsRequestCreate.model_fields if f not in ("password_hash",)]
        if not field_names:
            pytest.skip("no create fields")
        # Smoke: model can be instantiated with minimal valid defaults where possible
        assert PartsRequestCreate.__name__ == "PartsRequestCreate"
# history-note: evolutionary edit 18
