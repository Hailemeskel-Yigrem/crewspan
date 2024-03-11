      import { apiFetch, type PaginatedResponse } from './client';
      import type { StockMovement, StockMovementCreate, StockMovementUpdate, StockMovementListParams } from '../types/stock_movement';

      export const stockMovementApi = {
        list(params: StockMovementListParams = {}): Promise<PaginatedResponse<StockMovement>> {
          const qs = new URLSearchParams();
          if (params.page) qs.set('page', String(params.page));
          if (params.pageSize) qs.set('page_size', String(params.pageSize));
          if (params.search) qs.set('search', params.search);
          if (params.orderBy) qs.set('order_by', params.orderBy);
          if (params.orderDir) qs.set('order_dir', params.orderDir);
              if (params.item_id !== undefined) qs.set('item_id', String(params.item_id));
  if (params.from_location_id !== undefined) qs.set('from_location_id', String(params.from_location_id));
  if (params.to_location_id !== undefined) qs.set('to_location_id', String(params.to_location_id));
  if (params.movement_type !== undefined) qs.set('movement_type', String(params.movement_type));
          return apiFetch<PaginatedResponse<StockMovement>>(`/api/v1/stock-movements?${qs}`);
        },

        get(id: string): Promise<StockMovement> {
          return apiFetch<StockMovement>(`/api/v1/stock-movements/${id}`);
        },

        create(data: StockMovementCreate): Promise<StockMovement> {
          return apiFetch<StockMovement>('/api/v1/stock-movements', {
            method: 'POST',
            body: JSON.stringify(data),
          });
        },

        update(id: string, data: StockMovementUpdate): Promise<StockMovement> {
          return apiFetch<StockMovement>(`/api/v1/stock-movements/${id}`, {
            method: 'PATCH',
            body: JSON.stringify(data),
          });
        },

        remove(id: string): Promise<void> {
          return apiFetch<void>(`/api/v1/stock-movements/${id}`, { method: 'DELETE' });
        },

        count(): Promise<{ total: number }> {
          return apiFetch<{ total: number }>(`/api/v1/stock-movements/count`);
        },
        restore(id: string): Promise<StockMovement> {
  return apiFetch<StockMovement>(`/api/v1/stock-movements/${id}/restore`, { method: 'POST' });
},

        async validate_quantity(id: string): Promise<StockMovement> {
  return apiFetch<StockMovement>(`/api/v1/stock-movements/{id}/validate`, {
    method: "POST",
    body: undefined,
  });
}

async reverse(id: string, reason: str): Promise<StockMovement> {
  return apiFetch<StockMovement>(`/api/v1/stock-movements/{id}/reverse`, {
    method: "POST",
    body: JSON.stringify({reason: reason}),
  });
}
      };
