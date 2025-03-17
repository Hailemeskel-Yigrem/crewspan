"""Unit tests for ReportingService."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.services.reporting_service import ReportingService, DashboardMetrics


@pytest.fixture
def reporting_service():
    return ReportingService(AsyncMock())


def test_dashboard_metrics_dataclass():
    m = DashboardMetrics(open_work_orders=5, active_technicians=2)
    assert m.open_work_orders == 5
