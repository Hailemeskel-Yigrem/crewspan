      import { apiFetch, type PaginatedResponse } from './client';
      import type { Webhook, WebhookCreate, WebhookUpdate, WebhookListParams } from '../types/webhook';

      export const webhookApi = {
        list(params: WebhookListParams = {}): Promise<PaginatedResponse<Webhook>> {
          const qs = new URLSearchParams();
          if (params.page) qs.set('page', String(params.page));
          if (params.pageSize) qs.set('page_size', String(params.pageSize));
          if (params.search) qs.set('search', params.search);
          if (params.orderBy) qs.set('order_by', params.orderBy);
          if (params.orderDir) qs.set('order_dir', params.orderDir);

          return apiFetch<PaginatedResponse<Webhook>>(`/api/v1/webhooks?${qs}`);
        },

        get(id: string): Promise<Webhook> {
          return apiFetch<Webhook>(`/api/v1/webhooks/${id}`);
        },

        create(data: WebhookCreate): Promise<Webhook> {
          return apiFetch<Webhook>('/api/v1/webhooks', {
            method: 'POST',
            body: JSON.stringify(data),
          });
        },

        update(id: string, data: WebhookUpdate): Promise<Webhook> {
          return apiFetch<Webhook>(`/api/v1/webhooks/${id}`, {
            method: 'PATCH',
            body: JSON.stringify(data),
          });
        },

        remove(id: string): Promise<void> {
          return apiFetch<void>(`/api/v1/webhooks/${id}`, { method: 'DELETE' });
        },

        count(): Promise<{ total: number }> {
          return apiFetch<{ total: number }>(`/api/v1/webhooks/count`);
        },
        restore(id: string): Promise<Webhook> {
  return apiFetch<Webhook>(`/api/v1/webhooks/${id}/restore`, { method: 'POST' });
},

        async trigger_test(id: string): Promise<Webhook> {
  return apiFetch<Webhook>(`/api/v1/webhooks/${id}/test`, {
    method: "POST",
    body: undefined,
  });
},

async rotate_secret(id: string): Promise<Webhook> {
  return apiFetch<Webhook>(`/api/v1/webhooks/${id}/rotate-secret`, {
    method: "POST",
    body: undefined,
  });
},

async disable_on_failures(id: string, threshold: number): Promise<Webhook> {
  return apiFetch<Webhook>(`/api/v1/webhooks/${id}/disable-on-failures`, {
    method: "POST",
    body: JSON.stringify({threshold: threshold}),
  });
},
      };
