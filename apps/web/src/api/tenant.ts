      import { apiFetch, type PaginatedResponse } from './client';
      import type { Tenant, TenantCreate, TenantUpdate, TenantListParams } from '../types/tenant';

      export const tenantApi = {
        list(params: TenantListParams = {}): Promise<PaginatedResponse<Tenant>> {
          const qs = new URLSearchParams();
          if (params.page) qs.set('page', String(params.page));
          if (params.pageSize) qs.set('page_size', String(params.pageSize));
          if (params.search) qs.set('search', params.search);
          if (params.orderBy) qs.set('order_by', params.orderBy);
          if (params.orderDir) qs.set('order_dir', params.orderDir);
              if (params.slug !== undefined) qs.set('slug', String(params.slug));
          return apiFetch<PaginatedResponse<Tenant>>(`/api/v1/tenants?${qs}`);
        },

        get(id: string): Promise<Tenant> {
          return apiFetch<Tenant>(`/api/v1/tenants/${id}`);
        },

        create(data: TenantCreate): Promise<Tenant> {
          return apiFetch<Tenant>('/api/v1/tenants', {
            method: 'POST',
            body: JSON.stringify(data),
          });
        },

        update(id: string, data: TenantUpdate): Promise<Tenant> {
          return apiFetch<Tenant>(`/api/v1/tenants/${id}`, {
            method: 'PATCH',
            body: JSON.stringify(data),
          });
        },

        remove(id: string): Promise<void> {
          return apiFetch<void>(`/api/v1/tenants/${id}`, { method: 'DELETE' });
        },

        count(): Promise<{ total: number }> {
          return apiFetch<{ total: number }>(`/api/v1/tenants/count`);
        },
        restore(id: string): Promise<Tenant> {
  return apiFetch<Tenant>(`/api/v1/tenants/${id}/restore`, { method: 'POST' });
},

        async activate(id: string): Promise<Tenant> {
  return apiFetch<Tenant>(`/api/v1/tenants/${id}/activate`, {
    method: "POST",
    body: undefined,
  });
},

async deactivate(id: string): Promise<Tenant> {
  return apiFetch<Tenant>(`/api/v1/tenants/${id}/deactivate`, {
    method: "POST",
    body: undefined,
  });
},

async update_settings(id: string, settings: Record<string, unknown>): Promise<Tenant> {
  return apiFetch<Tenant>(`/api/v1/tenants/${id}/update-settings`, {
    method: "POST",
    body: JSON.stringify({settings: settings}),
  });
},
      };
