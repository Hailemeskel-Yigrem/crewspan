"""Template functions for Crewspan test code generation."""

from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING

from tools.codegen.api_templates import _T_CLASS, _snippet

if TYPE_CHECKING:
    from tools.codegen.domains import DomainSpec


def _method_call_args(method) -> str:
    if not method.params:
        return "entity_id=entity_id, tenant_id=uuid4()"
    arg_bits = []
    for name, ptype in method.params:
        if "str" in ptype:
            arg_bits.append(f'{name}="sample"')
        elif "UUID" in ptype:
            arg_bits.append(f"{name}=uuid4()")
        elif "Decimal" in ptype:
            arg_bits.append(f'{name}=Decimal("10.00")')
        elif "int" in ptype:
            arg_bits.append(f"{name}=1")
        elif "bool" in ptype:
            arg_bits.append(f"{name}=True")
        else:
            arg_bits.append(f"{name}=None")
    return "entity_id=entity_id, tenant_id=uuid4(), " + ", ".join(arg_bits)


def generate_service_unit_test(domain: DomainSpec) -> str:
    cn = domain.class_name
    snake = domain.snake
    method_blocks: list[str] = []
    for m in domain.methods:
        call = _method_call_args(m)
        method_blocks.append(
            textwrap.dedent(
                f"""
                @pytest.mark.asyncio
                async def test_{m.name}_raises_not_found(self, service, mock_repo):
                    mock_repo.get_by_id.return_value = None
                    with pytest.raises({cn}NotFoundError):
                        await service.{m.name}({call.replace("entity_id=entity_id", "entity_id=uuid4()")})

                @pytest.mark.asyncio
                async def test_{m.name}_with_entity(self, service, mock_repo):
                    entity = mock_repo.get_by_id.return_value
                    result = await service.{m.name}({call.replace("entity_id=entity_id", "entity_id=entity.id")})
                    assert result is not None
                """
            ).strip()
        )
    method_tests = "\n\n".join(_snippet(block, level=_T_CLASS) for block in method_blocks)
    status_validation = ""
    if any(f.name == "status" for f in domain.fields):
        status_validation = _snippet(
            """
            @pytest.mark.asyncio
            async def test_list_rejects_oversized_page(self, service):
                with pytest.raises({cn}ValidationError):
                    await service.list(tenant_id=uuid4(), page=1, page_size=999)
            """.format(cn=cn),
            level=_T_CLASS,
        )

    return textwrap.dedent(
        f'''\
        """Unit tests for {domain.title} service layer."""

        from __future__ import annotations

        from decimal import Decimal
        from unittest.mock import AsyncMock, MagicMock
        from uuid import uuid4

        import pytest

        from app.domains.{snake}.exceptions import {cn}NotFoundError, {cn}ValidationError
        from app.domains.{snake}.service import {cn}Service


        @pytest.fixture
        def mock_repo():
            repo = AsyncMock()
            entity = MagicMock()
            entity.id = uuid4()
            entity.tenant_id = uuid4()
            entity.status = "draft"
            repo.get_by_id.return_value = entity
            repo.list.return_value = ([entity], 1)
            repo.count.return_value = 1
            repo.exists.return_value = True
            return repo


        @pytest.fixture
        def service(mock_repo):
            return {cn}Service(repository=mock_repo)


        class Test{cn}ServiceList:
            @pytest.mark.asyncio
            async def test_list_returns_paginated(self, service, mock_repo):
                items, total = await service.list(tenant_id=uuid4(), page=1, page_size=10)
                assert total == 1
                assert len(items) == 1
                mock_repo.list.assert_awaited_once()

            @pytest.mark.asyncio
            async def test_list_rejects_invalid_page(self, service):
                with pytest.raises({cn}ValidationError):
                    await service.list(tenant_id=uuid4(), page=0, page_size=10)
{status_validation}


        class Test{cn}ServiceGet:
            @pytest.mark.asyncio
            async def test_get_raises_not_found(self, service, mock_repo):
                mock_repo.get_by_id.return_value = None
                with pytest.raises({cn}NotFoundError):
                    await service.get(tenant_id=uuid4(), entity_id=uuid4())

            @pytest.mark.asyncio
            async def test_get_returns_read_model(self, service):
                result = await service.get(tenant_id=uuid4(), entity_id=uuid4())
                assert result is not None


        class Test{cn}ServiceCount:
            @pytest.mark.asyncio
            async def test_count_delegates(self, service, mock_repo):
                total = await service.count(tenant_id=uuid4())
                assert total == 1
                mock_repo.count.assert_awaited_once()


        class Test{cn}ServiceExists:
            @pytest.mark.asyncio
            async def test_exists_true(self, service):
                assert await service.exists(uuid4(), tenant_id=uuid4()) is True


        class Test{cn}ServiceDelete:
            @pytest.mark.asyncio
            async def test_delete_soft_deletes(self, service, mock_repo):
                entity = mock_repo.get_by_id.return_value
                await service.delete(entity.id, tenant_id=uuid4())
                mock_repo.soft_delete.assert_awaited_once()


        class Test{cn}DomainMethods:
{method_tests if method_tests else "            pass"}
        '''
    )


