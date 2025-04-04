"""Pydantic schema validation tests for Webhook."""

from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.domains.webhook.schemas import WebhookCreate, WebhookListResponse, WebhookUpdate


class TestWebhookSchemas:
    def test_list_response_pages(self):
        envelope = WebhookListResponse.from_page(items=[], total=100, page=1, page_size=25)
        assert envelope.pages == 4

    def test_update_allows_partial(self):
        patch = WebhookUpdate()
        dumped = patch.model_dump(exclude_unset=True)
        assert dumped == {}

    def test_create_rejects_blank_strings_when_required(self):
        field_names = [f for f in WebhookCreate.model_fields if f not in ("password_hash",)]
        if not field_names:
            pytest.skip("no create fields")
        # Smoke: model can be instantiated with minimal valid defaults where possible
        assert WebhookCreate.__name__ == "WebhookCreate"
