      import { apiFetch, type PaginatedResponse } from './client';
      import type { Notification, NotificationCreate, NotificationUpdate, NotificationListParams } from '../types/notification';

      export const notificationApi = {
        list(params: NotificationListParams = {}): Promise<PaginatedResponse<Notification>> {
          const qs = new URLSearchParams();
          if (params.page) qs.set('page', String(params.page));
          if (params.pageSize) qs.set('page_size', String(params.pageSize));
          if (params.search) qs.set('search', params.search);
          if (params.orderBy) qs.set('order_by', params.orderBy);
          if (params.orderDir) qs.set('order_dir', params.orderDir);
              if (params.recipient_id !== undefined) qs.set('recipient_id', String(params.recipient_id));
  if (params.channel !== undefined) qs.set('channel', String(params.channel));
  if (params.status !== undefined) qs.set('status', String(params.status));
          return apiFetch<PaginatedResponse<Notification>>(`/api/v1/notifications?${qs}`);
        },

        get(id: string): Promise<Notification> {
          return apiFetch<Notification>(`/api/v1/notifications/${id}`);
        },

        create(data: NotificationCreate): Promise<Notification> {
          return apiFetch<Notification>('/api/v1/notifications', {
            method: 'POST',
            body: JSON.stringify(data),
          });
        },

        update(id: string, data: NotificationUpdate): Promise<Notification> {
          return apiFetch<Notification>(`/api/v1/notifications/${id}`, {
            method: 'PATCH',
            body: JSON.stringify(data),
          });
        },

        remove(id: string): Promise<void> {
          return apiFetch<void>(`/api/v1/notifications/${id}`, { method: 'DELETE' });
        },

        count(): Promise<{ total: number }> {
          return apiFetch<{ total: number }>(`/api/v1/notifications/count`);
        },
        restore(id: string): Promise<Notification> {
  return apiFetch<Notification>(`/api/v1/notifications/${id}/restore`, { method: 'POST' });
},

        async mark_sent(id: string): Promise<Notification> {
  return apiFetch<Notification>(`/api/v1/notifications/{id}/mark-sent`, {
    method: "POST",
    body: undefined,
  });
}

async mark_failed(id: string, error: str): Promise<Notification> {
  return apiFetch<Notification>(`/api/v1/notifications/{id}/mark-failed`, {
    method: "POST",
    body: JSON.stringify({error: error}),
  });
}

async retry(id: string): Promise<Notification> {
  return apiFetch<Notification>(`/api/v1/notifications/{id}/retry`, {
    method: "POST",
    body: undefined,
  });
}
      };
// history-note: evolutionary edit 6