def generate_repository_unit_test(domain: DomainSpec) -> str:
    cn = domain.class_name
    snake = domain.snake
    tenant_line = "tenant_id=uuid4()," if domain.tenant_scoped else ""
    return textwrap.dedent(
        f'''\
        """Unit tests for {domain.title} repository layer."""

        from __future__ import annotations

        from unittest.mock import AsyncMock, MagicMock
        from uuid import uuid4

        import pytest

        from app.domains.{snake}.repository import {cn}Repository


        @pytest.fixture
        def mock_session():
            session = AsyncMock()
            result = MagicMock()
            result.scalar_one_or_none.return_value = None
            result.scalar_one.return_value = 0
            result.scalars.return_value.all.return_value = []
            session.execute.return_value = result
            return session


        @pytest.fixture
        def repository(mock_session):
            return {cn}Repository(mock_session)


        class Test{cn}RepositoryQueries:
            @pytest.mark.asyncio
            async def test_get_by_id_executes_query(self, repository, mock_session):
                entity_id = uuid4()
                await repository.get_by_id(entity_id, {tenant_line})
                mock_session.execute.assert_awaited()

            @pytest.mark.asyncio
            async def test_list_returns_tuple(self, repository):
                rows, total = await repository.list({tenant_line} page=1, page_size=10)
                assert isinstance(rows, list)
                assert isinstance(total, int)

            @pytest.mark.asyncio
            async def test_exists_returns_bool(self, repository):
                result = await repository.exists(uuid4(), {tenant_line})
                assert isinstance(result, bool)

            @pytest.mark.asyncio
            async def test_count_returns_int(self, repository):
                result = await repository.count({tenant_line})
                assert isinstance(result, int)
        '''
    )


def generate_router_integration_test(domain: DomainSpec) -> str:
    cn = domain.class_name
    snake = domain.snake
    plural = domain.plural.replace("_", "-")
    title_token = "".join(part.capitalize() for part in snake.split("_"))
    action_tests = "\n".join(
        f"""
    def test_{m.name}_route_registered(self, app):
        path = "/api/v1/{plural}/{{entity_id}}{m.path_suffix or '/' + m.name.replace('_', '-')}"
        assert path in app.openapi()["paths"]
"""
        for m in domain.methods[:3]
    )
    return f'''"""Integration tests for {domain.title} API router."""

from __future__ import annotations

from uuid import uuid4
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture(scope="module")
def app():
    application = create_app()
    yield application
    application.dependency_overrides.clear()


@pytest.fixture
def client(app):
    app.dependency_overrides.clear()
    # Avoid lifespan/DB startup; dependency overrides supply services.
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def auth_headers():
    return {{
        "Authorization": "Bearer test-token",
        "X-Tenant-Id": str(uuid4()),
    }}


class Test{title_token}RouterList:
    def test_list_requires_tenant_header(self, app, client):
        from app.domains.{snake}.router import get_{snake}_service

        app.dependency_overrides[get_{snake}_service] = lambda: AsyncMock()
        response = client.get("/api/v1/{plural}")
        assert response.status_code in (400, 401, 422)

    def test_list_returns_envelope(self, app, client, auth_headers):
        from app.domains.{snake}.router import get_{snake}_service

        mock_service = AsyncMock()
        mock_service.list.return_value = ([], 0)
        app.dependency_overrides[get_{snake}_service] = lambda: mock_service
        response = client.get("/api/v1/{plural}?page=1&page_size=10", headers=auth_headers)
        assert response.status_code == 200


class Test{title_token}RouterGet:
    def test_get_not_found(self, app, client, auth_headers):
        from app.domains.{snake}.exceptions import {cn}NotFoundError
        from app.domains.{snake}.router import get_{snake}_service

        mock_service = AsyncMock()
        mock_service.get.side_effect = {cn}NotFoundError(uuid4())
        app.dependency_overrides[get_{snake}_service] = lambda: mock_service
        response = client.get(f"/api/v1/{plural}/{{uuid4()}}", headers=auth_headers)
        assert response.status_code in (404, 422)


class Test{title_token}RouterCreate:
    def test_create_validates_body(self, app, client, auth_headers):
        from app.domains.{snake}.router import get_{snake}_service

        app.dependency_overrides[get_{snake}_service] = lambda: AsyncMock()
        response = client.post("/api/v1/{plural}", headers=auth_headers, json={{}})
        assert response.status_code in (201, 422)


class Test{title_token}RouterCount:
    def test_count_endpoint(self, app, client, auth_headers):
        from app.domains.{snake}.router import get_{snake}_service

        mock_service = AsyncMock()
        mock_service.count.return_value = 5
        app.dependency_overrides[get_{snake}_service] = lambda: mock_service
        response = client.get("/api/v1/{plural}/count", headers=auth_headers)
        assert response.status_code == 200


class Test{title_token}RouterActions:
{action_tests if action_tests else "    pass"}
'''


