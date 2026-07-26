"""Generate Crewspan test suites for API and web applications."""

from __future__ import annotations

import textwrap
from pathlib import Path

from tools.codegen.domains import DOMAINS
from tools.codegen.test_templates import (
    generate_component_test,
    generate_domain_api_test,
    generate_domain_type_test,
    generate_hook_test,
    generate_repository_unit_test,
    generate_router_integration_test,
    generate_schemas_unit_test,
    generate_service_unit_test,
    generate_util_test,
)

COMPONENT_NAMES = [
    "StatusBadge", "DataTable", "FormField", "MetricCard", "EmptyState",
    "ConfirmDialog", "LoadingSpinner", "DateRangePicker", "TechnicianAvatar",
    "WorkOrderCard", "PageHeader", "Modal", "Layout", "Sidebar", "ErrorBoundary",
]

HOOK_NAMES = ["useDebounce", "usePagination", "useWorkOrders", "useAuth"]
UTIL_NAMES = ["formatting", "dates", "statusColors"]

PAGE_NAMES = [
    "DashboardPage", "WorkOrdersPage", "SchedulePage", "TechniciansPage",
    "CustomersPage", "InventoryPage", "InvoicesPage", "ReportsPage",
    "SettingsPage", "AuditLogPage", "NotificationsPage", "SlaPoliciesPage",
]


def _write(path: Path, content: str) -> int:
    from tools.codegen.api_templates import finalize_source

    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == ".py":
        normalized = finalize_source(content)
    else:
        normalized = textwrap.dedent(content).rstrip() + "\n"
    path.write_text(normalized, encoding="utf-8")
    return len(normalized.splitlines())


def _conftest_api() -> str:
    return """\"\"\"Shared pytest fixtures for Crewspan API tests.\"\"\"

from __future__ import annotations

from uuid import uuid4

import pytest


@pytest.fixture
def tenant_id():
    return uuid4()


@pytest.fixture
def user_id():
    return uuid4()
"""


def _conftest_web() -> str:
    return """import '@testing-library/jest-dom';
import { vi } from 'vitest';

vi.stubGlobal('matchMedia', vi.fn().mockImplementation((query: string) => ({
  matches: false,
  media: query,
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
})));
"""


def _page_test(page_name: str) -> str:
    return f"""import {{ render, screen }} from '@testing-library/react';
import {{ MemoryRouter }} from 'react-router-dom';
import {{ describe, it, expect, vi }} from 'vitest';
import {{ {page_name} }} from '../{page_name}';

vi.mock('../hooks/useAuth', () => ({{
  useAuth: () => ({{ isAuthenticated: true, user: {{ fullName: 'Test User' }}, logout: vi.fn() }}),
}}));

describe('{page_name}', () => {{
  it('renders page heading or content', () => {{
    render(
      <MemoryRouter>
        <{page_name} />
      </MemoryRouter>,
    );
    expect(document.querySelector('.page')).toBeTruthy();
  }});
}});
"""


def _package_common_test() -> str:
    return """\"\"\"Tests for crewspan_common package.\"\"\"

from crewspan_common.errors import CrewspanError, NotFoundError
from crewspan_common.logging import get_logger


def test_relay_ops_error_message():
    err = CrewspanError("test error", code="test_code")
    assert err.message == "test error"
    assert err.code == "test_code"


def test_not_found_error():
    err = NotFoundError(resource="work_order", identifier="abc-123")
    assert err.resource == "work_order"
    assert "abc-123" in err.message


def test_get_logger_returns_logger():
    logger = get_logger("test")
    assert logger is not None
"""


def _package_sdk_test() -> str:
    return """\"\"\"Tests for crewspan SDK client.\"\"\"

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from crewspan_sdk.client import CrewspanClient, CrewspanAPIError


def test_client_requires_base_url():
    client = CrewspanClient(base_url="http://localhost:8000", tenant_id=str(uuid4()))
    assert client.base_url == "http://localhost:8000"


@patch("crewspan_sdk.client.httpx.Client")
def test_list_work_orders(mock_client_cls):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": [], "total": 0}
    mock_response.raise_for_status = MagicMock()
    mock_client_cls.return_value.__enter__.return_value.get.return_value = mock_response

    client = CrewspanClient(base_url="http://localhost:8000", tenant_id=str(uuid4()), token="tok")
    result = client.list_work_orders()
    assert result["total"] == 0


def test_api_error_attributes():
    err = CrewspanAPIError("Not found", status_code=404)
    assert err.status_code == 404
"""


