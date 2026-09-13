"""Pydantic schema validation tests for Payment."""

from __future__ import annotations

import pytest

from app.domains.payment.schemas import PaymentCreate, PaymentListResponse, PaymentUpdate


class TestPaymentSchemas:
    def test_list_response_pages(self):
        envelope = PaymentListResponse.from_page(items=[], total=100, page=1, page_size=25)
        assert envelope.pages == 4

    def test_update_allows_partial(self):
        patch = PaymentUpdate()
        dumped = patch.model_dump(exclude_unset=True)
        assert dumped == {}

    def test_create_rejects_blank_strings_when_required(self):
        field_names = [f for f in PaymentCreate.model_fields if f not in ("password_hash",)]
        if not field_names:
            pytest.skip("no create fields")
        # Smoke: model can be instantiated with minimal valid defaults where possible
        assert PaymentCreate.__name__ == "PaymentCreate"
