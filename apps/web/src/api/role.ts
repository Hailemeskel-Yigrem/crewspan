      import { apiFetch, type PaginatedResponse } from './client';
      import type { Role, RoleCreate, RoleUpdate, RoleListParams } from '../types/role';

      export const roleApi = {
        list(params: RoleListParams = {}): Promise<PaginatedResponse<Role>> {
          const qs = new URLSearchParams();
          if (params.page) qs.set('page', String(params.page));
          if (params.pageSize) qs.set('page_size', String(params.pageSize));
          if (params.search) qs.set('search', params.search);
          if (params.orderBy) qs.set('order_by', params.orderBy);
          if (params.orderDir) qs.set('order_dir', params.orderDir);
              if (params.name !== undefined) qs.set('name', String(params.name));
          return apiFetch<PaginatedResponse<Role>>(`/api/v1/roles?${qs}`);
        },

        get(id: string): Promise<Role> {
          return apiFetch<Role>(`/api/v1/roles/${id}`);
        },

        create(data: RoleCreate): Promise<Role> {
          return apiFetch<Role>('/api/v1/roles', {
            method: 'POST',
            body: JSON.stringify(data),
          });
        },

        update(id: string, data: RoleUpdate): Promise<Role> {
          return apiFetch<Role>(`/api/v1/roles/${id}`, {
            method: 'PATCH',
            body: JSON.stringify(data),
          });
        },

        remove(id: string): Promise<void> {
          return apiFetch<void>(`/api/v1/roles/${id}`, { method: 'DELETE' });
        },

        count(): Promise<{ total: number }> {
          return apiFetch<{ total: number }>(`/api/v1/roles/count`);
        },
        restore(id: string): Promise<Role> {
  return apiFetch<Role>(`/api/v1/roles/${id}/restore`, { method: 'POST' });
},

        async grant_permission(id: string, permission: string): Promise<Role> {
  return apiFetch<Role>(`/api/v1/roles/${id}/grant-permission`, {
    method: "POST",
    body: JSON.stringify({permission: permission}),
  });
},

async revoke_permission(id: string, permission: string): Promise<Role> {
  return apiFetch<Role>(`/api/v1/roles/${id}/revoke-permission`, {
    method: "POST",
    body: JSON.stringify({permission: permission}),
  });
},

async clone(id: string, newName: string): Promise<Role> {
  return apiFetch<Role>(`/api/v1/roles/${id}/clone`, {
    method: "POST",
    body: JSON.stringify({new_name: newName}),
  });
},
      };
