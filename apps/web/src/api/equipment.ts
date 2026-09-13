      import { apiFetch, type PaginatedResponse } from './client';
      import type { Equipment, EquipmentCreate, EquipmentUpdate, EquipmentListParams } from '../types/equipment';

      export const equipmentApi = {
        list(params: EquipmentListParams = {}): Promise<PaginatedResponse<Equipment>> {
          const qs = new URLSearchParams();
          if (params.page) qs.set('page', String(params.page));
          if (params.pageSize) qs.set('page_size', String(params.pageSize));
          if (params.search) qs.set('search', params.search);
          if (params.orderBy) qs.set('order_by', params.orderBy);
          if (params.orderDir) qs.set('order_dir', params.orderDir);
              if (params.customer_id !== undefined) qs.set('customer_id', String(params.customer_id));
  if (params.site_id !== undefined) qs.set('site_id', String(params.site_id));
  if (params.asset_tag !== undefined) qs.set('asset_tag', String(params.asset_tag));
  if (params.serial_number !== undefined) qs.set('serial_number', String(params.serial_number));
          return apiFetch<PaginatedResponse<Equipment>>(`/api/v1/equipments?${qs}`);
        },

        get(id: string): Promise<Equipment> {
          return apiFetch<Equipment>(`/api/v1/equipments/${id}`);
        },

        create(data: EquipmentCreate): Promise<Equipment> {
          return apiFetch<Equipment>('/api/v1/equipments', {
            method: 'POST',
            body: JSON.stringify(data),
          });
        },

        update(id: string, data: EquipmentUpdate): Promise<Equipment> {
          return apiFetch<Equipment>(`/api/v1/equipments/${id}`, {
            method: 'PATCH',
            body: JSON.stringify(data),
          });
        },

        remove(id: string): Promise<void> {
          return apiFetch<void>(`/api/v1/equipments/${id}`, { method: 'DELETE' });
        },

        count(): Promise<{ total: number }> {
          return apiFetch<{ total: number }>(`/api/v1/equipments/count`);
        },
        restore(id: string): Promise<Equipment> {
  return apiFetch<Equipment>(`/api/v1/equipments/${id}/restore`, { method: 'POST' });
},

        async record_service(id: string, workOrderId: string, notes: string): Promise<Equipment> {
  return apiFetch<Equipment>(`/api/v1/equipments/${id}/record-service`, {
    method: "POST",
    body: JSON.stringify({work_order_id: workOrderId, notes: notes}),
  });
},

async retire(id: string, reason: string): Promise<Equipment> {
  return apiFetch<Equipment>(`/api/v1/equipments/${id}/retire`, {
    method: "POST",
    body: JSON.stringify({reason: reason}),
  });
},
      };
