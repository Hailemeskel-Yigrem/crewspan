      import { apiFetch, type PaginatedResponse } from './client';
      import type { InvoiceLineItem, InvoiceLineItemCreate, InvoiceLineItemUpdate, InvoiceLineItemListParams } from '../types/invoice_line_item';

      export const invoiceLineItemApi = {
        list(params: InvoiceLineItemListParams = {}): Promise<PaginatedResponse<InvoiceLineItem>> {
          const qs = new URLSearchParams();
          if (params.page) qs.set('page', String(params.page));
          if (params.pageSize) qs.set('page_size', String(params.pageSize));
          if (params.search) qs.set('search', params.search);
          if (params.orderBy) qs.set('order_by', params.orderBy);
          if (params.orderDir) qs.set('order_dir', params.orderDir);
              if (params.invoice_id !== undefined) qs.set('invoice_id', String(params.invoice_id));
          return apiFetch<PaginatedResponse<InvoiceLineItem>>(`/api/v1/invoice-line-items?${qs}`);
        },

        get(id: string): Promise<InvoiceLineItem> {
          return apiFetch<InvoiceLineItem>(`/api/v1/invoice-line-items/${id}`);
        },

        create(data: InvoiceLineItemCreate): Promise<InvoiceLineItem> {
          return apiFetch<InvoiceLineItem>('/api/v1/invoice-line-items', {
            method: 'POST',
            body: JSON.stringify(data),
          });
        },

        update(id: string, data: InvoiceLineItemUpdate): Promise<InvoiceLineItem> {
          return apiFetch<InvoiceLineItem>(`/api/v1/invoice-line-items/${id}`, {
            method: 'PATCH',
            body: JSON.stringify(data),
          });
        },

        remove(id: string): Promise<void> {
          return apiFetch<void>(`/api/v1/invoice-line-items/${id}`, { method: 'DELETE' });
        },

        count(): Promise<{ total: number }> {
          return apiFetch<{ total: number }>(`/api/v1/invoice-line-items/count`);
        },
        restore(id: string): Promise<InvoiceLineItem> {
  return apiFetch<InvoiceLineItem>(`/api/v1/invoice-line-items/${id}/restore`, { method: 'POST' });
},

        async recalculate(id: string): Promise<InvoiceLineItem> {
  return apiFetch<InvoiceLineItem>(`/api/v1/invoice-line-items/{id}/recalculate`, {
    method: "POST",
    body: undefined,
  });
}
      };