def _api_health_test() -> str:
    return """\"\"\"Smoke tests for API health endpoints.\"\"\"

from fastapi.testclient import TestClient

from app.main import create_app


def test_health_endpoint():
    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ready_endpoint():
    client = TestClient(create_app())
    response = client.get("/ready")
    assert response.status_code == 200
"""


def _core_validators_test() -> str:
    return """\"\"\"Tests for shared core validators.\"\"\"

from decimal import Decimal

import pytest

from app.core.errors import ValidationAppError
from app.core.validators import (
    clamp_page_size,
    validate_email,
    validate_enum,
    validate_positive_decimal,
)


def test_validate_email_normalizes():
    assert validate_email("  User@Example.COM ") == "user@example.com"


def test_validate_email_rejects_invalid():
    with pytest.raises(ValidationAppError):
        validate_email("not-an-email")


def test_validate_enum_allowed():
    assert validate_enum("draft", {"draft", "active"}, field="status") == "draft"


def test_validate_positive_decimal():
    assert validate_positive_decimal(Decimal("10.00"), field="amount") == Decimal("10.00")


def test_clamp_page_size():
    assert clamp_page_size(999, maximum=200) == 200
"""


def _auth_service_test() -> str:
    return """\"\"\"Unit tests for AuthService.\"\"\"

from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.errors import AuthorizationError
from app.services.auth_service import AuthService


@pytest.fixture
def auth_service():
    session = AsyncMock()
    return AuthService(session)


def test_authenticate_rejects_short_password(auth_service):
    with pytest.raises(Exception):
        import asyncio
        asyncio.get_event_loop().run_until_complete(
            auth_service.authenticate(email="a@b.com", password="short", tenant_id=uuid4())
        )
"""


def _reporting_service_test() -> str:
    return """\"\"\"Unit tests for ReportingService.\"\"\"

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
"""


def _search_service_test() -> str:
    return """\"\"\"Unit tests for SearchService.\"\"\"

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.services.search_service import SearchService


@pytest.fixture
def search_service():
    return SearchService(AsyncMock())


@pytest.mark.asyncio
async def test_search_returns_empty_for_short_query(search_service):
    hits = await search_service.search(uuid4(), "a")
    assert hits == []
"""


def _export_service_test() -> str:
    return """\"\"\"Unit tests for ExportService.\"\"\"

from unittest.mock import AsyncMock, MagicMock
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
"""


