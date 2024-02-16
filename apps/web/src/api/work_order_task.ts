      import { apiFetch, type PaginatedResponse } from './client';
      import type { WorkOrderTask, WorkOrderTaskCreate, WorkOrderTaskUpdate, WorkOrderTaskListParams } from '../types/work_order_task';

      export const workOrderTaskApi = {
        list(params: WorkOrderTaskListParams = {}): Promise<PaginatedResponse<WorkOrderTask>> {
          const qs = new URLSearchParams();
          if (params.page) qs.set('page', String(params.page));
          if (params.pageSize) qs.set('page_size', String(params.pageSize));
          if (params.search) qs.set('search', params.search);
          if (params.orderBy) qs.set('order_by', params.orderBy);
          if (params.orderDir) qs.set('order_dir', params.orderDir);
              if (params.work_order_id !== undefined) qs.set('work_order_id', String(params.work_order_id));
          return apiFetch<PaginatedResponse<WorkOrderTask>>(`/api/v1/work-order-tasks?${qs}`);
        },

        get(id: string): Promise<WorkOrderTask> {
          return apiFetch<WorkOrderTask>(`/api/v1/work-order-tasks/${id}`);
        },

        create(data: WorkOrderTaskCreate): Promise<WorkOrderTask> {
          return apiFetch<WorkOrderTask>('/api/v1/work-order-tasks', {
            method: 'POST',
            body: JSON.stringify(data),
          });
        },

        update(id: string, data: WorkOrderTaskUpdate): Promise<WorkOrderTask> {
          return apiFetch<WorkOrderTask>(`/api/v1/work-order-tasks/${id}`, {
            method: 'PATCH',
            body: JSON.stringify(data),
          });
        },

        remove(id: string): Promise<void> {
          return apiFetch<void>(`/api/v1/work-order-tasks/${id}`, { method: 'DELETE' });
        },

        count(): Promise<{ total: number }> {
          return apiFetch<{ total: number }>(`/api/v1/work-order-tasks/count`);
        },
        restore(id: string): Promise<WorkOrderTask> {
  return apiFetch<WorkOrderTask>(`/api/v1/work-order-tasks/${id}/restore`, { method: 'POST' });
},

        async complete(id: string): Promise<WorkOrderTask> {
  return apiFetch<WorkOrderTask>(`/api/v1/work-order-tasks/{id}/complete`, {
    method: "POST",
    body: undefined,
  });
}

async reopen(id: string): Promise<WorkOrderTask> {
  return apiFetch<WorkOrderTask>(`/api/v1/work-order-tasks/{id}/reopen`, {
    method: "POST",
    body: undefined,
  });
}

async reorder(id: string, sequence: int): Promise<WorkOrderTask> {
  return apiFetch<WorkOrderTask>(`/api/v1/work-order-tasks/{id}/reorder`, {
    method: "PATCH",
    body: JSON.stringify({sequence: sequence}),
  });
}
      };
