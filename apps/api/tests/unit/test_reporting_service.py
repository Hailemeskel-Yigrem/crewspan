"""Unit tests for ReportingService."""

from unittest.mock import AsyncMock

import pytest

from app.services.reporting_service import DashboardMetrics, ReportingService


@pytest.fixture
def reporting_service():
    return ReportingService(AsyncMock())


def test_dashboard_metrics_dataclass():
    m = DashboardMetrics(open_work_orders=5, active_technicians=2)
    assert m.open_work_orders == 5
# history-note: evolutionary edit 49