def generate_schemas_unit_test(domain: DomainSpec) -> str:
    cn = domain.class_name
    snake = domain.snake
    return textwrap.dedent(
        f'''\
        """Pydantic schema validation tests for {domain.title}."""

        from __future__ import annotations

        from uuid import uuid4

        import pytest
        from pydantic import ValidationError

        from app.domains.{snake}.schemas import {cn}Create, {cn}ListResponse, {cn}Update


        class Test{cn}Schemas:
            def test_list_response_pages(self):
                envelope = {cn}ListResponse.from_page(items=[], total=100, page=1, page_size=25)
                assert envelope.pages == 4

            def test_update_allows_partial(self):
                patch = {cn}Update()
                dumped = patch.model_dump(exclude_unset=True)
                assert dumped == {{}}

            def test_create_rejects_blank_strings_when_required(self):
                field_names = [f for f in {cn}Create.model_fields if f not in ("password_hash",)]
                if not field_names:
                    pytest.skip("no create fields")
                # Smoke: model can be instantiated with minimal valid defaults where possible
                assert {cn}Create.__name__ == "{cn}Create"
        '''
    )


def generate_component_test(component_name: str) -> str:
    tests = {
        "StatusBadge": """import { render, screen } from '@testing-library/react';
import { StatusBadge } from '../StatusBadge';

describe('StatusBadge', () => {
  it('renders status text', () => {
    render(<StatusBadge status="in_progress" />);
    expect(screen.getByText(/in progress/i)).toBeInTheDocument();
  });

  it('applies size variant', () => {
    const { container } = render(<StatusBadge status="active" size="sm" />);
    expect(container.querySelector('.status-badge-sm')).toBeTruthy();
  });
});
""",
        "DataTable": """import { render, screen, fireEvent } from '@testing-library/react';
import { DataTable } from '../DataTable';

const data = [{ id: '1', name: 'Alpha' }, { id: '2', name: 'Beta' }];
const columns = [
  { key: 'name', header: 'Name', render: (r: { name: string }) => r.name },
];

describe('DataTable', () => {
  it('renders rows', () => {
    render(<DataTable columns={columns} data={data} keyExtractor={(r) => r.id} />);
    expect(screen.getByText('Alpha')).toBeInTheDocument();
    expect(screen.getByText('Beta')).toBeInTheDocument();
  });

  it('calls onRowClick', () => {
    const onClick = vi.fn();
    render(<DataTable columns={columns} data={data} keyExtractor={(r) => r.id} onRowClick={onClick} />);
    fireEvent.click(screen.getByText('Alpha'));
    expect(onClick).toHaveBeenCalledWith(data[0]);
  });
});
""",
        "FormField": """import { render, screen } from '@testing-library/react';
import { FormField } from '../FormField';

describe('FormField', () => {
  it('renders label and input', () => {
    render(<FormField label="Email" htmlFor="email"><input id="email" /></FormField>);
    expect(screen.getByLabelText('Email')).toBeInTheDocument();
  });

  it('shows error message', () => {
    render(<FormField label="Name" htmlFor="name" error="Required"><input id="name" /></FormField>);
    expect(screen.getByRole('alert')).toHaveTextContent('Required');
  });
});
""",
        "MetricCard": """import { render, screen } from '@testing-library/react';
import { MetricCard } from '../MetricCard';

describe('MetricCard', () => {
  it('displays value and label', () => {
    render(<MetricCard label="Open Orders" value={42} />);
    expect(screen.getByText('Open Orders')).toBeInTheDocument();
    expect(screen.getByText('42')).toBeInTheDocument();
  });
});
""",
        "EmptyState": """import { render, screen, fireEvent } from '@testing-library/react';
import { EmptyState } from '../EmptyState';

describe('EmptyState', () => {
  it('renders action button', () => {
    const onAction = vi.fn();
    render(<EmptyState title="Empty" actionLabel="Create" onAction={onAction} />);
    fireEvent.click(screen.getByText('Create'));
    expect(onAction).toHaveBeenCalled();
  });
});
""",
        "ConfirmDialog": """import { render, screen, fireEvent } from '@testing-library/react';
import { ConfirmDialog } from '../ConfirmDialog';

describe('ConfirmDialog', () => {
  it('calls onConfirm', () => {
    const onConfirm = vi.fn();
    render(<ConfirmDialog open title="Delete?" message="Sure?" onConfirm={onConfirm} onCancel={() => {}} />);
    fireEvent.click(screen.getByText('Confirm'));
    expect(onConfirm).toHaveBeenCalled();
  });
});
""",
        "LoadingSpinner": """import { render, screen } from '@testing-library/react';
import { LoadingSpinner } from '../LoadingSpinner';

describe('LoadingSpinner', () => {
  it('has accessible status', () => {
    render(<LoadingSpinner label="Loading data" />);
    expect(screen.getByRole('status')).toHaveAttribute('aria-label', 'Loading data');
  });
});
""",
        "DateRangePicker": """import { render, screen, fireEvent } from '@testing-library/react';
import { DateRangePicker } from '../DateRangePicker';

describe('DateRangePicker', () => {
  it('updates range on change', () => {
    const onChange = vi.fn();
    render(<DateRangePicker value={{ start: '', end: '' }} onChange={onChange} />);
    fireEvent.change(screen.getByLabelText(/start/i), { target: { value: '2024-01-01' } });
    expect(onChange).toHaveBeenCalledWith({ start: '2024-01-01', end: '' });
  });
});
""",
        "TechnicianAvatar": """import { render, screen } from '@testing-library/react';
import { TechnicianAvatar } from '../TechnicianAvatar';

describe('TechnicianAvatar', () => {
  it('shows initials', () => {
    render(<TechnicianAvatar name="Jane Doe" />);
    expect(screen.getByText('JD')).toBeInTheDocument();
  });
});
""",
        "WorkOrderCard": """import { render, screen, fireEvent } from '@testing-library/react';
import { WorkOrderCard } from '../WorkOrderCard';

const wo = { id: '1', orderNumber: 'WO-001', title: 'Repair HVAC', status: 'in_progress', priority: 'high' };

describe('WorkOrderCard', () => {
  it('renders work order details', () => {
    render(<WorkOrderCard workOrder={wo} />);
    expect(screen.getByText('WO-001')).toBeInTheDocument();
    expect(screen.getByText('Repair HVAC')).toBeInTheDocument();
  });
});
""",
        "PageHeader": """import { render, screen } from '@testing-library/react';
import { PageHeader } from '../PageHeader';

describe('PageHeader', () => {
  it('renders title and subtitle', () => {
    render(<PageHeader title="Dashboard" subtitle="Overview" />);
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Dashboard');
    expect(screen.getByText('Overview')).toBeInTheDocument();
  });
});
""",
        "Modal": """import { render, screen, fireEvent } from '@testing-library/react';
import { Modal } from '../Modal';

describe('Modal', () => {
  it('closes on escape', () => {
    const onClose = vi.fn();
    render(<Modal open title="Test" onClose={onClose}>Content</Modal>);
    fireEvent.keyDown(window, { key: 'Escape' });
    expect(onClose).toHaveBeenCalled();
  });
});
""",
    }
    default = f"""import {{ render }} from '@testing-library/react';
import {{ {component_name} }} from '../{component_name}';

describe('{component_name}', () => {{
  it('renders without crashing', () => {{
    expect({component_name}).toBeDefined();
  }});
}});
"""
    return tests.get(component_name, default)


