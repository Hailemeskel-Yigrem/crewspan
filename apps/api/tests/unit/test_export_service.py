"""Unit tests for ExportService."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.services.export_service import ExportFormat, ExportService


@pytest.fixture
def export_service():
    session = AsyncMock()
    svc = ExportService(session)
    svc._work_orders = AsyncMock()
    svc._work_orders.list = AsyncMock(return_value=([], 0))
    return svc


@pytest.mark.asyncio
async def test_export_work_orders_csv(export_service):
    result = await export_service.export_work_orders(uuid4(), fmt=ExportFormat.CSV)
    assert result.format == ExportFormat.CSV
    assert result.row_count == 0
