      import { apiFetch, type PaginatedResponse } from './client';
      import type { InventoryItem, InventoryItemCreate, InventoryItemUpdate, InventoryItemListParams } from '../types/inventory_item';

      export const inventoryItemApi = {
        list(params: InventoryItemListParams = {}): Promise<PaginatedResponse<InventoryItem>> {
          const qs = new URLSearchParams();
          if (params.page) qs.set('page', String(params.page));
          if (params.pageSize) qs.set('page_size', String(params.pageSize));
          if (params.search) qs.set('search', params.search);
          if (params.orderBy) qs.set('order_by', params.orderBy);
          if (params.orderDir) qs.set('order_dir', params.orderDir);
              if (params.sku !== undefined) qs.set('sku', String(params.sku));
  if (params.name !== undefined) qs.set('name', String(params.name));
  if (params.category !== undefined) qs.set('category', String(params.category));
          return apiFetch<PaginatedResponse<InventoryItem>>(`/api/v1/inventory-items?${qs}`);
        },

        get(id: string): Promise<InventoryItem> {
          return apiFetch<InventoryItem>(`/api/v1/inventory-items/${id}`);
        },

        create(data: InventoryItemCreate): Promise<InventoryItem> {
          return apiFetch<InventoryItem>('/api/v1/inventory-items', {
            method: 'POST',
            body: JSON.stringify(data),
          });
        },

        update(id: string, data: InventoryItemUpdate): Promise<InventoryItem> {
          return apiFetch<InventoryItem>(`/api/v1/inventory-items/${id}`, {
            method: 'PATCH',
            body: JSON.stringify(data),
          });
        },

        remove(id: string): Promise<void> {
          return apiFetch<void>(`/api/v1/inventory-items/${id}`, { method: 'DELETE' });
        },

        count(): Promise<{ total: number }> {
          return apiFetch<{ total: number }>(`/api/v1/inventory-items/count`);
        },
        restore(id: string): Promise<InventoryItem> {
  return apiFetch<InventoryItem>(`/api/v1/inventory-items/${id}/restore`, { method: 'POST' });
},

        async adjust_reorder_levels(id: string, point: int, quantity: int): Promise<InventoryItem> {
  return apiFetch<InventoryItem>(`/api/v1/inventory-items/{id}/adjust-reorder-levels`, {
    method: "POST",
    body: JSON.stringify({point: point, quantity: quantity}),
  });
}

async deactivate(id: string): Promise<InventoryItem> {
  return apiFetch<InventoryItem>(`/api/v1/inventory-items/{id}/deactivate`, {
    method: "POST",
    body: undefined,
  });
}

async calculate_stock_value(id: string): Promise<InventoryItem> {
  return apiFetch<InventoryItem>('/api/v1/inventory-items/${id}/stock-value', { method: "GET" });
}
      };
