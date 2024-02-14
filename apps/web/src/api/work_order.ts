      import { apiFetch, type PaginatedResponse } from './client';
      import type { WorkOrder, WorkOrderCreate, WorkOrderUpdate, WorkOrderListParams } from '../types/work_order';

      export const workOrderApi = {
        list(params: WorkOrderListParams = {}): Promise<PaginatedResponse<WorkOrder>> {
          const qs = new URLSearchParams();
          if (params.page) qs.set('page', String(params.page));
          if (params.pageSize) qs.set('page_size', String(params.pageSize));
          if (params.search) qs.set('search', params.search);
          if (params.orderBy) qs.set('order_by', params.orderBy);
          if (params.orderDir) qs.set('order_dir', params.orderDir);
              if (params.order_number !== undefined) qs.set('order_number', String(params.order_number));
  if (params.customer_id !== undefined) qs.set('customer_id', String(params.customer_id));
  if (params.site_id !== undefined) qs.set('site_id', String(params.site_id));
  if (params.status !== undefined) qs.set('status', String(params.status));
  if (params.assigned_technician_id !== undefined) qs.set('assigned_technician_id', String(params.assigned_technician_id));
          return apiFetch<PaginatedResponse<WorkOrder>>(`/api/v1/work-orders?${qs}`);
        },

        get(id: string): Promise<WorkOrder> {
          return apiFetch<WorkOrder>(`/api/v1/work-orders/${id}`);
        },

        create(data: WorkOrderCreate): Promise<WorkOrder> {
          return apiFetch<WorkOrder>('/api/v1/work-orders', {
            method: 'POST',
            body: JSON.stringify(data),
          });
        },

        update(id: string, data: WorkOrderUpdate): Promise<WorkOrder> {
          return apiFetch<WorkOrder>(`/api/v1/work-orders/${id}`, {
            method: 'PATCH',
            body: JSON.stringify(data),
          });
        },

        remove(id: string): Promise<void> {
          return apiFetch<void>(`/api/v1/work-orders/${id}`, { method: 'DELETE' });
        },

        count(): Promise<{ total: number }> {
          return apiFetch<{ total: number }>(`/api/v1/work-orders/count`);
        },
        restore(id: string): Promise<WorkOrder> {
  return apiFetch<WorkOrder>(`/api/v1/work-orders/${id}/restore`, { method: 'POST' });
},

        async submit(id: string): Promise<WorkOrder> {
  return apiFetch<WorkOrder>(`/api/v1/work-orders/{id}/submit`, {
    method: "POST",
    body: undefined,
  });
}

async assign_technician(id: string, technicianId: string): Promise<WorkOrder> {
  return apiFetch<WorkOrder>(`/api/v1/work-orders/{id}/assign-technician`, {
    method: "POST",
    body: JSON.stringify({technicianId: technicianId}),
  });
}

async start(id: string): Promise<WorkOrder> {
  return apiFetch<WorkOrder>(`/api/v1/work-orders/{id}/start`, {
    method: "POST",
    body: undefined,
  });
}

async complete(id: string, notes: str | null): Promise<WorkOrder> {
  return apiFetch<WorkOrder>(`/api/v1/work-orders/{id}/complete`, {
    method: "POST",
    body: JSON.stringify({notes: notes}),
  });
}

async cancel(id: string, reason: str): Promise<WorkOrder> {
  return apiFetch<WorkOrder>(`/api/v1/work-orders/{id}/cancel`, {
    method: "POST",
    body: JSON.stringify({reason: reason}),
  });
}
      };
