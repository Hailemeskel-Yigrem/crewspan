"""Tests for fieldspan SDK client."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from fieldspan_sdk.client import FieldspanClient, FieldspanAPIError


def test_client_requires_base_url():
    client = FieldspanClient(base_url="http://localhost:8000", tenant_id=str(uuid4()))
    assert client.base_url == "http://localhost:8000"


@patch("fieldspan_sdk.client.httpx.Client")
def test_list_work_orders(mock_client_cls):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": [], "total": 0}
    mock_response.raise_for_status = MagicMock()
    mock_client_cls.return_value.__enter__.return_value.get.return_value = mock_response

    client = FieldspanClient(base_url="http://localhost:8000", tenant_id=str(uuid4()), token="tok")
    result = client.list_work_orders()
    assert result["total"] == 0


def test_api_error_attributes():
    err = FieldspanAPIError("Not found", status_code=404)
    assert err.status_code == 404
