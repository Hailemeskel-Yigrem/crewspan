      import { apiFetch, type PaginatedResponse } from './client';
      import type { SlaBreach, SlaBreachCreate, SlaBreachUpdate, SlaBreachListParams } from '../types/sla_breach';

      export const slaBreachApi = {
        list(params: SlaBreachListParams = {}): Promise<PaginatedResponse<SlaBreach>> {
          const qs = new URLSearchParams();
          if (params.page) qs.set('page', String(params.page));
          if (params.pageSize) qs.set('page_size', String(params.pageSize));
          if (params.search) qs.set('search', params.search);
          if (params.orderBy) qs.set('order_by', params.orderBy);
          if (params.orderDir) qs.set('order_dir', params.orderDir);
              if (params.work_order_id !== undefined) qs.set('work_order_id', String(params.work_order_id));
  if (params.sla_policy_id !== undefined) qs.set('sla_policy_id', String(params.sla_policy_id));
  if (params.breach_type !== undefined) qs.set('breach_type', String(params.breach_type));
          return apiFetch<PaginatedResponse<SlaBreach>>(`/api/v1/sla-breachs?${qs}`);
        },

        get(id: string): Promise<SlaBreach> {
          return apiFetch<SlaBreach>(`/api/v1/sla-breachs/${id}`);
        },

        create(data: SlaBreachCreate): Promise<SlaBreach> {
          return apiFetch<SlaBreach>('/api/v1/sla-breachs', {
            method: 'POST',
            body: JSON.stringify(data),
          });
        },

        update(id: string, data: SlaBreachUpdate): Promise<SlaBreach> {
          return apiFetch<SlaBreach>(`/api/v1/sla-breachs/${id}`, {
            method: 'PATCH',
            body: JSON.stringify(data),
          });
        },

        remove(id: string): Promise<void> {
          return apiFetch<void>(`/api/v1/sla-breachs/${id}`, { method: 'DELETE' });
        },

        count(): Promise<{ total: number }> {
          return apiFetch<{ total: number }>(`/api/v1/sla-breachs/count`);
        },
        restore(id: string): Promise<SlaBreach> {
  return apiFetch<SlaBreach>(`/api/v1/sla-breachs/${id}/restore`, { method: 'POST' });
},

        async acknowledge(id: string): Promise<SlaBreach> {
  return apiFetch<SlaBreach>(`/api/v1/sla-breachs/${id}/acknowledge`, {
    method: "POST",
    body: undefined,
  });
},

async escalate(id: string): Promise<SlaBreach> {
  return apiFetch<SlaBreach>(`/api/v1/sla-breachs/${id}/escalate`, {
    method: "POST",
    body: undefined,
  });
},
      };