def generate_tests_tree(root: Path) -> dict[str, int]:
    """Write pytest and vitest test trees under *root*."""
    stats: dict[str, int] = {}

    def record(base: Path, rel: str, content: str) -> None:
        stats[str(base.relative_to(root) / rel).replace("\\\\", "/")] = _write(base / rel, content)

    api_tests = root / "apps" / "api" / "tests"
    record(api_tests, "conftest.py", _conftest_api())
    record(api_tests, "test_health.py", _api_health_test())
    record(api_tests, "unit/test_core_validators.py", _core_validators_test())
    record(api_tests, "unit/test_reporting_service.py", _reporting_service_test())
    record(api_tests, "unit/test_search_service.py", _search_service_test())
    record(api_tests, "unit/test_export_service.py", _export_service_test())

    for domain in DOMAINS:
        record(api_tests, f"unit/test_{domain.snake}_service.py", generate_service_unit_test(domain))
        record(api_tests, f"unit/test_{domain.snake}_repository.py", generate_repository_unit_test(domain))
        record(api_tests, f"unit/test_{domain.snake}_schemas.py", generate_schemas_unit_test(domain))
        record(api_tests, f"integration/test_{domain.snake}_router.py", generate_router_integration_test(domain))

    web_root = root / "apps" / "web"
    record(web_root, "src/test/setup.ts", _conftest_web())

    for comp in COMPONENT_NAMES:
        record(web_root, f"src/components/{comp}.test.tsx", generate_component_test(comp))

    for hook in HOOK_NAMES:
        record(web_root, f"src/hooks/{hook}.test.ts", generate_hook_test(hook))

    for util in UTIL_NAMES:
        record(web_root, f"src/utils/{util}.test.ts", generate_util_test(util))

    for page in PAGE_NAMES:
        record(web_root, f"src/pages/{page}.test.tsx", _page_test(page))

    # Cover a representative subset of typed clients instead of one test per domain.
    for domain in DOMAINS:
        if domain.snake in {
            "work_order",
            "technician",
            "customer",
            "invoice",
            "schedule",
            "inventory_item",
            "sla_policy",
            "webhook",
        }:
            record(web_root, f"src/api/{domain.snake}.test.ts", generate_domain_api_test(domain))

    record(web_root, "src/auth/AuthContext.test.tsx", """import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { AuthProvider, useAuthContext } from './AuthContext';

vi.mock('../api/client', () => ({
  login: vi.fn().mockResolvedValue({ token: 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyLTEifQ.sig' }),
}));

describe('AuthContext', () => {
  it('starts unauthenticated', () => {
    localStorage.clear();
    const { result } = renderHook(() => useAuthContext(), { wrapper: AuthProvider });
    expect(result.current.isAuthenticated).toBe(false);
  });
});
""")

    record(web_root, "src/api/client.test.ts", """import { describe, it, expect, vi, beforeEach } from 'vitest';
import { apiFetch, ApiError } from './client';

describe('apiFetch', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn());
  });

  it('throws ApiError on failure', async () => {
    vi.mocked(fetch).mockResolvedValue({ ok: false, status: 404, statusText: 'Not Found', json: () => Promise.resolve({ message: 'Missing' }) } as Response);
    await expect(apiFetch('/test')).rejects.toThrow(ApiError);
  });
});
""")

    pkg_common = root / "packages" / "common"
    record(pkg_common, "tests/test_common.py", _package_common_test())

    pkg_sdk = root / "packages" / "sdk"
    record(pkg_sdk, "tests/test_client.py", _package_sdk_test())

    worker_tests = root / "apps" / "worker" / "tests"
    record(worker_tests, "test_notifications.py", """\"\"\"Worker notification job tests.\"\"\"

from worker.jobs.notifications import send_email, process_pending_batch


def test_send_email_returns_status():
    result = send_email("notif-id", tenant_id="tenant-1")
    assert result["status"] == "sent"


def test_process_pending_batch():
    result = process_pending_batch(limit=10)
    assert "processed" in result
""")

    record(worker_tests, "test_scheduling.py", """from worker.jobs.scheduling import send_upcoming_appointment_reminders


def test_reminders_returns_count():
    result = send_upcoming_appointment_reminders(horizon_hours=24)
    assert "reminders_sent" in result
""")

    record(worker_tests, "test_invoicing.py", """from worker.jobs.invoicing import generate_from_work_order


def test_generate_invoice():
    result = generate_from_work_order("wo-123", tenant_id="t-1")
    assert result["invoice_number"].startswith("INV-")
""")

    record(worker_tests, "test_webhooks.py", """from worker.jobs.webhooks import _sign_payload


def test_sign_payload_deterministic():
    sig1 = _sign_payload("secret", b"payload")
    sig2 = _sign_payload("secret", b"payload")
    assert sig1 == sig2
    assert len(sig1) == 64
""")

    record(worker_tests, "test_reports.py", """from worker.jobs.reports import export_work_orders_csv


def test_export_creates_file(tmp_path, monkeypatch):
    monkeypatch.setattr("worker.config.settings.report_export_dir", str(tmp_path))
    result = export_work_orders_csv(
        tenant_id="t-1", start_date="2024-01-01", end_date="2024-01-31", requested_by_id="u-1"
    )
    assert result["format"] == "csv"
""")

    return stats


def print_generation_summary(stats: dict[str, int]) -> None:
    total_lines = sum(stats.values())
    print(f"Generated {len(stats)} test files, ~{total_lines:,} lines")
    for rel, lines in sorted(stats.items()):
        print(f"  {rel}: {lines} lines")


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[2]
    print_generation_summary(generate_tests_tree(repo_root))
# history-note: evolutionary edit 2
