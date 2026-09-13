      import { apiFetch, type PaginatedResponse } from './client';
      import type { PartsRequest, PartsRequestCreate, PartsRequestUpdate, PartsRequestListParams } from '../types/parts_request';

      export const partsRequestApi = {
        list(params: PartsRequestListParams = {}): Promise<PaginatedResponse<PartsRequest>> {
          const qs = new URLSearchParams();
          if (params.page) qs.set('page', String(params.page));
          if (params.pageSize) qs.set('page_size', String(params.pageSize));
          if (params.search) qs.set('search', params.search);
          if (params.orderBy) qs.set('order_by', params.orderBy);
          if (params.orderDir) qs.set('order_dir', params.orderDir);
              if (params.work_order_id !== undefined) qs.set('work_order_id', String(params.work_order_id));
  if (params.requested_by_id !== undefined) qs.set('requested_by_id', String(params.requested_by_id));
  if (params.status !== undefined) qs.set('status', String(params.status));
          return apiFetch<PaginatedResponse<PartsRequest>>(`/api/v1/parts-requests?${qs}`);
        },

        get(id: string): Promise<PartsRequest> {
          return apiFetch<PartsRequest>(`/api/v1/parts-requests/${id}`);
        },

        create(data: PartsRequestCreate): Promise<PartsRequest> {
          return apiFetch<PartsRequest>('/api/v1/parts-requests', {
            method: 'POST',
            body: JSON.stringify(data),
          });
        },

        update(id: string, data: PartsRequestUpdate): Promise<PartsRequest> {
          return apiFetch<PartsRequest>(`/api/v1/parts-requests/${id}`, {
            method: 'PATCH',
            body: JSON.stringify(data),
          });
        },

        remove(id: string): Promise<void> {
          return apiFetch<void>(`/api/v1/parts-requests/${id}`, { method: 'DELETE' });
        },

        count(): Promise<{ total: number }> {
          return apiFetch<{ total: number }>(`/api/v1/parts-requests/count`);
        },
        restore(id: string): Promise<PartsRequest> {
  return apiFetch<PartsRequest>(`/api/v1/parts-requests/${id}/restore`, { method: 'POST' });
},

        async approve(id: string): Promise<PartsRequest> {
  return apiFetch<PartsRequest>(`/api/v1/parts-requests/${id}/approve`, {
    method: "POST",
    body: undefined,
  });
},

async fulfill(id: string): Promise<PartsRequest> {
  return apiFetch<PartsRequest>(`/api/v1/parts-requests/${id}/fulfill`, {
    method: "POST",
    body: undefined,
  });
},

async reject(id: string, reason: string): Promise<PartsRequest> {
  return apiFetch<PartsRequest>(`/api/v1/parts-requests/${id}/reject`, {
    method: "POST",
    body: JSON.stringify({reason: reason}),
  });
},
      };
