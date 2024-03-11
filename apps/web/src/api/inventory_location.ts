      import { apiFetch, type PaginatedResponse } from './client';
      import type { InventoryLocation, InventoryLocationCreate, InventoryLocationUpdate, InventoryLocationListParams } from '../types/inventory_location';

      export const inventoryLocationApi = {
        list(params: InventoryLocationListParams = {}): Promise<PaginatedResponse<InventoryLocation>> {
          const qs = new URLSearchParams();
          if (params.page) qs.set('page', String(params.page));
          if (params.pageSize) qs.set('page_size', String(params.pageSize));
          if (params.search) qs.set('search', params.search);
          if (params.orderBy) qs.set('order_by', params.orderBy);
          if (params.orderDir) qs.set('order_dir', params.orderDir);
              if (params.code !== undefined) qs.set('code', String(params.code));
  if (params.technician_id !== undefined) qs.set('technician_id', String(params.technician_id));
          return apiFetch<PaginatedResponse<InventoryLocation>>(`/api/v1/inventory-locations?${qs}`);
        },

        get(id: string): Promise<InventoryLocation> {
          return apiFetch<InventoryLocation>(`/api/v1/inventory-locations/${id}`);
        },

        create(data: InventoryLocationCreate): Promise<InventoryLocation> {
          return apiFetch<InventoryLocation>('/api/v1/inventory-locations', {
            method: 'POST',
            body: JSON.stringify(data),
          });
        },

        update(id: string, data: InventoryLocationUpdate): Promise<InventoryLocation> {
          return apiFetch<InventoryLocation>(`/api/v1/inventory-locations/${id}`, {
            method: 'PATCH',
            body: JSON.stringify(data),
          });
        },

        remove(id: string): Promise<void> {
          return apiFetch<void>(`/api/v1/inventory-locations/${id}`, { method: 'DELETE' });
        },

        count(): Promise<{ total: number }> {
          return apiFetch<{ total: number }>(`/api/v1/inventory-locations/count`);
        },
        restore(id: string): Promise<InventoryLocation> {
  return apiFetch<InventoryLocation>(`/api/v1/inventory-locations/${id}/restore`, { method: 'POST' });
},

        async assign_to_technician(id: string, technicianId: string): Promise<InventoryLocation> {
  return apiFetch<InventoryLocation>(`/api/v1/inventory-locations/{id}/assign-to-technician`, {
    method: "POST",
    body: JSON.stringify({technicianId: technicianId}),
  });
}

async list_low_stock(id: string): Promise<InventoryLocation> {
  return apiFetch<InventoryLocation>('/api/v1/inventory-locations/${id}/low-stock', { method: "GET" });
}
      };
