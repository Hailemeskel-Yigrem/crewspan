      import { apiFetch, type PaginatedResponse } from './client';
      import type { Contact, ContactCreate, ContactUpdate, ContactListParams } from '../types/contact';

      export const contactApi = {
        list(params: ContactListParams = {}): Promise<PaginatedResponse<Contact>> {
          const qs = new URLSearchParams();
          if (params.page) qs.set('page', String(params.page));
          if (params.pageSize) qs.set('page_size', String(params.pageSize));
          if (params.search) qs.set('search', params.search);
          if (params.orderBy) qs.set('order_by', params.orderBy);
          if (params.orderDir) qs.set('order_dir', params.orderDir);
              if (params.customer_id !== undefined) qs.set('customer_id', String(params.customer_id));
  if (params.site_id !== undefined) qs.set('site_id', String(params.site_id));
          return apiFetch<PaginatedResponse<Contact>>(`/api/v1/contacts?${qs}`);
        },

        get(id: string): Promise<Contact> {
          return apiFetch<Contact>(`/api/v1/contacts/${id}`);
        },

        create(data: ContactCreate): Promise<Contact> {
          return apiFetch<Contact>('/api/v1/contacts', {
            method: 'POST',
            body: JSON.stringify(data),
          });
        },

        update(id: string, data: ContactUpdate): Promise<Contact> {
          return apiFetch<Contact>(`/api/v1/contacts/${id}`, {
            method: 'PATCH',
            body: JSON.stringify(data),
          });
        },

        remove(id: string): Promise<void> {
          return apiFetch<void>(`/api/v1/contacts/${id}`, { method: 'DELETE' });
        },

        count(): Promise<{ total: number }> {
          return apiFetch<{ total: number }>(`/api/v1/contacts/count`);
        },
        restore(id: string): Promise<Contact> {
  return apiFetch<Contact>(`/api/v1/contacts/${id}/restore`, { method: 'POST' });
},

        async set_primary(id: string): Promise<Contact> {
  return apiFetch<Contact>(`/api/v1/contacts/${id}/set-primary`, {
    method: "POST",
    body: undefined,
  });
},

async opt_out_notifications(id: string): Promise<Contact> {
  return apiFetch<Contact>(`/api/v1/contacts/${id}/opt-out`, {
    method: "POST",
    body: undefined,
  });
},
      };
