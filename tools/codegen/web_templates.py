"""Template functions for Fieldspan web application code generation."""

from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tools.codegen.domains import DomainSpec, FieldSpec


def ts_type(field: FieldSpec) -> str:
    mapping = {
        "str": "string",
        "int": "number",
        "bool": "boolean",
        "UUID": "string",
        "Decimal": "string",
        "datetime": "string",
        "datetime | None": "string | null",
        "date": "string",
        "date | None": "string | null",
        "dict": "Record<string, unknown>",
        "list": "unknown[]",
        "Decimal | None": "string | null",
    }
    base = mapping.get(field.python_type, "unknown")
    if field.nullable and "| null" not in base and "| None" not in base:
        return f"{base} | null"
    return base.replace(" | None", " | null")


def pascal_case(name: str) -> str:
    return "".join(part.capitalize() for part in name.split("_"))


def camel_case(name: str) -> str:
    parts = name.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def generate_domain_type(domain: DomainSpec) -> str:
    cn = domain.class_name
    fields = "\n".join(f"  {f.name}: {ts_type(f)};" for f in domain.fields)
    return textwrap.dedent(
        f"""\
        /** {domain.description} */
        export interface {cn} {{
          id: string;
          {"tenantId: string;" if domain.tenant_scoped else ""}
        {fields}
          createdAt: string;
          updatedAt: string;
          {"deletedAt: string | null;" if domain.soft_delete else ""}
        }}

        export interface {cn}Create {{
        {chr(10).join(f"  {f.name}{'' if f.nullable else '?'}: {ts_type(f)};" for f in domain.fields if not f.default)}
        }}

        export interface {cn}Update {{
        {chr(10).join(f"  {f.name}?: {ts_type(f)};" for f in domain.fields)}
        }}

        export interface {cn}ListParams {{
          page?: number;
          pageSize?: number;
          search?: string;
          orderBy?: string;
          orderDir?: 'asc' | 'desc';
          {chr(10).join(f"  {f.name}?: {ts_type(f)};" for f in domain.fields if f.indexed)[:500]}
        }}

        export interface {cn}ListResponse {{
          items: {cn}[];
          total: number;
          page: number;
          pageSize: number;
          pages: number;
        }}

        export function is{cn}Active(record: {cn}): boolean {{
          const row = record as {{ isActive?: boolean; status?: string; deletedAt?: string | null }};
          if (row.deletedAt) return false;
          if (typeof row.isActive === 'boolean') return row.isActive;
          if (row.status) return !['cancelled', 'inactive', 'void'].includes(row.status);
          return true;
        }}

        export function {camel_case(domain.snake)}DisplayName(record: {cn}): string {{
          const row = record as {{ name?: string; title?: string; orderNumber?: string; displayName?: string }};
          return row.displayName || row.name || row.title || row.orderNumber || record.id.slice(0, 8);
        }}
        """
    )


def generate_domain_api_client(domain: DomainSpec) -> str:
    cn = domain.class_name
    snake = domain.snake
    plural = domain.plural.replace("_", "-")
    methods = []
    for m in domain.methods:
        params = ", ".join(f"{camel_case(p[0])}: {p[1].replace('UUID', 'string').replace(' | None', ' | null')}" for p in m.params)
        path = f"/api/v1/{plural}/{{id}}{m.path_suffix}"
        if m.http_verb == "GET":
            methods.append(
                f"""  async {m.name}(id: string{', ' + params if params else ''}): Promise<{cn}> {{
    return apiFetch<{cn}>('{path.replace('{id}', '${id}')}'{', { method: "GET" }' if not params else f', {{ method: "GET", body: JSON.stringify({{{", ".join(camel_case(p[0]) + ": " + camel_case(p[0]) for p in m.params)}}}) }}' if m.params else ', { method: "GET" }'});
  }}"""
            )
        elif m.http_verb in ("POST", "PATCH"):
            body = f"JSON.stringify({{{', '.join(camel_case(p[0]) + ': ' + camel_case(p[0]) for p in m.params)}}})" if m.params else "undefined"
            methods.append(
                f"""  async {m.name}(id: string{', ' + params if params else ''}): Promise<{cn}> {{
    return apiFetch<{cn}>(`{path}`, {{
      method: "{m.http_verb}",
      body: {body},
    }});
  }}"""
            )
    method_block = "\n\n".join(methods) if methods else ""
    return textwrap.dedent(
        f"""\
        import {{ apiFetch, type PaginatedResponse }} from './client';
        import type {{ {cn}, {cn}Create, {cn}Update, {cn}ListParams }} from '../types/{snake}';

        export const {camel_case(snake)}Api = {{
          list(params: {cn}ListParams = {{}}): Promise<PaginatedResponse<{cn}>> {{
            const qs = new URLSearchParams();
            if (params.page) qs.set('page', String(params.page));
            if (params.pageSize) qs.set('page_size', String(params.pageSize));
            if (params.search) qs.set('search', params.search);
            if (params.orderBy) qs.set('order_by', params.orderBy);
            if (params.orderDir) qs.set('order_dir', params.orderDir);
            {chr(10).join(f"    if (params.{f.name} !== undefined) qs.set('{f.name}', String(params.{f.name}));" for f in domain.fields if f.indexed)[:800]}
            return apiFetch<PaginatedResponse<{cn}>>(`/api/v1/{plural}?${{qs}}`);
          }},

          get(id: string): Promise<{cn}> {{
            return apiFetch<{cn}>(`/api/v1/{plural}/${{id}}`);
          }},

          create(data: {cn}Create): Promise<{cn}> {{
            return apiFetch<{cn}>('/api/v1/{plural}', {{
              method: 'POST',
              body: JSON.stringify(data),
            }});
          }},

          update(id: string, data: {cn}Update): Promise<{cn}> {{
            return apiFetch<{cn}>(`/api/v1/{plural}/${{id}}`, {{
              method: 'PATCH',
              body: JSON.stringify(data),
            }});
          }},

          remove(id: string): Promise<void> {{
            return apiFetch<void>(`/api/v1/{plural}/${{id}}`, {{ method: 'DELETE' }});
          }},

          count(): Promise<{{ total: number }}> {{
            return apiFetch<{{ total: number }}>(`/api/v1/{plural}/count`);
          }},
          {"restore(id: string): Promise<" + cn + "> {\n    return apiFetch<" + cn + ">(`/api/v1/" + plural + "/${id}/restore`, { method: 'POST' });\n  },\n" if domain.soft_delete else ""}
        {method_block}
        }};
        """
    )


