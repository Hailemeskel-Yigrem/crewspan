      import { apiFetch, type PaginatedResponse } from './client';
      import type { Dispatch, DispatchCreate, DispatchUpdate, DispatchListParams } from '../types/dispatch';

      export const dispatchApi = {
        list(params: DispatchListParams = {}): Promise<PaginatedResponse<Dispatch>> {
          const qs = new URLSearchParams();
          if (params.page) qs.set('page', String(params.page));
          if (params.pageSize) qs.set('page_size', String(params.pageSize));
          if (params.search) qs.set('search', params.search);
          if (params.orderBy) qs.set('order_by', params.orderBy);
          if (params.orderDir) qs.set('order_dir', params.orderDir);
              if (params.work_order_id !== undefined) qs.set('work_order_id', String(params.work_order_id));
  if (params.technician_id !== undefined) qs.set('technician_id', String(params.technician_id));
  if (params.status !== undefined) qs.set('status', String(params.status));
          return apiFetch<PaginatedResponse<Dispatch>>(`/api/v1/dispatchs?${qs}`);
        },

        get(id: string): Promise<Dispatch> {
          return apiFetch<Dispatch>(`/api/v1/dispatchs/${id}`);
        },

        create(data: DispatchCreate): Promise<Dispatch> {
          return apiFetch<Dispatch>('/api/v1/dispatchs', {
            method: 'POST',
            body: JSON.stringify(data),
          });
        },

        update(id: string, data: DispatchUpdate): Promise<Dispatch> {
          return apiFetch<Dispatch>(`/api/v1/dispatchs/${id}`, {
            method: 'PATCH',
            body: JSON.stringify(data),
          });
        },

        remove(id: string): Promise<void> {
          return apiFetch<void>(`/api/v1/dispatchs/${id}`, { method: 'DELETE' });
        },

        count(): Promise<{ total: number }> {
          return apiFetch<{ total: number }>(`/api/v1/dispatchs/count`);
        },
        restore(id: string): Promise<Dispatch> {
  return apiFetch<Dispatch>(`/api/v1/dispatchs/${id}/restore`, { method: 'POST' });
},

        async accept(id: string): Promise<Dispatch> {
  return apiFetch<Dispatch>(`/api/v1/dispatchs/{id}/accept`, {
    method: "POST",
    body: undefined,
  });
}

async decline(id: string, reason: str): Promise<Dispatch> {
  return apiFetch<Dispatch>(`/api/v1/dispatchs/{id}/decline`, {
    method: "POST",
    body: JSON.stringify({reason: reason}),
  });
}

async en_route(id: string): Promise<Dispatch> {
  return apiFetch<Dispatch>(`/api/v1/dispatchs/{id}/en-route`, {
    method: "POST",
    body: undefined,
  });
}

async arrive(id: string): Promise<Dispatch> {
  return apiFetch<Dispatch>(`/api/v1/dispatchs/{id}/arrive`, {
    method: "POST",
    body: undefined,
  });
}
      };