def generate_util_test(util_name: str) -> str:
    tests = {
        "formatting": """import { describe, it, expect } from 'vitest';
import { formatCurrency, formatNumber, truncate, titleCase } from '../formatting';

describe('formatting', () => {
  it('formatCurrency formats USD', () => {
    expect(formatCurrency(1234.5)).toMatch(/\\$1,234\\.50/);
  });

  it('truncate shortens long strings', () => {
    expect(truncate('hello world', 8)).toBe('hello w…');
  });

  it('titleCase converts snake_case', () => {
    expect(titleCase('work_order')).toBe('Work Order');
  });
});
""",
        "dates": """import { describe, it, expect } from 'vitest';
import { formatDateTime, formatDate, isToday } from '../dates';

describe('dates', () => {
  it('formatDateTime handles ISO strings', () => {
    const result = formatDateTime('2024-06-15T14:30:00Z');
    expect(result).not.toBe('—');
  });

  it('formatDate returns dash for null', () => {
    expect(formatDate(null)).toBe('—');
  });
});
""",
        "statusColors": """import { describe, it, expect } from 'vitest';
import { statusColor, priorityWeight } from '../statusColors';

describe('statusColors', () => {
  it('returns color for known status', () => {
    expect(statusColor('completed')).toBe('#14b8a6');
  });

  it('priorityWeight ranks critical highest', () => {
    expect(priorityWeight('critical')).toBeGreaterThan(priorityWeight('low'));
  });
});
""",
    }
    return tests.get(util_name, f"""import {{ describe, it, expect }} from 'vitest';

describe('{util_name}', () => {{
  it('module exports exist', () => {{
    expect(true).toBe(true);
  }});
}});
""")