def generate_domain_list_page(domain: DomainSpec) -> str:
    cn = domain.class_name
    snake = domain.snake
    title = domain.title
    filter_field = next((f for f in domain.fields if f.name in ("status", "name", "priority")), domain.fields[0])
    return textwrap.dedent(
        f"""\
        import {{ useCallback, useEffect, useMemo, useState }} from 'react';
        import {{ useNavigate }} from 'react-router-dom';
        import {{ DataTable, type Column }} from '../components/DataTable';
        import {{ EmptyState }} from '../components/EmptyState';
        import {{ FormField }} from '../components/FormField';
        import {{ LoadingSpinner }} from '../components/LoadingSpinner';
        import {{ PageHeader }} from '../components/PageHeader';
        import {{ StatusBadge }} from '../components/StatusBadge';
        import {{ useDebounce }} from '../hooks/useDebounce';
        import {{ usePagination }} from '../hooks/usePagination';
        import {{ {camel_case(snake)}Api }} from '../api/{snake}';
        import type {{ {cn} }} from '../types/{snake}';
        import {{ formatDateTime }} from '../utils/dates';

        export function {cn}ListPage() {{
          const navigate = useNavigate();
          const [items, setItems] = useState<{cn}[]>([]);
          const [total, setTotal] = useState(0);
          const [loading, setLoading] = useState(true);
          const [error, setError] = useState<string | null>(null);
          const [search, setSearch] = useState('');
          const [filterValue, setFilterValue] = useState('');
          const debouncedSearch = useDebounce(search, 300);
          const {{ page, pageSize, setPage, totalPages }} = usePagination({{ total, pageSize: 25 }});

          const load = useCallback(async () => {{
            setLoading(true);
            setError(null);
            try {{
              const res = await {camel_case(snake)}Api.list({{ page, pageSize, search: debouncedSearch || undefined }});
              setItems(res.data);
              setTotal(res.total);
            }} catch (err) {{
              setError(err instanceof Error ? err.message : 'Failed to load {title} records');
            }} finally {{
              setLoading(false);
            }}
          }}, [page, pageSize, debouncedSearch]);

          useEffect(() => {{ void load(); }}, [load]);

          const filtered = useMemo(
            () => items.filter((row) => !filterValue || String(row.{filter_field.name}).includes(filterValue)),
            [items, filterValue],
          );

          const columns: Column<{cn}>[] = [
            {{ key: 'id', header: 'ID', render: (row) => row.id.slice(0, 8) }},
            {{ key: '{filter_field.name}', header: '{filter_field.name.replace("_", " ").title()}', render: (row) => String(row.{filter_field.name}) }},
            {{ key: 'createdAt', header: 'Created', render: (row) => formatDateTime(row.createdAt) }},
          ];

          return (
            <div className="page">
              <PageHeader
                title="{title}"
                subtitle="Manage {domain.plural.replace('_', ' ')} across your tenant"
                actions={{<button type="button" className="btn btn-primary" onClick={{() => navigate('/{snake}/new')}}>New {title}</button>}}
              />
              <div className="toolbar">
                <FormField label="Search" htmlFor="{snake}-search">
                  <input id="{snake}-search" value={{search}} onChange={{(e) => {{ setSearch(e.target.value); setPage(1); }}}} placeholder="Search {title.lower()}..." />
                </FormField>
                <FormField label="Filter by {filter_field.name}" htmlFor="{snake}-filter">
                  <input id="{snake}-filter" value={{filterValue}} onChange={{(e) => setFilterValue(e.target.value)}} />
                </FormField>
              </div>
              {{loading ? <LoadingSpinner label="Loading {title.lower()}..." /> : null}}
              {{error ? <div className="alert alert-error">{{error}}</div> : null}}
              {{!loading && filtered.length === 0 ? (
                <EmptyState title="No {title.lower()} found" description="Adjust filters or create a new record." actionLabel="Create {title}" onAction={{() => navigate('/{snake}/new')}} />
              ) : (
                <DataTable
                  columns={{columns}}
                  data={{filtered}}
                  keyExtractor={{(row) => row.id}}
                  onRowClick={{(row) => navigate(`/{snake}/${{row.id}}`)}}
                  pagination={{{{ page, pageSize, totalPages, onPageChange: setPage }}}}
                />
              )}}
            </div>
          );
        }}
        """
    )


