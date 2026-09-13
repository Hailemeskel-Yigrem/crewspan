      import { apiFetch, type PaginatedResponse } from './client';
      import type { SlaPolicy, SlaPolicyCreate, SlaPolicyUpdate, SlaPolicyListParams } from '../types/sla_policy';

      export const slaPolicyApi = {
        list(params: SlaPolicyListParams = {}): Promise<PaginatedResponse<SlaPolicy>> {
          const qs = new URLSearchParams();
          if (params.page) qs.set('page', String(params.page));
          if (params.pageSize) qs.set('page_size', String(params.pageSize));
          if (params.search) qs.set('search', params.search);
          if (params.orderBy) qs.set('order_by', params.orderBy);
          if (params.orderDir) qs.set('order_dir', params.orderDir);
              if (params.name !== undefined) qs.set('name', String(params.name));
  if (params.priority !== undefined) qs.set('priority', String(params.priority));
          return apiFetch<PaginatedResponse<SlaPolicy>>(`/api/v1/sla-policies?${qs}`);
        },

        get(id: string): Promise<SlaPolicy> {
          return apiFetch<SlaPolicy>(`/api/v1/sla-policies/${id}`);
        },

        create(data: SlaPolicyCreate): Promise<SlaPolicy> {
          return apiFetch<SlaPolicy>('/api/v1/sla-policies', {
            method: 'POST',
            body: JSON.stringify(data),
          });
        },

        update(id: string, data: SlaPolicyUpdate): Promise<SlaPolicy> {
          return apiFetch<SlaPolicy>(`/api/v1/sla-policies/${id}`, {
            method: 'PATCH',
            body: JSON.stringify(data),
          });
        },

        remove(id: string): Promise<void> {
          return apiFetch<void>(`/api/v1/sla-policies/${id}`, { method: 'DELETE' });
        },

        count(): Promise<{ total: number }> {
          return apiFetch<{ total: number }>(`/api/v1/sla-policies/count`);
        },
        restore(id: string): Promise<SlaPolicy> {
  return apiFetch<SlaPolicy>(`/api/v1/sla-policies/${id}/restore`, { method: 'POST' });
},

        async evaluate_deadlines(id: string, openedAt: string): Promise<SlaPolicy> {
  return apiFetch<SlaPolicy>(`/api/v1/sla-policies/${id}/evaluate-deadlines`, {
    method: "POST",
    body: JSON.stringify({opened_at: openedAt}),
  });
},

async clone(id: string, newName: string): Promise<SlaPolicy> {
  return apiFetch<SlaPolicy>(`/api/v1/sla-policies/${id}/clone`, {
    method: "POST",
    body: JSON.stringify({new_name: newName}),
  });
},
      };