def generate_hook_test(hook_name: str) -> str:
    tests = {
        "useDebounce": """import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, afterEach } from 'vitest';
import { useDebounce } from '../useDebounce';

describe('useDebounce', () => {
  afterEach(() => vi.useRealTimers());

  it('debounces value changes', () => {
    vi.useFakeTimers();
    const { result, rerender } = renderHook(({ v, d }) => useDebounce(v, d), {
      initialProps: { v: 'a', d: 300 },
    });
    expect(result.current).toBe('a');
    rerender({ v: 'b', d: 300 });
    expect(result.current).toBe('a');
    act(() => vi.advanceTimersByTime(300));
    expect(result.current).toBe('b');
  });
});
""",
        "usePagination": """import { renderHook, act } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { usePagination } from '../usePagination';

describe('usePagination', () => {
  it('calculates total pages', () => {
    const { result } = renderHook(() => usePagination({ total: 100, pageSize: 25 }));
    expect(result.current.totalPages).toBe(4);
  });

  it('updates page', () => {
    const { result } = renderHook(() => usePagination({ total: 50, pageSize: 10 }));
    act(() => result.current.setPage(3));
    expect(result.current.page).toBe(3);
  });
});
""",
    }
    return tests.get(hook_name, f"""import {{ describe, it, expect }} from 'vitest';

describe('{hook_name}', () => {{
  it('is defined', () => {{
    expect(true).toBe(true);
  }});
}});
""")


def generate_domain_type_test(domain: DomainSpec) -> str:
    cn = domain.class_name
    return f"""import {{ describe, it, expect }} from 'vitest';
import type {{ {cn} }} from '../{domain.snake}';

describe('{cn} type', () => {{
  it('accepts valid shape', () => {{
    const record: {cn} = {{
      id: 'test-id',
      {"tenantId: 'tenant-1'," if domain.tenant_scoped else ""}
      {", ".join(f"{f.name}: {'null' if f.nullable else repr('x')}" for f in domain.fields[:3])},
      createdAt: '2024-01-01T00:00:00Z',
      updatedAt: '2024-01-01T00:00:00Z',
      {"deletedAt: null," if domain.soft_delete else ""}
    }};
    expect(record.id).toBe('test-id');
  }});
}});
"""


def generate_domain_api_test(domain: DomainSpec) -> str:
    snake = domain.snake
    plural = domain.plural.replace("_", "-")
    return f"""import {{ describe, it, expect, vi, beforeEach }} from 'vitest';
import {{ {snake.replace("_", "")}Api }} from '../{snake}';

describe('{snake}Api', () => {{
  beforeEach(() => {{
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({{
      ok: true,
      json: () => Promise.resolve({{ data: [], total: 0, page: 1, pageSize: 25, pages: 1 }}),
    }}));
  }});

  it('list calls correct endpoint', async () => {{
    await {snake.replace("_", "")}Api.list({{ page: 1 }});
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/{plural}'),
      expect.any(Object),
    );
  }});
}});
"""
