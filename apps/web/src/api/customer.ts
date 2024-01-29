      import { apiFetch, type PaginatedResponse } from './client';
      import type { Customer, CustomerCreate, CustomerUpdate, CustomerListParams } from '../types/customer';

      export const customerApi = {
        list(params: CustomerListParams = {}): Promise<PaginatedResponse<Customer>> {
          const qs = new URLSearchParams();
          if (params.page) qs.set('page', String(params.page));
          if (params.pageSize) qs.set('page_size', String(params.pageSize));
          if (params.search) qs.set('search', params.search);
          if (params.orderBy) qs.set('order_by', params.orderBy);
          if (params.orderDir) qs.set('order_dir', params.orderDir);
              if (params.account_number !== undefined) qs.set('account_number', String(params.account_number));
  if (params.name !== undefined) qs.set('name', String(params.name));
          return apiFetch<PaginatedResponse<Customer>>(`/api/v1/customers?${qs}`);
        },

        get(id: string): Promise<Customer> {
          return apiFetch<Customer>(`/api/v1/customers/${id}`);
        },

        create(data: CustomerCreate): Promise<Customer> {
          return apiFetch<Customer>('/api/v1/customers', {
            method: 'POST',
            body: JSON.stringify(data),
          });
        },

        update(id: string, data: CustomerUpdate): Promise<Customer> {
          return apiFetch<Customer>(`/api/v1/customers/${id}`, {
            method: 'PATCH',
            body: JSON.stringify(data),
          });
        },

        remove(id: string): Promise<void> {
          return apiFetch<void>(`/api/v1/customers/${id}`, { method: 'DELETE' });
        },

        count(): Promise<{ total: number }> {
          return apiFetch<{ total: number }>(`/api/v1/customers/count`);
        },
        restore(id: string): Promise<Customer> {
  return apiFetch<Customer>(`/api/v1/customers/${id}/restore`, { method: 'POST' });
},

        async update_credit_limit(id: string, limit: Decimal): Promise<Customer> {
  return apiFetch<Customer>(`/api/v1/customers/{id}/update-credit-limit`, {
    method: "POST",
    body: JSON.stringify({limit: limit}),
  });
}

async merge_into(id: string, targetId: string): Promise<Customer> {
  return apiFetch<Customer>(`/api/v1/customers/{id}/merge-into`, {
    method: "POST",
    body: JSON.stringify({targetId: targetId}),
  });
}

async archive(id: string): Promise<Customer> {
  return apiFetch<Customer>(`/api/v1/customers/{id}/archive`, {
    method: "POST",
    body: undefined,
  });
}
      };
