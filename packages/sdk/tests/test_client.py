"""Tests for crewspan SDK client."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

from crewspan_sdk.client import CrewspanAPIError, CrewspanClient


def test_client_requires_base_url():
    client = CrewspanClient(base_url="http://localhost:8000", tenant_id=str(uuid4()))
    assert client.base_url == "http://localhost:8000"


@patch("crewspan_sdk.client.httpx.Client")
def test_list_work_orders(mock_client_cls):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": [], "total": 0}
    mock_response.raise_for_status = MagicMock()
    mock_client_cls.return_value.__enter__.return_value.request.return_value = mock_response

    client = CrewspanClient(base_url="http://localhost:8000", tenant_id=str(uuid4()), token="tok")
    result = client.list_work_orders()
    assert result["total"] == 0


def test_api_error_attributes():
    err = CrewspanAPIError("Not found", status_code=404)
    assert err.status_code == 404
