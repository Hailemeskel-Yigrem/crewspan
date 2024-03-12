      import { apiFetch, type PaginatedResponse } from './client';
      import type { Invoice, InvoiceCreate, InvoiceUpdate, InvoiceListParams } from '../types/invoice';

      export const invoiceApi = {
        list(params: InvoiceListParams = {}): Promise<PaginatedResponse<Invoice>> {
          const qs = new URLSearchParams();
          if (params.page) qs.set('page', String(params.page));
          if (params.pageSize) qs.set('page_size', String(params.pageSize));
          if (params.search) qs.set('search', params.search);
          if (params.orderBy) qs.set('order_by', params.orderBy);
          if (params.orderDir) qs.set('order_dir', params.orderDir);
              if (params.invoice_number !== undefined) qs.set('invoice_number', String(params.invoice_number));
  if (params.customer_id !== undefined) qs.set('customer_id', String(params.customer_id));
  if (params.work_order_id !== undefined) qs.set('work_order_id', String(params.work_order_id));
  if (params.status !== undefined) qs.set('status', String(params.status));
          return apiFetch<PaginatedResponse<Invoice>>(`/api/v1/invoices?${qs}`);
        },

        get(id: string): Promise<Invoice> {
          return apiFetch<Invoice>(`/api/v1/invoices/${id}`);
        },

        create(data: InvoiceCreate): Promise<Invoice> {
          return apiFetch<Invoice>('/api/v1/invoices', {
            method: 'POST',
            body: JSON.stringify(data),
          });
        },

        update(id: string, data: InvoiceUpdate): Promise<Invoice> {
          return apiFetch<Invoice>(`/api/v1/invoices/${id}`, {
            method: 'PATCH',
            body: JSON.stringify(data),
          });
        },

        remove(id: string): Promise<void> {
          return apiFetch<void>(`/api/v1/invoices/${id}`, { method: 'DELETE' });
        },

        count(): Promise<{ total: number }> {
          return apiFetch<{ total: number }>(`/api/v1/invoices/count`);
        },
        restore(id: string): Promise<Invoice> {
  return apiFetch<Invoice>(`/api/v1/invoices/${id}/restore`, { method: 'POST' });
},

        async finalize(id: string): Promise<Invoice> {
  return apiFetch<Invoice>(`/api/v1/invoices/{id}/finalize`, {
    method: "POST",
    body: undefined,
  });
}

async send(id: string): Promise<Invoice> {
  return apiFetch<Invoice>(`/api/v1/invoices/{id}/send`, {
    method: "POST",
    body: undefined,
  });
}

async void(id: string, reason: str): Promise<Invoice> {
  return apiFetch<Invoice>(`/api/v1/invoices/{id}/void`, {
    method: "POST",
    body: JSON.stringify({reason: reason}),
  });
}

async recalculate_totals(id: string): Promise<Invoice> {
  return apiFetch<Invoice>(`/api/v1/invoices/{id}/recalculate`, {
    method: "POST",
    body: undefined,
  });
}
      };
