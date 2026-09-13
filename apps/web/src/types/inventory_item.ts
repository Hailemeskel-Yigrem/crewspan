      /** Catalog of parts and consumables tracked in inventory. */
      export interface InventoryItem {
        id: string;
        tenantId: string;
        sku: string;
name: string;
description: string | null;
unit_of_measure: string;
unit_cost: string;
reorder_point: number;
reorder_quantity: number;
is_active: boolean;
category: string | null;
        createdAt: string;
        updatedAt: string;
        deletedAt: string | null;
      }

      export interface InventoryItemCreate {
        sku?: string;
name?: string;
description?: string | null;
category?: string | null;
      }

      export interface InventoryItemUpdate {
        sku?: string;
name?: string;
description?: string | null;
unit_of_measure?: string;
unit_cost?: string;
reorder_point?: number;
reorder_quantity?: number;
is_active?: boolean;
category?: string | null;
      }

      export interface InventoryItemListParams {
        page?: number;
        pageSize?: number;
        search?: string;
        orderBy?: string;
        orderDir?: 'asc' | 'desc';
          sku?: string;
name?: string;
category?: string | null;
      }

      export interface InventoryItemListResponse {
        items: InventoryItem[];
        total: number;
        page: number;
        pageSize: number;
        pages: number;
      }

      export function isInventoryItemActive(record: InventoryItem): boolean {
        const row = record as { isActive?: boolean; status?: string; deletedAt?: string | null };
        if (row.deletedAt) return false;
        if (typeof row.isActive === 'boolean') return row.isActive;
        if (row.status) return !['cancelled', 'inactive', 'void'].includes(row.status);
        return true;
      }

      export function inventoryItemDisplayName(record: InventoryItem): string {
        const row = record as { name?: string; title?: string; orderNumber?: string; displayName?: string };
        return row.displayName || row.name || row.title || row.orderNumber || record.id.slice(0, 8);
      }
