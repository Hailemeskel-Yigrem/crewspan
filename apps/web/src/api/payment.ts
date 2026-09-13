      import { apiFetch, type PaginatedResponse } from './client';
      import type { Payment, PaymentCreate, PaymentUpdate, PaymentListParams } from '../types/payment';

      export const paymentApi = {
        list(params: PaymentListParams = {}): Promise<PaginatedResponse<Payment>> {
          const qs = new URLSearchParams();
          if (params.page) qs.set('page', String(params.page));
          if (params.pageSize) qs.set('page_size', String(params.pageSize));
          if (params.search) qs.set('search', params.search);
          if (params.orderBy) qs.set('order_by', params.orderBy);
          if (params.orderDir) qs.set('order_dir', params.orderDir);
              if (params.invoice_id !== undefined) qs.set('invoice_id', String(params.invoice_id));
          return apiFetch<PaginatedResponse<Payment>>(`/api/v1/payments?${qs}`);
        },

        get(id: string): Promise<Payment> {
          return apiFetch<Payment>(`/api/v1/payments/${id}`);
        },

        create(data: PaymentCreate): Promise<Payment> {
          return apiFetch<Payment>('/api/v1/payments', {
            method: 'POST',
            body: JSON.stringify(data),
          });
        },

        update(id: string, data: PaymentUpdate): Promise<Payment> {
          return apiFetch<Payment>(`/api/v1/payments/${id}`, {
            method: 'PATCH',
            body: JSON.stringify(data),
          });
        },

        remove(id: string): Promise<void> {
          return apiFetch<void>(`/api/v1/payments/${id}`, { method: 'DELETE' });
        },

        count(): Promise<{ total: number }> {
          return apiFetch<{ total: number }>(`/api/v1/payments/count`);
        },
        restore(id: string): Promise<Payment> {
  return apiFetch<Payment>(`/api/v1/payments/${id}/restore`, { method: 'POST' });
},

        async refund(id: string, amount: number, reason: string): Promise<Payment> {
  return apiFetch<Payment>(`/api/v1/payments/${id}/refund`, {
    method: "POST",
    body: JSON.stringify({amount: amount, reason: reason}),
  });
},

async reconcile(id: string): Promise<Payment> {
  return apiFetch<Payment>(`/api/v1/payments/${id}/reconcile`, {
    method: "POST",
    body: undefined,
  });
},
      };
