      import { apiFetch, type PaginatedResponse } from './client';
      import type { User, UserCreate, UserUpdate, UserListParams } from '../types/user';

      export const userApi = {
        list(params: UserListParams = {}): Promise<PaginatedResponse<User>> {
          const qs = new URLSearchParams();
          if (params.page) qs.set('page', String(params.page));
          if (params.pageSize) qs.set('page_size', String(params.pageSize));
          if (params.search) qs.set('search', params.search);
          if (params.orderBy) qs.set('order_by', params.orderBy);
          if (params.orderDir) qs.set('order_dir', params.orderDir);
              if (params.email !== undefined) qs.set('email', String(params.email));
  if (params.role_id !== undefined) qs.set('role_id', String(params.role_id));
          return apiFetch<PaginatedResponse<User>>(`/api/v1/users?${qs}`);
        },

        get(id: string): Promise<User> {
          return apiFetch<User>(`/api/v1/users/${id}`);
        },

        create(data: UserCreate): Promise<User> {
          return apiFetch<User>('/api/v1/users', {
            method: 'POST',
            body: JSON.stringify(data),
          });
        },

        update(id: string, data: UserUpdate): Promise<User> {
          return apiFetch<User>(`/api/v1/users/${id}`, {
            method: 'PATCH',
            body: JSON.stringify(data),
          });
        },

        remove(id: string): Promise<void> {
          return apiFetch<void>(`/api/v1/users/${id}`, { method: 'DELETE' });
        },

        count(): Promise<{ total: number }> {
          return apiFetch<{ total: number }>(`/api/v1/users/count`);
        },
        restore(id: string): Promise<User> {
  return apiFetch<User>(`/api/v1/users/${id}/restore`, { method: 'POST' });
},

        async change_password(id: string, newPassword: str): Promise<User> {
  return apiFetch<User>(`/api/v1/users/{id}/change-password`, {
    method: "POST",
    body: JSON.stringify({newPassword: newPassword}),
  });
}

async record_login(id: string): Promise<User> {
  return apiFetch<User>(`/api/v1/users/{id}/record-login`, {
    method: "POST",
    body: undefined,
  });
}

async deactivate(id: string): Promise<User> {
  return apiFetch<User>(`/api/v1/users/{id}/deactivate`, {
    method: "POST",
    body: undefined,
  });
}
      };