def generate_domain_detail_page(domain: DomainSpec) -> str:
    cn = domain.class_name
    snake = domain.snake
    title = domain.title
    field_rows = "\n".join(
        f'              <dt>{f.name.replace("_", " ").title()}</dt><dd>{{{{record.{f.name} != null ? String(record.{f.name}) : "—"}}}}</dd>'
        for f in domain.fields[:6]
    )
    return textwrap.dedent(
        f"""\
        import {{ useCallback, useEffect, useState }} from 'react';
        import {{ useNavigate, useParams }} from 'react-router-dom';
        import {{ ConfirmDialog }} from '../components/ConfirmDialog';
        import {{ LoadingSpinner }} from '../components/LoadingSpinner';
        import {{ PageHeader }} from '../components/PageHeader';
        import {{ StatusBadge }} from '../components/StatusBadge';
        import {{ {camel_case(snake)}Api }} from '../api/{snake}';
        import type {{ {cn} }} from '../types/{snake}';
        import {{ formatDateTime }} from '../utils/dates';

        export function {cn}DetailPage() {{
          const {{ id }} = useParams<{{ id: string }}>();
          const navigate = useNavigate();
          const [record, setRecord] = useState<{cn} | null>(null);
          const [loading, setLoading] = useState(true);
          const [error, setError] = useState<string | null>(null);
          const [confirmDelete, setConfirmDelete] = useState(false);
          const [deleting, setDeleting] = useState(false);

          const load = useCallback(async () => {{
            if (!id) return;
            setLoading(true);
            try {{
              setRecord(await {camel_case(snake)}Api.get(id));
            }} catch (err) {{
              setError(err instanceof Error ? err.message : 'Failed to load {title}');
            }} finally {{
              setLoading(false);
            }}
          }}, [id]);

          useEffect(() => {{ void load(); }}, [load]);

          const handleDelete = async () => {{
            if (!id) return;
            setDeleting(true);
            try {{
              await {camel_case(snake)}Api.remove(id);
              navigate('/{snake}');
            }} catch (err) {{
              setError(err instanceof Error ? err.message : 'Delete failed');
            }} finally {{
              setDeleting(false);
              setConfirmDelete(false);
            }}
          }};

          if (loading) return <LoadingSpinner label="Loading {title.lower()}..." />;
          if (error) return <div className="alert alert-error">{{error}}</div>;
          if (!record) return <div className="alert alert-warning">{title} not found</div>;

          return (
            <div className="page">
              <PageHeader
                title="{title} {{record.id.slice(0, 8)}}"
                subtitle="Created {{formatDateTime(record.createdAt)}}"
                actions={{
                  <>
                    <button type="button" className="btn btn-secondary" onClick={{() => navigate('/{snake}')}}>Back</button>
                    <button type="button" className="btn btn-danger" onClick={{() => setConfirmDelete(true)}}>Delete</button>
                  </>
                }}
              />
              <dl className="detail-grid">
        {field_rows}
                <dt>Updated</dt><dd>{{formatDateTime(record.updatedAt)}}</dd>
              </dl>
              <ConfirmDialog
                open={{confirmDelete}}
                title="Delete {title}?"
                message="This action cannot be undone."
                confirmLabel={{deleting ? 'Deleting...' : 'Delete'}}
                variant="danger"
                onConfirm={{() => void handleDelete()}}
                onCancel={{() => setConfirmDelete(false)}}
              />
            </div>
          );
        }}
        """
    )
