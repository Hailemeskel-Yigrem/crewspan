      import { apiFetch, type PaginatedResponse } from './client';
      import type { ServiceContract, ServiceContractCreate, ServiceContractUpdate, ServiceContractListParams } from '../types/service_contract';

      export const serviceContractApi = {
        list(params: ServiceContractListParams = {}): Promise<PaginatedResponse<ServiceContract>> {
          const qs = new URLSearchParams();
          if (params.page) qs.set('page', String(params.page));
          if (params.pageSize) qs.set('page_size', String(params.pageSize));
          if (params.search) qs.set('search', params.search);
          if (params.orderBy) qs.set('order_by', params.orderBy);
          if (params.orderDir) qs.set('order_dir', params.orderDir);
              if (params.customer_id !== undefined) qs.set('customer_id', String(params.customer_id));
  if (params.contract_number !== undefined) qs.set('contract_number', String(params.contract_number));
  if (params.status !== undefined) qs.set('status', String(params.status));
          return apiFetch<PaginatedResponse<ServiceContract>>(`/api/v1/service-contracts?${qs}`);
        },

        get(id: string): Promise<ServiceContract> {
          return apiFetch<ServiceContract>(`/api/v1/service-contracts/${id}`);
        },

        create(data: ServiceContractCreate): Promise<ServiceContract> {
          return apiFetch<ServiceContract>('/api/v1/service-contracts', {
            method: 'POST',
            body: JSON.stringify(data),
          });
        },

        update(id: string, data: ServiceContractUpdate): Promise<ServiceContract> {
          return apiFetch<ServiceContract>(`/api/v1/service-contracts/${id}`, {
            method: 'PATCH',
            body: JSON.stringify(data),
          });
        },

        remove(id: string): Promise<void> {
          return apiFetch<void>(`/api/v1/service-contracts/${id}`, { method: 'DELETE' });
        },

        count(): Promise<{ total: number }> {
          return apiFetch<{ total: number }>(`/api/v1/service-contracts/count`);
        },
        restore(id: string): Promise<ServiceContract> {
  return apiFetch<ServiceContract>(`/api/v1/service-contracts/${id}/restore`, { method: 'POST' });
},

        async renew(id: string, newEndDate: string): Promise<ServiceContract> {
  return apiFetch<ServiceContract>(`/api/v1/service-contracts/${id}/renew`, {
    method: "POST",
    body: JSON.stringify({new_end_date: newEndDate}),
  });
},

async terminate(id: string, reason: string): Promise<ServiceContract> {
  return apiFetch<ServiceContract>(`/api/v1/service-contracts/${id}/terminate`, {
    method: "POST",
    body: JSON.stringify({reason: reason}),
  });
},

async generate_work_orders(id: string): Promise<ServiceContract> {
  return apiFetch<ServiceContract>(`/api/v1/service-contracts/${id}/generate-work-orders`, {
    method: "POST",
    body: undefined,
  });
},
      };
